# Third-Party Notices

This project is designed to use the following external tools and libraries. Each component remains subject to its own license. Exact pinned revisions are recorded in the master specification and will be mirrored in the build lock/configuration once integration begins.

## Runtime and build dependencies

### libdragon

- Project: https://github.com/DragonMinded/libdragon
- Planned branch: `preview`
- License: The Unlicense
- Status: planned dependency; not vendored in this repository at Gate 1

### Tiny3D

- Project: https://github.com/HailToDodongo/tiny3d
- License: MIT
- Copyright: Max Bebök and contributors
- Status: planned dependency; not vendored in this repository at Gate 1

Tiny3D itself identifies additional third-party components used by its tooling, including cgltf (MIT), meshoptimizer (MIT), bvh (MIT), and TriStripper (zlib). Their notices must be preserved when those tools are integrated or redistributed.

## Content-production tools

### Blender

- Project: https://www.blender.org/
- License: GNU GPL
- Use: external content-production tool; Blender is not linked into the game ROM

### Fast64

- Project: https://github.com/Fast-64/fast64
- Planned version: 2.5.3, commit `8e9630c11824a9c00e9379279d43c64264eda87e`
- License: GNU GPLv3
- Use: Blender export workflow

Fast64 is an external authoring tool. Its source will not be copied into or linked with the MIT-licensed game code. Preserve its notices if it is ever redistributed.

### Ares

- Project: https://ares-emu.net/
- Planned version: 148, tag commit `0aafd85789215e84e1e43415c07d4c88461b7899`
- License/notices: verify against the installed distribution before redistribution
- Use: external emulator and initial certification target

## Reference-only projects

Pandemonium and Pokémon XD: Gale of Darkness are reference material only. No code or assets from either project are licensed for inclusion through this notice, and none may be copied into `n64game` without a separately verified legal basis.

This file must be updated whenever a dependency, font, sample, model source, texture source, audio source, or other third-party component enters the project. The asset ledger is the source of truth for individual non-code assets.
