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

## Launch command

```sh
scripts/run-ares --homebrew-mode \
  --expected-rom-sha256="$(shasum -a 256 build/game/n64game-gate3.z64 | awk '{print $1}')" \
  build/game/n64game-gate3.z64
```

Keyboard mapping supplied by `scripts/run-ares`:

- Arrows or WASD: N64 D-pad and stick directions
- `Z`: N64 `A`
- `X`: N64 `B`
- `C`: N64 `C-down` / Field Relay
- `Return`: N64 `Start`
- `Space`: N64 `Z`

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
11. Open Field Relay with `C` and inspect Party, Messages, Resonance, and Save.
12. Trigger a manual save from the Relay Save page.
13. Return to Sera and begin the trial.
14. Complete the Quarrune/Ayselor versus Gyreclast/Kivarrax 2v2 battle through legal commands.
15. Capture at least one alternate legal battle input path across the two runs.
16. Capture victory, reward, Annex return, and post-battle save behavior.
17. Trace the beacon at the overlook.
18. Verify `END OF OPENING CHAPTER` / stable post-chapter menu.

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

If the ROM cannot yet expose FPS/heap counters during an Ares run, do not invent them. Add or enable a real telemetry display/log first, then repeat the capture.

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
