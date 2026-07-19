from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import n64game_authoring as authoring  # noqa: E402


class AuthoringStackTests(unittest.TestCase):
    def make_fast64_fixture(self, root: Path, version: tuple[int, int, int] = (2, 5, 3)) -> dict[str, object]:
        root.mkdir(parents=True)
        (root / "__init__.py").write_text(
            f"bl_info = {{'name': 'Fast64', 'version': {version!r}}}\n",
            encoding="utf-8",
        )
        internal = root / "fast64_internal"
        internal.mkdir()
        (internal / "exporter.py").write_text("FORMAT = 'T3D'\n", encoding="utf-8")
        identity = authoring.fast64_source_identity(root)
        return {
            "version": ".".join(str(item) for item in version),
            "commit": "fixture-commit",
            "source_tree_file_count": identity["file_count"],
            "source_tree_size": identity["size_bytes"],
            "source_tree_manifest_sha256": identity["manifest_sha256"],
            "source_tree_manifest_algorithm": identity["manifest_algorithm"],
        }

    def test_lock_contains_the_exact_approved_distribution_pins(self) -> None:
        lock = authoring.load_authoring_lock()
        self.assertEqual(lock["blender_macos_arm64"], authoring.EXPECTED_BLENDER_PIN)
        self.assertEqual(lock["fast64"], authoring.EXPECTED_FAST64_PIN)
        self.assertEqual(lock["blender_macos_arm64"]["release_asset_size"], 308255028)
        self.assertEqual(
            lock["blender_macos_arm64"]["release_asset_sha256"],
            "1fad76c7da9451c7d6db99f1a5ed3c0a1a461d0aa07bf2b639e2fb4804ca4f13",
        )
        self.assertEqual(lock["fast64"]["release_asset_size"], 1882004)
        self.assertEqual(
            lock["fast64"]["release_asset_url"],
            "https://github.com/Fast-64/fast64/releases/download/v2.5.3/fast64-v2.5.3.zip",
        )
        self.assertEqual(
            lock["fast64"]["release_asset_sha256"],
            "2a308e04ee591e328856e8dff5bbe5aa72f284873e874ba5aba5927831889010",
        )
        self.assertEqual(
            lock["fast64"]["commit"],
            "8e9630c11824a9c00e9379279d43c64264eda87e",
        )

    def test_canonical_runner_is_python_isolated_and_bytecode_free(self) -> None:
        self.assertEqual(sys.flags.isolated, 1)
        self.assertEqual(sys.flags.ignore_environment, 1)
        self.assertEqual(sys.flags.no_user_site, 1)
        self.assertEqual(sys.flags.dont_write_bytecode, 1)

    def test_exact_blender_version_output_is_accepted(self) -> None:
        output = (
            "Blender 4.5.11 LTS\n"
            "\tbuild hash: 4db51e9d1e1e\n"
            "\tbuild platform: Darwin\n"
        )
        report = authoring.parse_blender_version(output, authoring.EXPECTED_BLENDER_PIN)
        self.assertEqual(report["version"], "4.5.11 LTS")

    def test_blender_5_2_is_explicitly_rejected(self) -> None:
        output = (
            "Blender 5.2.0\n"
            "\tbuild hash: not-the-pin\n"
            "\tbuild platform: Darwin\n"
        )
        with self.assertRaisesRegex(authoring.AuthoringContractError, "Blender 5.2 is not accepted"):
            authoring.parse_blender_version(output, authoring.EXPECTED_BLENDER_PIN)

    def test_distribution_file_requires_exact_size_and_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "asset.zip"
            path.write_bytes(b"pinned release bytes")
            pin = {
                "release_asset_size": path.stat().st_size,
                "release_asset_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "release_asset_url": "https://example.invalid/release.zip",
            }
            report = authoring.verify_distribution_asset(path, pin, "fixture archive")
            self.assertEqual(report["status"], "PASS")
            path.write_bytes(b"tampered release bytes")
            with self.assertRaises(authoring.AuthoringContractError):
                authoring.verify_distribution_asset(path, pin, "fixture archive")

    def test_fast64_exact_source_tree_is_accepted_without_runtime_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "fast64"
            pin = self.make_fast64_fixture(root)
            report = authoring.verify_fast64_source(root, pin)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["version"], "2.5.3")
            self.assertEqual(report["file_count"], 2)

    def test_fast64_source_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "fast64"
            pin = self.make_fast64_fixture(root)
            (root / "fast64_internal" / "exporter.py").write_text(
                "FORMAT = 'tampered'\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(authoring.AuthoringContractError, "source tree differs"):
                authoring.verify_fast64_source(root, pin)

    def test_wrong_fast64_version_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "fast64"
            pin = self.make_fast64_fixture(root, version=(2, 5, 3))
            (root / "__init__.py").write_text(
                "bl_info = {'name': 'Fast64', 'version': (2, 5, 2)}\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(authoring.AuthoringContractError, "Fast64 version"):
                authoring.verify_fast64_source(root, pin)

    def test_missing_fast64_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing-fast64"
            with self.assertRaises(authoring.AuthoringContractError):
                authoring.fast64_source_identity(missing)

    def test_fast64_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "fast64"
            pin = self.make_fast64_fixture(root)
            (root / "linked.py").symlink_to(root / "__init__.py")
            with self.assertRaisesRegex(authoring.AuthoringContractError, "contains a symlink"):
                authoring.verify_fast64_source(root, pin)

    def test_fast64_bytecode_and_updater_state_are_rejected(self) -> None:
        for relative, payload in (
            (Path("__pycache__") / "__init__.cpython-311.pyc", b"executable bytecode"),
            (Path("fast64_updater") / "fast64_updater_status.json", b"{}\n"),
        ):
            with self.subTest(path=relative), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir) / "fast64"
                pin = self.make_fast64_fixture(root)
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
                with self.assertRaisesRegex(authoring.AuthoringContractError, "forbidden"):
                    authoring.verify_fast64_source(root, pin)

    def test_isolated_blender_environment_drops_injection_variables(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.dict(
            os.environ,
            {
                "PYTHONPATH": "/tmp/injected-python",
                "BLENDER_USER_CONFIG": "/tmp/injected-config",
                "DYLD_INSERT_LIBRARIES": "/tmp/injected.dylib",
            },
        ):
            fast64 = Path(temp_dir) / "real" / "scripts" / "addons" / "fast64"
            environment = authoring.isolated_blender_environment(Path(temp_dir) / "isolated", fast64)
        self.assertNotIn("PYTHONPATH", environment)
        self.assertNotIn("DYLD_INSERT_LIBRARIES", environment)
        self.assertNotEqual(environment["BLENDER_USER_CONFIG"], "/tmp/injected-config")
        self.assertEqual(environment["BLENDER_USER_SCRIPTS"], str(fast64.parents[1]))
        self.assertEqual(environment["PYTHONDONTWRITEBYTECODE"], "1")

    def test_codesign_requires_absolute_deep_strict_verification(self) -> None:
        details = (
            "Identifier=org.blenderfoundation.blender\n"
            "Authority=Developer ID Application: Stichting Blender Foundation (68UA947AUU)\n"
            "TeamIdentifier=68UA947AUU\n"
        )
        with mock.patch.object(authoring, "_run", side_effect=["valid on disk\n", details]) as run:
            report = authoring._codesign_identity(Path("/Applications/Blender.app"), authoring.EXPECTED_BLENDER_PIN)
        verify_command = run.call_args_list[0].args[0]
        self.assertEqual(verify_command[0], "/usr/bin/codesign")
        self.assertIn("--verify", verify_command)
        self.assertIn("--deep", verify_command)
        self.assertIn("--strict", verify_command)
        self.assertIn("-R", verify_command)
        self.assertIs(report["deep_strict_verified"], True)

    def test_probe_requires_fast64_to_be_enabled_loaded_and_from_locked_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "fast64"
            root.mkdir()
            payload = {
                "blender": [4, 5, 11],
                "default_enabled": True,
                "enabled": True,
                "loaded": True,
                "module": "fast64",
                "module_file": str((root / "__init__.py").resolve()),
                "version": [2, 5, 3],
            }
            accepted = authoring.parse_probe_output(
                authoring.PROBE_SENTINEL + json.dumps(payload),
                authoring.EXPECTED_BLENDER_PIN,
                authoring.EXPECTED_FAST64_PIN,
                root,
            )
            self.assertIs(accepted["enabled"], True)
            payload["enabled"] = False
            with self.assertRaisesRegex(authoring.AuthoringContractError, "preference enabled"):
                authoring.parse_probe_output(
                    authoring.PROBE_SENTINEL + json.dumps(payload),
                    authoring.EXPECTED_BLENDER_PIN,
                    authoring.EXPECTED_FAST64_PIN,
                    root,
                )

    def test_probe_rechecks_the_exact_fast64_pin_after_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            fast64 = base / "4.5" / "scripts" / "addons" / "fast64"
            pin = self.make_fast64_fixture(fast64)
            config = base / "4.5" / "config"
            config.mkdir()
            (config / "userpref.blend").write_bytes(b"fixture preferences")
            blender = base / "Blender.app" / "Contents" / "MacOS" / "Blender"
            blender.parent.mkdir(parents=True)
            blender.write_bytes(b"fixture executable")
            expected = authoring.expected_fast64_source_identity(pin)
            changed = {**expected, "manifest_sha256": "0" * 64}
            with (
                mock.patch.object(
                    authoring,
                    "fast64_source_identity",
                    side_effect=[expected, expected, changed],
                ),
                mock.patch.object(authoring, "_run", return_value="probe output"),
                mock.patch.object(
                    authoring,
                    "parse_probe_output",
                    return_value={"enabled": True, "loaded": True},
                ),
            ):
                with self.assertRaisesRegex(
                    authoring.AuthoringContractError,
                    "changed during the isolated enabled-state probe",
                ):
                    authoring.probe_fast64_enabled(
                        blender,
                        fast64,
                        authoring.EXPECTED_BLENDER_PIN,
                        pin,
                    )

    def test_default_paths_are_versioned_and_overridable(self) -> None:
        lock = authoring.load_authoring_lock()
        blender, fast64 = authoring.default_paths(lock)
        self.assertTrue(str(blender).endswith("Applications/Blender-4.5.11.app/Contents/MacOS/Blender"))
        self.assertTrue(
            str(fast64).endswith("Library/Application Support/Blender/4.5/scripts/addons/fast64")
        )
        with mock.patch.dict(
            "os.environ",
            {
                "N64GAME_BLENDER_BINARY": "/tmp/blender-fixture",
                "N64GAME_FAST64_ROOT": "/tmp/fast64-fixture",
            },
        ):
            overridden = authoring.default_paths(lock)
        self.assertEqual(overridden, (Path("/tmp/blender-fixture"), Path("/tmp/fast64-fixture")))


if __name__ == "__main__":
    unittest.main()
