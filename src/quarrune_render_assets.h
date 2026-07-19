#ifndef N64GAME_QUARRUNE_RENDER_ASSETS_H
#define N64GAME_QUARRUNE_RENDER_ASSETS_H

#include <stdbool.h>
#include <stdint.h>

#include <libdragon.h>

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wconversion"
#include <t3d/t3dmodel.h>
#pragma GCC diagnostic pop

#define QUARRUNE_BODY_TOP_REFERENCE UINT32_C(0x51554230)
#define QUARRUNE_BODY_BOTTOM_REFERENCE UINT32_C(0x51554231)

typedef struct QuarruneRenderAssetsLifetime QuarruneRenderAssetsLifetime;

typedef struct {
    sprite_t *body_sprite;
    sprite_t *blob_shadow_sprite;
    surface_t body_regions[2];
    int body_palette_colors;
    QuarruneRenderAssetsLifetime *lifetime;
    uint8_t successful_body_callbacks;
    bool ready;
    bool callback_fault;
} QuarruneRenderAssets;

/* `assets` must be zero-initialized. Loading an already-live instance fails. */
bool quarrune_render_assets_load(QuarruneRenderAssets *assets);

void quarrune_render_assets_dynamic_texture_cb(
    void *user_data,
    const T3DMaterial *material,
    rdpq_texparms_t *tile_parameters,
    rdpq_tile_t tile
);

bool quarrune_render_assets_upload_blob_shadow(
    QuarruneRenderAssets *assets,
    rdpq_tile_t tile,
    const rdpq_texparms_t *tile_parameters
);

bool quarrune_render_assets_callback_ok(const QuarruneRenderAssets *assets);

/*
 * Stops new use immediately. Returns true when storage was released before
 * returning. Returns false when release was safely deferred until every RSPQ
 * block recorded through these helpers is freed. The caller must still obey
 * rspq_block_free's rule that a block cannot be freed while queued/running.
 */
bool quarrune_render_assets_unload(QuarruneRenderAssets *assets);

#endif
