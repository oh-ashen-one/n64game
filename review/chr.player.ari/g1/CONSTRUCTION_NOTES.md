# Ari Gate-1 construction notes

Status: `IN_PROGRESS`. This package replaces no runtime asset and approves no production mesh. It establishes the construction target that the existing disposable runtime candidate does not yet meet.

## Identity and ownership

- Production ID: `chr.player.ari`; role: nameable player avatar and Field Relay operator.
- Creator: `openai.codex-n64game`; rights holder: `oh-ashen-one.project`; both selected generated sources, their complete prompts, tool/job metadata, transformations, provider terms, and hashes are bound by the source manifest and provenance record.
- Benchmark basis `WB-001` remains inactive. No Gate pass, authorization, converted output, or runtime-quality claim is made.

## Locked construction

- Scale: 1.72 m total height, 1.58 m eye line, approximately 6.5 heads, roughly 0.45 m shoulder width, and approximately 0.28 m boot length.
- Silhouette phrase: forward-leaning wedge with cropped jacket, open forearm gaps, split field overskirt, compact Relay harness, and practical square-toe boots.
- Identity locks: short faceted dark fringe, compact low ponytail with cyan tie, warm-brown skin, angular brow/nose/cheek/jaw planes, field-navy cropped jacket, sand underlayer, asymmetric split overskirt, crossed brown harness, cyan sternum Relay, and left-hip pouch.
- Palette anchors: field navy `#314866`, fabric sand `#A98E6C`, Relay cyan `#5FC7C8`, worn leather brown, dark hair, and an individually authored warm skin ramp. These are material/value blocks, not a substitute for modeled facial and clothing form.

## Modeling and rig plan

- Geometry target: 1,400-triangle hero and 700-triangle distance model, three materials, with triangles prioritized for face direction, collar/jacket silhouette, hands, knees, ponytail, split overskirt, and boots.
- Texture target: one 64x64 CI8 body/clothing atlas, one 32x32 CI4 face atlas, and one 32x32 IA8 blob-shadow mask. Avoid texture-only jacket thickness, fingers, brow, nose, pouch flap, or Relay housing.
- Rig target: 24 deformation joints covering root/pelvis/spine/chest/head, clavicle-arm-hand chains, leg-foot chains, and ponytail; rigid pouch and Relay attachments use named sockets unless stress tests prove an additional joint necessary.
- Required release coverage: shared exploration idle, walk, run, interaction, and one dialogue gesture; player-specific battle command and dialogue nod remain separately owned by their animation packages.
- Collision remains separate from render topology. The pouch, jacket collar, overskirt panels, ponytail, and Relay never enlarge the player capsule.

## Evidence reading

- `CONCEPT_RENDER.png` binds front, left, rear, and right orthographic views at a shared ground line plus a three-view head row.
- `FUNCTIONAL_THREE_QUARTER.png` shows the same identity in a Field Relay interaction: planted weight shift, open left hand, right-hand Relay stabilization, directed gaze, separated feet, and three construction insets for hand/forearm, harness/Relay, and boot/ankle mechanics.
- `SCALE_LINEUP.png` uses 0.50 m horizontal intervals. Left to right: 2.30 m x 1.20 m standard door, Ari at 1.72 m, and current Quarrune concept at 0.95 m shoulder height; cyan brackets mark the two subject heights.
- `SILHOUETTE_64.png` is a deterministic black reduction of Ari's front orthographic. `SILHOUETTE_COMPARISON.png` places Ari first, framed in Relay cyan, against schematic art-bible peers: Tavi's short scarf triangle, Venn's tall sash column, and Oren's broad mantle/low-center block. The peer schematics are comparison guides, not approved character concepts.

## Clean-room and quality findings

- Protected references inform only high-level late-console pacing and presentation study. No protected character, costume, logo, icon, surface motif, mesh, texture, or layout is a source input.
- Similarity risks are generic anime adventurer, modern streetwear hero, and familiar monster-battler protagonist. Required differentiators are the compact functional Relay harness, open forearm silhouette, asymmetric field overskirt, forward working posture, restrained desert-research palette, and no cap, capture device, school uniform, or branded insignia.
- The current unapproved runtime candidate is not a production source and is not covered by this evidence. Its block anatomy, face, hands, jacket thickness, harness construction, and silhouette do not yet reproduce this package; Gate 2 must begin from a deliberate rebuild or a demonstrably equivalent repaired source.

## Open before Gate 1

- Confirm front/profile/rear garment overlap and harness continuity at exact model scale.
- Confirm the hand, Relay, pouch, ponytail, and split-overskirt sockets can be modeled without inventing identity-critical structure.
- Freeze skin, face, leather, navy, sand, and cyan ramps after a native 320x240 readability proof.
- Obtain independent non-owner H2 Gate-1 review; the creator cannot approve this gate.
