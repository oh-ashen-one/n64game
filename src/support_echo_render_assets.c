#include "support_echo_render_assets.h"

#include <stddef.h>
#include <stdlib.h>

enum {
    BODY_WIDTH = 64,
    BODY_HEIGHT = 64,
    BODY_REGION_HEIGHT = 32,
    BODY_REGION_BYTES = 2048,
    BODY_MIN_COLORS = 8,
    BODY_MAX_COLORS = 64,
    SHADOW_WIDTH = 32,
    SHADOW_HEIGHT = 32,
    SHADOW_BYTES = 1024,
};

typedef struct {
    const char *body_path;
    const char *shadow_path;
    uint32_t body_references[2];
} SupportEchoAssetProfile;

static const SupportEchoAssetProfile PROFILES[N64GAME_SUPPORT_ECHO_COUNT] = {
    [N64GAME_SUPPORT_ECHO_AYSELOR] = {
        .body_path =
            "rom:/echo/echo.ayselor/tex_ayselor_body_ci8_64x64.sprite",
        .shadow_path =
            "rom:/echo/echo.ayselor/tex_ayselor_blob_shadow_ia8_32x32.sprite",
        .body_references = {
            AYSELOR_BODY_TOP_REFERENCE,
            AYSELOR_BODY_BOTTOM_REFERENCE,
        },
    },
    [N64GAME_SUPPORT_ECHO_GYRECLAST] = {
        .body_path =
            "rom:/echo/echo.gyreclast/tex_gyreclast_body_ci8_64x64.sprite",
        .shadow_path =
            "rom:/echo/echo.gyreclast/tex_gyreclast_blob_shadow_ia8_32x32.sprite",
        .body_references = {
            GYRECLAST_BODY_TOP_REFERENCE,
            GYRECLAST_BODY_BOTTOM_REFERENCE,
        },
    },
    [N64GAME_SUPPORT_ECHO_KIVARRAX] = {
        .body_path =
            "rom:/echo/echo.kivarrax/tex_kivarrax_body_ci8_64x64.sprite",
        .shadow_path =
            "rom:/echo/echo.kivarrax/tex_kivarrax_blob_shadow_ia8_32x32.sprite",
        .body_references = {
            KIVARRAX_BODY_TOP_REFERENCE,
            KIVARRAX_BODY_BOTTOM_REFERENCE,
        },
    },
};

struct SupportEchoRenderAssetsLifetime {
    sprite_t *body_sprite;
    sprite_t *blob_shadow_sprite;
    size_t recorded_block_references;
    bool release_requested;
};

static void release_owned_sprites(SupportEchoRenderAssetsLifetime *lifetime)
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
    SupportEchoRenderAssetsLifetime *const lifetime =
        (SupportEchoRenderAssetsLifetime *)context;
    assertf(
        lifetime != NULL && lifetime->recorded_block_references > 0U,
        "Support Echoform render-asset block lifetime underflow"
    );
    --lifetime->recorded_block_references;
    if (lifetime->release_requested &&
        lifetime->recorded_block_references == 0U) {
        release_owned_sprites(lifetime);
    }
}

static void retain_current_recording(SupportEchoRenderAssets *assets)
{
    if (!rspq_block_is_recording()) {
        return;
    }
    assertf(
        assets->lifetime != NULL &&
            assets->lifetime->recorded_block_references < SIZE_MAX,
        "Support Echoform render-asset block lifetime overflow"
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
        palette_colors > BODY_MAX_COLORS) {
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

    bool seen[BODY_MAX_COLORS] = {false};
    int seen_colors = 0;
    for (uint16_t y = 0U; y < pixels.height; ++y) {
        const uint8_t *const row =
            (const uint8_t *)pixels.buffer + (size_t)y * (size_t)pixels.stride;
        for (uint16_t x = 0U; x < pixels.width; ++x) {
            const int palette_index = (int)row[x];
            if (palette_index >= palette_colors) {
                return false;
            }
            if (!seen[palette_index]) {
                seen[palette_index] = true;
                ++seen_colors;
            }
        }
    }
    /*
     * Pinned mksprite can retain one valid RGBA16 palette entry after two
     * close source colors quantize to the same indexed texel value. Keep the
     * reviewed pixels exact, but reject broader palette waste or a body that
     * falls below the authored-color floor.
     */
    if (seen_colors < BODY_MIN_COLORS || palette_colors - seen_colors > 1) {
        return false;
    }

    for (int index = 0; index < palette_colors; ++index) {
        if ((palette[index] & UINT16_C(1)) == UINT16_C(0)) {
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

bool support_echo_render_assets_load(
    SupportEchoRenderAssets *assets,
    N64GameSupportEchoKind kind
)
{
    if (assets == NULL ||
        (unsigned)kind >= (unsigned)N64GAME_SUPPORT_ECHO_COUNT ||
        assets->body_sprite != NULL ||
        assets->blob_shadow_sprite != NULL ||
        assets->lifetime != NULL ||
        assets->ready) {
        return false;
    }
    const SupportEchoAssetProfile *const profile = &PROFILES[kind];

    sprite_t *const body = sprite_load(profile->body_path);
    surface_t body_pixels = {0};
    int palette_colors = 0;
    if (!body_profile(body, &body_pixels, &palette_colors)) {
        debugf("[support-echo-assets] body profile failed: %s\n",
               profile->body_path);
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
        debugf("[support-echo-assets] body regions exceed TMEM: %s\n",
               profile->body_path);
        sprite_free(body);
        return false;
    }

    sprite_t *const shadow = sprite_load(profile->shadow_path);
    if (!shadow_profile(shadow)) {
        debugf("[support-echo-assets] shadow profile failed: %s\n",
               profile->shadow_path);
        if (shadow != NULL) {
            sprite_free(shadow);
        }
        sprite_free(body);
        return false;
    }

    SupportEchoRenderAssetsLifetime *const lifetime = malloc(sizeof(*lifetime));
    if (lifetime == NULL) {
        debugf("[support-echo-assets] lifetime allocation failed: %s\n",
               profile->body_path);
        sprite_free(shadow);
        sprite_free(body);
        return false;
    }
    *lifetime = (SupportEchoRenderAssetsLifetime){
        .body_sprite = body,
        .blob_shadow_sprite = shadow,
    };

    assets->body_sprite = body;
    assets->blob_shadow_sprite = shadow;
    assets->body_regions[0] = top;
    assets->body_regions[1] = bottom;
    assets->body_references[0] = profile->body_references[0];
    assets->body_references[1] = profile->body_references[1];
    assets->body_palette_colors = palette_colors;
    assets->lifetime = lifetime;
    assets->ready = true;
    return true;
}

void support_echo_render_assets_dynamic_texture_cb(
    void *user_data,
    const T3DMaterial *material,
    rdpq_texparms_t *tile_parameters,
    rdpq_tile_t tile
)
{
    SupportEchoRenderAssets *const assets = (SupportEchoRenderAssets *)user_data;
    if (assets == NULL ||
        !assets->ready ||
        assets->lifetime == NULL ||
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
    uint8_t success_bit = 0U;
    if (texture->texReference == assets->body_references[0]) {
        region = &assets->body_regions[0];
        success_bit = UINT8_C(1);
    } else if (texture->texReference == assets->body_references[1]) {
        region = &assets->body_regions[1];
        success_bit = UINT8_C(2);
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
    assets->successful_body_callbacks |= success_bit;
}

bool support_echo_render_assets_upload_blob_shadow(
    SupportEchoRenderAssets *assets,
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

bool support_echo_render_assets_callback_ok(
    const SupportEchoRenderAssets *assets
)
{
    return assets != NULL &&
        assets->ready &&
        !assets->callback_fault &&
        assets->successful_body_callbacks == UINT8_C(3);
}

bool support_echo_render_assets_unload(SupportEchoRenderAssets *assets)
{
    if (assets == NULL || assets->lifetime == NULL) {
        return false;
    }

    rspq_wait();
    SupportEchoRenderAssetsLifetime *const lifetime = assets->lifetime;
    const bool released_now = lifetime->recorded_block_references == 0U;
    lifetime->release_requested = true;
    *assets = (SupportEchoRenderAssets){0};
    if (released_now) {
        release_owned_sprites(lifetime);
    }
    return released_now;
}
