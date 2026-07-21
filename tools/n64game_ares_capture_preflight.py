#!/usr/bin/env python3
"""Preflight Ares launch/capture readiness without claiming certification.

This tool is intentionally conservative. It can verify the current ROM/Ares
wrapper and, when asked, run a short launch probe that records whether Ares
stays alive long enough for a human/native capture attempt. It does not create
visual benchmark evidence and never promotes certification state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "build" / "game" / "n64game-gate3.z64"
RUN_ARES = ROOT / "scripts" / "run-ares"
SCREENSHOTS = Path.home() / "Library" / "Application Support" / "ares-v148-n64game" / "Screenshots"
N64_MAGIC = bytes.fromhex("80371240")


class PreflightError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rom_identity(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise PreflightError(f"ROM is not one regular file: {path}")
    data = path.read_bytes()
    if len(data) < 64 or data[:4] != N64_MAGIC:
        raise PreflightError(f"ROM has invalid N64 header magic: {path}")
    return {
        "path": str(path),
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "header_sha256": hashlib.sha256(data[:64]).hexdigest(),
    }


def run_check_only(root: Path, rom: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            str(root / "scripts" / "run-ares"),
            "--check-only",
            f"--expected-rom-sha256={sha256_file(rom)}",
            str(rom),
        ],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    parsed: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            parsed[key] = value
    return {
        "result": "PASS" if result.returncode == 0 else "FAIL",
        "returncode": result.returncode,
        "fields": parsed,
        "output_tail": result.stdout.splitlines()[-20:],
    }


def run_input_audit(root: Path) -> dict[str, Any]:
    result = subprocess.run(
        [str(root / "scripts" / "audit-ares-input"), "--strict"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"result": "INVALID", "raw": result.stdout}
    return {
        "result": payload.get("result", "INVALID") if result.returncode == 0 else "FAIL",
        "returncode": result.returncode,
        "payload": payload,
    }


def list_screenshots(path: Path) -> list[dict[str, Any]]:
    if not path.is_dir():
        return []
    rows = []
    for file in sorted(path.rglob("*")):
        if file.is_file() and not file.is_symlink():
            rows.append({
                "path": str(file),
                "size": file.stat().st_size,
                "mtime": int(file.stat().st_mtime),
            })
    return rows


def log_tail(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()[-40:]


def ares_window_snapshot() -> dict[str, Any]:
    swift_source = """
import Foundation
import CoreGraphics
let opts = CGWindowListOption(arrayLiteral: .optionOnScreenOnly, .excludeDesktopElements)
var rows: [[String: Any]] = []
if let windows = CGWindowListCopyWindowInfo(opts, kCGNullWindowID) as? [[String: Any]] {
    for w in windows {
        let owner = w[kCGWindowOwnerName as String] as? String ?? ""
        let name = w[kCGWindowName as String] as? String ?? ""
        if owner.lowercased().contains("ares") || name.lowercased().contains("ares") {
            let bounds = w[kCGWindowBounds as String] as? [String: Any] ?? [:]
            rows.append([
                "window_id": w[kCGWindowNumber as String] ?? 0,
                "owner": owner,
                "name": name,
                "bounds": bounds,
            ])
        }
    }
}
let data = try! JSONSerialization.data(withJSONObject: rows, options: [.sortedKeys])
print(String(data: data, encoding: .utf8)!)
"""
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".swift", delete=False, encoding="utf-8") as swift_file:
            swift_file.write(swift_source)
            swift_path = Path(swift_file.name)
        try:
            result = subprocess.run(
                ["swift", str(swift_path)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10,
                check=False,
            )
        finally:
            swift_path.unlink(missing_ok=True)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"result": "UNAVAILABLE", "windows": [], "error": str(exc)}
    if result.returncode != 0:
        return {"result": "UNAVAILABLE", "windows": [], "error": result.stdout.strip()}
    try:
        windows = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return {"result": "INVALID", "windows": [], "error": str(exc), "raw": result.stdout}
    return {
        "result": "VISIBLE" if windows else "NOT_VISIBLE",
        "windows": windows,
        "count": len(windows),
    }


def attempt_screenshot_hotkey(wait_seconds: float) -> dict[str, Any]:
    """Focus the Ares process and press the wrapper's screenshot hotkey.

    This is a capture attempt, not evidence promotion. macOS UI automation can
    fail or deliver no key event even when the Ares window is visible, so callers
    must still compare the screenshot directory before/after.
    """
    script = """
tell application "System Events"
  set frontmost of process "ares" to true
  delay 0.2
  key code 35
end tell
"""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=max(2.0, wait_seconds + 2.0),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "result": "UNAVAILABLE",
            "method": "macos-system-events-key-code-35",
            "key": "P",
            "error": str(exc),
        }
    return {
        "result": "SENT" if result.returncode == 0 else "FAILED",
        "method": "macos-system-events-key-code-35",
        "key": "P",
        "returncode": result.returncode,
        "output_tail": result.stdout.splitlines()[-10:],
    }


def launch_probe(
    root: Path,
    rom: Path,
    wait_seconds: float,
    keep_running: bool,
    attempt_hotkey: bool,
) -> dict[str, Any]:
    log_path = Path("/tmp") / f"n64game-ares-capture-preflight-{os.getpid()}.log"
    before = list_screenshots(SCREENSHOTS)
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [
                str(root / "scripts" / "run-ares"),
                "--homebrew-mode",
                f"--expected-rom-sha256={sha256_file(rom)}",
                str(rom),
            ],
            cwd=root,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            text=True,
        )
    time.sleep(wait_seconds)
    still_running = process.poll() is None
    windows = ares_window_snapshot() if still_running else {"result": "NOT_VISIBLE", "windows": [], "count": 0}
    hotkey_attempt = {
        "result": "NOT_RUN",
        "reason": "pass --attempt-screenshot-hotkey to focus Ares and press P after the launch probe",
    }
    if still_running and attempt_hotkey:
        hotkey_attempt = attempt_screenshot_hotkey(wait_seconds)
        time.sleep(max(0.5, min(wait_seconds, 3.0)))

    if still_running and not keep_running:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=2)
    after = list_screenshots(SCREENSHOTS)
    before_paths = {row["path"] for row in before}
    new_screenshots = [row for row in after if row["path"] not in before_paths]
    if still_running and keep_running:
        result = "RUNNING_NEEDS_MANUAL_CAPTURE"
    elif still_running:
        result = "LAUNCH_STAYED_ALIVE_TERMINATED_BY_PREFLIGHT"
    else:
        result = "ARES_EXITED_DURING_PROBE"
    return {
        "result": result,
        "pid": process.pid,
        "wait_seconds": wait_seconds,
        "kept_running": still_running and keep_running,
        "returncode": process.poll(),
        "log_path": str(log_path),
        "log_tail": log_tail(log_path),
        "window_probe": windows,
        "screenshot_dir": str(SCREENSHOTS),
        "hotkey_attempt": hotkey_attempt,
        "new_screenshot_count": len(new_screenshots),
        "new_screenshots": new_screenshots,
    }


def audit(root: Path, rom: Path, *, probe: bool, wait_seconds: float, keep_running: bool, attempt_hotkey: bool) -> dict[str, Any]:
    identity = rom_identity(rom)
    check = run_check_only(root, rom)
    input_audit = run_input_audit(root)
    launch = launch_probe(root, rom, wait_seconds, keep_running, attempt_hotkey) if probe else {
        "result": "NOT_RUN",
        "reason": "pass --probe-launch to test whether Ares remains alive for capture",
        "hotkey_attempt": {
            "result": "NOT_RUN",
            "reason": "launch probe was not run",
        },
    }
    failures = []
    warnings = []
    if check["result"] != "PASS":
        failures.append("scripts/run-ares --check-only failed")
    if input_audit["result"] != "PASS":
        failures.append("scripts/audit-ares-input --strict failed")
    if launch["result"] == "ARES_EXITED_DURING_PROBE":
        warnings.append("Ares exited during the launch probe before capture evidence could be produced")
    if launch.get("window_probe", {}).get("result") == "NOT_VISIBLE" and probe:
        warnings.append("launch probe did not expose a visible Ares window")
    if launch.get("new_screenshot_count", 0) == 0 and probe:
        if attempt_hotkey:
            warnings.append("screenshot hotkey attempt produced no files in the isolated Ares screenshot directory")
        else:
            warnings.append("launch probe produced no files in the isolated Ares screenshot directory")
    result = "FAIL" if failures else ("WARN_CAPTURE_NOT_READY" if warnings else "PASS")
    return {
        "schema": "n64game-ares-capture-preflight-v1",
        "result": result,
        "failures": failures,
        "warnings": warnings,
        "rom": identity,
        "check_only": check,
        "input_audit": input_audit,
        "launch_probe": launch,
        "next_actions": [
            "do not populate visual benchmark captures unless native 320x240 Ares/gameplay PNGs exist",
            "if launch_probe is ARES_EXITED_DURING_PROBE, run Ares interactively and capture the visible failure/log before retrying evidence capture",
            "use --probe-launch --attempt-screenshot-hotkey to record whether the bound Ares P hotkey creates files",
            "after native frames exist, fill build/visual-benchmark/capture-packet.json and run scripts/assemble-visual-benchmark-captures --generate-enlarged",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    return "\n".join([
        "# N64GAME Ares Capture Preflight",
        "",
        f"- Result: `{payload['result']}`",
        f"- ROM SHA-256: `{payload['rom']['sha256']}`",
        f"- Check-only: `{payload['check_only']['result']}`",
        f"- Input audit: `{payload['input_audit']['result']}`",
        f"- Launch probe: `{payload['launch_probe']['result']}`",
        f"- Ares window: `{payload['launch_probe'].get('window_probe', {}).get('result', 'NOT_RUN')}`",
        f"- Screenshot hotkey: `{payload['launch_probe'].get('hotkey_attempt', {}).get('result', 'NOT_RUN')}`",
        f"- New screenshots: `{payload['launch_probe'].get('new_screenshot_count', 0)}`",
        "",
        "## Warnings",
        "",
        *(f"- {warning}" for warning in payload["warnings"]),
        "",
        "This report is not certification evidence. It prevents stale input, bad ROM identity, or invisible/exiting Ares sessions from being mistaken for visual benchmark progress.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--rom", type=Path, default=ROM)
    parser.add_argument("--probe-launch", action="store_true")
    parser.add_argument("--wait-seconds", type=float, default=4.0)
    parser.add_argument("--keep-running", action="store_true")
    parser.add_argument(
        "--attempt-screenshot-hotkey",
        action="store_true",
        help="during --probe-launch, focus Ares with macOS System Events and press the wrapper-bound P screenshot hotkey",
    )
    parser.add_argument("--json-out", type=Path, default=ROOT / "build" / "reports" / "ares-capture-preflight.json")
    parser.add_argument("--md-out", type=Path, default=ROOT / "build" / "reports" / "ares-capture-preflight.md")
    args = parser.parse_args()

    root = args.root.resolve()
    rom = args.rom if args.rom.is_absolute() else root / args.rom
    try:
        payload = audit(
            root,
            rom.resolve(),
            probe=args.probe_launch,
            wait_seconds=args.wait_seconds,
            keep_running=args.keep_running,
            attempt_hotkey=args.attempt_screenshot_hotkey,
        )
    except (OSError, PreflightError) as exc:
        print(f"ARES_CAPTURE_PREFLIGHT_ERROR: {exc}")
        return 2
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return 1 if payload["result"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
