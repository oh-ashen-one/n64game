#!/usr/bin/env python3
"""Generate the real Ares certification capture plan.

This plans the operator-facing capture package for the current ROM. It never
creates raw evidence, EEPROM snapshots, or certification claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import n64game_certification as certification  # noqa: E402
from tools import n64game_certification_saves as save_fixtures  # noqa: E402


SCHEMA = "n64game-certification-capture-plan-v1"


class CapturePlanError(ValueError):
    """The capture plan cannot be generated safely."""


def _require_regular_directory(path: Path, label: str) -> None:
    if path.exists():
        if path.is_symlink() or not path.is_dir():
            raise CapturePlanError(f"{label} must be a non-symlink directory: {path}")
    else:
        path.mkdir(parents=True)


def _require_writable_file_target(path: Path, label: str) -> None:
    if path.exists():
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise CapturePlanError(f"{label} must be a non-symlink regular file: {path}")
    parent = path.parent
    if not parent.exists() or parent.is_symlink() or not parent.is_dir():
        raise CapturePlanError(f"{label} parent must be an existing non-symlink directory")


def _require_rom(path: Path) -> Path:
    try:
        info = path.lstat()
    except OSError as exc:
        raise CapturePlanError("ROM path is missing or malformed") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise CapturePlanError("ROM must be a non-symlink regular file")
    if info.st_size < 4096 or info.st_size > certification.MAX_ROM_BYTES or info.st_size % 4 != 0:
        raise CapturePlanError("ROM is not a bounded big-endian N64 image")
    with path.open("rb") as stream:
        if stream.read(4) != b"\x80\x37\x12\x40":
            raise CapturePlanError("ROM is not a bounded big-endian N64 image")
    return path


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT).as_posix()
    except ValueError:
        return os.fspath(path)


def _shell_join(items: list[str]) -> str:
    import shlex

    return " ".join(shlex.quote(item) for item in items)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _run_ares_command(rom: str, rom_sha: str, log: str, *, eeprom_sha_placeholder: str | None = None) -> str:
    command = [
        "scripts/run-ares",
        "--homebrew-mode",
        f"--expected-rom-sha256={rom_sha}",
    ]
    if eeprom_sha_placeholder is not None:
        command.append(f"--expected-eeprom-sha256={eeprom_sha_placeholder}")
    command.append(rom)
    return f"{_shell_join(command)} 2>&1 | tee {log}"


def build_plan(rom_path: Path, out_dir: Path) -> dict[str, Any]:
    rom = _require_rom(rom_path)
    out = Path(os.path.abspath(os.fspath(out_dir)))
    _require_regular_directory(out, "capture root")
    _require_regular_directory(out / "logs", "log directory")
    _require_regular_directory(out / "saves", "save snapshot directory")
    rom_relative = _repo_relative(rom)
    out_relative = _repo_relative(out)
    rom_sha = certification._sha256(rom)
    timing_runs = [
        {
            "id": "timing-1",
            "kind": "timing",
            "slate_path": "watched",
            "name_path": "default",
            "log_path": "logs/timing-1.log",
            "operator_route": "Watch the INSERT CUTSCENE HERE slate, keep default ARI, complete one fresh 6-8 minute opening chapter with no intentional idle.",
        },
        {
            "id": "timing-2",
            "kind": "timing",
            "slate_path": "skipped",
            "name_path": "custom",
            "log_path": "logs/timing-2.log",
            "operator_route": "Skip the slate immediately, enter a custom 1-8 uppercase name, complete one fresh 6-8 minute opening chapter with no intentional idle.",
        },
    ]
    soak_run = {
        "id": "soak",
        "kind": "soak",
        "warmup_loop_count": 1,
        "log_path": "logs/soak.log",
        "operator_route": "In one uninterrupted Ares process, perform one labeled warm-up and exactly ten ANNEX -> BATTLE -> ANNEX loops without debug state mutation.",
    }
    input_run = {
        "id": "input-smoke",
        "kind": "input-smoke",
        "log_path": "logs/input-smoke.log",
        "operator_route": "Press arrows/WASD, Z, X, C, Space, and Return in visible in-game contexts to prove keyboard mappings reach the ROM.",
    }
    fixture_hashes = {
        scenario: _sha256_bytes(save_fixtures.eeprom_image(scenario))
        for scenario in save_fixtures.SCENARIOS
    }
    save_runs = [
        {
            "id": "valid_resume",
            "kind": "save-recovery",
            "scenario": "valid_resume",
            "log_path": "logs/valid_resume.log",
            "eeprom_path": "saves/valid_resume.eep",
            "eeprom_sha256": fixture_hashes["valid_resume"],
            "operator_route": "Boot from a preserved 512-byte valid prelaunch EEPROM snapshot and choose Continue once.",
        },
        {
            "id": "latest_corrupt_fallback",
            "kind": "save-recovery",
            "scenario": "latest_corrupt_fallback",
            "log_path": "logs/latest_corrupt_fallback.log",
            "eeprom_path": "saves/latest_corrupt_fallback.eep",
            "eeprom_sha256": fixture_hashes["latest_corrupt_fallback"],
            "operator_route": "Boot from a preserved 512-byte snapshot where the newest recognizable slot is corrupt and the older valid slot should resume.",
        },
        {
            "id": "all_corrupt_new_game",
            "kind": "save-recovery",
            "scenario": "all_corrupt_new_game",
            "log_path": "logs/all_corrupt_new_game.log",
            "eeprom_path": "saves/all_corrupt_new_game.eep",
            "eeprom_sha256": fixture_hashes["all_corrupt_new_game"],
            "operator_route": "Boot from a preserved 512-byte snapshot with recognizable corrupt N64GAME slots only and confirm it falls back to New Game.",
        },
    ]
    run_commands = []
    for run in [*timing_runs, soak_run, input_run]:
        run_commands.append({
            "id": run["id"],
            "command": _run_ares_command(
                rom_relative,
                rom_sha,
                f"{out_relative}/{run['log_path']}",
            ),
        })
    for run in save_runs:
        run_commands.append({
            "id": run["id"],
            "prepare_snapshot": (
                f"cp {out_relative}/{run['eeprom_path']} "
                "\"${N64GAME_ARES_STATE:-$HOME/Library/Application Support/ares-v148-n64game}\""
                f"/Saves/Nintendo\\ 64/{Path(rom_relative).stem}.eeprom"
            ),
            "command": _run_ares_command(
                rom_relative,
                rom_sha,
                f"{out_relative}/{run['log_path']}",
                eeprom_sha_placeholder=run["eeprom_sha256"],
            ),
        })
    fixture_command = (
        "scripts/prepare-certification-save-fixtures "
        f"--out-dir {out_relative}/saves"
    )
    assemble_command = (
        "scripts/assemble-certification-evidence "
        f"--rom {rom_relative} "
        f"--out {out_relative}/evidence.json "
        "--timing timing-1:watched:default:logs/timing-1.log "
        "--timing timing-2:skipped:custom:logs/timing-2.log "
        "--soak soak:1:logs/soak.log "
        "--save valid_resume:valid_resume:logs/valid_resume.log:saves/valid_resume.eep "
        "--save latest_corrupt_fallback:latest_corrupt_fallback:logs/latest_corrupt_fallback.log:saves/latest_corrupt_fallback.eep "
        "--save all_corrupt_new_game:all_corrupt_new_game:logs/all_corrupt_new_game.log:saves/all_corrupt_new_game.eep"
    )
    return {
        "schema": SCHEMA,
        "certification": "NOT_CLAIMED",
        "status": certification.STATUS,
        "rom_path": rom_relative,
        "rom_sha256": rom_sha,
        "ares_sha256": certification.PINNED_ARES_SHA256,
        "capture_root": out_relative,
        "runs": [*timing_runs, soak_run, input_run, *save_runs],
        "commands": run_commands,
        "pre_capture_commands": [
            {
                "id": "prepare-save-fixtures",
                "command": fixture_command,
            },
        ],
        "post_capture_commands": [
            {
                "id": "assemble",
                "command": assemble_command,
            },
            {
                "id": "validate-and-summarize",
                "command": (
                    f"{assemble_command} --validate "
                    f"--summary-md {out_relative}/evidence-summary.md"
                ),
            },
            {
                "id": "input-smoke-validate",
                "command": (
                    "scripts/validate-input-log "
                    f"--rom {rom_relative} "
                    f"--log {out_relative}/logs/input-smoke.log "
                    "--require up --require down --require left --require right "
                    "--require confirm --require cancel --require start --require pause --require relay"
                ),
            },
        ],
        "limitations": [
            "This plan creates no raw evidence and grants no certification.",
            "Every run still requires visible operator capture review.",
            "Save-recovery EEPROM snapshots must be preserved before launch and must be exactly 512 bytes.",
            "The final validator remains certification=NOT_CLAIMED until all external visual, audio, controller, and release checks pass.",
        ],
    }


def markdown_plan(plan: dict[str, Any]) -> str:
    lines = [
        "# N64GAME Ares Certification Capture Plan",
        "",
        f"- Certification: `{plan['certification']}`",
        f"- Status: `{plan['status']}`",
        f"- ROM: `{plan['rom_path']}`",
        f"- ROM SHA-256: `{plan['rom_sha256']}`",
        f"- Ares SHA-256: `{plan['ares_sha256']}`",
        f"- Capture root: `{plan['capture_root']}`",
        "",
        "This is an operator capture plan, not evidence and not release certification.",
        "",
        "## Required captures",
        "",
        "| Run | Kind | Output | Operator route |",
        "|---|---|---|---|",
    ]
    for run in plan["runs"]:
        output = run.get("log_path", "-")
        if "eeprom_path" in run:
            output = f"{output}; {run['eeprom_path']}"
        lines.append(f"| `{run['id']}` | `{run['kind']}` | `{output}` | {run['operator_route']} |")
    lines.extend([
        "",
        "## Pre-capture commands",
        "",
    ])
    for command in plan["pre_capture_commands"]:
        lines.append(f"### `{command['id']}`")
        lines.append("")
        lines.append("```sh")
        lines.append(command["command"])
        lines.append("```")
        lines.append("")
    lines.extend([
        "## Capture commands",
        "",
    ])
    for command in plan["commands"]:
        lines.append(f"### `{command['id']}`")
        lines.append("")
        if "prepare_snapshot" in command:
            lines.append("```sh")
            lines.append(command["prepare_snapshot"])
            lines.append("```")
            lines.append("")
            lines.append("This copies the deterministic prelaunch fixture into the isolated Ares save slot.")
            lines.append("")
        lines.append("```sh")
        lines.append(command["command"])
        lines.append("```")
        lines.append("")
    lines.extend([
        "## Post-capture commands",
        "",
    ])
    for command in plan["post_capture_commands"]:
        lines.append(f"### `{command['id']}`")
        lines.append("")
        lines.append("```sh")
        lines.append(command["command"])
        lines.append("```")
        lines.append("")
    lines.extend([
        "## Limitations",
        "",
    ])
    for limitation in plan["limitations"]:
        lines.append(f"- {limitation}")
    lines.append("")
    return "\n".join(lines)


def write_plan(plan: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    json_path = out_dir / "capture-plan.json"
    markdown_path = out_dir / "CAPTURE_PLAN.md"
    _require_writable_file_target(json_path, "capture-plan JSON")
    _require_writable_file_target(markdown_path, "capture-plan Markdown")
    json_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(markdown_plan(plan), encoding="utf-8")
    return json_path, markdown_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, default=ROOT / "build/game/n64game-gate3.z64")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "build/certification")
    arguments = parser.parse_args(argv)
    try:
        plan = build_plan(arguments.rom, arguments.out_dir)
        json_path, markdown_path = write_plan(plan, Path(os.path.abspath(os.fspath(arguments.out_dir))))
    except (OSError, ValueError) as exc:
        print(f"CERTIFICATION_CAPTURE_PLAN_FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({
        "result": "CERTIFICATION_CAPTURE_PLAN_READY",
        "certification": "NOT_CLAIMED",
        "plan_json": _repo_relative(json_path),
        "plan_markdown": _repo_relative(markdown_path),
        "rom_sha256": plan["rom_sha256"],
    }, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
