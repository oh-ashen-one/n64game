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
    ACTOR_STYLE_COUNT = 8,
    ANNEX_MATRIX_INDEX = 5,
    ACTOR_MATRIX_COUNT = 6,
    ARI_ANIMATION_IDLE = 0,
    ARI_ANIMATION_WALK,
    ARI_ANIMATION_RUN,
    BATTLE_ECHO_ANIMATION_IDLE = 0,
    BATTLE_ECHO_ANIMATION_REPOSITION,
    BATTLE_ECHO_ANIMATION_HIT,
};

static const char ANNEX_MODEL_PATH[] = "rom:/env/annex/annex_threshold.t3dm";
static const char ARI_MODEL_PATH[] = "rom:/chr/player_ari/ari.t3dm";
static const char ARI_BODY_PATH[] =
    "rom:/chr/player_ari/tex_ari_body_ci8_64x64.sprite";
static const char ARI_SHARED_SHADOW_PATH[] =
    "rom:/echo/echo.quarrune/tex_quarrune_blob_shadow_ia8_32x32.sprite";

typedef struct {
    const char *debug_name;
    const char *model_path;
    const char *body_path;
    uint32_t body_top_reference;
    uint32_t body_bottom_reference;
    uint16_t minimum_body_palette_colors;
    float reposition_speed;
    float hit_speed;
} N64GameBattleEchoAssetConfig;

static const char *const ARI_ANIMATION_NAMES[
    N64GAME_ARI_RUNTIME_ANIMATION_COUNT
] = {"idle_a", "walk", "run"};

static const char *const BATTLE_ECHO_ANIMATION_NAMES[
    N64GAME_BATTLE_ECHO_ANIMATION_COUNT
] = {"idle_a", "reposition", "hit"};

static const N64GameBattleEchoAssetConfig QUARRUNE_ASSET_CONFIG = {
    .debug_name = "quarrune",
    .model_path = "rom:/echo/echo.quarrune/quarrune.t3dm",
    .body_path =
        "rom:/echo/echo.quarrune/tex_quarrune_body_ci8_64x64.sprite",
    .body_top_reference = UINT32_C(0x51554231),
    .body_bottom_reference = UINT32_C(0x51554230),
    .minimum_body_palette_colors = 40U,
    .reposition_speed = 1.0f,
    .hit_speed = 1.0f,
};

static const N64GameBattleEchoAssetConfig AYSELOR_ASSET_CONFIG = {
    .debug_name = "ayselor",
    .model_path = "rom:/echo/echo.ayselor/ayselor.t3dm",
    .body_path =
        "rom:/echo/echo.ayselor/tex_ayselor_body_ci8_64x64.sprite",
    .body_top_reference = UINT32_C(0x41594230),
    .body_bottom_reference = UINT32_C(0x41594231),
    .minimum_body_palette_colors = 46U,
    .reposition_speed = 1.0f,
    .hit_speed = 1.0f,
};

static const N64GameBattleEchoAssetConfig GYRECLAST_ASSET_CONFIG = {
    .debug_name = "gyreclast",
    .model_path = "rom:/echo/echo.gyreclast/gyreclast.t3dm",
    .body_path =
        "rom:/echo/echo.gyreclast/tex_gyreclast_body_ci8_64x64.sprite",
    .body_top_reference = UINT32_C(0x47594230),
    .body_bottom_reference = UINT32_C(0x47594231),
    .minimum_body_palette_colors = 11U,
    .reposition_speed = 2.4f,
    .hit_speed = 1.8f,
};

static const N64GameBattleEchoAssetConfig KIVARRAX_ASSET_CONFIG = {
    .debug_name = "kivarrax",
    .model_path = "rom:/echo/echo.kivarrax/kivarrax.t3dm",
    .body_path =
        "rom:/echo/echo.kivarrax/tex_kivarrax_body_ci8_64x64.sprite",
    .body_top_reference = UINT32_C(0x4B564230),
    .body_bottom_reference = UINT32_C(0x4B564231),
    .minimum_body_palette_colors = 53U,
    .reposition_speed = 2.4f,
    .hit_speed = 1.8f,
};

static const uint32_t ACTOR_COLORS[ACTOR_STYLE_COUNT] = {
    UINT32_C(0xD7A253FF),
    UINT32_C(0x79C9D4FF),
    UINT32_C(0x3AA6A0FF),
    UINT32_C(0xD45E49FF),
    UINT32_C(0xE4C49AFF),
    UINT32_C(0x5DDDC6FF),
    UINT32_C(0xA36BD1FF),
    UINT32_C(0xC88B4AFF),
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

static void setup_actor_vertices(N64GameRenderer *renderer)
{
    const uint16_t top = t3d_vert_pack_normal(&(fm_vec3_t){{0.0f, 1.0f, 0.0f}});
    const uint16_t left = t3d_vert_pack_normal(&(fm_vec3_t){{-0.7f, -0.4f, 0.6f}});
    const uint16_t right = t3d_vert_pack_normal(&(fm_vec3_t){{0.7f, -0.4f, 0.6f}});
    const uint16_t back = t3d_vert_pack_normal(&(fm_vec3_t){{0.0f, -0.4f, -0.9f}});
    for (size_t style = 0U; style < ACTOR_STYLE_COUNT; ++style) {
        const uint32_t color = ACTOR_COLORS[style];
        renderer->actor_vertices[style * 2U] = (T3DVertPacked){
            .posA = {0, 22, 0}, .rgbaA = color, .normA = top,
            .posB = {-14, -16, 12}, .rgbaB = color, .normB = left,
        };
        renderer->actor_vertices[style * 2U + 1U] = (T3DVertPacked){
            .posA = {14, -16, 12}, .rgbaA = color, .normA = right,
            .posB = {0, -16, -16}, .rgbaB = color, .normB = back,
        };
    }
}

static bool setup_annex(N64GameRenderer *renderer)
{
    renderer->annex_model = t3d_model_load(ANNEX_MODEL_PATH);
    if (renderer->annex_model == NULL) {
        debugf("[annex] model load failed: %s\n", ANNEX_MODEL_PATH);
        return false;
    }

    rspq_block_begin();
    t3d_model_draw(renderer->annex_model);
    renderer->annex_draw_block = rspq_block_end();
    if (renderer->annex_draw_block == NULL) {
        debugf("[annex] draw-block recording failed\n");
        return false;
    }
    renderer->annex_ready = true;
    return true;
}

static bool setup_ari(N64GameRenderer *renderer)
{
    const N64GameIndexedRenderAssetsConfig assets_config = {
        .body_sprite_path = ARI_BODY_PATH,
        .blob_shadow_sprite_path = ARI_SHARED_SHADOW_PATH,
        .body_top_reference = UINT32_C(0x41524930),
        .body_bottom_reference = UINT32_C(0x41524931),
        .minimum_body_palette_colors = 24U,
    };
    if (!n64game_indexed_render_assets_load(
            &renderer->ari_assets, &assets_config
        )) {
        debugf("[ari] render-asset load failed\n");
        return false;
    }

    renderer->ari_model = t3d_model_load(ARI_MODEL_PATH);
    if (renderer->ari_model == NULL) {
        debugf("[ari] model load failed: %s\n", ARI_MODEL_PATH);
        return false;
    }
    if (t3d_model_get_skeleton(renderer->ari_model) == NULL) {
        debugf("[ari] model has no skeleton\n");
        return false;
    }

    renderer->ari_skeleton = t3d_skeleton_create_buffered(
        renderer->ari_model, (int)renderer->buffer_count
    );
    if (renderer->ari_skeleton.bones == NULL ||
        renderer->ari_skeleton.boneMatricesFP == NULL) {
        debugf("[ari] skeleton allocation failed\n");
        return false;
    }
    renderer->ari_idle_skeleton = t3d_skeleton_clone(
        &renderer->ari_skeleton, false
    );
    renderer->ari_walk_skeleton = t3d_skeleton_clone(
        &renderer->ari_skeleton, false
    );
    renderer->ari_run_skeleton = t3d_skeleton_clone(
        &renderer->ari_skeleton, false
    );
    renderer->ari_motion_skeleton = t3d_skeleton_clone(
        &renderer->ari_skeleton, false
    );
    if (renderer->ari_idle_skeleton.bones == NULL ||
        renderer->ari_walk_skeleton.bones == NULL ||
        renderer->ari_run_skeleton.bones == NULL ||
        renderer->ari_motion_skeleton.bones == NULL) {
        debugf("[ari] blend-skeleton allocation failed\n");
        return false;
    }

    T3DSkeleton *const animation_skeletons[
        N64GAME_ARI_RUNTIME_ANIMATION_COUNT
    ] = {
        &renderer->ari_idle_skeleton,
        &renderer->ari_walk_skeleton,
        &renderer->ari_run_skeleton,
    };
    for (uint8_t index = 0U;
         index < N64GAME_ARI_RUNTIME_ANIMATION_COUNT;
         ++index) {
        renderer->ari_animations[index] = t3d_anim_create(
            renderer->ari_model, ARI_ANIMATION_NAMES[index]
        );
        ++renderer->ari_animation_count;
        if (renderer->ari_animations[index].file == NULL) {
            debugf("[ari] animation stream open failed: %s\n",
                   ARI_ANIMATION_NAMES[index]);
            return false;
        }
        t3d_anim_attach(
            &renderer->ari_animations[index], animation_skeletons[index]
        );
        t3d_anim_update(&renderer->ari_animations[index], 0.0f);
    }
    t3d_skeleton_blend(
        &renderer->ari_motion_skeleton,
        &renderer->ari_walk_skeleton,
        &renderer->ari_run_skeleton,
        0.0f
    );
    t3d_skeleton_blend(
        &renderer->ari_skeleton,
        &renderer->ari_idle_skeleton,
        &renderer->ari_motion_skeleton,
        0.0f
    );
    for (uint32_t index = 0U; index < renderer->buffer_count; ++index) {
        t3d_skeleton_update(&renderer->ari_skeleton);
    }

    rspq_block_begin();
    t3d_model_draw_custom(
        renderer->ari_model,
        (T3DModelDrawConf){
            .userData = &renderer->ari_assets,
            .dynTextureCb = n64game_indexed_render_assets_dynamic_texture_cb,
            .matrices = (const T3DMat4FP *)t3d_segment_placeholder(
                T3D_SEGMENT_SKELETON
            ),
        }
    );
    renderer->ari_draw_block = rspq_block_end();
    if (renderer->ari_draw_block == NULL) {
        debugf("[ari] draw-block recording failed\n");
        return false;
    }
    if (!n64game_indexed_render_assets_callback_ok(&renderer->ari_assets)) {
        debugf(
            "[ari] dynamic-texture callback failed: callbacks=%u fault=%u\n",
            (unsigned int)renderer->ari_assets.successful_body_callbacks,
            renderer->ari_assets.callback_fault ? 1U : 0U
        );
        return false;
    }
    renderer->ari_ready = true;
    return true;
}

static bool setup_battle_echo(
    N64GameRenderer *renderer,
    N64GameBattleEchoRenderer *echo,
    const N64GameBattleEchoAssetConfig *config
)
{
    const N64GameIndexedRenderAssetsConfig assets_config = {
        .body_sprite_path = config->body_path,
        .blob_shadow_sprite_path = ARI_SHARED_SHADOW_PATH,
        .body_top_reference = config->body_top_reference,
        .body_bottom_reference = config->body_bottom_reference,
        .minimum_body_palette_colors = config->minimum_body_palette_colors,
    };
    if (!n64game_indexed_render_assets_load(&echo->assets, &assets_config)) {
        debugf("[%s] render-asset load failed\n", config->debug_name);
        return false;
    }

    echo->model = t3d_model_load(config->model_path);
    if (echo->model == NULL) {
        debugf("[%s] model load failed: %s\n",
               config->debug_name, config->model_path);
        return false;
    }
    if (t3d_model_get_skeleton(echo->model) == NULL) {
        debugf("[%s] model has no skeleton\n", config->debug_name);
        return false;
    }

    echo->skeleton = t3d_skeleton_create_buffered(
        echo->model, (int)renderer->buffer_count
    );
    if (echo->skeleton.bones == NULL ||
        echo->skeleton.boneMatricesFP == NULL) {
        debugf("[%s] skeleton allocation failed\n", config->debug_name);
        return false;
    }

    for (uint8_t index = 0U;
         index < N64GAME_BATTLE_ECHO_ANIMATION_COUNT;
         ++index) {
        echo->animations[index] = t3d_anim_create(
            echo->model, BATTLE_ECHO_ANIMATION_NAMES[index]
        );
        ++echo->animation_count;
        if (echo->animations[index].file == NULL) {
            debugf("[%s] animation stream open failed: %s\n",
                   config->debug_name,
                   BATTLE_ECHO_ANIMATION_NAMES[index]);
            return false;
        }
        t3d_anim_attach(&echo->animations[index], &echo->skeleton);
        t3d_anim_update(&echo->animations[index], 0.0f);
        t3d_anim_set_looping(
            &echo->animations[index], index == BATTLE_ECHO_ANIMATION_IDLE
        );
        t3d_anim_set_playing(
            &echo->animations[index], index == BATTLE_ECHO_ANIMATION_IDLE
        );
    }
    t3d_anim_set_speed(
        &echo->animations[BATTLE_ECHO_ANIMATION_REPOSITION],
        config->reposition_speed
    );
    t3d_anim_set_speed(
        &echo->animations[BATTLE_ECHO_ANIMATION_HIT], config->hit_speed
    );
    t3d_skeleton_reset(&echo->skeleton);
    t3d_anim_set_time(
        &echo->animations[BATTLE_ECHO_ANIMATION_IDLE], 0.0f
    );
    t3d_anim_update(
        &echo->animations[BATTLE_ECHO_ANIMATION_IDLE], 0.0f
    );
    for (uint32_t index = 0U; index < renderer->buffer_count; ++index) {
        t3d_skeleton_update(&echo->skeleton);
    }

    rspq_block_begin();
    t3d_model_draw_custom(
        echo->model,
        (T3DModelDrawConf){
            .userData = &echo->assets,
            .dynTextureCb = n64game_indexed_render_assets_dynamic_texture_cb,
            .matrices = (const T3DMat4FP *)t3d_segment_placeholder(
                T3D_SEGMENT_SKELETON
            ),
        }
    );
    echo->draw_block = rspq_block_end();
    if (echo->draw_block == NULL) {
        debugf("[%s] draw-block recording failed\n", config->debug_name);
        return false;
    }
    if (!n64game_indexed_render_assets_callback_ok(&echo->assets)) {
        debugf(
            "[%s] dynamic-texture callback failed: callbacks=%u fault=%u\n",
            config->debug_name,
            (unsigned int)echo->assets.successful_body_callbacks,
            echo->assets.callback_fault ? 1U : 0U
        );
        return false;
    }
    echo->last_event_key = UINT32_MAX;
    echo->active_animation = BATTLE_ECHO_ANIMATION_IDLE;
    echo->ready = true;
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
        renderer->floor_vertices != NULL || renderer->annex_ready ||
        renderer->ari_ready || renderer->quarrune.ready ||
        renderer->ayselor.ready ||
        renderer->gyreclast.ready || renderer->kivarrax.ready) {
        return false;
    }

    renderer->floor_vertices = malloc_uncached(sizeof(T3DVertPacked) * 2U);
    renderer->actor_vertices = malloc_uncached(
        sizeof(T3DVertPacked) * 2U * ACTOR_STYLE_COUNT
    );
    renderer->buffer_count = display_get_num_buffers();
    if (renderer->buffer_count == 0U || renderer->buffer_count > UINT16_MAX) {
        n64game_renderer_destroy(renderer);
        return false;
    }
    renderer->actor_matrices = malloc_uncached(
        sizeof(T3DMat4FP) * ACTOR_MATRIX_COUNT * (size_t)renderer->buffer_count
    );
    if (renderer->floor_vertices == NULL || renderer->actor_vertices == NULL ||
        renderer->actor_matrices == NULL) {
        n64game_renderer_destroy(renderer);
        return false;
    }
    const uint16_t up = t3d_vert_pack_normal(&(fm_vec3_t){{0.0f, 1.0f, 0.0f}});
    renderer->floor_vertices[0] = (T3DVertPacked){
        .posA = {-100, -18, -76}, .rgbaA = UINT32_C(0x5D4937FF), .normA = up,
        .posB = {100, -18, -76}, .rgbaB = UINT32_C(0x815D3EFF), .normB = up,
    };
    renderer->floor_vertices[1] = (T3DVertPacked){
        .posA = {100, -18, 76}, .rgbaA = UINT32_C(0x294B50FF), .normA = up,
        .posB = {-100, -18, 76}, .rgbaB = UINT32_C(0x3A5551FF), .normB = up,
    };
    setup_actor_vertices(renderer);
    renderer->viewport = t3d_viewport_create_buffered((uint16_t)renderer->buffer_count);
    if (renderer->viewport._matFP == NULL || !setup_annex(renderer) ||
        !setup_ari(renderer) ||
        !setup_battle_echo(
            renderer, &renderer->quarrune, &QUARRUNE_ASSET_CONFIG
        ) ||
        !setup_battle_echo(
            renderer, &renderer->ayselor, &AYSELOR_ASSET_CONFIG
        ) ||
        !setup_battle_echo(
            renderer, &renderer->gyreclast, &GYRECLAST_ASSET_CONFIG
        ) ||
        !setup_battle_echo(
            renderer, &renderer->kivarrax, &KIVARRAX_ASSET_CONFIG
        )) {
        n64game_renderer_destroy(renderer);
        return false;
    }
    return true;
}

bool n64game_renderer_init(N64GameRenderer *renderer)
{
    if (!n64game_renderer_init_bootstrap(renderer)) {
        return false;
    }
    return n64game_renderer_finish_init(renderer);
}

static void destroy_battle_echo(N64GameBattleEchoRenderer *echo)
{
    if (echo->draw_block != NULL) {
        rspq_block_free(echo->draw_block);
        echo->draw_block = NULL;
    }
    for (uint8_t index = 0U; index < echo->animation_count; ++index) {
        t3d_anim_destroy(&echo->animations[index]);
    }
    echo->animation_count = 0U;
    t3d_skeleton_destroy(&echo->skeleton);
    if (echo->model != NULL) {
        t3d_model_free(echo->model);
        echo->model = NULL;
    }
    if (echo->assets.lifetime != NULL) {
        (void)n64game_indexed_render_assets_unload(&echo->assets);
    }
    *echo = (N64GameBattleEchoRenderer){0};
}

void n64game_renderer_destroy(N64GameRenderer *renderer)
{
    if (renderer == NULL) {
        return;
    }
    rspq_wait();
    destroy_battle_echo(&renderer->kivarrax);
    destroy_battle_echo(&renderer->gyreclast);
    destroy_battle_echo(&renderer->ayselor);
    destroy_battle_echo(&renderer->quarrune);
    if (renderer->annex_draw_block != NULL) {
        rspq_block_free(renderer->annex_draw_block);
        renderer->annex_draw_block = NULL;
    }
    if (renderer->ari_draw_block != NULL) {
        rspq_block_free(renderer->ari_draw_block);
        renderer->ari_draw_block = NULL;
    }
    for (uint8_t index = 0U;
         index < renderer->ari_animation_count;
         ++index) {
        t3d_anim_destroy(&renderer->ari_animations[index]);
    }
    renderer->ari_animation_count = 0U;
    t3d_skeleton_destroy(&renderer->ari_motion_skeleton);
    t3d_skeleton_destroy(&renderer->ari_run_skeleton);
    t3d_skeleton_destroy(&renderer->ari_walk_skeleton);
    t3d_skeleton_destroy(&renderer->ari_idle_skeleton);
    t3d_skeleton_destroy(&renderer->ari_skeleton);
    if (renderer->annex_model != NULL) {
        t3d_model_free(renderer->annex_model);
    }
    if (renderer->ari_model != NULL) {
        t3d_model_free(renderer->ari_model);
    }
    if (renderer->ari_assets.lifetime != NULL) {
        (void)n64game_indexed_render_assets_unload(&renderer->ari_assets);
    }
    t3d_viewport_destroy(&renderer->viewport);
    if (renderer->actor_matrices != NULL) {
        free_uncached(renderer->actor_matrices);
    }
    if (renderer->actor_vertices != NULL) {
        free_uncached(renderer->actor_vertices);
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

static void draw_actor(
    N64GameRenderer *renderer,
    size_t matrix_index,
    size_t style,
    float x,
    float y,
    float z,
    float scale,
    float angle
)
{
    rdpq_mode_tlut(TLUT_NONE);
    rdpq_mode_combiner(RDPQ_COMBINER_SHADE);
    t3d_state_set_drawflags(T3D_FLAG_SHADED | T3D_FLAG_DEPTH);
    const float scales[3] = {scale, scale, scale};
    const float rotations[3] = {0.0f, angle, 0.0f};
    const float translation[3] = {x, y, z};
    const size_t matrix_slot = matrix_index * (size_t)renderer->buffer_count +
        (size_t)renderer->frame_index;
    t3d_mat4fp_from_srt_euler(
        &renderer->actor_matrices[matrix_slot], scales, rotations, translation
    );
    t3d_matrix_push(&renderer->actor_matrices[matrix_slot]);
    t3d_vert_load(&renderer->actor_vertices[style * 2U], 0, 4);
    t3d_matrix_pop(1);
    t3d_tri_draw(0, 1, 2);
    t3d_tri_draw(0, 3, 1);
    t3d_tri_draw(0, 2, 3);
    t3d_tri_draw(1, 3, 2);
    t3d_tri_sync();
}

static uint32_t battle_event_key(const N64GameBattle *battle)
{
    const N64GameBattleEvent *const event = &battle->last_event;
    return ((uint32_t)battle->round << 18) |
        ((uint32_t)battle->queue_cursor << 15) |
        ((uint32_t)event->actor << 13) |
        ((uint32_t)event->move << 10) |
        ((uint32_t)event->target << 2) |
        (event->happened ? UINT32_C(2) : UINT32_C(0)) |
        (event->skipped ? UINT32_C(1) : UINT32_C(0));
}

static bool battle_event_targets_actor(
    const N64GameBattle *battle,
    uint8_t actor
)
{
    const N64GameBattleEvent *const event = &battle->last_event;
    if (event->target == actor) {
        return true;
    }
    if (event->actor >= N64GAME_BATTLE_ACTOR_COUNT ||
        event->hp_delta >= 0) {
        return false;
    }
    if (event->move == N64GAME_MOVE_FINISHER) {
        return battle->actors[event->actor].player_side !=
            battle->actors[actor].player_side;
    }
    const N64GameMoveDef *const move = n64game_move_def(
        battle->actors[event->actor].id, event->move
    );
    return move != NULL &&
        move->target_rule == N64GAME_TARGET_ALL_ENEMIES &&
        battle->actors[event->actor].player_side !=
            battle->actors[actor].player_side;
}

static uint8_t battle_echo_animation_for(
    const N64GameCore *game,
    uint8_t actor
)
{
    const N64GameBattle *const battle = &game->battle;
    const N64GameBattleEvent *const event = &battle->last_event;
    if ((battle->phase != N64GAME_BATTLE_PRESENT &&
         battle->phase != N64GAME_BATTLE_VICTORY &&
         battle->phase != N64GAME_BATTLE_DEFEAT) ||
        !event->happened || event->skipped) {
        return BATTLE_ECHO_ANIMATION_IDLE;
    }
    if (event->hp_delta < 0 && battle_event_targets_actor(battle, actor)) {
        return BATTLE_ECHO_ANIMATION_HIT;
    }
    if (event->actor == actor) {
        return BATTLE_ECHO_ANIMATION_REPOSITION;
    }
    return BATTLE_ECHO_ANIMATION_IDLE;
}

static void set_battle_echo_animation(
    N64GameBattleEchoRenderer *echo,
    uint8_t animation
)
{
    assertf(
        animation < N64GAME_BATTLE_ECHO_ANIMATION_COUNT,
        "Battle Echoform animation index is invalid"
    );
    for (uint8_t index = 0U;
         index < N64GAME_BATTLE_ECHO_ANIMATION_COUNT;
         ++index) {
        t3d_anim_set_playing(&echo->animations[index], false);
    }
    T3DAnim *const selected = &echo->animations[animation];
    t3d_anim_set_time(selected, 0.0f);
    t3d_anim_set_looping(
        selected, animation == BATTLE_ECHO_ANIMATION_IDLE
    );
    t3d_anim_set_playing(selected, true);
    t3d_anim_update(selected, 0.0f);
    echo->active_animation = animation;
}

static void update_battle_echo_idle_pose(N64GameBattleEchoRenderer *echo)
{
    assertf(echo->ready, "Battle Echoform renderer is not ready");
    if (echo->active_animation != BATTLE_ECHO_ANIMATION_IDLE) {
        set_battle_echo_animation(echo, BATTLE_ECHO_ANIMATION_IDLE);
    }
    t3d_anim_update(
        &echo->animations[BATTLE_ECHO_ANIMATION_IDLE], 1.0f / 30.0f
    );
    t3d_skeleton_update(&echo->skeleton);
    echo->last_event_key = UINT32_MAX;
}

static void update_battle_echo_pose(
    N64GameBattleEchoRenderer *echo,
    const N64GameCore *game,
    uint8_t actor
)
{
    assertf(echo->ready, "Battle Echoform renderer is not ready");
    const uint32_t event_key = battle_event_key(&game->battle);
    if (event_key != echo->last_event_key) {
        set_battle_echo_animation(
            echo, battle_echo_animation_for(game, actor)
        );
        echo->last_event_key = event_key;
    }

    T3DAnim *active = &echo->animations[echo->active_animation];
    t3d_anim_update(active, 1.0f / 30.0f);
    if (echo->active_animation != BATTLE_ECHO_ANIMATION_IDLE &&
        !t3d_anim_is_playing(active)) {
        set_battle_echo_animation(echo, BATTLE_ECHO_ANIMATION_IDLE);
    }
    t3d_skeleton_update(&echo->skeleton);
}

static void draw_battle_echo(
    N64GameRenderer *renderer,
    N64GameBattleEchoRenderer *echo,
    size_t matrix_index,
    float x,
    float y,
    float z,
    float scale,
    float angle
)
{
    assertf(echo->ready, "Battle Echoform renderer is not ready");
    const float scales[3] = {scale, scale, scale};
    const float rotations[3] = {0.0f, angle, 0.0f};
    const float translation[3] = {x, y, z};
    const size_t matrix_slot = matrix_index * (size_t)renderer->buffer_count +
        (size_t)renderer->frame_index;
    t3d_mat4fp_from_srt_euler(
        &renderer->actor_matrices[matrix_slot], scales, rotations, translation
    );
    t3d_skeleton_use(&echo->skeleton);
    t3d_matrix_push(&renderer->actor_matrices[matrix_slot]);
    rspq_block_run(echo->draw_block);
    t3d_matrix_pop(1);
}

static float clamp_unit(float value)
{
    if (value < 0.0f) {
        return 0.0f;
    }
    return value > 1.0f ? 1.0f : value;
}

static void update_ari_pose(
    N64GameRenderer *renderer,
    const N64GameCore *game
)
{
    assertf(renderer->ari_ready, "Ari renderer is not ready");
    float velocity_x = (float)game->player_velocity_x_q8;
    float velocity_z = (float)game->player_velocity_z_q8;
    if (game->dialogue != N64GAME_DIALOGUE_NONE ||
        game->menu != N64GAME_MENU_CLOSED) {
        velocity_x = 0.0f;
        velocity_z = 0.0f;
    }
    const float speed = sqrtf(
        velocity_x * velocity_x + velocity_z * velocity_z
    );
    const float locomotion_blend = clamp_unit(speed / 256.0f);
    const float run_blend = clamp_unit((speed - 384.0f) / 256.0f);
    t3d_anim_set_speed(
        &renderer->ari_animations[ARI_ANIMATION_WALK],
        0.75f + clamp_unit(speed / 384.0f) * 0.35f
    );
    t3d_anim_set_speed(
        &renderer->ari_animations[ARI_ANIMATION_RUN],
        0.75f + clamp_unit(speed / 640.0f) * 0.45f
    );
    for (uint8_t index = 0U;
         index < N64GAME_ARI_RUNTIME_ANIMATION_COUNT;
         ++index) {
        t3d_anim_update(&renderer->ari_animations[index], 1.0f / 30.0f);
    }
    t3d_skeleton_blend(
        &renderer->ari_motion_skeleton,
        &renderer->ari_walk_skeleton,
        &renderer->ari_run_skeleton,
        run_blend
    );
    t3d_skeleton_blend(
        &renderer->ari_skeleton,
        &renderer->ari_idle_skeleton,
        &renderer->ari_motion_skeleton,
        locomotion_blend
    );
    t3d_skeleton_update(&renderer->ari_skeleton);

    if (speed > 32.0f) {
        const float target_angle = atan2f(velocity_x, velocity_z);
        renderer->ari_facing_angle = t3d_lerp_angle(
            renderer->ari_facing_angle, target_angle, 0.32f
        );
    }
}

static void draw_ari(
    N64GameRenderer *renderer,
    size_t matrix_index,
    float x,
    float y,
    float z,
    float scale
)
{
    assertf(renderer->ari_ready, "Ari renderer is not ready");
    const float scales[3] = {scale, scale, scale};
    const float rotations[3] = {0.0f, -renderer->ari_facing_angle, 0.0f};
    const float translation[3] = {x, y, z};
    const size_t matrix_slot = matrix_index * (size_t)renderer->buffer_count +
        (size_t)renderer->frame_index;
    t3d_mat4fp_from_srt_euler(
        &renderer->actor_matrices[matrix_slot], scales, rotations, translation
    );
    t3d_skeleton_use(&renderer->ari_skeleton);
    t3d_matrix_push(&renderer->actor_matrices[matrix_slot]);
    rspq_block_run(renderer->ari_draw_block);
    t3d_matrix_pop(1);
}

static void draw_annex_model(
    N64GameRenderer *renderer,
    float x,
    float y,
    float z,
    float scale,
    float angle
)
{
    assertf(renderer->annex_ready, "Annex renderer is not ready");
    const float scales[3] = {scale, scale, scale};
    const float rotations[3] = {0.0f, angle, 0.0f};
    const float translation[3] = {x, y, z};
    const size_t matrix_slot = ANNEX_MATRIX_INDEX *
        (size_t)renderer->buffer_count + (size_t)renderer->frame_index;
    t3d_mat4fp_from_srt_euler(
        &renderer->actor_matrices[matrix_slot], scales, rotations, translation
    );
    t3d_matrix_push(&renderer->actor_matrices[matrix_slot]);
    rspq_block_run(renderer->annex_draw_block);
    t3d_matrix_pop(1);
}

static void draw_annex_sector_model(
    N64GameRenderer *renderer,
    N64GameAnnexSector sector
)
{
    float x = 0.0f;
    float z = -6.0f;
    float scale = 0.08f;
    float angle = 0.0f;
    switch (sector) {
    case N64GAME_ANNEX_ATRIUM:
        break;
    case N64GAME_ANNEX_SIMULATION:
        x = -56.0f;
        z = -4.0f;
        scale = 0.055f;
        angle = T3D_DEG_TO_RAD(90.0f);
        break;
    case N64GAME_ANNEX_WORKSHOP:
        x = 52.0f;
        z = 7.0f;
        scale = 0.05f;
        angle = T3D_DEG_TO_RAD(-90.0f);
        break;
    case N64GAME_ANNEX_OVERLOOK:
        x = 76.0f;
        z = 50.0f;
        scale = 0.045f;
        angle = T3D_DEG_TO_RAD(180.0f);
        break;
    case N64GAME_ANNEX_SECTOR_COUNT:
        return;
    }
    draw_annex_model(renderer, x, -18.0f, z, scale, angle);
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
    case N64GAME_QUEST_RETRIEVE_RELAY: return "RETRIEVE THE FIELD RELAY";
    case N64GAME_QUEST_RETURN_TO_SERA: return "RETURN TO SERA";
    case N64GAME_QUEST_RESONANCE_TRIAL: return "COMPLETE THE RESONANCE TRIAL";
    case N64GAME_QUEST_BEACON_OVERLOOK: return "TRACE THE SIGNAL AT THE OVERLOOK";
    case N64GAME_QUEST_COMPLETE: return "OPENING CHAPTER COMPLETE";
    }
    return "";
}

static const char *dialogue_speaker(N64GameDialogue dialogue)
{
    switch (dialogue) {
    case N64GAME_DIALOGUE_SERA_INTRO:
    case N64GAME_DIALOGUE_SERA_TRIAL:
    case N64GAME_DIALOGUE_BATTLE_VICTORY:
    case N64GAME_DIALOGUE_BEACON_HOOK:
        return "DR. SERA VENN";
    case N64GAME_DIALOGUE_TAVI_OPTIONAL:
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
    static const char *const SERA_INTRO[] = {
        "The Annex heard your Resonance before you reached the floor.",
        "Quarrune and Ayselor are already matching your rhythm.",
        "Bring the Field Relay from the east bench. We will calibrate together.",
    };
    static const char *const RELAY[] = {
        "MERIDIAN FIELD RELAY / LINK ESTABLISHED",
        "PARTY, MESSAGES, RESONANCE, AND SAVE CHANNELS ARE READY.",
    };
    static const char *const SERA_TRIAL[] = {
        "Good. The Relay needs one live pattern before it can hear the desert.",
        "Take your pair into the chamber. Let the true pattern answer.",
    };
    static const char *const TAVI[] = {
        "The west antenna keeps pointing at empty sky.",
        "Sera says instruments do not get nervous. I think this one does.",
    };
    static const char *const VICTORY[] = {
        "There. Quarrune anchors; Ayselor carries. The Relay understands you now.",
        "A signal just crossed the old Solace band. Meet me at the overlook.",
    };
    static const char *const BEACON[] = {
        "That signature belongs to Solace.",
        "It vanished three nights ago. This beacon should not be moving.",
        "Something enormous is answering from beneath the storm.",
        "We follow at first light.",
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
    case N64GAME_DIALOGUE_SERA_INTRO: return SERA_INTRO[page];
    case N64GAME_DIALOGUE_RELAY: return RELAY[page];
    case N64GAME_DIALOGUE_SERA_TRIAL: return SERA_TRIAL[page];
    case N64GAME_DIALOGUE_TAVI_OPTIONAL: return TAVI[page];
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
    text_at(18.0f, 179.0f, STYLE_ACCENT, 280.0f, dialogue_speaker(game->dialogue));
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
        if (item == 2U && !game->relay_unlocked) {
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
    case N64GAME_QUEST_RETRIEVE_RELAY:
        return "SERA: Retrieve the Relay from the east workshop bench.";
    case N64GAME_QUEST_RETURN_TO_SERA:
        return "RELAY: Link established. Return to Sera for calibration.";
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

static void draw_save_page(const N64GameCore *game)
{
    char timing[48];
    char state[48];
    char coverage[48];
    n64game_core_certification_summary(
        game,
        timing, sizeof(timing),
        state, sizeof(state),
        coverage, sizeof(coverage)
    );

    panel(38, 48, 282, 204);
    centered(58.0f, STYLE_ACCENT, "SAVE RESONANCE FILE");
    text_at(
        54.0f, 84.0f, STYLE_TEXT, 212.0f,
        "Record your safe Annex checkpoint, objectives, and Field Relay discoveries."
    );
    text_at(54.0f, 121.0f, STYLE_ACCENT, 212.0f, timing);
    text_at(54.0f, 137.0f, STYLE_MUTED, 212.0f, state);
    text_at(54.0f, 153.0f, STYLE_MUTED, 212.0f, coverage);
    text_at(54.0f, 174.0f, STYLE_WARNING, 212.0f, "A  SAVE");
    text_at(54.0f, 188.0f, STYLE_MUTED, 212.0f, "B  BACK");
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
        draw_save_page(game);
        break;
    case N64GAME_MENU_HELP:
        draw_help_page();
        break;
    case N64GAME_MENU_POST_CHAPTER_ROOT:
        draw_post_chapter_root(game);
        break;
    }
}

static void draw_annex(N64GameRenderer *renderer, const N64GameCore *game)
{
    const float player_x = (float)game->player_x_q8 / 256.0f;
    const float player_z = (float)game->player_z_q8 / 256.0f;
    const fm_vec3_t camera = {{player_x, 62.0f, player_z + 88.0f}};
    const fm_vec3_t target = {{player_x, -4.0f, player_z - 6.0f}};
    begin_world_render(renderer, &camera, &target);
    draw_annex_sector_model(renderer, game->annex_sector);
    update_ari_pose(renderer, game);
    const float angle = (float)game->scene_ticks * 0.018f;
    draw_ari(renderer, 0U, player_x, -18.0f, player_z, 0.27f);
    draw_actor(renderer, 1U, 5U, -38.0f, -1.0f, -8.0f, 0.88f, 0.3f);
    draw_actor(renderer, 2U, 7U, 5.0f, -2.0f, -34.0f, 0.68f, -0.4f);
    update_battle_echo_idle_pose(&renderer->quarrune);
    draw_battle_echo(
        renderer, &renderer->quarrune, 3U,
        52.0f, -15.75f, 18.0f, 0.50f, 0.12f
    );
    draw_actor(renderer, 4U, 6U, 74.0f, -6.0f, 40.0f, 0.72f, -angle);

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
}

static const char *echo_name(uint8_t actor)
{
    static const char *const NAMES[] = {"QUARRUNE", "AYSELOR", "GYRECLAST", "KIVARRAX"};
    return actor < 4U ? NAMES[actor] : "";
}

static void draw_battle_status(const N64GameCore *game)
{
    const N64GameBattle *const battle = &game->battle;
    for (uint8_t actor = 0U; actor < 4U; ++actor) {
        const bool player = actor < 2U;
        const int x = player ? 8 + (int)actor * 112 : 96 + ((int)actor - 2) * 108;
        const int y = player ? 112 : 8;
        panel(x, y, x + 104, y + 29);
        text_at((float)(x + 5), (float)(y + 5), STYLE_TEXT, 94.0f, echo_name(actor));
        hp_bar(x + 5, y + 18, 92, battle->actors[actor].hp, battle->actors[actor].max_hp);
        if (game->battle_selecting_target && game->battle_target_cursor == actor) {
            fill_rect(x, y, x + 4, y + 29, RGBA32(221, 97, 163, 255));
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
            const N64GameMoveDef *const definition = n64game_move_def(
                battle->actors[actor].id, move
            );
            const uint8_t style = !game->battle_selecting_target &&
                game->battle_move_cursor == move ? STYLE_WARNING : STYLE_TEXT;
            text_at(18.0f, 168.0f + (float)move * 13.0f, style, 150.0f, definition->name);
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
                (void)snprintf(message, sizeof(message), "%s CANNOT ACT", echo_name(event->actor));
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
                text_at(18.0f, 184.0f, STYLE_WARNING, 150.0f, "AFFINITY ADVANTAGE");
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
        text_at(192.0f, 194.0f, STYLE_WARNING, 110.0f, "SELECT TARGET");
        text_at(192.0f, 214.0f, STYLE_MUTED, 110.0f, "A CONFIRM / B BACK");
    } else {
        text_at(192.0f, 194.0f, STYLE_TEXT, 110.0f, "D-PAD  MOVE\nA  CHOOSE\nB  BACK");
    }
}

static void draw_battle(N64GameRenderer *renderer, const N64GameCore *game)
{
    const fm_vec3_t camera = {{0.0f, 56.0f, 112.0f}};
    const fm_vec3_t target = {{0.0f, -4.0f, 0.0f}};
    begin_world_render(renderer, &camera, &target);
    draw_annex_model(renderer, 0.0f, -18.0f, -52.0f, 0.09f, 0.0f);
    static const float POSITIONS[4][3] = {
        {-31.0f, -2.0f, -34.0f}, {26.0f, 0.0f, -30.0f},
        {-28.0f, -2.0f, -76.0f}, {31.0f, -1.0f, -70.0f},
    };
    update_battle_echo_pose(&renderer->quarrune, game, 0U);
    update_battle_echo_pose(&renderer->ayselor, game, 1U);
    update_battle_echo_pose(&renderer->gyreclast, game, 2U);
    update_battle_echo_pose(&renderer->kivarrax, game, 3U);
    if (game->battle.actors[0].hp > 0 ||
        renderer->quarrune.active_animation == BATTLE_ECHO_ANIMATION_HIT) {
        draw_battle_echo(
            renderer, &renderer->quarrune, 0U,
            POSITIONS[0][0], -15.50f, POSITIONS[0][2],
            0.50f, 0.10f
        );
    }
    if (game->battle.actors[1].hp > 0 ||
        renderer->ayselor.active_animation == BATTLE_ECHO_ANIMATION_HIT) {
        draw_battle_echo(
            renderer, &renderer->ayselor, 1U,
            POSITIONS[1][0], -18.0f, POSITIONS[1][2],
            0.42f, T3D_DEG_TO_RAD(-18.0f)
        );
    }
    if (game->battle.actors[2].hp > 0 ||
        renderer->gyreclast.active_animation == BATTLE_ECHO_ANIMATION_HIT) {
        draw_battle_echo(
            renderer, &renderer->gyreclast, 2U,
            POSITIONS[2][0], -18.0f, POSITIONS[2][2],
            0.72f, -0.08f
        );
    }
    if (game->battle.actors[3].hp > 0 ||
        renderer->kivarrax.active_animation == BATTLE_ECHO_ANIMATION_HIT) {
        draw_battle_echo(
            renderer, &renderer->kivarrax, 3U,
            POSITIONS[3][0], -18.0f, POSITIONS[3][2],
            0.46f, 0.08f
        );
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
    clear_2d(RGBA32(4, 11, 19, 255));
    fill_rect(0, 0, 320, 5, RGBA32(184, 67, 151, 255));
    fill_rect(0, 235, 320, 240, RGBA32(24, 82, 91, 255));
    centered(24.0f, STYLE_ACCENT, "N64GAME");
    centered(43.0f, STYLE_TEXT, "MERIDIAN SIGNAL LAB");

    /* A small relay beacon reads clearly at native 320x240 without a texture. */
    fill_rect(156, 72, 164, 108, RGBA32(34, 91, 101, 255));
    fill_rect(151, 78, 169, 102, RGBA32(12, 31, 41, 255));
    fill_rect(156, 83, 164, 97, RGBA32(91, 231, 204, 255));
    fill_rect(146, 88, 151, 92, RGBA32(57, 147, 151, 255));
    fill_rect(169, 88, 174, 92, RGBA32(57, 147, 151, 255));
    fill_rect(137, 86, 142, 94, RGBA32(29, 82, 93, 255));
    fill_rect(178, 86, 183, 94, RGBA32(29, 82, 93, 255));

    panel(42, 126, 278, 187);
    centered(139.0f, STYLE_MUTED, STATUS[(size_t)stage]);
    for (int segment = 0; segment < 4; ++segment) {
        const int x0 = 68 + segment * 47;
        const color_t color = segment <= (int)stage ?
            RGBA32(87, 226, 203, 255) : RGBA32(24, 53, 63, 255);
        fill_rect(x0, 162, x0 + 39, 169, color);
    }
    centered(203.0f, STYLE_MUTED, "RESONANCE LINK / ORIGINAL N64 BUILD");
    rdpq_detach_show();
}

static void draw_opening(const N64GameCore *game, bool continue_available)
{
    clear_2d(RGBA32(6, 15, 24, 255));
    if (game->scene == N64GAME_SCENE_BOOT) {
        centered(72.0f, STYLE_ACCENT, "N64GAME");
        centered(96.0f, STYLE_TEXT, "MERIDIAN SIGNAL LAB");
        const int phase = (int)(game->scene_ticks % 20U);
        const int pulse = phase <= 10 ? phase : 20 - phase;
        fill_rect(154, 126, 166, 138, RGBA32(87, 226, 203, 255));
        fill_rect(136 - pulse, 130, 148 - pulse, 134, RGBA32(45, 126, 132, 255));
        fill_rect(172 + pulse, 130, 184 + pulse, 134, RGBA32(45, 126, 132, 255));
        centered(150.0f, STYLE_MUTED, "AN ORIGINAL N64 CHAPTER");
    } else {
        fill_rect(18, 18, 302, 222, RGBA32(22, 32, 44, 255));
        fill_rect(18, 18, 302, 22, RGBA32(183, 72, 154, 255));
        centered(84.0f, STYLE_WARNING, "INSERT CUTSCENE HERE");
        centered(110.0f, STYLE_TEXT, "SOLACE INTERCEPTION / 4:3 PLAYBACK SLOT");
        centered(
            178.0f,
            STYLE_MUTED,
            continue_available ? "START CONTINUE / A NEW FILE" : "A OR START TO BEGIN"
        );
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
    char player_line[40];
    const char *const save_state = save_busy ? "FINALIZING SAVE" :
        (save_available ? "RESONANCE FILE SAVED" : "PROGRESS VOLATILE");
    (void)snprintf(player_line, sizeof(player_line), "%s / %s",
                   game->player_name, save_state);
    centered(151.0f, STYLE_MUTED, player_line);
    centered(165.0f, STYLE_TEXT, "THE STORM IS ANSWERING.");
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
    if (save_busy) {
        panel(238, 214, 314, 234);
        text_at(246.0f, 221.0f, STYLE_ACCENT, 62.0f, "SAVING");
    } else if (!save_available) {
        text_at(218.0f, 224.0f, STYLE_WARNING, 96.0f, "SAVE UNAVAILABLE");
    }
    if (!controller_connected) {
        panel(42, 91, 278, 149);
        centered(104.0f, STYLE_WARNING, "CONTROLLER DISCONNECTED");
        centered(126.0f, STYLE_TEXT, "RECONNECT CONTROLLER 1");
    }
    rdpq_detach_show();
}
