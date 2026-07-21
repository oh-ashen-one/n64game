from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import n64game_final_acceptance_audit as audit_tool  # noqa: E402


ONE_BY_ONE_PNG = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00"
    b"\x90wS\xde"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


class FinalAcceptanceAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="n64game-final-audit-")
        self.root = Path(self.temp.name)
        self.make_fixture_repo()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, relative: str, text: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def write_bytes(self, relative: str, data: bytes) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def make_executable(self, relative: str, text: str) -> None:
        self.write(relative, text)
        (self.root / relative).chmod(0o755)

    def make_fixture_repo(self) -> None:
        master = (ROOT / "docs" / "N64GAME_MASTER_SPEC.md").read_text(encoding="utf-8")
        self.write("docs/N64GAME_MASTER_SPEC.md", master)
        self.write("docs/VISUAL_BENCHMARK_APPROVAL.md", "Decision: PENDING\n")
        for relative in ("LICENSE", "ASSET_LICENSE.md", "THIRD_PARTY_NOTICES.md", "README.md"):
            self.write(relative, f"{relative}\n")
        self.write_bytes("build/game/n64game-gate3.z64", b"\x80\x37\x12\x40" + bytes(4092))
        for relative in (
            "build/game/n64game-gate3.z64.sha256",
            "build/game/n64game-gate3.map",
            "build/reports/rom-size.md",
            "build/reports/validation-summary.md",
        ):
            self.write(relative, "fixture\n")
        self.write("build/reports/host-tests.txt", "suite=n64game_host_contracts\nresult=PASS\n")
        self.write("test/host/n64game_core_harness.c", "/* fixture */\n")
        for index in range(1, 13):
            self.write_bytes(f"storyboard/opening/panels/{index:02d}.png", ONE_BY_ONE_PNG)
        self.write_bytes("storyboard/opening/CONTACT_SHEET.png", ONE_BY_ONE_PNG)
        self.write_bytes("storyboard/opening/continuity/CONTINUITY_SHEET.png", ONE_BY_ONE_PNG)
        self.write_bytes("storyboard/opening/COLOR_SCRIPT.png", ONE_BY_ONE_PNG)
        self.write("storyboard/opening/SHOT_LIST.md", "shot list\n")
        self.make_executable("scripts/validate-release-projection", "#!/usr/bin/env bash\nprintf 'release_projection=PASS storyboard=18\\n'\n")
        self.make_executable("scripts/validate-public-hygiene", "#!/usr/bin/env bash\nprintf 'public hygiene pass\\n'\n")
        self.make_executable("scripts/validate-certification-evidence", "#!/usr/bin/env bash\nprintf 'not used\\n'\nexit 1\n")
        subprocess.run(["git", "init"], cwd=self.root, check=True, stdout=subprocess.PIPE)
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/oh-ashen-one/n64game.git"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "audit@example.invalid"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Audit Test"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "fixture"], cwd=self.root, check=True, stdout=subprocess.PIPE)

    def write_public_repro_report(self, *, head: str | None = None, mutate_artifact_sha: bool = False) -> None:
        actual_head = head or subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        rom = self.root / "build/game/n64game-gate3.z64"
        data = rom.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        header_sha = hashlib.sha256(data[:64]).hexdigest()
        artifact_sha = "0" * 64 if mutate_artifact_sha else sha
        identity = {
            "path": "build/game/n64game-gate3.z64",
            "size": len(data),
            "sha256": sha,
            "header_sha256": header_sha,
        }
        payload = {
            "schema": "n64game-public-reproducibility-v1",
            "result": "PASS",
            "repo": "oh-ashen-one/n64game",
            "origin": "https://github.com/oh-ashen-one/n64game.git",
            "head_sha": actual_head,
            "workflow": {
                "name": "Build ROM",
                "run_id": 123456789,
                "url": "https://github.com/oh-ashen-one/n64game/actions/runs/123456789",
                "artifact_name": f"n64game-gate3-{actual_head}",
            },
            "local": {"rom": identity, "files": {}},
            "fresh_public_clone": {"rom": identity, "files": {}, "clone_path": "discarded"},
            "ci_artifact": {"rom": {**identity, "sha256": artifact_sha}, "files": {}},
        }
        self.write("build/reports/public-reproducibility.json", json.dumps(payload, sort_keys=True))

    def test_audit_is_incomplete_and_fail_closed_with_current_missing_gates(self) -> None:
        payload = audit_tool.audit(self.root)
        self.assertEqual(payload["schema"], "n64game-final-acceptance-audit-v1")
        self.assertEqual(payload["result"], "INCOMPLETE")
        by_id = {item["id"]: item for item in payload["items"]}
        self.assertEqual(by_id["FAC-01"]["status"], "PARTIAL")
        self.assertEqual(by_id["FAC-02"]["status"], "PARTIAL")
        self.assertEqual(by_id["FAC-11"]["status"], "PASS")
        self.assertEqual(by_id["FAC-09"]["status"], "MISSING")
        self.assertEqual(by_id["FAC-03"]["status"], "MISSING")
        self.assertLess(payload["pass_count"], payload["item_count"])

    def test_exact_head_public_reproducibility_evidence_promotes_public_rows_only(self) -> None:
        self.write_public_repro_report()
        payload = audit_tool.audit(self.root)
        by_id = {item["id"]: item for item in payload["items"]}
        self.assertEqual(by_id["FAC-01"]["status"], "PASS")
        self.assertEqual(by_id["FAC-02"]["status"], "PASS")
        self.assertEqual(by_id["FAC-03"]["status"], "MISSING")
        self.assertEqual(by_id["FAC-09"]["status"], "MISSING")
        self.assertEqual(payload["result"], "INCOMPLETE")

    def test_not_claimed_certification_evidence_remains_partial(self) -> None:
        rom = self.root / "build/game/n64game-gate3.z64"
        self.write(
            "build/certification/evidence.json",
            json.dumps(
                {
                    "schema": "n64game-certification-evidence-v1",
                    "certification": "NOT_CLAIMED",
                    "rom": {
                        "sha256": hashlib.sha256(rom.read_bytes()).hexdigest(),
                        "size": rom.stat().st_size,
                    },
                    "blockers": ["real Ares playthrough logs have not been captured"],
                },
                sort_keys=True,
            ),
        )
        self.make_executable(
            "scripts/validate-certification-evidence",
            (ROOT / "scripts" / "validate-certification-evidence").read_text(encoding="utf-8"),
        )
        payload = audit_tool.audit(self.root)
        by_id = {item["id"]: item for item in payload["items"]}
        self.assertEqual(by_id["FAC-03"]["status"], "PARTIAL")
        self.assertIn("certification=NOT_CLAIMED", by_id["FAC-03"]["evidence"][0])
        self.assertIn("final visual/audio/controller/release checks still required", by_id["FAC-03"]["missing"][0])
        self.assertEqual(payload["result"], "INCOMPLETE")

    def test_public_reproducibility_report_must_match_head_and_all_identities(self) -> None:
        self.write_public_repro_report(head="0" * 40)
        status, evidence, missing = audit_tool.public_reproducibility_state(self.root)
        self.assertEqual(status, "MISSING")
        self.assertIn("stale", missing[0])
        self.assertIn("head=0000000000000000000000000000000000000000", evidence[0])

        self.write_public_repro_report(mutate_artifact_sha=True)
        status, _evidence, missing = audit_tool.public_reproducibility_state(self.root)
        self.assertEqual(status, "MISSING")
        self.assertIn("malformed", missing[0])

    def test_cli_writes_reports_and_require_complete_fails(self) -> None:
        json_out = self.root / "build/reports/final-acceptance-audit.json"
        md_out = self.root / "build/reports/final-acceptance-audit.md"
        passed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                str(ROOT / "tools" / "n64game_final_acceptance_audit.py"),
                "--root",
                str(self.root),
                "--json-out",
                str(json_out),
                "--md-out",
                str(md_out),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        self.assertEqual(json.loads(passed.stdout)["result"], "INCOMPLETE")
        self.assertEqual(json.loads(json_out.read_text(encoding="utf-8"))["result"], "INCOMPLETE")
        self.assertIn("Do not mark the goal complete", md_out.read_text(encoding="utf-8"))

        failed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                str(ROOT / "tools" / "n64game_final_acceptance_audit.py"),
                "--root",
                str(self.root),
                "--require-complete",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(failed.returncode, 1)
        self.assertEqual(json.loads(failed.stdout)["result"], "INCOMPLETE")

    def test_missing_master_is_a_hard_error(self) -> None:
        (self.root / "docs" / "N64GAME_MASTER_SPEC.md").unlink()
        failed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                str(ROOT / "tools" / "n64game_final_acceptance_audit.py"),
                "--root",
                str(self.root),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(failed.returncode, 2)
        self.assertIn("FINAL_ACCEPTANCE_AUDIT_ERROR", failed.stdout)

    def test_visual_decision_parser_ignores_approved_mentions_in_prose(self) -> None:
        self.write(
            "docs/VISUAL_BENCHMARK_APPROVAL.md",
            "Decision: PENDING\n\n"
            "The prose may describe `Decision: APPROVED` requirements without approving the payload.\n",
        )
        status, evidence, missing = audit_tool.visual_approval_state(self.root)
        self.assertEqual(status, "MISSING")
        self.assertIn("Decision: PENDING", evidence[0])
        self.assertIn("approved production asset gates and visual benchmark", missing)

        self.write(
            "docs/VISUAL_BENCHMARK_APPROVAL.md",
            "Notes mention Decision: PENDING in prose.\nDecision: APPROVED\n",
        )
        status, evidence, missing = audit_tool.visual_approval_state(self.root)
        self.assertEqual(status, "PASS")
        self.assertEqual(missing, ())


if __name__ == "__main__":
    unittest.main()
