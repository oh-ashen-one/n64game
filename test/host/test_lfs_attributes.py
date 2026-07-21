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
            "review/echo.quarrune/g5/quarrune_hero.t3dm",
            "review/anm.echo.quarrune/g5/anm_echo_quarrune.0.sdata",
            "review/echo.quarrune/g5/tex_quarrune_body_ci8_64x64.sprite",
            "runtime-candidates/echo/echo.quarrune/runtime/quarrune.t3dm",
            "runtime-candidates/echo/echo.quarrune/runtime/quarrune.0.sdata",
            "runtime-candidates/echo/echo.ayselor/runtime/ayselor.t3dm",
            "runtime-candidates/echo/echo.ayselor/runtime/ayselor.0.sdata",
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

    def test_authoring_receipts_are_explicit_lf_text_not_lfs(self) -> None:
        self.assertEqual(
            self.attributes("review/echo.quarrune/g2/AUTHORING_STACK_RECEIPT.txt"),
            {"filter": "unspecified", "diff": "unspecified", "merge": "unspecified", "text": "set"},
        )

    def test_skeleton_binding_is_explicit_lf_text_not_lfs(self) -> None:
        expected = {"filter": "unspecified", "diff": "unspecified", "merge": "unspecified", "text": "set"}
        for path in (
            "review/anm.echo.quarrune/g5/SKELETON_BINDING.tsv",
            "review/echo.quarrune/g5/RUNTIME_BINDING.tsv",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.attributes(path), expected)

    def test_gate5_tiny3d_review_snapshots_are_not_ignored(self) -> None:
        paths = (
            "review/echo.quarrune/g5/quarrune_hero.t3dm",
            "review/echo.quarrune/g5/quarrune_distance.t3dm",
            "review/anm.echo.quarrune/g5/anm_echo_quarrune.t3dm",
            "review/anm.echo.quarrune/g5/anm_echo_quarrune.0.sdata",
            "review/anm.echo.quarrune/g5/SKELETON_BINDING.tsv",
            "review/echo.quarrune/g5/tex_quarrune_body_ci8_64x64.sprite",
            "review/echo.quarrune/g5/tex_quarrune_accent_ci4_32x32.sprite",
            "review/echo.quarrune/g5/tex_quarrune_blob_shadow_ia8_32x32.sprite",
            "review/echo.quarrune/g5/RUNTIME_BINDING.tsv",
        )
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "--", *paths],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

        generated = subprocess.run(
            [
                "git", "check-ignore", "--no-index", "scratch/generated.t3dm",
                "scratch/generated.sdata", "scratch/generated.sprite",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(generated.returncode, 0, generated.stdout + generated.stderr)
        self.assertEqual(
            generated.stdout.splitlines(),
            ["scratch/generated.t3dm", "scratch/generated.sdata", "scratch/generated.sprite"],
        )

    def test_reviewed_runtime_candidate_packages_are_not_ignored(self) -> None:
        paths = (
            "runtime-candidates/echo/echo.quarrune/runtime/quarrune.t3dm",
            "runtime-candidates/echo/echo.quarrune/runtime/quarrune.0.sdata",
            "runtime-candidates/echo/echo.ayselor/runtime/ayselor.t3dm",
            "runtime-candidates/echo/echo.ayselor/runtime/ayselor.0.sdata",
        )
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "--", *paths],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
