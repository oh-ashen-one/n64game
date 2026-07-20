# Kivarrax Gate-1 construction notes

Status: `IN_PROGRESS`. This packet adds measurable construction evidence; it does not approve Gate 1 or authorize a production mesh.

## Identity and ownership

- Production ID: `echo.kivarrax`; role: Gale simulation opponent, speed manipulation and sweeping pressure.
- Creator: `openai.codex-n64game`; rights holder: `oh-ashen-one.project`; selected generated source, prompt/job metadata, transformations, provider terms, and hashes are bound by the source manifest and provenance record.
- Inventory dependency: paired animation owner `anm.echo.kivarrax`; benchmark basis `WB-051` remains inactive.

## Scale and quantitative plan

- Locked size: 1.35 m shoulder and 2.00 m nose-to-fan length; it is the longest vertical battle silhouette.
- `SCALE_LINEUP.png` uses a 0.50 m grid. Left to right: 2.30 m standard door, 1.72 m Ari marker, Kivarrax. Blue bars mark 2.00 m nose-to-fan construction length and the 1.35 m shoulder reference; the fan extends above the shoulder.
- Geometry: 1,050-triangle hero target, 540-triangle benchmark distance target; three materials.
- Texture plan: one 64x64 CI8 torso/leg atlas, one 32x32 CI4 fan/scoop accent atlas, and one 32x32 IA8 blob-shadow mask.
- Rig plan: 20 joints: root and torso, four upper/lower/foot leg chains, two rearward-vane joints, and fan base plus three independently keyed panel joints.
- Required benchmark paired-bank coverage: `idle_a`, `reposition`, and `hit`; full release bank remains 11 clips.
- Minimum intended battle read: 35 pixels tall; alternating leg gaps, scoop opening, rearward vane, and one fan wedge must remain separate.

## Construction and motion

- Front/action direction is the hollow pressure-scoop chest; the rearward vane is a faceless aerodynamic sensor, not an animal head.
- Long legs cycle in alternating diagonals with a low torso glide. Fan panels open for braking/support and close into one wedge for acceleration.
- Primary VFX origins: scoop mouth for Pressure Drop, leading feet for Crosswind Cut/Talon Sweep, torso wake sockets for Slipstream, and fan edges for recovery trails.
- Collision uses a narrow torso capsule and conservative planted-foot hull; the fan and vane are nonblocking presentation surfaces.
- Material callouts use Sun chalk `#D8C9A7`, Bleached bone `#BDAF91`, Teal iron `#204F53`, Cobalt shade `#273A68`, Ink brown `#241E20`, and a restrained Worklight amber `#F0B85A` status point.

## Silhouette and clean-room review preparation

- `SILHOUETTE_64.png` is the exact black 64x64 reduction derived from the selected sheet.
- `SILHOUETTE_COMPARISON.png` order is Quarrune, Ayselor, Gyreclast, Kivarrax; the cobalt frame marks Kivarrax. Its four long stilt gaps and vertical fan wedge remain distinct from every retained peer.
- Similarity risk: deer, horse, spider, or tall robot. Required differentiators are no animal face, no hooves, a forward pressure scoop, a rearward vane sensor, four aerodynamic stilt legs, and one three-panel folding fan.
- Protected references were used only for high-level pacing and technical presentation study. No protected creature, vehicle, logo, surface motif, model, texture, or layout is a source input.

## Open before Gate 1

- Add and inspect a functional three-quarter view with exact leg, scoop, vane, and fan continuity.
- Resolve fan-fold range, underside torso construction, foot contact area, and self-collision at full stride.
- Confirm the tall silhouette clears battle UI and neighboring actors during target selection.
- Obtain independent non-owner H2 Gate-1 review; the creator cannot approve this gate.
