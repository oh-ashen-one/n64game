# Reference, Technical, and Clean-Room Study

Snapshot date: 2026-07-18.

This document records evidence used to design `n64game`. It is not an asset-import list. All downloaded source archives, ROMs, footage, screenshots, and walkthrough captures remain outside this public repository.

## 1. Executive conclusions

1. A polished original 3D game on a standard 4 MB N64 is technically feasible with libdragon preview and Tiny3D. Pandemonium v0.71 is direct evidence: its release says the Expansion Pak is no longer required and distributes a 13,107,200-byte ROM.
2. The reference quality is not “free” low-poly output. Pandemonium v0.71 contains approximately 28,866 lines of C/header code and 201 source assets. Its two lead contributors made hundreds of recorded contributions, and the jam-window history contains approximately 147 commits. The asset, animation, scene, memory, and presentation work is the project.
3. The Drive source snapshot and v0.71 are materially different. The Drive archive corresponds to the 2026-02-02 commit `dfe02a3014763e01303e418d0fe2219bad4ef070`, while v0.71 points to `d6578443ec1ca7634435b6881fe29bbd890bf1f9`. Treat the GitHub release tag as the later engineering reference and the Drive archive as historical evidence, never as production input.
4. Pandemonium’s code is GPLv3 and its non-code assets expressly prohibit incorporation into another project. `n64game` therefore uses a clean original implementation based on Tiny3D’s MIT-licensed examples and libdragon, with no Pandemonium code or assets copied.
5. Pokémon XD’s opening is useful as a pacing grammar: spectacle, identity, safe tutorial, home-base exploration, a personal errand, map travel, a humorous misunderstanding battle, reunion, and a larger threat. Verified footage shows that the literal first 20 minutes end just after the estate battle/reunion; the complete return and larger-system hook occur closer to minutes 25–30. `n64game` deliberately compresses that complete functional arc into an original 18–25 minute chapter. Its characters, creatures, language, layouts, scenes, dialogue, UI, audiovisual identity, and exact expression are out of scope.
6. The current Mac has Git LFS but does not yet have Docker, libdragon CLI, Ares, or Blender installed. Toolchain claims remain unproven until Gate 3 produces a clean ROM and CI artifact.

## 2. Pandemonium v0.71

### 2.1 Evidence snapshot

- Repository: [Boxingbruin/Pandemonium](https://github.com/Boxingbruin/Pandemonium)
- Release: [v0.71](https://github.com/Boxingbruin/Pandemonium/releases/tag/v0.71), published 2026-06-05
- Tag commit inspected: `d6578443ec1ca7634435b6881fe29bbd890bf1f9`
- Repository code license: GPLv3
- Release ROM: `pandemonium.z64`, 13,107,200 bytes
- Published ROM SHA-256: `bc42c98d0e1ed424858b0bf37a45e63963cbb952d12d7e3ac05249dced9b38c3`
- Release notes: no Expansion Pak required; fixes an opening-credits memory spike and a title-scene navigation leak
- Inspected source size: about 28,866 lines across C and header files
- Tracked file count: 321
- Inspected source asset count: 201 files; the checkout’s asset directory was roughly 392 MiB because it contains editable source material as well as runtime inputs
- Source-format breakdown includes 36 GLB, 90 PNG, 34 WAV, 19 `.blend`, 18 `.blend1`, one FBX, one MP4, one TTF, and one Audacity project
- README-claimed hardware support: NTSC and PAL N64; Ares is the recommended emulator in the shared info file

The release tag and repository version file are not synchronized: tag `v0.71` points at a tree whose `VERSION` file contains `0.667`. That is a release-engineering defect to avoid through CI/version checks.

These quantities are reference measurements, not a target to inflate. They demonstrate that finished presentation needs an asset-production pipeline and substantial integration code.

### 2.2 Game and presentation structure

The project is a focused boss-game opening rather than a general engine. Its README lists a character controller with multiple animation states, lock-on, collision-driven weapons, boss AI with many attacks, realtime and video cutscenes, distance-based SFX, weapon trails, feedback systems, dialogue, vertex-colored low-resolution textures, skinned meshes, and scrolling materials.

The current application flow is explicit:

`Opening Credits → Title → Guardian encounter`

The top-level loop in [`src/main.c`](https://github.com/Boxingbruin/Pandemonium/blob/v0.71/src/main.c) owns global initialization, input/time, a pre-render-pump video boundary, scene update/draw, menu composition, debug overlays, and display submission. [`scene_controller.c`](https://github.com/Boxingbruin/Pandemonium/blob/v0.71/src/controllers/scene_controller.c) switches between concrete scenes and calls matching enter/exit or cleanup functions.

Actionable lessons:

- Keep a small explicit scene state machine; do not let content transitions emerge from unrelated booleans.
- Make each scene own and unload its heavy resources.
- Pump any blocking/special display mode before attaching the normal frame render target.
- Separate update, fixed-step simulation, draw, UI overlay, and final submission.
- Keep debug/profile overlays optional but available from the start.

Do not copy the controller or scene code. Reproduce the ownership principles through original interfaces documented in the master specification.

### 2.3 Opening presentation, loading, and cutscenes

[`opening_credits_scene.c`](https://github.com/Boxingbruin/Pandemonium/blob/v0.71/src/scenes/opening_credits/opening_credits_scene.c) is a real state machine, not a static splash. It loads separate libdragon/Tiny3D logo assets, animates them over timed phases, plays a synchronized sound, supports A/Start skip, frees each phase’s sprites before loading the next, and waits for queued RSP work at scene exit.

There is not evidence of a universal, reusable “loading screen engine” in the inspected tag. The visible quality comes from authored opening/title transitions and scene-specific loading/cleanup. `n64game` should therefore build its loading presentation around genuine scene loading and explicit transitions rather than fake waiting.

Pandemonium uses both realtime cutscene code and an FMV path:

- Guardian phase cutscenes are split into dedicated source modules and use scene context plus a cutscene manager.
- [`fmv_controller.c`](https://github.com/Boxingbruin/Pandemonium/blob/v0.71/src/controllers/fmv_controller.c) queues playback outside the ordinary attached frame, stops game audio, registers the H.264 codec, renders YUV frames to the existing display, provides A/Start skip, and returns through a defined scene callback.
- The implementation intentionally uses zero extra buffered decode pictures by default and reuses the active display to avoid framebuffer/decode allocation spikes on real hardware.
- The Makefile converts MP4 to 320×240 H.264 at 24 fps and converts audio separately to WAV64.

The source MP4 is approximately 60.3 seconds at 720×480/29.97 fps before conversion. The separate source WAV is mono 22,050 Hz. Realtime Guardian cinematics combine explicit camera states, smoothstep interpolation, boss animation requests, letterboxing, dialogue, fades, particles, music, lightning, and cutscene-only model loading. This staging is effective, but cameras/timing/draw logic are hard-coded across large phase modules. The skip flow is also phase-specific, increasing the risk of incomplete cleanup.

Actionable lessons:

- The approved `INSERT CUTSCENE HERE` slate needs the same deterministic skip/state behavior as final playback.
- The future video must be integrated at a frame boundary with clear audio ownership and no hidden extra framebuffer allocation.
- Test watch, skip, end-of-stream, missing-audio, and repeated-play transitions.
- Do not implement the final video now; preserve a documented compatible handoff.
- Use timestamped original `CutsceneEvent` data and one idempotent finalizer shared by natural completion and skip; do not reproduce the reference phase state machines.

### 2.4 Asset pipeline and rendering

The [v0.71 Makefile](https://github.com/Boxingbruin/Pandemonium/blob/v0.71/Makefile) discovers source assets and builds a ROM filesystem. It converts:

- PNG → libdragon sprite
- TTF → font64
- GLB → Tiny3D model, then applies ROM compression
- WAV/XM → libdragon audio formats
- MP4 → H.264
- Binary data → packed filesystem content

Source `.blend`, `.psd`, logs, archives, and other editable/intermediate files are excluded from ROM conversion. Paths are preserved in the filesystem. Collision data has a separate Python conversion environment.

The game uses 320×240 output, three framebuffers, Tiny3D fixed-point matrices, cached display lists, skinned models/animations, vertex colors, small texture formats, RDPQ UI, and explicit RSP synchronization.

Actionable lessons:

- Keep editable Blender/audio/image sources separate from deterministic runtime conversion.
- Preserve asset path identity and validate every conversion error.
- Use compression intentionally; source-repository size is not ROM size.
- Build representative assets through the complete Blender → GLB → Tiny3D → ROM → Ares path before mass production.
- Allocate buffered matrices/viewports correctly; never mutate memory while the RSP may still consume it.

### 2.5 Character, boss, and battle staging

The largest code module is the character implementation (about 3,096 lines). The character state includes locomotion, rolls, multiple attacks, knockdown, death, health, stamina, potions, collision, animation blending, skeleton ownership, shadows, and hit tracking. The boss is divided across AI, animation, attacks, render, SFX, UI, and environmental-mechanics modules rather than one monolith.

Boss definitions distinguish AI state, attack identity, animation state, animation priority, runtime mode, intent, cooldowns, collision attachments, targeting, visual feedback, and phase-specific behavior. This separation makes authored camera/animation timing possible without allowing cutscenes and combat to fight over the same state.

Actionable lessons for `n64game`:

- Separate immutable creature/move definitions from battle runtime state.
- Separate battle decision logic from animation/camera/VFX presentation.
- Use explicit animation priorities and completion events rather than time guesses scattered across UI code.
- Track per-action hit application so one animation cannot apply damage repeatedly.
- Treat tutorial scripting as constraints on the same real battle state machine, not a second fake battle implementation.

### 2.6 Memory and lifecycle

The v0.71 release itself is evidence that transition memory is a high-risk area. It calls out an opening-credits memory spike and title navigation leak. The inspected source consistently uses explicit `sprite_free`, `t3d_model_free`, `free_uncached`, animation/skeleton destruction, display-list release, `rspq_wait`, and nulling after cleanup.

The code also contains comments acknowledging transitional global ownership and earlier lack of a general memory manager. That is a warning, not a pattern to inherit.

The audit found a likely remaining environment leak even at v0.71: `floorGlowModel`/display-list/matrix and `bossChainsGlowModel`/display-list/matrix are loaded and used but not released by the inspected environment/scene teardown. This does not negate the release fixes; it proves that a passing playthrough and “no Expansion Pak” claim are weaker than an allocation ledger plus repeated-transition soak.

Locked `n64game` responses:

- Scene-owned allocation records from the beginning.
- One clear owner for every model, matrix, display list, skeleton, animation, sprite, and audio handle.
- Transition-loop soak tests before final asset volume hides leaks.
- No display close/reinitialize cycle during the placeholder cinematic.
- Peak heap and contiguous-allocation risks measured, not inferred from total free bytes.

### 2.7 Collision, audio, UI, and save-system cautions

The repository contains a GLB collision exporter that looks for a node named `COLLISION`, classifies triangle faces, and emits text. The inspected Makefile prepares Python dependencies but does not actually wire that exporter into the ROM build. Runtime room collision instead relies on ten hard-coded oriented boxes and iterative capsule resolution. `n64game` must not mistake the existence of a tool for an integrated pipeline: collision export, validation, compact conversion, runtime loading, and post-export navigation tests all need build ownership.

Pandemonium’s audio controller uses 22,050 Hz output, 16 mixer channels, 14 dynamic SFX slots, and a scene-local cache of up to 64 WAV64 handles. Its UI includes bespoke panels/fonts, dialogue typing controls, menus, letterboxing, health/stamina, button sprites, persisted overscan settings, and CRT-safe debugging. The lesson is cumulative presentation: camera, animation, typography, prompt timing, sound, transitions, and VFX create perceived finish together.

The EEPROM4K save layer uses EEPROMFS, three slots, checksums, validation, and debounced settings writes. However, it serializes native C layout/padding, wipes/reseeds on version mismatch, and lacks explicit migration or a dual-record power-loss journal. `n64game` will use fixed-width byte serialization with explicit offsets, version migration, per-slot recovery, and transition-safe snapshots rather than copying this representation.

### 2.8 License boundary

Pandemonium’s code is GPLv3. Its [`LICENSE_ASSETS`](https://github.com/Boxingbruin/Pandemonium/blob/v0.71/LICENSE_ASSETS) says non-code assets may be downloaded, viewed, and used to build/preserve Pandemonium, and that the unmodified project may be redistributed with the license. It explicitly denies permission to reuse, modify, extract, redistribute separately, or incorporate those assets into another project.

Therefore:

- No Pandemonium code enters this MIT repository.
- No Pandemonium asset, derivative texture, traced model, animation data, audio sample, UI element, logo, or extracted frame enters production.
- Reference screenshots may guide density and review standards but are not committed as project assets.
- Similar technical problems must be solved independently from Tiny3D/libdragon documentation and original code.

## 3. Shared Drive snapshot

The connected Drive folder currently contains three direct items:

| File | ID | Size | Meaning |
|---|---|---:|---|
| `INFO.txt` | `1eLKI7KPcvGAwbKsrNktqEq9A08SNeAhr` | 211 bytes | Team, hardware, emulator, and source note |
| `pandemonium.z64` | `1PXCbjDiIoKTTOEV6ojsJ6eMI4avaTnbw` | 21,807,104 bytes | Older submitted ROM |
| `Pandemonium-source.zip` | `1Uvn6TQ6NFgckkKFAvz8lppnMBJ-jTzDQ` | 193,412,989 bytes | Older source snapshot |

`INFO.txt` identifies Team Zero Cool (BoxingBruin and HelloNewman), states NTSC/PAL N64 testing, recommends Ares 147, and points back to the GitHub repository.

The source archive identifies commit `dfe02a3014763e01303e418d0fe2219bad4ef070` from 2026-02-02. Its inspected source has roughly 17,486 C/header lines and 172 assets. Comparing it with v0.71 shows substantial later restructuring and feature/polish work—approximately 95 source files affected with about 18,807 insertions and 7,394 deletions in a direct tree comparison. The release ROM also became smaller despite the later codebase.

This means the Drive archive is valuable evidence of iteration, not the preferred base and not licensed input. Nothing from the archive enters `n64game`.

## 4. Tiny3D

### 4.1 Evidence snapshot

- Repository: [HailToDodongo/tiny3d](https://github.com/HailToDodongo/tiny3d)
- License: MIT
- Current inspected main commit: `e84172f29f719680ac3213a7f408c2f721ef7b24`
- Purpose: custom N64 3D microcode and C API for libdragon preview
- Inspected core source size: approximately 7,075 lines across C/header/RSPL files
- Example set: basic geometry/model loading through animation, lighting, culling, particles, mipmaps, fresnel, large textures, HDR/bloom experiments, and a test scene

Tiny3D provides a 3D pipeline, matrices, directional/ambient/point lighting, normals and vertex color, culling/BVH support, skinned meshes, animation blending/streaming, GLTF import, Fast64 material support, texture loading in the model format, and RDPQ interoperation.

It is the renderer/tool layer, not a game engine. It does not provide our scene controller, battle system, collision/gameplay rules, quest/dialogue logic, saves, production art, cinematic direction, or quality gates.

### 4.2 Critical usage constraints

From the [Tiny3D README](https://github.com/HailToDodongo/tiny3d/blob/main/README.md) and examples:

- Tiny3D requires libdragon `preview`.
- The recommended starting point is a small example rather than an unrelated full game.
- A pinned local copy/submodule can prevent upstream changes from silently breaking the project.
- Matrices and vertices are DMA’d into the RSP and must remain valid while consumed.
- Uncached allocations or explicit cache management are required for RSP-visible data.
- Buffered viewport/matrix data is necessary when multiple frames may be in flight.
- Tiny3D has no generic modern material abstraction; RDP/Tiny3D constraints still matter.
- UVs use pixel-coordinate fixed-point conventions rather than normalized modern-engine assumptions.
- The built-in model format and GLTF importer should be preferred over an invented format unless profiling proves otherwise.
- Fast64 material metadata and custom properties are important. Tiny3D warns that vanilla Blender GLTF exports after 4.0 may be broken for this workflow; the newest compatible Fast64 exporter is preferred.

Locked response: integrate a pinned Tiny3D checkout and validate one representative humanoid, creature, environment, animation, material, and texture through the real importer before scaling production.

## 5. libdragon, Docker, Ares, Blender, and CI

### 5.1 Current pins and environment

- libdragon preview pin: `f13b48985edbf4310f07779c76d9a68c7605037b`
- Tiny3D pin: `e84172f29f719680ac3213a7f408c2f721ef7b24`
- libdragon CLI package target: `12.2.1`
- libdragon CLI tag commit: `f8a16abc81263781cf684602bcea98a1d096fd2d`
- immutable libdragon preview container index: `ghcr.io/dragonminded/libdragon@sha256:36a295cbe43168e8adbfa5c86d956df3dc762a1ab6fda1b50dcb33bd78dc2d83`
- Ares target: 148
- Ares tag commit: `0aafd85789215e84e1e43415c07d4c88461b7899`
- Fast64 target: 2.5.3, commit `8e9630c11824a9c00e9379279d43c64264eda87e`
- Blender target: 4.5.11 LTS; do not use current Blender 5.2 because it exceeds Fast64’s declared maximum of 5.0.1
- Host: Apple Silicon (`arm64`) macOS 26.5.2
- Free disk observed at audit: approximately 148 GiB, with the volume already 92% used
- Available now: Git LFS 3.7.1
- Missing now: Docker CLI/Desktop, libdragon CLI, Ares executable, Blender executable

The [libdragon installation documentation](https://github.com/DragonMinded/libdragon/wiki/Installing-libdragon) recommends its Docker-backed CLI for macOS x86/ARM. The Docker path installs the CLI, initializes a skeleton/toolchain image, checks out libdragon, optionally switches it to `preview`, installs it, and builds with `libdragon make`.

The [libdragon README](https://github.com/DragonMinded/libdragon/blob/preview/README.md) recommends modern accuracy-focused emulators, specifically Ares and Gopher64, and describes Ares Homebrew Mode as the development-oriented option. It also warns that preview APIs can change.

### 5.2 Gate 3 setup plan to verify

Do not mark these commands successful until they have actually run:

1. Install and launch Docker Desktop; verify `docker system info`.
2. Add exact `libdragon@12.2.1` as a development dependency so `package-lock.json` pins the CLI.
3. Bootstrap the dependency/container configuration without overwriting this repository, using the immutable preview image digest.
4. Checkout the exact libdragon preview pin inside the managed dependency and install it.
5. Add Tiny3D at the exact pin, build/install its library and GLTF importer, and verify the simplest model example.
6. Install Ares 148 and enable Homebrew Mode.
7. Install Blender 4.5.11 LTS and Fast64 2.5.3; save versioned `.blend` files frequently and validate the exporter/importer path before production.
8. Build a minimal `N64GAME` ROM locally from a clean tree, launch it in Ares, then reproduce the same build in GitHub Actions.

CI must use the same pinned scripts/container path as local development. It must not depend on undocumented state in a developer’s global install. Artifacts must include ROM, SHA-256, size/header report, and a dependency/build manifest.

### 5.3 Risks

- libdragon preview and Tiny3D main can drift independently; exact commits may not be mutually compatible despite both being current.
- Docker and asset sources will consume significant disk on an already 92%-used volume; monitor before large image/source generation.
- The current preview container is `linux/amd64`, not native `linux/arm64`; Docker Desktop will emulate it on this Apple Silicon Mac and local builds may be slower than amd64 CI.
- A successful compiler build does not validate GLB/Fast64 materials, skeletons, or animations.
- Ares boot does not prove real-hardware behavior.
- Apple Silicon support exists for the Docker route, but host GUI tools and CLI PATH still need verification.
- Fast64 is GPLv3 tooling and should remain an external authoring dependency rather than copied into the MIT codebase.

## 6. Pokémon XD opening study and clean-room mapping

### 6.1 Verified footage timeline

The strongest timing reference is [Ninbunchan’s no-commentary opening](https://www.youtube.com/watch?v=furbAaoFEK4). Its first 2:10 is an attract/demo reel rather than opening-story content. Absolute capture times:

| Capture time | Function |
|---|---|
| 2:10–2:35 | Title, new game, and name selection |
| 2:40–3:35 | Vessel-abduction cold open |
| 3:45–4:30 | High-power 1v1 battle simulation |
| 4:30–5:05 | Simulation reveal |
| 5:05–7:50 | First control and home-base assignment |
| 7:50–13:20 | Lab exploration, optional exposition, menus, devices, items |
| 13:20–15:10 | Handheld retrieval and clue-giver search |
| 15:10–16:30 | Optional news echo reconnecting the vessel mystery |
| 16:30–17:30 | Exit, map, travel, and estate establishment |
| 17:30–18:20 | Mistaken-identity confrontation |
| 18:20–19:05 | First real 1v1 battle |
| 19:05–20:10 | Apology and sibling reveal outside the estate |

The interior invention presentation, sibling conversation, return trip, objective resolution, new equipment/corruption-system briefing, and hostile interruption continue from roughly 20:10 through 29:40. Thus our locked chapter is not a shot-for-shot “first 20 minutes” copy. It is the complete functional opening compressed into 18–25 minutes with deeper original 2v2 battles and a resolved personal objective.

XD places name selection before the story cinematic. The locked `n64game` sequence places the approved cinematic slot before name entry. That difference is intentional and must not be “corrected” to imitate the reference.

### 6.2 Functional order

Walkthrough sources consistently describe this early flow:

1. A cinematic shows the S.S. Libra being taken by a dark legendary creature and an organized hostile group.
2. The player chooses a name.
3. The game begins in a deliberately overpowered one-versus-one battle.
4. The battle is revealed as a simulation; the player’s real starter is much weaker.
5. The player explores Pokémon HQ Lab, speaks with family/researchers, receives a missing-sibling objective, retrieves a handheld device, and finds a clue.
6. A world-map destination unlocks.
7. At Kaminko’s House, an eccentric assistant mistakes the player for a burglar and starts an easy real battle.
8. The player enters the house, sees strange inventions, finds the sibling with the inventor, and returns toward the lab.

Sources:

- [StrategyWiki: Pokémon Lab Headquarters](https://strategywiki.org/wiki/Pok%C3%A9mon_XD%3A_Gale_of_Darkness/Pok%C3%A9mon_Lab_Headquarters)
- [StrategyWiki: Kaminko’s House](https://strategywiki.org/wiki/Pok%C3%A9mon_XD%3A_Gale_of_Darkness/Kaminko%27s_House)
- [Bulbapedia walkthrough Part 1](https://bulbapedia.bulbagarden.net/wiki/Appendix%3APok%C3%A9mon_XD_walkthrough/Section_1)
- [Serebii XD walkthrough opening](https://www.serebii.net/xd/walkthrough/01.shtml)
- [First 15 Minutes gameplay reference](https://www.youtube.com/watch?v=6aJeKacWD3c)

The exact wall-clock point reached at 20 minutes varies with naming, exploration, reading speed, and battle decisions. `n64game` therefore preserves the functional arc and certifies its own runtime through three measured playthroughs rather than claiming an exact frame-for-frame 20-minute correspondence.

### 6.3 Locked original mapping

| Reference function | N64GAME expression | Protected elements explicitly excluded |
|---|---|---|
| Threat spectacle before player control | Severance intercepts the original Solace carrier using a colossal Fractured Echoform | S.S. Libra, Shadow Lugia, Cipher, helicopters, shot recreation |
| Name ownership | 1–8 character original UI, default `ARI` | Pokémon name screen graphics, sounds, fonts, wording |
| Safe high-power tutorial | Original 2v2 simulation with four loaned Echoforms and Resonance finisher | Salamence/Metagross, Pokémon moves/types, exact arena/cameras |
| Reveal of ordinary life | Simulation dissolves into Meridian Research Annex and the real starter duo | Michael, Eevee, Pokémon Lab layout/dialogue |
| Home-base onboarding | Retrieve Field Relay, explore two-level Annex, learn party/save/map | P★DA, exact rooms/NPC roles/placement |
| Personal errand | Tavi is missing after an original Annex errand/hide-and-seek setup | Jovi, copied jokes or dialogue |
| Map unlock and travel | Original illustrated desert node map and travel/loading animation | Orre map art, icons, music, node layout |
| Misunderstanding battle | Rusk mistakes the player for a Severance scout and fights with an original 2v2 team | Chobin, Sunkern, costume/body language, exact gag |
| Eccentric second location | Veyra Observatory Estate with authored kinetic inventions | Kaminko house geometry, Groudon statue, inventions, dialogue |
| Reunion and larger hook | Find Tavi with Ivo; return to Annex; receive Solace beacon/Fracture signal | Snag Machine, Shadow Pokémon terminology, later kidnapping scene |

### 6.4 Camera and pacing lessons

- Lead with a concise unanswered image, then give control quickly.
- Teach complicated battle UI in a consequence-free fictionally justified simulation.
- Follow spectacle with a quieter home space that teaches movement, interaction, party, and save systems.
- Use a small personal objective to motivate exploration before expanding the world conflict.
- Make the second location visually and tonally distinct from the first.
- Let the first real battle validate the player’s actual team and retry loop.
- End the included arc with its personal objective resolved and a new external question, not an arbitrary cutoff.
- Optional interactions should add texture and runtime; mandatory dialogue must remain concise.
- Exploration cameras should make each room read immediately through landmark silhouettes and clear destinations; battle cameras should return to a stable tactical three-quarter view between authored attack/impact/reaction cuts.
- The cold open may reuse an escalation curve—calm wide, operational medium, distant threat, creature reveal, energetic close-up, catastrophe wide, silence—but must use independently designed shots, vehicles, creature motion, setting, and edit timing.

## 7. Clean-room implementation rules

Before any production source or asset is accepted:

1. Identify whether it was created from original design requirements, permissively licensed technical documentation/examples, or a third-party source.
2. Record source, prompt, creator, transformations, and license in `docs/ASSET_LEDGER.md` for non-code content.
3. Reject anything based on extracted reference assets or close tracing.
4. Keep reference downloads in ignored temporary directories outside the repository.
5. Review creature silhouettes, character costumes, UI composition, environment layouts, terminology, and music against the exclusion list.
6. Keep code review focused on our documented architecture and public Tiny3D/libdragon APIs, not Pandemonium source similarity.
7. Preserve exact third-party notices for anything actually integrated.

## 8. Production decisions derived from the study

- Start from a minimal Tiny3D/libdragon project, never a Pandemonium fork.
- Keep dependencies pinned locally and in CI.
- Prove the complete model/material/skeleton/animation conversion path before mass art production.
- Build explicit scene resource ownership and transition instrumentation before scenes become asset-heavy.
- Treat opening/loading presentation as a real scene with deterministic skip and cleanup.
- Use one genuine battle state machine for the tutorial and estate battle.
- Separate battle simulation from camera/animation/VFX playback.
- Keep source assets in Git LFS and generated runtime conversions reproducible.
- Require authored concepts, turntables, animation reviews, native-resolution in-engine reviews, and at least two polish passes for hero assets.
- Measure runtime, memory, and frame time; do not infer them from visual smoothness or file counts.
- Do not claim real-hardware, PAL, or NTSC certification until those specific tests occur.

Gate 1 is complete only when this study, licenses/notices, repository hygiene scan, and public commit are all verified together.
