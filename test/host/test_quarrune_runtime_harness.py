from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class QuarruneRuntimeHarnessTests(unittest.TestCase):
    def test_callbacks_upload_and_recorded_blocks_retain_owned_sprites(self) -> None:
        with tempfile.TemporaryDirectory(prefix="n64game-quarrune-runtime-") as directory:
            executable = Path(directory) / "quarrune-runtime-harness"
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
                    str(ROOT / "test" / "host" / "quarrune_runtime_stub"),
                    "-I",
                    str(ROOT / "src"),
                    str(ROOT / "src" / "quarrune_render_assets.c"),
                    str(ROOT / "test" / "host" / "quarrune_runtime_harness.c"),
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
            self.assertEqual(run.stdout, "quarrune runtime harness: PASS\n")


if __name__ == "__main__":
    unittest.main()
