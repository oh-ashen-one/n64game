#!/usr/bin/env python3
"""Validate manual Ares input-edge evidence for N64GAME.

This is intentionally narrower than certification telemetry. It proves that a
raw Ares log is bound to the launched ROM and contains observed game-input edge
records emitted by the ROM. It does not certify timing, visual quality, or that
the operator completed the route without idle time.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import n64game_certification as certification


INPUT_PREFIX = "N64G_INPUT "
HEX_MASK = re.compile(r"[0-9a-f]{3}\Z")
UINT = re.compile(r"(0|[1-9][0-9]*)\Z")
SINT = re.compile(r"-?(0|[1-9][0-9]*)\Z")

BUTTON_MASKS = {
    "up": 0x001,
    "down": 0x002,
    "left": 0x004,
    "right": 0x008,
    "confirm": 0x010,
    "cancel": 0x020,
    "start": 0x040,
    "pause": 0x080,
    "relay": 0x100,
}


class InputLogError(ValueError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_regular_file(path: Path, label: str) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise InputLogError(f"{label} is missing: {path}") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise InputLogError(f"{label} must be a non-symlink regular file: {path}")


def parse_input_line(line: str) -> dict[str, str]:
    pieces = line.split(" ")
    if pieces[0] != "N64G_INPUT" or any(not piece for piece in pieces[1:]):
        raise InputLogError("input records must use exactly one ASCII space")
    fields: dict[str, str] = {}
    order: list[str] = []
    for token in pieces[1:]:
        if token.count("=") != 1:
            raise InputLogError(f"malformed input token: {token}")
        key, value = token.split("=", 1)
        if key in fields:
            raise InputLogError(f"duplicate input field: {key}")
        fields[key] = value
        order.append(key)
    expected = [
        "schema",
        "seq",
        "status",
        "wall_ticks",
        "submitted_frames",
        "scene",
        "pressed",
        "held",
        "stick_x",
        "stick_y",
    ]
    if order != expected:
        raise InputLogError("input record fields or order differ from schema 1")
    if fields["schema"] != "1" or fields["status"] != certification.STATUS:
        raise InputLogError("input record schema/status mismatch")
    for key in ("seq", "wall_ticks", "submitted_frames", "scene"):
        if UINT.fullmatch(fields[key]) is None:
            raise InputLogError(f"input field {key} must be unsigned decimal")
    for key in ("pressed", "held"):
        if HEX_MASK.fullmatch(fields[key]) is None:
            raise InputLogError(f"input field {key} must be a three-digit lowercase hex mask")
    for key in ("stick_x", "stick_y"):
        if SINT.fullmatch(fields[key]) is None:
            raise InputLogError(f"input field {key} must be signed decimal")
        value = int(fields[key], 10)
        if value < -128 or value > 127:
            raise InputLogError(f"input field {key} is outside int8 range")
    scene = int(fields["scene"], 10)
    if scene < 0 or scene > 5:
        raise InputLogError("input scene is outside the locked scene enum range")
    pressed = int(fields["pressed"], 16)
    held = int(fields["held"], 16)
    if pressed == 0 or pressed & ~0x1FF or held & ~0x1FF:
        raise InputLogError("input masks must be nonzero and stay inside the public input mask")
    if pressed & ~held:
        raise InputLogError("pressed inputs must also be held on the same frame")
    return fields


def validate(log_path: Path, rom_path: Path, required: list[str]) -> dict[str, object]:
    require_regular_file(log_path, "log")
    require_regular_file(rom_path, "ROM")
    rom_hash = sha256(rom_path)
    text = log_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    preamble = {
        "ares_version": certification.PINNED_ARES_VERSION,
        "ares_sha256": certification.PINNED_ARES_SHA256,
        "rom_sha256": rom_hash,
        "homebrew_mode": "true",
        "expansion_pak": "false",
        "defocus": "allow",
    }
    for key, expected in preamble.items():
        matches = [line for line in lines if line.startswith(f"{key}=")]
        if matches != [f"{key}={expected}"]:
            raise InputLogError(f"log must contain exactly one canonical {key} binding")
    records = [parse_input_line(line) for line in lines if line.startswith(INPUT_PREFIX)]
    if not records:
        raise InputLogError("log contains no N64G_INPUT records")
    for expected_sequence, record in enumerate(records):
        if int(record["seq"], 10) != expected_sequence:
            raise InputLogError("input sequence must begin at zero and be consecutive")
    observed_mask = 0
    for record in records:
        observed_mask |= int(record["pressed"], 16)
    required_mask = 0
    for name in required:
        try:
            required_mask |= BUTTON_MASKS[name]
        except KeyError as exc:
            raise InputLogError(f"unknown required input: {name}") from exc
    missing = [
        name for name, mask in BUTTON_MASKS.items()
        if required_mask & mask and not observed_mask & mask
    ]
    if missing:
        raise InputLogError(f"log is missing required input edge(s): {', '.join(missing)}")
    return {
        "result": "INPUT_LOG_PASS",
        "certification": "NOT_CLAIMED",
        "rom_sha256": rom_hash,
        "input_record_count": len(records),
        "observed_inputs": [
            name for name, mask in BUTTON_MASKS.items()
            if observed_mask & mask
        ],
        "required_inputs": required,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--rom", required=True, type=Path)
    parser.add_argument(
        "--require",
        action="append",
        choices=sorted(BUTTON_MASKS),
        default=[],
        help="Require at least one edge for this logical input.",
    )
    args = parser.parse_args()
    try:
        result = validate(args.log, args.rom, args.require)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"INPUT_LOG_FAIL: {exc}")
        return 1
    import json

    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
