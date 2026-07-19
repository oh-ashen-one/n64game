# N64GAME Asset Review Templates

Status: Gate 2 review contract

These forms turn the seven art gates into evidence-backed decisions. Copy the relevant sections into exact `review/<asset_id>/g<gate>/REVIEW.md`, replace every field, link every artifact through the gate's immutable evidence manifest, and keep the history when an asset returns to an earlier gate. A checked box without a manifest member/hash, measurement, build identifier, and reviewer observation is not evidence.

## 1. Review rules

- Review the exact exported asset revision that will be integrated. Record source and generated-output hashes.
- The machine gate decision is exactly `pass`, an allowed completion equivalent, or `fail`. A `fail` review separately records disposition `revise` or `rebuild`; a completion records disposition `NONE`. Never use “good enough,” “mostly done,” or a percentage.
- Every canonical production ID receives exactly seven ordered decisions under its inventory review profile/tier. `A0 present.*` aliases and `E0 ev.*` evidence/control records are the only zero-gate records.
- Bare `N/A`, a blank gate, “inherited,” or an informal substitute is a failure. The only permitted equivalents are `STATIC_STATE_EQ`, `NON_ROM_DELIVERY_EQ`, and `INHERITED_CHILD_EQ`; each requires the exact alternative evidence defined below, same-revision hashes, and reviewer approval.
- Capture at native 320×240 and 4× nearest-neighbor whenever the asset is visible in game.
- A clean concept render cannot pass technical, conversion, animation, or in-engine review.
- A clean converter log cannot pass visual review.
- Critical or high defects block the gate. Medium defects block Gate 7 unless explicitly scheduled and then proven resolved. Low defects may be accepted only with a named owner and no effect on final consistency.
- All production assets pass gates in order. A later failure may reopen any earlier gate.
- `H2` hero assets require two separate documented source revisions after the first in-engine appearance; each pass has before/after native evidence, defect decisions, source/output hashes, and a non-owner reviewer.
- Every accepted asset has a completed provenance/license row in `docs/ASSET_LEDGER.md`.
- Each gate contains `review/<asset_id>/g<gate>/EVIDENCE_MANIFEST.sha256` using the exact six-TAB-field UTF-8/LF/path/token/sort grammar in `docs/ART_BIBLE.md` section 16.3. The review and ledger record the repository-relative manifest path and recomputed 64-lowercase-hex SHA-256; the manifest cannot contain this review when the review records that digest.
- A canonical `RIGGED_MODEL`, `STATIC_MODEL_ENV`, or `ANIMATION` asset, plus any other canonical asset whose transitive source closure owns `.blend`, has exact ordinary-Git `AUTHORING_STACK_RECEIPT.txt` records at G2 and G5. Each is a single direct member of only that gate's evidence manifest at role `authoring.stack_receipt`; rollups and nonapplicable assets forbid the role. The receipt is never nested-only, output-manifest-owned, payload-double-owned, LFS, or copied to another gate.
- An authoring receipt is workflow evidence, not self-authenticating proof. The gate reviewer verifies or witnesses the stack/export result, and final benchmark authority comes only from the pinned-key signed public payload plus the rest of the conversion/in-engine evidence. A hand-written receipt or receipt alone cannot authorize a pass.
- Evidence must be retrievable from the reviewed Git revision as an ordinary blob or canonical Git LFS object. Art-review evidence cannot use public-release/URL locator files; a hashed locator is not the claimed media. Local-only files and screenshots altered after capture cannot support a pass.
- An owner/creator cannot approve their own `H2` Gate 1, 3, 6, or 7. Every `M7`, `S7`, `C7`, and `D7` Gate 7 has at least one named non-owner reviewer; a data-tuple author must not be the sole parent/consumer verifier, and a storyboard generator/operator/editor cannot approve their own delivery. Benchmark art, technical, and gameplay/readability reviewers are three distinct identities.

Manifest preflight is mandatory before reading visual conclusions:

- [ ] UTF-8 without BOM, LF only, one final LF; no blank/comment line.
- [ ] Every line has exactly six literal TAB-separated fields: portable repository-relative path, canonical decimal byte count, 64 lowercase hex, `build:<token|->`, `capture:<token|->`, `role:<semantic-token>`.
- [ ] Paths contain no absolute/`./`/empty/`.`/`..`/backslash/control component, resolve through no symlink and remain inside the repository, match Git case, are unique under exact and case-fold comparison, and sort by raw UTF-8 path bytes.
- [ ] Manifest dependency graph is acyclic; no manifest lists itself or any record that directly/transitively embeds its digest. Every populated/claimed member, byte count, digest, and the manifest digest is retrieved and recomputed; failure is closed.
- [ ] Across the complete graph, every member path, materialized content hash, and non-`-` capture ID has one owner; direct-plus-nested duplication fails.
- [ ] Ordinary blobs equal reviewed Git bytes. Canonical LFS pointer attribute/OID/size, materialized bytes, manifest values, and fresh-public-clone object agree. No locator/`REMOTE_OBJECT` role exists.

### Review-profile applicability and strict equivalents

The assigned profile/tier comes from `docs/ASSET_INVENTORY.md`; reviewers cannot downgrade it. Gate meanings are those in `docs/ART_BIBLE.md` section 16. The following substitute codes are exhaustive:

| Code | Legal use | Mandatory alternative evidence |
|---|---|---|
| `STATIC_STATE_EQ` | Gate 4 only for a truly static model, UI state, or data asset | state/interaction/re-entry/skip/culling or static-invariance matrix; proof that no required animation was omitted |
| `NON_ROM_DELIVERY_EQ` | Storyboard/non-ROM deliverable Gate 5 and 6 only | deterministic delivery package/hash plus high-resolution and 320×240/CRT-safe complete-sequence review |
| `INHERITED_CHILD_EQ` | Reserved aspect-level notation only; it is not a whole-gate completion decision for the 15 authored camera children | parent review/evidence hash, child source/output hash, BOM relationship, and child-specific validator/consumer proof; every camera-child G1–G7 row still uses real `pass` |

No code waives provenance, conversion/package determinism, real-context readability, cleanup, or final consistency. Static audio is not a reason to skip timing/mix review; a storyboard is not a reason to skip delivery conversion or native downsample review; a child with authored values cannot inherit those values' review.

### Severity and disposition

| Severity | Meaning | Required disposition |
|---|---|---|
| `critical` | Rights/clean-room violation, crash, corrupt state, converter corruption, unsafe collision, performance/memory acceptance failure, missing required asset | Stop integration; rebuild or resolve root cause before any pass |
| `high` | Visible broken anatomy/topology/weights, unreadable required UI, identity drift, major clipping, incomplete room face, generic/default final content | Gate fails; revise or rebuild |
| `medium` | Noticeable polish, consistency, timing, material, seam, or dressing issue that survives native-resolution play | Fix before Gate 7 |
| `low` | Small non-blocking refinement with no readability, performance, continuity, or completion impact | Fix if scheduled; record final disposition |

### Evidence naming

Use stable names rather than screenshots named `final2`:

```text
review/<asset_id>/
  g1/AUTHORIZATION.md
  g1/PROVENANCE.md
  g1/GATE_RECORD.tsv
  g1/REVIEW.md
  g1/concept_front.png
  g1/concept_side.png
  g1/concept_back.png
  g1/silhouette_64.png
  g2/topology.png
  g2/REVIEW.md
  g2/uv.png
  g2/weights_stress.png
  g3/turntable_neutral.mp4
  g3/turntable_game_light.mp4
  g4/animation_reel.mp4
  g5/converter.log
  g5/size_report.txt
  g6/native_320x240.png
  g6/frame_heap_report.txt
  g7/lineup.png
  g7/REVIEW.md
```

Before Gate 1 passes, an in-progress ordinary media concept is legal only with the ledger's exact `concept` locator grammar: canonical creator/rights holder, hashed `g1/PROVENANCE.md`, hashed `SOURCE_MANIFEST.sha256`, `output:NONE`, hashed `g1/EVIDENCE_MANIFEST.sha256` plus hashed `g1/REVIEW.md`, and seven literal `PENDING` decisions. The review is a direct evidence-manifest member at role `concept.review`. It owns only source members and Gate-1 provenance/review/evidence; `AUTHORIZATION.md`, `GATE_RECORD.tsv`, `SUBSET_EXPORT_ALLOWLIST.tsv`, `AUTHORING_STACK_RECEIPT.txt`, Gate 2–7 files, converted/output bytes, and `build/generated/` are forbidden. Acceptance also requires exact clean current `HEAD` advertised at a valid public branch or pull-request head/merge ref, plus an explicit same-ref credential-free fresh fetch whose bytes and OID match; ignored extras and symlinks in `assets-src/` or `review/` fail. A `planned` row owns no file, and the 15 fixed C7 tuples do not count as ordinary concepts.

When returning Gate 1, do not overwrite or promote the failed attempt. Add/update the single canonical `g1/attempts/ATTEMPT_HISTORY.tsv` member described in Art Bible 16.4; each row must resolve its source/evidence/failed review at a strict public ancestor commit, chain the prior row bytes, and record an independent reviewer, defects, substantive rationale, and exact `REJECT` or `REVISE`. The current concept review remains `IN_PROGRESS`, output remains `NONE`, and G1–G7 remain `PENDING` until a later genuine pass.

Do not copy free-form prose into the hashed record files. `AUTHORIZATION.md`, `PROVENANCE.md`, completed per-gate `REVIEW.md`, and in-progress concept `REVIEW.md` use the exact ordered `key: value` schemas in Art Bible section 16.4. The human-facing checklist may be longer, but the canonical hashed record must parse and project exactly to its registry/gate/ledger row; completion uses disposition `NONE`, machine `fail` uses `revise` or `rebuild`.

For an active whitelist row, independently inspect the parsed canonical `SUBSET_EXPORT_ALLOWLIST.tsv`: it must enumerate exactly every SOURCE/OUTPUT manifest member and bind production ID, subset digest, stage, path, digest, role, and a sorted deterministic selector list. Metadata/output selectors are fixed; `ALL` is legal only for complete-package content. A partial package must use only its validator-frozen collection/clip/state/sector/cue/asset vocabulary, cover that vocabulary exactly in union, and drive the Gate-5 exporter; it cannot hide or export locked siblings behind one whole-file hash.

For every completed `H2` Gate 7, verify the first-in-engine Gate-6 checkpoint's full historical gate record and parsed source/output closures, then the two-row `POLISH_PASSES.tsv`: two real chained revisions and canonical before/after evidence pairs after that checkpoint, pass 2 resolving to the final hashes, then final Gate-6 revalidation strictly before Gate 7, with exact RFC-3339 chronology, `PASS`/no defects, and non-owner review. Every phase manifest has exact `polish.native_capture`/`polish.phase_report` roles and its report projects scope/phase/hashes/build/reviewer/time/capture digest. Reusing bytes, arbitrary roles, timestamps, or a reviewer who owns any integrated rollup asset fails.

## 2. Common review header

Copy this header into every gate review.

```markdown
### Review record

- Asset ID:
- Inventory row/link:
- Ledger row/link:
- Category:
- Review profile / tier:
- Pair key / parent / generated children:
- Gate number and name:
- Review round:
- Date/time and timezone:
- Reviewer identity and role:
- Reviewer independent of owner for this required decision: yes / no / not-required-with-rule:
- Rights holder / actual asset creator(s):
- Provenance record path and SHA-256:
- Input-rights/license evidence path and SHA-256:
- Transformations/material human edits covered by this revision:
- Editable source path(s):
- Source commit and source-manifest path@SHA-256:
- Generated runtime/delivery path(s):
- Generated output-manifest path@SHA-256 or `NONE` before conversion:
- Canonical `GATE_RECORD.tsv` path@SHA-256:
- Build commit:
- Tool versions/pins:
- Ares version/mode, if applicable:
- Evidence directory:
- Evidence manifest path (repository-relative):
- Evidence manifest SHA-256:
- Previous decision and unresolved defect IDs:
- Machine decision: pass / STATIC_STATE_EQ / NON_ROM_DELIVERY_EQ / INHERITED_CHILD_EQ / fail
- Disposition: NONE / revise / rebuild
- Decision rationale:
- Next responsible owner and due gate:
```

### Defect log template

| Defect ID | Severity | Observation and reproduction | Evidence manifest member + SHA-256 | Required change | Owner | Status | Resolution manifest member + SHA-256 |
|---|---|---|---|---|---|---|---|
| `<asset>-G#-001` | critical/high/medium/low | | | | | open/fixed/accepted | |

Gate decision summary:

- Critical open: `__`
- High open: `__`
- Medium open: `__`
- Low open: `__`
- Gate result: machine `pass`, an allowed completion equivalent, or `fail`; completion disposition is `NONE`; on `fail`, disposition is `revise` or `rebuild`
- Reviewer signature/name and date: `__`
- Evidence manifest SHA-256 signed: `__`

## 3. Gate 1 — Concept and orthographic review

Required evidence: construction sheet, 64×64 silhouette comparison, front/side/back views, functional three-quarter, scale lineup, palette/material callouts, movement/rig notes, and clean-room comparison notes.

### Identity and provenance

- [ ] Asset ID, role, owner, and inventory dependency are explicit.
- [ ] Rights holder and every actual human/agent/tool creator role are distinguished.
- [ ] Original brief and all concept-generation prompts/source files are attached with byte hashes.
- [ ] Every visual/audio/data reference and input is listed with URL/path, acquisition date, hash, purpose, license/terms version, permission evidence, attribution/notice, and legal-use note.
- [ ] Protected references were used only for high-level study; no copied silhouette, costume, layout, icon, logo, name, or surface pattern remains.
- [ ] If generation was used, exact model/product/version, tool/date, complete prompt/negative constraints, selected output hashes, seed/job metadata when exposed, output-rights basis, and all human edits are documented.
- [ ] Transformations are an ordered material record rather than “edited”: selection, paintover/repair, model/UV/rig work, retiming, synthesis/layers, resampling/denoise, palette/format conversion, and removals are named as applicable.
- [ ] Every runtime-generating source is a reviewed ordinary-Git blob or canonical Git LFS object materialized by a credential-free fresh public clone; URLs/releases/later fetches are not production inputs and local-only archives are explicitly non-build.
- [ ] No fake text, malformed anatomy, perspective error, identity drift, or unexplained generated detail remains.

### Design construction

- [ ] Black silhouette is distinct from every same-category roster peer at 64×64.
- [ ] Front, side, back, and functional three-quarter agree on proportions and part count.
- [ ] Top/bottom or exploded views exist where construction cannot otherwise be modeled safely.
- [ ] Scale is shown beside the 1.72 m player and relevant door/battle footprint.
- [ ] Measured dimensions match the explicit scale chart in `docs/ART_BIBLE.md`; any approved revision updates concept, collision, camera, and inventory evidence together.
- [ ] Dominant, secondary, and tertiary shapes follow the assigned Annex, Estate, human, Echoform, or Severance language.
- [ ] Material boundaries can be built with the planned material/texture budget.
- [ ] Palette uses exact art-bible swatches or records an approved addition.
- [ ] Design has a clear front, gaze/action direction, contact points, and center of mass.
- [ ] Required moving parts, joint axes, sockets, VFX origins, and collision needs are marked.
- [ ] Design reads at the minimum intended on-screen height.
- [ ] Back, underside, door reveal, or unseen room surfaces are intentionally resolved, not left blank.

### Quantitative concept record

| Field | Planned value | Art-bible cap | Pass? | Evidence/notes |
|---|---:|---:|---|---|
| Estimated triangles | | | | |
| Materials | | | | |
| Texture atlases and formats | | | | |
| Rig joints / mechanism joints | | | | |
| Required clips/states | | | | |
| Minimum on-screen size | | | | |
| Approximate world dimensions | | | | |

Clean-room check:

- Compared against: `__`
- Similarity risk observed: `__`
- Original differentiators: `__`
- Reviewer conclusion: `clear / revise / legal escalation`

Gate 1 passes only when the modeler could build the asset without inventing identity-critical details.

## 4. Gate 2 — Blender technical review

Required evidence: source statistics, wireframe/topology captures, face-orientation/normal view, UV sheet, transform/origin capture, naming report, weight visualization, deformation stress poses, and validation log.

The mesh/rig checklist below applies to `RIGGED_MODEL` and `STATIC_MODEL_ENV`. Other profiles do not write `N/A`: they complete their named category overlay—including the section-10 `DATA_SPATIAL` overlay—plus the universal provenance, reproducibility, naming, bounds, deterministic-source, and validation checks, and record the profile's Gate 2 source-technical equivalent from the art bible.

### Source integrity

- [ ] If visual-benchmark approval is not yet valid, this exact production ID/subset has its populated `WB-###` authorization basis, explicit ledger row, Gate 1 pass hash, and current source/output hashes in the canonical control; no unlisted sector/clip/state/cue/output is present and the current `PENDING`/`REVIEW_REQUIRED`/`BLOCKED` rules permit this exact work.
- [ ] An `S3` milestone for visual/audio work proves only interface/event/ownership readiness with `tmp.*` integration; it is not submitted as final source or accepted as an `S4` replacement.
- [ ] Source is under `assets-src/<production-id-prefix>/<asset_id>/`, the directory prefix exactly equals the asset ID's segment before its first dot, and the bytes are tracked/licensed correctly.
- [ ] Every build input is an exact reviewed Git/Git-LFS payload member whose actual bytes materialize in a credential-free fresh public clone; no URL/release/later-fetch/manual/local-only production input exists.
- [ ] One Blender unit equals one meter; dimensions match the Gate 1 scale sheet.
- [ ] Location/rotation/scale are applied as required; no negative or accidental non-uniform scale remains.
- [ ] Origin and forward/up axes follow the art bible.
- [ ] Only named export collections contain runtime objects.
- [ ] No `Cube`, `Material`, `.001`, hidden backup, reference plane, high-poly source, camera, or light contaminates the export collection.
- [ ] All object, mesh, armature, bone, material, texture, socket, collision, and animation names follow conventions.
- [ ] When the asset is authoring-stack-applicable, `review/<asset_id>/g2/AUTHORING_STACK_RECEIPT.txt` was generated after an exact stack pass, directly owned by this gate's evidence manifest, and binds this source-manifest SHA-256, output `NONE`, build `-`, and a check time no later than this decision.

### Mesh, normals, and UVs

- [ ] Exported triangle/vertex count is measured after triangulation and within budget.
- [ ] Topology spends edges on silhouette and deformation; hidden or coplanar waste is removed.
- [ ] No unintended duplicate vertices/faces, zero-area faces, loose runtime geometry, or non-manifold defect remains.
- [ ] Face orientation is correct; custom/split normals are intentional and stable after triangulation.
- [ ] Hard edges and UV seams agree where required; no accidental shading seam remains.
- [ ] UV islands have planned texel density and minimum padding.
- [ ] Overlaps are intentional, documented, and do not mirror faces/text/damage incorrectly.
- [ ] Texture atlas dimensions, palette, format, and material count fit the planned runtime cap.
- [ ] Vertex color supports form and lighting without isolated dirt or impossible baked shadow.

### Rig and deformation

- [ ] Exported skin has exactly one bone influence per vertex.
- [ ] Every exported skinned triangle references no more than three bones.
- [ ] Joint count and hierarchy fit budget; unused/deform-disabled bones are removed from runtime export.
- [ ] Bone axes, names, mirrored orientation, and rest pose are consistent.
- [ ] All weighted vertices are assigned; no zero-weight or accidental remote assignment exists.
- [ ] Stress poses cover shoulders/hips/hands or the Echoform’s maximum bends, squash, twist, hood/vane/filament motion.
- [ ] One-influence segmentation preserves volume and avoids visible cracks, shears, or candy-wrapper deformation.
- [ ] Sockets for VFX, audio, interaction, camera focus, feet/contact, and carried props are named and positioned.
- [ ] Mechanisms have correct pivots, limits, and safe rest states.

### Gate 2 measured record

| Metric | Inventory target/cap | Actual | Validation method | Pass? |
|---|---:|---:|---|---|
| Exported triangles | | | | |
| Exported vertices | | | | |
| Materials/draw surfaces | | | | |
| Runtime texture bytes estimated | | | | |
| Rig joints | | | | |
| Max influences per exported vertex | 1 | | | |
| Max bones referenced per triangle | 3 | | | |
| Unweighted vertices | 0 | | | |
| Unexplained non-manifold elements | 0 | | | |
| Unexplained validation warnings | 0 | | | |

Gate 2 fails if the source looks attractive but cannot convert deterministically within the runtime contract.

## 5. Gate 3 — Textured turntable review

Required evidence: 8-angle neutral contact sheet, continuous neutral turntable, representative-light turntable, native-resolution crops, material/texture sheets, and comparison beside roster/location peers.

The turntable checklist applies to visible 3D/UI/VFX work. `AUDIO`, `DATA_SPATIAL`, `STORYBOARD`, and `GENERATED_CHILD` use the profile's isolated/decoded/high-resolution representation plus its representative-context comparison; this is a Gate 3 `pass`, not an N/A.

- [ ] Front, rear, both profiles, both three-quarters, top, and low/underside views are complete.
- [ ] Silhouette remains distinctive in black and in representative background values.
- [ ] Palette and value grouping match the approved concept after runtime-like quantization.
- [ ] Materials read as ceramic, metal, cloth, leather, energy, or living surface without PBR lighting dependence.
- [ ] Texel density is consistent with neighboring assets; no blurry hero zone or wastefully sharp hidden area exists.
- [ ] Seams, mirrored regions, palette banding, filtering, and transparency edges survive rotation.
- [ ] Vertex color supports planes and contact without dirty noise or a fixed-world shadow.
- [ ] Face/gaze, interaction surface, move origin, or mechanism state reads at native gameplay size.
- [ ] No camera angle exposes unfinished geometry, blank texture, penetrating part, accidental hole, or generation artifact.
- [ ] Neutral lighting proves the model; representative lighting proves integration intent.

Turntable record:

- Render/capture settings: `__`
- Neutral light path: `__`
- Representative light path: `__`
- Native crop path and on-screen height: `__`
- Texture atlas/palette path: `__`
- Peer lineup path: `__`
- Observed weakest angle and disposition: `__`

## 6. Gate 4 — Animation and deformation review

Required evidence: complete locked-camera reel, clip/event table, frame-by-frame contact sheets for impacts, foot/contact overlays, deformation stress captures, transition tests, and representative audio/VFX sync preview.

Animation-bearing work uses the reel below. A truly static asset uses `STATIC_STATE_EQ` only with the required state/re-entry/static-invariance evidence. `AUDIO`, `VFX`, UI motion, and storyboards use their timing/sequence overlays and receive a normal Gate 4 pass when complete.

### Clip coverage

| Clip ID | Frames / seconds | Loop? | Root motion | Contact/event frames | Required state | Evidence | Pass? |
|---|---:|---|---|---|---|---|---|
| | | | | | | | |

- [ ] Every clip required by `docs/ASSET_INVENTORY.md` is present with exact stable ID.
- [ ] `anm.humanoid.base` enumerates all 12 owned clips: idle A/B, walk, run, start, stop, turn left/right, interact, talk-neutral, listen, and reaction.
- [ ] Idle variations have personality, asymmetry, safe interruption, and no identical synchronized timing with peers.
- [ ] Locomotion matches runtime displacement; feet/contact points do not slide over two source pixels in a stable shot.
- [ ] Start, stop, turn, reposition, entrance, and exit transitions avoid bind-pose flashes or visible snapping.
- [ ] Anticipation changes center of mass or silhouette and clearly precedes the event.
- [ ] Contact/decision frame is readable at 320×240; recovery returns through a living pose.
- [ ] Hit, knockout, and victory keep valid anatomy, floor contact, and battle footprint.
- [ ] Dialogue performance includes listen/settle behavior and does not loop continuous generic gesturing.
- [ ] Secondary motion is intentionally delayed and does not penetrate body, floor, camera, or props.
- [ ] All required event markers fire once at the intended frame and are safe under skip/pause/fast confirm.
- [ ] VFX origin, target, hit, vocal, footstep, and prop events align within the approved frame tolerance.
- [ ] Locked diagnostic camera proves actor motion; gameplay camera does not hide missing animation.
- [ ] One-influence skinning remains attractive through maximum bends.

Animation defect measurements:

| Test | Acceptance | Actual | Evidence | Pass? |
|---|---|---:|---|---|
| Foot/contact slide | ≤2 source pixels in stable shot | | | |
| Mesh-floor penetration | 0 visible required frames | | | |
| Body/self intersection | 0 unacceptable required frames | | | |
| Missing/duplicate event | 0 | | | |
| Bind/rest-pose flash | 0 | | | |
| Required clips missing | 0 | | | |

## 7. Gate 5 — Tiny3D conversion review

Required evidence: exact conversion command/configuration, pinned tool versions, complete converter log, generated-file manifest and hashes, size report, runtime material/texture report, skeleton/animation enumeration, and automated validator output.

All ROM-bound profiles must pass deterministic conversion even when Blender is not involved. Only `STORYBOARD` may use `NON_ROM_DELIVERY_EQ`, and only with deterministic panel/contact-sheet/package exports and hashes; local manual export is a failure.

For every authoring-stack-applicable asset, Gate 5 conversion runs only through `scripts/record-authoring-stack-receipt g5-export`. The wrapper verifies the exact Blender/Fast64 stack, runs the deterministic exporter without a shell, materializes the review snapshot and `OUTPUT_MANIFEST.sha256`, verifies the stack again, requires the portable identities to match, then writes `review/<asset_id>/g5/AUTHORING_STACK_RECEIPT.txt`. Build the G5 evidence manifest after that sequence so the receipt is a direct `authoring.stack_receipt` member. A post-hoc receipt, precheck failure, exporter failure, postcheck failure, identity drift, or output mutation fails.

- [ ] Source revision and converter inputs match Gate 2/3/4 evidence.
- [ ] Blender, Fast64/exporter, Tiny3D, and libdragon pins are recorded.
- [ ] When applicable, the G5 authoring receipt binds the exact source/output manifest digests and this clean-build ID, and its `checked_at` is not later than this review decision.
- [ ] Conversion runs from a clean checkout with no manual untracked output required.
- [ ] The clean build regenerates runtime output only under ignored `build/generated/assets/...`; the output manifest owns an exact byte-matching Gate-5 review snapshot under `review/<production-id>/g5/`, never a committed build product.
- [ ] No missing texture, material fallback, invalid index, unsupported feature, animation omission, or unexplained warning remains.
- [ ] Exported mesh keeps the intended silhouette, normals, material assignment, UVs, vertex colors, and transparency mode.
- [ ] Exported skin has one bone per vertex and no triangle references more than three bones.
- [ ] All required animation IDs enumerate and play through their full range.
- [ ] Texture dimensions, formats, palettes, and runtime-expanded byte totals match the approved budget.
- [ ] `build/reports/asset_bom.csv` and `build/reports/bundle_sizes.md` distinguish source, packed ROM, unpacked payload, and measured peak resident bytes; alias/shared assets are counted once in ROM.
- [ ] Required/optional/action bundle rollups match `docs/ASSET_INVENTORY.md`, and no overlay plus base exceeds the declared scene arena cap.
- [ ] Generated assets are deterministic or documented metadata differences do not affect runtime content.
- [ ] Source-only helpers, reference images, hidden objects, and unused clips do not enter the runtime package.

Conversion record:

| Field | Value | Evidence |
|---|---|---|
| Conversion command/script | | |
| Blender version | | |
| Exporter/Fast64 commit | | |
| Tiny3D commit | | |
| libdragon commit/CLI | | |
| Input SHA-256 | | |
| Output SHA-256 | | |
| Runtime output bytes | | |
| Texture runtime bytes | | |
| Geometry/display bytes | | |
| Skeleton/animation bytes | | |
| Bundle packed / unpacked / resident rollup | | |
| Deduplicated ROM total | | |
| Converter warnings | | |
| Validator result | | |

Gate 5 has zero unexplained warnings. Writing “harmless” without a reproduced explanation is not resolution.

## 8. Gate 6 — In-engine review

Required evidence: Ares 148 Homebrew Mode build identifier, native and enlarged captures, gameplay video, busy-view frame timing, free-heap trace, draw/material/particle counts, load/unload baseline, collision/camera/follower checks where relevant, and artifact size report.

All ROM-bound profiles require real consumer/Ares context. Only `STORYBOARD` may use `NON_ROM_DELIVERY_EQ`, with the complete high-resolution sequence plus 320×240/CRT-safe downsample review and direct-delivery package proof. A host preview alone cannot pass a ROM asset.

### Visual and functional integration

- [ ] Asset appears with correct scale, orientation, material, texture, vertex color, lighting, fog, shadow, and animation.
- [ ] Raw 320×240 framebuffer and clean capture follow the art-bible display-transform contract; no emulator/capture LUT, HDR, sharpening, saturation, or post-hoc grade is required, and scene grade never affects UI.
- [ ] It reads at its minimum real gameplay size and against its brightest/darkest representative backgrounds.
- [ ] Gameplay cameras show a finished front, side, rear, top/low angle as applicable; no incomplete face is exposed.
- [ ] Interaction prompt, target cursor, dialogue focus, collision, sockets, and state transitions align.
- [ ] Required UI stays within x=16–303/y=12–227 and body text within x=20–299/y=16–223.
- [ ] Asset does not obscure player, target, HP/result, mandatory route, or story performance.
- [ ] Culling/sector transitions do not visibly pop critical silhouettes or remove collision early.
- [ ] Load presentation never shows a raw framebuffer, stale scene, debug text, or uninitialized asset.
- [ ] Applicable native construction relationships (`EXAMPLE_CAM_EXP_01`, `EXAMPLE_CAM_BTL_01`, `EXAMPLE_SCALE_01`) are shown by clean/diagnostic capture pairs or a documented stricter equivalent.
- [ ] Pause, skip, retry, scene exit, and controller reconnect leave the asset in a valid state.

### Performance and memory record

| Metric | Acceptance | Actual | Capture window / tool | Pass? |
|---|---:|---:|---|---|
| Output mode | 320×240, 16-bit, triple buffer | | | |
| Sustained frame rate | 30 FPS target; no approved sequence sustained below budget | | | |
| Mean frame time | ≤33.33 ms target | | | |
| Worst sustained frame-time window | explain every over-budget window | | | |
| Peak free heap | ≥512 KiB | | | |
| Heap after unload | returns to measured baseline | | | |
| Runtime texture working set | equals the measured scene-texture category; no more than 336 KiB in the battle benchmark and 300 KiB in exploration-specific reviews | | | |
| Visible triangles | scene target/cap | | | |
| Opaque/translucent batches | scene target/cap | | | |
| Active particles | event/scene cap | | | |
| Generated asset bytes | inventory cap or approved exception | | | |

Load/unload proof:

- Baseline free heap before load: `__`
- Peak allocation: `__`
- Free heap after synchronized unload: `__`
- Difference from baseline: `__`
- Repetition count: `__`
- Leak/double-free diagnostics: `__`

Gate 6 fails when performance, heap, native readability, or scene ownership is inferred rather than measured.

## 9. Gate 7 — Final consistency and polish review

Required evidence: cast/location lineup, final native gallery, before/after images for two hero polish passes, completed ledger/provenance, repository placeholder report, open-defect report, and category overlay review.

Every canonical production ID completes Gate 7. `H2` requires both polish records; `M7`/`S7`/`C7`/`D7` require their profile-appropriate final comparison. `A0` aliases and `E0` evidence records cannot be reviewed or approved independently.

- [ ] Asset matches the latest art-bible shape, palette, material, texture, lighting, UI, VFX, and animation rules.
- [ ] It looks coherent beside every directly neighboring cast/environment asset.
- [ ] It is neither noticeably weaker nor distractingly over-detailed at its real camera distance.
- [ ] Hero asset polish pass 1 is documented with before/after evidence and specific decisions.
- [ ] Hero asset polish pass 2 is documented with before/after evidence and specific decisions.
- [ ] For non-`H2`, the inventory tier and reason the hero-only polish rows do not apply are recorded; this does not waive any gate.
- [ ] The required non-owner Gate 7 reviewer is recorded for every `M7`/`S7`/`C7`/`D7`; C7 parent/consumer proof and D7 direct-delivery proof are not self-approved by their author/operator.
- [ ] If this is a regular-move child, Gate 7 closes only with both explicit suffix-matched rows approved: one of exactly 32 `vfx.move.*` and one of exactly 32 `sfx.move.*`, separate provenance/gates/evidence, and the shared synchronized pair capture.
- [ ] All critical/high/medium defects are resolved with linked evidence.
- [ ] All final clips/states/screens/angles remain present after integration changes.
- [ ] Provenance, separate rights holder/creator, every input-rights record, source prompt/file/tool/date/hash, ordered transformations/human edits, output license, retrievable editable source, reproducible runtime/delivery output, and Gates 1–7 are complete in the ledger.
- [ ] The signed evidence-manifest hash recomputes exactly and every manifest member is retrievable from the reviewed release candidate.
- [ ] Placeholder/default-material/primitive/TODO/FIXME/raw-generation search is clear for this asset and scene.
- [ ] No protected reference material, ambiguous media, unlicensed font, or external asset slipped into source or output.
- [ ] Final evidence is captured from the release candidate, not an earlier prettier build.

Final comparison:

| Comparison | Evidence | Reviewer observation | Pass? |
|---|---|---|---|
| Approved Gate 1 concept vs final model | | | |
| Neutral turntable vs in-engine | | | |
| Asset vs direct roster peers | | | |
| Asset vs surrounding location | | | |
| Native 320×240 vs enlarged capture | | | |
| First integration vs polish pass 1 | | | |
| Polish pass 1 vs polish pass 2 | | | |

## 10. Environment and landmark review overlay

Apply this in addition to Gates 1–7 for every `env.*`, `lmk.*`, and traversable prop group.

### Completeness and storytelling

- [ ] Floor, walls, ceiling/sky, door reveals, back faces, window views, underside of stairs, and portal transitions are finished wherever a camera can see them.
- [ ] Room function is legible through architecture and purposeful props before dialogue explains it.
- [ ] Dressing shows owner, job, route, and recent activity; no filler scatter or unexplained duplication.
- [ ] Annex and Estate remain distinguishable in untextured silhouette and converted palette.
- [ ] Landmark is visible from at least two intended route compositions and does not block navigation.
- [ ] Mandatory route uses value, framing, floor bands, light pools, and prop orientation before objective arrows.
- [ ] Optional examine points have safe approach and exit positions.
- [ ] Lighting/fog establish depth without hiding missing construction.
- [ ] Blob shadows/contact cues anchor people, creatures, and moving props.

### Navigation, collision, camera, and culling

- [ ] Render and collision overlays are both attached.
- [ ] ZoneDef resolves the approved required/optional/action bundles, collision asset, nav graph, and spawn table from `docs/ASSET_INVENTORY.md`.
- [ ] Every door/elevator/map transition, dialogue block, battle lane, follower handoff, and off-camera recovery spawn is capsule-clear, camera-safe, correctly faced, and reachable by the intended nav graph.
- [ ] Player can traverse every required route without snag, fall-out, prop trap, or unintended slope failure.
- [ ] Camera is tested at corners, doors, stairs, balcony rails, moving mechanisms, and close walls.
- [ ] Tavi companion route uses at least 2.2 m critical width or a documented recovery solution.
- [ ] Doors/elevator/gates cannot crush, trap, desynchronize, or leave control locked.
- [ ] Battle footprints and cameras are free of environment penetration.
- [ ] Sector/portal visibility is tested from boundary positions; no visible hole or premature pop remains.
- [ ] Re-entering the room and repeating optional interactions does not duplicate state or leave props in invalid poses.

Environment metrics:

| Metric | Planned | Actual busy view | Evidence | Pass? |
|---|---:|---:|---|---|
| Full package triangles | | | | |
| Maximum visible triangles | | | | |
| Collision triangles | | | | |
| Nav nodes / directed edges | | | | |
| Spawn / safe anchors | | | | |
| Texture working set | | | | |
| Opaque/translucent batches | | | | |
| Active moving mechanisms | | | | |
| Mean/worst sustained frame time | | | | |
| Peak free heap | ≥512 KiB | | | |

Route test record:

| Route / interaction | Player | Camera | Companion if applicable | Re-entry | Result/evidence |
|---|---|---|---|---|---|
| | | | | | |

Story-prop ownership matrix:

| Story beat / prop | Production asset | Actor/mechanism animation owner | Paired SFX | UI/state owner | Native integration evidence | Pass? |
|---|---|---|---|---|---|---|
| Relay acquisition dock | `prop.annex.relay_dock` + hero Relay | `anm.jo_renn.relay_dock_release/relay_handoff` + `anm.mech.field_relay_integration` | `sfx.environment.relay_dock_release` | acquisition story state | | |
| Pell side reader | `prop.annex.relay_side_reader` + same hero Relay | `anm.player.ari.relay_side_reader`, `anm.pell_anwar.side_reader_trace`, `anm.mech.field_relay_integration` | insert/trace/release events | `ui.panel.relay_trace` | | |
| Director assignment cradle | `prop.annex.director_relay_cradle` | static authored prop; dialogue camera proves empty socket and distinct design | room ambience | Relay objective start; no duplicate hero Relay | | |
| Calibration locator tag | `prop.annex.calibration_locator_tag` | `anm.tavi.tag_place_reveal` + `anm.prop.calibration_locator_tag` | `sfx.story.locator_tag_ping` | calibration/reunion story state | | |
| Rusk wrench drop | `prop.estate.rusk_wrench` | `anm.rusk.wrench_work/wrench_drop` | `sfx.story.rusk_wrench_drop` | prebattle story state | | |
| Estate cut-wave confrontation | same `prop.annex.field_relay` beside fountain | `anm.mech.field_relay_integration.estate_cut_wave_chirp` | `sfx.story.estate_cut_wave_chirp` | confrontation trigger | | |
| Rusk full-team restoration | both real starters + Rusk | `anm.rusk.team_restore` | `sfx.story.rusk_team_restore` | `vfx.story.rusk_team_restore`; transactional full-HP result | | |
| Impossible compass examine | `prop.estate.impossible_compass` | `anm.prop.impossible_compass` | `sfx.environment.compass_needles` | invention-hall examine state | | |
| Orrery hold-switch / study stair | `prop.estate.orrery_switch` + `lmk.estate.grand_orrery` | `anm.prop.orrery_switch` + `anm.mech.grand_orrery` | `sfx.environment.orrery` | held interaction, arm-clear/stair-open collision handoff, interrupted reset, re-entry state | | |
| Packet-recorder answer | `prop.estate.packet_recorder` + Ayselor keel lamp | `anm.prop.packet_recorder.keel_lamp_answer` + `anm.echo.ayselor.story_packet_ping` | `sfx.story.packet_recorder_answer` | reunion trigger and interruption-safe reset | | |
| Closing moving trace | `prop.annex.beacon_decoder` | `anm.mech.beacon_decoder.moving_trace/trace_shift/fracture_bend` | `sfx.story.hook_two_note_low_third` + Fracture cues | hook timeline and monitor trace state | | |
| Solace model practical | `prop.annex.solace_model` | `anm.prop.solace_model.practical_light_on/beacon_answer/fracture_flicker` | hook/Fracture cue timing | hook timeline material state | | |
| Closing starter/player performance | player + Quarrune + Ayselor | `anm.player.ari.hook_resolve`, `anm.echo.quarrune.story_brace_alert/story_resolve`, `anm.echo.ayselor.story_lamp_dim_alert/story_resolve` | hook/Fracture cues | exact HOOK_008/HOOK_014 events | | |
| Ivo track-roll comparison | `prop.estate.ivo_track_roll` | `anm.ivo_veyra.compare_track_roll` | `sfx.environment.paper_roll` | reunion story state | | |

- [ ] The same `prop.annex.field_relay` source instance and keyed socket language carry through workshop dock, Jo handoff, player hand, Pell side reader, and Relay UI hero render; no substitute model, scale drift, or overlap-only fake insertion appears.
- [ ] Every story-prop row completes normally and through skip, cancel, interruption, re-entry, and load recovery without duplicate props, stale sockets, repeated SFX, or an incorrect persistent state.

### DATA_SPATIAL scoped review overlay

Apply this overlay, in addition to the profile-equivalent Gates 1–7, to every `col.*`, `nav.*`, `spn.*`, `int.*`, and `bnd.*` production ID. It reviews authored spatial/data behavior, not the neighboring render package by implication. Each ID has its own source/output/evidence manifest and a non-owner Gate 7 reviewer.

- [ ] Canonical ID resolves to exactly one inventory row, one parent `ZoneId`/bundle owner where applicable, one `DATA_SPATIAL / S7` ledger row, and one seven-decision vector.
- [ ] Gate 1 records purpose, ownership, coordinate space, bounds/capacity, consumers, failure behavior, and clean-room/original-source basis.
- [ ] Gate 2 proves schema/marker/mesh source, exact units/origin/naming, deterministic authoring constraints, safe numeric ranges, and validator output; render geometry or screenshots are not substituted for source.
- [ ] Gate 3 supplies a decoded table/overlay with IDs and bounds readable over the correct scene plus a reverse lookup showing no orphan/duplicate entry.
- [ ] Gate 4 exercises transition, re-entry, interruption, rollback/failure, and static-invariance behavior; `STATIC_STATE_EQ` is used only with the complete matrix.
- [ ] Gate 5 clean-generates the exact binary/table/BOM child with input/output hashes, byte count, capacity report, and zero unexplained warnings.
- [ ] Gate 6 proves the real Ares consumer, collision/nav/camera/resource behavior, route/follower safety, and load/unload ownership at native resolution.
- [ ] Gate 7 compares the final scene matrix, proves every required/optional/action owner and reverse reference, resolves all medium-or-higher defects, and receives a named non-owner decision.

| Scope | Required subtype proof |
|---|---|
| `col.*` | simplified collision is independent of render mesh; no holes/snags/unsafe slope/early removal; door, elevator, battle footprint, camera clamp, and fallback volume tests as applicable |
| `nav.*` | all mandatory nodes/edges reachable; portal and follower-width/handoff paths valid; no isolated island, invalid edge, or route through closed collision |
| `spn.*` | every actor/safe/recovery anchor is unique, correctly faced, capsule-clear, reachable, and owned by the correct state; no orphan or unsafe fallback |
| `int.*` | every marker resolves one action/focus/approach owner; eligibility, cancel, repeat, re-entry, and save/load do not duplicate or strand interaction state |
| `bnd.*` | required/optional/action payloads and lifetimes are exact; no alias bytes, duplicate ROM payload, base/overlay double ownership, stale resident scope, or cap violation |

DATA_SPATIAL measured record:

| Source ID | Parent/consumer | Input SHA-256 | Output SHA-256 | Rows/bytes/cap | Validator | Ares route/failure evidence | Gate result |
|---|---|---|---|---:|---|---|---|
| | | | | | | | |

## 11. Humanoid character review overlay

- [ ] 64×64 silhouette is distinct by shoulder line, center of mass, negative space, and accent—not texture alone.
- [ ] Approximately 6.5-head stylization, enlarged hands/head, and actual character age/role are consistent with the art bible.
- [ ] Player reels prove exact authored `starter_hand_to_chest`, `dialogue_nod`, `field_hand_signal`, and `hook_resolve` performances plus the battle-command pose; scene cues do not rely on an unnamed generic gesture.
- [ ] Face has modeled brow/nose/jaw planes; gaze reads at dialogue distance.
- [ ] Skin palette is intentionally authored for the character with coherent lit/base/shadow ramps.
- [ ] Costume has two or three large color blocks, functional closures, and no random micro-accessories.
- [ ] Front/back/side costume continuity matches concepts and portraits.
- [ ] Hands contact Relay, tools, doors, and scene props without obvious gap or penetration.
- [ ] Base rig retargeting does not erase character posture or create clone motion.
- [ ] Named character has required bespoke gestures and scene performance.
- [ ] Player model reads in exploration, battle-command, dialogue, Relay, and companion scenes.
- [ ] Tavi follower animation supports door wait, separation recovery, and non-blocking return.
- [ ] Follower hard recovery uses `vfx.story.follower_recovery_relay_shimmer` with `sfx.story.follower_recovery_relay_shimmer`, stays Relay-cyan/violet-free, resolves at the previous camera-safe portal, and emits once per recovery.

Character identity record:

- Dominant silhouette phrase: `__`
- Minimum tested on-screen height: `__ px`
- Face/gaze native capture: `__`
- Costume palette swatches: `__`
- Bespoke clip IDs: `__`
- Portrait/model continuity evidence: `__`

## 12. Echoform review overlay

- [ ] Design combines one physical phenomenon, one non-animal structural metaphor, and one movement verb.
- [ ] Exactly one primary Resonance organ is visible and functionally animated.
- [ ] Front, gaze/action direction, balance, contact points, and locomotion are understandable without a real-animal head.
- [ ] 64×64 silhouette is distinct from all seven other Echoforms.
- [ ] Design does not read as a real animal with armor/accessories or resemble a protected creature family.
- [ ] Affinity appears as a controlled accent; identity does not depend on color.
- [ ] Four canonical moves have correct named animation, VFX socket, event frame, and paired audio event.
- [ ] Entrance, idle A/B, reposition, hit, knockout, and victory all express the same anatomy and weight.
- [ ] Finisher participant has a bespoke clip and does not disappear behind the camera/VFX.
- [ ] Floating designs have stable height behavior and authored blob shadow.
- [ ] Knockout preserves anatomy and battle footprint; no generic smoke disappearance replaces performance.

Roster comparison matrix:

| Peer Echoform | Silhouette difference | Locomotion difference | Resonance-organ difference | Palette/value difference | Pass? |
|---|---|---|---|---|---|
| | | | | | |

Canonical move check:

| Move | Animation ID | VFX ID | Audio ID | Socket/event | Native proof | Pass? |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |

## 13. Animation review overlay

Use for humanoids, Echoforms, mechanisms, cameras, and UI motion.

- [ ] Clip is necessary for the inventory/state contract and named by stable data ID.
- [ ] First readable pose, anticipation, contact/decision, recovery, and settle frames are identified.
- [ ] Loop seam has no position, lighting, bone, particle, or audio discontinuity.
- [ ] Event markers remain correct at 30 FPS and under pause/resume.
- [ ] Skip/rapid-confirm ends in the same authored state as normal playback.
- [ ] Root motion and gameplay displacement have one explicit owner.
- [ ] Mechanism limits and collision state update atomically with visible motion.
- [ ] Camera motion preserves screen direction, target readability, safe area, and actor animation.
- [ ] UI motion completes in its specified timing and input remains deterministic.

Pose/contact sheet:

| Clip | Anticipation frame | Contact/decision frame | Recovery frame | Settle/loop frame | Notes |
|---|---:|---:|---:|---:|---|
| | | | | | |

## 14. UI, type, icon, and loading review overlay

- [ ] The exact 37 production IDs in `docs/ASSET_INVENTORY.md` section 16.1 equal the exact 37 `ev.ui.*.native` subjects: 35 `ui.*` plus two `font.*`, with zero missing, duplicate, alias, or orphan IDs.
- [ ] Each package has its own evidence-manifest hash even when one native capture proves regions belonging to several packages; each manifest identifies the exact region/state it claims.
- [ ] Captured at 320×240 with x=16–303/y=12–227 safe overlay; required body text stays within x=20–299/y=16–223.
- [ ] Original `Meridian Raster` body glyphs explicitly cover `A–Z`, `a–z`, `0–9`, and every punctuation mark used by locked sentence-case dialogue/UI copy; the 128×128 IA4 atlas remains ≤8 KiB.
- [ ] Every authored string, eight-character name, number, and controller prompt renders without fallback fonts, replacement boxes, missing glyphs, or fabricated pseudo-text.
- [ ] Body cap height/line spacing is 8/10 pixels or an explicitly approved readable variant.
- [ ] All strings wrap deterministically; dialogue never exceeds three visible lines.
- [ ] Longest player name, longest move, longest speaker, low HP, STAGGERED plus maximum simultaneous Power/Guard/Speed/EMPOWERED modifiers, and all target layouts are tested.
- [ ] Selection, focused, disabled, invalid, full, saving, failure, and reconnect states differ by shape/icon/pattern as well as color.
- [ ] Affinity, STAGGERED, volatile modifier, Relay, and controller icons remain distinguishable in silhouette and reduced saturation.
- [ ] The controller atlas contains and native-capture tests exactly 12 distinct icons: Stick, D-pad, A, B, L, R, Z, C-Up, C-Down, C-Left, C-Right, and Start. Vertical camera prompts compose unambiguous `L + C-Up` and `L + C-Down` chords; bare `C-Down` remains Relay. No locked prompt substitutes text, a generic C cluster, or a missing glyph.
- [ ] Battle info/callouts use exact `STRONG — 1.5× affinity force` and `RESISTED — 0.75× affinity force`; no obsolete multiplier or additional ailment label appears.
- [ ] Every nonzero move priority is visible in move information and predicted order through the authored glyph plus exact label (for this chapter, `PRIORITY +1`); priority tiers visibly precede Speed and no hidden priority exists.
- [ ] Minimum selectable row height is 18 pixels and target-icon gap is at least 6 pixels.
- [ ] Cursor movement settles within 80–120 ms and paired audio is synchronized.
- [ ] The reusable settings panel is reachable from both title and pause, owns text speed, invert X/Y, music/SFX volume, rumble, X/Y overscan, and UI contrast, and exposes readable live preview, defaults, apply, and cancel states.
- [ ] Title Apply always updates only the sanitized process-resident profile, creates no SaveRequest, and makes no persistence claim, whether the journal is empty, invalid, or verified. New Game copies the profile into its first campaign page; Continue overlays it after decode and visibly/semantically begins DIRTY when any of the eight bytes differ. Only stable initialized Pause Apply performs the atomic sanitized settings-only journal update. Cancel, Pause write failure/retry, progress preservation, dirty-overlay presentation, and invalid-value recovery are all visibly correct.
- [ ] The Field Relay exposes a complete manual-save surface with current stable checkpoint/location, confirm, transition-blocked, writing, success, failure, retry, and safe-cancel states; no indicator alone substitutes for the actionable screen and no failed write claims success.
- [ ] `ui.screen.relay_map` is information-only: locked/unlocked focus, detail, directional navigation, and cancel/back are proven, while confirm cannot enqueue travel, select a destination transaction, or bypass world interaction. Physical `veh.meridian.sand_skimmer` boarding and its owned route/transition contract are the only travel initiator.
- [ ] `ui.screen.relay_messages` is information-only: it renders only the derived `READ`, `PENDING`, or `RESOLVED` story state and exact state-driven detail copy; open, focus, detail, Back, and re-entry mutate no story/read bit and manufacture no `UNREAD` state.
- [ ] No copied monster-battle UI composition, modern mobile card, tiny desktop type, fake text, or unlicensed font remains.
- [ ] Loading treatment corresponds to real work, never extends wait, and never exposes stale/raw/uninitialized frames.
- [ ] Raw framebuffer, 4× nearest-neighbor, overscan/blur, and reduced-saturation captures use no emulator/capture grade; scene grade never tints UI and matches the art-bible display-transform contract.
- [ ] The `INSERT CUTSCENE HERE` slate is exact and polished: 8-frame fade-in, 90-frame fully visible hold, 8-frame fade-out (106 ticks total) or immediate A/Start skip; every path uses the same finalizer and flag handoff.
- [ ] The end card owns `ZONE_END_CARD_UI`; no prior traversable/world-map `ZoneId`, environment bundle, collision, nav, spawn, or interaction scope remains resident.

UI test matrix:

| Surface | Default | Longest text/name | Disabled/invalid | Rapid input | Overscan/blur | Native evidence | Pass? |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

Contrast record:

- Foreground/background colors and measured ratio/tool: `__`
- Reduced-saturation/grayscale evidence: `__`
- Low-quality CRT simulation evidence: `__`
- Color-independent state cue: `__`

## 15. VFX review overlay

- [ ] For a regular move, the pair key resolves one `vfx.move.*` row and one suffix-matching `sfx.move.*` row; both have separate ledger/provenance/gate/evidence records and one synchronized in-engine pair capture.
- [ ] Effect clearly shows source, selected target, direction, and result.
- [ ] Anticipation, travel/build, impact, and recovery are each identifiable.
- [ ] Support motion travels inward/upward and cannot be mistaken for hostile impact.
- [ ] Affinity uses the approved accent and does not overwrite character identity.
- [ ] Resonance uses mint partner pulses and gold only at full/finisher peak.
- [ ] Fracture uses offset edges/negative silhouette/cold core, not generic purple smoke.
- [ ] Effect remains readable at native resolution with transparency disabled in a diagnostic capture.
- [ ] HP, STAGGERED/volatile modifiers, target cursor, actor face, and result text remain readable throughout.
- [ ] Particle/strip count fits event and scene cap; no unbounded emitter exists.
- [ ] Pool returns to baseline after completion, skip, pause, knockout, retry, and scene exit.
- [ ] VFX event and paired audio/animation contact align at 30 FPS.

VFX event record:

| Field | Value / evidence |
|---|---|
| VFX ID / paired audio ID | |
| Pair key / VFX evidence hash / audio evidence hash | |
| Source socket | |
| Target rule | |
| Anticipation frame | |
| Impact/result frame | |
| Lifetime | |
| Peak particles/strips | |
| Texture/material bytes | |
| Pool baseline before/after | |
| Max-load four-actor test | |
| Transparency-off diagnostic | |

## 16. Audio review overlay

- [ ] Source master/session, actual creator/tool roles, separate rights holder, every input hash/license/permission, ordered transformations, output license, and provenance-manifest hash are recorded.
- [ ] Every runtime-generating source is an exact reviewed Git/Git-LFS payload member retrievable by clean build; any local-only archival master is explicitly non-build and cannot stand in for production input.
- [ ] The move-audio set is exactly 32 `sfx.move.*` production IDs, suffix-bijective with the 32 `vfx.move.*` pair children; every audio child owns `ev.audio.move.<id>`, seven decisions, and synchronized pair proof.
- [ ] Runtime format, channel count, sample rate, compression, and byte size are measured.
- [ ] Mono compatibility and approximately 22.05 kHz treatment are intentional where suitable.
- [ ] Loop start/end are click-free and musically stable for at least three loops.
- [ ] Head/tail silence is deliberate; event cues respond within the intended frame.
- [ ] No clipping, DC offset, accidental denoise artifact, stock watermark, voice fragment, or copyrighted sample remains.
- [ ] Creature vocal derives from its Resonance organ/body and is distinct from all roster peers.
- [ ] Move sound identifies source/build/impact/result using shared layers only where composition remains unique.
- [ ] UI confirm/cancel/invalid/Resonance/save/message cues remain distinct at low playback level.
- [ ] Music leaves space for commands, dialogue, impacts, and creature vocals.
- [ ] Scene transition stops/fades/releases the old stream/bank without pop or resident leak.
- [ ] Estate confrontation uses the dedicated `sfx.story.estate_cut_wave_chirp`; Rusk restoration synchronizes `anm.rusk.team_restore`, `vfx.story.rusk_team_restore`, and `sfx.story.rusk_team_restore`; follower recovery synchronizes its dedicated shimmer VFX/SFX.
- [ ] Hook packet resolution uses `sfx.story.hook_two_note_low_third`: the established Field Relay two-note cue followed by one clearly lower third tone; no generic beacon-message cue substitutes for this exact event.

Audio technical record:

| Field | Source | Runtime | Acceptance/result |
|---|---|---|---|
| Format | | | |
| Channels | | | |
| Sample rate | | | |
| Duration | | | |
| Loop start/end | | | |
| Peak / loudness measurement | | | |
| File bytes | | | |
| Resident bytes | | | |
| Event frame/latency | | | |
| License/provenance | | | |

Mix test matrix:

| Context | Music | Ambience | UI/dialogue | VFX/impact | Vocals | Result/evidence |
|---|---|---|---|---|---|---|
| Exploration busy view | | | | | | |
| Four-actor battle | | | | | | |
| Duo finisher | | | | | | |
| Loading/transition | | | | | | |
| Closing Fracture hook | | | | | | |

## 17. Storyboard and continuity review overlay

Use for all 18 panels, contact sheet, continuity sheets, color script, and shot list.

Each canonical `sb.*` item is `STORYBOARD / D7` and receives seven ordered decisions. Gate 5 and 6 may use only `NON_ROM_DELIVERY_EQ`: deterministic numbered export/contact-sheet/package hashes at Gate 5, then high-resolution sequence plus 320×240/CRT-safe downsample and direct-delivery proof at Gate 6. The code is not permission to skip provenance, anatomy/continuity, package integrity, or user-facing review.

### Per-panel record

| Field | Value |
|---|---|
| Panel/shot ID | |
| Image path and SHA-256 | |
| Evidence manifest path and SHA-256 | |
| Dimensions/aspect | |
| GPT Image generation record | |
| Human edits | |
| Intended duration | |
| Framing/lens/camera height | |
| Camera movement | |
| Subject blocking/action | |
| Performance | |
| Lighting/color/atmosphere | |
| Transition in/out | |
| Dialogue/text | |
| Sound/music intent | |
| 320×240/CRT-safe note | |

### Per-panel checks

- [ ] Image is high-resolution 4:3, minimum 1600×1200, with no accidental crop.
- [ ] Panel matches the approved shot purpose and connects clearly to previous/next action.
- [ ] Solace hull, pods, hardpoints, orange tail, gliders, restraint lines, crew, beacon, and colossal Echoform match continuity sheets where visible.
- [ ] Screen direction, time of day, vehicle orientation, line attachments, and storm position are consistent.
- [ ] Character/creature anatomy and scale are coherent; no malformed hands/limbs/vehicle parts remain.
- [ ] No fake/gibberish text, watermark, panel number baked into art, or protected design appears.
- [ ] Palette follows warm dusk → violet Fracture storm → cool simulation color script.
- [ ] Primary action reads at 320×240; essential detail stays CRT-safe.
- [ ] Lighting and perspective do not change arbitrarily between adjacent shots.
- [ ] Generation prompt, tool/date, edits, provenance, and rights status are in the prompt manifest/ledger.
- [ ] Rights holder, source-output rights basis, every selected generation hash, ordered human correction, and rejected-output disposition are explicit; “GPT Image” alone is not provenance.

### Sequence checks

- [ ] Exactly 18 unique numbered panels exist in story order.
- [ ] Contact sheet uses those exact approved files and has readable applied numbers.
- [ ] Shot durations total 60–90 seconds.
- [ ] Sequence establishes Solace, research purpose, desert scale, Severance interception, colossal power, crew danger, falling beacon, and transition to name entry/simulation.
- [ ] Sequence is animatable: establishing views, screen direction, action continuity, performance beats, and transitions are sufficient.
- [ ] Continuity package includes Solace, glider, Severance figures, Solace crew, protagonist/name-entry context, Fractured colossus, beacon, the key desert/storm/research-deck environment sheet, spatial map, and color script.
- [ ] `storyboard/opening/SHOT_LIST.md` includes every master-spec field and exact format-neutral paths `rom:/cinematic/opening_solace.video`, `rom:/audio/cinematic/opening_solace.audio`, and `rom:/data/cutscene/opening_solace.cut`, the manifest-declared formats selected during future user-supplied video integration, plus idempotent `opening_cinematic_finish`, safe A/Start shutdown, missing/decode fallback to the slate, flag set, input-edge clear, and handoff to `SCENE_NAME_ENTRY`.
- [ ] Individual panels, contact sheet, continuity assets, color script, and shot list were delivered directly to the user.

Continuity matrix:

| Element | Approved sheet | Panels present | Identity drift found? | Fix/evidence | Pass? |
|---|---|---|---|---|---|
| Solace carrier | | | | | |
| Severance glider | | | | | |
| Severance figures | | | | | |
| Solace research crew | | | | | |
| Protagonist/name-entry context | | | | | |
| Fractured colossus | | | | | |
| Emergency beacon | | | | | |
| Desert/storm/research-deck environment | | | | | |
| Desert/storm spatial map | | | | | |

## 18. Visual benchmark approval form

The populated control record is always `docs/VISUAL_BENCHMARK_APPROVAL.md`; do not create a differently named local sign-off. `PENDING`, `REVIEW_REQUIRED`, and `BLOCKED` all require `Production-Lock: LOCKED`; only mechanically complete `APPROVED` pairs with `UNLOCKED`. `PENDING` permits exact populated whitelist authorizations, `REVIEW_REQUIRED` freezes new subsets and permits only named affected-row reauthorization, and `BLOCKED` permits only named defect remediation with no newly accepted converted/review output. The benchmark is the final-quality non-ID sub-sector `env.annex.atrium_lower#sector.atrium_lower.sim_threshold_corner`, not either complete Annex environment package and not a greybox dressed for one screenshot.

For any post-approval review, first apply Art Bible section 16.7. Confirm the worktree/index is completely clean; local and credential-free public default `HEAD` are identical; the signed approval target is an ancestor; no ROM extension is tracked/staged; and unchanged history matches all 15 ledger cells plus current referenced bytes. If anything changes, require direct current ledger/inventory ownership by `review/production/PAYLOAD_MANIFEST.sha256`, no workflow member, `SHA256("FULL_PRODUCTION")` plus `subset_allowlist: NONE` for each changed/new active row, and exact pair/generated controls with no special-namespace extras. Validate and scan the public commit, not mutable worktree bytes.

- [ ] Every pre-approval final source/output is inside the exact 52-production-ID canonical whitelist and exact permitted sector/clip/state/cue/asset list, with a populated unique `WB-###` basis, explicit ledger row, Gate 1 pass hash, canonical source-manifest `path@SHA-256`, and canonical output-manifest `path@SHA-256` or literal `NONE` matching the files.
- [ ] `env.annex.sim_chamber` and the other three `env.annex.atrium_lower` sectors remain final-production locked.
- [ ] Every whitelist production ID has exactly one inventory-resolving explicit ledger row, complete provenance/input rights/transformations/retrievable source, deterministic profile/tier, current gate vector, and canonical evidence-manifest state.
- [ ] The exact eight `present.*` labels are non-owning `alias_of`; any BOM alias has only the ordered owner list and `payload_bytes=0`, with offset/path/hash/compression/source/creator/rights/license/provenance/status/gates/evidence literal `NONE`, and contributes no payload/count/deduplication input.

### Required benchmark package

- [ ] Exact final room sector: ceramic brace, teal service cage, floor change, warm practical, cool ambient, simulation-facing doorway, signage glyphs, complete scoped collision/camera volumes, and at least five purposeful prop instances.
- [ ] Final player model: exploration idle, walk, run, interaction, and dialogue gesture.
- [ ] Final Quarrune: idle A/B, entrance, one attack, one support, hit, knockout, and Horizon Break participation preview.
- [ ] Ayselor, Gyreclast, and Kivarrax are fully finished supporting battle-distance silhouettes using only each exact final distance model, texture, rig, blob shadow, `idle_a`, `reposition`, and `hit`; Quarrune remains the only hero Echoform, and no supporting hero mesh, other clip, move VFX/audio, portrait, vocal, or full-package output exists pre-approval.
- [ ] Each supporting `echo.* / RIGGED_MODEL / H2` subset has its own seven decisions, independently reviewed first-in-engine checkpoint, two real polish revisions, and final Gate-6 revalidation; each paired `anm.echo.* / ANIMATION / M7` subset has its own seven decisions and exact three-clip evidence.
- [ ] Four-actor battle footprints and representative target cursor, HP, move list, affinity cue, and shared Resonance meter.
- [ ] One complete ordinary hit VFX and Horizon Break braid core with synchronized original/licensed review audio.
- [ ] Final texture conversion, vertex color, lighting, fog, art-bible display grade, blob shadows, loading transition, dialogue panel, and Field Relay motif.
- [ ] `EXAMPLE_CAM_EXP_01`, `EXAMPLE_CAM_BTL_01`, and `EXAMPLE_SCALE_01` diagnostic relationships are reproduced in clean/overlay capture pairs.

### Evidence manifest

`review/benchmark/PAYLOAD_MANIFEST.sha256` uses the canonical section-16.3 grammar. It covers the first 14 substantive evidence records through non-cyclic members/subordinate manifests. It excludes `docs/VISUAL_BENCHMARK_APPROVAL.md` and `ev.benchmark.approval`; the fifteenth record is a signed annotated origin-tag attestation pointing to the commit containing the populated control and attesting the separate payload commit/digest. The local validator checks the tag's origin presence, object, signature/signer, exact five-line attested text, and target/control; it cannot infer remote-host protection, which the release operator must confirm separately. The tag/control are never members of the payload graph, so no direct or transitive self-hash exists. Path alone is invalid.

The payload also owns exact `WHITELIST_GATE_REGISTRY.tsv`, `BENCHMARK_EVIDENCE_REGISTRY.tsv`, `ROM_BUILD_RECIPE.tsv`, parsed gate records, and every ordinary/LFS member those records bind. Validate Art Bible sections 16.4–16.5: exact headers/row counts/order; one global path/hash/capture owner; 52 subset/build/state/repair/seven-gate bindings; 14 evidence manifests/measurement records/role-count-build-capture sets; and all objective/rubric metric references. A URL/release locator is never review evidence and `PASS` text alone proves nothing.

- [ ] Every objective/rubric reference is sorted canonical `ev.benchmark.<id>#<metric>`, resolves to a parsed measurement row/member, and has a nonempty reviewer observation.
- [ ] Every advanced whitelist ledger row maps one-to-one to `AUTHORIZED`/exact-return `REPAIR_ONLY` and back; all registry paths/hashes/build/status/seven decisions match control and ledger.
- [ ] Derived state and aggregate mask agree exactly: `EMPTY=00000000` has no ordinary concept or advanced row and 52 inactive controls; `PUBLIC_HEAD_CONCEPT=00000000` has at least one ordinary concept, no advanced row, 52 inactive controls, and exact public-ref/fresh-clone authority; `STAGED_WB=11xxxxxx` has the payload/whitelist core plus at least one active row; `APPROVED=11111111` satisfies the full approval graph.
- [ ] Aggregate positions are exactly payload, whitelist, evidence, recipe, player, Quarrune, sector, presentation. Core bits transition together; every optional bit requires core `11`; recipe is optional after core; workflow may remain pending with a recipe but cannot populate without one. Each present rollup digest/build matches its aggregate/global build.
- [ ] Evidence presence means all 52 rows are active, all four rollups are present, all 392 gate decisions are legal completions, and every evidence/row/rollup build equals the global build. Before that claim, each ordinary active staged row still has a canonical individual build but need not equal the global build.
- [ ] Schema-Version 4 repair/block records populate all six prior-approved identity fields; the exact public pinned-key tag/control/payload/registry revalidates, unaffected control/TSV rows are byte-identical, only returned bases are `REPAIR_ONLY`, stable owner/subset paths do not move, and each changed gate has an exact return token. Initial `PENDING`/new `APPROVED` use six `NONE` values.
- [ ] The prior tag is the unique ancestry-maximal pinned-key-valid public approval ancestor of current public HEAD; a newer reachable approval or incomparable maxima fail. Any of the exact eight populated aggregate pairs requires the legal mask/core shape, public payload commit/build identity, fresh clone/LFS retrieval, payload-ledger/tree scan, and one shared commit-bound context; no worktree substitution is accepted.
- [ ] Preapproval current `HEAD` is clean and exactly advertised at `refs/heads/*`, `refs/pull/<positive>/head`, or `refs/pull/<positive>/merge`; an explicit same-ref no-checkout fresh fetch confirms the OID and supplies accepted bytes. Concept roots contain no ignored extra or symlink, and concept evidence owns no authority/receipt/Gate-2+ or output bytes. Postapproval still uses public default `HEAD` only.
- [ ] Staging is a two-commit transaction: payload commit `P` is `Reviewed payload Git commit`; control commit `A` has sole parent `P`; `P→A` changes only `docs/VISUAL_BENCHMARK_APPROVAL.md`; current public `HEAD` descends from `A`; control bytes at `A` equal current; and current `HEAD^{tree}` equals `A^{tree}` (an identical-tree synthetic PR merge is allowed, later byte drift is not).
- [ ] Every regular `assets-src/<production-id-prefix>/<asset_id>/` and `review/<asset_id>/g<gate>/` file has one explicit ledger/manifest owner, with exact prefix/ID correspondence; no alias/orphan/ambiguous/traversal/invalid-case/unauthorized source exists.
- [ ] Pinned ImageMagick `7.1.2-13` decodes all six native/enlarged PNG pairs and proves exact RGBA-pixel 4× point-filter equality; dimensions or the word `nearest-neighbor` alone fail.
- [ ] Pinned `ffprobe 8.1.2` decodes every MP4 as positive-duration H.264 with exact-4:3 positive dimensions and average frame rate at least 30 fps. The representative clip is exact native 320x240, at least 60,000 ms, and contains decodable audio; each VFX/audio sync clip also contains decodable audio. Missing/wrong-version tooling, fake headers, missing audio, low frame rate, or decode failure fail closed once media is populated.
- [ ] Pinned ffmpeg `8.1.2` fully decodes every representative MP4 frame to RGB24. Every `FRAME_AUDIT.tsv` index/start/duration/RGB hash matches the decoded frame, and duration, placeholder/sub-30, performance, five-category working set, warning, and unload/reload claims are recomputed from those rows. `MEASUREMENTS.tsv` value/unit pairs equal the canonical reports exactly.
- [ ] `ARES_RUN.tsv` binds one run ID/build/ROM/Ares-148 binary/revision/Homebrew Mode/three RGBA16 framebuffers/wrapper/invocation/capture/frame-audit/execution-log tuple. The seven wrapper events are exact and monotonic, derive `BOOT_READY` from a child handshake, and end at child/final exit zero. Approval reruns the reviewed wrapper and receives the exact digest-bound JSON receipt; a human operator statement alone is not evidence.
- [ ] Every native PNG report binding names one unique representative-video frame index and RGB SHA-256; full PNG decode equals that frame exactly. Enlarged PNGs are exact 4x nearest-neighbor derivatives. Reports use only pinned `n64game-evidence-analyzer` `1.0.0` at/after the run.
- [x] Gate 3 pins the audited Ares binary to `7a49f00f96a691458461d7c9cf453d95c0f5c054389bbd87c253987b8b6fa345`. The local-only lifecycle semantic snapshot/tamper suite is independently pinned to `a9f2ff50f53f4528c4cfeef1a55f15382ff86f5703b51acf66567af2f57a34b0`, byte-verified, run through `/usr/bin/python3 -I`, and emits exact `NON_APPROVAL_SEMANTIC_SNAPSHOT` authority; it cannot authorize a row or enter benchmark evidence.
- [x] The production-shared lifecycle kernel/harness is committed, pinned, and independently audited. It routes the real public-concept/populated/approved/repair/generated-child/move-pair/H2/release normalized records through one Ruby kernel and byte-binds eight positive paths plus their fail-closed death mutations; its exact receipt declares the GitHub/advertised-ref/tag/LFS/media/Ares/ROM adapters `EXCLUDED_BY_DESIGN`, so those remain mandatory live checks. `PRODUCTION_LIFECYCLE_HARNESS_IMPLEMENTED=true` and the exact manifest digest pinned by the validator satisfy only this prerequisite; they do not make `APPROVED` reachable without the complete real payload, evidence, release, and fresh-build graph.
- [ ] ROM is ignored/untracked and absent from Git/LFS. Local, fresh-public-clone build, successful public workflow run, same-repo release API/download, size/header/SHA, and build ID all match.
- [ ] SSH annotated tag suffix equals payload prefix; public origin object/peeled target equal local; payload is an ancestor and fresh-clone reachable; exact message verifies against the Gate-2-pinned ED25519 public key. Private signing material remains external/uncommitted.

| Exact evidence ID | Required content | Manifest member + SHA-256 | Build/tool version | Reviewer result |
|---|---|---|---|---|
| `ev.benchmark.native` | exact six named raw native members: exploration/dialogue/target_selection/attack_anticipation/impact/support | | | |
| `ev.benchmark.enlarged` | exact same six named unfiltered 4× members | | | |
| `ev.benchmark.turntable.player` | player neutral/game-light sheets and rotations | | | |
| `ev.benchmark.turntable.quarrune` | Quarrune neutral/game-light sheets and rotations | | | |
| `ev.benchmark.animation.player` | locked-camera reel/contact/deformation sheets | | | |
| `ev.benchmark.animation.quarrune` | locked-camera reel/contact/deformation sheets | | | |
| `ev.benchmark.environment.corner` | route/reverse/ceiling/props/collision/camera/grade set | | | |
| `ev.benchmark.ui` | whitelist UI state matrix/native/overscan/contrast gallery | | | |
| `ev.benchmark.vfx_audio` | synchronized ordinary-hit/support/braid records | | | |
| `ev.benchmark.capture_60s` | uninterrupted representative capture | | | |
| `ev.benchmark.performance` | frame/heap/batch/particle/working-set report | | | |
| `ev.benchmark.unload_reload` | exact baseline-return trace | | | |
| `ev.benchmark.gates` | 52 benchmark-scope seven-decision vectors plus player/hero-Quarrune/sector/integrated-presentation rollups; six paired support-model/animation rows remain partial packages | | | |
| `ev.benchmark.authorship` | nine-category rubric/reference calibration | | | |
| `ev.benchmark.approval` | signed non-self-referential origin-tag attestation; tag target contains populated control and message attests separate 40-hex payload commit plus payload-manifest digest; remote protection confirmed separately | external tag ref/signature, not payload member | | |

### Objective approval

| Criterion | Acceptance | Actual/evidence | Pass? |
|---|---|---|---|
| Frame rate | 30 FPS target met in representative views | | |
| Peak free heap | at least 512 KiB | | |
| Native readability | player/route plus Quarrune, Ayselor, Gyreclast, and Kivarrax positions, silhouettes, blob shadows, target, action, result, and UI all clear | | |
| Originality | no recognizable protected design/expression | | |
| Asset completeness | no placeholder/default/incomplete visible face | | |
| Conversion | zero unexplained warnings | | |
| Memory ownership | unload returns to baseline | | |
| Evidence integrity | payload and every child manifest obey canonical grammar, form an acyclic graph, recompute, and exclude control/attestation; all members retrievable | | |
| Provenance/rights | every whitelist production ID complete; no alias ownership/local-only build source | | |
| Open defects | zero critical/high/medium | | |

### Visual-authorship rubric

No score/average is allowed. Every category independently passes with a native/reel evidence hash and concrete reviewer observation; one failed category means `REBUILD` or `REVISE`.

| Category | Automatic failure examples | Evidence hash and reviewer observation | Pass/rebuild |
|---|---|---|---|
| Silhouette/originality | generic/generated identity, color-only distinction, protected similarity | | |
| Environment density/recent activity | empty room, filler scatter, purposeless duplication, incomplete reverse/ceiling | | |
| Topology/material/texture craft | default material, noisy generation, weak form hidden by texture | | |
| Lighting/fog/display grade | flat wash, crushed planes, UI tint, emulator filter dependency | | |
| Animation/deformation/personality | dead pose, slide/clip, stock timing, camera hiding omission | | |
| VFX/audio synchronization | generic effect/cue, hidden result, bad sync, pool/residency leak | | |
| UI/loading presentation | tiny/derivative UI, fake wait, unreadable state, stale/raw frame | | |
| Camera/native readability | unclear route/target/action, tangent silhouettes, unsafe framing | | |
| Cross-discipline cohesion | polished pieces do not read as one authored game | | |

Required sign-off:

- Art reviewer: `distinct non-owner identity / payload-manifest hash / PASS / RFC-3339 date / rationale`
- Technical reviewer: `distinct non-owner identity / same payload-manifest hash / PASS / RFC-3339 date / rationale`
- Gameplay/readability reviewer: `distinct non-owner identity / same payload-manifest hash / PASS / RFC-3339 date / rationale`
- Production decision: exact control fields verify payload commit; ignored/untracked local ROM plus identical fresh/public bytes; parsed whitelist/evidence/gate registries; ordinary/LFS materialization and fresh-clone retrieval; evidence/objective/rubric/reviewer results; `0 / 0 / 0` defects; three distinct non-owner identities; RFC-3339 time; pinned-key SSH origin attestation/object/ancestry/reachability; recorded external tag protection; matching final fields; `Production-Lock: UNLOCKED`; and `Decision: APPROVED`; otherwise remains locked
- If blocked, exact return gate and defect IDs: `__`

## 19. Final production batch audit

Use after individual Gate 7 passes to catch missing coverage and integration drift.

| Inventory group | Expected | Ledger approved | Evidence complete | Placeholder sweep | Native gallery | Final result |
|---|---:|---:|---|---|---|---|
| Runtime humanoids | 9 | | | | | |
| Battle Echoforms | 8 | | | | | |
| Authored environment/world-map source packages | 16; runtime composes 13 traversable/battle `ZoneId` values | | | | | |
| Landmarks | 8 | | | | | |
| Field vehicle assets | 1 hero + 1 map model | | | | | |
| Purposeful props | 63 | | | | | |
| Collision packages | 18 | | | | | |
| Navigation / spawn / interaction indexes | 13 + 13 + 13 | | | | | |
| UI-only end-zone manifest | 1 | | | | | |
| UI/type/icon packages | exactly 37 packages and exactly 37 mapped evidence subjects; controller atlas exactly 12 prompt icons with locked vertical-camera chords | | | | | |
| Regular-move presentation pairs | exactly 32 pair keys = 32 explicit approved `vfx.move.*` + 32 explicit approved suffix-matched `sfx.move.*` production children; pair-atomic Gate 7, separate provenance/gates/evidence, synchronized pair proof | | | | | |
| Common/environment/story VFX | 20 | | | | | |
| Humanoid/Echoform/vehicle-mechanism animation banks | 42 total: 10 + 8 + 24 | | | | | |
| Music cues | 8 | | | | | |
| Ambience / common SFX / Echoform vocal banks | 2 + 6 + 8 banks; story bank 14 events | | | | | |
| Storyboard panels/package | 18 + package | | | | | |
| Generated camera-shot children | 15 `C7` IDs with exact parent/BOM linkage and seven decisions before approval | | | | | |
| Presentation aliases | exactly 8 closed `A0 present.*` aliases; zero ledger/source/output/gates/evidence/bytes/count/dedup ownership; BOM metadata has ordered owners, `payload_bytes=0`, every ownership field `NONE` | | | | | |
| Visual benchmark control/evidence | one valid control record; exactly 52 whitelist production IDs and 15 benchmark evidence IDs before production unlock | | | | | |
| Converted BOM / bundle-size reports | 2 reports | | | | | |

Batch acceptance requires zero missing canonical production ID, every ID assigned exactly one profile/tier, seven valid ordered decisions per production ID, both post-integration passes for every `H2`, zero critical/high/medium defect, complete input/output rights and transformation provenance, recomputable release-candidate evidence manifests, exact pair/UI/alias/child set equality, and no temporary content except canonical polished `ui.screen.cutscene_slate` exposed through non-owning `present.cutscene_slate`.
