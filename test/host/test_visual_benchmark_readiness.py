from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import n64game_visual_benchmark_readiness as readiness  # noqa: E402


class VisualBenchmarkReadinessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="n64game-visual-readiness-")
        self.root = Path(self.temp.name)
        self.copy("docs/N64GAME_MASTER_SPEC.md")
        self.copy("docs/VISUAL_BENCHMARK_APPROVAL.md")
        self.copy("config/runtime-candidates.tsv")
        for relative in (
            "review/env.annex.atrium_lower/g1/PROVENANCE.md",
            "review/env.annex.atrium_lower/g1/EVIDENCE_MANIFEST.sha256",
            "review/env.annex.atrium_lower/g1/REVIEW.md",
            "review/env.annex.atrium_lower/g1/CONCEPT_RENDER.png",
        ):
            self.copy(relative)
        for line in (self.root / "config/runtime-candidates.tsv").read_text(encoding="utf-8").splitlines()[1:]:
            source_path = line.split("\t")[2]
            source = self.root / source_path
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(b"fixture candidate\n")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def copy(self, relative: str) -> None:
        src = ROOT / relative
        dst = self.root / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    def test_current_pending_control_reports_exact_blocking_counts(self) -> None:
        payload = readiness.audit(self.root)
        self.assertEqual(payload["schema"], "n64game-visual-benchmark-readiness-v1")
        self.assertEqual(payload["result"], "BLOCKED_BY_MISSING_EVIDENCE")
        self.assertEqual(payload["control"]["decision"], "PENDING")
        self.assertEqual(payload["control"]["production_lock"], "LOCKED")
        counts = payload["summary"]["counts"]
        self.assertEqual(counts["whitelist_rows"], 52)
        self.assertEqual(counts["authorization_rows"], 52)
        self.assertEqual(counts["authorization_active"], 0)
        self.assertEqual(counts["evidence_rows"], 15)
        self.assertEqual(counts["evidence_pass"], 0)
        self.assertEqual(counts["objective_rows"], 13)
        self.assertEqual(counts["objective_pass"], 0)
        self.assertEqual(counts["reviewer_rows"], 3)
        self.assertEqual(counts["reviewer_pass"], 0)
        self.assertEqual(counts["complete_concept_packets"], 1)
        self.assertEqual(counts["runtime_candidate_rows"], 28)
        self.assertEqual(counts["runtime_candidate_missing_files"], 0)
        self.assertIn("visual benchmark decision is not APPROVED", payload["summary"]["blockers"])
        self.assertEqual(payload["evidence_pending"][0]["evidence_id"], "ev.benchmark.native")
        self.assertEqual(payload["objective_pending"][0]["objective"], "Output")
        self.assertEqual(payload["reviewer_pending"][0]["role"], "Art / visual authorship")

    def test_missing_runtime_candidate_file_is_reported_without_approving(self) -> None:
        missing = self.root / "runtime-candidates/echo/echo.quarrune/quarrune_hero.glb"
        missing.unlink()
        payload = readiness.audit(self.root)
        self.assertEqual(payload["result"], "BLOCKED_BY_MISSING_EVIDENCE")
        self.assertIn(
            "runtime-candidates/echo/echo.quarrune/quarrune_hero.glb",
            payload["runtime_candidates"]["missing_files"],
        )
        self.assertEqual(payload["summary"]["counts"]["runtime_candidate_missing_files"], 1)

    def test_cli_writes_json_and_markdown_reports(self) -> None:
        json_out = self.root / "build/reports/visual-benchmark-readiness.json"
        md_out = self.root / "build/reports/visual-benchmark-readiness.md"
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                str(ROOT / "tools/n64game_visual_benchmark_readiness.py"),
                "--root",
                str(self.root),
                "--json-out",
                str(json_out),
                "--md-out",
                str(md_out),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(json_out.read_text(encoding="utf-8"))
        self.assertEqual(payload["result"], "BLOCKED_BY_MISSING_EVIDENCE")
        self.assertIn("Visual Benchmark Readiness", md_out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
