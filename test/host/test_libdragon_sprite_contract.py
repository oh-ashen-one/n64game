from __future__ import annotations

import base64
import json
import struct
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUBY = "/usr/bin/ruby"
FMT_CI4 = 8
FMT_CI8 = 9
FMT_IA8 = 13


def align(value: int, alignment: int) -> int:
    return (value + alignment - 1) // alignment * alignment


def palette_words(count: int) -> list[int]:
    return [
        (((index & 31) << 11) | (((index >> 5) & 31) << 6) | (((index >> 10) & 31) << 1) | 1)
        for index in range(count)
    ]


def sprite_file(
    format_code: int,
    width: int,
    height: int,
    pixels: list[int],
    *,
    palette: list[int] | None = None,
    palette_used: int = 0,
) -> bytes:
    bits = 4 if format_code == FMT_CI4 else 8
    row_bytes = (width * bits + 7) // 8
    if format_code == FMT_CI4:
        assert len(pixels) == width * height
        packed = bytearray()
        for y in range(height):
            row = pixels[y * width:(y + 1) * width]
            for x in range(0, width, 2):
                second = row[x + 1] if x + 1 < width else 0
                packed.append((row[x] << 4) | second)
        pixel_data = bytes(packed)
    else:
        pixel_data = bytes(pixels)
    assert len(pixel_data) == row_bytes * height

    ext_offset = align(8 + len(pixel_data), 8)
    output = bytearray(ext_offset + 128)
    struct.pack_into(">HHBBBB", output, 0, width, height, 0, 0x80 | format_code, 1, 1)
    output[8:8 + len(pixel_data)] = pixel_data
    tmem_bytes = align(row_bytes, 8) * height + (2048 if format_code in (FMT_CI4, FMT_CI8) else 0)
    ext_flags = 0x20 if tmem_bytes <= 4096 else 0
    palette_offset = ext_offset + 128 if palette is not None else 0
    struct.pack_into(">HHI", output, ext_offset, 128, 6, palette_offset)
    struct.pack_into(">HBB", output, ext_offset + 64, ext_flags, palette_used, 0)
    if palette is not None:
        output.extend(b"".join(struct.pack(">H", value) for value in palette))
    return bytes(output)


def body_sprite() -> bytes:
    pixels = [(x + y * 64) % 64 for y in range(64) for x in range(64)]
    return sprite_file(FMT_CI8, 64, 64, pixels, palette=palette_words(256), palette_used=64)


def accent_sprite() -> bytes:
    pixels = [(x + y) % 16 for y in range(32) for x in range(32)]
    return sprite_file(FMT_CI4, 32, 32, pixels, palette=palette_words(16), palette_used=16)


def shadow_sprite() -> bytes:
    pixels: list[int] = []
    for y in range(32):
        for x in range(32):
            distance = ((x - 15.5) / 13.0) ** 2 + ((y - 15.5) / 9.0) ** 2
            alpha = max(0, min(15, round((1.0 - distance) * 15))) if distance < 1.0 else 0
            pixels.append(alpha)
    return sprite_file(FMT_IA8, 32, 32, pixels)


def ext_offset(data: bytes) -> int:
    width, height = struct.unpack_from(">HH", data, 0)
    format_code = data[5] & 0x1F
    bits = 4 if format_code == FMT_CI4 else 8
    return align(8 + ((width * bits + 7) // 8) * height, 8)


class LibdragonSpriteContractTests(unittest.TestCase):
    maxDiff = None

    def ruby(self, data: bytes, **profile: object) -> dict[str, object]:
        program = r"""
          require 'base64'
          require 'json'
          require 'n64game/libdragon_sprite_contract'
          input = JSON.parse(STDIN.read)
          bytes = Base64.strict_decode64(input.fetch('bytes'))
          contract = N64Game::LibdragonSpriteContract
          begin
            decoded = if input['profile']
              p = input.fetch('profile')
              contract.validate_profile(
                bytes, label: 'subject', format: p.fetch('format'), width: p.fetch('width'),
                height: p.fetch('height'), fits_tmem: p.fetch('fits_tmem')
              )
            else
              contract.decode(bytes, 'subject')
            end
            decoded = decoded.reject { |key, _value| [:pixel_data, :indices, :palette].include?(key) }
            result = {'issues' => [], 'decoded' => decoded}
          rescue N64Game::LibdragonSpriteContract::ParseError => error
            result = {'issues' => [error.message]}
          end
          STDOUT.write(JSON.generate(result))
        """
        payload: dict[str, object] = {"bytes": base64.b64encode(data).decode()}
        if profile:
            payload["profile"] = profile
        completed = subprocess.run(
            [RUBY, "--disable-gems", "-I", str(ROOT / "lib"), "-e", program],
            input=json.dumps(payload), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False, env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    def test_exact_quarrune_profiles_decode_with_truthful_tmem_state(self) -> None:
        cases = (
            (body_sprite(), {"format": "CI8", "width": 64, "height": 64, "fits_tmem": False}, 6144),
            (accent_sprite(), {"format": "CI4", "width": 32, "height": 32, "fits_tmem": True}, 2560),
            (shadow_sprite(), {"format": "IA8", "width": 32, "height": 32, "fits_tmem": True}, 1024),
        )
        for data, profile, tmem_bytes in cases:
            with self.subTest(profile=profile):
                result = self.ruby(data, **profile)
                self.assertEqual(result["issues"], [], result)
                self.assertEqual(result["decoded"]["tmem_bytes"], tmem_bytes)

    def test_base_header_and_container_mutations_fail_closed(self) -> None:
        clean = body_sprite()
        cases: dict[str, tuple[callable, str]] = {
            "truncated": (lambda data: data.__delitem__(slice(0, len(data) - 4)), "shorter"),
            "deprecated": (lambda data: data.__setitem__(4, 8), "deprecated bitdepth"),
            "owned_flag": (lambda data: data.__setitem__(5, data[5] | 0x20), "base flags"),
            "format": (lambda data: data.__setitem__(5, 0x80 | 2), "format"),
            "tiles": (lambda data: data.__setitem__(6, 2), "untiled"),
        }
        for name, (mutate, expected) in cases.items():
            with self.subTest(mutation=name):
                mutated = bytearray(clean)
                mutate(mutated)
                result = self.ruby(bytes(mutated))
                self.assertTrue(result["issues"], result)
                self.assertIn(expected, result["issues"][0])
        for encoded, expected in ((b"DCAxxxxx", "DCA"), (b"\0\0\0\0BC1Q", "lossy")):
            result = self.ruby(encoded)
            self.assertTrue(result["issues"], result)
            self.assertIn(expected, result["issues"][0])

    def test_extended_header_offsets_flags_and_zero_fields_are_exact(self) -> None:
        clean = body_sprite()
        ext = ext_offset(clean)
        cases: dict[str, tuple[callable, str]] = {
            "size": (lambda data: struct.pack_into(">H", data, ext, 127), "size"),
            "version": (lambda data: struct.pack_into(">H", data, ext + 2, 5), "version"),
            "palette_offset": (lambda data: struct.pack_into(">I", data, ext + 4, ext + 120), "palette offset"),
            "lod": (lambda data: data.__setitem__(ext + 8, 1), "LOD"),
            "false_fit": (lambda data: struct.pack_into(">H", data, ext + 64, 0x20), "FITS_TMEM"),
            "texparms": (lambda data: data.__setitem__(ext + 68, 1), "texparms"),
            "trailing": (lambda data: data.extend(b"\0"), "palette/file size"),
        }
        for name, (mutate, expected) in cases.items():
            with self.subTest(mutation=name):
                mutated = bytearray(clean)
                mutate(mutated)
                result = self.ruby(bytes(mutated))
                self.assertTrue(result["issues"], result)
                self.assertIn(expected, result["issues"][0])

    def test_palette_and_index_census_cannot_be_forged(self) -> None:
        clean = accent_sprite()
        ext = ext_offset(clean)
        cases: dict[str, tuple[callable, str]] = {
            "used_count": (lambda data: data.__setitem__(ext + 66, 15), "used-color count"),
            "pixel_index": (lambda data: data.__setitem__(8, 0xF0), "used-color count"),
            "truncated_palette": (lambda data: data.__delitem__(slice(len(data) - 2, len(data))), "palette/file size"),
        }
        for name, (mutate, expected) in cases.items():
            with self.subTest(mutation=name):
                mutated = bytearray(clean)
                mutate(mutated)
                if name == "pixel_index":
                    mutated[ext + 66] = 15
                result = self.ruby(bytes(mutated))
                self.assertTrue(result["issues"], result)
                self.assertIn(expected, result["issues"][0])

    def test_profile_identity_is_separate_from_structural_decode(self) -> None:
        clean = accent_sprite()
        self.assertEqual(self.ruby(clean)["issues"], [])
        for profile, expected in (
            ({"format": "CI8", "width": 32, "height": 32, "fits_tmem": True}, "format"),
            ({"format": "CI4", "width": 64, "height": 32, "fits_tmem": True}, "dimensions"),
            ({"format": "CI4", "width": 32, "height": 32, "fits_tmem": False}, "TMEM-fit"),
        ):
            result = self.ruby(clean, **profile)
            self.assertTrue(result["issues"], result)
            self.assertIn(expected, result["issues"][0])


if __name__ == "__main__":
    unittest.main()
