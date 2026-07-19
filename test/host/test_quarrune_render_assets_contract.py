from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src" / "quarrune_render_assets.c"
HEADER = ROOT / "src" / "quarrune_render_assets.h"


class QuarruneRenderAssetsContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = SOURCE.read_text(encoding="utf-8")
        self.header = HEADER.read_text(encoding="utf-8")

    def function_body(self, name: str) -> str:
        match = re.search(rf"\b{name}\s*\([^;]*?\)\s*\{{", self.source, re.DOTALL)
        self.assertIsNotNone(match, name)
        assert match is not None
        depth = 1
        cursor = match.end()
        while cursor < len(self.source) and depth:
            depth += (self.source[cursor] == "{") - (self.source[cursor] == "}")
            cursor += 1
        self.assertEqual(depth, 0, name)
        return self.source[match.end():cursor - 1]

    def test_public_ids_and_canonical_rom_paths_are_exact(self) -> None:
        self.assertIn("QUARRUNE_BODY_TOP_REFERENCE UINT32_C(0x51554230)", self.header)
        self.assertIn("QUARRUNE_BODY_BOTTOM_REFERENCE UINT32_C(0x51554231)", self.header)
        self.assertIn(
            '"rom:/echo/echo.quarrune/tex_quarrune_body_ci8_64x64.sprite"', self.source
        )
        self.assertIn(
            '"rom:/echo/echo.quarrune/tex_quarrune_blob_shadow_ia8_32x32.sprite"', self.source
        )

    def test_full_ci8_atlas_is_never_uploaded_and_two_local_views_are_exact(self) -> None:
        load = self.function_body("quarrune_render_assets_load")
        self.assertEqual(load.count("surface_make_sub("), 2)
        self.assertIn("&body_pixels, 0U, 0U, BODY_WIDTH, BODY_REGION_HEIGHT", load)
        self.assertIn(
            "&body_pixels, 0U, BODY_REGION_HEIGHT, BODY_WIDTH, BODY_REGION_HEIGHT", load
        )
        self.assertIn("!rdpq_tex_can_upload(&top)", load)
        self.assertIn("!rdpq_tex_can_upload(&bottom)", load)
        self.assertNotIn("rdpq_sprite_upload", self.function_body("body_profile"))
        self.assertNotIn("rdpq_sprite_upload", load)

    def test_dynamic_callback_is_tile0_region_local_palette_complete_and_fail_closed(self) -> None:
        callback = self.function_body("quarrune_render_assets_dynamic_texture_cb")
        self.assertIn("if (tile != TILE0)", callback)
        self.assertIn("&material->textureA", callback)
        self.assertIn("material->textureB.texReference != 0U", callback)
        self.assertIn("material->textureB.texPath != NULL", callback)
        self.assertIn("QUARRUNE_BODY_TOP_REFERENCE", callback)
        self.assertIn("QUARRUNE_BODY_BOTTOM_REFERENCE", callback)
        self.assertEqual(callback.count("rdpq_tex_upload("), 1)
        self.assertNotIn("rdpq_tex_upload_sub", callback)
        self.assertNotIn("rdpq_sprite_upload", callback)
        self.assertNotIn("rdpq_tex_multi_begin", callback)
        self.assertIn("uploaded != BODY_REGION_BYTES", callback)
        self.assertIn("rdpq_mode_mipmap(MIPMAP_NONE, 0)", callback)
        self.assertIn("rdpq_mode_tlut(TLUT_RGBA16)", callback)
        self.assertIn("rdpq_tex_upload_tlut(", callback)
        self.assertLess(callback.index("rdpq_mode_tlut"), callback.index("rdpq_tex_upload_tlut"))
        self.assertGreaterEqual(callback.count("callback_fault = true"), 5)

    def test_recorded_blocks_retain_storage_and_success_requires_both_regions(self) -> None:
        retain = self.function_body("retain_current_recording")
        self.assertIn("rspq_block_is_recording()", retain)
        self.assertIn("++assets->lifetime->recorded_block_references", retain)
        self.assertIn("rspq_block_atexit(release_recorded_block_reference", retain)
        release = self.function_body("release_recorded_block_reference")
        self.assertIn("--lifetime->recorded_block_references", release)
        self.assertIn("lifetime->release_requested", release)
        self.assertIn("release_owned_sprites(lifetime)", release)
        callback_ok = self.function_body("quarrune_render_assets_callback_ok")
        self.assertIn("successful_body_callbacks == UINT8_C(3)", callback_ok)

    def test_runtime_profiles_and_teardown_keep_ownership_explicit(self) -> None:
        body = self.function_body("body_profile")
        for token in (
            "FMT_CI8", "BODY_WIDTH", "BODY_HEIGHT", "sprite_fits_tmem(sprite)",
            "BODY_MIN_COLORS", "rdpq_tex_can_upload(&pixels)", "seen[palette_index] = true",
            "palette[prior] == palette[index]",
        ):
            self.assertIn(token, body)
        shadow = self.function_body("shadow_profile")
        for token in ("FMT_IA8", "SHADOW_WIDTH", "SHADOW_HEIGHT", "sprite_fits_tmem(sprite)"):
            self.assertIn(token, shadow)
        unload = self.function_body("quarrune_render_assets_unload")
        self.assertLess(unload.index("rspq_wait();"), unload.index("release_requested = true"))
        self.assertIn("recorded_block_references == 0U", unload)
        self.assertIn("*assets = (QuarruneRenderAssets){0}", unload)
        self.assertIn("if (released_now)", unload)
        self.assertNotIn("sprite_free(", unload)
        load = self.function_body("quarrune_render_assets_load")
        self.assertIn("assets->lifetime != NULL", load)
        self.assertNotIn("*assets = (QuarruneRenderAssets){0}", load)

    def test_rom_build_compiles_the_helper_without_loading_assets_in_diagnostic(self) -> None:
        rom_make = (ROOT / "mk" / "rom.mk").read_text(encoding="utf-8")
        self.assertIn("$(BUILD_DIR)/quarrune_render_assets.o", rom_make)
        diagnostic = (ROOT / "src" / "main.c").read_text(encoding="utf-8")
        self.assertNotIn("quarrune_render_assets_load", diagnostic)

    def test_runtime_helper_bundle_matches_the_frozen_output_binding_pin(self) -> None:
        paths = ("src/quarrune_render_assets.c", "src/quarrune_render_assets.h")
        digest = hashlib.sha256(b"n64game-quarrune-runtime-helper-v1\n")
        for path in paths:
            member = (ROOT / path).read_bytes()
            digest.update(f"{path}\t{hashlib.sha256(member).hexdigest()}\n".encode())
        contract = (ROOT / "lib" / "n64game" / "tiny3d_package_contract.rb").read_text(
            encoding="utf-8"
        )
        match = re.search(
            r'APPROVED_RUNTIME_HELPER_BUNDLE_SHA256\s*=\s*\n\s*"([0-9a-f]{64})"',
            contract,
        )
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(digest.hexdigest(), match.group(1))


if __name__ == "__main__":
    unittest.main()
