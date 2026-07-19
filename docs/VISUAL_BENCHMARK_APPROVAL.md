# N64GAME Visual Benchmark Approval

Status: Gate 4 control record

Schema-Version: 4

Production-Lock: LOCKED

Decision: PENDING

This is the sole machine-verifiable unlock for mass final visual/audio-asset production. It does not claim that a benchmark exists today. The exact 15 camera-shot `C7` rows in `docs/ASSET_LEDGER.md` have a narrow Markdown-authoring exception at `concept`; this is not a Gate 1 pass or `source` status, and generated output plus Gates 5–7 remain locked. The master specification and `docs/ART_BIBLE.md` remain authoritative.

State machine:

| Decision | Required `Production-Lock` | Permitted work |
|---|---|---|
| `PENDING` | `LOCKED` | Gate 1 concept generally; only exact whitelist subsets with populated `WB-###` authorization may create benchmark final source/output |
| `REVIEW_REQUIRED` | `LOCKED` | unaffected valid `AUTHORIZED` rows retain immutable history; only exact returned rows may become `REPAIR_ONLY`, and no new subset may activate |
| `BLOCKED` | `LOCKED` | unaffected history remains; only exact defect-linked returned rows may be `REPAIR_ONLY`, with no newly accepted converted/review output |
| `APPROVED` | `UNLOCKED` | full production may proceed, subject to every asset's own gates |

Any other state/lock pairing fails. Whitelist presence alone never authorizes work.

The global lock does not prohibit manifest-bound Gate-1 exploration. A general media asset at ledger status `concept` may own only its canonical hashed `g1/PROVENANCE.md`, `SOURCE_MANIFEST.sha256`, `g1/EVIDENCE_MANIFEST.sha256`, `g1/REVIEW.md`, and their manifest members, with `output:NONE` and seven literal pending gates. It has no `AUTHORIZATION.md`, Gate 2+ bytes, generated output, or final-source authority. `planned` owns no files; the exact 15 Markdown-only C7 tuples retain their narrow exception.

For any non-`APPROVED` current record, approval-only ROM/run/release/tag/signer/protection/time fields and every final approval tuple are literal `PENDING`; the final production-decision field equals the current state and the return field follows the exact `NONE`/return-token rules below. The exact eight aggregate pairs—payload manifest, whitelist registry, evidence registry, ROM recipe, and four rollup gate records—are each jointly `PENDING` or jointly populated. Any populated pair activates the payload pair, exact 40-hex public payload commit, clean-build ID, credential-free fresh public clone, Git LFS retrieval, and one shared commit-bound manifest context; no aggregate/member is trusted from mutable worktree bytes. The public workflow, when populated, is ordinary-Git, payload-owned `.github/workflows/*.yml`. Every populated aggregate is owned by the payload graph, and no unowned regular file may hide under `review/benchmark/`. With all eight pairs `PENDING`, reviewed payload commit/build/workflow are also `PENDING` and the allowed regular-file scaffold set under that directory is empty. Recipe size/header/output metadata is structurally checked before approval; equality to local/fresh/public ROM bytes is approval-only because those current ROM identity fields remain `PENDING`. Prior approved controls, evidence, and decisions remain immutable under their signed historical tags rather than being copied as stale current authority.

A populated rollup requires the whitelist/gate registry. Every rollup gate row binds source/output SHA fields to that exact registry digest, not to the parent payload-manifest digest; this keeps the payload graph acyclic.

## 1. Approval identity

| Field | Required value | Current value |
|---|---|---|
| Reviewed payload Git commit | exactly 40 lowercase hex; contains reviewed source/output/evidence payload, not the later approval attestation | `PENDING` |
| Clean-build ID | 1–96 chars matching `[A-Za-z0-9][A-Za-z0-9._-]*` | `PENDING` |
| Local ROM path | repository-relative portable ignored/untracked path to one regular non-symlink `.z64`; never a Git/LFS payload member | `PENDING` |
| ROM byte count | canonical positive decimal, recomputed from local, fresh-build, and public-release bytes | `PENDING` |
| ROM SHA-256 | exactly 64 lowercase hex, recomputed from local, fresh-build, and public-release bytes | `PENDING` |
| ROM header SHA-256 | exactly 64 lowercase hex over the first 64 ROM bytes, recomputed locally and after fresh build/download | `PENDING` |
| Ares target | exact version and mode | `Ares 148 / Homebrew Mode` |
| Prior approved attestation ref | `NONE` for `PENDING`/`APPROVED`; under `REVIEW_REQUIRED`/`BLOCKED`, exact pinned-key public origin ref `refs/tags/n64game-visual-benchmark/<first-12-prior-payload-hex>` | `NONE` |
| Prior approved attestation tag object ID | `NONE` for `PENDING`/`APPROVED`; otherwise exact 40-hex public/local annotated-tag object ID | `NONE` |
| Prior approved control Git commit | `NONE` for `PENDING`/`APPROVED`; otherwise exact 40-hex peeled tag target containing the prior approved control | `NONE` |
| Prior approved payload Git commit | `NONE` for `PENDING`/`APPROVED`; otherwise exact 40-hex payload commit attested by the prior signed tag | `NONE` |
| Prior approved payload-manifest SHA-256 | `NONE` for `PENDING`/`APPROVED`; otherwise exact 64-hex digest attested by the prior signed tag | `NONE` |
| Prior approved whitelist/gate-registry SHA-256 | `NONE` for `PENDING`/`APPROVED`; otherwise exact 64-hex prior payload registry digest | `NONE` |
| ROM build recipe path | exact `review/benchmark/ROM_BUILD_RECIPE.tsv`, ordinary Git text in payload manifest | `PENDING` |
| ROM build recipe SHA-256 | exactly 64 lowercase hex and recomputed from reviewed payload commit | `PENDING` |
| Public build workflow file | safe `.github/workflows/<name>.yml` path present in payload commit | `PENDING` |
| Public build workflow run ID | canonical positive decimal; public same-repo Actions API reports success with `head_sha` equal payload commit | `PENDING` |
| Public ROM release tag | exact `n64game-benchmark-<40hex-payload-commit>` | `PENDING` |
| Public ROM release asset URL | exact unauthenticated same-repo GitHub URL ending `/releases/download/<release-tag>/n64game-<40hex-payload-commit>.z64` | `PENDING` |
| Payload manifest path | exact `review/benchmark/PAYLOAD_MANIFEST.sha256`; canonical grammar; excludes this control and approval attestation | `PENDING` |
| Payload manifest SHA-256 | exactly 64 lowercase hex, recomputed from payload-manifest bytes | `PENDING` |
| Whitelist/gate registry path | exact `review/benchmark/WHITELIST_GATE_REGISTRY.tsv`; 52 exact rows/subsets/current bindings/seven decisions | `PENDING` |
| Whitelist/gate registry SHA-256 | exactly 64 lowercase hex, recomputed and present in payload manifest | `PENDING` |
| Benchmark evidence registry path | exact `review/benchmark/BENCHMARK_EVIDENCE_REGISTRY.tsv`; first 14 evidence IDs, manifests, records, roles/counts/build/captures | `PENDING` |
| Benchmark evidence registry SHA-256 | exactly 64 lowercase hex, recomputed and present in payload manifest | `PENDING` |
| Player Gate 1–7 record path | exact `review/benchmark/rollups/player/GATE_RECORD.tsv` | `PENDING` |
| Player gate-record SHA-256 | exactly 64 lowercase hex and parsed/recomputed | `PENDING` |
| Quarrune Gate 1–7 record path | exact `review/benchmark/rollups/quarrune/GATE_RECORD.tsv` | `PENDING` |
| Quarrune gate-record SHA-256 | exactly 64 lowercase hex and parsed/recomputed | `PENDING` |
| Benchmark-sector Gate 1–7 record path | exact `review/benchmark/rollups/sector/GATE_RECORD.tsv` | `PENDING` |
| Benchmark-sector gate-record SHA-256 | exactly 64 lowercase hex and parsed/recomputed | `PENDING` |
| Integrated-presentation Gate 1–7 record path | exact `review/benchmark/rollups/presentation/GATE_RECORD.tsv` | `PENDING` |
| Integrated-presentation gate-record SHA-256 | exactly 64 lowercase hex and parsed/recomputed | `PENDING` |
| Approval attestation ref | signed annotated origin tag `refs/tags/n64game-visual-benchmark/<first-12-payload-hex>` pointing to commit containing this populated control | `PENDING` |
| Attestation signer fingerprint | exact Gate-2-pinned ED25519 `SHA256:8KL8xLkUqqsniUjeU4OaIHXhZYkXOyEOWs/INvJhlB0`; private key remains external | `PENDING` |
| Remote tag-protection release check | exact `CONFIRMED:<operator-id>@<RFC3339>@<https-evidence-url>` external host-side check | `PENDING` |
| Open critical/high/medium defects | `APPROVED` is exactly `0 / 0 / 0`; `BLOCKED` is a canonical nonnegative triple with critical or high greater than zero; `PENDING`/`REVIEW_REQUIRED` follow their state rules | `PENDING` |
| Decision timestamp/timezone | RFC 3339 timestamp with numeric offset or `Z` | `PENDING` |

`Decision: APPROVED` is invalid unless every current field above is populated and shape-valid; every record/manifest and ordinary/LFS member recomputes from the reviewed payload; the reviewed payload's own `docs/ASSET_LEDGER.md` and production-root tree—not a later worktree—prove ownership; all registry, gate, evidence, source/output, objective/rubric/reviewer, local/fresh/public ROM, public workflow/release, tag-object/ancestry/reachability, isolated pinned-key signer, and final-decision checks pass; defects are exactly `0 / 0 / 0`; and the external protection check is recorded. Later Gate-5+ ledger/assets do not erase the historical approval, but an orphan in the reviewed payload does. A source/output hash change to the benchmark sets `Decision: REVIEW_REQUIRED`; a critical/high regression sets `Decision: BLOCKED`. Every `.z64`, `.n64`, or `.v64` entry is forbidden in the payload Git tree. The ignored/untracked local, fresh-build, and public `.z64` bytes must all begin with `80 37 12 40` and match the recorded identities. Public `refs/tags/n64game-benchmark-<40hex>` must peel exactly to the payload commit.

The annotated tag is the non-self-referential `ev.benchmark.approval` record. Its target commit contains this populated control. The control row's evidence field is precomputable exact text `tag:<ref>; payload:<payload-commit>@<payload-manifest-sha256>; signer:<fingerprint>; protection:<external-record>`; it deliberately does not embed the future annotated-tag object ID or peeled target OID. Its signed message is exactly these five LF-delimited lines followed by one final LF and no extra signed text or keys: `schema=n64game-benchmark-attestation-v1`, `payload_commit=<40hex>`, `payload_manifest_sha256=<64hex>`, `control_path=docs/VISUAL_BENCHMARK_APPROVAL.md`, and `decision=APPROVED`. Its 12-hex ref suffix equals the payload prefix. The payload commit must be an ancestor of the tag target. The validator resolves the local annotated-tag object ID and peeled target externally, then requires them to equal the public origin values and be reachable with the payload from a credential-free fresh public clone. It verifies the SSH signature against its pinned ED25519 public key/principal in a temporary isolated allowed-signers file; the external private key is never committed and no control-supplied replacement key is accepted. The local validator cannot infer remote-host protection; the separately recorded release check owns that claim. The tag and control are excluded from `PAYLOAD_MANIFEST.sha256`; no direct or transitive self-hash is permitted.

`REVIEW_REQUIRED` and `BLOCKED` require all six prior-approved baseline fields populated together. The validator resolves that exact local/public annotated tag, verifies its object ID/peeled control target, pinned SSH signature, exact five-line message, payload ancestry/fresh-public-clone reachability, Schema-4 `APPROVED/UNLOCKED` historical control, payload-manifest graph, and exact 52-row whitelist registry from the historical payload commit. It enumerates all public `n64game-visual-benchmark/*` tags whose pinned-key-valid approved targets are ancestors of current public HEAD; the selected baseline must be the unique ancestry-maximal target, so an older signed approval cannot be chosen when a newer reachable approval exists and incomparable maxima fail as ambiguous. Every unaffected `AUTHORIZED` control row and external TSV row remains byte-identical to that signed baseline. Exact returned bases alone become `REPAIR_ONLY`; their stable basis/production/subset/authorization path and canonical owner-path projection cannot move, while the authorization record bytes/SHA must change with state/repair IDs, and every changed gate needs its own `WB-###:G#:DEFECT-ID` token. No new activation, inactive erasure, rollback, or stale prose-only history is accepted. Initial `PENDING` and a newly signed `APPROVED` record use literal `NONE` in all six fields.

Once approval is signed, current production is a separate public-head authority, not a rewrite of this control. Art Bible section 16.7 requires a clean local tree/index equal to isolated credential-free public default `HEAD`, ancestry from this signed control target, and no tracked/staged ROM. Exact full-15-cell historical rows may retain byte-identical current asset bytes; changed/new active rows require `review/production/PAYLOAD_MANIFEST.sha256`, direct committed ledger/inventory, `SHA256("FULL_PRODUCTION")`, `subset_allowlist: NONE`, zero workflow members, and exact validated pair/generated controls before current-root scans. Historical benchmark controls/evidence remain at this signed tag and need not be copied into current `HEAD`.

Every subordinate gate still owns its canonical `EVIDENCE_MANIFEST.sha256`; the payload manifest may hash those subordinate manifests only as an acyclic parent. Both filenames use the exact section-16.3 grammar, and every populated member/file/hash is conditionally recomputed.

## 2. Exact pre-approval production whitelist

The table contains exactly 52 canonical production IDs. The `Allowed final source subset` column is exhaustive. A whole row is eligible only when it says `complete package`; otherwise unlisted states, clips, sectors, variants, cues, and outputs remain locked. Eligibility becomes authorization only through the exact one-to-one `WB-001..WB-052` binding registry below. Evidence-only `ev.benchmark.*` records are permitted but own no production source. Temporary harness/greybox data uses `tmp.*`, is visually marked, and cannot be renamed into a production ID.

| Canonical production ID | Allowed final source subset before approval | Anything explicitly still locked |
|---|---|---|
| `chr.player.ari` | final hero and distance model, body/face texture, rig, blob-shadow/focus sockets | eight nonbenchmark player-specific clips |
| `echo.quarrune` | final hero/distance model, texture, rig, blob shadow; benchmark clip subset below | Grounding Ring, Steady Pulse, victory, story-brace/story-resolve final clips |
| `env.annex.atrium_lower` | non-ID `sector.atrium_lower.sim_threshold_corner` only, 1,600–2,200 tris and ≤72 KiB working textures | remaining three sectors and their final dressing |
| `col.annex.atrium_lower` | collision/camera support bounded to the exact benchmark sector only | remaining atrium collision and route data |
| `col.common.camera_volumes` | benchmark exploration/battle clamp volumes only | all other room camera volumes |
| `lmk.annex.simulation_ring` | complete package | — |
| `lmk.annex.skylight_spine` | complete package | — |
| `prop.annex.field_relay` | complete package | — |
| `prop.annex.monitor_console` | complete package | — |
| `prop.annex.sim_dais` | complete package | — |
| `prop.annex.sim_emitter` | complete package | — |
| `font.meridian_raster.body` | complete package and glyph audit | — |
| `ui.atlas.relay_core` | complete package | — |
| `ui.icons.controller` | complete 12-icon package; native `L + C-Up/C-Down` camera chords and bare C-Down Relay proof | — |
| `ui.icons.affinity` | complete four-icon package | — |
| `ui.panel.dialogue` | complete package | — |
| `ui.screen.relay_shell` | complete package | — |
| `ui.screen.loading` | Annex benchmark/loading variant only | Estate/other location variants |
| `ui.battle.hud` | complete package | — |
| `ui.battle.command` | complete package | — |
| `ui.battle.move_info` | complete package | — |
| `ui.battle.target` | complete package | — |
| `ui.battle.resonance` | complete package | — |
| `vfx.move.quarrune.ridge_ram` | complete VFX child | — |
| `sfx.move.quarrune.ridge_ram` | complete paired audio child | — |
| `vfx.move.quarrune.brace_relay` | complete VFX child | — |
| `sfx.move.quarrune.brace_relay` | complete paired audio child | — |
| `vfx.battle.hit_physical` | complete package | — |
| `vfx.battle.effectiveness` | complete package | — |
| `vfx.battle.state_feedback` | complete package | — |
| `vfx.resonance.gain` | complete package | — |
| `vfx.resonance.full` | complete package | — |
| `vfx.environment.dust_footstep` | complete package | — |
| `vfx.finisher.horizon_break` | Quarrune contribution and non-character-specific braid core | Ayselor contribution and final full-impact presentation |
| `vfx.transition.loading_relay` | final benchmark load/finish behavior | other location variants if source-distinct |
| `vfx.transition.fade_dither` | complete shared package | — |
| `anm.humanoid.base` | all 12 final shared clips | — |
| `anm.player.ari` | `battle_command`, `dialogue_nod` | remaining eight player-specific clips |
| `anm.echo.quarrune` | `idle_a`, `idle_b`, `entrance`, `reposition`, `ridge_ram`, `brace_relay`, `hit`, `knockout`, `horizon_break` participation preview | `grounding_ring`, `steady_pulse`, `victory`, `story_brace_alert`, `story_resolve`, final integrated finisher revision |
| `anm.mech.simulation_ring` | complete package | — |
| `anm.ui.loading_relay` | `load_progress`, `finish` | `skip_safe_exit` final source until S4; S3 permits interface timing only |
| `sfx.ui` | `move`, `confirm`, `cancel`, `invalid`, `target`, `move_info`, `res_gain`, `res_full` | remaining 10 events |
| `sfx.footstep` | `human_stone_l/r`, `human_dust_l/r`, `echo_heavy_l/r` | remaining four events |
| `sfx.battle_common` | `command_lock`, `turn_queue`, `hit`, `strong`, `resisted`, `staggered`, `stage_up`, `stage_down`, `ko` | remaining five events |
| `sfx.finisher` | `horizon_quarrune`, `horizon_braid` | remaining six events |
| `vox.quarrune` | complete six-cue package | — |
| `echo.ayselor` | final distance model, texture, rig, and blob shadow only | hero model and every other model/package variant |
| `anm.echo.ayselor` | `idle_a`, `reposition`, `hit` | `idle_b`, `entrance`, `sirocco_slice`, `lift_current`, `dazzle_wake`, `guiding_draft`, `knockout`, `victory`, `horizon_break`, `story_packet_ping`, `story_lamp_dim_alert`, `story_resolve` |
| `echo.gyreclast` | final distance model, texture, rig, and blob shadow only | hero model and every other model/package variant |
| `anm.echo.gyreclast` | `idle_a`, `reposition`, `hit` | `idle_b`, `entrance`, `auger_knuckle`, `dust_screen`, `fault_pin`, `carapace_brace`, `knockout`, `victory` |
| `echo.kivarrax` | final distance model, texture, rig, and blob shadow only | hero model and every other model/package variant |
| `anm.echo.kivarrax` | `idle_a`, `reposition`, `hit` | `idle_b`, `entrance`, `crosswind_cut`, `slipstream`, `pressure_drop`, `talon_sweep`, `knockout`, `victory` |

Whitelist integrity rules:

- The exact set above is the only final-source eligibility set. The closed eight-row `present.*` namespace never appears because it owns nothing; any future BOM alias metadata has only exact ordered owners and `payload_bytes=0`, with offset/path/hash/compression/source/creator/rights/license/provenance/status/gates/evidence literal `NONE` and no payload/count/deduplication effect.
- A row with a subset binds the exact subset-cell digest in the parsed authorization and provenance records plus the 52-row registry; source/output/evidence manifests prove only their six-field member closures and do not pretend to contain a subset field. Any member outside the authorized subset's machine allowlist is a critical lock violation.
- A subset row receives a benchmark-scope seven-decision vector for only that exported subset. It does not mark the full production package `approved`; completing or changing locked members later reopens every affected full-package gate.
- Quarrune remains the benchmark's only hero Echoform: it alone may create a hero model and owns the hero turntable/animation rollup. Ayselor, Gyreclast, and Kivarrax are three fully finished supporting battle-distance silhouettes needed to make the representative 2v2 scene truthful. Each supporting `echo.*` subset retains its canonical `RIGGED_MODEL / H2` seven-gate and two-polish-pass obligations, but authorizes only its exact distance-model/texture/rig/blob-shadow selectors; its paired `anm.echo.*` row authorizes only `idle_a`, `reposition`, and `hit`. Hero meshes, all other clips, move VFX/audio, portraits, vocals, and every other full-package member remain locked.
- Shared source files are permitted only when deterministic export collections/targets prove that locked payload cannot enter an output or be presented as reviewed.
- The validator fails on a ledger `source`, `converted`, `review`, or `approved` status outside this table while `Decision` is not `APPROVED`, or on an in-table status without an active exact binding below.

### 2.1 Exact authorization and current-hash bindings

The 52 rows below are one-to-one with the whitelist in the same order and are the exact control projection of `review/benchmark/WHITELIST_GATE_REGISTRY.tsv`. Its header/23-field grammar, subset-cell digest rule, build/state/repair rules, and seven explicit gate decisions are defined in `docs/ART_BIBLE.md` section 16.4. The projection must equal basis, production ID, three record path@digest pairs, source/output manifest path@digest, and state. For active production ID `<id>` with first-dot prefix `<prefix>`, paths are exact: `review/<id>/g1/AUTHORIZATION.md`, `review/<id>/g1/GATE_RECORD.tsv`, `review/<id>/g1/PROVENANCE.md`, `assets-src/<prefix>/<id>/SOURCE_MANIFEST.sha256`, and `review/<id>/g5/OUTPUT_MANIFEST.sha256` after conversion. Gate `G<n>` uses exact `review/<id>/g<n>/EVIDENCE_MANIFEST.sha256` and `review/<id>/g<n>/REVIEW.md`; an arbitrary safe path does not satisfy ownership. `INACTIVE` uses `PENDING` bindings and authorizes nothing. Before a row reaches `source`, its external registry row, authorization/provenance records, parsed seven-row gate record, source manifest, explicit ledger row, and control projection update together. `NONE` output is legal only before conversion and never under `APPROVED`. `REPAIR_ONLY` must equal exact returned `WB-###:G#:DEFECT-ID` tokens; unrelated valid `AUTHORIZED` history is preserved. No digest-only source/output locator and no other state is valid.

Every hashed `AUTHORIZATION.md`, `PROVENANCE.md`, and per-gate `REVIEW.md` is parsed with the exact ordered machine-key schema in Art Bible section 16.4. Its subset, owner, source/output, gate/evidence, creator/rightsholder, reviewer/non-owner, build/time, decision/defect/disposition, and rationale projection must match the TSV/gate/ledger. Arbitrary bytes or free-form prose cannot satisfy a hash slot.

| Basis | Canonical production ID | Authorization record path@SHA-256 | Gate record path@SHA-256 | Ledger provenance path@SHA-256 | Current source-manifest path@SHA-256 | Current output-manifest path@SHA-256 / `NONE` | State |
|---|---|---|---|---|---|---|---|
| WB-001 | `chr.player.ari` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-002 | `echo.quarrune` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-003 | `env.annex.atrium_lower` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-004 | `col.annex.atrium_lower` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-005 | `col.common.camera_volumes` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-006 | `lmk.annex.simulation_ring` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-007 | `lmk.annex.skylight_spine` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-008 | `prop.annex.field_relay` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-009 | `prop.annex.monitor_console` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-010 | `prop.annex.sim_dais` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-011 | `prop.annex.sim_emitter` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-012 | `font.meridian_raster.body` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-013 | `ui.atlas.relay_core` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-014 | `ui.icons.controller` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-015 | `ui.icons.affinity` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-016 | `ui.panel.dialogue` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-017 | `ui.screen.relay_shell` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-018 | `ui.screen.loading` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-019 | `ui.battle.hud` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-020 | `ui.battle.command` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-021 | `ui.battle.move_info` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-022 | `ui.battle.target` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-023 | `ui.battle.resonance` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-024 | `vfx.move.quarrune.ridge_ram` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-025 | `sfx.move.quarrune.ridge_ram` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-026 | `vfx.move.quarrune.brace_relay` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-027 | `sfx.move.quarrune.brace_relay` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-028 | `vfx.battle.hit_physical` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-029 | `vfx.battle.effectiveness` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-030 | `vfx.battle.state_feedback` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-031 | `vfx.resonance.gain` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-032 | `vfx.resonance.full` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-033 | `vfx.environment.dust_footstep` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-034 | `vfx.finisher.horizon_break` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-035 | `vfx.transition.loading_relay` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-036 | `vfx.transition.fade_dither` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-037 | `anm.humanoid.base` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-038 | `anm.player.ari` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-039 | `anm.echo.quarrune` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-040 | `anm.mech.simulation_ring` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-041 | `anm.ui.loading_relay` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-042 | `sfx.ui` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-043 | `sfx.footstep` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-044 | `sfx.battle_common` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-045 | `sfx.finisher` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-046 | `vox.quarrune` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-047 | `echo.ayselor` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-048 | `anm.echo.ayselor` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-049 | `echo.gyreclast` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-050 | `anm.echo.gyreclast` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-051 | `echo.kivarrax` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |
| WB-052 | `anm.echo.kivarrax` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `INACTIVE` |

## 3. Exact benchmark evidence set

| Evidence ID | Required | Manifest member/path and SHA-256 | Result |
|---|---|---|---|
| `ev.benchmark.native` | six named raw 320×240 members: exploration/dialogue/target_selection/attack_anticipation/impact/support | `PENDING` | `PENDING` |
| `ev.benchmark.enlarged` | exact same six named members at 4× nearest-neighbor | `PENDING` | `PENDING` |
| `ev.benchmark.turntable.player` | neutral/game-light turntables and sheets | `PENDING` | `PENDING` |
| `ev.benchmark.turntable.quarrune` | neutral/game-light turntables and sheets | `PENDING` | `PENDING` |
| `ev.benchmark.animation.player` | locked-camera reel/contact sheets | `PENDING` | `PENDING` |
| `ev.benchmark.animation.quarrune` | locked-camera reel/contact sheets | `PENDING` | `PENDING` |
| `ev.benchmark.environment.corner` | route/reverse/ceiling/props/collision/camera/grade set | `PENDING` | `PENDING` |
| `ev.benchmark.ui` | exact whitelist state matrix/native gallery | `PENDING` | `PENDING` |
| `ev.benchmark.vfx_audio` | hit/support/braid synchronized records | `PENDING` | `PENDING` |
| `ev.benchmark.capture_60s` | uninterrupted native 320×240 representative capture plus wrapper run/event log, decoded-frame audit, and canonical analysis | `PENDING` | `PENDING` |
| `ev.benchmark.performance` | frame/heap/batch/particle/working-set report | `PENDING` | `PENDING` |
| `ev.benchmark.unload_reload` | exact baseline return proof | `PENDING` | `PENDING` |
| `ev.benchmark.gates` | 52 benchmark-scope seven-decision vectors plus four integrated rollups | `PENDING` | `PENDING` |
| `ev.benchmark.authorship` | nine-category rubric/reference calibration | `PENDING` | `PENDING` |
| `ev.benchmark.approval` | signed annotated origin tag attesting separate payload commit/digest and pointing to commit containing this populated control; remote protection confirmed separately | `PENDING external tag ref/signature; never a payload member` | `PENDING` |

The first 14 rows are controlled by exact `review/benchmark/BENCHMARK_EVIDENCE_REGISTRY.tsv`, and their subordinate manifests/measurement records are owned by `review/benchmark/PAYLOAD_MANIFEST.sha256`. Benchmark evidence is ordinary Git text/metadata or canonical Git LFS media only; URL/release locator members are forbidden. The evidence-registry role/count/build/capture projection, exact metric schema/thresholds, and actual bytes all recompute. Pinned ImageMagick `7.1.2-13` proves each native PNG's full decoded 320×240 RGB24 hash equals its unique indexed representative-video frame, then proves exact decoded-pixel equality to its 4× point-filter enlargement. Pinned `ffprobe 8.1.2` and ffmpeg `8.1.2` fully decode the native H.264 representative capture (at least 60,000 ms, at least 30 average fps, exact 4:3, with audio) and byte-compare every frame index/start/duration/RGB hash to `FRAME_AUDIT.tsv`. The validator derives duration, placeholder and sub-30 windows, performance/working-set/warning peaks, and the ordered unload/reload baseline from those matched rows; every measurement value/unit must equal its pinned canonical report.

The same run ID binds build, ROM, Ares 148 audited binary/revision, Homebrew Mode, triple RGBA16 framebuffers, reviewed wrapper/invocation, capture, frame audit, and execution-event log. The event log has exact wrapper/child/`BOOT_READY`/capture/exit order, one child PID, monotonic time, exact hashes, boot-handshake proof, and zero exit. For approval the fresh-public-clone wrapper verifies these files against the exact local ROM/Ares binary and emits an exact digest-bound JSON receipt; operator prose cannot replace it. Reports use only `n64game-evidence-analyzer` `1.0.0` at/after the run. Gate 3 pins the audited Ares platform binary to SHA-256 `7a49f00f96a691458461d7c9cf453d95c0f5c054389bbd87c253987b8b6fa345`. The local semantic snapshot/tamper suite is separately pinned by `test/fixtures/asset_contract/LIFECYCLE_SNAPSHOT_MANIFEST.sha256` at SHA-256 `e0b0e632f7ebd49f48fd8e8a4cd94c682cf9e6d0d0cd3addbf05fb42c84622b0`; its receipt declares `NON_APPROVAL_SEMANTIC_SNAPSHOT`, parallel nonchronological scenarios, and independent approved-to-repair/approved-to-release bindings. It checks schema/type/cross-binding regressions only and never belongs to a benchmark payload. The independent production-shared Ruby harness is called by all seven normalized live lifecycle paths and is pinned at `af9b403081b175e9977ad0b6748d19f9c3220f1a58b8d12d5242b27a8ab750d6` after audit of twelve death cases, exact callsite coupling, profile/gate behavior, ordinary-Git ownership/modes, and isolated fresh-clone execution. Its runner explicitly excludes GitHub, signed-tag, LFS, media, Ares, and ROM-rebuild adapters; the live validator still requires those from reviewed fresh-public-clone bytes. This closes only the lifecycle-harness prerequisite, not the real evidence or approval requirements. Normal validation also always runs the deterministic hardening mutation suite; `--self-test-hardening` prints its telemetry/license/identity/G1-chain/camera/unlock coverage count.

Missing/wrong-version tools, fake headers, fabricated human attestations, missing audio, low frame rate, decode errors, chronology mismatch, report/measurement drift, or dimension/TSV words without byte proof fail closed; untouched `PENDING` invokes no media tools. The payload excludes this control and `ev.benchmark.approval`; the fifteenth row verifies through the signed origin tag and external protection check. `PASS` text alone, `N/A`, missing/blank observation, arbitrary evidence prose, unsafe/cyclic/duplicate ownership, or non-recomputing bytes is `FAIL`.

While the global decision is not approved, each first-14 evidence row is either exact `PENDING`/`PENDING`, or its manifest cell is one canonical populated path@SHA-256 and its Result is exactly `PASS`. A populated row is accepted only when the complete same-commit public payload/evidence registry and every referenced byte validate; `FAIL`, arbitrary result text, or a populated locator paired with `PENDING` is invalid.

Gate-1 concept rejection history does not count as an authorization or benchmark PASS. A current concept may carry the Art-Bible-defined chained `gate.attempt_history`, but each rejected/revise tuple must resolve at a strict public ancestor, while its live output remains `NONE` and all seven live gate tokens remain `PENDING`.

## 4. Objective acceptance

For a completed row, `Actual/evidence` is exactly `<sorted-comma-separated ev.benchmark.<id>#<metric> references> :: <nonempty reviewer observation>`. Every reference resolves to the parsed evidence registry/measurement row; the approval signature may additionally use exact `ev.benchmark.approval#signature`. Arbitrary prose, a bare manifest path, a digest alone, or an empty observation fails.

| Criterion | Required acceptance | Actual/evidence | Decision |
|---|---|---|---|
| Output | 320×240 RGBA16, triple buffered | `PENDING` | `PENDING` |
| Frame rate | 30 FPS target met in every representative benchmark view; every over-budget window explained/resolved | `PENDING` | `PENDING` |
| Peak free heap | at least 512 KiB | `PENDING` | `PENDING` |
| Scene/action arena | no more than 1,100 KiB; exact measured texture, geometry/display, skeleton/animation, collision/nav/state, and VFX category bytes sum to the reported total | `PENDING` | `PENDING` |
| Runtime texture working set | equals the measured scene-texture category and is no more than the battle maximum of 336 KiB; exploration-specific reviews retain the 300 KiB cap | `PENDING` | `PENDING` |
| Unload/reload | resource counts and heap return exactly to measured baseline | `PENDING` | `PENDING` |
| Conversion | zero unexplained warnings and deterministic clean output | `PENDING` | `PENDING` |
| Evidence graph | canonical manifest grammar; every conditional member/hash recomputes; no unsafe path, symlink, duplicate/case collision, self-member, or transitive cycle | `PENDING` | `PENDING` |
| Approval attestation | signed origin tag verifies exact five-line message bytes, payload commit/digest, target control, signer, and exact origin presence without entering payload graph; release operator separately confirms remote protection | `PENDING` | `PENDING` |
| Native readability | route and interaction plus hero Quarrune and the three finished supporting battle-distance silhouettes, their four actor positions, target, result, and UI read at native size | `PENDING` | `PENDING` |
| Completeness | no placeholder/default/incomplete visible face or unmanifested asset | `PENDING` | `PENDING` |
| Rights/provenance | every whitelist production ID complete and retrievable | `PENDING` | `PENDING` |
| Open defects | zero critical/high/medium | `PENDING` | `PENDING` |

## 5. Visual-authorship rubric

No score or average is used. Every category must independently pass with a native/reel evidence reference and a concrete reviewer observation. Calibration may cite the reference-study URL/version and private observation notes, but no protected reference frame enters the public repository or production source.

Each completed `Native evidence and reviewer observation` cell uses the same exact `<sorted references> :: <nonempty observation>` grammar as section 4. References must come from the category's underlying native/turntable/environment/animation/VFX/UI/performance evidence rather than citing `PASS` or the authorship summary itself.

| Category | Failure bar | Native evidence and reviewer observation | Decision |
|---|---|---|---|
| Silhouette and originality | generic/generated/readable only by color; protected similarity | `PENDING` | `PENDING` |
| Environment density and recent activity | empty room, filler scatter, purposeless duplication, incomplete reverse/ceiling | `PENDING` | `PENDING` |
| Topology/material/texture craft | default material, noisy generated texture, weak modeling hidden by surface noise | `PENDING` | `PENDING` |
| Lighting/fog/display grade | flat wash, crushed form, grade-dependent UI, emulator filter required | `PENDING` | `PENDING` |
| Animation/deformation/personality | dead poses, sliding, clipping, generic stock timing, camera hiding omissions | `PENDING` | `PENDING` |
| VFX/audio synchronization | generic particles/audio, hidden result, pool leak, weak source/impact/readback | `PENDING` | `PENDING` |
| UI/loading presentation | tiny/derivative UI, fake wait, unreadable state, stale/raw frame | `PENDING` | `PENDING` |
| Camera staging/native readability | unclear route/target/action, tangent silhouettes, unsafe framing | `PENDING` | `PENDING` |
| Cross-discipline cohesion | individually polished parts that do not look like one authored game | `PENDING` | `PENDING` |

## 6. Independent reviewer record

The three reviewer identities must be distinct and named; each is different from the sole creator of every package in the domain they approve. Asset owners may attend review and implement fixes but cannot fill their own required sign-off. `APPROVED` requires all three rows to say non-owner `YES`, cite the same recomputed payload-manifest digest, use RFC 3339 time, and decide `PASS`.

| Role | Reviewer identity | Non-owner confirmed | RFC 3339 decision time | Reviewed payload-manifest SHA-256 | Decision | Rationale/defect IDs |
|---|---|---|---|---|---|---|
| Art / visual authorship | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` |
| Technical / conversion-performance | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` |
| Gameplay / native readability | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` | `PENDING` |

## 7. Final decision

- Production decision: `PENDING`
- Exact return gate and defect IDs if not approved: `NONE`
- Approving payload commit / clean-build ID / ROM SHA-256 tuple: `PENDING`
- Payload-manifest SHA-256: `PENDING`
- Whitelist/gate-registry SHA-256: `PENDING`
- Benchmark-evidence-registry SHA-256: `PENDING`
- Public release tag / asset URL: `PENDING`
- Approval attestation ref / signer fingerprint: `PENDING`
- Decision owner / RFC 3339 timestamp: `PENDING`

For `APPROVED`, production decision is exactly `APPROVED`, return gate/defects is `NONE`, every final tuple/digest/ref/signer/time/release value equals section 1, all 52 rows are `AUTHORIZED` with populated output manifests and seven completion decisions, all 14 evidence registries/records/metrics and every objective/rubric/reviewer result are valid `PASS`, reviewer non-owner fields are `YES`, identities are pairwise distinct, and defects are `0 / 0 / 0`. The validator also proves the ignored/untracked local ROM, fresh public-clone rebuild, public workflow/release asset bytes, tag object identity/ancestry/reachability, exact signed message, and externally pinned signer. Remote protection is only the separately recorded external release check. No field may infer another or accept an abbreviation.

Only after those checks may all three exact top-level fields be changed together to:

```text
Production-Lock: UNLOCKED
Decision: APPROVED
Status: Gate 4 approved control record
```

Changing only those strings without valid supporting fields is a failed validator result and does not authorize production. Under `PENDING`, `REVIEW_REQUIRED`, or `BLOCKED`, the corresponding locked-state rules and exact return IDs are also mechanically enforced; stale approval/tag history never overrides the current control state.
