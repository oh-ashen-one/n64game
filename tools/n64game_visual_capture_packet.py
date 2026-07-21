#!/usr/bin/env python3
"""Validate native/enlarged visual benchmark capture packets.

This is an evidence-preparation tool, not a visual approval tool. It accepts a
filled packet of six native 320x240 PNG captures and their six 1280x960 review
enlargements only when every enlargement is the exact decoded-pixel 4x nearest
neighbor expansion of its matching native image.

It can also generate the six 4x review enlargements from filled packet rows so
the reviewer packet does not depend on lossy desktop tools or manual scaling.
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
ARES_HORIZONTAL_DUPLICATE_SIZE = (640, 240)
ENLARGED_SIZE = (1280, 960)
DEFAULT_PACKET = ROOT / "build" / "visual-benchmark" / "capture-packet.json"
DEFAULT_REPORT = ROOT / "build" / "reports" / "visual-capture-evidence.json"
DEFAULT_ARES_ANALYSIS = ROOT / "build" / "reports" / "ares-640x240-capture-analysis.json"


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


def resolve_output_artifact(path_value: Any, label: str, artifact_root: Path, overwrite: bool) -> Path:
    if not isinstance(path_value, str) or not path_value:
        raise CapturePacketError(f"{label} must be a repository-relative PNG path")
    path_fragment = Path(path_value)
    if path_value.startswith("/") or ".." in path_fragment.parts:
        raise CapturePacketError(f"{label} must be a safe repository-relative path")
    if path_fragment.suffix.lower() != ".png":
        raise CapturePacketError(f"{label} must end in .png: {path_value}")
    path = artifact_root / path_fragment
    if path.is_symlink():
        raise CapturePacketError(f"{label} is a symlink and will not be overwritten: {path_value}")
    if path.exists():
        if not overwrite:
            raise CapturePacketError(f"{label} already exists; pass --overwrite-generated to replace it: {path_value}")
        if not path.is_file():
            raise CapturePacketError(f"{label} exists but is not a regular file: {path_value}")
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


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
    )


def encode_png_rgba(width: int, height: int, rgba: bytes) -> bytes:
    expected_len = width * height * 4
    if len(rgba) != expected_len:
        raise CapturePacketError(f"RGBA buffer length {len(rgba)} != {expected_len}")
    row_bytes = width * 4
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw.extend(rgba[y * row_bytes:(y + 1) * row_bytes])
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(bytes(raw), level=9))
        + png_chunk(b"IEND", b"")
    )


def enlarge_rgba_4x(native_rgba: bytes) -> bytes:
    expected_len = NATIVE_SIZE[0] * NATIVE_SIZE[1] * 4
    if len(native_rgba) != expected_len:
        raise CapturePacketError(f"native RGBA buffer length {len(native_rgba)} != {expected_len}")
    enlarged = bytearray(ENLARGED_SIZE[0] * ENLARGED_SIZE[1] * 4)
    for y in range(NATIVE_SIZE[1]):
        for x in range(NATIVE_SIZE[0]):
            source = ((y * NATIVE_SIZE[0]) + x) * 4
            pixel = native_rgba[source:source + 4]
            for yy in range(y * 4, y * 4 + 4):
                row_offset = yy * ENLARGED_SIZE[0] * 4
                for xx in range(x * 4, x * 4 + 4):
                    target = row_offset + xx * 4
                    enlarged[target:target + 4] = pixel
    return bytes(enlarged)


def derive_native_from_horizontal_duplicate(ares_rgba: bytes) -> bytes:
    expected_len = ARES_HORIZONTAL_DUPLICATE_SIZE[0] * ARES_HORIZONTAL_DUPLICATE_SIZE[1] * 4
    if len(ares_rgba) != expected_len:
        raise CapturePacketError(f"Ares RGBA buffer length {len(ares_rgba)} != {expected_len}")
    native = bytearray(NATIVE_SIZE[0] * NATIVE_SIZE[1] * 4)
    for y in range(NATIVE_SIZE[1]):
        for x in range(NATIVE_SIZE[0]):
            left_offset = ((y * ARES_HORIZONTAL_DUPLICATE_SIZE[0]) + (x * 2)) * 4
            right_offset = left_offset + 4
            left = ares_rgba[left_offset:left_offset + 4]
            right = ares_rgba[right_offset:right_offset + 4]
            if left != right:
                raise CapturePacketError(
                    "Ares 640x240 source is not exact horizontal 2x duplication "
                    f"at native({x},{y}) source columns {x * 2}/{x * 2 + 1}"
                )
            target = ((y * NATIVE_SIZE[0]) + x) * 4
            native[target:target + 4] = left
    return bytes(native)


def analyze_ares_horizontal_duplicate(
    source_path: Path,
    artifact_root: Path,
    *,
    border_native_pixels: int = 8,
    max_samples: int = 24,
) -> dict[str, Any]:
    _width, _height, ares_rgba = decode_png_rgba(
        source_path,
        ARES_HORIZONTAL_DUPLICATE_SIZE,
        "ares_source",
    )
    if border_native_pixels < 0:
        raise CapturePacketError("border_native_pixels must be non-negative")
    if border_native_pixels * 2 >= NATIVE_SIZE[0] or border_native_pixels * 2 >= NATIVE_SIZE[1]:
        raise CapturePacketError("border_native_pixels is too large for a 320x240 native frame")

    total_pairs = NATIVE_SIZE[0] * NATIVE_SIZE[1]
    mismatch_count = 0
    border_mismatch_count = 0
    interior_mismatch_count = 0
    max_channel_delta = 0
    delta_sum = 0
    first_mismatches: list[dict[str, Any]] = []
    row_mismatch_counts = [0 for _ in range(NATIVE_SIZE[1])]
    column_mismatch_counts = [0 for _ in range(NATIVE_SIZE[0])]

    for y in range(NATIVE_SIZE[1]):
        for x in range(NATIVE_SIZE[0]):
            left_offset = ((y * ARES_HORIZONTAL_DUPLICATE_SIZE[0]) + (x * 2)) * 4
            right_offset = left_offset + 4
            left = ares_rgba[left_offset:left_offset + 4]
            right = ares_rgba[right_offset:right_offset + 4]
            if left == right:
                continue
            deltas = [abs(left[index] - right[index]) for index in range(4)]
            pair_max = max(deltas)
            max_channel_delta = max(max_channel_delta, pair_max)
            delta_sum += sum(deltas[:3])
            mismatch_count += 1
            row_mismatch_counts[y] += 1
            column_mismatch_counts[x] += 1
            is_border = (
                x < border_native_pixels or
                x >= NATIVE_SIZE[0] - border_native_pixels or
                y < border_native_pixels or
                y >= NATIVE_SIZE[1] - border_native_pixels
            )
            if is_border:
                border_mismatch_count += 1
            else:
                interior_mismatch_count += 1
            if len(first_mismatches) < max_samples:
                first_mismatches.append(
                    {
                        "native_x": x,
                        "native_y": y,
                        "source_columns": [x * 2, x * 2 + 1],
                        "left_rgba": list(left),
                        "right_rgba": list(right),
                        "max_channel_delta": pair_max,
                    }
                )

    worst_rows = sorted(
        (
            {"native_y": y, "mismatches": count}
            for y, count in enumerate(row_mismatch_counts)
            if count
        ),
        key=lambda item: (-item["mismatches"], item["native_y"]),
    )[:8]
    worst_columns = sorted(
        (
            {"native_x": x, "mismatches": count}
            for x, count in enumerate(column_mismatch_counts)
            if count
        ),
        key=lambda item: (-item["mismatches"], item["native_x"]),
    )[:8]
    mismatch_ratio = mismatch_count / total_pairs
    return {
        "schema": "n64game-ares-640x240-capture-analysis-v1",
        "result": "PASS_EXACT_DUPLICATE" if mismatch_count == 0 else "FAIL_NOT_EXACT_DUPLICATE",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": display_path(source_path, artifact_root),
        "source_sha256": sha256(source_path),
        "source_rgba_sha256": rgba_sha256(ares_rgba),
        "dimensions": {
            "width": ARES_HORIZONTAL_DUPLICATE_SIZE[0],
            "height": ARES_HORIZONTAL_DUPLICATE_SIZE[1],
            "expected_derivation": "horizontal 2x exact duplicate of 320x240 native frame",
        },
        "pair_analysis": {
            "total_pairs": total_pairs,
            "matching_pairs": total_pairs - mismatch_count,
            "mismatching_pairs": mismatch_count,
            "mismatch_ratio": mismatch_ratio,
            "max_channel_delta": max_channel_delta,
            "mean_rgb_delta_per_mismatching_pair": (
                0.0 if mismatch_count == 0 else delta_sum / (mismatch_count * 3)
            ),
            "border_native_pixels": border_native_pixels,
            "border_mismatches": border_mismatch_count,
            "interior_mismatches": interior_mismatch_count,
            "mismatches_are_border_only": mismatch_count > 0 and interior_mismatch_count == 0,
        },
        "first_mismatches": first_mismatches,
        "worst_rows": worst_rows,
        "worst_columns": worst_columns,
        "exact_import_allowed": mismatch_count == 0,
        "approval_effect": "DIAGNOSTIC_ONLY_NOT_VISUAL_BENCHMARK_EVIDENCE",
    }


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


def require_capture_rows(packet: dict[str, Any]) -> dict[str, Any]:
    if packet.get("schema") != PACKET_SCHEMA:
        raise CapturePacketError(f"packet.schema must be {PACKET_SCHEMA}")
    if packet.get("capture_request") != "COMPLETE":
        raise CapturePacketError("packet.capture_request must be COMPLETE")

    captures = require_mapping(packet.get("captures"), "captures")
    missing = [name for name in CAPTURE_NAMES if name not in captures]
    extra = sorted(set(captures) - set(CAPTURE_NAMES))
    if missing:
        raise CapturePacketError("captures missing rows: " + ", ".join(missing))
    if extra:
        raise CapturePacketError("captures contains unexpected rows: " + ", ".join(extra))
    return captures


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


def generate_enlarged_images(packet: dict[str, Any], artifact_root: Path, overwrite: bool) -> list[dict[str, str]]:
    require_capture_rows(packet)
    reject_placeholders(packet)

    captures = require_mapping(packet.get("captures"), "captures")
    written: list[dict[str, str]] = []
    seen_outputs: set[str] = set()
    for name in CAPTURE_NAMES:
        row = require_mapping(captures[name], f"captures.{name}")
        native_path = resolve_artifact(row.get("native_path"), f"captures.{name}.native_path", artifact_root)
        output_path = resolve_output_artifact(
            row.get("enlarged_path"),
            f"captures.{name}.enlarged_path",
            artifact_root,
            overwrite,
        )
        output_rel = display_path(output_path, artifact_root)
        if output_rel in seen_outputs:
            raise CapturePacketError(f"generated enlarged path is reused: {output_rel}")
        seen_outputs.add(output_rel)
        _width, _height, native_rgba = decode_png_rgba(native_path, NATIVE_SIZE, f"captures.{name}.native")
        enlarged_rgba = enlarge_rgba_4x(native_rgba)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(encode_png_rgba(ENLARGED_SIZE[0], ENLARGED_SIZE[1], enlarged_rgba))
        written.append(
            {
                "name": name,
                "native": display_path(native_path, artifact_root),
                "enlarged": output_rel,
            }
        )
    return written


def import_ares_horizontal_duplicate(source_value: str, output_value: str, artifact_root: Path, overwrite: bool) -> dict[str, str]:
    source_path = resolve_artifact(source_value, "ares_source", artifact_root)
    output_path = resolve_output_artifact(output_value, "native_output", artifact_root, overwrite)
    _width, _height, ares_rgba = decode_png_rgba(
        source_path,
        ARES_HORIZONTAL_DUPLICATE_SIZE,
        "ares_source",
    )
    native_rgba = derive_native_from_horizontal_duplicate(ares_rgba)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(encode_png_rgba(NATIVE_SIZE[0], NATIVE_SIZE[1], native_rgba))
    return {
        "source": display_path(source_path, artifact_root),
        "source_sha256": sha256(source_path),
        "source_rgba_sha256": rgba_sha256(ares_rgba),
        "native": display_path(output_path, artifact_root),
        "native_sha256": sha256(output_path),
        "native_rgba_sha256": rgba_sha256(native_rgba),
        "derivation": "exact-horizontal-2x-duplicate-deinterleave",
    }


def validate_packet(packet: dict[str, Any], artifact_root: Path) -> dict[str, Any]:
    require_capture_rows(packet)
    reject_placeholders(packet)

    captures = require_mapping(packet.get("captures"), "captures")
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
    parser.add_argument("--generate-enlarged", action="store_true", help="generate exact 4x nearest-neighbor enlarged PNGs from packet native_path rows before validation")
    parser.add_argument("--analyze-ares-640x240", metavar="SOURCE", help="diagnose whether an Ares 640x240 PNG is exact horizontal 2x duplicate native evidence")
    parser.add_argument("--analysis-out", type=Path, default=DEFAULT_ARES_ANALYSIS, help="JSON report path for --analyze-ares-640x240")
    parser.add_argument("--analysis-border-native-pixels", type=int, default=8, help="native-pixel border width used only for diagnostic mismatch classification")
    parser.add_argument("--import-ares-640x240", metavar="SOURCE", help="derive one native 320x240 PNG from an Ares 640x240 screenshot only if every horizontal pixel pair is identical")
    parser.add_argument("--native-out", metavar="OUTPUT", help="repository-relative output path for --import-ares-640x240")
    parser.add_argument("--overwrite-generated", action="store_true", help="allow --generate-enlarged to replace existing enlarged_path PNGs")
    args = parser.parse_args()

    artifact_root = args.artifact_root if args.artifact_root.is_absolute() else ROOT / args.artifact_root
    packet = args.packet if args.packet.is_absolute() else ROOT / args.packet
    report = args.report if args.report.is_absolute() else ROOT / args.report
    analysis_out = args.analysis_out if args.analysis_out.is_absolute() else ROOT / args.analysis_out

    if args.init_template:
        packet.parent.mkdir(parents=True, exist_ok=True)
        packet.write_text(json.dumps(template(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"result": "TEMPLATE_WRITTEN", "packet": display_path(packet, ROOT)}, sort_keys=True))
        return 0

    if args.import_ares_640x240:
        if not args.native_out:
            print("VISUAL_CAPTURE_PACKET_ERROR: --native-out is required with --import-ares-640x240")
            return 1
        try:
            imported = import_ares_horizontal_duplicate(
                args.import_ares_640x240,
                args.native_out,
                artifact_root,
                args.overwrite_generated,
            )
        except (OSError, CapturePacketError) as exc:
            print(f"VISUAL_CAPTURE_PACKET_ERROR: {exc}")
            return 1
        print(json.dumps({"result": "PASS", **imported}, sort_keys=True))
        return 0

    if args.analyze_ares_640x240:
        try:
            source_path = resolve_artifact(args.analyze_ares_640x240, "ares_source", artifact_root)
            analysis = analyze_ares_horizontal_duplicate(
                source_path,
                artifact_root,
                border_native_pixels=args.analysis_border_native_pixels,
            )
            analysis_out.parent.mkdir(parents=True, exist_ok=True)
            analysis_out.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except (OSError, CapturePacketError) as exc:
            print(f"VISUAL_CAPTURE_PACKET_ERROR: {exc}")
            return 1
        print(json.dumps(
            {
                "result": analysis["result"],
                "analysis": display_path(analysis_out, ROOT),
                "exact_import_allowed": analysis["exact_import_allowed"],
                "mismatching_pairs": analysis["pair_analysis"]["mismatching_pairs"],
                "interior_mismatches": analysis["pair_analysis"]["interior_mismatches"],
            },
            sort_keys=True,
        ))
        return 0

    try:
        payload = json.loads(packet.read_text(encoding="utf-8"))
        generated: list[dict[str, str]] = []
        if args.generate_enlarged:
            generated = generate_enlarged_images(payload, artifact_root, args.overwrite_generated)
        report_payload = validate_packet(payload, artifact_root)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(report_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, CapturePacketError) as exc:
        print(f"VISUAL_CAPTURE_PACKET_ERROR: {exc}")
        return 1

    print(json.dumps(
        {
            "result": "PASS",
            "report": display_path(report, ROOT),
            "capture_count": len(report_payload["captures"]),
            "generated_enlarged_count": len(generated),
        },
        sort_keys=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
