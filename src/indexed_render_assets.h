#ifndef N64GAME_INDEXED_RENDER_ASSETS_H
#define N64GAME_INDEXED_RENDER_ASSETS_H

#include <stdbool.h>
#include <stdint.h>

#include <libdragon.h>

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wconversion"
#include <t3d/t3dmodel.h>
#pragma GCC diagnostic pop

typedef struct N64GameIndexedRenderAssetsLifetime
    N64GameIndexedRenderAssetsLifetime;

typedef struct {
    const char *body_sprite_path;
    const char *blob_shadow_sprite_path;
    uint32_t body_top_reference;
    uint32_t body_bottom_reference;
    uint16_t minimum_body_palette_colors;
} N64GameIndexedRenderAssetsConfig;

typedef struct {
    sprite_t *body_sprite;
    sprite_t *blob_shadow_sprite;
    surface_t body_regions[2];
    N64GameIndexedRenderAssetsLifetime *lifetime;
    uint32_t body_references[2];
    int body_palette_colors;
    uint8_t successful_body_callbacks;
    bool ready;
    bool callback_fault;
} N64GameIndexedRenderAssets;

/*
 * Loads one reviewed 64x64 CI8 body atlas and one 32x32 IA8 blob shadow.
 * The CI8 body is exposed as two zero-copy 64x32 regions because the complete
 * atlas plus its TLUT does not fit in TMEM. `assets` must be zero-initialized.
 */
bool n64game_indexed_render_assets_load(
    N64GameIndexedRenderAssets *assets,
    const N64GameIndexedRenderAssetsConfig *config
);

void n64game_indexed_render_assets_dynamic_texture_cb(
    void *user_data,
    const T3DMaterial *material,
    rdpq_texparms_t *tile_parameters,
    rdpq_tile_t tile
);

bool n64game_indexed_render_assets_upload_blob_shadow(
    N64GameIndexedRenderAssets *assets,
    rdpq_tile_t tile,
    const rdpq_texparms_t *tile_parameters
);

bool n64game_indexed_render_assets_callback_ok(
    const N64GameIndexedRenderAssets *assets
);

/*
 * Stops new use immediately. A false result means sprite release is safely
 * deferred until every recorded RSPQ block using the helper has been freed.
 */
bool n64game_indexed_render_assets_unload(
    N64GameIndexedRenderAssets *assets
);

#endif
