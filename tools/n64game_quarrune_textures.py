#!/usr/bin/env python3
"""Author Quarrune's three source texture candidates deterministically.

This is an authoring tool, not a runtime converter.  It writes final-dimension,
explicit-palette PNG inputs so the pinned libdragon `mksprite` step never has to
invent colors, resize, dither, or choose a layout.  The 64x64 body atlas is split
into two independently usable 64x32 regions: ceramic plates above and flexible
joint/foot surfaces below.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import struct
import sys
import zlib
from pathlib import Path
from typing import Sequence


BODY_NAME = "tex_quarrune_body_ci8_64x64.png"
ACCENT_NAME = "tex_quarrune_accent_ci4_32x32.png"
SHADOW_NAME = "tex_quarrune_blob_shadow_ia8_32x32.png"


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    if len(kind) != 4:
        raise ValueError("PNG chunk type must be four bytes")
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def write_indexed_png(
    path: Path,
    width: int,
    height: int,
    palette: Sequence[tuple[int, int, int]],
    indices: Sequence[int],
) -> None:
    if not 1 <= len(palette) <= 256:
        raise ValueError("indexed PNG palette must contain 1..256 colors")
    if len(indices) != width * height:
        raise ValueError("indexed PNG pixel census mismatch")
    if any(index < 0 or index >= len(palette) for index in indices):
        raise ValueError("indexed PNG contains an out-of-palette index")
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        rows.extend(indices[y * width : (y + 1) * width])
    header = struct.pack(">IIBBBBB", width, height, 8, 3, 0, 0, 0)
    palette_bytes = bytes(channel for color in palette for channel in color)
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"PLTE", palette_bytes)
        + png_chunk(b"IDAT", zlib.compress(bytes(rows), level=9))
        + png_chunk(b"IEND", b"")
    )
    path.write_bytes(payload)


def write_gray_alpha_png(
    path: Path,
    width: int,
    height: int,
    pixels: Sequence[tuple[int, int]],
) -> None:
    if len(pixels) != width * height:
        raise ValueError("grayscale-alpha PNG pixel census mismatch")
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for intensity, alpha in pixels[y * width : (y + 1) * width]:
            rows.extend((intensity, alpha))
    header = struct.pack(">IIBBBBB", width, height, 8, 4, 0, 0, 0)
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(bytes(rows), level=9))
        + png_chunk(b"IEND", b"")
    )
    path.write_bytes(payload)


def gradient_palette(stops: Sequence[tuple[int, int, int]], count: int) -> list[tuple[int, int, int]]:
    if count < 2 or len(stops) < 2:
        raise ValueError("palette gradient requires at least two colors and entries")
    colors: list[tuple[int, int, int]] = []
    segments = len(stops) - 1
    for index in range(count):
        position = index * segments / (count - 1)
        segment = min(int(position), segments - 1)
        amount = position - segment
        start = stops[segment]
        end = stops[segment + 1]
        color = tuple(
            max(0, min(255, round(start[channel] * (1.0 - amount) + end[channel] * amount)))
            for channel in range(3)
        )
        if colors and color == colors[-1]:
            mutable = list(color)
            mutable[index % 3] = max(
                0,
                min(255, mutable[index % 3] + (1 if mutable[index % 3] < 255 else -1)),
            )
            color = tuple(mutable)
        colors.append(color)
    if len(set(colors)) != count:
        raise ValueError("palette gradient collapsed distinct author colors")
    return colors


def authored_noise(x: int, y: int, salt: int) -> int:
    value = (x * 0x45D9F3B + y * 0x119DE1F3 + salt * 0x27D4EB2D) & 0xFFFFFFFF
    value ^= value >> 16
    value = (value * 0x45D9F3B) & 0xFFFFFFFF
    value ^= value >> 16
    return value


def nearest_seam_distance(x: int, y: int) -> int:
    vertical = min(x % 16, 16 - (x % 16))
    diagonal_phase = (x + y * 2) % 23
    diagonal = min(diagonal_phase, 23 - diagonal_phase)
    return min(vertical, diagonal)


def body_texture() -> tuple[list[tuple[int, int, int]], list[int]]:
    ceramic = gradient_palette(
        ((65, 47, 43), (110, 76, 57), (189, 175, 145), (224, 211, 178)),
        32,
    )
    underbody = gradient_palette(
        ((34, 30, 32), (70, 57, 51), (126, 78, 48), (190, 132, 67)),
        32,
    )
    palette = ceramic + underbody
    pixels: list[int] = []
    for y in range(64):
        for x in range(64):
            noise = authored_noise(x, y, 0x5155)
            if y < 32:
                seam = nearest_seam_distance(x, y)
                bevel = min(x, 63 - x, y, 31 - y)
                if seam == 0:
                    index = 2 + ((noise >> 5) % 3)
                elif seam == 1:
                    index = 8 + ((noise >> 7) % 3)
                elif bevel <= 1:
                    index = 9 + ((noise >> 9) % 4)
                else:
                    plate_band = 18 + ((x // 8 + y // 6) % 6)
                    index = max(13, min(30, plate_band + int((noise >> 11) % 5) - 2))
                    if (noise & 0x1FF) < 10:
                        index = 11 + ((noise >> 12) % 4)
                    elif ((x * 3 + y * 5) % 29) == 0:
                        index = min(31, index + 5)
            else:
                local_y = y - 32
                ring = (local_y // 3 + x // 7) % 8
                tread = ((x // 4) ^ (local_y // 4)) & 3
                index = 32 + 7 + ring * 2 + tread
                index = max(34, min(63, index))
                if local_y in (0, 1, 30, 31):
                    index = 34 + ((noise >> 6) % 4)
                elif x % 16 in (0, 1):
                    index = 39 + ((noise >> 8) % 4)
                elif (noise & 0x3FF) < 12:
                    index = 48 + ((noise >> 10) % 6)
            pixels.append(index)
    for index in range(64):
        x = index % 32
        y = index // 32
        pixels[y * 64 + x] = index
    return palette, pixels


def accent_texture() -> tuple[list[tuple[int, int, int]], list[int]]:
    palette = gradient_palette(
        ((19, 30, 62), (39, 58, 104), (49, 78, 150), (90, 129, 205)),
        12,
    )
    pixels: list[int] = []
    center = 15.5
    for y in range(32):
        for x in range(32):
            dx = x - center
            dy = y - center
            radius = math.sqrt(dx * dx + dy * dy)
            angle = math.atan2(dy, dx)
            spoke = abs(math.sin(angle * 4.0))
            ring = abs(radius - 11.5)
            noise = authored_noise(x, y, 0x434F)
            if ring < 1.3 or (radius < 12.5 and spoke < 0.16):
                index = 8 + ((noise >> 8) % 4)
            elif ring < 3.0 or (radius < 13.5 and spoke < 0.31):
                index = 4 + ((noise >> 10) % 4)
            else:
                index = 1 + ((x // 4 + y // 5 + (noise >> 14)) % 3)
            if (x + y * 3) % 31 == 0:
                index = min(11, index + 2)
            pixels.append(index)
    for index in range(12):
        pixels[index] = index
    return palette, pixels


def shadow_texture() -> list[tuple[int, int]]:
    pixels: list[tuple[int, int]] = []
    center_x = 15.5
    center_y = 15.0
    for y in range(32):
        for x in range(32):
            nx = (x - center_x) / 14.0
            ny = (y - center_y) / 8.4
            distance = math.sqrt(nx * nx + ny * ny)
            if x in (0, 31) or y in (0, 31) or distance >= 1.0:
                alpha = 0
            else:
                falloff = 1.0 - distance
                alpha = int(round(176.0 * (falloff ** 0.72)))
                alpha = max(8, min(176, alpha))
            intensity = 42 + int(round(max(0.0, 1.0 - distance) * 20.0))
            pixels.append((max(0, min(255, intensity)), alpha))
    return pixels


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_output_dir(path: Path) -> Path:
    absolute = Path(os.path.abspath(path))
    if absolute.exists() and (absolute.is_symlink() or not absolute.is_dir()):
        raise ValueError(f"output path is not one real directory: {absolute}")
    absolute.mkdir(parents=True, exist_ok=True)
    return absolute


def generate(output_dir: Path) -> dict[str, object]:
    output_dir = require_output_dir(output_dir)
    body_palette, body_indices = body_texture()
    accent_palette, accent_indices = accent_texture()
    shadow_pixels = shadow_texture()
    paths = {
        "body": output_dir / BODY_NAME,
        "accent": output_dir / ACCENT_NAME,
        "shadow": output_dir / SHADOW_NAME,
    }
    write_indexed_png(paths["body"], 64, 64, body_palette, body_indices)
    write_indexed_png(paths["accent"], 32, 32, accent_palette, accent_indices)
    write_gray_alpha_png(paths["shadow"], 32, 32, shadow_pixels)
    return {
        "schema": "n64game-quarrune-texture-authoring-v1",
        "body_palette_colors": len(set(body_indices)),
        "accent_palette_colors": len(set(accent_indices)),
        "shadow_alpha_levels": len({alpha for _, alpha in shadow_pixels}),
        "shadow_nonzero_pixels": sum(1 for _, alpha in shadow_pixels if alpha > 0),
        "outputs": {
            key: {
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for key, path in paths.items()
        },
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report = generate(args.output_dir)
    except (OSError, ValueError) as exc:
        print(f"quarrune texture authoring failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
