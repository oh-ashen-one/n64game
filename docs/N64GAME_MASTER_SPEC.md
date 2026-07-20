# N64GAME One-Week Master Production Prompt

This document is the authoritative execution contract for `n64game`. It remains intentionally more detailed than the short `/goal` launcher. Read it completely before planning, coding, generating assets, evaluating completion, or delegating work.

Revision authority: on 2026-07-19 the user explicitly asked to shrink the project so a finished release could be delivered within the remaining one-week usage window. This revision replaces the former 18–25 minute, two-location, two-battle opening. Where older preproduction documents describe that larger plan, this document wins. Preserve useful compatible work, but do not spend the one-week window implementing or mechanically rewriting out-of-scope content.

## 1. Mission and Definition of Done

Create a polished, original-IP Nintendo 64 game with a genuine 6–8 minute first-time playthrough. The result is a complete small opening chapter: one finished explorable destination, one complete 2v2 battle, a resolved immediate objective, and a strong corruption-related hook. It must feel authored and release-ready, not like a greybox, disconnected systems demo, asset test, or 20%-finished larger game.

The public repository is:

- GitHub: `https://github.com/oh-ashen-one/n64game`
- Local checkout: `/Users/midir/Documents/New project 8`
- Default branch: `main`
- Visibility: public

The release must run as an N64 ROM in Ares 148 Homebrew Mode and include a polished boot/loading presentation, the approved `INSERT CUTSCENE HERE` slot, 1–8 character name entry, analog exploration, dialogue, one complete 2v2 Resonance battle, defeat/retry, save/load, a stable ending, and the user-facing GPT Image storyboard package.

Scope is reduced by cutting breadth, never finish quality. This release does **not** include Veyra Observatory Estate, a world map, Rusk/Ivo, a second battle, a companion-follow system, an elevator network, or the old missing-person round trip. Do not leave doors, menus, dialogue, or UI that falsely promise those systems. They may be future work only after this release is complete.

## 2. Authoritative References and Clean-Room Boundary

The engineering and presentation references remain:

1. Pandemonium v0.71: `https://github.com/Boxingbruin/Pandemonium/releases/tag/v0.71`
2. Shared Pandemonium Drive folder: `https://drive.google.com/drive/folders/1C1MZRS5iU9Pia12RhdLhsx9giqJ6z4TF`
3. Tiny3D: `https://github.com/HailToDodongo/tiny3d`
4. The opening rhythm of Pokémon XD: Gale of Darkness, used only to study pacing and presentation.

Use recorded findings in `docs/reference-study.md`. Do not repeat broad research unless a concrete implementation question requires it.

These are references, not content sources:

- Implement original code on libdragon/Tiny3D. Do not copy or translate Pandemonium GPL code into this MIT project.
- Do not reuse Pandemonium or Pokémon art, models, textures, animation, audio, writing, names, layouts, UI, story expression, or branded mechanics.
- Keep downloaded reference material outside the public repository.
- Record provenance and rights for every released asset.
- All characters, Echoforms, locations, factions, props, dialogue, and audiovisual expression must be original.

## 3. Locked Creative Direction

Working ROM title: `N64GAME`.

Art direction: authored late-1990s/early-2000s console RPG presentation in a retro desert-science-fiction world. Use sun-bleached ceramic, ochre dust, oxidized metal, dark teal machinery, warm practical lights, cobalt shadows, and controlled magenta-violet Fracture accents. Environments should combine analog research equipment, cloth shade, antennae, layered ceramic panels, readable signage icons, and purposeful wear.

World vocabulary:

- Creatures: **Echoforms**
- Cooperative trainer/team energy: **Resonance**
- Corrupted Echoforms: **Fractured**
- Playable location: **Meridian Research Annex**
- Hostile organization: **the Severance**
- Research carrier: **Solace**
- Default protagonist name: `ARI`
- Research guardian: **Dr. Sera Venn**
- Younger Annex resident: **Tavi**

The cinematic premise remains: Severance gliders intercept Solace over the desert at dusk while a colossal Fractured Echoform bends light and gravity. Solace disappears into a violet storm and one emergency beacon falls toward the wastes. Do not create the final video in this goal. Reserve its exact playback point and provide a coherent storyboard for the user’s later AI-video animation.

## 4. Locked 6–8 Minute Experience

Measure from cold boot to the stable end screen. The temporary slate counts for at most five seconds. A normal first-time playthrough must take 6–8 minutes excluding idle time, with at least four minutes of player control. Dialogue may not pad runtime.

### Segment A — Boot, Loading, and Cinematic Slot (0:00–0:25)

- Show an original studio/game mark and branded loading treatment that hides only real work.
- Fade to a polished 4:3 slate reading exactly `INSERT CUTSCENE HERE`.
- Hold for three seconds or allow A/Start to skip immediately.
- Watched and skipped paths set the same `opening_cinematic_seen` flag and reach name entry safely.
- The slate is the only intentionally temporary visual allowed in the accepted ROM.

### Segment B — Name Entry and Annex Arrival (0:25–1:20)

- Provide a final-styled 1–8 uppercase character name interface with default `ARI`, backspace, confirmation, and cancel protection.
- Transition into the Meridian Research Annex with a short authored camera reveal.
- Dr. Sera Venn welcomes `{PLAYER}` and identifies Tavi at the observation rail.
- Quarrune and Ayselor are introduced in-world as the player’s real team; they are not granted through a debug menu.

### Segment C — Focused Annex Exploration (1:20–3:00)

- Give the player free control through one coherent, finished Annex environment containing a simulation chamber, central research atrium, compact workshop/relay station, and exterior beacon overlook. These may be connected sectors of one scene.
- Support analog walk/run, stable camera, collision, two concise required conversations, at least four optional examine points, pause, party view, control help, and save.
- The immediate objective is to retrieve and calibrate the **Field Relay**. It exposes Party, Messages, Resonance, and Save; it does not expose a disabled world map.
- Tavi and Sera use staged idle/talk/reaction animation. Navigation must remain clear without invisible corridors or intrusive quest arrows.
- Activating the calibrated relay opens the simulation chamber and starts the required battle.

### Segment D — Complete 2v2 Resonance Battle (3:00–6:20)

- Use the persistent player pair Quarrune and Ayselor against simulation opponents Gyreclast and Kivarrax. These are the only four required battle-capable Echoforms for this release.
- Establish all four actors with a short camera fly-in and readable battle staging.
- Teach command selection, legal targets, move information, speed order, HP, affinity feedback, partner support, Resonance gain, and the `Horizon Break` duo finisher while retaining reasonable player agency.
- Each Echoform has four data-driven moves. The player can win through multiple legal strategies; enemy AI chooses understandable legal actions and demonstrates one support interaction.
- Include intro, command/target selection, queue construction, animation/VFX/audio presentation, damage/status resolution, knockout, victory/defeat, and exit.
- Defeat restores a pre-battle snapshot and offers Retry or Return to Annex. Retrying never duplicates rewards or flags. The tutorial may gently bias the encounter but may not fake unearned inputs or silently prevent legal choices.
- Victory applies progression once, restores a sensible post-battle state, and returns control to the Annex.

### Segment E — Beacon Hook and Stable Ending (6:20–8:00)

- The calibrated Field Relay receives the Solace emergency-beacon signature.
- Sera, Tavi, the player, Quarrune, and Ayselor stage a concise reaction at the exterior overlook or Resonance monitor.
- A violet Fracture pulse briefly interrupts the Annex instruments; do not reveal an unfinished creature model in gameplay.
- Save the completed state, display an authored `END OF OPENING CHAPTER` treatment, and return to a stable title/post-chapter menu.
- The immediate objective—calibrate the relay and complete the Resonance trial—is resolved. The Solace beacon is the future-story hook, not a broken doorway.

Two first-playthrough-style certification runs must each fall between 6 and 10 minutes, with a median between 6 and 8 minutes.

## 5. Gameplay and Data Contract

### Exploration

Implement analog movement, acceleration/deceleration, authored idle/walk/run animation, stable follow camera, safe camera clamping/collision, world collision, appropriate slopes/steps, interaction prompts, dialogue, examine points, pause/resume, controller reconnect handling, and honest loading transitions.

The player must not become trapped behind props, leave collision, lose control after dialogue, trigger one-shot scenes twice, or save a half-applied transition. Required interaction targets need strong visual composition and readable prompts at 320×240.

### Battle

Use a deterministic state machine with intro, command selection, target selection, turn queue, presentation, damage/status resolution, round cleanup, victory/defeat, and exit.

Required mechanics:

- Two active Echoforms per side and no reserve slots.
- Four moves per creature, including damage and support/debuff choices with differentiated target rules.
- Speed order with stable tie-breaking and legal-target recovery.
- HP, damage, simple affinities, one temporary status family, knockout, and battle-end detection.
- Enemy AI that scores legal moves/targets without hidden information.
- Shared Resonance earned by complementary play.
- `Horizon Break`, requiring both allies conscious and full Resonance, with bespoke camera, animation, VFX, and audio.
- Complete synchronization between logic, animation, VFX, UI, and audio.

Definitions for Echoforms, moves, encounter, dialogue, and flags must be data-driven. Scene code may not scatter asset filenames or story constants.

### Save Data

Use EEPROM4K with a versioned checksummed schema containing name, settings, Annex checkpoint, party composition/HP/progression, Relay unlock, battle result/reward state, cinematic flag, and slice-complete flag. Invalid/incompatible data falls back safely to New Game. Debounce writes.

Test slate skipping, battle defeat/retry, save/reboot/resume, controller disconnect, invalid saves, repeated interactions, and re-entering the completed state.

## 6. Technical Architecture

Use the existing pinned foundation:

- libdragon preview `f13b48985edbf4310f07779c76d9a68c7605037b`
- Tiny3D `e84172f29f719680ac3213a7f408c2f721ef7b24`
- libdragon CLI `12.2.1`
- Ares 148 Homebrew Mode certification target

Targets:

- Standard 4 MB N64; no Expansion Pak requirement.
- 320×240, 16-bit color, triple buffering.
- 30 FPS target with no sustained approved sequence below budget.
- EEPROM4K saves.
- ROM below 16 MiB; 32 MiB hard ceiling only with evidence.
- At least 512 KiB free heap at measured peak.
- No persistent heap reduction across ten complete title/Annex/battle transition loops.

Use explicit scene lifecycle ownership (`enter`, `update`, `fixed_update`, `draw`, `exit`). Scene-owned models, matrices, blocks, skeletons, sprites, and audio must synchronize and release safely. Preserve the reviewed Quarrune CI8 split-upload/TLUT/runtime-lifetime contract.

Stable data interfaces include `GameScene`, `GameState`, `CutsceneEvent`, `CreatureDef`, `MoveDef`, `BattleActor`, `BattleState`, `DialogueNode`, and fixed-width `SaveData` without runtime pointers.

Provide reproducible Docker/libdragon scripts, clean ROM builds, asset validation, Ares launch, checksums, and public CI artifacts. Never commit ROMs or build directories to ordinary Git. Use Git LFS only for appropriate editable binary sources and keep runtime outputs reproducible.

## 7. Art Direction and Anti-Slop Contract

Visual quality remains non-negotiable. The game should resemble an actual carefully authored console release in composition, density, animation, lighting, and presentation. “N64 low-poly” is not permission for crude primitives, generic generated characters, default materials, flat lighting, empty rooms, stiff animation, noisy AI textures, or unfinished UI.

`docs/ART_BIBLE.md` remains the style authority where compatible with this reduced roster. Existing full-game rows outside the release inventory are future reference, not release obligations.

Every production model requires an original readable silhouette, purposeful topology, clean normals, deliberate UVs, consistent texel density, authored vertex colors/materials, correct scale, meaningful naming, efficient rigging where needed, and no visible generation defects. Optimize for N64 limits without destroying the design.

Suggested visible budgets remain approximately 700–1,200 triangles for hero humanoids, 700–1,500 for battle Echoforms, and 20–400 for ordinary props. Primarily use 32×32 and 64×64 textures, split only when a visual benchmark proves the need. Use vertex colors for form and material richness.

### Reduced Release Inventory

Produce and track only what the release needs:

- One player model with exploration, dialogue, command, reaction, and ending coverage.
- Dr. Sera Venn and Tavi with authored idle, talk, gesture, reaction, and scene performances.
- Four polished battle-capable Echoforms: Quarrune, Ayselor, Gyreclast, and Kivarrax.
- One coherent Meridian Annex environment with four connected functional sectors: simulation chamber, atrium, relay workshop, and exterior overlook.
- At least twelve purposeful props distributed for composition, navigation, and storytelling.
- Complete title/loading, name-entry, dialogue, pause, party, Field Relay, battle, save, result, and end-chapter UI.
- VFX/audio for all implemented moves, Resonance, `Horizon Break`, Annex ambience, dust, loading/transitions, beacon hook, and feedback.
- Portraits/icons required by the selected UI direction.

Do not build the old Estate, world map, extra four Echoforms, Rusk/Ivo/Oren/supporting cast, follower system, or their assets during this release.

Minimum humanoid animation: idle variations, walk/run for the player, direction handling, interaction, talk gestures, reaction, battle command where applicable, and locked story poses.

Minimum Echoform animation: idle variations, entrance, reposition, at least two move performances, support, hit, knockout, victory, and duo-finisher participation where applicable. Reuse is allowed only when anatomically and directionally intentional.

### Asset Quality Gates

Keep the established seven-gate pipeline because its infrastructure already exists; reduce asset count instead of weakening quality:

1. Concept/orthographic and palette review.
2. Blender topology, normals, UV, scale, rig, and deformation review.
3. Textured turntable review.
4. Animation timing/clipping/weight review.
5. Tiny3D conversion review with no unexplained warning.
6. In-engine 320×240 camera, lighting, memory, and performance review.
7. Final consistency review after integration.

Hero assets require two deliberate post-integration polish passes. Reviews may be batched into evidence packets and need not be redundantly repeated after an unchanged passing artifact. Raw image-generation output is never shipped uncritically. Correct anatomy, identity drift, malformed geometry, fake text, perspective errors, palette drift, and baked-lighting mistakes before production use.

Maintain `docs/ASSET_LEDGER.md` and review evidence. Remove every placeholder before acceptance except the approved cutscene slate.

## 8. Storyboard and Future Cutscene Handoff

The opening storyboard remains a required direct user deliverable. Generate it with GPT Image after the continuity designs are stable.

Create:

- Twelve numbered high-resolution 4:3 panels, minimum 1600×1200.
- Individual panel files in story order.
- One high-resolution numbered contact sheet.
- `storyboard/opening/SHOT_LIST.md`.
- One continuity sheet covering Solace, Severance figures, gliders, the colossal Fractured Echoform, beacon, and desert sky.
- One concise warm-dusk-to-violet-storm-to-cool-interface color script.

The twelve panels must form one animatable 45–60 second sequence establishing Solace, desert scale, interception, restraint lines, Fracture distortion, crew danger, the falling beacon, and transition into name entry. They cannot be unrelated illustrations.

Each shot-list row specifies duration, framing/lens, camera height/movement, blocking/action, performance, lighting/color/atmosphere, transition, audio intent, and CRT-safe 4:3 notes. Document the future ROM asset path, audio pairing, playback callback, skip behavior, and state handoff that replace the temporary slate.

Visually inspect every panel. Regenerate or edit identity changes, malformed forms, incoherent action, unreadable staging, fake text, vehicle redesign, palette drift, and wrong aspect ratio. Deliver actual final image files to the user, not prompts alone.

## 9. Audio, UI, Loading, and Presentation

Create a cohesive original audio identity with N64-appropriate mono sources, normally around 22 kHz where suitable. Required cue families: boot/loading, Annex exploration, battle, victory/beacon hook. Required SFX include UI, footsteps, Relay, machinery, Echoform vocals, all moves, impacts, Resonance, finisher, battle transitions, save, and Fracture pulse.

Loading screens must be branded, attractive, and honest; never expose a raw framebuffer, debug text, frozen prior frame, or fake long wait.

All UI must remain readable at 320×240 within CRT-safe 4:3 margins. Test the longest eight-character name, low HP, status icons, 2v2 targeting, dialogue wrapping, button prompts, pause/resume, and color contrast. Avoid tiny desktop typography.

## 10. Repository, Licensing, and Public Hygiene

Keep `README.md`, MIT `LICENSE` for original code, `ASSET_LICENSE.md` for protected project content, `THIRD_PARTY_NOTICES.md`, this master prompt, the sub-4000-character goal prompt, art bible, asset ledger, build documentation, and release evidence current.

Never commit credentials, browser data, downloaded reference media, extracted commercial assets, Pandemonium assets, unlicensed fonts, or ambiguous media. Run secret, license, and large-file checks before public pushes. Public visibility does not place original art/audio under MIT.

## 11. Ordered One-Week Production Gates

Work in this order and stop expanding scope:

1. **Scope reconciliation:** record this reduction and map only retained story/data/assets to the release.
2. **Visual benchmark completion:** finish the existing Annex/player/Quarrune/Ayselor/Gyreclast/Kivarrax representative set and approve real 320×240 presentation.
3. **Playable spine:** implement cold boot through stable ending with final state flow, battle logic, save/retry, timing, and tracked temporary content.
4. **Production replacement:** replace every temporary retained-scope asset through the seven gates; do not create cut content.
5. **Presentation and storyboard:** finish UI, loading, audio, VFX, animation, camera staging, environment dressing, and the twelve-panel package.
6. **Certification and release:** run performance, soak, timing, save/retry, visual, license, fresh-build, and public-CI checks; publish verified artifacts and direct storyboard files.

Do not redo passed infrastructure work without a demonstrated defect. Prefer one evidence-backed implementation pass plus focused fixes. Compilation alone is never completion.

## 12. Test and Evidence Matrix

Automate battle order, legal targets, damage/status, Resonance, rewards, story flags, save checksum/version, invalid-save fallback, deterministic AI, and progression idempotence.

Ares certification covers:

- Cold boot; default and custom names.
- Slate watched and skipped.
- Required/optional Annex interactions.
- Save, quit/reboot, and resume at supported checkpoints.
- Battle legal alternate inputs, victory, defeat, retry, and Return to Annex.
- Duo-finisher legal and illegal states.
- Dialogue skipping and rapid confirm/cancel.
- Controller disconnect/reconnect during exploration, menus, dialogue, and battle.
- Corrupted EEPROM data.
- Re-entering completed sectors and repeating completed interactions.
- Full hook and stable post-chapter state.

Performance evidence includes busy exploration/battle frame timing, peak heap, ROM/map size, and ten repeated transition loops with no persistent memory loss. Run two first-playthrough timing passes; each is 6–10 minutes and their median is 6–8 minutes.

Visual evidence includes every Annex sector, the battle, every major UI surface, loading, hero turntables/animation captures, and storyboard contact sheet, inspected both at native 320×240 and nearest-neighbor enlargement.

## 13. Final Acceptance Checklist

Do not mark the goal complete until all are verified:

- The public repository exists and a fresh clone builds reproducibly.
- CI produces a structurally valid `.z64`, checksum, size/map evidence, and build report.
- The complete 6–8 minute chapter runs from cold boot to the stable beacon hook.
- Two timed runs satisfy the locked range with real player agency.
- Name entry, Annex exploration, Field Relay, one full 2v2 battle, victory/defeat/retry, save/reload, dialogue, transitions, and flags work.
- Ten transition loops show no persistent memory growth; peak free heap is at least 512 KiB.
- Required scenes meet the evidence-backed 30 FPS target.
- There are no crashes, softlocks, collision traps, missing assets, broken audio, unreadable required UI, progression blockers, duplicate rewards, or corrupt transitions.
- Every retained production asset has provenance, passed seven art gates, and looks finished at the actual gameplay camera.
- No primitive, default material, raw generated texture, temporary animation, unfinished environment, or gameplay-affecting TODO remains, except `INSERT CUTSCENE HERE`.
- Twelve storyboard panels, individual files, contact sheet, continuity sheet, color script, and shot list are visually reviewed and delivered directly to the user.
- Code/asset licensing, third-party notices, secret scan, and public hygiene pass.
- Emulator-only claims are labeled honestly; real N64 hardware is not claimed without testing.

## 14. Agent Operating Rules

- Pursue the reduced complete outcome autonomously and persistently.
- Cut content breadth, never visual or functional finish.
- Do not re-expand toward the superseded 20-minute plan during the one-week release.
- Reuse compatible validated infrastructure and the four-Echoform benchmark set.
- Avoid broad repeated research, speculative systems, duplicate reviews of unchanged passing artifacts, and documentation churn unrelated to release.
- Prefer verified ROMs, captures, tests, and public state over status claims.
- Preserve user work; use isolated branches where needed.
- Surface true blockers early, but exhaust safe focused alternatives first.
- Do not claim completion from file count, percentage, compilation, or one successful screen. Completion means every reduced Final Acceptance item above is proven.
