from __future__ import annotations

import json
import hashlib
import re
import shutil
import subprocess
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUBY = "/usr/bin/ruby"


class AuthoringReceiptAdapterTests(unittest.TestCase):
    def ruby_policy(self, method: str, payload: dict[str, object]) -> object:
        program = f"""
          require 'json'
          require 'n64game/authoring_stack_receipt'
          input = JSON.parse(STDIN.read)
          result = N64Game::AuthoringStackReceipt.{method}(**input.transform_keys(&:to_sym))
          STDOUT.write(JSON.generate(result))
        """
        completed = subprocess.run(
            [RUBY, "--disable-gems", "-I", str(ROOT / "lib"), "-e", program],
            input=json.dumps(payload),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    @staticmethod
    def g2_placement() -> dict[str, object]:
        path = "review/echo.quarrune/g2/AUTHORING_STACK_RECEIPT.txt"
        evidence = "review/echo.quarrune/g2/EVIDENCE_MANIFEST.sha256"
        return {
            "scope_id": "echo.quarrune",
            "gate": "G2",
            "applicable": True,
            "evidence_manifest_path": evidence,
            "evidence_entries": [
                {
                    "path": path,
                    "role": "authoring.stack_receipt",
                    "capture": "-",
                    "build": "-",
                    "kind": "git",
                    "mode": "100644",
                }
            ],
            "direct_owner": evidence,
            "source_owned_paths": [],
            "output_owned_paths": [],
            "build_id": "-",
        }

    def test_nested_source_blend_applies_without_unrelated_payload_or_output_overreach(self) -> None:
        nested = {
            "canonical_asset_scope": True,
            "profile": "UI_FONT_IMAGE",
            "source_paths": ["assets-src/ui/ui.panel/NESTED_MANIFEST.sha256", "assets-src/ui/ui.panel/model.BLEND"],
        }
        unrelated = {
            "canonical_asset_scope": True,
            "profile": "UI_FONT_IMAGE",
            "source_paths": ["assets-src/ui/ui.panel/layout.json"],
        }
        self.assertTrue(self.ruby_policy("applicable?", nested))
        self.assertFalse(self.ruby_policy("applicable?", unrelated))
        unrelated["source_paths"] = [None, 7, {"path": "unrelated.blend"}]
        self.assertFalse(self.ruby_policy("applicable?", unrelated))
        unrelated["profile"] = "RIGGED_MODEL"
        self.assertTrue(self.ruby_policy("applicable?", unrelated))
        unrelated["canonical_asset_scope"] = False
        self.assertFalse(self.ruby_policy("applicable?", unrelated))

    def test_exact_g2_placement_passes_and_mapped_mutations_fail(self) -> None:
        baseline = self.g2_placement()
        self.assertEqual(self.ruby_policy("placement_issues", baseline), [])

        mutations: list[tuple[str, object, str]] = []

        def case(name: str, mutate: object, expected: str) -> None:
            mutations.append((name, mutate, expected))

        case("missing", lambda value: value.__setitem__("evidence_entries", []), "exactly the canonical")
        case(
            "wrong_path",
            lambda value: value["evidence_entries"][0].__setitem__(  # type: ignore[index]
                "path", "review/echo.quarrune/g2/nested/AUTHORING_STACK_RECEIPT.txt"
            ),
            "exactly the canonical",
        )
        case("nested_owner", lambda value: value.__setitem__("direct_owner", "review/echo.quarrune/g2/NESTED_MANIFEST.sha256"), "direct evidence")
        case("wrong_role", lambda value: value["evidence_entries"][0].__setitem__("role", "gate.note"), "role mismatch")  # type: ignore[index]
        case("capture", lambda value: value["evidence_entries"][0].__setitem__("capture", "stack"), "capture token")  # type: ignore[index]
        case("manifest_build", lambda value: value["evidence_entries"][0].__setitem__("build", "n64game-real-001"), "build token")  # type: ignore[index]
        case("g2_row_build", lambda value: value.__setitem__("build_id", "n64game-real-001"), "G2 gate row build must be -")
        case("lfs", lambda value: value["evidence_entries"][0].__setitem__("kind", "lfs"), "ordinary Git")  # type: ignore[index]
        case("executable", lambda value: value["evidence_entries"][0].__setitem__("mode", "100755"), "mode 100644")  # type: ignore[index]
        receipt_path = "review/echo.quarrune/g2/AUTHORING_STACK_RECEIPT.txt"
        case("source_owned", lambda value: value.__setitem__("source_owned_paths", [receipt_path]), "source-manifest-owned")
        case("output_owned", lambda value: value.__setitem__("output_owned_paths", [receipt_path]), "output-manifest-owned")
        case("nonapplicable", lambda value: value.__setitem__("applicable", False), "forbidden")
        case("wrong_gate", lambda value: value.__setitem__("gate", "G3"), "forbidden")
        case("wrong_scope", lambda value: value.__setitem__("scope_id", "echo.ayselor"), "exactly the canonical")

        for name, mutate, expected in mutations:
            with self.subTest(mutation=name):
                value = deepcopy(baseline)
                mutate(value)  # type: ignore[operator]
                issues = self.ruby_policy("placement_issues", value)
                self.assertTrue(any(expected in issue for issue in issues), issues)

    def test_g5_manifest_projection_is_exact_even_before_exporter_can_unlock(self) -> None:
        value = self.g2_placement()
        value["gate"] = "G5"
        value["build_id"] = "n64game-g4-6531e405"
        value["evidence_manifest_path"] = "review/echo.quarrune/g5/EVIDENCE_MANIFEST.sha256"
        value["direct_owner"] = value["evidence_manifest_path"]
        value["evidence_entries"][0].update(  # type: ignore[index]
            {
                "path": "review/echo.quarrune/g5/AUTHORING_STACK_RECEIPT.txt",
                "build": value["build_id"],
            }
        )
        self.assertEqual(self.ruby_policy("placement_issues", value), [])
        value["evidence_entries"][0]["build"] = "n64game-other-001"  # type: ignore[index]
        self.assertIn("authoring receipt manifest build token mismatch", self.ruby_policy("placement_issues", value))

    @staticmethod
    def universe() -> dict[str, object]:
        path = "review/echo.quarrune/g2/AUTHORING_STACK_RECEIPT.txt"
        return {
            "expected_paths": [path],
            "tree_entries": [{"path": path, "mode": "100644", "type": "blob"}],
            "manifest_entries": [
                {"path": path, "role": "authoring.stack_receipt", "build": "-", "capture": "-", "kind": "git"}
            ],
        }

    def test_reviewed_tree_and_role_universe_rejects_orphans_case_variants_and_modes(self) -> None:
        baseline = self.universe()
        self.assertEqual(self.ruby_policy("universe_issues", baseline), [])
        extra_path = "review/echo.quarrune/g5/AUTHORING_STACK_RECEIPT.txt"
        mutations = {
            "missing_tree": lambda value: value.__setitem__("tree_entries", []),
            "extra_gate": lambda value: value["tree_entries"].append({"path": extra_path, "mode": "100644", "type": "blob"}),  # type: ignore[union-attr]
            "case_variant": lambda value: value["tree_entries"][0].__setitem__("path", "review/echo.quarrune/g2/authoring_stack_receipt.TXT"),  # type: ignore[index]
            "orphan": lambda value: value["tree_entries"].append({"path": "review/orphan/AUTHORING_STACK_RECEIPT.txt", "mode": "100644", "type": "blob"}),  # type: ignore[union-attr]
            "executable": lambda value: value["tree_entries"][0].__setitem__("mode", "100755"),  # type: ignore[index]
            "submodule": lambda value: value["tree_entries"][0].update({"mode": "160000", "type": "commit"}),  # type: ignore[index]
            "missing_manifest": lambda value: value.__setitem__("manifest_entries", []),
            "wrong_role": lambda value: value["manifest_entries"][0].__setitem__("role", "gate.note"),  # type: ignore[index]
            "hidden_role": lambda value: value["manifest_entries"][0].__setitem__("path", "review/echo.quarrune/g2/NOTE.txt"),  # type: ignore[index]
            "extra_role": lambda value: value["manifest_entries"].append({"path": "review/other/NOTE.txt", "role": "authoring.stack_receipt"}),  # type: ignore[union-attr]
            "duplicate_expectation": lambda value: value["expected_paths"].append(value["expected_paths"][0]),  # type: ignore[union-attr,index]
            "malformed_expectation": lambda value: value["expected_paths"].append(None),  # type: ignore[union-attr]
            "malformed_manifest_entry": lambda value: value.__setitem__("manifest_entries", [True]),
            "malformed_manifest_path": lambda value: value.__setitem__(
                "manifest_entries", [{"path": 7, "role": "authoring.stack_receipt"}]
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(mutation=name):
                value = deepcopy(baseline)
                mutate(value)
                self.assertNotEqual(self.ruby_policy("universe_issues", value), [])

    def test_live_production_adapter_accepts_frozen_g2_receipt_under_system_ruby(self) -> None:
        required_modes = {
            "scripts/validate-asset-contract": 0o755,
            "lib/n64game/authoring_stack_receipt.rb": 0o644,
            "lib/n64game/public_commit_authority.rb": 0o644,
            "lib/n64game/libdragon_sprite_contract.rb": 0o644,
            "lib/n64game/tiny3d_package_contract.rb": 0o644,
            "config/toolchain.lock.json": 0o644,
            "scripts/check-authoring-stack": 0o755,
            "scripts/record-authoring-stack-receipt": 0o755,
            "tools/n64game_authoring.py": 0o644,
            "tools/n64game_authoring_receipt.py": 0o644,
        }
        checker_paths = sorted(
            (
                "scripts/check-authoring-stack",
                "scripts/record-authoring-stack-receipt",
                "tools/n64game_authoring.py",
                "tools/n64game_authoring_receipt.py",
            )
        )
        checker = hashlib.sha256(b"n64game-authoring-checker-bundle-v1\n")
        for relative in checker_paths:
            checker.update(
                f"{relative}\t{hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()}\n".encode()
            )
        lock_sha = hashlib.sha256((ROOT / "config/toolchain.lock.json").read_bytes()).hexdigest()
        source_sha = "a" * 64
        receipt_path = "review/echo.quarrune/g2/AUTHORING_STACK_RECEIPT.txt"
        fields = (
            ("schema", "n64game-authoring-stack-receipt-v1"),
            ("scope_id", "echo.quarrune"),
            ("gate", "G2"),
            ("source_manifest_sha256", source_sha),
            ("output_manifest_sha256", "NONE"),
            ("build_id", "-"),
            ("toolchain_lock_sha256", lock_sha),
            ("checker_sha256", checker.hexdigest()),
            ("blender_executable_sha256", "8156431a9b9ec1daf49bccea4bd92f327f6efc1ca330d5103881580f3e7773ef"),
            ("blender_seal", "DEEP_STRICT_EXPLICIT_REQUIREMENT_PASS"),
            ("fast64_source_manifest_sha256", "14bb6c7b527ba364fa5e2a5011779ddd24c61f998c79c120f28d895d92e62e6b"),
            ("probe_mode", "ISOLATED_COPY_ENABLED_LOADED_NO_INHERITED_ENV"),
            ("result", "PASS"),
            ("checked_at", "2026-07-19T12:34:56Z"),
        )
        receipt = "".join(f"{key}: {value}\n" for key, value in fields).encode()

        with tempfile.TemporaryDirectory() as temporary:
            clone = Path(temporary) / "repo"
            clone.mkdir()
            for relative, mode in required_modes.items():
                source = ROOT / relative
                actual_mode = source.stat().st_mode & 0o777
                self.assertEqual(actual_mode, mode, relative)
                target = clone / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                target.chmod(actual_mode)
            target = clone / receipt_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(receipt)
            target.chmod(0o644)
            git_env = {
                "PATH": "/usr/bin:/bin",
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
                "GIT_CONFIG_GLOBAL": "/dev/null",
                "GIT_CONFIG_NOSYSTEM": "1",
            }
            subprocess.run(["git", "init", "-q"], cwd=clone, env=git_env, check=True)
            subprocess.run(["git", "add", "--", "."], cwd=clone, env=git_env, check=True)
            commit_env = {
                **git_env,
                "GIT_AUTHOR_NAME": "N64Game Test",
                "GIT_AUTHOR_EMAIL": "n64game-test@example.invalid",
                "GIT_COMMITTER_NAME": "N64Game Test",
                "GIT_COMMITTER_EMAIL": "n64game-test@example.invalid",
            }
            subprocess.run(
                ["git", "commit", "-q", "-m", "frozen authoring fixture"],
                cwd=clone,
                env=commit_env,
                check=True,
            )
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=clone, env=git_env, text=True).strip()
            program = r"""
              require 'json'
              validator = ARGV.fetch(0)
              source = File.binread(validator)
              marker = "\nart = read(\"docs/ART_BIBLE.md\")\n"
              prefix, remainder = source.split(marker, 2)
              abort "validator main marker missing" unless prefix && remainder
              eval(prefix, TOPLEVEL_BINDING, validator, 1)
              evidence_path = 'review/echo.quarrune/g2/EVIDENCE_MANIFEST.sha256'
              receipt_path = 'review/echo.quarrune/g2/AUTHORING_STACK_RECEIPT.txt'
              entry = {
                path: receipt_path, role: 'authoring.stack_receipt', capture: '-',
                build: '-', kind: 'git', mode: '100644'
              }
              local_context = new_manifest_context
              local_context[:manifests][evidence_path] = [entry]
              local_context[:entries][receipt_path] = entry
              local_context[:member_owner][receipt_path] = evidence_path
              validate_authoring_gate_receipt(
                scope: 'echo.quarrune', gate: 'G2', applicable: true,
                evidence_path: evidence_path, row: {
                  'build_id' => '-', 'decided_at' => '2026-07-19T12:35:00Z'
                },
                source_digest: 'a' * 64, output_digest: 'NONE',
                commit: ARGV.fetch(2), fresh_clone: ARGV.fetch(1),
                local_context: local_context, source_context: new_manifest_context,
                label: 'live system-ruby adapter fixture'
              )
              STDOUT.write(JSON.generate(ERRORS))
            """
            completed = subprocess.run(
                [RUBY, "--disable-gems", "-e", program, str(ROOT / "scripts/validate-asset-contract"), str(clone), commit],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                env=git_env,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout), [])

    def test_required_root_modes_match_the_real_git_index(self) -> None:
        program = """
          require 'json'
          require 'n64game/authoring_stack_receipt'
          STDOUT.write(JSON.generate(N64Game::AuthoringStackReceipt::ROOT_REQUIRED_MODES))
        """
        ruby = subprocess.run(
            [RUBY, "--disable-gems", "-I", str(ROOT / "lib"), "-e", program],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
        )
        self.assertEqual(ruby.returncode, 0, ruby.stderr)
        required = json.loads(ruby.stdout)
        indexed = subprocess.run(
            ["git", "ls-files", "--stage", "--", *required.keys()],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env={
                "PATH": "/usr/bin:/bin",
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
                "GIT_CONFIG_GLOBAL": "/dev/null",
                "GIT_CONFIG_NOSYSTEM": "1",
            },
        )
        self.assertEqual(indexed.returncode, 0, indexed.stderr)
        observed = {
            line.split(None, 3)[3]: line.split(None, 1)[0]
            for line in indexed.stdout.splitlines()
        }
        self.assertEqual(observed, required)

    def test_production_adapter_binds_historical_material_and_all_three_lifecycle_paths(self) -> None:
        validator = (ROOT / "scripts/validate-asset-contract").read_text(encoding="utf-8")
        self.assertIn('require ROOT.join("lib/n64game/authoring_stack_receipt").to_s', validator)
        self.assertIn("source_context: nil", validator)
        self.assertIn("[profile, tier] != canonical_profile_tier", validator)
        self.assertIn("manifest_owned_paths(source_context, canonical_source_path)", validator)
        self.assertIn("source_paths: source_owned_paths", validator)
        self.assertNotIn("source_paths: payload_context[:closure]", validator)
        for label in (
            "preapproval authoring receipts",
            "approved authoring receipts",
            "current post-approval authoring receipts",
            "current unchanged post-approval authoring receipts",
        ):
            self.assertIn(label, validator)
        adapter = re.search(
            r"def validate_authoring_gate_receipt.*?^end$", validator, flags=re.DOTALL | re.MULTILINE
        )
        self.assertIsNotNone(adapter)
        body = adapter.group(0)
        for token in (
            "materialized_commit_file",
            "commit",
            "fresh_clone",
            "allow_lfs: false",
            'material[:kind] == :git',
            'material[:mode] == expected_mode',
            'receipt_material[:mode] == "100644"',
            "AuthoringStackReceipt.validate",
        ):
            self.assertIn(token, body)
        root_paths = {
            "scripts/validate-asset-contract": "100755",
            "lib/n64game/authoring_stack_receipt.rb": "100644",
            "lib/n64game/public_commit_authority.rb": "100644",
            "lib/n64game/libdragon_sprite_contract.rb": "100644",
            "lib/n64game/tiny3d_package_contract.rb": "100644",
            "config/toolchain.lock.json": "100644",
            "scripts/check-authoring-stack": "100755",
            "scripts/record-authoring-stack-receipt": "100755",
            "tools/n64game_authoring.py": "100644",
            "tools/n64game_authoring_receipt.py": "100644",
        }
        for path, mode in root_paths.items():
            self.assertIn(f'"{path}" => "{mode}"', (ROOT / "lib/n64game/authoring_stack_receipt.rb").read_text(encoding="utf-8"))

    def test_lfs_text_materialization_and_gate5_export_remain_fail_closed(self) -> None:
        validator = (ROOT / "scripts/validate-asset-contract").read_text(encoding="utf-8")
        materializer = re.search(
            r"def materialized_commit_file.*?^end$", validator, flags=re.DOTALL | re.MULTILINE
        )
        self.assertIsNotNone(materializer)
        self.assertRegex(materializer.group(0), r"unless allow_lfs\s+error\(.*?\)\s+return nil")
        self.assertIn("mode: tree_mode", materializer.group(0))
        consumer = (ROOT / "lib/n64game/authoring_stack_receipt.rb").read_text(encoding="utf-8")
        self.assertRegex(consumer, r"(?m)^    GATE5_EXPORT_IMPLEMENTED = false$")
        self.assertRegex(consumer, r'(?m)^    APPROVED_GATE5_EXPORTER_SHA256 = "PENDING"\.freeze$')


if __name__ == "__main__":
    unittest.main()
