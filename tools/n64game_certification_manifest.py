#!/usr/bin/env python3
"""Assemble a fail-closed certification evidence manifest.

This helper computes the ROM, raw-log, and EEPROM hashes used by
``n64game_certification.py``. It does not certify a release. Without
``--validate`` it only creates a hash-bound manifest for captured Ares files.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import n64game_certification as certification  # noqa: E402


TIMING_PATHS = (("watched", "default"), ("skipped", "custom"))
SAVE_SCENARIOS = {"valid_resume", "latest_corrupt_fallback", "all_corrupt_new_game"}


class ManifestAssemblyError(ValueError):
    """The evidence inputs are unsafe, incomplete, or unsupported."""


def _reject_existing_symlink(path: Path, label: str) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise ManifestAssemblyError(f"{label} cannot be inspected: {path}") from exc
    if stat.S_ISLNK(info.st_mode):
        raise ManifestAssemblyError(f"{label} may not be a symlink: {path}")


def _require_safe_parent(path: Path, label: str) -> None:
    parent = path.parent
    if not parent.exists() or not parent.is_dir() or parent.is_symlink():
        raise ManifestAssemblyError(f"{label} parent must be an existing non-symlink directory")
    resolved_parent = parent.resolve(strict=True)
    current = resolved_parent.anchor
    probe = Path(current)
    for part in resolved_parent.parts[1:]:
        probe = probe / part
        if probe.is_symlink():
            raise ManifestAssemblyError(f"{label} parent may not traverse a symlink")


def _safe_relative_path(base: Path, raw: str, label: str, max_bytes: int) -> tuple[str, Path]:
    if not raw or any(ord(character) < 0x20 or ord(character) == 0x7F for character in raw):
        raise ManifestAssemblyError(f"{label} must be a non-empty printable relative path")
    pure = PurePosixPath(raw)
    if pure.is_absolute() or ".." in pure.parts or "." in pure.parts:
        raise ManifestAssemblyError(f"{label} must stay beneath the manifest directory")
    if any(not part for part in pure.parts):
        raise ManifestAssemblyError(f"{label} contains an empty path component")
    candidate = base.joinpath(*pure.parts)
    current = base
    for part in pure.parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except OSError as exc:
            raise ManifestAssemblyError(f"{label} is missing: {raw}") from exc
        if stat.S_ISLNK(mode):
            raise ManifestAssemblyError(f"{label} may not traverse a symlink: {raw}")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(base.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise ManifestAssemblyError(f"{label} escapes the manifest directory") from exc
    info = resolved.stat()
    if not stat.S_ISREG(info.st_mode):
        raise ManifestAssemblyError(f"{label} must be a regular file: {raw}")
    if info.st_size > max_bytes:
        raise ManifestAssemblyError(f"{label} exceeds {max_bytes} bytes: {raw}")
    return pure.as_posix(), resolved


def _require_rom(path: Path) -> Path:
    try:
        info = path.lstat()
    except OSError as exc:
        raise ManifestAssemblyError("ROM path is missing or malformed") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ManifestAssemblyError("ROM must be a non-symlink regular file")
    if info.st_size < 4096 or info.st_size > certification.MAX_ROM_BYTES or info.st_size % 4 != 0:
        raise ManifestAssemblyError("ROM is not a bounded big-endian N64 image")
    with path.open("rb") as stream:
        if stream.read(4) != b"\x80\x37\x12\x40":
            raise ManifestAssemblyError("ROM is not a bounded big-endian N64 image")
    return path


def _split_spec(value: str, count: int, label: str) -> list[str]:
    pieces = value.split(":")
    if len(pieces) != count or any(piece == "" for piece in pieces):
        raise ManifestAssemblyError(f"{label} must use exactly {count - 1} ':' separators")
    return pieces


def _require_id(value: str, label: str) -> str:
    if certification.TOKEN_VALUE.fullmatch(value) is None:
        raise ManifestAssemblyError(f"{label} must be a stable token")
    return value


def assemble(
    *,
    rom_path: Path,
    out_path: Path,
    timing_specs: list[str],
    soak_spec: str,
    save_specs: list[str],
) -> dict[str, Any]:
    out = Path(os.path.abspath(os.fspath(out_path)))
    _require_safe_parent(out, "manifest")
    _reject_existing_symlink(out, "manifest")
    base = out.parent
    rom = _require_rom(rom_path)
    rom_sha256 = certification._sha256(rom)
    if len(timing_specs) != 2:
        raise ManifestAssemblyError("exactly two --timing entries are required")
    if len(save_specs) != 3:
        raise ManifestAssemblyError("exactly three --save entries are required")

    ids: set[str] = set()
    log_paths: set[Path] = set()
    eeprom_paths: set[Path] = set()

    def claim_id(run_id: str) -> str:
        run_id = _require_id(run_id, "run id")
        if run_id in ids:
            raise ManifestAssemblyError(f"duplicate run id: {run_id}")
        ids.add(run_id)
        return run_id

    def claim_log(raw: str, label: str) -> tuple[str, str]:
        stored, path = _safe_relative_path(base, raw, label, certification.MAX_LOG_BYTES)
        if path in log_paths:
            raise ManifestAssemblyError(f"duplicate raw log path: {stored}")
        log_paths.add(path)
        return stored, certification._sha256(path)

    timing_runs: list[dict[str, Any]] = []
    for index, value in enumerate(timing_specs):
        run_id, slate_path, name_path, raw_log = _split_spec(value, 4, "--timing")
        expected_slate, expected_name = TIMING_PATHS[index]
        if (slate_path, name_path) != (expected_slate, expected_name):
            raise ManifestAssemblyError(
                f"--timing {index + 1} must declare {expected_slate}:{expected_name}"
            )
        log_path, log_sha256 = claim_log(raw_log, f"timing_runs[{index}].log_path")
        timing_runs.append({
            "id": claim_id(run_id),
            "log_path": log_path,
            "log_sha256": log_sha256,
            "slate_path": slate_path,
            "name_path": name_path,
            "cold_boot": True,
            "continue_used": False,
            "idle_declared_ms": 0,
        })

    soak_id, raw_warmup, raw_soak_log = _split_spec(soak_spec, 3, "--soak")
    try:
        warmup_loop_count = int(raw_warmup, 10)
    except ValueError as exc:
        raise ManifestAssemblyError("--soak warmup count must be 0 or 1") from exc
    if warmup_loop_count not in {0, 1}:
        raise ManifestAssemblyError("--soak warmup count must be 0 or 1")
    soak_log_path, soak_log_sha256 = claim_log(raw_soak_log, "soak_run.log_path")
    soak_run = {
        "id": claim_id(soak_id),
        "log_path": soak_log_path,
        "log_sha256": soak_log_sha256,
        "warmup_loop_count": warmup_loop_count,
    }

    save_runs: list[dict[str, Any]] = []
    scenarios: set[str] = set()
    for index, value in enumerate(save_specs):
        run_id, scenario, raw_log, raw_eeprom = _split_spec(value, 4, "--save")
        if scenario not in SAVE_SCENARIOS:
            raise ManifestAssemblyError(f"unsupported save scenario: {scenario}")
        if scenario in scenarios:
            raise ManifestAssemblyError(f"duplicate save scenario: {scenario}")
        scenarios.add(scenario)
        log_path, log_sha256 = claim_log(raw_log, f"save_runs[{index}].log_path")
        eeprom_path, eeprom = _safe_relative_path(
            base,
            raw_eeprom,
            f"save_runs[{index}].eeprom_path",
            certification.EEPROM_BYTES,
        )
        if eeprom in eeprom_paths:
            raise ManifestAssemblyError(f"duplicate EEPROM snapshot path: {eeprom_path}")
        if eeprom.stat().st_size != certification.EEPROM_BYTES:
            raise ManifestAssemblyError(f"EEPROM snapshot must be exactly 512 bytes: {eeprom_path}")
        eeprom_paths.add(eeprom)
        save_runs.append({
            "id": claim_id(run_id),
            "scenario": scenario,
            "log_path": log_path,
            "log_sha256": log_sha256,
            "eeprom_path": eeprom_path,
            "eeprom_sha256": certification._sha256(eeprom),
        })
    if scenarios != SAVE_SCENARIOS:
        missing = ", ".join(sorted(SAVE_SCENARIOS - scenarios))
        raise ManifestAssemblyError(f"save scenarios are incomplete: {missing}")

    return {
        "schema": certification.SCHEMA,
        "status": certification.STATUS,
        "rom_sha256": rom_sha256,
        "ares_sha256": certification.PINNED_ARES_SHA256,
        "timing_runs": timing_runs,
        "soak_run": soak_run,
        "save_runs": save_runs,
    }


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    text = json.dumps(manifest, indent=2, sort_keys=False) + "\n"
    path.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument(
        "--timing",
        action="append",
        default=[],
        metavar="ID:SLATE:NAME:LOG",
        help="add timing evidence; required order is watched/default then skipped/custom",
    )
    parser.add_argument(
        "--soak",
        required=True,
        metavar="ID:WARMUP_LOOP_COUNT:LOG",
        help="add ten-loop soak evidence",
    )
    parser.add_argument(
        "--save",
        action="append",
        default=[],
        metavar="ID:SCENARIO:LOG:EEPROM",
        help="add one save-recovery evidence row",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="run the strict certification validator after writing the manifest",
    )
    parser.add_argument(
        "--summary-md",
        type=Path,
        help="with --validate, write a Markdown validator summary",
    )
    arguments = parser.parse_args(argv)
    try:
        if arguments.summary_md is not None and not arguments.validate:
            raise ManifestAssemblyError("--summary-md requires --validate")
        manifest = assemble(
            rom_path=arguments.rom,
            out_path=arguments.out,
            timing_specs=arguments.timing,
            soak_spec=arguments.soak,
            save_specs=arguments.save,
        )
        write_manifest(arguments.out, manifest)
        validated = False
        validation_result: dict[str, Any] | None = None
        if arguments.validate:
            validation_result = certification.validate(arguments.out, arguments.rom)
            validated = True
            if arguments.summary_md is not None:
                certification._write_summary(arguments.summary_md, validation_result)
    except (OSError, ValueError) as exc:
        print(f"CERTIFICATION_MANIFEST_FAIL: {exc}", file=sys.stderr)
        return 1
    result: dict[str, Any] = {
        "result": "CERTIFICATION_MANIFEST_ASSEMBLED",
        "certification": "NOT_CLAIMED",
        "validated": validated,
        "manifest": os.fspath(arguments.out),
        "rom_sha256": manifest["rom_sha256"],
        "ares_sha256": manifest["ares_sha256"],
    }
    if validation_result is not None:
        result["validation_result"] = validation_result["result"]
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
