# Gate 3 Build Toolchain and Gate 4 Authoring Stack

This document describes the implemented Gate 3 build contract. The current ROM is a small original Tiny3D diagnostic scene used to prove exact dependency compatibility. Its clean public-CI bytes have completed a separate Ares boot review recorded in [GATE3_BOOT_EVIDENCE.md](GATE3_BOOT_EVIDENCE.md); the CI manifest correctly remains `ares_boot=NOT_RUN` because CI itself did not perform that GUI review. This ROM is not the complete game opening, a vertical slice, or a claim that later production gates are finished.

## Exact dependency authority

`config/toolchain.lock.json` is the machine-readable lock. The two source dependencies are public Git submodules whose gitlinks must exactly match that file:

- libdragon preview `f13b48985edbf4310f07779c76d9a68c7605037b`
- Tiny3D `e84172f29f719680ac3213a7f408c2f721ef7b24`
- libdragon CLI 12.2.1 with npm integrity locked by `package-lock.json`
- libdragon OCI index `sha256:36a295cbe43168e8adbfa5c86d956df3dc762a1ab6fda1b50dcb33bd78dc2d83`
- Ares v148 executable `7a49f00f96a691458461d7c9cf453d95c0f5c054389bbd87c253987b8b6fa345`
- official Blender 4.5.11 LTS macOS ARM64 DMG, 308255028 bytes, SHA-256 `1fad76c7da9451c7d6db99f1a5ed3c0a1a461d0aa07bf2b639e2fb4804ca4f13`
- Fast64 v2.5.3 release ZIP, commit `8e9630c11824a9c00e9379279d43c64264eda87e`, 1882004 bytes, SHA-256 `2a308e04ee591e328856e8dff5bbe5aa72f284873e874ba5aba5927831889010`

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

The Gate 3 bootstrap check is observational: it reports architecture, free disk, LFS, Node/npm/CLI, Docker client and engine, local image state, Ares, and any Blender found on `PATH` without changing repository files. `--build` requires the local build stack; `--ci` omits GUI tools; `--all` also requires the exact Ares executable. Blender/Fast64 authoring acceptance is a stricter, separate Gate 4 check described below.

## Stable entry points

```sh
make validate  # pins, data/contracts, asset lock, public hygiene
make assets    # asset-production contract plus Gate 3 empty runtime manifest
make rom       # clean immutable-container build
make test      # Gate 3 build tests plus Gate 4 semantic and shared-kernel lifecycle branch/death tests; not approval evidence
make authoring-check # exact installed Blender/Fast64 check; macOS authoring host only
make test-authoring  # portable unit/tamper tests for the authoring checker
make report    # ROM checksum, header/size, map, dependency and validation reports
make clean     # remove ignored build/ plus the one transient root ROM staging path
```

The production lifecycle is split at an explicit normalized-record boundary. `lib/n64game/asset_lifecycle_contract.rb` is the pure Ruby kernel called by the live public-concept, populated, approved, repair, generated-child, move-pair, H2, and release validator paths; `scripts/test-asset-lifecycle-production` runs those eight entrypoints plus their fail-closed death mutations from the byte-bound manifest under `test/fixtures/asset_lifecycle_production/`. Its receipt says `live_adapter_coverage=EXCLUDED_BY_DESIGN`: public GitHub/API state, advertised-ref freshness, signed tags, LFS materialization, media decode, Ares execution, and ROM rebuild remain mandatory live-validator adapters and are never synthesized by the runner. Independent audit accepted the boundary, exact callsite coupling, controlled malformed-input behavior, profile/gate semantics, and fresh-clone execution. `PRODUCTION_LIFECYCLE_HARNESS_IMPLEMENTED=true` binds the exact manifest SHA-256 pinned by the validator; this satisfies only the lifecycle-harness prerequisite and does not bypass any payload, evidence, release, performance, or approval requirement.

Gate 4 derives incremental authoring state from the eight positional aggregate pairs instead of trusting a user-set phase label. `EMPTY` and `PUBLIC_HEAD_CONCEPT` both use mask `00000000`; the latter additionally requires at least one ordinary concept, no advanced row, 52 `INACTIVE` control rows, and a clean current `HEAD` proven at an advertised `refs/heads/*`, `refs/pull/<positive>/head`, or `refs/pull/<positive>/merge` ref through an explicit credential-free fresh fetch. `STAGED_WB` uses `11xxxxxx`: payload plus whitelist are inseparable and at least one row is active. `APPROVED` is `11111111`. Optional bits require the core. A workflow may remain pending with a recipe but cannot populate without one. Present rollups bind their positional digest and global build. Evidence presence requires all 52 rows plus all four rollups active and all 392 gates complete on one global build. An ordinary staged active row still needs a canonical build ID but need not equal that global ID until evidence or approval.

Concept validation reads accepted files from the fresh clone and rejects dirty/local-only commits, ignored extras or symlinks in concept roots, Gate-1 authority records, authoring receipts, Gate 2–7 files, and converted/output bytes. Staging then uses reviewed-payload commit `P` followed by its sole-child control commit `A`; `P→A` changes only `docs/VISUAL_BENCHMARK_APPROVAL.md`, current public `HEAD` descends from `A`, the control at `A` byte-equals current, and current `HEAD^{tree}` equals `A^{tree}`. The last condition permits an identical-tree synthetic PR merge but rejects later byte drift. These preapproval branch/PR-ref rules do not alter the default-public-`HEAD` rule for postapproval production.

`scripts/build-rom` starts by deleting only the resolved repository `build/` path and the exact transient root-level `n64game-gate3.z64` staging path used by libdragon's upstream make rule. It exports each pinned submodule through `git archive` into `build/deps/`, so generated headers and dependency objects never dirty the public gitlinks. CLI 12.2.1 creates or starts the digest-addressed container; the wrapper then verifies its running state, exact image identity, and one expected read-write project mount before invoking the audited project build with Docker. The wrapper resolves the positive `SOURCE_DATE_EPOCH` from the trusted host checkout and passes that value into the container, so the container never needs to weaken Git ownership checks for differently presented bind mounts. Direct `libdragon exec` is intentionally avoided because its fresh-container recovery path silently runs the vendor's broader `build.sh` before the requested command. The audited container entrypoint installs the pinned libdragon library/tools, builds Tiny3D locally, and compiles the project with warnings as errors.

Project code enables `-Wshadow` and `-Wconversion` as errors in addition to the pinned toolchain defaults. One known conversion warning inside Tiny3D's inline `t3d_mat4fp_set_float` mask is suppressed only while parsing the pinned upstream header; strict conversion diagnostics resume before any project declaration or function body.

The selected OCI image currently publishes Linux AMD64 plus provenance, not an ARM64 runtime. The wrapper sets `DOCKER_DEFAULT_PLATFORM=linux/amd64`; Apple Silicon therefore requires Docker's x86 emulation. CI runs the same image natively on an AMD64 runner.

### Verified Apple Silicon runtime

Gate 3 passed on Docker Desktop 4.82.0 build 233772 using context `desktop-linux`, Docker client 29.6.2, and Docker Engine 29.6.1. On clean commit `dd038488d7100c30fa3699e15ffa0613ec6d6468`, Docker Desktop ran the exact pinned `linux/amd64` image and produced the CI/Ares ROM SHA-256 `230896d0d8a39dae3dd6ee5e1e471377be51fdbb2b45b78a5c8439f865394d7e`. `make validate`, `make rom`, 17/17 host tests, `make report`, and `scripts/bootstrap-check --all` all passed. Apple Silicon uses Docker Desktop's x86 emulation because the pinned image has an AMD64 runtime.

The Docker backend recovered after a fresh app launch without a host reboot. The earlier macOS diagnostic `failed to call driver: 0x3` remains disclosed in the evidence record; it did not prevent the verified run.

Before Docker Desktop recovered, the same immutable build was also verified through Colima 0.10.3 / Lima 2.1.4 using Virtualization.framework, virtiofs, and Rosetta. That historical fallback can help diagnose Docker Desktop host-service failures, but it is not the Gate 3 closure proof:

```sh
brew install colima
colima start --profile n64game \
  --runtime docker --vm-type vz --arch aarch64 --vz-rosetta \
  --mount-type virtiofs --cpus 4 --memory 8 --disk 60 --activate=false
export DOCKER_CONTEXT=colima-n64game
export DOCKER_DEFAULT_PLATFORM=linux/amd64
scripts/bootstrap-check --all
make validate && make rom && make test && make report
```

This fallback produced the exact same ROM from clean commit `85e91c793eccaeff70327ea6fd67e8f7e775faad`. Keep it separate from the verified Docker Desktop record so provider identity remains auditable.

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

The wrapper verifies both executable and ROM hashes, forces `General/HomebrewMode=true`, forces `Nintendo64/ExpansionPak=false`, pins the SDL input driver, supplies deterministic macOS keyboard bindings for every control used by the chapter, forces `Input/Defocus=Allow`, and uses isolated versioned settings/save/screenshot/debug paths. Keyboard arrows map to the N64 D-pad, `Z` maps to N64 `A`, `X` maps to N64 `B`, `C` maps to N64 C-down, `Space` maps to N64 `Z`, and `Return` maps to N64 `Start`; the Ares game window must still be focused for keyboard events. The first two overrides are mandatory because Ares v148 defaults Homebrew Mode off and Expansion Pak on. The defocus override keeps shell-launched certification runs advancing when macOS places the emulator window on a non-current Space; without it, Ares's default pause-on-defocus policy can leave a valid ROM on a black pre-frame window. `--check-only` verifies the complete tuple without launching the GUI.

## Gate 4 Blender and Fast64 authoring contract

Gate 4 asset work uses one exact native Apple Silicon stack. Blender 5.2, another Blender 4.5 patch, a generic `blender` executable from `PATH`, and a different or disabled Fast64 checkout all fail authoring acceptance.

| Component | Exact authority |
| --- | --- |
| Blender | 4.5.11 LTS, build hash `4db51e9d1e1e`, thin ARM64 macOS executable |
| Official Blender asset | [`blender-4.5.11-macos-arm64.dmg`](https://download.blender.org/release/Blender4.5/blender-4.5.11-macos-arm64.dmg), 308255028 bytes, SHA-256 `1fad76c7da9451c7d6db99f1a5ed3c0a1a461d0aa07bf2b639e2fb4804ca4f13` |
| Installed Blender executable | `$HOME/Applications/Blender-4.5.11.app/Contents/MacOS/Blender`, 175667888 bytes, SHA-256 `8156431a9b9ec1daf49bccea4bd92f327f6efc1ca330d5103881580f3e7773ef` |
| Fast64 | v2.5.3 at commit `8e9630c11824a9c00e9379279d43c64264eda87e` |
| Official Fast64 asset | [`fast64-v2.5.3.zip`](https://github.com/Fast-64/fast64/releases/download/v2.5.3/fast64-v2.5.3.zip), 1882004 bytes, SHA-256 `2a308e04ee591e328856e8dff5bbe5aa72f284873e874ba5aba5927831889010` |
| Enabled Fast64 root | `$HOME/Library/Application Support/Blender/4.5/scripts/addons/fast64` |

Run the installed-stack check before benchmark authoring or export:

```sh
scripts/check-authoring-stack
```

The checker is observational. Its checker and test entrypoints use absolute `/usr/bin/python3 -I -B`, so a `PATH`-selected interpreter, inherited `PYTHON*` import paths/home, user-site packages, and Python bytecode writes cannot alter the run. Before executing Blender, it verifies the locked metadata, exact executable bytes, ARM64 Mach-O identity, app version/build hash, and the complete app seal with absolute `/usr/bin/codesign --verify --deep --strict` plus an explicit Blender Foundation team/identifier requirement. It repeats that seal check after the probe. Fast64 must be the exact 226-file release source tree; any symlink, `__pycache__`, `.pyc`, or mutable updater-status file fails instead of being ignored.

The enabled-state probe never starts from the live Blender profile or imports the live add-on directory. It copies `userpref.blend` and the already byte-verified Fast64 source into a temporary profile, binds config/scripts/data/extensions/cache/home/temp paths there, drops inherited `PYTHONPATH`, `DYLD_*`, and other environment state, starts Blender in factory/background/offline/auto-execution-disabled mode, disables Python bytecode writes before loading the copied preference, and imports only the isolated Fast64 copy. The live app, preference, and Fast64 source are snapshotted before and after. Temporary probe state is removed on exit. The checker does not download, install, enable, update, save preferences, or alter project/global state.

The default paths are versioned rather than discovered from `PATH`. `N64GAME_BLENDER_BINARY` and `N64GAME_FAST64_ROOT` may point the checker at another host installation, but every byte/version/signature/path-to-module check still applies. Supplying a Blender 5.2 executable therefore fails; an override cannot weaken the pin.

Distribution archives do not need to remain on the host after verified installation. If retained, audit them directly without mounting or extracting them:

```sh
scripts/check-authoring-stack \
  --blender-dmg /absolute/path/to/blender-4.5.11-macos-arm64.dmg \
  --fast64-zip /absolute/path/to/fast64-v2.5.3.zip
```

Without those optional arguments, the report labels each archive `NOT_SUPPLIED_PIN_RECORDED`; this is not a claim that the archive was re-hashed during that run. The installed executable and add-on still must pass. Use `--json` for a machine-readable host observation. That path-bearing observation is not a Gate 2 or Gate 5 per-asset approval receipt and cannot unlock a production row; the asset pipeline must separately bind an exact stack pass to the reviewed source, output manifest, build, and gate evidence. Run `make test-authoring` for portable positive, wrong-version, missing-add-on, symlink, bytecode/updater-state, contaminated-interpreter/environment, deep-signature-command, disabled-add-on, and byte-tamper tests.

For a canonical `RIGGED_MODEL`, `STATIC_MODEL_ENV`, or `ANIMATION` asset—or any other canonical asset whose transitive source-manifest closure owns a `.blend` file—the binding is an exact per-asset receipt at both Gate 2 and Gate 5. Produce the source-stage record only after the canonical source manifest exists:

```sh
scripts/record-authoring-stack-receipt g2 --scope echo.quarrune
```

Gate 5 may not create a receipt after an unrelated manual export. The checked-in, still-locked implementation candidate is deliberately limited to the split Quarrune model/animation owners. After lawful G1-G4 source authorization exists, it can materialize a pre-approval conversion candidate from source-only allowlists; this runs the real export twice and does **not** create a receipt or approve any gate:

```sh
scripts/export-gate5-asset \
  --scope echo.quarrune \
  --paired-scope anm.echo.quarrune \
  --build-id n64game-g4-6531e405 \
  --deterministic \
  --candidate
```

The candidate command requires exact, owner-rooted, manifest-owned, materialized Git-LFS source at `assets-src/echo/echo.quarrune/quarrune.blend`, `assets-src/anm/anm.echo.quarrune/quarrune_actions.blend`, and the three canonical authored paletted PNG paths under the model owner. Those five exportable members must be `source.authored`; linked Blender libraries and unpacked external media are rejected. Both owners must already have exact tracked authorization and Gate 1–4 completion records. The exporter has no procedural model, texture, animation, or placeholder fallback. It captures the complete transitive source and validation-authority closure once, supplies each clean run from those immutable captured bytes, and rejects any live-byte drift before promotion. The current repository has no visually accepted canonical Quarrune source pair, so this precondition is intentionally unsatisfied.

The macOS-arm64 `gltf_to_t3d` and `mksprite` host tools are not trusted merely because they appear under `$N64_INST/bin`. `config/toolchain.lock.json` records the source commits, compiler identity, exact clean-build commands, two-build comparison count, executable sizes, and SHA-256 values. Export refuses a platform mismatch, arbitrary executable, or one-byte drift even when both submodules are clean at the correct commits.

Candidate publication is serialized by one repository-keyed exclusive transaction lock. Destination parents are opened component-by-component with directory descriptors and `O_NOFOLLOW`; candidate members use no-overwrite descriptor-relative promotion, an ignored durable transaction journal, directory `fsync`, rollback on ordinary failure, and a complete post-promotion pair validation while the lock remains held. A detected interrupted journal fails closed or is deterministically recovered before another transaction. Final regeneration is verification-only: once reviewed bytes and exact per-owner `OUTPUT:runtime` rows exist, the exporter regenerates twice and byte-compares them but does not rewrite the reviewed package. After a later lawful art transaction supplies and passes the real source, stores the reviewed pair through canonical LFS, represents it by exact per-owner output rows, and deliberately flips/pins the exporter locks, regenerate and verify it while producing both receipts under the same held lock:

```sh
scripts/record-authoring-stack-receipt g5-export-pair \
  --scope echo.quarrune \
  --paired-scope anm.echo.quarrune \
  --build-id n64game-g4-6531e405 \
  --replace
```

Until that later transaction, `g5-export-pair` fails before conversion because `GATE5_EXPORT_IMPLEMENTED=false` and `APPROVED_GATE5_EXPORTER_SHA256=PENDING`. Once lawfully enabled, the destinations are fixed as `review/echo.quarrune/g5/AUTHORING_STACK_RECEIPT.txt` and `review/anm.echo.quarrune/g5/AUTHORING_STACK_RECEIPT.txt`. The pair producer holds the shared transaction lock from preflight through receipt promotion, checks the exact stack before and after export, and returns an immutable checked snapshot of both source closures, both output manifests, and every owned output member. Both receipts are built only from that returned snapshot, revalidated immediately before descriptor-relative promotion, and rollback-protected as a pair. The legacy single-scope `g5-export` operation is fail-closed; extending Gate 5 to another owner requires a separately reviewed exporter change.

Each record contains exactly 14 ordered fields: schema, scope, gate, source/output hashes, build, reviewed toolchain-lock hash, checker-bundle hash, Blender/Fast64 pins and seals, result, and check time. G2 binds output `NONE` and build `-`; G5 binds the exact current output-manifest digest and substantive shared clean-build ID. The producer strips Python injection state and refuses a missing, symlinked, non-executable, failing, hash-drifted, or stack-changing exporter. It accepts no caller-selected executable: only the repository path `scripts/export-gate5-asset` may eventually be pinned. The Phase-1 exporter surface is present for fail-closed testing, but `GATE5_EXPORT_IMPLEMENTED=false` and `APPROVED_GATE5_EXPORTER_SHA256=PENDING` remain authoritative. No accepted G5 receipt can be created until real canonical Quarrune inputs complete deterministic pair conversion, closure sealing, tool provenance, review, and the implementation flag and exact hash are deliberately enabled together in a later audited change.

`checker_sha256` is not the digest of either small shell entrypoint alone. It is SHA-256 over the domain line `n64game-authoring-checker-bundle-v1`, followed by sorted `path<TAB>sha256<LF>` rows for `lib/n64game/libdragon_sprite_contract.rb`, `lib/n64game/tiny3d_package_contract.rb`, `scripts/check-authoring-stack`, `scripts/export-gate5-asset`, `scripts/record-authoring-stack-receipt`, `tools/n64game_authoring.py`, `tools/n64game_authoring_receipt.py`, and `tools/n64game_gate5_export.py`. The production validator recomputes that bundle and `config/toolchain.lock.json` from the exact reviewed historical commit. It verifies the frozen Blender/Fast64 identities, exact gate source/output/build bindings, strict timestamp ordering, and direct evidence ownership. Each receipt is one ordinary-Git text member of only its own G2/G5 `EVIDENCE_MANIFEST.sha256` at role `authoring.stack_receipt`; it is never owned by `OUTPUT_MANIFEST.sha256`, another gate, a rollup, or multiple manifests.

The receipt is deterministic workflow evidence, not a standalone cryptographic claim that can defeat a malicious repository author: its fields are public and therefore could be hand-written. Acceptance also requires the independently reviewed gate graph, the complete deterministic conversion/in-engine evidence, and the signed public benchmark approval whose pinned external key covers the payload bytes. Until those trust anchors, canonical inputs, reproducibly proven converter binaries, closure seals, and native evidence exist, the Phase-1 surface cannot unlock G5 or global approval. The validator freezes the full approved lock-file and checker/producer-bundle digests so ordinary code/pin drift cannot self-authorize a matching receipt.

## Quarrune Tiny3D package prerequisite

`lib/n64game/tiny3d_package_contract.rb` is the fail-closed package reader for the pinned Tiny3D commit. It is a narrow Gate-5 prerequisite, not a converter, a visual review, or proof that Quarrune is finished. The live validator invokes it in all four lifecycle paths: preapproval, approved payload, unchanged postapproval, and changed postapproval. Preapproval permits neither package to exist yet, but never permits a one-sided package; every later path requires the pair.

The model owner `echo.quarrune` directly owns exactly these reserved Tiny3D model members:

| Path | Manifest role | Storage |
| --- | --- | --- |
| `review/echo.quarrune/g5/quarrune_distance.t3dm` | `output.tiny3d.model` | canonical Git LFS |
| `review/echo.quarrune/g5/quarrune_hero.t3dm` | `output.tiny3d.model` | canonical Git LFS |
| `review/echo.quarrune/g5/tex_quarrune_body_ci8_64x64.sprite` | `output.texture.body` | canonical Git LFS |
| `review/echo.quarrune/g5/tex_quarrune_accent_ci4_32x32.sprite` | `output.texture.accent` | canonical Git LFS |
| `review/echo.quarrune/g5/tex_quarrune_blob_shadow_ia8_32x32.sprite` | `output.blob_shadow.sprite` | canonical Git LFS |
| `review/echo.quarrune/g5/RUNTIME_BINDING.tsv` | `output.runtime_binding` | ordinary Git, UTF-8/LF text |

The animation owner `anm.echo.quarrune` directly owns this paired package:

| Path | Manifest role | Storage |
| --- | --- | --- |
| `review/anm.echo.quarrune/g5/anm_echo_quarrune.t3dm` | `output.tiny3d.animation_header` | canonical Git LFS |
| `review/anm.echo.quarrune/g5/anm_echo_quarrune.0.sdata` through `.8.sdata` | `output.tiny3d.animation_stream` | canonical Git LFS |
| `review/anm.echo.quarrune/g5/SKELETON_BINDING.tsv` | `output.skeleton_binding` | ordinary Git, UTF-8/LF text |

The nine stream ordinals are fixed as `brace_relay`, `entrance`, `hit`, `horizon_break`, `idle_a`, `idle_b`, `knockout`, `reposition`, and `ridge_ram`. Their embedded ROM paths are exactly `rom:/anm/anm.echo.quarrune/anm_echo_quarrune.<ordinal>.sdata`. Reserved roles on any other path, extra `.t3dm`, `.sdata`, or `.sprite` members, nested-only package members, cross-owner streams, ordinary-Git binary payloads, executable modes, missing LFS objects, and unequal model/animation build IDs fail. Other nonreserved `echo.quarrune` output members remain legal only when the existing exact selector allowlist owns them; the package census does not create new source authority.

The binding has exactly these 15 ordered TAB keys and one final LF: `schema`, `tiny3d_commit`, `model_production_id`, `animation_production_id`, `hero_model_path`, `hero_model_sha256`, `distance_model_path`, `distance_model_sha256`, `animation_header_path`, `animation_header_sha256`, `animation_stream_set_sha256`, `skeleton_signature_sha256`, `bone_count`, `animation_names`, and `build_id`. It pins both model hashes, the animation-header hash, a domain-separated ordered stream-set hash, the shared build, and a domain-separated signature over all 20 bone ordinals, names, parents, depths, and raw big-endian rest SRT bytes. A digest-correct but semantically stale binding fails.

The reader bounds-checks the Tiny3D v4 header, chunk table, alignment and zero padding; exact model/animation chunk order; packed vertex source ranges, region-local UV bounds, and object/model AABBs; loaded vertex-cache domains; indexed, unindexed-sequence, and restart-strip triangle counts; strip DMA safety; optional BVH graph/object coverage and descendant AABBs; material runtime fields and bound texture path/hash pairs; the exact 20-joint, fully weighted Quarrune skeleton; animation mappings; and every compressed stream record, size flag, packed-quaternion radicand, channel coverage, and global writer order. Production models require an 850–1,250-triangle hero, a positive distance mesh of at most 650 triangles and 45–60 percent of the hero, exactly three distinct and used materials, non-collapsed UV islands measured only from vertices reached by real draw commands, and one slot-A/TILE0 texture per material with slot B empty. Every material pins the complete reviewed record: one-cycle `TEX0 × SHADE`, exact OtherMode value and mask, opaque blend word, depth/textured/shaded flags, disabled fog and color overrides, point filtering, no mipmaps, and ordinary mesh UVs in the closed interval from zero through the local texture edge. Two body materials use exact dynamic references `0x51554230` and `0x51554231` at logical 64×32, while the accent material uses `rom:/echo/echo.quarrune/tex_quarrune_accent_ci4_32x32.sprite`. Tests build independent big-endian fixtures, materialize real Git LFS pointers/objects, parse real committed output manifests, and mutate these boundaries.

`lib/n64game/libdragon_sprite_contract.rb` independently decodes the exact raw, uncompressed libdragon v6 sprite layout from the pinned commit. There is no invented magic header: the decoder checks the big-endian base header, pixel rows and alignment, 128-byte extended header, zero LOD/detail/embedded-parameter/runtime fields, exact palette offset and the Quarrune profile's deliberately full-capacity palette storage, file EOF, indices against the writer used-color count, and the writer's truthful `FITS_TMEM` calculation. Full-capacity palette storage is a stricter canonical-output choice for this package, not a claim that every valid `mksprite` file uses it. DCA, BC1Q, H264I, tiled, legacy, mipmapped, detail, and runtime-mutated sprites fail. The body is exactly 64×64 CI8 with a full 256-entry RGBA5551 palette and must report `FITS_TMEM=0`; the accent is exactly 32×32 CI4 with a full 16-entry palette and must fit; the blob shadow is exactly 32×32 IA8 and must fit. Body/accent indices must form contiguous intentional palettes of at least 32/8 unique opaque colors with a readable value span. The shadow requires a transparent perimeter, authored multi-level alpha ramp, central connected footprint, and nontrivial coverage.

Canonical source PNGs are already author-paletted at their final dimensions; the converter may not resize, quantize, dither, mipmap, tile into multiple slices, or choose compression implicitly. The clean exporter must invoke the pinned tool with the semantic equivalents of these exact argument vectors and then byte-compare regenerated outputs with the review snapshots:

```sh
mksprite --format CI8 --tiles 64,64 --mipmap NONE --dither NONE --compress 0 -o OUTPUT_DIR tex_quarrune_body_ci8_64x64.png
mksprite --format CI4 --tiles 32,32 --mipmap NONE --dither NONE --compress 0 -o OUTPUT_DIR tex_quarrune_accent_ci4_32x32.png
mksprite --format IA8 --tiles 32,32 --mipmap NONE --dither NONE --compress 0 -o OUTPUT_DIR tex_quarrune_blob_shadow_ia8_32x32.png
```

Omitting `--compress 0` is not equivalent: pinned `mksprite` defaults to an asset-compressed wrapper, while this contract deliberately validates the raw lossless payload that `sprite_load` receives after no decompression ambiguity.

The 64×64 CI8 body sprite intentionally occupies 4,096 texel bytes plus the 2,048-byte TLUT reservation, so Tiny3D's ordinary whole-sprite upload would assert instead of fitting CI's 2,048-byte texel bank. `src/quarrune_render_assets.c` loads that one authored atlas once, creates zero-copy top `(0,0,64,32)` and bottom `(0,32,64,32)` `surface_make_sub` views, explicitly disables mipmapping, and uploads the selected 64×32 view with `rdpq_tex_upload` on TILE0. It never uses `rdpq_sprite_upload` on the full body and never uses `rdpq_tex_upload_sub`, whose preserved full-atlas coordinates would disagree with the model's region-local UVs. Every body bind re-enables `TLUT_RGBA16` and uploads the shared palette, including after a CI4 accent draw; callback health becomes true only after both region references have successfully executed. The helper separately owns the IA8 shadow, rejects double loading, and uses `rspq_block_atexit` references whenever a body or shadow upload is recorded. Unload waits for current RSP work, stops new use, and keeps sprite storage alive until every recorded block is freed, closing replay-after-free. Its source/header bundle is materialized from the reviewed commit, verified as ordinary mode-`100644` Git bytes, frozen as `b9125d3375842e75dc4d0227abbf2158126e1b9ba684842c9f9326071c7b7853`, compiled by the pinned MIPS build, and executed through a strict host lifecycle harness; the no-assets diagnostic scene itself does not load it.

`RUNTIME_BINDING.tsv` has exactly 28 ordered TAB keys and one final LF: `schema`, `libdragon_commit`, `tiny3d_commit`, `runtime_helper_paths`, `runtime_helper_bundle_sha256`, `production_id`, `body_sprite_path`, `body_sprite_sha256`, `body_rom_path`, `body_top_reference`, `body_top_rect_px`, `body_bottom_reference`, `body_bottom_rect_px`, `body_reference_size_px`, `body_upload_mode`, `material_profile`, `accent_sprite_path`, `accent_sprite_sha256`, `accent_rom_path`, `blob_shadow_sprite_path`, `blob_shadow_sprite_sha256`, `blob_shadow_rom_path`, `blob_shadow_format`, `blob_shadow_size_px`, `footprint_mm`, `footprint_offset_mm`, `base_opacity_q8`, and `build_id`. It binds all three sprite hashes, both dynamic IDs/rectangles, the 64×32 local-view upload strategy, TILE0/TEX0/point material profile, exact ROM paths, 1,250×800 mm centered shadow footprint, Q8 opacity 176, helper bundle, tool commits, and shared build.

This prerequisite still does **not** certify that real Quarrune art exists or looks good. Structural anti-blank floors cannot prove the ceramic forms, horn lattice, palette craft, topology, deformation, animation appeal, 320×240 readability, native performance, or seven visual gates and two post-integration polish passes. The canonical source `.blend`/PNG bytes, real converted model/texture/shadow output, turntables, in-engine captures, reviewer decisions, and native evidence remain mandatory. The still-locked exporter candidate can only reject or convert those authored inputs; it cannot create them, waive a visual gate, populate benchmark control, or turn a future implementation pin into approval.

## Public CI

`.github/workflows/build-rom.yml` uses an explicit Ubuntu 24.04 runner, commit-pinned GitHub Actions, Node 24.18.0, recursive submodules, Git LFS, non-persisted checkout credentials, the same stable entry points, a clean-source diff check, and an artifact upload containing the ROM, checksum, linker map, ELF size output, dependency manifest, host-test report, and validation summary. Report generation fails closed if the map, ELF size output, or exact host-test PASS contract is missing. A successful workflow proves a fresh public build candidate; it still does not replace the local Ares boot inspection and is never labeled a boot proof by CI alone.

## Known upstream test boundary

The official workflow for libdragon `f13b48985edbf4310f07779c76d9a68c7605037b` successfully built its container, library, and tools but its full upstream `./build.sh --test` run failed in an `mkmaterial` fixture assertion. Gate 3 therefore runs the exact project-relevant library/tool/Tiny3D/ROM build and discloses the upstream red suite instead of claiming it passed. If the pinned project build itself fails, the incompatibility must be recorded and an explicit mutually compatible commit selected under the master specification; it may not be hidden by a floating update.
