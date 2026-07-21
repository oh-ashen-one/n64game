from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import n64game_ares_input_audit as audit  # noqa: E402


class AresInputAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="n64game-ares-input-")
        self.root = Path(self.temp.name)
        (self.root / "scripts").mkdir(parents=True)
        shutil.copy2(ROOT / "scripts/run-ares", self.root / "scripts/run-ares")
        self.state = self.root / "state"
        self.state.mkdir()
        self.empty_process_snapshot = self.root / "empty-ps.txt"
        self.empty_process_snapshot.write_text("", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_settings(self, text: str) -> None:
        (self.state / "settings.bml").write_text(text, encoding="utf-8")

    def test_wrapper_passes_and_missing_settings_are_nonblocking_before_first_launch(self) -> None:
        payload = audit.audit(self.root, self.state, self.empty_process_snapshot)
        self.assertEqual(payload["result"], "PASS")
        self.assertEqual(payload["wrapper"]["result"], "PASS")
        self.assertEqual(payload["settings"]["result"], "MISSING")

    def test_settings_with_legacy_keycodes_are_reported_stale(self) -> None:
        self.write_settings(
            """
Nintendo64
  Input
    Controller
      Port
        Up: 0x1/0/92;0x1/0/62;;
        Down: 0x1/0/81;0x1/0/22;;
        Left: 0x1/0/80;0x1/0/4;;
        Right: 0x1/0/79;0x1/0/7;;
        B: 0x1/0/29;;
        A: 0x1/0/27;;
        C-Down: 0x1/0/44;;
        Z: 0x1/0/225;;
        Start: 0x1/0/40;;
        X-Axis
          Lo: 0x1/0/80;0x1/0/4;;
          Hi: 0x1/0/79;0x1/0/7;;
        Y-Axis
          Lo: 0x1/0/81;0x1/0/22;;
          Hi: 0x1/0/82;0x1/0/26;;
"""
        )
        payload = audit.audit(self.root, self.state, self.empty_process_snapshot)
        self.assertEqual(payload["result"], "WARN_STALE_ARES_PROCESS")
        self.assertEqual(payload["settings"]["result"], "STALE")
        self.assertIn("0x1/0/92;0x1/0/62", payload["settings"]["legacy_fragments"])

    def test_settings_with_stale_l_axis_arrow_bindings_are_reported_stale(self) -> None:
        self.write_settings(
            """
Nintendo64
  Input
    Controller.Port.1
      Gamepad
        L-Up: 0x1/0/81;0x1/0/22;
        L-Down: 0x1/0/82;0x1/0/26;
        L-Left: 0x1/0/80;0x1/0/4;
        L-Right: 0x1/0/79;0x1/0/7;
        Up: 0x1/0/82;0x1/0/26;;
        Down: 0x1/0/81;0x1/0/22;;
        Left: 0x1/0/80;0x1/0/4;;
        Right: 0x1/0/79;0x1/0/7;;
        B: 0x1/0/29;;
        A: 0x1/0/27;;
        C-Down: 0x1/0/44;;
        Z: 0x1/0/225;;
        Start: 0x1/0/40;;
        X-Axis
          Lo: 0x1/0/80;0x1/0/4;;
          Hi: 0x1/0/79;0x1/0/7;;
        Y-Axis
          Lo: 0x1/0/81;0x1/0/22;;
          Hi: 0x1/0/82;0x1/0/26;;
      Mouse
        X: ;;
"""
        )
        payload = audit.audit(self.root, self.state, self.empty_process_snapshot)
        self.assertEqual(payload["result"], "WARN_STALE_ARES_PROCESS")
        self.assertEqual(payload["settings"]["result"], "STALE")
        self.assertIn("L-Up", payload["settings"]["missing_controls"])
        self.assertEqual(
            payload["settings"]["port1_gamepad_bindings"]["L-Up"],
            "0x1/0/81;0x1/0/22;",
        )

    def test_repaired_settings_pass_with_empty_l_axis_and_keyboard_arrows(self) -> None:
        self.write_settings(
            """
Nintendo64
  Input
    Controller.Port.1
      Gamepad
        L-Up: ;;
        L-Down: ;;
        L-Left: ;;
        L-Right: ;;
        Up: 0x1/0/82;0x1/0/26;;
        Down: 0x1/0/81;0x1/0/22;;
        Left: 0x1/0/80;0x1/0/4;;
        Right: 0x1/0/79;0x1/0/7;;
        B: 0x1/0/29;;
        A: 0x1/0/27;;
        C-Down: 0x1/0/44;;
        Z: 0x1/0/225;;
        Start: 0x1/0/40;;
        X-Axis
          Lo: 0x1/0/80;0x1/0/4;;
          Hi: 0x1/0/79;0x1/0/7;;
        Y-Axis
          Lo: 0x1/0/81;0x1/0/22;;
          Hi: 0x1/0/82;0x1/0/26;;
      Mouse
        X: ;;
Hotkey
  CaptureScreenshot: 0x1/0/19;;
"""
        )
        payload = audit.audit(self.root, self.state, self.empty_process_snapshot)
        self.assertEqual(payload["result"], "PASS")
        self.assertEqual(payload["settings"]["result"], "PASS")
        self.assertEqual(payload["settings"]["port1_gamepad_bindings"]["L-Up"], ";;")

    def test_running_legacy_process_is_reported_without_failing_wrapper(self) -> None:
        snapshot = self.root / "ps.txt"
        snapshot.write_text(
            "123 /Applications/ares --setting "
            "Nintendo64/Input/Controller.Port.1/Gamepad/Up=0x1/0/92;0x1/0/62; "
            "--setting Nintendo64/Input/Controller.Port.1/Gamepad/A=0x1/0/65;;\n",
            encoding="utf-8",
        )
        payload = audit.audit(self.root, self.state, snapshot)
        self.assertEqual(payload["result"], "WARN_STALE_ARES_PROCESS")
        self.assertEqual(payload["wrapper"]["result"], "PASS")
        self.assertEqual(payload["processes"]["result"], "STALE_RUNNING_PROCESS")
        self.assertEqual(len(payload["processes"]["stale_processes"]), 1)

    def test_process_id_is_extracted_from_ps_line(self) -> None:
        self.assertEqual(
            audit.process_id_from_snapshot_line("80660 /Applications/ares --setting ..."),
            80660,
        )
        self.assertIsNone(audit.process_id_from_snapshot_line("PID COMMAND"))
        self.assertIsNone(audit.process_id_from_snapshot_line(""))

    def test_terminate_stale_is_disabled_for_fixture_snapshots(self) -> None:
        snapshot = self.root / "ps.txt"
        snapshot.write_text(
            "123 ares --setting Nintendo64/Input/Controller.Port.1/Gamepad/Up=0x1/0/92;0x1/0/62;\n",
            encoding="utf-8",
        )
        payload = audit.terminate_stale_processes(self.root, self.state, snapshot)
        self.assertFalse(payload["attempted"])
        self.assertEqual(payload["terminated_pids"], [])
        self.assertEqual(payload["after"]["result"], "WARN_STALE_ARES_PROCESS")

    def test_cli_writes_json_and_strict_returns_nonzero_for_stale_process(self) -> None:
        snapshot = self.root / "ps.txt"
        snapshot.write_text(
            "123 ares --setting Nintendo64/Input/Controller.Port.1/Gamepad/Up=0x1/0/92;0x1/0/62;\n",
            encoding="utf-8",
        )
        json_out = self.root / "out.json"
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                str(ROOT / "tools/n64game_ares_input_audit.py"),
                "--root",
                str(self.root),
                "--state-root",
                str(self.state),
                "--process-snapshot",
                str(snapshot),
                "--json-out",
                str(json_out),
                "--strict",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(result.returncode, 1, result.stdout)
        payload = json.loads(json_out.read_text(encoding="utf-8"))
        self.assertEqual(payload["result"], "WARN_STALE_ARES_PROCESS")


if __name__ == "__main__":
    unittest.main()
