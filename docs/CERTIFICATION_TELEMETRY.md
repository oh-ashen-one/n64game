# Current-ROM Certification Telemetry Contract

This is a bounded instrumentation contract for the reduced Meridian Annex ROM. It does not certify the ROM by itself. A build, host-test pass, telemetry line, or local Ares launch remains `INSTRUMENTATION_ONLY` until a complete evidence package binds the raw log and captures to the exact launched ROM SHA-256 and pinned Ares executable.

## Runtime line protocol

The ROM emits canonical single-line records through libdragon's emulator log channel. Every record begins with:

```text
N64G_TELEM schema=1 seq=<strictly-increasing-u32> event=<name> status=INSTRUMENTATION_ONLY
```

The current events are:

- `session`: guest tick frequency, 30 Hz budget, one-millisecond cadence tolerance, boot/ready ticks, and post-initialization heap baseline.
- `save_load`: one boot-time EEPROM outcome (`selected`, `none`, or `unavailable`), the full-decoder valid-slot mask, and the selected slot/sequence/checkpoint when one exists.
- `transition`: normal core or Continue-resume scene edge, guest wall tick, play/control-available ticks, current free heap, global heap low-water, global submitted/measured frame counters, and the aggregate invalid-sample count.
- `scene_summary`: cumulative frame counters for the scene being left. A final End Chapter record is emitted with the first stable chapter boundary. The latest record for a scene is its complete run-local total.
- `summary`: cumulative submitted frames, measured frame intervals, over-budget intervals, rounded missed deadlines, maximum interval/streak, play/control-available ticks, and heap state. It is emitted every 300 submitted frames, not every frame.
- `save_write`: only a terminal verified or failed write result, including the attempted slot/sequence when a write reached EEPROM, whether it is the chapter-completion save, and the encoded checkpoint.
- `chapter_stable`: first rendered post-chapter frame after the final EEPROM request has verified and the writer is idle. It includes boot-to-stable guest ticks, the final save sequence, frame counters, and heap low-water.

Frame intervals use pinned libdragon guest ticks rather than `display_get_fps()` or `display_get_delta_time()`, which are smoothed display estimates. The target budget is `ceil(ticks_per_second / 30)`. An interval is placed in the diagnostic over-budget bucket only after one extra millisecond, preventing normal NTSC cadence from becoming a false positive. Rounded missed deadlines and maximum consecutive over-budget streak remain separately visible; no threshold here silently grants a performance pass.

Heap statistics are sampled after initialization, once every 30 submitted frames, and immediately before transition, summary, or first `chapter_stable` records. They are not queried every rendered frame, so the instrumentation does not add a heap walk to the measured frame hot path.

The validator reconstructs the heap stream from the session baseline and every emitted low-water value. A low-water may never exceed the session baseline, increase over time, or exceed a simultaneously reported `free_heap_bytes`. The 524,288-byte floor applies to every bound session and low-water stream; reporting a high low-water beside a smaller free-heap sample fails closed.

`active_control_ticks` retains the current core meaning: a connected 30 Hz update during name entry, Annex non-dialogue control (including interactive menus), or a battle command/result choice. It is control-available time, not proof that a runner avoided idling. Timing evidence therefore also requires a no-idle first-playthrough run record.

## Hash binding and capture

Never embed the final ROM SHA-256 inside the same ROM; that creates a recursive self-hash. Use `scripts/run-ares`, which already computes and prints the exact ROM SHA-256 and pinned Ares SHA-256 before launch. Capture that preamble and the emulator log in one raw UTF-8 file under ignored `build/certification/`, then hash the raw log. The validator recomputes the explicit ROM, raw-log, and EEPROM hashes and rejects a missing telemetry session, malformed or nonconsecutive sequence, mixed ROM hashes, Ares mismatch, absolute/traversing paths, symlinks, duplicate JSON keys, unknown fields, and oversized evidence files.

Every save-recovery log must also contain exactly one prelaunch `eeprom_sha256=<lowercase-sha256>` line. That value must equal both the manifest's EEPROM hash and the recomputed hash of its 512-byte snapshot. Timing and soak rows do not accept an undeclared EEPROM preamble.

The manifest root uses exactly these keys:

```json
{
  "schema": "n64game-certification-evidence-v1",
  "status": "INSTRUMENTATION_ONLY",
  "rom_sha256": "<lowercase-sha256>",
  "ares_sha256": "<pinned-lowercase-sha256>",
  "timing_runs": [],
  "soak_run": {},
  "save_runs": []
}
```

Every evidence path is relative to the manifest directory. `timing_runs` contains exactly two objects with `id`, `log_path`, `log_sha256`, `slate_path`, `name_path`, `cold_boot`, `continue_used`, and `idle_declared_ms`. `soak_run` has `id`, `log_path`, `log_sha256`, and `warmup_loop_count` (zero or one). `save_runs` contains exactly one object per required save scenario with `id`, `scenario`, `log_path`, `log_sha256`, `eeprom_path`, and `eeprom_sha256`. No raw log, EEPROM image, or filled evidence manifest belongs in the repository.

Use the manifest assembler instead of hand-editing hash fields once the raw logs and preserved EEPROM snapshots exist under the ignored evidence directory. It computes every hash from disk, rejects absolute paths, `..` traversal, symlink traversal, duplicate run IDs, duplicate raw logs, duplicate EEPROM snapshots, wrong timing-path order, unsupported save scenarios, and non-512-byte EEPROM snapshots before a package can be passed to the validator.

```sh
mkdir -p build/certification/logs build/certification/saves

scripts/assemble-certification-evidence \
  --rom build/game/n64game-gate3.z64 \
  --out build/certification/evidence.json \
  --timing timing-1:watched:default:logs/timing-1.log \
  --timing timing-2:skipped:custom:logs/timing-2.log \
  --soak soak:1:logs/soak.log \
  --save valid_resume:valid_resume:logs/valid_resume.log:saves/valid_resume.eep \
  --save latest_corrupt_fallback:latest_corrupt_fallback:logs/latest_corrupt_fallback.log:saves/latest_corrupt_fallback.eep \
  --save all_corrupt_new_game:all_corrupt_new_game:logs/all_corrupt_new_game.log:saves/all_corrupt_new_game.eep
```

The assembler output is `CERTIFICATION_MANIFEST_ASSEMBLED` with `certification=NOT_CLAIMED`. Add `--validate --summary-md build/certification/evidence-summary.md` only after all captures are expected to pass the strict contract. A successful assembly without `--validate` is just a hash-bound manifest, not a release certification.

## Two-run timing evidence schema

One evidence JSON object owns exactly two new-game runs of the same ROM/Ares tuple. Run 1 declares the watched slate and default-name path; run 2 declares the skipped slate and a custom name, covering both paths without widening scope. The immutable raw log, rather than copied derived values in the manifest, is authoritative for duration, save outcome, frame totals, per-scene counters, and heap low-water. The declared input path and no-idle condition still require capture review; telemetry does not infer player intent.

The validator must enforce:

- each duration is 360–600 seconds;
- the even-sample median, defined as the arithmetic mean of the two durations, is 360–480 seconds;
- each run has at least 7,200 control-available ticks at 30 Hz;
- both runs end at `chapter_stable` with a newly verified save sequence;
- `duration_ticks` equals `chapter_stable.wall_ticks - session.boot_ticks` exactly;
- the final save sequence is positive, newer than every earlier verified write in the fresh run, and its matching verified chapter-completion `save_write` precedes `chapter_stable`;
- both raw logs and the recomputed ROM use one exact hash tuple.

## Ten-loop soak evidence schema

One uninterrupted Ares process records exactly ten measured `ANNEX -> BATTLE -> ANNEX` round trips after any separately labeled warm-up. Each loop binds its opening and closing transition sequence and records start, minimum, and end free-heap bytes plus frame counters. A loop may close through the existing defeat/Return-to-Annex path; no debug state mutation or certification shortcut is allowed.

The validator must reject anything other than ten ordered, non-overlapping loops, any invalid telemetry sample, a global free-heap low-water below 524,288 bytes, or any end-boundary free-heap reduction from the warmed baseline. Power-cycling between loops cannot prove absence of persistent loss and is not accepted as one soak session.

## Save recovery evidence

Three separate cold-boot logs bind the exact 512-byte prelaunch EEPROM image used by Ares:

- `valid_resume`: at least one structurally valid slot is selected and exactly one Continue-resume edge occurs.
- `latest_corrupt_fallback`: the recognizable newer slot has a bad checksum, the older structurally valid slot is selected, and exactly one Continue-resume edge occurs.
- `all_corrupt_new_game`: no slot has a valid checksum, at least one slot is recognizable as this save format, the load outcome is `none`, and no Continue-resume edge occurs.

An all-`FF` or empty image does not prove corruption recovery. The validator independently checks the `N64G` magic, version, slot size, sequence, and FNV-1a checksum and compares the result with `save_load`.

Before each save-recovery launch, place the exact 512-byte fixture at Ares's active isolated save path:

```text
$N64GAME_ARES_STATE/Saves/Nintendo 64/<rom-filename-without-extension>.eeprom
```

If `N64GAME_ARES_STATE` is unset, the wrapper uses its documented versioned default. Copy those prelaunch bytes into the ignored evidence directory, compute their SHA-256, and launch with the same expected value:

```sh
scripts/run-ares \
  --homebrew-mode \
  --expected-rom-sha256=<rom-sha256> \
  --expected-eeprom-sha256=<prelaunch-eeprom-sha256> \
  build/game/n64game-gate3.z64
```

The wrapper rejects a missing, symlinked, non-512-byte, or hash-mismatched active EEPROM before launch and emits the verified hash into the raw preamble. The preserved manifest snapshot, not the save file Ares may modify during play, is the validator input.

## Validator command and result

Run only against an explicit manifest and ROM:

```sh
make certification-check \
  CERTIFICATION_MANIFEST=build/certification/evidence.json \
  CERTIFICATION_ROM=build/game/n64game-gate3.z64
```

A successful result is `EVIDENCE_CONTRACT_PASS` with `certification=NOT_CLAIMED`. It means the package is internally consistent with this bounded contract. It does not grant performance, visual, audio, controller, hardware, or overall game certification. CI runs `make test-certification` against synthetic death fixtures only; it never manufactures or substitutes release evidence.

To create a human-readable release-evidence attachment from the same strict pass, ask the validator to write a Markdown summary:

```sh
scripts/validate-certification-evidence \
  --manifest build/certification/evidence.json \
  --rom build/game/n64game-gate3.z64 \
  --summary-md build/certification/evidence-summary.md
```

The summary is derived after validation, includes the ROM/Ares hashes, two timing durations, arithmetic mean, soak-loop count, heap low-water, save-recovery outcomes, and the validator limitations. It is still `certification=NOT_CLAIMED`; it exists so release notes do not depend on hand-copied telemetry numbers.

The older broad architecture document still contains superseded three-run/twenty-loop language. For this one-week release, the authoritative master specification requires two timing runs and ten loops.

## Manual input-edge evidence

The timing/soak validator intentionally does not infer operator intent from the route. For the keyboard/controller acceptance pass, the ROM also emits separate input-edge records:

```text
N64G_INPUT schema=1 seq=<strictly-increasing-u32> status=INSTRUMENTATION_ONLY wall_ticks=<ticks> submitted_frames=<frames> scene=<scene> pressed=<hex-mask> held=<hex-mask> stick_x=<signed-int8> stick_y=<signed-int8>
```

`N64G_INPUT` is not parsed as certification telemetry and does not certify a run by itself. It is a manual-Ares proof aid for showing that the pinned wrapper's keyboard/controller mappings reached the ROM. Directional arrows and `WASD` should produce `up`, `down`, `left`, or `right` edges; `Z`, `X`, Return, Space, and `C` should produce confirm, cancel, start, pause, and Relay edges according to the wrapper map.

After capturing a raw Ares log with the same preamble produced by `scripts/run-ares`, validate the input subset explicitly:

```sh
scripts/validate-input-log \
  --rom build/game/n64game-gate3.z64 \
  --log build/certification/input-smoke.log \
  --require up --require down --require left --require right \
  --require confirm --require cancel --require start --require pause --require relay
```

A pass returns `INPUT_LOG_PASS` with `certification=NOT_CLAIMED`. It proves only that those logical input edges appeared in a ROM/Ares-bound log; capture review is still required to prove the operator used them in the expected on-screen contexts.
