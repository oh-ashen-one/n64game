from __future__ import annotations

import json
import binascii
import os
import stat
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import n64game_ares_capture_preflight as preflight  # noqa: E402


class AresCapturePreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="n64game-ares-capture-")
        self.root = Path(self.temp.name)
        (self.root / "scripts").mkdir(parents=True)
        (self.root / "build/game").mkdir(parents=True)
        self.rom = self.root / "build/game/n64game-gate3.z64"
        self.rom.write_bytes(bytes.fromhex("80371240") + (b"\0" * 1020))
        self.write_executable(
            self.root / "scripts/audit-ares-input",
            "#!/usr/bin/env bash\nprintf '{\"result\":\"PASS\"}\\n'\n",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_executable(self, path: Path, text: str) -> None:
        path.write_text(text, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)

    def write_run_ares(self, body: str) -> None:
        self.write_executable(
            self.root / "scripts/run-ares",
            "#!/usr/bin/env bash\nset -euo pipefail\n" + body,
        )

    def write_png_header(self, path: Path, width: int, height: int) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\0\0\0\rIHDR" + struct.pack(">II", width, height))

    def write_png_rgba(self, path: Path, width: int, height: int, rgba: bytes) -> None:
        def chunk(kind: bytes, payload: bytes) -> bytes:
            return (
                struct.pack(">I", len(payload))
                + kind
                + payload
                + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
            )
        row_bytes = width * 4
        raw = bytearray()
        for y in range(height):
            raw.append(0)
            raw.extend(rgba[y * row_bytes:(y + 1) * row_bytes])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw)))
            + chunk(b"IEND", b"")
        )

    def border_mismatch_ares_rgba(self) -> bytes:
        rgba = bytearray(640 * 240 * 4)
        for y in range(240):
            for x in range(320):
                pixel = bytes(((x + y) % 256, y % 256, x % 256, 255))
                left = ((y * 640) + x * 2) * 4
                rgba[left:left + 4] = pixel
                rgba[left + 4:left + 8] = pixel
        for y in range(240):
            offset = ((y * 640) + 633) * 4
            rgba[offset:offset + 4] = bytes((0, 0, 0, 255))
        return bytes(rgba)

    def test_no_probe_passes_when_identity_wrapper_and_input_pass(self) -> None:
        self.write_run_ares(
            "if [[ \" ${*} \" == *' --check-only '* ]]; then\n"
            "  ROM=\"${@: -1}\"\n"
            "  printf 'ares_version=\\nv148\\nrom_sha256=%s\\n' \"$(shasum -a 256 \"$ROM\" | awk '{print $1}')\"\n"
            "  exit 0\n"
            "fi\n"
        )
        payload = preflight.audit(self.root, self.rom, probe=False, wait_seconds=0.01, keep_running=False, attempt_hotkey=False, attempt_menu=False)
        self.assertEqual(payload["result"], "PASS")
        self.assertEqual(payload["launch_probe"]["result"], "NOT_RUN")
        self.assertEqual(payload["check_only"]["result"], "PASS")

    def test_probe_reports_exited_ares_without_claiming_capture(self) -> None:
        self.write_run_ares(
            "if [[ \" ${*} \" == *' --check-only '* ]]; then\n"
            "  ROM=\"${@: -1}\"\n"
            "  printf 'ares_version=\\nv148\\nrom_sha256=%s\\n' \"$(shasum -a 256 \"$ROM\" | awk '{print $1}')\"\n"
            "  exit 0\n"
            "fi\n"
            "printf 'fake ares exited before showing a window\\n'\n"
            "exit 0\n"
        )
        old_screenshots = preflight.SCREENSHOTS
        preflight.SCREENSHOTS = self.root / "screenshots"
        try:
            payload = preflight.audit(self.root, self.rom, probe=True, wait_seconds=0.01, keep_running=False, attempt_hotkey=False, attempt_menu=False)
        finally:
            preflight.SCREENSHOTS = old_screenshots
        self.assertEqual(payload["result"], "WARN_CAPTURE_NOT_READY")
        self.assertEqual(payload["launch_probe"]["result"], "ARES_EXITED_DURING_PROBE")
        self.assertIn("Ares exited during the launch probe", payload["warnings"][0])

    def test_invalid_rom_fails_before_preflight_claims_anything(self) -> None:
        self.rom.write_bytes(b"not an n64 rom")
        with self.assertRaises(preflight.PreflightError):
            preflight.audit(self.root, self.rom, probe=False, wait_seconds=0.01, keep_running=False, attempt_hotkey=False, attempt_menu=False)

    def test_probe_records_hotkey_attempt_without_promoting_capture(self) -> None:
        self.write_run_ares(
            "if [[ \" ${*} \" == *' --check-only '* ]]; then\n"
            "  ROM=\"${@: -1}\"\n"
            "  printf 'ares_version=\\nv148\\nrom_sha256=%s\\n' \"$(shasum -a 256 \"$ROM\" | awk '{print $1}')\"\n"
            "  exit 0\n"
            "fi\n"
            "sleep 2\n"
        )
        old_screenshots = preflight.SCREENSHOTS
        old_hotkey = preflight.attempt_screenshot_hotkey
        preflight.SCREENSHOTS = self.root / "screenshots"

        def fake_hotkey(wait_seconds: float) -> dict[str, object]:
            return {
                "result": "SENT",
                "method": "fixture",
                "key": "P",
                "wait_seconds": wait_seconds,
            }

        preflight.attempt_screenshot_hotkey = fake_hotkey
        try:
            payload = preflight.audit(self.root, self.rom, probe=True, wait_seconds=0.01, keep_running=False, attempt_hotkey=True, attempt_menu=False)
        finally:
            preflight.SCREENSHOTS = old_screenshots
            preflight.attempt_screenshot_hotkey = old_hotkey
        self.assertEqual(payload["result"], "WARN_CAPTURE_NOT_READY")
        self.assertEqual(payload["launch_probe"]["hotkey_attempt"]["result"], "SENT")
        self.assertIn(
            "screenshot capture attempt produced no files in the isolated Ares screenshot directory",
            payload["warnings"],
        )

    def test_probe_records_menu_capture_dimensions_without_native_approval(self) -> None:
        self.write_run_ares(
            "if [[ \" ${*} \" == *' --check-only '* ]]; then\n"
            "  ROM=\"${@: -1}\"\n"
            "  printf 'ares_version=\\nv148\\nrom_sha256=%s\\n' \"$(shasum -a 256 \"$ROM\" | awk '{print $1}')\"\n"
            "  exit 0\n"
            "fi\n"
            "sleep 2\n"
        )
        old_screenshots = preflight.SCREENSHOTS
        old_menu = preflight.attempt_screenshot_menu
        preflight.SCREENSHOTS = self.root / "screenshots"

        def fake_menu(wait_seconds: float) -> dict[str, object]:
            self.write_png_rgba(
                preflight.SCREENSHOTS / "Nintendo 64" / "capture.png",
                640,
                240,
                self.border_mismatch_ares_rgba(),
            )
            return {
                "result": "SENT",
                "method": "fixture",
                "menu": "Tools/Capture Screenshot",
                "wait_seconds": wait_seconds,
            }

        preflight.attempt_screenshot_menu = fake_menu
        try:
            payload = preflight.audit(self.root, self.rom, probe=True, wait_seconds=0.01, keep_running=False, attempt_hotkey=False, attempt_menu=True)
        finally:
            preflight.SCREENSHOTS = old_screenshots
            preflight.attempt_screenshot_menu = old_menu
        self.assertEqual(payload["result"], "WARN_CAPTURE_NOT_READY")
        self.assertEqual(payload["launch_probe"]["menu_attempt"]["result"], "SENT")
        self.assertTrue(payload["launch_probe"]["capture_session"])
        self.assertEqual(payload["launch_probe"]["capture_pixel_profile"]["Video/PixelAccuracy"], "true")
        self.assertEqual(payload["launch_probe"]["capture_pixel_profile"]["Video/DisableVideoInterfaceProcessing"], "true")
        self.assertIn("--capture-session", payload["launch_probe"]["launch_command"])
        self.assertEqual(payload["launch_probe"]["new_screenshot_count"], 1)
        self.assertEqual(payload["launch_probe"]["native_320x240_screenshot_count"], 0)
        self.assertEqual(payload["launch_probe"]["new_screenshots"][0]["dimensions"], (640, 240))
        self.assertEqual(payload["launch_probe"]["ares_640x240_analysis"][0]["result"], "FAIL_NOT_EXACT_DUPLICATE")
        self.assertTrue(payload["launch_probe"]["ares_640x240_analysis"][0]["mismatches_are_border_only"])
        self.assertTrue(any("none are native 320x240" in warning for warning in payload["warnings"]))
        self.assertTrue(any("border-only" in warning for warning in payload["warnings"]))


if __name__ == "__main__":
    unittest.main()
