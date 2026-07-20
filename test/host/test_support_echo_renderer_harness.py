from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class SupportEchoRendererHarnessTests(unittest.TestCase):
    def test_event_routing_serials_and_one_shots(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="n64game-support-echo-renderer-"
        ) as directory:
            executable = Path(directory) / "support-echo-renderer-harness"
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
                    str(ROOT / "test" / "host" / "support_echo_renderer_stub"),
                    "-I",
                    str(ROOT / "src"),
                    str(ROOT / "src" / "support_echo_renderer.c"),
                    str(ROOT / "test" / "host" / "support_echo_renderer_harness.c"),
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
                "support Echoform renderer behavior harness: PASS\n",
            )


if __name__ == "__main__":
    unittest.main()
