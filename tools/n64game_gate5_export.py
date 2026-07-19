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
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
import platform
import re
import secrets
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
from dataclasses import dataclass, replace as dataclass_replace
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable, Iterator, Mapping, Sequence


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
INDEX_ATTRIBUTE_NAMES = ("filter", "diff", "merge", "text", "eol")

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

MODEL_OWNER_ROOT = "assets-src/echo/echo.quarrune"
ANIMATION_OWNER_ROOT = "assets-src/anm/anm.echo.quarrune"
MODEL_SOURCE_PATH = f"{MODEL_OWNER_ROOT}/quarrune.blend"
ANIMATION_SOURCE_PATH = f"{ANIMATION_OWNER_ROOT}/quarrune_actions.blend"
MODEL_PNG_PATHS = {
    key: f"{MODEL_OWNER_ROOT}/{filename}" for key, filename in SOURCE_FILENAMES.items()
}
MODEL_SOURCE_MANIFEST_PATH = f"{MODEL_OWNER_ROOT}/SOURCE_MANIFEST.sha256"
ANIMATION_SOURCE_MANIFEST_PATH = f"{ANIMATION_OWNER_ROOT}/SOURCE_MANIFEST.sha256"
AUTHORIZATION_BASIS = {MODEL_SCOPE: "WB-002", ANIMATION_SCOPE: "WB-039"}
PROFILE_TIER = {
    MODEL_SCOPE: ("RIGGED_MODEL", "H2"),
    ANIMATION_SCOPE: ("ANIMATION", "M7"),
}
AUTHORIZATION_KEYS = (
    "schema", "basis", "production_id", "subset_sha256", "subset_allowlist",
    "state", "repair_ids", "build_id", "source_manifest", "output_manifest",
    "gate_record", "authorizer_id", "authorized_at",
)
PROVENANCE_KEYS = (
    "schema", "production_id", "subset_sha256", "subset_allowlist", "creator_id",
    "rights_holder_id", "source_manifest", "output_manifest", "rights_basis",
    "rights_evidence", "transformations_sha256", "output_license",
)
GATE_RECORD_HEADER = (
    "scope_id", "profile", "tier", "gate", "decision", "reviewer_id",
    "reviewer_non_owner", "source_manifest_sha256", "output_manifest_sha256",
    "evidence_manifest_path", "evidence_manifest_sha256", "review_record_path",
    "review_record_sha256", "build_id", "decided_at", "defect_ids",
)
GATE_REVIEW_KEYS = (
    "schema", "scope_id", "gate", "decision", "reviewer_id",
    "reviewer_non_owner", "source_manifest_sha256", "output_manifest_sha256",
    "evidence_manifest", "build_id", "decided_at", "defect_ids", "disposition",
    "rationale",
)
AUTHORING_CHECKER_PATHS = (
    "lib/n64game/libdragon_sprite_contract.rb",
    "lib/n64game/tiny3d_package_contract.rb",
    "scripts/check-authoring-stack",
    "scripts/export-gate5-asset",
    "scripts/record-authoring-stack-receipt",
    "tools/n64game_authoring.py",
    "tools/n64game_authoring_receipt.py",
    "tools/n64game_gate5_export.py",
)
AUTHORING_RECEIPT_KEYS = (
    "schema", "scope_id", "gate", "source_manifest_sha256",
    "output_manifest_sha256", "build_id", "toolchain_lock_sha256",
    "checker_sha256", "blender_executable_sha256", "blender_seal",
    "fast64_source_manifest_sha256", "probe_mode", "result", "checked_at",
)
FIXED_AUTHORITY_MODES = {
    ".gitattributes": "100644",
    "config/toolchain.lock.json": "100644",
    "lib/n64game/authoring_stack_receipt.rb": "100644",
    "lib/n64game/libdragon_sprite_contract.rb": "100644",
    "lib/n64game/tiny3d_package_contract.rb": "100644",
    "scripts/check-authoring-stack": "100755",
    "scripts/export-gate5-asset": "100755",
    "scripts/record-authoring-stack-receipt": "100755",
    "src/quarrune_render_assets.c": "100644",
    "src/quarrune_render_assets.h": "100644",
    "tools/n64game_authoring.py": "100644",
    "tools/n64game_authoring_receipt.py": "100644",
    "tools/n64game_gate5_export.py": "100644",
}
FIXED_AUTHORITY_PATHS = tuple(FIXED_AUTHORITY_MODES)
GATE_EVIDENCE_REQUIREMENTS = {
    1: (
        frozenset({"concept.construction"}),
        frozenset({"concept.silhouette"}),
        frozenset({"concept.orthographic"}),
        frozenset({"concept.functional"}),
        frozenset({"concept.scale"}),
        frozenset({"concept.palette", "concept.material"}),
        frozenset({"concept.rig", "concept.movement"}),
        frozenset({"concept.clean_room", "concept.cleanroom"}),
    ),
    2: (
        frozenset({"technical.statistics"}),
        frozenset({"technical.topology", "technical.wireframe"}),
        frozenset({"technical.normals", "technical.face_orientation"}),
        frozenset({"technical.uv"}),
        frozenset({"technical.transform", "technical.origin"}),
        frozenset({"technical.naming"}),
        frozenset({"technical.weights"}),
        frozenset({"technical.deformation", "technical.stress"}),
        frozenset({"technical.validation"}),
    ),
    3: (
        frozenset({"turntable.contact_sheet", "turntable.sheet"}),
        frozenset({"turntable.neutral"}),
        frozenset({"turntable.game_light", "turntable.representative_light"}),
        frozenset({"turntable.native_crop"}),
        frozenset({"turntable.texture", "turntable.material_sheet"}),
        frozenset({"turntable.peer_comparison"}),
    ),
    4: (
        frozenset({"animation.reel", "animation.locked_camera"}),
        frozenset({"animation.event_table", "animation.clip_table"}),
        frozenset({"animation.contact_sheet", "animation.impact"}),
        frozenset({"animation.contact_overlay", "animation.foot_overlay"}),
        frozenset({"animation.deformation", "animation.stress"}),
        frozenset({"animation.transition"}),
        frozenset({"animation.sync"}),
    ),
}
JOURNAL_RELATIVE = "build/gate5/quarrune-pair-promotion.journal.json"

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
class AuthoritySealEntry:
    """Exact worktree, index-blob, mode, and cached-attribute validation result."""

    path: str
    materialized_count: int
    materialized_sha256: str
    index_mode: str
    index_oid: str
    index_blob: bytes
    cached_attributes: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class ExportConfig:
    root: Path
    build_id: str
    inputs: SourceInputs
    model_allowlist: tuple[AllowlistRow, ...]
    animation_allowlist: tuple[AllowlistRow, ...]
    candidate: bool
    replace: bool
    authority_paths: tuple[str, ...] = ()
    contract_root: Path | None = None
    authority_seal: tuple[AuthoritySealEntry, ...] = ()
    output_attribute_seal: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = ()


@dataclass(frozen=True)
class AuthoritySnapshot:
    """Immutable live-authority bytes captured while the transaction lock is held."""

    members: tuple[tuple[str, bytes], ...]

    def bytes_by_path(self) -> dict[str, bytes]:
        return dict(self.members)


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


def transaction_lock_path(root: Path) -> Path:
    identity = os.path.realpath(os.fspath(root))
    digest = hashlib.sha256(identity.encode("utf-8", "surrogateescape")).hexdigest()
    return Path(f"/tmp/n64game-gate5-{digest}.lock")


def validate_lock_fd(fd: int, path: Path) -> None:
    expected_parent = Path("/tmp")
    if path.parent != expected_parent or not re.fullmatch(r"n64game-gate5-[0-9a-f]{64}\.lock", path.name):
        raise Gate5ExportError("Gate-5 lock path is not the exact canonical /tmp pathname")
    tmp_fd = -1
    try:
        tmp_fd = os.open(
            os.path.realpath(expected_parent),
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0),
        )
        descriptor_stat = os.fstat(fd)
        path_stat = os.stat(path.name, dir_fd=tmp_fd, follow_symlinks=False)
    except OSError as exc:
        raise Gate5ExportError(f"Gate-5 lock descriptor/path validation failed: {exc}") from exc
    finally:
        if tmp_fd >= 0:
            os.close(tmp_fd)
    if (
        not stat.S_ISREG(descriptor_stat.st_mode)
        or not stat.S_ISREG(path_stat.st_mode)
        or descriptor_stat.st_dev != path_stat.st_dev
        or descriptor_stat.st_ino != path_stat.st_ino
        or descriptor_stat.st_uid != os.geteuid()
        or path_stat.st_uid != os.geteuid()
        or stat.S_IMODE(descriptor_stat.st_mode) != 0o600
        or stat.S_IMODE(path_stat.st_mode) != 0o600
        or descriptor_stat.st_nlink != 1
        or path_stat.st_nlink != 1
    ):
        raise Gate5ExportError("Gate-5 lock descriptor does not match the canonical owned mode-0600 regular lock file")


def validate_lock_boundary(root: Path, fd: int, label: str) -> None:
    try:
        validate_lock_fd(fd, transaction_lock_path(root))
    except Gate5ExportError as exc:
        raise Gate5ExportError(f"Gate-5 lock pathname changed at {label}: {exc}") from exc


@contextlib.contextmanager
def transaction_lock(root: Path) -> Iterator[int]:
    """Hold the exact per-real-repository flock, reusing a validated inherited fd."""
    lock_path = transaction_lock_path(root)
    inherited_text = os.environ.get("N64GAME_GATE5_LOCK_FD")
    inherited = inherited_text is not None
    if inherited:
        if not re.fullmatch(r"0|[1-9][0-9]*", inherited_text or ""):
            raise Gate5ExportError("N64GAME_GATE5_LOCK_FD is not one canonical decimal descriptor")
        fd = int(inherited_text)
    else:
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
        try:
            fd = os.open(lock_path, flags, 0o600)
        except OSError as exc:
            raise Gate5ExportError(f"cannot open canonical Gate-5 lock: {exc}") from exc
    try:
        validate_lock_fd(fd, lock_path)
        # On inherited descriptors this is idempotent because the descriptor is
        # the same open-file description; on an unlocked but otherwise valid fd
        # it safely acquires the missing lock.
        fcntl.flock(fd, fcntl.LOCK_EX)
        validate_lock_fd(fd, lock_path)
        yield fd
    finally:
        active_exception = sys.exc_info()[0] is not None
        release_error: BaseException | None = None
        try:
            validate_lock_fd(fd, lock_path)
        except BaseException as exc:  # preserve cleanup while failing closed
            release_error = exc
        if not inherited:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)
        if release_error is not None and not active_exception:
            raise release_error


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
    return canonical_text_bytes(path.read_bytes(), label)


def canonical_text_bytes(data: bytes, label: str) -> tuple[bytes, list[str]]:
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
        self.validated_identities: dict[str, AuthoritySealEntry] = {}
        self.validated_control_bytes: dict[str, bytes] = {}
        self.validated_output_attributes: dict[str, tuple[tuple[str, str], ...]] = {}

    def record_validated_identity(
        self,
        relative: str,
        materialized: bytes,
        *,
        index_mode: str,
        index_oid: str,
        index_blob: bytes,
        attributes: Mapping[str, str],
    ) -> None:
        identity = AuthoritySealEntry(
            path=relative,
            materialized_count=len(materialized),
            materialized_sha256=sha256_bytes(materialized),
            index_mode=index_mode,
            index_oid=index_oid,
            index_blob=index_blob,
            cached_attributes=tuple((name, attributes[name]) for name in INDEX_ATTRIBUTE_NAMES),
        )
        prior = self.validated_identities.get(relative)
        if prior is not None and prior != identity:
            raise Gate5ExportError(f"validated authority changed identity during configuration: {relative}")
        self.validated_identities[relative] = identity

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

    def index_blob(
        self, relative: str, expected_modes: Sequence[str] = ("100644",)
    ) -> tuple[str, str, bytes]:
        raw = self.capture(["ls-files", "--stage", "-z", "--", relative])
        records = [record for record in raw.split(b"\0") if record]
        if len(records) != 1:
            raise Gate5ExportError(f"source member is not exactly one tracked index entry: {relative}")
        metadata, separator, encoded_path = records[0].partition(b"\t")
        fields = metadata.decode("ascii", "strict").split(" ")
        if not separator or len(fields) != 3 or fields[2] != "0" or encoded_path.decode() != relative:
            raise Gate5ExportError(f"source member has a conflicted/noncanonical index entry: {relative}")
        mode = fields[0]
        oid = fields[1]
        if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", oid):
            raise Gate5ExportError(f"source member has a malformed index blob identity: {relative}")
        if mode not in expected_modes:
            modes = "/".join(expected_modes)
            raise Gate5ExportError(
                f"source member must be one ordinary mode-{modes} blob: {relative}"
            )
        return mode, oid, self.capture(["show", f":{relative}"])

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
        if set(values) != set(INDEX_ATTRIBUTE_NAMES):
            raise Gate5ExportError(f"git attributes response lacks the exact cached fields for {relative}")
        return values

    def verify_member(self, entry: ManifestEntry, materialized: bytes) -> None:
        mode, oid, index_bytes = self.index_blob(entry.path)
        attrs = self.attributes(entry.path)
        if Path(entry.path).suffix.lower() in BINARY_LFS_EXTENSIONS:
            require_canonical_lfs(entry.path, materialized, index_bytes, attrs)
        elif index_bytes != materialized:
            raise Gate5ExportError(f"ordinary-Git source differs from its exact index bytes: {entry.path}")
        self.record_validated_identity(
            entry.path,
            materialized,
            index_mode=mode,
            index_oid=oid,
            index_blob=index_bytes,
            attributes=attrs,
        )

    def verify_control_file(
        self, relative: str, materialized: bytes, expected_mode: str = "100644"
    ) -> None:
        mode, oid, index_bytes = self.index_blob(relative, (expected_mode,))
        attrs = self.attributes(relative)
        if index_bytes != materialized:
            raise Gate5ExportError(f"Gate-5 control file differs from its exact index bytes: {relative}")
        self.record_validated_identity(
            relative,
            materialized,
            index_mode=mode,
            index_oid=oid,
            index_blob=index_bytes,
            attributes=attrs,
        )
        prior = self.validated_control_bytes.get(relative)
        if prior is not None and prior != materialized:
            raise Gate5ExportError(f"validated control bytes changed during configuration: {relative}")
        self.validated_control_bytes[relative] = materialized

    def validated_materialized_sha256(self, relative: str) -> str:
        identity = self.validated_identities.get(relative)
        if identity is None:
            raise Gate5ExportError(f"authority byte was not validated before semantic use: {relative}")
        return identity.materialized_sha256

    def control_bytes(self, relative: str) -> bytes | None:
        return self.validated_control_bytes.get(relative)

    def validated_seal(self, relatives: Sequence[str]) -> tuple[AuthoritySealEntry, ...]:
        seal: list[AuthoritySealEntry] = []
        for relative in sorted(relatives):
            identity = self.validated_identities.get(relative)
            if identity is None:
                raise Gate5ExportError(f"authority byte was not bound by build_config validation: {relative}")
            seal.append(identity)
        return tuple(seal)

    def verify_output_attributes(self) -> None:
        for relative in (*MODEL_BINARY_ROLES, *ANIMATION_BINARY_ROLES):
            attrs = self.attributes(relative)
            if not all(attrs.get(name) == "lfs" for name in ("filter", "diff", "merge")) or attrs.get("text") != "unset":
                raise Gate5ExportError(f"binary Gate-5 output lacks canonical Git LFS attributes: {relative}")
            self.validated_output_attributes[relative] = tuple(
                (name, attrs[name]) for name in INDEX_ATTRIBUTE_NAMES
            )
        for relative in (RUNTIME_BINDING_PATH, SKELETON_BINDING_PATH):
            attrs = self.attributes(relative)
            if attrs.get("text") != "set" or attrs.get("eol") != "lf":
                raise Gate5ExportError(f"Gate-5 binding lacks canonical text/LF attributes: {relative}")
            self.validated_output_attributes[relative] = tuple(
                (name, attrs[name]) for name in INDEX_ATTRIBUTE_NAMES
            )

    def output_attribute_seal(self) -> tuple[tuple[str, tuple[tuple[str, str], ...]], ...]:
        return tuple(sorted(self.validated_output_attributes.items()))


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


def parse_manifest(
    root: Path,
    relative: str,
    git: GitIndex,
    *,
    expected_root_bytes: bytes | None = None,
) -> dict[str, ManifestEntry]:
    entries: dict[str, ManifestEntry] = {}
    visited: set[str] = set()
    owners: set[str] = set()

    def walk(manifest_relative: str, ancestors: tuple[str, ...]) -> None:
        if manifest_relative in ancestors:
            raise Gate5ExportError(f"source manifest cycle: {' -> '.join((*ancestors, manifest_relative))}")
        if manifest_relative in visited:
            raise Gate5ExportError(f"source manifest is owned more than once: {manifest_relative}")
        manifest_path = repo_path(root, manifest_relative, "source manifest")
        if manifest_relative == relative and expected_root_bytes is not None:
            manifest_bytes = expected_root_bytes
            _checked_bytes, lines = canonical_text_bytes(manifest_bytes, manifest_relative)
        else:
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


def parse_allowlist(root: Path, scope: str, git: GitIndex) -> tuple[AllowlistRow, ...]:
    relative = f"review/{scope}/g1/SUBSET_EXPORT_ALLOWLIST.tsv"
    path = repo_path(root, relative, "subset export allowlist")
    data, lines = canonical_text(path, relative)
    # Bind the exact bytes that produced these in-memory rows.  A later reread
    # of this path must match this recorded worktree/index identity.
    git.verify_control_file(relative, data)
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


def parse_machine_record(data: bytes, keys: Sequence[str], label: str) -> dict[str, str]:
    if data.startswith(b"\xef\xbb\xbf") or b"\r" in data or not data.endswith(b"\n") or data.endswith(b"\n\n"):
        raise Gate5ExportError(f"{label} must be BOM-free LF-only with exactly one final LF")
    try:
        lines = data[:-1].decode("utf-8").split("\n")
    except UnicodeDecodeError as exc:
        raise Gate5ExportError(f"{label} is not valid UTF-8") from exc
    pairs: list[tuple[str, str]] = []
    for line in lines:
        match = re.fullmatch(r"([a-z][a-z0-9_]*): ([^\r\n]+)", line)
        if not match:
            raise Gate5ExportError(f"{label} contains a malformed key/value line")
        pairs.append((match.group(1), match.group(2)))
    if tuple(key for key, _value in pairs) != tuple(keys):
        raise Gate5ExportError(f"{label} key order/schema differs from the canonical record")
    return dict(pairs)


def canonical_identity(value: str) -> bool:
    return bool(
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._@+-]{2,127}", value)
        and value.lower() not in GENERIC_BUILD_PARTS
        and not any(part in GENERIC_BUILD_PARTS for part in re.split(r"[._-]+", value.lower()))
    )


def canonical_rfc3339(value: str) -> bool:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value):
        return False
    try:
        dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def parse_rfc3339(value: str, label: str) -> dt.datetime:
    if not canonical_rfc3339(value):
        raise Gate5ExportError(f"{label} is not strict RFC-3339")
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:  # canonical_rfc3339 already rejects this path.
        raise Gate5ExportError(f"{label} is not strict RFC-3339") from exc


def direct_manifest_entries(
    manifest_bytes: bytes,
    closure: Mapping[str, ManifestEntry],
    label: str,
) -> tuple[ManifestEntry, ...]:
    """Return only the root manifest rows after parse_manifest proved the graph."""
    try:
        lines = manifest_bytes[:-1].decode("utf-8").split("\n")
        paths = tuple(line.split("\t", 1)[0] for line in lines)
        return tuple(closure[path] for path in paths)
    except (UnicodeDecodeError, KeyError, IndexError) as exc:  # defensive projection guard
        raise Gate5ExportError(f"{label} direct-member projection is malformed") from exc


def validate_gate_evidence_roles(
    scope: str, gate_index: int, entries: Iterable[ManifestEntry]
) -> None:
    roles = {entry.role for entry in entries}
    missing = [
        "/".join(sorted(allowed))
        for allowed in GATE_EVIDENCE_REQUIREMENTS[gate_index]
        if roles.isdisjoint(allowed)
    ]
    if missing:
        raise Gate5ExportError(
            f"{scope} G{gate_index} lacks gate-specific evidence categories: {', '.join(missing)}"
        )


def authoring_checker_sha256(root: Path, git: GitIndex) -> str:
    digest = hashlib.sha256()
    digest.update(b"n64game-authoring-checker-bundle-v1\n")
    for relative in sorted(AUTHORING_CHECKER_PATHS):
        data = authority_path(root, relative).read_bytes()
        git.verify_control_file(relative, data, FIXED_AUTHORITY_MODES[relative])
        digest.update(f"{relative}\t{sha256_bytes(data)}\n".encode("utf-8"))
    return digest.hexdigest()


def validate_g2_authoring_receipt(
    root: Path,
    scope: str,
    source_digest: str,
    decided_at: str,
    evidence_path: str,
    evidence_entries: Sequence[ManifestEntry],
    direct_entries: Sequence[ManifestEntry],
    git: GitIndex,
) -> str:
    receipt_path = f"review/{scope}/g2/AUTHORING_STACK_RECEIPT.txt"
    candidates = [
        entry for entry in evidence_entries
        if PurePosixPath(entry.path).name.lower() == "authoring_stack_receipt.txt"
        or entry.role == "authoring.stack_receipt"
    ]
    direct_candidates = [entry for entry in direct_entries if entry.path == receipt_path]
    if len(candidates) != 1 or candidates[0].path != receipt_path or len(direct_candidates) != 1:
        raise Gate5ExportError(
            f"{scope} G2 evidence must directly contain exactly {receipt_path}"
        )
    receipt_entry = candidates[0]
    if (
        receipt_entry.role != "authoring.stack_receipt"
        or receipt_entry.build != "-"
        or receipt_entry.capture != "-"
    ):
        raise Gate5ExportError(f"{scope} G2 authoring receipt manifest binding mismatch")
    receipt_bytes = authority_path(root, receipt_path).read_bytes()
    git.verify_control_file(receipt_path, receipt_bytes)
    receipt = parse_machine_record(receipt_bytes, AUTHORING_RECEIPT_KEYS, receipt_path)

    lock_path = "config/toolchain.lock.json"
    lock_bytes = authority_path(root, lock_path).read_bytes()
    git.verify_control_file(lock_path, lock_bytes, FIXED_AUTHORITY_MODES[lock_path])
    try:
        lock = json.loads(lock_bytes)
        authoring = lock["authoring"]
        blender = authoring["blender_macos_arm64"]
        fast64 = authoring["fast64"]
        blender_digest = blender["executable_sha256"]
        fast64_digest = fast64["source_tree_manifest_sha256"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise Gate5ExportError(f"{scope} G2 toolchain lock lacks exact Blender/Fast64 pins") from exc
    if (
        lock.get("schema_version") != 1
        or blender.get("version") != "4.5.11 LTS"
        or blender.get("version_tuple") != [4, 5, 11]
        or blender.get("build_hash") != "4db51e9d1e1e"
        or blender.get("build_platform") != "Darwin"
        or blender_digest != "8156431a9b9ec1daf49bccea4bd92f327f6efc1ca330d5103881580f3e7773ef"
        or blender.get("bundle_identifier") != "org.blenderfoundation.blender"
        or blender.get("codesign_team_identifier") != "68UA947AUU"
        or fast64.get("version") != "2.5.3"
        or fast64.get("tag") != "v2.5.3"
        or fast64.get("commit") != "8e9630c11824a9c00e9379279d43c64264eda87e"
        or fast64_digest != "14bb6c7b527ba364fa5e2a5011779ddd24c61f998c79c120f28d895d92e62e6b"
        or not HEX64.fullmatch(str(blender_digest))
        or not HEX64.fullmatch(str(fast64_digest))
        or authoring.get("blender_target") != blender.get("version")
        or authoring.get("fast64_version") != fast64.get("version")
        or authoring.get("fast64_commit") != fast64.get("commit")
    ):
        raise Gate5ExportError(f"{scope} G2 toolchain lock has noncanonical Blender/Fast64 pins")
    expected = {
        "schema": "n64game-authoring-stack-receipt-v1",
        "scope_id": scope,
        "gate": "G2",
        "source_manifest_sha256": source_digest,
        "output_manifest_sha256": "NONE",
        "build_id": "-",
        "toolchain_lock_sha256": sha256_bytes(lock_bytes),
        "checker_sha256": authoring_checker_sha256(root, git),
        "blender_executable_sha256": str(blender_digest),
        "blender_seal": "DEEP_STRICT_EXPLICIT_REQUIREMENT_PASS",
        "fast64_source_manifest_sha256": str(fast64_digest),
        "probe_mode": "ISOLATED_COPY_ENABLED_LOADED_NO_INHERITED_ENV",
        "result": "PASS",
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise Gate5ExportError(f"{scope} G2 authoring receipt {key} mismatch")
    checked_at = parse_rfc3339(receipt.get("checked_at", ""), f"{scope} G2 receipt checked_at")
    if checked_at > parse_rfc3339(decided_at, f"{scope} G2 decided_at"):
        raise Gate5ExportError(f"{scope} G2 authoring receipt is later than the gate decision")
    if evidence_path != f"review/{scope}/g2/EVIDENCE_MANIFEST.sha256":  # defensive
        raise Gate5ExportError(f"{scope} G2 authoring receipt has a noncanonical direct owner")
    return receipt_path


def validate_gate_authority(
    root: Path,
    scope: str,
    rows: Sequence[AllowlistRow],
    source_manifest_path: str,
    source_manifest: Mapping[str, ManifestEntry],
    *,
    candidate: bool,
    build_id: str,
    git: GitIndex,
) -> set[str]:
    """Validate exact tracked G1-G4 authority and return every bound control byte."""
    authorization_path = f"review/{scope}/g1/AUTHORIZATION.md"
    provenance_path = f"review/{scope}/g1/PROVENANCE.md"
    gate_record_path = f"review/{scope}/g1/GATE_RECORD.tsv"
    allowlist_path = f"review/{scope}/g1/SUBSET_EXPORT_ALLOWLIST.tsv"
    authorization_bytes = repo_path(root, authorization_path, "Gate-1 authorization").read_bytes()
    provenance_bytes = repo_path(root, provenance_path, "Gate-1 provenance").read_bytes()
    gate_bytes, gate_lines = canonical_text(
        repo_path(root, gate_record_path, "Gate-1 gate record"), gate_record_path
    )
    allowlist_bytes = git.control_bytes(allowlist_path)
    if allowlist_bytes is None:
        allowlist_bytes = repo_path(root, allowlist_path, "subset export allowlist").read_bytes()
        git.verify_control_file(allowlist_path, allowlist_bytes)
    git.verify_control_file(authorization_path, authorization_bytes)
    git.verify_control_file(provenance_path, provenance_bytes)
    git.verify_control_file(gate_record_path, gate_bytes)
    authorization = parse_machine_record(authorization_bytes, AUTHORIZATION_KEYS, authorization_path)
    provenance = parse_machine_record(provenance_bytes, PROVENANCE_KEYS, provenance_path)
    subset_digests = {row.subset_sha256 for row in rows}
    if len(subset_digests) != 1:
        raise Gate5ExportError(f"{scope} does not have one exact subset digest")
    subset_digest = next(iter(subset_digests))
    source_digest = git.validated_materialized_sha256(source_manifest_path)
    output_manifest_path = MODEL_MANIFEST_PATH if scope == MODEL_SCOPE else ANIMATION_MANIFEST_PATH
    if candidate:
        expected_output = "NONE"
    else:
        output_digest = git.validated_materialized_sha256(output_manifest_path)
        expected_output = f"{output_manifest_path}@{output_digest}"
    expected_authorization = {
        "schema": "n64game-authorization-v1",
        "basis": AUTHORIZATION_BASIS[scope],
        "production_id": scope,
        "subset_sha256": subset_digest,
        "subset_allowlist": f"{allowlist_path}@{sha256_bytes(allowlist_bytes)}",
        "state": "AUTHORIZED",
        "repair_ids": "NONE",
        "source_manifest": f"{source_manifest_path}@{source_digest}",
        "output_manifest": expected_output,
        "gate_record": f"{gate_record_path}@{sha256_bytes(gate_bytes)}",
    }
    for key, expected in expected_authorization.items():
        if authorization.get(key) != expected:
            raise Gate5ExportError(f"{scope} authorization {key} binding mismatch")
    expected_provenance = {
        "schema": "n64game-provenance-v1",
        "production_id": scope,
        "subset_sha256": subset_digest,
        "subset_allowlist": f"{allowlist_path}@{sha256_bytes(allowlist_bytes)}",
        "source_manifest": f"{source_manifest_path}@{source_digest}",
        "output_manifest": expected_output,
    }
    for key, expected in expected_provenance.items():
        if provenance.get(key) != expected:
            raise Gate5ExportError(f"{scope} provenance {key} binding mismatch")
    owner_ids = {provenance.get("creator_id", ""), provenance.get("rights_holder_id", "")}
    if not all(canonical_identity(owner) for owner in owner_ids):
        raise Gate5ExportError(f"{scope} provenance creator/rightsholder identity is malformed")
    if (
        not HEX64.fullmatch(provenance.get("transformations_sha256", ""))
        or provenance.get("transformations_sha256")
        in {sha256_bytes(b""), sha256_bytes(b"PENDING")}
        or provenance.get("rights_basis", "").lower() in GENERIC_BUILD_PARTS
        or provenance.get("output_license", "").lower() in GENERIC_BUILD_PARTS
        or "@" not in provenance.get("rights_evidence", "")
    ):
        raise Gate5ExportError(f"{scope} provenance rights/transformation binding is malformed")
    authorization_build = authorization.get("build_id", "")
    if candidate:
        if authorization_build != "-" and not canonical_build_id(authorization_build):
            raise Gate5ExportError(f"{scope} authorization build_id is neither prebuild '-' nor substantive")
    elif authorization_build != build_id:
        raise Gate5ExportError(f"{scope} authorization build_id binding mismatch")
    if not canonical_identity(authorization.get("authorizer_id", "")):
        raise Gate5ExportError(f"{scope} authorization has a malformed/placeholder authorizer")
    if authorization.get("authorizer_id") in owner_ids:
        raise Gate5ExportError(f"{scope} authorization authorizer matches an asset owner")
    if not canonical_rfc3339(authorization.get("authorized_at", "")):
        raise Gate5ExportError(f"{scope} authorization timestamp is not strict RFC-3339")
    if tuple(gate_lines[0].split("\t")) != GATE_RECORD_HEADER or len(gate_lines) != 8:
        raise Gate5ExportError(f"{scope} Gate record must have the exact header and seven rows")

    authority_paths = {
        authorization_path, provenance_path, gate_record_path, allowlist_path, source_manifest_path,
        *source_manifest.keys(),
    }
    profile, tier = PROFILE_TIER[scope]
    previous_decided_at: dt.datetime | None = None
    for index, line in enumerate(gate_lines[1:], 1):
        fields = line.split("\t")
        if len(fields) != len(GATE_RECORD_HEADER):
            raise Gate5ExportError(f"{scope} G{index} does not have sixteen fields")
        record = dict(zip(GATE_RECORD_HEADER, fields))
        if (
            record["scope_id"] != scope
            or record["profile"] != profile
            or record["tier"] != tier
            or record["gate"] != f"G{index}"
        ):
            raise Gate5ExportError(f"{scope} Gate record identity mismatch at G{index}")
        if index >= 5:
            if record["decision"] != "PENDING" or any(value != "PENDING" for value in fields[5:]):
                raise Gate5ExportError(f"{scope} G5-G7 must remain fully PENDING before export")
            continue
        if record["decision"] != "pass":
            raise Gate5ExportError(f"{scope} G1-G4 must each have exact decision pass")
        if (
            not canonical_identity(record["reviewer_id"])
            or record["reviewer_non_owner"] not in {"YES", "NO"}
            or record["source_manifest_sha256"] != source_digest
            or record["output_manifest_sha256"] != "NONE"
            or record["defect_ids"] != "NONE"
            or (record["build_id"] != "-" and not canonical_build_id(record["build_id"]))
            or not canonical_rfc3339(record["decided_at"])
        ):
            raise Gate5ExportError(f"{scope} G{index} source/output/build/reviewer binding mismatch")
        independent_required = tier == "H2" and index in {1, 3}
        if independent_required and record["reviewer_non_owner"] != "YES":
            raise Gate5ExportError(f"{scope} G{index} requires a non-owner reviewer")
        if record["reviewer_non_owner"] == "YES" and record["reviewer_id"] in owner_ids:
            raise Gate5ExportError(f"{scope} G{index} claimed non-owner reviewer matches an asset owner")
        decided_at = parse_rfc3339(record["decided_at"], f"{scope} G{index} decided_at")
        if previous_decided_at is not None and decided_at < previous_decided_at:
            raise Gate5ExportError(f"{scope} G{index} decision timestamp precedes an earlier gate")
        previous_decided_at = decided_at
        evidence_path = f"review/{scope}/g{index}/EVIDENCE_MANIFEST.sha256"
        review_path = f"review/{scope}/g{index}/REVIEW.md"
        if (
            record["evidence_manifest_path"] != evidence_path
            or record["review_record_path"] != review_path
            or not HEX64.fullmatch(record["evidence_manifest_sha256"])
            or not HEX64.fullmatch(record["review_record_sha256"])
        ):
            raise Gate5ExportError(f"{scope} G{index} uses noncanonical evidence/review bindings")
        evidence_file = repo_path(root, evidence_path, f"{scope} G{index} evidence manifest")
        review_file = repo_path(root, review_path, f"{scope} G{index} review record")
        evidence_bytes = evidence_file.read_bytes()
        review_bytes = review_file.read_bytes()
        if (
            sha256_bytes(evidence_bytes) != record["evidence_manifest_sha256"]
            or sha256_bytes(review_bytes) != record["review_record_sha256"]
        ):
            raise Gate5ExportError(f"{scope} G{index} evidence/review digest binding mismatch")
        git.verify_control_file(review_path, review_bytes)
        evidence_closure = parse_manifest(
            root, evidence_path, git, expected_root_bytes=evidence_bytes
        )
        direct_evidence = direct_manifest_entries(evidence_bytes, evidence_closure, evidence_path)
        gate_root = f"review/{scope}/g{index}/"
        if any(not path.startswith(gate_root) for path in evidence_closure):
            raise Gate5ExportError(f"{scope} G{index} evidence closure escapes its canonical gate root")
        receipt_candidates = [
            entry for entry in evidence_closure.values()
            if PurePosixPath(entry.path).name.lower() == "authoring_stack_receipt.txt"
            or entry.role == "authoring.stack_receipt"
        ]
        if index == 2:
            if record["build_id"] != "-":
                raise Gate5ExportError(f"{scope} G2 gate row build must be -")
            receipt_path = validate_g2_authoring_receipt(
                root, scope, source_digest, record["decided_at"], evidence_path,
                tuple(evidence_closure.values()), direct_evidence, git,
            )
            authority_paths.add(receipt_path)
        elif receipt_candidates:
            raise Gate5ExportError(f"{scope} G{index} forbids authoring receipt evidence")
        validate_gate_evidence_roles(scope, index, evidence_closure.values())
        review = parse_machine_record(review_bytes, GATE_REVIEW_KEYS, review_path)
        expected_review = {
            "schema": "n64game-gate-review-v1",
            "scope_id": scope,
            "gate": f"G{index}",
            "decision": "pass",
            "reviewer_id": record["reviewer_id"],
            "reviewer_non_owner": record["reviewer_non_owner"],
            "source_manifest_sha256": source_digest,
            "output_manifest_sha256": "NONE",
            "evidence_manifest": f"{evidence_path}@{record['evidence_manifest_sha256']}",
            "build_id": record["build_id"],
            "decided_at": record["decided_at"],
            "defect_ids": "NONE",
            "disposition": "NONE",
        }
        for key, expected in expected_review.items():
            if review.get(key) != expected:
                raise Gate5ExportError(f"{scope} G{index} review {key} projection mismatch")
        if len(review.get("rationale", "")) < 12:
            raise Gate5ExportError(f"{scope} G{index} review rationale is not substantive")
        authority_paths.update({evidence_path, review_path, *evidence_closure.keys()})
    return authority_paths


def validate_allowlist_sources(
    scope: str, rows: Sequence[AllowlistRow], manifest: Mapping[str, ManifestEntry]
) -> None:
    source_rows = [row for row in rows if row.stage == "SOURCE"]
    owner_root = MODEL_OWNER_ROOT if scope == MODEL_SCOPE else ANIMATION_OWNER_ROOT
    owner_prefix = owner_root + "/"
    manifest_paths = tuple(manifest)
    if (
        any(not path.startswith(owner_prefix) for path in manifest_paths)
        or len(set(manifest_paths)) != len(manifest_paths)
        or len({path.lower() for path in manifest_paths}) != len(manifest_paths)
    ):
        raise Gate5ExportError(f"{scope} source-manifest closure escapes or case-collides in its exact owner root")
    if {row.member_path for row in source_rows} != set(manifest):
        raise Gate5ExportError(f"{scope} allowlist SOURCE rows differ from source-manifest closure")
    if (
        len(source_rows) != len(manifest)
        or len({row.member_path.lower() for row in source_rows}) != len(source_rows)
    ):
        raise Gate5ExportError(f"{scope} allowlist SOURCE rows duplicate or case-collide")
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
    if len(model_content) != 4 or len(animation_content) != 1:
        raise Gate5ExportError("Quarrune requires exactly four model and one animation exportable source rows")
    model_by_path = {row.member_path: row for row in model_content}
    animation_by_path = {row.member_path: row for row in animation_content}
    expected_model_paths = {MODEL_SOURCE_PATH, *MODEL_PNG_PATHS.values()}
    expected_animation_paths = {ANIMATION_SOURCE_PATH}
    combined_paths = [*model_by_path, *animation_by_path]
    if (
        set(model_by_path) != expected_model_paths
        or set(animation_by_path) != expected_animation_paths
        or len(combined_paths) != 5
        or len(set(combined_paths)) != 5
        or len({path.lower() for path in combined_paths}) != 5
    ):
        raise Gate5ExportError("Quarrune exportable inputs differ from the five exact disjoint canonical paths")
    if model_by_path[MODEL_SOURCE_PATH].selectors != (
        "ASSET:distance_model", "ASSET:hero_model", "ASSET:rig"
    ):
        raise Gate5ExportError("canonical model Blender source has the wrong selector partition")
    if animation_by_path[ANIMATION_SOURCE_PATH].selectors != ANIMATION_SELECTORS:
        raise Gate5ExportError("canonical animation Blender source has the wrong nine-clip selector partition")
    if model_by_path[MODEL_PNG_PATHS["shadow"]].selectors != ("ASSET:blob_shadow",):
        raise Gate5ExportError("blob-shadow PNG must own only ASSET:blob_shadow")
    for key in ("body", "accent"):
        if model_by_path[MODEL_PNG_PATHS[key]].selectors != ("ASSET:texture",):
            raise Gate5ExportError(f"{MODEL_PNG_PATHS[key]} must own only ASSET:texture")
    for row in (*model_content, *animation_content):
        source = model_manifest.get(row.member_path) or animation_manifest.get(row.member_path)
        if source is None or source.role != "source.authored" or row.manifest_role != "source.authored":
            raise Gate5ExportError(f"all five exportable inputs must use exact role source.authored: {row.member_path}")
    return SourceInputs(
        model_blend=repo_path(root, MODEL_SOURCE_PATH, "model Blender source"),
        animation_blend=repo_path(root, ANIMATION_SOURCE_PATH, "animation Blender source"),
        body_png=repo_path(root, MODEL_PNG_PATHS["body"], "body PNG"),
        accent_png=repo_path(root, MODEL_PNG_PATHS["accent"], "accent PNG"),
        shadow_png=repo_path(root, MODEL_PNG_PATHS["shadow"], "shadow PNG"),
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
    output_paths = [row.member_path for row in output_rows]
    if (
        len(output_rows) != len(MANAGED_OUTPUT_PATHS)
        or set(output_paths) != set(MANAGED_OUTPUT_PATHS)
        or len(set(output_paths)) != len(output_paths)
        or len({path.lower() for path in output_paths}) != len(output_paths)
        or len({path.lower() for path in MANAGED_OUTPUT_PATHS}) != len(MANAGED_OUTPUT_PATHS)
    ):
        raise Gate5ExportError("final Gate-5 export requires exact OUTPUT rows for every paired package member")
    owner_partitions = (
        (MODEL_SCOPE, model_output_rows, MODEL_ROLES),
        (ANIMATION_SCOPE, animation_output_rows, ANIMATION_ROLES),
    )
    for scope, rows, expected_roles in owner_partitions:
        expected_paths = set(expected_roles)
        row_paths = [row.member_path for row in rows]
        if (
            len(rows) != len(expected_paths)
            or set(row_paths) != expected_paths
            or len(set(row_paths)) != len(row_paths)
            or len({path.lower() for path in row_paths}) != len(row_paths)
            or any(row.production_id != scope for row in rows)
        ):
            raise Gate5ExportError("final Gate-5 OUTPUT rows violate the exact model/animation owner partition")
        for row in rows:
            if row.manifest_role != expected_roles[row.member_path]:
                raise Gate5ExportError(f"Gate-5 OUTPUT role mismatch: {row.member_path}")
    for row in output_rows:
        entry = staged_entries[row.member_path]
        if row.selectors != ("OUTPUT:runtime",):
            raise Gate5ExportError(f"Gate-5 OUTPUT selector mismatch: {row.member_path}")
        if row.member_sha256 != entry.digest or row.manifest_role != entry.role:
            raise Gate5ExportError(f"regenerated output differs from reviewed allowlist binding: {row.member_path}")


def require_tool(
    path: Path,
    label: str,
    *,
    expected_size: int | None = None,
    expected_sha256: str | None = None,
) -> None:
    if not path.is_file() or path.is_symlink() or not os.access(path, os.X_OK):
        raise Gate5ExportError(f"{label} is missing, symlinked, non-regular, or non-executable: {path}")
    current = path
    while current != current.parent:
        if current.is_symlink():
            raise Gate5ExportError(f"{label} path traverses a symlink: {current}")
        current = current.parent
    observed_size = path.stat().st_size
    if expected_size is not None and observed_size != expected_size:
        raise Gate5ExportError(f"{label} size differs from the toolchain lock")
    if expected_sha256 is not None:
        if not HEX64.fullmatch(expected_sha256) or sha256_file(path) != expected_sha256:
            raise Gate5ExportError(f"{label} SHA-256 differs from the toolchain lock")


def resolve_tools(root: Path, *, lock_bytes: bytes | None = None) -> ToolPaths:
    if platform.system() != "Darwin" or platform.machine().lower() != "arm64":
        raise Gate5ExportError("Gate-5 host tools require exact platform Darwin-arm64")
    if lock_bytes is None:
        lock_path = repo_path(root, "config/toolchain.lock.json", "toolchain lock")
        lock_bytes = lock_path.read_bytes()
    lock = json.loads(lock_bytes)
    blender_pin = lock["authoring"]["blender_macos_arm64"]
    host_pins = lock["authoring"]["gate5_host_tools_macos_arm64"]
    if host_pins.get("platform") != "Darwin-arm64":
        raise Gate5ExportError("Gate-5 host-tool lock has the wrong platform")
    override = os.environ.get("N64GAME_BLENDER_BINARY")
    if override:
        blender = Path(os.path.abspath(override))
    else:
        home = os.environ.get("HOME")
        if not home:
            raise Gate5ExportError("HOME is absent; cannot resolve the exact Blender application")
        blender = Path(home) / blender_pin["macos_user_relative_path"]
    require_tool(
        blender,
        "pinned Blender executable",
        expected_size=blender_pin["executable_size"],
        expected_sha256=blender_pin["executable_sha256"],
    )
    n64_inst = os.environ.get("N64_INST")
    if not n64_inst:
        raise Gate5ExportError("N64_INST is required for the pinned Tiny3D/libdragon tools")
    n64_root = Path(os.path.abspath(n64_inst))
    gltf_to_t3d = n64_root / "bin" / "gltf_to_t3d"
    mksprite = n64_root / "bin" / "mksprite"
    require_tool(
        gltf_to_t3d,
        "gltf_to_t3d",
        expected_size=host_pins["gltf_to_t3d"]["executable_size"],
        expected_sha256=host_pins["gltf_to_t3d"]["executable_sha256"],
    )
    require_tool(
        mksprite,
        "mksprite",
        expected_size=host_pins["mksprite"]["executable_size"],
        expected_sha256=host_pins["mksprite"]["executable_sha256"],
    )
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

def reject_external_dependencies():
    if list(bpy.data.libraries):
        fail("linked Blender libraries are forbidden")
    # Every linked ID, including indirect links that do not appear as an
    # obvious library collection entry, is forbidden.
    for collection_name in dir(bpy.data):
        if collection_name.startswith("_"):
            continue
        collection = getattr(bpy.data, collection_name, None)
        if not hasattr(collection, "__iter__"):
            continue
        try:
            values = list(collection)
        except (TypeError, RuntimeError):
            continue
        for value in values:
            if getattr(value, "library", None) is not None:
                fail("linked Blender datablocks are forbidden")
    for image in bpy.data.images:
        packed = getattr(image, "packed_file", None) is not None or bool(getattr(image, "packed_files", ()))
        if image.source not in {"GENERATED", "VIEWER"} and not packed:
            fail("unpacked or external Blender images are forbidden")
    if list(bpy.data.cache_files):
        fail("external Blender cache files are forbidden")
    if list(bpy.data.movieclips) or list(bpy.data.sounds):
        fail("external Blender movie clips or sounds are forbidden")
    for font in bpy.data.fonts:
        filepath = getattr(font, "filepath", "")
        if filepath and filepath != "<builtin>":
            fail("external Blender fonts are forbidden")
    for volume in getattr(bpy.data, "volumes", ()):
        if getattr(volume, "filepath", ""):
            fail("external Blender volume files are forbidden")

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
reject_external_dependencies()
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


def parse_output_manifest(
    stage: Path,
    relative: str,
    roles: Mapping[str, str],
    build_id: str,
    *,
    git: GitIndex | None = None,
) -> list[ManifestEntry]:
    path = repo_path(stage, relative, "staged output manifest")
    manifest_bytes, lines = canonical_text(path, relative)
    if git is not None:
        git.verify_control_file(relative, manifest_bytes)
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
        entry = ManifestEntry(member, int(count), digest, build_id, "-", expected_role, kind)
        if git is not None:
            git.verify_member(entry, materialized)
        entries.append(entry)
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


def validate_staged_pair(
    stage: Path,
    build_id: str,
    root: Path = ROOT,
    *,
    git: GitIndex | None = None,
) -> dict[str, ManifestEntry]:
    model = parse_output_manifest(stage, MODEL_MANIFEST_PATH, MODEL_ROLES, build_id, git=git)
    animation = parse_output_manifest(
        stage, ANIMATION_MANIFEST_PATH, ANIMATION_ROLES, build_id, git=git
    )
    all_entries = (*model, *animation)
    raw_bytes: dict[str, str] = {}
    for entry in all_entries:
        materialized = repo_path(stage, entry.path, "staged package member").read_bytes()
        if git is not None:
            git.verify_member(entry, materialized)
        raw_bytes[entry.path] = base64.b64encode(materialized).decode("ascii")
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
    finalize_staging(stage, config.build_id, config.contract_root or config.root)


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


def authority_path(root: Path, relative: str) -> Path:
    if relative == ".gitattributes":
        path = Path(os.path.abspath(root)) / relative
        if not path.is_file() or path.is_symlink():
            raise Gate5ExportError(f"authority member is missing/symlinked: {relative}")
        return path
    return repo_path(root, relative, "authority member")


def default_authority_paths(config: ExportConfig) -> tuple[str, ...]:
    root_absolute = Path(os.path.abspath(config.root))
    input_paths: list[str] = []
    for path in config.inputs.__dict__.values():
        try:
            input_paths.append(Path(os.path.abspath(path)).relative_to(root_absolute).as_posix())
        except ValueError as exc:
            raise Gate5ExportError(f"authoring input is outside the exact repository root: {path}") from exc
    required = {
        *input_paths,
        MODEL_SOURCE_MANIFEST_PATH,
        ANIMATION_SOURCE_MANIFEST_PATH,
        f"review/{MODEL_SCOPE}/g1/SUBSET_EXPORT_ALLOWLIST.tsv",
        f"review/{ANIMATION_SCOPE}/g1/SUBSET_EXPORT_ALLOWLIST.tsv",
        f"review/{MODEL_SCOPE}/g1/AUTHORIZATION.md",
        f"review/{ANIMATION_SCOPE}/g1/AUTHORIZATION.md",
        f"review/{MODEL_SCOPE}/g1/GATE_RECORD.tsv",
        f"review/{ANIMATION_SCOPE}/g1/GATE_RECORD.tsv",
        *FIXED_AUTHORITY_PATHS,
    }
    if not config.candidate:
        required.update(MANAGED_PATHS)
    return tuple(sorted(required))


def authority_seal_map(
    config: ExportConfig, relatives: Sequence[str]
) -> dict[str, AuthoritySealEntry]:
    if not config.authority_seal:
        return {}
    sealed = {entry.path: entry for entry in config.authority_seal}
    if (
        len(sealed) != len(config.authority_seal)
        or tuple(sorted(sealed)) != tuple(sorted(relatives))
        or len({path.lower() for path in sealed}) != len(sealed)
    ):
        raise Gate5ExportError("validated authority seal membership differs from the capture closure")
    for entry in sealed.values():
        if (
            entry.materialized_count < 0
            or not HEX64.fullmatch(entry.materialized_sha256)
            or entry.index_mode not in {"100644", "100755"}
            or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", entry.index_oid)
            or tuple(name for name, _value in entry.cached_attributes) != INDEX_ATTRIBUTE_NAMES
        ):
            raise Gate5ExportError(f"validated authority seal is malformed: {entry.path}")
    return sealed


def verify_authority_index(config: ExportConfig, label: str) -> None:
    relatives = tuple(sorted(config.authority_paths or default_authority_paths(config)))
    sealed = authority_seal_map(config, relatives)
    if not sealed and not config.output_attribute_seal:
        return
    git = GitIndex(config.root)
    for relative in relatives:
        expected = sealed[relative]
        try:
            mode, oid, blob = git.index_blob(relative, (expected.index_mode,))
            current_attributes = git.attributes(relative)
            attrs = tuple((name, current_attributes[name]) for name in INDEX_ATTRIBUTE_NAMES)
        except Gate5ExportError as exc:
            raise Gate5ExportError(
                f"Git index authority changed at {label}: {relative}: {exc}"
            ) from exc
        if (
            mode != expected.index_mode
            or oid != expected.index_oid
            or blob != expected.index_blob
            or attrs != expected.cached_attributes
        ):
            raise Gate5ExportError(f"Git index authority changed at {label}: {relative}")
    expected_output_attrs = dict(config.output_attribute_seal)
    if len(expected_output_attrs) != len(config.output_attribute_seal):
        raise Gate5ExportError("sealed Gate-5 output attributes are duplicated")
    for relative, expected in sorted(expected_output_attrs.items()):
        current = git.attributes(relative)
        attrs = tuple((name, current[name]) for name in INDEX_ATTRIBUTE_NAMES)
        if attrs != expected:
            raise Gate5ExportError(
                f"Git index output-attribute authority changed at {label}: {relative}"
            )


def capture_authority(config: ExportConfig) -> AuthoritySnapshot:
    relatives = config.authority_paths or default_authority_paths(config)
    if (
        len(relatives) != len(set(relatives))
        or len(relatives) != len({relative.lower() for relative in relatives})
    ):
        raise Gate5ExportError("authority closure duplicates or case-collides")
    members: list[tuple[str, bytes]] = []
    sealed = authority_seal_map(config, relatives)
    verify_authority_index(config, "before authority capture")
    for relative in sorted(relatives):
        path = authority_path(config.root, relative)
        data = path.read_bytes()
        expected = sealed.get(relative)
        if expected is not None and (
            expected.materialized_count != len(data)
            or expected.materialized_sha256 != sha256_bytes(data)
        ):
            raise Gate5ExportError(f"captured authority differs from the validated immutable seal: {relative}")
        members.append((relative, data))
    verify_authority_index(config, "after authority capture")
    return AuthoritySnapshot(tuple(members))


def seal_validated_authority(config: ExportConfig, git: GitIndex) -> ExportConfig:
    relatives = tuple(sorted(config.authority_paths or default_authority_paths(config)))
    return dataclass_replace(
        config,
        authority_paths=relatives,
        authority_seal=git.validated_seal(relatives),
        output_attribute_seal=git.output_attribute_seal(),
    )


def verify_authority_snapshot(config: ExportConfig, captured: AuthoritySnapshot) -> None:
    expected_paths = tuple(relative for relative, _data in captured.members)
    current_paths = tuple(sorted(config.authority_paths or default_authority_paths(config)))
    if expected_paths != current_paths:
        raise Gate5ExportError("authority closure membership changed during export")
    verify_authority_index(config, "live authority checkpoint start")
    for relative, expected in captured.members:
        path = authority_path(config.root, relative)
        current = path.read_bytes()
        if current != expected:
            raise Gate5ExportError(f"source/control identity changed during export: {relative}")
    verify_authority_index(config, "live authority checkpoint end")


def materialize_authority(
    config: ExportConfig, captured: AuthoritySnapshot, stage: Path
) -> ExportConfig:
    captured_root = stage / "captured-authority"
    for relative, data in captured.members:
        destination = captured_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        destination.chmod(0o644)
    inputs = SourceInputs(
        captured_root / MODEL_SOURCE_PATH,
        captured_root / ANIMATION_SOURCE_PATH,
        captured_root / MODEL_PNG_PATHS["body"],
        captured_root / MODEL_PNG_PATHS["accent"],
        captured_root / MODEL_PNG_PATHS["shadow"],
    )
    for path in inputs.__dict__.values():
        if not path.is_file() or path.is_symlink():
            raise Gate5ExportError(f"captured authority lacks exact exportable input: {path}")
    return dataclass_replace(config, inputs=inputs, contract_root=captured_root)


def source_fingerprint(config: ExportConfig) -> tuple[tuple[str, int, str], ...]:
    """Compatibility projection of the now-complete immutable authority capture."""
    captured = capture_authority(config)
    return tuple((relative, len(data), sha256_bytes(data)) for relative, data in captured.members)


def _directory_flags() -> int:
    return os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)


def _open_directory_chain(root_fd: int, parts: Sequence[str], *, create: bool) -> int:
    current = os.dup(root_fd)
    try:
        for component in parts:
            if not SAFE_COMPONENT.fullmatch(component) or component in {".", ".."}:
                raise Gate5ExportError(f"unsafe directory component during Gate-5 promotion: {component!r}")
            if create:
                try:
                    os.mkdir(component, 0o755, dir_fd=current)
                    os.fsync(current)
                except FileExistsError:
                    pass
            next_fd = os.open(component, _directory_flags(), dir_fd=current)
            os.close(current)
            current = next_fd
        return current
    except BaseException:
        os.close(current)
        raise


def _open_root_directory(path: Path) -> int:
    real = Path(os.path.realpath(path))
    fd = os.open(real, _directory_flags())
    if not stat.S_ISDIR(os.fstat(fd).st_mode):  # pragma: no cover - O_DIRECTORY enforces this
        os.close(fd)
        raise Gate5ExportError(f"Gate-5 root is not a directory: {real}")
    return fd


def _read_regular_at(parent_fd: int, name: str, label: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(name, flags, dir_fd=parent_fd)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise Gate5ExportError(f"{label} is not one regular single-link file")
        chunks: list[bytes] = []
        while True:
            block = os.read(descriptor, 1024 * 1024)
            if not block:
                return b"".join(chunks)
            chunks.append(block)
    finally:
        os.close(descriptor)


def _unique_temp_name(prefix: str) -> str:
    return f"{prefix}{os.getpid()}-{secrets.token_hex(12)}"


def _write_file_at(parent_fd: int, name: str, data: bytes, *, mode: int = 0o644) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(name, flags, 0o600, dir_fd=parent_fd)
    try:
        offset = 0
        while offset < len(data):
            offset += os.write(descriptor, data[offset:])
        os.fchmod(descriptor, mode)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _journal_bytes(snapshot_value: Mapping[str, tuple[int, str]], promoted: Sequence[str]) -> bytes:
    payload = {
        "schema": "n64game-gate5-candidate-journal-v1",
        "mode": "candidate-only-serialized-promotion",
        "promoted": list(promoted),
        "snapshot": {
            relative: {"size": count, "sha256": digest}
            for relative, (count, digest) in sorted(snapshot_value.items())
        },
    }
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _replace_journal(journal_fd: int, data: bytes, *, initial: bool) -> None:
    journal_name = PurePosixPath(JOURNAL_RELATIVE).name
    if initial:
        _write_file_at(journal_fd, journal_name, data, mode=0o600)
    else:
        temporary = _unique_temp_name(".gate5-journal-")
        try:
            _write_file_at(journal_fd, temporary, data, mode=0o600)
            os.replace(temporary, journal_name, src_dir_fd=journal_fd, dst_dir_fd=journal_fd)
        finally:
            try:
                os.unlink(temporary, dir_fd=journal_fd)
            except FileNotFoundError:
                pass
    os.fsync(journal_fd)


def _assert_directory_binding(root_fd: int, parts: Sequence[str], expected_fd: int) -> None:
    reopened = _open_directory_chain(root_fd, parts, create=False)
    try:
        expected = os.fstat(expected_fd)
        observed = os.fstat(reopened)
        if (expected.st_dev, expected.st_ino) != (observed.st_dev, observed.st_ino):
            raise Gate5ExportError("Gate-5 destination parent identity changed during promotion")
    finally:
        os.close(reopened)


def preflight_destinations(root: Path, relatives: Iterable[str], *, replace: bool) -> None:
    if replace:
        raise Gate5ExportError("reviewed Gate-5 regeneration is verification-only and cannot rewrite snapshots")
    root_fd = _open_root_directory(root)
    opened: list[int] = []
    try:
        for relative in relatives:
            path = PurePosixPath(relative)
            parent_fd = _open_directory_chain(root_fd, path.parts[:-1], create=True)
            opened.append(parent_fd)
            names = os.listdir(parent_fd)
            if path.name in names or path.name.lower() in {name.lower() for name in names}:
                raise Gate5ExportError(f"Gate-5 candidate destination exists or case-collides: {relative}")
    finally:
        for descriptor in opened:
            os.close(descriptor)
        os.close(root_fd)


def promote_pair(
    stage: Path,
    root: Path,
    *,
    replace: bool,
    build_id: str,
    contract_root: Path,
    step_hook: Callable[[str, str | None], None] | None = None,
    postcheck: Callable[[], None] | None = None,
    lockcheck: Callable[[], None] | None = None,
) -> None:
    if replace:
        raise Gate5ExportError("reviewed Gate-5 regeneration is verification-only and cannot rewrite snapshots")
    expected_snapshot = snapshot(stage)
    root_fd = _open_root_directory(root)
    stage_fd = _open_root_directory(stage)
    parent_handles: dict[str, tuple[int, tuple[str, ...], str]] = {}
    promoted: list[str] = []
    journal_parts = PurePosixPath(JOURNAL_RELATIVE).parts
    journal_fd = -1
    journal_created = False
    try:
        if lockcheck:
            lockcheck()
        journal_fd = _open_directory_chain(root_fd, journal_parts[:-1], create=True)
        try:
            os.stat(journal_parts[-1], dir_fd=journal_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise Gate5ExportError(
                f"unfinished Gate-5 promotion journal exists; inspect or remove only after recovery: {JOURNAL_RELATIVE}"
            )
        for relative in MANAGED_PATHS:
            path = PurePosixPath(relative)
            parent_fd = _open_directory_chain(root_fd, path.parts[:-1], create=True)
            parent_handles[relative] = (parent_fd, path.parts[:-1], path.name)
            names = os.listdir(parent_fd)
            if path.name in names or path.name.lower() in {name.lower() for name in names}:
                raise Gate5ExportError(f"Gate-5 candidate destination exists or case-collides: {relative}")
        if step_hook:
            step_hook("parents_pinned", None)
        _replace_journal(journal_fd, _journal_bytes(expected_snapshot, promoted), initial=True)
        journal_created = True
        for relative in MANAGED_PATHS:
            if lockcheck:
                lockcheck()
            if step_hook:
                step_hook("before_link", relative)
            parent_fd, parent_parts, destination_name = parent_handles[relative]
            _assert_directory_binding(root_fd, parent_parts, parent_fd)
            stage_path = PurePosixPath(relative)
            source_parent = _open_directory_chain(stage_fd, stage_path.parts[:-1], create=False)
            try:
                source_bytes = _read_regular_at(source_parent, stage_path.name, "staged promotion member")
            finally:
                os.close(source_parent)
            temporary = _unique_temp_name(".gate5-pair-")
            linked = False
            try:
                _write_file_at(parent_fd, temporary, source_bytes)
                os.link(
                    temporary, destination_name,
                    src_dir_fd=parent_fd, dst_dir_fd=parent_fd, follow_symlinks=False,
                )
                linked = True
                os.unlink(temporary, dir_fd=parent_fd)
            except BaseException:
                if linked:
                    promoted.append(relative)
                try:
                    os.unlink(temporary, dir_fd=parent_fd)
                except FileNotFoundError:
                    pass
                raise
            promoted.append(relative)
            os.fsync(parent_fd)
            _replace_journal(journal_fd, _journal_bytes(expected_snapshot, promoted), initial=False)
            if step_hook:
                step_hook("after_link", relative)

        if step_hook:
            step_hook("before_postvalidate", None)
        if lockcheck:
            lockcheck()
        live_bytes: dict[str, bytes] = {}
        for relative in MANAGED_PATHS:
            parent_fd, parent_parts, destination_name = parent_handles[relative]
            _assert_directory_binding(root_fd, parent_parts, parent_fd)
            data = _read_regular_at(parent_fd, destination_name, "promoted Gate-5 member")
            if (len(data), sha256_bytes(data)) != expected_snapshot[relative]:
                raise Gate5ExportError(f"post-promotion byte snapshot mismatch: {relative}")
            live_bytes[relative] = data
        with tempfile.TemporaryDirectory(prefix="n64game-gate5-postvalidate-") as temporary:
            verification = Path(temporary)
            for relative, data in live_bytes.items():
                destination = verification / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
            validate_staged_pair(verification, build_id, contract_root)
        if postcheck:
            postcheck()
        if lockcheck:
            lockcheck()
        os.unlink(journal_parts[-1], dir_fd=journal_fd)
        os.fsync(journal_fd)
        journal_created = False
    except BaseException as exc:
        rollback_errors: list[str] = []
        for relative in reversed(promoted):
            try:
                parent_fd, _parent_parts, destination_name = parent_handles[relative]
                current = _read_regular_at(parent_fd, destination_name, "rollback candidate member")
                if (len(current), sha256_bytes(current)) != expected_snapshot[relative]:
                    raise Gate5ExportError("candidate member changed before rollback")
                os.unlink(destination_name, dir_fd=parent_fd)
                os.fsync(parent_fd)
            except BaseException as rollback_exc:  # pragma: no cover - catastrophic host failure
                rollback_errors.append(f"{relative}: {rollback_exc}")
        if journal_created and not rollback_errors:
            try:
                os.unlink(journal_parts[-1], dir_fd=journal_fd)
                os.fsync(journal_fd)
                journal_created = False
            except BaseException as rollback_exc:  # pragma: no cover - catastrophic host failure
                rollback_errors.append(f"journal: {rollback_exc}")
        detail = f"; rollback failures: {', '.join(rollback_errors)}" if rollback_errors else ""
        raise Gate5ExportError(f"paired Gate-5 candidate promotion failed and was rolled back{detail}: {exc}") from exc
    finally:
        for parent_fd, _parts, _name in parent_handles.values():
            os.close(parent_fd)
        if journal_fd >= 0:
            os.close(journal_fd)
        os.close(stage_fd)
        os.close(root_fd)


def reject_existing_journal(root: Path) -> None:
    root_fd = _open_root_directory(root)
    journal_fd = -1
    try:
        try:
            journal_fd = _open_directory_chain(
                root_fd, PurePosixPath(JOURNAL_RELATIVE).parts[:-1], create=False
            )
        except FileNotFoundError:
            return
        try:
            os.stat(PurePosixPath(JOURNAL_RELATIVE).name, dir_fd=journal_fd, follow_symlinks=False)
        except FileNotFoundError:
            return
        raise Gate5ExportError(
            f"unfinished Gate-5 promotion journal exists; fail-closed recovery required: {JOURNAL_RELATIVE}"
        )
    finally:
        if journal_fd >= 0:
            os.close(journal_fd)
        os.close(root_fd)


def _export_pair_locked(
    config: ExportConfig, *, generator: Generator | None = None, lock_fd: int
) -> dict[str, tuple[int, str]]:
    lockcheck = lambda label: validate_lock_boundary(config.root, lock_fd, label)
    lockcheck("initial authority snapshot")
    reject_existing_journal(config.root)
    captured = capture_authority(config)
    lockcheck("completed authority snapshot")
    tools: ToolPaths | None = None
    initial_tools: tuple[tuple[str, int, str], ...] | None = None
    if generator is None:
        lockcheck("tool resolution")
        captured_bytes = captured.bytes_by_path()
        try:
            captured_lock = captured_bytes["config/toolchain.lock.json"]
        except KeyError as exc:
            raise Gate5ExportError("captured authority lacks the exact toolchain lock") from exc
        tools = resolve_tools(config.root, lock_bytes=captured_lock)
        initial_tools = tool_fingerprint(tools)
        generator = lambda value, stage: production_generate(value, stage, tools=tools)
    with tempfile.TemporaryDirectory(prefix="n64game-gate5-pair-") as temporary:
        temp_root = Path(temporary)
        first = temp_root / "run-a"
        second = temp_root / "run-b"
        first.mkdir()
        second.mkdir()
        first_config = materialize_authority(config, captured, first)
        second_config = materialize_authority(config, captured, second)
        lockcheck("run A start")
        generator(first_config, first)
        lockcheck("run A completion")
        if tools is not None and tool_fingerprint(tools) != initial_tools:
            raise Gate5ExportError("converter/tool identity changed during the first clean export")
        verify_authority_snapshot(config, captured)
        first_entries = validate_staged_pair(first, config.build_id, first_config.contract_root or config.root)
        validate_output_allowlists(
            config.model_allowlist, config.animation_allowlist, first_entries, candidate=config.candidate
        )
        lockcheck("run B start")
        generator(second_config, second)
        lockcheck("run B completion")
        if tools is not None and tool_fingerprint(tools) != initial_tools:
            raise Gate5ExportError("converter/tool identity changed during the second clean export")
        verify_authority_snapshot(config, captured)
        second_entries = validate_staged_pair(second, config.build_id, second_config.contract_root or config.root)
        validate_output_allowlists(
            config.model_allowlist, config.animation_allowlist, second_entries, candidate=config.candidate
        )
        first_snapshot = snapshot(first)
        if first_snapshot != snapshot(second):
            raise Gate5ExportError("clean staged double export is nondeterministic")
        validate_reviewed_snapshot(config, first, first_entries)
        verify_authority_snapshot(config, captured)
        lockcheck("candidate promotion or final verification")
        if config.candidate:
            promote_pair(
                first,
                config.root,
                replace=False,
                build_id=config.build_id,
                contract_root=first_config.contract_root or config.root,
                postcheck=lambda: verify_authority_snapshot(config, captured),
                lockcheck=lambda: lockcheck("candidate promotion"),
            )
        # A final regeneration is intentionally verification-only.  The exact
        # reviewed bytes were already compared above and are never rewritten.
        lockcheck("export completion")
        return first_snapshot


def export_pair(
    config: ExportConfig,
    *,
    generator: Generator | None = None,
    _lock_fd: int | None = None,
) -> dict[str, tuple[int, str]]:
    if _lock_fd is not None:
        validate_lock_fd(_lock_fd, transaction_lock_path(config.root))
        return _export_pair_locked(config, generator=generator, lock_fd=_lock_fd)
    with transaction_lock(config.root) as lock_fd:
        return _export_pair_locked(config, generator=generator, lock_fd=lock_fd)


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
    model_manifest_path = MODEL_SOURCE_MANIFEST_PATH
    animation_manifest_path = ANIMATION_SOURCE_MANIFEST_PATH
    model_manifest = parse_manifest(root, model_manifest_path, git)
    animation_manifest = parse_manifest(root, animation_manifest_path, git)
    model_rows = parse_allowlist(root, MODEL_SCOPE, git)
    animation_rows = parse_allowlist(root, ANIMATION_SCOPE, git)
    validate_allowlist_sources(MODEL_SCOPE, model_rows, model_manifest)
    validate_allowlist_sources(ANIMATION_SCOPE, animation_rows, animation_manifest)
    inputs = select_inputs(root, model_rows, animation_rows, model_manifest, animation_manifest)
    authority_paths = set(FIXED_AUTHORITY_PATHS)
    for relative in FIXED_AUTHORITY_PATHS:
        materialized = authority_path(root, relative).read_bytes()
        git.verify_control_file(relative, materialized, FIXED_AUTHORITY_MODES[relative])
    if not args.candidate:
        validate_staged_pair(root, args.build_id, root, git=git)
        authority_paths.update(MANAGED_PATHS)
    authority_paths.update(validate_gate_authority(
        root, MODEL_SCOPE, model_rows, model_manifest_path, model_manifest,
        candidate=args.candidate, build_id=args.build_id, git=git,
    ))
    authority_paths.update(validate_gate_authority(
        root, ANIMATION_SCOPE, animation_rows, animation_manifest_path, animation_manifest,
        candidate=args.candidate, build_id=args.build_id, git=git,
    ))
    config = ExportConfig(
        root=root,
        build_id=args.build_id,
        inputs=inputs,
        model_allowlist=model_rows,
        animation_allowlist=animation_rows,
        candidate=args.candidate,
        replace=args.replace,
        authority_paths=tuple(sorted(authority_paths)),
    )
    return seal_validated_authority(config, git)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministically export the paired Quarrune Gate-5 package.")
    parser.add_argument("--scope", required=True)
    parser.add_argument("--paired-scope", required=True)
    parser.add_argument("--build-id", required=True)
    parser.add_argument("--deterministic", action="count", default=0)
    parser.add_argument("--candidate", action="store_true", help="materialize pre-approval review candidates from source-only allowlists")
    parser.add_argument("--replace", action="store_true", help="verification-only regeneration against an existing exact reviewed pair")
    args = parser.parse_args(argv)
    try:
        with transaction_lock(ROOT) as lock_fd:
            config = build_config(args)
            result = export_pair(config, _lock_fd=lock_fd)
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
