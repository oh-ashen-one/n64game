from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src" / "n64game_render.c"
HEADER = ROOT / "src" / "n64game_render.h"
ANNEX_SOURCE = ROOT / "src" / "n64game_annex.c"


class StaticModelRenderContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = SOURCE.read_text(encoding="utf-8")
        self.header = HEADER.read_text(encoding="utf-8")
        self.annex_source = ANNEX_SOURCE.read_text(encoding="utf-8")

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

    def test_record_and_exact_candidate_path_are_asset_neutral(self) -> None:
        for field in (
            "T3DModel *model;",
            "T3DMat4FP *matrices;",
            "rspq_block_t *draw_block;",
            "uint32_t matrix_count;",
            "uint32_t buffer_count;",
            "bool ready;",
        ):
            self.assertIn(field, self.header)
        self.assertIn("N64GameStaticModel annex_kit;", self.header)
        self.assertIn(
            '"rom:/env/env.annex.threshold_kit/annex_threshold_kit.t3dm"',
            self.source,
        )
        self.assertNotIn("annex_threshold_kit", self.header)

    def test_load_owns_buffered_matrices_model_and_recorded_draw_block(self) -> None:
        body = self.function_body("n64game_static_model_load")
        for token in (
            "matrix_count == 0U",
            "buffer_count == 0U",
            "matrix_count > SIZE_MAX / (size_t)buffer_count",
            "slot_count > SIZE_MAX / sizeof(T3DMat4FP)",
            "t3d_model_load(rom_path)",
            "malloc_uncached(",
            "rspq_block_begin();",
            "t3d_model_draw(model);",
            "rspq_block_end();",
            ".matrix_count = matrix_count",
            ".buffer_count = buffer_count",
            ".ready = true",
        ):
            self.assertIn(token, body)
        self.assertLess(body.index("t3d_model_load"), body.index("rspq_block_begin"))
        self.assertLess(body.index("rspq_block_begin"), body.index("rspq_block_end"))
        self.assertIn("free_uncached(matrices);", body)
        self.assertGreaterEqual(body.count("t3d_model_free(model);"), 2)

    def test_draw_is_frame_buffered_bounded_and_balances_matrix_stack(self) -> None:
        body = self.function_body("n64game_static_model_draw")
        for token in (
            "matrix_index >= asset->matrix_count",
            "frame_index >= asset->buffer_count",
            "matrix_index * (size_t)asset->buffer_count",
            "(size_t)frame_index",
            "t3d_mat4fp_from_srt_euler(",
            "t3d_matrix_push(",
            "rspq_block_run(asset->draw_block);",
            "t3d_matrix_pop(1);",
        ):
            self.assertIn(token, body)
        self.assertLess(body.index("t3d_matrix_push"), body.index("rspq_block_run"))
        self.assertLess(body.index("rspq_block_run"), body.index("t3d_matrix_pop"))

    def test_free_waits_then_releases_every_owned_resource_and_zeros_record(self) -> None:
        body = self.function_body("n64game_static_model_free")
        for token in (
            "rspq_wait();",
            "rspq_block_free(asset->draw_block);",
            "t3d_model_free(asset->model);",
            "free_uncached(asset->matrices);",
            "*asset = (N64GameStaticModel){0};",
        ):
            self.assertIn(token, body)
        self.assertLess(body.index("rspq_wait"), body.index("rspq_block_free"))
        self.assertLess(body.index("rspq_block_free"), body.index("t3d_model_free"))
        self.assertLess(body.index("t3d_model_free"), body.index("free_uncached"))

    def test_renderer_lifecycle_loads_and_frees_the_generic_record(self) -> None:
        finish = self.function_body("n64game_renderer_finish_init")
        destroy = self.function_body("n64game_renderer_destroy")
        self.assertIn("n64game_static_model_load(", finish)
        self.assertIn("ANNEX_KIT_MODEL_PATH", finish)
        self.assertIn("ANNEX_KIT_MATRIX_COUNT", finish)
        self.assertIn("renderer->buffer_count", finish)
        self.assertIn("n64game_static_model_free(&renderer->annex_kit);", destroy)

    def test_annex_draw_uses_only_the_active_canonical_sector(self) -> None:
        module = self.function_body("draw_annex_kit_module")
        annex = self.function_body("draw_annex")
        self.assertIn("N64GAME_ANNEX_SECTOR_COUNT", module)
        self.assertIn("n64game_annex_safe_anchor(active_sector", module)
        self.assertIn("ANNEX_KIT_YAWS[sector]", module)
        for token in (
            "ANNEX_KIT_SCALE_X",
            "ANNEX_KIT_SCALE_Y",
            "ANNEX_KIT_SCALE_Z",
        ):
            self.assertIn(token, module)
        self.assertIn("n64game_static_model_draw(", module)
        self.assertNotIn("for (", module)
        self.assertIn("draw_annex_kit_module(renderer, game->annex_sector);", annex)
        self.assertLess(
            annex.index("begin_world_render(renderer"),
            annex.index("draw_annex_kit_module(renderer"),
        )

    def test_annex_room_footprints_and_ground_plane_are_reconciled(self) -> None:
        for constant in (
            "ANNEX_KIT_SCALE_X = 0.0833333f",
            "ANNEX_KIT_SCALE_Y = 0.12f",
            "ANNEX_KIT_SCALE_Z = 0.0825f",
            "ANNEX_KIT_CENTER_OFFSET_Z = 8.25f",
            "ANNEX_WORLD_FLOOR_Y = -18.0f",
        ):
            self.assertIn(constant, self.source)
        for room in (
            "{ Q8(-44), Q8(20), Q8(-40), Q8(24), N64GAME_ANNEX_ATRIUM, true }",
            "{ Q8(-116), Q8(-52), Q8(-40), Q8(24), N64GAME_ANNEX_SIMULATION, true }",
            "{ Q8(28), Q8(92), Q8(-20), Q8(44), N64GAME_ANNEX_WORKSHOP, true }",
            "{ Q8(84), Q8(148), Q8(36), Q8(100), N64GAME_ANNEX_OVERLOOK, true }",
        ):
            self.assertIn(room, self.annex_source)
        self.assertIn("return ANNEX_WORLD_FLOOR_Y + 16.0f * scale;", self.source)
        centered = self.function_body("centered_annex_kit_translation")
        self.assertIn("ANNEX_KIT_CENTER_OFFSET_Z * scale_multiplier", centered)
        self.assertIn(
            "rotate_annex_local_offset(yaw, 0.0f, offset, &offset_x, &offset_z)",
            centered,
        )
        self.assertIn("translation[0] = anchor_x + offset_x", centered)
        self.assertIn("translation[2] = anchor_z + offset_z", centered)
        module = self.function_body("draw_annex_kit_module")
        backdrop = self.function_body("draw_battle_kit_backdrop")
        self.assertIn("centered_annex_kit_translation(", module)
        self.assertRegex(module, r"yaw,\s*1\.0f,\s*translation")
        self.assertIn("centered_annex_kit_translation(", backdrop)
        self.assertRegex(
            backdrop,
            r"yaw,\s*ANNEX_KIT_BATTLE_SCALE_MULTIPLIER,\s*translation",
        )
        self.assertNotIn("ANNEX_KIT_FLOOR_Y", self.source)

    def test_battle_draw_reuses_a_safe_slot_for_one_backdrop(self) -> None:
        backdrop = self.function_body("draw_battle_kit_backdrop")
        battle = self.function_body("draw_battle")
        self.assertIn("ANNEX_KIT_BATTLE_SCALE_MULTIPLIER", backdrop)
        self.assertIn("n64game_static_model_draw(", backdrop)
        self.assertRegex(backdrop, r"&renderer->annex_kit,\s*0U,")
        self.assertIn("draw_battle_kit_backdrop(renderer);", battle)
        self.assertLess(
            battle.index("begin_world_render(renderer"),
            battle.index("draw_battle_kit_backdrop(renderer)"),
        )

    def test_native_camera_tracks_the_active_module_without_remote_actor_clutter(self) -> None:
        rotate = self.function_body("rotate_annex_local_offset")
        annex = self.function_body("draw_annex")
        battle = self.function_body("draw_battle")
        for token in (
            "cosine * local_x - sine * local_z",
            "sine * local_x + cosine * local_z",
        ):
            self.assertIn(token, rotate)
        for token in (
            "ANNEX_KIT_YAWS[sector]",
            "rotate_annex_local_offset(yaw, 15.0f, 23.0f",
            "rotate_annex_local_offset(yaw, 0.8f, -10.0f",
            "player_x + camera_x, 0.0f, player_z + camera_z",
            "player_x + target_x, -9.0f, player_z + target_z",
            "PLAYER_SCALE = 0.24f",
            "switch (game->annex_sector)",
            "case N64GAME_ANNEX_ATRIUM:",
            "case N64GAME_ANNEX_WORKSHOP:",
            "case N64GAME_ANNEX_OVERLOOK:",
        ):
            self.assertIn(token, annex)
        self.assertIn("N64GameAnnexSector annex_camera_sector;", self.header)
        self.assertIn("uint8_t annex_camera_fade_ticks;", self.header)
        self.assertIn("bool annex_camera_ready;", self.header)
        self.assertIn("ANNEX_CAMERA_FADE_FRAMES = 8", self.source)
        self.assertIn("renderer->annex_camera_sector != game->annex_sector", annex)
        self.assertIn("renderer->annex_camera_fade_ticks = ANNEX_CAMERA_FADE_FRAMES", annex)
        self.assertIn("fade_to_black(fade_alpha);", annex)
        self.assertIn("--renderer->annex_camera_fade_ticks;", annex)
        self.assertNotIn("player_z + 88.0f", annex)
        self.assertIn("ANNEX_QUARRUNE_SCALE = 0.10f", self.source)
        self.assertIn(
            "renderer, 3U, 48.0f, ANNEX_WORLD_FLOOR_Y, 10.0f",
            annex,
        )
        self.assertIn("ANNEX_QUARRUNE_SCALE", annex)
        self.assertIn("ANNEX_QUARRUNE_SCALE", battle)


if __name__ == "__main__":
    unittest.main()
