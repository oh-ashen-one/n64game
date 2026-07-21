from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src" / "player_render_assets.c"
HEADER = ROOT / "src" / "player_render_assets.h"


class PlayerRenderAssetsContractTests(unittest.TestCase):
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

    def test_public_api_ids_and_body_path_are_exact(self) -> None:
        self.assertIn("PLAYER_BODY_TOP_REFERENCE UINT32_C(0x41524930)", self.header)
        self.assertIn("PLAYER_BODY_BOTTOM_REFERENCE UINT32_C(0x41524931)", self.header)
        for name in (
            "player_render_assets_load",
            "player_render_assets_dynamic_texture_cb",
            "player_render_assets_callback_ok",
            "player_render_assets_unload",
        ):
            self.assertIn(name, self.header)
        self.assertIn(
            '"rom:/chr/chr.player.ari/tex_player_ari_body_ci8_64x64.sprite"',
            self.source,
        )
        self.assertNotIn("tex_player_ari_face", self.source)
        self.assertEqual(self.source.count("sprite_load("), 1)

    def test_full_ci8_atlas_is_split_into_two_tmem_safe_views(self) -> None:
        load = self.function_body("player_render_assets_load")
        self.assertEqual(load.count("surface_make_sub("), 2)
        self.assertIn("&body_pixels, 0U, 0U, BODY_WIDTH, BODY_REGION_HEIGHT", load)
        self.assertIn(
            "&body_pixels, 0U, BODY_REGION_HEIGHT, BODY_WIDTH, BODY_REGION_HEIGHT",
            load,
        )
        self.assertIn("!rdpq_tex_can_upload(&top)", load)
        self.assertIn("!rdpq_tex_can_upload(&bottom)", load)
        self.assertNotIn("rdpq_sprite_upload", load)

    def test_runtime_profile_locks_the_observed_five_color_atlas(self) -> None:
        profile = self.function_body("body_profile")
        self.assertIn("BODY_PALETTE_COLORS = 5", self.source)
        for token in (
            "FMT_CI8",
            "BODY_WIDTH",
            "BODY_HEIGHT",
            "sprite_fits_tmem(sprite)",
            "palette_colors != BODY_PALETTE_COLORS",
            "palette_index >= BODY_PALETTE_COLORS",
            "seen[palette_index] = true",
            "maximum_index + 1 != palette_colors",
            "palette[prior] == palette[index]",
            "palette[index] & UINT16_C(1)",
            "rdpq_tex_can_upload(&pixels)",
        ):
            self.assertIn(token, profile)

    def test_callback_is_fail_closed_region_local_and_palette_complete(self) -> None:
        callback = self.function_body("player_render_assets_dynamic_texture_cb")
        for token in (
            "if (tile != TILE0)",
            "&material->textureA",
            "PLAYER_BODY_TOP_REFERENCE",
            "PLAYER_BODY_BOTTOM_REFERENCE",
            "material->textureB.texReference != 0U",
            "material->textureB.texPath != NULL",
            "uploaded != BODY_REGION_BYTES",
            "rdpq_mode_mipmap(MIPMAP_NONE, 0)",
            "rdpq_mode_tlut(TLUT_RGBA16)",
            "rdpq_tex_upload_tlut(",
        ):
            self.assertIn(token, callback)
        self.assertEqual(callback.count("rdpq_tex_upload("), 1)
        self.assertNotIn("rdpq_sprite_upload", callback)
        self.assertNotIn("rdpq_tex_upload_sub", callback)
        self.assertGreaterEqual(callback.count("callback_fault = true"), 5)

    def test_recorded_block_owns_storage_until_atexit_release(self) -> None:
        retain = self.function_body("retain_current_recording")
        self.assertIn("rspq_block_is_recording()", retain)
        self.assertIn("++assets->lifetime->recorded_block_references", retain)
        self.assertIn("rspq_block_atexit(release_recorded_block_reference", retain)
        release = self.function_body("release_recorded_block_reference")
        self.assertIn("--lifetime->recorded_block_references", release)
        self.assertIn("lifetime->release_requested", release)
        self.assertIn("release_owned_sprite(lifetime)", release)
        callback_ok = self.function_body("player_render_assets_callback_ok")
        self.assertIn("successful_body_callbacks == UINT8_C(3)", callback_ok)

    def test_unload_waits_zeros_public_state_and_defers_when_referenced(self) -> None:
        unload = self.function_body("player_render_assets_unload")
        self.assertLess(unload.index("rspq_wait();"), unload.index("release_requested = true"))
        self.assertIn("recorded_block_references == 0U", unload)
        self.assertIn("*assets = (PlayerRenderAssets){0}", unload)
        self.assertIn("if (released_now)", unload)
        self.assertNotIn("sprite_free(", unload)


if __name__ == "__main__":
    unittest.main()
