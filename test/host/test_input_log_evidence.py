from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import n64game_certification as certification  # noqa: E402
from tools import n64game_input_log as input_log  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def log_text(rom_hash: str, records: list[str]) -> str:
    return "\n".join([
        f"ares_version={certification.PINNED_ARES_VERSION}",
        f"ares_sha256={certification.PINNED_ARES_SHA256}",
        f"rom_sha256={rom_hash}",
        "homebrew_mode=true",
        "expansion_pak=false",
        "defocus=allow",
        *records,
    ]) + "\n"


def input_record(
    sequence: int,
    *,
    pressed: int,
    held: int | None = None,
    scene: int = 2,
    stick_x: int = 0,
    stick_y: int = 0,
) -> str:
    return (
        "N64G_INPUT schema=1 "
        f"seq={sequence} "
        f"status={certification.STATUS} "
        f"wall_ticks={1000 + sequence} "
        f"submitted_frames={sequence} "
        f"scene={scene} "
        f"pressed={pressed:03x} "
        f"held={(pressed if held is None else held):03x} "
        f"stick_x={stick_x} "
        f"stick_y={stick_y}"
    )


class InputLogEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="n64game-input-log-")
        self.root = Path(self.temp.name)
        self.rom = self.root / "game.z64"
        self.rom.write_bytes(b"\x80\x37\x12\x40" + bytes(4092))
        self.rom_hash = sha256(self.rom)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_log(self, *records: str, rom_hash: str | None = None) -> Path:
        path = self.root / "input.log"
        path.write_text(log_text(rom_hash or self.rom_hash, list(records)), encoding="utf-8")
        return path

    def test_valid_input_log_binds_rom_and_required_edges(self) -> None:
        path = self.write_log(
            input_record(0, pressed=input_log.BUTTON_MASKS["up"], stick_y=127),
            input_record(1, pressed=input_log.BUTTON_MASKS["confirm"]),
            input_record(2, pressed=input_log.BUTTON_MASKS["start"]),
        )
        result = input_log.validate(
            path,
            self.rom,
            ["up", "confirm", "start"],
        )
        self.assertEqual(result["result"], "INPUT_LOG_PASS")
        self.assertEqual(result["certification"], "NOT_CLAIMED")
        self.assertEqual(result["rom_sha256"], self.rom_hash)
        self.assertEqual(result["input_record_count"], 3)
        self.assertEqual(result["required_inputs"], ["up", "confirm", "start"])
        self.assertIn("up", result["observed_inputs"])

    def test_cli_is_machine_readable_and_fail_closed(self) -> None:
        path = self.write_log(
            input_record(0, pressed=input_log.BUTTON_MASKS["left"], stick_x=-127),
            input_record(1, pressed=input_log.BUTTON_MASKS["right"], stick_x=127),
        )
        passed = subprocess.run(
            [
                str(ROOT / "scripts" / "validate-input-log"),
                "--log",
                str(path),
                "--rom",
                str(self.rom),
                "--require",
                "left",
                "--require",
                "right",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        self.assertEqual(json.loads(passed.stdout)["result"], "INPUT_LOG_PASS")

        failed = subprocess.run(
            [
                str(ROOT / "scripts" / "validate-input-log"),
                "--log",
                str(path),
                "--rom",
                str(self.rom),
                "--require",
                "relay",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("INPUT_LOG_FAIL", failed.stdout)

    def test_capture_helper_validate_only_requires_full_keyboard_map(self) -> None:
        required = [
            ("up", {"stick_y": 127}),
            ("down", {"stick_y": -127}),
            ("left", {"stick_x": -127}),
            ("right", {"stick_x": 127}),
            ("confirm", {}),
            ("cancel", {}),
            ("start", {}),
            ("pause", {}),
            ("relay", {}),
        ]
        path = self.write_log(*[
            input_record(
                sequence,
                pressed=input_log.BUTTON_MASKS[name],
                **kwargs,
            )
            for sequence, (name, kwargs) in enumerate(required)
        ])
        passed = subprocess.run(
            [
                str(ROOT / "scripts" / "capture-input-smoke"),
                "--validate-only",
                f"--log={path}",
                f"--rom={self.rom}",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        payload = json.loads(passed.stdout)
        self.assertEqual(payload["result"], "INPUT_LOG_PASS")
        self.assertEqual(payload["required_inputs"], [name for name, _ in required])

        missing_relay = self.write_log(*[
            input_record(
                sequence,
                pressed=input_log.BUTTON_MASKS[name],
                **kwargs,
            )
            for sequence, (name, kwargs) in enumerate(required[:-1])
        ])
        failed = subprocess.run(
            [
                str(ROOT / "scripts" / "capture-input-smoke"),
                "--validate-only",
                f"--log={missing_relay}",
                f"--rom={self.rom}",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("INPUT_LOG_FAIL", failed.stdout)
        self.assertIn("relay", failed.stdout)

    def test_capture_helper_documents_fail_closed_operator_path(self) -> None:
        helper = (ROOT / "scripts" / "capture-input-smoke").read_text(encoding="utf-8")
        self.assertIn("N64G_INPUT edge records", helper)
        self.assertIn("--require up", helper)
        self.assertIn("--require relay", helper)
        self.assertIn("This creates input-smoke evidence only", helper)
        self.assertIn('"$ROOT/scripts/run-ares"', helper)
        self.assertIn("tee \"$LOG\"", helper)

    def test_mutations_are_rejected(self) -> None:
        cases = {
            "wrong_rom_hash": self.write_log(
                input_record(0, pressed=input_log.BUTTON_MASKS["confirm"]),
                rom_hash="0" * 64,
            ),
            "nonconsecutive_sequence": self.write_log(
                input_record(1, pressed=input_log.BUTTON_MASKS["confirm"]),
            ),
            "pressed_without_held": self.write_log(
                input_record(
                    0,
                    pressed=input_log.BUTTON_MASKS["confirm"],
                    held=0,
                ),
            ),
            "unknown_scene": self.write_log(
                input_record(
                    0,
                    pressed=input_log.BUTTON_MASKS["confirm"],
                    scene=9,
                ),
            ),
        }
        for name, path in cases.items():
            with self.subTest(name=name):
                with self.assertRaises(input_log.InputLogError):
                    input_log.validate(path, self.rom, [])


if __name__ == "__main__":
    unittest.main()
