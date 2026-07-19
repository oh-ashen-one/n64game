# Story, Script, and Timing Contract

Status: Gate 2 preproduction lock

Authority: subordinate only to `docs/N64GAME_MASTER_SPEC.md` and later explicit user changes

Timing basis: first-time play from cold boot through the closing hook's stable interactive end-card handoff, excluding idle time

This document is the implementation-ready narrative contract for the complete opening chapter. It fixes the original story, scene order, encounter fiction, dialogue, objectives, progression flags, failure behavior, and pacing evidence. It does not authorize copying any protected reference expression. A scene may be restaged to solve a measured camera, memory, or navigation problem, but no required beat, destination, battle, or outcome may be removed without updating the master specification.

## 1. Experience and pacing lock

The median target is **22 minutes 30 seconds**. Run three qualifying first-playthrough-style certifications, excluding idle time from each. The median of their three total durations must be 18–25 minutes. Every one of the three qualifying runs must independently record at least 15 minutes of active-control time; active-control compliance is never evaluated by median. For this contract, the closing hook ends on the first frame that the authored end card has resolved its save outcome and its stable choices accept input; the post-`HOOK_014` fade, record feedback, and end-card reveal are therefore part of the measured hook handoff rather than unmeasured post-roll. Active control means movement, exploration, interaction choice, name entry, party/Field Relay use, world-map choice, battle command/target selection, or retry/end-card choice. Merely advancing mandatory dialogue does not count. The design must not stall the player or inflate text to hit time.

| Clock target | Segment | Required content | Active-control budget |
|---|---|---|---:|
| 0:00–0:11 | Boot/title | Game mark, real initialization, first-run New Game selection | 0:05 |
| 0:11–0:15 | Opening slot | 106-frame slate: 8-frame fade, 90-frame fully visible `INSERT CUTSCENE HERE` hold, 8-frame fade; or immediate skip | 0:00 |
| 0:15–0:45 | Name entry | 1–8 uppercase characters, default `ARI`, protected confirm/cancel | 0:30 |
| 0:45–4:40 | Simulation | Fly-in and complete interactive 2v2 tutorial | 3:10 |
| 4:40–10:35 | Meridian Annex | Starter onboarding, assignment, two-level exploration, Field Relay, Tavi clue, exit | 4:20 |
| 10:35–11:20 | World map/travel | Estate selection, travel animation, real loading | 0:35 |
| 11:20–13:15 | Estate courtyard | Arrival exploration, Rusk confrontation | 1:20 |
| 13:15–16:10 | Rusk battle | Complete real 2v2 battle, result/progression | 2:30 |
| 16:10–19:35 | Estate interior | Apology, invention exploration, Ivo/Tavi reunion, follower return | 2:00 |
| 19:35–22:15 | Annex return/hook | Map return, objective resolution, Solace beacon, Fracture response | 0:55 |
| 22:15–22:30 | End state | Save confirmation, chapter card, stable choice | 0:10 |
|  | **Target total** |  | **15:35** |

The controlled-time budget includes interactive menu/UI reading and decision time, but it excludes advancing or merely reading mandatory dialogue and includes no optional detour longer than 45 seconds. Mandatory paths must remain direct. Optional interactions can add roughly 2–4 minutes for curious players without being required to reach the 18-minute floor. Certification runners receive no route instructions beyond the on-screen game.

Clock entries are authored arrival targets with a ±15-second tolerance at each boundary, not timers. The game never waits for a boundary before allowing progress.

## 2. Original story premise and clean-room boundary

The Meridian researchers study Resonance: the measurable cooperative pattern formed between people and Echoforms. Their carrier, **Solace**, vanished while transporting a remote-sensing array. The opening slot will eventually show **the Severance** intercepting Solace over the desert, using glider craft and a colossal Fractured Echoform to bend light and gravity. One emergency beacon falls free.

The player is a young Meridian field trainee completing a supervised simulation at the **Meridian Research Annex**. A harmless calibration errand becomes personal when Tavi takes a locator tag beyond the Annex to the eccentric **Veyra Observatory Estate**. Retrieving the new **Field Relay** exposes Tavi's queued message and unlocks the estate. Rusk mistakes the player's Solace-band Relay signal for a Severance scout, forcing the first real battle. The player finds Tavi safe with Ivo, returns home, and closes the personal objective. Ivo's observatory packet then reveals that Solace's emergency beacon is moving—and that an enormous Fractured signature is answering it.

This story uses only the high-level pacing grammar approved by the master. It may not reproduce Pokémon names, creature biology, character archetype expression, dialogue, gags, locations, shots, UI, terminology, music, moves, or map composition. It may not use Pandemonium code or content. All words below are original project writing.

Core themes:

- **Connection versus control:** Resonance is cooperation; Fracture is a forced severing and distortion of that relationship.
- **Competence before destiny:** the player earns trust by training, navigating, and bringing Tavi home rather than being declared a chosen hero.
- **Curiosity with consequences:** Tavi and Ivo are not foolish; their curiosity finds a real signal, but leaving without telling anyone creates risk.
- **Warm home, strange horizon:** the Annex is busy and protective, the Estate is whimsical and independent, and the closing signal makes the desert suddenly feel vast.

## 3. Canonical vocabulary, cast, and factions

### 3.1 Cast

| ID | Display name | Function and performance rule |
|---|---|---|
| `player` | entered name, default `ARI` | Silent customizable protagonist. Never voiced, gendered, or assigned dialogue. Other characters use `{PLAYER}`. Clear head turns, nods, hand signals, and battle-command poses carry responses. |
| `npc_tavi` | Tavi | Younger companion and practical tinkerer. Curious, quick, and accountable; never babyish, helpless, or a walking joke. |
| `npc_sera_venn` | Dr. Sera Venn | Research guardian and tutorial voice. Warm, exact, dryly funny. She corrects without belittling and prioritizes safety. |
| `npc_oren_saye` | Director Oren Saye | Annex director. Economical, calm, and responsible. His authority comes from clear decisions, not exposition speeches. |
| `npc_ivo_veyra` | Ivo Veyra | Observatory inventor. Eccentric because he follows unusual measurements, not because he is incompetent. Speaks in concrete images. |
| `npc_rusk` | Rusk | Estate assistant and opponent. Earnest, vigilant, physically expressive, and mortified when wrong. He is never copied from a reference comic-relief character. |
| `npc_mara_ovelle` | Mara Ovelle | Annex clinic technician. Gentle, observant, cares for the real starter pair. |
| `npc_jo_renn` | Jo Renn | Workshop machinist and Field Relay custodian. Blunt, amused, proud of durable tools. |
| `npc_pell_anwar` | Pell Anwar | Comms/cartography analyst. Reads the queued locator packet and unlocks the map node. Precise under pressure. |

### 3.2 Factions and institutions

| ID | Name | Story function |
|---|---|---|
| `faction_meridian` | Meridian Research Network | Civilian desert observatories and clinics studying Echoforms and safe Resonance. The Annex is one field outpost. |
| `faction_veyra` | Veyra Observatory Estate | Ivo's independent observatory, workshop, and archive. Friendly to Meridian but technologically idiosyncratic. |
| `faction_severance` | the Severance | Hostile network that restrains Echoforms and disrupts Resonance. Only its name, interception methods, and cut-wave signature are established here. No leader or motive is explained in the opening chapter. |
| `carrier_solace` | Solace | Meridian research carrier missing above the desert. Its emergency beacon drives the closing hook. |

### 3.3 Locations and room IDs

`SCENE_ANNEX_INTERIOR` is one destination with streamed/owned room groups:

- `ANNEX_SIM_CHAMBER`: physical simulation platform and observation glass.
- `ANNEX_ATRIUM_L1`: navigation hub with split stair/elevator sightline and Resonance monitor.
- `ANNEX_CLINIC_L1`: creature bay and starter onboarding side entrance.
- `ANNEX_WORKSHOP_L1`: Jo's bench, Field Relay dock, tools, antenna parts.
- `ANNEX_EXTERIOR`: shaded threshold, map terminal, sand-skimmer departure point.
- `ANNEX_DIRECTOR_LAB_L2`: Oren's office, Solace model, mission board.
- `ANNEX_PLAYER_ROOM_L2`: save point, party tutorial, personal detail.
- `ANNEX_RELAY_BALCONY_L2`: Pell's comms/map station overlooking the atrium.
- `ANNEX_ELEVATOR`: authored elevator transition connecting both levels; never a teleport disguised as a door.

`SCENE_ESTATE_COURTYARD` contains the gate, observatory silhouette, kinetic fountain/energy apparatus, planted shade pockets, Rusk's work area, and battle staging court.

`SCENE_ESTATE_INTERIOR` contains:

- `ESTATE_FOYER`: portrait/gallery entry and coat/gear silhouettes.
- `ESTATE_INVENTION_HALL`: at least five readable kinetic devices and the main traversal room.
- `ESTATE_STUDY`: Ivo's orrery, telescope controls, packet recorder, and Tavi discovery staging.

The world map has exactly two opening-chapter destination nodes: `DEST_NODE_MERIDIAN_ANNEX` and `DEST_NODE_VEYRA_ESTATE`. These `DestinationNodeId` values are travel-menu choices, not durable save locations. It must visually imply a wider desert without presenting selectable fake destinations.

## 4. Echoforms, affinities, and encounter fiction

### 4.1 Affinity and temporary-state vocabulary

Four affinities form one readable cycle:

`CURRENT > EMBER > GALE > STRATA > CURRENT`

An advantage deals 1.5× affinity damage; the reverse relationship deals 0.75×; all other pairings are neutral. UI language is `STRONG`, `RESISTED`, or no label. The sole temporary status family in this chapter is **Staggered**: Speed is reduced by 25% through the affected actor's next completed action, then the status expires. If Staggered lands before that actor's pending command, only the unexecuted queue suffix is stably reordered; if the actor already acted, the reduction applies to its next round. Power/Guard/Speed stage changes are volatile battle modifiers, not status ailments; they expire at battle end and cannot exceed ±2.

Shared player Resonance ranges from 0–100. A successfully committed damaging move grants +6 once per action, plus +4 once if it lands at least one affinity-advantage hit. Partner-directed support grants the move-specific +10, +12, or +14 listed below. Clearing Staggered from the partner grants +8, and one tagged setup-to-partner follow-through grants +12 once per round. Invalid, cancelled, no-target, duplicated, or enemy actions grant nothing; spread moves do not multiply an award by target count. Resonance never falls from taking damage. A duo finisher requires both allied Echoforms conscious, both action slots available, and 100 Resonance. If either actor becomes invalid before execution, the command safely cancels, preserves 100 Resonance, and returns the remaining legal actor to command selection.

### 4.2 Canonical eight-Echoform roster

The display names and IDs below are locked for cross-document and asset consistency.

| ID | Name | Side/use | Affinity | Silhouette and battle identity |
|---|---|---|---|---|
| `echo_quarrune` | Quarrune | Real starter | Strata | Compact six-legged ram with layered ceramic plates and a cobalt horn lattice; durable protector and cleanser. |
| `echo_ayselor` | Ayselor | Real starter | Gale | Hovering tri-wing manta/kite with clothlike fins and an amber keel lamp; fast setup and field control. |
| `echo_kilnback` | Kilnback | Simulation loaner | Ember | Broad quadruped kiln beast with furnace ribs; direct power and team guard. |
| `echo_nacreel` | Nacreel | Simulation loaner | Current | Ribbon-bodied eel orbiting a broken halo of conductive droplets; fast support and spread pressure. |
| `echo_gyreclast` | Gyreclast | Simulation opponent | Strata | Three-legged drill crab with an off-center stone auger; guard and Stagger pressure. |
| `echo_kivarrax` | Kivarrax | Simulation opponent | Gale | Long-legged, fan-tailed desert runner; speed manipulation and sweeping attacks. |
| `echo_kovrass` | Kovrass | Rusk's team | Ember | Low jackal/badger body with brass bellows flanks; partner amplification and feints. |
| `echo_ulvorel` | Ulvorel | Rusk's team | Current | Squat amphibian with a translucent hood and pendulum throat; pressurized attacks and protection. |

### 4.3 Move and UI-copy lock

Each move entry below supplies the exact menu name, target rule, and player-facing information line. Numeric tuning may change only through measured balance review; function and teaching role stay intact.

| User | Move | Target | Power/effect | Exact info text |
|---|---|---|---|---|
| Quarrune | Ridge Ram | One opponent | 28 Strata damage | `A steady Strata charge into one foe.` |
| Quarrune | Brace Relay | Self or ally | Guard +1 for two rounds; +14 Resonance when used on ally | `Raise one ally's Guard. Builds Resonance.` |
| Quarrune | Grounding Ring | Both opponents | 14 Strata damage; removes one positive Power stage | `A grounding wave that checks both foes.` |
| Quarrune | Steady Pulse | Self or ally | Restore 12 HP and clear Staggered; once per encounter | `Restore a little HP and clear Staggered.` |
| Ayselor | Sirocco Slice | One opponent | 26 Gale damage | `A fast Gale edge against one foe.` |
| Ayselor | Lift Current | Self or ally | Speed +1 for two rounds; +14 Resonance when used on ally | `Raise one ally's Speed. Builds Resonance.` |
| Ayselor | Dazzle Wake | Both opponents | 12 Gale damage; 35% Staggered chance per target | `A bright wake that may Stagger both foes.` |
| Ayselor | Guiding Draft | Self or ally | Next damaging move gains 20% power; +12 Resonance on ally | `Guide an ally's next damaging move.` |
| Kilnback | Cinder Charge | One opponent | 32 Ember damage | `A forceful Ember rush into one foe.` |
| Kilnback | Bellows Guard | Both allies | Guard +1 for one round; +10 Resonance | `Brace both allies with furnace pressure.` |
| Kilnback | Scorch Mark | One opponent | Power −1 for two rounds | `Lower one foe's Power with a heat mark.` |
| Kilnback | Banked Flame | Self | Power +1 for two rounds | `Bank heat to strengthen later attacks.` |
| Nacreel | Arc Jet | One opponent | 29 Current damage | `A focused Current jet against one foe.` |
| Nacreel | Conductive Veil | One ally | Guard +1 for two rounds; +14 Resonance | `Shield one ally and build Resonance.` |
| Nacreel | Flow Switch | Both allies | Speed +1 for one round; +10 Resonance | `Shift the flow to hasten both allies.` |
| Nacreel | Static Ripple | Both opponents | 13 Current damage; 25% Staggered chance | `A low Current wave across both foes.` |
| Gyreclast | Auger Knuckle | One opponent | 27 Strata damage | `A turning Strata blow into one foe.` |
| Gyreclast | Dust Screen | Both opponents | Power −1 for one round | `Dust lowers both foes' Power briefly.` |
| Gyreclast | Fault Pin | One opponent | 18 Strata damage; guaranteed Staggered; two-round cooldown | `Pin one foe and leave it Staggered.` |
| Gyreclast | Carapace Brace | Self | Guard +1 for two rounds | `Brace the carapace against incoming force.` |
| Kivarrax | Crosswind Cut | One opponent | 25 Gale damage | `A crossing Gale strike against one foe.` |
| Kivarrax | Slipstream | Self or ally | Speed +1 for two rounds | `Raise one ally's Speed with a slipstream.` |
| Kivarrax | Pressure Drop | One opponent | Guard −1 for two rounds | `Lower one foe's Guard with sudden pressure.` |
| Kivarrax | Talon Sweep | Both opponents | 12 Gale damage | `Sweep a Gale edge across both foes.` |
| Kovrass | Clinker Bite | One opponent | 27 Ember damage | `A hot metal bite against one foe.` |
| Kovrass | Boiler Chorus | One ally | Power +1 for two rounds; visible priority +1 | `Raise one ally's Power before regular moves.` |
| Kovrass | Ash Mantle | Both allies | Guard +1 for one round | `Wrap both allies in a brief ash guard.` |
| Kovrass | Furnace Feint | One opponent | 17 Ember damage; guaranteed Staggered; two-round cooldown | `A false start that leaves one foe Staggered.` |
| Ulvorel | Rill Lash | One opponent | 28 Current damage | `A narrow Current lash against one foe.` |
| Ulvorel | Pressure Leap | One opponent | 26 Current damage; 34 while Power is raised | `A pressurized leap strengthened by support.` |
| Ulvorel | Cooling Shroud | Self or ally | Guard +1 for two rounds and clear Staggered | `Guard one ally and clear Staggered.` |
| Ulvorel | Undertow | Both opponents | 13 Current damage | `Pull both foes through a low Current surge.` |

Simulation finisher `Sunline Cascade`: Kilnback channels a narrow furnace beam through Nacreel's droplet halo; Nacreel refracts it into two controlled arcs. It targets both opponents, cannot miss, deals enough scripted non-random damage to finish the tutorial, consumes 100 Resonance, and has a bespoke camera/VFX/audio presentation.

Real-team finisher `Horizon Break`: Quarrune anchors its six feet and projects the cobalt horn lattice as a rising Strata ramp. Ayselor skims the ramp, catches a compressed Gale front, and dives through both targets in a single horizon-shaped light cut. It targets both opponents, uses normal tuned damage rather than a forced kill, consumes 100 Resonance, and is legal only while both are conscious.

## 5. Global interface and script notation

Each dialogue row is one text-box page. `{PLAYER}` is replaced with the entered uppercase name. `{A}`, `{B}`, `{Z}`, `{START}`, `{STICK}`, `{L}`, `{C-UP}`, `{C-DOWN}`, `{C-LEFT}`, and `{C-RIGHT}` render as icons, not literal braces. Speaker names use the exact display names above. Echoform vocalizations are animation/audio cues, not subtitled speech. The player never receives a dialogue menu that implies a different personality or outcome; meaningful choice occurs through exploration and battle.

Text behavior:

- First `{A}` during type-on completes the current page; the next `{A}` advances.
- `{B}` does not advance mandatory dialogue and cannot dismiss a choice without resolving it.
- `{START}` opens Pause only where the scene contract permits it. It never skips story dialogue.
- Rapid confirm/cancel input is edge-triggered. One physical press cannot both finish a page and select the next prompt.
- A scene action attached to a line executes once when the page is dismissed, never when it begins typing.
- A scene may be paused for controller reconnect between pages; it resumes on the same line and cannot duplicate an attached action.

Exploration input is a finished player-facing system, not placeholder motion.
The radial stick response uses the exact Data tuning (`12/76` raw inner/outer,
smoothstep Q15); movement is camera-relative with 1.5 m/s walk, 2.75 m/s run,
hysteretic walk/run thresholds, acceleration/deceleration, solved-velocity
animation, swept capsule/step/slope/door clearance, and safe-anchor fall
recovery. The orbit camera turns at 120 degrees/s, pitches -35..+55 degrees,
defaults to 3.5 m at a 1.25 m target, collides against world and doors, and uses
the eleven exact room-volume defaults in Data. Held `{C-LEFT}`/`{C-RIGHT}` yaw
at 4 degrees per fixed tick; held `{L}`+`{C-UP}`/`{C-DOWN}` pitches at 2 degrees
per tick. Bare `{C-DOWN}` opens the unlocked Relay, while the L chord wins first
and cannot also open it; Invert X/Y swaps only its corresponding axis. Start
opens Pause from stable exploration and battle command/target selection, never
from dialogue or an executing battle presentation. These controls remain responsive
for the full active-control budget and may not be replaced by snap movement,
noclip, a static camera, or inferred room rails.

Battle Pause keeps the same visible five-entry order. During a real encounter,
Party, Field Relay, and Settings are visibly disabled, leaving only Resume and
Return to Title enabled. The simulation tutorial may additionally enable
Settings only at its generation-current command/target pause-safe boundary at
`SAVELOC_SIM_INTRO`; Party and Field Relay remain disabled while its battle
owner exists. Returning from either battle uses the ordinary clean/dirty-loss
selector, then destroys the live battle and campaign without copying battle HP
to the story party and without writing any partial battle state. Canceling a
dirty-loss warning restores the exact frozen battle Pause boundary.

Universal player-facing strings:

| ID | Exact text |
|---|---|
| `UI_INTERACT` | `{A} INTERACT` |
| `UI_EXAMINE` | `{A} EXAMINE` |
| `UI_OPEN_RELAY` | `{C-DOWN} FIELD RELAY` |
| `UI_PAUSED_DISCONNECT` | `CONTROLLER DISCONNECTED` |
| `UI_RECONNECT` | `Reconnect a controller to continue.` |
| `UI_SAVING` | `RECORDING RESONANCE...` |
| `UI_SAVE_DONE` | `RESONANCE RECORDED` |
| `UI_SAVE_FAILED` | `The record could not be written. Continue without saving?` |
| `UI_LOADING_ANNEX` | `MERIDIAN RESEARCH ANNEX` |
| `UI_LOADING_ESTATE` | `VEYRA OBSERVATORY ESTATE` |

## 6. Beat-by-beat implementation script

### 6.1 Segment A: boot, title, and opening slot

#### Boot and title

`SCENE_BOOT` performs real display, input, audio, filesystem, and save validation beneath a dark-teal field with a small animated Resonance line. It shows the original studio mark (`UI_SCREEN_STUDIO_MARK`) only while real initialization remains and must not add a fake wait. The process may emit its one AUTO edge only after a typed boot owner has the exact current nonzero generations for display/safe frame, initial edge-cleared input poll, audio mixer or final silent-safe result, verified ROM filesystem, completed journal selection, initialized sanitized settings profile, and staged/validated Title shell. The frozen token mirrors all seven generations and is revalidated/consumed once; a stale display/audio callback leaves Boot visible. Once that exact readiness completes, the process fades to `SCENE_TITLE`, where the distinct final `N64GAME` title mark and menu appear with `NEW GAME` highlighted; `CONTINUE` is disabled when no valid save exists.

If no controller port is active, Start or A may claim one only through the
platform enrollment path. The claim edge is consumed, every latch is cleared,
and one full poll is discarded before Title receives a logical context. Thus a
claiming A never also selects `NEW GAME`, and a claiming Start never opens/
skips another surface. Later controller transfer is the separate reconnect
overlay's Start-only action; A cannot transfer ownership.

| ID | Surface | Exact text | Action |
|---|---|---|---|
| `TITLE_001` | Menu | `NEW GAME` | Start a clean in-memory story state after confirmation. |
| `TITLE_002` | Menu | `CONTINUE` | Load the last stable checkpoint; disabled if no compatible record. |
| `TITLE_003` | Menu | `OPTIONS` | Open settings without changing story state. |
| `TITLE_NEW_CONFIRM` | Prompt | `Begin a new Resonance record?` | Choices `BEGIN` / `BACK`. |
| `TITLE_OVERWRITE_CONFIRM` | Prompt | `This will replace the current record.` | Choices `REPLACE` / `BACK`; replacement is not written until the first stable save. |
| `TITLE_INVALID_SAVE` | Prompt | `This Resonance record cannot be read. Begin a new record?` | Choices `NEW GAME` / `BACK`. Never crash or partially load. |

New Game preconditions: no transition active; a controller is connected; confirmation is debounced. Postconditions: runtime story state is zeroed, no durable `current_location` exists yet, settings are preserved, no old progress reward is visible, and `SCENE_OPENING_SLOT` is requested. The unsaved new-game draft carries the first eventual resume tuple `SCENE_SIM_ARENA / ZONE_SIM_ARENA / SPAWN_SIM_INTRO`; name confirmation commits that tuple in `CHECKPOINT_AFTER_NAME` only after the simulation destination is coherent.

Title `OPTIONS` always edits a sanitized process-resident settings profile, regardless of whether the journal is empty, invalid, or contains a verified initialized page. `APPLY` advances only that profile generation: Title has no campaign owner, creates no `SaveRequest`, selects no journal address, and makes no persistence claim. `CANCEL` discards the scratch copy. New Game copies the profile into its runtime draft and eventual first page. Continue first decodes the selected verified page, then overlays all eight profile bytes; the loaded runtime begins CLEAN only when all eight bytes match the decoded settings and otherwise begins DIRTY so a later Pause Settings, manual Relay, or transition save can persist them honestly. Title Options never mutates an existing page, initializes an invalid page, or enables Continue. Powering off before a campaign save loses process-profile-only changes without corrupting either journal page.

Both Title and Pause render the same typed settings editor. Its exact defaults in
save-byte order are Normal Text, no camera inversion, Music 80%, SFX 80%, Rumble
On, Overscan X/Y 0 px, Standard Contrast. Focus order is Text, Invert X, Invert
Y, Music, SFX, Rumble, Overscan X, Overscan Y, Contrast, Reset Defaults, Apply,
Cancel. Text/contrast wrap their three labels; inversion and rumble toggle;
volumes clamp by 10 and overscan by 1. Every edit previews only session scratch
(including a six-tick rumble sample), Reset refreshes all previews without
applying, Down stops at Cancel, and B is always Cancel. Cancel restores the
captured origin/focus and original preview without dirtying or saving. Pause
Apply is the only settings route that may reserve a `SAVE_REASON_SETTINGS`
request; it cannot publish changed runtime bytes until its SaveService slot is
owned, and failure Cancel restores the prior settings, reason, and dirty state.

#### Approved temporary cinematic slate

The slate occurs **after New Game confirmation and before name entry**, at the same playback point reserved for the future Solace interception. The frame is polished 4:3 final UI: dusk-ochre horizon, dark-teal carrier-line motif, violet edge pulse, centered exact copy `INSERT CUTSCENE HERE`, and small bottom-safe prompt `{A} / {START} SKIP`. At 30 Hz, natural playback is exactly 106 presentation ticks: fade in for 8 frames, remain fully visible for 90 frames (3.0 seconds), then fade out for 8 frames. `{A}` or `{START}` during any presentation phase requests immediate skip; it does not leak through to name entry. The natural slate lasts about 3.53 seconds and therefore stays below the master contract's five-second ceiling.

One idempotent finalizer, `opening_cinematic_finish(reason)`, handles `OPENING_FINISH_NATURAL`, `OPENING_FINISH_SKIP`, and future `OPENING_FINISH_PLAYBACK_END`. It releases only cutscene-local audio/stream handles and opening-slot resources after render synchronization; it never stops or restarts the continuous `MUSIC_CUE_TITLE` motif. Skip queues `AUDIO_CUE_STORY_SLATE_SKIP` exactly once without blocking the transition; Natural and Playback End queue no skip cue. The finalizer clears input edges, sets `opening_cinematic_seen = true`, and requests `SCENE_NAME_ENTRY`. Calling it twice has no effect. It does not save during transition; the flag is included in the stable checkpoint after name confirmation.

Future replacement contract, fixed only where story continuity requires it:

- format-neutral video path: `rom:/cinematic/opening_solace.video`
- format-neutral paired-audio path: `rom:/audio/cinematic/opening_solace.audio`
- timeline/metadata path: `rom:/data/cutscene/opening_solace.cut`
- callback: `opening_cinematic_finish(OPENING_FINISH_PLAYBACK_END)`
- the `.video` and `.audio` logical assets carry manifest-declared formats selected during future video integration; these stable paths do not preselect a codec or container
- skip: `{A}` or `{START}` invokes the same finalizer after safe playback shutdown
- target story runtime: 60–90 seconds, **not counted until the master explicitly replaces the temporary-slate timing rule**
- no spoken dialogue or on-screen proper noun is required; the sequence communicates through action, insignia shapes, alarms, creature performance, and the falling beacon

### 6.2 Segment B: name entry and simulation

#### Name entry

The final panel header is `FIELD CALLSIGN`. The character grid contains A–Z plus `DELETE`, `DEFAULT`, `CONFIRM`, and `BACK`. One to eight letters are valid; spaces, punctuation, blank names, control codes, and unsupported glyphs are not. The field begins with `ARI` selected so typing replaces it; moving away without typing preserves `ARI`.

| ID | Surface | Exact text | Action |
|---|---|---|---|
| `NAME_001` | Header | `FIELD CALLSIGN` | Show 1–8 character counter. |
| `NAME_002` | Help | `{A} ENTER   {B} DELETE   {START} CONFIRM` | Button icons remain CRT-safe. |
| `NAME_EMPTY` | Prompt | `Enter at least one letter.` | Return to grid. |
| `NAME_CONFIRM` | Prompt | `Use {PLAYER}?` | Choices `YES` / `EDIT`. |
| `NAME_CANCEL` | Prompt | `Return to the title?` | Choices `KEEP EDITING` / `RETURN`. Default is safe. |

Selecting the grid's `BACK` item with `{A}` is the only name-screen action that opens `NAME_CANCEL`; `{B}` remains delete and never silently exits. `KEEP EDITING` restores the prior cursor/name unchanged. `RETURN` discards only the uninitialized draft, clears confirm/cancel edges, and returns to title without creating or overwriting a record. One physical press cannot open the prompt and select a choice.

Confirm validates the entered name in the unsaved new-game draft and requests `SCENE_SIM_ARENA`; it does not write EEPROM while the destination is staging. Once the simulation scene, `ZONE_SIM_ARENA`, and `SPAWN_SIM_INTRO` are coherent, the controller requires a quiescent SaveService, reserves and address-validates the active first-campaign request, then atomically publishes that `LocationKey` and `CHECKPOINT_AFTER_NAME` containing the name and `opening_cinematic_seen`. If simulation entry fails, destroy the partial destination and return to name entry with the draft editable and no half-applied runtime. If address identity changed before publish, return to Title for a fresh loader/confirmation without writing. If the addressed EEPROM write later fails, offer immutable Retry or explicit Return to Title; continuing a campaign with no verified first page is not legal, and failure is never disguised as success.

#### Simulation staging

The arena is an authored holographic salt basin at dusk, not a featureless grid. Kilnback and Nacreel enter on the near side; Gyreclast and Kivarrax enter on the far side. A 6–8 second fly-in establishes all four combatants and returns to a stable tactical three-quarter camera. Sera speaks through an inset comms portrait. Tutorial prompts use the same production battle UI as the estate fight.

The baseline encounter starts Kilnback at 112 HP/34 Speed, Nacreel at 86 HP/63 Speed, Gyreclast at 104 HP/28 Speed, and Kivarrax at 78 HP/70 Speed. All begin at full HP with no modifiers, Stagger, cooldown, or Resonance. The enemy tutorial policy uses only legal moves named in Section 4 and a fixed seed. Gate-specific nonlethal scoring and the calibrated final damage are explicit tutorial constraints on this encounter, not a second battle implementation. The encounter ends only after both opponents are knocked out by `SUNLINE CASCADE`; ordinary early knockouts are held at 1 simulated HP until gate 5 and labeled `CALIBRATION HOLD` so the player never sees a false defeat.

Mandatory opening script:

| ID | Speaker | Exact text | One-shot action |
|---|---|---|---|
| `SIM_001` | Dr. Sera Venn | `Signal is clean. {PLAYER}, take the near pair.` | Show Kilnback/Nacreel nameplates. |
| `SIM_002` | Dr. Sera Venn | `Two partners. Two commands. Read the field before you move.` | Enter tutorial gate 1. |

Tutorial gates are constraints layered over the real deterministic battle state machine:

1. **HP, commands, and legal targets.** Before command selection, the UI spotlights all four HP panels and the player dismisses the exact HP callout below, recording `HP_CALLOUT_ACK`. Both player actors must then receive a legal command. Any damaging move and either opponent are accepted. The first target selection displays target arrows and makes illegal allies unavailable rather than failing later. The authored first round must commit at least one nonzero damage event, visibly animate the affected HP bar and number from before to after, and record `HP_DELTA_OBSERVED` before this gate completes. Opponents use low-power legal attacks and cannot knock out a loaner in this gate; the HP change teaches the system rather than padding combat.

   | ID | Speaker | Exact text |
   |---|---|---|
   | `SIM_G1_HP` | Dr. Sera Venn | `HP shows who can still act. At zero, an Echoform leaves the field.` |
   | `SIM_G1_001` | Dr. Sera Venn | `Choose a move for each partner, then choose a legal target.` |
   | `SIM_G1_INFO` | UI | `{Z} MOVE INFO   {A} SELECT   {B} BACK` |
   | `SIM_G1_DONE` | Dr. Sera Venn | `Good. The queue is built only after both commands are sound.` |

2. **Move information, order, and affinity.** The info panel opens automatically once, then requires a player close. Kilnback's Cinder Charge displays `STRONG` against Gale-affinity Kivarrax. Nacreel's Current attack displays `RESISTED` against Strata-affinity Gyreclast. The player may choose either recommended or alternate legal actions. UI shows the predicted order without exposing hidden random values.

   | ID | Speaker | Exact text |
   |---|---|---|
   | `SIM_G2_001` | Dr. Sera Venn | `Affinity changes force, not permission. Check the marks beside each target.` |
   | `SIM_G2_002` | Dr. Sera Venn | `Priority marks resolve first. Speed orders matching marks. If a target falls first, that queued move safely drops.` |
   | `SIM_EFFECT_STRONG` | UI | `STRONG — 1.5× affinity force` |
   | `SIM_EFFECT_RESIST` | UI | `RESISTED — 0.75× affinity force` |

3. **Support and temporary effects.** At least one player actor must use a support/debuff move on a legal target. The other actor retains free choice. If the player refuses, the round resolves normally and the gate repeats with no enemy damage escalation. Staggered is demonstrated by scripted-but-legal Gyreclast `Fault Pin` if its target is conscious.

   | ID | Speaker | Exact text |
   |---|---|---|
   | `SIM_G3_001` | Dr. Sera Venn | `Power is only half a pair. Use one support move this round.` |
   | `SIM_G3_002` | Dr. Sera Venn | `Staggered slows the next action, then clears. Some field moves can clear it early.` |
   | `SIM_G3_REPEAT` | Dr. Sera Venn | `Try one marked SUPPORT move. Your other command is still yours.` |

4. **Resonance and complementary play.** The meter is introduced at its honestly accumulated value. Partner support, advantage damage, and complementary setup/use are highlighted as they add the exact awards in Section 4.1. The move-information glossary also previews the `+8` partner-cleanse award for later teams; the loaners are never asked to perform a move they do not know. This gate repeats with nonlethal legal enemy guard actions until the player completes one partner-directed setup-to-follow-through sequence and the honestly accumulated meter is at least 70. The scripted training calibration may then top the meter to 100 exactly once; it may not silently fill below 70 or award an unexplained gain.

   | ID | Speaker | Exact text |
   |---|---|---|
   | `SIM_G4_001` | Dr. Sera Venn | `That shared signal is Resonance. Cooperation builds it faster than repetition.` |
   | `SIM_G4_002` | Dr. Sera Venn | `Give one partner an opening. Let the other use it.` |
   | `SIM_G4_FULL` | Dr. Sera Venn | `Pattern locked. Both partners are ready.` |

5. **Duo finisher.** `SUNLINE CASCADE` appears as a shared command only at 100. Both actors must be alive. The player may inspect or back out. If a normal command is chosen, the round resolves with opponents using nonlethal guard actions and the meter stays full; the prompt returns. Executing the finisher ends the simulation through deterministic damage and the full presentation path.

   | ID | Speaker | Exact text |
   |---|---|---|
   | `SIM_G5_001` | Dr. Sera Venn | `Full Resonance opens a duo finisher. Choose SUNLINE CASCADE.` |
   | `SIM_G5_REPEAT` | Dr. Sera Venn | `The pattern will hold. Use it when you are ready.` |
   | `SIM_FINISHER_INFO` | UI | `SUNLINE CASCADE — BOTH FOES — REQUIRES BOTH PARTNERS` |
   | `SIM_G5_DONE` | Dr. Sera Venn | `Stable, readable, and together. Simulation complete.` |

The arena freezes on a clean result card: `SIMULATION COMPLETE`, not `VICTORY`. It reports commands issued, advantage hits, support actions, and Resonance finisher—never a grade that can fail the player. The holographic basin then peels into linework, revealing the physical simulation chamber under the same camera axis.

Simulation restart contract:

- If both loaners are knocked out because of extended alternate play, if no legal action exists, or if the battle watchdog detects an impossible state, show `SIMULATION INTERRUPTED` with `RESTART` as the only story-safe action.
- Restart destroys the runtime battle, rebuilds from the exact encounter definition, resets tutorial-local gates and meter, preserves name/settings, and leaves `tutorial_complete = false`.
- No simulation HP, reward, status, or partial gate is serialized.
- Completion sets `tutorial_complete = true` exactly once in memory before the dissolve. It is first persisted in `CHECKPOINT_AFTER_TUTORIAL` only after `ANNEX_SIM_CHAMBER` is ready, the real starter transaction is valid, and `ANNEX_INTRO_005` has completed. No save may contain `tutorial_complete = true` with a half-applied starter onboarding.

### 6.3 Segment C: Meridian Research Annex

#### Simulation reveal and real team onboarding

Quarrune and Ayselor wait behind the observation glass, already visible during the dissolve. Mara opens the clinic-side gate. Quarrune steps forward and plants all six feet; Ayselor circles once above the player and settles at shoulder height. The player responds with `anm.player.ari.starter_hand_to_chest`. This is a relationship introduction, not a menu grant.

| ID | Speaker | Exact text | Action |
|---|---|---|---|
| `ANNEX_INTRO_001` | Dr. Sera Venn | `Loaned patterns behave beautifully. Real partners have opinions.` | Sera enters from observation stair. |
| `ANNEX_INTRO_002` | Mara Ovelle | `These two watched every round. They did not agree with every choice.` | Open clinic gate. |
| `ANNEX_INTRO_003` | Dr. Sera Venn | `Quarrune. Ayselor. This is {PLAYER}.` | Starter entrance performance. |
| `ANNEX_INTRO_004` | Dr. Sera Venn | `No borrowed strength now. Listen to them, and let them learn you.` | Set real party. |
| `ANNEX_INTRO_005` | Dr. Sera Venn | `Director Saye wants you upstairs. Take the atrium and use the lift.` | Set navigation objective. |

Postconditions: `annex_intro_complete = true`, `starter_team_received = true`, party is exactly Quarrune/Ayselor at full HP with zero duplicate progression, Field Relay is still locked, and free control begins. Pause order is always Resume, Party, Field Relay, Settings, Return to Title. Party is enabled now even before the Relay; selecting it captures Pause as the physical origin and opens only the production Party view. Messages, Resonance, Map, and Save remain visibly disabled, and L/R stays on Party. B restores the captured Pause focus; Pause B/Resume restores the exact frozen gameplay owner without reloading a spawn.

#### Director assignment

The route from the simulation chamber opens naturally into the atrium. The elevator is in view but the clinic/workshop/player-room routes may be explored. Oren's door has a warm task light, not a giant floating arrow.

| ID | Speaker | Exact text | Action |
|---|---|---|---|
| `OREN_001` | Director Oren Saye | `{PLAYER}. Sera says the simulation held.` | Oren turns from Solace model. |
| `OREN_002` | Director Oren Saye | `Your field pair deserves a field instrument.` | Camera includes distinct empty `prop.annex.director_relay_cradle`, never Jo's workshop dock. |
| `OREN_003` | Director Oren Saye | `Jo finished your Field Relay. Collect it from the lower workshop.` | Start Relay objective. |
| `OREN_004` | Director Oren Saye | `It carries party records, messages, saves, and the desert map. Learn it before leaving the Annex.` | Unlock objective help only. |
| `OREN_005` | Director Oren Saye | `Tavi hid a calibration tag for its first test. The rule was: inside the Annex.` | Establish harmless errand. |
| `OREN_006` | Director Oren Saye | `Tavi is late. Retrieve the Relay; the tag will tell us whether to worry.` | End scene; no forced teleport. |

Set `field_relay_quest_started = true`; objective becomes `OBJ_RETRIEVE_FIELD_RELAY` with text `Collect the Field Relay from Jo in the lower workshop.`

#### Field Relay retrieval and Tavi clue

Jo's bench shows the finished device physically docked. The player must approach and interact; it is not awarded across a room.

| ID | Speaker | Exact text | Action |
|---|---|---|---|
| `JO_RELAY_001` | Jo Renn | `There it is. Sandproof, drop-tolerant, and almost Tavi-proof.` | Jo lifts Relay from dock. |
| `JO_RELAY_002` | Jo Renn | `Thumb the side latch. If it chirps twice, it trusts you.` | Player accepts; two-note cue. |
| `JO_RELAY_003` | Field Relay | `CALLSIGN LINKED: {PLAYER}` | Show the linked Relay UI preview; do not persist unlock yet. |
| `JO_RELAY_004` | Jo Renn | `Party on the left. Records on the right. Map stays honest about where you can go.` | Brief UI focus sweep. |
| `JO_RELAY_005` | Field Relay | `1 QUEUED CALIBRATION MESSAGE` | Queue opens only after player confirms. |
| `TAVI_MSG_001` | Tavi — recorded | `{PLAYER}! I found a better place for the tag.` | Display Tavi portrait and timestamp. |
| `TAVI_MSG_002` | Tavi — recorded | `The roof moves like a metal sky. Ivo says his stars can hear the desert.` | No destination yet. |
| `TAVI_MSG_003` | Tavi — recorded | `Come find me before Sera wins hide-and-seek by worrying.` | Packet ends with coordinate header. |
| `JO_RELAY_006` | Jo Renn | `That packet left the Annex repeater. Pell can read the route header upstairs.` | Set next step. |

`JO_RELAY_003` previews the linked party, messages, Resonance-record, save, and map surfaces inside the acquisition presentation, but the modal sequence still owns input and no persistent unlock exists yet. Dismissal of `JO_RELAY_006` atomically sets `field_relay_unlocked = true`, advances the Relay substage to `Ask Pell to trace Tavi's message.`, exposes those surfaces to player control, and completes the acquisition transaction. Once the workshop returns to stable exploration control with no dialogue action or transition pending, automatically write `CHECKPOINT_FIELD_RELAY` using that exact post-Jo state. Saving is available only in stable exploration state, not while the acquisition animation or message is active.

After that atomic unlock, Pause Field Relay and `{C-DOWN}` from stable
exploration open Party first. Exact tab order is Party, Messages, Resonance, Map,
Save; all five are rendered by the authored Relay screens and typed live views,
not debug text. Party shows player name, both active markers, creature names/
levels, current/max HP, Sync, four moves per slot, and Team Link. Messages shows
ordered message and detail-page positions, sender/title, READ/PENDING/RESOLVED
state, and graph-backed detail without acquiring DialogueController: Tavi's
three-page packet is READ, while Ivo's one-page packet appears after Tavi is
found, stays PENDING until Solace resolves, then uses `HOOK_001` as RESOLVED
detail. Resonance truthfully shows both Sync values, Team Link, and locked/
unlocked Rusk record. Map shows Annex, Estate lock state, current stable location,
and the exterior-skimmer restriction but cannot initiate travel. Save shows the
registry-resolved location, checkpoint, last reason, clean/unsaved state,
SaveService status, and Record eligibility. B returns to the exact captured
Pause focus or frozen gameplay origin; no tab change mutates story/read state.

Pell stands at `ANNEX_RELAY_BALCONY_L2`. The player may reach Pell by lift or stairs; neither route is blocked.

| ID | Speaker | Exact text | Action |
|---|---|---|---|
| `PELL_TRACE_001` | Pell Anwar | `Send me the header.` | Player docks Relay at side reader. |
| `PELL_TRACE_002` | Pell Anwar | `Veyra Observatory Estate. Western ridge.` | Map projects two real nodes. |
| `PELL_TRACE_003` | Pell Anwar | `The service crawler logged one passenger: Tavi. Arrival confirmed. No return trip.` | Establish safe arrival and missing state. |
| `SERA_RELAY_001` | Dr. Sera Venn — Relay | `Tavi is safe enough to send jokes, and far enough to come home now.` | Sera portrait appears. |
| `SERA_RELAY_002` | Dr. Sera Venn — Relay | `{PLAYER}, bring the field pair. Find Tavi; call if the route changes.` | Start main objective. |
| `PELL_TRACE_004` | Pell Anwar | `Estate node is live. The skimmer at the exterior threshold will take you.` | Unlock destination and exit guidance. |

Dismissal of `SERA_RELAY_002` atomically sets `tavi_missing_reported = true`, completes `OBJ_RETRIEVE_FIELD_RELAY`, and starts `OBJ_FIND_TAVI` with text `Travel to Veyra Observatory Estate and find Tavi.` Dismissal of `PELL_TRACE_004` then sets `estate_destination_unlocked = true` and, after the Atrium zone is again stable, commits `CHECKPOINT_ANNEX_TRACE_COMPLETE` at `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_ATRIUM / SPAWN_ANNEX_ATRIUM_TRACE_COMPLETE`. A later manual Relay save before first departure retains that semantic recipe while replacing current/last-safe only with the player's validated stable Annex tuple; `annex_exit_cleared` remains false. First confirmed departure promotes to the separate canonical `CHECKPOINT_ANNEX_DEPARTURE` threshold recipe. The Annex exit now has authored composition, map-node glow, and NPC look direction; movement remains free.

#### Required first-use UI prompts

The player must acknowledge one concise, interactive prompt for each newly relevant system. Prompts do not seize control while moving or stack over dialogue.

| ID | Exact text | Completion condition |
|---|---|---|
| `HELP_MOVE` | `{STICK} MOVE   Hold {B} RUN   {A} INTERACT` | Appears on first atrium control; dismiss after 3 seconds or any demonstrated action. |
| `HELP_CAMERA` | `{C-LEFT}/{C-RIGHT} TURN   HOLD {L}+{C-UP}/{C-DOWN} TILT` | Complete after one yaw or pitch adjustment, or explicit dismiss. Bare `{C-DOWN}` remains Field Relay. |
| `HELP_PAUSE` | `{START} PAUSE` | Complete after Pause opens once. |
| `HELP_PARTY` | `View Quarrune and Ayselor under PARTY.` | Complete after party screen opens or on exterior exit prompt. |
| `HELP_SAVE` | `Record progress from the Field Relay when the area is stable.` | Complete after successful manual save or on exterior exit prompt. |
| `HELP_MAP` | `Choose a lit destination. Dark horizon marks are not routes.` | Complete on first world-map entry. |

#### Optional Annex dialogue and examine script

These lines provide texture but never gate progression. Each has a pre-clue and post-clue variant where relevant; repeating the same state uses the final line without replaying animation.

| ID | Speaker/object | Condition | Exact text |
|---|---|---|---|
| `MARA_PRE_001` | Mara Ovelle | Before Relay | `Quarrune pretends not to watch Ayselor. The second you turn away, all six ears follow.` |
| `MARA_POST_001` | Mara Ovelle | Tavi objective active | `The pair are healthy. If Rusk gets dramatic, let Quarrune hold the line.` |
| `JO_PRE_001` | Jo Renn | Before assignment | `Your Relay passed the dust box. The dust box did not.` |
| `JO_POST_001` | Jo Renn | After retrieval | `If the map spins, you are holding it upside down. I put the latch on top.` |
| `PELL_PRE_001` | Pell Anwar | Before queued message | `Clear weather, quiet bands, one carrier still overdue.` |
| `PELL_POST_001` | Pell Anwar | Estate unlocked | `The Estate signal is odd, not hostile. There is a difference.` |
| `ANNEX_EX_SIM` | Simulation glass | Any | `The projected salt basin is gone. Four faint footprints still pulse in the floor.` |
| `ANNEX_EX_MONITOR` | Resonance monitor | Before hook | `Two clean waveforms overlap, separate, and meet again.` |
| `ANNEX_EX_SOLACE` | Solace model | Any before completion | `A long-range research carrier. Its brass nameplate reads: SOLACE.` |
| `ANNEX_EX_CLINIC` | Creature bay | Any | `Warm ceramic nests hold water, mineral blocks, and folded cooling cloth.` |
| `ANNEX_EX_TOOLWALL` | Workshop tool wall | Any | `Every tool has a painted outline. Three outlines are Tavi-sized and empty.` |
| `ANNEX_EX_PLAYER_ROOM` | Player room shelf | Any | `A desert-glass shard, a field notebook, and a space waiting for the Relay.` |
| `ANNEX_EX_WINDOW` | Upper window | Before estate trip | `The western ridge cuts a dark tooth into the bright desert.` |
| `ANNEX_EX_LIFT` | Elevator plate | Any | `The lift plate shows two levels and one very old dent.` |

#### Annex exit

At the sand-skimmer interaction:

| ID | Surface/speaker | Exact text | Action |
|---|---|---|---|
| `EXIT_LOCKED_NO_RELAY` | Field Relay | `A Field Relay is required for desert travel.` | Return control. |
| `EXIT_LOCKED_NO_TRACE` | Dr. Sera Venn — intercom | `Trace Tavi's packet with Pell before you leave.` | Return control. |
| `EXIT_READY_001` | Field Relay | `OPEN DESERT MAP?` | Choices `OPEN MAP` / `STAY`. |
| `SERA_DEPART_001` | Dr. Sera Venn — Relay | `Bring Tavi home. Keep the pair close.` | One-shot on first confirmed departure. |

Confirming sets `annex_exit_cleared = true`, creates `CHECKPOINT_ANNEX_DEPARTURE`, and requests `SCENE_WORLD_MAP` only after the save snapshot is internally complete. A failed write does not cancel the player's ability to travel; it is reported honestly.

### 6.4 Segment D: world map and Estate travel

The map shows the player's skimmer token at the Annex and a clear route line to the newly lit Estate. Only a visible node can receive focus. The wider painted desert has no false prompts. With no confirmation prompt open, Back returns to the captured physical `MapOrigin`: Annex threshold, Estate courtyard, or Estate courtyard with follower handoff. Back inside a confirmation prompt closes only that prompt and leaves the map owner active.

| ID | Surface | Exact text | Action |
|---|---|---|---|
| `MAP_ANNEX_NAME` | Node | `MERIDIAN ANNEX` | Current location on first departure. |
| `MAP_ANNEX_DESC` | Panel | `Research outpost and Resonance clinic — Eastern Basin` | Visible on either direction; no inaccessible-content promise. |
| `MAP_ESTATE_NAME` | Node | `VEYRA ESTATE` | Newly unlocked destination. |
| `MAP_ESTATE_DESC` | Panel | `Observatory and independent workshop — Western Ridge` | No threat promise. |
| `MAP_TRAVEL_CONFIRM` | Prompt | `Travel to Veyra Observatory Estate?` | Choices `TRAVEL` / `BACK`. |
| `MAP_RETURN_CONFIRM` | Prompt | `Travel to Meridian Research Annex?` | Choices `TRAVEL` / `BACK`; `BACK` returns to the map with Tavi still valid as the derived follower. |

Travel uses a 5–7 second skimmer animation across an illustrated relief map. The branded Estate card appears only while the destination scene performs real load/conversion work; if loading finishes early, the animation may complete its authored minimum but no additional fake spinner is added. The previous scene exits after render synchronization. The transaction preserves the incoming player name, party definitions, current HP/progression, settings, and every unrelated story fact. Its exact destination recipe may update only the destination arrival flag, checkpoint, current/last-safe locations, chapter/location provenance, and save-operation revision required by that route.

Arrival precondition: `field_relay_unlocked && estate_destination_unlocked`. Successful arrival sets `estate_arrived = true` and commits `SCENE_ESTATE_COURTYARD / ZONE_ESTATE_COURTYARD / SPAWN_ESTATE_COURTYARD_ARRIVAL` as the durable `LocationKey` in `CHECKPOINT_ESTATE_ARRIVAL`, but only after courtyard collision, player spawn, and the Rusk trigger are ready. Load failure returns to the map with the Annex tuple still valid; it never places the player in an empty scene.

### 6.5 Segment E: Estate courtyard and Rusk battle

#### Arrival and optional courtyard exploration

The player enters at the lower gate. Rusk is visible working beside the kinetic energy fountain but does not trigger until the player crosses a composed mid-courtyard line or speaks to him. The observatory dome, main door, and battle court are readable immediately. The player has 30–75 seconds of optional movement before the confrontation.

| ID | Object | Exact text |
|---|---|---|
| `ESTATE_EX_FOUNTAIN` | Energy fountain | `Copper petals turn falling water into a slow blue spark.` |
| `ESTATE_EX_WEATHERVANE` | Kinetic vane | `The vane points toward the wind, then argues with itself.` |
| `ESTATE_EX_TRACKS` | Small tracks | `Fresh, narrow footprints lead from the crawler stop to the front door.` |
| `ESTATE_EX_GARDEN` | Desert garden | `Shade cloth keeps silverleaf and red needlegrass cool.` |
| `ESTATE_EX_DOME` | Observatory dome | `The roof is open by one handspan. Something inside keeps ticking.` |

#### Mistaken-intruder confrontation

The Field Relay emits a brief cut-wave chirp near the fountain because Ivo's apparatus reflects the old Solace band. Rusk drops a wrench, blocks the door, and signals his team. Camera cuts establish the Relay, Rusk's reaction, the two Estate Echoforms, and the player's starters. The scene is tense but not cruel.

| ID | Speaker | Exact text | Action |
|---|---|---|---|
| `RUSK_PRE_001` | Rusk | `Stop there. That Relay just answered a cut-wave.` | Rusk steps between player and door. |
| `RUSK_PRE_002` | Rusk | `Severance scouts use that band to find what they have broken.` | Kovrass/Ulvorel enter frame. |
| `SERA_STATIC_001` | Dr. Sera Venn — Relay | `Rusk, stand down. That is—` | Signal breaks against fountain pulse. |
| `RUSK_PRE_003` | Rusk | `A borrowed voice is not clearance.` | Rusk raises guard, not a comic pose. |
| `RUSK_PRE_004` | Rusk | `Set the Relay down and step away from the Estate.` | Player looks to starters; they take positions. |
| `RUSK_PRE_005` | Rusk | `No? Then show me whose pattern you carry.` | Begin battle transition. |

Set `rusk_confrontation_seen = true` before battle handoff and write a memory-only `PRE_RUSK_BATTLE_SNAPSHOT` containing the arrival checkpoint's story state **plus that confrontation flag**, exact party HP/progression, and zero encounter rewards. Do not write any later battle or reward flag halfway through the transition.

#### Real 2v2 encounter contract

Player side: Quarrune and Ayselor at current valid HP, healed to at least 70% only if arrival-load recovery found an impossible low-HP state. No hidden full heal occurs in ordinary flow. Enemy side: Kovrass and Ulvorel at full encounter HP. Stable baseline tuning:

| Actor | Max HP | Speed | AI/role |
|---|---:|---:|---|
| Quarrune | 92 | 36 | Player defense, Current answer, cleanse |
| Ayselor | 74 | 64 | Player speed/setup, vulnerable to Ember |
| Kovrass | 82 | 58 | AI support and Ayselor pressure |
| Ulvorel | 88 | 52 | AI primary damage, weak to Quarrune's Strata |

Rusk's deterministic scored AI never reads uncommitted player commands. It considers only legal actions, visible HP/modifiers/status, and cooldowns. Equal scores resolve by ascending `MoveId`, then target instance; AI ties consume no RNG and cannot shift the later battle stream:

- On round one, if both enemies are conscious, Kovrass strongly prefers `Boiler Chorus` on Ulvorel and Ulvorel strongly prefers `Pressure Leap` against the legal player target with lower post-affinity survival. `Boiler Chorus` is the only non-duo regular move with priority +1, visibly labeled in move information, so the baseline queue is Kovrass, Ayselor, Ulvorel, Quarrune. This guarantees the readable support interaction without hidden initiative. Under the locked seed, Ayselor's first-round Dazzle Wake Staggers the already-acted Kovrass and does not Stagger Ulvorel; separate deterministic tests cover a synthetic pending-Ulvorel Stagger, which still leaves Speed 39 ahead of Quarrune's 36.
- Rusk avoids repeating the same support when its stage is already capped.
- An enemy at or below 30% HP raises the score of legal guard/cleanse moves but does not stall indefinitely; the same defensive move is penalized after one consecutive use.
- Damage actions prefer an affinity advantage, then a likely knockout, then lowest percentage HP. They never target a knocked-out actor.
- `Furnace Feint` obeys its cooldown and never applies Staggered twice to the same actor before that actor can act.

The player can win using direct advantage play, partner support into focused damage, spread pressure, Stagger control, or `Horizon Break`. Resonance starts at 0 in the real fight. The encounter may not require the finisher. If only one player Echoform remains conscious, shared finisher UI disappears and legal solo commands continue. No knockout replacement is needed because each opening team contains exactly two active members.

Battle presentation requirements tied to story:

- Intro: Rusk at far-right command mark; player at near-left; all four Echoforms enter from plausible courtyard positions.
- Tactical camera always returns before command selection.
- `Boiler Chorus → Pressure Leap` gets a short reaction shot so the support relationship reads.
- Quarrune/Ayselor each have entrance, two distinct attack performances across their kit, support, hit, knockout, victory, and finisher participation.
- HP, status, order, target arrows, `STRONG/RESISTED`, move info, and Resonance remain readable at 320×240.
- Pause freezes logic/presentation at a safe action boundary. Controller disconnect freezes immediately without advancing a queue or consuming a command.

Victory sequence and exact script:

| ID | Surface/speaker | Exact text | Action |
|---|---|---|---|
| `RUSK_WIN_UI_001` | Result | `FIELD RESONANCE VALIDATED` | Show both starter portraits. |
| `RUSK_WIN_UI_002` | Result | `Quarrune  +25 SYNC` | Apply once. |
| `RUSK_WIN_UI_003` | Result | `Ayselor  +25 SYNC` | Apply once. |
| `RUSK_WIN_UI_004` | Result | `TEAM LINK  1` | Set progression only if reward not claimed. |
| `RUSK_POST_001` | Rusk | `Hold. I know that horn lattice.` | Rusk lowers arm. |
| `RUSK_POST_002` | Rusk | `Sera's Quarrune. Sera's Ayselor.` | Recognition reaction. |
| `TAVI_DOOR_001` | Tavi — behind door | `{PLAYER}? Did the new Relay work?` | Tavi silhouette crosses high window. |
| `RUSK_POST_003` | Rusk | `It worked. I did not.` | One restrained beat, not slapstick. |
| `RUSK_POST_004` | Rusk | `I mistook your signal for Severance work. I am sorry.` | Direct apology. |
| `RUSK_POST_005` | Rusk | `Your companions are steady. Let me restore them, then I will open the Estate.` | Heal and unlock after line. |

Victory sets `rusk_battle_won = true`. Reward application is transactional: add 25 sync to each starter, set team link 1, then set `rusk_battle_reward_claimed = true`; if already true, apply nothing. Rusk restores both player Echoforms to full HP as an explicit post-battle action. The main door animation completes, then `estate_door_open = true` and `CHECKPOINT_RUSK_VICTORY` is saved. The checkpoint never contains reward without its claimed flag or claimed flag without reward.

Defeat sequence:

| ID | Surface | Exact text |
|---|---|---|
| `RUSK_LOSE_001` | Result | `YOUR RESONANCE FELL QUIET` |
| `RUSK_LOSE_002` | Rusk | `Enough. I will not press a fallen pair.` |
| `RUSK_LOSE_CHOICE` | Prompt | `Try the encounter again?` |
| `RUSK_LOSE_RETRY` | Choice | `RETRY` |
| `RUSK_LOSE_RETURN` | Choice | `RETURN TO ANNEX` |

`RETRY` restores the exact `PRE_RUSK_BATTLE_SNAPSHOT`, rebuilds the encounter, skips the long misunderstanding script, and uses Rusk's short line `Ready? Then let the true pattern answer.` It does not duplicate arrival, clue, confrontation, or reward flags. `RETURN TO ANNEX` restores the same snapshot, returns through `SCENE_ANNEX_INTERIOR / ZONE_ANNEX_THRESHOLD / SPAWN_ANNEX_THRESHOLD_DEPARTURE`, keeps the Estate unlocked, `estate_arrived`, `rusk_confrontation_seen`, and `OBJ_FIND_TAVI` active, and leaves every Rusk win/reward/door fact false. Only after normal Annex-threshold entry is stable, write `CHECKPOINT_RUSK_RETURN_TO_ANNEX` with the threshold tuple as both current and last-safe, `BATTLE_RESULT_RETURN_TO_ANNEX`, and `ENCOUNTER_RUSK_COURTYARD`; reboot resumes there. Sera's one-time return line is: `Regroup. Tavi is safe at the Estate; go back when your pair is ready.` A later Estate arrival uses `RUSK_RETRY_001`: `We still have an unanswered signal between us.` and re-enters the battle.

| ID | Speaker | Exact text | Trigger/action |
|---|---|---|---|
| `RUSK_RETRY_IMMEDIATE_001` | Rusk | `Ready? Then let the true pattern answer.` | Immediate Retry after snapshot restore; start the rebuilt encounter after dismissal. |
| `SERA_RUSK_RETURN_001` | Dr. Sera Venn — Relay | `Regroup. Tavi is safe at the Estate; go back when your pair is ready.` | First stable Annex-threshold control after defeat Return; one-shot only. |
| `RUSK_RETRY_001` | Rusk | `We still have an unanswered signal between us.` | Later Estate arrival after defeat Return; start the real battle after dismissal. |

### 6.6 Segment F: Estate interior, reunion, and follower

Rusk leads two steps inside, then moves aside so the player owns navigation. He does not escort the player down a forced corridor.

| ID | Speaker | Exact text | Action |
|---|---|---|---|
| `RUSK_ENTRY_001` | Rusk | `Tavi is with Ivo in the upper study.` | Frame foyer stairs and invention hall route. |
| `RUSK_ENTRY_002` | Rusk | `The direct stair is jammed by an orrery arm. The hall route is clear.` | Establish readable traversal, not an inaccessible tease. |
| `RUSK_ENTRY_003` | Rusk | `Touch nothing that hums in three directions.` | Rusk realizes nearly everything does; small look, no extra text. |

The route is `ESTATE_FOYER → ESTATE_INVENTION_HALL → ESTATE_STUDY`. The player may inspect devices but must solve no opaque puzzle. Mandatory interaction `INT_ORRERY_SWITCH` asks the player to hold `{A}` for 45 fixed gameplay ticks while the model sky rotates. Releasing early, losing the controller, leaving interaction range, or interrupting before the arm-clear event runs `anm.prop.orrery_switch.interrupted_reset` and `anm.mech.grand_orrery.interrupted_reset`; collision/nav remain blocked and `orrery_stair_open` remains false. After the held action, arm-clear animation, study-stair collision swap, and nav edge all validate coherently, one story transaction sets monotonic `orrery_stair_open = true`. Saving is rejected while the mechanism is moving. Once true, re-entry reconstructs the open pose/collision, the switch becomes repeat examine-only, and no path resets the flag.

Optional Estate interior copy:

| ID | Object | Exact text |
|---|---|---|
| `ESTATE_EX_PORTRAIT` | Gallery portrait | `Ivo and Rusk stand beside a younger observatory dome. Both are pretending not to smile.` |
| `ESTATE_EX_COMPASS` | Impossible compass | `Every needle points at a different interesting mistake.` |
| `ESTATE_EX_WALKDESK` | Walking desk | `Four padded feet lift in sequence. The desk has traveled almost a meter.` |
| `ESTATE_EX_BOTTLESTAR` | Bottled-star projector | `A warm point of light circles the glass whenever Ayselor passes.` |
| `ESTATE_EX_RAINCLOCK` | Rain clock | `It measures the time since rain. The smallest hand has not moved.` |
| `ESTATE_EX_ORRERY` | Orrery arm before `orrery_stair_open` | `The brass arm blocks the stair and tracks an object below the horizon.` |
| `ESTATE_EX_ORRERY_OPEN` | Orrery arm after `orrery_stair_open` | `The brass arm rests above the cleared stair, still tracking below the horizon.` |
| `ESTATE_EX_SWITCH_OPEN` | Rotation switch after `orrery_stair_open` | `The switch rests in its open notch. The stair is clear.` |
| `ESTATE_EX_LOGBOOK` | Study logbook | `One line is underlined twice: A FALLING SIGNAL CAN STILL BE MOVING.` |
| `ESTATE_EX_TELESCOPE` | Telescope | `The eyepiece is warm. Violet dust clings to the outer ring.` |

`INT_ORRERY_SWITCH` selects the held-open action only while `orrery_stair_open = false`. Once the coherent open transaction commits, the same physical switch selects `ESTATE_EX_SWITCH_OPEN` as an ordinary one-page examine interaction; it cannot reacquire a hold token, replay mechanism motion, or request another flag write. The adjacent orrery-arm examine anchor likewise switches from `ESTATE_EX_ORRERY` to `ESTATE_EX_ORRERY_OPEN`; the blocked-stair copy is never legal after the arm-clear commit.

Study discovery blocking: Tavi stands on a safe step turning the physical orrery with Ivo's guidance. Ivo is comparing its track to a paper roll. The player enters behind them; `anm.echo.ayselor.story_packet_ping` changes the keel-lamp state, which triggers `anm.prop.packet_recorder.keel_lamp_answer` and `sfx.story.packet_recorder_answer` exactly once. Tavi spots the player first.

| ID | Speaker | Exact text | Action |
|---|---|---|---|
| `REUNION_001` | Tavi | `You found me. The Relay works!` | Tavi hops down and stops at safe distance. |
| `REUNION_002` | Tavi | `I know. The rule was inside the Annex.` | Tavi sees player's/Sera's concern. |
| `REUNION_003` | Tavi | `The crawler was leaving, and Ivo's roof really does move. I should have asked.` | Accountable, no scolding pile-on. |
| `REUNION_004` | Ivo Veyra | `The fault is shared. I confirmed the tag and forgot to confirm the child.` | Ivo closes recorder. |
| `REUNION_005` | Ivo Veyra | `Still, your search brought the correct instrument.` | Gesture to Field Relay. |
| `REUNION_006` | Ivo Veyra | `At dusk, my lowest lens heard a star fall upward.` | Orrery tracks under horizon. |
| `REUNION_007` | Ivo Veyra | `Not light. A carrier handshake, buried inside a violet shear.` | Recorder sends packet. |
| `REUNION_008` | Field Relay | `OBSERVATORY PACKET RECEIVED — ANALYSIS PENDING` | Store message; do not reveal Solace yet. |
| `REUNION_009` | Tavi | `Sera is going to use my entire name.` | Small worried look. |
| `REUNION_010` | Ivo Veyra | `Then do not make her spend it twice. Go home together.` | Objective update. |
| `REUNION_011` | Tavi | `I will follow. Properly this time.` | Begin follower setup. |

Set `ivo_met = true`, `tavi_found = true`, `return_to_annex_requested = true`, and objective `OBJ_RETURN_WITH_TAVI` with text `Return to Meridian Research Annex with Tavi.` Runtime follower state becomes active only after Tavi's spawn and navigation state are valid. Its exact derived predicate is `OBJ_RETURN_WITH_TAVI active && return_to_annex_requested && tavi_found && !tavi_returned_to_annex && current zone has valid follower nav/handoff`; it is not a non-monotonic saved flag. `ivo_met` remains a required reunion/checkpoint invariant but is not an additional follower predicate. Save `CHECKPOINT_TAVI_FOUND` only once that derived follower state can be reconstructed safely.

Follower contract:

- Tavi uses the exact 1.2/1.6/2.0 m min/target/max trail contract. The reachable point nearest 1.6 m behind the player's solved facing wins by path cost then node ID. Inside 1.2 m Tavi stops/yields; through 2.0 m Tavi walks at up to 1.75 m/s; beyond 2.0 m Tavi catches up at up to 3.25 m/s. Acceleration/deceleration is 7/9 m/s², turn cap is 216 degrees/s, and a 0.75 m yield disc protects the player and mandatory interactions.
- Within 0.5 m of a door/portal anchor, Tavi enters the authored wait pose. The door-open fact, destination nav generation, and paired anchor must remain current for two fixed ticks before the transition captures the handoff and unloads the old room; the next room reconstructs Tavi at that exact paired anchor.
- Recovery is same-room only. It requires both player distance above that room's Data threshold for all 45 fixed ticks and path progress below 8/256 m for at least 30 ticks. It selects a clear same-connected-component recovery node by lowest path cost then node ID within 48 nodes, and both Tavi and the anchor must remain outside the camera frame plus 16 pixels and blocker-occluded for two rendered frames. Visibility, progress, distance, modal/transition, or any scene/follower/camera generation change cancels and resets recovery. It never crosses a closed door or zone; room separation uses only the handoff above, and World Map carries no live follower actor.
- Tavi cannot fall, trigger devices, start dialogue, block the orrery switch, or enter battle collision.
- If controller disconnects or Pause opens, follower simulation stops with the player.
- Interacting with Tavi while following uses `TAVI_FOLLOW_001`: `I am here. Annex first; questions after.`
- At the courtyard exit, `RUSK_EXIT_001` is `I will send Ivo's full chart when the bands clear.` Tavi answers in `TAVI_EXIT_001`: `And I will send Sera a message before I leave anywhere.`

The courtyard gate opens the world map. Only Annex is the required selection; Estate remains selectable/cancel-safe. Confirming Annex makes Tavi's map token visibly join the player's token. The return travel card performs real Annex loading. On Annex arrival, Tavi spawns behind the player at the exterior threshold with follower state intact.

### 6.7 Segment G: resolution, Solace signal, and closing hook

The Annex threshold-to-atrium route remains player-controlled for 20–45 seconds. NPCs look toward Tavi, but no trigger fires until both player and follower enter the atrium resolution volume. If Tavi is recovering at a portal, the scene waits without trapping the player.

Resolution blocking: Sera kneels briefly to Tavi's height, then stands; Oren remains near the Resonance monitor; Pell is at the upper rail. The player's Echoforms take readable positions. Tavi is responsible but safe. Dialogue stays concise.

| ID | Speaker | Exact text | Action |
|---|---|---|---|
| `RETURN_001` | Dr. Sera Venn | `Tavi.` | One beat; no music sting. |
| `RETURN_002` | Tavi | `I left the boundary without asking. I sent the tag, not the plan.` | Tavi owns mistake. |
| `RETURN_003` | Tavi | `I am sorry.` | Sera softens. |
| `RETURN_004` | Dr. Sera Venn | `You are home. We can be relieved and still change the rules.` | Sera places hand on shoulder. |
| `RETURN_005` | Director Oren Saye | `Objective resolved. Next time, the calibration tag hides where the map is lit.` | Clear missing objective. |
| `RETURN_006` | Tavi | `That is fair.` | Tavi moves beside Sera. |
| `RETURN_007` | Dr. Sera Venn | `{PLAYER}, you brought Tavi back and kept the pair steady. Well done.` | `anm.player.ari.dialogue_nod`; both starters play `story_resolve`. |

When `RETURN_005` is dismissed, set the monotonic flag `tavi_returned_to_annex = true`, resolve `OBJ_RETURN_WITH_TAVI`, and derive runtime follower state as inactive; Tavi remains a staged dialogue actor for `RETURN_006` and `RETURN_007`. After `RETURN_007` is dismissed, begin the transactional save of `CHECKPOINT_TAVI_RETURNED`. The hook starts only after runtime state is coherent; it may proceed if the EEPROM write reports failure, but the failure prompt appears before the end card.

Pell's station emits the Field Relay's two-note cue followed by a low third tone. Oren turns to the monitor. The hook is an in-engine staged scene, not the missing cinematic.

| ID | Speaker | Exact text | Action |
|---|---|---|---|
| `HOOK_001` | Field Relay | `OBSERVATORY PACKET RESOLVED` | Relay opens message without player input. |
| `HOOK_002` | Pell Anwar | `Director. Carrier handshake S-04.` | `anm.mech.beacon_decoder.moving_trace`. |
| `HOOK_003` | Director Oren Saye | `Solace.` | `anm.prop.solace_model.practical_light_on`. |
| `HOOK_004` | Dr. Sera Venn | `Its emergency beacon fell beyond our last sweep.` | Camera moves from model to map. |
| `HOOK_005` | Pell Anwar | `Then the beacon moved. Twelve kilometers against the wind.` | `anm.mech.beacon_decoder.trace_shift`. |
| `HOOK_006` | Tavi | `A beacon cannot walk.` | Tavi watches, not a joke. |
| `HOOK_007` | Ivo Veyra — recorded | `Correct. Something carried the signal—or bent the distance around it.` | Ivo waveform appears, no portrait animation needed. |
| `HOOK_008` | Dr. Sera Venn | `Quiet. The pair hear something.` | Quarrune `story_brace_alert`; Ayselor `story_lamp_dim_alert`. |
| `HOOK_009` | Field Relay | `UNKNOWN RESONANCE RESPONSE` | Monitor adds enormous third waveform. |
| `HOOK_010` | Pell Anwar | `That pattern is Fractured.` | Magenta-violet accent enters for first Annex contamination. |
| `HOOK_011` | Director Oren Saye | `It is answering Solace.` | Waveform bends toward beacon. |
| `HOOK_012` | Tavi | `Can it hear us?` | Tavi looks to Sera. |
| `HOOK_013` | Dr. Sera Venn | `Not yet.` | Sera looks to player. |
| `HOOK_014` | Dr. Sera Venn | `We find it before the Severance does.` | Cut on `anm.player.ari.hook_resolve` and both starters' `story_resolve`. |

Set `solace_beacon_received = true` immediately after `HOOK_005`, `fracture_signal_seen = true` after `HOOK_010`, and `slice_complete = true` only after `HOOK_014` finishes and the end-state checkpoint commits in memory. No line or flag may fire twice on reload.

End treatment:

1. Retain the coherent Annex Hook owner, monitor image, and low tone after `HOOK_014` while the immutable `CHECKPOINT_SLICE_COMPLETE` request resolves. `TRANS_DEF_HOOK_TO_END_CARD` is forbidden while the final outcome is `PENDING`.
2. On verified `SAVED + CLEAN`, show `RESONANCE RECORDED`. If the write fails, keep the retained Annex owner visible and show `The record could not be written. Continue without saving?` with `RETRY SAVE` / `CONTINUE UNSAVED`; retry is repeatable and never mutates progress twice. Continue Unsaved resolves the outcome as `CONTINUE_UNSAVED + DIRTY` without claiming persistence.
3. Only after either terminal resolved outcome, fade the monitor's violet line to black while preserving its low tone, transition to the authored mark `N64GAME`, and show the subtitle `END OF OPENING CHAPTER`.
4. Offer `CONTINUE EXPLORING` and `RETURN TO TITLE` only after that transition. Both are stable. If runtime progress remains dirty after `CONTINUE UNSAVED`, selecting `RETURN TO TITLE` first shows `Unsaved opening progress will be lost. Return to title?` with safe-default choices `STAY` / `RETURN`.
5. `CONTINUE EXPLORING` returns to post-chapter `ANNEX_ATRIUM_L1`, with Tavi beside Sera, both destinations available, Rusk friendly, no hook replay, and no inaccessible promised door.
6. `RETURN TO TITLE` destroys scene-owned hook resources. Only a successful complete-checkpoint write enables Continue from the complete beat. After an explicitly confirmed unsaved return, Continue loads the prior valid EEPROM checkpoint exactly as written; it never presents the dirty in-memory ending as saved.

The first Return press is always a selector, never the warning acknowledgement.
When dirty, it captures the exact originating Pause/gameplay, End Card, or
rollback-fatal owner generation/state/focus before opening the loss warning.
`STAY` destroys only that warning and restores the captured origin exactly.
Confirmed `RETURN` alone emits the origin-specific single-use acknowledgement
plus the current warning token; the other two origins cannot consume it. Clean
origins route directly. No dirty path may reuse the first press, fall through to
another screen, or return to a default focus.

Post-chapter optional lines:

`POST_OREN_001` is available whenever the save service has verified that a semantically complete `CHECKPOINT_SLICE_COMPLETE` page exists. It remains truthful if the current runtime later becomes dirty through a newer location/settings change, because the opening record itself is still secure. If the player chose `CONTINUE UNSAVED` before any complete page committed, use `POST_OREN_UNSAVED_001`; it remains active until any generation-current valid save successfully persists the coherent complete checkpoint or the dirty runtime is discarded. A later manual/settings/transition SaveReason does not erase the durable checkpoint identity. The unsaved copy is never shown for `SAVED+DIRTY`, and the saved copy is never shown for `CONTINUE_UNSAVED+DIRTY`.

| ID | Speaker | Exact text |
|---|---|---|
| `POST_SERA_001` | Dr. Sera Venn | `Rest the pair. We move when the signal is understood.` |
| `POST_OREN_001` | Director Oren Saye | `The opening record is secure. No guesses will become orders.` |
| `POST_OREN_UNSAVED_001` | Director Oren Saye | `The Relay has not secured this record yet. We will not pretend otherwise.` |
| `POST_TAVI_001` | Tavi | `Next trip: message first, moving roof second.` |
| `POST_PELL_001` | Pell Anwar | `The signal is still moving. The map is not ready to call it a route.` |
| `POST_RUSK_001` | Rusk | `The Estate recognizes your pattern. I am improving at that.` |
| `POST_IVO_001` | Ivo Veyra | `A falling star that climbs is either a discovery or an apology from physics.` |

## 7. Story-state contract

### 7.1 Canonical scene and objective IDs

Scenes:

`SCENE_BOOT`, `SCENE_TITLE`, `SCENE_OPENING_SLOT`, `SCENE_NAME_ENTRY`, `SCENE_SIM_ARENA`, `SCENE_ANNEX_INTERIOR`, `SCENE_WORLD_MAP`, `SCENE_ESTATE_COURTYARD`, `SCENE_ESTATE_INTERIOR`, `SCENE_END_CHAPTER`.

Objectives:

| ID | Start | Complete | Field Relay copy |
|---|---|---|---|
| `OBJ_RETRIEVE_FIELD_RELAY` | `OREN_003` dismissed | `SERA_RELAY_002` dismissed after Pell's valid trace | `Collect the Field Relay from Jo in the lower workshop.` then `Ask Pell to trace Tavi's message.` |
| `OBJ_FIND_TAVI` | `SERA_RELAY_002` dismissed | `REUNION_001` starts with Tavi valid in study | `Travel to Veyra Observatory Estate and find Tavi.` |
| `OBJ_RETURN_WITH_TAVI` | `REUNION_011` dismissed | `RETURN_005` dismissed with both player/Tavi in atrium | `Return to Meridian Research Annex with Tavi.` |
| `OBJ_OPENING_COMPLETE` | Hook begins | `HOOK_014` dismissed and stable end state entered | `Opening chapter complete.` |

Only one required objective is active at a time. Completed objectives remain in a record list and cannot be restarted.

### 7.2 Saved story flags

All flags default false in New Game. Their transitions are monotonic in the opening chapter.

| Flag | Exact set point | Required preconditions | Immediate postcondition |
|---|---|---|---|
| `opening_cinematic_seen` | Opening finalizer | New Game state; opening slot active | Request name entry; no input leak |
| `player_name_confirmed` | Name-to-Sim post recipe publishes after coherent Sim staging and successful address promotion | Valid 1–8-letter name; cinematic seen; quiescent SaveService; first-request address identity still exact | Stable after-name checkpoint and initialized campaign runtime |
| `tutorial_complete` | Result card accepted | All five tutorial gates; finisher resolved | Dissolve to Annex |
| `annex_intro_complete` | `ANNEX_INTRO_005` dismissed | Tutorial complete; room ready | Free Annex control |
| `starter_team_received` | `ANNEX_INTRO_004` dismissed | Quarrune/Ayselor assets and party slots valid | Real party available |
| `field_relay_quest_started` | `OREN_003` dismissed | Annex intro; Oren scene not completed | Relay objective active |
| `field_relay_unlocked` | `JO_RELAY_006` dismissed | Quest started; acquisition object valid; queued message presentation complete | Player-owned Relay UI and Ask-Pell substage available |
| `tavi_missing_reported` | `SERA_RELAY_002` dismissed | Relay unlocked; trace completed | Tavi objective active |
| `estate_destination_unlocked` | `PELL_TRACE_004` dismissed | Valid Estate node data | Estate selectable |
| `annex_exit_cleared` | First departure confirmed | Tavi objective; map unlocked | World map request |
| `estate_arrived` | Courtyard stable | Valid travel from map | Arrival checkpoint |
| `rusk_confrontation_seen` | Before battle handoff | Estate arrived; Rusk not won | Prebattle snapshot valid |
| `rusk_battle_won` | Victory runtime resolves | Legal real encounter victory | Post-battle script |
| `rusk_battle_reward_claimed` | Atomic reward commit | Rusk won; reward not already claimed | +25 sync each; team link 1 |
| `estate_door_open` | Door animation reaches open state | Rusk won | Interior entry enabled |
| `orrery_stair_open` | `INT_ORRERY_SWITCH` arm-clear/stair-nav/collision transaction commits | Estate door open; held action complete; mechanism and route coherent | Study route open permanently; safe re-entry/manual-save reconstruction |
| `ivo_met` | `REUNION_004` dismissed | Study scene active | Ivo known in records |
| `tavi_found` | `REUNION_001` starts | Tavi actor valid in study | Find objective may resolve |
| `tavi_returned_to_annex` | `RETURN_005` dismissed | Tavi found; return objective active; both actors valid in atrium | Follower runtime state off; personal objective complete |
| `return_to_annex_requested` | Same transaction that starts `OBJ_RETURN_WITH_TAVI` after `REUNION_011` is dismissed | Tavi found; return objective about to become active; follower spawn/nav handoff valid | Annex highlighted on map; derived follower state may become active |
| `solace_beacon_received` | `HOOK_005` dismissed | Tavi return coherent | Solace message stored |
| `fracture_signal_seen` | `HOOK_010` dismissed | Beacon received; monitor scene valid | Fracture record stored |
| `slice_complete` | End state entered after `HOOK_014` | Both hook flags; no active transition | Post-chapter state and final checkpoint |

Optional one-shot flags use prefixes `examined_`, `spoke_`, or `help_seen_`. They may alter repeat copy but never gate a mandatory trigger, consume required save capacity unpredictably, or affect battle tuning.

### 7.3 Progression invariants

- `starter_team_received` implies the real party contains exactly Quarrune and Ayselor.
- `field_relay_unlocked` implies `field_relay_quest_started`.
- `estate_destination_unlocked` implies `field_relay_unlocked` and `tavi_missing_reported`.
- `estate_door_open` implies `rusk_battle_won` and `rusk_battle_reward_claimed`.
- `orrery_stair_open` implies `estate_door_open`; `tavi_found` implies `orrery_stair_open` because the Study cannot be entered before the route transaction commits.
- `tavi_returned_to_annex` implies `tavi_found`, `ivo_met`, `estate_door_open`, and `return_to_annex_requested`.
- `solace_beacon_received` implies `tavi_returned_to_annex` and a completed return transition.
- `slice_complete` implies `tutorial_complete`, `rusk_battle_won`, `tavi_found`, `solace_beacon_received`, and `fracture_signal_seen`.
- A loaded record that violates an invariant is invalid or migratable; it is never patched by granting rewards opportunistically.

## 8. Checkpoints, retries, and edge cases

### 8.1 Stable checkpoints

| Checkpoint | Location/resume behavior | Serialized facts |
|---|---|---|
| `CHECKPOINT_AFTER_NAME` | Name entry complete; resume at simulation intro | name, settings, cinematic seen; tutorial false |
| `CHECKPOINT_AFTER_TUTORIAL` | Physical sim chamber after the onboarding script, before free Annex control | tutorial and starter-acquisition transaction |
| `CHECKPOINT_FIELD_RELAY` | Workshop or latest stable Annex room | Relay/objective/queued message progression |
| `CHECKPOINT_ANNEX_TRACE_COMPLETE` | Atrium/Relay-balcony handoff after Pell's trace; later predeparture manual saves may use any validated stable Annex room | Find-Tavi objective active, Estate unlocked, Annex exit not yet cleared, and exact current/last-safe tuple |
| `CHECKPOINT_ANNEX_DEPARTURE` | Annex exterior before map after first confirmed departure | full party HP/progression, Find-Tavi objective, Estate unlock, Annex exit cleared, and canonical threshold/fallback tuple |
| `CHECKPOINT_ESTATE_ARRIVAL` | Courtyard spawn before confrontation | exact party state; no battle reward |
| `CHECKPOINT_RUSK_VICTORY` | Courtyard after door opens | battle result/reward atomic state; full restored HP |
| `CHECKPOINT_RUSK_RETURN_TO_ANNEX` | Annex threshold after choosing Return on real-battle defeat | restored prebattle facts, Find-Tavi active, Estate arrived/confrontation retained, all Rusk win/reward/door facts false, typed Return result and Rusk encounter ID |
| `CHECKPOINT_TAVI_FOUND` | Study after follower becomes valid | orrery stair open, Tavi/Ivo/return objective state |
| `CHECKPOINT_TAVI_RETURNED` | Annex atrium before hook | follower off, personal objective resolved |
| `CHECKPOINT_SLICE_COMPLETE` | Annex post-chapter state | all hook flags, complete state, no active cutscene |

Manual saves exist only on Field Relay -> Save -> `RECORD PROGRESS`. The Save
view first resolves the exact current `SAVELOC_MANUAL_ALLOWED` tuple; an
unresolved/unstable state disables Record and shows `Finish the current
transition first.` Selecting Record opens `Record progress at this stable
location?`; Back closes only that confirm. Confirm consumes its edge and closes
the modal before the Manual Relay producer reserves SaveService. BUSY retains
unpublished scratch and shows `RECORDING RESONANCE...`; admission captures the
latest stable progress, replaces both current/last-safe keys with that exact
tuple, and writes only operation provenance `SAVE_REASON_MANUAL_RELAY` while
retaining the semantic checkpoint. COMMITTED shows `RESONANCE RECORDED` and
returns to Relay Save focus. Failure offers only immutable Retry or Cancel;
Cancel publishes nothing and preserves live progress/settings/dirty state.
Dialogue action application, battle, door/elevator movement, room load,
world-map travel, follower recovery, or hook staging is ineligible. Edges are
debounced. Power loss during a transition resumes the last verified stable
checkpoint, never a half-entered destination.

### 8.2 Dialogue and scene skipping

- The temporary opening slate alone uses `{A}`/`{START}` skip. Natural and skipped completion set the same flag and next scene.
- Mandatory dialogue supports type-on completion, not whole-scene skip. Rapid input cannot bypass an action-bearing line.
- Reloading after a dialogue-attached flag uses the next coherent beat. It never replays a reward or leaves actors in their pre-animation pose.
- Leaving and revisiting a room after its scene is complete uses ambient placement and repeat dialogue, not the original blocking.

### 8.3 Controller disconnect

- Boot/title/name/menu: selection freezes and `CONTROLLER DISCONNECTED` appears; no default choice fires.
- Exploration: an active held interaction first receives the disconnect edge and completes its idempotent cancel/reset transaction; only then do player motion, camera intent, follower simulation, interaction selection, and all remaining gameplay timers freeze. No partial hold progress survives reconnect. Ambient animation/audio may continue safely.
- Dialogue: type-on and action dismissal freeze on the current page.
- Battle: state machine and presentation clock freeze immediately. No queued action, damage event, VFX callback, or meter change advances.
- Slate: its presentation timer may finish because it requires no choice; reconnecting at name entry is safe. A skip press from the lost controller cannot leak.
- Reconnect requires a neutral stick and released confirm buttons for one frame before input resumes.

### 8.4 Revisit and repeated-objective behavior

- Completed Relay acquisition removes the bench pickup and leaves an empty powered dock. Jo uses post-retrieval dialogue.
- Completed Tavi trace keeps Estate lit; Pell never reruns the unlock animation.
- Before Rusk victory, every Estate arrival leads to either the confrontation or its shorter retry variant. After victory, Rusk is friendly and the door stays open.
- Tavi exists in exactly one ownership state: Estate study, active follower, Annex resolution actor, or Annex post-chapter actor. Never two.
- Repeated map travel preserves flags/party and uses normal loading; it cannot rerun reward or hook scenes.
- After `slice_complete`, entering the atrium never replays `RETURN_*` or `HOOK_*`. The monitor remains in a stable low-intensity analysis state.
- Attempting a completed objective only shows its record entry; no interaction prompt claims it can be repeated.

### 8.5 Invalid data and impossible-state recovery

- Invalid/incompatible EEPROM: preserve settings when independently valid, show the title prompt, and begin a clean New Game only after confirmation.
- Simulation impossible state: restart simulation; no story rollback beyond tutorial-local state.
- Estate battle impossible state: restore prebattle snapshot and show Retry/Return choices.
- Missing follower path: while valid same-room nav exists, attempt only the exact clear same-connected-component recovery-node selector described above; never relocate to a portal or across a door/zone. Missing/corrupt nav cancels recovery and aborts travel to the last stable room with no follower/story mutation, plus a debug assertion, rather than softlocking release play.
- Destination load failure: keep or restore the source scene, show `Travel could not be completed.`, and allow retry.
- Save write failure: use the exact source policy without claiming success. Established campaigns permit the documented Retry/Continue or Travel Unsaved choices; Manual/Settings permits Retry/Cancel; the unpersisted New Game initialization permits only immutable Retry or Return to Title. Footer-last journaling keeps the prior valid EEPROM anchor untouched.

## 9. Loading and transition matrix

| From → to | Presentation | Story handoff |
|---|---|---|
| Boot → title | Resonance line resolves into final logo/menu | Save validity known before Continue enables |
| Title → opening slot | Ochre fade with carrier-line motif | Clean New Game state |
| Opening slot → name | Violet edge contracts into name-panel cursor | Cinematic flag set, skip edge cleared |
| Name → simulation | Entered letters become arena call-sign plate | Stable name checkpoint |
| Simulation → Annex | Arena geometry dissolves to physical chamber | Tutorial battle destroyed; real party then granted |
| Annex rooms | Door/elevator choreography; brief honest fades only if streaming requires | One room owner exits after destination ready |
| Annex → map | Field Relay expands into illustrated desert relief | Departure checkpoint coherent |
| Map → Estate | Skimmer moves on relief; Estate branded load card over real work | Party/state unchanged; arrival set after collision ready |
| Courtyard → battle | Rusk hand signal, letterbox close, tactical camera reveal | Prebattle snapshot valid |
| Battle → courtyard | Result UI fades into same physical staging | Reward transaction then door state |
| Estate rooms | Authored doors/stairs, follower portal accounting | Follower never orphaned |
| Estate → map → Annex | Joined player/Tavi token and Annex load card | Tavi ownership transfers to Annex follower |
| Annex return → hook | No load; atrium monitor/camera staging | Return checkpoint coherent before hook |
| Hook → end card | Fracture line fades through black into title mark | Complete checkpoint before stable choice |

No transition may expose uninitialized frames, debug text, a frozen previous camera, or placeholder geometry. Apart from the approved opening slate, branded loading appears only around real work.

## 10. Pacing instrumentation and validation

Debug and certification builds record timestamped events without changing release timing. `RUN_END_HOOK` fires exactly when the stable end-card choices first accept input after the save-success or explicitly resolved continue-unsaved branch; it does not fire merely when `HOOK_014` is dismissed:

- `RUN_COLD_BOOT`, `RUN_END_HOOK`
- `SCENE_ENTER`, `SCENE_CONTROL_GRANTED`, `SCENE_CONTROL_REVOKED`, `SCENE_EXIT`
- `DIALOGUE_START`, `DIALOGUE_PAGE`, `DIALOGUE_END`
- `OBJECTIVE_START`, `OBJECTIVE_COMPLETE`
- `BATTLE_ENTER`, `BATTLE_COMMAND_OPEN`, `BATTLE_ACTION`, `BATTLE_RESULT`, `BATTLE_EXIT`
- `MAP_OPEN`, `TRAVEL_CONFIRMED`, `DESTINATION_READY`
- `SAVE_REQUEST`, `SAVE_SUCCESS`, `SAVE_FAILURE`
- `IDLE_START`, `IDLE_END`, `CONTROLLER_LOST`, `CONTROLLER_FOUND`
- `TUTORIAL_GATE_COMPLETE`, `FOLLOWER_RECOVERY`

Idle begins after 10 continuous seconds with no input while player control is available and no mandatory presentation is running; its full interval is subtracted from measured total and active-control time. Normal deliberation under 10 seconds remains gameplay. Dialogue reading time stays in total chapter time but never active-control time. Transition/load time stays in total because the player experiences it, and is separately reported so performance regression cannot masquerade as pacing.

Each certification timing report includes:

- total non-idle cold-boot-to-hook time;
- active-control time;
- segment times matching Section 1;
- mandatory dialogue time;
- battle command versus presentation time;
- real load/transition time;
- optional interactions used;
- retries, controller interruptions, and follower recoveries;
- route and final flag invariant result.

Run profiles:

1. **Curious first player:** opens party/save, speaks to all three Annex support NPCs, examines four props per destination, uses varied battle commands.
2. **Direct first player:** follows composition/prompts, opens each taught UI once, uses no optional dialogue beyond what naturally crosses the route.
3. **Alternate-input first player:** takes nonrecommended tutorial actions, loses or nearly loses the Rusk fight once, then retries without deliberately waiting.

The median total duration must be 18–25 minutes, and each qualifying run must contain at least 15 minutes of active control. Only total duration is evaluated by median. If any run falls short of the active-control floor, add meaningful navigation, battle decision depth, or optional-on-route interaction—not forced walking speed, repeated dialogue, fake loading, excessive HP, or unskippable idle animation. If the curious run exceeds 25 minutes, keep optional content but report both normal route and optional completion; the total-duration median still governs.

## 11. Acceptance criteria for this story implementation

The story/timing gate passes only when:

- Cold boot reaches the final hook without a missing beat, temporary story text, or inaccessible required room.
- The only accepted temporary presentation is the `INSERT CUTSCENE HERE` slate at the locked opening point, with an exact three-second fully visible hold and no more than five seconds total natural playback.
- Every mandatory line in this document is implemented with correct speaker, order, trigger, and one-shot action; any edited copy receives a documented narrative review.
- The player enters a valid 1–8-letter uppercase name, and every `{PLAYER}` occurrence handles all lengths at 320×240.
- The simulation teaches commands, targets, info, order, affinity, HP, support/status, Resonance, and its duo finisher while accepting reasonable alternate legal choices.
- The real starter onboarding is staged in-world; Quarrune and Ayselor are the persistent party thereafter.
- Both Annex levels and every required room can be visited; the Field Relay, trace, save, party, map, and departure flow remain player-controlled.
- The world map supports cancel, Estate travel, return travel, repeat travel, and real state preservation.
- Rusk's complete 2v2 supports multiple winning plans, readable legal AI, `Boiler Chorus → Pressure Leap`, victory, defeat, retry, Return to Annex, no duplicate reward, and coherent post-battle state.
- The Estate contains the complete courtyard, foyer, invention hall, study, optional invention copy, Ivo/Tavi discovery, and a visible reliable Tavi follower return.
- The personal objective resolves before the Solace/Fractured hook begins.
- Save/reload at every stable checkpoint, slate skip, tutorial restart, battle retry, controller reconnect, dialogue hammering, revisit, map repetition, invalid save, and follower recovery do not duplicate flags, rewards, actors, or scenes.
- Three instrumented runs meet the total and active-control timing contract without padding.
- The final state saves, offers a stable menu/post-chapter exploration state, and makes no inaccessible-content promise.
- All characters, factions, locations, Echoforms, moves, dialogue, scene expression, and terminology remain original and within the clean-room boundary.

This document locks content for implementation; it does not by itself prove the game exists or passes the gate.
