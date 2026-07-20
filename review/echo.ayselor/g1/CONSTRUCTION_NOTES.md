# Ayselor Gate-1 construction notes

Status: `IN_PROGRESS`. This packet adds measurable construction evidence; it does not approve Gate 1 or authorize a production mesh.

## Identity and ownership

- Production ID: `echo.ayselor`; role: persistent Gale starter and fast support carrier.
- Creator: `openai.codex-n64game`; rights holder: `oh-ashen-one.project`; selected generated source, prompt/job metadata, transformations, provider terms, and hashes are bound by the source manifest and provenance record.
- Inventory dependency: paired animation owner `anm.echo.ayselor`; benchmark basis `WB-047` remains inactive.

## Scale and quantitative plan

- Locked size: 1.90 m wingspan, 1.20 m body/keel length, 1.15 m hover center.
- `SCALE_LINEUP.png` uses a 0.50 m grid. Left to right: 2.30 m standard door, 1.72 m Ari marker, hovering Ayselor. Blue bars mark 1.90 m wingspan and 1.15 m hover center; the gray ellipse is its required ground shadow.
- Geometry: 1,150-triangle hero target, 600-triangle benchmark distance target; three materials.
- Texture plan: one 64x64 CI8 cloth/ceramic atlas, one 32x32 CI4 spar/lamp accent atlas, and one 32x32 IA8 blob-shadow mask.
- Rig plan: 18 joints: root, keel, three four-joint wing chains, two lamp-chain joints, and two stabilizer/deformation joints.
- Required benchmark paired-bank coverage: `idle_a`, `reposition`, and `hit`; full release bank remains 15 clips.
- Minimum intended battle read: 35 pixels tall; long leading wing, two counter-wings, keel, lamp, and facing must remain distinct.

## Construction and motion

- Front/action direction is defined by the one long leading wing and narrow keel, never by eyes or an animal head.
- Exactly three wing planes articulate around visible oxidized-brass spars. Clothlike ceramic membranes bend at rigged spars rather than stretching as rubber.
- Primary VFX origins: leading-wing tip for Sirocco Slice, lamp for Dazzle Wake, keel center for Lift Current, and ally-facing trailing spar for Guiding Draft.
- Collision is a narrow keel capsule plus nonblocking wing clearance; hover shadow proves altitude and target lane.
- Material callouts use Sun chalk `#D8C9A7`, Bleached bone `#BDAF91`, Teal iron `#204F53`, Cobalt shade `#273A68`, Ink brown `#241E20`, and Worklight amber `#F0B85A` for the single keel lamp.

## Silhouette and clean-room review preparation

- `SILHOUETTE_64.png` is the exact black 64x64 reduction derived from the selected sheet.
- `SILHOUETTE_COMPARISON.png` order is Quarrune, Ayselor, Gyreclast, Kivarrax; the cobalt frame marks Ayselor. Its extremely wide tri-wing span and dangling lamp do not overlap the grounded peers.
- Similarity risk: aircraft, manta, bird, or ordinary kite. Required differentiators are one asymmetrical leading wing, two counter-wings, a faceless narrow keel, tension-spar construction, and one hanging lamp.
- Protected references were used only for high-level pacing and technical presentation study. No protected creature silhouette, vehicle, logo, surface motif, model, texture, or layout is a source input.

## Open before Gate 1

- Add and inspect a functional three-quarter view with the same wing count and spar placement.
- Resolve membrane underside, fold limits, and lamp-chain clearance.
- Confirm the wide silhouette and shadow remain readable in the representative battle lane.
- Obtain independent non-owner H2 Gate-1 review; the creator cannot approve this gate.
