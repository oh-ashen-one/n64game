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

    def test_canonical_projection_passes(self) -> None:
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("release_projection=PASS", result.stdout)
        self.assertIn("retained_ids=185", result.stdout)
        self.assertIn("production_ids=178", result.stdout)
        self.assertIn("aliases=7", result.stdout)
        self.assertIn("humanoids=3", result.stdout)
        self.assertIn("echoforms=4", result.stdout)
        self.assertIn("move_pairs=16", result.stdout)
        self.assertIn("storyboard=18", result.stdout)

    def test_projection_rejects_cut_scope_reentry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            clone = Path(temporary) / "repo"
            shutil.copytree(ROOT, clone, symlinks=True, ignore=shutil.ignore_patterns(".git", "build"))
            path = clone / "docs" / "RETAINED_RELEASE.tsv"
            text = path.read_text(encoding="utf-8")
            anchor = "n64game-retained-release-v1\tFORBID\tPRODUCTION\tCUT_SCOPE\tEXACT\tchr.ivo_veyra"
            injected = (
                "n64game-retained-release-v1\tRETAIN\tPRODUCTION\tHUMANOID\tEXACT\tchr.ivo_veyra"
                "\tanm.humanoid.base\t1\tivo\tatrium\n"
            )
            with path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(text.replace(anchor, injected + anchor))
            result = self.run_validator(clone)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("HUMANOID release roster differs", result.stdout)

    def test_projection_rejects_move_audio_suffix_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            clone = Path(temporary) / "repo"
            shutil.copytree(ROOT, clone, symlinks=True, ignore=shutil.ignore_patterns(".git", "build"))
            path = clone / "docs" / "RETAINED_RELEASE.tsv"
            text = path.read_text(encoding="utf-8")
            text = text.replace(
                "sfx.move.quarrune.ridge_ram\t1\tridge_ram",
                "sfx.move.quarrune.brace_relay\t1\tridge_ram",
                1,
            )
            with path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
            result = self.run_validator(clone)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("move VFX/SFX suffix mismatch", result.stdout)


if __name__ == "__main__":
    unittest.main()
