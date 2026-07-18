# Third-Party Notices

This project is designed to use the following external tools and libraries. Each component remains subject to its own license. Exact pinned revisions are recorded in the master specification and will be mirrored in the build lock/configuration once integration begins.

## Runtime and build dependencies

### libdragon

- Project: https://github.com/DragonMinded/libdragon
- Planned branch: `preview`
- License: The Unlicense
- Status: planned Gate 3 dependency; not vendored in this repository at Gate 2

### Tiny3D

- Project: https://github.com/HailToDodongo/tiny3d
- License: MIT
- Copyright: Max Bebök and contributors
- Status: planned Gate 3 dependency; not vendored in this repository at Gate 2

Tiny3D itself identifies additional third-party components used by its tooling, including cgltf (MIT), meshoptimizer (MIT), bvh (MIT), and TriStripper (zlib). Their notices must be preserved when those tools are integrated or redistributed.

## Gate 2 validation tooling

### Ruby

- Project: https://www.ruby-lang.org/
- Gate 2 host version: Apple system Ruby 2.6.10p210, revision 67958 (`/usr/bin/ruby`)
- License: Ruby License or 2-clause BSD; the Apple-provided distribution remains subject to its accompanying Apple notices
- Use: external host interpreter for the Gate 2 validation scripts; Ruby is not linked into the game ROM or redistributed by this repository

### Apple Clang C compiler

- Project/distribution: Apple Xcode
- Gate 2 host version: Apple Clang 21.0.0 (`clang-2100.1.1.101`) via `/usr/bin/cc`; Xcode 26.6, build `17F113`
- License/notices: the installed Xcode toolchain and SDK remain subject to Apple's distribution terms and their accompanying component notices; those exact notices must be preserved if a toolchain is ever redistributed
- Use: external host compiler for the generated C aggregate validation; the compiler and SDK are not linked into the game ROM or redistributed by this repository

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
- License/notices: unresolved at Gate 2 because no Ares installation, source checkout, or authoritative local distribution notice is present
- Use: external emulator and initial certification target
- Gate 3 blocker: before Ares is accepted for certification or redistributed, record the exact download/source provenance and verify the license and notices supplied by that exact version; no Ares code or binary may enter this repository until that evidence exists

### FFmpeg / ffprobe

- Project: https://ffmpeg.org/
- Pinned evidence-validator version: 8.1.2
- License for the currently selected Homebrew package: GPL-3.0-or-later; FFmpeg licensing is configuration-dependent and must be re-audited if the packaged build changes
- Use: external command-line validation of H.264 review-capture structure, dimensions, and duration; it is not linked into the game ROM

### ImageMagick

- Project: https://imagemagick.org/
- Pinned evidence-validator version: 7.1.2-13
- License: ImageMagick License
- Use: external decoded-pixel comparison proving that enlarged review captures are exact 4x nearest-neighbor versions of their 320x240 sources; it is not linked into the game ROM

## Reference-only projects

Pandemonium and Pokémon XD: Gale of Darkness are reference material only. No code or assets from either project are licensed for inclusion through this notice, and none may be copied into `n64game` without a separately verified legal basis.

This file must be updated whenever a dependency, font, sample, model source, texture source, audio source, or other third-party component enters the project. The asset ledger is the source of truth for individual non-code assets.
