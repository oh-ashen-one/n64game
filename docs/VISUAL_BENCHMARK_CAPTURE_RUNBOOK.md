# Visual Benchmark Capture Runbook

Status: capture-preparation workflow, not visual approval

The visual benchmark remains controlled by `docs/VISUAL_BENCHMARK_APPROVAL.md`.
This runbook only prepares the first concrete media evidence needed by
`ev.benchmark.native` and `ev.benchmark.enlarged`. Passing these commands does
not approve FAC-09 or FAC-10; it proves that the six named stills and their
review enlargements are structurally usable evidence.

## Capture packet

Create a placeholder packet:

```sh
scripts/assemble-visual-benchmark-captures --init-template \
  --packet build/visual-benchmark/capture-packet.json
```

Or use the guarded preparation helper, which first writes the current readiness
report, creates the default packet only when it is missing, and prints the exact
next capture/validation commands:

```sh
scripts/prepare-visual-benchmark-captures
```

Pass `--force` only when intentionally replacing the default template before it
contains real capture paths or observations.

Replace every placeholder with real repository-relative files and observations.
The six required capture names are exact:

- `exploration`
- `dialogue`
- `target_selection`
- `attack_anticipation`
- `impact`
- `support`

Each row needs:

- a native 320×240 PNG from the actual Ares/gameplay view;
- a 1280×960 PNG derived only by exact 4× nearest-neighbor enlargement;
- a non-placeholder `frame_index` or capture locator tying the still back to the
  representative capture plan;
- notes that describe what the frame proves.

Before filling packet rows from Ares, run:

```sh
scripts/audit-ares-capture-preflight \
  --probe-launch \
  --attempt-screenshot-menu
```

The menu path is currently the verified way to make Ares write screenshot files
from the local wrapper, but the observed Ares output is `640×240`. That proves
capture reachability only. Do not use those raw files directly as `native`
packet members.

If a `640×240` Ares screenshot is only exact horizontal 2× duplication of the
game's `320×240` framebuffer, derive the native packet member through the
fail-closed importer:

```sh
scripts/assemble-visual-benchmark-captures \
  --artifact-root "$PWD" \
  --import-ares-640x240 review/benchmark/evidence/ares-raw/exploration.png \
  --native-out review/benchmark/evidence/native/exploration.png
```

The importer decodes the source PNG and rejects it unless every horizontal
pixel pair `(2x, 2x+1)` is byte-identical for all 320×240 native positions. It
then writes a fresh `320×240` PNG and reports the source/native file hashes and
decoded RGBA hashes. A rejection means the screenshot is scaled, filtered,
aspect-corrected, or otherwise not a safe native-frame source; leave the packet
row empty and fix capture rather than downsampling by eye.

The existing 2026-07-21 Ares menu screenshots in the local isolated screenshot
directory were tested against this importer and rejected because their
horizontal pixel pairs were not exact duplicates. They remain diagnostic
capture-reachability artifacts only, not visual benchmark input.

After the native files and non-placeholder packet metadata are filled in, the
assembler can create the review enlargements deterministically:

```sh
scripts/assemble-visual-benchmark-captures \
  --packet build/visual-benchmark/capture-packet.json \
  --report build/reports/visual-capture-evidence.json \
  --generate-enlarged
```

This refuses to replace existing enlarged files unless
`--overwrite-generated` is passed. Use overwrite only when intentionally
regenerating review images from the same current native captures.

## Validation command

```sh
scripts/assemble-visual-benchmark-captures \
  --packet build/visual-benchmark/capture-packet.json \
  --report build/reports/visual-capture-evidence.json
```

The assembler fails closed on placeholder text, missing files, unsafe paths,
empty files, non-PNGs, wrong native/enlarged dimensions, duplicate capture
paths, unsupported PNG encodings, corrupt PNG data, and any enlarged image that
is not exact decoded-pixel 4× nearest-neighbor from its native source.

The report is a staging artifact for later benchmark registry work. It does not
populate `docs/VISUAL_BENCHMARK_APPROVAL.md`, does not authorize whitelist
rows, and does not replace non-owner visual review.
