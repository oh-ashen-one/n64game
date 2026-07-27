# Laptop Handoff

This repository is the public handoff for the current `n64game` development slice:

- Repository: <https://github.com/oh-ashen-one/n64game>
- Default branch: `main`
- Required baseline: commit `3b84b56` or newer
- Baseline public CI: [Build ROM run 29836535817](https://github.com/oh-ashen-one/n64game/actions/runs/29836535817) passed
- Authoritative scope: [docs/N64GAME_MASTER_SPEC.md](docs/N64GAME_MASTER_SPEC.md)
- Reusable goal prompt: [docs/N64GAME_GOAL_PROMPT.md](docs/N64GAME_GOAL_PROMPT.md)

The authoritative target is the reduced, polished 6–8 minute opening chapter. Do not re-expand it to the older 20-minute plan. The Estate, world map, second battle, follower system, and extra Echoforms remain out of scope.

## Resume on the laptop

For a fresh checkout:

```sh
git clone --recurse-submodules https://github.com/oh-ashen-one/n64game.git
cd n64game
git lfs install
git lfs pull
npm ci --ignore-scripts
```

For an existing checkout with no uncommitted work:

```sh
git switch main
git pull --ff-only origin main
git submodule update --init --recursive
git lfs pull
npm ci --ignore-scripts
```

Do not overwrite a dirty checkout. Run `git status -sb` first and preserve any local work.

## Validate, build, and launch

Docker Desktop is the verified build runtime. The exact dependencies and pinned versions are in [docs/TOOLCHAIN.md](docs/TOOLCHAIN.md).

```sh
make validate
make rom
make test
make report
scripts/fix-ares-input
rom_sha=$(shasum -a 256 build/game/n64game-gate3.z64 | awk '{print $1}')
scripts/run-ares --homebrew-mode \
  --expected-rom-sha256="$rom_sha" \
  build/game/n64game-gate3.z64
```

The `n64game-gate3.z64` filename is retained for build-contract compatibility; it contains the current development game. Generated ROMs, reports, emulator configuration, and other local build outputs belong under ignored paths and must not be committed.

On macOS, permit the signed Ares app (`dev.ares.ares`) in **System Settings → Privacy & Security → Input Monitoring**, restart Ares, and click the game viewport once.

Keyboard controls in pinned Ares v148:

- Arrow keys or `WASD`: movement and menu navigation
- `X`: N64 A / confirm / interact
- `Z`: N64 B / back
- `Return`: N64 Start
- `Space`: N64 C-down / Field Relay
- `Left Shift`: N64 Z

The keyboard mapping was corrected in `3b84b56`. Ares uses its own Quartz keyboard-list indices, not raw macOS keycodes or SDL scancodes.

## Current state

Implemented:

- Player-driven Annex route through Atrium, Simulation, Workshop, and Overlook
- Name entry, dialogue, four examines, Pause, and Field Relay
- Full controller-driven Quarrune/Ayselor versus Gyreclast/Kivarrax 2v2 battle
- Retry and return restoration
- EEPROM save schema v2 and safe-anchor resume
- Beacon corruption hook and stable post-chapter archive
- Twelve-panel opening storyboard package
- Reproducible public ROM build and corrected Ares keyboard profile

Not yet certified or approved:

- Real timed cold-boot 6–8 minute Ares playthrough evidence
- Complete visual-benchmark capture and independent approval
- Production approval of the reviewed 3D and texture candidates
- Final audio, VFX, lighting, camera staging, and pacing pass
- Performance, soak, repeated-transition, and physical Nintendo 64 evidence

Run these to see the live acceptance state:

```sh
scripts/audit-ares-input --strict
scripts/audit-visual-benchmark-readiness
scripts/audit-final-acceptance
```

Do not claim physical-hardware completion from a build, public CI, or emulator run.

## Best next task

Finish one honest native Ares certification pass before expanding features:

1. Start from a cold boot and play only through controller/keyboard input.
2. Capture the six required native 320×240 benchmark frames listed in [docs/VISUAL_BENCHMARK_CAPTURE_RUNBOOK.md](docs/VISUAL_BENCHMARK_CAPTURE_RUNBOOK.md).
3. Record route duration and failures using [docs/ARES_CERTIFICATION_RUNBOOK.md](docs/ARES_CERTIFICATION_RUNBOOK.md).
4. Re-run the readiness and final-acceptance audits.
5. Commit only source, documentation, and approved evidence. Never commit ROMs, credentials, local settings, caches, or unrelated files.

## Paste-ready continuation prompt

```text
/goal Continue the public n64game repository from HANDOFF.md. Treat docs/N64GAME_MASTER_SPEC.md as authoritative and keep the reduced polished 6–8 minute scope; do not restore the old 20-minute plan. First inspect git status, current public main, CI, HANDOFF.md, and the acceptance audits. Preserve all existing work and never commit ROMs, credentials, emulator settings, caches, or private files. Build and verify before changing code. Prioritize the smallest remaining release gate: complete an honest native Ares cold-boot playthrough and visual-benchmark evidence, then improve only issues proven by that run. Keep emulator and CI evidence distinct from physical-N64 certification. Commit intentional changes and push public main only after tests and public-hygiene checks pass.
```
