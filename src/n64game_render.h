#ifndef N64GAME_RENDER_H
#define N64GAME_RENDER_H

#include <stdbool.h>

#include <libdragon.h>

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wconversion"
#include <t3d/t3d.h>
#pragma GCC diagnostic pop

#include "n64game_core.h"

typedef struct {
    rdpq_font_t *font;
    T3DViewport viewport;
    T3DVertPacked *floor_vertices;
    T3DVertPacked *actor_vertices;
    T3DMat4FP *actor_matrices;
    uint32_t buffer_count;
    uint32_t frame_index;
} N64GameRenderer;

bool n64game_renderer_init(N64GameRenderer *renderer);
void n64game_renderer_draw(
    N64GameRenderer *renderer,
    const N64GameCore *game,
    bool save_busy,
    bool save_available,
    bool continue_available,
    bool controller_connected
);

#endif
