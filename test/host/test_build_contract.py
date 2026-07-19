from __future__ import annotations

import hashlib
import json
import re
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
        self.assertIn(digest, (ROOT / "scripts" / "run-ares").read_text(encoding="utf-8"))
        self.assertIn(digest, (ROOT / "scripts" / "validate-asset-contract").read_text(encoding="utf-8"))

    def test_build_uses_audited_container_entrypoint(self) -> None:
        script = (ROOT / "scripts" / "build-rom").read_text(encoding="utf-8")
        self.assertIn("node node_modules/libdragon/index.js start", script)
        self.assertNotIn("libdragon/index.js exec", script)
        self.assertIn("docker exec", script)
        self.assertIn(".Config.Image", script)
        self.assertIn('.Destination "/libdragon"', script)


if __name__ == "__main__":
    unittest.main()
