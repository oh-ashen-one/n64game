#!/usr/bin/env python3
"""Validate native/enlarged visual benchmark capture packets.

This is an evidence-preparation tool, not a visual approval tool. It accepts a
filled packet of six native 320x240 PNG captures and their six 1280x960 review
enlargements only when every enlargement is the exact decoded-pixel 4x nearest
neighbor expansion of its matching native image.
"""

from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import struct
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKET_SCHEMA = "n64game-visual-capture-packet-v1"
REPORT_SCHEMA = "n64game-visual-capture-evidence-v1"
CAPTURE_NAMES = (
    "exploration",
    "dialogue",
    "target_selection",
    "attack_anticipation",
    "impact",
    "support",
)
PLACEHOLDERS = ("TODO", "PENDING", "REPLACE", "NOT_CAPTURED", "TBD")
NATIVE_SIZE = (320, 240)
ENLARGED_SIZE = (1280, 960)
DEFAULT_PACKET = ROOT / "build" / "visual-benchmark" / "capture-packet.json"
DEFAULT_REPORT = ROOT / "build" / "reports" / "visual-capture-evidence.json"


class CapturePacketError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def reject_placeholders(value: Any, label: str = "packet") -> None:
    if isinstance(value, str):
        upper = value.upper()
        for placeholder in PLACEHOLDERS:
            if placeholder in upper:
                raise CapturePacketError(f"{label} contains placeholder text: {placeholder}")
        if not value.strip():
            raise CapturePacketError(f"{label} contains an empty string")
    elif isinstance(value, dict):
        for key, child in value.items():
            reject_placeholders(child, f"{label}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_placeholders(child, f"{label}[{index}]")


def require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CapturePacketError(f"{label} must be an object")
    return value


def resolve_artifact(path_value: Any, label: str, artifact_root: Path) -> Path:
    if not isinstance(path_value, str) or not path_value:
        raise CapturePacketError(f"{label} must be a repository-relative PNG path")
    path_fragment = Path(path_value)
    if path_value.startswith("/") or ".." in path_fragment.parts:
        raise CapturePacketError(f"{label} must be a safe repository-relative path")
    path = artifact_root / path_fragment
    if not path.is_file() or path.is_symlink():
        raise CapturePacketError(f"{label} is not one regular non-symlink file: {path_value}")
    if path.stat().st_size <= 0:
        raise CapturePacketError(f"{label} is empty: {path_value}")
    if path.suffix.lower() != ".png":
        raise CapturePacketError(f"{label} must end in .png: {path_value}")
    if path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        raise CapturePacketError(f"{label} is not a PNG file: {path_value}")
    return path


def paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def decode_png_rgba(path: Path, expected_size: tuple[int, int], label: str) -> tuple[int, int, bytes]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise CapturePacketError(f"{label} is not a PNG file")
    offset = 8
    width = height = bit_depth = color_type = None
    idat = bytearray()
    while offset < len(data):
        if offset + 12 > len(data):
            raise CapturePacketError(f"{label} has a truncated PNG chunk")
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        chunk_type = data[offset + 4:offset + 8]
        chunk_data = data[offset + 8:offset + 8 + length]
        crc_expected = struct.unpack(">I", data[offset + 8 + length:offset + 12 + length])[0]
        crc_actual = binascii.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        if crc_actual != crc_expected:
            raise CapturePacketError(f"{label} has invalid PNG chunk CRC")
        offset += 12 + length
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(">IIBBBBB", chunk_data)
            if compression != 0 or filter_method != 0 or interlace != 0:
                raise CapturePacketError(f"{label} uses unsupported PNG compression/filter/interlace settings")
        elif chunk_type == b"IDAT":
            idat.extend(chunk_data)
        elif chunk_type == b"IEND":
            break
    if width is None or height is None or bit_depth is None or color_type is None:
        raise CapturePacketError(f"{label} is missing IHDR")
    if (width, height) != expected_size:
        raise CapturePacketError(f"{label} dimensions {width}x{height} != {expected_size[0]}x{expected_size[1]}")
    if bit_depth != 8 or color_type not in (2, 6):
        raise CapturePacketError(f"{label} must be 8-bit RGB or RGBA PNG")
    channels = 4 if color_type == 6 else 3
    row_bytes = width * channels
    try:
        raw = zlib.decompress(bytes(idat))
    except zlib.error as exc:
        raise CapturePacketError(f"{label} has invalid PNG deflate data: {exc}") from exc
    stride = row_bytes + 1
    if len(raw) != stride * height:
        raise CapturePacketError(f"{label} decoded PNG data length is invalid")
    prior = bytearray(row_bytes)
    rgba = bytearray(width * height * 4)
    out_offset = 0
    for y in range(height):
        filter_type = raw[y * stride]
        scanline = bytearray(raw[y * stride + 1:y * stride + stride])
        if filter_type == 0:
            pass
        elif filter_type == 1:
            for i in range(row_bytes):
                left = scanline[i - channels] if i >= channels else 0
                scanline[i] = (scanline[i] + left) & 0xFF
        elif filter_type == 2:
            for i in range(row_bytes):
                scanline[i] = (scanline[i] + prior[i]) & 0xFF
        elif filter_type == 3:
            for i in range(row_bytes):
                left = scanline[i - channels] if i >= channels else 0
                up = prior[i]
                scanline[i] = (scanline[i] + ((left + up) // 2)) & 0xFF
        elif filter_type == 4:
            for i in range(row_bytes):
                left = scanline[i - channels] if i >= channels else 0
                up = prior[i]
                up_left = prior[i - channels] if i >= channels else 0
                scanline[i] = (scanline[i] + paeth(left, up, up_left)) & 0xFF
        else:
            raise CapturePacketError(f"{label} uses unsupported PNG filter {filter_type}")
        for x in range(width):
            source = x * channels
            rgba[out_offset:out_offset + 3] = scanline[source:source + 3]
            rgba[out_offset + 3] = scanline[source + 3] if channels == 4 else 255
            out_offset += 4
        prior = scanline
    return width, height, bytes(rgba)


def rgba_sha256(rgba: bytes) -> str:
    return hashlib.sha256(rgba).hexdigest()


def assert_exact_nearest_neighbor(native_rgba: bytes, enlarged_rgba: bytes, label: str) -> None:
    for y in range(NATIVE_SIZE[1]):
        for x in range(NATIVE_SIZE[0]):
            native_offset = ((y * NATIVE_SIZE[0]) + x) * 4
            expected = native_rgba[native_offset:native_offset + 4]
            base_x = x * 4
            base_y = y * 4
            for yy in range(base_y, base_y + 4):
                for xx in range(base_x, base_x + 4):
                    enlarged_offset = ((yy * ENLARGED_SIZE[0]) + xx) * 4
                    if enlarged_rgba[enlarged_offset:enlarged_offset + 4] != expected:
                        raise CapturePacketError(
                            f"{label} is not exact 4x nearest-neighbor at native({x},{y}) enlarged({xx},{yy})"
                        )


def template() -> dict[str, Any]:
    captures = {
        name: {
            "native_path": f"review/benchmark/evidence/native/{name}.png",
            "enlarged_path": f"review/benchmark/evidence/enlarged/{name}.png",
            "frame_index": "TODO_FRAME_INDEX",
            "notes": "TODO replace with real Ares native framebuffer capture and exact nearest-neighbor enlargement",
        }
        for name in CAPTURE_NAMES
    }
    return {
        "schema": PACKET_SCHEMA,
        "capture_request": "COMPLETE",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": {
            "ares_version": "v148",
            "capture_method": "TODO describe Ares screenshot or decoded representative frame source",
            "operator_id": "TODO_OPERATOR",
        },
        "captures": captures,
    }


def validate_packet(packet: dict[str, Any], artifact_root: Path) -> dict[str, Any]:
    if packet.get("schema") != PACKET_SCHEMA:
        raise CapturePacketError(f"packet.schema must be {PACKET_SCHEMA}")
    if packet.get("capture_request") != "COMPLETE":
        raise CapturePacketError("packet.capture_request must be COMPLETE")
    reject_placeholders(packet)

    captures = require_mapping(packet.get("captures"), "captures")
    missing = [name for name in CAPTURE_NAMES if name not in captures]
    extra = sorted(set(captures) - set(CAPTURE_NAMES))
    if missing:
        raise CapturePacketError("captures missing rows: " + ", ".join(missing))
    if extra:
        raise CapturePacketError("captures contains unexpected rows: " + ", ".join(extra))

    rows: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for name in CAPTURE_NAMES:
        row = require_mapping(captures[name], f"captures.{name}")
        native_path = resolve_artifact(row.get("native_path"), f"captures.{name}.native_path", artifact_root)
        enlarged_path = resolve_artifact(row.get("enlarged_path"), f"captures.{name}.enlarged_path", artifact_root)
        native_rel = display_path(native_path, artifact_root)
        enlarged_rel = display_path(enlarged_path, artifact_root)
        for rel in (native_rel, enlarged_rel):
            if rel in seen_paths:
                raise CapturePacketError(f"capture path is reused: {rel}")
            seen_paths.add(rel)

        _native_width, _native_height, native_rgba = decode_png_rgba(native_path, NATIVE_SIZE, f"captures.{name}.native")
        _enlarged_width, _enlarged_height, enlarged_rgba = decode_png_rgba(enlarged_path, ENLARGED_SIZE, f"captures.{name}.enlarged")
        assert_exact_nearest_neighbor(native_rgba, enlarged_rgba, f"captures.{name}.enlarged")

        rows.append(
            {
                "name": name,
                "frame_index": row.get("frame_index"),
                "native": {
                    "path": native_rel,
                    "sha256": sha256(native_path),
                    "rgba_sha256": rgba_sha256(native_rgba),
                    "width": NATIVE_SIZE[0],
                    "height": NATIVE_SIZE[1],
                    "media_type": "image/png",
                    "color_decode": "RGBA",
                },
                "enlarged": {
                    "path": enlarged_rel,
                    "sha256": sha256(enlarged_path),
                    "rgba_sha256": rgba_sha256(enlarged_rgba),
                    "width": ENLARGED_SIZE[0],
                    "height": ENLARGED_SIZE[1],
                    "media_type": "image/png",
                    "scale_factor": 4,
                    "resampler": "nearest-neighbor",
                    "derived_from_native": native_rel,
                },
            }
        )

    return {
        "schema": REPORT_SCHEMA,
        "result": "PASS",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": packet.get("source", {}),
        "capture_count": len(rows),
        "native": {
            "width": NATIVE_SIZE[0],
            "height": NATIVE_SIZE[1],
            "media_type": "image/png",
            "color_decode": "RGBA",
        },
        "enlarged": {
            "width": ENLARGED_SIZE[0],
            "height": ENLARGED_SIZE[1],
            "media_type": "image/png",
            "scale_factor": 4,
            "resampler": "nearest-neighbor",
        },
        "captures": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--artifact-root", type=Path, default=ROOT)
    parser.add_argument("--init-template", action="store_true", help="write a placeholder capture packet and exit")
    args = parser.parse_args()

    artifact_root = args.artifact_root if args.artifact_root.is_absolute() else ROOT / args.artifact_root
    packet = args.packet if args.packet.is_absolute() else ROOT / args.packet
    report = args.report if args.report.is_absolute() else ROOT / args.report

    if args.init_template:
        packet.parent.mkdir(parents=True, exist_ok=True)
        packet.write_text(json.dumps(template(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"result": "TEMPLATE_WRITTEN", "packet": display_path(packet, ROOT)}, sort_keys=True))
        return 0

    try:
        payload = json.loads(packet.read_text(encoding="utf-8"))
        report_payload = validate_packet(payload, artifact_root)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(report_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, CapturePacketError) as exc:
        print(f"VISUAL_CAPTURE_PACKET_ERROR: {exc}")
        return 1

    print(json.dumps({"result": "PASS", "report": display_path(report, ROOT), "capture_count": len(report_payload["captures"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
