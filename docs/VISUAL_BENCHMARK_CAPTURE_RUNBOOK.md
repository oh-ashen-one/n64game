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
