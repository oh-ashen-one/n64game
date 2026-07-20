# Runtime candidates

This directory contains materialized inputs used only to prove the real N64 conversion, ROM-filesystem, and renderer path before formal asset promotion. Every binary is hash-locked by `config/runtime-candidates.tsv` and built by the pinned Tiny3D/libdragon tools.

These files are explicitly **not** Gate evidence, approvals, reviewed production source, or final art. They do not change `config/runtime-assets.tsv`, the Gate 5 exporter implementation lock, or any `PENDING` review decision. Every candidate must still pass the required native 320x240 review and remaining art gates; a later authorized promotion must replace this temporary lane with canonical `assets-src/` and reviewed output, then remove the corresponding candidate rows and files.

The current lane contains the Quarrune hero model plus three source textures; one reusable open-top Annex threshold module plus three source textures; Ari's concept-stage hero model plus CI8 body and CI4 face sources; and battle-distance candidates for Ayselor, Gyreclast, and Kivarrax with one body, accent, and blob-shadow source apiece. Ari's single GLB includes only the exact native-iteration clips `idle_a`, `walk`, and `run`; the Tiny3D converter emits their three `.sdata` streams beside the model. This is a deliberately reduced movement proof, not the final hero/distance mesh pair or the retained animation package.

The three supporting Echoform candidates retain only the benchmark subset `idle_a`, `reposition`, and `hit`. Their source-package budgets are locked here so accidental placeholder regressions fail before conversion:

| Candidate | Triangles | Ceiling | Materials | Joints | Retained clips |
| --- | ---: | ---: | ---: | ---: | --- |
| Ayselor distance | 382 | 600 | 3 | 18 | `idle_a`, `reposition`, `hit` |
| Gyreclast distance | 620 | 620 | 3 | 18 | `idle_a`, `reposition`, `hit` |
| Kivarrax distance | 528 | 540 | 3 | 20 | `idle_a`, `reposition`, `hit` |

Each supporting GLB uses exactly one weighted joint per exported vertex, two 64x32 dynamic body regions, and one direct 32x32 accent path. Each package also carries one 64x64 body source and one 32x32 blob-shadow source. These structural facts make the candidates usable for runtime integration; they are not aesthetic acceptance or production promotion.

The renderer places one Annex module at the active retained sector anchor, plus one battle backdrop, to test composition, scale, material readability, animation, and cost before promotion without drawing four full rooms per frame. Ari and the supporting Echoforms prove the real skinned-model and dynamic-texture paths only. Their inclusion does not authorize a workbook row, satisfy G1 or G5, establish final provenance, or represent art approval.
