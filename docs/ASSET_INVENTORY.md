# N64GAME Production Asset Inventory

Status: Gate 2 implementation inventory

This is the authoritative planned inventory for production assets. It defines what must be authored; `docs/ASSET_LEDGER.md` records who made each asset, its provenance, license, transformations, gate status, and evidence. An inventory row is not proof that an asset exists or has passed review.

All runtime art must fit standard 4 MB Nintendo 64 operation, the scene caps in `docs/ART_BIBLE.md`, a ROM target below 16 MiB, 30 FPS, and at least 512 KiB peak free heap. The reproducible generated runtime tree is ignored `build/generated/assets/` and is never committed; editable sources live under `assets-src/`, exact Gate-5 review snapshots live under `review/<production-id>/g5/`, and appropriate binary sources use Git LFS.

## 1. Status, priority, and dependency keys

Stages:

- `S0` preproduction: concepts, orthographics, palettes, data contracts.
- `S1` visual benchmark: one final environment corner, player, Quarrune, UI, animation, and VFX.
- `S2` end-to-end greybox: tracked temporary geometry for the complete game flow.
- `S3` gameplay/interface ready: finalized collision, nav/spawn/interaction data, event IDs, ownership, timing contracts, and temporary `tmp.*` integration only. `S3` never authorizes a final visual, animation, UI, VFX, music, voice, or SFX source/output.
- `S4` production: final models, textures, rigs, animations, environments, UI, and audio.
- `S5` polish: dressing, lighting, presentation, synchronization, and two hero polish passes.
- `S6` storyboard: GPT Image panels and future-video handoff after hero designs stabilize.
- `S7` certification: native captures, profiling, full-playthrough evidence, provenance audit.

Priorities:

- `P0`: blocks the benchmark or complete state flow.
- `P1`: required for a finished 18–25 minute opening.
- `P2`: required support/dressing that may follow its parent room or system.
- `P3`: produced after in-game visual continuity is locked, but required for final acceptance.

Dependencies:

| Key | Meaning |
|---|---|
| `EXP` | Exploration controller, camera, collision, interaction |
| `BTL` | Battle actor/data state machine |
| `DLG` | Dialogue/cutscene event system |
| `FOL` | Tavi companion follower |
| `MAP` | World-map selection and travel |
| `SAV` | Save/load and story flags |
| `UI` | Common UI renderer, type, icons, safe area |
| `VFX` | Fixed particle/strip pools and animation events |
| `AUD` | Audio event, stream, and bank system |
| `CNV` | Blender/Fast64/Tiny3D conversion pipeline |

Budgets are exported/runtime budgets. Every skinned export uses one bone per vertex and no more than three bones per triangle.

### 1.1 Executable stage lock

`docs/VISUAL_BENCHMARK_APPROVAL.md` is the sole global unlock record for final visual/audio asset production. Before its decision is `APPROVED`, only exact whitelist rows/subsets marked `S1` are eligible to advance beyond Gate 1, and eligibility becomes authorization only when the row's exact `WB-###` basis, explicit ledger row, Gate 1 pass hash, canonical source-manifest `path@SHA-256`, and canonical output-manifest `path@SHA-256` or literal `NONE` are populated and verifiable. The sole non-art exception is the exact 15 original camera-shot `C7` rows authored as Markdown tuples at `concept`; this authoring exception is not a Gate 1 pass or `source` status, and generated outputs plus Gates 5–7 remain locked. An `S1/S4` row means only the named whitelist subset can be authorized at `S1`; every unlisted clip, state, sector, texture, cue, or variation stays `S4`. `S0` authoring is brief, construction, palette, orthographic, and clean-room work only. `S2` temporary greybox uses `tmp.*` development IDs and never becomes production source by renaming. `S3` establishes interfaces/readiness after benchmark approval but never substitutes final visual/audio work for `S4`. A file timestamp, ledger row, or individual gate form cannot override this lock.

The asset validator must compare every explicit visual/audio ledger row at `source`, `converted`, `review`, or `approved` against the control state, exact whitelist subset, `WB-###` authorization, Gate 1 hash, and current source/output hashes. Editable source lives only at `assets-src/<production-id-prefix>/<canonical.production.id>/`, with the first directory byte-equal to the production ID's segment before its first dot. Under `PENDING`, only populated exact benchmark authorizations may proceed; under `REVIEW_REQUIRED`, no new subset may start and only named affected rows may be reauthorized after refreshed hashes; under `BLOCKED`, only defect-linked remediation rows named by the control record may change and no new converted/review output may be accepted. It separately enforces the 15 C7 tuples' `concept` authoring exception and blocks their generated outputs. A non-whitelisted or unpopulated final visual/audio source before approval is a critical defect and returns the asset to `planned`/Gate 1 rather than grandfathering it into production.

General Gate-1 media exploration is permitted at `concept` only through the ledger's canonical hashed provenance/source/evidence/review locator set, `output:NONE`, seven literal pending gates, and exact source/Gate-1 manifest ownership. It creates no whitelist authorization, final-source claim, Gate 2+ record, or generated output. `planned` owns no bytes; the 15 Markdown-only C7 tuples remain the sole no-media concept exception.

A rejected/revise Gate-1 attempt remains historical evidence, not a new inventory status and not a G1 pass. The optional canonical attempt-history member resolves each failed source/evidence/review tuple at its strict public ancestor commit while the current inventory owner remains `concept`, output `NONE`, and all seven gates pending. Generated media inventory sources additionally require their provider-terms basis or explicit proven self-owned-generator basis plus a compatible output license; “project original” cannot launder a `source.generated` member.

Schema-Version 4 prevents a repair state from inventing history: `REVIEW_REQUIRED`/`BLOCKED` must bind the six-field identity of one prior pinned-key public approved tag/control/payload/registry. Unaffected authorization/control rows remain byte-identical, returned rows alone become `REPAIR_ONLY`, stable owner/subset paths remain fixed, and every changed gate is returned explicitly. Initial `PENDING` and current `APPROVED` have no active baseline and use six `NONE` values.

After approval, current inventory production follows Art Bible section 16.7: a clean local tree/index must equal credential-free public default `HEAD` and descend from the signed approval target; tracked or staged ROM extensions fail. Exact full-15-cell historical ledger rows may retain their byte-identical asset graph while changed rows are revalidated from `review/production/PAYLOAD_MANIFEST.sha256` as `SHA256("FULL_PRODUCTION")` with no subset allowlist. That root directly owns the committed ledger/inventory, has no workflow member, and admits only semantically validated pair/generated controls in special review namespaces. Signed benchmark history stays at its tag and need not be copied forward.

The prior baseline is the unique ancestry-maximal pinned-key-valid public approval ancestor of current public HEAD; older reachable and ambiguous maximal choices fail. Populating any of the exact eight current aggregate pairs activates public commit/build identity, credential-free clone/LFS materialization, reviewed ledger/tree ownership, and one shared commit-bound manifest context. Recipe metadata can be staged structurally, but local/fresh/public ROM equality is approval-only.

Authorization, provenance, completed review, and concept-review Markdown are exact parsed machine records under Art Bible section 16.4. Their scope/subset, source/output, creator/rightsholder, reviewer/non-owner, gate/evidence, state/build/time/defect/disposition projections must match the inventory-resolved ledger and registry; an arbitrary blob with a matching hash is invalid.

### 1.2 Canonical production IDs, review profiles, and polish tiers

Every canonical production ID resolves by the ordered rules below. Rules apply to IDs in any table column, so the `sfx.move.*` ID paired beside a `vfx.move.*` ID is not hidden from review. `present.*` and `ev.*` are deliberately excluded as non-owning alias/evidence records. First matching rule wins.

| ID rule | Review profile | Tier | Required decision/evidence behavior |
|---|---|---|---|
| `chr.*`, `echo.*` | `RIGGED_MODEL` | `H2` | Seven decisions; first-in-engine Gate-6 checkpoint, two real polish revisions, then final Gate-6 revalidation on the integrated hero |
| `env.*`, `lmk.*`, `veh.*` | `STATIC_MODEL_ENV` | `H2` | Seven decisions; two integrated location/landmark/vehicle polish passes |
| Exact hero-prop registry below | `STATIC_MODEL_ENV` | `H2` | Seven decisions; two integrated story-prop polish passes |
| Remaining `prop.*` | `STATIC_MODEL_ENV` | `M7` | Seven decisions; size-appropriate all-angle/state evidence |
| `ui.screen.*`, `ui.battle.*`, `ui.panel.*` | `UI_FONT_IMAGE` | `H2` | Seven decisions; two complete-state native/overscan polish passes |
| Remaining `ui.*`, `font.*` | `UI_FONT_IMAGE` | `M7` | Seven decisions and exact UI evidence-map coverage |
| `vfx.finisher.*`, `vfx.story.fracture_monitor`, `vfx.transition.*` | `VFX` | `H2` | Seven decisions; two integrated timing/readability polish passes |
| Remaining `vfx.*` | `VFX` | `M7` | Seven decisions; move/common evidence as applicable |
| `sfx.*`, `mus.*`, `amb.*`, `vox.*` | `AUDIO` | `M7` | Seven decisions; source, conversion, sync/mix, and release evidence |
| `anm.*` | `ANIMATION` | `M7` | Seven decisions; parent hero polish additionally reviews integrated clips |
| `col.*`, `nav.*`, `spn.*`, `int.*`, `bnd.*` | `DATA_SPATIAL` | `S7` | Seven functional/source/generated/in-engine decisions; no bare N/A |
| `sb.*` | `STORYBOARD` | `D7` | Seven delivery-equivalent decisions, direct-delivery proof, and non-owner Gate 7 reviewer |
| Declared generated child `ASSET_*` | `GENERATED_CHILD` | `C7` | Seven child decisions with exact parent/revision/BOM linkage and non-owner Gate 7 reviewer |
| `present.*` | non-owning delivery alias | `A0` | `alias_of` only; no creator/source/license/status/gates/ledger row |
| `ev.*` | evidence/control record | `E0` | subject/evidence linkage only; never counted as a production asset |

Exact `H2` hero props:

`prop.annex.field_relay`, `prop.annex.relay_dock`, `prop.annex.relay_side_reader`, `prop.annex.calibration_locator_tag`, `prop.annex.beacon_decoder`, `prop.annex.solace_model`, `prop.estate.rusk_wrench`, `prop.estate.impossible_compass`, `prop.estate.orrery_switch`, `prop.estate.ivo_track_roll`, `prop.estate.packet_recorder`, and `prop.estate.telescope_controls`.

No package may self-select a lower tier. `H2` polish pass 1 and pass 2 are separate source revisions after first in-engine appearance, each with before/after native evidence, defect decisions, source/output hashes, and a non-owner reviewer. A parent and child may share evidence files, but each production ID retains its own seven-entry decision vector in the ledger. The strict gate-equivalent meanings and substitute codes are defined in `docs/ART_BIBLE.md` and `docs/ASSET_REVIEW_TEMPLATES.md`.

The canonical ownership tables in sections 3–13 and 15 contain exactly 381 production IDs. The validator parses the owning ID columns (including both move children and the nav/spawn/interaction columns), requires every ID exactly once, requires one deterministic profile/tier, and checks the frozen sorted-ID registry seal `b32202371a31494d5f9a755c543042f7fa6fe624f2a074902fdee5e9b4db5688`. Pattern/profile rows, section-8.2 generated bundle cross-references, section-8.3 examples/mappings, `present.*` aliases, and section-16 `ev.*` evidence records are deliberately not ownership definitions. Changing the canonical set requires an explicit inventory-contract and validator-seal revision; deleting one row while duplicating another cannot preserve completeness.

## 2. Inventory totals

| Group | Required count | Completeness rule |
|---|---:|---|
| Runtime humanoids | 9 unique character models | Player, five named story characters, three unique Annex staff; no recolor-only staff |
| Battle Echoforms | 8 unique models | Exactly two starters, two player simulation loans, two simulation opponents, two Estate opponents; no cross-role model reuse |
| Authored environment/world-map source packages | 16 source packages | Fifteen Annex/Estate environment sources plus the world map; these compose into 13 traversable/battle runtime `ZoneId` values, while the separate UI-only end manifest owns the fourteenth `ZoneId` |
| Landmark assets | 8 | Readable navigation and story anchors, not interchangeable set dressing |
| Field vehicle assets | 1 hero + 1 simplified map model | Sand-skimmer source identity and proportions shared across Annex departure and world-map travel |
| Purposeful props | 63 unique prop designs | Instances may repeat only with purposeful placement/variation |
| Collision packages | 18 | Separate simplified meshes, interaction blockers, safe camera volumes, and moving-door/elevator pieces |
| Navigation / spawn / interaction indexes | 13 + 13 + 13 | One set per stable traversable/battle `ZoneId`; the closing hook reuses the loaded Annex atrium set and the end chapter is UI-only |
| UI-only end-zone manifest | 1 | `ZONE_END_CARD_UI` has no environment, collision, nav, spawn, interaction, player, or action overlay |
| UI/type/icon packages | 37 packages; controller atlas has exactly 12 prompt icons | Every named screen/state and every locked controller prompt/chord, complete CRT-safe variants |
| Regular battle-move presentation pairs | 32 pair records = 32 VFX production IDs + 32 audio production IDs | One paired parent record for each of the eight Echoforms' four regular moves; both children retain separate ledger/gate/evidence ownership. The two duo finishers are separate common-VFX/finisher-audio packages, so all 34 `MoveDef` entries have presentation ownership |
| Common/environment/story VFX | 20 | Includes Resonance, both finishers, dust, loading/travel, Rusk restoration, follower recovery, and Fracture hook |
| Humanoid animation banks | 10 | One 12-clip shared base bank plus nine character-specific banks |
| Echoform animation banks | 8 | Real starters own 14/15 clips including story performances; simulation finisher participants own 12; remaining actors own 11 |
| Vehicle/mechanism animation banks | 24 | Sand-skimmer, doors, elevator, machinery, world map, landmarks, and seven story-prop integration banks |
| Music cues | 8 | Distinct treatments with intentional motif reuse |
| Ambience / common SFX / Echoform vocal banks | 2 + 6 + 8 banks; story bank has 14 events | Move-specific audio events cover the 32 regular per-creature moves; both duo finishers are owned separately by the finisher bank, and story-prop, restoration, follower-recovery, reunion, and hook cues have explicit owners |
| Storyboard panels | 18 individual 4:3 images | High-resolution, continuity-reviewed, delivered individually and as a contact sheet |
| Storyboard continuity/handoff | 9 stable continuity sheets + color script + shot/prompt/delivery manifests | Includes the key desert/storm/research-deck environment sheet; all outputs are directly deliverable and continuity-reviewed |

## 3. Humanoid characters

Textures listed are default maximums; an approved smaller atlas is preferred. Each exported model includes one authored blob-shadow footprint definition and dialogue focus sockets.

| Asset ID | Character / silhouette purpose | Count | Geometry / materials / textures | Rig and required animation | Dependencies | Stage / priority |
|---|---|---:|---|---|---|---|
| `chr.player.ari` | Nameable protagonist; forward wedge, field jacket, relay harness | 1 hero + 1 distance mesh | 1,100 / 600 tris; 3 mats; 64×64 CI8 body + 32×32 CI4 face | 24 joints; shared base; only `battle_command` and `dialogue_nod` player-specific clips are `S1`, remaining eight are `S4`; one-bone export | `EXP BTL DLG UI CNV` | `S1/S4 P0` |
| `chr.tavi` | Younger companion; scarf tail, pouch, upward triangles | 1 hero + 1 distance mesh | 850 / 450 tris; 3 mats; 64×64 CI8 body + 32×32 CI4 face | 22 joints; shared 12-clip base + 9 follower/scene clips | `EXP DLG FOL CNV` | `S4 P1` |
| `chr.sera_venn` | Research guardian; tall column and diagonal diagnostic sash | 1 hero | 1,000 tris; 3 mats; 64×64 CI8 body + 32×32 CI4 face | 22 joints; base + 4 diagnostic/story clips | `DLG SAV CNV` | `S4 P1` |
| `chr.oren_saye` | Director; broad yoke, low planted center | 1 hero | 1,050 tris; 3 mats; 64×64 CI8 body + 32×32 CI4 face | 22 joints; base + 4 director/story clips | `DLG SAV CNV` | `S4 P1` |
| `chr.ivo_veyra` | Inventor; crescent coat, asymmetric tool rig | 1 hero | 1,150 tris; 3 mats; 64×64 CI8 body + 32×32 CI4 face | 24 joints; shared 12-clip base + 6 invention/reunion clips | `DLG CNV` | `S4 P1` |
| `chr.rusk` | Estate assistant/opponent; squared apron and defensive triangle | 1 hero | 1,050 tris; 3 mats; 64×64 CI8 body + 32×32 CI4 face | 22 joints; shared 12-clip base + 11 wrench/confrontation/battle/restoration/apology clips | `DLG BTL UI SAV CNV` | `S4 P1` |
| `chr.mara_ovelle` | Clinic technician; curved smock and scanning loop silhouette | 1 support | 720 tris; 2 mats; 64×64 CI4 body + 16×16 face | 18 joints; base + 3 clinic/optional-dialogue clips | `EXP DLG CNV` | `S4 P2` |
| `chr.jo_renn` | Workshop machinist and Field Relay custodian; blocky apron/tool stance | 1 support | 760 tris; 3 mats; 64×64 CI4 body + 16×16 face | 20 joints; shared 12-clip base + 5 work/Relay-handoff clips | `EXP DLG UI CNV` | `S4 P1` |
| `chr.pell_anwar` | Comms/cartography analyst; layered map panels and headset arc | 1 support | 700 tris; 2 mats; 64×64 CI4 body + 16×16 face | 18 joints; shared 12-clip base + 4 reader/console/optional-dialogue clips | `EXP DLG MAP CNV` | `S4 P2` |

Humanoid texture working set target for a dialogue scene: no more than 32 KiB across three visible humans, including face states. Distance meshes are loaded only where persistent long views justify them.

## 4. Echoforms and battle-slot resolution

The roster is locked at eight unique creatures. Tutorial loans are simulation-only visual/data assets; the real starters are separate designs and remain the player party through the Estate battle. Rusk’s opponents are separate again. No model, texture, silhouette, portrait, vocal bank, or name is reused between the eight slots. Shared base VFX sprites and audio layers are allowed only when the composed move event remains distinct.

Affinity cycle: `CURRENT > EMBER > GALE > STRATA > CURRENT`; strong multiplier 1.5× (Q8.8 `384`), resisted multiplier 0.75× (Q8.8 `192`), and neutral multiplier 1.0× (Q8.8 `256`). The only temporary ailment is `STAGGERED`; Power/Guard/Speed stages and Guiding Draft’s one-use `EMPOWERED` presentation are volatile modifiers, not statuses.

| Asset ID | Battle slot / design | Affinity and four moves | Geometry / texture / rig | Required clips | Stage / priority |
|---|---|---|---|---|---|
| `echo.quarrune` | **Quarrune** — real starter A; compact six-legged ceramic ram, cobalt horn lattice, tank/support | Strata: Ridge Ram; Brace Relay; Grounding Ring; Steady Pulse | 1,250 / 650 tris; 3 mats; 64×64 CI8 + 32×32 CI4; 20 joints | 14 total; `S1` owns idle A/B, entrance, reposition, Ridge Ram, Brace Relay, hit, knockout, and Horizon Break participation preview; remaining clips are `S4` | `S1/S4 P0` |
| `echo.ayselor` | **Ayselor** — real starter B; hovering tri-wing manta/kite, clothlike fins, amber keel lamp | Gale: Sirocco Slice; Lift Current; Dazzle Wake; Guiding Draft | 1,150 / 600 tris; 3 mats; 64×64 CI8 + 32×32 CI4; 18 joints | 15 including all four moves, Horizon Break, packet answer, lamp-dim alert, and story resolve | `S4 P1` |
| `echo.kilnback` | **Kilnback** — simulation player loan A; broad quadruped kiln body, furnace ribs | Ember: Cinder Charge; Bellows Guard; Scorch Mark; Banked Flame | 1,300 / 680 tris; 3 mats; 64×64 CI8 + 32×32 CI4; 18 joints | 12 including all four moves and Sunline Cascade | `S4 P1` |
| `echo.nacreel` | **Nacreel** — simulation player loan B; ribbon body and broken halo of conductive droplets | Current: Arc Jet; Conductive Veil; Flow Switch; Static Ripple | 1,100 / 560 tris; 4 mats; 64×64 CI8 + 32×32 IA8; 20 joints | 12 including all four moves and Sunline Cascade | `S4 P1` |
| `echo.gyreclast` | **Gyreclast** — simulation opponent A; three-legged mineral excavator, offset drill claw | Strata: Auger Knuckle; Dust Screen; Fault Pin; Carapace Brace | 1,200 / 620 tris; 3 mats; 64×64 CI8 + 32×32 CI4; 18 joints | 11 including all four moves | `S4 P1` |
| `echo.kivarrax` | **Kivarrax** — simulation opponent B; long-legged fan-tailed desert runner | Gale: Crosswind Cut; Slipstream; Pressure Drop; Talon Sweep | 1,050 / 540 tris; 3 mats; 64×64 CI8 + 32×32 CI4; 20 joints | 11 including all four moves | `S4 P1` |
| `echo.kovrass` | **Kovrass** — Estate opponent A; low brass/ceramic bellows body; support showcase | Ember: Clinker Bite; Boiler Chorus; Ash Mantle; Furnace Feint | 1,200 / 620 tris; 3 mats; 64×64 CI8 + 32×32 CI4; 18 joints | 11 including all four moves | `S4 P1` |
| `echo.ulvorel` | **Ulvorel** — Estate opponent B; squat amphibious body, translucent hood, pendulum throat | Current: Rill Lash; Pressure Leap; Cooling Shroud; Undertow | 1,150 / 590 tris; 4 mats; 64×64 CI8 + 32×32 IA8; 20 joints | 11 including all four moves | `S4 P1` |

Estate support showcase dependency: `echo.kovrass` must perform Boiler Chorus, visibly raising Ulvorel’s Power, followed by Ulvorel’s Pressure Leap. Model sockets, animation event frames, VFX, UI modifier feedback, and audio must support that readable sequence.

Maximum four-active-actor battle texture working set: 176 KiB including portraits and VFX sprite atlas. Maximum actor geometry target: 6,000 visible triangles including distance-independent accessories.

## 5. Authored environment and world-map source packages

Every room package includes render sectors, complete floor/walls/ceiling or sky enclosure, portals, occluder/culling metadata, lighting/vertex-color pass, collision reference, interaction sockets, camera-safe volumes, audio zones, and a room-specific dressing manifest. The triangle totals are full authored packages; visible-sector caps still apply.

| Environment ID | Required finished scope and landmark view | Render budget | Runtime texture cap | Collision ID | Dependencies | Stage / priority |
|---|---|---:|---:|---|---|---|
| `env.annex.threshold` | Exterior apron, shade, antenna/skimmer view, sealable entry, desert boundary | 5,000 tris / 3 sectors | 72 KiB | `col.annex.threshold` | `EXP DLG CNV` | `S4 P1` |
| `env.annex.sim_chamber` | Four-actor simulation ring, dissolve shell, observation bay, transition into Annex; all three final sectors remain post-benchmark production | 5,500 / 3 sectors | 80 KiB | `col.annex.sim_chamber` | `BTL DLG VFX CNV` | `S4 P1` |
| `env.annex.atrium_lower` | Main route, Resonance monitor base, clinic/workshop approaches, elevator; only non-ID sub-sector `sector.atrium_lower.sim_threshold_corner` is `S1`, remaining three sectors are `S4` | 6,500 / 4 sectors; benchmark sector 1,600–2,200 tris within total | 96 KiB shared; benchmark working subset ≤72 KiB | `col.annex.atrium_lower` | `EXP DLG CNV` | `S1/S4 P0` |
| `env.annex.atrium_upper` | Balcony loop, director/player-room approaches, skylight frame | 5,000 / 3 sectors | shared with lower | `col.annex.atrium_upper` | `EXP DLG CNV` | `S4 P1` |
| `env.annex.director_lab` | Oren’s workspace, beacon-analysis wall, story blocking positions | 3,800 / 2 sectors | 64 KiB | `col.annex.director_lab` | `EXP DLG SAV CNV` | `S4 P1` |
| `env.annex.player_room` | Bed, locker, save point, personal field details, complete walls/ceiling | 2,800 / 2 sectors | 48 KiB | `col.annex.player_room` | `EXP SAV CNV` | `S4 P1` |
| `env.annex.clinic_bay` | Two Echoform care stations, Mara’s work area, starter onboarding staging | 4,500 / 3 sectors | 72 KiB | `col.annex.clinic_bay` | `EXP DLG CNV` | `S4 P1` |
| `env.annex.workshop` | Jo’s Relay bench, repair tools, active mechanisms, handoff blocking | 4,800 / 3 sectors | 72 KiB | `col.annex.workshop` | `EXP DLG UI CNV` | `S4 P1` |
| `env.annex.elevator` | Cab, both landings, gate/door motion, safe transition occluder | 1,600 / 2 sectors | 32 KiB | `col.annex.elevator` | `EXP DLG CNV` | `S3 interface / S4 final P0` |
| `env.annex.circulation` | Connecting halls, door reveals, route junctions, no unfinished backs | 5,500 / 5 sectors | 64 KiB shared | `col.annex.circulation` | `EXP CNV` | `S4 P1` |
| `env.estate.courtyard` | Gate, observatory landmark, battle footprint, kinetic inventions, energy fountain, dressing | 8,500 / 6 sectors | 128 KiB | `col.estate.courtyard` | `EXP BTL DLG VFX CNV` | `S4 P1` |
| `env.estate.foyer_gallery` | Entry reveal, gallery circuit, apology transition, complete portal views | 3,800 / 3 sectors | 64 KiB | `col.estate.foyer_gallery` | `EXP DLG CNV` | `S4 P1` |
| `env.estate.invention_hall` | Traversable mechanism gallery, optional examine points, safe moving props | 6,500 / 5 sectors | 96 KiB | `col.estate.invention_hall` | `EXP DLG VFX CNV` | `S4 P1` |
| `env.estate.observatory_study` | Telescope control, Ivo/Tavi reunion, window/dome vista, clue staging | 5,000 / 3 sectors | 80 KiB | `col.estate.observatory_study` | `EXP DLG FOL CNV` | `S4 P1` |
| `env.estate.circulation` | Courtyard-to-interior and room connectors, door/companion-safe portals | 3,500 / 4 sectors | 48 KiB shared | `col.estate.circulation` | `EXP FOL CNV` | `S4 P1` |
| `env.world_map.desert_relief` | Original relief map, Annex and Estate nodes, skimmer token, route pulse, travel camera | 2,400 tris | 64 KiB | `col.world_map.nodes` | `MAP UI SAV VFX CNV` | `S3 interface / S4 final P0` |

Location atlas plan:

- Annex: one 64×64 CI8 architectural atlas, two 64×32 CI4 trim/glyph atlases, one 32×32 IA8 mask atlas, and room-local 32×32 accents. Resident room cap still applies.
- Estate: one 64×64 CI8 architectural atlas, one 64×64 CI4 instrument atlas, one 64×32 CI4 trim/glyph atlas, one 32×32 IA8 energy mask, and room-local accents.
- Desert/world map: one 64×64 CI8 relief atlas plus 32×32 CI4 nodes and IA8 route mask.

## 6. Landmark assets

| Asset ID | Purpose | Budget | Motion / dependency | Stage / priority |
|---|---|---:|---|---|
| `lmk.annex.resonance_monitor` | Closing Fracture reaction and atrium navigation anchor | 1,200 tris; 3 mats; 64×64 + 32×32 mask | monitor trace, iris, Fracture event; `DLG VFX SAV` | `S4 P1` |
| `lmk.annex.simulation_ring` | Tutorial staging and chamber-to-atrium dissolve | 1,400 tris; 3 mats | ring segments, emitters; `BTL VFX` | `S1 P0` |
| `lmk.annex.skylight_spine` | Unifies two atrium levels and route readability | 1,000 tris; 2 mats | static light/culling anchor | `S1 P0` |
| `lmk.annex.antenna_array` | Exterior identity and map-node silhouette | 1,100 tris; 2 mats | slow aim motion; `MAP` | `S4 P2` |
| `lmk.estate.observatory_dome` | Estate identity from courtyard and map | 1,500 tris; 3 mats | slit/dome mechanism; `DLG` | `S4 P1` |
| `lmk.estate.orbital_fountain` | Courtyard route anchor and energy apparatus | 1,300 tris; 3 mats | three rings, controlled particles; `VFX` | `S4 P1` |
| `lmk.estate.kinetic_tower` | Moving exterior silhouette and environmental story | 1,400 tris; 3 mats | counterweighted vanes; `VFX` | `S4 P2` |
| `lmk.estate.grand_orrery` | Invention-hall focal mechanism | 1,450 tris; 3 mats | nested orbital motion; `DLG` | `S4 P1` |

### 6.1 Field vehicle

| Asset ID | Purpose / count | Geometry / materials / textures | Rig / clips | Dependencies | Stage / priority |
|---|---|---|---|---|---|
| `veh.meridian.sand_skimmer` | Annex departure hero model + simplified world-map travel model | 980 / 220 tris; 3 / 2 mats; 64×64 CI8 body + 32×32 CI4 runner/relay accents | 6 mechanism joints; idle_suspension, board_depart, travel_loop, arrive_settle | `EXP MAP DLG AUD CNV` | `S4 P1` |

## 7. Purposeful prop inventory

The 63 designs below exceed the minimum of 25. `Qty` is the planned maximum authored placement count, not permission to load every instance simultaneously. Each prop must show a use, owner, route function, or recent action. Instances use deliberate rotation, state, vertex color, and wear variation; scale jitter is not a sufficient variation pass.

### 7.1 Meridian Annex props

| Asset ID | Prop / purpose | Qty | Tri cap | Texture / motion | Stage / priority |
|---|---|---:|---:|---|---|
| `prop.annex.field_relay` | Hero handheld interface retrieved from Jo and inserted into Pell’s reader | 1 | 360 | 32×32 CI8; `anm.mech.field_relay_integration`, `anm.player.ari.relay_side_reader` | `S1 P0` |
| `prop.annex.relay_dock` | Workshop acquisition dock visibly releases the same hero Relay into Jo’s hand | 1 | 140 | shared instrument atlas; `anm.mech.field_relay_integration`, `sfx.environment.relay_dock_release` | `S4 P1` |
| `prop.annex.director_relay_cradle` | Distinct empty Director-lab instrument cradle framed during Oren's assignment; never substitutes for Jo's functional workshop dock | 1 | 120 | shared instrument atlas; inactive amber socket glyph, static/readable from dialogue camera | `S4 P1` |
| `prop.annex.relay_side_reader` | Pell’s keyed side reader accepts the hero Relay and projects the route header | 1 | 260 | shared + IA8 trace; `anm.mech.field_relay_integration`, `ui.panel.relay_trace`, insert/trace/release SFX | `S4 P1` |
| `prop.annex.calibration_locator_tag` | Tavi’s physical calibration target, visibly retained on the satchel/reunion staging | 1 | 96 | 16×16 CI8 + IA8 pulse; `anm.prop.calibration_locator_tag`, `sfx.story.locator_tag_ping` | `S4 P1` |
| `prop.annex.monitor_console` | Resonance-monitor operator station | 2 | 420 | shared + IA8 screen | `S1 P0` |
| `prop.annex.sim_dais` | Four actor footprint pads | 4 | 240 each | shared ceramic; emitter pulse | `S1 P0` |
| `prop.annex.sim_emitter` | Chamber dissolve projector | 6 | 180 | shared teal; shutter | `S1 P0` |
| `prop.annex.clinic_cradle` | Echoform care station | 2 | 480 | shared clinic; arm motion | `S4 P1` |
| `prop.annex.diagnostic_arm` | Mara’s scanning tool | 2 | 300 | shared; 4-joint mechanism | `S4 P2` |
| `prop.annex.specimen_vessel` | Non-living mineral/resonance sample | 5 | 180 | 32×32 CI4 + IA8 | `S4 P2` |
| `prop.annex.workbench` | Jo’s repair/handoff surface | 2 | 340 | shared trim | `S4 P1` |
| `prop.annex.tool_wall` | Painted tool outlines, including three empty Tavi-sized slots | 1 | 260 | shared tool atlas and authored outlines | `S4 P1` |
| `prop.annex.coil_spool` | Routed power/service cable | 4 | 120 | shared metal | `S4 P2` |
| `prop.annex.elevator_console` | Floor/state feedback | 2 | 100 | icon atlas; button motion | `S3 interface / S4 final P0` |
| `prop.annex.cargo_tote` | Reusable field equipment container | 6 | 160 | shared ceramic | `S4 P2` |
| `prop.annex.water_condenser` | Explains outpost desert survival | 2 | 460 | shared; fan/drop cues | `S4 P2` |
| `prop.annex.wall_fan` | Active ventilation and ambient sound source | 5 | 180 | 2-joint rotor | `S4 P2` |
| `prop.annex.shade_canopy` | Exterior shadow structure | 3 | 420 | 64×32 CI4 cloth | `S4 P2` |
| `prop.annex.director_desk` | Oren blocking and beacon briefing | 1 | 320 | shared furniture | `S4 P1` |
| `prop.annex.map_table` | Pell cartography/examine point | 1 | 560 | shared + IA8 route mask | `S4 P1` |
| `prop.annex.locker` | Player/staff storage and room dressing | 7 | 160 | shared; door variant | `S4 P2` |
| `prop.annex.player_bed` | Personal room save/rest anchor | 1 | 260 | 64×32 CI4 cloth | `S4 P1` |
| `prop.annex.message_terminal` | Optional lore and Field Relay message language | 4 | 220 | shared + UI glyphs | `S4 P2` |
| `prop.annex.beacon_decoder` | Pell’s Solace-signature station and moving-trace source | 1 | 380 | shared + IA8 trace; `anm.mech.beacon_decoder`; `sfx.story.hook_two_note_low_third` at packet resolution | `S4 P1` |
| `prop.annex.stack_chair` | Workstation seating with occupied/stacked states | 10 | 110 | shared furniture | `S4 P2` |
| `prop.annex.floor_cable_ramp` | Safe visible service crossing, included in collision | 4 | 80 | shared rubber/metal | `S3 interface / S4 final P1` |
| `prop.annex.waste_sorter` | Lived-in lab utility with three diagram slots | 2 | 140 | shared ceramic/glyph | `S4 P2` |
| `prop.annex.solace_model` | Director-lab carrier model with intentional `SOLACE` nameplate glyphs and hook practical | 1 | 520 | 64×32 CI4 vehicle/glyph atlas; `anm.prop.solace_model` owns tail/practical-light states | `S4 P1` |
| `prop.annex.player_shelf` | Desert-glass shard, field notebook, and empty Relay space | 1 set | 240 | shared room atlas + 32×32 CI4 personal accents | `S4 P1` |

### 7.2 Veyra Estate props

| Asset ID | Prop / purpose | Qty | Tri cap | Texture / motion | Stage / priority |
|---|---|---:|---:|---|---|
| `prop.estate.sun_dial` | Courtyard time/weather story | 1 | 520 | shared brass/ceramic | `S4 P2` |
| `prop.estate.wind_harp` | Gale-responsive silhouette and ambience | 2 | 440 | shared; string/vane motion | `S4 P2` |
| `prop.estate.counterweight_walker` | Safe kinetic invention exhibit | 1 | 680 | shared; 6-joint loop | `S4 P1` |
| `prop.estate.courtyard_bench` | Conversation/rest composition | 3 | 160 | shared furniture | `S4 P2` |
| `prop.estate.ceramic_planter` | Softens routes and anchors vegetation | 6 | 180 | shared ceramic | `S4 P2` |
| `prop.estate.drought_reeds` | Authored cluster with dust response | 8 clusters | 140 | 32×32 CI4 cutout | `S4 P2` |
| `prop.estate.gate_latch` | Rusk entry blocking and post-battle unlock | 1 | 120 | shared; latch animation | `S3 interface / S4 final P0` |
| `prop.estate.rusk_wrench` | Rusk’s gate-work tool, dropped on the cut-wave chirp and settled clear of combat | 1 | 120 | shared metal; `anm.rusk.wrench_work/wrench_drop`, `sfx.story.rusk_wrench_drop` | `S4 P1` |
| `prop.estate.star_projector` | Bottled-star projector that reacts when Ayselor passes | 2 | 480 | instrument atlas + IA8 | `S4 P1` |
| `prop.estate.table_orrery` | Small readable orbital demonstration | 2 | 620 | shared; 6-joint loop | `S4 P2` |
| `prop.estate.gyroscope` | Kinetic invention-hall obstacle/dressing | 2 | 460 | shared; nested rotation | `S4 P1` |
| `prop.estate.impossible_compass` | Optional examine object with several deliberately disagreeing needles | 1 | 280 | instrument atlas; `anm.prop.impossible_compass`, `sfx.environment.compass_needles` | `S4 P1` |
| `prop.estate.lens_cabinet` | Stores optics and frames a safe wall route | 2 | 300 | shared + 32×32 CI8 glass | `S4 P2` |
| `prop.estate.invention_pedestal` | Consistent examine staging | 6 | 140 | shared ceramic/glyph | `S4 P2` |
| `prop.estate.spiral_lift_model` | Optional mechanical miniature | 1 | 540 | shared; screw motion | `S4 P2` |
| `prop.estate.walking_desk` | Four padded feet advance an instrument desk through a safe tiny loop | 1 | 420 | shared; 6-joint loop and safety stop | `S4 P1` |
| `prop.estate.study_desk` | Ivo/Tavi reunion blocking | 1 | 340 | shared furniture | `S4 P1` |
| `prop.estate.ivo_track_roll` | Physical paper roll Ivo compares against the orrery track during discovery | 1 | 180 | 32×32 CI8 authored track; `anm.ivo_veyra.compare_track_roll`, `sfx.environment.paper_roll` | `S4 P1` |
| `prop.estate.observatory_chair` | Telescope operator station | 1 | 180 | shared; swivel | `S4 P2` |
| `prop.estate.packet_recorder` | Records the observatory packet and answers Ayselor’s keel lamp during reunion | 1 | 380 | shared + IA8 screen; `anm.prop.packet_recorder`, `anm.echo.ayselor.story_packet_ping`, `sfx.story.packet_recorder_answer` | `S4 P1` |
| `prop.estate.tavi_satchel` | Scene-specific hide-and-seek clue/character prop | 1 | 180 | 32×32 CI4 cloth | `S4 P1` |
| `prop.estate.tool_carousel` | Circular organized work storage | 2 | 400 | shared; indexed turn | `S4 P2` |
| `prop.estate.gallery_frame` | Original diagram/art display frame | 8 | 100 | curated 32×32 CI4 inserts | `S4 P2` |
| `prop.estate.tea_service` | Human-scale recent-activity story | 1 set | 160 | shared ceramic | `S4 P2` |
| `prop.estate.cable_bridge` | Overhead service connection and leading line | 3 | 260 | shared metal/cable | `S4 P2` |
| `prop.estate.folding_ladder` | Observatory maintenance evidence | 1 | 220 | shared metal | `S4 P2` |
| `prop.estate.weather_vane` | Exterior movement and Gale motif | 2 | 340 | shared; 2-joint aim | `S4 P2` |
| `prop.estate.shade_sail` | Courtyard value control and Estate cloth language | 3 | 280 | 64×32 CI4 cloth | `S4 P1` |
| `prop.estate.courtyard_tracks` | Fresh narrow crawler-stop-to-door footprints, authored as a readable clue | 1 trail | 80 | 32×32 IA4 decal/cutout, no collision | `S4 P1` |
| `prop.estate.rain_clock` | Measures time since rain with one intentionally still hand | 1 | 360 | instrument atlas; 5-joint slow mechanism | `S4 P1` |
| `prop.estate.orrery_switch` | Polished brass hold-switch that rotates the model sky, clears the blocking arm, and opens the study stair through an interruption-safe state transaction | 1 | 180 | shared brass; `anm.prop.orrery_switch`, `anm.mech.grand_orrery`, `sfx.environment.orrery`; collision handoff through `col.estate.invention_hall` | `S3 interface / S4 final P0` |
| `prop.estate.study_logbook` | Authored readable story line, no generated or fake writing | 1 | 160 | 32×32 CI8 approved glyph page | `S4 P1` |
| `prop.estate.telescope_controls` | Warm eyepiece, alignment controls, violet-dust continuity accent | 1 set | 620 | instrument atlas + 32×32 CI8 lens; aim dials | `S4 P1` |

## 8. Collision, navigation, and camera-support assets

Collision meshes are manually simplified, manifold where appropriate, and reviewed in a diagnostic render. Decorative concavity is removed. Steps, thresholds, door sweeps, companion width, battle footprints, and camera clamp volumes are tested separately.

| Collision ID | Scope | Triangle cap | Required tests | Stage / priority |
|---|---|---:|---|---|
| `col.annex.threshold` | Apron, ramp, desert bounds, entry portal | 220 | no fall-out; route and camera boundary; player/Tavi portal sweep, follower handoff, obstruction recovery | `S3 P0` |
| `col.annex.sim_chamber` | Ring floor, observation edge, exits | 180 | four actor anchors; no dissolve trap | `S2 P0` |
| `col.annex.atrium_lower` | Main floor, stairs/ramps, props, elevator queue; only collision bounded to `sector.atrium_lower.sim_threshold_corner` is final `S1` | 420 total; benchmark subset measured separately | benchmark player/camera sweep; full player/follower path sweep at `S3` | `S1/S3 P0` |
| `col.annex.atrium_upper` | Balcony, rails, room portals | 300 | no rail vault/fall; camera clamp | `S3 P0` |
| `col.annex.director_lab` | Room shell, desk blocking, dialogue marks | 140 | enter/exit after repeat scenes | `S3 P1` |
| `col.annex.player_room` | Shell, bed/locker blockers | 110 | save interaction and door recovery | `S3 P1` |
| `col.annex.clinic_bay` | Care stations and starter staging | 180 | no trap behind cradles | `S3 P1` |
| `col.annex.workshop` | Bench, cable ramp, Relay handoff | 190 | interaction approach and cancel | `S3 P1` |
| `col.annex.elevator` | Moving cab floor, door gates, both landings | 120 | disconnect/reconnect; follower warp recovery | `S3 P0` |
| `col.annex.circulation` | Halls, portals, safe wall offsets | 240 | all route loops; camera corner clamp | `S3 P0` |
| `col.estate.courtyard` | Exterior ground, fountain, inventions, battle zone | 480 | no prop trap; battle snapshot restore | `S3 P0` |
| `col.estate.battle_arena` | Four actor anchors and camera-safe perimeter | 64 | all animation bounds and target cameras | `S3 P0` |
| `col.estate.foyer_gallery` | Room, frames, entry doors | 150 | follower through opened gate | `S3 P1` |
| `col.estate.invention_hall` | Static blockers, moving-mechanism safety hulls, and orrery-arm/study-stair state collision | 260 | no crush/trap; held-switch interrupt/reset; arm-clear/open-stair handoff; examine recovery | `S3 P0` |
| `col.estate.observatory_study` | Study shell, desk, telescope approach | 180 | reunion blocking/follower exit | `S3 P0` |
| `col.estate.circulation` | Halls, stairs, companion-safe portals | 200 | follower never blocks player | `S3 P0` |
| `col.world_map.nodes` | Annex/Estate selection hit regions | 12 | stick/d-pad selection and cancel | `S2 P0` |
| `col.common.camera_volumes` | Authored soft/hard camera clamp boxes per room; exact benchmark exploration/battle clamps are final `S1` | data-only | benchmark camera/readability proof; full no-wall-clipping/hidden-objective matrix at `S3` | `S1/S3 P0` |

### 8.1 Navigation and spawn assets

Navigation is authored independently of render and collision meshes. Spawn tables contain stable entry, door, elevator, battle, dialogue-blocking, follower-handoff, and off-camera safe-recovery anchors as relevant. Every anchor stores position, facing, capsule-clearance result, camera-safe flag, and story-condition mask.

| Nav asset ID | Zone / coverage | Nodes / directed edges | Spawn-table asset ID | Spawn/safe anchors | Interaction index / records | Dependencies | Stage / priority |
|---|---|---:|---|---:|---|---|---|
| `nav.sim.arena` | `ZONE_SIM_ARENA`; four battle lanes and presentation clearances | 8 / 12 | `spn.sim.arena` | 10 | `int.sim.arena` / 0 validated exploration records | `BTL DLG` | `S2 P0` |
| `nav.annex.sim_room` | `ZONE_ANNEX_SIMULATION_ROOM`; chamber exit and onboarding marks | 12 / 18 | `spn.annex.sim_room` | 6 | `int.annex.sim_room` / 4 | `EXP DLG` | `S3 P0` |
| `nav.annex.atrium` | `ZONE_ANNEX_ATRIUM`; both levels, elevator, circulation, recovery | 36 / 58 | `spn.annex.atrium` | 18 | `int.annex.atrium` / 12 | `EXP DLG FOL` | `S3 P0` |
| `nav.annex.director_lab` | `ZONE_ANNEX_DIRECTOR_LAB`; desk and dialogue approaches | 12 / 20 | `spn.annex.director_lab` | 6 | `int.annex.director_lab` / 5 | `EXP DLG` | `S3 P0` |
| `nav.annex.player_room` | `ZONE_ANNEX_PLAYER_ROOM`; door, save point, bed/locker recovery | 8 / 12 | `spn.annex.player_room` | 4 | `int.annex.player_room` / 4 | `EXP SAV` | `S3 P0` |
| `nav.annex.clinic` | `ZONE_ANNEX_CLINIC`; cradle loop and starter presentation | 16 / 24 | `spn.annex.clinic` | 8 | `int.annex.clinic` / 7 | `EXP DLG` | `S3 P0` |
| `nav.annex.workshop` | `ZONE_ANNEX_WORKSHOP`; Relay bench and mechanism clearances | 18 / 28 | `spn.annex.workshop` | 8 | `int.annex.workshop` / 9 | `EXP DLG UI` | `S3 P0` |
| `nav.annex.threshold` | `ZONE_ANNEX_THRESHOLD`; interior/exterior/map transition, Tavi map-arrival handoff, follower path to atrium portal, off-camera separation recovery, and desert recovery | 14 / 22 | `spn.annex.threshold` | 8 including dedicated follower handoff/recovery anchors | `int.annex.threshold` / 6 | `EXP MAP FOL` | `S3 P0` |
| `nav.world_map.desert` | `ZONE_WORLD_MAP_DESERT`; two selectable route nodes | 2 / 2 | `spn.world_map.desert` | 2 | `int.world_map.desert` / 2 | `MAP UI` | `S2 P0` |
| `nav.estate.courtyard` | `ZONE_ESTATE_COURTYARD`; exploration, prebattle, four lanes, postbattle, gate | 32 / 52 | `spn.estate.courtyard` | 16 | `int.estate.courtyard` / 10 | `EXP BTL DLG FOL` | `S3 P0` |
| `nav.estate.foyer` | `ZONE_ESTATE_FOYER`; gate handoff, gallery loop, follower recovery | 14 / 22 | `spn.estate.foyer` | 8 | `int.estate.foyer` / 6 | `EXP DLG FOL` | `S3 P0` |
| `nav.estate.invention_hall` | `ZONE_ESTATE_INVENTION_HALL`; safe mechanism paths and examines | 28 / 46 | `spn.estate.invention_hall` | 14 | `int.estate.invention_hall` / 14 | `EXP DLG FOL` | `S3 P0` |
| `nav.estate.observatory_study` | `ZONE_ESTATE_OBSERVATORY_STUDY`; reunion staging and return portal | 18 / 28 | `spn.estate.observatory_study` | 10 | `int.estate.observatory_study` / 10 | `EXP DLG FOL` | `S3 P0` |

The mandatory follower-return chain is exact and continuous:
`nav.estate.observatory_study` -> `nav.estate.invention_hall` ->
`nav.estate.foyer` -> `nav.estate.courtyard` -> `nav.world_map.desert` ->
`nav.annex.threshold` -> `nav.annex.atrium`. Each physical-zone pack on that chain
contains a Tavi-compatible portal/handoff pair and safe recovery anchor; the
world-map pack owns the nonphysical route handoff. `nav.annex.threshold` is not
an ordinary no-follower arrival pack on `TRANS_DEF_MAP_RETURN_TO_ANNEX`: its
follower nodes remain active until `TRANS_DEF_THRESHOLD_TO_ATRIUM` transfers
both actors. Asset validation rejects a missing `FOL` dependency, absent anchor,
collision test without the follower capsule, or any gap in this exact chain.

### 8.2 Zone-to-bundle implementation map

`Required` bundles contain the zone shell, collision, nav, spawn table, mandatory actor set, and essential UI/data. `Optional` bundles contain noncritical dressing/examine content. `Action` bundles contain battle/cutscene actors, animations, VFX, audio, and screen-specific UI and are destroyed immediately after their action fence. Arena cap includes required + currently loaded optional + current action; it is never the sum of independent maxima.

| Stable ZoneId | Authored environment/source | Required bundle | Optional bundle | Action bundle | Generated collision asset | Nav / spawn / interaction | Arena cap |
|---|---|---|---|---|---|---|---:|
| `ZONE_SIM_ARENA` | `env.annex.sim_chamber` physical base obscured by virtual presentation + `lmk.annex.simulation_ring` | `bnd.annex.sim_room.base` | — | `bnd.sim.tutorial_overlay` | `COL_ANNEX_SIM_ROOM` from `col.annex.sim_chamber` | `nav.sim.arena` / `spn.sim.arena` / `int.sim.arena` | 1,040 KiB |
| `ZONE_ANNEX_SIMULATION_ROOM` | Same already-loaded `env.annex.sim_chamber` physical base after dissolve | `bnd.annex.sim_room.base` | `bnd.annex.sim_room.optional` | `bnd.annex.sim_room.onboarding` | Same resident `COL_ANNEX_SIM_ROOM`; no reload | `nav.annex.sim_room` / `spn.annex.sim_room` / `int.annex.sim_room` | 900 KiB |
| `ZONE_ANNEX_ATRIUM` | `env.annex.atrium_lower`, `atrium_upper`, `elevator`, `circulation` | `bnd.annex.atrium.required` | `bnd.annex.atrium.optional` | `bnd.annex.atrium.story` | `COL_ANNEX_ATRIUM` composed from lower/upper/elevator/circulation collision sources | `nav.annex.atrium` / `spn.annex.atrium` / `int.annex.atrium` | 1,000 KiB |
| `ZONE_ANNEX_DIRECTOR_LAB` | `env.annex.director_lab` | `bnd.annex.director.required` | `bnd.annex.director.optional` | `bnd.annex.director.story` | `COL_ANNEX_DIRECTOR` from `col.annex.director_lab` | `nav.annex.director_lab` / `spn.annex.director_lab` / `int.annex.director_lab` | 800 KiB |
| `ZONE_ANNEX_PLAYER_ROOM` | `env.annex.player_room` | `bnd.annex.player_room.required` | `bnd.annex.player_room.optional` | — | `COL_ANNEX_PLAYER_ROOM` from `col.annex.player_room` | `nav.annex.player_room` / `spn.annex.player_room` / `int.annex.player_room` | 700 KiB |
| `ZONE_ANNEX_CLINIC` | `env.annex.clinic_bay` | `bnd.annex.clinic.required` | `bnd.annex.clinic.optional` | `bnd.annex.clinic.onboarding` | `COL_ANNEX_CLINIC` from `col.annex.clinic_bay` | `nav.annex.clinic` / `spn.annex.clinic` / `int.annex.clinic` | 900 KiB |
| `ZONE_ANNEX_WORKSHOP` | `env.annex.workshop` | `bnd.annex.workshop.required` | `bnd.annex.workshop.optional` | `bnd.annex.workshop.relay` | `COL_ANNEX_WORKSHOP` from `col.annex.workshop` | `nav.annex.workshop` / `spn.annex.workshop` / `int.annex.workshop` | 900 KiB |
| `ZONE_ANNEX_THRESHOLD` | `env.annex.threshold` | `bnd.annex.threshold.required` | `bnd.annex.threshold.optional` | `bnd.annex.threshold.map_exit` | `COL_ANNEX_THRESHOLD` from `col.annex.threshold` | `nav.annex.threshold` / `spn.annex.threshold` / `int.annex.threshold` | 850 KiB |
| `ZONE_WORLD_MAP_DESERT` | `env.world_map.desert_relief` | `bnd.map.required` | — | `bnd.map.travel` | `COL_WORLD_MAP_NODES` from `col.world_map.nodes` | `nav.world_map.desert` / `spn.world_map.desert` / `int.world_map.desert` | 600 KiB |
| `ZONE_ESTATE_COURTYARD` | `env.estate.courtyard` | `bnd.estate.courtyard.required` | `bnd.estate.courtyard.optional` | `bnd.estate.courtyard.battle` or `bnd.estate.courtyard.story`, never both | `COL_ESTATE_COURTYARD` + action-only `COL_ESTATE_BATTLE` | `nav.estate.courtyard` / `spn.estate.courtyard` / `int.estate.courtyard` | 1,040 KiB |
| `ZONE_ESTATE_FOYER` | `env.estate.foyer_gallery` + circulation portal | `bnd.estate.foyer.required` | `bnd.estate.foyer.optional` | `bnd.estate.foyer.entry` | `COL_ESTATE_FOYER` from `col.estate.foyer_gallery` | `nav.estate.foyer` / `spn.estate.foyer` / `int.estate.foyer` | 750 KiB |
| `ZONE_ESTATE_INVENTION_HALL` | `env.estate.invention_hall` + circulation portal | `bnd.estate.hall.required` | `bnd.estate.hall.optional` | `bnd.estate.hall.examine` | `COL_ESTATE_HALL` from `col.estate.invention_hall` | `nav.estate.invention_hall` / `spn.estate.invention_hall` / `int.estate.invention_hall` | 950 KiB |
| `ZONE_ESTATE_OBSERVATORY_STUDY` | `env.estate.observatory_study` + circulation portal | `bnd.estate.study.required` | `bnd.estate.study.optional` | `bnd.estate.study.reunion` | `COL_ESTATE_STUDY` from `col.estate.observatory_study` | `nav.estate.observatory_study` / `spn.estate.observatory_study` / `int.estate.observatory_study` | 900 KiB |
| `ZONE_END_CARD_UI` | UI-only `ui.screen.chapter_end`; no environment reuse | `bnd.ui.chapter_end` | — | — | none | none; `NO_PLAYER_CONTROL`, no spawn required | 48 KiB UI-shell media |

`SCENE_SIM_ARENA` enters with `bnd.annex.sim_room.base` already resident and then loads only `bnd.sim.tutorial_overlay`. Tutorial completion render-fences and destroys the overlay actors, battle UI, VFX, audio, and virtual shell; it retains the physical base, transfers its owner token to `SCENE_ANNEX_INTERIOR`, switches to the physical chamber nav/spawn/interaction set, and loads only the onboarding action. There is no second heavy simulation-room base and no empty frame between modes.

The closing `HOOK_*` sequence is `bnd.annex.atrium.hook`, an action overlay on the already-loaded `ZONE_ANNEX_ATRIUM` base and its existing collision/nav/spawn/interaction assets. After the hook, a fade render-fences and destroys the hook plus atrium scene scope. `SCENE_END_CHAPTER` then loads only `bnd.ui.chapter_end` under its own UI-only `ZONE_END_CARD_UI`; it allocates no duplicate environment or closing-monitor `ZoneId`.

### 8.3 ID namespaces and approved mappings

Production-package IDs, story/content IDs, and runtime asset IDs are distinct typed namespaces. A dotted inventory/ledger row identifies the authored package and its provenance; `CreatureId` and `CharacterId` identify gameplay content; generated `AssetId`, animation-set, portrait-region, and audio-bank values identify runtime resources emitted from one or more packages. The generator may derive several runtime children from one production package, but it must record that mapping and fail an undeclared collision. A `CreatureId` or `CharacterId` is never reused as an `AssetId` merely because the names describe the same subject.

| Production package ID | Source-data content symbol | Generated `CreatureId` | Generated model `AssetId` |
|---|---|---|---|
| echo.quarrune | echo_quarrune | ECHO_QUARRUNE | ASSET_MODEL_ECHO_QUARRUNE |
| echo.ayselor | echo_ayselor | ECHO_AYSELOR | ASSET_MODEL_ECHO_AYSELOR |
| echo.kilnback | echo_kilnback | ECHO_KILNBACK | ASSET_MODEL_ECHO_KILNBACK |
| echo.nacreel | echo_nacreel | ECHO_NACREEL | ASSET_MODEL_ECHO_NACREEL |
| echo.gyreclast | echo_gyreclast | ECHO_GYRECLAST | ASSET_MODEL_ECHO_GYRECLAST |
| echo.kivarrax | echo_kivarrax | ECHO_KIVARRAX | ASSET_MODEL_ECHO_KIVARRAX |
| echo.kovrass | echo_kovrass | ECHO_KOVRASS | ASSET_MODEL_ECHO_KOVRASS |
| echo.ulvorel | echo_ulvorel | ECHO_ULVOREL | ASSET_MODEL_ECHO_ULVOREL |

All eight portrait regions share `ASSET_UI_PORTRAITS_ECHOFORMS` from `ui.portraits.echoforms`; the `CreatureDef` table fixes region order, animation-set ID, and `vox.*` bank. The matching human `CharacterDef` table fixes distinct model `AssetId` values, regions of `ui.portraits.humans`, and `anm.*` sets for the nine packages below.

| Character production package | Story/source symbol | Generated `CharacterId` |
|---|---|---|
| chr.player.ari | player | CHAR_PLAYER |
| chr.tavi | npc_tavi | CHAR_TAVI |
| chr.sera_venn | npc_sera_venn | CHAR_DR_SERA_VENN |
| chr.oren_saye | npc_oren_saye | CHAR_OREN_SAYE |
| chr.ivo_veyra | npc_ivo_veyra | CHAR_IVO_VEYRA |
| chr.rusk | npc_rusk | CHAR_RUSK |
| chr.mara_ovelle | npc_mara_ovelle | CHAR_MARA_OVELLE |
| chr.jo_renn | npc_jo_renn | CHAR_JO_RENN |
| chr.pell_anwar | npc_pell_anwar | CHAR_PELL_ANWAR |

Presentation rows are delivery/assembly aliases, not duplicate runtime assets. The left column is always `alias_of` the canonical source(s) in the right column. This namespace is closed at the exact eight rows below for the opening slice. An alias has tier `A0`: it owns no creator, prompt, editable source, transformation history, license, runtime payload, status, gate decision, evidence, inventory count, or ledger row. The canonical source owns all of those records; manifests/BOMs may emit the alias only as lookup metadata and must carry the exact ordered canonical-owner list. A validator rejects an alias with independent bytes or provenance.

| Non-owning delivery alias | `alias_of` canonical runtime inventory source(s) |
|---|---|
| present.studio_mark | `ui.screen.studio_mark` |
| present.game_mark | `ui.screen.title_mark` |
| present.loading_backdrop | `ui.screen.loading` |
| present.loading_indicator | `vfx.transition.loading_relay`, `anm.ui.loading_relay` |
| present.cutscene_slate | `ui.screen.cutscene_slate` |
| present.world_route | `env.world_map.desert_relief`, `vfx.transition.world_route` |
| present.sim_dissolve | `vfx.transition.sim_dissolve` |
| present.chapter_end | `ui.screen.chapter_end` |

Any future BOM alias record has exactly `alias_id`, `alias_of` ordered canonical owner IDs, and `payload_bytes=0`; its offset, packed path, payload hash, compression, source, creator, rights/license, provenance, status, gates, and evidence fields are literal `NONE`. It cannot appear in packed-file totals, bundle payload membership, generated-asset counts, or deduplication inputs, and resolving it returns the already-owned canonical payload(s) without copying bytes. A ninth `present.*` label or a changed owner list is a contract/count change requiring an explicit inventory revision; tooling may not synthesize one from filenames.

The 15 `ASSET_CAMERA_SHOT_*` values `0x7801..0x780F` are 36-byte generated data children, not additional art packages. `DATA_SCHEMAS.md` is the canonical child-to-parent/payload table; every parent is one existing `ui.*`, `env.*`, `lmk.*`, or `col.*` inventory ID. `ASSET_LEDGER.md` records explicit provenance for every generated child, and the BOM must carry both child and parent IDs. This mapping adds neither hidden production work nor a count exemption: the parent still owns its editable marker/volume data, camera review evidence, and all applicable seven-gate obligations. The ordered source tuples are sealed at SHA-256 `7d176cacd076ffbf8dfb092103b6f82d4e4f5a5b658a822b8072c350410c3100`; their exact concatenated `15 * 36 = 540` packed bytes are sealed at `b26a6697e47daf2787ab513b13dc36ac6bd79b43d895b0b21773228d39d28cde`.

Bundle IDs repeated in the Zone map, BOM, and residency table are cross-references to one generated bundle definition, not duplicate definitions or duplicated ROM payload. The manifest/BOM generator rejects a second definition, conflicting alias, or repeated payload count.

## 9. UI, fonts, icons, portraits, and presentation

All UI is reviewed at 320×240 with 5% overscan. Process/UI-shell font and media remain within 48 KiB; screen-specific atlases replace one another and are charged to the active scene’s 300 KiB exploration or 336 KiB battle texture cap.

| Asset ID | Deliverable | Format / budget | Dependencies | Stage / priority |
|---|---|---|---|---|
| `font.meridian_raster.body` | Original sentence-case dialogue/UI bitmap font: `A–Z`, `a–z`, `0–9`, and every punctuation mark used by locked copy | 128×128 IA4; ≤8 KiB; 8 px caps, 10 px line | `UI DLG` | `S1 P0` |
| `font.meridian_raster.title` | Original 12/16 px heading glyphs | 128×64 IA4 | `UI` | `S4 P1` |
| `ui.atlas.relay_core` | Panel corners, traces, tabs, cursor, focus states | 128×64 CI4/IA8 split; ≤12 KiB | `UI` | `S1 P0` |
| `ui.icons.controller` | Stick, D-pad, A, B, L, R, Z, C-Up, C-Down, C-Left, C-Right, and Start; vertical camera is displayed as `L + C-Up/C-Down`, while bare C-Down remains Relay | exactly 12 icons, 12×12 IA4 packed in 64×64 IA4; ≤2 KiB | `UI` | `S1 P0` |
| `ui.icons.affinity` | Current, Ember, Gale, Strata icons | 4 icons, 16×16 CI4 | `BTL UI` | `S1 P0` |
| `ui.icons.battle_state` | STAGGERED; Power, Guard, Speed, and one-use EMPOWERED modifier icons; visible priority arrow/order-bar glyph | 6 icons, 12×12 CI4 | `BTL UI` | `S4 P1` |
| `ui.icons.relay` | Party, messages, Resonance, map, save/settings | 5 icons, 16×16 CI4 | `UI` | `S4 P1` |
| `ui.portraits.humans` | All 9 humanoid dialogue portraits with approved expression states | 9 base + 12 expressions; 32×32 CI4 | `DLG` | `S4 P1` |
| `ui.portraits.echoforms` | All 8 Echoform battle/party portraits | 8; 32×32 CI4 | `BTL UI` | `S4 P1` |
| `ui.screen.studio_mark` | Original boot studio mark | 128×64 CI4; ≤6 KiB | `UI` | `S4 P1` |
| `ui.screen.title_mark` | `N64GAME` title treatment, no copied logo grammar | 128×64 CI4; ≤6 KiB | `UI` | `S4 P1` |
| `ui.screen.title_menu` | New Game/Continue/settings-safe title state | components + 1 background | `SAV UI` | `S4 P1` |
| `ui.screen.loading` | Honest branded loading frame, relay indicator, location card; Annex benchmark variant is `S1`, remaining location variants are `S4` | 160×120 CI4 tiled; ≤12 KiB | `UI VFX` | `S1/S4 P0` |
| `ui.screen.cutscene_slate` | Final-styled `INSERT CUTSCENE HERE` slate; 8-frame fade-in, 90-frame fully visible hold, 8-frame fade-out, immediate safe skip | 160×120 CI4 tiled; ≤12 KiB | `UI SAV` | `S3 interface / S4 final P0` |
| `ui.screen.name_entry` | 1–8 uppercase grid, backspace, default ARI, confirm/cancel protection | component set; ≤8 KiB | `UI SAV` | `S3 interface / S4 final P0` |
| `ui.panel.dialogue` | Three-line text panel, speaker tab, portrait/no-portrait variants | shared atlas | `DLG UI` | `S1 P0` |
| `ui.prompt.interact` | Context action and controller reconnect-safe prompt | shared atlas | `EXP UI` | `S3 interface / S4 final P0` |
| `ui.screen.pause` | Resume, Field Relay, settings, save/quit-safe state | shared atlas | `UI SAV` | `S3 interface / S4 final P0` |
| `ui.screen.settings` | Reusable title/pause options panel: text speed, invert X/Y, music/SFX volume, rumble, X/Y overscan, UI contrast, live preview, defaults, apply, and cancel; Title Apply always updates only the process profile with no SaveRequest or persistence claim, New Game copies it into the first page, Continue overlays it dirty-on-difference, and only stable initialized Pause Apply performs an atomic settings-only journal update | shared atlas + ≤4 KiB preview media | `UI SAV AUD` | `S3 interface / S4 final P0` |
| `ui.screen.process_safe_recovery` | Process-resident rollback-fatal screen with explicit Retry Recovery and Return to Title choices; it cannot depend on either source- or destination-scene assets | component set; ≤6 KiB in shared UI bundle | `UI EXP SAV` | `S3 interface / S4 final P0` |
| `ui.screen.relay_shell` | Common Field Relay frame and tab motion | shared atlas | `UI` | `S1 P0` |
| `ui.screen.relay_party` | Real party composition, HP/progression, move access | ≤8 KiB screen-specific | `BTL UI` | `S3 interface / S4 final P0` |
| `ui.screen.relay_messages` | Information-only message list/detail with derived `READ`, `PENDING`, or `RESOLVED` story state; opening never mutates a read/story bit | ≤8 KiB | `DLG SAV UI` | `S3 interface / S4 final P0` |
| `ui.panel.relay_trace` | Pell side-reader header scan, two-node route projection, signal-break state, and incoming Sera portrait handoff | shared Relay shell + ≤4 KiB trace/map media | `DLG SAV UI AUD` | `S4 P1` |
| `ui.screen.relay_resonance` | Records, shared meter explanation, unlocked state | ≤8 KiB | `BTL SAV UI` | `S3 interface / S4 final P1` |
| `ui.screen.relay_map` | Information-only destination nodes, lock/unlock, focus/detail, and cancel/back; it cannot initiate travel | ≤10 KiB | `MAP SAV UI` | `S3 interface / S4 final P0` |
| `ui.screen.relay_save` | Manual record surface with current stable location/checkpoint, save confirm, transition-blocked state, writing, success, write failure, retry, and safe cancel without false success | shared Relay shell + ≤6 KiB screen-specific | `SAV UI` | `S3 interface / S4 final P0` |
| `ui.battle.hud` | Four HP blocks, STAGGERED/volatile modifiers, turn focus, actor identity | ≤14 KiB | `BTL UI` | `S1 P0` |
| `ui.battle.command` | Command categories and legal availability | shared atlas | `BTL UI` | `S1 P0` |
| `ui.battle.move_info` | Four moves, affinity, target rule, power/effect, and visible nonzero priority label/order glyph | shared atlas | `BTL UI` | `S1 P0` |
| `ui.battle.target` | Legal target cursors for ally/enemy/self/all | shared atlas | `BTL UI` | `S1 P0` |
| `ui.battle.resonance` | Shared meter, gain pulse, full/invalid finisher states | shared atlas | `BTL VFX UI` | `S1 P0` |
| `ui.battle.result` | Victory/defeat, progression, reward, continue | ≤6 KiB | `BTL SAV UI` | `S3 interface / S4 final P0` |
| `ui.screen.retry` | Retry or Return to Annex with snapshot explanation | shared atlas | `BTL SAV UI` | `S3 interface / S4 final P0` |
| `ui.indicator.save` | Saving/saved/failure feedback | shared atlas | `SAV UI` | `S3 interface / S4 final P0` |
| `ui.modal.controller` | Disconnect/reconnect and safe resume | shared atlas | `UI` | `S3 interface / S4 final P0` |
| `ui.screen.chapter_end` | Final authored title/hook and stable return prompt | 160×120 CI4 tiled; ≤12 KiB | `DLG SAV UI` | `S4 P1` |

## 10. Battle move VFX and paired audio events

Each table row is one canonical **paired parent record**, keyed by the suffix shared after `vfx.move.` and `sfx.move.` (for example, pair key `quarrune.ridge_ram`). The row registers two separate production IDs: the first-column VFX ID and second-column audio ID. Neither child is an alias and neither may inherit the other's creator, source, transformations, rights, output hash, seven-decision vector, or evidence. Before production, both receive explicit ledger rows carrying the same pair key. The asset validator requires the exact 32 pair keys, a one-to-one suffix match, 32 VFX ledger/evidence records, 32 audio ledger/evidence records, and no orphan or duplicate child.

Shared sprite/strip kernels and common impact layers reduce memory, but timing, direction, color, and result feedback remain authored per move. Shared layers cite their own ledger IDs; sharing does not erase a child record. `P` is maximum particles alive for the event; ordinary events must also fit the 24-particle guidance unless justified. Pair approval requires both child Gate 7 decisions plus one synchronized in-engine pair capture; a green VFX review cannot hide stock, missing, unlicensed, or poorly synchronized audio.

| VFX ID | Paired audio ID | Move / visual action | P | Stage / priority |
|---|---|---|---:|---|
| `vfx.move.quarrune.ridge_ram` | `sfx.move.quarrune.ridge_ram` | Cobalt horn lattice compresses into a low ochre ridge impact | 18 | `S1 P0` |
| `vfx.move.quarrune.brace_relay` | `sfx.move.quarrune.brace_relay` | Three Strata plates relay outward to an ally guard | 14 | `S1 P0` |
| `vfx.move.quarrune.grounding_ring` | `sfx.move.quarrune.grounding_ring` | Ground ring crosses both opponents, checks Power-up chevrons, and absorbs Current sparks into six footpads | 16 | `S4 P1` |
| `vfx.move.quarrune.steady_pulse` | `sfx.move.quarrune.steady_pulse` | Slow cobalt-to-mint heal pulse and explicit STAGGERED clear handoff | 12 | `S4 P1` |
| `vfx.move.ayselor.sirocco_slice` | `sfx.move.ayselor.sirocco_slice` | Two pale wind cuts cross from the leading wing | 14 | `S4 P1` |
| `vfx.move.ayselor.lift_current` | `sfx.move.ayselor.lift_current` | Amber lift helix raises ally posture and speed cue | 16 | `S4 P1` |
| `vfx.move.ayselor.dazzle_wake` | `sfx.move.ayselor.dazzle_wake` | Keel lamp fans across both foes; successful proc ends in the STAGGERED timing break | 18 | `S4 P1` |
| `vfx.move.ayselor.guiding_draft` | `sfx.move.ayselor.guiding_draft` | Narrow route stream connects Ayselor to selected ally | 12 | `S4 P1` |
| `vfx.move.kilnback.cinder_charge` | `sfx.move.kilnback.cinder_charge` | Furnace-rib glow drives a low cinder wedge impact | 20 | `S4 P1` |
| `vfx.move.kilnback.bellows_guard` | `sfx.move.kilnback.bellows_guard` | Expanding heat shield follows visible bellows compression | 16 | `S4 P1` |
| `vfx.move.kilnback.scorch_mark` | `sfx.move.kilnback.scorch_mark` | Controlled three-prong ember mark lands under target and lowers its Power stage | 12 | `S4 P1` |
| `vfx.move.kilnback.banked_flame` | `sfx.move.kilnback.banked_flame` | Flame retracts into ribs, then leaves a stored amber core | 14 | `S4 P1` |
| `vfx.move.nacreel.arc_jet` | `sfx.move.nacreel.arc_jet` | Droplet halo aligns into a cyan electrical jet | 20 | `S4 P1` |
| `vfx.move.nacreel.conductive_veil` | `sfx.move.nacreel.conductive_veil` | Broken droplet curtain wraps ally without obscuring body | 18 | `S4 P1` |
| `vfx.move.nacreel.flow_switch` | `sfx.move.nacreel.flow_switch` | Two droplet streams link both allies and resolve into Speed-up chevrons | 16 | `S4 P1` |
| `vfx.move.nacreel.static_ripple` | `sfx.move.nacreel.static_ripple` | Flat cyan rings cross both foes; successful proc resolves to STAGGERED break | 18 | `S4 P1` |
| `vfx.move.gyreclast.auger_knuckle` | `sfx.move.gyreclast.auger_knuckle` | Drill spiral sheds three mineral chips at contact | 16 | `S4 P1` |
| `vfx.move.gyreclast.dust_screen` | `sfx.move.gyreclast.dust_screen` | Low directional dust sheet crosses both foes and lowers Power; silhouettes remain visible | 20 | `S4 P1` |
| `vfx.move.gyreclast.fault_pin` | `sfx.move.gyreclast.fault_pin` | Narrow blue fault line pins one target and hands off guaranteed STAGGERED | 12 | `S4 P1` |
| `vfx.move.gyreclast.carapace_brace` | `sfx.move.gyreclast.carapace_brace` | Three plate wedges close around core then settle | 10 | `S4 P1` |
| `vfx.move.kivarrax.crosswind_cut` | `sfx.move.kivarrax.crosswind_cut` | Perpendicular fan-tail gusts cross at target | 16 | `S4 P1` |
| `vfx.move.kivarrax.slipstream` | `sfx.move.kivarrax.slipstream` | Thin wake hugs Kivarrax locomotion and speed icon | 12 | `S4 P1` |
| `vfx.move.kivarrax.pressure_drop` | `sfx.move.kivarrax.pressure_drop` | Air ring contracts around one foe, pops outward, and lowers Guard | 18 | `S4 P1` |
| `vfx.move.kivarrax.talon_sweep` | `sfx.move.kivarrax.talon_sweep` | Ground-hugging three-stroke sweep with dust response | 14 | `S4 P1` |
| `vfx.move.kovrass.clinker_bite` | `sfx.move.kovrass.clinker_bite` | Two furnace-clinker arcs close at bite contact | 14 | `S4 P1` |
| `vfx.move.kovrass.boiler_chorus` | `sfx.move.kovrass.boiler_chorus` | Bellows pulses travel visibly to Ulvorel and raise Power | 18 | `S4 P1` |
| `vfx.move.kovrass.ash_mantle` | `sfx.move.kovrass.ash_mantle` | Sparse ash plates orbit low, preserving target silhouette | 18 | `S4 P1` |
| `vfx.move.kovrass.furnace_feint` | `sfx.move.kovrass.furnace_feint` | False bright vent precedes a lateral ember jab and guaranteed STAGGERED handoff | 16 | `S4 P1` |
| `vfx.move.ulvorel.rill_lash` | `sfx.move.ulvorel.rill_lash` | One translucent water ribbon follows the throat pendulum | 16 | `S4 P1` |
| `vfx.move.ulvorel.pressure_leap` | `sfx.move.ulvorel.pressure_leap` | Hood compresses, launches, and releases boosted impact ring | 22 | `S4 P1` |
| `vfx.move.ulvorel.cooling_shroud` | `sfx.move.ulvorel.cooling_shroud` | Hood-wide blue veil raises Guard and visibly clears STAGGERED from one ally | 18 | `S4 P1` |
| `vfx.move.ulvorel.undertow` | `sfx.move.ulvorel.undertow` | Low spiral pulls dust/water strokes toward Ulvorel | 20 | `S4 P1` |

## 11. Common, environment, transition, and story VFX

| Asset ID | Event | Maximum live elements | Dependencies | Stage / priority |
|---|---|---:|---|---|
| `vfx.battle.hit_physical` | Common affinity-neutral contact punctuation | 10 | `BTL` | `S1 P0` |
| `vfx.battle.effectiveness` | Strong/resisted directional accent, also conveyed by UI/audio | 8 | `BTL UI` | `S1 P0` |
| `vfx.battle.state_feedback` | Exact STAGGERED ailment or Power/Guard/Speed/EMPOWERED modifier handoff to UI | 10 | `BTL UI` | `S1 P0` |
| `vfx.battle.knockout` | Actor-specific energy settle, not disappearance smoke | 20 | `BTL` | `S4 P1` |
| `vfx.resonance.gain` | Partner-to-shared-meter mint pulses | 12 | `BTL UI` | `S1 P0` |
| `vfx.resonance.full` | Three-node gold completion and held ready state | 16 | `BTL UI` | `S1 P0` |
| `vfx.finisher.horizon_break` | Quarrune/Ayselor Strata-Gale braid and bespoke impact; Quarrune contribution plus non-character-specific braid core is `S1`, Ayselor contribution/full impact is `S4` | 64 | `BTL DLG UI` | `S1/S4 P0` |
| `vfx.finisher.sunline_cascade` | Kilnback/Nacreel Ember-Current tutorial braid | 64 | `BTL DLG UI` | `S4 P1` |
| `vfx.environment.dust_footstep` | Surface-aware player/NPC/Echoform dust | 8 per actor | `EXP BTL` | `S1 P0` |
| `vfx.environment.dust_gust` | Exterior depth-layered gust event | 32 | `EXP` | `S4 P2` |
| `vfx.environment.fountain_energy` | Estate orbital fountain streams | 24 | `EXP` | `S4 P1` |
| `vfx.environment.machine_steam` | Short authored vent event | 12 | `EXP` | `S4 P2` |
| `vfx.environment.monitor_trace` | Annex Resonance-monitor normal waveform | 16 | `DLG` | `S4 P1` |
| `vfx.story.rusk_team_restore` | Rusk’s explicit two-starter full-HP restoration: one grounded instrument ring, two separate ally pulses, then HP confirmation | 18 | `DLG UI SAV` | `S4 P1` |
| `vfx.story.follower_recovery_relay_shimmer` | Violet-free Relay-cyan contour places Tavi at the previous safe portal without implying Fracture teleportation | 12 | `EXP FOL` | `S3 interface / S4 final P0` |
| `vfx.story.fracture_monitor` | Closing violet offset, core pulse, delayed edge | 48 | `DLG SAV` | `S4 P1` |
| `vfx.transition.sim_dissolve` | Arena grid dissolves into chamber geometry | 64 pooled | `BTL DLG` | `S3 interface / S4 final P0` |
| `vfx.transition.world_route` | Relay pulse travels Annex↔Estate after physical skimmer boarding owns the transition request | 18 | `MAP UI` | `S3 interface / S4 final P0` |
| `vfx.transition.loading_relay` | Three-lobe indicator tied to real loading; benchmark load/finish path is final `S1` source | 6 | `UI` | `S1 benchmark final / S3 interface / S4 remaining final P0` |
| `vfx.transition.fade_dither` | Dithered color fade with no raw-frame exposure; benchmark fade path is final `S1` source | screen primitive | `UI` | `S1 benchmark final / S3 interface / S4 remaining final P0` |

## 12. Animation banks

### 12.1 Humanoids

| Bank ID | Clip count and explicit coverage | Stage / priority |
|---|---|---|
| `anm.humanoid.base` | 12: idle_a, idle_b, walk, run, start, stop, turn_l, turn_r, interact, talk_neutral, listen, reaction | `S1 P0` |
| `anm.player.ari` | 10 beyond the shared base: relay_use, relay_side_reader, door_elevator, battle_command, victory_relief, tavi_acknowledge, starter_hand_to_chest, dialogue_nod, field_hand_signal, hook_resolve | `S1/S4 P0` |
| `anm.tavi` | 9: follow_walk, follow_run, door_wait, separation_recover, hide_reveal, tag_place_reveal, greet_player, listen_ivo, reunion_exit | `S4 P1` |
| `anm.sera_venn` | 4: diagnostic_scan, explain_starter, receive_tavi, react_fracture | `S4 P1` |
| `anm.oren_saye` | 4: director_brief, unlock_map, welcome_return, read_beacon | `S4 P1` |
| `anm.ivo_veyra` | 6: tune_device, compare_track_roll, explain_invention, notice_player, reunion_present, farewell | `S4 P1` |
| `anm.rusk` | 11: wrench_work, wrench_drop, gate_work, challenge, battle_command, battle_reaction, defeat, apology, team_restore, unlock_gate, invite_inside | `S4 P1` |
| `anm.mara_ovelle` | 3: scan_cradle, tend_echoform, optional_talk | `S4 P2` |
| `anm.jo_renn` | 5: solder_relay, inspect_relay, relay_dock_release, relay_handoff, optional_talk | `S4 P1` |
| `anm.pell_anwar` | 4: side_reader_trace, map_trace, comms_listen, optional_talk | `S4 P2` |

Shared clips are retargeted only among compatible human rigs, then reviewed per character. Timing offsets and posture changes prevent synchronized clone motion.

### 12.2 Echoforms

Each bank includes `idle_a`, `idle_b`, `entrance`, `reposition`, one clip named for each of its four canonical moves, `hit`, `knockout`, and `victory`. Starter/tutorial-player banks add their named duo-finisher participation clip. Real starters also own the exact story-performance clips listed below rather than hiding hook/reunion acting inside generic battle idles.

| Bank ID | Count | Move-performance clips | Finisher clip | Stage / priority |
|---|---:|---|---|---|
| `anm.echo.quarrune` | 14 | `S1`: idle_a/b, entrance, reposition, ridge_ram, brace_relay, hit, knockout; `S4`: grounding_ring, steady_pulse, victory, story_brace_alert, story_resolve | `S1` participation preview; final integrated horizon_break remains `S4` | `S1/S4 P0` |
| `anm.echo.ayselor` | 15 | sirocco_slice, lift_current, dazzle_wake, guiding_draft; story_packet_ping, story_lamp_dim_alert, story_resolve | horizon_break | `S4 P1` |
| `anm.echo.kilnback` | 12 | cinder_charge, bellows_guard, scorch_mark, banked_flame | sunline_cascade | `S4 P1` |
| `anm.echo.nacreel` | 12 | arc_jet, conductive_veil, flow_switch, static_ripple | sunline_cascade | `S4 P1` |
| `anm.echo.gyreclast` | 11 | auger_knuckle, dust_screen, fault_pin, carapace_brace | — | `S4 P1` |
| `anm.echo.kivarrax` | 11 | crosswind_cut, slipstream, pressure_drop, talon_sweep | — | `S4 P1` |
| `anm.echo.kovrass` | 11 | clinker_bite, boiler_chorus, ash_mantle, furnace_feint | — | `S4 P1` |
| `anm.echo.ulvorel` | 11 | rill_lash, pressure_leap, cooling_shroud, undertow | — | `S4 P1` |

### 12.3 Mechanisms and presentation

| Bank ID | Clips / states | Stage / priority |
|---|---|---|
| `anm.mech.annex_door` | sealed, opening, open, closing | `S3 interface / S4 final P0` |
| `anm.mech.annex_elevator` | gate, depart, arrive, floor indicator | `S3 interface / S4 final P0` |
| `anm.mech.simulation_ring` | boot, idle, battle pulse, dissolve, shutdown | `S1 P0` |
| `anm.mech.field_relay_integration` | relay_docked, dock_release, handheld_latch, side_reader_insert, trace_scan, side_reader_release, estate_cut_wave_chirp, interrupt_safe | `S4 P1` |
| `anm.prop.calibration_locator_tag` | dormant, calibration_ping, located, interrupt_safe | `S4 P1` |
| `anm.mech.beacon_decoder` | idle, packet_resolved, moving_trace, trace_shift, fracture_bend, stop_safe | `S4 P1` |
| `anm.prop.solace_model` | dark, practical_light_on, beacon_answer, fracture_flicker, settle_safe | `S4 P1` |
| `anm.mech.resonance_monitor` | idle trace, message trace, Fracture reaction | `S4 P1` |
| `anm.mech.antenna_array` | idle aim, beacon acquire | `S4 P2` |
| `anm.mech.clinic_cradle` | idle, scan, present_starter | `S4 P1` |
| `anm.mech.diagnostic_arm` | idle, scan, retract | `S4 P2` |
| `anm.mech.wall_fan` | slow, normal, stop | `S4 P2` |
| `anm.mech.estate_gate` | locked, challenge, unlock, open | `S3 interface / S4 final P0` |
| `anm.mech.observatory_dome` | idle, slit_open, align | `S4 P1` |
| `anm.mech.orbital_fountain` | start, idle, story_accent | `S4 P1` |
| `anm.mech.kinetic_tower` | continuous safe loop | `S4 P2` |
| `anm.mech.grand_orrery` | idle, examine, sky_rotate_hold, arm_clear_stair, study_stair_open, interrupted_reset, stop_safe | `S4 P1` |
| `anm.mech.counterweight_walker` | idle, walk_cycle, safety_stop | `S4 P1` |
| `anm.prop.impossible_compass` | idle_disagreement, examine_flurry, settle_safe | `S4 P1` |
| `anm.prop.orrery_switch` | released, press, held, release, interrupted_reset | `S3 interface / S4 final P0` |
| `anm.prop.packet_recorder` | idle, keel_lamp_answer, recording, close_safe, interrupt_safe | `S4 P1` |
| `anm.mech.world_map` | information focus plus skimmer-owned route_out/route_return presentation | `S3 interface / S4 final P0` |
| `anm.ui.loading_relay` | load_progress and finish are final `S1`; skip-safe exit interface lands at `S3` and its final animation lands at `S4` | `S1 benchmark final / S3 interface / S4 remaining final P0` |
| `anm.veh.sand_skimmer` | idle_suspension, board_depart, travel_loop, arrive_settle | `S4 P1` |

## 13. Music, ambience, vocals, and SFX

Runtime audio target: all music no more than 1.8 MiB, all SFX/vocals/ambience no more than 750 KiB, and active resident bank/stream buffers no more than 256 KiB. Prefer sequenced/XM64 or validated compressed mono treatment; editable masters remain lossless. Every cue records sample rate, loop points, loudness review, runtime size, and license in the ledger.

Peak audio residency is deduplicated: one ≤144 KiB music stream/buffer state plus one ≤112 KiB current SFX/ambience/vocal cache. Transitions fade the outgoing music to zero, release its stream/cache ownership, and only then open the destination stream; two full music buffers never overlap. Common UI layers are one shared cache entry referenced by events, not copied into every zone bank.

### 13.1 Music

| Asset ID | Purpose / target loop | Runtime cap | Stage / priority |
|---|---|---:|---|
| `mus.title_loading` | 35–50 s relay motif; supports marks, slate, loading | 180 KiB | `S4 P1` |
| `mus.simulation_battle` | 75–105 s interactive tutorial battle loop | 260 KiB | `S4 P1` |
| `mus.annex_exploration` | 100–140 s dry percussion/analog outpost loop | 300 KiB | `S4 P1` |
| `mus.world_travel` | 20–35 s motif transition, clean loop/exit | 100 KiB | `S4 P1` |
| `mus.estate_exploration` | 100–140 s clockwork/glass Estate loop | 300 KiB | `S4 P1` |
| `mus.estate_battle` | 75–105 s higher-stakes real-battle loop | 280 KiB | `S4 P1` |
| `mus.victory_return` | 15–25 s victory sting with return variation | 100 KiB | `S4 P1` |
| `mus.closing_fracture` | 35–55 s warm resolution interrupted by Fracture | 180 KiB | `S4 P1` |

### 13.2 Ambience and SFX banks

Child identifiers are mandatory event IDs, not examples.

| Bank ID | Count | Child event IDs / coverage | Runtime cap | Stage / priority |
|---|---:|---|---:|---|
| `amb.annex` | 5 loops | `threshold_wind`, `atrium_hum`, `sim_room`, `clinic`, `workshop` | 64 KiB | `S4 P1` |
| `amb.estate` | 5 loops | `courtyard_wind`, `fountain`, `foyer`, `invention_hall`, `observatory` | 64 KiB | `S4 P1` |
| `sfx.ui` | 18 | `move`, `confirm`, `cancel`, `invalid`, `prompt`, `tab`, `message`, `name_add`, `name_backspace`, `target`, `move_info`, `res_gain`, `res_full`, `save_start`, `save_ok`, `save_fail`, `pause`, `reconnect` | 48 KiB | `S1/S4 P0` |
| `sfx.environment` | 33 | `door_open`, `door_close`, `elevator_gate`, `elevator_move`, `elevator_arrive`, `relay_pickup`, `relay_open`, `relay_dock_release`, `side_reader_insert`, `side_reader_trace`, `side_reader_release`, `console`, `clinic_scan`, `tool_loop`, `fan`, `water_drop`, `antenna`, `estate_gate`, `fountain`, `wind_harp`, `walker`, `gyroscope`, `compass_needles`, `paper_roll`, `orrery`, `dome`, `projector`, `beacon_ping`, `map_depart`, `map_arrive`, `skimmer_start`, `skimmer_loop`, `skimmer_stop` | 72 KiB | `S4 P1` |
| `sfx.footstep` | 10 | `human_stone_l/r`, `human_metal_l/r`, `human_dust_l/r`, `echo_heavy_l/r`, `echo_light_l/r` | 28 KiB | `S1/S4 P0` |
| `sfx.battle_common` | 14 | `transition_in`, `transition_out`, `command_lock`, `turn_queue`, `hit`, `strong`, `resisted`, `staggered`, `stage_up`, `stage_down`, `ko`, `victory`, `defeat`, `reward` | 48 KiB | `S1/S4 P0` |
| `sfx.finisher` | 8 | `horizon_quarrune` and `horizon_braid` are final `S1` review cues; `horizon_ayselor`, `horizon_impact`, and four Sunline children complete at `S4` | 36 KiB | `S1/S4 P0` |
| `sfx.story` | 14 | `slate_in`, `slate_skip`, `sim_dissolve`, `tavi_reveal`, `rusk_wrench_drop`, `locator_tag_ping`, `estate_cut_wave_chirp`, `rusk_team_restore`, `follower_recovery_relay_shimmer`, `packet_recorder_answer`, `hook_two_note_low_third`, `fracture_begin`, `fracture_core`, `chapter_end` | 30 KiB | `S3 interface / S4 final P0` |

### 13.3 Echoform vocal banks

| Bank ID | Six required cues | Runtime cap each | Stage / priority |
|---|---|---:|---|
| `vox.quarrune` | entrance, idle, attack, support, hit, knockout/victory variant | 16 KiB | `S1 P0` |
| `vox.ayselor` | entrance, idle, attack, support, hit, knockout/victory variant | 16 KiB | `S4 P1` |
| `vox.kilnback` | entrance, idle, attack, support, hit, knockout/victory variant | 16 KiB | `S4 P1` |
| `vox.nacreel` | entrance, idle, attack, support, hit, knockout/victory variant | 16 KiB | `S4 P1` |
| `vox.gyreclast` | entrance, idle, attack, support, hit, knockout/victory variant | 16 KiB | `S4 P1` |
| `vox.kivarrax` | entrance, idle, attack, support, hit, knockout/victory variant | 16 KiB | `S4 P1` |
| `vox.kovrass` | entrance, idle, attack, support, hit, knockout/victory variant | 16 KiB | `S4 P1` |
| `vox.ulvorel` | entrance, idle, attack, support, hit, knockout/victory variant | 16 KiB | `S4 P1` |

The 32 `sfx.move.*` events paired in section 10 each combine a small move-specific accent with shared physical/affinity layers. Their combined runtime accents are capped at 96 KiB. Ambience (128 KiB), six common SFX banks (262 KiB), vocal banks (128 KiB), and move accents (96 KiB) therefore plan to no more than 614 KiB in ROM, leaving 136 KiB beneath the 750 KiB group ceiling for headers/alignment and measured exceptions.

## 14. Boot, loading, slate, and transition sources

This is an assembly/delivery view over canonical packages, not eight additional assets. Each row inherits source, output, tier, stage, provenance, and gates from its `alias_of` owner(s); the stage shown is the required assembly milestone only and never authorizes source creation. At an `S3` milestone only interface lookup/ownership is proven with `tmp.*` presentation where necessary; final visual/audio bytes still arrive from the canonical owner's `S4` work unless an exact `S1` whitelist subset already passed.

| Non-owning alias | `alias_of` canonical owner(s) and owned source/output scope | Required states and proof | Assembly stage / priority |
|---|---|---|---|
| `present.studio_mark` | `ui.screen.studio_mark`; canonical layered vector/raster source → CI4 sprite | fade-in/out, native capture, original mark provenance | `S4 P1` |
| `present.game_mark` | `ui.screen.title_mark`; canonical layered vector/raster source → CI4 sprite | title/loading/chapter consistency | `S4 P1` |
| `present.loading_backdrop` | `ui.screen.loading`; canonical layered 4:3 source → tiled CI4 | Annex and Estate location-card variants; no fake wait | `S4 P1` |
| `present.loading_indicator` | `vfx.transition.loading_relay` + `anm.ui.loading_relay`; canonical sprite strip/timing sources | progress/active/finish states; releases after load | `S3 interface / owners S4 final P0` |
| `present.cutscene_slate` | `ui.screen.cutscene_slate`; canonical layered 4:3 source → tiled CI4 | exact `INSERT CUTSCENE HERE`; 3 s, A/Start skip, same flag | `S3 interface / owner S4 final P0` |
| `present.world_route` | `env.world_map.desert_relief` + `vfx.transition.world_route`; canonical relief/path/node sources | Annex→Estate and return variants after physical skimmer boarding owns travel; state preserved | `S3 interface / owners S4 final P0` |
| `present.sim_dissolve` | `vfx.transition.sim_dissolve`; canonical grid/strip/event sources | battle arena to chamber without raw frame | `S3 interface / owner S4 final P0` |
| `present.chapter_end` | `ui.screen.chapter_end`; canonical layered 4:3 source → tiled CI4 | authored closing hook, stable menu/post-slice handoff | `S4 P1` |

`present.cutscene_slate` is the only intentionally temporary accepted visual. It must itself look final and may not be accompanied by placeholder sound, debug text, or unfinished framing. Its canonical `ui.screen.cutscene_slate` row alone owns the ledger and seven decisions. All eight aliases obey the zero-byte BOM schema above; none may be promoted into a canonical asset by adding payload fields.

## 15. Opening storyboard package

Storyboard images are generated with GPT Image only after the art bible, Solace, glider, Severance, and colossal Fractured Echoform continuity designs are approved. Each panel is an individual high-resolution 4:3 image, minimum 1600×1200, with no baked panel number or fake text; numbering is applied non-destructively in the contact sheet. Final delivery includes the image files themselves, not prompts alone.

Canonical outputs are `storyboard/opening/panels/01.png` through `18.png`, `storyboard/opening/CONTACT_SHEET.png`, `storyboard/opening/SHOT_LIST.md`, `storyboard/opening/continuity/`, `storyboard/opening/COLOR_SCRIPT.png`, `storyboard/opening/PROMPT_MANIFEST.md`, and `storyboard/opening/DELIVERY_MANIFEST.md`. Editable layered corrections, if any, live under `assets-src/storyboard/opening/`.

| Asset ID | Required shot content | Dependencies | Stage / priority |
|---|---|---|---|
| `sb.opening.panel.01` | Warm desert dusk extreme wide; tiny Solace establishes scale | approved Solace/environment continuity | `S6 P3` |
| `sb.opening.panel.02` | Solace three-quarter research-carrier reveal and instrument pods | Solace sheet | `S6 P3` |
| `sb.opening.panel.03` | Ventral research deck activity and humanitarian purpose | crew/environment-and-deck sheet | `S6 P3` |
| `sb.opening.panel.04` | Beacon instrument detects impossible violet disturbance | beacon/UI motif | `S6 P3` |
| `sb.opening.panel.05` | Distant storm folds light behind carrier | environment continuity + Fracture color script | `S6 P3` |
| `sb.opening.panel.06` | First split-diamond glider crosses foreground | glider sheet | `S6 P3` |
| `sb.opening.panel.07` | Multiple gliders take restraint positions around Solace | spatial continuity map | `S6 P3` |
| `sb.opening.panel.08` | Severance restraint reels open; lines not yet attached | Severance sheet | `S6 P3` |
| `sb.opening.panel.09` | Lines strike three designed Solace hardpoints | vehicle continuity | `S6 P3` |
| `sb.opening.panel.10` | Crew danger reaction with readable blocking, no gore | crew sheet | `S6 P3` |
| `sb.opening.panel.11` | Colossal Fractured Echoform silhouette emerges behind storm | creature continuity | `S6 P3` |
| `sb.opening.panel.12` | Creature bends starlight/gravity around the carrier | Fracture rules | `S6 P3` |
| `sb.opening.panel.13` | Solace deck tilts while restraint lines pull taut | spatial continuity | `S6 P3` |
| `sb.opening.panel.14` | Emergency beacon ejects from orange tail | beacon continuity | `S6 P3` |
| `sb.opening.panel.15` | Beacon falls foreground as Solace enters violet fold | color script | `S6 P3` |
| `sb.opening.panel.16` | Solace vanishes; empty restraint arc and closing storm | continuity map | `S6 P3` |
| `sb.opening.panel.17` | Beacon descends toward cool desert night, pulse visible | beacon/UI motif + environment continuity | `S6 P3` |
| `sb.opening.panel.18` | Beacon pulse graphic-match transitions to cool simulation/name interface | final UI motif | `S6 P3` |
| `sb.opening.contact_sheet` | All 18 panels in order with readable applied numbers | all panels | `S6 P3` |
| `sb.opening.shot_list` | Exact `storyboard/opening/SHOT_LIST.md`: duration, framing, lens, height, movement, blocking, performance, light, transitions, sound, CRT notes for every shot | panels/continuity | `S6 P3` |
| `sb.opening.continuity.solace` | Orthographic/three-quarter carrier sheet, hardpoints, pods, palette | approved cinematic vehicle design | `S0/S6 P3` |
| `sb.opening.continuity.glider` | Split-diamond glider sheet, restraint reel and scale | approved Severance design | `S0/S6 P3` |
| `sb.opening.continuity.severance` | Severance figure/costume silhouettes and restraint-operator gesture language | clean-room review | `S0/S6 P3` |
| `sb.opening.continuity.crew` | Solace research-crew role silhouettes, safety gear, deck blocking, and scale | Solace/research-purpose design | `S0/S6 P3` |
| `sb.opening.continuity.protagonist_context` | Approved player silhouette, Field Relay, name-entry handoff motif, and explicit note that the player is not aboard Solace | player/UI continuity | `S0/S6 P3` |
| `sb.opening.continuity.fractured_colossus` | Stable anatomy, scale, silhouette, Fracture organ/rules | approved creature concept | `S0/S6 P3` |
| `sb.opening.continuity.beacon` | Solace beacon shape, deployment, pulse motif | UI/story contract | `S0/S6 P3` |
| `sb.opening.continuity.environment_and_deck` | Key-environment sheet: desert horizon/terrain scale, dusk-to-night sky, violet storm/fold anatomy, Solace research-deck stations, instrument pods, emergency-prop placement, and fixed spatial/color anchors | Art Bible environment/Fracture rules + Solace/crew sheets | `S0/S6 P3` |
| `sb.opening.continuity.spatial_map` | Solace/gliders/creature screen direction and line attachment map | all continuity sheets | `S6 P3` |
| `sb.opening.color_script` | 6–9 frames: warm dusk → warning → violet storm → cool simulation | art bible palette | `S6 P3` |
| `sb.opening.prompt_manifest` | Prompt, generation date/tool, edits, seed/metadata if available, rights/provenance per image | every generated image | `S6 P3` |
| `sb.opening.delivery_manifest` | File dimensions, hashes, panel order, contact sheet, user delivery links | approved package | `S6 P3` |

Future-video replacement contract is fixed in `storyboard/opening/SHOT_LIST.md`:

- format-neutral video asset: `rom:/cinematic/opening_solace.video`;
- format-neutral paired-audio asset: `rom:/audio/cinematic/opening_solace.audio`;
- timeline/metadata: `rom:/data/cutscene/opening_solace.cut`;
- the `.video` and `.audio` logical assets receive manifest-declared concrete formats only during future user-supplied video integration, preserving stable paths without preselecting a codec;
- natural end, safe `{A}`/`{START}` skip, missing media, and decode failure converge on the idempotent callback `opening_cinematic_finish`;
- the callback stops playback/audio ownership, render-fences and releases only opening-slot resources, clears input edges, sets `opening_cinematic_seen = true`, and requests `SCENE_NAME_ENTRY`;
- repeated calls are no-ops; a media failure falls back to the approved slate and records telemetry; no path leaks input into name entry or saves half-transition state;
- target video runtime is 60–90 seconds and remains outside accepted playtime until the master explicitly replaces the temporary-slate timing rule.

## 16. Evidence and review deliverables

Evidence is stored outside runtime assets and kept size-conscious. Still captures use PNG; short review clips use a documented efficient codec. Every runtime-generating source—including `.blend`, layered images used for conversion, font sources, editable VFX, and lossless/editable audio masters—must be an ordinary reviewed Git blob or canonical Git LFS object whose actual bytes materialize in a credential-free fresh public clone of the exact payload commit. A URL, release locator, deterministic later fetch, or local-only file is not a production input; a local archive may be retained only as an explicitly non-build record. All art-review evidence follows the same Git/Git-LFS rule.

Every evidence set contains `EVIDENCE_MANIFEST.sha256` using the exact six-TAB-field UTF-8/LF/path/token/sort grammar in `docs/ART_BIBLE.md` section 16.3. The set's inventory/ledger record stores the manifest path and its own SHA-256. The verifier rejects unsafe paths, symlinks, duplicate/case-colliding or direct/nested ownership, repeated materialized hashes/capture IDs, malformed fields, noncanonical LFS pointers/objects, self-membership, and cycles, then recomputes every member from the reviewed ordinary/LFS revision and fresh public clone. A changed, missing, locator-only, or unretrievable member invalidates the gate.

The benchmark aggregate is `review/benchmark/PAYLOAD_MANIFEST.sha256`, not a self-covering approval manifest. It owns exact whitelist/evidence registries, build recipe, 14 substantive evidence records/subordinate manifests, canonical gate records, and their non-cyclic ordinary/LFS members. It excludes `docs/VISUAL_BENCHMARK_APPROVAL.md`, the ignored/untracked ROM, and `ev.benchmark.approval`. The fifteenth record is the Gate-2-pinned-key SSH annotated-origin-tag attestation; local/public object identity, ancestry, fresh-clone reachability, exact message, and target/control are verified, while remote-host protection remains a recorded external check.

| Evidence ID / pattern | Count | Required contents | Stage / priority |
|---|---:|---|---|
| `ev.benchmark.native` | exactly 6 named stills | members `exploration`, `dialogue`, `target_selection`, `attack_anticipation`, `impact`, `support` at raw 320×240 | `S1 P0` |
| `ev.benchmark.enlarged` | exactly 6 same-name stills | exact six native members at 4× nearest-neighbor; no repaint/filter | `S1 P0` |
| `ev.benchmark.turntable.player` | 2 turntables + contact sheets | `chr.player.ari` neutral and benchmark lighting, all angles, native crop | `S1 P0` |
| `ev.benchmark.turntable.quarrune` | 2 turntables + contact sheets | `echo.quarrune` neutral and benchmark battle lighting, all angles, native crop | `S1 P0` |
| `ev.benchmark.animation.player` | 1 locked-camera reel + contact sheets | exact whitelisted player/base clips, contacts, deformation, interrupt/settle | `S1 P0` |
| `ev.benchmark.animation.quarrune` | 1 locked-camera reel + contact sheets | exact whitelisted Quarrune clips, Ridge Ram/Brace Relay events, Horizon contribution preview | `S1 P0` |
| `ev.benchmark.environment.corner` | 1 complete set | exact `sector.atrium_lower.sim_threshold_corner`: route/reverse/ceiling, five purposeful prop instances, collision/camera/grade overlays | `S1 P0` |
| `ev.benchmark.ui` | 1 state matrix + native gallery | exact whitelist UI/font/icons, longest strings, all command/target/Resonance/dialogue/loading states, overscan/contrast | `S1 P0` |
| `ev.benchmark.vfx_audio` | 3 synchronized event records | Ridge Ram ordinary hit, Brace Relay support, Horizon braid core; source/result/cleanup and original/licensed audio | `S1 P0` |
| `ev.benchmark.capture_60s` | 1 continuous capture | at least 60 seconds representative traversal/dialogue/command/attack/support; raw audio and no hidden cuts around defects | `S1 P0` |
| `ev.benchmark.performance` | 1 report + trace | frame time, heap, batches, particles, texture/geometry/animation/audio working sets | `S1 P0` |
| `ev.benchmark.unload_reload` | 1 repeated trace | synchronized unload/reload returns resources and heap to exact measured baseline | `S1 P0` |
| `ev.benchmark.gates` | exactly 46 benchmark-scope production-ID seven-decision vectors + 4 integrated rollups | every whitelist ID/subset individually; rollups for player, Quarrune, exact environment sector, and integrated UI/VFX/audio presentation; partial-package passes do not claim final full-package approval | `S1 P0` |
| `ev.benchmark.authorship` | 1 rubric + reference-calibration record | nine visual-authorship categories, three independent reviewers, no protected reference frame committed | `S1 P0` |
| `ev.benchmark.approval` | 1 non-self-referential attestation record | signed annotated origin tag points to the commit containing populated `docs/VISUAL_BENCHMARK_APPROVAL.md` and attests the separate 40-hex payload commit plus payload-manifest digest; local checks plus separate release-operator confirmation of remote protection; control/tag excluded from payload manifest | `S1 P0` |
| `ev.turntable.chr.<id>.neutral` | 9 sets | 8-angle still/contact sheet and full rotation | `S4 P1` |
| `ev.turntable.chr.<id>.representative` | 9 sets | gameplay-light rotation and native crop | `S4 P1` |
| `ev.turntable.echo.<id>.neutral` | 8 sets | 8-angle still/contact sheet and full rotation | `S4 P1` |
| `ev.turntable.echo.<id>.representative` | 8 sets | battle-light rotation and native crop | `S4 P1` |
| `ev.turntable.veh.sand_skimmer` | 2 sets | neutral/game-light hero turntable plus simplified-map comparison | `S4 P1` |
| `ev.turntable.lmk.<id>` | 8 sets | neutral construction views plus representative location/camera capture | `S4 P1` |
| `ev.review.prop.<id>` | 63 sets | 8-angle hero-prop review or size-appropriate contact sheet, UV/material stats, native integration crop | `S4 P1/P2` |
| `ev.environment.<source>.native` | 16 sets | entrance/route or world-map view, landmark, reverse/ceiling completeness where applicable, interaction view | `S4 P1` |
| `ev.animation.humanoid.<bank>` | 10 reels | locked camera, contact markers, deformation stress frames | `S4 P1` |
| `ev.animation.echo.<bank>` | 8 reels | all required clips and event frames | `S4 P1` |
| `ev.animation.mechanism.<bank>` | 24 reels | vehicle/mechanism/story-prop full range, safety stop, looping seam where applicable | `S4 P1` |
| `ev.ui.<production-id>.native` | exactly 37 evidence sets | one set for every ID in section 16.1 mapping; longest text/name, all states, overscan/contrast, and no orphan package | `S1/S4 P0` |
| `ev.vfx.move.<id>` | exactly 32 clips/sheets | one for every first-column `vfx.move.*` child: source, travel/build, impact/result, cleanup frame | `S1/S4 P0` |
| `ev.audio.move.<id>` | exactly 32 reports/clips | one for every paired `sfx.move.*` child: source/rights/transform, waveform, rate/size, event sync, representative mix | `S1/S4 P0` |
| `ev.vfx.common.<id>` | 20 clips/sheets | representative camera and max-load cleanup, including Rusk restoration and follower-recovery Relay shimmer | `S4 P1` |
| `ev.audio.<bank>` | exactly 24 bank reports (`8 + 2 + 6 + 8`) | music, ambience, common SFX, and vocal banks: waveform, loop, event sync, sample rate, size, provenance, mix note | `S1/S4 P0` |
| `ev.collision.<room>` | 18 overlays + tests | collision render, route trace, camera/follower/battle tests as relevant | `S3 P0` |
| `ev.zone_data.<zone>` | 13 reports | nav graph, every spawn/safe anchor, interaction index, ZoneId/bundle resolution, orphan/reachability validation | `S3 P0` |
| `ev.zone_data.end_card_ui` | 1 report | UI-only ZoneId resolves no environment/collision/nav/spawn/interaction and owns only `bnd.ui.chapter_end` | `S3 P0` |
| `ev.integration.scene_matrix` | 1 matrix | every room, cast, UI, VFX, audio, placeholder search result | `S5 P0` |
| `ev.storyboard.panel.<01-18>` | 18 reviews | aspect, identity, anatomy, staging, palette, clean text, continuity | `S6 P3` |
| `ev.storyboard.contact_sheet` | 1 high-res image | numbered sequence readable and animatable | `S6 P3` |
| `ev.cert.native_gallery` | complete gallery | every environment, both battles, major UI, loading, closing hook | `S7 P0` |

### 16.1 Exact 37-package UI evidence map

The production-ID column must equal the exact 35 `ui.*` plus two `font.*` inventory IDs—no wildcard substitution, orphan, or alias. One capture may appear in several sets only when each set's manifest names the exact region/state it proves. Every set includes raw 320×240, 4× nearest-neighbor, 5% overscan/blur, reduced-saturation/contrast, source/output hashes, and all applicable interactive states.

| Production ID | Canonical evidence ID | Mandatory focus beyond common captures |
|---|---|---|
| `font.meridian_raster.body` | `ev.ui.font.meridian_raster.body.native` | full authored-glyph audit, longest dialogue, eight-character name substitution, no fallback/replacement |
| `font.meridian_raster.title` | `ev.ui.font.meridian_raster.title.native` | every heading size, title/loading/chapter contexts, quantized edge quality |
| `ui.atlas.relay_core` | `ev.ui.atlas.relay_core.native` | panels, tabs, cursor/focus/disabled states, seam/palette inspection |
| `ui.icons.controller` | `ev.ui.icons.controller.native` | all exact 12 prompt icons individually; native proof of `L + C-Up/C-Down` vertical-camera chords and bare C-Down Relay without ambiguity |
| `ui.icons.affinity` | `ev.ui.icons.affinity.native` | four silhouettes in color, grayscale, and move/target contexts |
| `ui.icons.battle_state` | `ev.ui.icons.battle_state.native` | STAGGERED, Power/Guard/Speed, EMPOWERED, and priority/order glyph |
| `ui.icons.relay` | `ev.ui.icons.relay.native` | all five tab icons, focused/unfocused/locked states and the derived `PENDING` message-attention cue; no mutable `UNREAD` state or read bit |
| `ui.portraits.humans` | `ev.ui.portraits.humans.native` | nine identities plus all 12 expressions against dialogue framing |
| `ui.portraits.echoforms` | `ev.ui.portraits.echoforms.native` | eight distinct portraits against battle/party values |
| `ui.screen.studio_mark` | `ev.ui.screen.studio_mark.native` | original mark, fade sequence, no raw frame |
| `ui.screen.title_mark` | `ev.ui.screen.title_mark.native` | title/loading/end-card consistency and protected-logo similarity check |
| `ui.screen.title_menu` | `ev.ui.screen.title_menu.native` | New Game, verified Continue, disabled/invalid recovery, Options, rapid input |
| `ui.screen.loading` | `ev.ui.screen.loading.native` | Annex/Estate variants, honest progress, finish/release, no stale frame |
| `ui.screen.cutscene_slate` | `ev.ui.screen.cutscene_slate.native` | exact text, 106-tick natural path, immediate A/Start path, identical finalizer |
| `ui.screen.name_entry` | `ev.ui.screen.name_entry.native` | ARI, 1/8 chars, grid, backspace, confirm, protected cancel, rapid input |
| `ui.panel.dialogue` | `ev.ui.panel.dialogue.native` | longest copy/name, portrait/no-portrait, three-line wrap, skip/rapid confirm |
| `ui.prompt.interact` | `ev.ui.prompt.interact.native` | all contextual prompt placements, reconnect, background extremes |
| `ui.screen.pause` | `ev.ui.screen.pause.native` | Resume/Relay/Settings/Save ownership, blocked/rapid resume states |
| `ui.screen.settings` | `ev.ui.screen.settings.native` | Title profile-only and Pause persistence, dirty overlay, defaults/apply/cancel/write fail/retry |
| `ui.screen.process_safe_recovery` | `ev.ui.screen.process_safe_recovery.native` | process-only assets, Retry Recovery/Return Title, source/destination absence |
| `ui.screen.relay_shell` | `ev.ui.screen.relay_shell.native` | every tab, open/close, focus motion, ownership/release |
| `ui.screen.relay_party` | `ev.ui.screen.relay_party.native` | two starters, low/full HP, progression, four moves, eight-character name |
| `ui.screen.relay_messages` | `ev.ui.screen.relay_messages.native` | state-gated list/detail, exact derived `READ`/`PENDING`/`RESOLVED` labels and copy swap, longest message, stable re-entry, and proof that opening/closing changes no story/read bit |
| `ui.panel.relay_trace` | `ev.ui.panel.relay_trace.native` | scan, two nodes, signal break, incoming portrait, interruption/recovery |
| `ui.screen.relay_resonance` | `ev.ui.screen.relay_resonance.native` | locked/unlocked records, empty/full meter explanation |
| `ui.screen.relay_map` | `ev.ui.screen.relay_map.native` | information-only locked/unlocked nodes, focus/detail in both directions, cancel/back, and proof that confirm cannot request travel; physical `veh.meridian.sand_skimmer` boarding owns travel |
| `ui.screen.relay_save` | `ev.ui.screen.relay_save.native` | checkpoint/location, confirm/blocked/writing/success/failure/retry/safe cancel |
| `ui.battle.hud` | `ev.ui.battle.hud.native` | four actors, low/zero HP, status/modifier stack, identity/turn focus |
| `ui.battle.command` | `ev.ui.battle.command.native` | legal/disabled categories, alternate inputs, rapid confirm/cancel |
| `ui.battle.move_info` | `ev.ui.battle.move_info.native` | longest moves, affinity/target/power/effect, exact priority label |
| `ui.battle.target` | `ev.ui.battle.target.native` | ally/enemy/self/all legal layouts and invalid-target recovery |
| `ui.battle.resonance` | `ev.ui.battle.resonance.native` | empty/gain/full/invalid/consume states and three-node braid |
| `ui.battle.result` | `ev.ui.battle.result.native` | tutorial/real victory, defeat, progression/reward, continue, idempotency |
| `ui.screen.retry` | `ev.ui.screen.retry.native` | Retry/Return Annex, snapshot explanation, disconnect/rapid input |
| `ui.indicator.save` | `ev.ui.indicator.save.native` | saving/saved/failure, no false success, scene transition coexistence |
| `ui.modal.controller` | `ev.ui.modal.controller.native` | exploration/menu/dialogue/battle disconnect/reconnect and safe resume |
| `ui.screen.chapter_end` | `ev.ui.screen.chapter_end.native` | final hook/title, stable prompt/return, UI-only zone and prior-scope absence |

Each evidence set uses the templates in `docs/ASSET_REVIEW_TEMPLATES.md` and links back to exact source/output hashes. Missing evidence is a failed gate, not an administrative omission.

## 17. Converted ROM BOM and bundle rollup

The build reports three different sizes and must never substitute one for another:

- **Editable source bytes** are `.blend`, layered image, lossless audio, and data-authoring files under `assets-src/`; they affect repository/storage policy, not N64 residency.
- **Packed ROM bytes** are converted/compressed payload plus alignment in the DFS image; these determine ROM size.
- **Unpacked bytes** are the manifest-declared decoded payload for one bundle; the loader rejects a bundle whose declared bytes exceed its arena cap.
- **Peak resident bytes** are all concurrently live scene/action dependencies, allocator alignment, and registered external resources. This is the number compared with the 1,100 KiB scene cap and global 512 KiB free-heap floor.

Planning rollup below is an upper-bound contract for converted output. A `.*` row is the CI rollup of the required/optional/action subbundles named in section 8.2; the generated report also lists each subbundle individually. Shared catalog packed bytes are counted once even when several zone manifests reference them. Zone peak resident values already include the selectively loaded catalog dependencies and are not added again.

| Bundle or generated catalog | Packed ROM cap | Unpacked payload cap | Peak resident contribution / concurrency rule |
|---|---:|---:|---|
| Process/UI shell catalog | 48 KiB | 48 KiB | 48 KiB process/UI media; inside architecture persistent allocation |
| `bnd.boot_title_opening_name.*` | 280 KiB | 340 KiB | ≤340 KiB; never concurrent with a heavy game zone |
| `bnd.annex.sim_room.base` | 360 KiB | 520 KiB | ≤520 KiB retained physical base |
| `bnd.sim.tutorial_overlay` | 500 KiB | 520 KiB | ≤520 KiB; with base exactly ≤1,040 KiB |
| `bnd.annex.sim_room.optional/onboarding` | 120 KiB | 380 KiB | Base + current onboarding/optional set ≤900 KiB after tutorial overlay unload |
| `bnd.annex.atrium.required/optional` | 500 KiB | 700 KiB | ≤700 KiB base/optional residency |
| `bnd.annex.atrium.story` | 90 KiB | 160 KiB | Base + normal story overlay ≤860 KiB |
| `bnd.annex.atrium.hook` | 220 KiB | 300 KiB | Base + hook overlay ≤1,000 KiB; never with normal story overlay |
| `bnd.annex.director.*` | 260 KiB | 800 KiB | ≤800 KiB current zone |
| `bnd.annex.player_room.*` | 190 KiB | 700 KiB | ≤700 KiB current zone |
| `bnd.annex.clinic.*` | 310 KiB | 900 KiB | ≤900 KiB current zone/onboarding action |
| `bnd.annex.workshop.*` | 330 KiB | 900 KiB | ≤900 KiB current zone/Relay action |
| `bnd.annex.threshold.*` | 270 KiB | 850 KiB | ≤850 KiB current zone/map-exit action |
| `bnd.map.required/travel` | 180 KiB | 600 KiB | ≤600 KiB; destination heavy bundle absent |
| `bnd.estate.courtyard.required/optional` | 470 KiB | 520 KiB | ≤520 KiB base/optional residency |
| `bnd.estate.courtyard.battle` | 480 KiB | 520 KiB | Base + battle overlay ≤1,040 KiB |
| `bnd.estate.courtyard.story` | 150 KiB | 300 KiB | Base + confrontation/postbattle story ≤820 KiB; never with battle overlay |
| `bnd.estate.foyer.*` | 230 KiB | 750 KiB | ≤750 KiB current zone |
| `bnd.estate.hall.*` | 390 KiB | 950 KiB | ≤950 KiB current zone/examine action |
| `bnd.estate.study.*` | 340 KiB | 900 KiB | ≤900 KiB current zone/reunion action |
| `bnd.ui.chapter_end` | 12 KiB | 12 KiB | Included in the ≤48 KiB UI shell after atrium unload |
| Shared humanoid/Echoform/vehicle model, texture, portrait catalog | 1,450 KiB | 3,200 KiB catalog total | Selective actors only; ≤420 KiB inside current scene row |
| Shared animation catalog | 1,350 KiB | 3,000 KiB catalog total | Current clips only; ≤208 KiB inside current scene row |
| Shared UI/VFX converted catalog | 550 KiB | 1,100 KiB catalog total | Current atlases/pools only; already charged to scene texture/action rows |
| Music catalog | 1,800 KiB | 1,800 KiB | One active stream ≤144 KiB inside separate 300 KiB audio allocation |
| Ambience/SFX/vocal/move catalog | 614 KiB | 614 KiB | Deduplicated active bank/cache ≤112 KiB; old scene bank released before new bank commit |
| Dialogue/data/collision/nav/spawn/interaction catalog | 450 KiB | 720 KiB catalog total | Current zone subset ≤128 KiB inside scene row |
| Manifest tables, CRCs, and alignment reserve | 300 KiB | 300 KiB | Process manifest/index target ≤48 KiB; remainder read on demand |

The zone-owned converted rows plan to approximately 5.5 MiB packed and the shared catalogs to approximately 6.4 MiB packed. With an initial 1.3 MiB allowance for executable, DFS/header, and non-art runtime content, the working ROM plan is approximately 13.2 MiB, leaving about 2.8 MiB beneath the 16 MiB target for measured alignment and corrections. The temporary-slate build does not include future cinematic media; future user-supplied video integration must choose and profile the manifest-declared video/audio formats at the exact three logical paths before adding them. Source `.blend`, lossless masters, storyboard PNGs, review clips, and generated ROM binaries are not silently counted as runtime DFS payload.

CI must emit `build/reports/asset_bom.csv` and `build/reports/bundle_sizes.md` with every manifest entry’s asset ID, bundle, packed bytes, unpacked bytes, declared arena cap, measured peak resident bytes, and budget result. It also emits one deduplicated ROM total and fails on double-counted aliases, out-of-cap bundles, ROM ≥16 MiB without approved exception evidence, or absent provenance.

## 18. Memory residency and loading groups

Assets are packaged into the zone bundles in section 8.2; the scene controller owns and releases each scene/action scope. A ROM asset may be shared without remaining resident in RAM.

| Scope / bundle family | Contents | Runtime cap | Unload boundary |
|---|---|---:|---|
| Process/UI shell | Body font subset, branded transition shell, save indicator, reconnect modal, fixed VFX kernels only | ≤48 KiB media inside the architecture’s 160 KiB persistent-state cap | Process shutdown; exact ownership measured |
| `bnd.annex.sim_room.base` | One physical chamber sector, collision, zone data, simulation ring base, mandatory fixed presentation data | ≤520 KiB scene base; its textures are part of the 336 KiB combined cap | Loaded before tutorial overlay; retained across tutorial completion and owner-token transfer into Annex interior |
| `bnd.sim.tutorial_overlay` | Four tutorial actors, virtual shell, current clips, tutorial battle UI/VFX/SFX | ≤520 KiB action overlay; combined base + overlay ≤1,040 KiB and ≤336 KiB textures | Destroy after tutorial result/dissolve render fence; never reload or overlap a second chamber base |
| `bnd.annex.<zone>.*` | Current zone, player model, only required NPCs/props/ambience, screen-specific UI; follower-recovery shimmer/audio only while Tavi is the derived follower | 700–1,000 KiB by section 8.2; ≤300 KiB textures | Zone/scene exit after render/audio fence |
| `bnd.map.*` | Relief map, two nodes, travel VFX/audio; no player model required | ≤600 KiB scene arena; ≤96 KiB textures | Destination load commit |
| `bnd.estate.courtyard.required/optional` | Courtyard exploration shell, current exploration cast/dressing | Shares ≤1,040 KiB cap with one current action bundle | Courtyard/interior or map transition |
| `bnd.estate.courtyard.battle` | Four battle Echoforms, battle clips/UI/VFX/SFX; Rusk/player story bodies retained only if measured and required for current shot | Action portion within the same 1,040 KiB cap; ≤336 KiB total textures | Destroy after `RESULT_PRESENT` completion fence, before post-victory exploration and before interior load |
| `bnd.estate.courtyard.story` | Field Relay cut-wave clip/cue, Rusk wrench performance, confrontation cast, and post-result `team_restore` animation/VFX/SFX; never battle actors | Base + story overlay ≤820 KiB and ≤300 KiB textures | Destroy before Estate interior load and never coexist with `bnd.estate.courtyard.battle` |
| `bnd.estate.interior.<zone>.*` | Current room, player, Tavi/Ivo/Rusk only when required, local props/ambience, and follower-recovery shimmer/audio only while Tavi is the derived follower | 750–950 KiB by zone; ≤300 KiB textures | Zone/map exit |
| `bnd.annex.atrium.hook` | Closing cast/animations, beacon/Fracture monitor events, hook UI, and exact `hook_two_note_low_third` cue over the already-loaded atrium | Action overlay inside the atrium’s ≤1,000 KiB arena and ≤300 KiB texture cap | Destroy with atrium scene after closing fade/render fence |
| `bnd.ui.chapter_end` | UI-only final chapter card and stable menu choice under `ZONE_END_CARD_UI` | Included in ≤48 KiB process/UI-shell media cap | Stable post-slice state or title return; no prior world/environment `ZoneId` or its environment scope remains resident |

The player, Echoforms, scene-specific UI, animation banks, and active VFX are scene-owned, not process-owned. Battle actors and presentation resources use action scope and are torn down as soon as the battle result handoff is complete. No scope may retain source images, debug overlays, unused animation banks, off-location music, or storyboard media in runtime memory. Twenty transition loops must return to the same measured heap and resource-count baseline.

## 19. Production completion rule

The inventory is complete only when every canonical production ID has exactly one matching explicit ledger row that resolves back to its inventory row and deterministic profile/tier, contains complete creator/rights/input/provenance/transform/source/output fields, carries seven same-revision gate decisions, and links recomputable evidence manifests. At Gate 7 this includes exactly 32 explicit `vfx.move.*` rows plus 32 explicit suffix-matched `sfx.move.*` rows: both children of every pair are `approved`, have separate provenance/gates/evidence, and share one synchronized pair proof before either child can complete Gate 7. `A0 present.*` aliases inherit and cannot duplicate those records; their future BOM metadata is zero-byte/`NONE` only. `E0 ev.*` records prove work but are not production assets. Final acceptance requires an automated and visual placeholder sweep. Everything marked temporary must be removed except canonical `ui.screen.cutscene_slate`, exposed through non-owning alias `present.cutscene_slate`, the single approved authored slate.
