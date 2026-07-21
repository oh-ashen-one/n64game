# Runtime candidates

This directory contains materialized inputs used only to prove the real N64 conversion, ROM-filesystem, and renderer path before formal asset promotion. Every binary is hash-locked by `config/runtime-candidates.tsv`; generated sprite containers use the pinned libdragon toolchain.

These files are explicitly **not** Gate evidence, approved production source, or final art. They do not change `config/runtime-assets.tsv`, the Gate 5 exporter implementation lock, or any `PENDING` review decision. Every candidate must still pass the in-engine 320x240 review and the remaining art gates; a later authorized promotion must replace this temporary lane with canonical `assets-src/` and reviewed output, then remove the corresponding candidate rows and files.

The 28-row lane contains the Annex module, Ari, and all four retained battle Echoforms. Quarrune and Ayselor include provenance GLBs plus exact reviewed-host Tiny3D models and three animation streams apiece; the ROM build copies and verifies those package bytes instead of silently replacing them with platform-divergent reconversions. Gyreclast and Kivarrax remain deterministic source-converted candidates. The Annex module is deliberately instanced as a sector-aware environment proof; it is not a claim that all four Annex sectors have final, unique art.
