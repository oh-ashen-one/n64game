from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class StoryCastRendererHarnessTests(unittest.TestCase):
    def test_lifecycle_dialogue_edges_and_fixed_step_one_shots(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="n64game-story-cast-renderer-"
        ) as directory:
            executable = Path(directory) / "story-cast-renderer-harness"
            build = subprocess.run(
                [
                    "cc",
                    "-std=gnu2x",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-Wshadow",
                    "-Wconversion",
                    "-I",
                    str(ROOT / "test" / "host" / "story_cast_renderer_stub"),
                    "-I",
                    str(ROOT / "src"),
                    str(ROOT / "src" / "story_cast_renderer.c"),
                    str(ROOT / "test" / "host" / "story_cast_renderer_harness.c"),
                    "-lm",
                    "-o",
                    str(executable),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            run = subprocess.run(
                [str(executable)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertEqual(
                run.stdout,
                "story cast renderer behavior harness: PASS\n",
            )


if __name__ == "__main__":
    unittest.main()
