from __future__ import annotations

import hashlib
import contextlib
import fcntl
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import multiprocessing
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import n64game_authoring as authoring  # noqa: E402
import n64game_authoring_receipt as receipt  # noqa: E402


def _concurrent_receipt_writer(
    root_text: str,
    tag: str,
    start: multiprocessing.synchronize.Event,
) -> None:
    root = Path(root_text)
    first = root / "review" / "echo.quarrune" / "g5" / "AUTHORING_STACK_RECEIPT.txt"
    second = root / "review" / "anm.echo.quarrune" / "g5" / "AUTHORING_STACK_RECEIPT.txt"
    log = root / "transaction.log"
    start.wait(10)
    with receipt.gate5_transaction_lock(root) as transaction:
        with log.open("a", encoding="utf-8") as handle:
            handle.write(f"enter:{tag}\n")
            handle.flush()

        def pause_after_first(index: int, _path: Path) -> None:
            if index == 1:
                time.sleep(0.1)

        receipt.write_receipts_atomically(
            [(first, f"{tag}:model\n".encode()), (second, f"{tag}:animation\n".encode())],
            root=root,
            replace=True,
            transaction=transaction,
            before_promote=pause_after_first,
        )
        with log.open("a", encoding="utf-8") as handle:
            handle.write(f"exit:{tag}\n")
            handle.flush()


def _replace_and_lock_canonical_gate5_path(
    root_text: str,
    ready: multiprocessing.synchronize.Event,
    release: multiprocessing.synchronize.Event,
    status: multiprocessing.queues.Queue,
) -> None:
    """Adversarial helper that creates the split-inode flock condition."""
    parent_fd: int | None = None
    lock_fd: int | None = None
    try:
        parent_fd = os.open(
            os.path.realpath("/tmp"),
            os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC,
        )
        lock_name = receipt.gate5_lock_path(Path(root_text)).name
        os.unlink(lock_name, dir_fd=parent_fd)
        lock_fd = os.open(
            lock_name,
            os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC,
            0o600,
            dir_fd=parent_fd,
        )
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        metadata = os.fstat(lock_fd)
        status.put(("locked", metadata.st_dev, metadata.st_ino))
        ready.set()
        release.wait(20)
    except BaseException as exc:
        status.put(("error", repr(exc)))
        ready.set()
    finally:
        if lock_fd is not None:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
            finally:
                os.close(lock_fd)
        if parent_fd is not None:
            os.close(parent_fd)


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

    def prepare_export_root(self, root: Path) -> Path:
        for relative in receipt.CHECKER_BUNDLE_PATHS:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((relative + "\n").encode("utf-8"))
        lock_path = root / "config" / "toolchain.lock.json"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_bytes((ROOT / "config" / "toolchain.lock.json").read_bytes())
        exporter = root / receipt.CANONICAL_GATE5_EXPORTER_PATH
        exporter.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        os.chmod(exporter, 0o755)
        return exporter

    def prepare_manifest_pair(
        self, root: Path, build_id: str = "n64game-g5-deadbeef"
    ) -> tuple[tuple[Path, Path], tuple[Path, Path], tuple[Path, Path]]:
        source_manifests: list[Path] = []
        output_manifests: list[Path] = []
        output_members: list[Path] = []
        fixtures = (
            (
                "echo.quarrune",
                "assets-src/echo/echo.quarrune/quarrune.blend",
                "source.model.blend",
                "review/echo.quarrune/g5/quarrune_hero.t3dm",
                "output.tiny3d.model",
            ),
            (
                "anm.echo.quarrune",
                "assets-src/anm/anm.echo.quarrune/quarrune_animation.blend",
                "source.animation.blend",
                "review/anm.echo.quarrune/g5/anm_echo_quarrune.0.sdata",
                "output.tiny3d.animation_stream",
            ),
        )
        for scope, source_relative, source_role, output_relative, output_role in fixtures:
            source_member = root / source_relative
            source_member.parent.mkdir(parents=True, exist_ok=True)
            source_member.write_bytes(("source:" + scope + "\n").encode())
            source_manifest = receipt.canonical_source_manifest(scope, root)
            source_manifest.write_text(
                f"{source_relative}\t{source_member.stat().st_size}\t"
                f"{receipt.sha256_file(source_member)}\tbuild:-\tcapture:-\trole:{source_role}\n",
                encoding="utf-8",
            )
            output_member = root / output_relative
            output_member.parent.mkdir(parents=True, exist_ok=True)
            output_member.write_bytes(("output:" + scope + "\n").encode())
            output_manifest = receipt.canonical_output_manifest(scope, root)
            output_manifest.write_text(
                f"{output_relative}\t{output_member.stat().st_size}\t"
                f"{receipt.sha256_file(output_member)}\tbuild:{build_id}\t"
                f"capture:-\trole:{output_role}\n",
                encoding="utf-8",
            )
            source_manifests.append(source_manifest)
            output_manifests.append(output_manifest)
            output_members.append(output_member)
        return (
            (source_manifests[0], source_manifests[1]),
            (output_manifests[0], output_manifests[1]),
            (output_members[0], output_members[1]),
        )

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
                    [str(exporter)],
                    check=mock.Mock(),
                    snapshot=lambda: ("unused",),
                    transaction=mock.Mock(spec=receipt.ReceiptTransaction),
                    run=mock.Mock(),
                    root=root,
                )

    def test_true_implementation_flag_still_requires_exact_nonpending_sha(self) -> None:
        with (
            mock.patch.object(receipt, "GATE5_EXPORT_IMPLEMENTED", True),
            mock.patch.object(receipt, "APPROVED_GATE5_EXPORTER_SHA256", "PENDING"),
        ):
            with self.assertRaisesRegex(receipt.AuthoringReceiptError, "approval SHA-256"):
                receipt.run_checked_export(
                    [receipt.CANONICAL_GATE5_EXPORTER_PATH],
                    check=mock.Mock(),
                    snapshot=lambda: ("unused",),
                    transaction=mock.Mock(spec=receipt.ReceiptTransaction),
                    run=mock.Mock(),
                )

    def test_gate5_export_command_injects_scope_and_build_and_forbids_override(self) -> None:
        command = receipt.gate5_exporter_command(
            "echo.quarrune", "n64game-g5-deadbeef", ["--deterministic"]
        )
        self.assertEqual(
            command,
            [
                str(ROOT / receipt.CANONICAL_GATE5_EXPORTER_PATH),
                "--scope", "echo.quarrune",
                "--paired-scope", "anm.echo.quarrune",
                "--build-id", "n64game-g5-deadbeef",
                "--deterministic",
            ],
        )
        for arguments in (
            [],
            ["--scope", "echo.ayselor", "--deterministic"],
            ["--build-id", "other", "--deterministic"],
            ["--deterministic", "--deterministic"],
        ):
            with self.subTest(arguments=arguments), self.assertRaises(receipt.AuthoringReceiptError):
                receipt.gate5_exporter_command("echo.quarrune", "n64game-g5-deadbeef", arguments)
        paired_command = receipt.gate5_exporter_command(
            "anm.echo.quarrune", "n64game-g5-deadbeef", ["--deterministic"]
        )
        self.assertEqual(paired_command, command)
        with self.assertRaisesRegex(receipt.AuthoringReceiptError, "Quarrune scope pair"):
            receipt.gate5_exporter_command(
                "echo.ayselor", "n64game-g5-deadbeef", ["--deterministic"]
            )

    def test_pair_export_command_injects_both_owners_and_replace_once(self) -> None:
        self.assertEqual(
            receipt.gate5_pair_exporter_command(
                "echo.quarrune", "anm.echo.quarrune", "n64game-g5-deadbeef", replace=True
            ),
            [
                str(ROOT / receipt.CANONICAL_GATE5_EXPORTER_PATH),
                "--scope", "echo.quarrune",
                "--paired-scope", "anm.echo.quarrune",
                "--build-id", "n64game-g5-deadbeef",
                "--deterministic",
                "--replace",
            ],
        )
        with self.assertRaisesRegex(receipt.AuthoringReceiptError, "only echo.quarrune"):
            receipt.gate5_pair_exporter_command(
                "echo.ayselor", "anm.echo.ayselor", "n64game-g5-deadbeef", replace=False
            )
        with self.assertRaisesRegex(receipt.AuthoringReceiptError, "requires --replace"):
            receipt.gate5_pair_exporter_command(
                "echo.quarrune", "anm.echo.quarrune", "n64game-g5-deadbeef", replace=False
            )

    def test_explicitly_pinned_export_runs_between_two_equal_stack_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            exporter = self.prepare_export_root(root)
            report = self.passing_stack_report()
            events: list[str] = []

            def check() -> dict[str, object]:
                events.append("check")
                return report

            def run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
                events.append("export")
                self.assertEqual(kwargs["check"], False)
                self.assertNotIn("PYTHONPATH", kwargs["env"])
                self.assertEqual(
                    kwargs["env"]["N64GAME_GATE5_LOCK_FD"],
                    str(kwargs["pass_fds"][0]),
                )
                return subprocess.CompletedProcess(args[0], 0)

            def snapshot() -> tuple[str]:
                events.append("snapshot")
                return ("stable",)

            with (
                mock.patch.object(receipt, "ROOT", root),
                mock.patch.object(receipt, "GATE5_EXPORT_IMPLEMENTED", True),
                mock.patch.object(
                    receipt, "APPROVED_GATE5_EXPORTER_SHA256", receipt.sha256_file(exporter)
                ),
            ):
                with receipt.gate5_transaction_lock(root) as transaction:
                    checked = receipt.run_checked_export(
                        [str(exporter)],
                        check=check,
                        snapshot=snapshot,
                        transaction=transaction,
                        run=run,
                        root=root,
                    )
        self.assertEqual(events, ["check", "export", "snapshot", "check", "snapshot"])
        self.assertEqual(dict(checked.stack_identity)["probe_mode"], receipt.PROBE_MODE)
        self.assertEqual(checked.snapshot, ("stable",))

    def test_unlinked_recreated_lock_makes_old_holder_fail_before_postcheck(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            exporter = self.prepare_export_root(root)
            context = multiprocessing.get_context("spawn")
            ready = context.Event()
            release = context.Event()
            status = context.Queue()
            worker = context.Process(
                target=_replace_and_lock_canonical_gate5_path,
                args=(str(root), ready, release, status),
            )
            check = mock.Mock(return_value=self.passing_stack_report())
            snapshot = mock.Mock(return_value=("must-not-run",))
            old_inode: tuple[int, int] | None = None

            def split_lock_run(
                *args: object, **_kwargs: object
            ) -> subprocess.CompletedProcess[bytes]:
                worker.start()
                self.assertTrue(ready.wait(10), "split-lock worker did not become ready")
                observed = status.get(timeout=5)
                self.assertEqual(observed[0], "locked", observed)
                self.assertIsNotNone(old_inode)
                self.assertNotEqual(tuple(observed[1:]), old_inode)
                return subprocess.CompletedProcess(args[0], 0)

            try:
                with (
                    mock.patch.object(receipt, "GATE5_EXPORT_IMPLEMENTED", True),
                    mock.patch.object(
                        receipt,
                        "APPROVED_GATE5_EXPORTER_SHA256",
                        receipt.sha256_file(exporter),
                    ),
                    self.assertRaisesRegex(
                        receipt.AuthoringReceiptError,
                        "lock pathname changed while held",
                    ),
                ):
                    with receipt.gate5_transaction_lock(root) as transaction:
                        old_inode = (
                            transaction.lock_device,
                            transaction.lock_inode,
                        )
                        receipt.run_checked_export(
                            [str(exporter)],
                            check=check,
                            snapshot=snapshot,
                            transaction=transaction,
                            run=split_lock_run,
                            root=root,
                        )
            finally:
                release.set()
                if worker.pid is not None:
                    worker.join(20)
                receipt.gate5_lock_path(root).unlink(missing_ok=True)
            self.assertEqual(worker.exitcode, 0)
            self.assertEqual(check.call_count, 1)
            snapshot.assert_not_called()
            self.assertFalse((root / "review").exists())

    def test_checked_export_failure_does_not_run_post_check(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            exporter = self.prepare_export_root(root)
            exporter.write_text("#!/bin/sh\nexit 9\n", encoding="utf-8")
            check = mock.Mock(return_value=self.passing_stack_report())
            run = mock.Mock(return_value=subprocess.CompletedProcess([str(exporter)], 9))
            with (
                mock.patch.object(receipt, "GATE5_EXPORT_IMPLEMENTED", True),
                mock.patch.object(
                    receipt, "APPROVED_GATE5_EXPORTER_SHA256", receipt.sha256_file(exporter)
                ),
                self.assertRaisesRegex(receipt.AuthoringReceiptError, "exited 9"),
            ):
                with receipt.gate5_transaction_lock(root) as transaction:
                    receipt.run_checked_export(
                        [str(exporter)],
                        check=check,
                        snapshot=mock.Mock(),
                        transaction=transaction,
                        run=run,
                        root=root,
                    )
            self.assertEqual(check.call_count, 1)

    def test_checked_export_rejects_stack_or_output_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            exporter = self.prepare_export_root(root)
            passing = self.passing_stack_report()
            changed = self.passing_stack_report()
            changed["fast64"]["enabled_probe"]["inherited_environment"] = True  # type: ignore[index]
            approval = mock.patch.object(
                receipt, "APPROVED_GATE5_EXPORTER_SHA256", receipt.sha256_file(exporter)
            )
            with mock.patch.object(receipt, "GATE5_EXPORT_IMPLEMENTED", True), approval:
                with self.assertRaises(receipt.AuthoringReceiptError):
                    with receipt.gate5_transaction_lock(root) as transaction:
                        receipt.run_checked_export(
                            [str(exporter)],
                            check=mock.Mock(side_effect=[passing, changed]),
                            snapshot=lambda: ("stable",),
                            transaction=transaction,
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
                with receipt.gate5_transaction_lock(root) as transaction:
                    receipt.run_checked_export(
                        [str(exporter)],
                        check=mock.Mock(side_effect=[passing, passing]),
                        run=mock.Mock(return_value=subprocess.CompletedProcess([str(exporter)], 0)),
                        snapshot=lambda: next(snapshots),
                        transaction=transaction,
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
                        [str(arbitrary)],
                        check=mock.Mock(),
                        snapshot=lambda: ("unused",),
                        transaction=mock.Mock(spec=receipt.ReceiptTransaction),
                        run=mock.Mock(),
                        root=root,
                    )
                with self.assertRaisesRegex(receipt.AuthoringReceiptError, "locked to reviewed"):
                    receipt.run_checked_export(
                        ["/usr/bin/true"],
                        check=mock.Mock(),
                        snapshot=lambda: ("unused",),
                        transaction=mock.Mock(spec=receipt.ReceiptTransaction),
                        run=mock.Mock(),
                        root=root,
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

    def test_paired_writer_rolls_back_both_receipts_on_promotion_fault(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "review" / "echo.quarrune" / "g5" / "AUTHORING_STACK_RECEIPT.txt"
            second = root / "review" / "anm.echo.quarrune" / "g5" / "AUTHORING_STACK_RECEIPT.txt"
            for path, payload in ((first, b"old-model\n"), (second, b"old-animation\n")):
                path.parent.mkdir(parents=True)
                path.write_bytes(payload)
            def fault_second(index: int, _destination: Path) -> None:
                if index == 1:
                    raise OSError("controlled receipt fault")

            with self.assertRaisesRegex(receipt.AuthoringReceiptError, "rolled back"):
                receipt.write_receipts_atomically(
                    [(first, b"new-model\n"), (second, b"new-animation\n")],
                    root=root,
                    replace=True,
                    before_promote=fault_second,
                )
            self.assertEqual(first.read_bytes(), b"old-model\n")
            self.assertEqual(second.read_bytes(), b"old-animation\n")

    def test_paired_writer_rolls_back_both_receipts_on_interruption(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "review" / "echo.quarrune" / "g5" / "AUTHORING_STACK_RECEIPT.txt"
            second = root / "review" / "anm.echo.quarrune" / "g5" / "AUTHORING_STACK_RECEIPT.txt"
            for path, payload in ((first, b"old-model\n"), (second, b"old-animation\n")):
                path.parent.mkdir(parents=True)
                path.write_bytes(payload)
            def interrupt_second(index: int, _destination: Path) -> None:
                if index == 1:
                    raise KeyboardInterrupt("controlled receipt interruption")

            with self.assertRaisesRegex(receipt.AuthoringReceiptError, "rolled back"):
                receipt.write_receipts_atomically(
                    [(first, b"new-model\n"), (second, b"new-animation\n")],
                    root=root,
                    replace=True,
                    before_promote=interrupt_second,
                )
            self.assertEqual(first.read_bytes(), b"old-model\n")
            self.assertEqual(second.read_bytes(), b"old-animation\n")

    def test_parent_swap_fails_closed_and_rolls_back_without_touching_attacker_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as outside:
            root = Path(temporary)
            outside_root = Path(outside)
            first = root / "review/echo.quarrune/g5/AUTHORING_STACK_RECEIPT.txt"
            second = root / "review/anm.echo.quarrune/g5/AUTHORING_STACK_RECEIPT.txt"
            for path, payload in ((first, b"old-model\n"), (second, b"old-animation\n")):
                path.parent.mkdir(parents=True)
                path.write_bytes(payload)
            attacker = outside_root / "attacker"
            attacker.mkdir()
            moved = outside_root / "moved-original"

            def swap_second_parent(index: int, _destination: Path) -> None:
                if index == 1:
                    second.parent.rename(moved)
                    second.parent.symlink_to(attacker, target_is_directory=True)

            with self.assertRaisesRegex(receipt.AuthoringReceiptError, "rolled back"):
                receipt.write_receipts_atomically(
                    [(first, b"new-model\n"), (second, b"new-animation\n")],
                    root=root,
                    replace=True,
                    before_promote=swap_second_parent,
                )
            self.assertEqual(first.read_bytes(), b"old-model\n")
            self.assertFalse((attacker / second.name).exists())
            self.assertEqual((moved / second.name).read_bytes(), b"old-animation\n")

    def test_gate5_lock_serializes_concurrent_pair_writers_without_mixed_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "review/echo.quarrune/g5/AUTHORING_STACK_RECEIPT.txt"
            second = root / "review/anm.echo.quarrune/g5/AUTHORING_STACK_RECEIPT.txt"
            for path in (first, second):
                path.parent.mkdir(parents=True)
                path.write_bytes(b"old\n")
            context = multiprocessing.get_context("spawn")
            start = context.Event()
            workers = [
                context.Process(
                    target=_concurrent_receipt_writer,
                    args=(str(root), tag, start),
                )
                for tag in ("A", "B")
            ]
            for worker in workers:
                worker.start()
            start.set()
            for worker in workers:
                worker.join(20)
            self.assertEqual([worker.exitcode for worker in workers], [0, 0])
            model_tag = first.read_text(encoding="utf-8").split(":", 1)[0]
            animation_tag = second.read_text(encoding="utf-8").split(":", 1)[0]
            self.assertEqual(model_tag, animation_tag)
            events = (root / "transaction.log").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(events), 4)
            self.assertEqual(events[0].replace("enter:", ""), events[1].replace("exit:", ""))
            self.assertEqual(events[2].replace("enter:", ""), events[3].replace("exit:", ""))

    def test_complete_pair_snapshot_rejects_output_closure_member_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sources, outputs, members = self.prepare_manifest_pair(root)
            captured = receipt.capture_gate5_pair_snapshot(
                sources, outputs, build_id="n64game-g5-deadbeef", root=root
            )
            self.assertEqual(len(captured.source.roots), 2)
            self.assertEqual(len(captured.output.roots), 2)
            self.assertEqual(len(captured.output.members), 2)
            members[1].write_bytes(b"closure mutation\n")
            with self.assertRaisesRegex(receipt.AuthoringReceiptError, "digest/count mismatch"):
                receipt.capture_gate5_pair_snapshot(
                    sources, outputs, build_id="n64game-g5-deadbeef", root=root
                )

    def test_checked_export_rejects_valid_postcheck_output_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            exporter = self.prepare_export_root(root)
            sources, outputs, members = self.prepare_manifest_pair(root)
            calls = 0

            def check() -> dict[str, object]:
                nonlocal calls
                calls += 1
                if calls == 2:
                    members[0].write_bytes(b"valid but changed output\n")
                    fields = outputs[0].read_text(encoding="utf-8").rstrip("\n").split("\t")
                    fields[1] = str(members[0].stat().st_size)
                    fields[2] = receipt.sha256_file(members[0])
                    outputs[0].write_text("\t".join(fields) + "\n", encoding="utf-8")
                return self.passing_stack_report()

            def snapshot() -> receipt.Gate5PairSnapshot:
                return receipt.capture_gate5_pair_snapshot(
                    sources,
                    outputs,
                    build_id="n64game-g5-deadbeef",
                    root=root,
                )

            with (
                mock.patch.object(receipt, "GATE5_EXPORT_IMPLEMENTED", True),
                mock.patch.object(
                    receipt,
                    "APPROVED_GATE5_EXPORTER_SHA256",
                    receipt.sha256_file(exporter),
                ),
                receipt.gate5_transaction_lock(root) as transaction,
                self.assertRaisesRegex(
                    receipt.AuthoringReceiptError, "source/output identity changed"
                ),
            ):
                receipt.run_checked_export(
                    [str(exporter)],
                    check=check,
                    snapshot=snapshot,
                    transaction=transaction,
                    run=mock.Mock(
                        return_value=subprocess.CompletedProcess([str(exporter)], 0)
                    ),
                    root=root,
                )

    def test_paired_main_builds_two_receipts_from_one_checked_export(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scopes = ("echo.quarrune", "anm.echo.quarrune")
            sources: dict[str, Path] = {}
            outputs: dict[str, Path] = {}
            destinations: dict[str, Path] = {}
            for scope in scopes:
                sources[scope] = root / "source" / scope / "SOURCE_MANIFEST.sha256"
                outputs[scope] = root / "output" / scope / "OUTPUT_MANIFEST.sha256"
                destinations[scope] = root / "receipt" / scope / "AUTHORING_STACK_RECEIPT.txt"
                sources[scope].parent.mkdir(parents=True)
                outputs[scope].parent.mkdir(parents=True)
                sources[scope].write_bytes(("source:" + scope + "\n").encode())
                outputs[scope].write_bytes(("output:" + scope + "\n").encode())
            source_roots = tuple(
                receipt.FileSnapshot(
                    str(path.relative_to(root)),
                    path.stat().st_size,
                    digest,
                )
                for path, digest in zip(sources.values(), ("a" * 64, "b" * 64))
            )
            output_roots = tuple(
                receipt.FileSnapshot(
                    str(path.relative_to(root)),
                    path.stat().st_size,
                    digest,
                )
                for path, digest in zip(outputs.values(), ("c" * 64, "d" * 64))
            )
            source_closure = receipt.ManifestClosureSnapshot(source_roots, source_roots, ())
            output_closure = receipt.ManifestClosureSnapshot(output_roots, output_roots, ())
            verified = receipt.Gate5PairSnapshot(source_closure, output_closure)
            written: list[tuple[Path, bytes]] = []

            def capture_write(records: list[tuple[Path, bytes]], **_kwargs: object) -> None:
                written.extend(records)

            with (
                mock.patch.object(receipt, "ROOT", root),
                mock.patch.object(receipt, "GATE5_EXPORT_IMPLEMENTED", True),
                mock.patch.object(receipt, "APPROVED_GATE5_EXPORTER_SHA256", "a" * 64),
                mock.patch.object(receipt, "canonical_source_manifest", side_effect=lambda scope: sources[scope]),
                mock.patch.object(receipt, "canonical_output_manifest", side_effect=lambda scope: outputs[scope]),
                mock.patch.object(receipt, "canonical_receipt_path", side_effect=lambda scope, _gate: destinations[scope]),
                mock.patch.object(receipt, "preflight_receipt_target"),
                mock.patch.object(receipt, "_capture_manifest_closure", return_value=source_closure),
                mock.patch.object(
                    receipt, "capture_gate5_pair_snapshot", return_value=verified
                ),
                mock.patch.object(
                    receipt,
                    "run_checked_export",
                    return_value=receipt.CheckedExport(
                        tuple(self.stack_identity().items()), verified
                    ),
                ) as checked,
                mock.patch.object(receipt, "write_receipts_atomically", side_effect=capture_write),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                result = receipt.main([
                    "g5-export-pair", "--scope", scopes[0], "--paired-scope", scopes[1],
                    "--build-id", "n64game-g5-deadbeef", "--replace",
                ])
            self.assertEqual(result, 0)
            command = checked.call_args.args[0]
            self.assertEqual(command.count("--scope"), 1)
            self.assertEqual(command.count("--paired-scope"), 1)
            self.assertEqual([path for path, _payload in written], [destinations[value] for value in scopes])
            rendered = [payload.decode("utf-8") for _path, payload in written]
            self.assertIn("scope_id: echo.quarrune\n", rendered[0])
            self.assertIn("scope_id: anm.echo.quarrune\n", rendered[1])
            self.assertIn("build_id: n64game-g5-deadbeef\n", rendered[0])
            self.assertIn("build_id: n64game-g5-deadbeef\n", rendered[1])
            self.assertIn(f"output_manifest_sha256: {'c' * 64}\n", rendered[0])
            self.assertIn(f"output_manifest_sha256: {'d' * 64}\n", rendered[1])

    def test_writer_rejects_parent_symlink_even_when_target_stays_inside_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_parent = root / "real"
            real_parent.mkdir()
            (root / "review").symlink_to(real_parent, target_is_directory=True)
            destination = root / "review" / "echo.quarrune" / "g2" / "AUTHORING_STACK_RECEIPT.txt"
            with self.assertRaisesRegex(receipt.AuthoringReceiptError, "symlink"):
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
