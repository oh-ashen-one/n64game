#ifndef N64GAME_RENDER_H
#define N64GAME_RENDER_H

#include <stdbool.h>

#include <libdragon.h>

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wconversion"
#include <t3d/t3d.h>
#include <t3d/t3danim.h>
#include <t3d/t3dskeleton.h>
#pragma GCC diagnostic pop

#include "indexed_render_assets.h"
#include "n64game_core.h"
#include "quarrune_render_assets.h"

#define N64GAME_ARI_RUNTIME_ANIMATION_COUNT 3

typedef struct {
    rdpq_font_t *font;
    T3DViewport viewport;
    T3DVertPacked *floor_vertices;
    T3DVertPacked *actor_vertices;
    T3DMat4FP *actor_matrices;
    T3DModel *annex_model;
    rspq_block_t *annex_draw_block;
    T3DModel *ari_model;
    T3DSkeleton ari_skeleton;
    T3DSkeleton ari_idle_skeleton;
    T3DSkeleton ari_walk_skeleton;
    T3DSkeleton ari_run_skeleton;
    T3DSkeleton ari_motion_skeleton;
    T3DAnim ari_animations[N64GAME_ARI_RUNTIME_ANIMATION_COUNT];
    N64GameIndexedRenderAssets ari_assets;
    rspq_block_t *ari_draw_block;
    T3DModel *quarrune_model;
    T3DSkeleton quarrune_skeleton;
    QuarruneRenderAssets quarrune_assets;
    rspq_block_t *quarrune_draw_block;
    uint32_t buffer_count;
    uint32_t frame_index;
    uint8_t ari_animation_count;
    float ari_facing_angle;
    bool font_registered;
    bool annex_ready;
    bool ari_ready;
    bool quarrune_ready;
} N64GameRenderer;

typedef enum {
    N64GAME_LOADING_RUNTIME = 0,
    N64GAME_LOADING_ANNEX_ASSETS,
    N64GAME_LOADING_SAVE_DATA,
    N64GAME_LOADING_READY,
} N64GameLoadingStage;

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
