from __future__ import annotations

import hashlib
import struct
import sys
import tempfile
import unittest
import zlib
from collections import deque
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import n64game_quarrune_textures as textures  # noqa: E402


def png_chunks(path: Path) -> dict[bytes, list[bytes]]:
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise AssertionError("not a PNG")
    chunks: dict[bytes, list[bytes]] = {}
    offset = 8
    while offset < len(data):
        length = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        chunks.setdefault(kind, []).append(payload)
        offset += 12 + length
    return chunks


def decoded_rows(path: Path) -> tuple[tuple[int, int, int, int, int], list[bytes]]:
    chunks = png_chunks(path)
    width, height, depth, color_type, _compression, _filtering, _interlace = struct.unpack(
        ">IIBBBBB", chunks[b"IHDR"][0]
    )
    channels = {3: 1, 4: 2}[color_type]
    raw = zlib.decompress(b"".join(chunks[b"IDAT"]))
    stride = width * channels
    rows = []
    offset = 0
    for _ in range(height):
        if raw[offset] != 0:
            raise AssertionError("authoring PNG must use deterministic filter NONE")
        rows.append(raw[offset + 1 : offset + 1 + stride])
        offset += stride + 1
    if offset != len(raw):
        raise AssertionError("decoded PNG contains trailing scanline bytes")
    return (width, height, depth, color_type, channels), rows


class QuarruneTextureAuthoringTests(unittest.TestCase):
    def test_generation_is_byte_deterministic_and_has_exact_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as left_temp, tempfile.TemporaryDirectory() as right_temp:
            left = Path(left_temp)
            right = Path(right_temp)
            left_report = textures.generate(left)
            right_report = textures.generate(right)
            self.assertEqual(left_report["body_palette_colors"], 64)
            self.assertEqual(left_report["accent_palette_colors"], 12)
            self.assertGreaterEqual(left_report["shadow_alpha_levels"], 16)
            for name in (textures.BODY_NAME, textures.ACCENT_NAME, textures.SHADOW_NAME):
                left_bytes = (left / name).read_bytes()
                right_bytes = (right / name).read_bytes()
                self.assertEqual(left_bytes, right_bytes, name)
                self.assertEqual(
                    hashlib.sha256(left_bytes).hexdigest(),
                    hashlib.sha256(right_bytes).hexdigest(),
                )

            body_chunks = png_chunks(left / textures.BODY_NAME)
            body_header, body_rows = decoded_rows(left / textures.BODY_NAME)
            self.assertEqual(body_header, (64, 64, 8, 3, 1))
            self.assertEqual(len(body_chunks[b"PLTE"][0]), 64 * 3)
            self.assertEqual(set(b"".join(body_rows)), set(range(64)))

            accent_chunks = png_chunks(left / textures.ACCENT_NAME)
            accent_header, accent_rows = decoded_rows(left / textures.ACCENT_NAME)
            self.assertEqual(accent_header, (32, 32, 8, 3, 1))
            self.assertEqual(len(accent_chunks[b"PLTE"][0]), 12 * 3)
            self.assertEqual(set(b"".join(accent_rows)), set(range(12)))

    def test_blob_shadow_has_zero_perimeter_ramp_and_one_connected_footprint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            textures.generate(root)
            header, rows = decoded_rows(root / textures.SHADOW_NAME)
        self.assertEqual(header, (32, 32, 8, 4, 2))
        alpha = [[rows[y][x * 2 + 1] for x in range(32)] for y in range(32)]
        self.assertTrue(all(alpha[0][x] == 0 and alpha[31][x] == 0 for x in range(32)))
        self.assertTrue(all(alpha[y][0] == 0 and alpha[y][31] == 0 for y in range(32)))
        levels = {value for row in alpha for value in row}
        self.assertGreaterEqual(len(levels), 16)
        self.assertGreater(alpha[15][15], 150)

        nonzero = {(x, y) for y in range(32) for x in range(32) if alpha[y][x] > 0}
        self.assertGreater(len(nonzero), 300)
        queue = deque([next(iter(nonzero))])
        visited = {queue[0]}
        while queue:
            x, y = queue.popleft()
            for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if neighbor in nonzero and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        self.assertEqual(visited, nonzero)


if __name__ == "__main__":
    unittest.main()
