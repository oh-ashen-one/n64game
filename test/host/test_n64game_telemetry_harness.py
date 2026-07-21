from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class N64GameTelemetryHarnessTests(unittest.TestCase):
    def test_frame_heap_and_transition_recorder_executes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="n64game-telemetry-") as directory:
            executable = Path(directory) / "n64game-telemetry-harness"
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
                    str(ROOT / "src"),
                    str(ROOT / "src" / "n64game_telemetry.c"),
                    str(ROOT / "test" / "host" / "n64game_telemetry_harness.c"),
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
            self.assertEqual(run.stdout, "n64game telemetry harness: PASS\n")


if __name__ == "__main__":
    unittest.main()
