from __future__ import annotations

import hashlib
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import n64game_authoring as authoring  # noqa: E402
import n64game_authoring_receipt as receipt  # noqa: E402


class AuthoringReceiptTests(unittest.TestCase):
    def stack_identity(self) -> dict[str, str]:
        return {
            "toolchain_lock_sha256": "1" * 64,
            "checker_sha256": "2" * 64,
            "blender_executable_sha256": "3" * 64,
            "blender_seal": receipt.BLENDER_SEAL,
            "fast64_source_manifest_sha256": "4" * 64,
            "probe_mode": receipt.PROBE_MODE,
        }

    def passing_stack_report(self) -> dict[str, object]:
        lock = authoring.load_authoring_lock()
        return {
            "status": "PASS",
            "blender": {
                "sha256": lock["blender_macos_arm64"]["executable_sha256"],
                "codesign": {"deep_strict_verified": True},
                "post_probe_deep_strict_verified": True,
            },
            "fast64": {
                "manifest_sha256": lock["fast64"]["source_tree_manifest_sha256"],
                "enabled_probe": {
                    "enabled": True,
                    "loaded": True,
                    "isolated_profile": True,
                    "inherited_environment": False,
                    "offline_mode": True,
                    "autoexec_disabled": True,
                    "module_execution": "isolated_copy_of_pinned_fast64",
                },
            },
        }

    def test_checker_bundle_binds_both_canonical_files_and_domain(self) -> None:
        expected = hashlib.sha256(receipt.CHECKER_BUNDLE_DOMAIN)
        for relative in sorted(receipt.CHECKER_BUNDLE_PATHS):
            expected.update(
                f"{relative}\t{receipt.sha256_file(ROOT / relative)}\n".encode("utf-8")
            )
        self.assertEqual(receipt.checker_bundle_sha256(), expected.hexdigest())

    def test_receipt_entrypoint_uses_the_absolute_isolated_interpreter(self) -> None:
        wrapper = (ROOT / "scripts" / "record-authoring-stack-receipt").read_text(encoding="utf-8")
        self.assertTrue(wrapper.startswith("#!/bin/sh\n"))
        self.assertIn('/usr/bin/dirname -- "$0"', wrapper)
        self.assertIn('exec /usr/bin/python3 -I -B "$ROOT/tools/n64game_authoring_receipt.py" "$@"', wrapper)
        self.assertNotIn("python3 tools/", wrapper)

    def test_receipt_entrypoint_rejects_symlink_invocation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            alias = Path(temporary) / "receipt-alias"
            alias.symlink_to(ROOT / "scripts" / "record-authoring-stack-receipt")
            completed = subprocess.run(
                [str(alias), "--help"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must not be invoked through a symlink", completed.stderr)

    def test_receipt_entrypoint_resolves_a_symlinked_parent_physically(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            alias = Path(temporary) / "scripts-alias"
            alias.symlink_to(ROOT / "scripts", target_is_directory=True)
            completed = subprocess.run(
                [str(alias / "record-authoring-stack-receipt"), "--help"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Produce exact per-asset authoring-stack receipts", completed.stdout)

    def test_gate2_receipt_has_exact_order_and_bindings(self) -> None:
        record = receipt.build_receipt(
            scope_id="echo.quarrune",
            gate="G2",
            source_manifest_sha256="a" * 64,
            output_manifest_sha256="NONE",
            build_id="-",
            checked_at="2026-07-19T12:34:56Z",
            stack_identity=self.stack_identity(),
        )
        self.assertEqual(tuple(record), receipt.RECEIPT_KEYS)
        payload = receipt.render_receipt(record)
        self.assertTrue(payload.endswith(b"checked_at: 2026-07-19T12:34:56Z\n"))
        self.assertEqual(payload.count(b"\n"), 14)

    def test_gate2_rejects_output_or_build_and_gate5_requires_both(self) -> None:
        common = {
            "scope_id": "echo.quarrune",
            "source_manifest_sha256": "a" * 64,
            "checked_at": "2026-07-19T12:34:56Z",
            "stack_identity": self.stack_identity(),
        }
        with self.assertRaises(receipt.AuthoringReceiptError):
            receipt.build_receipt(
                **common, gate="G2", output_manifest_sha256="b" * 64, build_id="n64game-g4-real001"
            )
        with self.assertRaises(receipt.AuthoringReceiptError):
            receipt.build_receipt(
                **common, gate="G5", output_manifest_sha256="NONE", build_id="-"
            )
        accepted = receipt.build_receipt(
            **common,
            gate="G5",
            output_manifest_sha256="b" * 64,
            build_id="n64game-g4-6531e405",
        )
        self.assertEqual(accepted["gate"], "G5")
        for generic_build in (
            "test001", "n64game-test0002", "placeholder_03", "unassigned001", "n-a", "nil",
        ):
            with self.subTest(build_id=generic_build), self.assertRaises(receipt.AuthoringReceiptError):
                receipt.build_receipt(
                    **common,
                    gate="G5",
                    output_manifest_sha256="b" * 64,
                    build_id=generic_build,
                )

    def test_portable_identity_rejects_false_probe_or_wrong_pin(self) -> None:
        accepted = receipt.portable_stack_identity(self.passing_stack_report())
        self.assertEqual(accepted["blender_seal"], receipt.BLENDER_SEAL)
        broken = self.passing_stack_report()
        broken["fast64"]["enabled_probe"]["inherited_environment"] = True  # type: ignore[index]
        with self.assertRaises(receipt.AuthoringReceiptError):
            receipt.portable_stack_identity(broken)

    def test_python_producer_and_ruby_validator_share_exact_bytes(self) -> None:
        stack = receipt.portable_stack_identity(self.passing_stack_report())
        record = receipt.build_receipt(
            scope_id="echo.quarrune",
            gate="G2",
            source_manifest_sha256="a" * 64,
            output_manifest_sha256="NONE",
            build_id="-",
            checked_at="2026-07-19T12:34:56Z",
            stack_identity=stack,
        )
        ruby = shutil.which("ruby") or "/usr/bin/ruby"
        program = """
          require 'json'
          require 'n64game/authoring_stack_receipt'
          root = ARGV.fetch(0)
          bytes = STDIN.read.b
          members = N64Game::AuthoringStackReceipt::CHECKER_BUNDLE_PATHS.to_h do |path|
            [path, File.binread(File.join(root, path))]
          end
          errors = N64Game::AuthoringStackReceipt.validate(
            bytes: bytes,
            scope_id: 'echo.quarrune', gate: 'G2',
            source_manifest_sha256: 'a' * 64,
            output_manifest_sha256: 'NONE', build_id: '-',
            decided_at: '2026-07-19T12:35:00Z',
            toolchain_lock_bytes: File.binread(File.join(root, 'config/toolchain.lock.json')),
            checker_members: members
          )
          STDOUT.write(JSON.generate(errors))
        """
        completed = subprocess.run(
            [ruby, "-I", str(ROOT / "lib"), "-e", program, str(ROOT)],
            input=receipt.render_receipt(record),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", "replace"))
        self.assertEqual(json.loads(completed.stdout), [])

    def test_ruby_consumer_rejects_gate5_until_exporter_is_implemented_and_pinned(self) -> None:
        stack = receipt.portable_stack_identity(self.passing_stack_report())
        record = receipt.build_receipt(
            scope_id="echo.quarrune",
            gate="G5",
            source_manifest_sha256="a" * 64,
            output_manifest_sha256="b" * 64,
            build_id="n64game-g4-6531e405",
            checked_at="2026-07-19T12:34:56Z",
            stack_identity=stack,
        )
        ruby = shutil.which("ruby") or "/usr/bin/ruby"
        program = """
          require 'json'
          require 'n64game/authoring_stack_receipt'
          root = ARGV.fetch(0)
          members = N64Game::AuthoringStackReceipt::CHECKER_BUNDLE_PATHS.to_h do |path|
            [path, File.binread(File.join(root, path))]
          end
          errors = N64Game::AuthoringStackReceipt.validate(
            bytes: STDIN.read.b,
            scope_id: 'echo.quarrune', gate: 'G5',
            source_manifest_sha256: 'a' * 64,
            output_manifest_sha256: 'b' * 64,
            build_id: 'n64game-g4-6531e405',
            decided_at: '2026-07-19T12:35:00Z',
            toolchain_lock_bytes: File.binread(File.join(root, 'config/toolchain.lock.json')),
            checker_members: members
          )
          STDOUT.write(JSON.generate(errors))
        """
        completed = subprocess.run(
            [ruby, "-I", str(ROOT / "lib"), "-e", program, str(ROOT)],
            input=receipt.render_receipt(record),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", "replace"))
        self.assertIn(
            "Gate-5 exporter is not implemented and approved",
            json.loads(completed.stdout),
        )

    def test_ruby_validator_rejects_receipt_after_gate_decision(self) -> None:
        stack = receipt.portable_stack_identity(self.passing_stack_report())
        record = receipt.build_receipt(
            scope_id="echo.quarrune",
            gate="G2",
            source_manifest_sha256="a" * 64,
            output_manifest_sha256="NONE",
            build_id="-",
            checked_at="2026-07-19T12:35:01Z",
            stack_identity=stack,
        )
        ruby = shutil.which("ruby") or "/usr/bin/ruby"
        program = """
          require 'json'
          require 'n64game/authoring_stack_receipt'
          root = ARGV.fetch(0)
          members = N64Game::AuthoringStackReceipt::CHECKER_BUNDLE_PATHS.to_h do |path|
            [path, File.binread(File.join(root, path))]
          end
          errors = N64Game::AuthoringStackReceipt.validate(
            bytes: STDIN.read.b,
            scope_id: 'echo.quarrune', gate: 'G2',
            source_manifest_sha256: 'a' * 64,
            output_manifest_sha256: 'NONE', build_id: '-',
            decided_at: '2026-07-19T12:35:00Z',
            toolchain_lock_bytes: File.binread(File.join(root, 'config/toolchain.lock.json')),
            checker_members: members
          )
          STDOUT.write(JSON.generate(errors))
        """
        completed = subprocess.run(
            [ruby, "-I", str(ROOT / "lib"), "-e", program, str(ROOT)],
            input=receipt.render_receipt(record),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", "replace"))
        self.assertIn("receipt checked_at is later than the gate decision", json.loads(completed.stdout))

    def test_ruby_timestamp_contract_rejects_year_zero_and_leap_second(self) -> None:
        ruby = shutil.which("ruby") or "/usr/bin/ruby"
        program = """
          require 'json'
          require 'n64game/authoring_stack_receipt'
          values = ['0000-01-01T00:00:00Z', '2026-07-19T12:34:60Z', '2026-02-29T00:00:00Z']
          STDOUT.write(JSON.generate(values.map { |value| N64Game::AuthoringStackReceipt.strict_rfc3339?(value) }))
        """
        completed = subprocess.run(
            [ruby, "-I", str(ROOT / "lib"), "-e", program],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", "replace"))
        self.assertEqual(json.loads(completed.stdout), [False, False, False])

    def test_ruby_validator_freezes_full_lock_and_checker_bundle(self) -> None:
        stack = receipt.portable_stack_identity(self.passing_stack_report())
        record = receipt.build_receipt(
            scope_id="echo.quarrune",
            gate="G2",
            source_manifest_sha256="a" * 64,
            output_manifest_sha256="NONE",
            build_id="-",
            checked_at="2026-07-19T12:34:56Z",
            stack_identity=stack,
        )
        ruby = shutil.which("ruby") or "/usr/bin/ruby"
        program = """
          require 'json'
          require 'n64game/authoring_stack_receipt'
          root = ARGV.fetch(0)
          members = N64Game::AuthoringStackReceipt::CHECKER_BUNDLE_PATHS.to_h do |path|
            [path, File.binread(File.join(root, path))]
          end
          members['scripts/check-authoring-stack'] += "# mutation\n"
          lock = File.binread(File.join(root, 'config/toolchain.lock.json')) + " \n"
          errors = N64Game::AuthoringStackReceipt.validate(
            bytes: STDIN.read.b,
            scope_id: 'echo.quarrune', gate: 'G2',
            source_manifest_sha256: 'a' * 64,
            output_manifest_sha256: 'NONE', build_id: '-',
            decided_at: '2026-07-19T12:35:00Z',
            toolchain_lock_bytes: lock, checker_members: members
          )
          STDOUT.write(JSON.generate(errors))
        """
        completed = subprocess.run(
            [ruby, "-I", str(ROOT / "lib"), "-e", program, str(ROOT)],
            input=receipt.render_receipt(record),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", "replace"))
        errors = json.loads(completed.stdout)
        self.assertIn("historical toolchain lock differs from the frozen approved file", errors)
        self.assertIn("historical checker/producer bundle differs from the frozen approved bundle", errors)

    def test_canonical_noop_cannot_unlock_unimplemented_gate5_export(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            exporter = root / receipt.CANONICAL_GATE5_EXPORTER_PATH
            exporter.parent.mkdir(parents=True, exist_ok=True)
            exporter.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            os.chmod(exporter, 0o755)
            with self.assertRaisesRegex(receipt.AuthoringReceiptError, "not implemented and approved"):
                receipt.run_checked_export(
                    [str(exporter)], check=mock.Mock(), run=mock.Mock(), root=root
                )

    def test_true_implementation_flag_still_requires_exact_nonpending_sha(self) -> None:
        with mock.patch.object(receipt, "GATE5_EXPORT_IMPLEMENTED", True):
            with self.assertRaisesRegex(receipt.AuthoringReceiptError, "approval SHA-256"):
                receipt.run_checked_export(
                    [receipt.CANONICAL_GATE5_EXPORTER_PATH],
                    check=mock.Mock(),
                    run=mock.Mock(),
                )

    def test_explicitly_pinned_export_runs_between_two_equal_stack_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in receipt.CHECKER_BUNDLE_PATHS:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((relative + "\n").encode("utf-8"))
            lock_path = root / "config" / "toolchain.lock.json"
            lock_path.parent.mkdir(parents=True)
            lock_path.write_bytes((ROOT / "config" / "toolchain.lock.json").read_bytes())
            exporter = root / receipt.CANONICAL_GATE5_EXPORTER_PATH
            exporter.parent.mkdir(parents=True, exist_ok=True)
            exporter.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            os.chmod(exporter, 0o755)
            report = self.passing_stack_report()
            events: list[str] = []

            def check() -> dict[str, object]:
                events.append("check")
                return report

            def run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
                events.append("export")
                self.assertEqual(kwargs["check"], False)
                self.assertNotIn("PYTHONPATH", kwargs["env"])
                return subprocess.CompletedProcess(args[0], 0)

            with (
                mock.patch.object(receipt, "GATE5_EXPORT_IMPLEMENTED", True),
                mock.patch.object(
                    receipt, "APPROVED_GATE5_EXPORTER_SHA256", receipt.sha256_file(exporter)
                ),
            ):
                identity = receipt.run_checked_export(
                    [str(exporter)], check=check, run=run, root=root
                )
        self.assertEqual(events, ["check", "export", "check"])
        self.assertEqual(identity["probe_mode"], receipt.PROBE_MODE)

    def test_checked_export_failure_does_not_run_post_check(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in receipt.CHECKER_BUNDLE_PATHS:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((relative + "\n").encode("utf-8"))
            lock_path = root / "config" / "toolchain.lock.json"
            lock_path.parent.mkdir(parents=True)
            lock_path.write_bytes((ROOT / "config" / "toolchain.lock.json").read_bytes())
            exporter = root / receipt.CANONICAL_GATE5_EXPORTER_PATH
            exporter.parent.mkdir(parents=True, exist_ok=True)
            exporter.write_text("#!/bin/sh\nexit 9\n", encoding="utf-8")
            os.chmod(exporter, 0o755)
            check = mock.Mock(return_value=self.passing_stack_report())
            run = mock.Mock(return_value=subprocess.CompletedProcess([str(exporter)], 9))
            with (
                mock.patch.object(receipt, "GATE5_EXPORT_IMPLEMENTED", True),
                mock.patch.object(
                    receipt, "APPROVED_GATE5_EXPORTER_SHA256", receipt.sha256_file(exporter)
                ),
                self.assertRaisesRegex(receipt.AuthoringReceiptError, "exited 9"),
            ):
                receipt.run_checked_export([str(exporter)], check=check, run=run, root=root)
            self.assertEqual(check.call_count, 1)

    def test_checked_export_rejects_stack_or_output_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in receipt.CHECKER_BUNDLE_PATHS:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((relative + "\n").encode("utf-8"))
            lock_path = root / "config" / "toolchain.lock.json"
            lock_path.parent.mkdir(parents=True)
            lock_path.write_bytes((ROOT / "config" / "toolchain.lock.json").read_bytes())
            exporter = root / receipt.CANONICAL_GATE5_EXPORTER_PATH
            exporter.parent.mkdir(parents=True, exist_ok=True)
            exporter.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            os.chmod(exporter, 0o755)
            passing = self.passing_stack_report()
            changed = self.passing_stack_report()
            changed["fast64"]["enabled_probe"]["inherited_environment"] = True  # type: ignore[index]
            approval = mock.patch.object(
                receipt, "APPROVED_GATE5_EXPORTER_SHA256", receipt.sha256_file(exporter)
            )
            with mock.patch.object(receipt, "GATE5_EXPORT_IMPLEMENTED", True), approval:
                with self.assertRaises(receipt.AuthoringReceiptError):
                    receipt.run_checked_export(
                        [str(exporter)],
                        check=mock.Mock(side_effect=[passing, changed]),
                        run=mock.Mock(return_value=subprocess.CompletedProcess([str(exporter)], 0)),
                        root=root,
                    )
            snapshots = iter([("source", "output-a"), ("source", "output-b")])
            with (
                mock.patch.object(receipt, "GATE5_EXPORT_IMPLEMENTED", True),
                mock.patch.object(
                    receipt, "APPROVED_GATE5_EXPORTER_SHA256", receipt.sha256_file(exporter)
                ),
                self.assertRaisesRegex(receipt.AuthoringReceiptError, "source/output identity changed"),
            ):
                receipt.run_checked_export(
                    [str(exporter)],
                    check=mock.Mock(side_effect=[passing, passing]),
                    run=mock.Mock(return_value=subprocess.CompletedProcess([str(exporter)], 0)),
                    snapshot=lambda: next(snapshots),
                    root=root,
                )

    def test_checked_export_rejects_arbitrary_or_system_executable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            arbitrary = root / "scripts" / "other-exporter"
            arbitrary.parent.mkdir(parents=True)
            arbitrary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            os.chmod(arbitrary, 0o755)
            with (
                mock.patch.object(receipt, "GATE5_EXPORT_IMPLEMENTED", True),
                mock.patch.object(receipt, "APPROVED_GATE5_EXPORTER_SHA256", "a" * 64),
            ):
                with self.assertRaisesRegex(receipt.AuthoringReceiptError, "locked to reviewed"):
                    receipt.run_checked_export(
                        [str(arbitrary)], check=mock.Mock(), run=mock.Mock(), root=root
                    )
                with self.assertRaisesRegex(receipt.AuthoringReceiptError, "locked to reviewed"):
                    receipt.run_checked_export(
                        ["/usr/bin/true"], check=mock.Mock(), run=mock.Mock(), root=root
                    )

    def test_g5_invalid_build_fails_before_stack_check_or_export(self) -> None:
        with (
            mock.patch.object(receipt, "stack_report") as check,
            mock.patch.object(receipt, "run_checked_export") as export,
            mock.patch.object(
                receipt,
                "canonical_receipt_path",
                return_value=ROOT / "review" / "echo.quarrune" / "g5" / "AUTHORING_STACK_RECEIPT.txt",
            ),
        ):
            with contextlib.redirect_stderr(io.StringIO()):
                result = receipt.main(
                    ["g5-export", "--scope", "echo.quarrune", "--build-id", "test001"]
                )
        self.assertEqual(result, 1)
        check.assert_not_called()
        export.assert_not_called()

    def test_existing_receipt_fails_before_stack_check(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "review" / "echo.quarrune" / "g2" / "AUTHORING_STACK_RECEIPT.txt"
            destination.parent.mkdir(parents=True)
            destination.write_text("existing\n", encoding="utf-8")
            with (
                mock.patch.object(receipt, "stack_report") as check,
                mock.patch.object(receipt, "canonical_receipt_path", return_value=destination),
                mock.patch.object(receipt, "preflight_receipt_target") as preflight,
            ):
                preflight.side_effect = receipt.AuthoringReceiptError("receipt already exists")
                with contextlib.redirect_stderr(io.StringIO()):
                    result = receipt.main(["g2", "--scope", "echo.quarrune"])
            self.assertEqual(result, 1)
            check.assert_not_called()

    def test_writer_is_atomic_and_refuses_silent_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "review" / "echo.quarrune" / "g2" / "AUTHORING_STACK_RECEIPT.txt"
            receipt.write_receipt(destination, b"first\n", root=root)
            self.assertEqual(destination.read_bytes(), b"first\n")
            with self.assertRaises(receipt.AuthoringReceiptError):
                receipt.write_receipt(destination, b"second\n", root=root)
            receipt.write_receipt(destination, b"second\n", root=root, replace=True)
            self.assertEqual(destination.read_bytes(), b"second\n")

    def test_writer_rejects_parent_symlink_even_when_target_stays_inside_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_parent = root / "real"
            real_parent.mkdir()
            (root / "review").symlink_to(real_parent, target_is_directory=True)
            destination = root / "review" / "echo.quarrune" / "g2" / "AUTHORING_STACK_RECEIPT.txt"
            with self.assertRaisesRegex(receipt.AuthoringReceiptError, "traverses a symlink"):
                receipt.write_receipt(destination, b"receipt\n", root=root)

    def test_repo_regular_rejects_parent_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_parent = root / "real"
            real_parent.mkdir()
            target = real_parent / "SOURCE_MANIFEST.sha256"
            target.write_text("fixture\n", encoding="utf-8")
            (root / "assets-src").symlink_to(real_parent, target_is_directory=True)
            with self.assertRaisesRegex(receipt.AuthoringReceiptError, "traverses a symlink"):
                receipt.require_repo_regular(root / "assets-src" / target.name, "fixture", root)


if __name__ == "__main__":
    unittest.main()
