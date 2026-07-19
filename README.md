# N64GAME

`n64game` is an original Nintendo 64 creature-battler being built with libdragon and Tiny3D. The locked target is a polished, complete 18–25 minute opening chapter with two cinematic 2v2 battles, two explorable locations, world-map travel, a companion-return sequence, saving/retries, and an original corruption mystery.

## Current status

**Toolchain — Gate 3: verification in progress. Gate 2 is complete.**

The exact libdragon, Tiny3D, CLI, container, Ares, and CI dependencies are locked, with public gitlinks and stable build entry points under `scripts/`. Clean public CI and an audited local Docker-compatible engine now produce the same ROM bytes, and those exact bytes rendered advancing frames in pinned Ares 148; the audit is recorded in [docs/GATE3_BOOT_EVIDENCE.md](docs/GATE3_BOOT_EVIDENCE.md). The current ROM remains deliberately a Gate 3 diagnostic, not the playable opening and not a full-game claim. Gate 3 stays in verification because macOS still blocks Docker Desktop itself, which the master specification names literally; the Colima fallback is recorded without pretending it satisfied that final runtime requirement.

The authoritative production contract is [docs/N64GAME_MASTER_SPEC.md](docs/N64GAME_MASTER_SPEC.md). The reusable goal prompt is [docs/N64GAME_GOAL_PROMPT.md](docs/N64GAME_GOAL_PROMPT.md).

![Gate 3 diagnostic running in Ares v148](captures/gate3/ares-v148-ci-29674638989-frame-a.png)

This screenshot is the small Gate 3 diagnostic—not gameplay or representative production art. Its rotating Tiny3D solid proves the pinned render stack is alive; the `A` button toggles the diagnostic pulse state.

## Creative direction

The game uses an original retro desert-science-fiction setting:

- Creatures: **Echoforms**
- Team energy: **Resonance**
- Corrupted creatures: **Fractured** Echoforms
- Home: **Meridian Research Annex**
- Second destination: **Veyra Observatory Estate**

Pokémon XD: Gale of Darkness informs only the high-level pacing and functional rhythm of the opening. Pandemonium is an engineering and presentation reference. No Pokémon or Pandemonium code, characters, assets, maps, dialogue, music, UI, or protected expression may be copied into this project.

## Technical target

- Standard 4 MB Nintendo 64; no Expansion Pak requirement
- 320×240, 16-bit color, triple buffering, 30 FPS target
- libdragon preview and Tiny3D with exact dependency pins
- EEPROM4K saves
- Reproducible Docker-based builds
- Ares 148 Homebrew Mode as the first certification target
- Public CI-generated `.z64` and SHA-256 artifacts

The reproducible build contract and exact commands are documented in [docs/TOOLCHAIN.md](docs/TOOLCHAIN.md). Generated ROMs and reports stay under ignored `build/`; ROM binaries never enter normal Git history.

## Build and run the Gate 3 diagnostic

```sh
git clone --recurse-submodules https://github.com/oh-ashen-one/n64game.git
cd n64game
git lfs install && git lfs pull
npm ci --ignore-scripts
make validate
make rom && make test && make report
scripts/run-ares --homebrew-mode \
  --expected-rom-sha256="$(shasum -a 256 build/game/n64game-gate3.z64 | awk '{print $1}')" \
  build/game/n64game-gate3.z64
```

The build requires a working Docker-compatible engine; the production contract still names Docker Desktop, and Ares v148 Homebrew Mode is the certification target. See [the toolchain guide](docs/TOOLCHAIN.md) for exact versions, host checks, outputs, the successful audited fallback, and the remaining Docker Desktop blocker.

## Licensing

Original source code is licensed under the [MIT License](LICENSE). Original and generated non-code assets—including art, models, animation, audio, writing, characters, creature designs, and world content—are governed separately by [ASSET_LICENSE.md](ASSET_LICENSE.md) and are All Rights Reserved unless an asset-ledger entry explicitly says otherwise.

Third-party components retain their own licenses. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
