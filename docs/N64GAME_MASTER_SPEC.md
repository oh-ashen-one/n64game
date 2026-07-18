# N64GAME Master Production Prompt

This document is the authoritative execution contract for `n64game`. It is intentionally comprehensive. Any short goal prompt, chat message, task description, or progress summary is subordinate to this file unless the user explicitly changes a requirement. Read this document completely before planning, coding, generating assets, evaluating completion, or delegating work.

## 1. Mission and Definition of Done

Create a polished, original-IP Nintendo 64 game with a genuine 18–25 minute first-time playthrough. The result must feel like a small finished commercial-quality game opening, not a prototype, technical demo, greybox, asset test, or collection of disconnected systems.

The public repository must be:

- GitHub: `https://github.com/oh-ashen-one/n64game`
- Local checkout: `/Users/midir/Documents/New project 8`
- Default branch: `main`
- Repository visibility: public

The game must run as an N64 ROM in Ares 148 Homebrew Mode, provide two complete playable battles, two complete explorable destinations, a world-map transition, a companion-return sequence, a resolved opening objective, and a final corruption-related story hook. A compiled ROM alone is not completion. A 20%-finished game, a “vertical slice” containing placeholders, or a polished room surrounded by unfinished content is not completion.

Quality takes priority over speed. Do not shorten the experience, simplify the visual promise, reduce asset quality, or silently remove a system to finish sooner. If a locked requirement is genuinely impossible because of N64 hardware, licensing, or unavailable authority, collect evidence, explain the exact conflict, and ask the user. Never reduce scope silently.

## 2. Authoritative References and Clean-Room Boundary

Study these sources deeply before production:

1. Pandemonium v0.71 release: `https://github.com/Boxingbruin/Pandemonium/releases/tag/v0.71`
2. Shared Pandemonium Drive folder: `https://drive.google.com/drive/folders/1C1MZRS5iU9Pia12RhdLhsx9giqJ6z4TF`
3. Tiny3D: `https://github.com/HailToDodongo/tiny3d`
4. The opening 20 minutes of Pokémon XD: Gale of Darkness, using gameplay footage and walkthroughs to understand pacing and functional beats.

Record reference findings in `docs/reference-study.md`, covering presentation, loading screens, cinematics, environment density, player control, animation coverage, battle staging, camera work, UI cadence, asset conversion, memory management, and technical architecture.

These references are inspiration and engineering research, not source material to copy:

- Implement original code from a clean Tiny3D/libdragon foundation. Do not copy, closely paraphrase, or translate Pandemonium GPL code into this MIT-licensed project.
- Do not reuse Pandemonium art, models, textures, animation, music, sound, writing, or other protected assets. Its asset license permits viewing and preservation builds, not incorporation into a new game.
- Do not copy Pokémon names, creatures, recognizable silhouettes, characters, dialogue, map layouts, logos, UI, music, animations, story expression, terminology, or branded mechanics.
- Downloaded reference material must remain outside the public repository.
- Every production asset must have ownership and provenance recorded before public release.

The project may follow Pokémon XD’s high-level opening rhythm—abduction mystery, name entry, simulated battle, research base, missing-person errand, second location, mistaken-intruder battle, reunion, return, and larger threat—while expressing every detail through an original world and original audiovisual design.

## 3. Locked Creative Direction

Working ROM title: `N64GAME`.

Art direction: retro desert science fiction with the confident, authored low-poly presentation of a late-1990s/early-2000s console RPG. Use sun-bleached stone, ochre dust, oxidized metal, dark teal machinery, warm practical lights, cobalt night shadows, and controlled magenta-violet corruption accents. Shapes should combine chunky field equipment, analog screens, sweeping observatory geometry, cloth shade structures, antennae, ceramic panels, and readable creature silhouettes.

World vocabulary:

- Creatures are called **Echoforms**.
- The relationship energy shared by a trainer and team is **Resonance**.
- Corrupted Echoforms are **Fractured**.
- The home location is **Meridian Research Annex**.
- The second destination is **Veyra Observatory Estate**.
- The hostile organization teased in the opening is **the Severance**.
- The customizable protagonist has no voiced name; the default entry is `ARI`.
- The missing younger companion is **Tavi**.
- The research guardian is **Dr. Sera Venn**.
- The Annex director is **Director Oren Saye**.
- The eccentric inventor is **Ivo Veyra**.
- The estate assistant and mistaken-intruder opponent is **Rusk**.

The opening cinematic depicts the Severance intercepting the research carrier **Solace** above the desert at dusk. A colossal Fractured Echoform bends light and gravity around the carrier while glider craft attach restraint lines. The Solace vanishes into a violet storm, leaving one emergency beacon falling toward the wastes. The cinematic cuts to the player-name interface and battle simulation.

Do not make the final cinematic video during this goal. The game must reserve its exact playback point and the storyboard package must enable the user to create the AI video later.

## 4. Locked 20-Minute Experience

Measure playtime from cold boot to the end of the closing hook. The temporary cinematic slate counts for no more than five seconds. A normal first-time playthrough must take 18–25 minutes, excluding time spent idling. At least 15 minutes must be player-controlled gameplay. Dialogue cannot be bloated to reach the runtime.

### Segment A — Boot, Loading Presentation, and Cinematic Slot (0:00–0:30)

- Display an original studio/game mark and an attractive branded loading treatment that hides only real loading work.
- Fade into a polished 4:3 slate reading `INSERT CUTSCENE HERE`.
- Hold the slate for three seconds or allow A/Start to skip immediately.
- Whether watched or skipped, set the same `opening_cinematic_seen` flag and continue safely to name entry.
- Use final UI styling, transitions, sound cue, and color treatment. The slate is the only intentionally temporary visual allowed in the accepted build.

### Segment B — Name Entry and Battle Simulation (0:30–4:30)

- Present a polished character-name interface supporting 1–8 uppercase characters, backspace, default `ARI`, confirmation, and cancel protection.
- Enter a visually complete simulation arena with a short camera fly-in.
- Run a scripted but interactive 2v2 tutorial using four loaned Echoforms.
- Teach command selection, legal target selection, move information, turn order, HP, effectiveness feedback, Resonance gain, and one duo finisher.
- The tutorial must accept reasonable alternate commands while guaranteeing that the player learns the required actions.
- Losing or reaching an impossible state restarts the simulation cleanly; it never corrupts story progress.
- End with the arena dissolving into the Meridian Research Annex simulation chamber.

### Segment C — Meridian Research Annex (4:30–10:30)

- Return control in a complete two-level research outpost containing the simulation room, central atrium, director’s lab, player room, clinic/creature bay, workshop, elevator, exterior threshold, and optional examine points.
- Introduce Dr. Sera Venn and Director Oren Saye through concise dialogue and staged character animation.
- Reveal the player’s real two-Echoform starter team; the starters must be visible in the world or presented through an authored onboarding sequence.
- Send the player to retrieve the **Field Relay**, the project’s handheld interface for party, messages, Resonance records, and map destinations.
- Let the player explore, speak to optional NPCs, inspect props, learn controls, save, pause, and view the party.
- Establish that Tavi left during a hide-and-seek errand and may be at Veyra Observatory Estate.
- Unlock the estate on the world map and guide the player to the outpost exit without an invisible forced corridor.

### Segment D — World Map and Estate Arrival (10:30–11:30)

- Transition through a responsive original desert map with the Annex and Estate as visible nodes.
- Selecting the Estate shows a short travel animation and branded loading transition.
- Preserve player name, party, settings, quest state, HP rules, and save state across the transition.

### Segment E — Veyra Observatory Estate and Real Battle (11:30–16:30)

- Provide a complete exterior courtyard with observatory landmark, kinetic invention props, fountain or energy apparatus, vegetation/dust dressing, strong navigation, and environmental storytelling.
- Rusk mistakes the player for a Severance intruder. Use blocking, facial/body animation, camera cuts, and concise dialogue before battle.
- Run the first real 2v2 battle using the player’s actual starter team against Rusk’s two Echoforms.
- The player can win through multiple valid command choices. Enemy AI must choose legal, understandable actions and demonstrate one support interaction.
- Support victory, defeat, retry, pause, camera transitions, animation/VFX/audio synchronization, experience or progression feedback, and correct post-battle state.
- On defeat, restore the pre-battle snapshot and offer Retry or Return to Annex. Retry must not duplicate rewards or flags.

### Segment F — Estate Interior and Reunion (16:30–20:30)

- After victory, Rusk apologizes and opens the estate.
- Include a foyer/gallery, invention hall, observatory study, and Tavi’s discovery scene with Ivo Veyra.
- Allow optional inspection of several eccentric inventions and environmental details.
- Tavi joins as a visible following companion. The follower must navigate doors, avoid obvious clipping, recover from separation, and never block the player.
- Return through the world map to Meridian Research Annex.

### Segment G — Resolution and Hook (20:30–23:00 target, variable by player)

- Resolve the missing-person objective with Dr. Sera Venn and Director Oren Saye.
- Deliver a new Field Relay message containing the Solace emergency beacon signature.
- Briefly show a Resonance monitor reacting to an unknown Fractured Echoform.
- Save progress, display a final authored title/hook screen, and return to a stable menu or post-slice state.
- Do not promise inaccessible content through a broken door or crash. A tasteful `End of opening chapter` treatment is acceptable.

The segment estimates are pacing targets, not forced timers. Three first-playthrough-style certification runs must have a median between 18 and 25 minutes.

## 5. Gameplay and Data Contract

### Exploration

Implement analog movement, acceleration/deceleration, authored idle/walk/run animation, a stable follow camera, camera collision or safe clamping, world collision, slopes/steps appropriate to the environments, interaction prompts, doors, elevators, dialogue, examine points, pause/resume, controller reconnect handling, companion following, loading transitions, and world-map travel.

The player must not become trapped behind props, fall outside collision, lose control after dialogue, or trigger a scene twice. All mandatory interaction targets require clear visual composition and prompt placement without intrusive arrows covering the screen.

### Battle

Use a deterministic state machine with these phases: intro, command selection, target selection, turn queue construction, action presentation, damage/status resolution, knockout replacement if applicable, round cleanup, victory/defeat, and exit.

Required mechanics:

- Two active Echoforms per side.
- Four moves per creature, with at least one attack, one support or debuff option, and differentiated target rules.
- Speed-based order with stable tie-breaking.
- Legal target validation and graceful recovery if a target becomes invalid.
- HP, damage, simple affinity/effectiveness, one temporary status family, knockout, and battle-end detection.
- Enemy AI that scores legal moves and targets without cheating.
- Shared player Resonance meter earned through complementary actions and successful play.
- A duo finisher that requires full Resonance, uses both active creatures, has a bespoke camera/animation/VFX sequence, and cannot fire in invalid states.
- Tutorial gates that teach without disabling all agency.
- Complete animation, VFX, UI, and audio synchronization.

Create data-driven definitions for creatures, moves, encounters, dialogue, and story flags. Gameplay logic may not depend on asset filenames scattered through scene code.

### Save Data

Use EEPROM4K with a versioned, checksummed schema containing player name, settings, current location, party composition, party HP/progression, Field Relay unlock, completed tutorial, battle rewards, story flags, cinematic-seen flag, and slice-complete flag. Write safely, detect invalid or incompatible data, and fall back to a new-game path without crashing. Debounce writes and never save a half-applied transition.

Required behavior must be defined and tested for dialogue skipping, slate skipping, losing either battle, retrying, loading mid-arc, controller disconnects, invalid saves, revisiting rooms, repeated world-map travel, and attempting completed objectives again.

## 6. Technical Architecture

Use libdragon preview and Tiny3D with original project code. Initial dependency pins:

- libdragon preview: `f13b48985edbf4310f07779c76d9a68c7605037b`
- Tiny3D main: `e84172f29f719680ac3213a7f408c2f721ef7b24`
- libdragon CLI: `12.2.1`
- primary emulator certification target: Ares 148 with Homebrew Mode enabled

If a pin cannot build together, record the exact incompatibility and move to a mutually compatible explicit commit set. Never float production dependencies on `latest` or an unpinned branch.

Targets:

- Standard 4 MB Nintendo 64; no Expansion Pak requirement.
- 320×240 output, 16-bit color, triple buffering.
- 30 FPS target during exploration and battles, with no sustained sequence below the approved budget.
- EEPROM4K saves.
- ROM target below 16 MiB; hard ceiling 32 MiB only if evidence shows the original target cannot retain required quality.
- At least 512 KiB free heap at the measured peak.
- No persistent heap reduction across twenty complete scene-transition loops.

Use a scene controller with explicit `enter`, `update`, `fixed_update`, `draw`, and `exit` ownership. Scene-owned models, matrices, display lists, skeletons, animations, sprites, and audio handles must be released during exit after appropriate RSP/RDP synchronization. Use scene arenas or equivalent ownership accounting so leaks and double frees are visible.

Define stable interfaces equivalent to:

- `GameScene`: lifecycle callbacks and scene identifier.
- `GameState`: global progression, transition request, settings, and save snapshot.
- `CutsceneEvent`: timestamp/type/payload records for camera, animation, dialogue, fade, audio, and flags.
- `CreatureDef`: identity, stats, affinity, model, animation set, moves, portrait, and audio.
- `MoveDef`: targeting, power/effect, Resonance contribution, animation, VFX, and audio.
- `BattleActor` and `BattleState`: runtime combat state separated from immutable definitions.
- `DialogueNode`: speaker, text, next node, optional condition, optional action.
- `SaveData`: fixed-width versioned serialization independent of runtime pointers.

Use Docker Desktop and libdragon CLI for reproducible local builds. Provide scripts for toolchain bootstrap checks, clean build, ROM build, Ares launch, asset validation, and checksum creation. GitHub Actions must perform a fresh public build and upload the `.z64`, SHA-256 checksum, map/size report, and validation summary as artifacts.

Do not commit generated build directories or ROM binaries to normal Git history. Use Git LFS only for appropriate editable binary sources such as `.blend`, selected `.glb`, and lossless source audio; keep optimized runtime outputs reproducible from sources.

## 7. Art Direction and Anti-Slop Contract

The visual-quality bar is non-negotiable. The game must resemble an actual carefully authored release comparable in care, density, atmosphere, animation coverage, and presentation to the Pandemonium reference. It does not need to imitate Pandemonium’s dark-fantasy style. “N64 low-poly” is a technical and aesthetic constraint, not permission for crude shapes, generic generated characters, default materials, flat lighting, empty rooms, stiff animation, or unfinished presentation.

Before mass asset production, create `docs/ART_BIBLE.md` containing:

- Shape language for humans, Echoforms, Severance technology, Annex equipment, and Veyra inventions.
- Character and creature proportion rules.
- Palette with environment, skin/fabric/metal, UI, Resonance, and Fracture swatches.
- Material and vertex-color rules.
- Texture-density and resolution rules.
- Lighting, shadow, fog, and color-grading approach.
- UI typography, panels, icons, spacing, and 4:3 safe-area rules.
- VFX rules for hits, support moves, Resonance, Fracture, transitions, and loading.
- Animation principles, pose clarity, anticipation, impact, recovery, and idle personality.
- Scale chart and gameplay-camera readability examples.
- Explicit good/bad examples and prohibited shortcuts.

### Asset Standards

Every production model must have a distinctive original silhouette, purposeful topology, clean normals, deliberate UVs, consistent texel density, authored vertex colors/materials, readable features, correct scale, meaningful naming, an efficient rig where required, and no visible generation defects. Optimize for N64 limitations without destroying the design.

Suggested starting budgets, to be validated in the representative benchmark:

- Player and hero NPCs: roughly 700–1,200 visible triangles.
- Supporting NPCs: roughly 450–900 visible triangles.
- Battle Echoforms: roughly 700–1,500 visible triangles depending on silhouette and effects.
- Small props: roughly 20–400 triangles; landmark props may exceed this when justified.
- Keep visible scene complexity within the verified 30 FPS and memory budget using culling, segmentation, and disciplined material/texture use.

Textures should primarily use 32×32 and 64×64 sources, with larger or split textures only when a visual benchmark proves the need and performance remains compliant. Use vertex colors to add form, material variation, and lighting richness. Do not hide weak modeling beneath noisy AI textures.

### Required Production Inventory

At minimum, produce and track:

- One customizable-name player model with complete exploration and dialogue animation coverage.
- Tavi, Dr. Sera Venn, Director Oren Saye, Ivo Veyra, Rusk, and at least three supporting Annex NPCs.
- Eight polished battle-capable Echoforms: two real starters, two player-side simulation loaners, two simulation opponents, and two estate opponents.
- Meridian Annex exterior threshold and complete two-level interior set.
- Veyra Estate courtyard/exterior plus complete foyer, invention hall, and observatory study.
- An original world map and location-node presentation.
- At least 25 purposeful environment props across the two destinations.
- Complete dialogue, pause, Field Relay, battle, loading, save, name-entry, and result UI.
- Battle and environment VFX for all implemented moves, Resonance, duo finisher, Fracture hook, dust, transitions, and feedback.
- Portraits/icons as required by the selected UI direction.

Minimum humanoid animation coverage: idle variations, walk, run, turn or direction handling, interaction, talk gestures, reaction, battle-command pose where applicable, and scene-specific performances.

Minimum Echoform animation coverage: idle variations, entrance, locomotion or repositioning, at least two distinct move performances, support performance where applicable, hit reaction, knockout, victory, and participation in the duo finisher. Reusing an animation is permitted only when it remains visually intentional and anatomically correct.

### Asset Review Gates

Image generation may be used for concept exploration, orthographic sheets, texture source material, portraits, UI motifs, color scripts, and storyboards. Raw generated output must never be dropped into the game uncritically. Remove malformed anatomy, random detail, fake text, inconsistent costume elements, perspective errors, lighting baked into the wrong texture, and identity drift. Translate approved concepts into purpose-built Blender models.

Every major asset must pass all seven gates:

1. Concept and orthographic review: front/side/back or equivalent construction information, palette, materials, and readable silhouette.
2. Blender technical review: topology, normals, UVs, scale, origin, naming, rig, weights, and deformation.
3. Textured turntable review: attractive from all major angles under neutral and representative lighting.
4. Animation review: expressive timing, no unacceptable clipping, foot sliding, broken weights, or dead poses.
5. Tiny3D conversion review: correct materials, textures, skeletons, animation playback, and no converter warnings left unexplained.
6. In-engine review: correct appearance under real gameplay cameras, resolution, lighting, culling, memory, and performance.
7. Final consistency review: matches the art bible and surrounding cast/environment after integration.

Require at least two deliberate polish passes after the first in-engine appearance of each hero asset. Reject and rebuild assets that are generic, anatomically broken, visually inconsistent, unexpressive, poorly textured, under-detailed for their camera distance, or attractive from only one angle.

Greybox primitives and temporary materials are allowed only during tracked development milestones. Before acceptance, search the repository and game for every placeholder marker and visually inspect every scene. Remove all temporary content except the explicitly approved `INSERT CUTSCENE HERE` slate.

Maintain `docs/ASSET_LEDGER.md` with asset ID, owner, source prompt or source file, transformations, license, Blender source, runtime output, review status, and reviewer evidence. Maintain turntables and representative in-engine captures under an organized review directory without bloating runtime assets.

## 8. Storyboard and Future Cutscene Handoff

The opening-cinematic storyboard is a required user-facing deliverable. Generate it with GPT Image only after the art bible and hero designs are stable enough to preserve continuity. The storyboard must use original designs and match the final game’s visual language.

Create:

- Eighteen numbered high-resolution 4:3 storyboard panels.
- Individual panel files in story order.
- One high-resolution contact sheet with readable panel numbers.
- `storyboard/opening/SHOT_LIST.md`.
- A continuity sheet for protagonist-related visual context, Severance figures, the colossal Fractured Echoform, Solace carrier, glider craft, and key environment elements.
- A concise color script showing the progression from warm desert dusk to violet Fracture storm to cool simulation interface.

The panels must collectively establish the Solace, its research purpose, the desert scale, the Severance interception, the colossal creature’s power, the crew’s danger, the falling beacon, and the visual transition into name entry/battle simulation. They must form an animatable sequence, not eighteen unrelated illustrations.

For every shot, the shot list must specify:

- Panel and shot number.
- Intended duration and total target runtime.
- Framing, virtual lens, camera height, and camera movement.
- Subject blocking and action.
- Character/creature performance.
- Lighting, color, atmosphere, and continuity notes.
- Transition in/out.
- Dialogue or on-screen text, if any.
- Sound design and music intent.
- 320×240 and CRT-safe framing notes.

Target a future cutscene length of 60–90 seconds. The eventual playback format will be selected during video integration, but framing must be designed natively for 4:3 N64 presentation. Clearly document the exact ROM asset path, expected audio pairing, playback callback, skip behavior, and state handoff that will replace the temporary slate.

Visually inspect every generated panel. Identity changes, malformed anatomy, incoherent action, unreadable staging, fake text, vehicle redesigns between panels, palette drift, or incorrect aspect ratio are failures. Regenerate or edit failed panels before delivery. Provide the final storyboard files to the user directly at handoff; merely committing prompts is insufficient.

## 9. Audio, UI, Loading, and Presentation

Create an original cohesive audio identity. Use compressed mono or otherwise N64-appropriate sources, typically around 22 kHz where suitable. Provide separate music treatment for title/loading, simulation battle, Annex exploration, Estate exploration, real battle, victory, and closing hook, while reusing motifs intentionally. Include footsteps, UI feedback, doors/elevator, ambient machinery, creature vocals, every move, impacts, Resonance, duo finisher, battle transitions, and save feedback.

Loading screens must be branded, attractive, and honest. Do not add fake long waits. Use a consistent logo/graphic motif, animated indicator where performance allows, location title, and smooth fade. Loading presentation must never expose a raw framebuffer, debug text, uninitialized asset, or frozen last frame.

All UI must remain readable at 320×240 on a CRT-safe 4:3 frame. Test long allowed player names, low HP, status icons, two-versus-two target selection, dialogue wrapping, button prompts, and color contrast. Do not use tiny modern-desktop typography.

## 10. Repository, Licensing, and Public Hygiene

Required public files:

- `README.md` with screenshots, build/run instructions, controls, project status, and license summary.
- `LICENSE` containing the MIT License for original source code.
- `ASSET_LICENSE.md` stating that original/generated art, models, animation, audio, writing, characters, creature designs, world, and other non-code content are All Rights Reserved unless a ledger entry says otherwise.
- `THIRD_PARTY_NOTICES.md` with Tiny3D, libdragon, tooling, fonts, and every other dependency’s notices.
- `docs/N64GAME_MASTER_SPEC.md` and `docs/N64GAME_GOAL_PROMPT.md`.
- `docs/ASSET_LEDGER.md`, `docs/ART_BIBLE.md`, reference study, test evidence, and build documentation as production progresses.

Never commit credentials, browser data, copyrighted reference downloads, extracted Pokémon assets, Pandemonium assets, unlicensed fonts, or ambiguous media. Run secret and large-file checks before every public push. The repository being public does not place protected project assets under MIT; keep code and asset licensing explicitly separate.

## 11. Ordered Production Gates

Work through these gates in order. Maintain an evidence-backed checklist. Files existing do not prove features work.

1. **Reference and legal audit:** study sources, record lessons, establish clean-room and asset-license boundaries.
2. **Preproduction:** lock the story beat sheet, pacing map, technical architecture, art bible, data schemas, asset inventory, and review templates.
3. **Toolchain:** install and pin Docker/libdragon/Tiny3D, compile a clean ROM, configure Ares, and establish public CI.
4. **Visual benchmark:** complete one representative environment corner, one hero Echoform, one humanoid, final lighting, representative UI, one battle animation, and one VFX event. Do not mass-produce assets until this benchmark passes the visual bar in-engine.
5. **End-to-end greybox:** make the full cold-boot-to-ending state flow playable with tracked temporary assets, both battles, saves, retries, transitions, and timing instrumentation.
6. **Gameplay completion:** finish battle rules, AI, exploration, camera, collision, dialogue, companion, world map, save/load, and edge cases before final asset replacement obscures logic bugs.
7. **Production assets:** replace every tracked placeholder through the seven-gate asset pipeline.
8. **Presentation polish:** finish animation, audio, UI, VFX, lighting, loading, camera staging, environmental dressing, and transitions.
9. **Storyboard package:** create, review, and deliver the complete GPT Image storyboard and future-video integration contract.
10. **Certification:** conduct performance profiling, transition soak, clean builds, timed full playthroughs, save/retry testing, public-license audit, and final visual review.
11. **Release handoff:** publish verified artifacts, screenshots, captures, checksums, known limitations, and direct links without falsely claiming real-hardware validation that did not occur.

Do not move past a gate with hidden critical failures. It is acceptable to iterate backward. It is not acceptable to call a missing production asset “good enough” because the system works.

## 12. Test and Evidence Matrix

Automate host-side tests where feasible for battle ordering, legal targets, damage/status logic, Resonance, story flags, save serialization/checksum, invalid-save fallback, and deterministic AI inputs. Use compiler warnings and static checks appropriate to the toolchain. Asset validation must check required files, dimensions/formats, naming, missing animations, conversion errors, and accidental placeholder markers.

Ares certification must cover:

- Cold boot, new game, default and custom names.
- Slate watched and skipped.
- Tutorial alternate inputs and restart path.
- Every required/optional Annex interaction.
- Save, quit/reboot, and resume at supported progress points.
- World-map travel in both directions.
- Estate victory and defeat/retry paths.
- Companion follow through doors, transitions, obstruction, separation, and return.
- Dialogue skipping and rapid confirm/cancel input.
- Controller disconnect/reconnect during exploration, menus, dialogue, and battle.
- Corrupted EEPROM data.
- Re-entering completed rooms and attempting completed objectives.
- Full ending and stable post-slice state.

Performance evidence must include frame timing for the busiest exploration and battle views, peak heap measurements, ROM/map size, and twenty repeated scene-transition loops showing no persistent memory loss. Required 30 FPS may be assessed with frame-time evidence rather than an unsubstantiated visual claim.

Run three first-playthrough-style timing passes. Record total time and segment times; the median must be 18–25 minutes without counting idle time or using the missing cinematic to pad duration.

Final visual evidence must include representative gameplay screenshots from every environment, both battles, each major UI surface, loading presentation, hero-asset turntables, representative animation captures, and the storyboard contact sheet. Inspect at native 320×240 as well as enlarged nearest-neighbor output.

## 13. Final Acceptance Checklist

Do not mark the goal complete until all of the following are true:

- The public `oh-ashen-one/n64game` repository exists and a fresh clone builds reproducibly.
- CI produces a bootable `.z64`, SHA-256 checksum, header/size evidence, and build report.
- The complete game opening runs from cold boot through the closing corruption hook.
- Three timed runs meet the 18–25 minute median requirement with real player agency.
- Both 2v2 battles, defeat/retry, save/reload, dialogue, exploration, elevators/doors, world map, companion flow, transitions, and story flags work.
- Twenty transition loops show no persistent memory growth; peak free heap remains at least 512 KiB.
- Required scenes meet the verified 30 FPS target.
- There are no crashes, softlocks, collision traps, missing assets, broken audio, unreadable required UI, progression blockers, duplicate rewards, or corrupt state transitions.
- Every production asset has provenance and has passed the seven art gates.
- No placeholder, primitive, default material, raw generated texture, temporary animation, TODO/FIXME affecting play, or unfinished environment remains, except the approved `INSERT CUTSCENE HERE` slate.
- The complete 18-panel storyboard, individual panels, contact sheet, continuity sheet, color script, and shot list have been visually reviewed and delivered directly to the user.
- Code and asset licenses are separated correctly; third-party notices and public-repository hygiene checks pass.
- Any emulator-only claims are labeled honestly; real N64 hardware support is not claimed until tested.

## 14. Agent Operating Rules

- Pursue the complete outcome autonomously and persistently.
- Prefer verified output over status claims. Inspect the ROM, repository, CI, screenshots, captures, and generated files before saying they exist or work.
- Preserve user work and avoid destructive operations.
- Use isolated branches/worktrees when the checkout becomes dirty or concurrent work risks collisions.
- Keep the user informed during long work and surface meaningful design or legal blockers early.
- Use sub-agents for bounded parallel work when it materially improves quality, but the primary agent remains responsible for integration and verification.
- Do not replace this master prompt with a shorter interpretation, regenerate it from memory, or silently revise locked requirements.
- User instructions explicitly changing scope override this document; record such changes in the document and implementation history.
- Never claim completion based on percentage, file count, compilation, or one successful screen. Completion means every acceptance condition above is proven.

