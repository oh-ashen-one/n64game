#!/usr/bin/env python3
"""Report current visual-benchmark readiness without approving anything.

The visual benchmark approval record is deliberately fail-closed. This tool
extracts the concrete pending whitelist, evidence, objective, rubric, reviewer,
concept-packet, and runtime-candidate state so the next production work can be
prioritized from repository facts instead of prose guesses.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "docs" / "VISUAL_BENCHMARK_APPROVAL.md"
MASTER = ROOT / "docs" / "N64GAME_MASTER_SPEC.md"
RUNTIME_CANDIDATES = ROOT / "config" / "runtime-candidates.tsv"
DECISION_LINE = re.compile(r"^Decision:\s+([A-Z_]+)\s*$", re.MULTILINE)
LOCK_LINE = re.compile(r"^Production-Lock:\s+([A-Z_]+)\s*$", re.MULTILINE)


class VisualBenchmarkReadinessError(RuntimeError):
    pass


@dataclass(frozen=True)
class TableRow:
    cells: tuple[str, ...]
    line_number: int


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require_master(root: Path) -> None:
    master = root / "docs" / "N64GAME_MASTER_SPEC.md"
    if not master.is_file():
        raise VisualBenchmarkReadinessError(f"missing master prompt: {master}")
    text = read(master)
    if "Create a polished, original-IP Nintendo 64 game with a genuine 6–8 minute first-time playthrough" not in text:
        raise VisualBenchmarkReadinessError("master prompt does not match the reduced 6-8 minute authority")
    if "## 13. Final Acceptance Checklist" not in text:
        raise VisualBenchmarkReadinessError("master prompt is missing the Final Acceptance Checklist")


def split_markdown_row(line: str) -> tuple[str, ...]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return ()
    return tuple(cell.strip() for cell in stripped.strip("|").split("|"))


def section(text: str, start_heading: str, next_heading: str | None = None) -> str:
    start = text.find(start_heading)
    if start < 0:
        return ""
    body = text[start:]
    if next_heading:
        marker = body.find(next_heading, len(start_heading))
        if marker >= 0:
            body = body[:marker]
    return body


def table_rows(text: str) -> list[TableRow]:
    rows: list[TableRow] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        cells = split_markdown_row(line)
        if not cells or set(cells[0]) <= {"-"}:
            continue
        rows.append(TableRow(cells, line_number))
    return rows


def code_value(value: str) -> str:
    match = re.search(r"`([^`]+)`", value)
    return match.group(1) if match else value.strip()


def parse_control(root: Path) -> dict[str, Any]:
    control = root / "docs" / "VISUAL_BENCHMARK_APPROVAL.md"
    if not control.is_file():
        raise VisualBenchmarkReadinessError(f"missing visual benchmark control: {control}")
    text = read(control)
    decision_match = DECISION_LINE.search(text)
    lock_match = LOCK_LINE.search(text)
    decision = decision_match.group(1) if decision_match else "MISSING"
    production_lock = lock_match.group(1) if lock_match else "MISSING"

    whitelist_rows = []
    whitelist_section = section(text, "## 2. Exact pre-approval production whitelist", "### 2.1")
    for row in table_rows(whitelist_section):
        if row.cells[:3] == ("Canonical production ID", "Allowed final source subset before approval", "Anything explicitly still locked"):
            continue
        if len(row.cells) == 3 and row.cells[0].startswith("`"):
            whitelist_rows.append(
                {
                    "production_id": code_value(row.cells[0]),
                    "allowed_subset": row.cells[1],
                    "locked": row.cells[2],
                    "line": row.line_number,
                }
            )

    authorization_rows = []
    auth_section = section(text, "### 2.1 Exact authorization and current-hash bindings", "## 3.")
    for row in table_rows(auth_section):
        if row.cells and row.cells[0] == "Basis":
            continue
        if len(row.cells) == 8 and re.fullmatch(r"WB-\d{3}", row.cells[0]):
            authorization_rows.append(
                {
                    "basis": row.cells[0],
                    "production_id": code_value(row.cells[1]),
                    "authorization": code_value(row.cells[2]),
                    "gate_record": code_value(row.cells[3]),
                    "provenance": code_value(row.cells[4]),
                    "source_manifest": code_value(row.cells[5]),
                    "output_manifest": code_value(row.cells[6]),
                    "state": code_value(row.cells[7]),
                    "line": row.line_number,
                }
            )

    evidence_rows = []
    evidence_section = section(text, "## 3. Exact benchmark evidence set", "The same run ID binds")
    for row in table_rows(evidence_section):
        if row.cells[:4] == ("Evidence ID", "Required", "Manifest member/path and SHA-256", "Result"):
            continue
        if len(row.cells) == 4 and row.cells[0].startswith("`ev.benchmark."):
            evidence_rows.append(
                {
                    "evidence_id": code_value(row.cells[0]),
                    "required": row.cells[1],
                    "manifest": code_value(row.cells[2]),
                    "result": code_value(row.cells[3]),
                    "line": row.line_number,
                }
            )

    objective_rows = []
    objective_section = section(text, "## 4. Objective acceptance", "## 5.")
    for row in table_rows(objective_section):
        if len(row.cells) == 4 and row.cells[0] not in ("Criterion", "---"):
            objective_rows.append(
                {
                    "objective": row.cells[0],
                    "required": row.cells[1],
                    "actual": code_value(row.cells[2]),
                    "result": code_value(row.cells[3]),
                    "line": row.line_number,
                }
            )

    rubric_rows = []
    rubric_section = section(text, "## 5. Visual-authorship rubric", "## 6.")
    for row in table_rows(rubric_section):
        if len(row.cells) == 4 and row.cells[0] not in ("Category", "---"):
            rubric_rows.append(
                {
                    "category": row.cells[0],
                    "rejects": row.cells[1],
                    "actual": code_value(row.cells[2]),
                    "result": code_value(row.cells[3]),
                    "line": row.line_number,
                }
            )

    reviewer_rows = []
    reviewer_section = section(text, "## 6. Independent reviewer record", "## 7.")
    for row in table_rows(reviewer_section):
        if len(row.cells) == 7 and row.cells[0] not in ("Role", "---"):
            reviewer_rows.append(
                {
                    "role": row.cells[0],
                    "reviewer": code_value(row.cells[1]),
                    "non_owner": code_value(row.cells[2]),
                    "reviewed_at": code_value(row.cells[3]),
                    "manifest_sha256": code_value(row.cells[4]),
                    "decision": code_value(row.cells[5]),
                    "rationale": code_value(row.cells[6]),
                    "line": row.line_number,
                }
            )

    return {
        "path": "docs/VISUAL_BENCHMARK_APPROVAL.md",
        "sha256": sha256(control),
        "decision": decision,
        "production_lock": production_lock,
        "whitelist_rows": whitelist_rows,
        "authorization_rows": authorization_rows,
        "evidence_rows": evidence_rows,
        "objective_rows": objective_rows,
        "rubric_rows": rubric_rows,
        "reviewer_rows": reviewer_rows,
    }


def concept_packets(root: Path) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    for g1 in sorted((root / "review").glob("*.*/*")):
        if not g1.is_dir() or g1.name != "g1":
            continue
        asset_id = g1.parent.name
        required = ("PROVENANCE.md", "EVIDENCE_MANIFEST.sha256", "REVIEW.md", "CONCEPT_RENDER.png")
        present = [name for name in required if (g1 / name).is_file() and not (g1 / name).is_symlink()]
        packets.append(
            {
                "asset_id": asset_id,
                "path": str(g1.relative_to(root)),
                "complete_concept_packet": len(present) == len(required),
                "present": present,
                "missing": [name for name in required if name not in present],
            }
        )
    return packets


def runtime_candidates(root: Path) -> dict[str, Any]:
    path = root / "config" / "runtime-candidates.tsv"
    if not path.is_file():
        return {"path": "config/runtime-candidates.tsv", "present": False, "rows": [], "missing_files": []}
    rows = []
    missing_files = []
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        for row in reader:
            source_path = row.get("source_path", "")
            source = root / source_path
            exists = source.is_file() and not source.is_symlink()
            if not exists:
                missing_files.append(source_path)
            rows.append({**row, "source_exists": exists})
    statuses = sorted({row.get("status", "") for row in rows})
    return {
        "path": "config/runtime-candidates.tsv",
        "present": True,
        "sha256": sha256(path),
        "row_count": len(rows),
        "statuses": statuses,
        "rows": rows,
        "missing_files": missing_files,
    }


def summarize(control: dict[str, Any], packets: list[dict[str, Any]], candidates: dict[str, Any]) -> dict[str, Any]:
    auth_rows = control["authorization_rows"]
    evidence_rows = control["evidence_rows"]
    objective_rows = control["objective_rows"]
    rubric_rows = control["rubric_rows"]
    reviewer_rows = control["reviewer_rows"]

    active_auth = [row for row in auth_rows if row["state"] != "INACTIVE"]
    pending_auth = [row for row in auth_rows if row["state"] == "INACTIVE"]
    passed_evidence = [row for row in evidence_rows if row["result"] == "PASS"]
    pending_evidence = [row for row in evidence_rows if row["result"] != "PASS"]
    pending_objectives = [row for row in objective_rows if row["result"] != "PASS"]
    pending_rubric = [row for row in rubric_rows if row["result"] != "PASS"]
    pending_reviewers = [row for row in reviewer_rows if row["decision"] != "PASS"]
    complete_concepts = [row for row in packets if row["complete_concept_packet"]]

    blockers = []
    if control["decision"] != "APPROVED":
        blockers.append("visual benchmark decision is not APPROVED")
    if control["production_lock"] != "UNLOCKED":
        blockers.append("production lock is not UNLOCKED")
    if pending_auth:
        blockers.append(f"{len(pending_auth)} / {len(auth_rows)} whitelist authorization rows are inactive")
    if pending_evidence:
        blockers.append(f"{len(pending_evidence)} / {len(evidence_rows)} benchmark evidence rows are not PASS")
    if pending_objectives:
        blockers.append(f"{len(pending_objectives)} objective approval checks are not PASS")
    if pending_rubric:
        blockers.append(f"{len(pending_rubric)} visual-authorship rubric rows are not PASS")
    if pending_reviewers:
        blockers.append(f"{len(pending_reviewers)} independent reviewer rows are not PASS")
    if candidates.get("missing_files"):
        blockers.append(f"{len(candidates['missing_files'])} runtime candidate files are missing")

    return {
        "ready_for_visual_approval": not blockers,
        "blockers": blockers,
        "counts": {
            "whitelist_expected": 52,
            "whitelist_rows": len(control["whitelist_rows"]),
            "authorization_expected": 52,
            "authorization_rows": len(auth_rows),
            "authorization_active": len(active_auth),
            "authorization_inactive": len(pending_auth),
            "evidence_expected": 15,
            "evidence_rows": len(evidence_rows),
            "evidence_pass": len(passed_evidence),
            "evidence_pending": len(pending_evidence),
            "objective_rows": len(objective_rows),
            "objective_pass": len(objective_rows) - len(pending_objectives),
            "rubric_rows": len(rubric_rows),
            "rubric_pass": len(rubric_rows) - len(pending_rubric),
            "reviewer_rows": len(reviewer_rows),
            "reviewer_pass": len(reviewer_rows) - len(pending_reviewers),
            "concept_packets": len(packets),
            "complete_concept_packets": len(complete_concepts),
            "runtime_candidate_rows": candidates.get("row_count", 0),
            "runtime_candidate_missing_files": len(candidates.get("missing_files", [])),
        },
        "first_next_actions": [
            "create a capture packet with scripts/assemble-visual-benchmark-captures --init-template",
            "capture native 320x240 benchmark frames for exploration, dialogue, target selection, attack anticipation, impact, and support",
            "generate or provide exact 4x nearest-neighbor enlargements from those native frames and validate the packet with scripts/assemble-visual-benchmark-captures",
            "promote whitelist rows through real authorization, Gate records, source manifests, output manifests, and seven evidence-backed gate decisions",
            "populate objective/rubric/reviewer rows only after recomputable media, performance, provenance, and non-owner review exist",
        ],
    }


def audit(root: Path) -> dict[str, Any]:
    require_master(root)
    control = parse_control(root)
    packets = concept_packets(root)
    candidates = runtime_candidates(root)
    summary = summarize(control, packets, candidates)
    return {
        "schema": "n64game-visual-benchmark-readiness-v1",
        "result": "BLOCKED_BY_MISSING_EVIDENCE" if not summary["ready_for_visual_approval"] else "READY_FOR_APPROVAL",
        "control": {
            "path": control["path"],
            "sha256": control["sha256"],
            "decision": control["decision"],
            "production_lock": control["production_lock"],
        },
        "summary": summary,
        "whitelist_inactive": [
            {"basis": row["basis"], "production_id": row["production_id"]}
            for row in control["authorization_rows"]
            if row["state"] == "INACTIVE"
        ],
        "evidence_pending": [
            {"evidence_id": row["evidence_id"], "required": row["required"]}
            for row in control["evidence_rows"]
            if row["result"] != "PASS"
        ],
        "objective_pending": [
            {"objective": row["objective"], "required": row["required"]}
            for row in control["objective_rows"]
            if row["result"] != "PASS"
        ],
        "rubric_pending": [
            {"category": row["category"], "rejects": row["rejects"]}
            for row in control["rubric_rows"]
            if row["result"] != "PASS"
        ],
        "reviewer_pending": [
            {"role": row["role"], "reviewer": row["reviewer"], "decision": row["decision"]}
            for row in control["reviewer_rows"]
            if row["decision"] != "PASS"
        ],
        "concept_packets": packets,
        "runtime_candidates": {
            "path": candidates["path"],
            "present": candidates["present"],
            "sha256": candidates.get("sha256"),
            "row_count": candidates.get("row_count", 0),
            "statuses": candidates.get("statuses", []),
            "missing_files": candidates.get("missing_files", []),
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    counts = payload["summary"]["counts"]
    lines = [
        "# N64GAME Visual Benchmark Readiness",
        "",
        f"- Result: `{payload['result']}`",
        f"- Control: `{payload['control']['path']}@{payload['control']['sha256']}`",
        f"- Decision / lock: `{payload['control']['decision']}` / `{payload['control']['production_lock']}`",
        f"- Active whitelist rows: `{counts['authorization_active']} / {counts['authorization_rows']}`",
        f"- Passing evidence rows: `{counts['evidence_pass']} / {counts['evidence_rows']}`",
        f"- Complete concept packets: `{counts['complete_concept_packets']} / {counts['concept_packets']}`",
        f"- Runtime candidate rows: `{counts['runtime_candidate_rows']}`",
        "",
        "## Blocking facts",
        "",
    ]
    for blocker in payload["summary"]["blockers"]:
        lines.append(f"- {blocker}")
    lines.extend(["", "## First next actions", ""])
    for action in payload["summary"]["first_next_actions"]:
        lines.append(f"- {action}")
    lines.extend(["", "## Pending benchmark evidence", ""])
    for row in payload["evidence_pending"]:
        lines.append(f"- `{row['evidence_id']}` — {row['required']}")
    lines.extend([
        "",
        "This report is not an approval. It exists to keep FAC-09/FAC-10 work concrete while the canonical visual benchmark remains locked.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        payload = audit(root)
    except (OSError, VisualBenchmarkReadinessError) as exc:
        print(f"VISUAL_BENCHMARK_READINESS_ERROR: {exc}")
        return 2
    text = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(render_markdown(payload), encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
