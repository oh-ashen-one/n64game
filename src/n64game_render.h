#ifndef N64GAME_RENDER_H
#define N64GAME_RENDER_H

#include <stdbool.h>

#include <libdragon.h>

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wconversion"
#include <t3d/t3d.h>
#include <t3d/t3dskeleton.h>
#pragma GCC diagnostic pop

#include "n64game_core.h"
#include "quarrune_render_assets.h"

typedef struct {
    rdpq_font_t *font;
    T3DViewport viewport;
    T3DVertPacked *floor_vertices;
    T3DVertPacked *actor_vertices;
    T3DMat4FP *actor_matrices;
    T3DModel *quarrune_model;
    T3DSkeleton quarrune_skeleton;
    QuarruneRenderAssets quarrune_assets;
    rspq_block_t *quarrune_draw_block;
    uint32_t buffer_count;
    uint32_t frame_index;
    bool font_registered;
    bool quarrune_ready;
} N64GameRenderer;

bool n64game_renderer_init(N64GameRenderer *renderer);
void n64game_renderer_destroy(N64GameRenderer *renderer);
void n64game_renderer_draw(
    N64GameRenderer *renderer,
    const N64GameCore *game,
    bool save_busy,
    bool save_available,
    bool continue_available,
    bool controller_connected
);

#endif
