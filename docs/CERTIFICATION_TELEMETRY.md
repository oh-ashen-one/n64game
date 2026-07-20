# Current-ROM Certification Telemetry Contract

This is a bounded instrumentation contract for the reduced Meridian Annex ROM. It does not certify the ROM by itself. A build, host-test pass, telemetry line, or local Ares launch remains `INSTRUMENTATION_ONLY` until a complete evidence package binds the raw log and captures to the exact launched ROM SHA-256 and pinned Ares executable.

## Runtime line protocol

The ROM emits canonical single-line records through libdragon's emulator log channel. Every record begins with:

```text
N64G_TELEM schema=1 seq=<strictly-increasing-u32> event=<name> status=INSTRUMENTATION_ONLY
```

The current events are:

- `session`: guest tick frequency, 30 Hz budget, one-millisecond cadence tolerance, boot/ready ticks, and post-initialization heap baseline.
- `transition`: normal core or Continue-resume scene edge, guest wall tick, play/control-available ticks, current free heap, and global heap low-water.
- `summary`: cumulative submitted frames, measured frame intervals, over-budget intervals, rounded missed deadlines, maximum interval/streak, play/control-available ticks, and heap state. It is emitted every 300 submitted frames, not every frame.
- `chapter_stable`: first rendered post-chapter frame after the final EEPROM request has verified and the writer is idle. It includes boot-to-stable guest ticks, the final save sequence, frame counters, and heap low-water.

Frame intervals use pinned libdragon guest ticks rather than `display_get_fps()` or `display_get_delta_time()`, which are smoothed display estimates. The target budget is `ceil(ticks_per_second / 30)`. An interval is placed in the diagnostic over-budget bucket only after one extra millisecond, preventing normal NTSC cadence from becoming a false positive. Rounded missed deadlines and maximum consecutive over-budget streak remain separately visible; no threshold here silently grants a performance pass.

Heap statistics are sampled after initialization, once every 30 submitted frames, and immediately before transition, summary, or first `chapter_stable` records. They are not queried every rendered frame, so the instrumentation does not add a heap walk to the measured frame hot path.

`active_control_ticks` retains the current core meaning: a connected 30 Hz update during name entry, Annex non-dialogue control (including interactive menus), or a battle command/result choice. It is control-available time, not proof that a runner avoided idling. Timing evidence therefore also requires a no-idle first-playthrough run record.

The current core exposes the post-chapter menu before the asynchronous final save has verified. `chapter_stable` deliberately waits for that verification, but telemetry does not itself lock the already-visible menu. Final gameplay acceptance still requires a separate UI/state fix so post-chapter choices cannot act on an unresolved save; the event is not evidence that this behavior is already corrected.

## Hash binding and capture

Never embed the final ROM SHA-256 inside the same ROM; that creates a recursive self-hash. Use `scripts/run-ares`, which already computes and prints the exact ROM SHA-256 and pinned Ares SHA-256 before launch. Capture that preamble and the emulator log in one raw file under ignored `build/certification/`, then hash the raw log. A final evidence manifest must recompute the ROM and log hashes and reject a missing telemetry session, malformed sequence, mixed ROM hashes, or Ares mismatch.

## Two-run timing evidence schema

One evidence JSON object owns exactly two new-game runs of the same ROM/Ares tuple. Run 1 uses the watched slate and default-name path; run 2 uses the skipped slate and a custom name, covering both paths without widening scope. Each row records `raw_log_sha256`, `rom_sha256`, `ares_sha256`, `cold_boot=true`, `continue_used=false`, `idle_declared_ms=0`, `chapter_stable=true`, `final_save_verified=true`, `duration_ticks`, `ticks_per_second`, `play_ticks`, `active_control_ticks`, frame totals, and heap low-water.

The validator must enforce:

- each duration is 360–600 seconds;
- the even-sample median, defined as the arithmetic mean of the two durations, is 360–480 seconds;
- each run has at least 7,200 control-available ticks at 30 Hz;
- both runs end at `chapter_stable` with a newly verified save sequence;
- both raw logs and the recomputed ROM use one exact hash tuple.

## Ten-loop soak evidence schema

One uninterrupted Ares process records exactly ten measured `ANNEX -> BATTLE -> ANNEX` round trips after any separately labeled warm-up. Each loop binds its opening and closing transition sequence and records start, minimum, and end free-heap bytes plus frame counters. A loop may close through the existing defeat/Return-to-Annex path; no debug state mutation or certification shortcut is allowed.

The validator must reject anything other than ten ordered, non-overlapping loops, any invalid telemetry sample, a global free-heap low-water below 524,288 bytes, or any end-boundary free-heap reduction from the warmed baseline. Power-cycling between loops cannot prove absence of persistent loss and is not accepted as one soak session.

The older broad architecture document still contains superseded three-run/twenty-loop language. For this one-week release, the authoritative master specification requires two timing runs and ten loops.
