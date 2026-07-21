#!/usr/bin/env python3
"""Audit Ares v148 keyboard input bindings for certification readiness.

This is not controller certification. It verifies that the repository wrapper
uses the SDL scancode bindings needed for manual Ares certification, inspects
the isolated Ares settings file when present, and warns when a currently running
Ares process still appears to have legacy keyboard mappings from before the
wrapper fix.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUN_ARES = ROOT / "scripts" / "run-ares"
DEFAULT_STATE = Path.home() / "Library" / "Application Support" / "ares-v148-n64game"

EXPECTED_BINDINGS = {
    "Up": "0x1/0/82;0x1/0/26;",
    "Down": "0x1/0/81;0x1/0/22;",
    "Left": "0x1/0/80;0x1/0/4;",
    "Right": "0x1/0/79;0x1/0/7;",
    "X-Axis/Lo": "0x1/0/80;0x1/0/4;",
    "X-Axis/Hi": "0x1/0/79;0x1/0/7;",
    "Y-Axis/Lo": "0x1/0/81;0x1/0/22;",
    "Y-Axis/Hi": "0x1/0/82;0x1/0/26;",
    "B": "0x1/0/29;;",
    "A": "0x1/0/27;;",
    "C-Down": "0x1/0/44;;",
    "Z": "0x1/0/225;;",
    "Start": "0x1/0/40;;",
}

EXPECTED_HOTKEY_BINDINGS = {
    "CaptureScreenshot": "0x1/0/19;;",
}

EXPECTED_INPUT_DRIVER = "Quartz"

EXPECTED_EMPTY_GAMEPAD_BINDINGS = {
    "L-Up": ";;",
    "L-Down": ";;",
    "L-Left": ";;",
    "L-Right": ";;",
}

LEGACY_BINDING_FRAGMENTS = (
    "0x1/0/92;0x1/0/62",
    "0x1/0/93;0x1/0/58",
    "0x1/0/94;0x1/0/40",
    "0x1/0/95;0x1/0/43",
    "0x1/0/63;;",
    "0x1/0/65;;",
    "0x1/0/42;;",
    "0x1/0/98;;",
    "0x1/0/97;;",
)


def expected_settings_value(binding: str) -> str:
    if binding == ";;" or binding.endswith(";;"):
        return binding
    return f"{binding};"


def extract_port1_gamepad_bindings(text: str) -> dict[str, str]:
    match = re.search(
        r"(?ms)^    Controller\.Port\.1\n      Gamepad\n(?P<body>.*?)(?=^      Mouse\n)",
        text,
    )
    if match is None:
        return {}
    bindings: dict[str, str] = {}
    active_axis: str | None = None
    for raw_line in match.group("body").splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped in {"X-Axis", "Y-Axis"}:
            active_axis = stripped
            continue
        if ": " not in stripped:
            continue
        key, value = stripped.split(": ", 1)
        if active_axis in {"X-Axis", "Y-Axis"} and key in {"Lo", "Hi"}:
            bindings[f"{active_axis}/{key}"] = value
        else:
            active_axis = None
            bindings[key] = value
    return bindings


def display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def wrapper_audit(wrapper: Path) -> dict[str, Any]:
    text = wrapper.read_text(encoding="utf-8")
    missing = []
    expected_driver_setting = f"--setting Input/Driver={EXPECTED_INPUT_DRIVER}"
    if expected_driver_setting not in text:
        missing.append(expected_driver_setting)
    for control, binding in EXPECTED_BINDINGS.items():
        expected = f"Nintendo64/Input/Controller.Port.1/Gamepad/{control}={binding}"
        if expected not in text:
            missing.append(expected)
    for control in ("L-Up", "L-Down", "L-Left", "L-Right"):
        expected = f"Nintendo64/Input/Controller.Port.1/Gamepad/{control}=;;"
        if expected not in text and f"s/(\\n        {control}: )" not in text:
            missing.append(expected)
    for hotkey, binding in EXPECTED_HOTKEY_BINDINGS.items():
        expected = f"Hotkey/{hotkey}={binding}"
        if expected not in text and f"s/(\\n  {hotkey}: )" not in text:
            missing.append(expected)
    return {
        "path": display_path(wrapper, wrapper.parents[1]),
        "result": "PASS" if not missing else "FAIL",
        "missing_bindings": missing,
    }


def settings_audit(settings_file: Path) -> dict[str, Any]:
    if not settings_file.is_file() or settings_file.is_symlink():
        return {
            "path": str(settings_file),
            "present": False,
            "result": "MISSING",
            "notes": "run scripts/run-ares --check-only to create/repair isolated Ares settings",
        }
    text = settings_file.read_text(encoding="utf-8", errors="replace")
    missing = []
    legacy = []
    driver_match = re.search(r"(?m)^Input\n  Driver: (?P<driver>[^\n]+)$", text)
    input_driver = driver_match.group("driver") if driver_match is not None else None
    if input_driver != EXPECTED_INPUT_DRIVER:
        missing.append("Input/Driver")
    port1_bindings = extract_port1_gamepad_bindings(text)
    if port1_bindings:
        for control, binding in EXPECTED_BINDINGS.items():
            expected = expected_settings_value(binding)
            if port1_bindings.get(control) != expected:
                missing.append(control)
        for control, binding in EXPECTED_EMPTY_GAMEPAD_BINDINGS.items():
            if port1_bindings.get(control) != binding:
                missing.append(control)
    else:
        for control, binding in EXPECTED_BINDINGS.items():
            if binding not in text:
                missing.append(control)
        for control in EXPECTED_EMPTY_GAMEPAD_BINDINGS:
            missing.append(control)
    for hotkey, binding in EXPECTED_HOTKEY_BINDINGS.items():
        if f"{hotkey}: {binding}" not in text:
            missing.append(f"Hotkey/{hotkey}")
    for fragment in LEGACY_BINDING_FRAGMENTS:
        if fragment in text:
            legacy.append(fragment)
    return {
        "path": str(settings_file),
        "present": True,
        "result": "PASS" if not missing and not legacy else "STALE",
        "missing_controls": missing,
        "legacy_fragments": legacy,
        "input_driver": input_driver,
        "expected_input_driver": EXPECTED_INPUT_DRIVER,
        "port1_gamepad_bindings": port1_bindings,
    }


def read_process_snapshot(snapshot: Path | None) -> tuple[str, str | None]:
    if snapshot is not None:
        return snapshot.read_text(encoding="utf-8", errors="replace"), None
    try:
        result = subprocess.run(
            ["ps", "-axo", "pid,command"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    except OSError as exc:
        return "", str(exc)
    if result.returncode != 0:
        return "", result.stdout.strip() or f"ps exited {result.returncode}"
    return result.stdout, None


def process_audit(snapshot: Path | None) -> dict[str, Any]:
    text, error = read_process_snapshot(snapshot)
    if error is not None:
        return {
            "result": "UNAVAILABLE",
            "process_count": 0,
            "stale_processes": [],
            "error": error,
        }
    stale = []
    current = []
    unknown = []
    for line in text.splitlines():
        if "ares" not in line or "Nintendo64/Input/Controller.Port.1/Gamepad" not in line:
            continue
        if any(fragment in line for fragment in LEGACY_BINDING_FRAGMENTS):
            stale.append(line.strip())
        elif all(binding in line for binding in EXPECTED_BINDINGS.values()):
            current.append(line.strip())
        else:
            unknown.append(line.strip())
    return {
        "result": "STALE_RUNNING_PROCESS" if stale else "PASS",
        "process_count": len(stale) + len(current) + len(unknown),
        "current_processes": current,
        "stale_processes": stale,
        "unknown_processes": unknown,
    }


def process_id_from_snapshot_line(line: str) -> int | None:
    fields = line.strip().split(maxsplit=1)
    if not fields:
        return None
    try:
        return int(fields[0])
    except ValueError:
        return None


def terminate_stale_processes(
    root: Path,
    state_root: Path,
    process_snapshot: Path | None,
    *,
    timeout_seconds: float = 2.0,
) -> dict[str, Any]:
    if process_snapshot is not None:
        before = audit(root, state_root, process_snapshot)
        return {
            "attempted": False,
            "reason": "--terminate-stale is only available against live process state, not --process-snapshot fixtures",
            "terminated_pids": [],
            "before": before,
            "after": before,
        }

    before = audit(root, state_root, None)
    stale_lines = before["processes"].get("stale_processes", [])
    stale_pids = [
        pid for pid in (process_id_from_snapshot_line(line) for line in stale_lines)
        if pid is not None and pid != os.getpid()
    ]
    terminated: list[int] = []
    errors: list[str] = []
    for pid in stale_pids:
        try:
            os.kill(pid, signal.SIGTERM)
            terminated.append(pid)
        except ProcessLookupError:
            continue
        except PermissionError as exc:
            errors.append(f"{pid}: {exc}")
        except OSError as exc:
            errors.append(f"{pid}: {exc}")

    deadline = time.monotonic() + timeout_seconds
    after = audit(root, state_root, None)
    while after["processes"]["result"] == "STALE_RUNNING_PROCESS" and time.monotonic() < deadline:
        time.sleep(0.1)
        after = audit(root, state_root, None)

    return {
        "attempted": True,
        "terminated_pids": terminated,
        "errors": errors,
        "before": before,
        "after": after,
    }


def audit(root: Path, state_root: Path, process_snapshot: Path | None) -> dict[str, Any]:
    wrapper = wrapper_audit(root / "scripts" / "run-ares")
    settings = settings_audit(state_root / "settings.bml")
    processes = process_audit(process_snapshot)
    failures = []
    warnings = []
    if wrapper["result"] != "PASS":
        failures.append("scripts/run-ares is missing required Ares keyboard bindings")
    if settings["result"] == "STALE":
        warnings.append("isolated Ares settings file still contains stale or incomplete bindings")
    if processes["result"] == "STALE_RUNNING_PROCESS":
        warnings.append("a currently running Ares process was launched with stale keyboard bindings")
    result = "FAIL" if failures else ("WARN_STALE_ARES_PROCESS" if warnings else "PASS")
    return {
        "schema": "n64game-ares-input-audit-v1",
        "result": result,
        "failures": failures,
        "warnings": warnings,
        "wrapper": wrapper,
        "settings": settings,
        "processes": processes,
        "expected_bindings": EXPECTED_BINDINGS,
        "expected_empty_gamepad_bindings": EXPECTED_EMPTY_GAMEPAD_BINDINGS,
        "expected_hotkey_bindings": EXPECTED_HOTKEY_BINDINGS,
        "expected_input_driver": EXPECTED_INPUT_DRIVER,
        "remediation": [
            "quit any running Ares process that reports stale bindings",
            "run scripts/run-ares --check-only to repair the isolated settings file",
            "launch certification only through scripts/run-ares after the audit reports PASS or only nonblocking MISSING settings before first launch",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--state-root", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--process-snapshot", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--strict", action="store_true", help="return nonzero on stale-process warnings as well as failures")
    parser.add_argument(
        "--terminate-stale",
        action="store_true",
        help="send SIGTERM to live Ares processes launched with legacy n64game key bindings before reporting",
    )
    args = parser.parse_args()

    if args.terminate_stale:
        payload = terminate_stale_processes(args.root.resolve(), args.state_root, args.process_snapshot)
        result_payload = payload["after"]
    else:
        payload = audit(args.root.resolve(), args.state_root, args.process_snapshot)
        result_payload = payload
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    print(text, end="")
    if result_payload["result"] == "FAIL" or (args.strict and result_payload["result"] != "PASS"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
