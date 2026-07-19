#include "quarrune_render_assets.h"

#include <stddef.h>
#include <stdlib.h>

enum {
    BODY_WIDTH = 64,
    BODY_HEIGHT = 64,
    BODY_REGION_HEIGHT = 32,
    BODY_REGION_BYTES = 2048,
    BODY_MIN_COLORS = 32,
    SHADOW_WIDTH = 32,
    SHADOW_HEIGHT = 32,
    SHADOW_BYTES = 1024,
};

static const char BODY_PATH[] =
    "rom:/echo/echo.quarrune/tex_quarrune_body_ci8_64x64.sprite";
static const char SHADOW_PATH[] =
    "rom:/echo/echo.quarrune/tex_quarrune_blob_shadow_ia8_32x32.sprite";

struct QuarruneRenderAssetsLifetime {
    sprite_t *body_sprite;
    sprite_t *blob_shadow_sprite;
    size_t recorded_block_references;
    bool release_requested;
};

static void release_owned_sprites(QuarruneRenderAssetsLifetime *lifetime)
{
    if (lifetime->blob_shadow_sprite != NULL) {
        sprite_free(lifetime->blob_shadow_sprite);
    }
    if (lifetime->body_sprite != NULL) {
        sprite_free(lifetime->body_sprite);
    }
    free(lifetime);
}

static void release_recorded_block_reference(void *context)
{
    QuarruneRenderAssetsLifetime *const lifetime =
        (QuarruneRenderAssetsLifetime *)context;
    assertf(
        lifetime != NULL && lifetime->recorded_block_references > 0U,
        "Quarrune render-asset block lifetime underflow"
    );
    --lifetime->recorded_block_references;
    if (lifetime->release_requested &&
        lifetime->recorded_block_references == 0U) {
        release_owned_sprites(lifetime);
    }
}

static void retain_current_recording(QuarruneRenderAssets *assets)
{
    if (!rspq_block_is_recording()) {
        return;
    }
    assertf(
        assets->lifetime->recorded_block_references < SIZE_MAX,
        "Quarrune render-asset block lifetime overflow"
    );
    ++assets->lifetime->recorded_block_references;
    rspq_block_atexit(release_recorded_block_reference, assets->lifetime);
}

static bool plain_sprite_profile(sprite_t *sprite)
{
    if (sprite == NULL ||
        sprite->hslices != 1U ||
        sprite->vslices != 1U ||
        sprite_get_lod_count(sprite) != 1 ||
        sprite_is_shq(sprite)) {
        return false;
    }

    rdpq_texparms_t embedded_parameters = {0};
    if (sprite_get_texparms(sprite, &embedded_parameters)) {
        return false;
    }

    const surface_t detail = sprite_get_detail_pixels(sprite, NULL, NULL);
    return detail.buffer == NULL;
}

static bool body_profile(
    sprite_t *sprite,
    surface_t *pixels_out,
    int *palette_colors_out
)
{
    if (!plain_sprite_profile(sprite) ||
        sprite_get_format(sprite) != FMT_CI8 ||
        sprite->width != BODY_WIDTH ||
        sprite->height != BODY_HEIGHT ||
        sprite_fits_tmem(sprite)) {
        return false;
    }

    uint16_t *const palette = sprite_get_palette(sprite);
    const int palette_colors = sprite_get_palette_used_colors(sprite);
    if (palette == NULL ||
        (((uintptr_t)palette & (uintptr_t)7U) != (uintptr_t)0U) ||
        palette_colors < BODY_MIN_COLORS ||
        palette_colors > 256) {
        return false;
    }

    const surface_t pixels = sprite_get_pixels(sprite);
    if (surface_get_format(&pixels) != FMT_CI8 ||
        pixels.width != BODY_WIDTH ||
        pixels.height != BODY_HEIGHT ||
        pixels.stride != BODY_WIDTH ||
        pixels.buffer == NULL ||
        rdpq_tex_can_upload(&pixels)) {
        return false;
    }

    bool seen[256] = {false};
    int maximum_index = -1;
    for (uint16_t y = 0U; y < pixels.height; ++y) {
        const uint8_t *const row =
            (const uint8_t *)pixels.buffer + (size_t)y * (size_t)pixels.stride;
        for (uint16_t x = 0U; x < pixels.width; ++x) {
            const int palette_index = (int)row[x];
            seen[palette_index] = true;
            if (palette_index > maximum_index) {
                maximum_index = palette_index;
            }
        }
    }
    if (maximum_index + 1 != palette_colors) {
        return false;
    }

    for (int index = 0; index < palette_colors; ++index) {
        if (!seen[index] ||
            (palette[index] & UINT16_C(1)) == UINT16_C(0)) {
            return false;
        }
        for (int prior = 0; prior < index; ++prior) {
            if (palette[prior] == palette[index]) {
                return false;
            }
        }
    }

    *pixels_out = pixels;
    *palette_colors_out = palette_colors;
    return true;
}

static bool shadow_profile(sprite_t *sprite)
{
    if (!plain_sprite_profile(sprite) ||
        sprite_get_format(sprite) != FMT_IA8 ||
        sprite->width != SHADOW_WIDTH ||
        sprite->height != SHADOW_HEIGHT ||
        !sprite_fits_tmem(sprite) ||
        sprite_get_palette(sprite) != NULL) {
        return false;
    }

    const surface_t pixels = sprite_get_pixels(sprite);
    return surface_get_format(&pixels) == FMT_IA8 &&
        pixels.width == SHADOW_WIDTH &&
        pixels.height == SHADOW_HEIGHT &&
        pixels.stride == SHADOW_WIDTH &&
        pixels.buffer != NULL &&
        rdpq_tex_can_upload(&pixels);
}

bool quarrune_render_assets_load(QuarruneRenderAssets *assets)
{
    if (assets == NULL) {
        return false;
    }
    if (assets->body_sprite != NULL ||
        assets->blob_shadow_sprite != NULL ||
        assets->lifetime != NULL ||
        assets->ready) {
        return false;
    }

    sprite_t *const body = sprite_load(BODY_PATH);
    surface_t body_pixels = {0};
    int palette_colors = 0;
    if (!body_profile(body, &body_pixels, &palette_colors)) {
        if (body != NULL) {
            sprite_free(body);
        }
        return false;
    }

    const surface_t top = surface_make_sub(
        &body_pixels, 0U, 0U, BODY_WIDTH, BODY_REGION_HEIGHT
    );
    const surface_t bottom = surface_make_sub(
        &body_pixels, 0U, BODY_REGION_HEIGHT, BODY_WIDTH, BODY_REGION_HEIGHT
    );
    if (!rdpq_tex_can_upload(&top) || !rdpq_tex_can_upload(&bottom)) {
        sprite_free(body);
        return false;
    }

    sprite_t *const shadow = sprite_load(SHADOW_PATH);
    if (!shadow_profile(shadow)) {
        if (shadow != NULL) {
            sprite_free(shadow);
        }
        sprite_free(body);
        return false;
    }

    QuarruneRenderAssetsLifetime *const lifetime = malloc(sizeof(*lifetime));
    if (lifetime == NULL) {
        sprite_free(shadow);
        sprite_free(body);
        return false;
    }
    *lifetime = (QuarruneRenderAssetsLifetime){
        .body_sprite = body,
        .blob_shadow_sprite = shadow,
    };

    assets->body_sprite = body;
    assets->blob_shadow_sprite = shadow;
    assets->body_regions[0] = top;
    assets->body_regions[1] = bottom;
    assets->body_palette_colors = palette_colors;
    assets->lifetime = lifetime;
    assets->ready = true;
    return true;
}

void quarrune_render_assets_dynamic_texture_cb(
    void *user_data,
    const T3DMaterial *material,
    rdpq_texparms_t *tile_parameters,
    rdpq_tile_t tile
)
{
    QuarruneRenderAssets *const assets = (QuarruneRenderAssets *)user_data;
    if (assets == NULL ||
        !assets->ready ||
        material == NULL ||
        tile_parameters == NULL) {
        if (assets != NULL) {
            assets->callback_fault = true;
        }
        return;
    }
    if (tile != TILE0) {
        assets->callback_fault = true;
        return;
    }

    const T3DMaterialTexture *const texture = &material->textureA;
    const surface_t *region = NULL;
    if (texture->texReference == QUARRUNE_BODY_TOP_REFERENCE) {
        region = &assets->body_regions[0];
    } else if (texture->texReference == QUARRUNE_BODY_BOTTOM_REFERENCE) {
        region = &assets->body_regions[1];
    } else {
        assets->callback_fault = true;
        return;
    }

    if (texture->texPath != NULL ||
        texture->texWidth != BODY_WIDTH ||
        texture->texHeight != BODY_REGION_HEIGHT ||
        material->textureB.texReference != 0U ||
        material->textureB.texPath != NULL ||
        tile_parameters->tmem_addr != 0 ||
        tile_parameters->palette != 0) {
        assets->callback_fault = true;
        return;
    }

    retain_current_recording(assets);
    rdpq_mode_mipmap(MIPMAP_NONE, 0);
    const int uploaded = rdpq_tex_upload(tile, region, tile_parameters);
    if (uploaded != BODY_REGION_BYTES) {
        assets->callback_fault = true;
        return;
    }

    rdpq_mode_tlut(TLUT_RGBA16);
    rdpq_tex_upload_tlut(
        sprite_get_palette(assets->body_sprite),
        0,
        assets->body_palette_colors
    );
    assets->successful_body_callbacks |=
        texture->texReference == QUARRUNE_BODY_TOP_REFERENCE ? UINT8_C(1) : UINT8_C(2);
}

bool quarrune_render_assets_upload_blob_shadow(
    QuarruneRenderAssets *assets,
    rdpq_tile_t tile,
    const rdpq_texparms_t *tile_parameters
)
{
    if (assets == NULL ||
        !assets->ready ||
        assets->blob_shadow_sprite == NULL) {
        return false;
    }
    retain_current_recording(assets);
    rdpq_mode_mipmap(MIPMAP_NONE, 0);
    return rdpq_sprite_upload(
        tile, assets->blob_shadow_sprite, tile_parameters
    ) == SHADOW_BYTES;
}

bool quarrune_render_assets_callback_ok(const QuarruneRenderAssets *assets)
{
    return assets != NULL &&
        assets->ready &&
        !assets->callback_fault &&
        assets->successful_body_callbacks == UINT8_C(3);
}

bool quarrune_render_assets_unload(QuarruneRenderAssets *assets)
{
    if (assets == NULL || assets->lifetime == NULL) {
        return false;
    }

    rspq_wait();
    QuarruneRenderAssetsLifetime *const lifetime = assets->lifetime;
    const bool released_now = lifetime->recorded_block_references == 0U;
    lifetime->release_requested = true;
    *assets = (QuarruneRenderAssets){0};
    if (released_now) {
        release_owned_sprites(lifetime);
    }
    return released_now;
}
