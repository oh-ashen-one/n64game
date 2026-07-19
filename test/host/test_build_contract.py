from __future__ import annotations

import hashlib
import json
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import n64game_build as build  # noqa: E402


class BuildContractTests(unittest.TestCase):
    @staticmethod
    def pinned_rom_fixture() -> bytearray:
        ipl3_source = (ROOT / "vendor" / "libdragon" / "tools" / "ipl3.h").read_text(encoding="utf-8")
        data = bytearray(int(value, 16) for value in re.findall(r"0x([0-9a-fA-F]{2})", ipl3_source))
        if len(data) != build.LIBDRAGON_IPL3_END:
            raise AssertionError("unexpected pinned libdragon IPL3 length")
        data[0x20:0x34] = b"N64GAME GATE 3".ljust(20, b" ")
        data[0x34:0x38] = bytes(4)
        data[0x3B] = ord("N")
        data[0x3C:0x3E] = b"ED"
        data[0x3E] = 0
        data[0x3F] = 0x12
        data.extend(bytes(16384 - len(data)))
        data[build.TOC_OFFSET:build.TOC_OFFSET + 4] = b"TOC0"
        elf_offset = 0x1E00
        data[elf_offset:elf_offset + 20] = (
            b"\x7fELF" + bytes((2, 2, 1, 0)) + bytes(10) + bytes.fromhex("0008")
        )
        return data

    def test_dependency_pins_are_exact(self) -> None:
        resolved = build.verify_pins()
        self.assertEqual(resolved["libdragon"], "f13b48985edbf4310f07779c76d9a68c7605037b")
        self.assertEqual(resolved["tiny3d"], "e84172f29f719680ac3213a7f408c2f721ef7b24")

    def test_runtime_manifest_is_intentionally_empty_at_gate3(self) -> None:
        report = build.validate_runtime_assets()
        self.assertEqual(report["runtime_asset_count"], 0)

    def test_pinned_structural_rom_fixture_is_accepted(self) -> None:
        data = self.pinned_rom_fixture()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "test.z64"
            path.write_bytes(data)
            report = build.inspect_rom(path)
        self.assertEqual(report["title"], "N64GAME GATE 3")
        self.assertEqual(report["sha256"], hashlib.sha256(data).hexdigest())

    def test_validate_rom_command_rejects_a_symlink(self) -> None:
        data = self.pinned_rom_fixture()
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "target.z64"
            link = Path(temp_dir) / "link.z64"
            target.write_bytes(data)
            link.symlink_to(target)
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "n64game_build.py"), "validate-rom", str(link)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must not be a symlink", result.stdout)

    def test_wrong_rom_byte_order_is_rejected(self) -> None:
        data = self.pinned_rom_fixture()
        data[:4] = bytes.fromhex("37804012")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "test.v64"
            path.write_bytes(data)
            with self.assertRaises(build.ContractError):
                build.inspect_rom(path)

    def test_nonzero_legacy_checksum_words_are_rejected(self) -> None:
        data = self.pinned_rom_fixture()
        data[0x10:0x18] = bytes.fromhex("0123456789abcdef")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "test.z64"
            path.write_bytes(data)
            with self.assertRaises(build.ContractError):
                build.inspect_rom(path)

    def test_modified_pinned_ipl3_is_rejected(self) -> None:
        data = self.pinned_rom_fixture()
        data[0x100] ^= 0x01
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "test.z64"
            path.write_bytes(data)
            with self.assertRaises(build.ContractError):
                build.inspect_rom(path)

    def test_wrong_advanced_homebrew_config_is_rejected(self) -> None:
        data = self.pinned_rom_fixture()
        data[0x3F] = 0x10
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "test.z64"
            path.write_bytes(data)
            with self.assertRaises(build.ContractError):
                build.inspect_rom(path)

    def test_diagnostic_source_uses_locked_display_and_tiny3d(self) -> None:
        source = (ROOT / "src" / "main.c").read_text(encoding="utf-8")
        self.assertIn("RESOLUTION_320x240", source)
        self.assertIn("DEPTH_16_BPP", source)
        self.assertIn("display_set_fps_limit(30.0f)", source)
        self.assertIn("t3d_init", source)
        self.assertIn("fm_vec3_norm(&rotation_axis, &rotation_axis)", source)

    def test_rom_is_staged_at_the_contract_path(self) -> None:
        makefile = (ROOT / "mk" / "rom.mk").read_text(encoding="utf-8")
        self.assertIn("ROM_OUTPUT := $(BUILD_DIR)/$(ROM_NAME).z64", makefile)
        self.assertIn("all: stage-rom", makefile)
        self.assertIn("stage-rom: $(ROM_NAME).z64", makefile)
        self.assertIn("mkdir -p $(dir $(ROM_OUTPUT))", makefile)
        self.assertIn("mv $< $(ROM_OUTPUT)", makefile)
        self.assertNotIn("$(ROM_OUTPUT): $(ROM_NAME).z64", makefile)

    def test_tiny3d_archive_is_linked_exactly_once(self) -> None:
        makefile = (ROOT / "mk" / "rom.mk").read_text(encoding="utf-8")
        elf_rule = "$(BUILD_DIR)/$(ROM_NAME).elf: $(OBJS) | $(T3D_ROOT)/build/libt3d.a"
        duplicate_rule = "$(BUILD_DIR)/$(ROM_NAME).elf: $(OBJS) $(T3D_ROOT)/build/libt3d.a"
        self.assertIn(elf_rule, makefile)
        self.assertNotIn(duplicate_rule, makefile)
        self.assertIn("include $(T3D_ROOT)/t3d.mk", makefile)

    def test_conversion_suppression_is_scoped_to_the_tiny3d_header(self) -> None:
        source = (ROOT / "src" / "main.c").read_text(encoding="utf-8")
        push = source.index("#pragma GCC diagnostic push")
        include = source.index("#include <t3d/t3d.h>")
        pop = source.index("#pragma GCC diagnostic pop")
        main = source.index("int main(void)")
        self.assertLess(push, include)
        self.assertLess(include, pop)
        self.assertLess(pop, main)

    def test_lock_is_valid_json_with_immutable_container(self) -> None:
        lock = json.loads((ROOT / "config" / "toolchain.lock.json").read_text(encoding="utf-8"))
        reference = lock["container"]["reference"]
        self.assertIn("@sha256:", reference)
        self.assertNotIn(":latest", reference)
        self.assertNotIn(":preview", reference)

    def test_libdragon_config_is_cli_canonical_and_byte_stable(self) -> None:
        path = ROOT / ".libdragon" / "config.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        expected = json.dumps(config, indent=2).encode("utf-8")
        self.assertEqual(path.read_bytes(), expected)

    def test_audited_ares_hash_is_consistent(self) -> None:
        lock = json.loads((ROOT / "config" / "toolchain.lock.json").read_text(encoding="utf-8"))
        digest = lock["ares"]["macos_executable_sha256"]
        wrapper = (ROOT / "scripts" / "run-ares").read_text(encoding="utf-8")
        self.assertIn(digest, wrapper)
        self.assertIn("--setting General/HomebrewMode=true", wrapper)
        self.assertIn("--setting Nintendo64/ExpansionPak=false", wrapper)
        self.assertIn("--setting Input/Defocus=Allow", wrapper)
        self.assertIn(digest, (ROOT / "scripts" / "validate-asset-contract").read_text(encoding="utf-8"))

    def test_gate3_boot_captures_match_the_evidence_manifest(self) -> None:
        capture_root = ROOT / "captures" / "gate3"
        evidence = json.loads((capture_root / "evidence.json").read_text(encoding="utf-8"))
        lines = (capture_root / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
        expected = {
            "ares-v148-ci-29674638989-frame-a.png": (
                "b5fde7458a6e606f76139732894dfa4784dd6fae2eb57f351fea5424ebe1d75a",
                (836, 672),
            ),
            "ares-v148-ci-29674638989-frame-b.png": (
                "0db4dc319016fbaddd01671748927c9560fb6e2af173948b18b9358ee98e94a5",
                (836, 672),
            ),
        }
        self.assertEqual(evidence["schema_version"], 2)
        self.assertEqual(evidence["ci"]["workflow_run"], 29674638989)
        self.assertEqual(evidence["ci"]["workflow_job"], 88159621235)
        self.assertEqual(evidence["ci"]["artifact_id"], 8438442749)
        self.assertEqual(
            evidence["rom"]["sha256"],
            "230896d0d8a39dae3dd6ee5e1e471377be51fdbb2b45b78a5c8439f865394d7e",
        )
        self.assertEqual(evidence["rom"]["size_bytes"], 212992)
        self.assertEqual(evidence["ares"]["version"], "v148")
        self.assertEqual(
            evidence["ares"]["executable_sha256"],
            "7a49f00f96a691458461d7c9cf453d95c0f5c054389bbd87c253987b8b6fa345",
        )
        self.assertIs(evidence["ares"]["homebrew_mode"], True)
        self.assertIs(evidence["ares"]["expansion_pak"], False)
        self.assertEqual(evidence["ares"]["defocus"], "Allow")
        self.assertEqual(evidence["confirmation_ci"]["workflow_run"], 29675864028)
        self.assertEqual(evidence["confirmation_ci"]["workflow_job"], 88163077829)
        self.assertEqual(evidence["confirmation_ci"]["artifact_id"], 8438863000)
        self.assertEqual(
            evidence["confirmation_ci"]["artifact_name"],
            "n64game-gate3-75499d5784967852cab2c4ca071cf7aeb05e2e70",
        )
        self.assertEqual(
            evidence["confirmation_ci"]["artifact_sha256"],
            "f7bc2ba02d37ed1535f300702fa721f40da9b7fe0787dac76b6653d026c3ca83",
        )
        self.assertEqual(
            evidence["confirmation_ci"]["pr_head"],
            "85e91c793eccaeff70327ea6fd67e8f7e775faad",
        )
        self.assertEqual(
            evidence["confirmation_ci"]["actions_merge_revision"],
            "75499d5784967852cab2c4ca071cf7aeb05e2e70",
        )
        self.assertEqual(
            evidence["confirmation_ci"]["actions_merge_tree"],
            "292a0c867bd71b1f1c7d5cf7d935f9b0953a0016",
        )
        self.assertIs(evidence["confirmation_ci"]["rom_matches_boot_evidence"], True)
        local_build = evidence["local_build"]
        self.assertEqual(local_build["status"], "PASS_WITH_AUDITED_DOCKER_COMPATIBLE_FALLBACK")
        self.assertEqual(local_build["gate3_closure"], "BLOCKED_DOCKER_DESKTOP_REQUIRED_BY_MASTER_SPEC")
        self.assertEqual(local_build["rom_built_at"], "2026-07-19T02:06:35-04:00")
        self.assertEqual(local_build["completed_at"], "2026-07-19T02:07:41-04:00")
        self.assertEqual(local_build["source_commit"], evidence["confirmation_ci"]["pr_head"])
        self.assertEqual(local_build["source_tree"], evidence["confirmation_ci"]["actions_merge_tree"])
        self.assertIs(local_build["source_dirty"], False)
        self.assertEqual(
            local_build["commands"],
            {
                "make_validate": "PASS",
                "make_rom": "PASS",
                "make_test": "PASS_17_OF_17",
                "make_report": "PASS",
                "bootstrap_all": "PASS",
            },
        )
        self.assertEqual(local_build["rom_sha256"], evidence["rom"]["sha256"])
        self.assertEqual(local_build["rom_size_bytes"], evidence["rom"]["size_bytes"])
        self.assertEqual(local_build["runtime"]["colima_version"], "0.10.3")
        self.assertEqual(local_build["runtime"]["lima_version"], "2.1.4")
        self.assertEqual(local_build["runtime"]["vm_driver"], "macOS Virtualization.Framework")
        self.assertEqual(local_build["runtime"]["vm_arch"], "aarch64")
        self.assertEqual(local_build["runtime"]["mount_type"], "virtiofs")
        self.assertIs(local_build["runtime"]["rosetta"], True)
        self.assertEqual(local_build["runtime"]["docker_client"], "29.6.2")
        self.assertEqual(local_build["runtime"]["docker_engine"], "29.5.2")
        self.assertEqual(local_build["runtime"]["container_platform"], "linux/amd64")
        self.assertEqual(
            local_build["runtime"]["container_image_id"],
            "sha256:36a295cbe43168e8adbfa5c86d956df3dc762a1ab6fda1b50dcb33bd78dc2d83",
        )
        self.assertEqual(local_build["docker_desktop"]["status"], "BLOCKED")
        self.assertEqual(local_build["docker_desktop"]["version"], "4.82.0")
        self.assertEqual(local_build["docker_desktop"]["build"], "233772")
        self.assertEqual(local_build["docker_desktop"]["engine"], "UNAVAILABLE")
        self.assertEqual(local_build["docker_desktop"]["host_policy_error"], "failed to call driver: 0x3")
        manifest_captures = {row["path"]: row for row in evidence["captures"]}
        self.assertEqual(set(manifest_captures), set(expected))
        self.assertEqual(len(lines), len(expected))
        seen: set[str] = set()
        for line in lines:
            digest, filename = line.split("  ", 1)
            self.assertIn(filename, expected)
            self.assertNotIn(filename, seen)
            seen.add(filename)
            data = (capture_root / filename).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), digest)
            self.assertEqual(digest, expected[filename][0])
            self.assertEqual(data[:16], b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
            self.assertEqual(struct.unpack(">II", data[16:24]), expected[filename][1])
            capture = manifest_captures[filename]
            self.assertEqual(capture["sha256"], digest)
            self.assertEqual(capture["size_bytes"], len(data))
            self.assertEqual((capture["width"], capture["height"]), expected[filename][1])
        self.assertEqual(seen, set(expected))
        self.assertEqual(len({row["sha256"] for row in manifest_captures.values()}), len(expected))

    def test_build_uses_audited_container_entrypoint(self) -> None:
        script = (ROOT / "scripts" / "build-rom").read_text(encoding="utf-8")
        container_script = (ROOT / "scripts" / "container-build").read_text(encoding="utf-8")
        self.assertIn("node node_modules/libdragon/index.js start", script)
        self.assertNotIn("libdragon/index.js exec", script)
        self.assertIn("docker exec", script)
        self.assertIn(".Config.Image", script)
        self.assertIn('.Destination "/libdragon"', script)
        self.assertIn('SOURCE_DATE_EPOCH="$(git show -s --format=%ct HEAD)"', script)
        self.assertIn('--env "SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH"', script)
        self.assertNotIn("git show", container_script)
        self.assertIn('[[ ! "${SOURCE_DATE_EPOCH:-}" =~ ^[1-9][0-9]*$ ]]', container_script)


if __name__ == "__main__":
    unittest.main()
