#ifndef N64GAME_RENDER_H
#define N64GAME_RENDER_H

#include <stdbool.h>
#include <stdint.h>

#include <libdragon.h>

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wconversion"
#include <t3d/t3d.h>
#include <t3d/t3danim.h>
#include <t3d/t3dskeleton.h>
#pragma GCC diagnostic pop

#include "n64game_core.h"
#include "player_render_assets.h"
#include "quarrune_render_assets.h"
#include "support_echo_renderer.h"

typedef struct {
    T3DModel *model;
    T3DMat4FP *matrices;
    rspq_block_t *draw_block;
    uint32_t matrix_count;
    uint32_t buffer_count;
    bool ready;
} N64GameStaticModel;

typedef struct {
    rdpq_font_t *font;
    T3DViewport viewport;
    T3DVertPacked *floor_vertices;
    T3DVertPacked *actor_vertices;
    T3DMat4FP *actor_matrices;
    N64GameStaticModel annex_kit;
    T3DModel *player_model;
    T3DSkeleton player_skeleton;
    T3DSkeleton player_idle_pose;
    T3DSkeleton player_walk_pose;
    T3DSkeleton player_run_pose;
    T3DAnim player_idle_anim;
    T3DAnim player_walk_anim;
    T3DAnim player_run_anim;
    PlayerRenderAssets player_assets;
    rspq_block_t *player_draw_block;
    T3DModel *quarrune_model;
    T3DSkeleton quarrune_skeleton;
    QuarruneRenderAssets quarrune_assets;
    rspq_block_t *quarrune_draw_block;
    SupportEchoRenderer support_echoes;
    float player_yaw;
    uint32_t buffer_count;
    uint32_t frame_index;
    N64GameAnnexSector annex_camera_sector;
    uint8_t annex_camera_fade_ticks;
    int8_t annex_camera_boom_side;
    bool font_registered;
    bool player_ready;
    bool quarrune_ready;
    bool support_echoes_ready;
    bool annex_camera_ready;
} N64GameRenderer;

typedef enum {
    N64GAME_LOADING_RUNTIME = 0,
    N64GAME_LOADING_ANNEX_ASSETS,
    N64GAME_LOADING_SAVE_DATA,
    N64GAME_LOADING_READY,
} N64GameLoadingStage;

bool n64game_static_model_load(
    N64GameStaticModel *asset,
    const char *rom_path,
    uint32_t matrix_count,
    uint32_t buffer_count
);
bool n64game_static_model_draw(
    N64GameStaticModel *asset,
    uint32_t matrix_index,
    uint32_t frame_index,
    const float scales[3],
    const float rotations[3],
    const float translation[3]
);
void n64game_static_model_free(N64GameStaticModel *asset);

bool n64game_renderer_init_bootstrap(N64GameRenderer *renderer);
bool n64game_renderer_finish_init(N64GameRenderer *renderer);
bool n64game_renderer_init(N64GameRenderer *renderer);
void n64game_renderer_destroy(N64GameRenderer *renderer);
void n64game_renderer_draw_loading(
    const N64GameRenderer *renderer,
    N64GameLoadingStage stage
);
void n64game_renderer_draw(
    N64GameRenderer *renderer,
    const N64GameCore *game,
    bool save_busy,
    bool save_available,
    bool continue_available,
    bool controller_connected
);

#endif
