from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ASSET_SOURCE = (ROOT / "src" / "support_echo_render_assets.c").read_text(
    encoding="utf-8"
)
ASSET_HEADER = (ROOT / "src" / "support_echo_render_assets.h").read_text(
    encoding="utf-8"
)
RENDER_SOURCE = (ROOT / "src" / "support_echo_renderer.c").read_text(
    encoding="utf-8"
)
GAME_RENDER_SOURCE = (ROOT / "src" / "n64game_render.c").read_text(
    encoding="utf-8"
)
GAME_RENDER_HEADER = (ROOT / "src" / "n64game_render.h").read_text(
    encoding="utf-8"
)
CORE_SOURCE = (ROOT / "src" / "n64game_core.c").read_text(encoding="utf-8")
CORE_HEADER = (ROOT / "src" / "n64game_core.h").read_text(encoding="utf-8")


def function_body(source: str, name: str) -> str:
    match = re.search(rf"\b{name}\s*\([^;]*?\)\s*\{{", source, re.DOTALL)
    if match is None:
        raise AssertionError(name)
    depth = 1
    cursor = match.end()
    while cursor < len(source) and depth:
        depth += (source[cursor] == "{") - (source[cursor] == "}")
        cursor += 1
    if depth != 0:
        raise AssertionError(name)
    return source[match.end():cursor - 1]


class SupportEchoRenderContractTests(unittest.TestCase):
    def test_three_canonical_profiles_have_disjoint_dynamic_references(self) -> None:
        expected = {
            "AYSELOR": ("0x41595330", "0x41595331"),
            "GYRECLAST": ("0x47595230", "0x47595231"),
            "KIVARRAX": ("0x4B495630", "0x4B495631"),
        }
        observed: set[str] = set()
        for name, references in expected.items():
            for suffix, reference in zip(("TOP", "BOTTOM"), references):
                self.assertIn(
                    f"{name}_BODY_{suffix}_REFERENCE UINT32_C({reference})",
                    ASSET_HEADER,
                )
                self.assertNotIn(reference, observed)
                observed.add(reference)
            slug = name.lower()
            self.assertIn(
                f'"rom:/echo/echo.{slug}/tex_{slug}_body_ci8_64x64.sprite"',
                ASSET_SOURCE,
            )
            self.assertIn(
                f'"rom:/echo/echo.{slug}/tex_{slug}_blob_shadow_ia8_32x32.sprite"',
                ASSET_SOURCE,
            )

    def test_ci8_atlas_is_split_into_two_tmem_safe_views_and_fails_closed(self) -> None:
        profile = function_body(ASSET_SOURCE, "body_profile")
        load = function_body(ASSET_SOURCE, "support_echo_render_assets_load")
        callback = function_body(
            ASSET_SOURCE, "support_echo_render_assets_dynamic_texture_cb"
        )
        self.assertEqual(load.count("surface_make_sub("), 2)
        self.assertIn("!rdpq_tex_can_upload(&top)", load)
        self.assertIn("!rdpq_tex_can_upload(&bottom)", load)
        for token in (
            "if (tile != TILE0)",
            "texture->texWidth != BODY_WIDTH",
            "texture->texHeight != BODY_REGION_HEIGHT",
            "material->textureB.texReference != 0U",
            "material->textureB.texPath != NULL",
            "uploaded != BODY_REGION_BYTES",
            "rdpq_mode_tlut(TLUT_RGBA16)",
            "rdpq_tex_upload_tlut(",
        ):
            self.assertIn(token, callback)
        self.assertGreaterEqual(callback.count("callback_fault = true"), 5)
        callback_ok = function_body(
            ASSET_SOURCE, "support_echo_render_assets_callback_ok"
        )
        self.assertIn("successful_body_callbacks == UINT8_C(3)", callback_ok)
        self.assertIn("palette_index >= palette_colors", profile)
        self.assertIn("palette_colors - seen_colors > 1", profile)
        self.assertIn("seen_colors < BODY_MIN_COLORS", profile)
        self.assertIn("(palette[index] & UINT16_C(1))", profile)

    def test_recorded_draw_blocks_retain_sprite_ownership_through_teardown(self) -> None:
        retain = function_body(ASSET_SOURCE, "retain_current_recording")
        release = function_body(
            ASSET_SOURCE, "release_recorded_block_reference"
        )
        unload = function_body(ASSET_SOURCE, "support_echo_render_assets_unload")
        self.assertIn("rspq_block_is_recording()", retain)
        self.assertIn("rspq_block_atexit(release_recorded_block_reference", retain)
        self.assertIn("--lifetime->recorded_block_references", release)
        self.assertIn("lifetime->release_requested", release)
        self.assertLess(unload.index("rspq_wait();"), unload.index("release_requested = true"))
        self.assertIn("*assets = (SupportEchoRenderAssets){0}", unload)

    def test_renderer_preflights_exact_reduced_animation_and_bone_contracts(self) -> None:
        model_contract = function_body(RENDER_SOURCE, "model_contract_ok")
        setup = function_body(RENDER_SOURCE, "setup_instance")
        for count in ("AYSELOR_BONE_COUNT = 18", "GYRECLAST_BONE_COUNT = 18", "KIVARRAX_BONE_COUNT = 20"):
            self.assertIn(count, RENDER_SOURCE)
        for name in ("idle_a", "reposition", "hit"):
            self.assertIn(f'"{name}"', RENDER_SOURCE)
        self.assertIn("t3d_model_get_animation_count(model)", model_contract)
        self.assertIn("skeleton->boneCount != profile->bone_count", model_contract)
        self.assertIn("animation->duration <= 0.0f", model_contract)
        for token in (
            "support_echo_render_assets_load(&instance->assets, kind)",
            "t3d_skeleton_create_buffered(",
            "t3d_skeleton_clone(",
            "t3d_anim_set_looping(&instance->reposition_anim, false)",
            "t3d_anim_set_looping(&instance->hit_anim, false)",
            "t3d_model_draw_custom(",
            "support_echo_render_assets_dynamic_texture_cb",
            "support_echo_render_assets_callback_ok(&instance->assets)",
            "instance->ready = true",
        ):
            self.assertIn(token, setup)

    def test_fixed_step_events_drive_one_shots_and_preserve_knockout_hit_pose(self) -> None:
        update = function_body(RENDER_SOURCE, "support_echo_renderer_update")
        ambient_update = function_body(
            RENDER_SOURCE, "support_echo_renderer_update_ambient"
        )
        update_instance = function_body(RENDER_SOURCE, "update_instance")
        apply_event = function_body(RENDER_SOURCE, "apply_battle_event")
        draw_battle = function_body(GAME_RENDER_SOURCE, "draw_battle")
        draw_annex = function_body(GAME_RENDER_SOURCE, "draw_annex")
        self.assertIn("uint32_t event_serial;", CORE_HEADER)
        apply_action = function_body(CORE_SOURCE, "apply_action")
        self.assertLess(
            apply_action.index("++battle->event_serial;"),
            apply_action.index("battle->last_event = (N64GameBattleEvent){0};"),
        )
        self.assertIn("battle->event_serial", update)
        self.assertIn("delta_seconds", update_instance)
        self.assertIn("1.0f / 30.0f", update)
        self.assertIn("2.0f / 30.0f", ambient_update)
        self.assertIn("t3d_anim_is_playing(motion_anim)", update_instance)
        self.assertIn("t3d_skeleton_blend(", update_instance)
        self.assertIn("N64GAME_TARGET_ALL", apply_event)
        self.assertIn("N64GAME_SUPPORT_ECHO_MOTION_HIT", apply_event)
        self.assertIn("knockout_motion", draw_battle)
        self.assertIn("reset_motion(&renderer->instances[index])", ambient_update)
        self.assertIn(
            "update_instance(&renderer->instances[kind], AMBIENT_DELTA_SECONDS)",
            ambient_update,
        )
        self.assertIn("support_echo_renderer_update_ambient(", draw_annex)
        self.assertNotIn("&renderer->support_echoes, &game->battle", draw_annex)

    def test_battle_uses_three_real_models_and_shadows_without_procedural_fallback(self) -> None:
        finish = function_body(GAME_RENDER_SOURCE, "n64game_renderer_finish_init")
        battle = function_body(GAME_RENDER_SOURCE, "draw_battle")
        destroy = function_body(GAME_RENDER_SOURCE, "n64game_renderer_destroy")
        self.assertIn("SupportEchoRenderer support_echoes;", GAME_RENDER_HEADER)
        self.assertIn("support_echo_renderer_init(", finish)
        self.assertIn("support_echo_renderer_update(", battle)
        self.assertIn("support_echo_renderer_draw_shadow(", battle)
        self.assertIn("support_echo_renderer_draw(", battle)
        self.assertIn("BATTLE_QUARRUNE_SCALE", battle)
        self.assertIn("BATTLE_SUPPORT_YAWS[kind]", battle)
        self.assertNotIn("draw_actor(", battle)
        self.assertIn("support_echo_renderer_destroy(&renderer->support_echoes)", destroy)
        makefile = (ROOT / "mk" / "rom.mk").read_text(encoding="utf-8")
        self.assertIn("$(BUILD_DIR)/support_echo_render_assets.o", makefile)
        self.assertIn("$(BUILD_DIR)/support_echo_renderer.o", makefile)


if __name__ == "__main__":
    unittest.main()
