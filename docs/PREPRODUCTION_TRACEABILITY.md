# Gate 2 Preproduction Traceability

This document is the exit audit for production Gate 2. It does not replace the master specification. A checked item means the cited production document contains an implementation-ready decision that has been reconciled with every other Gate 2 document.

## Authority and change control

- The authority order is: explicit user change, `docs/N64GAME_MASTER_SPEC.md`, then the supporting documents named below.
- Supporting documents may add detail but may not reduce runtime, content, art quality, hardware targets, review depth, or certification requirements.
- A locked name, ID, count, timing range, palette value, asset budget, serialized field, or state transition must have one canonical definition. Other documents reference it rather than silently introducing a competing value.
- A later measured hardware failure may revise a suggested budget only through an evidence-backed decision log. It may not remove the associated player-facing content or lower the accepted visual bar without user approval.
- Gate 3 may not begin until every Gate 2 exit item is checked and the complete document set has passed a consistency review.

## Required document set

| Contract area | Canonical artifact | Exit evidence |
|---|---|---|
| Story, script, chapter state flow, and measured pacing | `docs/STORY_AND_TIMING.md` | Every mandatory and optional beat has start/end conditions, story flags, dialogue or performance intent, expected active-control time, and failure/skip behavior |
| Runtime ownership and platform design | `docs/TECHNICAL_ARCHITECTURE.md` | Each subsystem has boundaries, lifetime, memory/performance implications, failure behavior, and test seams |
| Fixed-width gameplay and serialization contracts | `docs/DATA_SCHEMAS.md` | IDs, invariants, byte layouts, bounds, versioning, checksum rules, and migration behavior are explicit and internally consistent |
| Visual and audiovisual production contract | `docs/ART_BIBLE.md` | Original visual thesis, exact palettes, shape/material/texture/lighting/UI/VFX/animation rules, budgets, and objective rejection criteria exist |
| Complete content bill of materials | `docs/ASSET_INVENTORY.md` | Every required model, environment module, prop, animation, UI surface, VFX event, audio cue, storyboard output, collision asset, and review capture has a unique ID and budget |
| Repeatable quality reviews | `docs/ASSET_REVIEW_TEMPLATES.md` | All seven asset gates plus benchmark, environment, animation, UI, VFX, audio, and storyboard reviews demand inspectable evidence |
| Per-asset provenance and actual production status | `docs/ASSET_LEDGER.md` | The inventory is the normalized planned registry; each item receives an explicit provenance row before any concept/source work begins; no unverified third-party source is allowed |
| Naming collision screen and roster lock | `docs/NAMING_AND_ORIGINALITY_AUDIT.md` | Rejected working names are purged; eight canonical display/symbolic IDs agree everywhere; limitations of the screen are stated honestly |
| Reference and clean-room constraints | `docs/reference-study.md`, `THIRD_PARTY_NOTICES.md`, `ASSET_LICENSE.md` | Supporting documents contain no copied reference expression and preserve the separate code/asset license boundary |

## Locked chapter envelope

These values come directly from the master specification and must agree across every supporting document:

| Item | Locked value |
|---|---|
| Measured chapter | Cold boot through stable closing Fracture hook |
| Normal first-time runtime | 18–25 minutes, excluding idle time |
| Minimum player-controlled time | At least 15 minutes in every qualifying first-playthrough certification run; never a median-only test |
| Temporary cinematic | Final-styled, skippable `INSERT CUTSCENE HERE` slate; three-second hold and no more than five seconds total |
| Destinations | Meridian Research Annex and Veyra Observatory Estate, plus an interactive world map |
| Battles | One complete interactive simulation 2v2 and one complete real 2v2 against Rusk |
| Battle roster | Eight distinct polished battle-capable Echoforms: two real starters, two simulation loaners, two simulation opponents, two estate opponents |
| Annex spaces | Simulation room, central atrium, director's lab, player room, clinic/creature bay, workshop, elevator, and exterior threshold |
| Estate spaces | Courtyard/exterior, foyer/gallery, invention hall, and observatory study |
| Companion flow | Tavi discovered, joins visibly, follows safely through the return transition, and resolves the objective at the Annex |
| Closing hook | Field Relay receives the Solace beacon signature; a Resonance monitor reacts to an unknown Fractured Echoform; progress saves into a stable post-chapter state |
| Hardware | Standard 4 MB N64, no Expansion Pak, 320×240, 16-bit, triple-buffered, target 30 FPS |
| Resource targets | ROM under 16 MiB target, peak free heap at least 512 KiB, no persistent loss over 20 complete transition loops |
| Save medium | EEPROM4K with explicit versioning, checksums, safe writes, fallback, and migration policy |
| Intentionally temporary final content | The cinematic slate only |

## Gate 2 exit audit

### Story and pacing

- [ ] The full chapter can be followed from cold boot without inventing a missing transition, objective, conversation, or destination.
- [ ] Every segment includes expected time, active-control time, critical path, optional content, and anti-padding intent.
- [ ] The exact slate insertion point and one idempotent watched/skipped handoff are defined.
- [ ] Name entry handles default/custom input, length bounds, backspace, confirmation, and cancel protection.
- [ ] Both 2v2 battles identify participants, encounter intent, tutorial or AI behavior, win/loss state, retry behavior, and reward idempotency.
- [ ] The Annex and Estate have critical-path and optional interactions with readable objective guidance.
- [ ] World-map travel preserves and saves the correct state in both directions.
- [ ] Tavi's discovery, follower recovery, transitions, return, and objective resolution are state-complete.
- [ ] Dialogue skipping, rapid input, controller loss, invalid save, revisit, and repeated-objective cases have explicit outcomes.
- [ ] Three eventual timing captures can be compared against named segment markers without manual interpretation.

### Technical and data design

- [ ] Scene ownership includes synchronized exit, arena/registry accounting, partial-load rollback, and transition safety.
- [ ] Update, fixed simulation, rendering, UI, audio, loading, and final display submission have an explicit frame order.
- [ ] Exploration, dialogue, battle, world map, cutscene slate, save, and post-chapter systems have defined interfaces and ownership.
- [ ] Future FMV playback can replace the slate without changing the completion callback or story flags.
- [ ] Immutable content definitions are separate from runtime actor/state objects and asset paths are not scattered through gameplay logic.
- [ ] Save serialization uses exact byte offsets and endianness rather than native C struct layout, and every serialized ID/bit domain is bound to the immutable reviewed-commit registry with append/tombstone-only history checks.
- [ ] Power interruption, invalid checksum, incompatible version, and interrupted transition behavior are specified.
- [ ] The memory plan accounts for triple framebuffers, scene assets, battle assets, audio, UI, stacks/heap, and a measured 512 KiB margin.
- [ ] Host-side deterministic tests and on-emulator instrumentation are designed before implementation.
- [ ] Build and asset conversion inputs are pinned and public CI outputs are named.

### Art and asset production

- [ ] Every major faction, humanoid, Echoform class, location, UI family, VFX family, and prop family has an original, coherent shape language.
- [ ] Palette values, texture formats/sizes, vertex-color behavior, material counts, geometry/rig limits, scale, naming, and export conventions are numeric where practical.
- [ ] The art bible rejects generic generated shapes, primitives as final art, default materials, empty rooms, flat lighting, baked-light mistakes, stiff animation, malformed anatomy, and identity drift.
- [ ] Gameplay-camera and native 320×240 readability drive silhouettes, poses, contrast, and interface sizing.
- [ ] The asset inventory contains all eight Echoforms, all required humanoids, both complete destinations, world map, at least 25 purposeful props, every collision/export unit, all UI, all implemented move VFX/audio, all required animations, the loading/slate presentation, and every storyboard/review deliverable.
- [ ] Each inventory item has a unique stable ID, scope/budget, dependency, production priority, and required evidence.
- [ ] Every major asset must pass the seven review gates and receive two deliberate polish passes after its first in-engine appearance.
- [ ] The visual benchmark is a representative integrated scene, not isolated attractive renders.
- [ ] Review templates record reviewer, date, version/commit, evidence paths, failures, revisions, and explicit approve/rebuild decisions.

### Cross-document consistency and public hygiene

- [ ] All named characters, Echoforms, moves, locations, scene IDs, story flags, encounter IDs, and asset IDs agree across the document set.
- [ ] Roster and asset counts reconcile exactly; reuse is explicit and does not disguise a missing distinct Echoform.
- [ ] The three total durations have an 18–25 minute median, and every qualifying run independently contains at least 15 minutes of active control.
- [ ] Art budgets fit the architecture's memory/render assumptions and are marked for Gate 4 measurement rather than presented as already proven.
- [ ] Save flags and transition states cover every story precondition/postcondition named in the script.
- [ ] No production content uses a Pokémon or Pandemonium name, asset, protected design, dialogue, layout, UI expression, or closely paraphrased code; clean-room audit mentions are explicitly non-production constraints.
- [ ] Every reachable Git blob plus the index and worktree has been scanned by content; no credential, reference download, ROM/archive extension or magic, unlicensed font, or ambiguous third-party media is present.
- [ ] Markdown links resolve, files pass `git diff --check`, and public files contain no placeholder/TODO language presented as accepted production content.

## Gate 2 approval record

Gate 2 remains **in progress** until the audit above is completed against the actual files. The approval record must contain the full reviewed-content commit, exactly one `Independent reviewer 1` and one `Independent reviewer 2`, canonical distinct identities using the `github:<handle>` or `agent:/<canonical-task-path>` form, and an ISO review date no earlier than the reviewed commit and no later than the approval commit. It must contain one exact validation-evidence row per required command; the value syntax is `reviewed=<40-hex SHA>; command=<exact command>; result=PASS`. The required ordered commands are `scripts/validate-data-c`, `scripts/validate-dialogue-graph`, `scripts/validate-condition-registry`, `scripts/validate-id-locks`, `scripts/validate-asset-contract`, `scripts/validate-public-hygiene`, and `scripts/validate-preproduction --reviewed-content`. The last mode succeeds only when every substantive check passes and the error set is exactly the seven approval-only placeholders, making the evidence reproducible on the reviewed-content commit; normal `scripts/validate-preproduction` must still fail there and may pass only after the direct approval child. It must also contain one explicit deferred-measurement-risk row covering Gate 3 and Gate 4, followed by a final `APPROVED` or `REBUILD` decision. The approval transition remains a direct, single-parent child of the reviewed-content commit and changes only the three controlled approval artifacts.
