# Gate 3 Toolchain and Reproducible ROM Build

This document describes the implemented Gate 3 build contract. The current ROM is a small original Tiny3D diagnostic scene used to prove exact dependency compatibility and to produce the candidate for a separate Ares boot review. It is not the complete game opening, a vertical slice, or a claim that later production gates are finished.

## Exact dependency authority

`config/toolchain.lock.json` is the machine-readable lock. The two source dependencies are public Git submodules whose gitlinks must exactly match that file:

- libdragon preview `f13b48985edbf4310f07779c76d9a68c7605037b`
- Tiny3D `e84172f29f719680ac3213a7f408c2f721ef7b24`
- libdragon CLI 12.2.1 with npm integrity locked by `package-lock.json`
- libdragon OCI index `sha256:36a295cbe43168e8adbfa5c86d956df3dc762a1ab6fda1b50dcb33bd78dc2d83`
- Ares v148 executable `7a49f00f96a691458461d7c9cf453d95c0f5c054389bbd87c253987b8b6fa345`

Do not run `libdragon update`, float a submodule branch, substitute `latest`, or replace the OCI digest with a tag. `scripts/verify-toolchain-pins` rejects index/worktree/package/config drift before a build.

## Fresh checkout

```sh
git clone --recurse-submodules https://github.com/oh-ashen-one/n64game.git
cd n64game
git lfs install
git lfs pull
npm ci --ignore-scripts
scripts/bootstrap-check --all
```

The bootstrap check is observational: it reports architecture, free disk, LFS, Node/npm/CLI, Docker client and engine, local image state, Ares, and Blender without changing repository files. `--build` requires the local build stack; `--ci` omits GUI tools; `--all` also requires the exact Ares executable.

## Stable entry points

```sh
make validate  # pins, data/contracts, asset lock, public hygiene
make assets    # asset-production contract plus Gate 3 empty runtime manifest
make rom       # clean immutable-container build
make test      # deterministic host build-contract tests
make report    # ROM checksum, header/size, map, dependency and validation reports
make clean     # remove ignored build/ plus the one transient root ROM staging path
```

`scripts/build-rom` starts by deleting only the resolved repository `build/` path and the exact transient root-level `n64game-gate3.z64` staging path used by libdragon's upstream make rule. It exports each pinned submodule through `git archive` into `build/deps/`, so generated headers and dependency objects never dirty the public gitlinks. CLI 12.2.1 creates or starts the digest-addressed container; the wrapper then verifies its running state, exact image identity, and one expected read-write project mount before invoking the audited project build with Docker. Direct `libdragon exec` is intentionally avoided because its fresh-container recovery path silently runs the vendor's broader `build.sh` before the requested command. The audited container entrypoint installs the pinned libdragon library/tools, builds Tiny3D locally, and compiles the project with warnings as errors.

Project code enables `-Wshadow` and `-Wconversion` as errors in addition to the pinned toolchain defaults. One known conversion warning inside Tiny3D's inline `t3d_mat4fp_set_float` mask is suppressed only while parsing the pinned upstream header; strict conversion diagnostics resume before any project declaration or function body.

The selected OCI image currently publishes Linux AMD64 plus provenance, not an ARM64 runtime. The wrapper sets `DOCKER_DEFAULT_PLATFORM=linux/amd64`; Apple Silicon therefore requires Docker's x86 emulation. CI runs the same image natively on an AMD64 runner.

## Outputs

All generated files remain below ignored `build/`:

- `build/game/n64game-gate3.z64`
- `build/game/n64game-gate3.z64.sha256`
- `build/game/n64game-gate3.map`
- `build/game/n64game-gate3.elf.size.txt`
- `build/reports/dependency-build-manifest.json`
- `build/reports/rom-size.md`
- `build/reports/validation-summary.md`
- `build/reports/host-tests.txt`

The ROM validator requires canonical big-endian N64 magic, the exact Gate 3 diagnostic title, a standard-4-MB-aligned entrypoint, EEPROM4K/region-free/controller advanced-header declarations, the exact pinned libdragon IPL3 payload, deterministic TOC placement, a 256-byte-aligned big-endian MIPS ELF, 16 KiB ROM alignment, and size below the locked 16 MiB target. Libdragon's open IPL3 intentionally does not use the commercial-ROM checksum words, so the validator requires those words to remain zero exactly as emitted by the pinned tool instead of falsely claiming a legacy checksum. These structural checks do not prove that the ROM booted; Ares evidence is separate.

## Ares v148 launch

The versioned macOS installation is expected by default at:

```text
$HOME/Applications/Emulators/ares-v148/ares.app/Contents/MacOS/ares
```

Override it only with `N64GAME_ARES_BINARY`. Launch through the wrapper:

```sh
scripts/run-ares \
  --homebrew-mode \
  --expected-rom-sha256="$(shasum -a 256 build/game/n64game-gate3.z64 | awk '{print $1}')" \
  build/game/n64game-gate3.z64
```

The wrapper verifies both executable and ROM hashes, forces `General/HomebrewMode=true`, forces `Nintendo64/ExpansionPak=false`, and uses isolated versioned settings/save/screenshot/debug paths. Those overrides are mandatory because Ares v148 defaults Homebrew Mode off and Expansion Pak on. `--check-only` verifies the complete tuple without launching the GUI.

## Public CI

`.github/workflows/build-rom.yml` uses an explicit Ubuntu 24.04 runner, commit-pinned GitHub Actions, Node 24.18.0, recursive submodules, Git LFS, non-persisted checkout credentials, the same stable entry points, a clean-source diff check, and an artifact upload containing the ROM, checksum, linker map, ELF size output, dependency manifest, host-test report, and validation summary. Report generation fails closed if the map, ELF size output, or exact host-test PASS contract is missing. A successful workflow proves a fresh public build candidate; it still does not replace the local Ares boot inspection and is never labeled a boot proof by CI alone.

## Known upstream test boundary

The official workflow for libdragon `f13b48985edbf4310f07779c76d9a68c7605037b` successfully built its container, library, and tools but its full upstream `./build.sh --test` run failed in an `mkmaterial` fixture assertion. Gate 3 therefore runs the exact project-relevant library/tool/Tiny3D/ROM build and discloses the upstream red suite instead of claiming it passed. If the pinned project build itself fails, the incompatibility must be recorded and an explicit mutually compatible commit selected under the master specification; it may not be hidden by a floating update.
