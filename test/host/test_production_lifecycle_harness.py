from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER_RELATIVE = Path("scripts/test-asset-lifecycle-production")
KERNEL_RELATIVE = Path("lib/n64game/asset_lifecycle_contract.rb")
FIXTURE_ROOT_RELATIVE = Path("test/fixtures/asset_lifecycle_production")
MANIFEST_RELATIVE = FIXTURE_ROOT_RELATIVE / "PRODUCTION_LIFECYCLE_HARNESS_MANIFEST.sha256"
BRANCHES = ["public_concept", "populated", "approved", "repair", "generated_child", "move_pair", "h2", "release"]
NEGATIVE_CASES = [
    "public_concept.no_concept",
    "public_concept.active_row",
    "public_concept.nonpending_aggregate",
    "public_concept.false_authority",
    "public_concept.malformed_authority",
    "public_concept.malformed_ref",
    "public_concept.advanced_id",
    "populated.aggregate_count",
    "populated.split_core",
    "populated.optional_without_core",
    "populated.zero_active_rows",
    "populated.malformed_pending_pair",
    "populated.rollup_mask_mismatch",
    "populated.evidence_incomplete",
    "populated.rollup_digest_crossbind",
    "populated.rollup_build_crossbind",
    "populated.rollup_gate_vector",
    "populated.evidence_build_crossbind",
    "populated.pending_repair_only",
    "populated.active_build_pending",
    "approved.inherited_completion",
    "approved.rollup_non_rom_g1",
    "approved.rollup_static_state_g1",
    "approved.pending_build",
    "repair.out_of_range_basis",
    "repair.non_string_token",
    "generated_child.noncanonical_tuple",
    "generated_child.extra_row",
    "move_pair.non_hash_child",
    "move_pair.missing_asset_id",
    "h2.non_hash_pass",
    "release.failed_workflow",
]
LIVE_ONLY_ADAPTERS = [
    "github_api",
    "signed_git_tags",
    "git_lfs_materialization",
    "advertised_ref_fresh_clone",
    "benchmark_control_transaction",
    "ffprobe_media_decode",
    "ares_execution",
    "rom_rebuild",
]


class ProductionLifecycleHarnessTests(unittest.TestCase):
    def run_harness(self, root: Path = ROOT) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "/usr/bin/ruby",
                "--disable-gems",
                str((root / RUNNER_RELATIVE).resolve()),
                "--manifest",
                str((root / MANIFEST_RELATIVE).resolve()),
            ],
            cwd=root,
            env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def copied_harness(self, destination: Path) -> Path:
        root = destination / "repo"
        (root / RUNNER_RELATIVE.parent).mkdir(parents=True)
        (root / KERNEL_RELATIVE.parent).mkdir(parents=True)
        shutil.copy2(ROOT / RUNNER_RELATIVE, root / RUNNER_RELATIVE)
        shutil.copy2(ROOT / KERNEL_RELATIVE, root / KERNEL_RELATIVE)
        shutil.copytree(ROOT / FIXTURE_ROOT_RELATIVE, root / FIXTURE_ROOT_RELATIVE)
        os.chmod(root / RUNNER_RELATIVE, 0o755)
        return root

    @staticmethod
    def rewrite_manifest_member(root: Path, member_relative: str) -> None:
        member = root / member_relative
        data = member.read_bytes()
        manifest = root / MANIFEST_RELATIVE
        rows = []
        for line in manifest.read_text(encoding="utf-8").splitlines():
            fields = line.split("\t")
            if fields[0] == member_relative:
                fields[1] = str(len(data))
                fields[2] = hashlib.sha256(data).hexdigest()
            rows.append("\t".join(fields))
        manifest.write_bytes(("\n".join(rows) + "\n").encode("utf-8"))

    def test_shared_kernel_harness_passes_with_exact_branch_and_death_receipt(self) -> None:
        result = self.run_harness()
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(
            receipt,
            {
                "schema": "n64game-production-lifecycle-harness-v1",
                "authority": "PRODUCTION_SHARED_KERNEL_BRANCH_COVERAGE",
                "result": "PASS",
                "manifest_sha256": hashlib.sha256((ROOT / MANIFEST_RELATIVE).read_bytes()).hexdigest(),
                "kernel_sha256": hashlib.sha256((ROOT / KERNEL_RELATIVE).read_bytes()).hexdigest(),
                "branch_ids": BRANCHES,
                "negative_case_ids": NEGATIVE_CASES,
                "live_adapter_coverage": "EXCLUDED_BY_DESIGN",
                "live_only_adapters": LIVE_ONLY_ADAPTERS,
            },
        )

    def test_manifest_byte_binds_only_kernel_runner_and_eight_cases(self) -> None:
        lines = (ROOT / MANIFEST_RELATIVE).read_text(encoding="utf-8").splitlines()
        paths = []
        for line in lines:
            fields = line.split("\t")
            self.assertEqual(len(fields), 6)
            path, count, digest, build, capture, role = fields
            member = ROOT / path
            data = member.read_bytes()
            self.assertEqual(len(data), int(count))
            self.assertEqual(hashlib.sha256(data).hexdigest(), digest)
            self.assertEqual((build, capture), ("build:-", "capture:-"))
            self.assertTrue(role.startswith("role:production_harness."))
            paths.append(path)
        expected = sorted(
            [
                KERNEL_RELATIVE.as_posix(),
                RUNNER_RELATIVE.as_posix(),
                *[f"{FIXTURE_ROOT_RELATIVE.as_posix()}/{branch}/CASE.json" for branch in BRANCHES],
            ]
        )
        self.assertEqual(paths, expected)
        self.assertNotIn(MANIFEST_RELATIVE.as_posix(), paths)
        self.assertNotIn("scripts/validate-asset-contract", paths)
        self.assertFalse(any("receipt" in path.lower() for path in paths))

    def test_production_validator_has_exactly_one_callsite_for_every_branch(self) -> None:
        validator = (ROOT / "scripts/validate-asset-contract").read_text(encoding="utf-8")
        callsites = re.findall(r'validate_shared_lifecycle_branch\(\s*"([a-z0-9_]+)"', validator)
        self.assertEqual(
            callsites,
            ["h2", "generated_child", "move_pair", "public_concept", "populated", "repair", "approved", "release"],
        )
        self.assertEqual(set(callsites), set(BRANCHES))
        self.assertIn("N64Game::AssetLifecycleContract.validate!(branch, payload)", validator)

    def test_fresh_clone_verifier_requires_reviewed_payload_ownership_and_isolated_ruby(self) -> None:
        validator = (ROOT / "scripts/validate-asset-contract").read_text(encoding="utf-8")
        verifier = re.search(
            r"def verify_approval_lifecycle_fixture_suite.*?^end$",
            validator,
            flags=re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(verifier)
        body = verifier.group(0)
        for token in (
            "materialized_commit_file",
            'payload_context[:member_owner][manifest_path]',
            'payload_context[:member_owner]["scripts/validate-asset-contract"]',
            'payload_context[:member_owner]["lib/n64game/public_commit_authority.rb"]',
            "payload_context[:closure].include?(path)",
            "commit_tree_entries(commit, fresh_clone)",
            'Dir.mktmpdir("n64game-reviewed-lifecycle-")',
            "reviewed_modes == expected_modes",
            "File.binwrite(target, bytes)",
            "harness_root, manifest_path",
            "run_production_lifecycle_harness",
        ):
            self.assertIn(token, body)
        ruby_env = re.search(r"def lifecycle_ruby_env.*?^end$", validator, flags=re.DOTALL | re.MULTILINE)
        self.assertIsNotNone(ruby_env)
        for variable in ("RUBYOPT", "RUBYLIB", "GEM_HOME", "GEM_PATH"):
            self.assertIn(f'"{variable}" => nil', ruby_env.group(0))
        self.assertIn('"--disable-gems"', validator)
        self.assertIn("unsetenv_others: true", validator)

    def test_rehashed_positive_fixture_mutation_is_rejected_by_shared_kernel(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.copied_harness(Path(temp_dir))
            relative = f"{FIXTURE_ROOT_RELATIVE.as_posix()}/approved/CASE.json"
            case = root / relative
            value = json.loads(case.read_text(encoding="utf-8"))
            value["payload"]["defects"]["high"] = 1
            case.write_bytes((json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8"))
            self.rewrite_manifest_member(root, relative)
            result = self.run_harness(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("zero critical/high/medium defects", result.stderr)

    def test_extra_fixture_file_is_rejected_even_when_unmanifested(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.copied_harness(Path(temp_dir))
            extra = root / FIXTURE_ROOT_RELATIVE / "EXTRA.txt"
            extra.write_text("extra\n", encoding="utf-8")
            result = self.run_harness(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixture root contains missing, extra, or symlinked files", result.stderr)

    def test_unlock_constants_match_independently_audited_manifest(self) -> None:
        validator = (ROOT / "scripts/validate-asset-contract").read_text(encoding="utf-8")
        implemented = re.search(r"(?m)^PRODUCTION_LIFECYCLE_HARNESS_IMPLEMENTED = (true|false)$", validator)
        pin = re.search(r'(?m)^PRODUCTION_LIFECYCLE_HARNESS_SHA256 = "([^"]+)"\.freeze$', validator)
        self.assertIsNotNone(implemented)
        self.assertIsNotNone(pin)
        self.assertEqual(implemented.group(1), "true")
        self.assertEqual(pin.group(1), hashlib.sha256((ROOT / MANIFEST_RELATIVE).read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
