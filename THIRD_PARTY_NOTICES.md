# Third-Party Notices

This project uses the following external tools and libraries. Each component remains subject to its own license. Exact revisions, archive hashes, container digests, and tool versions are recorded in `config/toolchain.lock.json`. Dependency source is fetched through pinned public Git submodules; compiler, CLI, emulator, and authoring-tool binaries are not committed to this repository.

## Runtime and build dependencies

### libdragon

- Project: https://github.com/DragonMinded/libdragon
- Pinned branch/commit: `preview` at `f13b48985edbf4310f07779c76d9a68c7605037b`
- License: The Unlicense
- Status: pinned public Git submodule at `vendor/libdragon`; compiled from an archive of the exact gitlink inside ignored `build/`

### Tiny3D

- Project: https://github.com/HailToDodongo/tiny3d
- Pinned commit: `e84172f29f719680ac3213a7f408c2f721ef7b24`
- License: MIT
- Copyright: Max Bebök and contributors
- Status: pinned public Git submodule at `vendor/tiny3d`; compiled from an archive of the exact gitlink inside ignored `build/`

Tiny3D identifies or embeds tooling components including cgltf (MIT), meshoptimizer (MIT), bvh (MIT), TriStripper (zlib), lodepng (zlib), and nlohmann/json (MIT, with separately attributed Apache-2.0 utility fragments). Their upstream notices remain in the pinned source and must be preserved if the converter or a source/tool bundle is redistributed.

### libdragon CLI and build container

- CLI project: https://github.com/anacierdem/libdragon-docker
- Pinned CLI: npm `libdragon` 12.2.1, repository commit `f8a16abc81263781cf684602bcea98a1d096fd2d`
- CLI license: MIT
- Container: `ghcr.io/dragonminded/libdragon@sha256:36a295cbe43168e8adbfa5c86d956df3dc762a1ab6fda1b50dcb33bd78dc2d83`
- Container platform: Linux AMD64; compiler/toolchain includes GCC 14.4.0, binutils 2.44, newlib 4.4.0.20231231, and GDB 16.2 under their respective upstream licenses
- Use: external reproducible build environment; neither the CLI package, container image, nor compiler toolchain is redistributed with the ROM artifact

The container's published provenance binds it to the pinned libdragon commit. Apple Silicon local builds use Docker's AMD64 emulation because this exact OCI index has no ARM64 runtime manifest.

The locked CLI package graph also contains the following host-only npm dependencies: `ansi-styles`, `array-back`, `chalk`, `color-convert`, `color-name`, `command-line-usage`, `deep-extend`, `escape-string-regexp`, `has-flag`, `reduce-flatten`, `supports-color`, `table-layout`, `typical`, and `wordwrapjs` under MIT licenses, plus `zx` under Apache-2.0. Exact versions and registry integrity hashes are retained in `package-lock.json`; the packages are not bundled into the ROM or CI artifact.

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

The observed host installation is Blender 5.2.0 LTS. Production authoring remains pinned to Blender 4.5.11 LTS because the selected Fast64 release does not declare compatibility with 5.2.0; the observed newer installation is not silently treated as the production exporter.

### Fast64

- Project: https://github.com/Fast-64/fast64
- Planned version: 2.5.3, commit `8e9630c11824a9c00e9379279d43c64264eda87e`
- License: GNU GPLv3
- Use: Blender export workflow

Fast64 is an external authoring tool. Its source will not be copied into or linked with the MIT-licensed game code. Preserve its notices if it is ever redistributed.

### Ares

- Project: https://github.com/ares-emulator/ares
- Pinned version: v148, tag commit `0aafd85789215e84e1e43415c07d4c88461b7899`
- Official macOS archive: `ares-macos-universal.zip`, SHA-256 `1ae232ab6de341210f171f51d84b311527eb1399060706589334a8a7de136bb0`
- Pinned universal macOS executable SHA-256: `7a49f00f96a691458461d7c9cf453d95c0f5c054389bbd87c253987b8b6fa345`
- Main license: ISC-style Ares license; official v148 source `LICENSE` SHA-256 `a1053dec5f15ee7c851abf7716634344b9d5740b414bf5893802f9910fdc7a97`
- Bundled notices: the official source license consolidates Ares and third-party notices; the binary archive also carries shader/component licenses including MIT, zlib, LGPL-3.0, GPL-2.0, and GPL-3.0 material
- Use: external emulator and initial certification target
- Verification: official archive digest matched GitHub; app and native frameworks are universal ARM64/x86_64; deep code-signature, notarization, stapled-ticket, and Apple distribution-policy checks passed

The Ares binary is installed outside the repository and is not redistributed with project artifacts. Anyone redistributing Ares itself must include the complete applicable upstream license/notices. The v148 binary ZIP omits the consolidated root source `LICENSE`, so copying that ZIP onward without a separate notice review is not authorized by this project.

### Docker Desktop

- Project: https://www.docker.com/products/docker-desktop/
- Gate 3 observed install: 4.82.0 build 233772
- Use: external macOS container engine for the pinned libdragon build image
- Distribution: Docker Desktop is not committed or redistributed by this project and remains subject to Docker's own subscription/service terms

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
