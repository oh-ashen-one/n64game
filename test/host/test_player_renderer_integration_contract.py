from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src" / "n64game_render.c"
HEADER = ROOT / "src" / "n64game_render.h"


class PlayerRendererIntegrationContractTests(unittest.TestCase):
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

    def test_renderer_owns_the_complete_skinned_player_lifecycle(self) -> None:
        for field in (
            "T3DModel *player_model;",
            "T3DSkeleton player_skeleton;",
            "T3DSkeleton player_idle_pose;",
            "T3DSkeleton player_walk_pose;",
            "T3DSkeleton player_run_pose;",
            "T3DAnim player_idle_anim;",
            "T3DAnim player_walk_anim;",
            "T3DAnim player_run_anim;",
            "PlayerRenderAssets player_assets;",
            "rspq_block_t *player_draw_block;",
            "float player_yaw;",
            "bool player_ready;",
        ):
            self.assertIn(field, self.header)

    def test_setup_is_fail_closed_and_preflights_exact_model_contract(self) -> None:
        model_contract = self.function_body("player_model_contract_ok")
        skeleton_contract = self.function_body("player_skeleton_contract_ok")
        setup = self.function_body("setup_player")
        self.assertIn('"rom:/chr/chr.player.ari/player_ari.t3dm"', self.source)
        self.assertIn("t3d_model_get_animation_count(model)", model_contract)
        self.assertIn("animation->duration <= 0.0f", model_contract)
        self.assertIn("animation->filePath[0] == '\\0'", model_contract)
        self.assertIn("PLAYER_BONE_COUNT = 24", self.source)
        self.assertIn("t3d_skeleton_find_bone", skeleton_contract)
        for name in ("idle_a", "walk", "run"):
            self.assertIn(f'"{name}"', self.source)
        for token in (
            "player_render_assets_load(&renderer->player_assets)",
            "t3d_model_load(PLAYER_MODEL_PATH)",
            "player_model_contract_ok(renderer->player_model)",
            "t3d_skeleton_create_buffered(",
            "t3d_skeleton_clone(",
            "t3d_anim_create(",
            "t3d_anim_attach(",
            "t3d_anim_update(&renderer->player_idle_anim, 0.0f)",
            "t3d_anim_update(&renderer->player_walk_anim, 0.0f)",
            "t3d_anim_update(&renderer->player_run_anim, 0.0f)",
            "t3d_model_draw_custom(",
            "player_render_assets_dynamic_texture_cb",
            "player_render_assets_callback_ok(&renderer->player_assets)",
            "renderer->player_ready = true",
        ):
            self.assertIn(token, setup)
        self.assertLess(setup.index("player_model_contract_ok"), setup.index("t3d_anim_create"))
        self.assertLess(
            setup.index("player_render_assets_callback_ok"),
            setup.index("renderer->player_ready = true"),
        )

    def test_fixed_step_locomotion_blends_and_retains_yaw_when_still(self) -> None:
        update = self.function_body("update_player_pose")
        self.assertIn("PLAYER_WALK_SPEED_Q8 = 85", self.source)
        self.assertIn("PLAYER_RUN_SPEED_Q8 = 154", self.source)
        for token in (
            "1.0f / 30.0f",
            "game->paused",
            "game->menu != N64GAME_MENU_CLOSED",
            "game->dialogue != N64GAME_DIALOGUE_NONE",
            "speed_q8 > (float)PLAYER_YAW_DEADZONE_Q8",
            "renderer->player_yaw = -atan2f(velocity_x_q8, velocity_z_q8)",
            "t3d_anim_set_speed(&renderer->player_walk_anim, walk_cycle_speed)",
            "t3d_anim_set_speed(&renderer->player_run_anim, run_cycle_speed)",
            "t3d_anim_update(&renderer->player_idle_anim, FIXED_DELTA_SECONDS)",
            "t3d_anim_update(&renderer->player_walk_anim, FIXED_DELTA_SECONDS)",
            "t3d_anim_update(&renderer->player_run_anim, FIXED_DELTA_SECONDS)",
            "t3d_skeleton_blend(",
            "t3d_skeleton_update(&renderer->player_skeleton)",
        ):
            self.assertIn(token, update)
        self.assertIn(
            "if (speed_q8 > (float)PLAYER_YAW_DEADZONE_Q8)", update
        )
        self.assertIn("&renderer->player_idle_pose,\n            0.0f", update)
        yaw_guard = update.index("speed_q8 > (float)PLAYER_YAW_DEADZONE_Q8")
        yaw_write = update.index("renderer->player_yaw = -atan2f")
        self.assertLess(yaw_guard, yaw_write)
        self.assertEqual(update.count("t3d_skeleton_blend("), 3)

    def test_annex_has_no_procedural_player_fallback(self) -> None:
        draw_player = self.function_body("draw_player")
        annex = self.function_body("draw_annex")
        for token in (
            "ANNEX_PLAYER_SCALE = 0.0833333f",
            "{x, ANNEX_WORLD_FLOOR_Y, z}",
            "renderer->frame_index",
            "t3d_skeleton_use(&renderer->player_skeleton)",
            "rspq_block_run(renderer->player_draw_block)",
        ):
            self.assertIn(token, self.source if token.startswith("ANNEX_PLAYER") else draw_player)
        self.assertIn("draw_player(renderer, game, player_x, player_z);", annex)
        self.assertNotRegex(annex, r"draw_actor\s*\(\s*renderer\s*,\s*0U\s*,")

    def test_finish_and_destroy_require_and_release_player_before_storage(self) -> None:
        finish = self.function_body("n64game_renderer_finish_init")
        destroy = self.function_body("n64game_renderer_destroy")
        self.assertIn("!setup_player(renderer)", finish)
        self.assertLess(finish.index("!setup_player(renderer)"), finish.index("!setup_quarrune(renderer)"))
        ordered = (
            "rspq_wait();",
            "rspq_block_free(renderer->player_draw_block)",
            "t3d_anim_destroy(&renderer->player_run_anim)",
            "t3d_skeleton_destroy(&renderer->player_run_pose)",
            "t3d_skeleton_destroy(&renderer->player_skeleton)",
            "t3d_model_free(renderer->player_model)",
            "player_render_assets_unload(&renderer->player_assets)",
        )
        positions = [destroy.index(token) for token in ordered]
        self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main()
