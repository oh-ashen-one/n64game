#!/usr/bin/env python3
"""Fail-closed, observational checks for the Gate 4 macOS authoring stack."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "config" / "toolchain.lock.json"
PROBE_SENTINEL = "N64GAME_AUTHORING_JSON="

EXPECTED_BLENDER_PIN: dict[str, Any] = {
    "version": "4.5.11 LTS",
    "version_tuple": [4, 5, 11],
    "build_hash": "4db51e9d1e1e",
    "build_platform": "Darwin",
    "release_asset_url": "https://download.blender.org/release/Blender4.5/blender-4.5.11-macos-arm64.dmg",
    "release_asset_size": 308255028,
    "release_asset_sha256": "1fad76c7da9451c7d6db99f1a5ed3c0a1a461d0aa07bf2b639e2fb4804ca4f13",
    "executable_size": 175667888,
    "executable_sha256": "8156431a9b9ec1daf49bccea4bd92f327f6efc1ca330d5103881580f3e7773ef",
    "bundle_identifier": "org.blenderfoundation.blender",
    "codesign_team_identifier": "68UA947AUU",
    "macos_user_relative_path": "Applications/Blender-4.5.11.app/Contents/MacOS/Blender",
}

EXPECTED_FAST64_PIN: dict[str, Any] = {
    "version": "2.5.3",
    "tag": "v2.5.3",
    "commit": "8e9630c11824a9c00e9379279d43c64264eda87e",
    "repository": "https://github.com/Fast-64/fast64.git",
    "release_url": "https://github.com/Fast-64/fast64/releases/tag/v2.5.3",
    "release_asset_url": "https://github.com/Fast-64/fast64/releases/download/v2.5.3/fast64-v2.5.3.zip",
    "release_asset_size": 1882004,
    "release_asset_sha256": "2a308e04ee591e328856e8dff5bbe5aa72f284873e874ba5aba5927831889010",
    "blender_user_relative_path": "Library/Application Support/Blender/4.5/scripts/addons/fast64",
    "source_tree_file_count": 226,
    "source_tree_size": 10387545,
    "source_tree_manifest_sha256": "14bb6c7b527ba364fa5e2a5011779ddd24c61f998c79c120f28d895d92e62e6b",
    "source_tree_manifest_algorithm": "sha256-size-path-v1",
    "source_tree_exclusions": [],
}

CODESIGN = "/usr/bin/codesign"
SYSTEM_TOOL_ENV = {
    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    "LANG": "C",
    "LC_ALL": "C",
}


class AuthoringContractError(RuntimeError):
    """Raised when an authoring dependency differs from the locked contract."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require_regular_file(path: Path, label: str) -> None:
    if not path.is_file() or path.is_symlink():
        raise AuthoringContractError(f"{label} is not one regular, non-symlink file: {path}")


def load_authoring_lock(path: Path = LOCK_PATH) -> dict[str, Any]:
    try:
        lock = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AuthoringContractError(f"cannot read authoring lock from {path}: {exc}") from exc
    if lock.get("schema_version") != 1:
        raise AuthoringContractError("unsupported toolchain lock schema")
    authoring = lock.get("authoring")
    if not isinstance(authoring, dict):
        raise AuthoringContractError("toolchain lock has no authoring object")
    blender = authoring.get("blender_macos_arm64")
    fast64 = authoring.get("fast64")
    if blender != EXPECTED_BLENDER_PIN:
        raise AuthoringContractError("Blender authoring pin differs from the approved 4.5.11 LTS macOS ARM64 contract")
    if fast64 != EXPECTED_FAST64_PIN:
        raise AuthoringContractError("Fast64 authoring pin differs from the approved v2.5.3 release contract")
    if authoring.get("blender_target") != blender["version"]:
        raise AuthoringContractError("legacy Blender target alias differs from the exact Blender pin")
    if authoring.get("fast64_version") != fast64["version"]:
        raise AuthoringContractError("legacy Fast64 version alias differs from the exact Fast64 pin")
    if authoring.get("fast64_commit") != fast64["commit"]:
        raise AuthoringContractError("legacy Fast64 commit alias differs from the exact Fast64 pin")
    return authoring


def verify_distribution_asset(path: Path, pin: Mapping[str, Any], label: str) -> dict[str, Any]:
    _require_regular_file(path, label)
    size = path.stat().st_size
    if size != pin["release_asset_size"]:
        raise AuthoringContractError(
            f"{label} size is {size}, expected {pin['release_asset_size']} bytes"
        )
    digest = sha256_file(path)
    if digest != pin["release_asset_sha256"]:
        raise AuthoringContractError(
            f"{label} SHA-256 is {digest}, expected {pin['release_asset_sha256']}"
        )
    return {
        "status": "PASS",
        "path": str(path),
        "size_bytes": size,
        "sha256": digest,
        "official_url": pin["release_asset_url"],
    }


def parse_blender_version(output: str, pin: Mapping[str, Any]) -> dict[str, Any]:
    lines = output.splitlines()
    expected_first_line = f"Blender {pin['version']}"
    if not lines or lines[0] != expected_first_line:
        observed = lines[0] if lines else "no version output"
        raise AuthoringContractError(
            f"Blender version is {observed!r}; Gate 4 requires {expected_first_line!r} (Blender 5.2 is not accepted)"
        )
    fields: dict[str, str] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            fields[key] = value.strip()
    if fields.get("build hash") != pin["build_hash"]:
        raise AuthoringContractError(
            f"Blender build hash is {fields.get('build hash')!r}, expected {pin['build_hash']!r}"
        )
    if fields.get("build platform") != pin["build_platform"]:
        raise AuthoringContractError(
            f"Blender build platform is {fields.get('build platform')!r}, expected {pin['build_platform']!r}"
        )
    return {
        "version": pin["version"],
        "build_hash": fields["build hash"],
        "build_platform": fields["build platform"],
    }


def _run(command: list[str], *, timeout: int = 45, env: Mapping[str, str] | None = None) -> str:
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
            env=None if env is None else dict(env),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AuthoringContractError(f"command failed: {' '.join(command)}: {exc}") from exc
    if result.returncode != 0:
        raise AuthoringContractError(
            f"command failed ({result.returncode}): {' '.join(command)}: {result.stdout.strip()}"
        )
    return result.stdout


def _codesign_identity(app_path: Path, pin: Mapping[str, Any]) -> dict[str, Any]:
    requirement = (
        "=anchor apple generic and "
        f'certificate leaf[subject.OU] = "{pin["codesign_team_identifier"]}" and '
        f'identifier "{pin["bundle_identifier"]}"'
    )
    _run(
        [
            CODESIGN,
            "--verify",
            "--deep",
            "--strict",
            "--verbose=4",
            "-R",
            requirement,
            str(app_path),
        ],
        env=SYSTEM_TOOL_ENV,
    )
    output = _run([CODESIGN, "-dv", "--verbose=4", str(app_path)], env=SYSTEM_TOOL_ENV)
    fields: dict[str, str] = {}
    for line in output.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            fields[key] = value
    if fields.get("Identifier") != pin["bundle_identifier"]:
        raise AuthoringContractError("Blender bundle identifier differs from the official pin")
    if fields.get("TeamIdentifier") != pin["codesign_team_identifier"]:
        raise AuthoringContractError("Blender code-signing team differs from the official pin")
    expected_authority = (
        "Developer ID Application: Stichting Blender Foundation "
        f"({pin['codesign_team_identifier']})"
    )
    if expected_authority not in output:
        raise AuthoringContractError("Blender app is not signed by the locked Blender Foundation identity")
    return {
        "bundle_identifier": fields["Identifier"],
        "team_identifier": fields["TeamIdentifier"],
        "authority": expected_authority,
        "deep_strict_verified": True,
        "designated_requirement": requirement,
    }


def isolated_blender_environment(temp_root: Path, fast64_root: Path) -> dict[str, str]:
    paths = {
        "HOME": temp_root / "home",
        "TMPDIR": temp_root / "tmp",
        "PYTHONPYCACHEPREFIX": temp_root / "pycache",
        "BLENDER_USER_CONFIG": temp_root / "config",
        "BLENDER_USER_DATAFILES": temp_root / "datafiles",
        "BLENDER_USER_EXTENSIONS": temp_root / "extensions",
        "BLENDER_USER_CACHE": temp_root / "cache",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    scripts_root = fast64_root.parents[1]
    return {
        **SYSTEM_TOOL_ENV,
        **{key: str(value) for key, value in paths.items()},
        "BLENDER_USER_SCRIPTS": str(scripts_root),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
    }


def verify_blender_binary(path: Path, pin: Mapping[str, Any]) -> dict[str, Any]:
    _require_regular_file(path, "Blender executable")
    size = path.stat().st_size
    if size != pin["executable_size"]:
        raise AuthoringContractError(
            f"Blender executable size is {size}, expected {pin['executable_size']} bytes"
        )
    digest = sha256_file(path)
    if digest != pin["executable_sha256"]:
        raise AuthoringContractError(
            f"Blender executable SHA-256 is {digest}, expected {pin['executable_sha256']}"
        )
    with path.open("rb") as handle:
        macho_identity = handle.read(8)
    if macho_identity != bytes.fromhex("cffaedfe0c000001"):
        raise AuthoringContractError("Blender executable is not the locked thin ARM64 Mach-O build")

    app_path = path.parents[2]
    info_path = app_path / "Contents" / "Info.plist"
    _require_regular_file(info_path, "Blender Info.plist")
    with info_path.open("rb") as handle:
        info = plistlib.load(handle)
    if info.get("CFBundleShortVersionString") != "4.5.11":
        raise AuthoringContractError("Blender app bundle version is not exactly 4.5.11")
    if info.get("CFBundleIdentifier") != pin["bundle_identifier"]:
        raise AuthoringContractError("Blender Info.plist bundle identifier differs from the lock")
    signature = _codesign_identity(app_path, pin)
    with tempfile.TemporaryDirectory(prefix="n64game-blender-version-") as temp_dir:
        version_env = isolated_blender_environment(Path(temp_dir), Path(temp_dir) / "scripts" / "addons" / "fast64")
        version = parse_blender_version(_run([str(path), "--version"], timeout=20, env=version_env), pin)
    return {
        "status": "PASS",
        "path": str(path),
        "size_bytes": size,
        "sha256": digest,
        "architecture": "arm64",
        **version,
        "codesign": signature,
    }


def _fast64_source_files(root: Path) -> list[Path]:
    if not root.is_dir() or root.is_symlink():
        raise AuthoringContractError(f"Fast64 root is not one regular, non-symlink directory: {root}")
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_symlink():
            raise AuthoringContractError(f"Fast64 installation contains a symlink: {relative.as_posix()}")
        if "__pycache__" in relative.parts or path.suffix == ".pyc":
            raise AuthoringContractError(f"Fast64 installation contains forbidden executable bytecode/cache state: {relative.as_posix()}")
        if relative.as_posix() == "fast64_updater/fast64_updater_status.json":
            raise AuthoringContractError("Fast64 installation contains forbidden mutable updater state")
        if path.is_dir():
            continue
        if not path.is_file():
            raise AuthoringContractError(f"Fast64 installation contains a non-regular entry: {relative.as_posix()}")
        files.append(path)
    return files


def fast64_source_identity(root: Path) -> dict[str, Any]:
    files = _fast64_source_files(root)
    manifest = hashlib.sha256()
    total_size = 0
    for path in files:
        relative = path.relative_to(root).as_posix()
        size = path.stat().st_size
        digest = sha256_file(path)
        manifest.update(f"{digest}  {size}  {relative}\n".encode("utf-8"))
        total_size += size
    return {
        "file_count": len(files),
        "size_bytes": total_size,
        "manifest_sha256": manifest.hexdigest(),
        "manifest_algorithm": "sha256-size-path-v1",
    }


def expected_fast64_source_identity(pin: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "file_count": pin["source_tree_file_count"],
        "size_bytes": pin["source_tree_size"],
        "manifest_sha256": pin["source_tree_manifest_sha256"],
        "manifest_algorithm": pin["source_tree_manifest_algorithm"],
    }


def _fast64_version(root: Path) -> list[int]:
    init_path = root / "__init__.py"
    _require_regular_file(init_path, "Fast64 __init__.py")
    try:
        module = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise AuthoringContractError(f"cannot parse Fast64 metadata: {exc}") from exc
    for node in module.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "bl_info" for target in node.targets
        ):
            try:
                info = ast.literal_eval(node.value)
                version = info["version"]
            except (ValueError, TypeError, KeyError) as exc:
                raise AuthoringContractError("Fast64 bl_info version is not a literal tuple") from exc
            if not isinstance(version, tuple) or not all(isinstance(item, int) for item in version):
                raise AuthoringContractError("Fast64 bl_info version is not an integer tuple")
            return list(version)
    raise AuthoringContractError("Fast64 bl_info metadata is missing")


def verify_fast64_source(root: Path, pin: Mapping[str, Any]) -> dict[str, Any]:
    expected_version = [int(part) for part in pin["version"].split(".")]
    observed_version = _fast64_version(root)
    if observed_version != expected_version:
        raise AuthoringContractError(
            f"Fast64 version is {observed_version}, expected {expected_version}"
        )
    identity = fast64_source_identity(root)
    expected_identity = expected_fast64_source_identity(pin)
    if identity != expected_identity:
        raise AuthoringContractError(
            "Fast64 source tree differs from the exact v2.5.3 release extraction: "
            f"observed={json.dumps(identity, sort_keys=True)} "
            f"expected={json.dumps(expected_identity, sort_keys=True)}"
        )
    return {
        "status": "PASS",
        "path": str(root),
        "version": pin["version"],
        "commit_pin": pin["commit"],
        **identity,
    }


def parse_probe_output(output: str, blender_pin: Mapping[str, Any], fast64_pin: Mapping[str, Any], root: Path) -> dict[str, Any]:
    payloads = [
        line[len(PROBE_SENTINEL) :]
        for line in output.splitlines()
        if line.startswith(PROBE_SENTINEL)
    ]
    if len(payloads) != 1:
        raise AuthoringContractError("Blender Fast64 probe did not emit exactly one audit record")
    try:
        payload = json.loads(payloads[0])
    except json.JSONDecodeError as exc:
        raise AuthoringContractError(f"Blender Fast64 probe emitted invalid JSON: {exc}") from exc
    expected_module_path = str((root / "__init__.py").resolve())
    checks = {
        "Blender version": payload.get("blender") == blender_pin["version_tuple"],
        "Fast64 version": payload.get("version") == [int(part) for part in fast64_pin["version"].split(".")],
        "Fast64 preference enabled": payload.get("enabled") is True,
        "Fast64 default enabled": payload.get("default_enabled") is True,
        "Fast64 module loaded": payload.get("loaded") is True,
        "Fast64 module name": payload.get("module") == "fast64",
        "Fast64 module path": payload.get("module_file") == expected_module_path,
    }
    failed = [label for label, passed in checks.items() if not passed]
    if failed:
        raise AuthoringContractError(
            "Blender/Fast64 enabled-state probe failed: " + ", ".join(failed)
        )
    return payload


def _snapshot_file(path: Path) -> dict[str, Any]:
    _require_regular_file(path, "observed state file")
    stat = path.stat()
    return {
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": sha256_file(path),
    }


def _snapshot_tree(root: Path) -> list[tuple[str, int, int, str]]:
    if not root.is_dir() or root.is_symlink():
        raise AuthoringContractError(f"cannot snapshot non-directory authoring root: {root}")
    rows: list[tuple[str, int, int, str]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise AuthoringContractError(f"authoring root contains a symlink: {relative}")
        if path.is_file():
            stat = path.stat()
            rows.append((relative, stat.st_size, stat.st_mtime_ns, sha256_file(path)))
        elif not path.is_dir():
            raise AuthoringContractError(f"authoring root contains a non-regular entry: {relative}")
    return rows


def _snapshot_tree_metadata(root: Path) -> list[tuple[str, str, int, int]]:
    if not root.is_dir() or root.is_symlink():
        raise AuthoringContractError(f"cannot snapshot non-directory app root: {root}")
    rows: list[tuple[str, str, int, int]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        stat = path.lstat()
        if path.is_symlink():
            rows.append((relative, f"symlink:{os.readlink(path)}", stat.st_size, stat.st_mtime_ns))
        elif path.is_file():
            rows.append((relative, "file", stat.st_size, stat.st_mtime_ns))
        elif path.is_dir():
            rows.append((relative, "directory", stat.st_size, stat.st_mtime_ns))
        else:
            raise AuthoringContractError(f"app root contains a non-regular entry: {relative}")
    return rows


def probe_fast64_enabled(blender: Path, root: Path, blender_pin: Mapping[str, Any], fast64_pin: Mapping[str, Any]) -> dict[str, Any]:
    preference_path = root.parents[2] / "config" / "userpref.blend"
    app_path = blender.parents[2]
    expected_identity = expected_fast64_source_identity(fast64_pin)
    if fast64_source_identity(root) != expected_identity:
        raise AuthoringContractError("live Fast64 source changed before the isolated enabled-state probe")
    before_preference = _snapshot_file(preference_path)
    before_tree = _snapshot_tree(root)
    before_app = _snapshot_tree_metadata(app_path)
    with tempfile.TemporaryDirectory(prefix="n64game-blender-probe-") as temp_dir:
        temp_root = Path(temp_dir)
        isolated_root = temp_root / "scripts" / "addons" / "fast64"
        isolated_root.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(root, isolated_root)
        if fast64_source_identity(isolated_root) != expected_identity:
            raise AuthoringContractError("isolated Fast64 execution copy differs from the exact source pin")
        environment = isolated_blender_environment(temp_root, isolated_root)
        isolated_preference = Path(environment["BLENDER_USER_CONFIG"]) / "userpref.blend"
        shutil.copy2(preference_path, isolated_preference)
        expression = (
            "import sys;"
            "sys.dont_write_bytecode=True;"
            f"sys.pycache_prefix={str(temp_root / 'pycache')!r};"
            "import addon_utils,bpy,json;"
            "bpy.ops.wm.read_userpref();"
            "import fast64;"
            "p=bpy.context.preferences.addons.get('fast64');"
            "d,l=addon_utils.check('fast64');"
            "payload={"
            "'blender':list(bpy.app.version),"
            "'module':fast64.__name__,"
            "'module_file':str(__import__('pathlib').Path(fast64.__file__).resolve()),"
            "'version':list(fast64.bl_info['version']),"
            "'enabled':p is not None,'default_enabled':d,'loaded':l"
            "};"
            f"print({PROBE_SENTINEL!r}+json.dumps(payload,sort_keys=True))"
        )
        output = _run(
            [
                str(blender),
                "--background",
                "--factory-startup",
                "--offline-mode",
                "--disable-autoexec",
                "-noaudio",
                "--python-exit-code",
                "71",
                "--python-expr",
                expression,
            ],
            timeout=45,
            env=environment,
        )
        payload = parse_probe_output(output, blender_pin, fast64_pin, isolated_root)
    after_preference = _snapshot_file(preference_path)
    after_tree = _snapshot_tree(root)
    after_app = _snapshot_tree_metadata(app_path)
    if fast64_source_identity(root) != expected_identity:
        raise AuthoringContractError("live Fast64 source changed during the isolated enabled-state probe")
    if before_preference != after_preference or before_tree != after_tree or before_app != after_app:
        raise AuthoringContractError(
            "authoring probe changed the Blender app, preferences, or Fast64 installation; restore the audited state"
        )
    return {
        "status": "PASS",
        "enabled": payload["enabled"],
        "loaded": payload["loaded"],
        "module_execution": "isolated_copy_of_pinned_fast64",
        "source_path": str(root),
        "observational_no_mutation": True,
        "isolated_profile": True,
        "global_preference_read_only": True,
        "inherited_environment": False,
        "offline_mode": True,
        "autoexec_disabled": True,
    }


def _archive_report(path: Path | None, pin: Mapping[str, Any], label: str) -> dict[str, Any]:
    if path is not None:
        return verify_distribution_asset(path, pin, label)
    return {
        "status": "NOT_SUPPLIED_PIN_RECORDED",
        "official_url": pin["release_asset_url"],
        "size_bytes": pin["release_asset_size"],
        "sha256": pin["release_asset_sha256"],
    }


def check_authoring_stack(
    blender: Path,
    fast64_root: Path,
    *,
    blender_dmg: Path | None = None,
    fast64_zip: Path | None = None,
) -> dict[str, Any]:
    authoring = load_authoring_lock()
    blender_pin = authoring["blender_macos_arm64"]
    fast64_pin = authoring["fast64"]
    report = {
        "schema_version": 1,
        "gate": 4,
        "status": "PASS",
        "mutations_performed": False,
        "distribution_assets": {
            "blender_dmg": _archive_report(blender_dmg, blender_pin, "Blender DMG"),
            "fast64_zip": _archive_report(fast64_zip, fast64_pin, "Fast64 release ZIP"),
        },
        "blender": verify_blender_binary(blender, blender_pin),
        "fast64": verify_fast64_source(fast64_root, fast64_pin),
    }
    report["fast64"]["enabled_probe"] = probe_fast64_enabled(
        blender, fast64_root, blender_pin, fast64_pin
    )
    post_probe_signature = _codesign_identity(blender.parents[2], blender_pin)
    if post_probe_signature != report["blender"]["codesign"]:
        raise AuthoringContractError("Blender signing identity changed during the authoring probe")
    report["blender"]["post_probe_deep_strict_verified"] = True
    return report


def default_paths(authoring: Mapping[str, Any]) -> tuple[Path, Path]:
    blender = Path(
        os.environ.get(
            "N64GAME_BLENDER_BINARY",
            str(Path.home() / authoring["blender_macos_arm64"]["macos_user_relative_path"]),
        )
    )
    fast64 = Path(
        os.environ.get(
            "N64GAME_FAST64_ROOT",
            str(Path.home() / authoring["fast64"]["blender_user_relative_path"]),
        )
    )
    return blender, fast64


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify the exact, enabled Blender 4.5.11 LTS + Fast64 v2.5.3 Gate 4 stack without changing it."
    )
    parser.add_argument("--blender", type=Path, help="override the locked user-relative Blender executable")
    parser.add_argument("--fast64-root", type=Path, help="override the locked Blender 4.5 Fast64 directory")
    parser.add_argument("--blender-dmg", type=Path, help="also verify a retained official Blender DMG")
    parser.add_argument("--fast64-zip", type=Path, help="also verify a retained official Fast64 release ZIP")
    parser.add_argument("--json", action="store_true", help="emit the complete machine-readable report")
    args = parser.parse_args(argv)
    try:
        authoring = load_authoring_lock()
        default_blender, default_fast64 = default_paths(authoring)
        report = check_authoring_stack(
            args.blender or default_blender,
            args.fast64_root or default_fast64,
            blender_dmg=args.blender_dmg,
            fast64_zip=args.fast64_zip,
        )
    except (AuthoringContractError, OSError, UnicodeError, ValueError) as exc:
        print(f"authoring_stack=FAIL {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("authoring_stack=PASS")
        print(f"blender=PASS {report['blender']['version']} arm64 {report['blender']['path']}")
        print(
            "fast64=PASS "
            f"v{report['fast64']['version']} enabled={str(report['fast64']['enabled_probe']['enabled']).lower()} "
            f"{report['fast64']['path']}"
        )
        print("mutations_performed=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
