from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import n64game_certification as certification  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resequence_telemetry(text: str) -> str:
    sequence = 0
    output = []
    for line in text.splitlines():
        if line.startswith("N64G_TELEM "):
            line = re.sub(r"\bseq=[0-9]+", f"seq={sequence}", line, count=1)
            sequence += 1
        output.append(line)
    return "\n".join(output) + "\n"


def replace_in_telemetry_line(text: str, needle: str, old: str, new: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("N64G_TELEM ") and needle in line:
            if old not in line:
                raise AssertionError(f"fixture mutation token is absent: {old}")
            lines[index] = line.replace(old, new, 1)
            return "\n".join(lines) + "\n"
    raise AssertionError(f"fixture mutation line is absent: {needle}")


class LogBuilder:
    def __init__(self, rom_sha256: str, run_id: str, eeprom_sha256: str | None = None) -> None:
        self.rom_sha256 = rom_sha256
        self.lines = [
            f"ares_version={certification.PINNED_ARES_VERSION}",
            f"ares_sha256={certification.PINNED_ARES_SHA256}",
            f"rom_sha256={rom_sha256}",
            "homebrew_mode=true",
            "expansion_pak=false",
            "defocus=allow",
            f"test_fixture_id={run_id}",
        ]
        if eeprom_sha256 is not None:
            self.lines.append(f"eeprom_sha256={eeprom_sha256}")
        self.sequence = 0
        self.transition_count = 0

    def add(self, event: str, **fields: Any) -> None:
        values = {
            "schema": 1,
            "seq": self.sequence,
            "event": event,
            "status": certification.STATUS,
            **fields,
        }
        expected = certification.EVENT_FIELDS[event]
        if set(values) != set(expected):
            raise AssertionError(f"fixture fields differ for {event}: {set(values) ^ set(expected)}")
        self.lines.append("N64G_TELEM " + " ".join(f"{key}={values[key]}" for key in expected))
        self.sequence += 1

    def session(self, boot_ticks: int = 100, ready_ticks: int = 110) -> None:
        self.add(
            "session",
            ticks_per_second=1000,
            target_fps=30,
            budget_ticks=34,
            tolerance_ticks=1,
            boot_ticks=boot_ticks,
            ready_ticks=ready_ticks,
            heap_baseline_bytes=700000,
        )

    def load(self, *, mask: int, outcome: str, slot: Any = "NONE", sequence: Any = "NONE", scene: Any = "NONE", quest: Any = "NONE") -> None:
        self.add(
            "save_load",
            wall_ticks=120,
            eeprom_present=1,
            valid_slot_mask=mask,
            outcome=outcome,
            selected_slot=slot,
            save_sequence=sequence,
            checkpoint_scene=scene,
            checkpoint_quest=quest,
        )

    def transition(self, source: int, target: int, wall: int, frames: int, heap: int = 600000, cause: str = "core") -> None:
        self.transition_count += 1
        self.add(
            "transition",
            wall_ticks=wall,
            cause=cause,
            **{"from": source},
            to=target,
            transition_count=self.transition_count,
            play_ticks=frames,
            active_control_ticks=min(frames, 8000),
            free_heap_bytes=heap,
            heap_low_water_bytes=min(heap, 600000),
            submitted_frames=frames,
            measured_intervals=max(frames - 1, 0),
            invalid_samples=0,
        )

    def scene_summary(self, scene: int, wall: int, frames: int) -> None:
        measured = max(frames - 1, 0)
        self.add(
            "scene_summary",
            wall_ticks=wall,
            scene=scene,
            submitted_frames=frames,
            measured_intervals=measured,
            over_budget_frames=min(2, measured),
            missed_deadlines=min(1, measured),
            max_frame_ticks=40,
            max_over_budget_streak=1,
            invalid_samples=0,
        )

    def text(self) -> str:
        return "\n".join(self.lines) + "\n"


def timing_log(rom_sha256: str, run_id: str, duration: int = 400000) -> str:
    log = LogBuilder(rom_sha256, run_id)
    log.session()
    log.load(mask=0, outcome="none")
    route = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 3), (3, 5)]
    scene_frames = {0: 30, 1: 120, 2: 240, 3: 4500, 4: 3000, 5: 2}
    total_frames = 0
    wall = 10000
    for source, target in route:
        total_frames += scene_frames[source]
        log.scene_summary(source, wall, scene_frames[source])
        log.transition(source, target, wall + 1, total_frames)
        wall += 50000
    log.add(
        "save_write",
        wall_ticks=399900,
        outcome="verified",
        reason="none",
        slot=0,
        save_sequence=2,
        chapter_completion=1,
        checkpoint_scene=5,
        checkpoint_quest=7,
    )
    log.scene_summary(5, 400000, scene_frames[5])
    log.add(
        "chapter_stable",
        wall_ticks=100 + duration,
        duration_ticks=duration,
        play_ticks=12000,
        active_control_ticks=8000,
        save_verified=1,
        save_sequence=2,
        submitted_frames=total_frames + scene_frames[5],
        measured_intervals=total_frames + scene_frames[5] - 1,
        over_budget_frames=8,
        missed_deadlines=4,
        max_frame_ticks=42,
        max_over_budget_streak=2,
        heap_low_water_bytes=600000,
        invalid_samples=0,
    )
    return log.text()


def soak_log(rom_sha256: str, run_id: str, loop_count: int = 11, final_heap: int = 600000) -> str:
    log = LogBuilder(rom_sha256, run_id)
    log.session()
    log.load(mask=1, outcome="selected", slot=0, sequence=5, scene=3, quest=4)
    log.transition(0, 1, 1000, 30)
    log.transition(1, 3, 2000, 60, cause="continue_resume")
    frames = 60
    wall = 3000
    for index in range(loop_count):
        frames += 100
        log.transition(3, 4, wall, frames, heap=600100)
        frames += 100
        heap = final_heap if index == loop_count - 1 else 600000
        log.transition(4, 3, wall + 1000, frames, heap=heap)
        wall += 2000
    return log.text()


def save_slot(sequence: int, corrupt: bool = False) -> bytes:
    slot = bytearray(64)
    slot[:4] = b"N64G"
    struct.pack_into(">H", slot, 4, 3)
    struct.pack_into(">H", slot, 6, 64)
    struct.pack_into(">I", slot, 8, sequence)
    slot[12] = 4
    slot[13:17] = b"TEST"
    slot[21] = 3
    slot[22] = 4
    slot[23] = 0x23
    struct.pack_into(">H", slot, 24, 92)
    struct.pack_into(">H", slot, 26, 78)
    struct.pack_into(">I", slot, 32, 100)
    struct.pack_into(">I", slot, 36, 50)
    slot[40] = 0
    slot[41] = 1
    value = certification._fnv1a(slot[:60])
    struct.pack_into(">I", slot, 60, value ^ (1 if corrupt else 0))
    return bytes(slot)


def save_log(rom_sha256: str, eeprom_sha256: str, run_id: str, mask: int, outcome: str, slot: Any = "NONE", sequence: Any = "NONE") -> str:
    log = LogBuilder(rom_sha256, run_id, eeprom_sha256)
    log.session()
    log.load(mask=mask, outcome=outcome, slot=slot, sequence=sequence, scene=3 if slot != "NONE" else "NONE", quest=4 if slot != "NONE" else "NONE")
    if slot != "NONE":
        log.transition(0, 1, 1000, 30)
        log.transition(1, 3, 2000, 60, cause="continue_resume")
    return log.text()


class EvidencePackage:
    def __init__(self, root: Path) -> None:
        self.root = root
        (root / "logs").mkdir()
        (root / "saves").mkdir()
        self.rom = root / "game.z64"
        self.rom.write_bytes(b"\x80\x37\x12\x40" + bytes(4092))
        self.rom_hash = sha256(self.rom)

        timing_specs = []
        for index, (slate, name) in enumerate((("watched", "default"), ("skipped", "custom")), 1):
            path = root / "logs" / f"timing-{index}.log"
            path.write_text(timing_log(self.rom_hash, f"timing-{index}"), encoding="utf-8")
            timing_specs.append({
                "id": f"timing-{index}",
                "log_path": f"logs/{path.name}",
                "log_sha256": sha256(path),
                "slate_path": slate,
                "name_path": name,
                "cold_boot": True,
                "continue_used": False,
                "idle_declared_ms": 0,
            })

        soak = root / "logs" / "soak.log"
        soak.write_text(soak_log(self.rom_hash, "soak"), encoding="utf-8")

        save_specs = []
        scenarios = (
            ("valid_resume", save_slot(5) + bytes([0xFF]) * 64, 1, "selected", 0, 5),
            ("latest_corrupt_fallback", save_slot(5) + save_slot(6, corrupt=True), 1, "selected", 0, 5),
            ("all_corrupt_new_game", save_slot(7, corrupt=True) + bytes([0xFF]) * 64, 0, "none", "NONE", "NONE"),
        )
        for scenario, first_slots, mask, outcome, slot, sequence in scenarios:
            eeprom = root / "saves" / f"{scenario}.eep"
            eeprom.write_bytes(first_slots + bytes([0xFF]) * (512 - len(first_slots)))
            log = root / "logs" / f"{scenario}.log"
            eeprom_hash = sha256(eeprom)
            log.write_text(save_log(self.rom_hash, eeprom_hash, scenario, mask, outcome, slot, sequence), encoding="utf-8")
            save_specs.append({
                "id": scenario,
                "scenario": scenario,
                "log_path": f"logs/{log.name}",
                "log_sha256": sha256(log),
                "eeprom_path": f"saves/{eeprom.name}",
                "eeprom_sha256": eeprom_hash,
            })

        self.manifest_data = {
            "schema": certification.SCHEMA,
            "status": certification.STATUS,
            "rom_sha256": self.rom_hash,
            "ares_sha256": certification.PINNED_ARES_SHA256,
            "timing_runs": timing_specs,
            "soak_run": {
                "id": "soak",
                "log_path": "logs/soak.log",
                "log_sha256": sha256(soak),
                "warmup_loop_count": 1,
            },
            "save_runs": save_specs,
        }
        self.manifest = root / "evidence.json"
        self.write_manifest()

    def write_manifest(self) -> None:
        self.manifest.write_text(json.dumps(self.manifest_data, indent=2) + "\n", encoding="utf-8")

    def replace_log(self, relative: str, text: str) -> None:
        path = self.root / relative
        path.write_text(text, encoding="utf-8")
        for entry in [*self.manifest_data["timing_runs"], self.manifest_data["soak_run"], *self.manifest_data["save_runs"]]:
            if entry["log_path"] == relative:
                entry["log_sha256"] = sha256(path)
        self.write_manifest()


class CertificationEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="n64game-certification-")
        self.package = EvidencePackage(Path(self.temp.name))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def assert_rejected(self) -> None:
        with self.assertRaises(certification.EvidenceError):
            certification.validate(self.package.manifest, self.package.rom)

    def test_runtime_emitters_match_the_validator_field_schema(self) -> None:
        source = (ROOT / "src" / "main.c").read_text(encoding="utf-8")
        formats = []
        for call in re.findall(r"debugf\((.*?)\);", source, flags=re.DOTALL):
            pieces = re.findall(r'"(?:\\.|[^"\\])*"', call)
            if not pieces:
                continue
            rendered = "".join(ast.literal_eval(piece) for piece in pieces)
            if rendered.startswith("N64G_TELEM "):
                formats.append(rendered)
        observed_events = set()
        for rendered in formats:
            event = re.search(r" event=([a-z_]+) ", rendered)
            self.assertIsNotNone(event)
            name = event.group(1)
            observed_events.add(name)
            fields = tuple(re.findall(r"\b([a-z][a-z0-9_]*)=", rendered))
            self.assertEqual(fields, certification.EVENT_FIELDS[name])
        self.assertEqual(observed_events, set(certification.EVENT_FIELDS))

    def test_real_pinned_ares_check_only_emits_canonical_version_preamble(self) -> None:
        ares = Path.home() / "Applications/Emulators/ares-v148/ares.app/Contents/MacOS/ares"
        if not ares.is_file():
            self.skipTest("pinned macOS Ares v148 binary is not installed on this host")
        self.assertFalse(ares.is_symlink())
        self.assertEqual(sha256(ares), certification.PINNED_ARES_SHA256)
        with tempfile.TemporaryDirectory(prefix="n64game-ares-version-") as directory:
            state = Path(directory) / "state"
            raw_version = subprocess.run(
                [str(ares), "--settings-file", str(state / "shape-settings.bml"), "--version"],
                cwd=ROOT,
                capture_output=True,
                check=False,
            )
            self.assertEqual(raw_version.returncode, 0, raw_version.stderr.decode("utf-8", errors="replace"))
            self.assertEqual(raw_version.stdout, b"\nv148\n")
            rom_hash = sha256(self.package.rom)
            environment = {
                **os.environ,
                "N64GAME_ARES_BINARY": str(ares),
                "N64GAME_ARES_STATE": str(state),
            }
            checked = subprocess.run(
                [
                    str(ROOT / "scripts" / "run-ares"),
                    "--homebrew-mode",
                    "--check-only",
                    f"--expected-rom-sha256={rom_hash}",
                    str(self.package.rom),
                ],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        self.assertEqual(checked.stderr, "")
        self.assertEqual(
            checked.stdout.splitlines(),
            [
                f"ares_version={certification.PINNED_ARES_VERSION}",
                f"ares_sha256={certification.PINNED_ARES_SHA256}",
                f"rom_sha256={rom_hash}",
                "homebrew_mode=true",
                "expansion_pak=false",
                "defocus=allow",
            ],
        )

    def test_complete_contract_passes_without_claiming_certification(self) -> None:
        result = certification.validate(self.package.manifest, self.package.rom)
        self.assertEqual(result["result"], "EVIDENCE_CONTRACT_PASS")
        self.assertEqual(result["certification"], "NOT_CLAIMED")
        self.assertEqual(result["soak_run"]["measured_loop_count"], 10)
        self.assertEqual({item["scenario"] for item in result["save_runs"]}, {
            "valid_resume", "latest_corrupt_fallback", "all_corrupt_new_game",
        })
        self.assertNotIn("CERTIFIED", json.dumps(result))

    def test_cli_is_fail_closed_and_machine_readable(self) -> None:
        command = [
            str(ROOT / "scripts" / "validate-certification-evidence"),
            "--manifest", str(self.package.manifest),
            "--rom", str(self.package.rom),
        ]
        passed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)
        self.assertEqual(json.loads(passed.stdout)["certification"], "NOT_CLAIMED")
        malformed = subprocess.run(
            [*command[:-1], str(self.package.root)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(malformed.returncode, 0)
        self.assertIn("EVIDENCE_CONTRACT_FAIL", malformed.stderr)
        self.assertNotIn("Traceback", malformed.stderr)
        self.package.manifest_data["rom_sha256"] = "0" * 64
        self.package.write_manifest()
        failed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("EVIDENCE_CONTRACT_FAIL", failed.stderr)
        self.assertEqual(failed.stdout, "")

    def test_hash_sequence_and_duration_deaths_are_rejected(self) -> None:
        with self.subTest("declared log hash mismatch"):
            original = self.package.manifest_data["timing_runs"][0]["log_sha256"]
            self.package.manifest_data["timing_runs"][0]["log_sha256"] = "0" * 64
            self.package.write_manifest()
            self.assert_rejected()
            self.package.manifest_data["timing_runs"][0]["log_sha256"] = original
            self.package.write_manifest()

        with self.subTest("telemetry sequence gap"):
            relative = "logs/timing-1.log"
            original_text = (self.package.root / relative).read_text(encoding="utf-8")
            mutated = original_text.replace("seq=2 event=scene_summary", "seq=99 event=scene_summary", 1)
            self.package.replace_log(relative, mutated)
            self.assert_rejected()
            self.package.replace_log(relative, original_text)

        with self.subTest("timing below six minutes"):
            relative = "logs/timing-1.log"
            original_text = (self.package.root / relative).read_text(encoding="utf-8")
            mutated = original_text.replace("wall_ticks=400100 duration_ticks=400000", "wall_ticks=300100 duration_ticks=300000")
            self.package.replace_log(relative, mutated)
            self.assert_rejected()
            self.package.replace_log(relative, original_text)

        with self.subTest("timing above ten minutes"):
            relative = "logs/timing-1.log"
            original_text = (self.package.root / relative).read_text(encoding="utf-8")
            mutated = original_text.replace("wall_ticks=400100 duration_ticks=400000", "wall_ticks=700100 duration_ticks=700000")
            self.package.replace_log(relative, mutated)
            self.assert_rejected()
            self.package.replace_log(relative, original_text)

        with self.subTest("two individually legal runs still miss the 6-8 minute median"):
            originals = {}
            for relative in ("logs/timing-1.log", "logs/timing-2.log"):
                originals[relative] = (self.package.root / relative).read_text(encoding="utf-8")
                mutated = originals[relative].replace(
                    "wall_ticks=400100 duration_ticks=400000",
                    "wall_ticks=590100 duration_ticks=590000",
                )
                self.package.replace_log(relative, mutated)
            self.assert_rejected()
            for relative, original_text in originals.items():
                self.package.replace_log(relative, original_text)

        with self.subTest("active control below four minutes"):
            relative = "logs/timing-1.log"
            original_text = (self.package.root / relative).read_text(encoding="utf-8")
            mutated = original_text.replace("active_control_ticks=8000", "active_control_ticks=7199")
            self.package.replace_log(relative, mutated)
            self.assert_rejected()
            self.package.replace_log(relative, original_text)

        with self.subTest("timing runs use different guest clocks"):
            relative = "logs/timing-2.log"
            original_text = (self.package.root / relative).read_text(encoding="utf-8")
            mutated = original_text.replace(
                "ticks_per_second=1000 target_fps=30 budget_ticks=34 tolerance_ticks=1",
                "ticks_per_second=1001 target_fps=30 budget_ticks=34 tolerance_ticks=2",
            )
            self.package.replace_log(relative, mutated)
            self.assert_rejected()
            self.package.replace_log(relative, original_text)

    def test_final_save_order_freshness_and_stable_clock_deaths_are_rejected(self) -> None:
        relative = "logs/timing-1.log"
        original_text = (self.package.root / relative).read_text(encoding="utf-8")

        with self.subTest("chapter stable precedes matching final write"):
            lines = original_text.splitlines()
            write_index = next(index for index, line in enumerate(lines) if " event=save_write " in line)
            write = lines.pop(write_index).replace("wall_ticks=399900", "wall_ticks=400200")
            stable_index = next(index for index, line in enumerate(lines) if " event=chapter_stable " in line)
            lines.insert(stable_index + 1, write)
            self.package.replace_log(relative, resequence_telemetry("\n".join(lines) + "\n"))
            self.assert_rejected()
            self.package.replace_log(relative, original_text)

        with self.subTest("verified rebound save follows chapter stable"):
            lines = original_text.splitlines()
            final_write = next(line for line in lines if " event=save_write " in line)
            rebound = final_write.replace("wall_ticks=399900", "wall_ticks=400200")
            rebound = rebound.replace("slot=0", "slot=1")
            rebound = rebound.replace("save_sequence=2", "save_sequence=3")
            rebound = rebound.replace("chapter_completion=1", "chapter_completion=0")
            lines.append(rebound)
            self.package.replace_log(relative, resequence_telemetry("\n".join(lines) + "\n"))
            self.assert_rejected()
            self.package.replace_log(relative, original_text)

        with self.subTest("stable duration does not equal wall minus boot"):
            mutated = original_text.replace("duration_ticks=400000", "duration_ticks=399999", 1)
            self.package.replace_log(relative, mutated)
            self.assert_rejected()
            self.package.replace_log(relative, original_text)

        with self.subTest("zero final sequence"):
            mutated = original_text.replace("save_sequence=2", "save_sequence=0")
            self.package.replace_log(relative, mutated)
            self.assert_rejected()
            self.package.replace_log(relative, original_text)

        with self.subTest("final sequence reuses a prior verified sequence"):
            lines = original_text.splitlines()
            final_index = next(index for index, line in enumerate(lines) if " event=save_write " in line)
            prior = lines[final_index]
            prior = prior.replace("wall_ticks=399900", "wall_ticks=350000")
            prior = prior.replace("chapter_completion=1", "chapter_completion=0")
            prior = prior.replace("checkpoint_scene=5", "checkpoint_scene=3")
            prior = prior.replace("checkpoint_quest=7", "checkpoint_quest=4")
            lines.insert(final_index, prior)
            self.package.replace_log(relative, resequence_telemetry("\n".join(lines) + "\n"))
            self.assert_rejected()
            self.package.replace_log(relative, original_text)

    def test_heap_stream_consistency_deaths_are_rejected(self) -> None:
        relative = "logs/timing-1.log"
        original_text = (self.package.root / relative).read_text(encoding="utf-8")

        with self.subTest("low water exceeds simultaneous free heap"):
            mutated = replace_in_telemetry_line(
                original_text,
                "event=transition",
                "free_heap_bytes=600000",
                "free_heap_bytes=1",
            )
            self.package.replace_log(relative, mutated)
            self.assert_rejected()
            self.package.replace_log(relative, original_text)

        with self.subTest("internally consistent one-byte heap still breaches floor"):
            mutated = replace_in_telemetry_line(
                original_text,
                "event=transition",
                "free_heap_bytes=600000 heap_low_water_bytes=600000",
                "free_heap_bytes=1 heap_low_water_bytes=1",
            )
            self.package.replace_log(relative, mutated)
            self.assert_rejected()
            self.package.replace_log(relative, original_text)

        with self.subTest("low water increases"):
            mutated = replace_in_telemetry_line(
                original_text,
                "transition_count=2",
                "free_heap_bytes=600000 heap_low_water_bytes=600000",
                "free_heap_bytes=650000 heap_low_water_bytes=610000",
            )
            self.package.replace_log(relative, mutated)
            self.assert_rejected()
            self.package.replace_log(relative, original_text)

        with self.subTest("low water exceeds session baseline"):
            mutated = replace_in_telemetry_line(
                original_text,
                "event=session",
                "heap_baseline_bytes=700000",
                "heap_baseline_bytes=590000",
            )
            self.package.replace_log(relative, mutated)
            self.assert_rejected()
            self.package.replace_log(relative, original_text)

    def test_save_log_must_bind_exact_prelaunch_eeprom_hash(self) -> None:
        entry = self.package.manifest_data["save_runs"][0]
        relative = entry["log_path"]
        original_text = (self.package.root / relative).read_text(encoding="utf-8")

        with self.subTest("missing EEPROM preamble"):
            mutated = "\n".join(
                line for line in original_text.splitlines()
                if not line.startswith("eeprom_sha256=")
            ) + "\n"
            self.package.replace_log(relative, mutated)
            self.assert_rejected()
            self.package.replace_log(relative, original_text)

        with self.subTest("different EEPROM preamble"):
            mutated = re.sub(
                r"^eeprom_sha256=[0-9a-f]{64}$",
                "eeprom_sha256=" + "0" * 64,
                original_text,
                count=1,
                flags=re.MULTILINE,
            )
            self.package.replace_log(relative, mutated)
            self.assert_rejected()
            self.package.replace_log(relative, original_text)

        wrapper = (ROOT / "scripts" / "run-ares").read_text(encoding="utf-8")
        self.assertIn("--expected-eeprom-sha256=*", wrapper)
        self.assertIn('EEPROM_PATH="$STATE_ROOT/Saves/Nintendo 64/${ROM_FILENAME%.*}.eeprom"', wrapper)
        self.assertIn("printf 'eeprom_sha256=%s\\n'", wrapper)

    def test_scene_soak_and_save_deaths_are_rejected(self) -> None:
        with self.subTest("missing scene performance"):
            relative = "logs/timing-1.log"
            original_text = (self.package.root / relative).read_text(encoding="utf-8")
            mutated = original_text.replace("scene=4 submitted_frames=3000", "scene=3 submitted_frames=3000", 1)
            self.package.replace_log(relative, mutated)
            self.assert_rejected()
            self.package.replace_log(relative, original_text)

        with self.subTest("only nine measured loops"):
            relative = "logs/soak.log"
            original_text = (self.package.root / relative).read_text(encoding="utf-8")
            self.package.replace_log(relative, soak_log(self.package.rom_hash, "soak-short", loop_count=10))
            self.assert_rejected()
            self.package.replace_log(relative, original_text)

        with self.subTest("heap loss at a measured boundary"):
            relative = "logs/soak.log"
            original_text = (self.package.root / relative).read_text(encoding="utf-8")
            self.package.replace_log(relative, soak_log(self.package.rom_hash, "soak-loss", final_heap=599999))
            self.assert_rejected()
            self.package.replace_log(relative, original_text)

        with self.subTest("save snapshot disagrees with scenario"):
            entry = self.package.manifest_data["save_runs"][1]
            eeprom = self.package.root / entry["eeprom_path"]
            log = self.package.root / entry["log_path"]
            original_bytes = eeprom.read_bytes()
            original_eeprom_hash = entry["eeprom_sha256"]
            original_log = log.read_text(encoding="utf-8")
            eeprom.write_bytes(save_slot(5) + save_slot(6) + original_bytes[128:])
            entry["eeprom_sha256"] = sha256(eeprom)
            rebound_log = original_log.replace(
                f"eeprom_sha256={original_eeprom_hash}",
                f"eeprom_sha256={entry['eeprom_sha256']}",
                1,
            )
            self.package.replace_log(entry["log_path"], rebound_log)
            self.assert_rejected()
            eeprom.write_bytes(original_bytes)
            entry["eeprom_sha256"] = original_eeprom_hash
            self.package.replace_log(entry["log_path"], original_log)

    def test_path_duplicate_key_and_symlink_deaths_are_rejected(self) -> None:
        with self.subTest("path traversal"):
            original = self.package.manifest_data["timing_runs"][0]["log_path"]
            self.package.manifest_data["timing_runs"][0]["log_path"] = "../outside.log"
            self.package.write_manifest()
            self.assert_rejected()
            self.package.manifest_data["timing_runs"][0]["log_path"] = original
            self.package.write_manifest()

        with self.subTest("control character in evidence path"):
            original = self.package.manifest_data["timing_runs"][0]["log_path"]
            self.package.manifest_data["timing_runs"][0]["log_path"] = "logs/bad\nname.log"
            self.package.write_manifest()
            self.assert_rejected()
            self.package.manifest_data["timing_runs"][0]["log_path"] = original
            self.package.write_manifest()

        with self.subTest("symlinked evidence"):
            target = self.package.root / "logs" / "timing-1.log"
            link = self.package.root / "logs" / "linked.log"
            os.symlink(target.name, link)
            original = self.package.manifest_data["timing_runs"][0]["log_path"]
            self.package.manifest_data["timing_runs"][0]["log_path"] = "logs/linked.log"
            self.package.write_manifest()
            self.assert_rejected()
            self.package.manifest_data["timing_runs"][0]["log_path"] = original
            self.package.write_manifest()

        with self.subTest("duplicate JSON key"):
            data = self.package.manifest.read_text(encoding="utf-8")
            self.package.manifest.write_text(data.replace('"schema":', '"schema": "duplicate",\n  "schema":', 1), encoding="utf-8")
            self.assert_rejected()


if __name__ == "__main__":
    unittest.main()
