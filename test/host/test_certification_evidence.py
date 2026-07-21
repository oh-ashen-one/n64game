from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts" / "validate-certification-evidence"
ASSEMBLER = ROOT / "scripts" / "assemble-certification-evidence"
PINNED_ARES_SHA256 = "7a49f00f96a691458461d7c9cf453d95c0f5c054389bbd87c253987b8b6fa345"


class CertificationEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="n64game-certification-")
        self.root = Path(self.temp.name)
        self.rom = self.root / "game.z64"
        self.rom.write_bytes(b"\x80\x37\x12\x40" + bytes(4092))
        self.rom_sha = self.run_command(["shasum", "-a", "256", str(self.rom)]).stdout.split()[0]

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_command(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)

    def write_manifest(self, payload: dict[str, object]) -> Path:
        path = self.root / "evidence.json"
        path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        return path

    def write_artifact(self, relative: str, body: str = "captured Ares evidence\n") -> str:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return relative

    def artifact_record(self, relative: str) -> dict[str, object]:
        path = self.root / relative
        return {
            "path": relative,
            "sha256": self.run_command(["shasum", "-a", "256", str(path)]).stdout.split()[0],
            "size": path.stat().st_size,
        }

    def base_payload(self) -> dict[str, object]:
        return {
            "schema": "n64game-certification-evidence-v1",
            "certification": "NOT_CLAIMED",
            "rom": {"sha256": self.rom_sha, "size": self.rom.stat().st_size},
            "observed_current_state": {
                "check_only": "PASS",
                "ares_input_audit": {
                    "result": "PASS",
                    "wrapper": {"result": "PASS"},
                    "settings": {"result": "PASS"},
                    "processes": {"result": "PASS"},
                    "warnings": [],
                },
            },
            "blockers": ["real Ares playthrough logs have not been captured"],
        }

    def test_not_claimed_manifest_validates_without_certifying_release(self) -> None:
        manifest = self.write_manifest(self.base_payload())
        result = self.run_command([
            str(VALIDATOR),
            "--manifest",
            str(manifest),
            "--rom",
            str(self.rom),
            "--artifact-root",
            str(self.root),
        ])
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["result"], "PASS")
        self.assertEqual(payload["certification"], "NOT_CLAIMED")
        self.assertEqual(payload["blocker_count"], 1)

    def test_not_claimed_manifest_requires_clean_ares_input_audit(self) -> None:
        payload = self.base_payload()
        payload["observed_current_state"] = {
            "check_only": "PASS",
            "ares_input_audit": {
                "result": "WARN_STALE_ARES_PROCESS",
                "wrapper": {"result": "PASS"},
                "settings": {"result": "STALE"},
                "processes": {"result": "PASS"},
                "warnings": ["isolated Ares settings file still contains stale or incomplete bindings"],
            },
        }
        manifest = self.write_manifest(payload)
        result = self.run_command([
            str(VALIDATOR),
            "--manifest",
            str(manifest),
            "--rom",
            str(self.rom),
            "--artifact-root",
            str(self.root),
        ])
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("Ares input audit must be PASS", result.stdout)

    def test_rom_identity_must_match_manifest(self) -> None:
        payload = self.base_payload()
        payload["rom"] = {"sha256": "0" * 64, "size": self.rom.stat().st_size}
        manifest = self.write_manifest(payload)
        result = self.run_command([
            str(VALIDATOR),
            "--manifest",
            str(manifest),
            "--rom",
            str(self.rom),
            "--artifact-root",
            str(self.root),
        ])
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("rom.sha256 does not match", result.stdout)

    def test_complete_manifest_requires_timing_soak_performance_and_qa(self) -> None:
        payload = self.base_payload()
        payload["certification"] = "COMPLETE"
        manifest = self.write_manifest(payload)
        result = self.run_command([
            str(VALIDATOR),
            "--manifest",
            str(manifest),
            "--rom",
            str(self.rom),
            "--artifact-root",
            str(self.root),
        ])
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("ares must be an object", result.stdout)

    def test_complete_manifest_can_validate_when_all_required_rows_pass(self) -> None:
        qa_names = (
            "cold_boot_default_name",
            "cold_boot_custom_name",
            "slate_watched",
            "slate_skipped",
            "required_annex_route",
            "optional_examines",
            "save_reboot_resume",
            "battle_alternate_inputs",
            "battle_victory",
            "battle_defeat_retry",
            "battle_defeat_return",
            "horizon_break_legal",
            "horizon_break_illegal",
            "dialogue_rapid_confirm_cancel",
            "controller_disconnect_reconnect",
            "corrupted_eeprom_fallback",
            "completed_sector_reentry",
            "stable_post_chapter_state",
        )
        timed_a = self.write_artifact("timed-run-a.md", "timed run a stable beacon hook\n")
        timed_b = self.write_artifact("timed-run-b.md", "timed run b stable beacon hook\n")
        soak = self.write_artifact("transition-soak.md", "ten loops heap/resource stable\n")
        performance = self.write_artifact("performance.md", "fps and heap pass\n")
        qa_artifacts = {
            name: self.write_artifact(f"qa/{name}.md", f"{name}: PASS\n")
            for name in qa_names
        }
        payload = {
            "schema": "n64game-certification-evidence-v1",
            "certification": "COMPLETE",
            "rom": {"sha256": self.rom_sha, "size": self.rom.stat().st_size},
            "ares": {
                "version": "v148",
                "executable_sha256": PINNED_ARES_SHA256,
                "homebrew_mode": True,
                "expansion_pak": False,
            },
            "timed_runs": [
                {
                    "id": "timed-run-a",
                    "duration_seconds": 390,
                    "active_control_seconds": 260,
                    "route_result": "STABLE_BEACON_HOOK",
                    "evidence_path": timed_a,
                    "evidence_sha256": self.artifact_record(timed_a)["sha256"],
                },
                {
                    "id": "timed-run-b",
                    "duration_seconds": 450,
                    "active_control_seconds": 300,
                    "route_result": "STABLE_BEACON_HOOK",
                    "evidence_path": timed_b,
                    "evidence_sha256": self.artifact_record(timed_b)["sha256"],
                },
            ],
            "transition_soak": {
                "loops": 10,
                "heap_delta_bytes": 0,
                "resource_delta_count": 0,
                "peak_free_heap_bytes": 700000,
                "evidence_path": soak,
                "evidence_sha256": self.artifact_record(soak)["sha256"],
            },
            "performance": {
                "fps_min": 30,
                "free_heap_min_bytes": 700000,
                "sustained_sub30_windows": 0,
                "evidence_path": performance,
                "evidence_sha256": self.artifact_record(performance)["sha256"],
            },
            "qa_matrix": {
                name: "PASS" for name in qa_names
            },
            "evidence_artifacts": {
                "required_count": 22,
                "timed_and_metric_artifacts": {
                    "timed_runs[1]": self.artifact_record(timed_a),
                    "timed_runs[2]": self.artifact_record(timed_b),
                    "transition_soak": self.artifact_record(soak),
                    "performance": self.artifact_record(performance),
                },
                "qa_artifacts": {
                    name: self.artifact_record(relative)
                    for name, relative in qa_artifacts.items()
                },
            },
        }
        manifest = self.write_manifest(payload)
        result = self.run_command([
            str(VALIDATOR),
            "--manifest",
            str(manifest),
            "--rom",
            str(self.rom),
            "--artifact-root",
            str(self.root),
        ])
        self.assertEqual(result.returncode, 0, result.stdout)
        output = json.loads(result.stdout)
        self.assertEqual(output["certification"], "COMPLETE")
        self.assertEqual(output["timed_run_count"], 2)
        self.assertEqual(output["timed_run_median_seconds"], 420)

    def test_complete_manifest_rejects_low_fps_and_missing_qa(self) -> None:
        payload = self.base_payload()
        timed_a = self.write_artifact("timed-lowfps-a.md")
        timed_b = self.write_artifact("timed-lowfps-b.md")
        soak = self.write_artifact("soak-lowfps.md")
        performance = self.write_artifact("performance-lowfps.md")
        payload.update(
            {
                "certification": "COMPLETE",
                "ares": {
                    "version": "v148",
                    "executable_sha256": PINNED_ARES_SHA256,
                    "homebrew_mode": True,
                    "expansion_pak": False,
                },
                "timed_runs": [
                    {
                        "duration_seconds": 390,
                        "active_control_seconds": 260,
                        "route_result": "STABLE_BEACON_HOOK",
                        "evidence_path": timed_a,
                        "evidence_sha256": self.artifact_record(timed_a)["sha256"],
                    },
                    {
                        "duration_seconds": 450,
                        "active_control_seconds": 300,
                        "route_result": "STABLE_BEACON_HOOK",
                        "evidence_path": timed_b,
                        "evidence_sha256": self.artifact_record(timed_b)["sha256"],
                    },
                ],
                "transition_soak": {
                    "loops": 10,
                    "heap_delta_bytes": 0,
                    "resource_delta_count": 0,
                    "peak_free_heap_bytes": 700000,
                    "evidence_path": soak,
                    "evidence_sha256": self.artifact_record(soak)["sha256"],
                },
                "performance": {
                    "fps_min": 29,
                    "free_heap_min_bytes": 700000,
                    "sustained_sub30_windows": 0,
                    "evidence_path": performance,
                    "evidence_sha256": self.artifact_record(performance)["sha256"],
                },
                "qa_matrix": {},
            }
        )
        manifest = self.write_manifest(payload)
        result = self.run_command([
            str(VALIDATOR),
            "--manifest",
            str(manifest),
            "--rom",
            str(self.rom),
            "--artifact-root",
            str(self.root),
        ])
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("performance.fps_min is below 30", result.stdout)

    def test_complete_manifest_rejects_missing_artifact_bindings(self) -> None:
        payload = self.base_payload()
        payload.update(
            {
                "certification": "COMPLETE",
                "ares": {
                    "version": "v148",
                    "executable_sha256": PINNED_ARES_SHA256,
                    "homebrew_mode": True,
                    "expansion_pak": False,
                },
                "timed_runs": [
                    {"duration_seconds": 390, "active_control_seconds": 260, "route_result": "STABLE_BEACON_HOOK"},
                    {"duration_seconds": 450, "active_control_seconds": 300, "route_result": "STABLE_BEACON_HOOK"},
                ],
                "transition_soak": {
                    "loops": 10,
                    "heap_delta_bytes": 0,
                    "resource_delta_count": 0,
                    "peak_free_heap_bytes": 700000,
                },
                "performance": {
                    "fps_min": 30,
                    "free_heap_min_bytes": 700000,
                    "sustained_sub30_windows": 0,
                },
                "qa_matrix": {name: "PASS" for name in (
                    "cold_boot_default_name",
                    "cold_boot_custom_name",
                    "slate_watched",
                    "slate_skipped",
                    "required_annex_route",
                    "optional_examines",
                    "save_reboot_resume",
                    "battle_alternate_inputs",
                    "battle_victory",
                    "battle_defeat_retry",
                    "battle_defeat_return",
                    "horizon_break_legal",
                    "horizon_break_illegal",
                    "dialogue_rapid_confirm_cancel",
                    "controller_disconnect_reconnect",
                    "corrupted_eeprom_fallback",
                    "completed_sector_reentry",
                    "stable_post_chapter_state",
                )},
            }
        )
        manifest = self.write_manifest(payload)
        result = self.run_command([
            str(VALIDATOR),
            "--manifest",
            str(manifest),
            "--rom",
            str(self.rom),
            "--artifact-root",
            str(self.root),
        ])
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("timed_runs[1].path", result.stdout)

    def complete_capture_packet(self) -> dict[str, object]:
        qa_rows = {
            name: {
                "status": "PASS",
                "evidence_path": self.write_artifact(f"qa/{name}.md", f"{name}: PASS\n"),
                "notes": f"{name} observed in Ares v148",
            }
            for name in (
                "cold_boot_default_name",
                "cold_boot_custom_name",
                "slate_watched",
                "slate_skipped",
                "required_annex_route",
                "optional_examines",
                "save_reboot_resume",
                "battle_alternate_inputs",
                "battle_victory",
                "battle_defeat_retry",
                "battle_defeat_return",
                "horizon_break_legal",
                "horizon_break_illegal",
                "dialogue_rapid_confirm_cancel",
                "controller_disconnect_reconnect",
                "corrupted_eeprom_fallback",
                "completed_sector_reentry",
                "stable_post_chapter_state",
            )
        }
        return {
            "schema": "n64game-certification-capture-packet-v1",
            "certification_request": "COMPLETE",
            "rom": {"sha256": self.rom_sha, "size": self.rom.stat().st_size},
            "ares": {
                "version": "v148",
                "executable_sha256": PINNED_ARES_SHA256,
                "homebrew_mode": True,
                "expansion_pak": False,
            },
            "timed_runs": [
                {
                    "id": "timed-run-a",
                    "duration_seconds": 390,
                    "active_control_seconds": 260,
                    "route_result": "STABLE_BEACON_HOOK",
                    "evidence_path": self.write_artifact("timed-run-a.md"),
                },
                {
                    "id": "timed-run-b",
                    "duration_seconds": 450,
                    "active_control_seconds": 300,
                    "route_result": "STABLE_BEACON_HOOK",
                    "evidence_path": self.write_artifact("timed-run-b.md"),
                },
            ],
            "transition_soak": {
                "loops": 10,
                "heap_delta_bytes": 0,
                "resource_delta_count": 0,
                "peak_free_heap_bytes": 700000,
                "evidence_path": self.write_artifact("transition-soak.md"),
            },
            "performance": {
                "fps_min": 30,
                "free_heap_min_bytes": 700000,
                "sustained_sub30_windows": 0,
                "evidence_path": self.write_artifact("performance.md"),
            },
            "qa_matrix": qa_rows,
        }

    def test_assembler_rejects_placeholder_capture_packet(self) -> None:
        packet = self.root / "packet.json"
        packet.write_text(
            json.dumps(
                {
                    "schema": "n64game-certification-capture-packet-v1",
                    "certification_request": "COMPLETE",
                    "rom": {"sha256": self.rom_sha, "size": self.rom.stat().st_size},
                    "ares": {
                        "version": "v148",
                        "executable_sha256": PINNED_ARES_SHA256,
                        "homebrew_mode": True,
                        "expansion_pak": False,
                    },
                    "timed_runs": [
                        {
                            "id": "timed-run-a",
                            "duration_seconds": 390,
                            "active_control_seconds": 260,
                            "route_result": "PENDING",
                            "evidence_path": "missing.md",
                        }
                    ],
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        result = self.run_command(
            [
                str(ASSEMBLER),
                "--rom",
                str(self.rom),
                "--packet",
                str(packet),
                "--manifest",
                str(self.root / "assembled.json"),
                "--artifact-root",
                str(self.root),
            ]
        )
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("placeholder", result.stdout)

    def test_assembler_writes_complete_validator_compatible_manifest(self) -> None:
        packet = self.root / "packet.json"
        manifest = self.root / "assembled.json"
        packet.write_text(json.dumps(self.complete_capture_packet(), sort_keys=True), encoding="utf-8")
        result = self.run_command(
            [
                str(ASSEMBLER),
                "--rom",
                str(self.rom),
                "--packet",
                str(packet),
                "--manifest",
                str(manifest),
                "--artifact-root",
                str(self.root),
            ]
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        assembled = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(assembled["certification"], "COMPLETE")
        self.assertEqual(assembled["evidence_artifacts"]["required_count"], 22)
        self.assertIn("evidence_sha256", assembled["timed_runs"][0])
        validation = self.run_command([
            str(VALIDATOR),
            "--manifest",
            str(manifest),
            "--rom",
            str(self.rom),
            "--artifact-root",
            str(self.root),
        ])
        self.assertEqual(validation.returncode, 0, validation.stdout)

        Path(self.root / assembled["timed_runs"][0]["evidence_path"]).write_text(
            "tampered after assembly\n",
            encoding="utf-8",
        )
        tampered = self.run_command([
            str(VALIDATOR),
            "--manifest",
            str(manifest),
            "--rom",
            str(self.rom),
            "--artifact-root",
            str(self.root),
        ])
        self.assertNotEqual(tampered.returncode, 0, tampered.stdout)
        self.assertIn("evidence_sha256 does not match", tampered.stdout)


if __name__ == "__main__":
    unittest.main()
