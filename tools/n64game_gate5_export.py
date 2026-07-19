#!/usr/bin/env python3
"""Deterministic, fail-closed Gate-5 exporter for the paired Quarrune package.

This is deliberately narrow.  It accepts only ``echo.quarrune`` paired with
``anm.echo.quarrune``, consumes only the frozen selector vocabulary, runs the
reviewed Blender/Tiny3D/libdragon command vectors twice in clean staging roots,
validates the complete package with the repository's byte-level Ruby reader,
and promotes both owners as one rollback-protected transaction.

The ``--candidate`` mode is the only bootstrap path.  It requires a source-only
allowlist and materializes deterministic review candidates, but it is not a
Gate-5 approval.  The normal mode requires exact OUTPUT rows and byte-compares
the regenerated pair with those already reviewed snapshots before promotion.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
MODEL_SCOPE = "echo.quarrune"
ANIMATION_SCOPE = "anm.echo.quarrune"
MODEL_SELECTORS = (
    "ASSET:blob_shadow",
    "ASSET:distance_model",
    "ASSET:hero_model",
    "ASSET:rig",
    "ASSET:texture",
)
ANIMATION_NAMES = (
    "brace_relay",
    "entrance",
    "hit",
    "horizon_break",
    "idle_a",
    "idle_b",
    "knockout",
    "reposition",
    "ridge_ram",
)
ANIMATION_SELECTORS = tuple(f"CLIP:{name}" for name in ANIMATION_NAMES)
SUBSET_HEADER = (
    "production_id",
    "subset_sha256",
    "stage",
    "member_path",
    "member_sha256",
    "manifest_role",
    "export_selectors_csv",
)
HEX64 = re.compile(r"^[0-9a-f]{64}$")
BUILD_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")
SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
GENERIC_BUILD_PARTS = {
    "pending", "none", "unassigned", "unknown", "todo", "tbd", "test", "testing",
    "example", "sample", "placeholder", "dummy", "fake", "reviewer", "operator",
    "person", "user", "agent", "owner", "creator", "temp", "temporary", "na", "n-a",
    "nil", "null",
}
BINARY_LFS_EXTENSIONS = {
    ".blend", ".fbx", ".glb", ".gltf", ".psd", ".kra", ".xcf", ".png", ".jpg",
    ".jpeg", ".webp", ".qoi", ".mp4", ".mov", ".mkv", ".wav", ".flac", ".aiff",
    ".ogg", ".t3dm", ".sdata", ".sprite",
}

HERO_MODEL_PATH = "review/echo.quarrune/g5/quarrune_hero.t3dm"
DISTANCE_MODEL_PATH = "review/echo.quarrune/g5/quarrune_distance.t3dm"
BODY_TEXTURE_PATH = "review/echo.quarrune/g5/tex_quarrune_body_ci8_64x64.sprite"
ACCENT_TEXTURE_PATH = "review/echo.quarrune/g5/tex_quarrune_accent_ci4_32x32.sprite"
BLOB_SHADOW_PATH = "review/echo.quarrune/g5/tex_quarrune_blob_shadow_ia8_32x32.sprite"
RUNTIME_BINDING_PATH = "review/echo.quarrune/g5/RUNTIME_BINDING.tsv"
MODEL_MANIFEST_PATH = "review/echo.quarrune/g5/OUTPUT_MANIFEST.sha256"
ANIMATION_HEADER_PATH = "review/anm.echo.quarrune/g5/anm_echo_quarrune.t3dm"
ANIMATION_STREAM_PATHS = tuple(
    f"review/anm.echo.quarrune/g5/anm_echo_quarrune.{index}.sdata" for index in range(9)
)
SKELETON_BINDING_PATH = "review/anm.echo.quarrune/g5/SKELETON_BINDING.tsv"
ANIMATION_MANIFEST_PATH = "review/anm.echo.quarrune/g5/OUTPUT_MANIFEST.sha256"

MODEL_BINARY_ROLES = {
    DISTANCE_MODEL_PATH: "output.tiny3d.model",
    HERO_MODEL_PATH: "output.tiny3d.model",
    BODY_TEXTURE_PATH: "output.texture.body",
    ACCENT_TEXTURE_PATH: "output.texture.accent",
    BLOB_SHADOW_PATH: "output.blob_shadow.sprite",
}
ANIMATION_BINARY_ROLES = {
    ANIMATION_HEADER_PATH: "output.tiny3d.animation_header",
    **{path: "output.tiny3d.animation_stream" for path in ANIMATION_STREAM_PATHS},
}
MODEL_ROLES = {**MODEL_BINARY_ROLES, RUNTIME_BINDING_PATH: "output.runtime_binding"}
ANIMATION_ROLES = {**ANIMATION_BINARY_ROLES, SKELETON_BINDING_PATH: "output.skeleton_binding"}
MANAGED_OUTPUT_PATHS = tuple(sorted((*MODEL_ROLES, *ANIMATION_ROLES)))
MANAGED_PATHS = tuple(sorted((*MANAGED_OUTPUT_PATHS, MODEL_MANIFEST_PATH, ANIMATION_MANIFEST_PATH)))

SOURCE_FILENAMES = {
    "body": "tex_quarrune_body_ci8_64x64.png",
    "accent": "tex_quarrune_accent_ci4_32x32.png",
    "shadow": "tex_quarrune_blob_shadow_ia8_32x32.png",
}

RUNTIME_BINDING_KEYS = (
    "schema", "libdragon_commit", "tiny3d_commit", "runtime_helper_paths",
    "runtime_helper_bundle_sha256", "production_id", "body_sprite_path",
    "body_sprite_sha256", "body_rom_path", "body_top_reference", "body_top_rect_px",
    "body_bottom_reference", "body_bottom_rect_px", "body_reference_size_px",
    "body_upload_mode", "material_profile", "accent_sprite_path", "accent_sprite_sha256",
    "accent_rom_path", "blob_shadow_sprite_path", "blob_shadow_sprite_sha256",
    "blob_shadow_rom_path", "blob_shadow_format", "blob_shadow_size_px", "footprint_mm",
    "footprint_offset_mm", "base_opacity_q8", "build_id",
)
BINDING_KEYS = (
    "schema", "tiny3d_commit", "model_production_id", "animation_production_id",
    "hero_model_path", "hero_model_sha256", "distance_model_path", "distance_model_sha256",
    "animation_header_path", "animation_header_sha256", "animation_stream_set_sha256",
    "skeleton_signature_sha256", "bone_count", "animation_names", "build_id",
)


class Gate5ExportError(RuntimeError):
    """Raised when the exporter cannot prove the paired result."""


@dataclass(frozen=True)
class ManifestEntry:
    path: str
    count: int
    digest: str
    build: str
    capture: str
    role: str
    kind: str = "git"
    mode: str = "100644"

    def ruby(self) -> dict[str, object]:
        return {
            "path": self.path,
            "count": self.count,
            "digest": self.digest,
            "build": self.build,
            "capture": self.capture,
            "role": self.role,
            "kind": self.kind,
            "mode": self.mode,
        }


@dataclass(frozen=True)
class AllowlistRow:
    production_id: str
    subset_sha256: str
    stage: str
    member_path: str
    member_sha256: str
    manifest_role: str
    selectors: tuple[str, ...]


@dataclass(frozen=True)
class SourceInputs:
    model_blend: Path
    animation_blend: Path
    body_png: Path
    accent_png: Path
    shadow_png: Path


@dataclass(frozen=True)
class ToolPaths:
    blender: Path
    gltf_to_t3d: Path
    mksprite: Path


@dataclass(frozen=True)
class ExportConfig:
    root: Path
    build_id: str
    inputs: SourceInputs
    model_allowlist: tuple[AllowlistRow, ...]
    animation_allowlist: tuple[AllowlistRow, ...]
    candidate: bool
    replace: bool


CommandRunner = Callable[..., subprocess.CompletedProcess[bytes]]
Generator = Callable[[ExportConfig, Path], None]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_build_id(value: str) -> bool:
    if not BUILD_ID.fullmatch(value) or value == "-":
        return False
    parts = re.split(r"[._-]+", value.lower())

    def generic(component: str) -> bool:
        normalized = re.sub(r"[._-]+", "", component)
        return any(
            normalized == root or re.fullmatch(re.escape(root) + r"0*[0-9]+", normalized)
            for root in GENERIC_BUILD_PARTS
        )

    return not generic("".join(parts)) and not any(generic(part) for part in parts)


def safe_repo_path(value: str) -> bool:
    if not value or "\\" in value or "\x00" in value or value.startswith("/"):
        return False
    path = PurePosixPath(value)
    return (
        str(path) == value
        and len(path.parts) >= 2
        and all(part not in {"", ".", ".."} and SAFE_COMPONENT.fullmatch(part) for part in path.parts)
    )


def repo_path(root: Path, relative: str, label: str, *, must_exist: bool = True) -> Path:
    if not safe_repo_path(relative):
        raise Gate5ExportError(f"{label} is not a safe canonical repository path: {relative!r}")
    absolute_root = Path(os.path.abspath(root))
    current = absolute_root
    for component in PurePosixPath(relative).parts:
        current = current / component
        if current.is_symlink():
            raise Gate5ExportError(f"{label} traverses a symlink: {current}")
        if not current.exists():
            if must_exist:
                raise Gate5ExportError(f"{label} is missing: {current}")
            break
    if must_exist and (not current.is_file() or current.is_symlink()):
        raise Gate5ExportError(f"{label} is not one regular non-symlink file: {current}")
    return current


def canonical_text(path: Path, label: str) -> tuple[bytes, list[str]]:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        raise Gate5ExportError(f"{label} has a UTF-8 BOM")
    if b"\r" in data or not data.endswith(b"\n") or data.endswith(b"\n\n"):
        raise Gate5ExportError(f"{label} must use LF and exactly one final LF")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Gate5ExportError(f"{label} is not valid UTF-8") from exc
    lines = text[:-1].split("\n")
    if not lines or any(not line or line.startswith("#") for line in lines):
        raise Gate5ExportError(f"{label} contains blank/comment lines")
    return data, lines


class GitIndex:
    """Read-only index/LFS materialization checks used by production export."""

    def __init__(self, root: Path, run: CommandRunner = subprocess.run):
        self.root = root
        self.run = run

    def capture(self, args: Sequence[str]) -> bytes:
        completed = self.run(
            ["/usr/bin/git", "-c", "core.quotepath=false", *args],
            cwd=self.root,
            env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            detail = completed.stderr.decode("utf-8", "replace").strip()
            raise Gate5ExportError(f"git {' '.join(args)} failed: {detail}")
        return completed.stdout

    def index_blob(self, relative: str) -> tuple[str, bytes]:
        raw = self.capture(["ls-files", "--stage", "-z", "--", relative])
        records = [record for record in raw.split(b"\0") if record]
        if len(records) != 1:
            raise Gate5ExportError(f"source member is not exactly one tracked index entry: {relative}")
        metadata, separator, encoded_path = records[0].partition(b"\t")
        fields = metadata.decode("ascii", "strict").split(" ")
        if not separator or len(fields) != 3 or fields[2] != "0" or encoded_path.decode() != relative:
            raise Gate5ExportError(f"source member has a conflicted/noncanonical index entry: {relative}")
        mode = fields[0]
        if mode != "100644":
            raise Gate5ExportError(f"source member must be one ordinary mode-100644 blob: {relative}")
        return mode, self.capture(["show", f":{relative}"])

    def attributes(self, relative: str) -> dict[str, str]:
        raw = self.capture([
            "check-attr", "--cached", "-z", "filter", "diff", "merge", "text", "eol",
            "--", relative,
        ])
        fields = raw.split(b"\0")
        if fields and fields[-1] == b"":
            fields.pop()
        if len(fields) % 3:
            raise Gate5ExportError(f"git attributes response is malformed for {relative}")
        values: dict[str, str] = {}
        for index in range(0, len(fields), 3):
            path, name, value = (part.decode("utf-8", "strict") for part in fields[index:index + 3])
            if path != relative:
                raise Gate5ExportError(f"git attributes path mismatch for {relative}")
            values[name] = value
        return values

    def verify_member(self, entry: ManifestEntry, materialized: bytes) -> None:
        _mode, index_bytes = self.index_blob(entry.path)
        if Path(entry.path).suffix.lower() in BINARY_LFS_EXTENSIONS:
            attrs = self.attributes(entry.path)
            require_canonical_lfs(entry.path, materialized, index_bytes, attrs)
        elif index_bytes != materialized:
            raise Gate5ExportError(f"ordinary-Git source differs from its exact index bytes: {entry.path}")

    def verify_control_file(self, relative: str, materialized: bytes) -> None:
        _mode, index_bytes = self.index_blob(relative)
        if index_bytes != materialized:
            raise Gate5ExportError(f"Gate-5 control file differs from its exact index bytes: {relative}")

    def verify_output_attributes(self) -> None:
        for relative in (*MODEL_BINARY_ROLES, *ANIMATION_BINARY_ROLES):
            attrs = self.attributes(relative)
            if not all(attrs.get(name) == "lfs" for name in ("filter", "diff", "merge")) or attrs.get("text") != "unset":
                raise Gate5ExportError(f"binary Gate-5 output lacks canonical Git LFS attributes: {relative}")
        for relative in (RUNTIME_BINDING_PATH, SKELETON_BINDING_PATH):
            attrs = self.attributes(relative)
            if attrs.get("text") != "set" or attrs.get("eol") != "lf":
                raise Gate5ExportError(f"Gate-5 binding lacks canonical text/LF attributes: {relative}")


def require_canonical_lfs(
    relative: str, materialized: bytes, pointer: bytes, attributes: Mapping[str, str]
) -> None:
    if not all(attributes.get(name) == "lfs" for name in ("filter", "diff", "merge")):
        raise Gate5ExportError(f"binary source is not assigned to canonical Git LFS: {relative}")
    if attributes.get("text") != "unset":
        raise Gate5ExportError(f"binary source is not marked -text in Git attributes: {relative}")
    match = re.fullmatch(
        rb"version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize (0|[1-9][0-9]*)\n",
        pointer,
    )
    if not match:
        raise Gate5ExportError(f"binary source index blob is not one canonical Git LFS pointer: {relative}")
    expected_digest = match.group(1).decode("ascii")
    expected_size = int(match.group(2))
    if len(materialized) != expected_size or sha256_bytes(materialized) != expected_digest:
        raise Gate5ExportError(f"binary source does not materialize its exact Git LFS object: {relative}")


def parse_manifest(root: Path, relative: str, git: GitIndex) -> dict[str, ManifestEntry]:
    entries: dict[str, ManifestEntry] = {}
    visited: set[str] = set()
    owners: set[str] = set()

    def walk(manifest_relative: str, ancestors: tuple[str, ...]) -> None:
        if manifest_relative in ancestors:
            raise Gate5ExportError(f"source manifest cycle: {' -> '.join((*ancestors, manifest_relative))}")
        if manifest_relative in visited:
            raise Gate5ExportError(f"source manifest is owned more than once: {manifest_relative}")
        manifest_path = repo_path(root, manifest_relative, "source manifest")
        manifest_bytes, lines = canonical_text(manifest_path, manifest_relative)
        git.verify_member(
            ManifestEntry(manifest_relative, len(manifest_bytes), sha256_bytes(manifest_bytes), "-", "-", "source.manifest"),
            manifest_bytes,
        )
        member_paths: list[str] = []
        for index, line in enumerate(lines, 1):
            fields = line.split("\t")
            if len(fields) != 6:
                raise Gate5ExportError(f"{manifest_relative} line {index} must contain six TAB fields")
            path, count_text, digest, build_token, capture_token, role_token = fields
            if not safe_repo_path(path) or path == manifest_relative:
                raise Gate5ExportError(f"{manifest_relative} has unsafe/self member path: {path!r}")
            if not re.fullmatch(r"0|[1-9][0-9]*", count_text) or not HEX64.fullmatch(digest):
                raise Gate5ExportError(f"{manifest_relative} has malformed member identity: {path}")
            if not build_token.startswith("build:") or not capture_token.startswith("capture:") or not role_token.startswith("role:"):
                raise Gate5ExportError(f"{manifest_relative} has malformed member tokens: {path}")
            build, capture, role = build_token[6:], capture_token[8:], role_token[5:]
            if not re.fullmatch(r"-|[A-Za-z0-9][A-Za-z0-9._-]{0,95}", build):
                raise Gate5ExportError(f"{manifest_relative} has malformed build token: {path}")
            if not re.fullmatch(r"-|[A-Za-z0-9][A-Za-z0-9._-]{0,95}", capture):
                raise Gate5ExportError(f"{manifest_relative} has malformed capture token: {path}")
            if not re.fullmatch(r"[a-z][a-z0-9._-]{0,63}", role) or role in {"file", "misc"}:
                raise Gate5ExportError(f"{manifest_relative} has malformed role token: {path}")
            if path in owners or path.lower() in {prior.lower() for prior in owners}:
                raise Gate5ExportError(f"source manifest has duplicate/case-colliding member: {path}")
            member_path = repo_path(root, path, "source manifest member")
            materialized = member_path.read_bytes()
            if len(materialized) != int(count_text) or sha256_bytes(materialized) != digest:
                raise Gate5ExportError(f"source manifest digest/count mismatch: {path}")
            entry = ManifestEntry(path, int(count_text), digest, build, capture, role)
            git.verify_member(entry, materialized)
            entries[path] = entry
            owners.add(path)
            member_paths.append(path)
            if path.endswith("MANIFEST.sha256"):
                walk(path, (*ancestors, manifest_relative))
        if member_paths != sorted(member_paths) or len(member_paths) != len(set(member_paths)):
            raise Gate5ExportError(f"{manifest_relative} members are not unique raw-byte path sorted")
        visited.add(manifest_relative)

    walk(relative, ())
    return entries


def parse_allowlist(root: Path, scope: str) -> tuple[AllowlistRow, ...]:
    relative = f"review/{scope}/g1/SUBSET_EXPORT_ALLOWLIST.tsv"
    path = repo_path(root, relative, "subset export allowlist")
    _data, lines = canonical_text(path, relative)
    if tuple(lines[0].split("\t")) != SUBSET_HEADER:
        raise Gate5ExportError(f"{relative} header differs from the canonical seven fields")
    rows: list[AllowlistRow] = []
    for index, line in enumerate(lines[1:], 1):
        fields = line.split("\t")
        if len(fields) != len(SUBSET_HEADER):
            raise Gate5ExportError(f"{relative} row {index} must contain seven TAB fields")
        production_id, subset_digest, stage, member_path, member_digest, role, selectors_csv = fields
        selectors = tuple(selectors_csv.split(","))
        if production_id != scope or not HEX64.fullmatch(subset_digest):
            raise Gate5ExportError(f"{relative} row {index} has wrong production/subset identity")
        if stage not in {"SOURCE", "OUTPUT"} or not safe_repo_path(member_path) or not HEX64.fullmatch(member_digest):
            raise Gate5ExportError(f"{relative} row {index} has malformed stage/member identity")
        if (
            not selectors
            or any(not selector for selector in selectors)
            or tuple(sorted(selectors)) != selectors
            or len(set(selectors)) != len(selectors)
        ):
            raise Gate5ExportError(f"{relative} row {index} selectors are empty, unsorted, or duplicated")
        rows.append(AllowlistRow(production_id, subset_digest, stage, member_path, member_digest, role, selectors))
    expected_order = sorted(rows, key=lambda row: (0 if row.stage == "SOURCE" else 1, row.member_path))
    if rows != expected_order or len({(row.stage, row.member_path) for row in rows}) != len(rows):
        raise Gate5ExportError(f"{relative} rows are not unique SOURCE-then-OUTPUT/path sorted")
    if len({row.subset_sha256 for row in rows}) != 1:
        raise Gate5ExportError(f"{relative} rows do not share one subset digest")
    return tuple(rows)


def validate_allowlist_sources(
    scope: str, rows: Sequence[AllowlistRow], manifest: Mapping[str, ManifestEntry]
) -> None:
    source_rows = [row for row in rows if row.stage == "SOURCE"]
    if {row.member_path for row in source_rows} != set(manifest):
        raise Gate5ExportError(f"{scope} allowlist SOURCE rows differ from source-manifest closure")
    observed: set[str] = set()
    expected = set(MODEL_SELECTORS if scope == MODEL_SCOPE else ANIMATION_SELECTORS)
    transformations = f"assets-src/{scope.split('.', 1)[0]}/{scope}/TRANSFORMATIONS.md"
    for row in source_rows:
        entry = manifest[row.member_path]
        if row.member_sha256 != entry.digest or row.manifest_role != entry.role:
            raise Gate5ExportError(f"{scope} allowlist digest/role mismatch: {row.member_path}")
        expected_special: tuple[str, ...] | None = None
        if row.member_path == transformations:
            expected_special = ("METADATA:transformations",)
        elif entry.role == "rights.record":
            expected_special = ("METADATA:rights",)
        elif entry.role == "rights.support":
            expected_special = ("METADATA:rights_support",)
        elif entry.role == "generation.record":
            expected_special = ("METADATA:generation",)
        elif entry.role == "source.manifest":
            # Nested manifests are metadata containers, never exportable content.
            expected_special = ("METADATA:transformations",)
        if expected_special is not None:
            if row.selectors != expected_special:
                raise Gate5ExportError(f"{scope} metadata selector mismatch: {row.member_path}")
            continue
        extras = set(row.selectors) - expected
        if extras or "ALL" in row.selectors:
            raise Gate5ExportError(f"{scope} source row widens the frozen selector set: {row.member_path}")
        observed.update(row.selectors)
    if observed != expected:
        raise Gate5ExportError(f"{scope} content selector union differs from the frozen policy")


def select_inputs(
    root: Path,
    model_rows: Sequence[AllowlistRow],
    animation_rows: Sequence[AllowlistRow],
    model_manifest: Mapping[str, ManifestEntry],
    animation_manifest: Mapping[str, ManifestEntry],
) -> SourceInputs:
    def content(rows: Sequence[AllowlistRow]) -> list[AllowlistRow]:
        return [row for row in rows if row.stage == "SOURCE" and any(value.startswith(("ASSET:", "CLIP:")) for value in row.selectors)]

    model_content = content(model_rows)
    animation_content = content(animation_rows)
    model_blends = [
        row for row in model_content
        if Path(row.member_path).suffix.lower() == ".blend" and row.selectors == (
            "ASSET:distance_model", "ASSET:hero_model", "ASSET:rig"
        )
    ]
    animation_blends = [
        row for row in animation_content
        if Path(row.member_path).suffix.lower() == ".blend" and row.selectors == ANIMATION_SELECTORS
    ]
    png_by_name = {
        Path(row.member_path).name: row for row in model_content if Path(row.member_path).suffix.lower() == ".png"
    }
    if len(model_blends) != 1 or len(animation_blends) != 1:
        raise Gate5ExportError("Quarrune requires one exact model/rig .blend and one exact nine-clip .blend")
    expected_pngs = set(SOURCE_FILENAMES.values())
    if set(png_by_name) != expected_pngs:
        raise Gate5ExportError("Quarrune requires exactly the three canonical source PNG basenames")
    if png_by_name[SOURCE_FILENAMES["shadow"]].selectors != ("ASSET:blob_shadow",):
        raise Gate5ExportError("blob-shadow PNG must own only ASSET:blob_shadow")
    for name in (SOURCE_FILENAMES["body"], SOURCE_FILENAMES["accent"]):
        if png_by_name[name].selectors != ("ASSET:texture",):
            raise Gate5ExportError(f"{name} must own only ASSET:texture")
    selected_model = {row.member_path for row in model_blends} | {row.member_path for row in png_by_name.values()}
    if {row.member_path for row in model_content} != selected_model:
        raise Gate5ExportError("echo.quarrune has unrecognized exportable content rows")
    if {row.member_path for row in animation_content} != {animation_blends[0].member_path}:
        raise Gate5ExportError("anm.echo.quarrune has unrecognized exportable content rows")
    for row in (*model_content, *animation_content):
        source = model_manifest.get(row.member_path) or animation_manifest.get(row.member_path)
        if source is None or source.role not in {"source.authored", "source.generated"}:
            raise Gate5ExportError(f"exportable content must use source.authored/source.generated: {row.member_path}")
    return SourceInputs(
        model_blend=repo_path(root, model_blends[0].member_path, "model Blender source"),
        animation_blend=repo_path(root, animation_blends[0].member_path, "animation Blender source"),
        body_png=repo_path(root, png_by_name[SOURCE_FILENAMES["body"]].member_path, "body PNG"),
        accent_png=repo_path(root, png_by_name[SOURCE_FILENAMES["accent"]].member_path, "accent PNG"),
        shadow_png=repo_path(root, png_by_name[SOURCE_FILENAMES["shadow"]].member_path, "shadow PNG"),
    )


def validate_output_allowlists(
    model_rows: Sequence[AllowlistRow],
    animation_rows: Sequence[AllowlistRow],
    staged_entries: Mapping[str, ManifestEntry],
    *,
    candidate: bool,
) -> None:
    model_output_rows = [row for row in model_rows if row.stage == "OUTPUT"]
    animation_output_rows = [row for row in animation_rows if row.stage == "OUTPUT"]
    output_rows = [*model_output_rows, *animation_output_rows]
    if candidate:
        if output_rows:
            raise Gate5ExportError("--candidate requires source-only allowlists; partial/final OUTPUT authority is forbidden")
        return
    if len(output_rows) != len(MANAGED_OUTPUT_PATHS) or {
        row.member_path for row in output_rows
    } != set(MANAGED_OUTPUT_PATHS):
        raise Gate5ExportError("final Gate-5 export requires exact OUTPUT rows for every paired package member")
    owner_partitions = (
        (MODEL_SCOPE, model_output_rows, set(MODEL_ROLES)),
        (ANIMATION_SCOPE, animation_output_rows, set(ANIMATION_ROLES)),
    )
    for scope, rows, expected_paths in owner_partitions:
        if (
            len(rows) != len(expected_paths)
            or {row.member_path for row in rows} != expected_paths
            or any(row.production_id != scope for row in rows)
        ):
            raise Gate5ExportError("final Gate-5 OUTPUT rows violate the exact model/animation owner partition")
    for row in output_rows:
        entry = staged_entries[row.member_path]
        if row.selectors != ("OUTPUT:runtime",):
            raise Gate5ExportError(f"Gate-5 OUTPUT selector mismatch: {row.member_path}")
        if row.member_sha256 != entry.digest or row.manifest_role != entry.role:
            raise Gate5ExportError(f"regenerated output differs from reviewed allowlist binding: {row.member_path}")


def require_tool(path: Path, label: str) -> None:
    if not path.is_file() or path.is_symlink() or not os.access(path, os.X_OK):
        raise Gate5ExportError(f"{label} is missing, symlinked, non-regular, or non-executable: {path}")


def resolve_tools(root: Path) -> ToolPaths:
    lock_path = repo_path(root, "config/toolchain.lock.json", "toolchain lock")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    blender_pin = lock["authoring"]["blender_macos_arm64"]
    override = os.environ.get("N64GAME_BLENDER_BINARY")
    if override:
        blender = Path(os.path.abspath(override))
    else:
        home = os.environ.get("HOME")
        if not home:
            raise Gate5ExportError("HOME is absent; cannot resolve the exact Blender application")
        blender = Path(home) / blender_pin["macos_user_relative_path"]
    require_tool(blender, "pinned Blender executable")
    if sha256_file(blender) != blender_pin["executable_sha256"]:
        raise Gate5ExportError("Blender executable differs from the toolchain lock")
    n64_inst = os.environ.get("N64_INST")
    if not n64_inst:
        raise Gate5ExportError("N64_INST is required for the pinned Tiny3D/libdragon tools")
    gltf_to_t3d = Path(n64_inst) / "bin" / "gltf_to_t3d"
    mksprite = Path(n64_inst) / "bin" / "mksprite"
    require_tool(gltf_to_t3d, "gltf_to_t3d")
    require_tool(mksprite, "mksprite")
    for submodule, expected in (("vendor/tiny3d", lock["tiny3d"]["commit"]), ("vendor/libdragon", lock["libdragon"]["commit"])):
        completed = subprocess.run(
            ["/usr/bin/git", "-C", str(root / submodule), "rev-parse", "HEAD"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"},
        )
        if completed.returncode != 0 or completed.stdout.decode().strip() != expected:
            raise Gate5ExportError(f"{submodule} does not resolve to its exact pinned commit")
        status = subprocess.run(
            ["/usr/bin/git", "-C", str(root / submodule), "status", "--porcelain", "--untracked-files=all"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"},
        )
        if status.returncode != 0 or status.stdout:
            raise Gate5ExportError(f"{submodule} is dirty or its exact source tree cannot be verified")
    return ToolPaths(blender, gltf_to_t3d, mksprite)


def tool_fingerprint(tools: ToolPaths) -> tuple[tuple[str, int, str], ...]:
    values: list[tuple[str, int, str]] = []
    for path in (tools.blender, tools.gltf_to_t3d, tools.mksprite):
        require_tool(path, "Gate-5 tool")
        values.append((str(path), path.stat().st_size, sha256_file(path)))
    return tuple(values)


BLENDER_DRIVER = r'''import bpy
import pathlib
import sys

EXPECTED_ACTIONS = [
    "brace_relay", "entrance", "hit", "horizon_break", "idle_a", "idle_b",
    "knockout", "reposition", "ridge_ram",
]

def fail(message):
    raise RuntimeError("N64GAME_GATE5: " + message)

def recursive_objects(collection):
    values = set(collection.objects)
    for child in collection.children:
        values.update(recursive_objects(child))
    return values

def select_collections(names):
    bpy.ops.object.select_all(action="DESELECT")
    selected = set()
    for name in names:
        collection = bpy.data.collections.get(name)
        if collection is None:
            fail("missing exact collection " + name)
        selected.update(recursive_objects(collection))
    if not selected:
        fail("selected collections contain no objects")
    for obj in selected:
        obj.hide_set(False)
        obj.hide_viewport = False
        obj.hide_render = False
        obj.select_set(True)
    armatures = [obj for obj in selected if obj.type == "ARMATURE"]
    if len(armatures) != 1:
        fail("selection must contain exactly one armature")
    bpy.context.view_layer.objects.active = armatures[0]

def export(path, animations):
    result = bpy.ops.export_scene.gltf(
        filepath=str(path), check_existing=False, export_format="GLB", use_selection=True,
        export_extras=True, export_animations=animations, export_animation_mode="ACTIONS",
        export_merge_animation="ACTION", export_action_filter=False, export_nla_strips=False,
        export_frame_range=True, export_frame_step=1, export_force_sampling=True,
        export_bake_animation=True, export_skins=True, export_def_bones=False,
        export_all_influences=False, export_influence_nb=4, export_morph=False,
        export_cameras=False, export_lights=False, export_materials="EXPORT",
        export_image_format="NONE", export_texcoords=True, export_normals=True,
        export_tangents=False, export_vertex_color="MATERIAL", export_yup=True,
        export_apply=False, export_shared_accessors=False, export_try_sparse_sk=False,
        export_try_omit_sparse_sk=False, export_draco_mesh_compression_enable=False,
        export_use_gltfpack=False, will_save_settings=False,
    )
    if "FINISHED" not in result or not pathlib.Path(path).is_file():
        fail("glTF export did not produce one GLB")

args = sys.argv[sys.argv.index("--") + 1:]
mode = args[0]
if mode == "model" and len(args) == 3:
    if bpy.data.actions:
        for action in list(bpy.data.actions):
            bpy.data.actions.remove(action)
    select_collections(["hero_model", "rig"])
    export(args[1], False)
    select_collections(["distance_model", "rig"])
    export(args[2], False)
elif mode == "animation" and len(args) == 2:
    names = [action.name for action in bpy.data.actions]
    if any(name not in names for name in EXPECTED_ACTIONS) or len(set(names)) != len(names):
        fail("one or more exact authorized actions are missing or duplicated")
    for action in list(bpy.data.actions):
        if action.name not in EXPECTED_ACTIONS:
            bpy.data.actions.remove(action)
    select_collections(["rig"])
    export(args[1], True)
else:
    fail("invalid driver mode/arguments")
'''


def tool_commands(tools: ToolPaths, config: ExportConfig, stage: Path, driver: Path) -> tuple[tuple[str, ...], ...]:
    intermediate = stage / "intermediate"
    filesystem = stage / "filesystem"
    hero_glb = intermediate / "quarrune_hero.glb"
    distance_glb = intermediate / "quarrune_distance.glb"
    animation_glb = intermediate / "anm_echo_quarrune.glb"
    hero_t3dm = filesystem / "echo/echo.quarrune/quarrune_hero.t3dm"
    distance_t3dm = filesystem / "echo/echo.quarrune/quarrune_distance.t3dm"
    animation_t3dm = filesystem / "anm/anm.echo.quarrune/anm_echo_quarrune.t3dm"
    model_blender = (
        str(tools.blender), "--background", "--factory-startup", "--offline-mode",
        "--disable-autoexec", str(config.inputs.model_blend), "--python", str(driver), "--",
        "model", str(hero_glb), str(distance_glb),
    )
    animation_blender = (
        str(tools.blender), "--background", "--factory-startup", "--offline-mode",
        "--disable-autoexec", str(config.inputs.animation_blend), "--python", str(driver), "--",
        "animation", str(animation_glb),
    )
    converter_flags = ("--base-scale=64", "--asset-path=filesystem")
    sprite_root = filesystem / "echo/echo.quarrune"
    return (
        model_blender,
        animation_blender,
        (str(tools.gltf_to_t3d), str(hero_glb), str(hero_t3dm), *converter_flags),
        (str(tools.gltf_to_t3d), str(distance_glb), str(distance_t3dm), *converter_flags),
        (str(tools.gltf_to_t3d), str(animation_glb), str(animation_t3dm), *converter_flags),
        (str(tools.mksprite), "--format", "CI8", "--tiles", "64,64", "--mipmap", "NONE", "--dither", "NONE", "--compress", "0", "-o", str(sprite_root), str(config.inputs.body_png)),
        (str(tools.mksprite), "--format", "CI4", "--tiles", "32,32", "--mipmap", "NONE", "--dither", "NONE", "--compress", "0", "-o", str(sprite_root), str(config.inputs.accent_png)),
        (str(tools.mksprite), "--format", "IA8", "--tiles", "32,32", "--mipmap", "NONE", "--dither", "NONE", "--compress", "0", "-o", str(sprite_root), str(config.inputs.shadow_png)),
    )


def canonicalize_glb(path: Path, *, expected_animations: Sequence[str] | None) -> None:
    data = path.read_bytes()
    if len(data) < 20 or data[:4] != b"glTF" or struct.unpack_from("<I", data, 4)[0] != 2:
        raise Gate5ExportError(f"Blender output is not one GLB v2 file: {path}")
    declared = struct.unpack_from("<I", data, 8)[0]
    if declared != len(data):
        raise Gate5ExportError(f"GLB declared length mismatch: {path}")
    offset = 12
    chunks: list[tuple[int, bytes]] = []
    while offset < len(data):
        if offset + 8 > len(data):
            raise Gate5ExportError(f"GLB has a truncated chunk header: {path}")
        length, kind = struct.unpack_from("<II", data, offset)
        offset += 8
        if offset + length > len(data):
            raise Gate5ExportError(f"GLB has a truncated chunk: {path}")
        chunks.append((kind, data[offset:offset + length]))
        offset += length
    if not chunks or chunks[0][0] != 0x4E4F534A:
        raise Gate5ExportError(f"GLB lacks a leading JSON chunk: {path}")
    try:
        document = json.loads(chunks[0][1].rstrip(b" \t\r\n\0"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Gate5ExportError(f"GLB JSON chunk is malformed: {path}") from exc
    animations = document.get("animations", [])
    names = [value.get("name") for value in animations if isinstance(value, dict)]
    if expected_animations is None:
        if animations:
            raise Gate5ExportError(f"model GLB unexpectedly contains animation data: {path}")
    else:
        if sorted(names) != sorted(expected_animations) or len(names) != len(expected_animations):
            raise Gate5ExportError(f"animation GLB differs from the exact authorized clip set: {path}")
        by_name = {value["name"]: value for value in animations}
        document["animations"] = [by_name[name] for name in expected_animations]
    json_bytes = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    json_bytes += b" " * ((-len(json_bytes)) % 4)
    chunks[0] = (0x4E4F534A, json_bytes)
    output = bytearray(b"glTF" + struct.pack("<II", 2, 0))
    for kind, payload in chunks:
        output.extend(struct.pack("<II", len(payload), kind))
        output.extend(payload)
    struct.pack_into("<I", output, 8, len(output))
    path.write_bytes(output)


def run_tool(command: Sequence[str], *, root: Path, run: CommandRunner) -> None:
    environment = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "TZ": "UTC",
    }
    for name in ("HOME", "TMPDIR", "N64_INST"):
        if os.environ.get(name):
            environment[name] = os.environ[name]
    completed = run(
        list(command), cwd=root, env=environment, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=False,
    )
    if completed.returncode != 0:
        output = completed.stdout.decode("utf-8", "replace")[-4000:]
        raise Gate5ExportError(f"tool exited {completed.returncode}: {command[0]}\n{output}")


RUBY_FINALIZE = r'''
require "base64"
require "json"
require "n64game/tiny3d_package_contract"
c = N64Game::Tiny3DPackageContract
payload = JSON.parse(STDIN.read)
model = payload.fetch("model_entries").map { |entry| entry.transform_keys(&:to_sym) }
animation = payload.fetch("animation_entries").map { |entry| entry.transform_keys(&:to_sym) }
bytes = payload.fetch("bytes").transform_values { |value| Base64.strict_decode64(value).b }
build = payload.fetch("build_id")
models = c::MODEL_PATHS.map { |path| c.decode_model(bytes.fetch(path), path) }
streams = c::ANIMATION_STREAM_PATHS.to_h { |path| [path, bytes.fetch(path)] }
decoded_animation = c.decode_animation(bytes.fetch(c::ANIMATION_HEADER_PATH), streams, c::ANIMATION_HEADER_PATH)
signatures = models.map { |value| value.fetch(:skeleton_signature) } + [decoded_animation.fetch(:skeleton_signature)]
raise "skeleton signatures differ before binding" unless signatures.uniq.length == 1
runtime_values = c.expected_runtime_binding(model, build)
runtime = c::RUNTIME_BINDING_KEYS.map { |key| "#{key}\t#{runtime_values.fetch(key)}\n" }.join.b
model << {
  path: c::RUNTIME_BINDING_PATH, role: c::RUNTIME_BINDING_ROLE,
  digest: Digest::SHA256.hexdigest(runtime), count: runtime.bytesize, build: build,
  capture: "-", kind: "git", mode: "100644"
}
binding_values = c.expected_binding(model, animation, signatures.first, build)
binding = c::BINDING_KEYS.map { |key| "#{key}\t#{binding_values.fetch(key)}\n" }.join.b
animation << {
  path: c::SKELETON_BINDING_PATH, role: c::SKELETON_BINDING_ROLE,
  digest: Digest::SHA256.hexdigest(binding), count: binding.bytesize, build: build,
  capture: "-", kind: "git", mode: "100644"
}
bytes[c::RUNTIME_BINDING_PATH] = runtime
bytes[c::SKELETON_BINDING_PATH] = binding
issues = c.validate_pair(
  model_entries: model, animation_entries: animation, bytes_by_path: bytes,
  model_build_id: build, animation_build_id: build
)
STDOUT.write(JSON.generate({
  runtime_binding: Base64.strict_encode64(runtime),
  skeleton_binding: Base64.strict_encode64(binding), issues: issues
}))
'''

RUBY_VALIDATE = r'''
require "base64"
require "json"
require "n64game/tiny3d_package_contract"
payload = JSON.parse(STDIN.read)
symbolize = ->(entry) { entry.transform_keys(&:to_sym) }
issues = N64Game::Tiny3DPackageContract.validate_pair(
  model_entries: payload.fetch("model_entries").map(&symbolize),
  animation_entries: payload.fetch("animation_entries").map(&symbolize),
  bytes_by_path: payload.fetch("bytes").transform_values { |value| Base64.strict_decode64(value).b },
  model_build_id: payload.fetch("build_id"), animation_build_id: payload.fetch("build_id")
)
STDOUT.write(JSON.generate(issues))
'''


def ruby_call(root: Path, program: str, payload: Mapping[str, object]) -> object:
    completed = subprocess.run(
        ["/usr/bin/ruby", "-I", str(root / "lib"), "-e", program],
        cwd=root,
        input=json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace")[-4000:]
        raise Gate5ExportError(f"Quarrune package reader failed closed: {detail}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise Gate5ExportError("Quarrune package reader returned malformed JSON") from exc


def binary_entries(stage: Path, roles: Mapping[str, str], build_id: str) -> list[ManifestEntry]:
    entries: list[ManifestEntry] = []
    for relative, role in sorted(roles.items()):
        path = repo_path(stage, relative, "staged Gate-5 binary")
        data = path.read_bytes()
        entries.append(ManifestEntry(relative, len(data), sha256_bytes(data), build_id, "-", role, "lfs"))
    return entries


def render_manifest(entries: Sequence[ManifestEntry]) -> bytes:
    ordered = sorted(entries, key=lambda entry: entry.path)
    if len({entry.path for entry in ordered}) != len(ordered):
        raise Gate5ExportError("output manifest entries are duplicated")
    return "".join(
        f"{entry.path}\t{entry.count}\t{entry.digest}\tbuild:{entry.build}\t"
        f"capture:{entry.capture}\trole:{entry.role}\n"
        for entry in ordered
    ).encode("utf-8")


def parse_output_manifest(stage: Path, relative: str, roles: Mapping[str, str], build_id: str) -> list[ManifestEntry]:
    path = repo_path(stage, relative, "staged output manifest")
    _bytes, lines = canonical_text(path, relative)
    entries: list[ManifestEntry] = []
    for line in lines:
        fields = line.split("\t")
        if len(fields) != 6:
            raise Gate5ExportError(f"{relative} row does not have six TAB fields")
        member, count, digest, build, capture, role = fields
        expected_role = roles.get(member)
        if (
            expected_role is None or not re.fullmatch(r"0|[1-9][0-9]*", count)
            or not HEX64.fullmatch(digest) or build != f"build:{build_id}"
            or capture != "capture:-" or role != f"role:{expected_role}"
        ):
            raise Gate5ExportError(f"{relative} row differs from canonical package identity: {member}")
        materialized = repo_path(stage, member, "staged output member").read_bytes()
        if len(materialized) != int(count) or sha256_bytes(materialized) != digest:
            raise Gate5ExportError(f"{relative} digest/count mismatch: {member}")
        kind = "git" if member in {RUNTIME_BINDING_PATH, SKELETON_BINDING_PATH} else "lfs"
        entries.append(ManifestEntry(member, int(count), digest, build_id, "-", expected_role, kind))
    if [entry.path for entry in entries] != sorted(roles) or len(entries) != len(roles):
        raise Gate5ExportError(f"{relative} member set/order differs from the exact package")
    return entries


def finalize_staging(stage: Path, build_id: str, root: Path) -> dict[str, ManifestEntry]:
    model = binary_entries(stage, MODEL_BINARY_ROLES, build_id)
    animation = binary_entries(stage, ANIMATION_BINARY_ROLES, build_id)
    raw_bytes = {
        entry.path: base64.b64encode(repo_path(stage, entry.path, "staged binary").read_bytes()).decode("ascii")
        for entry in (*model, *animation)
    }
    result = ruby_call(root, RUBY_FINALIZE, {
        "model_entries": [entry.ruby() for entry in model],
        "animation_entries": [entry.ruby() for entry in animation],
        "bytes": raw_bytes,
        "build_id": build_id,
    })
    if not isinstance(result, dict) or result.get("issues") != []:
        issues = result.get("issues") if isinstance(result, dict) else result
        raise Gate5ExportError(f"staged Quarrune pair failed semantic validation: {issues}")
    runtime = base64.b64decode(str(result["runtime_binding"]), validate=True)
    binding = base64.b64decode(str(result["skeleton_binding"]), validate=True)
    runtime_path = stage / RUNTIME_BINDING_PATH
    binding_path = stage / SKELETON_BINDING_PATH
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    binding_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_path.write_bytes(runtime)
    binding_path.write_bytes(binding)
    model.append(ManifestEntry(RUNTIME_BINDING_PATH, len(runtime), sha256_bytes(runtime), build_id, "-", MODEL_ROLES[RUNTIME_BINDING_PATH], "git"))
    animation.append(ManifestEntry(SKELETON_BINDING_PATH, len(binding), sha256_bytes(binding), build_id, "-", ANIMATION_ROLES[SKELETON_BINDING_PATH], "git"))
    model_manifest = stage / MODEL_MANIFEST_PATH
    animation_manifest = stage / ANIMATION_MANIFEST_PATH
    model_manifest.parent.mkdir(parents=True, exist_ok=True)
    animation_manifest.parent.mkdir(parents=True, exist_ok=True)
    model_manifest.write_bytes(render_manifest(model))
    animation_manifest.write_bytes(render_manifest(animation))
    validate_staged_pair(stage, build_id, root)
    return {entry.path: entry for entry in (*model, *animation)}


def validate_staged_pair(stage: Path, build_id: str, root: Path = ROOT) -> dict[str, ManifestEntry]:
    model = parse_output_manifest(stage, MODEL_MANIFEST_PATH, MODEL_ROLES, build_id)
    animation = parse_output_manifest(stage, ANIMATION_MANIFEST_PATH, ANIMATION_ROLES, build_id)
    all_entries = (*model, *animation)
    raw_bytes = {
        entry.path: base64.b64encode(repo_path(stage, entry.path, "staged package member").read_bytes()).decode("ascii")
        for entry in all_entries
    }
    issues = ruby_call(root, RUBY_VALIDATE, {
        "model_entries": [entry.ruby() for entry in model],
        "animation_entries": [entry.ruby() for entry in animation],
        "bytes": raw_bytes,
        "build_id": build_id,
    })
    if issues != []:
        raise Gate5ExportError(f"staged Quarrune pair failed semantic validation: {issues}")
    return {entry.path: entry for entry in all_entries}


def production_generate(
    config: ExportConfig,
    stage: Path,
    *,
    tools: ToolPaths | None = None,
    run: CommandRunner = subprocess.run,
) -> None:
    tools = tools or resolve_tools(config.root)
    intermediate = stage / "intermediate"
    filesystem_model = stage / "filesystem/echo/echo.quarrune"
    filesystem_animation = stage / "filesystem/anm/anm.echo.quarrune"
    intermediate.mkdir(parents=True)
    filesystem_model.mkdir(parents=True)
    filesystem_animation.mkdir(parents=True)
    driver = intermediate / "gate5_blender_driver.py"
    driver.write_bytes(BLENDER_DRIVER.encode("utf-8"))
    # Tiny3D resolves Fast64 texture names under filesystem/ and rewrites that
    # prefix to rom:/.  Source bytes are copied without image processing.
    for source in (config.inputs.body_png, config.inputs.accent_png, config.inputs.shadow_png):
        shutil.copyfile(source, filesystem_model / source.name)
    commands = tool_commands(tools, config, stage, driver)
    run_tool(commands[0], root=config.root, run=run)
    run_tool(commands[1], root=config.root, run=run)
    canonicalize_glb(intermediate / "quarrune_hero.glb", expected_animations=None)
    canonicalize_glb(intermediate / "quarrune_distance.glb", expected_animations=None)
    canonicalize_glb(intermediate / "anm_echo_quarrune.glb", expected_animations=ANIMATION_NAMES)
    for command in commands[2:]:
        run_tool(command, root=stage, run=run)
    source_to_review = {
        filesystem_model / "quarrune_hero.t3dm": HERO_MODEL_PATH,
        filesystem_model / "quarrune_distance.t3dm": DISTANCE_MODEL_PATH,
        filesystem_model / "tex_quarrune_body_ci8_64x64.sprite": BODY_TEXTURE_PATH,
        filesystem_model / "tex_quarrune_accent_ci4_32x32.sprite": ACCENT_TEXTURE_PATH,
        filesystem_model / "tex_quarrune_blob_shadow_ia8_32x32.sprite": BLOB_SHADOW_PATH,
        filesystem_animation / "anm_echo_quarrune.t3dm": ANIMATION_HEADER_PATH,
        **{
            filesystem_animation / f"anm_echo_quarrune.{index}.sdata": path
            for index, path in enumerate(ANIMATION_STREAM_PATHS)
        },
    }
    observed_streams = sorted(path.name for path in filesystem_animation.glob("*.sdata"))
    expected_streams = [f"anm_echo_quarrune.{index}.sdata" for index in range(9)]
    if observed_streams != expected_streams:
        raise Gate5ExportError("Tiny3D emitted a missing, extra, or differently ordered animation stream set")
    for source, relative in source_to_review.items():
        if not source.is_file() or source.is_symlink():
            raise Gate5ExportError(f"converter omitted canonical output: {source}")
        destination = stage / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    finalize_staging(stage, config.build_id, config.root)


def snapshot(stage: Path) -> dict[str, tuple[int, str]]:
    result: dict[str, tuple[int, str]] = {}
    for relative in MANAGED_PATHS:
        path = repo_path(stage, relative, "deterministic staged output")
        data = path.read_bytes()
        result[relative] = (len(data), sha256_bytes(data))
    return result


def validate_reviewed_snapshot(
    config: ExportConfig, stage: Path, expected: Mapping[str, ManifestEntry]
) -> None:
    if config.candidate:
        return
    for relative in MANAGED_PATHS:
        path = repo_path(config.root, relative, "reviewed Gate-5 snapshot")
        staged = expected.get(relative)
        if relative in {MODEL_MANIFEST_PATH, ANIMATION_MANIFEST_PATH}:
            expected_digest = sha256_file(repo_path(stage, relative, "regenerated output manifest"))
        elif staged is not None:
            expected_digest = staged.digest
        else:
            raise Gate5ExportError(f"internal expected snapshot is absent: {relative}")
        if sha256_file(path) != expected_digest:
            raise Gate5ExportError(f"reviewed snapshot differs from regenerated bytes: {relative}")


def source_fingerprint(config: ExportConfig) -> tuple[tuple[str, int, str], ...]:
    """Bind both runs to unchanged canonical source/control bytes."""
    paths = {
        config.inputs.model_blend,
        config.inputs.animation_blend,
        config.inputs.body_png,
        config.inputs.accent_png,
        config.inputs.shadow_png,
        config.root / f"assets-src/echo/{MODEL_SCOPE}/SOURCE_MANIFEST.sha256",
        config.root / f"assets-src/anm/{ANIMATION_SCOPE}/SOURCE_MANIFEST.sha256",
        config.root / f"review/{MODEL_SCOPE}/g1/SUBSET_EXPORT_ALLOWLIST.tsv",
        config.root / f"review/{ANIMATION_SCOPE}/g1/SUBSET_EXPORT_ALLOWLIST.tsv",
    }
    values: list[tuple[str, int, str]] = []
    for path in sorted(paths, key=lambda value: str(value)):
        if not path.is_file() or path.is_symlink():
            raise Gate5ExportError(f"source/control identity changed during export: {path}")
        data = path.read_bytes()
        values.append((str(path), len(data), sha256_bytes(data)))
    return tuple(values)


def preflight_destinations(root: Path, relatives: Iterable[str], *, replace: bool) -> None:
    for relative in relatives:
        destination = repo_path(root, relative, "Gate-5 destination", must_exist=False)
        current = root
        for component in PurePosixPath(relative).parts[:-1]:
            current = current / component
            if current.exists() and (current.is_symlink() or not current.is_dir()):
                raise Gate5ExportError(f"Gate-5 destination parent is unsafe: {current}")
        if destination.exists():
            if destination.is_symlink() or not destination.is_file():
                raise Gate5ExportError(f"Gate-5 destination is not one regular file: {destination}")
            if not replace:
                raise Gate5ExportError("Gate-5 outputs already exist; pass --replace only for an intentional rerun")


def promote_pair(
    stage: Path,
    root: Path,
    *,
    replace: bool,
    replace_func: Callable[[os.PathLike[str] | str, os.PathLike[str] | str], None] = os.replace,
) -> None:
    preflight_destinations(root, MANAGED_PATHS, replace=replace)
    prepared: dict[str, Path] = {}
    backups: dict[str, tuple[bytes, int] | None] = {}
    promoted: list[str] = []
    try:
        for relative in MANAGED_PATHS:
            source = repo_path(stage, relative, "staged promotion member")
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                backups[relative] = (destination.read_bytes(), stat.S_IMODE(destination.stat().st_mode))
            else:
                backups[relative] = None
            descriptor, temporary_name = tempfile.mkstemp(prefix=".gate5-pair-", dir=destination.parent)
            temporary = Path(temporary_name)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(source.read_bytes())
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary, 0o644)
            prepared[relative] = temporary
        for relative in MANAGED_PATHS:
            replace_func(prepared[relative], root / relative)
            promoted.append(relative)
            prepared.pop(relative, None)
    except BaseException as exc:
        rollback_errors: list[str] = []
        for relative in reversed(promoted):
            destination = root / relative
            backup = backups[relative]
            try:
                if backup is None:
                    destination.unlink(missing_ok=True)
                else:
                    descriptor, temporary_name = tempfile.mkstemp(prefix=".gate5-rollback-", dir=destination.parent)
                    temporary = Path(temporary_name)
                    with os.fdopen(descriptor, "wb") as handle:
                        handle.write(backup[0])
                        handle.flush()
                        os.fsync(handle.fileno())
                    os.chmod(temporary, backup[1])
                    replace_func(temporary, destination)
            except BaseException as rollback_exc:  # pragma: no cover - catastrophic host failure
                rollback_errors.append(f"{relative}: {rollback_exc}")
        detail = f"; rollback failures: {', '.join(rollback_errors)}" if rollback_errors else ""
        raise Gate5ExportError(f"paired Gate-5 promotion failed and was rolled back{detail}: {exc}") from exc
    finally:
        for temporary in prepared.values():
            temporary.unlink(missing_ok=True)


def export_pair(config: ExportConfig, *, generator: Generator | None = None) -> dict[str, tuple[int, str]]:
    tools: ToolPaths | None = None
    initial_tools: tuple[tuple[str, int, str], ...] | None = None
    if generator is None:
        tools = resolve_tools(config.root)
        initial_tools = tool_fingerprint(tools)
        generator = lambda value, stage: production_generate(value, stage, tools=tools)
    initial_source = source_fingerprint(config)
    with tempfile.TemporaryDirectory(prefix="n64game-gate5-pair-") as temporary:
        temp_root = Path(temporary)
        first = temp_root / "run-a"
        second = temp_root / "run-b"
        first.mkdir()
        second.mkdir()
        generator(config, first)
        if tools is not None and tool_fingerprint(tools) != initial_tools:
            raise Gate5ExportError("converter/tool identity changed during the first clean export")
        if source_fingerprint(config) != initial_source:
            raise Gate5ExportError("source/control identity changed during the first clean export")
        first_entries = validate_staged_pair(first, config.build_id, config.root)
        validate_output_allowlists(
            config.model_allowlist, config.animation_allowlist, first_entries, candidate=config.candidate
        )
        generator(config, second)
        if tools is not None and tool_fingerprint(tools) != initial_tools:
            raise Gate5ExportError("converter/tool identity changed during the second clean export")
        if source_fingerprint(config) != initial_source:
            raise Gate5ExportError("source/control identity changed during the second clean export")
        second_entries = validate_staged_pair(second, config.build_id, config.root)
        validate_output_allowlists(
            config.model_allowlist, config.animation_allowlist, second_entries, candidate=config.candidate
        )
        first_snapshot = snapshot(first)
        if first_snapshot != snapshot(second):
            raise Gate5ExportError("clean staged double export is nondeterministic")
        validate_reviewed_snapshot(config, first, first_entries)
        promote_pair(first, config.root, replace=config.replace)
        return first_snapshot


def build_config(args: argparse.Namespace, root: Path = ROOT) -> ExportConfig:
    if args.scope != MODEL_SCOPE or args.paired_scope != ANIMATION_SCOPE:
        raise Gate5ExportError(f"exporter accepts only {MODEL_SCOPE} paired with {ANIMATION_SCOPE}")
    if args.deterministic != 1:
        raise Gate5ExportError("--deterministic is mandatory exactly once")
    if not canonical_build_id(args.build_id):
        raise Gate5ExportError("--build-id must be one substantive canonical clean-build ID")
    if args.candidate and args.replace:
        raise Gate5ExportError("--candidate cannot replace an existing reviewed package")
    if not args.candidate and not args.replace:
        raise Gate5ExportError("final regeneration requires --replace after candidate review bindings exist")
    git = GitIndex(root)
    git.verify_output_attributes()
    model_manifest_path = f"assets-src/echo/{MODEL_SCOPE}/SOURCE_MANIFEST.sha256"
    animation_manifest_path = f"assets-src/anm/{ANIMATION_SCOPE}/SOURCE_MANIFEST.sha256"
    model_manifest = parse_manifest(root, model_manifest_path, git)
    animation_manifest = parse_manifest(root, animation_manifest_path, git)
    model_rows = parse_allowlist(root, MODEL_SCOPE)
    animation_rows = parse_allowlist(root, ANIMATION_SCOPE)
    for scope in (MODEL_SCOPE, ANIMATION_SCOPE):
        relative = f"review/{scope}/g1/SUBSET_EXPORT_ALLOWLIST.tsv"
        materialized = repo_path(root, relative, "subset export allowlist").read_bytes()
        git.verify_control_file(relative, materialized)
    validate_allowlist_sources(MODEL_SCOPE, model_rows, model_manifest)
    validate_allowlist_sources(ANIMATION_SCOPE, animation_rows, animation_manifest)
    inputs = select_inputs(root, model_rows, animation_rows, model_manifest, animation_manifest)
    return ExportConfig(
        root=root,
        build_id=args.build_id,
        inputs=inputs,
        model_allowlist=model_rows,
        animation_allowlist=animation_rows,
        candidate=args.candidate,
        replace=args.replace,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministically export the paired Quarrune Gate-5 package.")
    parser.add_argument("--scope", required=True)
    parser.add_argument("--paired-scope", required=True)
    parser.add_argument("--build-id", required=True)
    parser.add_argument("--deterministic", action="count", default=0)
    parser.add_argument("--candidate", action="store_true", help="materialize pre-approval review candidates from source-only allowlists")
    parser.add_argument("--replace", action="store_true", help="replace an existing exact pair after intentional re-export")
    args = parser.parse_args(argv)
    try:
        config = build_config(args)
        result = export_pair(config)
    except (Gate5ExportError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"gate5_export=FAIL {exc}", file=sys.stderr)
        return 1
    bundle = hashlib.sha256()
    for relative, (count, digest) in sorted(result.items()):
        bundle.update(f"{relative}\t{count}\t{digest}\n".encode("utf-8"))
    mode = "CANDIDATE" if config.candidate else "FINAL_REGENERATION_MATCH"
    print(f"gate5_export=PASS mode={mode} pair_sha256={bundle.hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
