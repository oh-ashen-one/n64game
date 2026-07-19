# N64GAME

`n64game` is an original Nintendo 64 creature-battler being built with libdragon and Tiny3D. The locked target is a polished, complete 18–25 minute opening chapter with two cinematic 2v2 battles, two explorable locations, world-map travel, a companion-return sequence, saving/retries, and an original corruption mystery.

## Current status

**Toolchain — Gate 3: in progress. Gate 2 is complete.**

The exact libdragon, Tiny3D, CLI, container, Ares, and CI dependencies are now locked, with public gitlinks and stable build entry points under `scripts/`. The current ROM target is deliberately a Gate 3 toolchain/boot diagnostic, not the playable opening and not a full-game claim. Gate 3 remains open until a clean public-CI ROM artifact and a visually inspected Ares 148 boot are both recorded. Status claims are updated only after the corresponding output has been verified.

The authoritative production contract is [docs/N64GAME_MASTER_SPEC.md](docs/N64GAME_MASTER_SPEC.md). The reusable goal prompt is [docs/N64GAME_GOAL_PROMPT.md](docs/N64GAME_GOAL_PROMPT.md).

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

## Licensing

Original source code is licensed under the [MIT License](LICENSE). Original and generated non-code assets—including art, models, animation, audio, writing, characters, creature designs, and world content—are governed separately by [ASSET_LICENSE.md](ASSET_LICENSE.md) and are All Rights Reserved unless an asset-ledger entry explicitly says otherwise.

Third-party components retain their own licenses. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
