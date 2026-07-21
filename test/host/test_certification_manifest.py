from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_certification_evidence import EvidencePackage  # noqa: E402
from tools import n64game_certification as certification  # noqa: E402
from tools import n64game_certification_manifest as assembler  # noqa: E402


def timing_specs() -> list[str]:
    return [
        "timing-1:watched:default:logs/timing-1.log",
        "timing-2:skipped:custom:logs/timing-2.log",
    ]


def save_specs() -> list[str]:
    return [
        "valid_resume:valid_resume:logs/valid_resume.log:saves/valid_resume.eep",
        "latest_corrupt_fallback:latest_corrupt_fallback:logs/latest_corrupt_fallback.log:saves/latest_corrupt_fallback.eep",
        "all_corrupt_new_game:all_corrupt_new_game:logs/all_corrupt_new_game.log:saves/all_corrupt_new_game.eep",
    ]


class CertificationManifestAssemblerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="n64game-certification-manifest-")
        self.package = EvidencePackage(Path(self.temp.name))
        self.out = self.package.root / "assembled.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def assemble(self, **overrides: object) -> dict[str, object]:
        kwargs = {
            "rom_path": self.package.rom,
            "out_path": self.out,
            "timing_specs": timing_specs(),
            "soak_spec": "soak:1:logs/soak.log",
            "save_specs": save_specs(),
        }
        kwargs.update(overrides)
        return assembler.assemble(**kwargs)  # type: ignore[arg-type]

    def test_assembles_manifest_hashes_that_pass_the_strict_validator(self) -> None:
        manifest = self.assemble()
        assembler.write_manifest(self.out, manifest)
        result = certification.validate(self.out, self.package.rom)
        self.assertEqual(result["result"], "EVIDENCE_CONTRACT_PASS")
        self.assertEqual(result["certification"], "NOT_CLAIMED")
        self.assertEqual(manifest["rom_sha256"], self.package.rom_hash)
        self.assertEqual(manifest["timing_runs"][0]["log_sha256"], self.package.manifest_data["timing_runs"][0]["log_sha256"])
        self.assertNotIn("CERTIFIED", json.dumps(manifest))

    def test_cli_outputs_machine_json_without_claiming_certification(self) -> None:
        summary = self.package.root / "summary.md"
        command = [
            str(ROOT / "scripts" / "assemble-certification-evidence"),
            "--rom", str(self.package.rom),
            "--out", str(self.out),
            "--timing", timing_specs()[0],
            "--timing", timing_specs()[1],
            "--soak", "soak:1:logs/soak.log",
            "--save", save_specs()[0],
            "--save", save_specs()[1],
            "--save", save_specs()[2],
            "--validate",
            "--summary-md", str(summary),
        ]
        passed = subprocess.run(command, cwd=self.package.root, capture_output=True, text=True, check=False)
        self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)
        payload = json.loads(passed.stdout)
        self.assertEqual(payload["result"], "CERTIFICATION_MANIFEST_ASSEMBLED")
        self.assertEqual(payload["certification"], "NOT_CLAIMED")
        self.assertTrue(payload["validated"])
        self.assertEqual(payload["validation_result"], "EVIDENCE_CONTRACT_PASS")
        self.assertIn("not a release certification", summary.read_text(encoding="utf-8"))

        no_validate = subprocess.run(
            command[:-3] + ["--summary-md", str(self.package.root / "bad-summary.md")],
            cwd=self.package.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(no_validate.returncode, 0)
        self.assertIn("CERTIFICATION_MANIFEST_FAIL", no_validate.stderr)
        self.assertFalse((self.package.root / "bad-summary.md").exists())

    def test_fail_closed_for_unsafe_paths_before_writing(self) -> None:
        cases = [
            {"timing_specs": ["timing-1:watched:default:/tmp/log.txt", timing_specs()[1]]},
            {"timing_specs": ["timing-1:watched:default:../logs/timing-1.log", timing_specs()[1]]},
            {"timing_specs": ["timing-1:skipped:custom:logs/timing-1.log", timing_specs()[1]]},
            {"soak_spec": "soak:2:logs/soak.log"},
            {"save_specs": [save_specs()[0], save_specs()[1], "bad:unknown:logs/all_corrupt_new_game.log:saves/all_corrupt_new_game.eep"]},
        ]
        for case in cases:
            with self.subTest(case=case):
                with self.assertRaises(assembler.ManifestAssemblyError):
                    self.assemble(**case)
                self.assertFalse(self.out.exists())

    def test_fail_closed_for_duplicates_and_symlinks(self) -> None:
        with self.subTest("duplicate run id"):
            with self.assertRaises(assembler.ManifestAssemblyError):
                self.assemble(timing_specs=[
                    "same:watched:default:logs/timing-1.log",
                    "same:skipped:custom:logs/timing-2.log",
                ])

        with self.subTest("duplicate log path"):
            with self.assertRaises(assembler.ManifestAssemblyError):
                self.assemble(timing_specs=[
                    "timing-1:watched:default:logs/timing-1.log",
                    "timing-2:skipped:custom:logs/timing-1.log",
                ])

        with self.subTest("duplicate eeprom path"):
            bad_saves = save_specs()
            bad_saves[1] = "latest_corrupt_fallback:latest_corrupt_fallback:logs/latest_corrupt_fallback.log:saves/valid_resume.eep"
            with self.assertRaises(assembler.ManifestAssemblyError):
                self.assemble(save_specs=bad_saves)

        with self.subTest("symlink evidence traversal"):
            os.symlink(self.package.root / "logs" / "timing-1.log", self.package.root / "logs" / "link.log")
            with self.assertRaises(assembler.ManifestAssemblyError):
                self.assemble(timing_specs=[
                    "timing-1:watched:default:logs/link.log",
                    timing_specs()[1],
                ])


if __name__ == "__main__":
    unittest.main()
