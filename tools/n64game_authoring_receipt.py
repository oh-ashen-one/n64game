#!/usr/bin/env python3
"""Produce asset-bound Blender/Fast64 receipts for Gate 2 and Gate 5.

The repository validator remains the authority for accepting these records. This
producer refuses to write a receipt unless the exact authoring stack passes. A
Gate-5 export is wrapped by checks both before and after the exporter command.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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


class AuthoringReceiptError(RuntimeError):
    """Raised when a receipt cannot truthfully be produced."""


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


def write_receipt(path: Path, payload: bytes, *, root: Path = ROOT, replace: bool = False) -> None:
    root = Path(os.path.abspath(root))
    path = Path(os.path.abspath(path))
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise AuthoringReceiptError("receipt path escapes the repository root") from exc
    parent = root
    for component in relative.parent.parts:
        parent = parent / component
        if parent.exists() and parent.is_symlink():
            raise AuthoringReceiptError(f"receipt parent traverses a symlink: {parent}")
        parent.mkdir(exist_ok=True)
    if path.exists() and (path.is_symlink() or not path.is_file()):
        raise AuthoringReceiptError("existing receipt target is not one regular file")
    if path.exists() and not replace:
        raise AuthoringReceiptError("receipt already exists; pass --replace after an intentional new check")
    temporary: Path | None = None
    try:
        descriptor, name = tempfile.mkstemp(prefix=".authoring-receipt-", dir=path.parent)
        temporary = Path(name)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def write_receipts_atomically(
    records: Sequence[tuple[Path, bytes]],
    *,
    root: Path = ROOT,
    replace: bool = False,
    replace_func: Callable[[os.PathLike[str] | str, os.PathLike[str] | str], None] = os.replace,
) -> None:
    """Install multiple owner receipts with rollback on any promotion failure."""
    if not records or len({Path(path) for path, _payload in records}) != len(records):
        raise AuthoringReceiptError("paired receipt targets are empty or duplicated")
    for path, _payload in records:
        preflight_receipt_target(path, root=root, replace=replace)
    prepared: dict[Path, Path] = {}
    backups: dict[Path, tuple[bytes, int] | None] = {}
    promoted: list[Path] = []
    try:
        for path, payload in records:
            destination = Path(os.path.abspath(path))
            destination.parent.mkdir(parents=True, exist_ok=True)
            backups[destination] = (
                (destination.read_bytes(), destination.stat().st_mode & 0o777)
                if destination.exists() else None
            )
            descriptor, name = tempfile.mkstemp(prefix=".authoring-pair-receipt-", dir=destination.parent)
            temporary = Path(name)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary, 0o644)
            prepared[destination] = temporary
        for destination, _payload in records:
            destination = Path(os.path.abspath(destination))
            replace_func(prepared[destination], destination)
            prepared.pop(destination, None)
            promoted.append(destination)
    except BaseException as exc:
        rollback_errors: list[str] = []
        for destination in reversed(promoted):
            backup = backups[destination]
            try:
                if backup is None:
                    destination.unlink(missing_ok=True)
                else:
                    descriptor, name = tempfile.mkstemp(
                        prefix=".authoring-pair-rollback-", dir=destination.parent
                    )
                    temporary = Path(name)
                    with os.fdopen(descriptor, "wb") as handle:
                        handle.write(backup[0])
                        handle.flush()
                        os.fsync(handle.fileno())
                    os.chmod(temporary, backup[1])
                    replace_func(temporary, destination)
            except BaseException as rollback_exc:  # pragma: no cover - catastrophic host failure
                rollback_errors.append(f"{destination}: {rollback_exc}")
        detail = f"; rollback failures: {', '.join(rollback_errors)}" if rollback_errors else ""
        raise AuthoringReceiptError(f"paired receipt promotion failed and was rolled back{detail}: {exc}") from exc
    finally:
        for temporary in prepared.values():
            temporary.unlink(missing_ok=True)


def preflight_receipt_target(path: Path, *, root: Path = ROOT, replace: bool = False) -> None:
    root = Path(os.path.abspath(root))
    path = Path(os.path.abspath(path))
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise AuthoringReceiptError("receipt path escapes the repository root") from exc
    current = root
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise AuthoringReceiptError(f"receipt target traverses a symlink: {current}")
        if not current.exists():
            break
    if path.exists() and not path.is_file():
        raise AuthoringReceiptError("existing receipt target is not one regular file")
    if path.exists() and not replace:
        raise AuthoringReceiptError("receipt already exists; pass --replace after an intentional new check")


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
    run: Callable[..., subprocess.CompletedProcess[Any]] = subprocess.run,
    snapshot: Callable[[], object] | None = None,
    root: Path = ROOT,
) -> dict[str, str]:
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
    before = portable_stack_identity(check(), root)
    with tempfile.TemporaryDirectory(prefix="n64game-authoring-export-") as temporary:
        completed = run(
            [str(executable), *command[1:]],
            cwd=root,
            env=export_environment(Path(temporary)),
            check=False,
        )
    if completed.returncode != 0:
        raise AuthoringReceiptError(f"Gate-5 exporter exited {completed.returncode}")
    post_export_snapshot = snapshot() if snapshot is not None else None
    after = portable_stack_identity(check(), root)
    if before != after:
        raise AuthoringReceiptError("authoring stack identity changed during Gate-5 export")
    if snapshot is not None and snapshot() != post_export_snapshot:
        raise AuthoringReceiptError("Gate-5 source/output identity changed during the post-export stack check")
    return after


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
            if not canonical_build_id(args.build_id):
                raise AuthoringReceiptError("G5 requires one substantive clean-build ID before export")
            require_approved_gate5_exporter()
            scopes = (args.scope, args.paired_scope)
            destinations = tuple(canonical_receipt_path(scope, "G5") for scope in scopes)
            for destination in destinations:
                preflight_receipt_target(destination, replace=args.replace)
            source_paths = tuple(canonical_source_manifest(scope) for scope in scopes)
            for source_path in source_paths:
                require_repo_regular(source_path, "source manifest")
            source_digests = tuple(sha256_file(path) for path in source_paths)
            output_paths = tuple(canonical_output_manifest(scope) for scope in scopes)
            check = lambda: stack_report(
                blender=args.blender,
                fast64_root=args.fast64_root,
                blender_dmg=args.blender_dmg,
                fast64_zip=args.fast64_zip,
            )
            command = gate5_pair_exporter_command(
                args.scope, args.paired_scope, args.build_id, replace=args.replace
            )

            def pair_snapshot() -> tuple[tuple[str, str], ...]:
                observed: list[tuple[str, str]] = []
                for source_path, expected_digest in zip(source_paths, source_digests):
                    require_repo_regular(source_path, "source manifest")
                    digest = sha256_file(source_path)
                    if digest != expected_digest:
                        raise AuthoringReceiptError("source manifest changed during paired Gate-5 export")
                    observed.append((str(source_path), digest))
                for output_path in output_paths:
                    require_repo_regular(output_path, "Gate-5 output manifest")
                    observed.append((str(output_path), sha256_file(output_path)))
                return tuple(observed)

            identity = run_checked_export(command, check=check, snapshot=pair_snapshot)
            checked_at = canonical_checked_at()
            records: list[tuple[Path, bytes]] = []
            for scope, source_digest, output_path, destination in zip(
                scopes, source_digests, output_paths, destinations
            ):
                record = build_receipt(
                    scope_id=scope,
                    gate="G5",
                    source_manifest_sha256=source_digest,
                    output_manifest_sha256=sha256_file(output_path),
                    build_id=args.build_id,
                    checked_at=checked_at,
                    stack_identity=identity,
                )
                records.append((destination, render_receipt(record)))
            write_receipts_atomically(records, replace=args.replace)
            print(
                "authoring_receipt=PASS "
                + ",".join(str(path) for path in destinations)
            )
            return 0
        gate = "G2" if args.operation == "g2" else "G5"
        destination = canonical_receipt_path(args.scope, gate)
        preflight_receipt_target(destination, replace=args.replace)
        if gate == "G5" and not canonical_build_id(args.build_id):
            raise AuthoringReceiptError("G5 requires one substantive clean-build ID before export")
        if args.operation == "g5-export":
            raise AuthoringReceiptError(
                "single-scope Gate-5 export is disabled; use g5-export-pair for the Quarrune owner pair"
            )
        if gate == "G5":
            require_approved_gate5_exporter()
        source_path = canonical_source_manifest(args.scope)
        require_repo_regular(source_path, "source manifest")
        source_digest = sha256_file(source_path)
        check = lambda: stack_report(
            blender=args.blender,
            fast64_root=args.fast64_root,
            blender_dmg=args.blender_dmg,
            fast64_zip=args.fast64_zip,
        )
        if args.operation == "g2":
            identity = portable_stack_identity(check())
            output_digest = "NONE"
            build_id = "-"
        else:
            exporter_args = list(args.exporter_args)
            if exporter_args[:1] == ["--"]:
                exporter_args = exporter_args[1:]
            command = gate5_exporter_command(args.scope, args.build_id, exporter_args)
            output_path = canonical_output_manifest(args.scope)
            def export_snapshot() -> tuple[str, str]:
                require_repo_regular(source_path, "source manifest")
                require_repo_regular(output_path, "Gate-5 output manifest")
                observed_source = sha256_file(source_path)
                if observed_source != source_digest:
                    raise AuthoringReceiptError("source manifest changed during Gate-5 export")
                return observed_source, sha256_file(output_path)

            identity = run_checked_export(command, check=check, snapshot=export_snapshot)
            output_digest = sha256_file(output_path)
            build_id = args.build_id
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
