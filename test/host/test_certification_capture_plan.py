from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_certification_evidence import sha256  # noqa: E402
from tools import n64game_certification as certification  # noqa: E402
from tools import n64game_certification_plan as plan_tool  # noqa: E402


class CertificationCapturePlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="n64game-certification-plan-")
        self.root = Path(self.temp.name)
        self.rom = self.root / "game.z64"
        self.rom.write_bytes(b"\x80\x37\x12\x40" + bytes(4092))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_plan_binds_current_rom_and_required_capture_matrix_without_claiming_certification(self) -> None:
        out = self.root / "certification"
        plan = plan_tool.build_plan(self.rom, out)
        self.assertEqual(plan["schema"], plan_tool.SCHEMA)
        self.assertEqual(plan["certification"], "NOT_CLAIMED")
        self.assertEqual(plan["status"], certification.STATUS)
        self.assertEqual(plan["rom_sha256"], sha256(self.rom))
        run_ids = {run["id"] for run in plan["runs"]}
        self.assertEqual(run_ids, {
            "timing-1", "timing-2", "soak", "input-smoke",
            "valid_resume", "latest_corrupt_fallback", "all_corrupt_new_game",
        })
        command_text = json.dumps(plan["commands"] + plan["post_capture_commands"])
        self.assertIn("--expected-rom-sha256=" + sha256(self.rom), command_text)
        self.assertIn("scripts/assemble-certification-evidence", command_text)
        self.assertIn("scripts/validate-input-log", command_text)
        self.assertNotIn("CERTIFIED", json.dumps(plan))

    def test_cli_writes_json_and_markdown_plan(self) -> None:
        out = self.root / "certification"
        result = subprocess.run(
            [
                str(ROOT / "scripts" / "plan-certification-captures"),
                "--rom", str(self.rom),
                "--out-dir", str(out),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["result"], "CERTIFICATION_CAPTURE_PLAN_READY")
        self.assertEqual(payload["certification"], "NOT_CLAIMED")
        plan_json = out / "capture-plan.json"
        plan_md = out / "CAPTURE_PLAN.md"
        self.assertTrue(plan_json.is_file())
        self.assertTrue(plan_md.is_file())
        self.assertEqual(json.loads(plan_json.read_text(encoding="utf-8"))["rom_sha256"], sha256(self.rom))
        markdown = plan_md.read_text(encoding="utf-8")
        self.assertIn("# N64GAME Ares Certification Capture Plan", markdown)
        self.assertIn("not evidence and not release certification", markdown)

    def test_rejects_bad_rom_and_symlink_output(self) -> None:
        with self.subTest("bad ROM"):
            bad = self.root / "bad.z64"
            bad.write_bytes(b"not a rom")
            with self.assertRaises(plan_tool.CapturePlanError):
                plan_tool.build_plan(bad, self.root / "certification")

        with self.subTest("symlink output root"):
            target = self.root / "target"
            target.mkdir()
            link = self.root / "link"
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaises(plan_tool.CapturePlanError):
                plan_tool.build_plan(self.rom, link)


if __name__ == "__main__":
    unittest.main()
