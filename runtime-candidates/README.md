# Runtime candidates

This directory contains materialized inputs used only to prove the real N64 conversion, ROM-filesystem, and renderer path before formal asset promotion. Every binary is hash-locked by `config/runtime-candidates.tsv` and built by the pinned Tiny3D/libdragon tools.

These files are explicitly **not** Gate evidence, reviewed production source, or final art. They do not change `config/runtime-assets.tsv`, the Gate 5 exporter implementation lock, or any `PENDING` review decision. The Quarrune, Annex, and Ari candidates must still pass the in-engine 320x240 review and the remaining art gates; a later authorized promotion must replace this temporary lane with canonical `assets-src/` and reviewed output, then remove the corresponding candidate rows and files.

The current lane contains the Quarrune hero model plus three source textures; one reusable open-top Annex threshold module plus three source textures; and Ari's concept-stage hero model plus CI8 body and CI4 face sources. Ari's single GLB includes only the exact native-iteration clips `idle_a`, `walk`, and `run`; the Tiny3D converter emits their three `.sdata` streams beside the model. This is a deliberately reduced movement proof, not the final hero/distance mesh pair or the retained animation package.

The renderer places one Annex module at the active retained sector anchor, plus one battle backdrop, to test composition, scale, material readability, animation, and cost before promotion without drawing four full rooms per frame. Ari's inclusion proves the real skinned-model and dynamic-texture path only. It does not authorize WB-001, satisfy G1 or G5, establish final provenance, or represent art approval.
