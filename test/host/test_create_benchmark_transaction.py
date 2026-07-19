from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "scripts/create-benchmark-transaction"
CANONICAL_URL = "https://github.com/oh-ashen-one/n64game.git"
CONTROL_PATH = Path("docs/VISUAL_BENCHMARK_APPROVAL.md")


class BenchmarkTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="n64game-transaction-test-")
        self.base = Path(self.temp.name)
        self.repo = self.base / "repo"
        self.remote = self.base / "public.git"
        self.inputs = self.base / "inputs"
        self.home = self.base / "home"
        self.inputs.mkdir()
        self.home.mkdir()

        subprocess.run(["git", "init", "--bare", "--quiet", str(self.remote)], check=True)
        self.fixture_url = self.remote.as_uri()
        self.env = {
            **os.environ,
            "HOME": str(self.home),
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
            "LC_ALL": "C",
            "LANG": "C",
        }

        self.git(None, "init", "--quiet", str(self.repo))
        self.git(self.repo, "checkout", "--quiet", "-b", "fixture")
        self.git(self.repo, "config", "user.name", "N64Game Test")
        self.git(self.repo, "config", "user.email", "n64game@example.invalid")
        self.git(self.repo, "remote", "add", "origin", self.fixture_url)
        (self.repo / "scripts").mkdir()
        (self.repo / "docs").mkdir()
        (self.repo / "review").mkdir()
        helper_text = HELPER.read_text(encoding="utf-8")
        canonical_line = f"  CANONICAL_REMOTE = {json.dumps(CANONICAL_URL)}"
        fixture_line = f"  CANONICAL_REMOTE = {json.dumps(self.fixture_url)}"
        self.assertEqual(helper_text.count(canonical_line), 1)
        (self.repo / "scripts/create-benchmark-transaction").write_text(
            helper_text.replace(canonical_line, fixture_line),
            encoding="utf-8",
        )
        os.chmod(self.repo / "scripts/create-benchmark-transaction", 0o755)
        (self.repo / CONTROL_PATH).write_text(self.control_text("BASE"), encoding="utf-8")
        (self.repo / "review/payload.txt").write_text("base\n", encoding="utf-8")
        self.git(self.repo, "add", ".")
        self.git(self.repo, "commit", "--quiet", "-m", "fixture base")
        self.base_commit = self.git(self.repo, "rev-parse", "HEAD").stdout.strip()
        self.git(self.repo, "push", "--quiet", "-u", "origin", "fixture")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def git(self, cwd: Path | None, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        command = ["git"]
        if cwd is not None:
            command.extend(["-C", str(cwd)])
        command.extend(args)
        return subprocess.run(
            command,
            env=self.env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=check,
        )

    @staticmethod
    def control_text(note: str) -> str:
        return (
            "# N64GAME Visual Benchmark Approval\n\n"
            "Decision: PENDING\n\n"
            "| Field | Required value | Current value |\n"
            "|---|---|---|\n"
            "| Reviewed payload Git commit | exact 40 lowercase hex | `PENDING` |\n\n"
            f"Operator-note: {note}\n"
        )

    def make_payload_patch(self, path: str = "review/payload.txt", content: bytes = b"staged\n", mode: int | None = None) -> Path:
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        existed = target.exists() or target.is_symlink()
        original = target.read_bytes() if target.exists() and not target.is_symlink() else None
        if target.is_symlink():
            target.unlink()
        if mode == stat.S_IFLNK:
            os.symlink("outside", target)
        else:
            target.write_bytes(content)
        self.git(self.repo, "add", "-f", "--", path)
        patch = self.inputs / (path.replace("/", "_") + ".patch")
        diff = subprocess.run(
            ["git", "-C", str(self.repo), "diff", "--cached", "--binary", "--", path],
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        ).stdout
        patch.write_bytes(diff)
        self.git(self.repo, "reset", "--quiet", "HEAD", "--", path)
        if target.is_symlink():
            target.unlink()
        elif target.exists():
            target.unlink()
        if existed and original is not None:
            target.write_bytes(original)
        return patch

    def make_gitlink_patch(self, path: str = "review/forbidden-gitlink") -> Path:
        self.git(
            self.repo,
            "update-index",
            "--add",
            "--cacheinfo",
            "160000",
            self.base_commit,
            path,
        )
        patch = self.inputs / "gitlink.patch"
        patch.write_bytes(
            subprocess.run(
                ["git", "-C", str(self.repo), "diff", "--cached", "--binary", "--", path],
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            ).stdout
        )
        self.git(self.repo, "reset", "--quiet", "HEAD", "--", path)
        return patch

    def prepared_control(self, note: str = "READY") -> Path:
        path = self.inputs / f"control-{note}.md"
        path.write_text(self.control_text(note), encoding="utf-8")
        return path

    def invoke(
        self,
        patch: Path,
        control: Path,
        token: str,
        env_overrides: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command_env = {**self.env, **(env_overrides or {})}
        return subprocess.run(
            [
                "/usr/bin/ruby",
                "--disable-gems",
                "scripts/create-benchmark-transaction",
                "--payload-patch",
                str(patch),
                "--control-file",
                str(control),
                "--token",
                token,
            ],
            cwd=self.repo,
            env=command_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_success_creates_exact_two_commit_transaction_without_push(self) -> None:
        patch = self.make_payload_patch()
        control = self.prepared_control()
        remote_before = self.git(None, "ls-remote", "--refs", self.fixture_url, "refs/heads/fixture").stdout

        result = self.invoke(patch, control, "success")
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["result"], "PASS")
        self.assertEqual(receipt["base_commit"], self.base_commit)
        self.assertEqual(receipt["payload_changed_paths"], ["review/payload.txt"])
        self.assertEqual(receipt["control_changed_paths"], [CONTROL_PATH.as_posix()])
        self.assertFalse(receipt["automatic_push"])
        self.assertFalse(receipt["automatic_merge"])
        self.assertFalse(receipt["source_branch_moved"])

        payload = receipt["payload_commit_p"]
        control_commit = receipt["control_commit_a"]
        self.assertEqual(self.git(self.repo, "rev-parse", f"{payload}^1").stdout.strip(), self.base_commit)
        self.assertEqual(self.git(self.repo, "rev-parse", f"{control_commit}^1").stdout.strip(), payload)
        changed = self.git(self.repo, "diff", "--name-only", payload, control_commit).stdout.splitlines()
        self.assertEqual(changed, [CONTROL_PATH.as_posix()])
        committed_control = self.git(self.repo, "show", f"{control_commit}:{CONTROL_PATH.as_posix()}").stdout
        self.assertIn(f"`{payload}`", committed_control)
        self.assertIn("Operator-note: READY", committed_control)
        self.assertEqual(receipt["committed_control_sha256"], hashlib.sha256(committed_control.encode()).hexdigest())
        self.assertEqual(self.git(self.repo, "rev-parse", receipt["safety_ref"]).stdout.strip(), control_commit)
        self.assertEqual(self.git(self.repo, "rev-parse", "HEAD").stdout.strip(), self.base_commit)
        self.assertEqual(self.git(self.repo, "status", "--porcelain").stdout, "")
        self.assertEqual(self.git(None, "ls-remote", "--refs", self.fixture_url, "refs/heads/fixture").stdout, remote_before)
        self.assertEqual(len(receipt["manual_steps"]), 4)
        self.assertTrue(receipt["manual_steps"][-1].startswith(f"git push origin {control_commit}:refs/heads/"))

        repeat = self.invoke(patch, control, "success-repeat")
        self.assertEqual(repeat.returncode, 0, repeat.stderr)
        repeated_receipt = json.loads(repeat.stdout)
        self.assertEqual(repeated_receipt["payload_commit_p"], payload)
        self.assertEqual(repeated_receipt["control_commit_a"], control_commit)
        self.assertEqual(
            self.git(self.repo, "rev-parse", repeated_receipt["safety_ref"]).stdout.strip(),
            control_commit,
        )

    def test_dirty_or_untracked_source_repository_is_rejected_before_safety_ref(self) -> None:
        patch = self.make_payload_patch()
        (self.repo / "ambiguous.tmp").write_text("dirty\n", encoding="utf-8")
        result = self.invoke(patch, self.prepared_control(), "dirty")
        self.assertNotEqual(result.returncode, 0)
        failure = json.loads(result.stderr)
        self.assertIn("exactly clean", failure["error"])
        self.assertNotIn("safety_ref", failure)

    def test_poisoned_git_environment_cannot_redirect_authority_or_transaction_state(self) -> None:
        patch = self.make_payload_patch()
        poison_config = self.inputs / "poison.gitconfig"
        poison_config.write_text(
            f"[url \"file:///does-not-exist\"]\n\tinsteadOf = {self.fixture_url}\n",
            encoding="utf-8",
        )
        fake_bin = self.inputs / "fake-bin"
        fake_bin.mkdir()
        fake_git = fake_bin / "git"
        fake_git.write_text("#!/bin/sh\nexit 91\n", encoding="utf-8")
        os.chmod(fake_git, 0o755)
        hostile_hook = self.inputs / "hostile-hook"
        hostile_hook.write_text("#!/bin/sh\nexit 92\n", encoding="utf-8")
        os.chmod(hostile_hook, 0o755)
        hooks = self.inputs / "hostile-hooks"
        hooks.mkdir()
        for hook_name in ("post-checkout", "post-commit", "reference-transaction"):
            shutil.copy2(hostile_hook, hooks / hook_name)
        self.git(self.repo, "config", "core.hooksPath", str(hooks))
        self.git(self.repo, "config", "core.fsmonitor", str(hostile_hook))
        self.git(
            self.repo,
            "config",
            "url.file:///does-not-exist.insteadOf",
            self.fixture_url,
        )
        poison = {
            "PATH": f"{fake_bin}:/usr/bin:/bin",
            "GIT_DIR": str(self.base / "wrong.git"),
            "GIT_WORK_TREE": str(self.inputs),
            "GIT_INDEX_FILE": str(self.inputs / "wrong-index"),
            "GIT_OBJECT_DIRECTORY": str(self.inputs / "wrong-objects"),
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(self.inputs / "wrong-alternates"),
            "GIT_CONFIG_GLOBAL": str(poison_config),
            "GIT_CONFIG_NOSYSTEM": "0",
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.hooksPath",
            "GIT_CONFIG_VALUE_0": str(self.inputs),
            "GIT_REPLACE_REF_BASE": "refs/poison/",
            "GH_TOKEN": "must-not-propagate",
            "GITHUB_TOKEN": "must-not-propagate",
        }
        result = self.invoke(patch, self.prepared_control(), "poisoned-env", poison)
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["result"], "PASS")
        self.assertEqual(receipt["base_commit"], self.base_commit)
        self.assertEqual(self.git(self.repo, "rev-parse", "HEAD").stdout.strip(), self.base_commit)

    def test_control_only_patch_is_rejected_and_recovery_ref_is_retained(self) -> None:
        patch = self.make_payload_patch(CONTROL_PATH.as_posix(), self.control_text("PATCHED").encode())
        result = self.invoke(patch, self.prepared_control("READY"), "control-only")
        self.assertNotEqual(result.returncode, 0)
        failure = json.loads(result.stderr)
        self.assertIn("must exclude", failure["error"])
        self.assertEqual(failure["safety_ref_target"], self.base_commit)
        self.assertEqual(self.git(self.repo, "rev-parse", failure["safety_ref"]).stdout.strip(), self.base_commit)
        self.assertEqual(len(failure["recovery_steps"]), 2)

    def test_empty_payload_patch_is_rejected(self) -> None:
        patch = self.inputs / "empty.patch"
        patch.write_bytes(b"")
        result = self.invoke(patch, self.prepared_control(), "empty-payload")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must not be empty", json.loads(result.stderr)["error"])

    def test_payload_only_transaction_without_caller_control_change_is_rejected(self) -> None:
        patch = self.make_payload_patch()
        result = self.invoke(patch, self.prepared_control("BASE"), "payload-only")
        self.assertNotEqual(result.returncode, 0)
        failure = json.loads(result.stderr)
        self.assertIn("caller-authored change", failure["error"])
        self.assertNotIn("safety_ref", failure)

    def test_rom_payload_is_rejected_with_recovery_evidence_and_no_remote_change(self) -> None:
        patch = self.make_payload_patch("review/forbidden.z64", b"\x80\x37\x12\x40")
        remote_before = self.git(None, "ls-remote", "--refs", self.fixture_url, "refs/heads/fixture").stdout
        result = self.invoke(patch, self.prepared_control(), "rom")
        self.assertNotEqual(result.returncode, 0)
        failure = json.loads(result.stderr)
        self.assertIn("forbidden ROM", failure["error"])
        self.assertEqual(failure["safety_ref_target"], self.base_commit)
        self.assertEqual(self.git(self.repo, "rev-parse", failure["safety_ref"]).stdout.strip(), self.base_commit)
        self.assertEqual(self.git(None, "ls-remote", "--refs", self.fixture_url, "refs/heads/fixture").stdout, remote_before)

    def test_post_commit_failure_retains_a_and_emits_exact_recovery_chain(self) -> None:
        patch = self.make_payload_patch(
            ".gitattributes",
            b"docs/VISUAL_BENCHMARK_APPROVAL.md filter=corrupt-control\n",
        )
        self.git(self.repo, "config", "filter.corrupt-control.clean", "/usr/bin/tr A B")
        self.git(self.repo, "config", "filter.corrupt-control.smudge", "cat")
        self.git(self.repo, "config", "filter.corrupt-control.required", "true")
        remote_before = self.git(None, "ls-remote", "--refs", self.fixture_url, "refs/heads/fixture").stdout

        result = self.invoke(patch, self.prepared_control(), "post-commit-failure")
        self.assertNotEqual(result.returncode, 0)
        failure = json.loads(result.stderr)
        self.assertIn("bytes differ", failure["error"])
        payload = failure["payload_commit_p"]
        control_commit = failure["control_commit_a"]
        self.assertEqual(failure["safety_ref_target"], control_commit)
        self.assertEqual(self.git(self.repo, "rev-parse", failure["safety_ref"]).stdout.strip(), control_commit)
        self.assertEqual(self.git(self.repo, "rev-parse", f"{control_commit}^1").stdout.strip(), payload)
        self.assertEqual(self.git(self.repo, "rev-parse", f"{payload}^1").stdout.strip(), self.base_commit)
        self.assertEqual(self.git(self.repo, "rev-parse", "HEAD").stdout.strip(), self.base_commit)
        self.assertEqual(self.git(self.repo, "status", "--porcelain").stdout, "")
        self.assertEqual(self.git(None, "ls-remote", "--refs", self.fixture_url, "refs/heads/fixture").stdout, remote_before)
        self.assertEqual(len(failure["recovery_steps"]), 2)

    def test_symlink_payload_is_rejected_without_touching_source_worktree(self) -> None:
        patch = self.make_payload_patch("review/link.txt", mode=stat.S_IFLNK)
        result = self.invoke(patch, self.prepared_control(), "symlink")
        self.assertNotEqual(result.returncode, 0)
        failure = json.loads(result.stderr)
        self.assertIn("symlink", failure["error"])
        self.assertEqual(failure["safety_ref_target"], self.base_commit)
        self.assertEqual(self.git(self.repo, "status", "--porcelain").stdout, "")

    def test_gitlink_payload_mode_is_rejected_and_safety_ref_is_retained(self) -> None:
        patch = self.make_gitlink_patch()
        result = self.invoke(patch, self.prepared_control(), "gitlink")
        self.assertNotEqual(result.returncode, 0)
        failure = json.loads(result.stderr)
        self.assertIn("gitlink", failure["error"])
        self.assertEqual(failure["safety_ref_target"], self.base_commit)
        self.assertEqual(self.git(self.repo, "rev-parse", failure["safety_ref"]).stdout.strip(), self.base_commit)
        self.assertEqual(self.git(self.repo, "status", "--porcelain").stdout, "")

    def test_local_only_branch_tip_is_rejected(self) -> None:
        patch = self.make_payload_patch()
        (self.repo / "local.txt").write_text("local\n", encoding="utf-8")
        self.git(self.repo, "add", "local.txt")
        self.git(self.repo, "commit", "--quiet", "-m", "local only")
        result = self.invoke(patch, self.prepared_control(), "local-only")
        self.assertNotEqual(result.returncode, 0)
        failure = json.loads(result.stderr)
        self.assertIn("advertised public branch tip", failure["error"])
        self.assertNotIn("safety_ref", failure)


if __name__ == "__main__":
    unittest.main()
