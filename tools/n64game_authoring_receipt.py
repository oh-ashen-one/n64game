#!/usr/bin/env python3
"""Produce asset-bound Blender/Fast64 receipts for Gate 2 and Gate 5.

The repository validator remains the authority for accepting these records. This
producer refuses to write a receipt unless the exact authoring stack passes. A
Gate-5 export is wrapped by checks both before and after the exporter command.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import os
import re
import secrets
import stat
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterator

TOOLS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_ROOT))
import n64game_authoring as authoring


ROOT = Path(__file__).resolve().parents[1]
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SCOPE_ID = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z0-9][a-z0-9_-]*)+$")
BUILD_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")
RFC3339 = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:Z|([+-])(\d{2}):(\d{2}))$"
)
GENERIC_BUILD_PARTS = {
    "pending", "none", "unassigned", "unknown", "todo", "tbd", "test", "testing",
    "example", "sample", "placeholder", "dummy", "fake", "reviewer", "operator",
    "person", "user", "agent", "owner", "creator", "temp", "temporary", "na", "n-a",
    "nil", "null",
}
CHECKER_BUNDLE_DOMAIN = b"n64game-authoring-checker-bundle-v1\n"
CHECKER_BUNDLE_PATHS = (
    "lib/n64game/libdragon_sprite_contract.rb",
    "lib/n64game/tiny3d_package_contract.rb",
    "scripts/check-authoring-stack",
    "scripts/export-gate5-asset",
    "scripts/record-authoring-stack-receipt",
    "tools/n64game_authoring.py",
    "tools/n64game_authoring_receipt.py",
    "tools/n64game_gate5_export.py",
)
CANONICAL_GATE5_EXPORTER_PATH = "scripts/export-gate5-asset"
GATE5_EXPORT_IMPLEMENTED = False
APPROVED_GATE5_EXPORTER_SHA256 = "PENDING"
RECEIPT_KEYS = (
    "schema",
    "scope_id",
    "gate",
    "source_manifest_sha256",
    "output_manifest_sha256",
    "build_id",
    "toolchain_lock_sha256",
    "checker_sha256",
    "blender_executable_sha256",
    "blender_seal",
    "fast64_source_manifest_sha256",
    "probe_mode",
    "result",
    "checked_at",
)
RECEIPT_SCHEMA = "n64game-authoring-stack-receipt-v1"
BLENDER_SEAL = "DEEP_STRICT_EXPLICIT_REQUIREMENT_PASS"
PROBE_MODE = "ISOLATED_COPY_ENABLED_LOADED_NO_INHERITED_ENV"
SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
TRANSACTION_LOCK_PREFIX = "n64game-gate5-"


@dataclass(frozen=True)
class FileSnapshot:
    """One immutable repository-file identity captured through no-follow FDs."""

    path: str
    byte_count: int
    sha256: str


@dataclass(frozen=True)
class ManifestClosureSnapshot:
    """The manifest roots and all bytes reachable from their rows."""

    roots: tuple[FileSnapshot, ...]
    manifests: tuple[FileSnapshot, ...]
    members: tuple[FileSnapshot, ...]


@dataclass(frozen=True)
class Gate5PairSnapshot:
    """A complete, immutable source/output observation for the owner pair."""

    source: ManifestClosureSnapshot
    output: ManifestClosureSnapshot

    def source_manifest_sha256(self, path: Path, *, root: Path = ROOT) -> str:
        return _snapshot_digest(self.source.roots, path, root)

    def output_manifest_sha256(self, path: Path, *, root: Path = ROOT) -> str:
        return _snapshot_digest(self.output.roots, path, root)


@dataclass(frozen=True)
class CheckedExport:
    """The stack identity and exact second (postchecked) closure observation."""

    stack_identity: tuple[tuple[str, str], ...]
    snapshot: object


@dataclass
class ReceiptTransaction:
    """Capability proving this process holds the repository transaction lock."""

    root_device: int
    root_inode: int
    temp_device: int
    temp_inode: int
    lock_device: int
    lock_inode: int
    temp_fd: int
    lock_name: str
    lock_fd: int
    active: bool = True


class AuthoringReceiptError(RuntimeError):
    """Raised when a receipt cannot truthfully be produced."""


def _directory_flags() -> int:
    return os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)


def _file_read_flags() -> int:
    return os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)


def _file_write_flags() -> int:
    return (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | os.O_CLOEXEC
        | getattr(os, "O_NOFOLLOW", 0)
    )


def _absolute_root(root: Path) -> Path:
    return Path(os.path.abspath(root))


def _safe_relative(path: Path, root: Path, label: str) -> PurePosixPath:
    absolute_root = _absolute_root(root)
    absolute_path = Path(os.path.abspath(path))
    try:
        relative = absolute_path.relative_to(absolute_root)
    except ValueError as exc:
        raise AuthoringReceiptError(f"{label} escapes the repository root") from exc
    value = relative.as_posix()
    result = PurePosixPath(value)
    if (
        not value
        or value == "."
        or str(result) != value
        or any(
            component in {"", ".", ".."} or SAFE_COMPONENT.fullmatch(component) is None
            for component in result.parts
        )
    ):
        raise AuthoringReceiptError(
            f"{label} is not one safe canonical repository path: {value!r}"
        )
    return result


def _safe_manifest_member(value: str, label: str) -> PurePosixPath:
    if not value or value.startswith("/") or "\\" in value or "\x00" in value:
        raise AuthoringReceiptError(f"{label} has unsafe member path: {value!r}")
    result = PurePosixPath(value)
    if (
        str(result) != value
        or len(result.parts) < 2
        or any(
            component in {"", ".", ".."} or SAFE_COMPONENT.fullmatch(component) is None
            for component in result.parts
        )
    ):
        raise AuthoringReceiptError(f"{label} has unsafe member path: {value!r}")
    return result


def _open_root_fd(root: Path) -> int:
    absolute_root = _absolute_root(root)
    try:
        descriptor = os.open(absolute_root, _directory_flags())
    except OSError as exc:
        raise AuthoringReceiptError(
            f"repository root is not one no-follow directory: {absolute_root}"
        ) from exc
    metadata = os.fstat(descriptor)
    if not stat.S_ISDIR(metadata.st_mode):  # pragma: no cover - O_DIRECTORY is authoritative
        os.close(descriptor)
        raise AuthoringReceiptError("repository root descriptor is not a directory")
    return descriptor


def _open_directory_chain(
    root_fd: int,
    components: Sequence[str],
    *,
    create: bool = False,
) -> int:
    current = os.dup(root_fd)
    try:
        for component in components:
            if SAFE_COMPONENT.fullmatch(component) is None:
                raise AuthoringReceiptError(
                    f"unsafe repository directory component: {component!r}"
                )
            if create:
                try:
                    os.mkdir(component, 0o755, dir_fd=current)
                except FileExistsError:
                    pass
            try:
                following = os.open(component, _directory_flags(), dir_fd=current)
            except OSError as exc:
                raise AuthoringReceiptError(
                    f"repository directory is missing, non-directory, or a symlink: {component}"
                ) from exc
            os.close(current)
            current = following
        return current
    except BaseException:
        os.close(current)
        raise


def _verify_root_anchor(root: Path, root_fd: int) -> None:
    try:
        observed_fd = _open_root_fd(root)
    except AuthoringReceiptError as exc:
        raise AuthoringReceiptError(
            "repository root was swapped during receipt transaction"
        ) from exc
    try:
        expected = os.fstat(root_fd)
        observed = os.fstat(observed_fd)
        if (expected.st_dev, expected.st_ino) != (observed.st_dev, observed.st_ino):
            raise AuthoringReceiptError(
                "repository root was swapped during receipt transaction"
            )
    finally:
        os.close(observed_fd)


def _verify_parent_anchor(
    root: Path,
    root_fd: int,
    components: Sequence[str],
    parent_fd: int,
) -> None:
    _verify_root_anchor(root, root_fd)
    observed_fd = _open_directory_chain(root_fd, components)
    try:
        expected = os.fstat(parent_fd)
        observed = os.fstat(observed_fd)
        if (expected.st_dev, expected.st_ino) != (observed.st_dev, observed.st_ino):
            raise AuthoringReceiptError("receipt parent was swapped during the transaction")
    finally:
        os.close(observed_fd)


def _read_all(descriptor: int) -> bytes:
    blocks: list[bytes] = []
    while True:
        block = os.read(descriptor, 1024 * 1024)
        if not block:
            return b"".join(blocks)
        blocks.append(block)


def _read_repo_file(
    root_fd: int, relative: PurePosixPath, label: str
) -> tuple[FileSnapshot, bytes]:
    parent_fd = _open_directory_chain(root_fd, relative.parts[:-1])
    try:
        try:
            descriptor = os.open(relative.name, _file_read_flags(), dir_fd=parent_fd)
        except OSError as exc:
            raise AuthoringReceiptError(
                f"{label} is missing, non-regular, or a symlink: {relative}"
            ) from exc
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode):
                raise AuthoringReceiptError(f"{label} is not one regular file: {relative}")
            data = _read_all(descriptor)
            after = os.fstat(descriptor)
            before_identity = (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mtime_ns,
                before.st_ctime_ns,
            )
            after_identity = (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            )
            if before_identity != after_identity or len(data) != after.st_size:
                raise AuthoringReceiptError(
                    f"{label} changed while it was being captured: {relative}"
                )
        finally:
            os.close(descriptor)
    finally:
        os.close(parent_fd)
    return FileSnapshot(
        str(relative), len(data), hashlib.sha256(data).hexdigest()
    ), data


def _snapshot_digest(values: Sequence[FileSnapshot], path: Path, root: Path) -> str:
    relative = str(_safe_relative(path, root, "snapshot lookup"))
    matches = [value.sha256 for value in values if value.path == relative]
    if len(matches) != 1:
        raise AuthoringReceiptError(
            f"verified snapshot lacks one exact manifest identity: {relative}"
        )
    return matches[0]


def gate5_lock_path(root: Path = ROOT) -> Path:
    physical_root = os.path.realpath(_absolute_root(root))
    digest = hashlib.sha256(os.fsencode(physical_root)).hexdigest()
    return Path("/tmp") / f"{TRANSACTION_LOCK_PREFIX}{digest}.lock"


def _assert_lock_namespace(transaction: ReceiptTransaction) -> None:
    """Prove the held flock is still the one named by the canonical /tmp path."""
    if not transaction.active:
        raise AuthoringReceiptError("receipt transaction capability is no longer active")
    try:
        lock_metadata = os.fstat(transaction.lock_fd)
        temp_metadata = os.fstat(transaction.temp_fd)
        path_metadata = os.stat(
            transaction.lock_name,
            dir_fd=transaction.temp_fd,
            follow_symlinks=False,
        )
        observed_temp_fd = _open_root_fd(Path(os.path.realpath("/tmp")))
    except (OSError, AuthoringReceiptError) as exc:
        raise AuthoringReceiptError(
            "canonical Gate-5 transaction lock pathname changed while held"
        ) from exc
    try:
        observed_temp = os.fstat(observed_temp_fd)
    finally:
        os.close(observed_temp_fd)
    expected_lock = (transaction.lock_device, transaction.lock_inode)
    if (
        (temp_metadata.st_dev, temp_metadata.st_ino)
        != (transaction.temp_device, transaction.temp_inode)
        or (observed_temp.st_dev, observed_temp.st_ino)
        != (transaction.temp_device, transaction.temp_inode)
        or (lock_metadata.st_dev, lock_metadata.st_ino) != expected_lock
        or (path_metadata.st_dev, path_metadata.st_ino) != expected_lock
        or not stat.S_ISREG(lock_metadata.st_mode)
        or not stat.S_ISREG(path_metadata.st_mode)
        or lock_metadata.st_uid != os.getuid()
        or path_metadata.st_uid != os.getuid()
        or stat.S_IMODE(lock_metadata.st_mode) != 0o600
        or stat.S_IMODE(path_metadata.st_mode) != 0o600
        or lock_metadata.st_nlink != 1
        or path_metadata.st_nlink != 1
    ):
        raise AuthoringReceiptError(
            "canonical Gate-5 transaction lock pathname changed while held"
        )


@contextmanager
def gate5_transaction_lock(root: Path = ROOT) -> Iterator[ReceiptTransaction]:
    """Hold the cross-process lock across paired export, postcheck, and promotion."""
    physical_root = Path(os.path.realpath(_absolute_root(root)))
    root_fd = _open_root_fd(physical_root)
    temp_fd: int | None = None
    lock_fd: int | None = None
    transaction: ReceiptTransaction | None = None
    primary_error: BaseException | None = None
    try:
        physical_temp = Path(os.path.realpath("/tmp"))
        temp_fd = _open_root_fd(physical_temp)
        lock_name = gate5_lock_path(physical_root).name
        for attempt in range(3):
            try:
                lock_fd = os.open(
                    lock_name,
                    os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                    dir_fd=temp_fd,
                )
                break
            except FileNotFoundError:
                if attempt == 2:
                    raise AuthoringReceiptError(
                        "cannot open the no-follow Gate-5 transaction lock"
                    )
            except OSError as exc:
                raise AuthoringReceiptError(
                    "cannot open the no-follow Gate-5 transaction lock"
                ) from exc
        metadata = os.fstat(lock_fd)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or metadata.st_nlink != 1
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            raise AuthoringReceiptError(
                "Gate-5 transaction lock is not one private root-keyed regular file"
            )
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        _verify_root_anchor(physical_root, root_fd)
        root_metadata = os.fstat(root_fd)
        temp_metadata = os.fstat(temp_fd)
        lock_metadata = os.fstat(lock_fd)
        transaction = ReceiptTransaction(
            root_metadata.st_dev,
            root_metadata.st_ino,
            temp_metadata.st_dev,
            temp_metadata.st_ino,
            lock_metadata.st_dev,
            lock_metadata.st_ino,
            temp_fd,
            lock_name,
            lock_fd,
        )
        _assert_lock_namespace(transaction)
        yield transaction
        _assert_lock_namespace(transaction)
    except BaseException as exc:
        primary_error = exc
        if transaction is not None and transaction.active:
            try:
                _assert_lock_namespace(transaction)
            except BaseException as namespace_exc:
                if hasattr(exc, "add_note"):
                    exc.add_note(
                        f"lock namespace also failed before release: {namespace_exc}"
                    )
        raise
    finally:
        if transaction is not None:
            transaction.active = False
        cleanup_errors: list[str] = []
        if lock_fd is not None:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
            except BaseException as exc:
                cleanup_errors.append(f"unlock: {exc}")
            try:
                os.close(lock_fd)
            except BaseException as exc:
                cleanup_errors.append(f"lock close: {exc}")
        if temp_fd is not None:
            try:
                os.close(temp_fd)
            except BaseException as exc:
                cleanup_errors.append(f"temporary-directory close: {exc}")
        try:
            os.close(root_fd)
        except BaseException as exc:
            cleanup_errors.append(f"repository-root close: {exc}")
        if cleanup_errors:
            detail = "; ".join(cleanup_errors)
            if primary_error is not None:
                if hasattr(primary_error, "add_note"):
                    primary_error.add_note(f"transaction cleanup also failed: {detail}")
            else:
                raise AuthoringReceiptError(
                    f"Gate-5 transaction cleanup failed: {detail}"
                )


def _assert_transaction(transaction: ReceiptTransaction, root_fd: int) -> None:
    if not transaction.active:
        raise AuthoringReceiptError("receipt transaction capability is no longer active")
    root_metadata = os.fstat(root_fd)
    if (root_metadata.st_dev, root_metadata.st_ino) != (
        transaction.root_device,
        transaction.root_inode,
    ):
        raise AuthoringReceiptError(
            "receipt transaction belongs to a different repository root"
        )
    _assert_lock_namespace(transaction)
    try:
        fcntl.flock(transaction.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:  # pragma: no cover - capability corruption is not expected
        raise AuthoringReceiptError("receipt transaction lock is not held") from exc
    _assert_lock_namespace(transaction)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_regular(path: Path, label: str) -> None:
    if not path.is_file() or path.is_symlink():
        raise AuthoringReceiptError(f"{label} is not one regular non-symlink file: {path}")


def require_repo_regular(path: Path, label: str, root: Path = ROOT) -> None:
    root = Path(os.path.abspath(root))
    path = Path(os.path.abspath(path))
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise AuthoringReceiptError(f"{label} escapes the repository root: {path}") from exc
    current = root
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise AuthoringReceiptError(f"{label} traverses a symlink: {current}")
    require_regular(path, label)


def checker_bundle_sha256(root: Path = ROOT) -> str:
    """Hash the canonical entrypoint and implementation with path separation."""
    digest = hashlib.sha256(CHECKER_BUNDLE_DOMAIN)
    for relative in sorted(CHECKER_BUNDLE_PATHS):
        path = root / relative
        require_repo_regular(path, f"authoring checker member {relative}", root)
        digest.update(f"{relative}\t{sha256_file(path)}\n".encode("utf-8"))
    return digest.hexdigest()


def require_approved_gate5_exporter() -> str:
    """Keep Gate 5 closed until one reviewed exporter is explicitly pinned."""
    if not GATE5_EXPORT_IMPLEMENTED:
        raise AuthoringReceiptError("Gate-5 exporter is not implemented and approved")
    if not HEX64.fullmatch(APPROVED_GATE5_EXPORTER_SHA256):
        raise AuthoringReceiptError("Gate-5 exporter approval SHA-256 is not one exact reviewed digest")
    return APPROVED_GATE5_EXPORTER_SHA256


def valid_rfc3339(value: str) -> bool:
    match = RFC3339.fullmatch(value)
    if not match:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    if match.group(7) is not None:
        return int(match.group(8)) <= 23 and int(match.group(9)) <= 59
    return True


def canonical_checked_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_build_id(value: str) -> bool:
    if not BUILD_ID.fullmatch(value):
        return False
    parts = re.split(r"[._-]+", value.lower())
    compact = "".join(parts)
    def generic(component: str) -> bool:
        normalized = re.sub(r"[._-]+", "", component)
        return any(
            normalized == root or re.fullmatch(re.escape(root) + r"0*[0-9]+", normalized) is not None
            for root in GENERIC_BUILD_PARTS
        )

    return value != "-" and not generic(compact) and not any(generic(part) for part in parts)


def canonical_source_manifest(scope_id: str, root: Path = ROOT) -> Path:
    if not SCOPE_ID.fullmatch(scope_id):
        raise AuthoringReceiptError(f"scope ID is not canonical: {scope_id!r}")
    return root / "assets-src" / scope_id.split(".", 1)[0] / scope_id / "SOURCE_MANIFEST.sha256"


def canonical_output_manifest(scope_id: str, root: Path = ROOT) -> Path:
    if not SCOPE_ID.fullmatch(scope_id):
        raise AuthoringReceiptError(f"scope ID is not canonical: {scope_id!r}")
    return root / "review" / scope_id / "g5" / "OUTPUT_MANIFEST.sha256"


def canonical_receipt_path(scope_id: str, gate: str, root: Path = ROOT) -> Path:
    if not SCOPE_ID.fullmatch(scope_id):
        raise AuthoringReceiptError(f"scope ID is not canonical: {scope_id!r}")
    if gate not in {"G2", "G5"}:
        raise AuthoringReceiptError("authoring receipts are legal only at G2 and G5")
    return root / "review" / scope_id / gate.lower() / "AUTHORING_STACK_RECEIPT.txt"


def _manifest_rows(
    data: bytes, label: str
) -> tuple[tuple[str, int, str, str, str, str], ...]:
    if not data or not data.endswith(b"\n") or b"\r" in data or b"\x00" in data:
        raise AuthoringReceiptError(f"{label} is not canonical nonempty LF text")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AuthoringReceiptError(f"{label} is not UTF-8") from exc
    rows: list[tuple[str, int, str, str, str, str]] = []
    observed_paths: list[str] = []
    for index, line in enumerate(text[:-1].split("\n"), 1):
        fields = line.split("\t")
        if len(fields) != 6:
            raise AuthoringReceiptError(
                f"{label} line {index} must contain six TAB fields"
            )
        member, count_text, digest, build_token, capture_token, role_token = fields
        _safe_manifest_member(member, label)
        if (
            re.fullmatch(r"0|[1-9][0-9]*", count_text) is None
            or HEX64.fullmatch(digest) is None
        ):
            raise AuthoringReceiptError(
                f"{label} has malformed member identity: {member}"
            )
        if not build_token.startswith("build:") or not capture_token.startswith("capture:"):
            raise AuthoringReceiptError(
                f"{label} has malformed build/capture tokens: {member}"
            )
        if not role_token.startswith("role:"):
            raise AuthoringReceiptError(f"{label} has malformed role token: {member}")
        build, capture, role = build_token[6:], capture_token[8:], role_token[5:]
        token = r"-|[A-Za-z0-9][A-Za-z0-9._-]{0,95}"
        if re.fullmatch(token, build) is None or re.fullmatch(token, capture) is None:
            raise AuthoringReceiptError(
                f"{label} has malformed build/capture values: {member}"
            )
        if (
            re.fullmatch(r"[a-z][a-z0-9._-]{0,63}", role) is None
            or role in {"file", "misc"}
        ):
            raise AuthoringReceiptError(
                f"{label} has malformed role value: {member}"
            )
        observed_paths.append(member)
        rows.append((member, int(count_text), digest, build, capture, role))
    if not rows:
        raise AuthoringReceiptError(f"{label} has no members")
    if observed_paths != sorted(observed_paths) or len(
        {value.lower() for value in observed_paths}
    ) != len(observed_paths):
        raise AuthoringReceiptError(
            f"{label} members are not unique raw-byte path sorted"
        )
    return tuple(rows)


def _capture_manifest_closure(
    root: Path,
    manifest_paths: Sequence[Path],
    *,
    expected_build_id: str | None = None,
) -> ManifestClosureSnapshot:
    """Capture and validate manifest roots plus every recursively referenced member."""
    absolute_root = _absolute_root(root)
    root_fd = _open_root_fd(absolute_root)
    roots: list[FileSnapshot] = []
    manifests: dict[str, FileSnapshot] = {}
    members: dict[str, FileSnapshot] = {}
    owners: set[str] = set()
    visiting: set[str] = set()

    def walk(
        relative: PurePosixPath,
        data: bytes | None = None,
        identity: FileSnapshot | None = None,
    ) -> FileSnapshot:
        manifest_name = str(relative)
        if manifest_name in visiting:
            raise AuthoringReceiptError(
                f"manifest closure cycle includes {manifest_name}"
            )
        prior = manifests.get(manifest_name)
        if prior is not None:
            if identity is not None and identity != prior:
                raise AuthoringReceiptError(
                    f"manifest identity changed while closing {manifest_name}"
                )
            return prior
        if identity is None or data is None:
            identity, data = _read_repo_file(root_fd, relative, "manifest")
        manifests[manifest_name] = identity
        visiting.add(manifest_name)
        try:
            for member, count, digest, build, capture, _role in _manifest_rows(
                data, manifest_name
            ):
                folded = member.lower()
                if folded in owners:
                    raise AuthoringReceiptError(
                        f"manifest closure owns a member more than once: {member}"
                    )
                owners.add(folded)
                member_relative = _safe_manifest_member(member, manifest_name)
                member_identity, member_data = _read_repo_file(
                    root_fd, member_relative, "manifest member"
                )
                if (
                    member_identity.byte_count != count
                    or member_identity.sha256 != digest
                ):
                    raise AuthoringReceiptError(
                        f"manifest digest/count mismatch: {member}"
                    )
                if expected_build_id is not None and (
                    build != expected_build_id or capture != "-"
                ):
                    raise AuthoringReceiptError(
                        f"output manifest member has wrong build/capture identity: {member}"
                    )
                members[member] = member_identity
                if member.endswith("MANIFEST.sha256"):
                    walk(member_relative, member_data, member_identity)
        finally:
            visiting.remove(manifest_name)
        return identity

    try:
        seen_roots: set[str] = set()
        for path in manifest_paths:
            relative = _safe_relative(path, absolute_root, "manifest root")
            value = str(relative)
            if value.lower() in seen_roots:
                raise AuthoringReceiptError(
                    "manifest roots are duplicated or case-colliding"
                )
            seen_roots.add(value.lower())
            roots.append(walk(relative))
        _verify_root_anchor(absolute_root, root_fd)
    finally:
        os.close(root_fd)
    return ManifestClosureSnapshot(
        roots=tuple(roots),
        manifests=tuple(sorted(manifests.values(), key=lambda value: value.path)),
        members=tuple(sorted(members.values(), key=lambda value: value.path)),
    )


def capture_gate5_pair_snapshot(
    source_paths: Sequence[Path],
    output_paths: Sequence[Path],
    *,
    build_id: str,
    root: Path = ROOT,
) -> Gate5PairSnapshot:
    if len(source_paths) != 2 or len(output_paths) != 2:
        raise AuthoringReceiptError(
            "Gate-5 snapshot requires exactly two source and two output manifests"
        )
    if not canonical_build_id(build_id):
        raise AuthoringReceiptError(
            "Gate-5 snapshot requires one substantive clean-build ID"
        )
    return Gate5PairSnapshot(
        source=_capture_manifest_closure(root, source_paths),
        output=_capture_manifest_closure(
            root, output_paths, expected_build_id=build_id
        ),
    )


def portable_stack_identity(report: Mapping[str, Any], root: Path = ROOT) -> dict[str, str]:
    """Reduce a host-path-heavy observation to the exact portable receipt pins."""
    lock_path = root / "config" / "toolchain.lock.json"
    require_repo_regular(lock_path, "toolchain lock", root)
    lock = authoring.load_authoring_lock(lock_path)
    blender_pin = lock["blender_macos_arm64"]
    fast64_pin = lock["fast64"]
    blender = report.get("blender")
    fast64 = report.get("fast64")
    if report.get("status") != "PASS" or not isinstance(blender, Mapping) or not isinstance(fast64, Mapping):
        raise AuthoringReceiptError("authoring checker did not return one passing stack report")
    codesign = blender.get("codesign")
    probe = fast64.get("enabled_probe")
    if not isinstance(codesign, Mapping) or not isinstance(probe, Mapping):
        raise AuthoringReceiptError("authoring report lacks code-signing or isolated-probe evidence")
    if (
        blender.get("sha256") != blender_pin["executable_sha256"]
        or codesign.get("deep_strict_verified") is not True
        or blender.get("post_probe_deep_strict_verified") is not True
    ):
        raise AuthoringReceiptError("Blender executable/signing seal differs from the exact lock")
    if fast64.get("manifest_sha256") != fast64_pin["source_tree_manifest_sha256"]:
        raise AuthoringReceiptError("Fast64 source manifest differs from the exact lock")
    if not (
        probe.get("enabled") is True
        and probe.get("loaded") is True
        and probe.get("isolated_profile") is True
        and probe.get("inherited_environment") is False
        and probe.get("offline_mode") is True
        and probe.get("autoexec_disabled") is True
        and probe.get("module_execution") == "isolated_copy_of_pinned_fast64"
    ):
        raise AuthoringReceiptError("Fast64 did not pass the exact isolated enabled/loaded probe")
    return {
        "toolchain_lock_sha256": sha256_file(lock_path),
        "checker_sha256": checker_bundle_sha256(root),
        "blender_executable_sha256": blender_pin["executable_sha256"],
        "blender_seal": BLENDER_SEAL,
        "fast64_source_manifest_sha256": fast64_pin["source_tree_manifest_sha256"],
        "probe_mode": PROBE_MODE,
    }


def build_receipt(
    *,
    scope_id: str,
    gate: str,
    source_manifest_sha256: str,
    output_manifest_sha256: str,
    build_id: str,
    checked_at: str,
    stack_identity: Mapping[str, str],
) -> dict[str, str]:
    if not SCOPE_ID.fullmatch(scope_id):
        raise AuthoringReceiptError(f"scope ID is not canonical: {scope_id!r}")
    if gate not in {"G2", "G5"}:
        raise AuthoringReceiptError("authoring receipts are legal only at G2 and G5")
    if not HEX64.fullmatch(source_manifest_sha256):
        raise AuthoringReceiptError("source manifest SHA-256 is malformed")
    if gate == "G2":
        if output_manifest_sha256 != "NONE" or build_id != "-":
            raise AuthoringReceiptError("G2 must bind output NONE and prebuild ID -")
    elif not HEX64.fullmatch(output_manifest_sha256) or not canonical_build_id(build_id):
        raise AuthoringReceiptError("G5 requires one output SHA-256 and substantive clean-build ID")
    if not valid_rfc3339(checked_at):
        raise AuthoringReceiptError("checked_at is not strict RFC 3339")
    expected_stack_keys = {
        "toolchain_lock_sha256",
        "checker_sha256",
        "blender_executable_sha256",
        "blender_seal",
        "fast64_source_manifest_sha256",
        "probe_mode",
    }
    if set(stack_identity) != expected_stack_keys:
        raise AuthoringReceiptError("portable stack identity has missing or extra fields")
    for key in (
        "toolchain_lock_sha256",
        "checker_sha256",
        "blender_executable_sha256",
        "fast64_source_manifest_sha256",
    ):
        if not HEX64.fullmatch(stack_identity[key]):
            raise AuthoringReceiptError(f"{key} is malformed")
    if stack_identity["blender_seal"] != BLENDER_SEAL or stack_identity["probe_mode"] != PROBE_MODE:
        raise AuthoringReceiptError("portable stack identity uses a noncanonical seal")
    values = {
        "schema": RECEIPT_SCHEMA,
        "scope_id": scope_id,
        "gate": gate,
        "source_manifest_sha256": source_manifest_sha256,
        "output_manifest_sha256": output_manifest_sha256,
        "build_id": build_id,
        **stack_identity,
        "result": "PASS",
        "checked_at": checked_at,
    }
    return {key: values[key] for key in RECEIPT_KEYS}


def render_receipt(receipt: Mapping[str, str]) -> bytes:
    if tuple(receipt) != RECEIPT_KEYS:
        raise AuthoringReceiptError("receipt keys are missing, extra, or out of order")
    for key, value in receipt.items():
        if not isinstance(value, str) or not value or "\n" in value or "\r" in value:
            raise AuthoringReceiptError(f"receipt field is not one nonempty line: {key}")
    return ("".join(f"{key}: {receipt[key]}\n" for key in RECEIPT_KEYS)).encode("utf-8")


def stack_report(
    *,
    blender: Path | None = None,
    fast64_root: Path | None = None,
    blender_dmg: Path | None = None,
    fast64_zip: Path | None = None,
) -> dict[str, Any]:
    lock = authoring.load_authoring_lock()
    default_blender, default_fast64 = authoring.default_paths(lock)
    return authoring.check_authoring_stack(
        blender or default_blender,
        fast64_root or default_fast64,
        blender_dmg=blender_dmg,
        fast64_zip=fast64_zip,
    )


def _create_file_at(parent_fd: int, prefix: str, payload: bytes, mode: int) -> str:
    for _attempt in range(128):
        name = f"{prefix}{secrets.token_hex(12)}"
        try:
            descriptor = os.open(name, _file_write_flags(), mode, dir_fd=parent_fd)
        except FileExistsError:
            continue
        try:
            view = memoryview(payload)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:  # pragma: no cover - POSIX write either advances or raises
                    raise OSError("receipt temporary write made no progress")
                view = view[written:]
            os.fsync(descriptor)
            os.fchmod(descriptor, mode)
        except BaseException:
            os.close(descriptor)
            os.unlink(name, dir_fd=parent_fd)
            raise
        os.close(descriptor)
        return name
    raise AuthoringReceiptError("could not allocate one unpredictable receipt temporary")


def _read_existing_at(
    parent_fd: int, name: str
) -> tuple[bytes, int, tuple[int, int]] | None:
    try:
        metadata = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(metadata.st_mode):
        raise AuthoringReceiptError("existing receipt target is not one regular file")
    descriptor = os.open(name, _file_read_flags(), dir_fd=parent_fd)
    try:
        opened = os.fstat(descriptor)
        if (metadata.st_dev, metadata.st_ino) != (opened.st_dev, opened.st_ino):
            raise AuthoringReceiptError("receipt target changed during secure preflight")
        payload = _read_all(descriptor)
        after = os.fstat(descriptor)
        if (
            (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns)
            != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
            or len(payload) != after.st_size
        ):
            raise AuthoringReceiptError("receipt target changed during secure preflight")
    finally:
        os.close(descriptor)
    return payload, stat.S_IMODE(opened.st_mode), (opened.st_dev, opened.st_ino)


def _target_matches_backup(
    parent_fd: int,
    name: str,
    backup: tuple[bytes, int, tuple[int, int]] | None,
) -> bool:
    try:
        metadata = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return backup is None
    return (
        backup is not None
        and stat.S_ISREG(metadata.st_mode)
        and (metadata.st_dev, metadata.st_ino) == backup[2]
    )


def _promoted_payload_matches(parent_fd: int, name: str, expected: bytes) -> bool:
    try:
        descriptor = os.open(name, _file_read_flags(), dir_fd=parent_fd)
    except OSError:
        return False
    try:
        metadata = os.fstat(descriptor)
        return stat.S_ISREG(metadata.st_mode) and _read_all(descriptor) == expected
    finally:
        os.close(descriptor)


def _write_receipts_locked(
    records: Sequence[tuple[Path, bytes]],
    *,
    root: Path,
    replace: bool,
    transaction: ReceiptTransaction,
    before_promote: Callable[[int, Path], None] | None,
) -> None:
    absolute_root = _absolute_root(root)
    root_fd = _open_root_fd(absolute_root)
    prepared: list[dict[str, object]] = []
    promoted: list[dict[str, object]] = []
    try:
        _assert_transaction(transaction, root_fd)
        relative_records = [
            (_safe_relative(path, absolute_root, "receipt path"), payload)
            for path, payload in records
        ]
        folded = [str(relative).lower() for relative, _payload in relative_records]
        if not relative_records or len(set(folded)) != len(folded):
            raise AuthoringReceiptError("paired receipt targets are empty or duplicated")
        for relative, payload in relative_records:
            _assert_transaction(transaction, root_fd)
            parent_parts = relative.parts[:-1]
            parent_fd = _open_directory_chain(root_fd, parent_parts, create=True)
            backup: tuple[bytes, int, tuple[int, int]] | None = None
            temporary: str | None = None
            try:
                _verify_parent_anchor(absolute_root, root_fd, parent_parts, parent_fd)
                backup = _read_existing_at(parent_fd, relative.name)
                if backup is not None and not replace:
                    raise AuthoringReceiptError(
                        "receipt already exists; pass --replace after an intentional new check"
                    )
                temporary = _create_file_at(
                    parent_fd, ".authoring-pair-receipt-", payload, 0o644
                )
                _assert_transaction(transaction, root_fd)
                prepared.append(
                    {
                        "relative": relative,
                        "payload": payload,
                        "parent_parts": parent_parts,
                        "parent_fd": parent_fd,
                        "backup": backup,
                        "temporary": temporary,
                    }
                )
            except BaseException:
                if temporary is not None:
                    try:
                        _assert_transaction(transaction, root_fd)
                        _verify_parent_anchor(
                            absolute_root, root_fd, parent_parts, parent_fd
                        )
                        os.unlink(temporary, dir_fd=parent_fd)
                    except BaseException:
                        pass
                os.close(parent_fd)
                raise
        for index, item in enumerate(prepared):
            relative = item["relative"]
            assert isinstance(relative, PurePosixPath)
            parent_fd = item["parent_fd"]
            temporary = item["temporary"]
            backup = item["backup"]
            assert isinstance(parent_fd, int) and isinstance(temporary, str)
            if before_promote is not None:
                before_promote(index, absolute_root / str(relative))
            _assert_transaction(transaction, root_fd)
            _verify_parent_anchor(
                absolute_root, root_fd, item["parent_parts"], parent_fd  # type: ignore[arg-type]
            )
            if not _target_matches_backup(parent_fd, relative.name, backup):  # type: ignore[arg-type]
                raise AuthoringReceiptError("receipt target changed before promotion")
            _assert_transaction(transaction, root_fd)
            os.replace(
                temporary,
                relative.name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
            )
            item["temporary"] = None
            promoted.append(item)
            _assert_transaction(transaction, root_fd)
            os.fsync(parent_fd)
            _assert_transaction(transaction, root_fd)
        _assert_transaction(transaction, root_fd)
    except BaseException as exc:
        rollback_errors: list[str] = []
        for item in reversed(promoted):
            relative = item["relative"]
            parent_fd = item["parent_fd"]
            payload = item["payload"]
            backup = item["backup"]
            assert isinstance(relative, PurePosixPath)
            assert isinstance(parent_fd, int) and isinstance(payload, bytes)
            try:
                _assert_transaction(transaction, root_fd)
                _verify_parent_anchor(
                    absolute_root, root_fd, item["parent_parts"], parent_fd  # type: ignore[arg-type]
                )
                if not _promoted_payload_matches(parent_fd, relative.name, payload):
                    raise AuthoringReceiptError(
                        "promoted receipt changed before rollback"
                    )
                if backup is None:
                    _assert_transaction(transaction, root_fd)
                    os.unlink(relative.name, dir_fd=parent_fd)
                else:
                    backup_payload, backup_mode, _identity = backup  # type: ignore[misc]
                    rollback_name = _create_file_at(
                        parent_fd,
                        ".authoring-pair-rollback-",
                        backup_payload,
                        backup_mode,
                    )
                    _assert_transaction(transaction, root_fd)
                    os.replace(
                        rollback_name,
                        relative.name,
                        src_dir_fd=parent_fd,
                        dst_dir_fd=parent_fd,
                    )
                os.fsync(parent_fd)
                _assert_transaction(transaction, root_fd)
            except BaseException as rollback_exc:
                rollback_errors.append(f"{relative}: {rollback_exc}")
        detail = (
            f"; rollback failures: {', '.join(rollback_errors)}"
            if rollback_errors
            else ""
        )
        raise AuthoringReceiptError(
            f"paired receipt promotion failed and was rolled back{detail}: {exc}"
        ) from exc
    finally:
        for item in prepared:
            parent_fd = item["parent_fd"]
            temporary = item["temporary"]
            assert isinstance(parent_fd, int)
            if isinstance(temporary, str):
                try:
                    _assert_transaction(transaction, root_fd)
                    _verify_parent_anchor(
                        absolute_root,
                        root_fd,
                        item["parent_parts"],  # type: ignore[arg-type]
                        parent_fd,
                    )
                    os.unlink(temporary, dir_fd=parent_fd)
                except BaseException:
                    pass
            os.close(parent_fd)
        os.close(root_fd)


def write_receipts_atomically(
    records: Sequence[tuple[Path, bytes]],
    *,
    root: Path = ROOT,
    replace: bool = False,
    transaction: ReceiptTransaction | None = None,
    before_promote: Callable[[int, Path], None] | None = None,
) -> None:
    """Install receipts with dir-FD no-follow promotion and safe rollback."""
    if transaction is None:
        with gate5_transaction_lock(root) as acquired:
            _write_receipts_locked(
                records,
                root=root,
                replace=replace,
                transaction=acquired,
                before_promote=before_promote,
            )
        return
    _write_receipts_locked(
        records,
        root=root,
        replace=replace,
        transaction=transaction,
        before_promote=before_promote,
    )


def write_receipt(path: Path, payload: bytes, *, root: Path = ROOT, replace: bool = False) -> None:
    write_receipts_atomically([(path, payload)], root=root, replace=replace)


def preflight_receipt_target(path: Path, *, root: Path = ROOT, replace: bool = False) -> None:
    absolute_root = _absolute_root(root)
    relative = _safe_relative(path, absolute_root, "receipt path")
    root_fd = _open_root_fd(absolute_root)
    current = os.dup(root_fd)
    try:
        for component in relative.parts[:-1]:
            try:
                following = os.open(component, _directory_flags(), dir_fd=current)
            except FileNotFoundError:
                return
            except OSError as exc:
                raise AuthoringReceiptError(
                    f"receipt target traverses a symlink or non-directory: {component}"
                ) from exc
            os.close(current)
            current = following
        existing = _read_existing_at(current, relative.name)
        if existing is not None and not replace:
            raise AuthoringReceiptError(
                "receipt already exists; pass --replace after an intentional new check"
            )
    finally:
        os.close(current)
        os.close(root_fd)


def export_environment(temp_root: Path) -> dict[str, str]:
    environment = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "TMPDIR": str(temp_root),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
    }
    for name in ("HOME", "N64_INST", "N64GAME_BLENDER_BINARY", "N64GAME_FAST64_ROOT"):
        value = os.environ.get(name)
        if value:
            environment[name] = value
    return environment


def run_checked_export(
    command: Sequence[str],
    *,
    check: Callable[[], Mapping[str, Any]],
    snapshot: Callable[[], object],
    transaction: ReceiptTransaction,
    run: Callable[..., subprocess.CompletedProcess[Any]] = subprocess.run,
    root: Path = ROOT,
) -> CheckedExport:
    approved_exporter_sha256 = require_approved_gate5_exporter()
    if not command or not command[0]:
        raise AuthoringReceiptError("Gate-5 exporter command is empty")
    executable = Path(command[0])
    if not executable.is_absolute():
        executable = root / executable
    expected_exporter = Path(os.path.abspath(root / CANONICAL_GATE5_EXPORTER_PATH))
    executable = Path(os.path.abspath(executable))
    if executable != expected_exporter:
        raise AuthoringReceiptError(
            f"Gate-5 export is locked to reviewed {CANONICAL_GATE5_EXPORTER_PATH}"
        )
    require_repo_regular(executable, "Gate-5 exporter executable", root)
    if not os.access(executable, os.X_OK):
        raise AuthoringReceiptError("Gate-5 exporter is not executable")
    if sha256_file(executable) != approved_exporter_sha256:
        raise AuthoringReceiptError("Gate-5 exporter differs from the exact reviewed SHA-256")
    root_fd = _open_root_fd(root)
    try:
        _assert_transaction(transaction, root_fd)
    finally:
        os.close(root_fd)
    before = portable_stack_identity(check(), root)
    _assert_lock_namespace(transaction)
    with tempfile.TemporaryDirectory(prefix="n64game-authoring-export-") as temporary:
        environment = export_environment(Path(temporary))
        environment["N64GAME_GATE5_LOCK_FD"] = str(transaction.lock_fd)
        completed = run(
            [str(executable), *command[1:]],
            cwd=root,
            env=environment,
            pass_fds=(transaction.lock_fd,),
            check=False,
        )
        _assert_lock_namespace(transaction)
    if completed.returncode != 0:
        raise AuthoringReceiptError(f"Gate-5 exporter exited {completed.returncode}")
    _assert_lock_namespace(transaction)
    post_export_snapshot = snapshot()
    _assert_lock_namespace(transaction)
    try:
        hash(post_export_snapshot)
    except TypeError as exc:
        raise AuthoringReceiptError("Gate-5 snapshot is not one immutable value") from exc
    _assert_lock_namespace(transaction)
    after = portable_stack_identity(check(), root)
    _assert_lock_namespace(transaction)
    if before != after:
        raise AuthoringReceiptError("authoring stack identity changed during Gate-5 export")
    _assert_lock_namespace(transaction)
    postcheck_snapshot = snapshot()
    _assert_lock_namespace(transaction)
    try:
        hash(postcheck_snapshot)
    except TypeError as exc:
        raise AuthoringReceiptError("Gate-5 postcheck snapshot is not one immutable value") from exc
    if postcheck_snapshot != post_export_snapshot:
        raise AuthoringReceiptError("Gate-5 source/output identity changed during the post-export stack check")
    _assert_lock_namespace(transaction)
    return CheckedExport(tuple(after.items()), postcheck_snapshot)


def add_stack_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--blender", type=Path)
    parser.add_argument("--fast64-root", type=Path)
    parser.add_argument("--blender-dmg", type=Path)
    parser.add_argument("--fast64-zip", type=Path)
    parser.add_argument("--replace", action="store_true")


def gate5_exporter_command(scope_id: str, build_id: str, exporter_args: Sequence[str]) -> list[str]:
    """Inject receipt authority and expose only the reviewed deterministic switch."""
    if scope_id not in {"echo.quarrune", "anm.echo.quarrune"}:
        raise AuthoringReceiptError("Gate-5 exporter is limited to the exact Quarrune scope pair")
    if list(exporter_args) != ["--deterministic"]:
        raise AuthoringReceiptError(
            "Gate-5 exporter arguments must be exactly '--deterministic'; scope/build are injected"
        )
    return [
        str(ROOT / CANONICAL_GATE5_EXPORTER_PATH),
        "--scope",
        "echo.quarrune",
        "--paired-scope",
        "anm.echo.quarrune",
        "--build-id",
        build_id,
        "--deterministic",
    ]


def gate5_pair_exporter_command(
    scope_id: str, paired_scope_id: str, build_id: str, *, replace: bool
) -> list[str]:
    """Build the sole production command vector for the Quarrune owner pair."""
    if scope_id != "echo.quarrune" or paired_scope_id != "anm.echo.quarrune":
        raise AuthoringReceiptError(
            "paired Gate-5 receipt accepts only echo.quarrune + anm.echo.quarrune"
        )
    if not replace:
        raise AuthoringReceiptError(
            "paired Gate-5 receipt requires --replace after candidate outputs are reviewed and bound"
        )
    command = [
        str(ROOT / CANONICAL_GATE5_EXPORTER_PATH),
        "--scope", scope_id,
        "--paired-scope", paired_scope_id,
        "--build-id", build_id,
        "--deterministic",
    ]
    command.append("--replace")
    return command


def run_gate5_pair(args: argparse.Namespace) -> int:
    if not canonical_build_id(args.build_id):
        raise AuthoringReceiptError("G5 requires one substantive clean-build ID before export")
    scopes = (args.scope, args.paired_scope)
    command = gate5_pair_exporter_command(
        args.scope, args.paired_scope, args.build_id, replace=args.replace
    )
    with gate5_transaction_lock(ROOT) as transaction:
        _assert_lock_namespace(transaction)
        require_approved_gate5_exporter()
        destinations = tuple(canonical_receipt_path(scope, "G5") for scope in scopes)
        for destination in destinations:
            _assert_lock_namespace(transaction)
            preflight_receipt_target(destination, replace=args.replace)
        _assert_lock_namespace(transaction)
        source_paths = tuple(canonical_source_manifest(scope) for scope in scopes)
        output_paths = tuple(canonical_output_manifest(scope) for scope in scopes)
        _assert_lock_namespace(transaction)
        source_before = _capture_manifest_closure(ROOT, source_paths)
        _assert_lock_namespace(transaction)
        check = lambda: stack_report(
            blender=args.blender,
            fast64_root=args.fast64_root,
            blender_dmg=args.blender_dmg,
            fast64_zip=args.fast64_zip,
        )

        def pair_snapshot() -> Gate5PairSnapshot:
            _assert_lock_namespace(transaction)
            observed = capture_gate5_pair_snapshot(
                source_paths,
                output_paths,
                build_id=args.build_id,
            )
            _assert_lock_namespace(transaction)
            if observed.source != source_before:
                raise AuthoringReceiptError(
                    "source manifest closure changed during paired Gate-5 export"
                )
            return observed

        checked = run_checked_export(
            command,
            check=check,
            snapshot=pair_snapshot,
            transaction=transaction,
        )
        _assert_lock_namespace(transaction)
        if not isinstance(checked.snapshot, Gate5PairSnapshot):
            raise AuthoringReceiptError(
                "paired Gate-5 export returned the wrong verified snapshot type"
            )
        checked_at = canonical_checked_at()
        records: list[tuple[Path, bytes]] = []
        for scope, source_path, output_path, destination in zip(
            scopes, source_paths, output_paths, destinations
        ):
            record = build_receipt(
                scope_id=scope,
                gate="G5",
                source_manifest_sha256=checked.snapshot.source_manifest_sha256(
                    source_path, root=ROOT
                ),
                output_manifest_sha256=checked.snapshot.output_manifest_sha256(
                    output_path, root=ROOT
                ),
                build_id=args.build_id,
                checked_at=checked_at,
                stack_identity=dict(checked.stack_identity),
            )
            records.append((destination, render_receipt(record)))
        if pair_snapshot() != checked.snapshot:
            raise AuthoringReceiptError(
                "Gate-5 source/output closure changed before receipt promotion"
            )
        write_receipts_atomically(
            records,
            replace=args.replace,
            transaction=transaction,
        )
        _assert_lock_namespace(transaction)
    print("authoring_receipt=PASS " + ",".join(str(path) for path in destinations))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Produce exact per-asset authoring-stack receipts.")
    subparsers = parser.add_subparsers(dest="operation", required=True)
    gate2 = subparsers.add_parser("g2", help="check the stack and record a Gate-2 source receipt")
    gate2.add_argument("--scope", required=True)
    add_stack_arguments(gate2)
    gate5 = subparsers.add_parser("g5-export", help="wrap conversion with pre/post checks and record Gate 5")
    gate5.add_argument("--scope", required=True)
    gate5.add_argument("--build-id", required=True)
    add_stack_arguments(gate5)
    gate5.add_argument(
        "exporter_args",
        nargs=argparse.REMAINDER,
        help=f"arguments passed only to {CANONICAL_GATE5_EXPORTER_PATH}",
    )
    gate5_pair = subparsers.add_parser(
        "g5-export-pair",
        help="atomically export and receipt the paired Quarrune model/animation package",
    )
    gate5_pair.add_argument("--scope", required=True)
    gate5_pair.add_argument("--paired-scope", required=True)
    gate5_pair.add_argument("--build-id", required=True)
    add_stack_arguments(gate5_pair)
    args = parser.parse_args(argv)
    try:
        if args.operation == "g5-export-pair":
            return run_gate5_pair(args)
        gate = "G2" if args.operation == "g2" else "G5"
        destination = canonical_receipt_path(args.scope, gate)
        preflight_receipt_target(destination, replace=args.replace)
        if gate == "G5" and not canonical_build_id(args.build_id):
            raise AuthoringReceiptError("G5 requires one substantive clean-build ID before export")
        if args.operation == "g5-export":
            raise AuthoringReceiptError(
                "single-scope Gate-5 export is disabled; use g5-export-pair for the Quarrune owner pair"
            )
        source_path = canonical_source_manifest(args.scope)
        require_repo_regular(source_path, "source manifest")
        source_digest = sha256_file(source_path)
        check = lambda: stack_report(
            blender=args.blender,
            fast64_root=args.fast64_root,
            blender_dmg=args.blender_dmg,
            fast64_zip=args.fast64_zip,
        )
        identity = portable_stack_identity(check())
        output_digest = "NONE"
        build_id = "-"
        receipt = build_receipt(
            scope_id=args.scope,
            gate=gate,
            source_manifest_sha256=source_digest,
            output_manifest_sha256=output_digest,
            build_id=build_id,
            checked_at=canonical_checked_at(),
            stack_identity=identity,
        )
        write_receipt(destination, render_receipt(receipt), replace=args.replace)
    except (AuthoringReceiptError, authoring.AuthoringContractError, OSError, ValueError) as exc:
        print(f"authoring_receipt=FAIL {exc}", file=sys.stderr)
        return 1
    print(f"authoring_receipt=PASS {destination.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
