from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RUBY = "/usr/bin/ruby"
HEAD = "a" * 40
OTHER = "b" * 40
CONTROL = "c" * 40
PUBLIC_MERGE = "d" * 40
GIT_LFS = shutil.which("git-lfs")
SAFE_PATH_PARTS = ["/usr/bin", "/bin"]
if GIT_LFS:
    SAFE_PATH_PARTS.insert(0, str(Path(GIT_LFS).parent))
SAFE_PATH = os.pathsep.join(dict.fromkeys(SAFE_PATH_PARTS))


RUBY_ADAPTER = r"""
  require 'json'
  require 'n64game/public_commit_authority'

  policy = N64Game::PublicCommitAuthority
  input = JSON.parse(STDIN.read)
  action = input.fetch('action')
  payload = input.fetch('payload')
  begin
    result = case action
    when 'select'
      valid_branch = lambda do |ref|
        system('/usr/bin/git', 'check-ref-format', ref, out: File::NULL, err: File::NULL)
      end
      policy.select_advertised_ref!(
        head: payload['head'],
        status_bytes: payload['status_bytes'],
        advertised_bytes: payload['advertised_bytes'],
        branch_ref_valid: valid_branch
      )
    when 'verify_fetched'
      policy.verify_fetched_ref!(
        expected_head: payload['expected_head'], fetched_oid: payload['fetched_oid']
      )
    when 'clone_and_fetch'
      policy.clone_and_fetch!(
        remote_url: payload['remote_url'],
        selected_ref: payload['selected_ref'],
        expected_head: payload['expected_head'],
        root: payload['root'],
        env: payload['env']
      )
    when 'control_transaction'
      policy.validate_control_transaction!(
        public_head: payload['public_head'],
        control_commit: payload['control_commit'],
        parents: payload['parents'],
        reviewed_payload_commit: payload['reviewed_payload_commit'],
        changed_paths: payload['changed_paths'],
        current_descends_from_control: payload['current_descends_from_control'],
        control_public: payload['control_public'],
        control_bytes_equal: payload['control_bytes_equal'],
        public_tree_equal: payload['public_tree_equal']
      )
    else
      raise "unknown action: #{action}"
    end
    STDOUT.write(JSON.generate({ 'ok' => true, 'result' => result }))
  rescue N64Game::PublicCommitAuthority::Violation => violation
    STDOUT.write(JSON.generate({ 'ok' => false, 'issues' => violation.issues }))
  end
"""


class PublicConceptAuthorityTests(unittest.TestCase):
    maxDiff = None

    def ruby_call(
        self,
        action: str,
        payload: dict[str, Any],
        *,
        extra_env: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        env = {
            "PATH": SAFE_PATH,
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
        }
        if extra_env:
            env.update(extra_env)
        completed = subprocess.run(
            [RUBY, "--disable-gems", "-I", str(ROOT / "lib"), "-e", RUBY_ADAPTER],
            input=json.dumps({"action": action, "payload": payload}),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=env,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    @staticmethod
    def advertised(*rows: tuple[str, str]) -> str:
        return "".join(f"{oid}\t{ref}\n" for oid, ref in rows)

    def select(
        self,
        advertised_bytes: str,
        *,
        head: str = HEAD,
        status_bytes: str = "",
        extra_env: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return self.ruby_call(
            "select",
            {
                "head": head,
                "status_bytes": status_bytes,
                "advertised_bytes": advertised_bytes,
            },
            extra_env=extra_env,
        )

    def assert_issue(self, result: dict[str, Any], fragment: str) -> None:
        self.assertFalse(result["ok"], result)
        self.assertTrue(
            any(fragment in issue for issue in result["issues"]),
            f"missing {fragment!r} in {result['issues']!r}",
        )

    @staticmethod
    def git_env() -> dict[str, str]:
        return {
            "PATH": SAFE_PATH,
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "N64Game Authority Test",
            "GIT_AUTHOR_EMAIL": "authority@example.invalid",
            "GIT_COMMITTER_NAME": "N64Game Authority Test",
            "GIT_COMMITTER_EMAIL": "authority@example.invalid",
        }

    @staticmethod
    def clone_env() -> dict[str, str | None]:
        return {
            "PATH": SAFE_PATH,
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "GIT_TERMINAL_PROMPT": "0",
            "GCM_INTERACTIVE": "never",
            "GIT_ASKPASS": "/usr/bin/false",
            "GIT_ASKPASS_REQUIRE": "force",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GH_TOKEN": None,
            "GITHUB_TOKEN": None,
            "GITLAB_TOKEN": None,
        }

    def git(
        self,
        *args: str,
        cwd: Path | None = None,
        check: bool = True,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            ["/usr/bin/git", *args],
            cwd=cwd,
            env=self.git_env(),
            input=input_text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if check:
            self.assertEqual(completed.returncode, 0, completed.stderr)
        return completed

    def make_file_remote(
        self, parent: Path
    ) -> tuple[str, Path, dict[str, str]]:
        source = parent / "source"
        remote = parent / "public.git"
        source.mkdir()
        self.git("init", "-q", cwd=source)

        commits: list[str] = []
        fixture = source / "fixture.txt"
        for number, label in enumerate(("branch", "pull-head", "pull-merge"), start=1):
            fixture.write_text(f"{label}\n", encoding="utf-8")
            self.git("add", "--", "fixture.txt", cwd=source)
            self.git("commit", "-q", "-m", f"fixture {number}", cwd=source)
            commits.append(self.git("rev-parse", "HEAD", cwd=source).stdout.strip())

        self.git("init", "--bare", "-q", str(remote), cwd=parent)
        remote_url = remote.as_uri()
        self.git(
            "push",
            "-q",
            remote_url,
            f"{commits[0]}:refs/heads/concept",
            f"{commits[1]}:refs/pull/11/head",
            f"{commits[2]}:refs/pull/11/merge",
            f"{commits[0]}:refs/tags/poison-tag",
            cwd=source,
        )
        return remote_url, remote, {
            "branch": commits[0],
            "pull_head": commits[1],
            "pull_merge": commits[2],
        }

    def advertised_from_remote(self, remote_url: str) -> str:
        return self.git(
            "ls-remote",
            "--refs",
            remote_url,
            "refs/heads/*",
            "refs/pull/*/head",
            "refs/pull/*/merge",
        ).stdout

    def test_selects_exact_tip_with_branch_then_pull_head_then_pull_merge_priority(self) -> None:
        all_kinds = self.advertised(
            (HEAD, "refs/pull/7/merge"),
            (HEAD, "refs/heads/zeta"),
            (HEAD, "refs/pull/7/head"),
            (HEAD, "refs/heads/alpha"),
        )
        self.assertEqual(
            self.select(all_kinds),
            {
                "ok": True,
                "result": {"commit": HEAD, "ref": "refs/heads/alpha", "kind": "branch"},
            },
        )

        pull_kinds = self.advertised(
            (HEAD, "refs/pull/21/merge"),
            (HEAD, "refs/pull/9/head"),
            (HEAD, "refs/pull/21/head"),
        )
        self.assertEqual(
            self.select(pull_kinds)["result"],
            {"commit": HEAD, "ref": "refs/pull/21/head", "kind": "pull_head"},
        )
        self.assertEqual(
            self.select(self.advertised((HEAD, "refs/pull/9/merge")))["result"],
            {"commit": HEAD, "ref": "refs/pull/9/merge", "kind": "pull_merge"},
        )

    def test_clean_status_is_exact_and_dirty_index_worktree_and_untracked_bytes_die(self) -> None:
        refs = self.advertised((HEAD, "refs/heads/main"))
        self.assertTrue(self.select(refs, status_bytes="")["ok"])
        for label, status_bytes in {
            "worktree": " M docs/ART_BIBLE.md\0",
            "index": "M  docs/ART_BIBLE.md\0",
            "untracked": "?? assets-src/local-only.blend\0",
            "nonempty-newline": "\n",
        }.items():
            with self.subTest(label=label):
                self.assert_issue(
                    self.select(refs, status_bytes=status_bytes),
                    "clean worktree and index",
                )

    def test_local_only_and_old_reachable_but_non_tip_heads_die(self) -> None:
        cases = {
            "local_only_unpushed": "",
            "old_reachable_not_tip": self.advertised((OTHER, "refs/heads/main")),
            "unrelated_public_tip": self.advertised(
                (OTHER, "refs/heads/main"), (CONTROL, "refs/pull/4/head")
            ),
        }
        for label, advertised_bytes in cases.items():
            with self.subTest(label=label):
                self.assert_issue(
                    self.select(advertised_bytes),
                    "not the tip of an allowed advertised public ref",
                )

    def test_tag_unexpected_malformed_zero_pull_and_conflicting_refs_die_closed(self) -> None:
        valid = (HEAD, "refs/heads/main")
        cases = {
            "tag": self.advertised(valid, (OTHER, "refs/tags/v0.71")),
            "unexpected_namespace": self.advertised(valid, (OTHER, "refs/remotes/origin/main")),
            "pull_zero": self.advertised(valid, (OTHER, "refs/pull/0/head")),
            "bad_branch_ref": self.advertised(valid, (OTHER, "refs/heads/bad..name")),
            "malformed_row": self.advertised(valid) + "not-an-ls-remote-row\n",
            "malformed_oid": self.advertised(valid) + f"{'A' * 40}\trefs/heads/upper\n",
            "conflicting_ref": self.advertised(
                valid, (OTHER, "refs/heads/main")
            ),
        }
        expected = {
            "tag": "outside the allowed",
            "unexpected_namespace": "outside the allowed",
            "pull_zero": "outside the allowed",
            "bad_branch_ref": "outside the allowed",
            "malformed_row": "is malformed",
            "malformed_oid": "is malformed",
            "conflicting_ref": "conflicting object IDs",
        }
        for label, advertised_bytes in cases.items():
            with self.subTest(label=label):
                self.assert_issue(self.select(advertised_bytes), expected[label])

    def test_selection_ignores_poisoned_ci_identity_environment(self) -> None:
        refs = self.advertised((HEAD, "refs/heads/public-concept"))
        result = self.select(
            refs,
            extra_env={
                "CI": "true",
                "GITHUB_SHA": OTHER,
                "GITHUB_REF": "refs/tags/attacker-controlled",
                "GITHUB_HEAD_REF": "attacker-controlled",
                "GITHUB_TOKEN": "must-not-be-authority",
                "GH_TOKEN": "must-not-be-authority",
            },
        )
        self.assertEqual(result["result"]["commit"], HEAD)
        self.assertEqual(result["result"]["ref"], "refs/heads/public-concept")

    def test_explicit_fetch_oid_must_still_equal_selected_head(self) -> None:
        accepted = self.ruby_call(
            "verify_fetched", {"expected_head": HEAD, "fetched_oid": HEAD}
        )
        self.assertEqual(accepted, {"ok": True, "result": True})

        moved = self.ruby_call(
            "verify_fetched", {"expected_head": HEAD, "fetched_oid": OTHER}
        )
        self.assert_issue(moved, "moved or disappeared")
        disappeared = self.ruby_call(
            "verify_fetched", {"expected_head": HEAD, "fetched_oid": None}
        )
        self.assert_issue(disappeared, "moved or disappeared")

    def test_clone_and_fetch_materializes_branch_pr_head_and_pr_merge_refs(self) -> None:
        self.assertIsNotNone(GIT_LFS, "git-lfs is required by the production authority path")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            remote_url, _remote, commits = self.make_file_remote(root)
            advertised_bytes = self.advertised_from_remote(remote_url)
            cases = (
                ("branch", "refs/heads/concept"),
                ("pull_head", "refs/pull/11/head"),
                ("pull_merge", "refs/pull/11/merge"),
            )
            for kind, expected_ref in cases:
                with self.subTest(kind=kind):
                    selected = self.select(
                        advertised_bytes, head=commits[kind]
                    )
                    self.assertTrue(selected["ok"], selected)
                    self.assertEqual(selected["result"]["ref"], expected_ref)

                    clone_root = root / f"clone-{kind}"
                    clone_root.mkdir()
                    result = self.ruby_call(
                        "clone_and_fetch",
                        {
                            "remote_url": remote_url,
                            "selected_ref": selected["result"]["ref"],
                            "expected_head": commits[kind],
                            "root": str(clone_root),
                            "env": self.clone_env(),
                        },
                    )
                    self.assertTrue(result["ok"], result)
                    clone = Path(result["result"])
                    fetched = self.git(
                        "rev-parse",
                        "refs/n64game/public-concept-authority^{commit}",
                        cwd=clone,
                    ).stdout.strip()
                    self.assertEqual(fetched, commits[kind])
                    self.assertFalse((clone / "fixture.txt").exists(), "clone must remain no-checkout")
                    tag = self.git(
                        "show-ref", "--verify", "--quiet", "refs/tags/poison-tag",
                        cwd=clone, check=False
                    )
                    self.assertNotEqual(tag.returncode, 0, "clone/fetch must remain no-tags")

    def test_clone_and_fetch_rejects_ref_moved_or_disappeared_after_selection(self) -> None:
        self.assertIsNotNone(GIT_LFS, "git-lfs is required by the production authority path")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            remote_url, remote, commits = self.make_file_remote(root)
            advertised_bytes = self.advertised_from_remote(remote_url)

            branch = self.select(advertised_bytes, head=commits["branch"])
            self.assertTrue(branch["ok"], branch)
            self.git(
                "--git-dir",
                str(remote),
                "update-ref",
                branch["result"]["ref"],
                commits["pull_head"],
            )
            moved_root = root / "moved"
            moved_root.mkdir()
            moved = self.ruby_call(
                "clone_and_fetch",
                {
                    "remote_url": remote_url,
                    "selected_ref": branch["result"]["ref"],
                    "expected_head": commits["branch"],
                    "root": str(moved_root),
                    "env": self.clone_env(),
                },
            )
            self.assert_issue(moved, "moved or disappeared")

            pull_head = self.select(advertised_bytes, head=commits["pull_head"])
            self.assertTrue(pull_head["ok"], pull_head)
            self.git(
                "--git-dir", str(remote), "update-ref", "-d", pull_head["result"]["ref"]
            )
            disappeared_root = root / "disappeared"
            disappeared_root.mkdir()
            disappeared = self.ruby_call(
                "clone_and_fetch",
                {
                    "remote_url": remote_url,
                    "selected_ref": pull_head["result"]["ref"],
                    "expected_head": commits["pull_head"],
                    "root": str(disappeared_root),
                    "env": self.clone_env(),
                },
            )
            self.assert_issue(disappeared, "moved/disappeared")

    def test_clone_and_fetch_uses_only_explicit_env_under_poisoned_ci_and_git_state(self) -> None:
        self.assertIsNotNone(GIT_LFS, "git-lfs is required by the production authority path")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            remote_url, _remote, commits = self.make_file_remote(root)
            selected_ref = "refs/pull/11/merge"
            clone_root = root / "poisoned"
            clone_root.mkdir()
            result = self.ruby_call(
                "clone_and_fetch",
                {
                    "remote_url": remote_url,
                    "selected_ref": selected_ref,
                    "expected_head": commits["pull_merge"],
                    "root": str(clone_root),
                    "env": self.clone_env(),
                },
                extra_env={
                    "PATH": "/definitely/not/a/tool/path",
                    "CI": "true",
                    "GITHUB_SHA": commits["branch"],
                    "GITHUB_REF": "refs/tags/poison-tag",
                    "GIT_DIR": "/definitely/not/a/repository",
                    "GIT_WORK_TREE": "/definitely/not/a/worktree",
                    "GIT_INDEX_FILE": "/definitely/not/an/index",
                    "GIT_OBJECT_DIRECTORY": "/definitely/not/objects",
                    "GIT_ALTERNATE_OBJECT_DIRECTORIES": "/definitely/not/alternate-objects",
                    "GIT_EXEC_PATH": "/definitely/not/git-core",
                    "GH_TOKEN": "must-not-be-used",
                    "GITHUB_TOKEN": "must-not-be-used",
                },
            )
            self.assertTrue(result["ok"], result)
            clone = Path(result["result"])
            fetched = self.git(
                "rev-parse",
                "refs/n64game/public-concept-authority^{commit}",
                cwd=clone,
            ).stdout.strip()
            self.assertEqual(fetched, commits["pull_merge"])

    @staticmethod
    def control_transaction() -> dict[str, Any]:
        # PUBLIC_MERGE intentionally differs from CONTROL. This is the PR-merge
        # case: the advertised commit may differ from A while its tree is exact.
        return {
            "public_head": PUBLIC_MERGE,
            "control_commit": CONTROL,
            "parents": [HEAD],
            "reviewed_payload_commit": HEAD,
            "changed_paths": ["docs/VISUAL_BENCHMARK_APPROVAL.md"],
            "current_descends_from_control": True,
            "control_public": True,
            "control_bytes_equal": True,
            "public_tree_equal": True,
        }

    def test_payload_to_control_transaction_accepts_public_merge_with_identical_tree(self) -> None:
        result = self.ruby_call("control_transaction", self.control_transaction())
        self.assertEqual(result, {"ok": True, "result": True})

    def test_git_path_history_resolves_control_a_through_identical_tree_two_parent_merge(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / "repo"
            repo.mkdir()
            self.git("init", "-q", cwd=repo)
            control_path = "docs/VISUAL_BENCHMARK_APPROVAL.md"
            control = repo / control_path
            control.parent.mkdir(parents=True)
            control.write_text("Decision: PENDING\n", encoding="utf-8")
            (repo / "payload.txt").write_text("payload P\n", encoding="utf-8")
            self.git("add", "--", ".", cwd=repo)
            self.git("commit", "-q", "-m", "payload P", cwd=repo)
            payload_p = self.git("rev-parse", "HEAD", cwd=repo).stdout.strip()

            control.write_text("Decision: REVIEW_REQUIRED\n", encoding="utf-8")
            self.git("add", "--", control_path, cwd=repo)
            self.git("commit", "-q", "-m", "control A", cwd=repo)
            control_a = self.git("rev-parse", "HEAD", cwd=repo).stdout.strip()

            self.git("checkout", "-q", "-b", "side", payload_p, cwd=repo)
            (repo / "side.txt").write_text("independent parent\n", encoding="utf-8")
            self.git("add", "--", "side.txt", cwd=repo)
            self.git("commit", "-q", "-m", "side parent", cwd=repo)
            side = self.git("rev-parse", "HEAD", cwd=repo).stdout.strip()

            control_tree = self.git(
                "rev-parse", f"{control_a}^{{tree}}", cwd=repo
            ).stdout.strip()
            public_h = self.git(
                "commit-tree",
                control_tree,
                "-p",
                control_a,
                "-p",
                side,
                cwd=repo,
                input_text="synthetic PR merge H\n",
            ).stdout.strip()

            resolved = self.git(
                "rev-list", "-1", public_h, "--", control_path, cwd=repo
            ).stdout.strip()
            self.assertEqual(resolved, control_a)
            self.assertNotEqual(public_h, control_a)
            self.assertEqual(
                self.git("rev-parse", f"{public_h}^{{tree}}", cwd=repo).stdout.strip(),
                control_tree,
            )
            self.assertEqual(
                self.git("rev-list", "--parents", "-n", "1", public_h, cwd=repo)
                .stdout.strip()
                .split(),
                [public_h, control_a, side],
            )

            result = self.ruby_call(
                "control_transaction",
                {
                    "public_head": public_h,
                    "control_commit": resolved,
                    "parents": [payload_p],
                    "reviewed_payload_commit": payload_p,
                    "changed_paths": [control_path],
                    "current_descends_from_control": True,
                    "control_public": True,
                    "control_bytes_equal": True,
                    "public_tree_equal": True,
                },
            )
            self.assertEqual(result, {"ok": True, "result": True})

    def test_payload_to_control_transaction_deaths_are_independent(self) -> None:
        cases: dict[str, tuple[Any, str]] = {
            "wrong_parent": (
                lambda value: value.__setitem__("parents", [OTHER]),
                "parent differs",
            ),
            "merge_control_commit": (
                lambda value: value.__setitem__("parents", [HEAD, OTHER]),
                "exactly one parent",
            ),
            "extra_changed_path": (
                lambda value: value.__setitem__(
                    "changed_paths",
                    ["docs/VISUAL_BENCHMARK_APPROVAL.md", "assets-src/hidden.blend"],
                ),
                "change only docs/VISUAL_BENCHMARK_APPROVAL.md",
            ),
            "non_descendant": (
                lambda value: value.__setitem__("current_descends_from_control", False),
                "does not descend",
            ),
            "missing_public_control": (
                lambda value: value.__setitem__("control_public", False),
                "not present in the verified public clone",
            ),
            "differing_control_bytes": (
                lambda value: value.__setitem__("control_bytes_equal", False),
                "control bytes",
            ),
            "descendant_changed_tree": (
                lambda value: value.__setitem__("public_tree_equal", False),
                "tree",
            ),
        }
        for label, (mutate, expected) in cases.items():
            with self.subTest(label=label):
                payload = deepcopy(self.control_transaction())
                mutate(payload)
                self.assert_issue(
                    self.ruby_call("control_transaction", payload), expected
                )

    def test_validator_integrates_authority_without_ci_or_raw_sha_shortcuts(self) -> None:
        validator = (ROOT / "scripts/validate-asset-contract").read_text(encoding="utf-8")
        self.assertIn(
            'require ROOT.join("lib/n64game/public_commit_authority").to_s', validator
        )
        execution_paths_match = re.search(
            r"PUBLIC_AUTHORITY_EXECUTION_PATHS\s*=\s*%w\[(.*?)\]\.freeze",
            validator,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(execution_paths_match)
        self.assertIn(
            "lib/n64game/libdragon_sprite_contract.rb",
            execution_paths_match.group(1).split(),
        )
        adapter_match = re.search(
            r"^def prepare_fresh_advertised_public_head\b.*?(?=^def validate_staged_control_transaction\b)",
            validator,
            flags=re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(adapter_match)
        adapter = adapter_match.group(0)

        self.assertIn(
            '"status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignore-submodules=none"',
            adapter,
        )
        self.assertGreaterEqual(adapter.count("unsetenv_others: true"), 2)
        self.assertIn('"ls-remote", "--refs", public_url', adapter)
        self.assertIn(
            '"refs/heads/*", "refs/pull/*/head", "refs/pull/*/merge"', adapter
        )
        self.assertNotIn('"refs/tags/*"', adapter)
        self.assertIn(
            "N64Game::PublicCommitAuthority.clone_and_fetch!", adapter
        )
        self.assertIn(
            'remote_url: public_url, selected_ref: authority["ref"], expected_head: local_head',
            adapter,
        )
        self.assertIn("root: root, env: public_clone_env", adapter)
        self.assertNotIn("Open3.capture3", adapter)
        self.assertNotIn("GITHUB_SHA", adapter)
        self.assertNotIn("GITHUB_REF", adapter)

        slug_adapter = re.search(
            r"^def same_repo_slug\b.*?^end$", validator, flags=re.DOTALL | re.MULTILINE
        )
        self.assertIsNotNone(slug_adapter)
        self.assertIn("unsetenv_others: true", slug_adapter.group(0))

        helper = (ROOT / "lib/n64game/public_commit_authority.rb").read_text(
            encoding="utf-8"
        )
        clone_match = re.search(
            r"^\s*def clone_and_fetch!.*?(?=^\s*def validate_control_transaction!)",
            helper,
            flags=re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(clone_match)
        clone_adapter = clone_match.group(0)
        self.assertIn(
            'command_prefix = ["/usr/bin/git", "-c", "credential.helper=", "-c", "http.extraHeader="]',
            clone_adapter,
        )
        self.assertIn(
            '"clone", "--no-checkout", "--no-tags", "--quiet"', clone_adapter
        )
        self.assertIn(
            '"fetch", "--force", "--no-tags", remote_url,\n'
            '        "+#{selected_ref}:#{destination_ref}"',
            clone_adapter,
        )
        self.assertIn("verify_fetched_ref!", clone_adapter)
        self.assertIn(
            '"lfs", "fetch", remote_url, expected_head, destination_ref',
            clone_adapter,
        )
        self.assertGreaterEqual(clone_adapter.count("unsetenv_others: true"), 4)
        direct_fetches = re.findall(
            r'\*command_prefix,\s*"fetch",(.*?)\n\s*\)',
            clone_adapter,
            flags=re.DOTALL,
        )
        self.assertEqual(len(direct_fetches), 1, direct_fetches)
        self.assertIn("selected_ref", direct_fetches[0])
        self.assertNotIn("expected_head", direct_fetches[0])

        credential_adapter = re.search(
            r"^def public_git_capture\b.*?(?=^def prepare_fresh_public_clone\b)",
            validator,
            flags=re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(credential_adapter)
        credential_body = credential_adapter.group(0)
        for token in (
            '"credential.helper="',
            '"http.extraHeader="',
            "public_clone_env",
            "unsetenv_others: true",
        ):
            self.assertIn(token, credential_body)
        self.assertIn('"GITHUB_TOKEN" => nil', validator)
        self.assertIn('"GH_TOKEN" => nil', validator)
        self.assertIn('PUBLIC_GIT_BINARY = "/usr/bin/git".freeze', validator)
        self.assertIn(
            'PUBLIC_CLONE_PATH = "/usr/bin:/bin:/opt/homebrew/bin:/usr/local/bin".freeze',
            validator,
        )
        clone_env_match = re.search(
            r"^def public_clone_env\b.*?^end$", validator, flags=re.DOTALL | re.MULTILINE
        )
        self.assertIsNotNone(clone_env_match)
        self.assertIn('"PATH" => PUBLIC_CLONE_PATH', clone_env_match.group(0))
        self.assertNotIn('ENV.fetch("PATH"', clone_env_match.group(0))

    def test_validator_binds_fresh_public_tree_concepts_and_staged_transaction(self) -> None:
        validator = (ROOT / "scripts/validate-asset-contract").read_text(encoding="utf-8")
        transaction_match = re.search(
            r"^def validate_staged_control_transaction\b.*?(?=^def production_root_paths\b)",
            validator,
            flags=re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(transaction_match)
        transaction = transaction_match.group(0)
        self.assertIn('"rev-list", "-1", public_head, "--", control_path', transaction)
        self.assertIn('"diff", "--name-only", "-z", parents.first, control_commit', transaction)
        self.assertIn('"merge-base", "--is-ancestor", control_commit, public_head', transaction)
        self.assertIn('"#{control_commit}^{tree}"', transaction)
        self.assertIn('"#{public_head}^{tree}"', transaction)
        self.assertIn("public_tree_equal:", transaction)
        self.assertIn(
            "validate_staged_control_transaction(preapproval_public_authority, preapproval_commit)",
            validator,
        )

        for path in (
            "docs/ART_BIBLE.md",
            "docs/ASSET_INVENTORY.md",
            "docs/ASSET_LEDGER.md",
            "docs/ASSET_REVIEW_TEMPLATES.md",
            "docs/TOOLCHAIN.md",
            "docs/VISUAL_BENCHMARK_APPROVAL.md",
        ):
            self.assertIn(path, validator)
        self.assertIn('toolchain = read("docs/TOOLCHAIN.md")', validator)
        self.assertIn('"ASSET_REVIEW_TEMPLATES" => reviews, "TOOLCHAIN" => toolchain,', validator)
        for token in (
            "Gate 4 derives incremental authoring state from the eight positional aggregate pairs",
            "A workflow may remain pending with a recipe but cannot populate without one",
            "all 392 gates complete on one global build",
        ):
            self.assertIn(token, validator)
        self.assertIn("PUBLIC_CONCEPT_CONTRACT_PATHS.each", validator)
        self.assertIn("public-head concept contract #{path}", validator)
        self.assertIn("fresh_clone: concept_clone", validator)
        self.assertIn("public_production_paths = tree_entries", validator)
        self.assertIn("local_production_paths = production_root_paths", validator)
        self.assertIn("local_production_paths == public_production_paths", validator)
        self.assertIn('validate_shared_lifecycle_branch(\n        "public_concept"', validator)
        self.assertIn(
            'error("preapproval public workflow requires a populated ROM recipe aggregate") unless preapproval_recipe_binding',
            validator,
        )


if __name__ == "__main__":
    unittest.main()
