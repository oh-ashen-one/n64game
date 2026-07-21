#!/usr/bin/env python3
"""Verify public fresh-clone and CI-artifact ROM reproducibility."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROM_REL = Path("build/game/n64game-gate3.z64")
SHA_REL = Path("build/game/n64game-gate3.z64.sha256")
MAP_REL = Path("build/game/n64game-gate3.map")
BUILD_REPORT_REL = Path("build/reports/validation-summary.md")
N64_MAGIC = bytes.fromhex("80371240")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
ARTIFACT_NAME_PREFIX = "n64game-gate3-"
DEFAULT_REPO = "oh-ashen-one/n64game"


class ReproError(RuntimeError):
    pass


@dataclass(frozen=True)
class RomIdentity:
    path: str
    size: int
    sha256: str
    header_sha256: str

    def to_json(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "size": self.size,
            "sha256": self.sha256,
            "header_sha256": self.header_sha256,
        }


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str], *, cwd: Path, timeout: int = 900) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReproError(f"command failed to run: {' '.join(command)}: {exc}") from exc


def require_success(result: subprocess.CompletedProcess[str], description: str) -> str:
    if result.returncode != 0:
        output = result.stdout.strip().splitlines()
        excerpt = "\n".join(output[-30:])
        raise ReproError(f"{description} failed ({result.returncode}): {excerpt}")
    return result.stdout


def git(root: Path, *args: str, timeout: int = 120) -> str:
    return require_success(run(["git", *args], cwd=root, timeout=timeout), f"git {' '.join(args)}").strip()


def gh(root: Path, *args: str, timeout: int = 120) -> str:
    return require_success(run(["gh", *args], cwd=root, timeout=timeout), f"gh {' '.join(args)}").strip()


def materialize_lfs(clone: Path) -> None:
    version = run(["git", "lfs", "version"], cwd=clone, timeout=60)
    if version.returncode != 0:
        raise ReproError("git lfs is required to materialize public clone assets")
    require_success(run(["git", "lfs", "install", "--local"], cwd=clone, timeout=60), "git lfs install in fresh clone")
    require_success(run(["git", "lfs", "pull"], cwd=clone, timeout=600), "git lfs pull in fresh clone")


def rom_identity(root: Path, relative: Path) -> RomIdentity:
    path = root / relative
    if not path.is_file() or path.is_symlink():
        raise ReproError(f"ROM is not one regular file: {relative}")
    data = path.read_bytes()
    if len(data) < 64 or data[:4] != N64_MAGIC:
        raise ReproError(f"ROM has invalid N64 header magic: {relative}")
    return RomIdentity(
        path=relative.as_posix(),
        size=len(data),
        sha256=sha256_bytes(data),
        header_sha256=sha256_bytes(data[:64]),
    )


def require_checksum_file(root: Path, relative: Path, expected_sha: str) -> str:
    path = root / relative
    if not path.is_file() or path.is_symlink() or path.stat().st_size == 0:
        raise ReproError(f"missing checksum file: {relative}")
    first = path.read_text(encoding="utf-8").strip().split()[0]
    if first != expected_sha:
        raise ReproError(f"checksum file {relative} records {first}, expected {expected_sha}")
    return sha256_file(path)


def require_file(root: Path, relative: Path) -> str:
    path = root / relative
    if not path.is_file() or path.is_symlink() or path.stat().st_size == 0:
        raise ReproError(f"missing required report file: {relative}")
    return sha256_file(path)


def current_head(root: Path) -> str:
    head = git(root, "rev-parse", "HEAD")
    if not HEX40.fullmatch(head):
        raise ReproError(f"current HEAD is not a full commit hash: {head}")
    return head


def verify_public_origin(root: Path, repo: str, head: str) -> str:
    origin = git(root, "remote", "get-url", "origin")
    if repo not in origin:
        raise ReproError(f"origin {origin!r} does not target {repo}")
    remote_refs = git(root, "ls-remote", f"https://github.com/{repo}.git", timeout=300).splitlines()
    if not any(line.split(maxsplit=1)[0] == head for line in remote_refs if line.strip()):
        raise ReproError(f"commit {head} is not reachable from any public ref at https://github.com/{repo}.git")
    return origin


def find_successful_run(root: Path, repo: str, head: str) -> dict[str, Any]:
    raw = gh(
        root,
        "run",
        "list",
        "--repo",
        repo,
        "--workflow",
        "Build ROM",
        "--commit",
        head,
        "--limit",
        "20",
        "--json",
        "databaseId,headSha,status,conclusion,workflowName,url",
    )
    runs = json.loads(raw)
    for run_info in runs:
        if (
            run_info.get("headSha") == head
            and run_info.get("status") == "completed"
            and run_info.get("conclusion") == "success"
            and run_info.get("workflowName") == "Build ROM"
        ):
            return run_info
    raise ReproError(f"no successful public Build ROM run found for {head}")


def build_fresh_public_clone(root: Path, repo: str, head: str, keep_clone: Path | None) -> tuple[RomIdentity, dict[str, str], str]:
    temp_root = root / "build" / "tmp-public-repro"
    temp_root.mkdir(parents=True, exist_ok=True)
    parent = Path(tempfile.mkdtemp(prefix="clone-", dir=temp_root))
    clone = parent / "n64game"
    try:
        require_success(
            run(["git", "clone", "--recurse-submodules", f"https://github.com/{repo}.git", str(clone)], cwd=root, timeout=900),
            "credential-free fresh public clone",
        )
        git(clone, "checkout", "--detach", head)
        materialize_lfs(clone)
        require_success(run(["npm", "ci", "--ignore-scripts"], cwd=clone, timeout=900), "npm ci in fresh clone")
        require_success(run(["make", "validate"], cwd=clone, timeout=900), "make validate in fresh clone")
        require_success(run(["make", "rom"], cwd=clone, timeout=1800), "make rom in fresh clone")
        identity = rom_identity(clone, ROM_REL)
        files = {
            SHA_REL.as_posix(): require_checksum_file(clone, SHA_REL, identity.sha256),
            MAP_REL.as_posix(): require_file(clone, MAP_REL),
            BUILD_REPORT_REL.as_posix(): require_file(clone, BUILD_REPORT_REL),
        }
        if keep_clone:
            if keep_clone.exists():
                raise ReproError(f"--keep-clone path already exists: {keep_clone}")
            keep_clone.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(clone), str(keep_clone))
            clone_path = str(keep_clone)
        else:
            clone_path = "discarded"
        return identity, files, clone_path
    finally:
        if keep_clone is None:
            shutil.rmtree(parent, ignore_errors=True)
        elif parent.exists() and not clone.exists():
            shutil.rmtree(parent, ignore_errors=True)


def download_ci_artifact(root: Path, repo: str, run_info: dict[str, Any], head: str) -> tuple[RomIdentity, dict[str, str]]:
    artifact_name = f"{ARTIFACT_NAME_PREFIX}{head}"
    with tempfile.TemporaryDirectory(prefix="n64game-ci-artifact-") as temp:
        out_dir = Path(temp) / "artifact"
        out_dir.mkdir()
        gh(
            root,
            "run",
            "download",
            str(run_info["databaseId"]),
            "--repo",
            repo,
            "--name",
            artifact_name,
            "--dir",
            str(out_dir),
            timeout=300,
        )
        identity = rom_identity(out_dir, ROM_REL)
        files = {
            SHA_REL.as_posix(): require_checksum_file(out_dir, SHA_REL, identity.sha256),
            MAP_REL.as_posix(): require_file(out_dir, MAP_REL),
            BUILD_REPORT_REL.as_posix(): require_file(out_dir, BUILD_REPORT_REL),
        }
        return identity, files


def compare_identities(local: RomIdentity, fresh: RomIdentity, artifact: RomIdentity) -> None:
    expected = (local.size, local.sha256, local.header_sha256)
    if (fresh.size, fresh.sha256, fresh.header_sha256) != expected:
        raise ReproError("fresh public clone ROM identity differs from local ROM")
    if (artifact.size, artifact.sha256, artifact.header_sha256) != expected:
        raise ReproError("downloaded public CI artifact ROM identity differs from local ROM")


def build_report(root: Path, repo: str, keep_clone: Path | None) -> dict[str, Any]:
    head = current_head(root)
    origin = verify_public_origin(root, repo, head)
    local = rom_identity(root, ROM_REL)
    local_files = {
        SHA_REL.as_posix(): require_checksum_file(root, SHA_REL, local.sha256),
        MAP_REL.as_posix(): require_file(root, MAP_REL),
        BUILD_REPORT_REL.as_posix(): require_file(root, BUILD_REPORT_REL),
    }
    run_info = find_successful_run(root, repo, head)
    fresh, fresh_files, clone_path = build_fresh_public_clone(root, repo, head, keep_clone)
    artifact, artifact_files = download_ci_artifact(root, repo, run_info, head)
    compare_identities(local, fresh, artifact)
    return {
        "schema": "n64game-public-reproducibility-v1",
        "result": "PASS",
        "repo": repo,
        "origin": origin,
        "head_sha": head,
        "workflow": {
            "name": "Build ROM",
            "run_id": run_info["databaseId"],
            "url": run_info["url"],
            "artifact_name": f"{ARTIFACT_NAME_PREFIX}{head}",
        },
        "local": {"rom": local.to_json(), "files": local_files},
        "fresh_public_clone": {"rom": fresh.to_json(), "files": fresh_files, "clone_path": clone_path},
        "ci_artifact": {"rom": artifact.to_json(), "files": artifact_files},
    }


def render_markdown(payload: dict[str, Any]) -> str:
    rom = payload["local"]["rom"]
    return "\n".join([
        "# N64GAME Public Reproducibility Evidence",
        "",
        f"- Result: `{payload['result']}`",
        f"- Repository: `{payload['repo']}`",
        f"- HEAD: `{payload['head_sha']}`",
        f"- CI run: [{payload['workflow']['run_id']}]({payload['workflow']['url']})",
        f"- Artifact: `{payload['workflow']['artifact_name']}`",
        f"- ROM size: `{rom['size']}` bytes",
        f"- ROM SHA-256: `{rom['sha256']}`",
        f"- ROM header SHA-256: `{rom['header_sha256']}`",
        "",
        "The local ROM, credential-free fresh public clone build, and downloaded public CI artifact matched byte-for-byte.",
        "This proves public reproducible build identity only; it is not Ares playthrough, soak, visual, audio, or final release certification.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--json-out", type=Path, default=ROOT / "build/reports/public-reproducibility.json")
    parser.add_argument("--md-out", type=Path, default=ROOT / "build/reports/public-reproducibility.md")
    parser.add_argument("--keep-clone", type=Path, help="move the verified fresh clone here instead of deleting it")
    args = parser.parse_args()

    root = args.root.resolve()
    try:
        payload = build_report(root, args.repo, args.keep_clone.resolve() if args.keep_clone else None)
    except (OSError, json.JSONDecodeError, ReproError) as exc:
        print(f"PUBLIC_REPRODUCIBILITY_ERROR: {exc}")
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
