# Meridian Music Handoff

## Integrated development candidate

`Meridian Annex Drift` is now integrated as the user-selected development
candidate for `mus.annex_exploration`. It begins when the player enters the
Annex, continues at a lower level during the Resonance battle, and fades out
when leaving those scenes.

- Intended use: Meridian Research Annex exploration and dialogue
- Supplied source: 85.520167-second stereo 48 kHz MP3
- Derived loop: 68.080907-second mono 22.05 kHz PCM WAV
- Runtime form: deterministic looping Opus WAV64
- Runtime size: 295,040 bytes
- Mix priority: leave room for UI chirps, dialogue advance sounds, creature
  vocals, and later battle effects
- Runtime budget: 300 KiB maximum after conversion
- Provenance and exact transformation record:
  [`runtime-candidates/audio/mus.annex_exploration/PROVENANCE.md`](../runtime-candidates/audio/mus.annex_exploration/PROVENANCE.md)

The source is a compressed MP3 rather than a lossless master and the finished
loop is shorter than the eventual 100–140 second production target. Those are
known candidate limitations, not silently upgraded production claims.

## Suno prompt

Use Suno's instrumental mode. Put `[Instrumental]` in the lyrics field and use
this as the style prompt:

> Original seamless-loopable late-1990s console RPG exploration theme for a
> warm desert research outpost called Meridian Annex. Curious, protective, and
> quietly adventurous rather than epic. About 92 BPM, gently syncopated 4/4.
> Dry hand percussion, soft frame drum, woodblock, muted plucked strings,
> kalimba-like ceramic tones, dusty analog polysynth pads, low ventilation hum,
> tiny relay chirps, and occasional restrained bowed-metal resonance. Build the
> melody from a memorable four-note motif that passes between warm plucks and a
> breathy synth lead, with subtle braided counterpoint suggesting two creatures
> learning to work together. Sparse, tactile mix with clear midrange space for
> dialogue and game sound effects. Begin with a clean eight-bar establishment,
> settle into a steady explorable loop, add one gentle harmonic lift halfway
> through, then return naturally to the opening harmony with a clean tail that
> can be edited into a seamless 100–140 second loop. Instrumental only. No
> vocals, choir, lyrics, trailer impacts, EDM drop, trap hats, modern cinematic
> drums, distorted guitars, orchestral bombast, comedy, or imitation of any
> existing game soundtrack.

## Delivery checklist

1. Obtain a lossless Suno master if the project owner's account exposes one.
2. Confirm the generation account/plan grants the required commercial rights.
3. Complete a native Ares listening pass through exploration, dialogue, and
   battle at the committed fade levels.
4. Confirm the seam after at least two uninterrupted loops on native playback.
5. Revisit the mix when UI, creature, battle, and environmental SFX are added.
6. Promote the candidate only through the repository's normal audio gates.

The present integration is a hash-locked runtime candidate, not final audio
approval.
