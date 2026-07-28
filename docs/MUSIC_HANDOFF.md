# Meridian Music Handoff

## First cue to produce

Start with `mus.annex_exploration`. It covers the largest uninterrupted stretch
of the current opening and will improve the game more than a title sting or
ending cue.

- Intended use: Meridian Research Annex exploration and dialogue
- Target source duration: 100–140 seconds
- Runtime form: seamless looping mono asset, generally near 22.05 kHz
- Mix priority: leave room for UI chirps, dialogue advance sounds, creature
  vocals, and later battle effects
- Runtime budget: 300 KiB maximum after conversion

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

1. Export or download the highest-quality lossless master available.
2. Preserve that source outside the runtime directory and record its origin,
   creation date, and applicable usage rights.
3. Choose a musically stable 100–140 second section and make a sample-accurate
   loop; do not merely fade out.
4. Keep the master stereo, then derive the runtime mono version near 22.05 kHz.
5. Document loop start/end samples and any removed head or tail silence.
6. Test the converted asset beneath dialogue and battle/UI effects at native
   volume before committing it.

Do not add a generated file to the ROM until its provenance, loop, conversion,
and in-engine playback have been checked.
