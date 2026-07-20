from __future__ import annotations

import hashlib
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "test" / "host"))

import n64game_gate5_export as gate5  # noqa: E402
from test_libdragon_sprite_contract import body_sprite, ext_offset  # noqa: E402


class Gate5SpriteCanonicalizerTests(unittest.TestCase):
    def strict_decode(self, data: bytes) -> subprocess.CompletedProcess[bytes]:
        program = r'''
          require "n64game/libdragon_sprite_contract"
          N64Game::LibdragonSpriteContract.validate_profile(
            STDIN.read.b, label: "subject", format: "CI8",
            width: 64, height: 64, fits_tmem: false
          )
          STDOUT.write("PASS\n")
        '''
        return subprocess.run(
            ["/usr/bin/ruby", "--disable-gems", "-I", str(ROOT / "lib"), "-e", program],
            input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
        )

    def mksprite_default_tail(self) -> bytes:
        data = bytearray(body_sprite())
        ext = ext_offset(data)
        struct.pack_into(">f", data, ext + 72, 1.0)
        struct.pack_into(">f", data, ext + 84, 1.0)
        struct.pack_into(">f", data, ext + 96, 2048.0)
        struct.pack_into(">h", data, ext + 100, -1)
        struct.pack_into(">f", data, ext + 108, 2048.0)
        struct.pack_into(">h", data, ext + 112, -1)
        return bytes(data)

    def test_inactive_writer_defaults_are_zeroed_and_strict_contract_passes(self) -> None:
        source = self.mksprite_default_tail()
        ext = ext_offset(source)
        rejected = self.strict_decode(source)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn(b"texparms", rejected.stderr)

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "body.sprite"
            path.write_bytes(source)
            gate5.canonicalize_sprite(path)
            canonical = path.read_bytes()
            first_digest = hashlib.sha256(canonical).hexdigest()

            self.assertEqual(canonical[:ext + 68], source[:ext + 68])
            self.assertEqual(canonical[ext + 68:ext + 128], bytes(60))
            self.assertEqual(canonical[ext + 128:], source[ext + 128:])
            accepted = self.strict_decode(canonical)
            self.assertEqual(accepted.returncode, 0, accepted.stderr.decode("utf-8", "replace"))
            self.assertEqual(accepted.stdout, b"PASS\n")

            gate5.canonicalize_sprite(path)
            self.assertEqual(path.read_bytes(), canonical)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), first_digest)

    def test_active_texparms_detail_lod_or_redirected_data_fail_closed(self) -> None:
        clean = body_sprite()
        ext = ext_offset(clean)
        mutations = {
            "texparms": lambda data: struct.pack_into(">H", data, ext + 64, 0x0008),
            "detail": lambda data: struct.pack_into(">H", data, ext + 64, 0x0010),
            "lod": lambda data: struct.pack_into(">H", data, ext + 64, 0x0001),
            "redirected-data": lambda data: data.__setitem__(5, data[5] | 0x40),
        }
        for name, mutate in mutations.items():
            with self.subTest(feature=name), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "body.sprite"
                mutated = bytearray(clean)
                mutate(mutated)
                before = bytes(mutated)
                path.write_bytes(before)
                with self.assertRaises(gate5.Gate5ExportError):
                    gate5.canonicalize_sprite(path)
                self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
