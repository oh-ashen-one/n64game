from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class IndexedRuntimeHarnessTests(unittest.TestCase):
    def test_helper_is_part_of_the_n64_link(self) -> None:
        rom_make = (ROOT / "mk" / "rom.mk").read_text(encoding="utf-8")
        self.assertIn("$(BUILD_DIR)/indexed_render_assets.o", rom_make)

    def test_configured_ci8_callbacks_and_recorded_lifetimes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="n64game-indexed-runtime-") as directory:
            executable = Path(directory) / "indexed-runtime-harness"
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
                    str(ROOT / "src" / "indexed_render_assets.c"),
                    str(ROOT / "test" / "host" / "indexed_runtime_harness.c"),
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
            self.assertEqual(run.stdout, "indexed runtime harness: PASS\n")


if __name__ == "__main__":
    unittest.main()
