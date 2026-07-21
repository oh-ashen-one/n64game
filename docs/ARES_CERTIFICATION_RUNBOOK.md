# Ares v148 Certification Runbook

Status: certification capture plan, not a certification claim

Authority: `docs/N64GAME_MASTER_SPEC.md`

This runbook exists to produce the real evidence required by the Final Acceptance Checklist. It must not be used to mark certification complete until the emulator captures exist and `scripts/validate-certification-evidence` accepts a `COMPLETE` manifest.

## Current boundary

The pinned Ares binary and current ROM identity can be verified locally:

```sh
scripts/run-ares --check-only \
  --expected-rom-sha256="$(shasum -a 256 build/game/n64game-gate3.z64 | awk '{print $1}')" \
  build/game/n64game-gate3.z64
```

On 2026-07-21, that check passed with Ares v148 and SHA-256 `7a49f00f96a691458461d7c9cf453d95c0f5c054389bbd87c253987b8b6fa345`. The ROM was visible in Ares at the `RESONANCE IDENTITY` name-entry screen. Codex Computer Use key injection did not move the selector, so no timed emulator certification is claimed from that observation.

Before a manual run, add `dev.ares.ares` to macOS **System Settings → Privacy & Security → Input Monitoring**, restart Ares, click the game viewport, and confirm that the selector moves with arrows or WASD.

If keyboard input does not move the selector, audit the wrapper, isolated
settings file, and any already-running Ares process before recording evidence:

```sh
scripts/audit-ares-input
```

`PASS` means the launch path is using the expected SDL scancodes. A
`WARN_STALE_ARES_PROCESS` result means the repository wrapper is fixed but an
already-running emulator was launched with old bindings; quit Ares and relaunch
through `scripts/run-ares` before attempting a timed route. Use
`scripts/audit-ares-input --strict` when preparing certification so stale input
state fails the preflight instead of becoming a soft warning.

For the common “arrows/WASD do nothing because an older Ares process is still
open” case, run the explicit repair helper:

```sh
scripts/fix-ares-input
```

It repairs the isolated settings file, terminates only live Ares processes that
the audit identifies as launched with legacy n64game bindings, and then reruns
the strict audit. `scripts/run-ares` also performs this strict audit immediately
before launching a playable session, so stale input state blocks launch instead
of silently producing another broken certification attempt.

Before investing time in a visual/certification capture, run the capture
preflight:

```sh
scripts/audit-ares-capture-preflight --probe-launch
```

This verifies ROM identity, the guarded Ares wrapper, strict input bindings, and
whether a short Ares launch stays alive long enough for manual/native capture.
If it reports `ARES_EXITED_DURING_PROBE` or produces no screenshot/capture files,
do not fill visual benchmark packet rows from desktop screenshots or prose.
Resolve the interactive emulator visibility/capture problem first.

To make the preflight attempt the repository-bound capture key and record the
exact before/after screenshot result, run:

```sh
scripts/audit-ares-capture-preflight \
  --probe-launch \
  --attempt-screenshot-hotkey
```

The report distinguishes a visible Ares window, a sent `P` hotkey, and actual
new screenshot files. A visible window plus `hotkey_attempt: SENT` is still not
visual evidence when `new_screenshot_count` is `0`.

For Ares' menu-based capture path, use the explicit menu-capable capture mode:

```sh
scripts/audit-ares-capture-preflight \
  --probe-launch \
  --attempt-screenshot-menu
```

This launches through `scripts/run-ares --capture-session`, which omits `--kiosk`
only for capture diagnostics so Ares' **Tools → Capture Screenshot** menu exists.
It also forces a deterministic pixel-capture profile: fixed `320×240` window,
`FixedScale=1`, no shader, no color emulation, no interframe blending, no
overscan, no supersampling, `PixelAccuracy=true`, and
`DisableVideoInterfaceProcessing=true`. The preflight JSON records this profile
under `launch_probe.capture_pixel_profile`.

Older pre-profile captures on this Mac/Ares v148 setup produced screenshot
files under `Screenshots/Nintendo 64/`, but the observed image was `640×240`,
not native `320×240`. Treat those older files as diagnostic proof of Ares
capture reachability, not as visual benchmark packet members.

The current profile improved the failure mode: Ares logs a `320×240` output
buffer and the automatic preflight analyzer reports the new `640×240`
screenshot as border-only mismatch (`240` mismatching pairs, `0` interior
mismatches). That is still diagnostic-only; exact import remains disallowed
until every horizontal pair is byte-identical or a true native capture path is
found.

The isolated wrapper also binds Ares `Capture Screenshot` to `P`
(`Hotkey/CaptureScreenshot=0x1/0/35;;`) and sends screenshots to:

```text
~/Library/Application Support/ares-v148-n64game/Screenshots/
```

Treat the hotkey binding as readiness only. A capture attempt is evidence only
after a new image file actually appears in that isolated screenshot directory
and can be tied to the visible route state. If macOS automation or a menu/hotkey
attempt produces no file, leave the evidence row empty and record the blocker
instead of substituting a desktop/window screenshot.

## Launch command

```sh
scripts/run-ares --homebrew-mode \
  --expected-rom-sha256="$(shasum -a 256 build/game/n64game-gate3.z64 | awk '{print $1}')" \
  build/game/n64game-gate3.z64
```

Use `--capture-session` only for menu-based capture diagnostics; the ordinary
certification launch remains kiosk-controlled.

Keyboard mapping supplied by `scripts/run-ares`:

- Arrows or WASD: N64 D-pad and stick directions
- `X`: N64 `A`
- `Z`: N64 `B`
- `Space`: N64 `C-down` / Field Relay
- `Left Shift`: N64 `Z`
- `Return`: N64 `Start`
- `P`: Ares native screenshot hotkey, when the Ares process/window receives it

The wrapper forces Ares' native Quartz input driver and uses Ares keyboard
scancodes, not macOS virtual key codes: Up/Down/Left/Right are `82/81/80/79`,
and W/A/S/D are `26/4/22/7`.

## Required route for each timed playthrough

Record wall-clock start at cold boot and stop at the stable post-chapter menu after the beacon hook. Exclude idle time, but do not exclude ordinary reading, choosing, movement, or battle decision time.

1. Boot through the title/loading sequence.
2. Watch the `INSERT CUTSCENE HERE` slate for one run and skip it in the other run.
3. Confirm the default `ARI` name in one run and enter a custom 1–8 character uppercase name in the other.
4. Talk to Sera.
5. Examine the simulation ring.
6. Talk to Tavi.
7. Examine the atrium map.
8. Retrieve the Field Relay in the workshop.
9. Examine the workshop log.
10. Examine the overlook scope.
11. Open Field Relay with `Space` and inspect Party, Messages, Resonance, and Save.
12. Capture the Relay Save page. It prints the current route evidence line:
    `TIME mm:ss / CTRL mm:ss`, `STATE <scene> / <quest>`, and
    `EXAM n/4 RELAY n/4 <OPEN|HOOK>`. These values are derived from live ROM
    state and are suitable screenshot evidence for timing and route coverage.
    It also prints live certification telemetry: `FPS current/min`,
    `HEAP current/min/baseline`, and `FRAME microseconds / RES count`. These
    values come from libdragon `display_get_fps()`, `sys_get_heap_stats()`,
    hardware ticks, and the renderer's tracked resource owners. Capture this
    page during busy Annex traversal and after the battle so performance/heap
    evidence is tied to visible route state instead of operator prose.
13. Trigger a manual save from the Relay Save page.
14. Return to Sera and begin the trial.
15. Complete the Quarrune/Ayselor versus Gyreclast/Kivarrax 2v2 battle through legal commands.
16. Capture at least one alternate legal battle input path across the two runs.
17. Capture victory, reward, Annex return, and post-battle save behavior.
18. Trace the beacon at the overlook.
19. Verify `END OF OPENING CHAPTER` / stable post-chapter menu. Re-open the
    archive pages and, when returning to Annex through a supported path, capture
    the Save page again with `HOOK` and final timing/control values visible.

The two timed runs must each be 6–10 minutes, and their median must be 6–8 minutes. Each run must show at least four minutes of player control.

## Separate QA captures

The complete manifest also needs evidence for:

- default and custom name entry;
- slate watched and skipped;
- save, quit/reboot, and resume;
- battle victory;
- battle defeat then Retry;
- battle defeat then Return to Annex;
- legal and illegal `Horizon Break` states;
- rapid dialogue confirm/cancel;
- controller disconnect/reconnect during exploration, menu, dialogue, and battle;
- corrupted EEPROM fallback;
- completed-sector re-entry;
- stable post-chapter menu behavior.

## Transition soak and performance evidence

Run ten complete title/Annex/battle/end-card loops in Ares v148 Homebrew Mode. Record:

- loop count;
- starting and ending free heap;
- peak free heap, which must stay at or above 524,288 bytes;
- persistent heap delta, which must be zero;
- resource delta count, which must be zero;
- minimum FPS across required scenes, which must be at least 30;
- any sustained sub-30 windows, which must be zero.

The ROM exposes live FPS, free-heap, frame-time, and tracked-resource counters
on the Relay Save page. These on-screen counters are capture aids, not a
certification claim by themselves; the final manifest still needs the measured
two-run timing, ten-loop soak, QA matrix, and validator-accepted `COMPLETE`
evidence.

## Manifest workflow

Generate the current honest partial manifest:

```sh
scripts/create-certification-evidence-template
```

That writes `build/certification/evidence.json` with `certification: NOT_CLAIMED` and validates it. It is useful for audit transparency, but it does not satisfy final acceptance.

After real captures exist, replace the manifest with `certification: COMPLETE` and include the exact fields enforced by:

```sh
scripts/validate-certification-evidence \
  --manifest build/certification/evidence.json \
  --rom build/game/n64game-gate3.z64
```

Only a passing `COMPLETE` manifest may promote the Ares rows in `scripts/audit-final-acceptance`.

For a real completion attempt, first create the capture packet:

```sh
scripts/assemble-certification-evidence --init-template \
  --rom build/game/n64game-gate3.z64 \
  --packet build/certification/capture-packet.json
```

Then replace every placeholder in `build/certification/capture-packet.json` with
the two timed-run metrics, the ten-loop soak metrics, performance metrics, QA
row results, and repository-relative paths to the actual captured screenshots,
notes, or video-derived reports. Finally assemble and validate:

```sh
scripts/assemble-certification-evidence \
  --rom build/game/n64game-gate3.z64 \
  --packet build/certification/capture-packet.json \
  --manifest build/certification/evidence.json
```

The assembler fails closed on placeholder text, missing/empty artifact files,
bad ROM identity, wrong Ares identity, non-`PASS` QA rows, and any manifest that
`scripts/validate-certification-evidence` rejects.
