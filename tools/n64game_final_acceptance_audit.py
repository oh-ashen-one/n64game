#!/usr/bin/env python3
"""Fail-closed final-acceptance audit for N64GAME.

The master production prompt is the authority. This tool does not certify the
release. It records which Final Acceptance Checklist items currently have hard
local evidence, partial/indirect evidence, or missing evidence, and it keeps the
overall result INCOMPLETE until every checklist item is proven.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "docs" / "N64GAME_MASTER_SPEC.md"
ROM = ROOT / "build" / "game" / "n64game-gate3.z64"
N64_MAGIC = bytes.fromhex("80371240")
STATUSES = {"PASS", "PARTIAL", "MISSING"}
DECISION_LINE = re.compile(r"^Decision:\s+([A-Z_]+)\s*$", re.MULTILINE)
PUBLIC_REPRO_SCHEMA = "n64game-public-reproducibility-v1"


class AcceptanceAuditError(RuntimeError):
    pass


@dataclass(frozen=True)
class AuditItem:
    item_id: str
    requirement: str
    status: str
    evidence: tuple[str, ...]
    missing: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.item_id,
            "requirement": self.requirement,
            "status": self.status,
            "evidence": list(self.evidence),
            "missing": list(self.missing),
        }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str], *, root: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    except OSError as exc:
        return subprocess.CompletedProcess(command, 127, stdout=str(exc))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require_master(root: Path) -> str:
    path = root / "docs" / "N64GAME_MASTER_SPEC.md"
    if not path.is_file():
        raise AcceptanceAuditError(f"missing master prompt: {path}")
    text = read(path)
    if "## 13. Final Acceptance Checklist" not in text:
        raise AcceptanceAuditError("master prompt is missing the Final Acceptance Checklist")
    if "Create a polished, original-IP Nintendo 64 game with a genuine 6–8 minute first-time playthrough" not in text:
        raise AcceptanceAuditError("master prompt does not match the reduced 6-8 minute authority")
    return text


def git_output(root: Path, *args: str) -> str:
    result = run(["git", *args], root=root)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def remote_is_public_repo(root: Path) -> bool:
    urls = git_output(root, "remote", "get-url", "origin").splitlines()
    return any("github.com" in url and "oh-ashen-one/n64game" in url for url in urls)


def rom_info(root: Path) -> tuple[bool, tuple[str, ...]]:
    rom = root / "build" / "game" / "n64game-gate3.z64"
    if not rom.is_file() or rom.is_symlink():
        return False, ()
    data = rom.read_bytes()[:4]
    if data != N64_MAGIC:
        return False, (f"{rom.relative_to(root)} has invalid N64 magic",)
    return True, (
        f"{rom.relative_to(root)} size={rom.stat().st_size} sha256={sha256(rom)}",
    )


def file_evidence(root: Path, *paths: str) -> tuple[str, ...]:
    evidence: list[str] = []
    for raw in paths:
        path = root / raw
        if path.is_file() and not path.is_symlink() and path.stat().st_size > 0:
            evidence.append(raw)
    return tuple(evidence)


def public_reproducibility_state(root: Path) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    path = root / "build" / "reports" / "public-reproducibility.json"
    if not path.is_file() or path.is_symlink():
        return "MISSING", (), ("build/reports/public-reproducibility.json from scripts/verify-public-reproducibility",)
    try:
        payload = json.loads(read(path))
    except json.JSONDecodeError:
        return "MISSING", (str(path.relative_to(root)),), ("public reproducibility report is not valid JSON",)
    head = git_output(root, "rev-parse", "HEAD")
    local_rom = payload.get("local", {}).get("rom", {})
    fresh_rom = payload.get("fresh_public_clone", {}).get("rom", {})
    artifact_rom = payload.get("ci_artifact", {}).get("rom", {})
    workflow = payload.get("workflow", {})
    expected = (local_rom.get("size"), local_rom.get("sha256"), local_rom.get("header_sha256"))
    if (
        payload.get("schema") == PUBLIC_REPRO_SCHEMA
        and payload.get("result") == "PASS"
        and payload.get("repo") == "oh-ashen-one/n64game"
        and payload.get("head_sha") == head
        and expected == (fresh_rom.get("size"), fresh_rom.get("sha256"), fresh_rom.get("header_sha256"))
        and expected == (artifact_rom.get("size"), artifact_rom.get("sha256"), artifact_rom.get("header_sha256"))
        and isinstance(workflow.get("run_id"), int)
        and str(workflow.get("url", "")).startswith("https://github.com/oh-ashen-one/n64game/actions/runs/")
    ):
        return "PASS", (
            f"{path.relative_to(root)} head={head}",
            f"public CI run={workflow['run_id']} artifact={workflow.get('artifact_name')}",
            f"local=fresh-clone=ci-artifact sha256={local_rom.get('sha256')}",
        ), ()
    return "MISSING", (str(path.relative_to(root)) + f" head={payload.get('head_sha', 'MISSING')}",), (
        "public reproducibility report is stale, malformed, or not bound to current HEAD",
    )


def certification_manifest_state(root: Path) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    manifest = root / "build" / "certification" / "evidence.json"
    if not manifest.is_file():
        return "MISSING", (), ("build/certification/evidence.json with real captured Ares logs",)
    result = run([str(root / "scripts" / "validate-certification-evidence"), "--manifest", str(manifest), "--rom", str(ROM)], root=root)
    if result.returncode != 0:
        return "MISSING", (str(manifest.relative_to(root)),), (result.stdout.strip() or "certification evidence did not validate",)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return "MISSING", (str(manifest.relative_to(root)),), ("validator output was not JSON",)
    return "PARTIAL", (
        f"{manifest.relative_to(root)} validated result={payload.get('result')} certification={payload.get('certification')}",
    ), ("validator explicitly reports NOT_CLAIMED; final visual/audio/controller/release checks still required",)


def visual_approval_state(root: Path) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    path = root / "docs" / "VISUAL_BENCHMARK_APPROVAL.md"
    if not path.is_file():
        return "MISSING", (), ("docs/VISUAL_BENCHMARK_APPROVAL.md",)
    text = read(path)
    match = DECISION_LINE.search(text)
    decision = match.group(1) if match else "MISSING"
    if decision == "APPROVED":
        return "PASS", (str(path.relative_to(root)),), ()
    if decision == "PENDING":
        return "MISSING", (str(path.relative_to(root)) + " Decision: PENDING",), ("approved production asset gates and visual benchmark",)
    return "MISSING", (str(path.relative_to(root)) + f" Decision: {decision}",), ("visual benchmark has no approved decision",)


def storyboard_state(root: Path) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    result = run([str(root / "scripts" / "validate-release-projection")], root=root)
    if result.returncode != 0:
        return "MISSING", (), (result.stdout.strip() or "storyboard projection validation failed",)
    expected = [
        *(f"storyboard/opening/panels/{index:02d}.png" for index in range(1, 13)),
        "storyboard/opening/CONTACT_SHEET.png",
        "storyboard/opening/continuity/CONTINUITY_SHEET.png",
        "storyboard/opening/COLOR_SCRIPT.png",
        "storyboard/opening/SHOT_LIST.md",
    ]
    present = file_evidence(root, *expected)
    if len(present) != len(expected):
        missing = tuple(sorted(set(expected) - set(present)))
        return "MISSING", present, missing
    return "PASS", ("scripts/validate-release-projection: " + result.stdout.strip(), *present), ()


def public_hygiene_state(root: Path) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    required = file_evidence(root, "LICENSE", "ASSET_LICENSE.md", "THIRD_PARTY_NOTICES.md", "README.md")
    result = run([str(root / "scripts" / "validate-public-hygiene")], root=root)
    if len(required) == 4 and result.returncode == 0:
        return "PARTIAL", (*required, "scripts/validate-public-hygiene: PASS"), ("final public release asset/license audit and real certification evidence",)
    missing = [path for path in ("LICENSE", "ASSET_LICENSE.md", "THIRD_PARTY_NOTICES.md", "README.md") if path not in required]
    if result.returncode != 0:
        missing.append(result.stdout.strip() or "public hygiene validation failed")
    return "MISSING", required, tuple(missing)


def host_spine_state(root: Path) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    report = root / "build" / "reports" / "host-tests.txt"
    evidence: list[str] = []
    if report.is_file():
        text = read(report)
        if "result=PASS" in text:
            evidence.append("build/reports/host-tests.txt result=PASS")
    if (root / "test" / "host" / "n64game_core_harness.c").is_file():
        evidence.append("test/host/n64game_core_harness.c input-only route/retry/save contracts")
    if evidence:
        return "PARTIAL", tuple(evidence), ("host tests are indirect; timed real Ares playthrough and visual/audio inspection are still required",)
    return "MISSING", (), ("host route/save/battle report",)


def ci_state(root: Path) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    repro_status, repro_evidence, repro_missing = public_reproducibility_state(root)
    rom_ok, rom_evidence = rom_info(root)
    reports = file_evidence(
        root,
        "build/game/n64game-gate3.z64.sha256",
        "build/game/n64game-gate3.map",
        "build/reports/rom-size.md",
        "build/reports/validation-summary.md",
        "build/reports/host-tests.txt",
    )
    if rom_ok and len(reports) == 5 and repro_status == "PASS":
        return "PASS", (*rom_evidence, *reports, *repro_evidence), ()
    if rom_ok and len(reports) == 5:
        return "PARTIAL", (*rom_evidence, *reports), ("fresh public clone build and downloaded public CI artifact equality must be verified for final release",)
    missing = []
    if not rom_ok:
        missing.append("structurally valid local ROM")
    for path in (
        "build/game/n64game-gate3.z64.sha256",
        "build/game/n64game-gate3.map",
        "build/reports/rom-size.md",
        "build/reports/validation-summary.md",
        "build/reports/host-tests.txt",
    ):
        if path not in reports:
            missing.append(path)
    missing.extend(repro_missing)
    return "MISSING", (*rom_evidence, *reports), tuple(missing)


def build_items(root: Path) -> list[AuditItem]:
    require_master(root)
    cert_status, cert_evidence, cert_missing = certification_manifest_state(root)
    visual_status, visual_evidence, visual_missing = visual_approval_state(root)
    storyboard_status, storyboard_evidence, storyboard_missing = storyboard_state(root)
    hygiene_status, hygiene_evidence, hygiene_missing = public_hygiene_state(root)
    host_status, host_evidence, host_missing = host_spine_state(root)
    ci_status, ci_evidence, ci_missing = ci_state(root)
    repro_status, repro_evidence, repro_missing = public_reproducibility_state(root)
    repo_evidence = (
        f"origin={git_output(root, 'remote', 'get-url', 'origin')}",
        f"HEAD={git_output(root, 'rev-parse', 'HEAD')}",
    )
    repo_status = "PASS" if remote_is_public_repo(root) and repro_status == "PASS" else ("PARTIAL" if remote_is_public_repo(root) else "MISSING")
    repo_evidence = (*repo_evidence, *repro_evidence)
    repo_missing = () if repo_status == "PASS" else (
        "credential-free fresh clone reproducible build proof",
    ) if remote_is_public_repo(root) else ("canonical public GitHub origin", *repro_missing)

    return [
        AuditItem("FAC-01", "The public repository exists and a fresh clone builds reproducibly.", repo_status, repo_evidence, repo_missing),
        AuditItem("FAC-02", "CI produces a structurally valid .z64, checksum, size/map evidence, and build report.", ci_status, ci_evidence, ci_missing),
        AuditItem("FAC-03", "The complete 6-8 minute chapter runs from cold boot to the stable beacon hook.", cert_status, cert_evidence, cert_missing),
        AuditItem("FAC-04", "Two timed runs satisfy the locked range with real player agency.", cert_status, cert_evidence, cert_missing),
        AuditItem("FAC-05", "Name entry, Annex exploration, Field Relay, one full 2v2 battle, victory/defeat/retry, save/reload, dialogue, transitions, and flags work.", host_status, host_evidence, host_missing),
        AuditItem("FAC-06", "Ten transition loops show no persistent memory growth; peak free heap is at least 512 KiB.", cert_status, cert_evidence, cert_missing),
        AuditItem("FAC-07", "Required scenes meet the evidence-backed 30 FPS target.", cert_status, cert_evidence, cert_missing),
        AuditItem("FAC-08", "There are no crashes, softlocks, collision traps, missing assets, broken audio, unreadable required UI, progression blockers, duplicate rewards, or corrupt transitions.", "MISSING", host_evidence, ("full Ares QA matrix and visual/audio inspection",)),
        AuditItem("FAC-09", "Every retained production asset has provenance, passed seven art gates, and looks finished at the actual gameplay camera.", visual_status, visual_evidence, visual_missing),
        AuditItem("FAC-10", "No primitive, default material, raw generated texture, temporary animation, unfinished environment, or gameplay-affecting TODO remains, except INSERT CUTSCENE HERE.", visual_status, visual_evidence, visual_missing),
        AuditItem("FAC-11", "Twelve storyboard panels, individual files, contact sheet, continuity sheet, color script, and shot list are visually reviewed and delivered directly to the user.", storyboard_status, storyboard_evidence, storyboard_missing),
        AuditItem("FAC-12", "Code/asset licensing, third-party notices, secret scan, and public hygiene pass.", hygiene_status, hygiene_evidence, hygiene_missing),
        AuditItem("FAC-13", "Emulator-only claims are labeled honestly; real N64 hardware is not claimed without testing.", "PARTIAL", ("README labels Ares/emulator evidence and avoids real hardware claim",), ("final release notes must preserve emulator-only labeling",)),
    ]


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# N64GAME Final Acceptance Audit",
        "",
        f"- Result: `{payload['result']}`",
        f"- Passing items: `{payload['pass_count']} / {payload['item_count']}`",
        f"- Source: `{payload['master_prompt']}`",
        "",
        "| ID | Status | Requirement | Missing proof |",
        "|---|---|---|---|",
    ]
    for item in payload["items"]:
        missing = "<br>".join(item["missing"]) if item["missing"] else "—"
        lines.append(f"| `{item['id']}` | `{item['status']}` | {item['requirement']} | {missing} |")
    lines.extend([
        "",
        "This audit is fail-closed. `PARTIAL` and `MISSING` are not completion.",
        "Do not mark the goal complete until every row is `PASS` with current evidence.",
        "",
    ])
    return "\n".join(lines)


def audit(root: Path) -> dict[str, Any]:
    items = build_items(root)
    pass_count = sum(1 for item in items if item.status == "PASS")
    result = "COMPLETE" if pass_count == len(items) else "INCOMPLETE"
    return {
        "schema": "n64game-final-acceptance-audit-v1",
        "result": result,
        "master_prompt": str((root / "docs" / "N64GAME_MASTER_SPEC.md").relative_to(root)),
        "item_count": len(items),
        "pass_count": pass_count,
        "items": [item.to_json() for item in items],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        payload = audit(root)
    except (OSError, AcceptanceAuditError) as exc:
        print(f"FINAL_ACCEPTANCE_AUDIT_ERROR: {exc}")
        return 2

    text = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(render_markdown(payload), encoding="utf-8")
    print(text, end="")
    if args.require_complete and payload["result"] != "COMPLETE":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
