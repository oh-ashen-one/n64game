#!/usr/bin/env python3
"""Fail-closed validation for local N64GAME certification evidence.

This validates evidence integrity and the bounded telemetry contract. It never
awards certification; successful output is explicitly NOT_CLAIMED.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import struct
from pathlib import Path, PurePath
from typing import Any, Iterable


SCHEMA = "n64game-certification-evidence-v1"
STATUS = "INSTRUMENTATION_ONLY"
PINNED_ARES_VERSION = "ares version v148"
PINNED_ARES_SHA256 = "7a49f00f96a691458461d7c9cf453d95c0f5c054389bbd87c253987b8b6fa345"
MIN_HEAP_BYTES = 524_288
MAX_MANIFEST_BYTES = 256 * 1024
MAX_LOG_BYTES = 16 * 1024 * 1024
MAX_ROM_BYTES = 64 * 1024 * 1024
EEPROM_BYTES = 512
SAVE_SLOT_BYTES = 64
SAVE_SLOT_COUNT = 2
SAVE_VERSION = 3
HEX_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
TOKEN_KEY = re.compile(r"[a-z][a-z0-9_]*\Z")
TOKEN_VALUE = re.compile(r"[A-Za-z0-9_.-]+\Z")


class EvidenceError(ValueError):
    """The package is incomplete, malformed, inconsistent, or unsupported."""


class _DuplicateKey(EvidenceError):
    pass


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _exact_keys(value: Any, keys: Iterable[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceError(f"{label} must be an object")
    expected = set(keys)
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise EvidenceError(f"{label} keys differ; missing={missing} extra={extra}")
    return value


def _require_string(value: Any, label: str) -> str:
    if type(value) is not str or not value:
        raise EvidenceError(f"{label} must be a non-empty string")
    return value


def _require_hash(value: Any, label: str) -> str:
    text = _require_string(value, label)
    if HEX_SHA256.fullmatch(text) is None:
        raise EvidenceError(f"{label} must be a lowercase SHA-256")
    return text


def _require_bool(value: Any, expected: bool, label: str) -> None:
    if type(value) is not bool or value is not expected:
        raise EvidenceError(f"{label} must be {str(expected).lower()}")


def _require_int(value: Any, label: str, minimum: int = 0, maximum: int | None = None) -> int:
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        raise EvidenceError(f"{label} is outside the supported integer range")
    return value


def _safe_file(base: Path, raw_path: Any, label: str, max_bytes: int) -> Path:
    text = _require_string(raw_path, label)
    if any(ord(character) < 0x20 or ord(character) == 0x7F for character in text):
        raise EvidenceError(f"{label} contains a control character")
    pure = PurePath(text)
    if pure.is_absolute() or ".." in pure.parts:
        raise EvidenceError(f"{label} must stay beneath the manifest directory")
    candidate = base.joinpath(*pure.parts)
    current = base
    for part in pure.parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except (OSError, ValueError) as exc:
            raise EvidenceError(f"{label} does not exist: {text}") from exc
        if stat.S_ISLNK(mode):
            raise EvidenceError(f"{label} may not traverse a symlink: {text}")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(base.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise EvidenceError(f"{label} escapes the manifest directory") from exc
    info = resolved.stat()
    if not stat.S_ISREG(info.st_mode):
        raise EvidenceError(f"{label} must be a regular file")
    if info.st_size > max_bytes:
        raise EvidenceError(f"{label} exceeds {max_bytes} bytes")
    return resolved


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        info = path.lstat()
    except (OSError, ValueError) as exc:
        raise EvidenceError("manifest path is missing or malformed") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise EvidenceError("manifest must be a non-symlink regular file")
    if info.st_size > MAX_MANIFEST_BYTES:
        raise EvidenceError("manifest exceeds the size limit")
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"manifest is not canonical UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise EvidenceError("manifest root must be an object")
    return value


EVENT_FIELDS: dict[str, tuple[str, ...]] = {
    "session": (
        "schema", "seq", "event", "status", "ticks_per_second", "target_fps",
        "budget_ticks", "tolerance_ticks", "boot_ticks", "ready_ticks",
        "heap_baseline_bytes",
    ),
    "save_load": (
        "schema", "seq", "event", "status", "wall_ticks", "eeprom_present",
        "valid_slot_mask", "outcome", "selected_slot", "save_sequence",
        "checkpoint_scene", "checkpoint_quest",
    ),
    "transition": (
        "schema", "seq", "event", "status", "wall_ticks", "cause", "from", "to",
        "transition_count", "play_ticks", "active_control_ticks", "free_heap_bytes",
        "heap_low_water_bytes", "submitted_frames", "measured_intervals",
        "invalid_samples",
    ),
    "scene_summary": (
        "schema", "seq", "event", "status", "wall_ticks", "scene", "submitted_frames",
        "measured_intervals", "over_budget_frames", "missed_deadlines",
        "max_frame_ticks", "max_over_budget_streak", "invalid_samples",
    ),
    "summary": (
        "schema", "seq", "event", "status", "wall_ticks", "scene", "submitted_frames",
        "measured_intervals", "over_budget_frames", "missed_deadlines",
        "max_frame_ticks", "max_over_budget_streak", "play_ticks",
        "active_control_ticks", "free_heap_bytes", "heap_low_water_bytes",
        "invalid_samples",
    ),
    "save_write": (
        "schema", "seq", "event", "status", "wall_ticks", "outcome", "reason", "slot",
        "save_sequence", "chapter_completion", "checkpoint_scene", "checkpoint_quest",
    ),
    "chapter_stable": (
        "schema", "seq", "event", "status", "wall_ticks", "duration_ticks", "play_ticks",
        "active_control_ticks", "save_verified", "save_sequence", "submitted_frames",
        "measured_intervals", "over_budget_frames", "missed_deadlines",
        "max_frame_ticks", "max_over_budget_streak", "heap_low_water_bytes",
        "invalid_samples",
    ),
}

NUMERIC_FIELDS = {
    field
    for fields in EVENT_FIELDS.values()
    for field in fields
    if field not in {"event", "status", "cause", "outcome", "reason", "selected_slot"}
}
NUMERIC_FIELDS -= {"save_sequence", "checkpoint_scene", "checkpoint_quest", "slot"}


def _uint(record: dict[str, str], field: str, maximum: int = (1 << 64) - 1) -> int:
    raw = record[field]
    if not raw.isascii() or not raw.isdecimal():
        raise EvidenceError(f"telemetry {record['event']} field {field} must be unsigned decimal")
    value = int(raw, 10)
    if value > maximum:
        raise EvidenceError(f"telemetry {record['event']} field {field} overflows")
    return value


def _optional_uint(record: dict[str, str], field: str, maximum: int = (1 << 32) - 1) -> int | None:
    if record[field] == "NONE":
        return None
    return _uint(record, field, maximum)


def _parse_telemetry_line(line: str) -> dict[str, str]:
    if not line.startswith("N64G_TELEM "):
        raise EvidenceError("internal parser called on a non-telemetry line")
    pieces = line.split(" ")
    if pieces[0] != "N64G_TELEM" or any(not piece for piece in pieces[1:]):
        raise EvidenceError("telemetry must use exactly one ASCII space between tokens")
    record: dict[str, str] = {}
    order: list[str] = []
    for token in pieces[1:]:
        if token.count("=") != 1:
            raise EvidenceError(f"malformed telemetry token: {token}")
        key, value = token.split("=", 1)
        if TOKEN_KEY.fullmatch(key) is None or TOKEN_VALUE.fullmatch(value) is None:
            raise EvidenceError(f"unsupported telemetry token: {token}")
        if key in record:
            raise EvidenceError(f"duplicate telemetry field: {key}")
        record[key] = value
        order.append(key)
    if order[:4] != ["schema", "seq", "event", "status"]:
        raise EvidenceError("telemetry prefix fields are not canonical")
    event = record.get("event", "")
    expected = EVENT_FIELDS.get(event)
    if expected is None:
        raise EvidenceError(f"unsupported telemetry event: {event}")
    if tuple(order) != expected:
        raise EvidenceError(f"telemetry {event} fields or order differ from schema 1")
    if record["schema"] != "1" or record["status"] != STATUS:
        raise EvidenceError("telemetry schema/status mismatch")
    _uint(record, "seq", (1 << 32) - 1)
    for field in expected:
        if field in NUMERIC_FIELDS:
            _uint(record, field)
    for field in ("save_sequence", "checkpoint_scene", "checkpoint_quest", "slot"):
        if field in record:
            _optional_uint(record, field)
    _validate_record_values(record)
    return record


def _validate_record_values(record: dict[str, str]) -> None:
    event = record["event"]
    if event == "session":
        ticks = _uint(record, "ticks_per_second", (1 << 32) - 1)
        if ticks < 30 or _uint(record, "target_fps") != 30:
            raise EvidenceError("session guest clock or target frame rate is invalid")
        if _uint(record, "budget_ticks") != (ticks + 29) // 30:
            raise EvidenceError("session frame budget differs from the runtime contract")
        if _uint(record, "tolerance_ticks") != (ticks + 999) // 1000:
            raise EvidenceError("session frame tolerance differs from the runtime contract")
        if _uint(record, "ready_ticks") < _uint(record, "boot_ticks"):
            raise EvidenceError("session ready tick precedes boot")
    elif event == "save_load":
        present = _uint(record, "eeprom_present", 1)
        mask = _uint(record, "valid_slot_mask", 3)
        outcome = record["outcome"]
        selected = _optional_uint(record, "selected_slot", 1)
        sequence = _optional_uint(record, "save_sequence")
        scene = _optional_uint(record, "checkpoint_scene", 5)
        quest = _optional_uint(record, "checkpoint_quest", 7)
        if outcome == "selected":
            if present != 1 or selected is None or sequence is None or scene is None or quest is None or not (mask & (1 << selected)):
                raise EvidenceError("selected save_load fields are inconsistent")
        elif outcome == "none":
            if present != 1 or mask != 0 or any(value is not None for value in (selected, sequence, scene, quest)):
                raise EvidenceError("empty save_load fields are inconsistent")
        elif outcome == "unavailable":
            if present != 0 or mask != 0 or any(value is not None for value in (selected, sequence, scene, quest)):
                raise EvidenceError("unavailable save_load fields are inconsistent")
        else:
            raise EvidenceError(f"unsupported save_load outcome: {outcome}")
    elif event == "transition":
        source = _uint(record, "from", 5)
        target = _uint(record, "to", 5)
        if source == target or record["cause"] not in {"core", "continue_resume"}:
            raise EvidenceError("transition edge/cause is invalid")
        if record["cause"] == "continue_resume" and (source != 1 or target not in {3, 5}):
            raise EvidenceError("Continue transition is not an opening-to-checkpoint edge")
        if _uint(record, "measured_intervals") > _uint(record, "submitted_frames"):
            raise EvidenceError("transition frame counters are inconsistent")
    elif event in {"scene_summary", "summary"}:
        _uint(record, "scene", 5)
        submitted = _uint(record, "submitted_frames")
        measured = _uint(record, "measured_intervals")
        over_budget = _uint(record, "over_budget_frames")
        if measured > submitted or over_budget > measured:
            raise EvidenceError(f"{event} frame counters are inconsistent")
    elif event == "save_write":
        outcome = record["outcome"]
        reason = record["reason"]
        slot = _optional_uint(record, "slot", 1)
        sequence = _optional_uint(record, "save_sequence")
        _uint(record, "checkpoint_scene", 5)
        _uint(record, "checkpoint_quest", 7)
        _uint(record, "chapter_completion", 1)
        if outcome == "verified":
            if reason != "none" or slot is None or sequence is None:
                raise EvidenceError("verified save_write fields are inconsistent")
        elif outcome == "failed":
            if reason == "verification":
                if slot is None or sequence is None:
                    raise EvidenceError("verification failure lacks attempted slot/sequence")
            elif reason in {"eeprom_unavailable", "request_rejected"}:
                if slot is not None or sequence is not None:
                    raise EvidenceError("unattempted save failure reports a slot/sequence")
            else:
                raise EvidenceError(f"unsupported save_write failure reason: {reason}")
        else:
            raise EvidenceError(f"unsupported save_write outcome: {outcome}")
    elif event == "chapter_stable":
        if _uint(record, "save_verified", 1) != 1:
            raise EvidenceError("chapter_stable must bind a verified save")
        submitted = _uint(record, "submitted_frames")
        measured = _uint(record, "measured_intervals")
        over_budget = _uint(record, "over_budget_frames")
        if measured > submitted or over_budget > measured:
            raise EvidenceError("chapter_stable frame counters are inconsistent")


def _validate_heap_stream(records: list[dict[str, str]]) -> None:
    session = _only(records, "session")
    baseline = _uint(session, "heap_baseline_bytes")
    if baseline < MIN_HEAP_BYTES:
        raise EvidenceError("session heap baseline is below the evidence floor")
    previous_low_water = baseline
    for record in records:
        if "heap_low_water_bytes" not in record:
            continue
        low_water = _uint(record, "heap_low_water_bytes")
        if low_water < MIN_HEAP_BYTES:
            raise EvidenceError("heap low-water stream falls below the evidence floor")
        if low_water > baseline or low_water > previous_low_water:
            raise EvidenceError("heap low-water stream increases or exceeds its session baseline")
        if "free_heap_bytes" in record and low_water > _uint(record, "free_heap_bytes"):
            raise EvidenceError("heap low-water exceeds the simultaneously sampled free heap")
        previous_low_water = low_water


def _records(path: Path, rom_sha256: str, eeprom_sha256: str | None = None) -> list[dict[str, str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise EvidenceError(f"raw log is not UTF-8: {path.name}") from exc
    preamble = {
        "ares_version": PINNED_ARES_VERSION,
        "ares_sha256": PINNED_ARES_SHA256,
        "rom_sha256": rom_sha256,
        "homebrew_mode": "true",
        "expansion_pak": "false",
        "defocus": "allow",
    }
    if eeprom_sha256 is not None:
        preamble["eeprom_sha256"] = eeprom_sha256
    lines = text.splitlines()
    for key, expected in preamble.items():
        matches = [line for line in lines if line.startswith(f"{key}=")]
        if matches != [f"{key}={expected}"]:
            raise EvidenceError(f"raw log must contain exactly one canonical {key} binding")
    result = [_parse_telemetry_line(line) for line in lines if line.startswith("N64G_TELEM")]
    if not result:
        raise EvidenceError("raw log has no telemetry")
    for expected_seq, record in enumerate(result):
        if _uint(record, "seq", (1 << 32) - 1) != expected_seq:
            raise EvidenceError("telemetry sequence must begin at zero and be consecutive")
    wall_ticks = [_uint(record, "wall_ticks") for record in result if "wall_ticks" in record]
    if wall_ticks != sorted(wall_ticks):
        raise EvidenceError("telemetry wall ticks move backward")
    if len([record for record in result if record["event"] == "session"]) != 1:
        raise EvidenceError("raw log must contain exactly one session event")
    if len([record for record in result if record["event"] == "save_load"]) != 1:
        raise EvidenceError("raw log must contain exactly one save_load event")
    if result[0]["event"] != "session" or result[1]["event"] != "save_load":
        raise EvidenceError("session and save_load must be the first two telemetry events")
    unexpected_eeprom = [line for line in lines if line.startswith("eeprom_sha256=")]
    if eeprom_sha256 is None and unexpected_eeprom:
        raise EvidenceError("raw log has an EEPROM binding not declared by this evidence row")
    if any(
        _uint(record, "invalid_samples") != 0
        for record in result
        if "invalid_samples" in record
    ):
        raise EvidenceError("raw log contains invalid telemetry samples")
    _validate_heap_stream(result)
    return result


def _only(records: list[dict[str, str]], event: str) -> dict[str, str]:
    matches = [record for record in records if record["event"] == event]
    if len(matches) != 1:
        raise EvidenceError(f"raw log must contain exactly one {event} event")
    return matches[0]


def _latest_scene_summaries(records: list[dict[str, str]]) -> dict[int, dict[str, str]]:
    latest: dict[int, dict[str, str]] = {}
    for record in records:
        if record["event"] == "scene_summary":
            scene = _uint(record, "scene", 5)
            latest[scene] = record
    return latest


def _transition_edges(records: list[dict[str, str]]) -> list[tuple[dict[str, str], int, int]]:
    edges: list[tuple[dict[str, str], int, int]] = []
    expected_count = 1
    previous_target: int | None = None
    previous_submitted = 0
    previous_measured = 0
    for record in records:
        if record["event"] != "transition":
            continue
        source = _uint(record, "from", 5)
        target = _uint(record, "to", 5)
        if source == target or _uint(record, "transition_count", (1 << 32) - 1) != expected_count:
            raise EvidenceError("transition stream is not canonical")
        if previous_target is not None and source != previous_target:
            raise EvidenceError("transition stream is discontinuous")
        submitted = _uint(record, "submitted_frames", (1 << 32) - 1)
        measured = _uint(record, "measured_intervals", (1 << 32) - 1)
        if submitted < previous_submitted or measured < previous_measured:
            raise EvidenceError("transition frame counters move backward")
        expected_count += 1
        previous_target = target
        previous_submitted = submitted
        previous_measured = measured
        edges.append((record, source, target))
    return edges


def _contains_ordered_edges(edges: list[tuple[dict[str, str], int, int]], required: list[tuple[int, int]]) -> bool:
    cursor = 0
    for _, source, target in edges:
        if cursor < len(required) and (source, target) == required[cursor]:
            cursor += 1
    return cursor == len(required)


def _heap_low_water(records: list[dict[str, str]]) -> int:
    values = [
        _uint(record, "heap_low_water_bytes")
        for record in records
        if "heap_low_water_bytes" in record
    ]
    if not values:
        raise EvidenceError("raw log has no heap low-water samples")
    return min(values)


def _validate_timing_run(
    entry: Any,
    index: int,
    base: Path,
    rom_sha256: str,
) -> tuple[dict[str, Any], int, int]:
    run = _exact_keys(entry, (
        "id", "log_path", "log_sha256", "slate_path", "name_path", "cold_boot",
        "continue_used", "idle_declared_ms",
    ), f"timing_runs[{index}]")
    run_id = _require_string(run["id"], f"timing_runs[{index}].id")
    expected_paths = (("watched", "default"), ("skipped", "custom"))
    if (run["slate_path"], run["name_path"]) != expected_paths[index]:
        raise EvidenceError(f"timing_runs[{index}] must bind the required slate/name path")
    _require_bool(run["cold_boot"], True, f"timing_runs[{index}].cold_boot")
    _require_bool(run["continue_used"], False, f"timing_runs[{index}].continue_used")
    if _require_int(run["idle_declared_ms"], f"timing_runs[{index}].idle_declared_ms") != 0:
        raise EvidenceError("timing run must declare zero intentional idle milliseconds")
    log_path = _safe_file(base, run["log_path"], f"timing_runs[{index}].log_path", MAX_LOG_BYTES)
    if _sha256(log_path) != _require_hash(run["log_sha256"], f"timing_runs[{index}].log_sha256"):
        raise EvidenceError(f"timing run {run_id} log hash mismatch")
    records = _records(log_path, rom_sha256)
    session = _only(records, "session")
    load = _only(records, "save_load")
    stable = _only(records, "chapter_stable")
    if records[-1] is not stable:
        raise EvidenceError(f"timing run {run_id} contains telemetry after chapter_stable")
    ticks_per_second = _uint(session, "ticks_per_second", (1 << 32) - 1)
    if ticks_per_second < 30 or _uint(session, "target_fps") != 30:
        raise EvidenceError(f"timing run {run_id} has an invalid guest clock")
    duration = _uint(stable, "duration_ticks")
    stable_wall_ticks = _uint(stable, "wall_ticks")
    boot_ticks = _uint(session, "boot_ticks")
    if stable_wall_ticks < boot_ticks or duration != stable_wall_ticks - boot_ticks:
        raise EvidenceError(f"timing run {run_id} stable duration does not match guest wall ticks")
    if duration < 360 * ticks_per_second or duration > 600 * ticks_per_second:
        raise EvidenceError(f"timing run {run_id} is outside 360-600 seconds")
    if _uint(stable, "active_control_ticks") < 7_200:
        raise EvidenceError(f"timing run {run_id} has fewer than 7200 active-control ticks")
    if load["outcome"] != "none" or _uint(load, "eeprom_present", 1) != 1 or _uint(load, "valid_slot_mask", 3) != 0:
        raise EvidenceError(f"timing run {run_id} is not a fresh-save new game")
    if any(record["event"] == "transition" and record["cause"] == "continue_resume" for record in records):
        raise EvidenceError(f"timing run {run_id} used Continue")
    edges = _transition_edges(records)
    required = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 3), (3, 5)]
    if not _contains_ordered_edges(edges, required):
        raise EvidenceError(f"timing run {run_id} does not contain the complete chapter route")
    summaries = _latest_scene_summaries(records)
    if set(summaries) != set(range(6)):
        raise EvidenceError(f"timing run {run_id} lacks final summaries for all scenes")
    if any(_uint(summaries[scene], "submitted_frames") == 0 for scene in range(6)):
        raise EvidenceError(f"timing run {run_id} has an empty scene summary")
    if any(_uint(summaries[scene], "measured_intervals") == 0 for scene in (3, 4)):
        raise EvidenceError(f"timing run {run_id} lacks measured Annex/Battle intervals")
    stable_sequence = _uint(stable, "save_sequence", (1 << 32) - 1)
    if stable_sequence == 0:
        raise EvidenceError(f"timing run {run_id} final save sequence is not positive")
    final_writes = [
        record for record in records
        if record["event"] == "save_write" and record["outcome"] == "verified"
        and _uint(record, "chapter_completion", 1) == 1
        and _optional_uint(record, "save_sequence") == stable_sequence
        and _uint(record, "checkpoint_scene", 5) == 5
        and _uint(record, "checkpoint_quest", 7) == 7
    ]
    if len(final_writes) != 1 or _uint(stable, "save_verified", 1) != 1:
        raise EvidenceError(f"timing run {run_id} lacks one matching verified final save")
    final_write = final_writes[0]
    final_write_event_sequence = _uint(final_write, "seq", (1 << 32) - 1)
    stable_event_sequence = _uint(stable, "seq", (1 << 32) - 1)
    if final_write_event_sequence >= stable_event_sequence:
        raise EvidenceError(f"timing run {run_id} chapter_stable precedes its verified final save")
    prior_verified_sequences = [
        _optional_uint(record, "save_sequence")
        for record in records
        if record["event"] == "save_write" and record["outcome"] == "verified"
        and _uint(record, "seq", (1 << 32) - 1) < final_write_event_sequence
    ]
    if any(sequence is None or sequence >= stable_sequence for sequence in prior_verified_sequences):
        raise EvidenceError(f"timing run {run_id} final save sequence is not new")
    if any(
        record["event"] == "save_write"
        and (
            record["outcome"] != "verified"
            or final_write_event_sequence < _uint(record, "seq", (1 << 32) - 1) < stable_event_sequence
        )
        for record in records
    ):
        raise EvidenceError(f"timing run {run_id} has a failed or superseding save write")
    low_water = _heap_low_water(records)
    if low_water < MIN_HEAP_BYTES:
        raise EvidenceError(f"timing run {run_id} fell below the heap floor")
    return {
        "id": run_id,
        "duration_ticks": duration,
        "ticks_per_second": ticks_per_second,
        "active_control_ticks": _uint(stable, "active_control_ticks"),
        "heap_low_water_bytes": low_water,
        "scene_performance": {
            str(scene): {
                field: _uint(summaries[scene], field)
                for field in (
                    "submitted_frames", "measured_intervals", "over_budget_frames",
                    "missed_deadlines", "max_frame_ticks", "max_over_budget_streak",
                )
            }
            for scene in range(6)
        },
    }, duration, ticks_per_second


def _validate_soak(entry: Any, base: Path, rom_sha256: str) -> dict[str, Any]:
    run = _exact_keys(entry, ("id", "log_path", "log_sha256", "warmup_loop_count"), "soak_run")
    run_id = _require_string(run["id"], "soak_run.id")
    warmup_count = _require_int(run["warmup_loop_count"], "soak_run.warmup_loop_count", 0, 1)
    log_path = _safe_file(base, run["log_path"], "soak_run.log_path", MAX_LOG_BYTES)
    if _sha256(log_path) != _require_hash(run["log_sha256"], "soak_run.log_sha256"):
        raise EvidenceError(f"soak run {run_id} log hash mismatch")
    records = _records(log_path, rom_sha256)
    edges = _transition_edges(records)
    pairs: list[tuple[dict[str, str], dict[str, str]]] = []
    open_edge: dict[str, str] | None = None
    for record, source, target in edges:
        if (source, target) == (3, 4):
            if open_edge is not None:
                raise EvidenceError("soak run has nested Annex-to-Battle loops")
            open_edge = record
        elif (source, target) == (4, 3):
            if open_edge is None:
                raise EvidenceError("soak run closes a loop that was not opened")
            pairs.append((open_edge, record))
            open_edge = None
        elif open_edge is not None:
            raise EvidenceError("soak loop contains an intervening scene edge")
    if open_edge is not None or len(pairs) != warmup_count + 10:
        raise EvidenceError("soak run must contain warm-up plus exactly ten complete loops")
    measured = pairs[warmup_count:]
    baseline = (
        _uint(pairs[warmup_count - 1][1], "free_heap_bytes")
        if warmup_count
        else _uint(measured[0][0], "free_heap_bytes")
    )
    loop_results = []
    previous_end_seq = -1
    for index, (start, end) in enumerate(measured, 1):
        start_seq = _uint(start, "seq", (1 << 32) - 1)
        end_seq = _uint(end, "seq", (1 << 32) - 1)
        start_frames = _uint(start, "submitted_frames", (1 << 32) - 1)
        end_frames = _uint(end, "submitted_frames", (1 << 32) - 1)
        start_intervals = _uint(start, "measured_intervals", (1 << 32) - 1)
        end_intervals = _uint(end, "measured_intervals", (1 << 32) - 1)
        end_heap = _uint(end, "free_heap_bytes")
        if start_seq <= previous_end_seq or end_seq <= start_seq or end_frames <= start_frames or end_intervals <= start_intervals:
            raise EvidenceError("soak loops are overlapping, unordered, or unmeasured")
        if end_heap < baseline:
            raise EvidenceError(f"soak loop {index} ends below the warmed heap baseline")
        previous_end_seq = end_seq
        loop_results.append({
            "loop": index,
            "start_transition_seq": start_seq,
            "end_transition_seq": end_seq,
            "start_free_heap_bytes": _uint(start, "free_heap_bytes"),
            "end_free_heap_bytes": end_heap,
            "submitted_frames": end_frames - start_frames,
            "measured_intervals": end_intervals - start_intervals,
        })
    low_water = _heap_low_water(records)
    if low_water < MIN_HEAP_BYTES:
        raise EvidenceError("soak run fell below the global heap floor")
    return {
        "id": run_id,
        "warmup_loop_count": warmup_count,
        "measured_loop_count": len(measured),
        "warmed_heap_baseline_bytes": baseline,
        "heap_low_water_bytes": low_water,
        "loops": loop_results,
    }


def _fnv1a(data: bytes) -> int:
    value = 2_166_136_261
    for byte in data:
        value ^= byte
        value = (value * 16_777_619) & 0xFFFF_FFFF
    return value


def _save_slot(slot: bytes) -> dict[str, Any]:
    recognizable = slot[:4] == b"N64G" and struct.unpack(">H", slot[4:6])[0] == SAVE_VERSION and struct.unpack(">H", slot[6:8])[0] == SAVE_SLOT_BYTES
    checksum_ok = struct.unpack(">I", slot[60:64])[0] == _fnv1a(slot[:60])
    sequence = struct.unpack(">I", slot[8:12])[0]
    structurally_valid = recognizable and checksum_ok
    return {
        "recognizable": recognizable,
        "checksum_ok": checksum_ok,
        "valid": structurally_valid,
        "sequence": sequence,
        "scene": slot[21],
        "quest": slot[22],
    }


def _sequence_newer(candidate: int, current: int) -> bool:
    delta = (candidate - current) & 0xFFFF_FFFF
    return delta != 0 and delta < 0x8000_0000


def _selected_slot(slots: list[dict[str, Any]]) -> int | None:
    valid = [index for index, slot in enumerate(slots) if slot["valid"]]
    if not valid:
        return None
    if len(valid) == 1:
        return valid[0]
    return 1 if _sequence_newer(slots[1]["sequence"], slots[0]["sequence"]) else 0


def _validate_save_run(entry: Any, index: int, base: Path, rom_sha256: str) -> dict[str, Any]:
    run = _exact_keys(entry, (
        "id", "scenario", "log_path", "log_sha256", "eeprom_path", "eeprom_sha256",
    ), f"save_runs[{index}]")
    run_id = _require_string(run["id"], f"save_runs[{index}].id")
    scenario = _require_string(run["scenario"], f"save_runs[{index}].scenario")
    if scenario not in {"valid_resume", "latest_corrupt_fallback", "all_corrupt_new_game"}:
        raise EvidenceError(f"unsupported save scenario: {scenario}")
    log_path = _safe_file(base, run["log_path"], f"save_runs[{index}].log_path", MAX_LOG_BYTES)
    eeprom_path = _safe_file(base, run["eeprom_path"], f"save_runs[{index}].eeprom_path", EEPROM_BYTES)
    if _sha256(log_path) != _require_hash(run["log_sha256"], f"save_runs[{index}].log_sha256"):
        raise EvidenceError(f"save run {run_id} log hash mismatch")
    eeprom_hash = _require_hash(run["eeprom_sha256"], f"save_runs[{index}].eeprom_sha256")
    if _sha256(eeprom_path) != eeprom_hash:
        raise EvidenceError(f"save run {run_id} EEPROM hash mismatch")
    image = eeprom_path.read_bytes()
    if len(image) != EEPROM_BYTES:
        raise EvidenceError(f"save run {run_id} EEPROM image must be exactly 512 bytes")
    slots = [_save_slot(image[index * SAVE_SLOT_BYTES:(index + 1) * SAVE_SLOT_BYTES]) for index in range(SAVE_SLOT_COUNT)]
    valid_mask = sum((1 << index) for index, slot in enumerate(slots) if slot["valid"])
    selected = _selected_slot(slots)
    records = _records(log_path, rom_sha256, eeprom_hash)
    _transition_edges(records)
    load = _only(records, "save_load")
    if _uint(load, "eeprom_present", 1) != 1 or _uint(load, "valid_slot_mask", 3) != valid_mask:
        raise EvidenceError(f"save run {run_id} load telemetry disagrees with EEPROM slots")
    resume_edges = [
        record for record in records
        if record["event"] == "transition" and record["cause"] == "continue_resume"
    ]
    if scenario == "valid_resume":
        if selected is None or load["outcome"] != "selected" or len(resume_edges) != 1:
            raise EvidenceError(f"save run {run_id} did not resume a valid slot")
    elif scenario == "latest_corrupt_fallback":
        valid = [slot for slot in slots if slot["valid"]]
        corrupt = [slot for slot in slots if slot["recognizable"] and not slot["checksum_ok"]]
        if len(valid) != 1 or len(corrupt) != 1 or not _sequence_newer(corrupt[0]["sequence"], valid[0]["sequence"]):
            raise EvidenceError(f"save run {run_id} is not a newest-slot corruption fixture")
        if load["outcome"] != "selected" or len(resume_edges) != 1:
            raise EvidenceError(f"save run {run_id} did not fall back and resume")
    else:
        corrupt = [slot for slot in slots if slot["recognizable"] and not slot["checksum_ok"]]
        if selected is not None or not corrupt or load["outcome"] != "none" or resume_edges:
            raise EvidenceError(f"save run {run_id} did not reject corrupt slots into new game")
    if selected is not None:
        if _optional_uint(load, "selected_slot", 1) != selected or _optional_uint(load, "save_sequence") != slots[selected]["sequence"]:
            raise EvidenceError(f"save run {run_id} selected the wrong valid slot")
        if _optional_uint(load, "checkpoint_scene", 5) != slots[selected]["scene"] or _optional_uint(load, "checkpoint_quest", 7) != slots[selected]["quest"]:
            raise EvidenceError(f"save run {run_id} checkpoint telemetry disagrees with the selected slot")
        if _uint(resume_edges[0], "to", 5) != slots[selected]["scene"]:
            raise EvidenceError(f"save run {run_id} resumed a different scene than the selected slot")
    else:
        if any(_optional_uint(load, field) is not None for field in ("selected_slot", "save_sequence", "checkpoint_scene", "checkpoint_quest")):
            raise EvidenceError(f"save run {run_id} reports a nonexistent checkpoint")
    return {
        "id": run_id,
        "scenario": scenario,
        "valid_slot_mask": valid_mask,
        "selected_slot": selected,
        "outcome": load["outcome"],
    }


def validate(manifest_path: Path | str, rom_path: Path | str) -> dict[str, Any]:
    manifest_file = Path(os.path.abspath(os.fspath(manifest_path)))
    manifest = _exact_keys(_read_json(manifest_file), (
        "schema", "status", "rom_sha256", "ares_sha256", "timing_runs", "soak_run",
        "save_runs",
    ), "manifest")
    if manifest["schema"] != SCHEMA or manifest["status"] != STATUS:
        raise EvidenceError("manifest schema/status mismatch")
    rom_hash = _require_hash(manifest["rom_sha256"], "manifest.rom_sha256")
    if _require_hash(manifest["ares_sha256"], "manifest.ares_sha256") != PINNED_ARES_SHA256:
        raise EvidenceError("manifest does not bind the pinned Ares executable")
    rom = Path(rom_path)
    try:
        info = rom.lstat()
    except (OSError, ValueError) as exc:
        raise EvidenceError("ROM path is missing or malformed") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_size > MAX_ROM_BYTES:
        raise EvidenceError("ROM must be a bounded non-symlink regular file")
    with rom.open("rb") as stream:
        rom_magic = stream.read(4)
    if info.st_size < 4096 or info.st_size % 4 != 0 or rom_magic != b"\x80\x37\x12\x40":
        raise EvidenceError("ROM is not a bounded big-endian N64 image")
    if _sha256(rom) != rom_hash:
        raise EvidenceError("ROM hash differs from the evidence manifest")
    timing_entries = manifest["timing_runs"]
    if not isinstance(timing_entries, list) or len(timing_entries) != 2:
        raise EvidenceError("manifest must contain exactly two timing runs")
    save_entries = manifest["save_runs"]
    if not isinstance(save_entries, list) or len(save_entries) != 3:
        raise EvidenceError("manifest must contain exactly three save runs")
    all_entries = [*timing_entries, manifest["soak_run"], *save_entries]
    declared_log_hashes = [
        _require_hash(entry.get("log_sha256") if isinstance(entry, dict) else None, "evidence log hash")
        for entry in all_entries
    ]
    if len(declared_log_hashes) != len(set(declared_log_hashes)):
        raise EvidenceError("each evidence run must bind a distinct raw log")
    eeprom_hashes = [
        _require_hash(entry.get("eeprom_sha256") if isinstance(entry, dict) else None, "save EEPROM hash")
        for entry in save_entries
    ]
    if len(eeprom_hashes) != len(set(eeprom_hashes)):
        raise EvidenceError("each save scenario must bind a distinct EEPROM snapshot")
    base = manifest_file.parent
    timing_results = []
    durations = []
    clocks = []
    for index, entry in enumerate(timing_entries):
        result, duration, clock = _validate_timing_run(entry, index, base, rom_hash)
        timing_results.append(result)
        durations.append(duration)
        clocks.append(clock)
    if clocks[0] != clocks[1] or sum(durations) < 720 * clocks[0] or sum(durations) > 960 * clocks[0]:
        raise EvidenceError("two-run arithmetic-mean duration is outside 360-480 seconds")
    soak_result = _validate_soak(manifest["soak_run"], base, rom_hash)
    save_results = [_validate_save_run(entry, index, base, rom_hash) for index, entry in enumerate(save_entries)]
    if {result["scenario"] for result in save_results} != {
        "valid_resume", "latest_corrupt_fallback", "all_corrupt_new_game",
    }:
        raise EvidenceError("save_runs must cover each required scenario exactly once")
    ids = [result["id"] for result in timing_results] + [soak_result["id"]] + [result["id"] for result in save_results]
    if len(ids) != len(set(ids)):
        raise EvidenceError("evidence run ids must be unique")
    return {
        "result": "EVIDENCE_CONTRACT_PASS",
        "certification": "NOT_CLAIMED",
        "status": STATUS,
        "rom_sha256": rom_hash,
        "ares_sha256": PINNED_ARES_SHA256,
        "timing_runs": timing_results,
        "soak_run": soak_result,
        "save_runs": save_results,
        "limitations": [
            "No performance threshold grants certification.",
            "Declared input path and no-idle conditions still require capture review.",
            "Visual, audio, controller, and hardware acceptance are outside this validator.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--rom", required=True, type=Path)
    arguments = parser.parse_args(argv)
    try:
        result = validate(arguments.manifest, arguments.rom)
    except (OSError, ValueError) as exc:
        print(f"EVIDENCE_CONTRACT_FAIL: {exc}", file=os.sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
