# Technical Architecture

Status: Gate 2 implementation contract. This document defines the intended runtime boundaries before Gate 3 toolchain work begins. A compiled implementation and measured budgets remain required evidence; this document alone does not prove performance or compatibility.

## 1. Locked platform contract

| Area | Contract |
|---|---|
| Hardware | Standard 4 MiB Nintendo 64; no Expansion Pak dependency |
| Video | 320x240, 16-bit color, three framebuffers, one 16-bit depth buffer |
| Cadence | 30 Hz fixed gameplay tick and 30 FPS presentation target |
| Save | 4 Kbit/512-byte EEPROM, versioned dual-page journal |
| ROM | Target below 16 MiB; 32 MiB is a documented exception ceiling, not the working target |
| Memory | At least 512 KiB free heap at the measured worst point |
| Soak | Twenty complete transition loops with no persistent heap reduction |
| Renderer | libdragon preview `f13b48985edbf4310f07779c76d9a68c7605037b` and Tiny3D `e84172f29f719680ac3213a7f408c2f721ef7b24` |
| Build wrapper | libdragon CLI `12.2.1`; immutable preview container digest recorded in `reference-study.md` |
| Emulator | Ares 148, Homebrew Mode; emulator validation is not a real-hardware claim |

The application is a content-specific game, not a general engine. Its abstractions exist to make ownership, deterministic behavior, testing, and the complete opening chapter understandable.

## 2. Layering and source boundaries

Production code is divided into six one-way layers:

1. `platform/`: libdragon/Tiny3D adapters for display, RSP/RDP submission, controller polling, EEPROM blocks, ROM filesystem reads, audio, time, and debug output.
2. `core/`: main loop, scene controller, arenas, resource registry, transitions, save service, deterministic random number generator, assertions, and telemetry. `core` knows no story-specific IDs beyond generic types.
3. `data/`: generated immutable definition tables and decoders for creatures, moves, encounters, dialogue, quests, cutscene timelines, scene manifests, and strings.
4. `systems/`: exploration, collision, camera, interaction, dialogue, follower, battle simulation, battle presentation, world map, UI, audio direction, and story actions.
5. `scenes/`: thin composition modules that bind data and systems for each room or mode.
6. `game/`: `GameProgress`, story rules, boot policy, and the authoritative high-level flow.

Host tests compile `core`, pure parts of `data`, `systems/battle`, story conditions/actions, and save codecs without libdragon. No gameplay rule may require a Tiny3D object, an audio handle, or a ROM path.

Generated runtime assets and tables live under `build/generated/` and are never edited by hand. Editable sources live under `assets-src/`; optimized ROM outputs are reproduced by the build.

Dialogue and conditions have singular declarative inputs. `docs/DIALOGUE_GRAPH.md` supplies every literal DialogueNode/StringId field and exact UTF-8 byte string; `docs/CONDITION_REGISTRY.md` supplies every nonzero ConditionId as a typed AST plus one normative postorder compiler. `DATA_SCHEMAS.md` owns the runtime layouts, numeric domains, bridge byte comparisons, consumers, and invariants. Code may not reconstruct either table from story prose. The generator emits one topologically ordered `schema_all.h`/`.c` pair. Gate 2 compiles its canonical aggregate units with the host compiler; Gate 3 and later compile the identical units with both host and pinned N64 compilers under warnings-as-errors. Raw Markdown-fence concatenation is not a build interface.

The frozen dialogue input is exactly SHA-256 `5151387d32be8929f9a992f598393a152df3d6983aebc6a8b3cf2c2a35fbe5f6`. Generation parses exactly `223` `DialogueNode` records (`16` byte-locked bridge rows plus `207` nonbridge rows), including exactly `160` first-column Story copy rows and exactly `26` nonzero action mirrors, and emits one sorted `4,460`-byte array. It byte-compares every bridge field, action xref in both directions, camera cue/resource xref, and root-owner relation against Data. `scripts/validate-dialogue-graph` asserts the frozen hash, all counts, the bridge lock, graph closure, and generated coverage; any mismatch is a Gate 2 failure.

## 3. Global ownership model

`App` is the only process-lifetime owner. It contains:

- `Platform`: initialized display, depth buffer, controller, audio, EEPROM, DFS, and time services.
- `FramePipeline`: three `FrameContext` slots and render fences.
- `SceneController`: active scene, pending transition, loading shell, and transition token.
- `ResourceRegistry`: typed resource handles, generation checks, destructors, sizes, and owner scopes.
- `SaveService`: decoded progress, immutable pending snapshot, journal write state, and error status.
- `AudioDirector`: persistent mixer and music policy; scene-owned audio resources remain scoped.
- `InputRouter`: active controller, calibrated analog state, edge events, and reconnect modal.
- `Telemetry`: frame ring, allocation ledger, transition baselines, and debug overlay state.
- `GameState`: persistent progression and settings expressed only with fixed-width values and stable IDs.

`GameState` contains no pointers, renderer handles, scene-local actor instances, or open audio streams. Scenes receive a restricted `SceneServices` view rather than the full `App`. Systems cannot free resources owned by another scope.

### 3.1 Resource scopes

There are four explicit lifetimes:

- **Process:** display/depth surfaces, mixer, default font/glyph set, missing-asset debug resources, telemetry storage.
- **UI shell:** branded transition panel, save indicator, reconnect modal, and location-card primitives that survive scene replacement.
- **Scene:** environment models, collision, actors, matrices, display-list caches, skeletons, animations, sprites, scene SFX, dialogue pages, and camera rails.
- **Action:** short-lived battle/cutscene presentation objects allocated from a resettable action arena and destroyed after a completion fence.

Each successful load registers a typed destructor and byte count against one scope. A handle is `{slot, generation, type}`; stale generations fail in debug builds and resolve to a safe missing asset only for noncritical presentation assets. Critical collision, definitions, and required models fail scene entry.

Scene arenas serve POD state, collision data, transforms, and temporary decode output. Resources whose library destructor must run are registered even if their backing allocation is in the scene arena. Destruction is reverse-order and idempotent. Direct scene `malloc`/`free` is prohibited after `enter`; exceptions require a telemetry tag and review.

## 4. Scene controller

Every scene implements the following original interface:

```c
typedef struct GameSceneVTable {
    bool (*enter)(SceneContext *ctx, const SceneEnterArgs *args);
    void (*update)(SceneContext *ctx, const InputFrame *input);
    void (*fixed_update)(SceneContext *ctx, const InputTickFrame *input, uint32_t tick);
    void (*draw)(SceneContext *ctx, const RenderView *view);
    void (*exit)(SceneContext *ctx, SceneExitReason reason);
} GameSceneVTable;
```

`enter` is transactional: it either establishes every required invariant or returns false after its partial scope has been destroyed. `exit` may be called after a partial entry and must tolerate a second call. A scene never invokes another scene directly; it submits one `TransitionRequest` to the controller. New requests are rejected while a transition token is active.

The saved scene graph uses ten stable top-level scene IDs. Large interiors are segmented into independently owned zone bundles so save IDs remain stable without keeping every room resident:

```text
SCENE_BOOT -> SCENE_TITLE -> SCENE_OPENING_SLOT -> SCENE_NAME_ENTRY
 -> SCENE_SIM_ARENA -> SCENE_ANNEX_INTERIOR
SCENE_ANNEX_INTERIOR <-> SCENE_WORLD_MAP <-> SCENE_ESTATE_COURTYARD
SCENE_ESTATE_COURTYARD <-> SCENE_ESTATE_INTERIOR
SCENE_ANNEX_INTERIOR -> SCENE_END_CHAPTER
```

`SCENE_SIM_ARENA` is a simulation mode inside the already-loaded physical Annex simulation-room base, not a second environment. Entry loads `bnd.annex.sim_room.base`, then the action-scoped `bnd.sim.tutorial_overlay` supplies the virtual shell, four battle actors, battle UI, VFX, and battle audio. After the result and final presentation fence, the controller destroys that overlay and records the exact source generation, SceneId, ZoneId, SpawnId, action bundle, and action-state token. While the base is still source-owned it validates the destination nav/spawn/interaction tables and stages the lightweight onboarding action in a pending scope. Only at the no-fail commit point does it transfer the base owner token to `SCENE_ANNEX_INTERIOR`, select the physical room data, and publish onboarding handles. Retention is legal only for a required bundle whose complete AssetId/CRC/unpacked-size identity is byte-for-byte equal in both zone manifests. The registry atomically retags that one scope to the destination generation, invalidates every overlay handle, and asserts that no other source-scene resource survived. If an unexpected post-retag entry failure occurs, it destroys the pending destination scope, atomically retags the base back to the recorded source generation, restores that exact recorded source tuple/action state, and follows normal source rollback. Old and destination heavy bases never overlap and there is no empty reveal frame.

`SCENE_ANNEX_INTERIOR` switches among simulation room, atrium, director lab, player room, clinic, workshop, and threshold `ZoneId` bundles through the same fenced unload/stage contract. `SCENE_ESTATE_INTERIOR` similarly switches foyer, invention hall, and observatory study zones. The courtyard confrontation, real battle, and post-victory exploration are explicit modes of `SCENE_ESTATE_COURTYARD`: its required/optional physical base remains resident, while the Echoforms, battle UI, battle VFX, and battle audio live only in `bnd.estate.courtyard.battle`. That action bundle is fenced and destroyed immediately after the result, before post-battle exploration/story resources are admitted.

The closing `HOOK_001..HOOK_014` timeline is likewise an action/camera/VFX overlay on the already-loaded Annex atrium base; it does not load another environment. After `HOOK_014`, the controller publishes the immutable `CHECKPOINT_SLICE_COMPLETE` candidate for the stable post-chapter Annex tuple but retains the coherent Hook overlay, Annex base, monitor image, camera, and low tone while `FINAL_SAVE_OUTCOME_PENDING`. Verified success presents the generation-bound Save Done timed status over that retained owner; failure presents Retry/Continue Unsaved there, and Retry never releases it. Only after Save Done's visible-tick completion or explicit Continue Unsaved resolves the current outcome may `TRANS_DEF_HOOK_TO_END_CARD` reserve, fade to black, fence, destroy the Hook/Annex scopes, and enter UI-only `SCENE_END_CHAPTER`/`ZONE_END_CARD_UI`. That UI zone is non-saveable and has no spawn; its authored mark sequence then opens the end menu, and Continue reloads/re-enters the post-chapter Annex tuple rather than serializing the end card. `SceneId + ZoneId + SpawnId`, never a filename, is the durable location key for saveable scenes.

The controller chooses legal gameplay destinations from `TransitionDef`, process-screen destinations from `ProcessNavigationDef`, and durable current/last-safe/Continue tuples from `SaveableLocationDef`. Boot, Title, opening, name confirmation/cancel, Continue, and Return-to-Title therefore have explicit rows too. Data cannot create an arbitrary ROM path or function pointer, and a portal destination does not become saveable unless the separate registry admits it.

Boot AUTO is a typed completion, not a controller default. One nonzero
`BootReadyOwner` records exact nonzero generations for display, input, audio
(including the final typed silent-safe owner), filesystem, journal selection,
settings profile, and the staged Title shell. A subsystem callback may set its
bit only when both its boot-owner generation and live subsystem generation
match. Only the exact `0x7F` mask, `SCENE_BOOT`, empty campaign/draft/save/
transition ownership, and a second equality check of all seven live generations
may freeze the owner and mint `BootReadyToken`; that token copies all seven
generations. The process selector byte-compares token to frozen owner,
revalidates all seven live generations, consumes both once, clears input, and
then emits `PROC_TRIGGER_AUTO`. `COND_PROC_ALWAYS` remains constant only because
this typed structural gate runs first; stale display/audio callbacks, a pending
silent fallback, or a generation change leave Boot visible.

### 4.1 What a scene owns

A scene owns its camera state, environment/collision resource handles, instantiated actors, interaction index, local event queue, ambient loop handles, spawn table, and subsystem instances. It does not own player identity, party progression, objective state, settings, save journal, or transition state. Battle scenes own `BattleState` and a presentation queue; the estate retry snapshot remains in `GameState` until the battle resolves.

Room revisits reconstruct scene state from story flags, objective state, and one-time interaction bitsets. No scene-local boolean is relied on after exit.

## 5. Main loop and frame pipeline

The simulation tick is exactly 1/30 second. The platform clock feeds an accumulator; at most two fixed steps may be executed for one submitted frame. If more time accumulated, the excess is recorded as a timing fault and clamped rather than causing an unbounded catch-up spiral. Battle rules and story actions run only on fixed ticks. Menu cursor animation and fades also use integer ticks so behavior is testable.

`InputTickBridge` is the sole poll-to-simulation handoff. `InputRouter` stamps every hardware poll with a nonzero monotonic `poll_epoch` and records ordered press/release events in a fixed 32-event queue. `update` receives the read-only poll frame and may consume only edges owned by the active presentation/UI owner; each consumed event is removed by `(poll_epoch, event_ordinal)` before simulation delivery. For every fixed step, the bridge produces one `InputTickFrame`: held buttons and the latest calibrated analog sample are available on each step, while each unclaimed press/release event is delivered to the first eligible fixed step exactly once and then removed. A frame with zero fixed steps retains its unclaimed events; a frame with two steps cannot replay them on the second step. Queue overflow is a certification assertion and freezes input rather than dropping or inventing an edge. Controller loss flushes the queue without synthesizing releases, and reconnect/port transfer discards one complete poll before accepting or queuing input again.

One frame proceeds in this order:

1. Pump any special playback mode before acquiring a normal framebuffer.
2. Poll controller ports once and build edge-stable `InputFrame` data.
3. Apply the reconnect modal policy; disconnected gameplay cannot advance.
4. Call active-scene `update`, remove any presentation-owned accepted edges, then emit zero to two `InputTickFrame` values and call `fixed_update` once per emitted tick.
5. Advance audio commands generated by completed simulation events.
6. Commit only transition/save requests produced by a completed tick.
7. Acquire the next framebuffer and its matching `FrameContext`.
8. Verify that frame slot's prior RSP/RDP fence is complete before reuse.
9. Attach RDPQ, begin Tiny3D, populate the slot-local viewport/matrix pool, and draw world then UI.
10. Draw optional telemetry last, detach/show, and record a fence for that slot.
11. Record CPU, RSP/RDP, audio, arena, heap-low-water, and dropped-tick metrics.

Each `FrameContext` owns uncached or explicitly cache-managed viewport, matrices, dynamic vertices, and command data for only its framebuffer. No frame-visible memory is mutated until its fence completes. Models, textures, skeletons, animations, display lists, and their backing memory remain alive while any submitted frame can reference them.

Before scene resources are released, the controller stops new draws, calls the libdragon synchronization boundary (`rspq_wait` plus any required RDPQ detach/flush), verifies no frame generation references the old scope, then calls `exit`. This fence is mandatory for normal transitions, retry, skip, load failure, and shutdown.

## 6. Memory strategy

The 512 KiB floor is a measured global free-heap low-water mark, not merely unused bytes in a scene arena. Gate 3 records the linker map and post-initialization baseline; Gate 4 replaces the following planning caps with evidence without weakening the floor.

| Consumer | Planning cap |
|---|---:|
| Three 320x240x16 framebuffers | 450 KiB |
| One 320x240x16 depth buffer | 150 KiB |
| Process code/data, stacks, libraries, and fixed platform state | 700 KiB |
| Three frame render contexts and RSP-visible dynamic data | 300 KiB |
| Audio mixer, streams, and active SFX cache | 300 KiB |
| Persistent game/save/input/telemetry/UI state | 160 KiB |
| Largest active zone composite including action presentation | 1,100 KiB |
| Transition/decompression scratch | 250 KiB |
| Required measured free floor | 512 KiB |
| Planning headroom | 174 KiB |

The entries sum to 4 MiB. The 1,100 KiB zone envelope is the complete simultaneous zone composite: required base + loaded optional content + the single current action bundle + collision/nav/spawn/interaction data + scene/actor state + registered scene/action allocations and allocator overhead. It excludes the separately budgeted process/frame, global audio mixer/cache, persistent UI shell/save/input/telemetry, and transition scratch rows. `ASSET_INVENTORY.md` composite totals and the generated bundle report must remain at or below this same envelope; a bundle-local cap is not permission to add several maxima together. A category may grow only if a measured category shrinks and both memory acceptance tests below still pass. The telemetry overlay reports total free bytes, largest free block, each arena used/high-water value, registered external allocations, and active resource counts.

The contiguous-block acceptance value is generated, not subjective. Every legal dynamic heap allocation site that is not served by an already-reserved fixed arena or pool emits its maximum requested bytes and allocator metadata bytes. The report computes `required_largest_free_block = align_up_16(max(request_bytes + allocator_metadata_bytes))`. Fixed arenas/pools may be excluded only when their complete backing allocation occurred before the measured post-initialization baseline; an on-demand arena reservation remains a request in the maximum. At every certified worst point, total free heap must be at least 512 KiB **and** the measured largest free block must be at least `required_largest_free_block`. The report records the contributing allocation site, both byte values, and a same-size allocate/free probe; an empty registry, an unreported allocation site, fragmentation below the computed value, or a probe that changes the warmed baseline fails certification.

The scene arena is a 16-byte-aligned bump allocator with named submarks for scene state, collision, actor state, and action scratch. Decode scratch is a fixed pool and cannot silently fall back to heap allocation. Steady-state exploration and command selection perform no unbounded allocation. Dialogue text is prewrapped or uses a fixed glyph-layout buffer. The battle presentation queue and particle pools have fixed capacities and deterministic overflow policies.

At each transition the soak harness records:

- free heap and largest block before destination load;
- old scope registered bytes/resource counts after teardown;
- destination arena and external-allocation high-water marks;
- frame-context generations outstanding;
- audio stream/cache counts;
- transition scratch high-water mark.

After warming caches, the same source/destination point must return to the same baseline within allocator bookkeeping tolerance. Any monotonic loss fails the twenty-loop soak.

## 7. Resource loading and transitions

Runtime resources are addressed by generated numeric `AssetId`; scene code never embeds filenames. A generated manifest records type, one owning pack bundle, ROM offset, packed/unpacked size, alignment, and CRC. Separate load-manifest reference lists let required, optional, and action bundles reference shared actor/animation/UI/VFX assets without duplicating their packed bytes. Source dependency graphs are cycle-checked and flattened to AssetId lists; the validator rejects cycles, missing/orphan references, multiple pack owners, and mismatched retained-bundle identity. Both ROM and resident totals deduplicate by AssetId.

### 7.1 Transactional transition

A transition advances through explicit phases:

1. **Requested:** validate source scene, destination, spawn, story condition, and that no request is active.
2. **Quiesce:** close dialogue/menus through their normal cancel policy, freeze gameplay, snapshot stable progress, and begin fade/audio release.
3. **Fence:** finish the last old-scene frame and RSP/RDP work.
4. **Unload:** call old `exit`, destroy its resource scope, reset scene/action arenas, and verify ownership counts. The one declared `RETAIN_IDENTICAL_REQUIRED_BASE` transition instead fences and atomically retags only the identity-matched base scope as specified above.
5. **Load shell:** retain only process/UI-shell state. Show the branded location/loading treatment while real manifest I/O, decode, and conversion work remains.
6. **Stage:** load into a fresh scene scope, validating size, CRC, type, alignment, model/animation dependencies, collision, and entry prerequisites. Progress is bytes completed divided by known required bytes; no fake percentage is shown.
7. **Commit:** call `enter`. Only after success set `current_scene/current_spawn`, apply pending story actions, and create a stable save snapshot.
8. **Reveal:** end the loading indicator as soon as work completes, present the location card during the authored fade, restore control, and clear the transition token.

These names and numeric order are shared verbatim with data: `IDLE=0`, `REQUESTED=1`, `QUIESCE=2`, `FENCE=3`, `UNLOAD=4`, `LOAD_SHELL=5`, `STAGE=6`, `COMMIT=7`, `REVEAL=8`, `FAILED=9`, `ROLLBACK_SOURCE=10`, and `ROLLBACK_FATAL=11`. `enter` runs inside COMMIT; there is no separate ENTER phase. `FAILED` is reachable only after the recorded source has been reconstructed coherently and owns the closeable travel-failure page. `ROLLBACK_SOURCE` owns source reload while no scene is exposed. If that reload also fails, `ROLLBACK_FATAL` destroys every partial scene scope and exposes only the process-resident recovery UI; it can retry the immutable source descriptor or take the typed clean/acknowledged-dirty Return-to-Title path.

Story recipes have explicit sides around that phase machine. A PRE_SOURCE binding validates scratch progress, every resource/queue reservation, and its immutable save snapshot while the source scene is still recoverable; it publishes the complete recipe before FENCE/UNLOAD and never exposes a half-mutated source. A POST_ENTER binding stages against prospective progress, enters the destination, then atomically publishes the recipe and its save request before any StoryStart or player control. SAVE_AFTER_DESTINATION rows use the typed stable-destination recipe through the same post-enter transaction. Required owner close, suffix queue, milestone/save, and rollback slots are reserved before any progress publish, so a committed close/enqueue cannot subsequently fail.

First Annex departure is a distinct path: the first exit choice starts `SERA_DEPART_001`; only its final dismissal requests `TRANS_DEF_THRESHOLD_TO_MAP`. Its deferred dialogue-once bit, `FLAG_ANNEX_EXIT_CLEARED`, Departure checkpoint/chapter, stable threshold tuple, and immutable save page publish together in `TRANS_RECIPE_ANNEX_DEPARTURE`. Cancel/failure before that publish leaves both once bit and departure flag clear. Repeat exit uses the distinct choice root and `TRANS_DEF_THRESHOLD_TO_MAP_REPEAT`, whose stable-source recipe retains all later checkpoint/chapter/result/encounter semantics. The two transition conditions are exhaustive/disjoint and no controller chooses by priority.

The old and destination heavy scene bundles are never resident together. Very fast loads do not receive an artificial spinner delay; the visual fade/location card may still complete its authored transition. EEPROM writes cannot capture phases 2-6 as the current location.

Request admission first creates a process-resident provisional rollback descriptor that validates the source tuple, complete required-load identity, and recovery resources but deliberately leaves runtime generation/state/CRC unbound. Immediately before QUIESCE, after any `SAVE_BEFORE` request has either committed or explicitly published Travel Unsaved, the controller finalizes that descriptor with the resulting source progress generation, source-state token, and CRC; Cancel destroys the provisional copy. Other policies finalize after source validation. If destination staging or `enter` fails, every partial destination allocation is destroyed and phase enters `ROLLBACK_SOURCE`; the controller then performs a normal reload/entry of that exact finalized source tuple and post-pre-recipe progress state. A successful rollback advances to `FAILED`, reveals the coherent source, displays the exact message `Travel could not be completed.`, and re-enables the original interaction so the player can retry. The prior EEPROM page remains valid. A source prepare/load/enter failure advances to `ROLLBACK_FATAL`; no scene, collision, actor, or scene-owned UI is exposed. Retry uses the same finalized descriptor with a fresh load generation. Return-to-Title fences campaign callbacks and invalidates the campaign owner only after clean teardown or explicit dirty-loss acknowledgement. Neither failure may enter a scene with missing collision or required actors.

### 7.2 ROM and asset pipeline

The intended authored pipeline is:

```text
assets-src/<production-id-prefix>/<canonical.production.id>/{blender,audio,images,data}
    -> source validators and provenance checks
    -> Blender 4.5.11 LTS + Fast64 2.5.3 export where applicable
    -> pinned Tiny3D/libdragon converters
    -> generated packed assets + manifest + CRC/size report
    -> DFS image
    -> N64 ROM
```

Model conversion must fail on missing required animations, unexplained converter warnings, unsupported materials, invalid names, out-of-range texture dimensions, missing collision, or budget overflow. A source hash, tool versions, conversion arguments, runtime hash, and ledger asset ID appear in the validation report. Generated code uses numeric IDs and compile-time table counts.

Bundle validation is three-dimensional: every entry and bundle declares packed ROM bytes, unpacked bytes, and arena-cap bytes. For every legal zone/action composition, the validator resolves shared dependencies once and proves `required + loaded optional + one action + collision/nav/spawn/interaction + scene state + allocator overhead <= 1,100 KiB` and the zone's tighter cap. It also sums code, read-only data, DFS contents, alignment/padding, and ROM header to prove the complete image is below the 16 MiB working target. Crossing 16 MiB fails the normal build; the 32 MiB hardware ceiling is available only through an explicit reviewed exception report, never an automatic fallback.

## 8. Input and controller reconnect

`InputRouter` polls all four ports. While unbound, platform enrollment runs before logical mapping and accepts only a new Start/A edge, sorted by lower port then Start. It consumes the winning claim, clears every latch, discards one complete following poll, and publishes no logical context until that poll finishes; claiming A therefore cannot also confirm Title/New Game. Normal play then stays bound to that port. Reconnect transfer is distinct and Start-only. `InputTuningDef` is the sole radial-shaping and generic UI hysteresis/repeat authority; `CameraInputTuningDef` separately owns its checked digital yaw/pitch steps and mirrors. Inner/outer raw radii are `12/76`, UI enter/exit are `18022/13107` Q15, first/later repeats are `12/4` fixed ticks, and reconnect discards exactly one poll. For interior integer magnitude `m`, linear magnitude is `n=((m-12)*32767+32)/64`; with `Q=32767`, smoothstep forms the full widened numerator `n*n*(3*Q-2*n)`, divides once by `Q*Q` using `(num+den/2)/den`, then saturates to Q. Endpoint branches precede the formula. Goldens are `12 -> 0`, `44 -> 16384`, and `76 -> 32767`. The shaped result multiplies the normalized radial direction; no per-axis dead zone is legal. Digital UI events come only from the declared hysteresis/repeat state rather than raw stick noise.

The 29-row `HardwareInputBindingDef` table is the only hardware mapping. One
primary context is active. Exploration maps Stick=Move, A press/hold=Interact,
held B=Run, C-Left/Right=Yaw, held L+C-Up/C-Down=Pitch, bare C-Down=Relay, and
Start=Pause. Start also pauses only at a battle command/target safe boundary;
Dialogue has A reveal/advance alone and excludes Start. Name Grid uses repeated
Stick/D-pad directions, A Enter, B Delete, Start Confirm. Menus/Relay/Map/
battle use repeated directions, A Confirm, B Back; Relay adds L/R tabs and
battle adds Z Move Info. A/Start Skip exists only in the opening slate, and
Start transfer only in reconnect. Higher-priority L-chord pitch is resolved from
the same poll before bare C-Down Relay, so one press cannot do both. Context
change clears edges/held/repeat state, preventing exploration B-Run from
becoming menu B-Back. Invert X/Y swaps only the corresponding camera action.

On active-controller loss:

- latch a reconnect overlay from the persistent UI shell;
- freeze fixed gameplay, battle timers, dialogue typing, transition confirmation, and every name-entry edit/confirmation path;
- allow the presentation-only 106-tick opening-slate timeline to finish while disconnected, but hold the completed finalizer handoff at a locked name-entry state until a controller reconnects;
- keep audio at a deliberate paused/ducked state;
- do not synthesize releases as menu confirmation;
- allow the original port to resume, or require Start on another connected controller to transfer control;
- clear the pre-loss edge latch and discard all edge inputs for one complete poll frame after transfer.

This policy applies in exploration, dialogue, menus, battles, the world map, the slate, and the closing hook. Presentation time continuing on the slate cannot accept input or initialize/save progress. EEPROM writes already committed may finish, but a disconnect never begins or cancels a write.

### 8.1 Process/UI ownership

`ProcessUiBindingDef` is the only process-page composition and button/action authority. Its unique `(SceneId, ProcessUiOwnerId, state_variant)` key selects a canonical `UIScreenDef` plus a bounded slice of `ProcessUiItemDef`; every item declares Dialogue-page, static-String, or typed runtime-view source, layer/render/focus order, and either a typed `PROCESS_ACCEPT_*` token or a local UI action. The literal table has exactly 38 bindings and 125 nonoverlapping items. Process code may compare owner/state enums but cannot embed a DialogueId, StringId, copy literal, duplicate a save-failure button domain, or use content IDs as actions. Acquisition, close, state change, controller recovery, and capability selection clear edges and permit one accept per poll/render frame.
Exactly eighteen represented global/process-overlay owners may use `scene_id=0`;
all other owners require their exact scene. Process-static copy is exactly the
103-row `0x9F01..0x9F67` catalog. Relay display is exactly 27 ordered runtime
fields plus 68 exhaustive enum-to-string rows, so location/checkpoint/reason/
service/eligibility copy cannot be hard-coded by a formatter.

Title composes exactly `NEW GAME`, verified-save-gated `CONTINUE`, and `OPTIONS`; Options opens the reusable settings panel. Title Apply sanitizes and advances only the process-resident settings-profile generation: no campaign owner exists at Title, so it never creates a SaveRequest, selects a journal address, or claims persistence. New Game copies that profile into its runtime draft and eventual first page. Continue first decodes the selected verified page, then overlays the profile and marks the new runtime dirty iff any of the eight settings bytes differ from the decoded bytes. New Game invokes the typed title-journal selector: EMPTY routes to the new-game prompt, a verified legal page routes to overwrite confirmation, and preserved invalid/incompatible candidate bytes route to the invalid-save prompt; a stale loader generation fails closed and selection itself never mutates EEPROM. Name Entry uses its distinct `UI_SCREEN_NAME_ENTRY`/`ASSET_UI_SCREEN_NAME_ENTRY` generated from the existing `ui.screen.name_entry` inventory package—never the title background—and its YES/Return targets alone emit `PROCESS_ACCEPT_NAME_CONFIRM`/`PROCESS_ACCEPT_NAME_CANCEL_RETURN`. The opening binds branded `UI_SCREEN_CUTSCENE_SLATE` at layer 0, `INSERT CUTSCENE HERE` at layer 1, and the A/Start skip affordance at layer 2; accepted skip or natural completion emits the one idempotent `PROCESS_ACCEPT_OPENING_FINISH`, without DialogueController sequencing.

Pause is acquired only at a generation-current `SCENE_ALLOW_PAUSE` fixed-step
boundary. It freezes and snapshots the exact gameplay owner. Its fixed order is
Resume, Party, Field Relay, Settings, Return to Title. Party becomes legal with
a nonempty party even before Relay acquisition; pre-Relay Party opens the Party
runtime view with Messages/Resonance/Map/Save disabled and L/R pinned. Field
Relay remains visibly disabled until the unlock flag and all four page bits are
present. Party and Field Relay additionally require no live
`BattleRuntimeOwner`. Settings requires its typed stable-location rule and no
live battle owner, except for `ENCOUNTER_SIM_TUTORIAL` at `SAVELOC_SIM_INTRO`
when the retained Pause snapshot matches the current runtime/battle generations
and the phase is exactly command/target selection with no action, presentation,
result, transition, save candidate, or tutorial-gate transaction live. Thus a
real-battle Pause visibly enables only Resume and Return to Title; the tutorial
may also enable Settings at that exact boundary. Resume or Pause B restores the
exact frozen owner without a reload. Unlocked Relay always opens on
Party, then L/R/direct tab order is Party, Messages, Resonance, Map, Save. Party
shows the two validated `GameProgress.PartySlot`s, HP, Sync, moves, and Team
Link; it never reads `BattleActor` or an in-progress battle HP endpoint. Messages shows
typed Tavi/Ivo rows and reads graph copy without acquiring dialogue; Resonance
shows Team Link/Sync/record state; Map is informational and cannot travel; Save
shows registry-resolved location/checkpoint/reason/dirty/service/eligibility.
Every Relay B returns through its captured physical Pause or gameplay origin;
save-confirm B returns only to Relay Save. No state switch can reuse an edge.

The settings runtime view has exact default bytes `{1,0,80,80,1,0,0,0}` and
focus order Text Speed, Invert X, Invert Y, Music, SFX, Rumble, Overscan X,
Overscan Y, UI Contrast, Reset Defaults, Apply, Cancel. Text and contrast wrap
`0..2` by 1; camera X/Y independently XOR bits `1/2`; music and SFX clamp
`0..100` by 10; rumble toggles `0/1`; overscan axes clamp `0..8` by 1. Every
accepted edit changes scratch only and immediately invokes its typed text,
camera-model, mixer, SFX, six-tick rumble, safe-frame, or palette preview.
Reset copies the whole default vector and refreshes previews once in field order;
Down does not wrap past Cancel; B is Cancel at every focus. Cancel restores
preview/base bytes and the exact captured Title/Pause focus without generation,
dirty, profile, or EEPROM mutation. Title Apply sanitizes and advances only the
process profile. Pause Apply reserves the Settings SaveService route before
publishing runtime bytes; BUSY retains/locks the session, failure Retry reuses
the immutable request, failure Cancel restores prior settings/SaveReason/dirty,
and only a current verified commit updates the profile and returns to captured
Pause focus.

Relay Record Progress is the sole player-manual save producer. Its confirm owner
must close before capture; admission requires initialized campaign, stable
control, Relay plus all page bits, and the exact `SAVELOC_MANUAL_ALLOWED`
registry tuple. It captures immutable current progress, sets both LocationKeys
to that tuple and only `SAVE_REASON_MANUAL_RELAY`, and enters the ordinary
SaveRequest queue. BUSY retains unpublished scratch, COMMITTED shows Save Done
and restores Relay Save focus, and failure offers only immutable Retry or Cancel
through the Manual/Settings owner. Cancel publishes nothing and preserves live
settings/progress/dirty state.

Return-to-Title selection is origin-aware. On the first physical Return press,
clean gameplay/end-card/rollback owners route directly; dirty state creates one
`DirtyReturnWarningOwner` that captures exactly GAMEPLAY Pause, END_CARD menu,
or ROLLBACK_FATAL recovery generation/state/focus and consumes that press without
acknowledging loss. STAY destroys the warning and restores that exact origin and
focus. Confirmed Return alone emits the origin-specific one-use acknowledgement
(`GAMEPLAY`, `END_CARD`, or `ROLLBACK_FATAL`) with its current warning token;
only the corresponding navigation condition can consume the pair. A warning
cannot switch origins, fall through to screen zero, or use the first selector as
an acknowledgement. For the two gameplay Return conditions,
`CONTROL_STATE_STABLE` and `PROC_SOURCE_ANY_STABLE_GAMEPLAY` admit either a
current stable exploration Pause snapshot or a current
`BattleRuntimeOwner`-matched command/target Pause snapshot; no other battle
phase qualifies. Battle Return advances and destroys the battle owner, queues,
presenter state, `BattleState`, UI, and action bundle before destroying the
campaign. It never copies `BattleActor` HP into the durable party and never
creates or serializes a SaveRequest. Canceling a dirty warning instead restores
the exact frozen battle boundary.

Save failure resolves one of eighteen typed producers through one of eight source routes and six policies into exactly one Process UI owner. Only `PROCESS_UI_OWNER_FINAL_SAVE_FAILURE` may acquire the binary node `UI_SAVE_FAILED -> END_RETRY_SAVE / END_CONTINUE_UNSAVED`, and it appears once globally. Pre-transition, already-committed progress, retention-once, manual/settings, and first-New-Game failures each use their own exact process-static prompt; none acquires or reuses the final Dialogue root or a shared failure StringId. Their legal actions are respectively Retry/Travel Unsaved/Cancel, Retry/Continue Dirty, Retry/Continue Dirty, Retry/Cancel, and Retry/Return-to-Title. New Game never continues before its first page verifies. Every button is bound to the current request, UI, snapshot, owner, input epoch, and—when completing storage—the current attempt generation. A generic callback cannot inherit another policy, close a newer page, clean newer play, or erase the older journal anchor.

## 9. Exploration systems

### 9.1 Player motion and collision

Exploration uses one fixed-step kinematic capsule and the one literal
`PlayerMotionTuningDef`: walk/run speeds `384/704` Q8 (1.5/2.75 m/s),
acceleration/deceleration `1536/2048` Q8, yaw speed `46080` degree-Q8
(180 degrees/s), move enter/exit `3277/2458` Q15, run enter/exit
`22937/19660`, gravity `2304` Q8, and max fall speed `3072` Q8. Intent is
camera-relative on the ground plane; thresholds are hysteretic, integration is
saturating, and animation follows solved velocity rather than requested input.

`CollisionTuningDef` fixes capsule radius/height `72/384` Q8, skin `4`, step
height `64`, maximum walkable-slope cosine `23170` Q15 (45 degrees), ground
probe `12`, door clearance `152`, and fall recovery distance `768`. Each tick
uses a swept capsule, no more than four motion substeps and four ordered
penetration solves, then slide; a step requires full top and landing clearance
and a door requires the full capsule clearance. Unsupported motion returns to
the previous safe transform. Falling 3 m below the last grounded point or
leaving collision bounds validates the current zone generation and restores
exactly `ZoneBindingDef.safe_anchor_spawn_id`, logs the fault, and changes no
story state.

### 9.2 Camera

The follow camera owns desired target, yaw/pitch/distance, and a smoothed solved
pose. The sole `CameraTuningDef` sets yaw speed `30720` degree-Q8 (120
degrees/s), pitch `-8960..14080` degree-Q8 (-35..+55), distance
`384..1152` Q8 with default `896` (1.5..4.5 m, default 3.5 m), target height
`320` (1.25 m), sphere radius `32` (0.125 m), and yaw/pitch/distance/target
smoothing `6/6/8/6` ticks. The sweep tests WORLD+DOOR blockers from target to
desired eye before reveal, pulls in to contact minus skin, and never pushes
through a blocker.

`col.common.camera_volumes` is set-equal to exactly eleven generation-bound,
room-default orbit rows—no inferred rails or secondary fallbacks—with
`volume_id==source_volume_id==1..11`, priority 0, yaw/pitch bias 0, blocker mask
`0x0003`, and flags `0x0029`. Their `(zone, distance Q8, blend ticks)` values are
Annex Sim `(768,8)`, Atrium `(1024,12)`, Director Lab `(768,8)`, Player Room
`(704,8)`, Clinic `(768,8)`, Workshop `(768,8)`, Threshold `(896,8)`, Estate
Courtyard `(1024,12)`, Foyer `(768,8)`, Invention Hall `(896,10)`, and Study
`(768,8)`. The global orbit is the zero fallback; an additional volume/rail is a
reviewed data revision. Dialogue and cutscenes acquire a camera token; returning
it blends from the current solved pose, never a stale snapshot.

C-Left/Right apply exactly 4 degrees per fixed tick (120 degrees/s); held
L+C-Up/Down applies 2 degrees per tick (60 degrees/s). The input yaw-speed field
is only a checked mirror of `CameraTuningDef.yaw_speed_deg_q8`, and both speeds
must equal step times 30. Desired yaw/pitch/distance and Q16.16 target-vector
components use the Data finite interpolation, not an arbitrary lerp: a desired
change captures solved start/target, then tick `k` applies signed, ties-away
rounding of `abs(delta)*k/duration` from the original start. Durations are
`6/6/8/6`; final tick assigns target exactly. Yaw uses the shortest half-open
[-180,+180) degree-Q8 arc; scalar deltas <=1 Q8 and target components <=256 Q16
snap. Goldens are yaw `0->7680: 1280/3840/7680` at ticks 1/3/6, pitch
`-2560->5120: -1280/1280/5120`, distance `896->512: 848/704/512` at
1/4/8, and target component `0->65536: 10923/32768/65536`. Collision pull-in
runs after interpolation and never feeds the distance owner. New desired input
restarts from the current solved pose; token/generation changes cancel stale
ticks.

Dialogue composition is data, not a speaker-name switch. Every nonzero graph cue resolves one of the 15 exact `DialogueCameraCueDef` rows `0x8600..0x860E`, then one manifest-backed 36-byte `CameraShotResourceDef` containing target/framing modes, Q16 eye/look offsets, FOV, and blend ticks. Literal node value `0` means no camera request and resolves no resource; `CAMERA_CUE_UI_NONE=0x8600` is distinct and explicitly preserves the active camera for UI ownership. The complete shot payload is only `15 * 36 = 540` unpacked bytes before manifest alignment. Each runtime AssetId is a generated child of the existing UI/environment/landmark/camera-volume/world-map production package named in Data, so the BOM records that parent and does not create hidden inventory or ledger work.

Scene/load closures must contain every shot used by their graph rows. A world cue cannot acquire until its speaker/group/interaction/scene marker and current actor generation resolve; missing required target/shot data fails owner acquisition before movement or camera tokens change. Chain close, cancel, controller takeover, transition, and failure all release the exact token and blend from the current solved pose. Generation proves the graph camera domain is exactly zero-or-registered, all 15 registered assets have one manifest owner and valid parent mapping, and `RUSK_ENTRY_001..003` byte-lock to the authored foyer cue `0x8607` under the approved pre-build lock migration.

### 9.3 Interaction, doors, elevators, and dialogue

Interactables are stable IDs with a proximity volume, facing score, prompt anchor, condition, and action. The selector chooses the best legal candidate using selection priority, distance, facing, then `InteractionId`, preventing flicker. The prompt is projected into the CRT-safe frame and falls back to a bottom prompt if its world anchor is occluded or offscreen.

Dialogue acquires movement and camera locks, displays prevalidated wrapped strings, and accepts A alone: the first A completes type-on and a later poll-frame A advances. Start has no Dialogue action and cannot reveal, advance, skip, or open Pause while Dialogue owns the context. Each story action applies exactly once when its node commits. Closing dialogue always releases its tokens, including rapid cancel, transition, or controller loss. Doors and elevators enqueue transitions only after dialogue/action completion and never change scene state from a draw callback.

The runtime graph is generated byte-for-byte from `DIALOGUE_GRAPH.md`; it never infers the next row, camera, emote, action, auto timing, or zero default from file order. Dialogue emits typed ENTER/DISMISS events, but `StoryTriggerBindingDef` is the only StoryAction dispatcher; every DialogueNode action field is an equality-only xref. Exact-once keys include runtime generation, dialogue owner generation, node, and phase. Conversation-level once records commit only at the declared terminal node, so interruption of `RUSK_ENTRY_001..003` cannot hide the remaining pages. The first Sera-depart bit is the sole deferred once record and commits with its transition recipe rather than early dialogue closure.

`PortalDialogueRouteDef` owns both skimmers. The Annex selector has disjoint no-Relay, no-trace, first-ready, and repeat-ready rows; first/repeat OPEN options are distinct DialogueIds with one action owner each. The Estate selector splits ordinary departure from follower return, then uses saved once bit 9 to play `RUSK_EXIT_001 -> TAVI_EXIT_001` exactly once or route directly to a repeat confirmation. Back/cancel changes no progress or transition state. The generated `HelpPromptDef` table similarly owns six first-use prompts with exact triggers, completion events, priorities, predecessor bits, nonstacking behavior, and controller-loss pause; completion only sets its registered once bit for the next otherwise-legal save.

`NpcInteractionRouteDef` owns mandatory/repeat/post selection for shared characters and the five locked physical IDs `0x201E..0x2022`. Each ID resolves a real `InteractionDef` or actor-attached Tavi record with an authored model focus socket, nonzero prompt/radius, exact facing/priority, and router-owned zero condition/action; the fixed Annex/Courtyard/Study rows remain inside their frozen inventory interaction counts. The selector validates stable control, reserves DialogueController before releasing the prompt, and dispatches mandatory rows through the equality-matched `StoryStartEdgeDef` rather than acquiring them twice. Oren's legal priority is dirty post `6`, saved post `5`, assignment `3`, then pre-Relay repeat `2`; that repeat requires quest-started and Relay-not-unlocked, so `OREN_004..006` cannot become stale after Jo's handoff. Later pre-chapter Oren states intentionally offer no dialogue. Saved/dirty conditions use the generation-bound post-chapter view and reject cross-paired outcomes; optional NPC once state never selects era copy.

The Estate orrery switch is owned by the generated `HeldInteractionDef` for `INT_ORRERY_SWITCH`: exactly 45 consecutive fixed 30 Hz gameplay ticks, not presentation time. From press until cleanup, saving and the study transition are disabled while the switch animation, arm-clear animation, open stair pose, replacement collision, and study-stair nav edge are staged. Only their coherent publish commit sets monotonic `FLAG_ORRERY_STAIR_OPEN`; `TRANS_DEF_HALL_TO_STUDY` tests that exact flag. Release, controller disconnect, leaving the legal interaction volume, transition/dialogue/state takeover, or any external interruption before commit invokes the same idempotent cancel/reset action, restores the released switch and blocked arm pose, retains blocked collision/nav, and leaves the flag false. Hall/study entry and manual-save load reconstruct open pose/collision/nav iff the flag is true. Story validation rejects `tavi_found` without it.

### 9.4 Companion follower

Tavi follows using room-authored nav nodes plus short-range steering, yields
around the player and mandatory interactions, is nonsolid to the player capsule,
and crosses rooms only through explicit door/elevator handoff anchors. Normal
follow uses exact min/target/max `307/410/512` Q8 (~1.2/1.6/2.0 m), selects
the reachable 1.6 m-behind offset by path cost then node ID, and rejects any
swept path entering the 192-Q8 player/interaction yield disc. Below min it stops
and yields; through max it caps at 448 Q8 (1.75 m/s); above max it caps at 832
Q8 (3.25 m/s). Velocity changes by +60/-77 Q8 per tick (1792/2304 Q8/s^2)
without overshoot and facing by at most 1843 degree-Q8/tick (216 degrees/s).
Within 128 Q8 of a portal it stops in the authored wait pose; door-open,
destination-nav, and paired-anchor facts must remain generation-current for two
ticks before handoff capture and source unload. There is no timeout teleport.
The sole
valid follower zones and recovery-distance Q8 thresholds are Study `1536`,
Invention Hall `2048`, Foyer `1536`, Courtyard `2560`, Annex Threshold `1536`,
and Annex Atrium `2048`. Recovery becomes eligible only when distance remains
above that row's threshold for all 45 fixed ticks **and** path progress remains
below `8/256 m` for at least 30 ticks. It searches no more than 48 nodes in the
same connected component for a clear `NAV_NODE_RECOVERY` behind the player,
choosing lowest path cost then node ID. Both actor and anchor must be outside the
camera frustum plus 16 pixels and blocker-occluded for two consecutive rendered
frames before the next fixed-step relocation. A scene/follower/camera generation
change, transition, Pause/modal, recovered progress, visibility, or distance
drop cancels the pending recovery and resets both timers. It can never recover
across a closed door or zone; room separation is handled only by handoff, and
World Map stores only the handoff snapshot. A legal recovery is logged and may
not mutate story state.

World-map transfer has mutually exclusive transition rows rather than request priority. Ordinary Estate-to-map and map-node rows require the return-objective follower derived false; return-story rows require `return_to_annex_requested`, the active Return objective, and that follower derived true. Tavi follows the concrete Study -> Invention Hall -> Foyer -> Courtyard handoff chain and enters the map only through the courtyard skimmer interaction. Annex is the only progressing return-story selection. Selecting Estate uses the appropriate ordinary or follower-handoff row back to `SPAWN_ESTATE_COURTYARD_FROM_MAP`; selecting Annex hands off Map -> Threshold -> Atrium. There is no direct Study-to-map teleport or top-level Estate-interior-to-map edge.

Map focus/prompt/confirmation is also typed data. `MapNodePresentationDef` points at the exact graph rows for both names/descriptions; `MapConfirmRouteDef` maps selected node plus one condition to one prompt/choice triple and one TransitionId. Follower-only Courtyard-to-map uses `COND_TRANS_RETURN_FOLLOWER_ACTIVE`; map-to-Annex and map-to-Estate use distinct conditions that additionally require `MAP_SELECTION_ANNEX` and `MAP_SELECTION_ESTATE`, respectively. No ConditionId changes meaning by caller. Back inside an open confirmation closes only that prompt, discards one poll frame, and stays on the map. Map-level Back with no confirmation does **not** mean stay: it resolves the generation-current immutable `MapOriginSnapshot` through the exact three-row `MapCancelRouteDef` registry and returns to the captured Annex threshold, Estate courtyard, or Estate courtyard with follower handoff. Every cancel row uses `SAVE_NONE`, preserves progress, requires stable map control/current origin generation, and clears selection without story/save mutation.

On the Annex side, `TRANS_DEF_MAP_RETURN_TO_ANNEX` reaches the threshold and ordinary player control continues through the threshold-to-atrium portal. RETURN dialogue does not start on portal COMMIT. The player and derived Tavi follower must physically overlap `INT_ANNEX_RETURN_RESOLUTION_VOLUME` for two stable ticks after an authored 20–45 second normal-speed walk; only that WORLD_VOLUME_ENTER edge starts `RETURN_001`. Reboot resumes at a legal route point and can reach the same volume. Teleport/scene-enter/portal-scan shortcuts fail reachability validation.

## 10. Dialogue, quest, and story execution

Conditions are pure reads over immutable typed scalar views. Progress/dialogue/save conditions receive only `ProgressConditionView`; transition conditions may additionally receive confirmed-draft, tutorial-result, selected-map-node, prebattle-snapshot, derived-follower, and in-memory-checkpoint tokens; process navigation may additionally receive journal validity, dirty state, resolved save outcome, and warning acknowledgement. The narrow `PostChapterInteractionConditionView` exposes persisted sources plus only generation-current save outcome/dirty state, enabling disjoint saved versus unsaved Oren copy without granting ordinary interactions process tokens. Each `ConditionDef` declares its allowed context/source mask, and the evaluator rejects unavailable sources. No condition mutates state, consumes RNG, allocates, or reads future presentation/input.

Every nonzero ConditionId appears exactly once in the canonical typed AST registry. Its compiler emits literal source/constant leaves and operators in normative left-to-right postorder with no folding, reordering, or alternate simplification, then deterministically computes the dense instruction range, peak stack, exact context mask, and exact source mask. Generation compiles every registry row and byte-compares `ConditionDef`/`ConditionInstr`; an unregistered consumer or unused registry ID fails. Persisted save predicates spell out every accessible flag/objective/checkpoint/result/party fact; the global SaveData semantic validator proves exact tuple, party layout, encounter/reward, and other facts not exposed as condition sources.

Actions are a small validated opcode set. Besides monotonic flags/objectives and one-time grants, a bounded quest-substage opcode enforces the Relay counter's exact `0->1->2->3` path inside scratch-progress transactions. The Orrery flag cannot use the generic flag opcode: its commit action invokes one typed mechanism-world transaction that stages and atomically publishes the open pose, collision, and nav edge before setting the flag. Actions cannot call arbitrary code or manipulate asset paths.

The Relay acquisition has one locked persistence boundary. `JO_RELAY_003` is only an authored linked-UI preview while the modal sequence owns input. Dismissing `JO_RELAY_006` atomically sets `FLAG_FIELD_RELAY_UNLOCKED`, Relay quest substage 2, all four player-owned Relay page bits, and the visible `Ask Pell to trace Tavi's message.` step while keeping Retrieve Relay as the sole active objective. Its automatic `CHECKPOINT_FIELD_RELAY` request occurs only after workshop exploration control is stable; no save is legal inside the acquisition presentation.

One event dispatcher owns story action idempotence. `StoryTriggerBindingDef` is the sole dispatcher for dialogue, encounter result, world callback, hook sequence, held interaction, and transition-recipe owners; every other `*_xref` is validation-only and direct list calls are a certification failure. Each list prevalidates scratch progress, typed resources, external targets, owner-close/queue reservations, and generation tokens before one no-fail publish. Chapter milestones reserve close/save/continuation ownership before progress; final SAVED and explicit CONTINUE_UNSAVED outcomes both use typed rows to request `TRANS_DEF_HOOK_TO_END_CARD` without claiming a dirty write succeeded.

Story acquisition is also data. `StoryStartEdgeDef` maps transition outcomes, tutorial-intro completion, world volumes, interactions, milestones, stable reveals, and Continue checkpoints to registered dialogue/sequence roots under exact location/flag/objective/actor/resource/once preconditions. This is the only automatic root path; scenes do not scan flags or hard-code `SIM_001`, Rusk, Reunion, Return, or Hook IDs. The tutorial has two literal, mutually exclusive edges to `SIM_001`: live Name-to-Sim releases `TUTORIAL_INTRO_COMPLETE / TUTORIAL_SCRIPT_OPENING`, while a fresh loaded bootstrap releases `CONTINUE_LOADED_STABLE / CHECKPOINT_AFTER_NAME`; the bootstrap records its source kind and cannot publish both. One-time rewards have both the completion flag and a dedicated claim bit; repeated dialogue may show alternate text but cannot grant again. Scene entry validates mandatory actor/interaction availability against the current objective. Debug builds can print the condition and StoryStart traces explaining why a row is or is not available.

## 11. Battle architecture

The tutorial and estate fight use the same deterministic simulation. `BattleState` contains only IDs, integer stats, actor state, commands, a seeded RNG, and phase state. `BattlePresenter` consumes the 64-entry simulation-to-presentation `BattleEvent` queue and owns camera cues, animation requests, VFX, UI timing, and audio. The simulation cannot query animation time. Completion returns through a separate eight-entry presenter-to-simulation `BattlePresentationAck` queue as `BATTLE_ACK_PRESENTATION_COMPLETE`, carrying action sequence plus runtime/battle generations; stale, duplicate, wrong-sequence, or wrong-generation acknowledgements never advance phase.

Simulation bootstrap precedes tutorial dialogue. After Name-to-Sim's post recipe/save outcome—or a validated Continue at `CHECKPOINT_AFTER_NAME`—the typed bootstrap constructs `ENCOUNTER_SIM_TUTORIAL` exactly once, stages all four TeamDef actors/nameplates/arena/UI, binds runtime/battle/tutorial generations, and runs the exact 210-tick (seven-second) fly-in. Only its blocking completion advances to INTRO_DIALOGUE. A live row then emits `TUTORIAL_INTRO_COMPLETE / TUTORIAL_SCRIPT_OPENING`; a loaded row instead releases the delayed `CONTINUE_LOADED_STABLE / CHECKPOINT_AFTER_NAME` source. The source kind is bound when the bootstrap owner is created, the two events cannot coexist, and either exact edge acquires `SIM_001 -> SIM_002` before player input. `SIM_002` dismissal executes `ACTION_ADVANCE_TUTORIAL_GATE`, an internal compare-and-advance from INTRO_DIALOGUE to Gate 1; it never constructs a second encounter. Controller loss pauses the fly-in and stale completions cannot acquire a new generation.

The phase machine is:

```text
INTRO
 -> COMMAND_SELECT -> TARGET_SELECT (for each required actor)
 -> BUILD_TURN_QUEUE
 -> ACTION_BEGIN -> ACTION_PRESENT -> DAMAGE_STATUS_RESOLVE
 -> optional KNOCKOUT_REPLACE
 -> next action or ROUND_CLEANUP
 -> COMMAND_SELECT, VICTORY, or DEFEAT
 -> RESULT_PRESENT -> EXIT
```

All commands are validated at selection and again at execution. If a target became invalid, the lowest-lane/lowest-instance same-side replacement is chosen only when that `MoveDef` has `MOVE_RETARGET_SAME_SIDE`; there is no implicit retarget. Otherwise the action resolves as a documented no-op after revalidation and battle-end detection. Turn sorting is integer-only: move priority descending, effective speed descending, then stable actor instance ID. Every damage/status application has an action sequence ID and can commit once only.

Damage uses an original integer formula defined by tests:

```text
base = max(1, move_power + (power * 3) / 4 - guard / 2)
damage = max(1, base * affinity_q8 * variance_q8 / (256 * 256))
```

`affinity_q8` is `384` for advantage (1.5x), `192` for disadvantage (0.75x), and `256` for neutral. `variance_q8` is a deterministic bounded value in `[240,272]` from the battle seed. The multiply uses a widened intermediate and one final floor division. Required golden vectors are:

| Move power | Power stat | Guard | Affinity | Variance | Exact damage |
|---:|---:|---:|---:|---:|---:|
| 28 | 40 | 30 | 256 | 256 | 43 |
| 26 | 43 | 38 | 384 | 256 | 58 |
| 32 | 48 | 28 | 192 | 256 | 40 |
| 29 | 41 | 46 | 256 | 240 | 33 |
| 1 | 1 | 200 | 192 | 240 | 1 |

`Power`, `Guard`, and `Speed` are the canonical player-facing stat names. Internal C fields may use `base_attack`/`effective_attack`, but the schema maps them explicitly to displayed Power and no UI/string data may emit `Attack`. Their stage multipliers for `-2,-1,0,+1,+2` are exactly `128,192,256,320,384` Q8.8; effective stats floor `derived*multiplier/256` and clamp to at least 1. Staggered's 192/256 Speed multiplier applies after the Speed stage. Each stage has its own duration and applied-round stamp: reapplication adds/clamps the stage and refreshes duration, same-round cleanup does not decrement it, later cleanups decrement and expire at zero. Speed changes stable-sort only the unexecuted queue suffix; Power/Guard never reorder. Knockout and battle end clear every volatile modifier. `Guiding Draft` is a separate one-use flag: it multiplies the actor's next successfully committed damaging move by 120% after the normal damage calculation, then clears; it is not a status or Power stage even if the UI labels it `EMPOWERED`.

The sole temporary status ailment in this chapter is `STATUS_STAGGERED`. It applies Speed -25% through that actor's next completed action, then expires. If applied before a target's pending action, the simulation recomputes effective Speed and stable-sorts only the unexecuted command suffix; executed commands never move. If the target already acted, Staggered changes its next-round queue key and remains until that next action completes. KO and an explicit cleanse clear it without creating an action; battle retry rebuilds status-free actors from the encounter seed. After a successful hit, each chance-bearing status consumes one 8-bit draw per living target in stable lane/instance order before effects commit and applies on `draw < chance`: Dazzle is 89/256 (UI 35%) and Static is 64/256. Guaranteed Fault Pin/Furnace Feint use an always-apply flag rather than a fake 255 threshold. The only permitted RNG calls are intermediate accuracy, per-target variance, and chance status; schema golden vectors lock their order. AI ties use sorted MoveId then target instance and consume no RNG.

Support effects use explicit effect opcodes and never pass through the damage formula. `TARGET_SELF_OR_ALLY` includes the acting creature and its conscious active partner, rejects every enemy, and rejects a KO partner; move-specific validation may further require a partner. UI previews disclose target legality and affinity category, not hidden AI state.

Enemy AI enumerates legal `(move,target)` pairs, assigns bounded integer scores from visible HP, affinity, status, support synergy, expected knockout, and repetition penalties, then uses stable IDs for ties. Difficulty scripts may alter weights but never read the player's unconfirmed commands or future RNG.

Resonance is an integer from 0 to 100 in simulation, schema, save-facing records, and UI. Only player-side sources can award it; enemy damage/support always grants zero. Player awards commit after the successful effect and are deduplicated by action sequence and source: a damaging action that deals HP grants `+6` once, an affinity-advantage hit adds `+4` once, partner support grants its move-defined `+10`/`+12`/`+14`, clearing the partner's Staggered grants `+8`, and one setup-to-different-partner follow-through grants `+12` once per round. The setup must apply an ally-tagged stage, cleanse, or Guiding Draft to the conscious partner; that same different actor must then commit a damage-tagged move in the same round. Invalid/no-op/missed/duplicate resolution and self-support grant nothing. Complementary action tags are a 32-bit mask; `(round, setup action, partner)` is consumed to prevent multi-target duplication. Tutorial Gate 4 must demonstrate partner support and partner follow-through and honestly reach at least 70 through these awards before its calibration event may set 100; golden tests cover both the primary and alternate legal input paths. The duo finisher is one linked command requiring both active allies alive, conscious, able to act, the specified creature pair, and 100 Resonance, plus its legal target set. It replaces both allied commands for that round and consumes exactly 100 only when the linked action commits. If all targets are gone, battle end wins first. If a partner becomes invalid first, preserve 100, clear the linked command, leave both surviving/uncommitted allies unacted, return only those allies to legal command selection, and rebuild the unexecuted suffix; committed actors never gain a second action. The presenter has one bespoke, bounded camera/animation/VFX sequence and acknowledges completion exactly once.

The fixed battle event queue holds 64 entries. Generation is transactional per action, the producer validates the complete worst-case finisher/status/dual-target/dual-KO burst before enqueue, and unread events are never overwritten or dropped. A capacity proof and high-water assertion are certification requirements.

Tutorial guidance is a constraint layer over this machine. It tracks lesson bits, chooses safe scripted opponents, explains legal alternatives, and adapts prompts/HP pressure until the required concepts occur. It does not maintain a parallel fake damage system. An impossible or losing tutorial rebuilds the simulation from its immutable encounter seed and does not mutate persistent progress.

### 11.1 Victory, defeat, and retry

After the confrontation and immediately before the estate battle, `GameProgress` creates the typed immutable `PRE_RUSK_BATTLE_SNAPSHOT` in memory only. No new EEPROM autosave is requested; durable reboot resume remains `CHECKPOINT_ESTATE_ARRIVAL`, which replays the confrontation. Battle-start state is never persisted as a half-applied transition. Victory applies battle-clear, reward claim, +25 Sync each, Team Link 1, battle history, and the post-battle dialogue start while preserving exact post-battle HP. Only `RUSK_POST_005` dismissal executes the typed heal/door list: it restores both starters in scratch progress, reserves the world callback, publishes HP, then starts door animation. Callback completion opens the world coherently and requests `CHECKPOINT_RUSK_VICTORY`, which remains illegal until full HP, reward facts, door pose/collision/nav, and story facts all agree.

Defeat offers Retry or Return to Annex through a separate `DefeatFlowOwner` created only after battle generation teardown. Its result token carries runtime, defeat-flow, menu, and input-event generations; one accepted edge moves the owner to HANDOFF_PENDING and cannot replay. Retry restores/rebinds the immutable snapshot, advances runtime generation, commits the battle-retry transition, and acquires `RUSK_RETRY_IMMEDIATE_001`; its dismissal starts a fresh encounter generation and grants nothing. Return restores in the typed post recipe, transitions to the Annex threshold, preserves Estate-arrived/Rusk-confrontation-seen/Find-Tavi progress while leaving every Rusk win/reward/door fact false, then enqueues exact `CHECKPOINT_RUSK_RETURN_TO_ANNEX`, `BATTLE_RESULT_RETURN_TO_ANNEX`, `last_encounter_id=ENCOUNTER_RUSK_COURTYARD`, and the threshold tuple as both current/last-safe. Reboot resumes there.

After the Retry dialogue handoff is acquired, or after Return destination/progress and immutable save enqueue succeed, a no-fail finalizer zeroes the result token, empties/advances DefeatFlowOwner, and only then releases the continuation. If a prior step fails, rollback reconstructs the overlay rather than reloading a scene, advances menu generation and input-event epoch, clears accepted input/latches, mints a new token, and discards one poll frame. Thus old menu presses cannot act on the new dialogue/scene. Duplicate result events remain rejected by generation/action sequence and reward-claim facts.

## 12. Opening slate and future FMV contract

The current opening uses a realtime UI-shell scene at the exact cinematic playback point. Its complete timeline is 106 presentation ticks: 8-tick fade-in, exactly 90 fully visible ticks (3.0 seconds), then 8-tick fade-out, safely below five seconds. It displays `INSERT CUTSCENE HERE`; A/Start during any of the 106 ticks, including fade-in, full hold, and fade-out, shuts the slate down safely and proceeds immediately after input-edge reset. The finalizer reason is diagnostic only; natural fade-out completion, accepted skip, and future playback end call the same idempotent finalizer:

```c
typedef enum OpeningCinematicFinishReason {
    OPENING_FINISH_NATURAL = 1,
    OPENING_FINISH_SKIP = 2,
    OPENING_FINISH_PLAYBACK_END = 3
} OpeningCinematicFinishReason;

opening_cinematic_finish(OpeningCinematicFinishReason reason);
```

The finalizer may run once per new-game opening generation. It sets the flag only in the uninitialized runtime draft, clears input edges, and transitions to name entry; it never requests or writes a save. Name confirmation freezes the validated draft and requests the simulation tuple, but still does not initialize/write. After `SCENE_SIM_ARENA / ZONE_SIM_ARENA / SPAWN_SIM_INTRO` has staged coherently, Name-to-Sim requires a quiescent SaveService, reserves the sole active slot, rereads/assigns the planned journal address, and only then publishes both LocationKeys and `CHECKPOINT_AFTER_NAME`; this is the first persistence attempt for `opening_cinematic_seen`, `player_name_confirmed`, name, and the Title profile settings copied into the draft. Simulation staging or page-identity conflict returns to Name Entry or Title, respectively, without a half-published campaign. Write/verify failure after coherent publish offers immutable Retry or explicit Return-to-Title abort; continuing before the first campaign page verifies is illegal. Cancel/back before confirmation returns to title with no initialized page. All Title settings remain process-profile-only; neither an empty journal nor a selected verified page grants Title a campaign owner or persistence authority.

The future 60-90 second video replacement reserves:

- video: `rom:/cinematic/opening_solace.video`
- paired audio: `rom:/audio/cinematic/opening_solace.audio`
- timeline/metadata: `rom:/data/cutscene/opening_solace.cut`
- logical ID: `CUTSCENE_OPENING_SOLACE`

The `.video` and `.audio` logical payloads carry manifest-declared formats chosen and benchmarked during future user-supplied video integration; this contract does not prematurely select a codec. Gate 9 remains a media-free storyboard/handoff gate. Playback is pumped before normal framebuffer acquisition and owns audio routing while active. It reuses the configured display rather than opening another display or allocating hidden framebuffers. The exact callback symbol is `opening_cinematic_finish`. Watch, A/Start skip, end-of-stream, missing video, missing audio, decode error, and repeated entry all converge on it; missing/failed media falls back to the approved slate and records telemetry. The state handoff and flag behavior therefore do not change when the user supplies the final video.

Timestamped `CutsceneEvent` data is also used for realtime dialogue/camera staging. Events are sorted by tick and source index, and skip fast-forwards through only events marked `APPLY_ON_SKIP` before calling one finalizer. This prevents half-applied story flags or audio/camera ownership leaks.

## 13. Audio architecture

The mixer runs at an N64-appropriate measured configuration, initially 22,050 Hz, with fixed channel roles for music, ambience, UI, creature vocals, movement, and battle effects. Runtime SFX are converted to mono WAV64 unless a reviewed stereo exception fits the budget. Music format is selected during the benchmark from measured libdragon-supported streaming/module options; sources remain lossless and runtime format is recorded in the manifest.

`AudioDirector` accepts logical cues, not filenames. It owns one music state and cross-scene fade policy; scene scopes own ambient loops and loaded SFX banks. Battle simulation emits semantic events, and the presenter schedules animation/VFX/audio from the same action sequence. A missing optional SFX logs and continues silently; missing required music fails asset validation before ROM build. Scene exit fades/stops channels, waits for callback ownership to clear, then releases handles. No callback retains a scene pointer.

Audio allocation is capped. The SFX cache uses manifest sizes and least-recently-used eviction only between actions; assets referenced by queued presentation events are pinned. Audio underruns, rejected cues, peak voices, and cache high-water are telemetry fields.

## 14. Save service

EEPROM is treated as 64 addressable 8-byte blocks. The 512-byte layout is a 32-byte global header followed by two independent 240-byte journal pages. Full offsets, CRCs, and the 216-byte payload are defined in `DATA_SCHEMAS.md`.

Writes are copy-on-write through the fixed two-slot SaveService:

1. Before its producer publishes story, transition, settings, or owner-close state, reserve ACTIVE or SUCCESSOR, field-copy a stable `GameProgressSnapshot`, and encode all 216 canonical payload bytes with explicit byte writers. The request stores those bytes and their CRC but no target page or sequence yet.
2. When the request becomes the sole-writer head, reread and validate both complete pages, apply unsigned journal ordering, and atomically assign a fresh address generation, anchor page/sequence, the opposite target page (page A when no envelope is valid), and exact next sequence. A successor never projects its predecessor's target. First New Game additionally CRC-prechecks and byte-compares both entire 240-byte pages against its confirmation-time plan before initialized progress can publish.
3. Clear the assigned destination footer commit marker; the selected anchor remains untouched.
4. Write and reread the header/payload in aligned blocks under a measured per-frame budget.
5. Verify header and payload CRC from EEPROM bytes.
6. Write the final 8-byte footer containing payload CRC and `COMT` as the commit operation.
7. Reread/validate the complete page, then update the global active-page hint best-effort.

Boot validates both pages independently and selects the newest sequence with portable unsigned arithmetic: `delta=a-b`; equality is zero, exact half-range is ambiguous, A is newer only for `0<delta<0x80000000u`, otherwise B is newer. Header corruption does not prevent page recovery. Unknown newer payload versions are preserved and reported incompatible; known older versions pass a field-by-field migrator. Invalid or incompatible progression is never accepted, guessed, or automatically overwritten: both raw pages remain intact and the title offers New Game with a diagnostic prompt. An ordinary write anchors on the newest envelope-valid page, writes the other page at `anchor+1` modulo `2^32`, and starts at sequence 1 when neither envelope is valid. Confirmed New Game also treats unsupported envelopes as anchors and follows its exact raw-page plan; equal-divergent/half-range pairs remain unusable until explicit overwrite confirmation establishes the deterministic plan. The anchor remains untouched through footer-last commit and reread verification.

Settings recovery is separate from progression acceptance but follows one freshness order. Boot completes two-page progression selection first. A selected supported semantically valid page's sanitized eight settings bytes seed `SettingsProfileOwner` and outrank every `GS` capsule. Only when no supported page is selected may a CRC-valid global-header `GS` capsule seed the profile; if it is absent/invalid, one unambiguously newest envelope-valid page with a known payload layout may expose those bytes, while unknown or ambiguous candidates are never guessed and fall back to defaults. Salvage does not make a page valid, expose Continue, initialize progress, or write EEPROM. Title Apply advances only the process profile. Pause Settings publishes runtime candidate bytes but updates the process profile only after a current campaign/seed/settings-generation-matched `SAVE_REASON_SETTINGS` commit; failure leaves the profile untouched and Cancel restores runtime only. The service updates `GS` best-effort only after a campaign-matched current reconciliation whose reread page is unambiguously newest, so late historical commits cannot poison future recovery. A later New Game persists the profile through the ordinary first checkpoint after coherent simulation entry. Native structures and pointers are never written.

Save-producing input is debounced before it becomes a transaction, but admitted requests are never coalesced, displaced, or silently dropped. The queue holds exactly one active writer and one immutable successor. Every live producer is either mandatory owner-blocking or an explicit user request. Mandatory producers reserve before no-fail publish and retain their origin until terminal resolution; a full queue returns typed BUSY_RETRY without publishing progress. Manual Relay and Pause Settings retain their scratch UI while `UI_SAVING` co-renders, then retry admission when a slot releases. Name-to-Sim is the sole active-and-fully-quiescent producer and can never wait as successor. A failed/retrying head retains its address and blocks successor promotion until `COMMITTED`, `CANCELED`, `CONTINUED_DIRTY`, `TRAVELED_UNSAVED`, or `ABORTED_TO_TITLE` releases it.

Every encoded `current_location` and `last_safe_location` must resolve to a condition-valid `SaveableLocationDef`; checkpoint-only anchors live in that registry even when no `TransitionDef` targets them. Ordinary door/world transitions may retain the latest checkpoint ID and save a stable registry destination/source-safe tuple. No save request is legal between New Game acceptance and coherent simulation entry after confirmed name; confirmation alone is still draft state. A transition request may capture a snapshot, but `current_scene` changes only during COMMIT after successful `enter`. Writes cannot observe a battle midway through rewards or a story action halfway through its opcode list.

The first After-Name recipe is the sole zero-to-initialized constructor. It field-copies only the validated draft name/playtime/seed/settings/opening bit, writes both active party indices to `0xFF` explicitly, and validates `party_count==0 iff left==right==0xFF`; zero-filled `0/0/0` is invalid. Starter grant later atomically publishes the exact `2/0/1` active tuple with its two PartySlots. Optional dialogue/help/examine/NPC once bits are ordinary encoded fields; the Sera-depart deferred bit is committed in the same first-departure recipe, while Sera's post-defeat retention recipe replaces only the current stable save page semantics plus that one-shot mutation.

Every playable runtime has one process-only campaign owner. Title itself has none. A verified Title Continue mints a fresh nonzero campaign generation, mirrors the decoded nonzero seed, sets final outcome to SAVED only for a semantically complete Slice page (otherwise PENDING), requires the `RuntimeDraftOwner` to be entirely zero, and overlays the sanitized Title profile after decode. It starts CLEAN only when all eight profile bytes equal the decoded settings; any difference starts the runtime DIRTY while leaving the decoded SaveReason unchanged. New Game transfers its already-minted draft generation/seed rather than allocating a second identity, with the Title profile already copied into that draft. Its first verified `COMMITTED` result records the consuming request, moves overwrite authority to CONSUMED, and zeroes all 580 draft bytes. Every clean Return-to-Title, confirmed dirty-loss Return, rollback-fatal Return, and New Game abort fences SaveService requests/callbacks and invalidates the campaign owner before Title may mint another. Reconciliation and late callbacks must match both campaign generation and campaign seed, so an old campaign can at most leave a historical valid page on EEPROM; it cannot mutate the current runtime, outcome, dirty state, or UI.

The page stores one exact `last_save_reason`: milestone autosaves use `CHECKPOINT`; ordinary stable transition autosaves use `TRANSITION`; player Relay saves use `MANUAL_RELAY`; only Pause Settings Apply uses `SETTINGS`; Rusk victory/Return use `BATTLE_RESULT`; and the committed closing hook uses `FINAL_HOOK`. Initialized pages may not use NONE. Manual Relay requires the unlocked player-owned Relay save surface and all page bits. Pause Settings is the only settings UI permitted to create a SaveRequest: it requires an initialized campaign, stable control, and a condition-valid current `SAVELOC_CONTINUE_ALLOWED` tuple. Exploration additionally requires `SAVELOC_MANUAL_ALLOWED`; simulation admits only `SAVELOC_SIM_INTRO` at a tutorial pause-safe command boundary and saves settings against the restart-at-intro checkpoint without serializing partial battle state. Title Settings changes only the process profile; a later New Game first checkpoint or a Continue runtime's Pause/Manual/transition save may persist those bytes honestly. Decode validates persisted semantics, not historical UI origin. Later manual/transition/settings saves may retain an older checkpoint ID without pretending to be that checkpoint operation.

If the final-hook write succeeds, end-card Continue loads the verified post-chapter registry tuple. If retries fail and the player explicitly chooses Continue Unsaved, the end card retains coherent dirty in-memory `GameProgress`: Continue Exploring re-enters that same post-chapter tuple without reading or updating EEPROM and keeps the dirty marker for a later manual retry. Return-to-Title in that branch requires the separate discard warning, then destroys dirty runtime; Title Continue can load only the older verified page. If dirty Continue first returns to Annex, Pause Return-to-Title still requires a fresh process-owned unsaved-loss acknowledgement before it can select the dirty teardown row; the clean stable-gameplay row requires dirty=false.

Final outcome and current-runtime cleanliness are separate axes. A verified semantically complete Slice page—whether written by Final Hook or a later legal Manual/Settings/Transition request—sets `FINAL_SAVE_OUTCOME_SAVED`; SaveReason remains operation provenance. Verified success clears runtime dirty only when campaign generation/seed match, the captured semantic runtime generation equals the live generation, and a fresh canonical encode is byte-identical to all 216 immutable request bytes after only the four playtime bytes are normalized to the captured value; live playtime must not regress. CRC is a precheck, never the equality authority. A late asynchronous success may secure the opening record while leaving newer runtime dirty. The only postchapter pairs are SAVED+CLEAN, SAVED+DIRTY, and CONTINUE_UNSAVED+DIRTY; the last upgrades atomically on a later current complete-page save, and CONTINUE_UNSAVED+CLEAN is invalid. Oren's secure-record copy selects SAVED regardless dirty, while the unsaved copy selects only CONTINUE_UNSAVED+DIRTY.

The initial final-save resolver has two literal continuation rows: verified SAVED requires clean runtime at that immediate end-card handoff, and explicit CONTINUE_UNSAVED requires dirty runtime. Both require the committed Slice milestone/current generation and request the same `TRANS_DEF_HOOK_TO_END_CARD`; PENDING has no row. Retry reuses the immutable snapshot without transitioning. The dirty branch never sets clean or reports EEPROM success. Later postchapter SAVED+DIRTY is handled by ordinary exploration/save routing, not by replaying the end-card continuation.

The page shown on failure is selected by the typed save policy, not a generic error callback. Final Hook hands its immutable Slice snapshot to the sole binary `UI_SAVE_FAILED` binding. PRE_SOURCE transition failure owns Retry, Travel Unsaved, and Cancel before any publish; post-enter/story progress and retention failures own Retry/Continue Dirty after coherent publish; manual/settings failure owns Retry/Cancel; first-New-Game write/verify failure owns immutable Retry/Return-to-Title only. Each nonfinal policy renders its own exact process-static prompt and never acquires the final node or borrows another policy's StringId. Address conflict before New Game publish bypasses generic Retry, releases request/draft through the no-publish unwind, returns to Title, reruns the two-page loader, and requires fresh confirmation. Every button action is generation-bound to the exact immutable snapshot/owner, and controller loss or policy re-entry clears its prior edge.

## 15. Telemetry and debug evidence

Debug builds maintain a fixed-capacity event ring and frame-metrics ring; release builds retain low-cost frame, heap-low-water, transition, and fatal error counters. The overlay can show:

- CPU frame time, fixed steps, dropped ticks, and 33.33 ms misses;
- RSP/RDP fence age and frame-context generation;
- total free heap, largest block, arena used/high-water, and resource bytes by scope/type;
- active models, skeletons, animations, sprites, display lists, audio streams, and SFX voices;
- scene ID, transition phase/token, spawn, objective, and story flag trace;
- battle seed, phase, round, actor/command IDs, Resonance, and presentation wait;
- save page validity, sequence, pending reason, blocks written, and last error;
- collision corrections, out-of-bounds recoveries, follower relocations, and reconnect events.

The timing harness marks the busiest Annex, estate, and battle camera views and records a frame-time histogram. The transition harness performs the required twenty loops after one warm-up cycle and emits machine-readable CSV/JSON through the emulator debug channel or a captured log. Claims in certification cite the ROM hash and build manifest that produced the evidence.

## 16. Test seams and verification plan

Platform calls sit behind narrow function tables for host tests:

- `StorageBackend`: read/write 8-byte EEPROM blocks with power-loss and corruption fault injection.
- `ClockSource`: deterministic ticks and simulated stalls.
- `InputSource`: scripted controller state and disconnect/reconnect sequences.
- `AssetBackend`: manifest bytes, CRC/type/size failures, and allocation failures.
- `AudioSink`/`PresentationSink`: record semantic cues and acknowledgements without rendering.
- `DebugSink`: captures assertions, metrics, transition traces, and save diagnostics.

Host suites cover byte-exact save golden vectors, every truncation/corruption case, page sequence wrap, migration, independent settings salvage, battle ordering/targets/damage/status/AI/Resonance, tutorial alternate inputs, reward idempotence, story condition/action traces, dialogue skip, and transition legality. Input bridge goldens exercise zero/one/two fixed steps, UI-consumed versus simulation-owned edges, quick press/release, queue overflow, disconnect flush, port transfer, and the reconnect discard poll; no edge may vanish or replay. Save/location goldens cover every checkpoint-only and transition-save registry tuple, each SaveReason matrix row, active/successor/BUSY admission, failed-head terminal outcomes, address-conflict versus addressed Retry, New Game raw-page drift/abort/consume, campaign load/mint/invalidate, late callbacks, normalized 216-byte equality, dirty-versus-saved end-card navigation, and rejection of map/battle/end-card tuples. Transition goldens prove exact phases through `ROLLBACK_SOURCE`/`ROLLBACK_FATAL`, disjoint first-arrival/reselect/follower/map-origin-cancel conditions, process navigation, and that the simulation-to-Annex retain path accepts only an identical AssetId/CRC/size base, atomically retags it, invalidates all overlay handles, and retains no other source allocation; any mismatch takes the normal unload/load path. Held-interaction goldens require 45 fixed ticks and test release, disconnect, range exit, external takeover, coherent commit, and save exclusion. Battle goldens include the five exact damage vectors above plus Staggered-before-pending-action reorder, Staggered-after-acted next-round behavior, KO clearing, cleanse clearing, retry clearing, 64-event worst-case high water, and queue-overflow assertion. Property tests generate legal battle states and assert no illegal command or dead target survives validation.

Target tests add the renderer, RSP lifetime, controller hardware API, asset conversion, audio streaming, timing, and memory. Ares scripts/capture check cold boot, both slate paths, all rooms, battle victory/defeat/retry, save/reboot, map round trips, follower recovery, disconnects, invalid EEPROM, completed-objective revisits, closing hook, the twenty-loop soak, and three timed playthroughs.

## 17. Build and CI interface

Gate 3 must implement these stable entry points (names may be shell wrappers but behavior is fixed):

| Entry point | Required result |
|---|---|
| `scripts/bootstrap-check` | Report host architecture, Docker, pinned image, disk space, LFS objects, and required GUI tool versions without mutating the repo |
| `scripts/validate-data` | Parse singular dialogue/condition sources, generate topologically ordered `schema_all.h/.c`, compile canonical host/N64 aggregate units with warnings as errors, and emit ID/layout/table/hash coverage |
| `scripts/validate-assets` | Validate ledger coverage, sources, names, dimensions, animation sets, material rules, collision, packed/unpacked/arena caps, every legal zone composite, full-ROM budget, placeholder markers, and generated manifest |
| `scripts/build-rom` | Clean reproducible build through the pinned container; output ROM and reports only under `build/` |
| `scripts/test-host` | Compile/run deterministic gameplay, story, and save suites on the host/CI |
| `scripts/run-ares` | Launch the selected ROM in Ares 148 Homebrew Mode after validating ROM hash/path |
| `scripts/make-checksums` | Emit SHA-256 plus ROM header, byte size, linker map summary, dependency pins, and source commit |

The Makefile/build graph must expose `clean`, `assets`, `test`, `rom`, `validate`, and `report` targets and use the same commands locally and in CI. CI starts from a fresh public checkout with LFS, checks dependency pins, runs host tests and asset validation, builds the ROM, confirms N64 header/size, scans the map and ROM budget, and uploads `.z64`, `.sha256`, map/size report, dependency/build manifest, and validation summary. The ROM is an artifact, never normal Git history.

Every artifact report includes the Git commit, dirty-tree status (CI must be clean), libdragon/Tiny3D/CLI/container pins, converter versions, asset-manifest hash, ROM size, ROM SHA-256, and test summary. A tag/version mismatch fails release validation.

## 18. Failure-mode policy

| Failure | Required behavior |
|---|---|
| Missing/CRC-failed required destination asset | Abort destination staging, release partial scope, normally reload recorded source unchanged, show `Travel could not be completed.`, and allow retry; safe menu only if rollback reload also fails |
| Missing optional portrait/SFX | Use reviewed fallback or silence, log once; never dereference null |
| Scene/action arena overflow or heap floor breach | Reject load/action before commit in debug/certification; emit category/high-water evidence |
| Invalid transition/spawn | Reject request, retain control in current stable scene, show debug fault; production data validation must prevent shipment |
| RSP-visible resource still in flight | Wait at the explicit fence; never free or mutate it |
| Controller disconnect | Freeze gameplay/name entry and show reconnect modal; slate presentation timer may finish; clear latches and discard edge inputs on recovery |
| Both EEPROM pages invalid | Salvage only independently validated/clamped settings when readable, offer New Game, preserve raw pages and diagnostics, never expose invalid progress or auto-wipe |
| EEPROM write interruption | Previous page remains valid; incomplete page lacks the commit marker |
| Unsupported save version | Preserve and report incompatible; do not reinterpret or erase |
| Battle target invalidated | Deterministically retarget if rules allow, otherwise no-op and reevaluate battle end |
| Duplicate battle/story result | Reject by action sequence and one-time claim bits |
| Follower stuck/separated | Recover at an off-camera validated anchor and log; never block the player |
| Cutscene media absent/decoder error | Fall back to approved slate; apply the same finalizer and story flag |
| Audio stream underrun | Continue gameplay, log the underrun, lower measured cache/stream pressure before release |
| Camera collision cannot solve | Use last safe camera or authored room fallback, never place the eye outside the room indefinitely |
| Out-of-bounds player | Restore the latest room safe anchor and log a certification failure |
| Presentation completion lost | Debug watchdog identifies action ID; certification fails rather than silently mutating battle state |

No fallback may convert a required production asset into a final placeholder. Fallbacks exist to preserve state, produce diagnostics, and prevent crashes during development; release validation rejects any activation on a required path.

## 19. Gate evidence this architecture requires

This contract advances only when evidence replaces its assumptions:

- Gate 3: exact pins build together locally and in clean CI; minimal ROM boots in Ares 148.
- Gate 4: representative humanoid, Echoform, room corner, UI, battle animation, VFX, collision, and audio establish real per-category memory/performance numbers.
- Gates 5-6: full state flow, deterministic battles, save/retry, map/follower/dialogue edge cases, and timing instrumentation pass with tracked temporary assets.
- Gates 7-8: every production resource enters through the registry/manifest and passes visual plus in-engine review without violating budgets.
- Gate 9: media-free storyboard delivery and animation handoff conform to the reserved playback/finalizer contract; codec profiling happens only during future user-supplied video integration.
- Gate 10: 30 FPS evidence, 512 KiB free floor, ROM target, transition soak, clean builds, corrupt-save tests, and three timed runs pass on the same hashed ROM.

Any implementation discovery that invalidates an interface here must update this document and its tests before content code works around it.
