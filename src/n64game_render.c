#include "n64game_render.h"

#include <math.h>
#include <stddef.h>
#include <stdio.h>

enum {
    FONT_ID = 1,
    STYLE_TEXT = 0,
    STYLE_ACCENT = 1,
    STYLE_MUTED = 2,
    STYLE_WARNING = 3,
    STYLE_SELECTED = 4,
    ACTOR_MATRIX_COUNT = 2,
    ANNEX_KIT_MATRIX_COUNT = N64GAME_ANNEX_SECTOR_COUNT,
    ANNEX_CAMERA_FADE_FRAMES = 8,
    ANNEX_CAMERA_BOOM_DISTANCE = 18,
    ANNEX_CAMERA_LOOK_LEAD = 5,
    ANNEX_CAMERA_SAFE_HALF_EXTENT = 20,
    ANNEX_CAMERA_SWITCH_LOCAL_Z =
        ANNEX_CAMERA_SAFE_HALF_EXTENT - ANNEX_CAMERA_BOOM_DISTANCE,
    PLAYER_BONE_COUNT = 24,
    PLAYER_YAW_DEADZONE_Q8 = 4,
    PLAYER_WALK_SPEED_Q8 = 85,
    PLAYER_RUN_SPEED_Q8 = 154,
};

static const char PLAYER_MODEL_PATH[] =
    "rom:/chr/chr.player.ari/player_ari.t3dm";
static const char QUARRUNE_MODEL_PATH[] =
    "rom:/echo/echo.quarrune/quarrune_hero.t3dm";
static const char ANNEX_KIT_MODEL_PATH[] =
    "rom:/env/env.annex.threshold_kit/annex_threshold_kit.t3dm";

/*
 * The candidate's authored bounds are converted with --base-scale=64. Keep
 * these two alignment values centralized until native 320x240 captures lock
 * the final export origin and scale.
 */
static const float ANNEX_KIT_SCALE_X = 0.0833333f;
static const float ANNEX_KIT_SCALE_Y = 0.12f;
static const float ANNEX_KIT_SCALE_Z = 0.0825f;
/* Converted local Z bounds are [-488, 288], so their scaled center is -8.25. */
static const float ANNEX_KIT_CENTER_OFFSET_Z = 8.25f;
static const float ANNEX_WORLD_FLOOR_Y = -18.0f;
static const float ANNEX_KIT_BATTLE_SCALE_MULTIPLIER = 1.6f;
static const float ANNEX_PLAYER_SCALE = 0.0833333f;
static const float ANNEX_SERA_SCALE = 0.0833333f;
static const float ANNEX_TAVI_SCALE = 0.0833333f;
static const float ANNEX_BEACON_SCALE = 0.10f;
static const float ANNEX_QUARRUNE_SCALE = 0.10f;
static const float BATTLE_QUARRUNE_SCALE = 0.20f;
static const float BATTLE_SUPPORT_SCALES[N64GAME_SUPPORT_ECHO_COUNT] = {
    [N64GAME_SUPPORT_ECHO_AYSELOR] = 0.28f,
    [N64GAME_SUPPORT_ECHO_GYRECLAST] = 0.42f,
    [N64GAME_SUPPORT_ECHO_KIVARRAX] = 0.36f,
};
static const float BATTLE_SUPPORT_YAWS[N64GAME_SUPPORT_ECHO_COUNT] = {
    [N64GAME_SUPPORT_ECHO_AYSELOR] = 3.9269908f,
    [N64GAME_SUPPORT_ECHO_GYRECLAST] = 0.60f,
    [N64GAME_SUPPORT_ECHO_KIVARRAX] = 3.9269908f,
};
static const float BATTLE_SUPPORT_SHADOW_RADII[N64GAME_SUPPORT_ECHO_COUNT] = {
    [N64GAME_SUPPORT_ECHO_AYSELOR] = 15.0f,
    [N64GAME_SUPPORT_ECHO_GYRECLAST] = 18.0f,
    [N64GAME_SUPPORT_ECHO_KIVARRAX] = 16.0f,
};

static const char *const PLAYER_ANIMATION_NAMES[] = {
    "idle_a",
    "walk",
    "run",
};

static const char *const PLAYER_BONE_NAMES[PLAYER_BONE_COUNT] = {
    "b_root_c",
    "b_pelvis_c",
    "b_spine_a_c",
    "b_spine_b_c",
    "b_chest_c",
    "b_neck_c",
    "b_head_c",
    "b_ponytail_c",
    "b_clavicle_l",
    "b_upperarm_l",
    "b_forearm_l",
    "b_hand_l",
    "b_clavicle_r",
    "b_upperarm_r",
    "b_forearm_r",
    "b_hand_r",
    "b_thigh_l",
    "b_shin_l",
    "b_foot_l",
    "b_toe_l",
    "b_thigh_r",
    "b_shin_r",
    "b_foot_r",
    "b_toe_r",
};

static const float ANNEX_KIT_YAWS[N64GAME_ANNEX_SECTOR_COUNT] = {
    [N64GAME_ANNEX_ATRIUM] = 0.0f,
    [N64GAME_ANNEX_SIMULATION] = 1.5707963f,
    [N64GAME_ANNEX_WORKSHOP] = -1.5707963f,
    [N64GAME_ANNEX_OVERLOOK] = 3.1415927f,
};

static void text_at(float x, float y, uint8_t style, float width, const char *text)
{
    const rdpq_textparms_t parameters = {
        .style_id = style,
        .width = (int16_t)width,
        .height = (int16_t)(240.0f - y),
        .align = ALIGN_LEFT,
        .valign = VALIGN_TOP,
        .wrap = WRAP_WORD,
    };
    rdpq_text_print(&parameters, FONT_ID, x, y, text);
}

static void centered(float y, uint8_t style, const char *text)
{
    const rdpq_textparms_t parameters = {
        .style_id = style,
        .width = 320.0f,
        .align = ALIGN_CENTER,
        .valign = VALIGN_TOP,
    };
    rdpq_text_print(&parameters, FONT_ID, 0.0f, y, text);
}

static void fill_rect(int x0, int y0, int x1, int y1, color_t color)
{
    rdpq_set_mode_fill(color);
    rdpq_fill_rectangle(x0, y0, x1, y1);
}

static void panel(int x0, int y0, int x1, int y1)
{
    fill_rect(x0, y0, x1, y1, RGBA32(7, 18, 27, 255));
    fill_rect(x0, y0, x1, y0 + 2, RGBA32(78, 210, 190, 255));
    fill_rect(x0, y1 - 2, x1, y1, RGBA32(29, 67, 76, 255));
}

static void clear_2d(color_t color)
{
    fill_rect(0, 0, 320, 240, color);
}

static void fade_to_black(uint8_t alpha)
{
    if (alpha == 0U) {
        return;
    }
    rdpq_set_mode_standard();
    rdpq_mode_combiner(RDPQ_COMBINER_FLAT);
    rdpq_mode_blender(RDPQ_BLENDER_MULTIPLY);
    rdpq_set_prim_color(RGBA32(0, 0, 0, alpha));
    rdpq_fill_rectangle(0, 0, 320, 240);
}

static void hp_bar(int x, int y, int width, int hp, int maximum)
{
    const int safe_hp = hp < 0 ? 0 : hp;
    const int fill = maximum > 0 ? width * safe_hp / maximum : 0;
    fill_rect(x, y, x + width, y + 5, RGBA32(31, 45, 50, 255));
    const color_t color = safe_hp * 4 > maximum ?
        RGBA32(81, 211, 166, 255) : RGBA32(218, 93, 70, 255);
    fill_rect(x, y, x + fill, y + 5, color);
}

bool n64game_static_model_load(
    N64GameStaticModel *asset,
    const char *rom_path,
    uint32_t matrix_count,
    uint32_t buffer_count
)
{
    if (asset == NULL || rom_path == NULL || rom_path[0] == '\0' ||
        matrix_count == 0U || buffer_count == 0U || asset->model != NULL ||
        asset->matrices != NULL || asset->draw_block != NULL || asset->ready) {
        return false;
    }
    if ((size_t)matrix_count > SIZE_MAX / (size_t)buffer_count) {
        return false;
    }
    const size_t slot_count = (size_t)matrix_count * (size_t)buffer_count;
    if (slot_count > SIZE_MAX / sizeof(T3DMat4FP)) {
        return false;
    }

    T3DModel *const model = t3d_model_load(rom_path);
    if (model == NULL) {
        debugf("[static-model] model load failed: %s\n", rom_path);
        return false;
    }
    T3DMat4FP *const matrices = malloc_uncached(
        sizeof(T3DMat4FP) * slot_count
    );
    if (matrices == NULL) {
        debugf("[static-model] matrix allocation failed: %s\n", rom_path);
        t3d_model_free(model);
        return false;
    }

    rspq_block_begin();
    t3d_model_draw(model);
    rspq_block_t *const draw_block = rspq_block_end();
    if (draw_block == NULL) {
        debugf("[static-model] draw-block recording failed: %s\n", rom_path);
        free_uncached(matrices);
        t3d_model_free(model);
        return false;
    }

    *asset = (N64GameStaticModel){
        .model = model,
        .matrices = matrices,
        .draw_block = draw_block,
        .matrix_count = matrix_count,
        .buffer_count = buffer_count,
        .ready = true,
    };
    return true;
}

bool n64game_static_model_draw(
    N64GameStaticModel *asset,
    uint32_t matrix_index,
    uint32_t frame_index,
    const float scales[3],
    const float rotations[3],
    const float translation[3]
)
{
    if (asset == NULL || !asset->ready || asset->model == NULL ||
        asset->matrices == NULL || asset->draw_block == NULL ||
        matrix_index >= asset->matrix_count || frame_index >= asset->buffer_count ||
        scales == NULL || rotations == NULL || translation == NULL) {
        return false;
    }
    const size_t matrix_slot = (size_t)matrix_index * (size_t)asset->buffer_count +
        (size_t)frame_index;
    t3d_mat4fp_from_srt_euler(
        &asset->matrices[matrix_slot], scales, rotations, translation
    );
    t3d_matrix_push(&asset->matrices[matrix_slot]);
    rspq_block_run(asset->draw_block);
    t3d_matrix_pop(1);
    return true;
}

void n64game_static_model_free(N64GameStaticModel *asset)
{
    if (asset == NULL) {
        return;
    }
    if (asset->draw_block != NULL || asset->model != NULL ||
        asset->matrices != NULL) {
        rspq_wait();
    }
    if (asset->draw_block != NULL) {
        rspq_block_free(asset->draw_block);
    }
    if (asset->model != NULL) {
        t3d_model_free(asset->model);
    }
    if (asset->matrices != NULL) {
        free_uncached(asset->matrices);
    }
    *asset = (N64GameStaticModel){0};
}

static bool player_model_contract_ok(const T3DModel *model)
{
    if (model == NULL || t3d_model_get_skeleton(model) == NULL ||
        t3d_model_get_animation_count(model) !=
            (uint32_t)(sizeof(PLAYER_ANIMATION_NAMES) /
                       sizeof(PLAYER_ANIMATION_NAMES[0]))) {
        return false;
    }
    const T3DChunkSkeleton *const skeleton = t3d_model_get_skeleton(model);
    if (skeleton->boneCount != (uint16_t)PLAYER_BONE_COUNT) {
        return false;
    }
    for (size_t index = 0U;
         index < sizeof(PLAYER_ANIMATION_NAMES) /
             sizeof(PLAYER_ANIMATION_NAMES[0]);
         ++index) {
        const T3DChunkAnim *const animation = t3d_model_get_animation(
            model, PLAYER_ANIMATION_NAMES[index]
        );
        if (animation == NULL || animation->duration <= 0.0f ||
            animation->filePath == NULL || animation->filePath[0] == '\0') {
            return false;
        }
    }
    return true;
}

static bool player_skeleton_contract_ok(T3DSkeleton *skeleton)
{
    if (skeleton == NULL || skeleton->bones == NULL ||
        skeleton->boneMatricesFP == NULL || skeleton->skeletonRef == NULL ||
        skeleton->skeletonRef->boneCount != (uint16_t)PLAYER_BONE_COUNT) {
        return false;
    }
    for (size_t index = 0U; index < (size_t)PLAYER_BONE_COUNT; ++index) {
        if (t3d_skeleton_find_bone(skeleton, PLAYER_BONE_NAMES[index]) !=
            (int)index) {
            return false;
        }
    }
    return true;
}

static bool setup_player(N64GameRenderer *renderer)
{
    if (!player_render_assets_load(&renderer->player_assets)) {
        debugf("[player] render-asset load failed\n");
        return false;
    }
    renderer->player_model = t3d_model_load(PLAYER_MODEL_PATH);
    if (!player_model_contract_ok(renderer->player_model)) {
        debugf("[player] model contract failed: %s\n", PLAYER_MODEL_PATH);
        return false;
    }

    renderer->player_skeleton = t3d_skeleton_create_buffered(
        renderer->player_model, (int)renderer->buffer_count
    );
    if (!player_skeleton_contract_ok(&renderer->player_skeleton)) {
        debugf("[player] skeleton contract or allocation failed\n");
        return false;
    }
    renderer->player_idle_pose = t3d_skeleton_clone(
        &renderer->player_skeleton, false
    );
    renderer->player_walk_pose = t3d_skeleton_clone(
        &renderer->player_skeleton, false
    );
    renderer->player_run_pose = t3d_skeleton_clone(
        &renderer->player_skeleton, false
    );
    if (renderer->player_idle_pose.bones == NULL ||
        renderer->player_walk_pose.bones == NULL ||
        renderer->player_run_pose.bones == NULL) {
        debugf("[player] animation-pose allocation failed\n");
        return false;
    }

    renderer->player_idle_anim = t3d_anim_create(
        renderer->player_model, PLAYER_ANIMATION_NAMES[0]
    );
    renderer->player_walk_anim = t3d_anim_create(
        renderer->player_model, PLAYER_ANIMATION_NAMES[1]
    );
    renderer->player_run_anim = t3d_anim_create(
        renderer->player_model, PLAYER_ANIMATION_NAMES[2]
    );
    if (renderer->player_idle_anim.animRef == NULL ||
        renderer->player_walk_anim.animRef == NULL ||
        renderer->player_run_anim.animRef == NULL ||
        renderer->player_idle_anim.file == NULL ||
        renderer->player_walk_anim.file == NULL ||
        renderer->player_run_anim.file == NULL) {
        debugf("[player] animation-stream load failed\n");
        return false;
    }
    t3d_anim_attach(&renderer->player_idle_anim, &renderer->player_idle_pose);
    t3d_anim_attach(&renderer->player_walk_anim, &renderer->player_walk_pose);
    t3d_anim_attach(&renderer->player_run_anim, &renderer->player_run_pose);
    t3d_anim_set_time(&renderer->player_idle_anim, 0.0f);
    t3d_anim_set_time(&renderer->player_walk_anim, 0.0f);
    t3d_anim_set_time(&renderer->player_run_anim, 0.0f);
    t3d_anim_update(&renderer->player_idle_anim, 0.0f);
    t3d_anim_update(&renderer->player_walk_anim, 0.0f);
    t3d_anim_update(&renderer->player_run_anim, 0.0f);
    t3d_skeleton_blend(
        &renderer->player_skeleton,
        &renderer->player_idle_pose,
        &renderer->player_walk_pose,
        0.0f
    );
    t3d_skeleton_blend(
        &renderer->player_skeleton,
        &renderer->player_skeleton,
        &renderer->player_run_pose,
        0.0f
    );
    for (uint32_t index = 0U; index < renderer->buffer_count; ++index) {
        t3d_skeleton_update(&renderer->player_skeleton);
    }

    rspq_block_begin();
    t3d_model_draw_custom(
        renderer->player_model,
        (T3DModelDrawConf){
            .userData = &renderer->player_assets,
            .dynTextureCb = player_render_assets_dynamic_texture_cb,
            .matrices = (const T3DMat4FP *)t3d_segment_placeholder(
                T3D_SEGMENT_SKELETON
            ),
        }
    );
    renderer->player_draw_block = rspq_block_end();
    if (renderer->player_draw_block == NULL) {
        debugf("[player] draw-block recording failed\n");
        return false;
    }
    if (!player_render_assets_callback_ok(&renderer->player_assets)) {
        debugf("[player] dynamic-texture callback contract failed\n");
        return false;
    }
    renderer->player_yaw = 0.0f;
    renderer->player_ready = true;
    return true;
}

static bool setup_quarrune(N64GameRenderer *renderer)
{
    if (!quarrune_render_assets_load(&renderer->quarrune_assets)) {
        debugf("[quarrune] render-asset load failed\n");
        return false;
    }
    renderer->quarrune_model = t3d_model_load(QUARRUNE_MODEL_PATH);
    if (renderer->quarrune_model == NULL) {
        debugf("[quarrune] model load failed: %s\n", QUARRUNE_MODEL_PATH);
        return false;
    }
    if (t3d_model_get_skeleton(renderer->quarrune_model) == NULL) {
        debugf("[quarrune] model has no skeleton\n");
        return false;
    }

    renderer->quarrune_skeleton = t3d_skeleton_create_buffered(
        renderer->quarrune_model, (int)renderer->buffer_count
    );
    if (renderer->quarrune_skeleton.bones == NULL ||
        renderer->quarrune_skeleton.boneMatricesFP == NULL) {
        debugf("[quarrune] skeleton allocation failed\n");
        return false;
    }
    for (uint32_t index = 0U; index < renderer->buffer_count; ++index) {
        t3d_skeleton_update(&renderer->quarrune_skeleton);
    }

    rspq_block_begin();
    t3d_model_draw_custom(
        renderer->quarrune_model,
        (T3DModelDrawConf){
            .userData = &renderer->quarrune_assets,
            .dynTextureCb = quarrune_render_assets_dynamic_texture_cb,
            .matrices = (const T3DMat4FP *)t3d_segment_placeholder(
                T3D_SEGMENT_SKELETON
            ),
        }
    );
    renderer->quarrune_draw_block = rspq_block_end();
    if (renderer->quarrune_draw_block == NULL) {
        debugf("[quarrune] draw-block recording failed\n");
        return false;
    }
    if (!quarrune_render_assets_callback_ok(&renderer->quarrune_assets)) {
        debugf(
            "[quarrune] dynamic-texture callback failed: callbacks=%u fault=%u\n",
            (unsigned int)renderer->quarrune_assets.successful_body_callbacks,
            renderer->quarrune_assets.callback_fault ? 1U : 0U
        );
        return false;
    }
    renderer->quarrune_ready = true;
    return true;
}

bool n64game_renderer_init_bootstrap(N64GameRenderer *renderer)
{
    if (renderer == NULL) {
        return false;
    }
    *renderer = (N64GameRenderer){0};
    renderer->font = rdpq_font_load_builtin(FONT_BUILTIN_DEBUG_MONO);
    if (renderer->font == NULL) {
        return false;
    }
    rdpq_font_style(renderer->font, STYLE_TEXT, &(rdpq_fontstyle_t){
        .color = RGBA32(232, 224, 202, 255),
        .outline_color = RGBA32(4, 10, 16, 255),
    });
    rdpq_font_style(renderer->font, STYLE_ACCENT, &(rdpq_fontstyle_t){
        .color = RGBA32(87, 226, 203, 255),
        .outline_color = RGBA32(4, 10, 16, 255),
    });
    rdpq_font_style(renderer->font, STYLE_MUTED, &(rdpq_fontstyle_t){
        .color = RGBA32(139, 155, 157, 255),
        .outline_color = RGBA32(4, 10, 16, 255),
    });
    rdpq_font_style(renderer->font, STYLE_WARNING, &(rdpq_fontstyle_t){
        .color = RGBA32(221, 97, 163, 255),
        .outline_color = RGBA32(4, 10, 16, 255),
    });
    rdpq_font_style(renderer->font, STYLE_SELECTED, &(rdpq_fontstyle_t){
        .color = RGBA32(12, 24, 31, 255),
        .outline_color = RGBA32(87, 226, 203, 255),
    });
    rdpq_text_register_font(FONT_ID, renderer->font);
    renderer->font_registered = true;

    return true;
}

bool n64game_renderer_finish_init(N64GameRenderer *renderer)
{
    if (renderer == NULL || !renderer->font_registered ||
        renderer->floor_vertices != NULL || renderer->player_ready ||
        renderer->quarrune_ready || renderer->support_echoes_ready ||
        renderer->story_cast_ready) {
        return false;
    }

    renderer->floor_vertices = malloc_uncached(sizeof(T3DVertPacked) * 2U);
    renderer->buffer_count = display_get_num_buffers();
    if (renderer->buffer_count == 0U || renderer->buffer_count > UINT16_MAX) {
        n64game_renderer_destroy(renderer);
        return false;
    }
    renderer->actor_matrices = malloc_uncached(
        sizeof(T3DMat4FP) * ACTOR_MATRIX_COUNT * (size_t)renderer->buffer_count
    );
    if (renderer->floor_vertices == NULL || renderer->actor_matrices == NULL) {
        n64game_renderer_destroy(renderer);
        return false;
    }
    const uint16_t up = t3d_vert_pack_normal(&(fm_vec3_t){{0.0f, 1.0f, 0.0f}});
    renderer->floor_vertices[0] = (T3DVertPacked){
        .posA = {-130, -18, -52}, .rgbaA = UINT32_C(0x5D4937FF), .normA = up,
        .posB = {160, -18, -52}, .rgbaB = UINT32_C(0x815D3EFF), .normB = up,
    };
    renderer->floor_vertices[1] = (T3DVertPacked){
        .posA = {160, -18, 108}, .rgbaA = UINT32_C(0x294B50FF), .normA = up,
        .posB = {-130, -18, 108}, .rgbaB = UINT32_C(0x3A5551FF), .normB = up,
    };
    renderer->viewport = t3d_viewport_create_buffered((uint16_t)renderer->buffer_count);
    if (renderer->viewport._matFP == NULL ||
        !n64game_static_model_load(
            &renderer->annex_kit,
            ANNEX_KIT_MODEL_PATH,
            (uint32_t)ANNEX_KIT_MATRIX_COUNT,
            renderer->buffer_count
        ) ||
        !setup_player(renderer) ||
        !setup_quarrune(renderer) ||
        !support_echo_renderer_init(
            &renderer->support_echoes, renderer->buffer_count
        ) ||
        !story_cast_renderer_init(
            &renderer->story_cast, renderer->buffer_count
        )) {
        n64game_renderer_destroy(renderer);
        return false;
    }
    renderer->support_echoes_ready = true;
    renderer->story_cast_ready = true;
    return true;
}

bool n64game_renderer_init(N64GameRenderer *renderer)
{
    if (!n64game_renderer_init_bootstrap(renderer)) {
        return false;
    }
    return n64game_renderer_finish_init(renderer);
}

void n64game_renderer_destroy(N64GameRenderer *renderer)
{
    if (renderer == NULL) {
        return;
    }
    n64game_static_model_free(&renderer->annex_kit);
    story_cast_renderer_destroy(&renderer->story_cast);
    support_echo_renderer_destroy(&renderer->support_echoes);
    rspq_wait();
    if (renderer->player_draw_block != NULL) {
        rspq_block_free(renderer->player_draw_block);
        renderer->player_draw_block = NULL;
    }
    t3d_anim_destroy(&renderer->player_run_anim);
    t3d_anim_destroy(&renderer->player_walk_anim);
    t3d_anim_destroy(&renderer->player_idle_anim);
    t3d_skeleton_destroy(&renderer->player_run_pose);
    t3d_skeleton_destroy(&renderer->player_walk_pose);
    t3d_skeleton_destroy(&renderer->player_idle_pose);
    t3d_skeleton_destroy(&renderer->player_skeleton);
    if (renderer->player_model != NULL) {
        t3d_model_free(renderer->player_model);
        renderer->player_model = NULL;
    }
    (void)player_render_assets_unload(&renderer->player_assets);
    if (renderer->quarrune_draw_block != NULL) {
        rspq_block_free(renderer->quarrune_draw_block);
        renderer->quarrune_draw_block = NULL;
    }
    t3d_skeleton_destroy(&renderer->quarrune_skeleton);
    if (renderer->quarrune_model != NULL) {
        t3d_model_free(renderer->quarrune_model);
    }
    if (renderer->quarrune_assets.lifetime != NULL) {
        (void)quarrune_render_assets_unload(&renderer->quarrune_assets);
    }
    t3d_viewport_destroy(&renderer->viewport);
    if (renderer->actor_matrices != NULL) {
        free_uncached(renderer->actor_matrices);
    }
    if (renderer->floor_vertices != NULL) {
        free_uncached(renderer->floor_vertices);
    }
    if (renderer->font_registered) {
        rdpq_text_unregister_font(FONT_ID);
    }
    if (renderer->font != NULL) {
        rdpq_font_free(renderer->font);
    }
    *renderer = (N64GameRenderer){0};
}

static void draw_floor(const N64GameRenderer *renderer)
{
    t3d_vert_load(renderer->floor_vertices, 0, 4);
    t3d_tri_draw(0, 1, 2);
    t3d_tri_draw(0, 2, 3);
    t3d_tri_sync();
}

static float clamp_unit(float value)
{
    if (value < 0.0f) {
        return 0.0f;
    }
    if (value > 1.0f) {
        return 1.0f;
    }
    return value;
}

static void update_player_pose(
    N64GameRenderer *renderer,
    const N64GameCore *game
)
{
    static const float FIXED_DELTA_SECONDS = 1.0f / 30.0f;
    const bool locomotion_frozen = game->paused ||
        game->menu != N64GAME_MENU_CLOSED ||
        game->dialogue != N64GAME_DIALOGUE_NONE;
    const float velocity_x_q8 = locomotion_frozen ?
        0.0f : (float)game->player_velocity_x_q8;
    const float velocity_z_q8 = locomotion_frozen ?
        0.0f : (float)game->player_velocity_z_q8;
    const float speed_q8 = sqrtf(
        velocity_x_q8 * velocity_x_q8 + velocity_z_q8 * velocity_z_q8
    );

    if (speed_q8 > (float)PLAYER_YAW_DEADZONE_Q8) {
        /*
         * Ari faces Blender -Y, which exports as Tiny3D local +Z. Tiny3D's
         * +Y Euler convention therefore needs the negative X/Z heading.
         */
        renderer->player_yaw = -atan2f(velocity_x_q8, velocity_z_q8);
    }

    const float walk_blend = clamp_unit(
        speed_q8 / (float)PLAYER_WALK_SPEED_Q8
    );
    const float run_blend = clamp_unit(
        (speed_q8 - (float)PLAYER_WALK_SPEED_Q8) /
        (float)(PLAYER_RUN_SPEED_Q8 - PLAYER_WALK_SPEED_Q8)
    );
    const float walk_cycle_speed = locomotion_frozen ?
        0.0f : speed_q8 / (float)PLAYER_WALK_SPEED_Q8;
    const float run_cycle_speed = locomotion_frozen ?
        0.0f : speed_q8 / (float)PLAYER_RUN_SPEED_Q8;

    t3d_anim_set_speed(&renderer->player_idle_anim, 1.0f);
    t3d_anim_update(&renderer->player_idle_anim, FIXED_DELTA_SECONDS);
    if (speed_q8 > (float)PLAYER_YAW_DEADZONE_Q8) {
        t3d_anim_set_speed(&renderer->player_walk_anim, walk_cycle_speed);
        t3d_anim_set_speed(&renderer->player_run_anim, run_cycle_speed);
        t3d_anim_update(&renderer->player_walk_anim, FIXED_DELTA_SECONDS);
        t3d_anim_update(&renderer->player_run_anim, FIXED_DELTA_SECONDS);
        t3d_skeleton_blend(
            &renderer->player_skeleton,
            &renderer->player_idle_pose,
            &renderer->player_walk_pose,
            walk_blend
        );
        t3d_skeleton_blend(
            &renderer->player_skeleton,
            &renderer->player_skeleton,
            &renderer->player_run_pose,
            run_blend
        );
    } else {
        t3d_skeleton_blend(
            &renderer->player_skeleton,
            &renderer->player_idle_pose,
            &renderer->player_idle_pose,
            0.0f
        );
    }
    t3d_skeleton_update(&renderer->player_skeleton);
}

static void draw_player(
    N64GameRenderer *renderer,
    const N64GameCore *game,
    float x,
    float z
)
{
    assertf(renderer->player_ready, "Ari player renderer is not ready");
    update_player_pose(renderer, game);
    const float scales[3] = {
        ANNEX_PLAYER_SCALE,
        ANNEX_PLAYER_SCALE,
        ANNEX_PLAYER_SCALE,
    };
    const float rotations[3] = {0.0f, renderer->player_yaw, 0.0f};
    const float translation[3] = {x, ANNEX_WORLD_FLOOR_Y, z};
    const size_t matrix_slot = (size_t)renderer->frame_index;
    t3d_mat4fp_from_srt_euler(
        &renderer->actor_matrices[matrix_slot], scales, rotations, translation
    );
    t3d_skeleton_use(&renderer->player_skeleton);
    t3d_matrix_push(&renderer->actor_matrices[matrix_slot]);
    rspq_block_run(renderer->player_draw_block);
    t3d_matrix_pop(1);
}

static void draw_quarrune(
    N64GameRenderer *renderer,
    size_t matrix_index,
    float x,
    float y,
    float z,
    float scale,
    float angle
)
{
    assertf(renderer->quarrune_ready, "Quarrune renderer is not ready");
    const float scales[3] = {scale, scale, scale};
    const float rotations[3] = {0.0f, angle, 0.0f};
    const float translation[3] = {x, y, z};
    const size_t matrix_slot = matrix_index * (size_t)renderer->buffer_count +
        (size_t)renderer->frame_index;
    t3d_mat4fp_from_srt_euler(
        &renderer->actor_matrices[matrix_slot], scales, rotations, translation
    );
    t3d_skeleton_use(&renderer->quarrune_skeleton);
    t3d_matrix_push(&renderer->actor_matrices[matrix_slot]);
    rspq_block_run(renderer->quarrune_draw_block);
    t3d_matrix_pop(1);
}

static void rotate_annex_local_offset(
    float yaw,
    float local_x,
    float local_z,
    float *world_x,
    float *world_z
)
{
    const float sine = fm_sinf(yaw);
    const float cosine = fm_cosf(yaw);
    *world_x = cosine * local_x - sine * local_z;
    *world_z = sine * local_x + cosine * local_z;
}

static void centered_annex_kit_translation(
    float anchor_x,
    float anchor_z,
    float yaw,
    float scale_multiplier,
    float translation[3]
)
{
    const float offset = ANNEX_KIT_CENTER_OFFSET_Z * scale_multiplier;
    float offset_x = 0.0f;
    float offset_z = 0.0f;
    rotate_annex_local_offset(yaw, 0.0f, offset, &offset_x, &offset_z);
    translation[0] = anchor_x + offset_x;
    translation[1] = ANNEX_WORLD_FLOOR_Y;
    translation[2] = anchor_z + offset_z;
}

static void draw_annex_kit_module(
    N64GameRenderer *renderer,
    N64GameAnnexSector active_sector
)
{
    const uint32_t sector = (uint32_t)active_sector;
    assertf(
        sector < (uint32_t)N64GAME_ANNEX_SECTOR_COUNT,
        "Annex kit sector is invalid: %lu",
        (unsigned long)sector
    );
    const float scales[3] = {
        ANNEX_KIT_SCALE_X, ANNEX_KIT_SCALE_Y, ANNEX_KIT_SCALE_Z,
    };
    int32_t anchor_x_q8 = 0;
    int32_t anchor_z_q8 = 0;
    n64game_annex_safe_anchor(active_sector, &anchor_x_q8, &anchor_z_q8);
    const float yaw = ANNEX_KIT_YAWS[sector];
    const float rotations[3] = {0.0f, yaw, 0.0f};
    float translation[3];
    centered_annex_kit_translation(
        (float)anchor_x_q8 / 256.0f,
        (float)anchor_z_q8 / 256.0f,
        yaw,
        1.0f,
        translation
    );
    assertf(
        n64game_static_model_draw(
            &renderer->annex_kit,
            sector,
            renderer->frame_index,
            scales,
            rotations,
            translation
        ),
        "Annex kit module draw failed for sector %lu",
        (unsigned long)sector
    );
}

static void draw_battle_kit_backdrop(N64GameRenderer *renderer)
{
    const float scales[3] = {
        ANNEX_KIT_SCALE_X * ANNEX_KIT_BATTLE_SCALE_MULTIPLIER,
        ANNEX_KIT_SCALE_Y * ANNEX_KIT_BATTLE_SCALE_MULTIPLIER,
        ANNEX_KIT_SCALE_Z * ANNEX_KIT_BATTLE_SCALE_MULTIPLIER,
    };
    const float yaw = 3.1415927f;
    const float rotations[3] = {0.0f, yaw, 0.0f};
    float translation[3];
    centered_annex_kit_translation(
        0.0f,
        -105.0f,
        yaw,
        ANNEX_KIT_BATTLE_SCALE_MULTIPLIER,
        translation
    );
    assertf(
        n64game_static_model_draw(
            &renderer->annex_kit,
            0U,
            renderer->frame_index,
            scales,
            rotations,
            translation
        ),
        "Battle Annex kit backdrop draw failed"
    );
}

static void begin_world_render(
    N64GameRenderer *renderer,
    const fm_vec3_t *camera,
    const fm_vec3_t *target
)
{
    const fm_vec3_t up = {{0.0f, 1.0f, 0.0f}};
    const uint8_t ambient[4] = {54, 48, 57, 255};
    const uint8_t sun[4] = {255, 224, 177, 255};
    const fm_vec3_t direction = {{-0.45f, 0.72f, 0.6f}};
    renderer->frame_index = (renderer->frame_index + 1U) % renderer->buffer_count;
    t3d_frame_start();
    t3d_viewport_set_projection(&renderer->viewport, T3D_DEG_TO_RAD(68.0f), 8.0f, 300.0f);
    t3d_viewport_look_at(&renderer->viewport, camera, target, &up);
    t3d_viewport_attach(&renderer->viewport);
    t3d_screen_clear_color(RGBA32(19, 31, 42, 255));
    t3d_screen_clear_depth();
    rdpq_mode_combiner(RDPQ_COMBINER_SHADE);
    t3d_light_set_ambient(ambient);
    t3d_light_set_directional(0, sun, &direction);
    t3d_light_set_count(1);
    t3d_state_set_drawflags(T3D_FLAG_SHADED | T3D_FLAG_DEPTH);
    draw_floor(renderer);
}

static const char *objective_text(N64GameQuest quest)
{
    switch (quest) {
    case N64GAME_QUEST_MEET_SERA: return "MEET DR. SERA VENN";
    case N64GAME_QUEST_MEET_TAVI: return "CHECK IN WITH TAVI";
    case N64GAME_QUEST_RETRIEVE_RELAY: return "RETRIEVE THE FIELD RELAY";
    case N64GAME_QUEST_CALIBRATE_RELAY: return "CALIBRATE AT THE SIMULATION RING";
    case N64GAME_QUEST_READY_FOR_TRIAL: return "BEGIN THE TRIAL AT THE SIMULATION RING";
    case N64GAME_QUEST_RESONANCE_TRIAL: return "COMPLETE THE RESONANCE TRIAL";
    case N64GAME_QUEST_BEACON_OVERLOOK: return "TRACE THE SIGNAL AT THE OVERLOOK";
    case N64GAME_QUEST_COMPLETE: return "OPENING CHAPTER COMPLETE";
    }
    return "";
}

static const char *dialogue_speaker(const N64GameCore *game)
{
    switch (game->dialogue) {
    case N64GAME_DIALOGUE_SERA_INTRO:
    case N64GAME_DIALOGUE_SERA_TRIAL:
    case N64GAME_DIALOGUE_BATTLE_VICTORY:
        return "DR. SERA VENN";
    case N64GAME_DIALOGUE_BEACON_HOOK:
        switch (game->dialogue_page) {
        case 0U:
        case 5U:
            return "DR. SERA VENN";
        case 1U:
            return "TAVI";
        case 2U:
            return "QUARRUNE";
        case 3U:
            return "AYSELOR";
        case 4U:
            return "FIELD RELAY";
        default:
            return "SOLACE BEACON";
        }
    case N64GAME_DIALOGUE_TAVI_INTRO:
    case N64GAME_DIALOGUE_TAVI_REPEAT:
        return "TAVI";
    case N64GAME_DIALOGUE_RELAY:
        return "FIELD RELAY";
    case N64GAME_DIALOGUE_EXAMINE_SIM_RING:
        return "SIMULATION RING";
    case N64GAME_DIALOGUE_EXAMINE_ATRIUM_MAP:
        return "ANNEX CARTOGRAPHY";
    case N64GAME_DIALOGUE_EXAMINE_WORKSHOP_LOG:
        return "WORKSHOP LOG 17";
    case N64GAME_DIALOGUE_EXAMINE_OVERLOOK_SCOPE:
        return "OVERLOOK SCOPE";
    case N64GAME_DIALOGUE_NONE:
        return "";
    }
    return "";
}

static const char *dialogue_text(const N64GameCore *game)
{
    static char dynamic_line[96];
    static const char *const SERA_INTRO[] = {
        "",
        "Quarrune is your Strata anchor. Ayselor is your Gale carrier.",
        "Tavi is waiting by the atrium observation rail. Check in with him.",
        "Then collect your Field Relay from the east workshop bench.",
    };
    static const char *const TAVI_INTRO[] = {
        "The west antenna keeps pointing at empty sky. Sera says it is impossible.",
        "Your Field Relay is on the east bench. Bring it to the Simulation Ring.",
    };
    static const char *const TAVI_REPEAT[] = {
        "Relay first, then the Simulation Ring. I will keep watching the west antenna.",
    };
    static const char *const RELAY[] = {
        "MERIDIAN FIELD RELAY ACQUIRED / LINK LOCKED",
        "CALIBRATION REQUIRED AT THE SIMULATION RING.",
    };
    static const char *const SERA_TRIAL[] = {
        "Calibration holds. The Relay needs one live pattern before it can hear the desert.",
        "Take Quarrune and Ayselor into the ring. Let the true pattern answer.",
    };
    static const char *const VICTORY[] = {
        "There. Quarrune anchors; Ayselor carries. The Relay understands you now.",
        "A signal just crossed the old Solace band. Meet me at the overlook.",
    };
    static const char *const BEACON[] = {
        "That signature belongs to Solace.",
        "A beacon cannot walk. This one has crossed twelve kilometers since dusk.",
        "Quarrune plants both foreclaws. A warning rolls through the overlook floor.",
        "Ayselor's wings snap wide toward the storm, answering a voice no one else can hear.",
        "FRACTURE PULSE / SOURCE BELOW SOLACE / RANGE UNRESOLVED",
        "Something enormous is answering from beneath the storm. We follow at first light.",
    };
    static const char SIM_RING[] =
        "Brass grooves record thirty years of paired Echoform trials. One ring is newly scorched.";
    static const char ATRIUM_MAP[] =
        "Old routes converge on Solace Pass. Every marker beyond it has gone dark.";
    static const char WORKSHOP_LOG[] =
        "The Relay heard a second pulse below the storm, then erased its own timestamp.";
    static const char OVERLOOK_SCOPE[] =
        "The sight is fixed on Solace Pass. Its brass housing is warm, though no one signed it out.";
    const uint8_t page = game->dialogue_page;
    switch (game->dialogue) {
    case N64GAME_DIALOGUE_SERA_INTRO:
        if (page == 0U) {
            (void)snprintf(
                dynamic_line, sizeof(dynamic_line),
                "%s, welcome to Meridian Research Annex.", game->player_name
            );
            return dynamic_line;
        }
        return SERA_INTRO[page];
    case N64GAME_DIALOGUE_TAVI_INTRO: return TAVI_INTRO[page];
    case N64GAME_DIALOGUE_TAVI_REPEAT: return TAVI_REPEAT[page];
    case N64GAME_DIALOGUE_RELAY: return RELAY[page];
    case N64GAME_DIALOGUE_SERA_TRIAL: return SERA_TRIAL[page];
    case N64GAME_DIALOGUE_BATTLE_VICTORY: return VICTORY[page];
    case N64GAME_DIALOGUE_BEACON_HOOK: return BEACON[page];
    case N64GAME_DIALOGUE_EXAMINE_SIM_RING: return SIM_RING;
    case N64GAME_DIALOGUE_EXAMINE_ATRIUM_MAP: return ATRIUM_MAP;
    case N64GAME_DIALOGUE_EXAMINE_WORKSHOP_LOG: return WORKSHOP_LOG;
    case N64GAME_DIALOGUE_EXAMINE_OVERLOOK_SCOPE: return OVERLOOK_SCOPE;
    case N64GAME_DIALOGUE_NONE: return "";
    }
    return "";
}

static void draw_dialogue(const N64GameCore *game)
{
    panel(8, 172, 312, 234);
    text_at(18.0f, 179.0f, STYLE_ACCENT, 280.0f, dialogue_speaker(game));
    text_at(18.0f, 193.0f, STYLE_TEXT, 276.0f, dialogue_text(game));
    text_at(286.0f, 219.0f, STYLE_MUTED, 20.0f, "A");
}

static const char *annex_sector_name(N64GameAnnexSector sector)
{
    switch (sector) {
    case N64GAME_ANNEX_ATRIUM: return "ATRIUM";
    case N64GAME_ANNEX_SIMULATION: return "SIMULATION CHAMBER";
    case N64GAME_ANNEX_WORKSHOP: return "RELAY WORKSHOP";
    case N64GAME_ANNEX_OVERLOOK: return "STORM OVERLOOK";
    case N64GAME_ANNEX_SECTOR_COUNT: return "MERIDIAN ANNEX";
    }
    return "MERIDIAN ANNEX";
}

static void draw_menu_item(float y, const char *label, bool selected)
{
    text_at(82.0f, y, selected ? STYLE_WARNING : STYLE_TEXT, 170.0f, label);
}

static void draw_pause_root(const N64GameCore *game)
{
    static const char *const ITEMS[] = { "PARTY", "HELP", "SAVE", "RESUME" };
    panel(62, 38, 258, 215);
    centered(48.0f, STYLE_ACCENT, "PAUSED");
    text_at(77.0f, 67.0f, STYLE_MUTED, 170.0f, annex_sector_name(game->annex_sector));
    for (uint8_t item = 0U; item < 4U; ++item) {
        const char *label = ITEMS[item];
        if (item == 0U && !game->relay_unlocked) {
            label = "PARTY  LOCKED";
        } else if (item == 2U && !game->relay_unlocked) {
            label = "SAVE  LOCKED";
        }
        draw_menu_item(91.0f + (float)item * 22.0f, label, game->menu_cursor == item);
    }
    text_at(77.0f, 192.0f, STYLE_MUTED, 170.0f, "A SELECT / B BACK");
}

static void draw_relay_root(const N64GameCore *game)
{
    static const char *const ITEMS[] = {
        "PARTY", "MESSAGES", "RESONANCE", "SAVE", "CLOSE"
    };
    panel(62, 26, 258, 220);
    centered(36.0f, STYLE_ACCENT, "FIELD RELAY");
    text_at(77.0f, 55.0f, STYLE_MUTED, 170.0f, "LINK STABLE / CHANNELS");
    for (uint8_t item = 0U; item < 5U; ++item) {
        draw_menu_item(78.0f + (float)item * 22.0f, ITEMS[item], game->menu_cursor == item);
    }
    text_at(77.0f, 198.0f, STYLE_MUTED, 170.0f, "A SELECT / B BACK");
}

static void draw_party_page(const N64GameCore *game)
{
    char status[48];
    panel(28, 26, 292, 220);
    centered(36.0f, STYLE_ACCENT, "PARTY / LINKED PAIR");

    text_at(42.0f, 64.0f, STYLE_TEXT, 236.0f, "QUARRUNE / STRATA ANCHOR");
    (void)snprintf(
        status, sizeof(status), "HP %d / %d",
        (int)game->party_hp[0], N64GAME_QUARRUNE_MAX_HP
    );
    text_at(42.0f, 81.0f, STYLE_MUTED, 90.0f, status);
    hp_bar(138, 85, 136, game->party_hp[0], N64GAME_QUARRUNE_MAX_HP);

    text_at(42.0f, 116.0f, STYLE_TEXT, 236.0f, "AYSELOR / GALE CARRIER");
    (void)snprintf(
        status, sizeof(status), "HP %d / %d",
        (int)game->party_hp[1], N64GAME_AYSELOR_MAX_HP
    );
    text_at(42.0f, 133.0f, STYLE_MUTED, 90.0f, status);
    hp_bar(138, 137, 136, game->party_hp[1], N64GAME_AYSELOR_MAX_HP);

    text_at(42.0f, 169.0f, STYLE_ACCENT, 236.0f, "IDENTITY: MERIDIAN RESONANT PAIR");
    text_at(42.0f, 198.0f, STYLE_MUTED, 236.0f, "A OR B  BACK");
}

static const char *relay_message(N64GameQuest quest)
{
    switch (quest) {
    case N64GAME_QUEST_MEET_SERA:
        return "SERA: Report to the west simulation chamber.";
    case N64GAME_QUEST_MEET_TAVI:
        return "SERA: Tavi is waiting at the atrium observation rail.";
    case N64GAME_QUEST_RETRIEVE_RELAY:
        return "SERA: Retrieve the Relay from the east workshop bench.";
    case N64GAME_QUEST_CALIBRATE_RELAY:
        return "RELAY: Link locked. Calibrate at the Simulation Ring.";
    case N64GAME_QUEST_READY_FOR_TRIAL:
        return "SERA: Checkpoint stable. Begin the trial at the Simulation Ring.";
    case N64GAME_QUEST_RESONANCE_TRIAL:
        return "SERA: Hold the pair together. Let the true pattern answer.";
    case N64GAME_QUEST_BEACON_OVERLOOK:
        return "URGENT: Solace-band signal detected at the north overlook.";
    case N64GAME_QUEST_COMPLETE:
        return "SERA: Solace is moving. We depart at first light.";
    }
    return "NO NEW MESSAGES.";
}

static void draw_messages_page(const N64GameCore *game)
{
    panel(28, 34, 292, 214);
    centered(44.0f, STYLE_ACCENT, "MESSAGES / PRIORITY");
    text_at(44.0f, 78.0f, STYLE_TEXT, 232.0f, relay_message(game->quest));
    text_at(44.0f, 160.0f, STYLE_MUTED, 232.0f, "ENCRYPTION: MERIDIAN / LOCAL");
    text_at(44.0f, 192.0f, STYLE_MUTED, 232.0f, "A OR B  BACK");
}

static void draw_resonance_page(const N64GameCore *game)
{
    char status[40];
    const int resonance = (int)game->battle.resonance;
    panel(28, 30, 292, 218);
    centered(40.0f, STYLE_ACCENT, "RESONANCE");
    (void)snprintf(status, sizeof(status), "PAIR METER  %d / %d",
                   resonance, N64GAME_RESONANCE_MAX);
    text_at(44.0f, 71.0f, STYLE_TEXT, 232.0f, status);
    hp_bar(44, 91, 232, resonance, N64GAME_RESONANCE_MAX);
    text_at(
        44.0f, 115.0f, STYLE_TEXT, 232.0f,
        "Build 100 through linked actions. At 100, Quarrune can use HORIZON BREAK while Ayselor stands."
    );
    text_at(44.0f, 196.0f, STYLE_MUTED, 232.0f, "A OR B  BACK");
}

static void draw_save_page(void)
{
    panel(38, 48, 282, 204);
    centered(58.0f, STYLE_ACCENT, "SAVE RESONANCE FILE");
    text_at(
        54.0f, 91.0f, STYLE_TEXT, 212.0f,
        "Record your safe Annex checkpoint, objectives, and Field Relay discoveries."
    );
    text_at(54.0f, 156.0f, STYLE_WARNING, 212.0f, "A  SAVE");
    text_at(54.0f, 178.0f, STYLE_MUTED, 212.0f, "B  BACK");
}

static void draw_help_page(void)
{
    panel(28, 24, 292, 222);
    centered(34.0f, STYLE_ACCENT, "CONTROLS");
    text_at(
        44.0f, 63.0f, STYLE_TEXT, 232.0f,
        "CONTROL STICK   MOVE\nHOLD B          RUN\nA               INTERACT\nSTART           PAUSE\nC-DOWN          FIELD RELAY"
    );
    text_at(44.0f, 199.0f, STYLE_MUTED, 232.0f, "A OR B  BACK");
}

static void draw_calibration(const N64GameCore *game)
{
    static const char *const BANDS[] = { "LOW", "MID", "HIGH" };
    char heading[48];
    char target[48];
    const uint8_t step = game->calibration_step < N64GAME_CALIBRATION_STEP_COUNT ?
        game->calibration_step : (uint8_t)(N64GAME_CALIBRATION_STEP_COUNT - 1U);
    const uint8_t target_band = n64game_core_calibration_target(step);
    panel(34, 30, 286, 216);
    centered(40.0f, STYLE_ACCENT, "FIELD RELAY CALIBRATION");
    (void)snprintf(
        heading, sizeof(heading), "STEP %u / %u",
        (unsigned)step + 1U, (unsigned)N64GAME_CALIBRATION_STEP_COUNT
    );
    centered(67.0f, STYLE_TEXT, heading);
    (void)snprintf(target, sizeof(target), "MATCH REQUESTED BAND: %s", BANDS[target_band]);
    centered(88.0f, STYLE_WARNING, target);
    for (uint8_t band = 0U; band < 3U; ++band) {
        const int left = 49 + (int)band * 78;
        panel(left, 116, left + 66, 151);
        text_at(
            (float)(left + 13), 128.0f,
            game->calibration_cursor == band ? STYLE_WARNING : STYLE_TEXT,
            48.0f, BANDS[band]
        );
    }
    centered(
        169.0f,
        game->calibration_error ? STYLE_WARNING : STYLE_MUTED,
        game->calibration_error ? "PHASE MISMATCH / SELECT AGAIN" : "D-PAD SELECT / A LOCK BAND"
    );
    centered(193.0f, STYLE_MUTED, "B CANCELS WITHOUT UNLOCKING");
}

static void draw_post_chapter_root(const N64GameCore *game)
{
    const uint8_t log_style = game->menu_cursor == 0U ? STYLE_WARNING : STYLE_TEXT;
    const uint8_t party_style = game->menu_cursor == 1U ? STYLE_WARNING : STYLE_TEXT;
    const uint8_t resonance_style = game->menu_cursor == 2U ? STYLE_WARNING : STYLE_TEXT;
    panel(20, 178, 300, 232);
    centered(184.0f, STYLE_ACCENT, "POST-CHAPTER ARCHIVE");
    text_at(30.0f, 207.0f, log_style, 78.0f, "SIGNAL LOG");
    text_at(125.0f, 207.0f, party_style, 52.0f, "PARTY");
    text_at(202.0f, 207.0f, resonance_style, 88.0f, "RESONANCE");
}

static void draw_annex_menu(const N64GameCore *game)
{
    switch (game->menu) {
    case N64GAME_MENU_CLOSED:
        break;
    case N64GAME_MENU_PAUSE_ROOT:
        draw_pause_root(game);
        break;
    case N64GAME_MENU_FIELD_RELAY_ROOT:
        draw_relay_root(game);
        break;
    case N64GAME_MENU_PARTY:
        draw_party_page(game);
        break;
    case N64GAME_MENU_MESSAGES:
        draw_messages_page(game);
        break;
    case N64GAME_MENU_RESONANCE:
        draw_resonance_page(game);
        break;
    case N64GAME_MENU_SAVE:
        draw_save_page();
        break;
    case N64GAME_MENU_HELP:
        draw_help_page();
        break;
    case N64GAME_MENU_RELAY_CALIBRATION:
        draw_calibration(game);
        break;
    case N64GAME_MENU_POST_CHAPTER_ROOT:
        draw_post_chapter_root(game);
        break;
    }
}

static void annex_camera_player_local_position(
    N64GameAnnexSector sector,
    float yaw,
    float player_x,
    float player_z,
    float *player_local_x,
    float *player_local_z
)
{
    int32_t anchor_x_q8 = 0;
    int32_t anchor_z_q8 = 0;
    n64game_annex_safe_anchor(sector, &anchor_x_q8, &anchor_z_q8);
    const float delta_x = player_x - (float)anchor_x_q8 / 256.0f;
    const float delta_z = player_z - (float)anchor_z_q8 / 256.0f;
    const float sine = fm_sinf(yaw);
    const float cosine = fm_cosf(yaw);
    *player_local_x = cosine * delta_x + sine * delta_z;
    *player_local_z = -sine * delta_x + cosine * delta_z;
}

static float clamp_annex_camera_local(float value)
{
    if (value < -(float)ANNEX_CAMERA_SAFE_HALF_EXTENT) {
        return -(float)ANNEX_CAMERA_SAFE_HALF_EXTENT;
    }
    if (value > (float)ANNEX_CAMERA_SAFE_HALF_EXTENT) {
        return (float)ANNEX_CAMERA_SAFE_HALF_EXTENT;
    }
    return value;
}

static void update_annex_camera_rail(
    N64GameRenderer *renderer,
    N64GameAnnexSector sector,
    float player_local_z
)
{
    const bool sector_changed = renderer->annex_camera_ready &&
        renderer->annex_camera_sector != sector;
    if (!renderer->annex_camera_ready || sector_changed) {
        renderer->annex_camera_sector = sector;
        renderer->annex_camera_boom_side = player_local_z > 0.0f ? -1 : 1;
        renderer->annex_camera_ready = true;
        if (sector_changed) {
            renderer->annex_camera_fade_ticks = ANNEX_CAMERA_FADE_FRAMES;
        }
        return;
    }

    int8_t next_side = renderer->annex_camera_boom_side;
    if (next_side > 0 &&
        player_local_z > (float)ANNEX_CAMERA_SWITCH_LOCAL_Z) {
        next_side = -1;
    } else if (next_side < 0 &&
               player_local_z < -(float)ANNEX_CAMERA_SWITCH_LOCAL_Z) {
        next_side = 1;
    }
    if (next_side != renderer->annex_camera_boom_side) {
        renderer->annex_camera_boom_side = next_side;
        renderer->annex_camera_fade_ticks = ANNEX_CAMERA_FADE_FRAMES;
    }
}

static void draw_annex(N64GameRenderer *renderer, const N64GameCore *game)
{
    const float player_x = (float)game->player_x_q8 / 256.0f;
    const float player_z = (float)game->player_z_q8 / 256.0f;
    const uint32_t sector = (uint32_t)game->annex_sector;
    assertf(
        sector < (uint32_t)N64GAME_ANNEX_SECTOR_COUNT,
        "Annex camera sector is invalid: %lu",
        (unsigned long)sector
    );
    assertf(
        renderer->story_cast_ready &&
            story_cast_renderer_update(&renderer->story_cast, game),
        "Story-cast renderer update failed"
    );
    const float yaw = ANNEX_KIT_YAWS[sector];
    float player_local_x = 0.0f;
    float player_local_z = 0.0f;
    annex_camera_player_local_position(
        game->annex_sector,
        yaw,
        player_x,
        player_z,
        &player_local_x,
        &player_local_z
    );
    update_annex_camera_rail(renderer, game->annex_sector, player_local_z);
    assertf(
        renderer->annex_camera_boom_side == -1 ||
            renderer->annex_camera_boom_side == 1,
        "Annex camera rail side is invalid: %d",
        (int)renderer->annex_camera_boom_side
    );
    const float camera_boom_z = (float)(
        renderer->annex_camera_boom_side * ANNEX_CAMERA_BOOM_DISTANCE
    );
    const float target_lead_z = (float)(
        -renderer->annex_camera_boom_side * ANNEX_CAMERA_LOOK_LEAD
    );
    const float camera_local_x = clamp_annex_camera_local(player_local_x);
    const float camera_local_z = clamp_annex_camera_local(
        player_local_z + camera_boom_z
    );
    const float camera_offset_local_x = camera_local_x - player_local_x;
    const float camera_offset_local_z = camera_local_z - player_local_z;
    float camera_x = 0.0f;
    float camera_z = 0.0f;
    float target_x = 0.0f;
    float target_z = 0.0f;
    rotate_annex_local_offset(
        yaw,
        camera_offset_local_x,
        camera_offset_local_z,
        &camera_x,
        &camera_z
    );
    rotate_annex_local_offset(yaw, 0.0f, target_lead_z, &target_x, &target_z);
    const fm_vec3_t camera = {{player_x + camera_x, -4.0f, player_z + camera_z}};
    const fm_vec3_t target = {{player_x + target_x, -12.0f, player_z + target_z}};
    begin_world_render(renderer, &camera, &target);
    draw_annex_kit_module(renderer, game->annex_sector);
    const float angle = (float)game->scene_ticks * 0.018f;
    draw_player(renderer, game, player_x, player_z);
    switch (game->annex_sector) {
    case N64GAME_ANNEX_ATRIUM:
        /*
         * Keep authored NPCs inside their ten-unit interaction halos but off
         * the halo centers, so the player cannot cover the speaker at the
         * normal prompt position.
         */
        assertf(
            story_cast_renderer_draw(
                &renderer->story_cast,
                N64GAME_STORY_CAST_SERA,
                renderer->frame_index,
                -36.0f,
                ANNEX_WORLD_FLOOR_Y,
                4.0f,
                ANNEX_SERA_SCALE,
                0.3f
            ),
            "Sera draw failed"
        );
        assertf(
            story_cast_renderer_draw(
                &renderer->story_cast,
                N64GAME_STORY_CAST_TAVI,
                renderer->frame_index,
                8.0f,
                ANNEX_WORLD_FLOOR_Y,
                -26.0f,
                ANNEX_TAVI_SCALE,
                -0.4f
            ),
            "Tavi draw failed"
        );
        break;
    case N64GAME_ANNEX_SIMULATION:
        if (game->quest == N64GAME_QUEST_READY_FOR_TRIAL ||
            game->quest == N64GAME_QUEST_RESONANCE_TRIAL ||
            game->dialogue == N64GAME_DIALOGUE_SERA_TRIAL ||
            game->dialogue == N64GAME_DIALOGUE_BATTLE_VICTORY) {
            assertf(
                story_cast_renderer_draw(
                    &renderer->story_cast,
                    N64GAME_STORY_CAST_SERA,
                    renderer->frame_index,
                    -74.0f,
                    ANNEX_WORLD_FLOOR_Y,
                    10.0f,
                    ANNEX_SERA_SCALE,
                    -1.3f
                ),
                "Simulation Sera draw failed"
            );
        }
        break;
    case N64GAME_ANNEX_WORKSHOP:
        draw_quarrune(
            renderer, 1U, 48.0f, ANNEX_WORLD_FLOOR_Y, 10.0f,
            ANNEX_QUARRUNE_SCALE,
            0.12f + fm_sinf(angle * 1.4f) * 0.035f
        );
        break;
    case N64GAME_ANNEX_OVERLOOK:
        assertf(
            story_cast_renderer_draw(
                &renderer->story_cast,
                N64GAME_STORY_CAST_BEACON,
                renderer->frame_index,
                100.0f,
                ANNEX_WORLD_FLOOR_Y,
                44.0f,
                ANNEX_BEACON_SCALE,
                0.15f
            ),
            "Beacon draw failed"
        );
        if (game->quest == N64GAME_QUEST_BEACON_OVERLOOK) {
            assertf(
                story_cast_renderer_draw(
                    &renderer->story_cast,
                    N64GAME_STORY_CAST_SERA,
                    renderer->frame_index,
                    116.0f,
                    ANNEX_WORLD_FLOOR_Y,
                    44.0f,
                    ANNEX_SERA_SCALE,
                    0.3f
                ),
                "Overlook Sera draw failed"
            );
            assertf(
                story_cast_renderer_draw(
                    &renderer->story_cast,
                    N64GAME_STORY_CAST_TAVI,
                    renderer->frame_index,
                    90.0f,
                    ANNEX_WORLD_FLOOR_Y,
                    40.0f,
                    ANNEX_TAVI_SCALE,
                    -0.4f
                ),
                "Overlook Tavi draw failed"
            );
            assertf(
                renderer->support_echoes_ready &&
                    (((game->scene_ticks & UINT32_C(1)) != 0U) ||
                     support_echo_renderer_update_ambient(
                         &renderer->support_echoes,
                         N64GAME_SUPPORT_ECHO_AYSELOR
                     )),
                "Overlook Ayselor ambient update failed"
            );
            assertf(
                support_echo_renderer_draw_shadow(
                    &renderer->support_echoes,
                    N64GAME_SUPPORT_ECHO_AYSELOR,
                    renderer->frame_index,
                    108.0f,
                    ANNEX_WORLD_FLOOR_Y,
                    40.0f,
                    12.0f
                ),
                "Overlook Ayselor shadow draw failed"
            );
            draw_quarrune(
                renderer,
                1U,
                122.0f,
                ANNEX_WORLD_FLOOR_Y,
                38.0f,
                ANNEX_QUARRUNE_SCALE,
                -1.65f + fm_sinf(angle * 1.4f) * 0.025f
            );
            assertf(
                support_echo_renderer_draw(
                    &renderer->support_echoes,
                    N64GAME_SUPPORT_ECHO_AYSELOR,
                    renderer->frame_index,
                    108.0f,
                    ANNEX_WORLD_FLOOR_Y,
                    40.0f,
                    0.21f,
                    3.7f
                ),
                "Overlook Ayselor draw failed"
            );
        }
        break;
    case N64GAME_ANNEX_SECTOR_COUNT:
        break;
    }

    panel(8, 8, 250, 31);
    text_at(16.0f, 15.0f, STYLE_ACCENT, 228.0f, objective_text(game->quest));
    const char *const prompt = n64game_core_interaction_label(game);
    if (prompt != NULL) {
        panel(74, 142, 246, 164);
        text_at(84.0f, 149.0f, STYLE_TEXT, 156.0f, prompt);
    }
    if (game->menu != N64GAME_MENU_CLOSED) {
        draw_annex_menu(game);
    } else if (game->dialogue != N64GAME_DIALOGUE_NONE) {
        draw_dialogue(game);
    }
    if (renderer->annex_camera_fade_ticks > 0U) {
        const uint8_t fade_alpha = (uint8_t)(
            (uint32_t)renderer->annex_camera_fade_ticks * UINT32_C(255) /
            (uint32_t)ANNEX_CAMERA_FADE_FRAMES
        );
        fade_to_black(fade_alpha);
        --renderer->annex_camera_fade_ticks;
    }
}

static const char *echo_name(uint8_t actor)
{
    static const char *const NAMES[] = {"QUARRUNE", "AYSELOR", "GYRECLAST", "KIVARRAX"};
    return actor < 4U ? NAMES[actor] : "";
}

static const char *affinity_short_name(N64GameAffinity affinity)
{
    static const char *const NAMES[] = { "STR", "GAL", "CUR", "EMB" };
    return (unsigned)affinity < 4U ? NAMES[affinity] : "---";
}

static bool affinity_advantage_ui(N64GameAffinity attack, N64GameAffinity defense)
{
    return (attack == N64GAME_AFFINITY_STRATA && defense == N64GAME_AFFINITY_CURRENT) ||
        (attack == N64GAME_AFFINITY_CURRENT && defense == N64GAME_AFFINITY_EMBER) ||
        (attack == N64GAME_AFFINITY_EMBER && defense == N64GAME_AFFINITY_GALE) ||
        (attack == N64GAME_AFFINITY_GALE && defense == N64GAME_AFFINITY_STRATA);
}

static bool damaging_move(const N64GameMoveDef *move)
{
    return move != NULL &&
        (move->effect == N64GAME_EFFECT_DAMAGE ||
         move->effect == N64GAME_EFFECT_DAMAGE_STAGGER_CHANCE ||
         move->effect == N64GAME_EFFECT_DAMAGE_STAGGER ||
         move->effect == N64GAME_EFFECT_DAMAGE_GROUND);
}

static bool move_disabled(
    const N64GameBattle *battle,
    uint8_t actor,
    uint8_t move,
    const N64GameMoveDef *definition
)
{
    const N64GameBattleActor *const user = &battle->actors[actor];
    const bool spent_once = definition->once_per_encounter &&
        (user->used_move_mask & (uint8_t)(UINT8_C(1) << move)) != 0U;
    const bool cooling_down = user->move_ready_round[move] != 0U &&
        battle->round < user->move_ready_round[move];
    return spent_once || cooling_down;
}

static const char *move_target_name(N64GameTargetRule rule)
{
    switch (rule) {
    case N64GAME_TARGET_ONE_ENEMY:
        return "1FOE";
    case N64GAME_TARGET_ALL_ENEMIES:
        return "ALLFOE";
    case N64GAME_TARGET_ONE_ALLY:
        return "ALLY";
    case N64GAME_TARGET_SELF:
        return "SELF";
    }
    return "TARGET";
}

static void format_move_detail(
    const N64GameMoveDef *move,
    char *summary,
    size_t summary_size,
    char *effect,
    size_t effect_size
)
{
    (void)snprintf(
        summary, summary_size, "%s / %s",
        move_target_name(move->target_rule), affinity_short_name(move->affinity)
    );
    switch (move->effect) {
    case N64GAME_EFFECT_DAMAGE:
        (void)snprintf(effect, effect_size, "PWR %u", (unsigned)move->power);
        break;
    case N64GAME_EFFECT_DAMAGE_STAGGER_CHANCE:
        (void)snprintf(
            effect, effect_size, "P%u / %u%%STG",
            (unsigned)move->power, (unsigned)move->effect_chance_percent
        );
        break;
    case N64GAME_EFFECT_DAMAGE_STAGGER:
        (void)snprintf(
            effect, effect_size, "P%u STG / C%u",
            (unsigned)move->power, (unsigned)move->cooldown_rounds
        );
        break;
    case N64GAME_EFFECT_DAMAGE_GROUND:
        (void)snprintf(
            effect, effect_size, "P%u STRIP+",
            (unsigned)move->power
        );
        break;
    case N64GAME_EFFECT_GUARD_UP:
        (void)snprintf(
            effect, effect_size, "GRD+1 / %uR",
            (unsigned)move->stage_rounds
        );
        break;
    case N64GAME_EFFECT_SPEED_UP:
        (void)snprintf(
            effect, effect_size, "SPD+1 / %uR",
            (unsigned)move->stage_rounds
        );
        break;
    case N64GAME_EFFECT_EMPOWER_NEXT_DAMAGE:
        (void)snprintf(effect, effect_size, "NEXT PWR +20%%");
        break;
    case N64GAME_EFFECT_HEAL_CLEAR_STAGGER:
        (void)snprintf(
            effect, effect_size, "HEAL%u CLR 1X",
            (unsigned)move->power
        );
        break;
    case N64GAME_EFFECT_POWER_DOWN:
        (void)snprintf(
            effect, effect_size, "PWR-1 / %uR",
            (unsigned)move->stage_rounds
        );
        break;
    case N64GAME_EFFECT_GUARD_DOWN:
        (void)snprintf(
            effect, effect_size, "GRD-1 / %uR",
            (unsigned)move->stage_rounds
        );
        break;
    case N64GAME_EFFECT_FINISHER:
        (void)snprintf(effect, effect_size, "LINKED DUO ATTACK");
        break;
    }
}

static void draw_battle_status(const N64GameCore *game)
{
    const N64GameBattle *const battle = &game->battle;
    for (uint8_t actor = 0U; actor < 4U; ++actor) {
        char hp[24];
        char status[40];
        const N64GameBattleActor *const state = &battle->actors[actor];
        const bool player = actor < 2U;
        const int x = player ? 8 + (int)actor * 112 : 96 + ((int)actor - 2) * 108;
        const int y = player ? 112 : 8;
        panel(x, y, x + 104, y + 34);
        text_at((float)(x + 5), (float)(y + 4), STYLE_TEXT, 56.0f, echo_name(actor));
        (void)snprintf(hp, sizeof(hp), "%d/%d", (int)state->hp, (int)state->max_hp);
        text_at((float)(x + 63), (float)(y + 4), STYLE_MUTED, 36.0f, hp);
        hp_bar(x + 5, y + 16, 94, state->hp, state->max_hp);
        (void)snprintf(
            status, sizeof(status), "P%+d G%+d S%+d%s",
            (int)state->power_stage, (int)state->guard_stage, (int)state->speed_stage,
            state->stagger_rounds > 0U ? " STG" : ""
        );
        text_at(
            (float)(x + 5), (float)(y + 23),
            state->stagger_rounds > 0U ? STYLE_WARNING : STYLE_MUTED,
            94.0f, status
        );
        if (game->battle_selecting_target && game->battle_target_cursor == actor) {
            fill_rect(x, y, x + 4, y + 34, RGBA32(221, 97, 163, 255));
        }
    }
}

static void draw_battle_menu(const N64GameCore *game)
{
    const N64GameBattle *const battle = &game->battle;
    panel(8, 146, 178, 234);
    if (battle->phase == N64GAME_BATTLE_INTRO) {
        text_at(18.0f, 158.0f, STYLE_ACCENT, 150.0f, "RESONANCE TRIAL");
        text_at(18.0f, 181.0f, STYLE_TEXT, 150.0f, "GYRECLAST + KIVARRAX\nPATTERN LINKING...");
    } else if (battle->phase == N64GAME_BATTLE_COMMAND) {
        const uint8_t actor = battle->command_actor;
        text_at(16.0f, 153.0f, STYLE_ACCENT, 150.0f, echo_name(actor));
        for (uint8_t move = 0U; move < 4U; ++move) {
            char label[40];
            const N64GameMoveDef *const definition = n64game_move_def(
                battle->actors[actor].id, move
            );
            const bool disabled = move_disabled(battle, actor, move, definition);
            const uint8_t style = disabled ? STYLE_MUTED :
                (!game->battle_selecting_target && game->battle_move_cursor == move ?
                 STYLE_WARNING : STYLE_TEXT);
            (void)snprintf(
                label, sizeof(label), "%s%s", definition->name,
                disabled ? (definition->once_per_encounter ? " [USED]" : " [WAIT]") : ""
            );
            text_at(18.0f, 168.0f + (float)move * 13.0f, style, 150.0f, label);
        }
        if (actor == 0U && battle->resonance == N64GAME_RESONANCE_MAX &&
            battle->actors[1].hp > 0) {
            const uint8_t style = game->battle_move_cursor == N64GAME_MOVE_FINISHER ?
                STYLE_WARNING : STYLE_ACCENT;
            text_at(18.0f, 220.0f, style, 150.0f, "HORIZON BREAK");
        }
    } else if (battle->phase == N64GAME_BATTLE_VICTORY) {
        text_at(18.0f, 158.0f, STYLE_ACCENT, 150.0f, "RESONANCE STABLE");
        text_at(18.0f, 181.0f, STYLE_TEXT, 150.0f, "TRIAL COMPLETE\nA  CONTINUE");
    } else if (battle->phase == N64GAME_BATTLE_DEFEAT) {
        text_at(18.0f, 158.0f, STYLE_WARNING, 150.0f, "PATTERN LOST");
        text_at(18.0f, 181.0f, STYLE_TEXT, 150.0f, "A  RETRY\nB  RETURN");
    } else {
        const N64GameBattleEvent *const event = &battle->last_event;
        if (event->happened) {
            char message[96];
            if (event->skipped) {
                (void)snprintf(
                    message, sizeof(message), "%s",
                    event->move == N64GAME_MOVE_FINISHER ?
                        "HORIZON BREAK CANCELED" : "ACTION RESISTED / CANNOT ACT"
                );
            } else if (event->move == N64GAME_MOVE_FINISHER) {
                (void)snprintf(message, sizeof(message), "HORIZON BREAK");
            } else {
                const N64GameMoveDef *const move = n64game_move_def(
                    battle->actors[event->actor].id, event->move
                );
                (void)snprintf(message, sizeof(message), "%s / %s",
                               echo_name(event->actor), move != NULL ? move->name : "ACTION");
            }
            text_at(18.0f, 158.0f, STYLE_ACCENT, 150.0f, message);
            if (event->affinity_advantage) {
                text_at(
                    18.0f, 184.0f, STYLE_WARNING, 150.0f,
                    "STRONG - 1.5x affinity force"
                );
            } else if (!event->skipped && event->target < N64GAME_BATTLE_ACTOR_COUNT &&
                       event->move < N64GAME_BATTLE_MOVE_COUNT) {
                const N64GameMoveDef *const move = n64game_move_def(
                    battle->actors[event->actor].id, event->move
                );
                if (damaging_move(move) &&
                    affinity_advantage_ui(
                        battle->actors[event->target].affinity, move->affinity
                    )) {
                    text_at(
                        18.0f, 184.0f, STYLE_MUTED, 150.0f,
                        "RESISTED - 0.75x affinity force"
                    );
                }
            }
        } else {
            text_at(18.0f, 158.0f, STYLE_MUTED, 150.0f, "BUILDING TURN QUEUE");
        }
    }

    panel(184, 146, 312, 180);
    text_at(192.0f, 153.0f, STYLE_ACCENT, 110.0f, "RESONANCE");
    hp_bar(192, 168, 110, battle->resonance, N64GAME_RESONANCE_MAX);
    panel(184, 186, 312, 234);
    if (game->battle_selecting_target) {
        const uint8_t actor = battle->command_actor;
        const uint8_t target = game->battle_target_cursor;
        const N64GameMoveDef *const move = n64game_move_def(
            battle->actors[actor].id, game->battle_move_cursor
        );
        const char *forecast = "NEUTRAL FORCE";
        if (target < N64GAME_BATTLE_ACTOR_COUNT && damaging_move(move)) {
            if (affinity_advantage_ui(move->affinity, battle->actors[target].affinity)) {
                forecast = "STRONG 1.5x";
            } else if (affinity_advantage_ui(
                           battle->actors[target].affinity, move->affinity)) {
                forecast = "RESIST 0.75x";
            }
        }
        text_at(192.0f, 192.0f, STYLE_WARNING, 110.0f, echo_name(target));
        text_at(192.0f, 207.0f, STYLE_TEXT, 110.0f, forecast);
        text_at(192.0f, 221.0f, STYLE_MUTED, 110.0f, "A OK B BACK");
    } else {
        char move_summary[56];
        char move_effect[64];
        if (battle->phase == N64GAME_BATTLE_COMMAND &&
            game->battle_move_cursor < N64GAME_BATTLE_MOVE_COUNT) {
            const uint8_t actor = battle->command_actor;
            const N64GameMoveDef *const move = n64game_move_def(
                battle->actors[actor].id, game->battle_move_cursor
            );
            format_move_detail(
                move,
                move_summary,
                sizeof(move_summary),
                move_effect,
                sizeof(move_effect)
            );
            text_at(192.0f, 192.0f, STYLE_TEXT, 110.0f, move_summary);
            text_at(192.0f, 207.0f, STYLE_ACCENT, 110.0f, move_effect);
            text_at(192.0f, 221.0f, STYLE_MUTED, 110.0f, "A OK B BACK");
        } else if (battle->phase == N64GAME_BATTLE_COMMAND) {
            text_at(192.0f, 192.0f, STYLE_WARNING, 110.0f, "STRATA + GALE");
            text_at(192.0f, 207.0f, STYLE_ACCENT, 110.0f, "ALL / P36 S+G");
            text_at(192.0f, 221.0f, STYLE_MUTED, 110.0f, "A LINK B BACK");
        } else {
            text_at(192.0f, 194.0f, STYLE_TEXT, 110.0f, "D-PAD MOVE\nA CHOOSE");
        }
    }
}

static void draw_battle(N64GameRenderer *renderer, const N64GameCore *game)
{
    const fm_vec3_t camera = {{0.0f, 56.0f, 112.0f}};
    const fm_vec3_t target = {{0.0f, -4.0f, 0.0f}};
    begin_world_render(renderer, &camera, &target);
    draw_battle_kit_backdrop(renderer);
    static const uint8_t BATTLE_ACTOR_AMBIENT[4] = {112, 105, 112, 255};
    t3d_light_set_ambient(BATTLE_ACTOR_AMBIENT);
    static const float POSITIONS[4][2] = {
        {-32.0f, -43.0f}, {32.0f, -40.0f},
        {-72.0f, -76.0f}, {72.0f, -70.0f},
    };
    const float angle = (float)game->scene_ticks * 0.012f;
    assertf(
        renderer->support_echoes_ready &&
            support_echo_renderer_update(
                &renderer->support_echoes, &game->battle
            ),
        "Support Echoform renderer update failed"
    );
    for (uint8_t actor = 1U; actor < N64GAME_BATTLE_ACTOR_COUNT; ++actor) {
        const N64GameSupportEchoKind kind =
            (N64GameSupportEchoKind)(actor - 1U);
        const bool knockout_motion =
            renderer->support_echoes.instances[kind].motion ==
                N64GAME_SUPPORT_ECHO_MOTION_HIT;
        if (game->battle.actors[actor].hp > 0 || knockout_motion) {
            assertf(
                support_echo_renderer_draw_shadow(
                    &renderer->support_echoes,
                    kind,
                    renderer->frame_index,
                    POSITIONS[actor][0],
                    ANNEX_WORLD_FLOOR_Y,
                    POSITIONS[actor][1],
                    BATTLE_SUPPORT_SHADOW_RADII[kind]
                ),
                "Support Echoform shadow draw failed for actor %u",
                (unsigned int)actor
            );
        }
    }
    for (uint8_t actor = 0U; actor < 4U; ++actor) {
        const bool knockout_motion = actor > 0U &&
            renderer->support_echoes.instances[actor - 1U].motion ==
                N64GAME_SUPPORT_ECHO_MOTION_HIT;
        if (game->battle.actors[actor].hp > 0 || knockout_motion) {
            if (actor == 0U) {
                draw_quarrune(
                    renderer, actor,
                    POSITIONS[actor][0], ANNEX_WORLD_FLOOR_Y, POSITIONS[actor][1],
                    BATTLE_QUARRUNE_SCALE,
                    0.10f + fm_sinf(angle * 2.0f) * 0.035f
                );
            } else {
                const N64GameSupportEchoKind kind =
                    (N64GameSupportEchoKind)(actor - 1U);
                assertf(
                    support_echo_renderer_draw(
                        &renderer->support_echoes,
                        kind,
                        renderer->frame_index,
                        POSITIONS[actor][0],
                        ANNEX_WORLD_FLOOR_Y,
                        POSITIONS[actor][1],
                        BATTLE_SUPPORT_SCALES[kind],
                        BATTLE_SUPPORT_YAWS[kind]
                    ),
                    "Support Echoform model draw failed for actor %u",
                    (unsigned int)actor
                );
            }
        }
    }
    draw_battle_status(game);
    draw_battle_menu(game);
}

static void draw_name_entry(const N64GameCore *game)
{
    clear_2d(RGBA32(10, 25, 35, 255));
    centered(18.0f, STYLE_ACCENT, "RESONANCE IDENTITY");
    panel(56, 42, 264, 72);
    centered(51.0f, STYLE_TEXT, game->name_length > 0U ? game->player_name : "ARI");
    for (uint8_t slot = 0U; slot < 28U; ++slot) {
        const int column = slot % 7U;
        const int row = slot / 7U;
        const float x = 41.0f + (float)column * 36.0f;
        const float y = 92.0f + (float)row * 27.0f;
        char label[5] = {0};
        if (slot < 26U) {
            label[0] = (char)('A' + slot);
        } else if (slot == 26U) {
            (void)snprintf(label, sizeof(label), "DEL");
        } else {
            (void)snprintf(label, sizeof(label), "OK");
        }
        text_at(x, y, game->name_cursor == slot ? STYLE_WARNING : STYLE_TEXT, 32.0f, label);
    }
    centered(214.0f, STYLE_MUTED, "D-PAD SELECT / A ENTER / B ERASE");
}

static void draw_signal_diamond(int center_x, int center_y, color_t color)
{
    fill_rect(center_x - 2, center_y - 5, center_x + 2, center_y + 5, color);
    fill_rect(center_x - 4, center_y - 3, center_x + 4, center_y + 3, color);
}

static void draw_signal_brackets(color_t color)
{
    fill_rect(12, 14, 52, 16, color);
    fill_rect(12, 14, 14, 34, color);
    fill_rect(268, 14, 308, 16, color);
    fill_rect(306, 14, 308, 34, color);
    fill_rect(12, 224, 52, 226, color);
    fill_rect(12, 206, 14, 226, color);
    fill_rect(268, 224, 308, 226, color);
    fill_rect(306, 206, 308, 226, color);
}

void n64game_renderer_draw_loading(
    const N64GameRenderer *renderer,
    N64GameLoadingStage stage
)
{
    static const char *const STATUS[] = {
        "INITIALIZING SIGNAL RUNTIME",
        "LOADING MERIDIAN ANNEX",
        "VERIFYING RESONANCE FILE",
        "SIGNAL PATH READY",
    };
    if (renderer == NULL || !renderer->font_registered ||
        stage < N64GAME_LOADING_RUNTIME || stage > N64GAME_LOADING_READY) {
        return;
    }

    rdpq_attach(display_get(), display_get_zbuf());
    clear_2d(RGBA32(3, 10, 17, 255));
    fill_rect(0, 0, 320, 5, RGBA32(184, 67, 151, 255));
    fill_rect(0, 5, 320, 7, RGBA32(72, 29, 75, 255));
    fill_rect(0, 233, 320, 235, RGBA32(18, 55, 65, 255));
    fill_rect(0, 235, 320, 240, RGBA32(31, 104, 110, 255));
    fill_rect(18, 13, 302, 15, RGBA32(20, 63, 73, 255));
    fill_rect(18, 15, 20, 52, RGBA32(20, 63, 73, 255));
    fill_rect(300, 15, 302, 52, RGBA32(20, 63, 73, 255));
    centered(19.0f, STYLE_ACCENT, "N64GAME");
    centered(37.0f, STYLE_TEXT, "MERIDIAN SIGNAL LAB");
    centered(52.0f, STYLE_MUTED, "ANNEX RELAY / COLD START");

    draw_signal_diamond(148, 68, RGBA32(42, 126, 132, 255));
    draw_signal_diamond(160, 65, RGBA32(91, 231, 204, 255));
    draw_signal_diamond(172, 68, RGBA32(42, 126, 132, 255));

    /* The relay is built from crisp native-resolution geometry, never a placeholder texture. */
    fill_rect(154, 78, 166, 114, RGBA32(36, 105, 111, 255));
    fill_rect(151, 84, 169, 108, RGBA32(8, 26, 35, 255));
    fill_rect(156, 87, 164, 103, RGBA32(91, 231, 204, 255));
    fill_rect(143, 89, 151, 103, RGBA32(22, 64, 73, 255));
    fill_rect(169, 89, 177, 103, RGBA32(22, 64, 73, 255));
    fill_rect(135, 93, 143, 99, RGBA32(43, 121, 126, 255));
    fill_rect(177, 93, 185, 99, RGBA32(43, 121, 126, 255));
    fill_rect(128, 95, 135, 97, RGBA32(31, 87, 96, 255));
    fill_rect(185, 95, 192, 97, RGBA32(31, 87, 96, 255));
    fill_rect(157, 114, 163, 120, RGBA32(120, 69, 45, 255));

    fill_rect(37, 126, 283, 189, RGBA32(17, 47, 57, 255));
    fill_rect(39, 128, 281, 187, RGBA32(7, 21, 30, 255));
    fill_rect(43, 132, 277, 183, RGBA32(13, 32, 42, 255));
    centered(139.0f, STYLE_MUTED, STATUS[(size_t)stage]);
    for (int segment = 0; segment < 4; ++segment) {
        const int x0 = 68 + segment * 47;
        const color_t color = segment <= (int)stage ?
            RGBA32(87, 226, 203, 255) : RGBA32(24, 53, 63, 255);
        fill_rect(x0, 160, x0 + 39, 168, RGBA32(7, 18, 26, 255));
        fill_rect(x0 + 2, 162, x0 + 37, 166, color);
    }
    centered(178.0f, STYLE_ACCENT, "01 / 02 / 03 / READY");
    fill_rect(58, 204, 262, 205, RGBA32(24, 71, 79, 255));
    centered(211.0f, STYLE_MUTED, "RESONANCE LINK / ORIGINAL N64 BUILD");
    rdpq_detach_show();
}

static void draw_opening(const N64GameCore *game, bool continue_available)
{
    clear_2d(RGBA32(6, 15, 24, 255));
    if (game->scene == N64GAME_SCENE_BOOT) {
        fill_rect(18, 18, 302, 222, RGBA32(8, 22, 31, 255));
        fill_rect(20, 20, 300, 220, RGBA32(5, 14, 23, 255));
        draw_signal_brackets(RGBA32(41, 120, 126, 255));
        draw_signal_diamond(148, 58, RGBA32(42, 126, 132, 255));
        draw_signal_diamond(160, 55, RGBA32(91, 231, 204, 255));
        draw_signal_diamond(172, 58, RGBA32(42, 126, 132, 255));
        centered(73.0f, STYLE_ACCENT, "N64GAME");
        centered(96.0f, STYLE_TEXT, "MERIDIAN SIGNAL LAB");
        const int phase = (int)(game->scene_ticks % 20U);
        const int pulse = phase <= 10 ? phase : 20 - phase;
        fill_rect(154, 122, 166, 144, RGBA32(24, 70, 78, 255));
        fill_rect(157, 126, 163, 140, RGBA32(87, 226, 203, 255));
        fill_rect(136 - pulse, 130, 149 - pulse, 136, RGBA32(45, 126, 132, 255));
        fill_rect(171 + pulse, 130, 184 + pulse, 136, RGBA32(45, 126, 132, 255));
        fill_rect(127 - pulse, 132, 133 - pulse, 134, RGBA32(26, 75, 84, 255));
        fill_rect(187 + pulse, 132, 193 + pulse, 134, RGBA32(26, 75, 84, 255));
        centered(163.0f, STYLE_MUTED, "AN ORIGINAL N64 CHAPTER");
        fill_rect(86, 187, 234, 188, RGBA32(61, 34, 67, 255));
        centered(198.0f, STYLE_MUTED, "30 HZ SIGNAL ACQUISITION");
    } else {
        fill_rect(8, 8, 312, 232, RGBA32(15, 39, 49, 255));
        fill_rect(11, 11, 309, 229, RGBA32(5, 13, 22, 255));
        fill_rect(14, 14, 306, 18, RGBA32(183, 72, 154, 255));
        fill_rect(14, 222, 306, 226, RGBA32(30, 99, 105, 255));
        draw_signal_brackets(RGBA32(62, 142, 144, 255));
        draw_signal_diamond(148, 45, RGBA32(60, 130, 137, 255));
        draw_signal_diamond(160, 42, RGBA32(184, 67, 151, 255));
        draw_signal_diamond(172, 45, RGBA32(60, 130, 137, 255));
        centered(60.0f, STYLE_MUTED, "PLAYBACK WINDOW / 4:3 / 54.5 SEC");
        fill_rect(45, 79, 275, 81, RGBA32(52, 30, 61, 255));
        fill_rect(45, 118, 275, 120, RGBA32(20, 62, 71, 255));
        centered(88.0f, STYLE_WARNING, "INSERT CUTSCENE HERE");
        centered(108.0f, STYLE_TEXT, "SOLACE INTERCEPTION");
        centered(129.0f, STYLE_MUTED, "DESERT DUSK / FRACTURE STORM / BEACON FALL");
        centered(
            181.0f,
            STYLE_MUTED,
            continue_available ? "START CONTINUE / A NEW FILE" : "A OR START TO BEGIN"
        );
        centered(205.0f, STYLE_ACCENT, "STORYBOARD PACKAGE INCLUDED");
        uint8_t fade_alpha = 0U;
        if (game->scene_ticks < 8U) {
            fade_alpha = (uint8_t)(
                UINT32_C(255) - game->scene_ticks * UINT32_C(255) / UINT32_C(8)
            );
        } else if (game->scene_ticks >= 98U) {
            const uint32_t fade_tick = game->scene_ticks - UINT32_C(97);
            fade_alpha = (uint8_t)(fade_tick * UINT32_C(255) / UINT32_C(8));
        }
        fade_to_black(fade_alpha);
    }
}

static void draw_ending(const N64GameCore *game, bool save_busy, bool save_available)
{
    clear_2d(RGBA32(7, 13, 24, 255));
    fill_rect(0, 0, 320, 8, RGBA32(170, 61, 145, 255));
    centered(54.0f, STYLE_WARNING, "SIGNAL ACQUIRED");
    centered(80.0f, STYLE_ACCENT, "SOLACE / EMERGENCY BEACON");
    centered(119.0f, STYLE_TEXT, "END OF OPENING CHAPTER");
    char player_line[64];
    const char *save_state = "ARCHIVE LOCKED";
    switch (game->final_save_state) {
    case N64GAME_FINAL_SAVE_PENDING:
        save_state = save_busy ? "FINALIZING SAVE / ARCHIVE LOCKED" :
            "AWAITING SAVE / ARCHIVE LOCKED";
        break;
    case N64GAME_FINAL_SAVE_FAILED:
        save_state = save_available ? "SAVE WRITE FAILED" : "EEPROM UNAVAILABLE";
        break;
    case N64GAME_FINAL_SAVE_CONFIRM_UNSAVED:
        save_state = "UNSAVED PROGRESS WILL BE LOST";
        break;
    case N64GAME_FINAL_SAVE_VERIFIED:
        save_state = "RESONANCE FILE VERIFIED";
        break;
    case N64GAME_FINAL_SAVE_ACCEPTED_UNSAVED:
        save_state = "CONTINUING WITHOUT A SAVE";
        break;
    case N64GAME_FINAL_SAVE_NONE:
        break;
    }
    (void)snprintf(player_line, sizeof(player_line), "%s / %s",
                   game->player_name, save_state);
    centered(151.0f, STYLE_MUTED, player_line);
    centered(165.0f, STYLE_TEXT, "THE STORM IS ANSWERING.");
    if (game->final_save_state == N64GAME_FINAL_SAVE_FAILED) {
        centered(187.0f, STYLE_WARNING, "A RETRY SAVE / B CONTINUE WITHOUT SAVING");
    } else if (game->final_save_state == N64GAME_FINAL_SAVE_CONFIRM_UNSAVED) {
        centered(187.0f, STYLE_WARNING, "CONTINUE WITHOUT SAVING?");
        centered(207.0f, STYLE_TEXT, "A CONFIRM / B BACK");
    }
    if (game->menu != N64GAME_MENU_CLOSED) {
        draw_annex_menu(game);
    }
}

void n64game_renderer_draw(
    N64GameRenderer *renderer,
    const N64GameCore *game,
    bool save_busy,
    bool save_available,
    bool continue_available,
    bool controller_connected
)
{
    if (renderer == NULL || game == NULL) {
        return;
    }
    rdpq_attach(display_get(), display_get_zbuf());
    switch (game->scene) {
    case N64GAME_SCENE_BOOT:
    case N64GAME_SCENE_OPENING_SLATE:
        draw_opening(game, continue_available);
        break;
    case N64GAME_SCENE_NAME_ENTRY:
        draw_name_entry(game);
        break;
    case N64GAME_SCENE_ANNEX:
        draw_annex(renderer, game);
        break;
    case N64GAME_SCENE_BATTLE:
        draw_battle(renderer, game);
        break;
    case N64GAME_SCENE_END_CHAPTER:
        draw_ending(game, save_busy, save_available);
        break;
    }
    if (game->scene == N64GAME_SCENE_END_CHAPTER &&
        game->final_save_state == N64GAME_FINAL_SAVE_PENDING && save_busy) {
        panel(238, 214, 314, 234);
        text_at(246.0f, 221.0f, STYLE_ACCENT, 62.0f, "SAVING");
    } else if (game->scene != N64GAME_SCENE_END_CHAPTER && save_busy) {
        panel(238, 214, 314, 234);
        text_at(246.0f, 221.0f, STYLE_ACCENT, 62.0f, "SAVING");
    } else if (game->scene != N64GAME_SCENE_END_CHAPTER && !save_available) {
        text_at(218.0f, 224.0f, STYLE_WARNING, 96.0f, "SAVE UNAVAILABLE");
    }
    if (!controller_connected) {
        panel(42, 91, 278, 149);
        centered(104.0f, STYLE_WARNING, "CONTROLLER DISCONNECTED");
        centered(126.0f, STYLE_TEXT, "RECONNECT CONTROLLER 1");
    }
    rdpq_detach_show();
}
