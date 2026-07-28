# Meridian Annex Drift — Candidate Provenance

Status: `SOURCE_CANDIDATE_NOT_GATE_EVIDENCE`

This is the user-selected development candidate for
`mus.annex_exploration`. It is not a production-approval or commercial-rights
claim.

## Supplied source

- File: `meridian_annex_drift.mp3`
- Supplied by the project owner on 2026-07-27 America/New_York
- Embedded title: `Meridian Annex Drift`
- Embedded artist: `notashenone`
- Embedded generator: Suno
- Embedded creation time: `2026-07-28T02:28:43.056062Z`
- Embedded generation ID: `e41f570b-e91d-465a-9dd6-a2200456e9c0`
- Source format: MP3, stereo, 48,000 Hz
- Source duration: 85.520167 seconds
- Source SHA-256:
  `fb24af3f10009ec94e30093694b2ec1b80fca5258d0f649595d8482e608f53e3`

The project owner explicitly instructed this repository to use the supplied
track. Before commercial distribution, the owner must separately confirm that
the Suno account and plan used for this generation grant the needed rights.

## Derived loop

- File: `mus_annex_exploration.wav`
- Format: signed 16-bit PCM WAV, mono, 22,050 Hz
- Duration: 68.080907 seconds
- Integrated loudness: approximately -17.4 LUFS
- True peak: -3.0 dBFS
- SHA-256:
  `866bb1856e31ee31ccdd1d62839ab424a0372906b006e2dddd71aa75bbc41239`

FFmpeg 8.1.2 performed the transformation:

1. Downmix stereo equally to mono and resample to 22,050 Hz.
2. Use beat-aligned source points 11.84217687–13.74621315 seconds as the loop
   head and 79.92308390–81.82712018 seconds as the loop tail.
3. Apply a 1.90403628-second linear crossfade between tail and head.
4. Place the uninterrupted 13.74621315–79.92308390-second body before the
   seam, so the rendered endpoint returns to the rendered starting moment.
5. Apply loudness normalization targeting -18 LUFS, LRA 7, and -3 dBTP.

The loop-boundary sample step is 0.032685, about 25.6% of the source's 99th
percentile internal adjacent-sample step; the 250 ms edge-RMS delta is
0.003269.

## Runtime conversion

Pinned libdragon `audioconv64` converts the derived WAV with:

```text
--wav-mono --wav-resample 22050 --wav-compress 3 --wav-loop true
```

The deterministic development output is a 295,040-byte looping Opus WAV64
with SHA-256
`1e4def610d630060f77f167f0a20f22df525e76088f6a284fb24158838b29176`.
The ROM build verifies both this digest and the 300 KiB runtime cap.
