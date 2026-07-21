#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "support_echo_render_assets.h"

enum { MAX_EXIT_CALLBACKS = 16 };

typedef struct {
    void (*callback)(void *);
    void *context;
} ExitCallback;

static bool recording;
static ExitCallback exit_callbacks[MAX_EXIT_CALLBACKS];
static size_t exit_callback_count;
static int sprite_free_count;
static int wait_count;
static int texture_upload_count;
static int palette_upload_count;
static int mipmap_none_count;

void debugf(const char *format, ...)
{
    (void)format;
}

static size_t surface_bytes(const surface_t *surface)
{
    return (size_t)surface->width * (size_t)surface->height;
}

sprite_t *sprite_load(const char *path)
{
    assert(strstr(path, "rom:/echo/echo.") == path);
    sprite_t *const sprite = calloc(1U, sizeof(*sprite));
    assert(sprite != NULL);
    const bool body = strstr(path, "body_ci8") != NULL;
    sprite->width = body ? UINT16_C(64) : UINT16_C(32);
    sprite->height = body ? UINT16_C(64) : UINT16_C(32);
    sprite->hslices = UINT8_C(1);
    sprite->vslices = UINT8_C(1);
    sprite->format = body ? FMT_CI8 : FMT_IA8;
    sprite->fits_tmem = !body;
    sprite->pixels = (surface_t){
        .buffer = malloc((size_t)sprite->width * (size_t)sprite->height),
        .width = sprite->width,
        .height = sprite->height,
        .stride = (int)sprite->width,
        .format = sprite->format,
    };
    assert(sprite->pixels.buffer != NULL);
    if (body) {
        const bool pinned_kivarrax_gap = strstr(path, "echo.kivarrax") != NULL;
        sprite->palette_colors = pinned_kivarrax_gap ? 15 : 32;
        sprite->palette = malloc(256U * sizeof(*sprite->palette));
        assert(sprite->palette != NULL);
        for (int index = 0; index < sprite->palette_colors; ++index) {
            sprite->palette[index] =
                (uint16_t)((uint16_t)index * UINT16_C(2) + UINT16_C(1));
        }
        uint8_t *const pixels = sprite->pixels.buffer;
        for (size_t index = 0U;
             index < surface_bytes(&sprite->pixels);
             ++index) {
            pixels[index] = pinned_kivarrax_gap
                ? (uint8_t)(index % 14U + 1U)
                : (uint8_t)(index % (size_t)sprite->palette_colors);
        }
    }
    return sprite;
}

void sprite_free(sprite_t *sprite)
{
    ++sprite_free_count;
    free(sprite->pixels.buffer);
    free(sprite->palette);
    free(sprite);
}

int sprite_get_lod_count(const sprite_t *sprite) { (void)sprite; return 1; }
bool sprite_is_shq(const sprite_t *sprite) { (void)sprite; return false; }
bool sprite_get_texparms(const sprite_t *sprite, rdpq_texparms_t *parameters)
{
    (void)sprite;
    (void)parameters;
    return false;
}
surface_t sprite_get_detail_pixels(const sprite_t *sprite, int *level, int *blend)
{
    (void)sprite;
    (void)level;
    (void)blend;
    return (surface_t){0};
}
tex_format_t sprite_get_format(const sprite_t *sprite) { return sprite->format; }
bool sprite_fits_tmem(const sprite_t *sprite) { return sprite->fits_tmem; }
uint16_t *sprite_get_palette(const sprite_t *sprite) { return sprite->palette; }
int sprite_get_palette_used_colors(const sprite_t *sprite)
{
    return sprite->palette_colors;
}
surface_t sprite_get_pixels(const sprite_t *sprite) { return sprite->pixels; }

surface_t surface_make_sub(
    const surface_t *surface,
    unsigned x,
    unsigned y,
    unsigned width,
    unsigned height
)
{
    return (surface_t){
        .buffer = (uint8_t *)surface->buffer +
            (size_t)y * (size_t)surface->stride + x,
        .width = (uint16_t)width,
        .height = (uint16_t)height,
        .stride = surface->stride,
        .format = surface->format,
    };
}

tex_format_t surface_get_format(const surface_t *surface)
{
    return surface->format;
}
bool rdpq_tex_can_upload(const surface_t *surface)
{
    return surface_bytes(surface) <= 2048U;
}
int rdpq_tex_upload(
    rdpq_tile_t tile,
    const surface_t *surface,
    const rdpq_texparms_t *parameters
)
{
    assert(tile == TILE0);
    assert(parameters != NULL);
    ++texture_upload_count;
    return (int)surface_bytes(surface);
}
int rdpq_sprite_upload(
    rdpq_tile_t tile,
    const sprite_t *sprite,
    const rdpq_texparms_t *parameters
)
{
    assert(tile == TILE0);
    assert(parameters != NULL);
    ++texture_upload_count;
    return (int)surface_bytes(&sprite->pixels);
}
void rdpq_mode_tlut(rdpq_tlut_t mode) { assert(mode == TLUT_RGBA16); }
void rdpq_mode_mipmap(rdpq_mipmap_t mode, int levels)
{
    assert(mode == MIPMAP_NONE);
    assert(levels == 0);
    ++mipmap_none_count;
}
void rdpq_tex_upload_tlut(const uint16_t *palette, int first, int count)
{
    assert(palette != NULL);
    assert(first == 0);
    assert(count == 15 || count == 32);
    ++palette_upload_count;
}

bool rspq_block_is_recording(void) { return recording; }
void rspq_block_atexit(void (*callback)(void *), void *context)
{
    assert(recording);
    assert(exit_callback_count < MAX_EXIT_CALLBACKS);
    exit_callbacks[exit_callback_count++] = (ExitCallback){callback, context};
}
void rspq_wait(void) { ++wait_count; }

static void free_recorded_block(void)
{
    while (exit_callback_count > 0U) {
        const ExitCallback item = exit_callbacks[--exit_callback_count];
        item.callback(item.context);
    }
}

static T3DMaterial body_material(uint32_t reference)
{
    return (T3DMaterial){
        .textureA = {
            .texReference = reference,
            .texWidth = UINT16_C(64),
            .texHeight = UINT16_C(32),
        },
    };
}

static void run_immediate_profile(
    N64GameSupportEchoKind kind,
    uint32_t top_reference,
    uint32_t bottom_reference
)
{
    rdpq_texparms_t parameters = {0};
    T3DMaterial top = body_material(top_reference);
    T3DMaterial bottom = body_material(bottom_reference);
    SupportEchoRenderAssets assets = {0};
    assert(support_echo_render_assets_load(&assets, kind));
    assert(!support_echo_render_assets_load(&assets, kind));
    assert(!support_echo_render_assets_callback_ok(&assets));
    support_echo_render_assets_dynamic_texture_cb(
        &assets, &top, &parameters, TILE0
    );
    assert(!support_echo_render_assets_callback_ok(&assets));
    support_echo_render_assets_dynamic_texture_cb(
        &assets, &bottom, &parameters, TILE0
    );
    assert(support_echo_render_assets_callback_ok(&assets));
    assert(support_echo_render_assets_upload_blob_shadow(
        &assets, TILE0, &parameters
    ));
    assert(support_echo_render_assets_unload(&assets));
}

int main(void)
{
    run_immediate_profile(
        N64GAME_SUPPORT_ECHO_AYSELOR,
        AYSELOR_BODY_TOP_REFERENCE,
        AYSELOR_BODY_BOTTOM_REFERENCE
    );
    run_immediate_profile(
        N64GAME_SUPPORT_ECHO_GYRECLAST,
        GYRECLAST_BODY_TOP_REFERENCE,
        GYRECLAST_BODY_BOTTOM_REFERENCE
    );
    run_immediate_profile(
        N64GAME_SUPPORT_ECHO_KIVARRAX,
        KIVARRAX_BODY_TOP_REFERENCE,
        KIVARRAX_BODY_BOTTOM_REFERENCE
    );
    assert(texture_upload_count == 9);
    assert(palette_upload_count == 6);
    assert(mipmap_none_count == 9);
    assert(sprite_free_count == 6);
    assert(wait_count == 3);

    rdpq_texparms_t parameters = {0};
    T3DMaterial top = body_material(GYRECLAST_BODY_TOP_REFERENCE);
    T3DMaterial bottom = body_material(GYRECLAST_BODY_BOTTOM_REFERENCE);
    SupportEchoRenderAssets deferred = {0};
    assert(support_echo_render_assets_load(
        &deferred, N64GAME_SUPPORT_ECHO_GYRECLAST
    ));
    recording = true;
    support_echo_render_assets_dynamic_texture_cb(
        &deferred, &top, &parameters, TILE0
    );
    support_echo_render_assets_dynamic_texture_cb(
        &deferred, &bottom, &parameters, TILE0
    );
    assert(support_echo_render_assets_upload_blob_shadow(
        &deferred, TILE0, &parameters
    ));
    recording = false;
    assert(exit_callback_count == 3U);
    assert(!support_echo_render_assets_unload(&deferred));
    assert(!deferred.ready && deferred.lifetime == NULL);
    assert(sprite_free_count == 6);
    free_recorded_block();
    assert(sprite_free_count == 8);

    SupportEchoRenderAssets faulted = {0};
    assert(support_echo_render_assets_load(
        &faulted, N64GAME_SUPPORT_ECHO_KIVARRAX
    ));
    support_echo_render_assets_dynamic_texture_cb(
        &faulted, &top, &parameters, TILE0
    );
    assert(!support_echo_render_assets_callback_ok(&faulted));
    assert(support_echo_render_assets_unload(&faulted));
    assert(sprite_free_count == 10);

    SupportEchoRenderAssets invalid = {0};
    assert(!support_echo_render_assets_load(
        &invalid, N64GAME_SUPPORT_ECHO_COUNT
    ));
    puts("support Echoform runtime harness: PASS");
    return 0;
}
