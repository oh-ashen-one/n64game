#ifndef N64GAME_SUPPORT_ECHO_RENDER_ASSETS_H
#define N64GAME_SUPPORT_ECHO_RENDER_ASSETS_H

#include <stdbool.h>
#include <stdint.h>

#include <libdragon.h>

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wconversion"
#include <t3d/t3dmodel.h>
#pragma GCC diagnostic pop

#define AYSELOR_BODY_TOP_REFERENCE UINT32_C(0x41595330)
#define AYSELOR_BODY_BOTTOM_REFERENCE UINT32_C(0x41595331)
#define GYRECLAST_BODY_TOP_REFERENCE UINT32_C(0x47595230)
#define GYRECLAST_BODY_BOTTOM_REFERENCE UINT32_C(0x47595231)
#define KIVARRAX_BODY_TOP_REFERENCE UINT32_C(0x4B495630)
#define KIVARRAX_BODY_BOTTOM_REFERENCE UINT32_C(0x4B495631)

typedef enum {
    N64GAME_SUPPORT_ECHO_AYSELOR = 0,
    N64GAME_SUPPORT_ECHO_GYRECLAST,
    N64GAME_SUPPORT_ECHO_KIVARRAX,
    N64GAME_SUPPORT_ECHO_COUNT,
} N64GameSupportEchoKind;

typedef struct SupportEchoRenderAssetsLifetime SupportEchoRenderAssetsLifetime;

typedef struct {
    sprite_t *body_sprite;
    sprite_t *blob_shadow_sprite;
    surface_t body_regions[2];
    uint32_t body_references[2];
    int body_palette_colors;
    SupportEchoRenderAssetsLifetime *lifetime;
    uint8_t successful_body_callbacks;
    bool ready;
    bool callback_fault;
} SupportEchoRenderAssets;

/* `assets` must be zero-initialized. Loading an already-live instance fails. */
bool support_echo_render_assets_load(
    SupportEchoRenderAssets *assets,
    N64GameSupportEchoKind kind
);

void support_echo_render_assets_dynamic_texture_cb(
    void *user_data,
    const T3DMaterial *material,
    rdpq_texparms_t *tile_parameters,
    rdpq_tile_t tile
);

bool support_echo_render_assets_upload_blob_shadow(
    SupportEchoRenderAssets *assets,
    rdpq_tile_t tile,
    const rdpq_texparms_t *tile_parameters
);

bool support_echo_render_assets_callback_ok(
    const SupportEchoRenderAssets *assets
);

/*
 * Stops new use immediately. Returns true when storage was released before
 * returning. Returns false when release was safely deferred until every RSPQ
 * block recorded through this helper is freed.
 */
bool support_echo_render_assets_unload(SupportEchoRenderAssets *assets);

#endif
