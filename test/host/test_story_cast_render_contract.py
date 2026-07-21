from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / "src" / "story_cast_renderer.c").read_text(encoding="utf-8")
HEADER = (ROOT / "src" / "story_cast_renderer.h").read_text(encoding="utf-8")
GAME_SOURCE = (ROOT / "src" / "n64game_render.c").read_text(encoding="utf-8")
GAME_HEADER = (ROOT / "src" / "n64game_render.h").read_text(encoding="utf-8")
ROM_MAKEFILE = (ROOT / "mk" / "rom.mk").read_text(encoding="utf-8")


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
    return source[match.end() : cursor - 1]


class StoryCastRenderContractTests(unittest.TestCase):
    def test_public_surface_has_three_exact_kinds_and_required_api(self) -> None:
        for token in (
            "N64GAME_STORY_CAST_SERA = 0",
            "N64GAME_STORY_CAST_TAVI",
            "N64GAME_STORY_CAST_BEACON",
            "N64GAME_STORY_CAST_COUNT",
            "bool story_cast_renderer_init(StoryCastRenderer *renderer, uint32_t buffer_count)",
            "const N64GameCore *game",
            "void story_cast_renderer_destroy(StoryCastRenderer *renderer)",
        ):
            self.assertIn(token, HEADER)
        draw_declaration = re.search(
            r"bool story_cast_renderer_draw\s*\((.*?)\);",
            HEADER,
            re.DOTALL,
        )
        self.assertIsNotNone(draw_declaration)
        assert draw_declaration is not None
        for token in (
            "StoryCastRenderer *renderer",
            "StoryCastKind kind",
            "uint32_t frame_index",
            "float x",
            "float y",
            "float z",
            "float scale",
            "float yaw",
        ):
            self.assertIn(token, draw_declaration.group(1))

    def test_profiles_preflight_exact_models_bones_and_animation_sets(self) -> None:
        expected = (
            (
                "rom:/chr/chr.sera_venn/sera_venn_distance.t3dm",
                "SERA_BONE_COUNT = 22",
                ("idle_a", "diagnostic_scan", "explain_starter", "react_fracture"),
            ),
            (
                "rom:/chr/chr.tavi/tavi_distance.t3dm",
                "TAVI_BONE_COUNT = 20",
                ("idle_a", "greet", "listen", "reaction"),
            ),
            (
                "rom:/prop/prop.annex.beacon_decoder/annex_beacon_decoder.t3dm",
                "BEACON_BONE_COUNT = 10",
                ("idle_aim", "beacon_acquire", "fracture"),
            ),
        )
        for path, bone, animation_names in expected:
            self.assertIn(f'"{path}"', SOURCE)
            self.assertIn(bone, SOURCE)
            for animation_name in animation_names:
                self.assertIn(f'"{animation_name}"', SOURCE)
        contract = function_body(SOURCE, "model_contract_ok")
        for token in (
            "t3d_model_get_animation_count(model)",
            "skeleton->boneCount != profile->bone_count",
            "animation_definition_ok(model, profile->idle_name)",
            "animation_definition_ok(model, profile->cue_names[index])",
        ):
            self.assertIn(token, contract)

    def test_setup_is_buffered_direct_texture_and_fails_shut(self) -> None:
        setup = function_body(SOURCE, "setup_instance")
        initialize = function_body(SOURCE, "story_cast_renderer_init")
        destroy_instance = function_body(SOURCE, "destroy_instance")
        destroy = function_body(SOURCE, "story_cast_renderer_destroy")
        for token in (
            "t3d_skeleton_create_buffered(",
            "t3d_skeleton_clone(",
            "t3d_anim_set_looping(&instance->idle_anim, true)",
            "t3d_anim_set_looping(&instance->cue_anims[index], false)",
            "t3d_model_draw_custom(",
            "T3D_SEGMENT_SKELETON",
            "instance->draw_block = rspq_block_end()",
            "instance->ready = true",
        ):
            self.assertIn(token, setup)
        self.assertNotIn("dynTextureCb", setup)
        self.assertNotIn("userData", setup)
        self.assertIn("story_cast_renderer_destroy(renderer)", initialize)
        self.assertIn("SIZE_MAX / sizeof(T3DMat4FP)", initialize)
        for token in (
            "rspq_block_free(instance->draw_block)",
            "t3d_anim_destroy(&instance->cue_anims[index])",
            "t3d_skeleton_destroy(&instance->cue_poses[index])",
            "t3d_model_free(instance->model)",
        ):
            self.assertIn(token, destroy_instance)
        self.assertLess(destroy.index("rspq_wait();"), destroy.index("destroy_instance("))
        self.assertIn("free_uncached(renderer->model_matrices)", destroy)
        self.assertIn("*renderer = (StoryCastRenderer){0}", destroy)

    def test_dialogue_page_edges_have_only_the_required_cues(self) -> None:
        update = function_body(SOURCE, "story_cast_renderer_update")
        dispatch = function_body(SOURCE, "dispatch_dialogue_edge")
        self.assertIn("!renderer->observed_dialogue_valid", update)
        self.assertIn("renderer->observed_dialogue != game->dialogue", update)
        self.assertIn("renderer->observed_dialogue_page != game->dialogue_page", update)
        self.assertEqual(update.count("dispatch_dialogue_edge("), 1)
        expected_conditions = (
            ("N64GAME_DIALOGUE_SERA_INTRO", "UINT8_C(1)"),
            ("N64GAME_DIALOGUE_SERA_TRIAL", "UINT8_C(0)"),
            ("N64GAME_DIALOGUE_TAVI_INTRO", "UINT8_C(0)"),
            ("N64GAME_DIALOGUE_BEACON_HOOK", "UINT8_C(0)"),
            ("N64GAME_DIALOGUE_BEACON_HOOK", "UINT8_C(4)"),
        )
        for dialogue, page in expected_conditions:
            self.assertRegex(
                dispatch,
                rf"dialogue == {dialogue}[\s\S]*?page == {re.escape(page)}",
            )
        self.assertEqual(dispatch.count("start_cue("), 8)
        self.assertNotIn("set_playing", update)

    def test_fixed_step_blends_idle_with_nonlooping_cue_until_completion(self) -> None:
        update_instance = function_body(SOURCE, "update_instance")
        update = function_body(SOURCE, "story_cast_renderer_update")
        start_cue = function_body(SOURCE, "start_cue")
        for token in (
            "t3d_anim_update(&instance->idle_anim, delta_seconds)",
            "t3d_anim_update(cue_anim, delta_seconds)",
            "t3d_anim_is_playing(cue_anim)",
            "t3d_skeleton_blend(",
            "t3d_skeleton_update(&instance->skeleton)",
        ):
            self.assertIn(token, update_instance)
        self.assertIn("2.0f / 30.0f", update)
        self.assertIn("game->scene_ticks & UINT32_C(1)", update)
        self.assertIn("ANIMATION_DELTA_SECONDS", update)
        self.assertIn("t3d_anim_set_time(&instance->cue_anims[cue], 0.0f)", start_cue)
        self.assertIn("instance->active_cue = cue", start_cue)

    def test_game_integration_has_no_procedural_story_actor_fallback(self) -> None:
        finish = function_body(GAME_SOURCE, "n64game_renderer_finish_init")
        annex = function_body(GAME_SOURCE, "draw_annex")
        destroy = function_body(GAME_SOURCE, "n64game_renderer_destroy")
        self.assertIn("StoryCastRenderer story_cast;", GAME_HEADER)
        self.assertIn("bool story_cast_ready;", GAME_HEADER)
        self.assertIn("story_cast_renderer_init(", finish)
        self.assertIn("story_cast_renderer_destroy(&renderer->story_cast)", destroy)
        self.assertEqual(annex.count("story_cast_renderer_update("), 1)
        for kind in (
            "N64GAME_STORY_CAST_SERA",
            "N64GAME_STORY_CAST_TAVI",
            "N64GAME_STORY_CAST_BEACON",
        ):
            self.assertIn(kind, annex)
        self.assertIn("N64GAME_DIALOGUE_SERA_TRIAL", annex)
        self.assertIn("N64GAME_QUEST_BEACON_OVERLOOK", annex)
        for removed_fallback in (
            "draw_actor(",
            "ACTOR_STYLE_COUNT",
            "ACTOR_COLORS",
            "actor_vertices",
            "grounded_actor_origin",
        ):
            self.assertNotIn(removed_fallback, GAME_SOURCE)

    def test_build_converts_every_model_stream_texture_and_dfs_dependency(self) -> None:
        self.assertIn("$(BUILD_DIR)/story_cast_renderer.o", ROM_MAKEFILE)
        expected = (
            "SERA_SOURCE_DIR := runtime-candidates/chr/chr.sera_venn",
            "sera_venn_distance.0.sdata",
            "sera_venn_distance.3.sdata",
            "TAVI_SOURCE_DIR := runtime-candidates/chr/chr.tavi",
            "tavi_distance.0.sdata",
            "tavi_distance.3.sdata",
            "BEACON_SOURCE_DIR := runtime-candidates/prop/prop.annex.beacon_decoder",
            "annex_beacon_decoder.0.sdata",
            "annex_beacon_decoder.2.sdata",
            "$(SERA_RUNTIME_CANDIDATES)",
            "$(TAVI_RUNTIME_CANDIDATES)",
            "$(BEACON_RUNTIME_CANDIDATES)",
        )
        for token in expected:
            self.assertIn(token, ROM_MAKEFILE)
        self.assertGreaterEqual(
            ROM_MAKEFILE.count(
                '--base-scale=64 --asset-path=runtime-candidates'
            ),
            8,
        )
        self.assertGreaterEqual(
            ROM_MAKEFILE.count(
                "--format CI4 --tiles 64,64 --mipmap NONE --dither NONE --compress 0"
            ),
            4,
        )


if __name__ == "__main__":
    unittest.main()
