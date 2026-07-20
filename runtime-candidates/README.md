# Runtime candidates

This directory contains materialized inputs used only to prove the real N64 conversion, ROM-filesystem, and renderer path before formal asset promotion. Every binary is hash-locked by `config/runtime-candidates.tsv` and built by the pinned Tiny3D/libdragon tools.

These files are explicitly **not** Gate evidence, reviewed production source, or final art. They do not change `config/runtime-assets.tsv`, the Gate 5 exporter implementation lock, or any `PENDING` review decision. The Quarrune and Annex candidates must still pass the in-engine 320x240 review and the remaining art gates; a later authorized promotion must replace this temporary lane with canonical `assets-src/` and reviewed output, then remove the corresponding candidate rows and files.

The current lane contains the Quarrune hero model with its three source textures and one authored Annex threshold/atrium module with three source textures. The Annex module is deliberately instanced as a sector-aware environment proof; it is not a claim that all four Annex sectors have final, unique art. Quarrune distance and animation packages remain out of the ROM until the static integration is visually proven.
