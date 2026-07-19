# Gate 3 Ares Boot Evidence

## Result

**PASS for Gate 3 boot and live-frame advancement.** The exact ROM downloaded from the public GitHub Actions artifact opened in the pinned Ares v148 binary, rendered the original Tiny3D diagnostic scene, and advanced between two direct window captures. This is deliberately narrow evidence: it does not claim controller certification, performance certification, production-art approval, the playable opening, or the complete game.

## Public build identity

| Field | Verified value |
|---|---|
| Repository / PR | `oh-ashen-one/n64game` / pull request `#3` |
| Workflow run | `29674638989` (`success`) |
| Workflow job | `88159621235` (`success`, Ubuntu 24.04) |
| PR head | `4265329248375578e1bbe1c416e9ba004f7fa36b` |
| Actions merge revision | `657d3500e157bd10e09618a178a12c792c9977b5` |
| Recorded source tree | `cf03da713305db581b5113a2b2d726b37df57b73` |
| Artifact | `n64game-gate3-657d3500e157bd10e09618a178a12c792c9977b5`, ID `8438442749` |
| Uploaded artifact digest | `b95c1b06cdf1a2a682967099630d82170f3e533a91d088249f0faef44c3b5a1b` |
| ROM SHA-256 | `230896d0d8a39dae3dd6ee5e1e471377be51fdbb2b45b78a5c8439f865394d7e` |
| ROM size | `212992` bytes |

The downloaded artifact had exactly the eight workflow-declared files and no symlinks. Its checksum file passed from the artifact's `game/` directory. The ROM, map, ELF-size, and host-test hashes recomputed to the values in `dependency-build-manifest.json`; the manifest reported a clean source tree and `PASS` for pins, ROM structure, embedded big-endian MIPS ELF, ROM budget, and host tests. The live `refs/pull/3/merge` value matched the recorded Actions merge revision at audit time.

After the local-runtime portability fix, public confirmation run `29675864028` / job `88163077829` passed on PR head `85e91c793eccaeff70327ea6fd67e8f7e775faad` and Actions merge revision `75499d5784967852cab2c4ca071cf7aeb05e2e70`. Artifact `8438863000` contained the same exact eight-file inventory; its uploaded ZIP digest is `f7bc2ba02d37ed1535f300702fa721f40da9b7fe0787dac76b6653d026c3ca83`. Its 212992-byte ROM retained SHA-256 `230896d0d8a39dae3dd6ee5e1e471377be51fdbb2b45b78a5c8439f865394d7e`, so the later source revision is byte-identical to the ROM used for both Ares captures.

The machine-readable identity record is [`captures/gate3/evidence.json`](../captures/gate3/evidence.json). Host tests recompute both PNG hashes, byte sizes, PNG signatures, dimensions, and the distinct-frame requirement, then lock the recorded ROM, Ares, and CI identifiers to audited values against it and `SHA256SUMS`.

The successful link command contained Tiny3D exactly once through `N64_LDFLAGS`. The ROM validator independently confirmed big-endian magic, title `N64GAME GATE 3`, entrypoint `0x80000400`, EEPROM4K/region-free/controller configuration, pinned libdragon IPL3 hash, deterministic TOC, embedded ELF at byte `7680`, 16 KiB alignment, and the ROM hash above.

## Emulator identity and launch tuple

| Field | Verified value |
|---|---|
| Ares version | `v148` |
| Ares executable SHA-256 | `7a49f00f96a691458461d7c9cf453d95c0f5c054389bbd87c253987b8b6fa345` |
| Ares release commit | `0aafd85789215e84e1e43415c07d4c88461b7899` |
| Mode | `General/HomebrewMode=true` |
| Memory | `Nintendo64/ExpansionPak=false` |
| Defocus policy | `Input/Defocus=Allow` |
| State root | isolated `ares-v148-n64game` settings/save/screenshot/debug directories |

The defocus override is part of the reviewed `scripts/run-ares` launch contract. It is required for shell-driven evidence capture because Ares v148 otherwise pauses before the first presented frame when macOS places its window on a non-current Space. The ROM and executable hashes were checked before launch.

## Direct visual observations

The first capture shows the Ares window named `n64game-gate3` presenting:

- cyan `N64GAME` title;
- `PINNED TINY3D TOOLCHAIN PROOF` label;
- a lit, shaded four-vertex Tiny3D diagnostic solid on the dark cleared framebuffer; and
- `A  PULSE: OFF` status text.

The second capture shows a materially different orientation and lighting silhouette while all fixed text remains coherent. The distinct PNG hashes provide a simple frame-advancement check; they do not substitute for later frame-time instrumentation.

| Capture | Local time (`America/New_York`) | Dimensions | Bytes | SHA-256 |
|---|---:|---:|---:|---|
| [`frame-a`](../captures/gate3/ares-v148-ci-29674638989-frame-a.png) | `2026-07-19T01:25:09-04:00` | `836x672` | `75210` | `b5fde7458a6e606f76139732894dfa4784dd6fae2eb57f351fea5424ebe1d75a` |
| [`frame-b`](../captures/gate3/ares-v148-ci-29674638989-frame-b.png) | `2026-07-19T01:26:18-04:00` | `836x672` | `73695` | `0db4dc319016fbaddd01671748927c9560fb6e2af173948b18b9358ee98e94a5` |

These are unedited macOS Quartz captures of Ares window `19558`; the window chrome is intentionally retained so the evidence shows the emulator-owned surface and ROM title. The ROM binary remains an ignored CI artifact and is not committed.

## Known emulator diagnostic

Ares emitted `[unusual]` RSP cache-coherence diagnostics while the scene continued to render. A source/map audit resolved the recorded CPU PCs to pinned libdragon/newlib internals (`register_DP_handler`, `register_TI_handler`, `_malloc_r`, and `_memalign_r`), and the two warned RDRAM regions are separated by `0x820`, matching libdragon's paired `0x800`-byte RSPQ queue allocations plus allocator spacing. The project's matrix and vertex buffers already use `malloc_uncached` exactly as in Tiny3D's pinned official example. Adding a project-side cache writeback would target the wrong allocations and could corrupt uncached data, so the warning is disclosed as an upstream libdragon allocator/RSPQ interaction rather than suppressed or falsely called clean. It remains technical debt for later certification, not evidence that this rendered Gate 3 frame failed to boot.

## Local-build status

**PASS through an audited Docker-compatible fallback; the master specification's literal Docker Desktop requirement remains blocked, so Gate 3 remains open.** On clean source commit `85e91c793eccaeff70327ea6fd67e8f7e775faad` (tree `292a0c867bd71b1f1c7d5cf7d935f9b0953a0016`), `make validate`, `make rom`, all 17 host tests, `make report`, and `scripts/bootstrap-check --all` passed. The local ROM was 212992 bytes with SHA-256 `230896d0d8a39dae3dd6ee5e1e471377be51fdbb2b45b78a5c8439f865394d7e`, identical to the public CI and Ares evidence ROM.

The successful local build used Colima 0.10.3 and Lima 2.1.4 with macOS Virtualization.framework, an ARM64 VM, virtiofs, Rosetta enabled, Docker client 29.6.2, and Docker Engine 29.5.2. The engine executed the exact locked `linux/amd64` image ID `sha256:36a295cbe43168e8adbfa5c86d956df3dc762a1ab6fda1b50dcb33bd78dc2d83`. The wrapper now derives the positive `SOURCE_DATE_EPOCH` from the trusted host checkout and passes it into the container, avoiding a Git `safe.directory` exception when a Docker-compatible runtime presents bind-mount ownership differently.

This fallback does not get relabeled as Docker Desktop. Docker Desktop 4.82.0 build 233772 remains installed from the exact Homebrew ARM64 archive SHA-256 `2da717ef1ca2ae0240a68458e0aaee32be9bd9fe574fd916dd43dae40f17c12c`; its deep Developer ID signature for Docker Inc team `9BNSXJN65R` passes and the official DMG notarization ticket validates. The host policy service still reports `failed to call driver: 0x3`, kills or stalls the backend before `dyld` startup, and never creates its Docker socket. Because `docs/N64GAME_MASTER_SPEC.md` explicitly says to use Docker Desktop, Gate 3 cannot be called complete unless Docker Desktop itself passes after a host reboot or the user explicitly authorizes a contract amendment.

## Explicit boundaries

- Gate 3 proves that the exact pinned dependencies can produce a structurally valid ROM in clean public CI and that those exact ROM bytes boot and render live Tiny3D frames in the pinned Ares target.
- The diagnostic geometry is original engineering proof, not a production visual benchmark or a shortcut around the seven-gate asset process.
- `A  PULSE: OFF` is visible, but this capture did not certify a mapped physical controller or the A-button transition. Controller matrices belong to later gameplay/certification gates.
- Gate 4 remains responsible for the representative environment, humanoid, Echoform, UI, lighting, battle-animation, VFX, native-resolution, memory, and performance benchmark.
