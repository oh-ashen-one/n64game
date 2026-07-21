from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import n64game_certification as certification  # noqa: E402
from tools import n64game_certification_saves as fixtures  # noqa: E402


class CertificationSaveFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="n64game-certification-saves-")
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def assert_slots(self, scenario: str, expected_mask: int, expected_selected: int | None) -> None:
        image = fixtures.eeprom_image(scenario)
        self.assertEqual(len(image), certification.EEPROM_BYTES)
        slots = [
            certification._save_slot(image[index * certification.SAVE_SLOT_BYTES:(index + 1) * certification.SAVE_SLOT_BYTES])
            for index in range(certification.SAVE_SLOT_COUNT)
        ]
        valid_mask = sum((1 << index) for index, slot in enumerate(slots) if slot["valid"])
        self.assertEqual(valid_mask, expected_mask)
        self.assertEqual(certification._selected_slot(slots), expected_selected)

    def test_fixture_slot_semantics_match_recovery_scenarios(self) -> None:
        self.assert_slots("valid_resume", 1, 0)
        self.assert_slots("latest_corrupt_fallback", 1, 0)
        self.assert_slots("all_corrupt_new_game", 0, None)
        corrupt_latest = fixtures.eeprom_image("latest_corrupt_fallback")
        slot_1 = certification._save_slot(corrupt_latest[64:128])
        self.assertTrue(slot_1["recognizable"])
        self.assertFalse(slot_1["checksum_ok"])
        self.assertGreater(slot_1["sequence"], certification._save_slot(corrupt_latest[:64])["sequence"])

    def test_prepare_writes_512_byte_files_manifest_and_machine_json(self) -> None:
        out = self.root / "saves"
        result = subprocess.run(
            [
                str(ROOT / "scripts" / "prepare-certification-save-fixtures"),
                "--out-dir", str(out),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["result"], "CERTIFICATION_SAVE_FIXTURES_READY")
        self.assertEqual(payload["certification"], "NOT_CLAIMED")
        manifest = json.loads((out / "SAVE_FIXTURES.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["certification"], "NOT_CLAIMED")
        self.assertNotIn("CERTIFIED", json.dumps(manifest))
        for row in manifest["fixtures"]:
            path = ROOT / row["path"] if not Path(row["path"]).is_absolute() else Path(row["path"])
            self.assertTrue(path.is_file())
            self.assertEqual(path.stat().st_size, certification.EEPROM_BYTES)
            self.assertEqual(certification._sha256(path), row["sha256"])

    def test_rejects_symlink_output_directory(self) -> None:
        target = self.root / "target"
        target.mkdir()
        link = self.root / "link"
        link.symlink_to(target, target_is_directory=True)
        with self.assertRaises(fixtures.SaveFixtureError):
            fixtures.prepare(link)


if __name__ == "__main__":
    unittest.main()
