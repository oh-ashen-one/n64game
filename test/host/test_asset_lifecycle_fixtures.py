from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts" / "test-asset-contract-lifecycle"
FIXTURE_ROOT = ROOT / "test" / "fixtures" / "asset_contract"
MANIFEST_RELATIVE = Path("test/fixtures/asset_contract/LIFECYCLE_SNAPSHOT_MANIFEST.sha256")
CASES = ["populated", "approved", "repair", "generated_child", "move_pair", "h2", "release"]


class AssetLifecycleSemanticSnapshotTests(unittest.TestCase):
    @staticmethod
    def write_utf8_lf(path: Path, content: str) -> None:
        if "\r" in content:
            raise ValueError("canonical fixture text must use LF line endings")
        path.write_bytes(content.encode("utf-8"))

    def run_suite(self, root: Path = ROOT) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-I",
                str(root / "scripts" / "test-asset-contract-lifecycle"),
                "--json",
                "--fixture-manifest",
                str(root / MANIFEST_RELATIVE),
            ],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def copied_suite(self, destination: Path) -> Path:
        root = destination / "repo"
        (root / "scripts").mkdir(parents=True)
        shutil.copy2(RUNNER, root / "scripts" / RUNNER.name)
        shutil.copytree(FIXTURE_ROOT, root / "test" / "fixtures" / "asset_contract")
        os.chmod(root / "scripts" / RUNNER.name, 0o755)
        return root

    @staticmethod
    def rewrite_manifest_member(root: Path, member_relative: str) -> None:
        member = root / member_relative
        data = member.read_bytes()
        manifest = root / MANIFEST_RELATIVE
        lines = manifest.read_text(encoding="utf-8").splitlines()
        rewritten = []
        for line in lines:
            fields = line.split("\t")
            if fields[0] == member_relative:
                fields[1] = str(len(data))
                fields[2] = hashlib.sha256(data).hexdigest()
            rewritten.append("\t".join(fields))
        AssetLifecycleSemanticSnapshotTests.write_utf8_lf(manifest, "\n".join(rewritten) + "\n")

    def test_pinned_semantic_snapshot_suite_passes_with_exact_receipt(self) -> None:
        result = self.run_suite()
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(
            receipt,
            {
                "schema": "n64game-asset-lifecycle-semantic-snapshots-v1",
                "authority": "NON_APPROVAL_SEMANTIC_SNAPSHOT",
                "result": "PASS",
                "manifest_sha256": hashlib.sha256((ROOT / MANIFEST_RELATIVE).read_bytes()).hexdigest(),
                "cases": CASES,
                "topology": "parallel_nonchronological_scenarios",
                "cross_bindings": ["approved->repair", "approved->release"],
            },
        )

    def test_validator_pin_equals_the_exact_semantic_snapshot_manifest(self) -> None:
        validator = (ROOT / "scripts" / "validate-asset-contract").read_text(encoding="utf-8")
        match = re.search(
            r'^SEMANTIC_LIFECYCLE_SNAPSHOT_SHA256 = "([0-9a-f]{64})"\.freeze$',
            validator,
            flags=re.MULTILINE,
        )
        self.assertIsNotNone(match)
        self.assertEqual(
            match.group(1),
            hashlib.sha256((ROOT / MANIFEST_RELATIVE).read_bytes()).hexdigest(),
        )

    def test_semantic_snapshot_cannot_unlock_production_approval(self) -> None:
        validator = (ROOT / "scripts" / "validate-asset-contract").read_text(encoding="utf-8")
        self.assertRegex(
            validator,
            r'(?m)^PRODUCTION_LIFECYCLE_HARNESS_SHA256 = "PENDING"\.freeze$',
        )
        self.assertRegex(
            validator,
            r'(?m)^PRODUCTION_LIFECYCLE_HARNESS_IMPLEMENTED = false$',
        )
        readiness = re.search(
            r'def approval_lifecycle_pins_ready\?\n(.*?)\nend',
            validator,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(readiness)
        self.assertIn("PRODUCTION_LIFECYCLE_HARNESS_IMPLEMENTED", readiness.group(1))
        self.assertIn("PRODUCTION_LIFECYCLE_HARNESS_SHA256", readiness.group(1))
        self.assertIn("SEMANTIC_LIFECYCLE_SNAPSHOT_SHA256", readiness.group(1))
        verifier = re.search(
            r'def verify_approval_lifecycle_fixture_suite.*?^end$',
            validator,
            flags=re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(verifier)
        self.assertIn(
            "verifier is not implemented; a SHA-256 pin alone cannot unlock approval",
            verifier.group(0),
        )

    def test_unmanifested_case_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.copied_suite(Path(temp_dir))
            case = root / "test/fixtures/asset_contract/approved/CASE.json"
            case.write_bytes(case.read_bytes() + b"\n")
            result = self.run_suite(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("digest/count mismatch", result.stderr)

    def test_semantic_tamper_with_rehashed_manifest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.copied_suite(Path(temp_dir))
            relative = "test/fixtures/asset_contract/approved/CASE.json"
            case = root / relative
            value = json.loads(case.read_text(encoding="utf-8"))
            value["counts"]["total_gate_decisions"] = 391
            self.write_utf8_lf(case, json.dumps(value, indent=2, sort_keys=True) + "\n")
            self.rewrite_manifest_member(root, relative)
            result = self.run_suite(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("approved coverage counts mismatch", result.stderr)

    def test_rehashed_semantic_and_type_bypasses_are_rejected(self) -> None:
        def h2_same_commit(value: dict[str, object]) -> None:
            for phase in value["scope"]["phases"]:
                phase["commit"] = "1" * 40

        def repair_other_baseline(value: dict[str, object]) -> None:
            value["prior"]["payload_commit"] = "d" * 40
            value["prior"]["tag_ref"] = "refs/tags/n64game-visual-benchmark/" + "d" * 12

        def h2_cycles_to_initial(value: dict[str, object]) -> None:
            phases = value["scope"]["phases"]
            phases[4]["commit"] = phases[0]["commit"]
            phases[4]["source_sha256"] = phases[0]["source_sha256"]
            phases[4]["output_sha256"] = phases[0]["output_sha256"]

        mutations = (
            ("release", lambda value: value["release"].__setitem__("rom_size_bytes", True), "release ROM identity is malformed"),
            ("move_pair", lambda value: value["pair"].__setitem__("sync_error_ms", True), "move-pair synchronization proof mismatch"),
            ("generated_child", lambda value: value["transition"].__setitem__("child_id", "ASSET_CAMERA_SHOT_NOT_IN_FROZEN_DOMAIN"), "generated child is outside the frozen camera-child domain"),
            ("populated", lambda value: value["whitelist_row"].__setitem__("source_manifest", "@"), "populated source manifest binding is missing"),
            ("h2", h2_same_commit, "H2 polish pass commit transition is not strict"),
            ("repair", lambda value: value["prior"].__setitem__("control_commit", int("1" * 40)), "repair prior commit identity is malformed"),
            ("move_pair", lambda value: value["pair"]["children"][0].__setitem__("source_sha256", int("1" * 64)), "move-pair child digest is malformed"),
            ("h2", lambda value: value["scope"].__setitem__("polish_passes", 2.0), "H2 scope identity/pass count mismatch"),
            ("release", lambda value: value["release"].__setitem__("payload_commit", int("1" * 40)), "release is not built from the payload commit"),
            ("repair", repair_other_baseline, "repair baseline is not the exact approved fixture identity"),
            ("h2", h2_cycles_to_initial, "H2 polish phase commit chain cycles or aliases"),
            ("repair", lambda value: value["prior"].__setitem__("control_commit", value["prior"]["payload_commit"]), "repair prior control/payload/tag object identities are not distinct"),
            ("repair", lambda value: value["prior"].__setitem__("tag_object", value["prior"]["control_commit"]), "repair prior control/payload/tag object identities are not distinct"),
            ("move_pair", lambda value: value["pair"]["children"][0].__setitem__("evidence_sha256", value["pair"]["children"][0]["source_sha256"]), "move-pair children improperly share source/evidence"),
        )
        for index, (case_name, mutate, expected_error) in enumerate(mutations):
            with self.subTest(case=case_name, mutation=index), tempfile.TemporaryDirectory() as temp_dir:
                root = self.copied_suite(Path(temp_dir))
                relative = f"test/fixtures/asset_contract/{case_name}/CASE.json"
                case = root / relative
                value = json.loads(case.read_text(encoding="utf-8"))
                mutate(value)
                self.write_utf8_lf(case, json.dumps(value, indent=2, sort_keys=True) + "\n")
                self.rewrite_manifest_member(root, relative)
                result = self.run_suite(root)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected_error, result.stderr)

    def test_manifest_role_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.copied_suite(Path(temp_dir))
            manifest = root / MANIFEST_RELATIVE
            self.write_utf8_lf(
                manifest,
                manifest.read_text(encoding="utf-8").replace(
                    "role:semantic_snapshot.release",
                    "role:semantic_snapshot.approved",
                ),
            )
            result = self.run_suite(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("roles/order", result.stderr)

    def test_symlinked_case_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.copied_suite(Path(temp_dir))
            case = root / "test/fixtures/asset_contract/release/CASE.json"
            case.unlink()
            case.symlink_to("../approved/CASE.json")
            result = self.run_suite(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlinked", result.stderr)

    def test_extra_fixture_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.copied_suite(Path(temp_dir))
            self.write_utf8_lf(root / "test/fixtures/asset_contract/EXTRA.txt", "not owned\n")
            result = self.run_suite(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing, extra, or symlinked", result.stderr)

    def test_runner_self_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.copied_suite(Path(temp_dir))
            runner = root / "scripts/test-asset-contract-lifecycle"
            runner.write_bytes(runner.read_bytes() + b"\n")
            result = self.run_suite(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("digest/count mismatch", result.stderr)

    def test_shadow_stdlib_module_cannot_replace_the_audited_runner(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = self.copied_suite(Path(temp_dir))
            relative = "test/fixtures/asset_contract/approved/CASE.json"
            case = root / relative
            value = json.loads(case.read_text(encoding="utf-8"))
            value["counts"]["total_gate_decisions"] = 391
            self.write_utf8_lf(case, json.dumps(value, indent=2, sort_keys=True) + "\n")
            self.rewrite_manifest_member(root, relative)
            manifest_digest = hashlib.sha256((root / MANIFEST_RELATIVE).read_bytes()).hexdigest()
            forged_receipt = json.dumps(
                {
                    "schema": "n64game-asset-lifecycle-semantic-snapshots-v1",
                    "authority": "NON_APPROVAL_SEMANTIC_SNAPSHOT",
                    "result": "PASS",
                    "manifest_sha256": manifest_digest,
                    "cases": CASES,
                    "topology": "parallel_nonchronological_scenarios",
                    "cross_bindings": ["approved->repair", "approved->release"],
                },
                separators=(",", ":"),
            )
            self.write_utf8_lf(
                root / "scripts" / "hashlib.py",
                f"print({forged_receipt!r})\nraise SystemExit(0)\n",
            )
            result = self.run_suite(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("approved coverage counts mismatch", result.stderr)


if __name__ == "__main__":
    unittest.main()
