from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ATTRIBUTES = ("filter", "diff", "merge", "text")


class LfsAttributeTests(unittest.TestCase):
    @staticmethod
    def attributes(path: str) -> dict[str, str]:
        result = subprocess.run(
            ["git", "check-attr", *ATTRIBUTES, "--", path],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr)
        observed: dict[str, str] = {}
        for line in result.stdout.splitlines():
            _path, attribute, value = line.split(": ", 2)
            observed[attribute] = value
        return observed

    def test_gate4_source_and_review_media_are_exact_lfs_paths(self) -> None:
        expected = {"filter": "lfs", "diff": "lfs", "merge": "lfs", "text": "unset"}
        paths = (
            "assets-src/echo/echo.ayselor/texture.png",
            "assets-src/env/env.annex.atrium_lower/reference_capture.mp4",
            "review/benchmark/evidence/native/exploration.png",
            "review/echo.ayselor/g1/concept_front.png",
            "review/benchmark/evidence/capture_60s/REPRESENTATIVE_60S.mp4",
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.attributes(path), expected)

    def test_gate3_capture_pngs_remain_ordinary_git_blobs(self) -> None:
        expected = {attribute: "unspecified" for attribute in ATTRIBUTES}
        paths = (
            "captures/gate3/ares-v148-ci-29674638989-frame-a.png",
            "captures/gate3/ares-v148-ci-29674638989-frame-b.png",
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.attributes(path), expected)

    def test_no_global_png_or_mp4_rule_can_reclassify_gate3_history(self) -> None:
        patterns = []
        for line in (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                patterns.append(stripped.split()[0])
        self.assertNotIn("*.png", patterns)
        self.assertNotIn("*.mp4", patterns)


if __name__ == "__main__":
    unittest.main()
