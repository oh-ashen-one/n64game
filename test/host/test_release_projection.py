from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts" / "validate-release-projection"


class ReleaseProjectionTests(unittest.TestCase):
    def run_validator(self, root: Path = ROOT) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(VALIDATOR), "--root", str(root)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

    def test_opening_storyboard_projection_passes(self) -> None:
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("release_projection=PASS", result.stdout)
        self.assertIn("storyboard_panels=12", result.stdout)
        self.assertIn("support_images=3", result.stdout)
        self.assertIn("support_docs=4", result.stdout)
        self.assertIn("runtime_seconds=54.5", result.stdout)

    def test_projection_rejects_missing_panel(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            clone = Path(temporary) / "repo"
            shutil.copytree(ROOT, clone, symlinks=True, ignore=shutil.ignore_patterns(".git", "build"))
            (clone / "storyboard" / "opening" / "panels" / "12.png").unlink()
            result = self.run_validator(clone)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("missing, symlinked, or empty file", result.stdout)

    def test_projection_rejects_stale_manifest_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            clone = Path(temporary) / "repo"
            shutil.copytree(ROOT, clone, symlinks=True, ignore=shutil.ignore_patterns(".git", "build"))
            manifest = clone / "storyboard" / "opening" / "DELIVERY_MANIFEST.md"
            text = manifest.read_text(encoding="utf-8")
            with manifest.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(text.replace("7a4eafb97c5c", "000000000000", 1))
            result = self.run_validator(clone)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("SHA-256 changed", result.stdout)

    def test_projection_rejects_timing_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            clone = Path(temporary) / "repo"
            shutil.copytree(ROOT, clone, symlinks=True, ignore=shutil.ignore_patterns(".git", "build"))
            shot_list = clone / "storyboard" / "opening" / "SHOT_LIST.md"
            text = shot_list.read_text(encoding="utf-8")
            with shot_list.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(text.replace("**54.5 s**", "**55.0 s**", 1))
            result = self.run_validator(clone)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("shot list does not bind", result.stdout)

    def test_master_prompt_is_the_reduced_release_authority(self) -> None:
        master = (ROOT / "docs" / "N64GAME_MASTER_SPEC.md").read_text(encoding="utf-8")
        goal = (ROOT / "docs" / "N64GAME_GOAL_PROMPT.md").read_text(encoding="utf-8")

        self.assertIn("Create a polished, original-IP Nintendo 64 game with a genuine 6–8 minute", master)
        self.assertIn("Where older preproduction documents describe that larger plan, this document wins", master)
        self.assertIn("Quarrune and Ayselor against simulation opponents Gyreclast and Kivarrax", master)
        self.assertIn("Do not re-expand toward the superseded 20-minute plan", master)
        self.assertIn("replaced the former 18–25 minute/two-location plan", goal)
        self.assertIn("Deliver a genuine polished 6–8 minute chapter", goal)
        for stale_phrase in (
            "The median target is **22 minutes 30 seconds**",
            "18–25 minute median",
            "At least 15 minutes",
            "Meridian Research Annex and Veyra Observatory Estate",
            "interactive world map",
        ):
            self.assertNotIn(stale_phrase, master)
            self.assertNotIn(stale_phrase, goal)


if __name__ == "__main__":
    unittest.main()
