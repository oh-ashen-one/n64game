#!/usr/bin/env python3
"""Deterministic Gate 3 pin, ROM, asset, and report checks."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "config" / "toolchain.lock.json"
ROM_PATH = ROOT / "build" / "game" / "n64game-gate3.z64"
MAP_PATH = ROOT / "build" / "game" / "n64game-gate3.map"
ELF_SIZE_PATH = ROOT / "build" / "game" / "n64game-gate3.elf.size.txt"
RUNTIME_ASSET_PATH = ROOT / "config" / "runtime-assets.tsv"
RUNTIME_ASSET_HEADER = "asset_id\tkind\tsource_path\truntime_path\tsha256\tstatus\n"
RUNTIME_CANDIDATE_PATH = ROOT / "config" / "runtime-candidates.tsv"
RUNTIME_CANDIDATE_HEADER = (
    "candidate_id\tkind\tsource_path\truntime_path\tsource_sha256\tstatus"
)
RUNTIME_CANDIDATE_STATUS = "SOURCE_CANDIDATE_NOT_GATE_EVIDENCE"
N64_MAGIC = bytes.fromhex("80371240")
ROM_LIMIT = 16 * 1024 * 1024
LIBDRAGON_IPL3_END = 6444
LIBDRAGON_IPL3_PAYLOAD_SHA256 = "587926030874012808dc2645a2eae0106b180f24892154eaded270ae3abbfcc9"
TOC_OFFSET = (LIBDRAGON_IPL3_END + 15) & ~15
EXPECTED_HOST_TEST_REPORT = (
    "suite=n64game_host_contracts\n"
    "result=PASS\n"
    "scope=dependency pins, production and candidate runtime manifests, ROM header parser, report contract, boot-capture manifest, semantic snapshot, production-shared lifecycle branch/death tests, exact opening timing, controller disconnect freeze, four-sector input-only Annex route, acceleration/run/collision, examines, pause and Field Relay pages, controller-only 2v2 victory, defeat/retry/return snapshots, post-chapter archive, versioned canonical checkpoints, save debounce, corruption rejection, and dual-slot copy-on-write recovery (live adapters, Ares timing, and final visual approval excluded)\n"
)


class ContractError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_lock() -> dict[str, Any]:
    with LOCK_PATH.open("r", encoding="utf-8") as handle:
        lock = json.load(handle)
    if lock.get("schema_version") != 1:
        raise ContractError("unsupported toolchain lock schema")
    return lock


def run(command: list[str], *, cwd: Path = ROOT, timeout: int = 30, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ContractError(f"command failed: {' '.join(command)}: {exc}") from exc
    if check and result.returncode != 0:
        output = result.stdout.strip()
        raise ContractError(f"command failed ({result.returncode}): {' '.join(command)}: {output}")
    return result


def git(*args: str, check: bool = True) -> str:
    return run(["git", *args], check=check).stdout.strip()


def index_gitlink(path: str) -> str:
    fields = git("ls-files", "--stage", "--", path).split()
    if len(fields) < 4 or fields[0] != "160000":
        raise ContractError(f"{path} is not an indexed gitlink")
    return fields[1]


def verify_pins() -> dict[str, str]:
    lock = load_lock()
    resolved: dict[str, str] = {}
    for key, path in (("libdragon", "vendor/libdragon"), ("tiny3d", "vendor/tiny3d")):
        expected = lock[key]["commit"]
        indexed = index_gitlink(path)
        if indexed != expected:
            raise ContractError(f"{path} index pin is {indexed}, expected {expected}")
        worktree = git("-C", path, "rev-parse", "HEAD")
        if worktree != expected:
            raise ContractError(f"{path} checkout is {worktree}, expected {expected}")
        if git("-C", path, "status", "--porcelain"):
            raise ContractError(f"{path} checkout is dirty")
        resolved[key] = expected

    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    expected_cli = lock["libdragon_cli"]["version"]
    if package.get("dependencies", {}).get("libdragon") != expected_cli:
        raise ContractError("package.json does not use the exact libdragon CLI version")

    package_lock_path = ROOT / "package-lock.json"
    if not package_lock_path.is_file():
        raise ContractError("package-lock.json is missing")
    package_lock = json.loads(package_lock_path.read_text(encoding="utf-8"))
    cli_entry = package_lock.get("packages", {}).get("node_modules/libdragon", {})
    if cli_entry.get("version") != expected_cli:
        raise ContractError("package-lock libdragon CLI version mismatch")
    if cli_entry.get("integrity") != lock["libdragon_cli"]["npm_integrity"]:
        raise ContractError("package-lock libdragon CLI integrity mismatch")

    cli_config = json.loads((ROOT / ".libdragon" / "config.json").read_text(encoding="utf-8"))
    if cli_config.get("imageName") != lock["container"]["reference"]:
        raise ContractError(".libdragon image is not the immutable container reference")
    if cli_config.get("vendorDirectory") != "build/deps/libdragon":
        raise ContractError(".libdragon vendor directory must remain inside build/")
    if cli_config.get("vendorStrategy") != "manual":
        raise ContractError(".libdragon vendor strategy must be manual")

    resolved["libdragon_cli"] = expected_cli
    resolved["container"] = lock["container"]["oci_index_digest"]
    return resolved


def inspect_rom(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise ContractError(f"ROM is not one regular file: {path}")
    size = path.stat().st_size
    if size < 4096:
        raise ContractError(f"ROM is implausibly small: {size} bytes")
    if size >= ROM_LIMIT:
        raise ContractError(f"Gate 3 ROM exceeds the locked <16 MiB target: {size} bytes")
    if size % 16384:
        raise ContractError("ROM byte size is not aligned to the required 16 KiB boundary")
    data = path.read_bytes()
    header = data[:64]
    if len(header) != 64 or header[:4] != N64_MAGIC:
        raise ContractError("ROM does not have the canonical big-endian N64 header")
    title = header[0x20:0x34].decode("ascii", errors="strict").rstrip(" \x00")
    if title != "N64GAME OPENING":
        raise ContractError(f"unexpected N64 ROM title: {title!r}")
    # libdragon's open IPL3 deliberately does not use the legacy commercial-ROM
    # checksum. Its pinned n64tool output leaves both words at zero.
    if header[0x10:0x18] != bytes(8):
        raise ContractError("legacy checksum words differ from pinned libdragon IPL3 output")
    entrypoint = int.from_bytes(header[0x08:0x0C], "big")
    if not (0x80000400 <= entrypoint < 0x80400000) or entrypoint % 8:
        raise ContractError(f"ROM entrypoint is outside aligned standard-4-MB RDRAM: 0x{entrypoint:08x}")
    if header[0x34:0x38] != bytes(4):
        raise ContractError("advanced header must declare plain N64 controllers on all four ports")
    if header[0x3B] != ord("N"):
        raise ContractError("advanced header media category is not cartridge ('N')")
    if header[0x3C:0x3E] != b"ED":
        raise ContractError("advanced homebrew cartridge ID is not 'ED'")
    if header[0x3E] != 0:
        raise ContractError("ROM region byte must remain neutral for the region-free declaration")
    if header[0x3F] != 0x12:
        raise ContractError("advanced header config must be EEPROM4K plus region-free (0x12)")

    if len(data) < LIBDRAGON_IPL3_END:
        raise ContractError("ROM is shorter than the pinned libdragon IPL3")
    ipl3_payload = data[0x40:LIBDRAGON_IPL3_END]
    ipl3_payload_sha256 = hashlib.sha256(ipl3_payload).hexdigest()
    if ipl3_payload_sha256 != LIBDRAGON_IPL3_PAYLOAD_SHA256:
        raise ContractError("ROM IPL3 payload does not match the pinned libdragon bootcode")
    if data[TOC_OFFSET:TOC_OFFSET + 4] != b"TOC0":
        raise ContractError("ROM does not contain libdragon's deterministic TOC at the expected offset")

    elf_offsets = [
        offset
        for offset in range((LIBDRAGON_IPL3_END + 255) & ~255, len(data) - 19, 256)
        if data[offset:offset + 4] == b"\x7fELF"
    ]
    if not elf_offsets:
        raise ContractError("ROM does not contain a 256-byte-aligned ELF payload")
    elf_offset = elf_offsets[0]
    elf_ident = data[elf_offset:elf_offset + 20]
    if elf_ident[5] != 2 or int.from_bytes(elf_ident[18:20], "big") != 8:
        raise ContractError("embedded ELF is not a big-endian MIPS executable")
    try:
        report_path = path.relative_to(ROOT).as_posix()
    except ValueError:
        report_path = str(path)
    return {
        "path": report_path,
        "size_bytes": size,
        "sha256": sha256_file(path),
        "header_magic": header[:4].hex(),
        "header_sha256": hashlib.sha256(header).hexdigest(),
        "title": title,
        "country_code_hex": f"{header[0x3E]:02x}",
        "entrypoint_hex": f"0x{entrypoint:08x}",
        "legacy_checksum_policy": "not_required_by_libdragon_ipl3; zero_as_pinned",
        "advanced_header": {
            "controller_ports_hex": header[0x34:0x38].hex(),
            "media_category": chr(header[0x3B]),
            "cart_id": header[0x3C:0x3E].decode("ascii"),
            "region_hex": f"{header[0x3E]:02x}",
            "config_hex": f"{header[0x3F]:02x}",
        },
        "ipl3_payload_sha256": ipl3_payload_sha256,
        "toc_offset": TOC_OFFSET,
        "elf_offset": elf_offset,
    }


def validate_runtime_assets() -> dict[str, Any]:
    data = RUNTIME_ASSET_PATH.read_text(encoding="utf-8")
    if data != RUNTIME_ASSET_HEADER:
        raise ContractError(
            "Gate 3 runtime asset manifest must contain only its canonical header; "
            "production assets stay locked until the visual benchmark"
        )
    tracked_roms = [line for line in git("ls-files").splitlines() if line.lower().endswith((".z64", ".n64", ".v64"))]
    if tracked_roms:
        raise ContractError(f"ROM binaries entered Git history: {', '.join(tracked_roms)}")
    return {
        "manifest": RUNTIME_ASSET_PATH.relative_to(ROOT).as_posix(),
        "sha256": sha256_file(RUNTIME_ASSET_PATH),
        "runtime_asset_count": 0,
        "scope": "Gate 3 diagnostic ROM; no production visual/audio assets authorized",
    }


def validate_runtime_candidates() -> dict[str, Any]:
    data = RUNTIME_CANDIDATE_PATH.read_text(encoding="utf-8")
    if not data.endswith("\n") or "\r" in data:
        raise ContractError("runtime candidate manifest must be canonical UTF-8/LF text")
    lines = data.splitlines()
    if not lines or lines[0] != RUNTIME_CANDIDATE_HEADER:
        raise ContractError("runtime candidate manifest header is not canonical")

    expected = (
        (
            "candidate.echo.quarrune.hero",
            "model_glb",
            "runtime-candidates/echo/echo.quarrune/quarrune_hero.glb",
            "rom:/echo/echo.quarrune/quarrune_hero.t3dm",
        ),
        (
            "candidate.echo.quarrune.body",
            "texture_png",
            "runtime-candidates/echo/echo.quarrune/tex_quarrune_body_ci8_64x64.png",
            "rom:/echo/echo.quarrune/tex_quarrune_body_ci8_64x64.sprite",
        ),
        (
            "candidate.echo.quarrune.accent",
            "texture_png",
            "runtime-candidates/echo/echo.quarrune/tex_quarrune_accent_ci4_32x32.png",
            "rom:/echo/echo.quarrune/tex_quarrune_accent_ci4_32x32.sprite",
        ),
        (
            "candidate.echo.quarrune.shadow",
            "texture_png",
            "runtime-candidates/echo/echo.quarrune/tex_quarrune_blob_shadow_ia8_32x32.png",
            "rom:/echo/echo.quarrune/tex_quarrune_blob_shadow_ia8_32x32.sprite",
        ),
        (
            "candidate.env.annex.atrium_lower.threshold_kit",
            "model_glb",
            "runtime-candidates/env/env.annex.threshold_kit/annex_threshold_kit.glb",
            "rom:/env/env.annex.threshold_kit/annex_threshold_kit.t3dm",
        ),
        (
            "candidate.env.annex.atrium_lower.architecture",
            "texture_png",
            "runtime-candidates/env/env.annex.threshold_kit/tex_annex_architecture_ci4_64x64.png",
            "rom:/env/env.annex.threshold_kit/tex_annex_architecture_ci4_64x64.sprite",
        ),
        (
            "candidate.env.annex.atrium_lower.trim_resonance",
            "texture_png",
            "runtime-candidates/env/env.annex.threshold_kit/tex_annex_trim_resonance_ci4_64x32.png",
            "rom:/env/env.annex.threshold_kit/tex_annex_trim_resonance_ci4_64x32.sprite",
        ),
        (
            "candidate.env.annex.atrium_lower.resonance_mask",
            "texture_png",
            "runtime-candidates/env/env.annex.threshold_kit/tex_annex_resonance_mask_ia8_32x32.png",
            "rom:/env/env.annex.threshold_kit/tex_annex_resonance_mask_ia8_32x32.sprite",
        ),
        (
            "candidate.chr.player.ari.hero",
            "model_glb",
            "runtime-candidates/chr/chr.player.ari/player_ari.glb",
            "rom:/chr/chr.player.ari/player_ari.t3dm",
        ),
        (
            "candidate.chr.player.ari.body",
            "texture_png",
            "runtime-candidates/chr/chr.player.ari/tex_player_ari_body_ci8_64x64.png",
            "rom:/chr/chr.player.ari/tex_player_ari_body_ci8_64x64.sprite",
        ),
        (
            "candidate.chr.player.ari.face",
            "texture_png",
            "runtime-candidates/chr/chr.player.ari/tex_player_ari_face_ci4_32x32.png",
            "rom:/chr/chr.player.ari/tex_player_ari_face_ci4_32x32.sprite",
        ),
    )
    rows: list[dict[str, str]] = []
    observed_identity: list[tuple[str, str, str, str]] = []
    runtime_paths: set[str] = set()
    source_paths: set[str] = set()
    for line_number, line in enumerate(lines[1:], start=2):
        fields = line.split("\t")
        if len(fields) != 6:
            raise ContractError(f"runtime candidate row {line_number} has the wrong field count")
        candidate_id, kind, source_path, runtime_path, source_digest, status = fields
        observed_identity.append((candidate_id, kind, source_path, runtime_path))
        if status != RUNTIME_CANDIDATE_STATUS:
            raise ContractError(f"runtime candidate row {line_number} has an approval-like status")
        if len(source_digest) != 64 or any(character not in "0123456789abcdef" for character in source_digest):
            raise ContractError(f"runtime candidate row {line_number} has an invalid SHA-256")
        if source_path in source_paths or runtime_path in runtime_paths:
            raise ContractError(f"runtime candidate row {line_number} duplicates a source or runtime path")
        source_paths.add(source_path)
        runtime_paths.add(runtime_path)
        if not source_path.startswith("runtime-candidates/") or ".." in Path(source_path).parts:
            raise ContractError(f"runtime candidate row {line_number} escapes its temporary source root")
        source = ROOT / source_path
        if not source.is_file() or source.is_symlink():
            raise ContractError(f"runtime candidate source is not one regular file: {source_path}")
        if sha256_file(source) != source_digest:
            raise ContractError(f"runtime candidate source hash mismatch: {source_path}")
        attributes = git("check-attr", "filter", "--", source_path).split(": ")
        if len(attributes) != 3 or attributes[-1] != "lfs":
            raise ContractError(f"runtime candidate binary is not assigned to Git LFS: {source_path}")
        rows.append(
            {
                "candidate_id": candidate_id,
                "kind": kind,
                "source_path": source_path,
                "runtime_path": runtime_path,
                "source_sha256": source_digest,
                "status": status,
            }
        )
    if tuple(observed_identity) != expected:
        raise ContractError(
            "runtime candidate identity/path census is not the exact Quarrune, Annex, and Ari proof set"
        )
    return {
        "manifest": RUNTIME_CANDIDATE_PATH.relative_to(ROOT).as_posix(),
        "sha256": sha256_file(RUNTIME_CANDIDATE_PATH),
        "runtime_candidate_count": len(rows),
        "status": RUNTIME_CANDIDATE_STATUS,
        "scope": (
            "Quarrune, Annex, and Ari in-engine proof only; "
            "not Gate evidence or production approval"
        ),
        "entries": rows,
    }


def source_identity() -> dict[str, Any]:
    status = git("status", "--porcelain", "--untracked-files=normal", "--ignore-submodules=none")
    return {
        "commit": git("rev-parse", "HEAD"),
        "tree": git("rev-parse", "HEAD^{tree}"),
        "commit_time": git("show", "-s", "--format=%cI", "HEAD"),
        "dirty": bool(status),
        "dirty_paths": status.splitlines(),
    }


def required_nonempty_file(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise ContractError(f"{label} is not one regular file: {path}")
    size = path.stat().st_size
    if size <= 0:
        raise ContractError(f"{label} is empty: {path}")
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "size_bytes": size,
        "sha256": sha256_file(path),
    }


def write_reports(rom_path: Path = ROM_PATH) -> dict[str, Any]:
    pins = verify_pins()
    assets = validate_runtime_assets()
    candidates = validate_runtime_candidates()
    rom = inspect_rom(rom_path)
    lock = load_lock()
    source = source_identity()
    reports = ROOT / "build" / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    map_info = required_nonempty_file(MAP_PATH, "linker map")
    elf_size_info = required_nonempty_file(ELF_SIZE_PATH, "ELF size report")

    host_report = reports / "host-tests.txt"
    host_info = required_nonempty_file(host_report, "host test report")
    if host_report.read_text(encoding="utf-8") != EXPECTED_HOST_TEST_REPORT:
        raise ContractError("host test report is not the exact n64game host-contract PASS record")
    host_status = "PASS"
    manifest = {
        "schema_version": 1,
        "artifact_kind": "runtime_integration_candidate",
        "full_game_claim": False,
        "ares_boot": "NOT_RUN",
        "source": source,
        "pins": pins,
        "toolchain": lock,
        "runtime_assets": assets,
        "runtime_candidates": candidates,
        "rom": rom,
        "linker_map": map_info,
        "elf_size_report": elf_size_info,
        "host_test_report": host_info,
        "validation": {
            "host_tests": host_status,
            "rom_header_and_advanced_config": "PASS",
            "pinned_libdragon_ipl3": "PASS",
            "embedded_big_endian_mips_elf": "PASS",
            "legacy_header_checksum": "NOT_REQUIRED_ZERO_AS_PINNED",
            "rom_budget": "PASS",
            "dependency_pins": "PASS",
            "production_runtime_asset_count": 0,
            "runtime_candidate_asset_count": candidates["runtime_candidate_count"],
            "ares_boot": "NOT_RUN",
        },
    }

    manifest_path = reports / "dependency-build-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    checksum_path = rom_path.with_suffix(rom_path.suffix + ".sha256")
    checksum_path.write_text(f"{rom['sha256']}  {rom_path.name}\n", encoding="ascii")

    size_report = reports / "rom-size.md"
    size_report.write_text(
        "# Gate 3 ROM Size Report\n\n"
        f"- ROM: `{rom['path']}`\n"
        f"- Size: {rom['size_bytes']} bytes ({rom['size_bytes'] / (1024 * 1024):.3f} MiB)\n"
        f"- Budget: PASS (`< 16 MiB`)\n"
        f"- SHA-256: `{rom['sha256']}`\n"
        f"- Header SHA-256: `{rom['header_sha256']}`\n"
        f"- Header magic: `{rom['header_magic']}`\n"
        f"- Header title: `{rom['title']}`\n"
        f"- Pinned IPL3 payload: PASS (`{rom['ipl3_payload_sha256']}`)\n"
        f"- Embedded ELF offset: `{rom['elf_offset']}`\n"
        f"- Linker map: `{map_info['path']}` ({map_info['size_bytes']} bytes, SHA-256 `{map_info['sha256']}`)\n"
        f"- ELF size report: `{elf_size_info['path']}` ({elf_size_info['size_bytes']} bytes, SHA-256 `{elf_size_info['sha256']}`)\n",
        encoding="utf-8",
    )

    summary_path = reports / "validation-summary.md"
    summary_path.write_text(
        "# Gate 3 Validation Summary\n\n"
        "This artifact is a pinned Tiny3D/libdragon build candidate. CI does not boot Ares, so this is not yet a boot proof, the playable opening, or a full-game claim.\n\n"
        f"- Dependency pins: PASS\n"
        f"- N64 header and advanced homebrew config: PASS\n"
        f"- Pinned libdragon IPL3: PASS\n"
        f"- Embedded big-endian MIPS ELF: PASS\n"
        f"- Legacy header checksum: not required by libdragon IPL3; zero as pinned\n"
        f"- ROM budget: PASS ({rom['size_bytes']} bytes)\n"
        f"- Host contract tests: {host_status}\n"
        f"- Ares boot: NOT RUN (separate visual evidence required)\n"
        f"- Runtime production assets: 0 (production approval remains locked)\n"
        f"- Runtime candidate inputs: {candidates['runtime_candidate_count']} ({candidates['scope']})\n"
        f"- Source commit: `{source['commit']}`\n"
        f"- Dirty source tree: `{'yes' if source['dirty'] else 'no'}`\n",
        encoding="utf-8",
    )
    for generated_path, label in (
        (manifest_path, "dependency build manifest"),
        (checksum_path, "ROM checksum"),
        (size_report, "ROM size report"),
        (summary_path, "validation summary"),
    ):
        required_nonempty_file(generated_path, label)
    return manifest


def command_output(command: list[str], timeout: int = 10) -> tuple[bool, str]:
    try:
        result = run(command, timeout=timeout, check=False)
    except ContractError as exc:
        return False, str(exc)
    return result.returncode == 0, result.stdout.strip()


def find_docker() -> str | None:
    found = shutil.which("docker")
    if found:
        return found
    bundled = Path("/Applications/Docker.app/Contents/Resources/bin/docker")
    return str(bundled) if bundled.is_file() else None


def bootstrap(mode: str) -> int:
    lock = load_lock()
    failures: list[str] = []
    print(f"host_arch={platform.machine()}")
    print(f"host_os={platform.platform()}")
    disk = shutil.disk_usage(ROOT)
    print(f"disk_free_bytes={disk.free}")
    print(f"container_reference={lock['container']['reference']}")
    print(f"container_platform={lock['container']['platform']}")

    try:
        resolved = verify_pins()
        print(f"dependency_pins=PASS {json.dumps(resolved, sort_keys=True)}")
    except ContractError as exc:
        failures.append(str(exc))
        print(f"dependency_pins=FAIL {exc}")

    for label, command in (
        ("git_lfs", ["git", "lfs", "version"]),
        ("node", ["node", "--version"]),
        ("npm", ["npm", "--version"]),
        (
            "libdragon_cli",
            ["node", str(ROOT / "node_modules" / "libdragon" / "index.js"), "version"],
        ),
    ):
        ok, output = command_output(command)
        print(f"{label}={'PASS' if ok else 'FAIL'} {output}")
        if not ok and mode in {"build", "ci", "all"}:
            failures.append(f"{label} unavailable")

    docker = find_docker()
    if docker:
        ok_client, client = command_output([docker, "--version"], timeout=15)
        ok_engine, engine = command_output([docker, "version", "--format", "{{.Server.Version}}"], timeout=20)
        ok_image, image = command_output([docker, "image", "inspect", lock["container"]["reference"], "--format", "{{.Id}}"], timeout=15)
        print(f"docker_client={'PASS' if ok_client else 'FAIL'} path={docker} {client}")
        print(f"docker_engine={'PASS' if ok_engine else 'FAIL'} {engine}")
        print(f"pinned_image_local={'PASS' if ok_image else 'NOT_PRESENT'} {image}")
        if mode in {"build", "ci", "all"} and (not ok_client or not ok_engine):
            failures.append("Docker client/engine is not ready")
    else:
        print("docker_client=FAIL not found")
        if mode in {"build", "ci", "all"}:
            failures.append("Docker CLI is missing")

    ares_rel = lock["ares"]["macos_user_relative_path"]
    ares = Path(os.environ.get("N64GAME_ARES_BINARY", str(Path.home() / ares_rel)))
    ares_ok = ares.is_file() and not ares.is_symlink() and sha256_file(ares) == lock["ares"]["macos_executable_sha256"]
    version_ok = False
    version_text = "not installed"
    if ares_ok:
        with tempfile.TemporaryDirectory(prefix="n64game-ares-check-") as temp_dir:
            version_ok, version_text = command_output([str(ares), "--settings-file", str(Path(temp_dir) / "settings.bml"), "--version"])
        version_ok = version_ok and lock["ares"]["version"] in version_text
    print(f"ares_v148={'PASS' if ares_ok and version_ok else 'FAIL'} path={ares} {version_text}")
    if mode == "all" and not (ares_ok and version_ok):
        failures.append("Ares v148 exact binary is missing")

    blender = shutil.which("blender")
    if blender:
        ok, output = command_output([blender, "--version"], timeout=15)
        first_line = output.splitlines()[0] if output else "unknown"
        print(f"blender_observed={'PASS' if ok else 'FAIL'} {first_line}")
        print(f"blender_target={lock['authoring']['blender_target']}")
    else:
        print(f"blender_observed=NOT_PRESENT target={lock['authoring']['blender_target']}")

    if failures:
        for failure in failures:
            print(f"error={failure}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify-pins")
    sub.add_parser("validate-assets")
    validate_rom_parser = sub.add_parser("validate-rom")
    validate_rom_parser.add_argument("rom", nargs="?", default=str(ROM_PATH))
    report_parser = sub.add_parser("report")
    report_parser.add_argument("rom", nargs="?", default=str(ROM_PATH))
    bootstrap_parser = sub.add_parser("bootstrap")
    bootstrap_parser.add_argument("--mode", choices=("report", "build", "ci", "all"), default="report")
    args = parser.parse_args()

    try:
        if args.command == "verify-pins":
            print(json.dumps(verify_pins(), sort_keys=True))
        elif args.command == "validate-assets":
            print(json.dumps({
                "production": validate_runtime_assets(),
                "candidates": validate_runtime_candidates(),
            }, sort_keys=True))
        elif args.command == "validate-rom":
            rom_argument = Path(args.rom)
            if rom_argument.is_symlink():
                raise ContractError(f"ROM path must not be a symlink: {rom_argument}")
            print(json.dumps(inspect_rom(rom_argument.resolve()), sort_keys=True))
        elif args.command == "report":
            rom_argument = Path(args.rom)
            if rom_argument.is_symlink():
                raise ContractError(f"ROM path must not be a symlink: {rom_argument}")
            manifest = write_reports(rom_argument.resolve())
            print(json.dumps({"rom_sha256": manifest["rom"]["sha256"], "result": "PASS"}, sort_keys=True))
        elif args.command == "bootstrap":
            return bootstrap(args.mode)
    except (ContractError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
