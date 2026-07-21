from __future__ import annotations

import json
import binascii
import subprocess
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "assemble-visual-benchmark-captures"
CAPTURE_NAMES = (
    "exploration",
    "dialogue",
    "target_selection",
    "attack_anticipation",
    "impact",
    "support",
)


class VisualCapturePacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="n64game-visual-captures-")
        self.root = Path(self.temp.name)
        self.packet = self.root / "packet.json"
        self.report = self.root / "report.json"
        self.make_packet()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_prepare_wrapper_initializes_packet_without_visual_approval(self) -> None:
        packet = self.root / "prepared-packet.json"
        report = self.root / "prepared-report.json"
        result = subprocess.run(
            [
                str(ROOT / "scripts/prepare-visual-benchmark-captures"),
                f"--packet={packet}",
                f"--report={report}",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("next_visual_capture_steps:", result.stdout)
        payload = json.loads(packet.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], "n64game-visual-capture-packet-v1")
        self.assertEqual(payload["capture_request"], "COMPLETE")
        self.assertEqual(set(payload["captures"]), set(CAPTURE_NAMES))
        self.assertFalse(report.exists())

    def write_png_rgba(self, path: Path, width: int, height: int, rgba: bytes) -> None:
        def chunk(kind: bytes, payload: bytes) -> bytes:
            return (
                struct.pack(">I", len(payload))
                + kind
                + payload
                + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
            )
        raw = bytearray()
        row_bytes = width * 4
        for y in range(height):
            raw.append(0)
            raw.extend(rgba[y * row_bytes:(y + 1) * row_bytes])
        data = (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw)))
            + chunk(b"IEND", b"")
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def make_native_rgba(self, index: int) -> bytes:
        rgba = bytearray(320 * 240 * 4)
        for y in range(240):
            for x in range(320):
                offset = ((y * 320) + x) * 4
                rgba[offset:offset + 4] = bytes((
                    (x + index * 17) % 256,
                    (y + index * 23) % 256,
                    (x + y + index * 31) % 256,
                    255,
                ))
        return bytes(rgba)

    def enlarge_4x(self, native: bytes) -> bytes:
        enlarged = bytearray(1280 * 960 * 4)
        for y in range(240):
            for x in range(320):
                source = ((y * 320) + x) * 4
                pixel = native[source:source + 4]
                for yy in range(y * 4, y * 4 + 4):
                    for xx in range(x * 4, x * 4 + 4):
                        target = ((yy * 1280) + xx) * 4
                        enlarged[target:target + 4] = pixel
        return bytes(enlarged)

    def horizontal_duplicate_2x(self, native: bytes) -> bytes:
        duplicated = bytearray(640 * 240 * 4)
        for y in range(240):
            for x in range(320):
                source = ((y * 320) + x) * 4
                pixel = native[source:source + 4]
                left = ((y * 640) + x * 2) * 4
                duplicated[left:left + 4] = pixel
                duplicated[left + 4:left + 8] = pixel
        return bytes(duplicated)

    def make_packet(self) -> None:
        captures = {}
        for index, name in enumerate(CAPTURE_NAMES):
            native_path = Path("captures") / f"{name}.png"
            enlarged_path = Path("captures") / f"{name}_4x.png"
            native = self.make_native_rgba(index)
            self.write_png_rgba(self.root / native_path, 320, 240, native)
            self.write_png_rgba(self.root / enlarged_path, 1280, 960, self.enlarge_4x(native))
            captures[name] = {
                "native_path": native_path.as_posix(),
                "enlarged_path": enlarged_path.as_posix(),
                "frame_index": index * 10,
                "notes": f"fixture capture {name}",
            }
        payload = {
            "schema": "n64game-visual-capture-packet-v1",
            "capture_request": "COMPLETE",
            "source": {
                "ares_version": "v148",
                "capture_method": "unit-test generated PNG fixtures",
                "operator_id": "test.operator",
            },
            "captures": captures,
        }
        self.packet.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    def run_script(self, *extra_args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                str(SCRIPT),
                "--packet",
                str(self.packet),
                "--report",
                str(self.report),
                "--artifact-root",
                str(self.root),
                *extra_args,
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

    def test_import_ares_640x240_exact_horizontal_duplicate_to_native(self) -> None:
        native = self.make_native_rgba(9)
        self.write_png_rgba(self.root / "captures/ares-menu.png", 640, 240, self.horizontal_duplicate_2x(native))
        output = self.root / "captures/imported-native.png"
        result = self.run_script(
            "--import-ares-640x240",
            "captures/ares-menu.png",
            "--native-out",
            "captures/imported-native.png",
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue(output.is_file())
        payload = json.loads(result.stdout)
        self.assertEqual(payload["derivation"], "exact-horizontal-2x-duplicate-deinterleave")
        self.assertEqual(payload["native"], "captures/imported-native.png")
        replacement = json.loads(self.packet.read_text(encoding="utf-8"))
        replacement["captures"]["exploration"]["native_path"] = "captures/imported-native.png"
        replacement["captures"]["exploration"]["enlarged_path"] = "captures/imported-native_4x.png"
        self.packet.write_text(json.dumps(replacement, sort_keys=True), encoding="utf-8")
        generated = self.run_script("--generate-enlarged", "--overwrite-generated")
        self.assertEqual(generated.returncode, 0, generated.stdout)

    def test_analyze_ares_640x240_reports_exact_duplicate_without_approval(self) -> None:
        native = self.make_native_rgba(12)
        self.write_png_rgba(self.root / "captures/ares-exact.png", 640, 240, self.horizontal_duplicate_2x(native))
        analysis = self.root / "analysis/exact.json"
        result = self.run_script(
            "--analyze-ares-640x240",
            "captures/ares-exact.png",
            "--analysis-out",
            str(analysis),
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        stdout = json.loads(result.stdout)
        self.assertEqual(stdout["result"], "PASS_EXACT_DUPLICATE")
        self.assertTrue(stdout["exact_import_allowed"])
        payload = json.loads(analysis.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], "n64game-ares-640x240-capture-analysis-v1")
        self.assertEqual(payload["pair_analysis"]["mismatching_pairs"], 0)
        self.assertEqual(payload["approval_effect"], "DIAGNOSTIC_ONLY_NOT_VISUAL_BENCHMARK_EVIDENCE")

    def test_analyze_ares_640x240_reports_interior_mismatches(self) -> None:
        native = bytearray(self.horizontal_duplicate_2x(self.make_native_rgba(13)))
        native[((0 * 640) + 3) * 4:((0 * 640) + 3) * 4 + 4] = bytes((1, 2, 3, 255))
        native[((55 * 640) + 101) * 4:((55 * 640) + 101) * 4 + 4] = bytes((4, 5, 6, 255))
        self.write_png_rgba(self.root / "captures/ares-filtered.png", 640, 240, bytes(native))
        analysis = self.root / "analysis/filtered.json"
        result = self.run_script(
            "--analyze-ares-640x240",
            "captures/ares-filtered.png",
            "--analysis-out",
            str(analysis),
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        stdout = json.loads(result.stdout)
        self.assertEqual(stdout["result"], "FAIL_NOT_EXACT_DUPLICATE")
        self.assertFalse(stdout["exact_import_allowed"])
        self.assertEqual(stdout["mismatching_pairs"], 2)
        self.assertEqual(stdout["interior_mismatches"], 1)
        payload = json.loads(analysis.read_text(encoding="utf-8"))
        self.assertEqual(payload["pair_analysis"]["border_mismatches"], 1)
        self.assertEqual(payload["pair_analysis"]["interior_mismatches"], 1)
        self.assertFalse(payload["pair_analysis"]["mismatches_are_border_only"])
        self.assertEqual(payload["first_mismatches"][0]["source_columns"], [2, 3])

    def test_import_ares_640x240_rejects_non_duplicate_horizontal_pairs(self) -> None:
        native = bytearray(self.horizontal_duplicate_2x(self.make_native_rgba(10)))
        native[((7 * 640) + 11) * 4:((7 * 640) + 11) * 4 + 4] = bytes((1, 2, 3, 255))
        self.write_png_rgba(self.root / "captures/ares-bad.png", 640, 240, bytes(native))
        result = self.run_script(
            "--import-ares-640x240",
            "captures/ares-bad.png",
            "--native-out",
            "captures/imported-bad.png",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not exact horizontal 2x duplication", result.stdout)
        self.assertFalse((self.root / "captures/imported-bad.png").exists())

    def test_valid_packet_writes_exact_capture_report(self) -> None:
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], "n64game-visual-capture-evidence-v1")
        self.assertEqual(payload["result"], "PASS")
        self.assertEqual(payload["capture_count"], 6)
        self.assertEqual(payload["native"]["width"], 320)
        self.assertEqual(payload["enlarged"]["width"], 1280)
        self.assertEqual(payload["enlarged"]["resampler"], "nearest-neighbor")
        self.assertEqual(payload["captures"][0]["name"], "exploration")
        self.assertEqual(payload["captures"][0]["enlarged"]["derived_from_native"], "captures/exploration.png")

    def test_generate_enlarged_writes_exact_review_images_before_validation(self) -> None:
        for name in CAPTURE_NAMES:
            (self.root / "captures" / f"{name}_4x.png").unlink()
        result = self.run_script("--generate-enlarged")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('"generated_enlarged_count": 6', result.stdout)
        payload = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(payload["result"], "PASS")
        for name in CAPTURE_NAMES:
            self.assertTrue((self.root / "captures" / f"{name}_4x.png").is_file())

    def test_generate_enlarged_refuses_existing_outputs_without_overwrite_flag(self) -> None:
        result = self.run_script("--generate-enlarged")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already exists", result.stdout)
        overwrite = self.run_script("--generate-enlarged", "--overwrite-generated")
        self.assertEqual(overwrite.returncode, 0, overwrite.stdout)
        self.assertIn('"generated_enlarged_count": 6', overwrite.stdout)

    def test_rejects_non_nearest_neighbor_enlargement(self) -> None:
        bad = bytearray(self.enlarge_4x(self.make_native_rgba(4)))
        offset = ((19 * 1280) + 17) * 4
        bad[offset:offset + 4] = bytes((1, 2, 3, 255))
        self.write_png_rgba(self.root / "captures/impact_4x.png", 1280, 960, bytes(bad))
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not exact 4x nearest-neighbor", result.stdout)

    def test_rejects_wrong_native_dimensions(self) -> None:
        self.write_png_rgba(self.root / "captures/dialogue.png", 319, 240, bytes((0, 0, 0, 255)) * 319 * 240)
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dimensions 319x240 != 320x240", result.stdout)

    def test_init_template_contains_placeholders_that_normal_validation_rejects(self) -> None:
        template_packet = self.root / "template.json"
        init = subprocess.run(
            [str(SCRIPT), "--init-template", "--packet", str(template_packet)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(init.returncode, 0, init.stdout)
        validation = subprocess.run(
            [str(SCRIPT), "--packet", str(template_packet), "--report", str(self.report), "--artifact-root", str(self.root)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertNotEqual(validation.returncode, 0)
        self.assertIn("placeholder text", validation.stdout)


if __name__ == "__main__":
    unittest.main()
