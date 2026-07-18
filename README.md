# N64GAME

`n64game` is an original Nintendo 64 creature-battler being built with libdragon and Tiny3D. The locked target is a polished, complete 18–25 minute opening chapter with two cinematic 2v2 battles, two explorable locations, world-map travel, a companion-return sequence, saving/retries, and an original corruption mystery.

## Current status

**Preproduction — Gate 1: reference and legal audit.**

The repository does not contain a playable ROM yet. Current work is establishing the clean-room reference study, art direction, technical architecture, production inventory, licensing, reproducible toolchain, and evidence gates required before implementation. Status claims will be updated only when the corresponding output has been verified.

The authoritative production contract is [docs/N64GAME_MASTER_SPEC.md](docs/N64GAME_MASTER_SPEC.md). The reusable goal prompt is [docs/N64GAME_GOAL_PROMPT.md](docs/N64GAME_GOAL_PROMPT.md).

## Creative direction

The game uses an original retro desert-science-fiction setting:

- Creatures: **Echoforms**
- Team energy: **Resonance**
- Corrupted creatures: **Fractured** Echoforms
- Home: **Meridian Research Annex**
- Second destination: **Veyra Observatory Estate**

Pokémon XD: Gale of Darkness informs only the high-level pacing and functional rhythm of the opening. Pandemonium is an engineering and presentation reference. No Pokémon or Pandemonium code, characters, assets, maps, dialogue, music, UI, or protected expression may be copied into this project.

## Planned technical target

- Standard 4 MB Nintendo 64; no Expansion Pak requirement
- 320×240, 16-bit color, triple buffering, 30 FPS target
- libdragon preview and Tiny3D with exact dependency pins
- EEPROM4K saves
- Reproducible Docker-based builds
- Ares 148 Homebrew Mode as the first certification target
- Public CI-generated `.z64` and SHA-256 artifacts

Build and run instructions will be added after the pinned toolchain produces a verified clean ROM. Until then, this README intentionally does not provide speculative commands.

## Licensing

Original source code is licensed under the [MIT License](LICENSE). Original and generated non-code assets—including art, models, animation, audio, writing, characters, creature designs, and world content—are governed separately by [ASSET_LICENSE.md](ASSET_LICENSE.md) and are All Rights Reserved unless an asset-ledger entry explicitly says otherwise.

Third-party components retain their own licenses. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
