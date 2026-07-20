#ifndef N64GAME_PLAYER_RENDER_ASSETS_H
#define N64GAME_PLAYER_RENDER_ASSETS_H

#include <stdbool.h>
#include <stdint.h>

#include <libdragon.h>

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wconversion"
#include <t3d/t3dmodel.h>
#pragma GCC diagnostic pop

#define PLAYER_BODY_TOP_REFERENCE UINT32_C(0x41524930)
#define PLAYER_BODY_BOTTOM_REFERENCE UINT32_C(0x41524931)

typedef struct PlayerRenderAssetsLifetime PlayerRenderAssetsLifetime;

typedef struct {
    sprite_t *body_sprite;
    surface_t body_regions[2];
    int body_palette_colors;
    PlayerRenderAssetsLifetime *lifetime;
    uint8_t successful_body_callbacks;
    bool ready;
    bool callback_fault;
} PlayerRenderAssets;

/* `assets` must be zero-initialized. Loading an already-live instance fails. */
bool player_render_assets_load(PlayerRenderAssets *assets);

void player_render_assets_dynamic_texture_cb(
    void *user_data,
    const T3DMaterial *material,
    rdpq_texparms_t *tile_parameters,
    rdpq_tile_t tile
);

bool player_render_assets_callback_ok(const PlayerRenderAssets *assets);

/*
 * Stops new use immediately. Returns true when storage was released before
 * returning. Returns false when release was safely deferred until every RSPQ
 * block recorded through this helper is freed. The caller must still obey
 * rspq_block_free's rule that a block cannot be freed while queued/running.
 */
bool player_render_assets_unload(PlayerRenderAssets *assets);

#endif
