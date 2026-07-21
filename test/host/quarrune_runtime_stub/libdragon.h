#ifndef N64GAME_HOST_STUB_LIBDRAGON_H
#define N64GAME_HOST_STUB_LIBDRAGON_H

#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define assertf(condition, ...) assert(condition)

void debugf(const char *format, ...);

typedef enum {
    FMT_CI8 = 1,
    FMT_IA8 = 2,
} tex_format_t;

typedef struct {
    void *buffer;
    uint16_t width;
    uint16_t height;
    int stride;
    tex_format_t format;
} surface_t;

typedef struct sprite_s {
    uint16_t width;
    uint16_t height;
    uint8_t hslices;
    uint8_t vslices;
    tex_format_t format;
    bool fits_tmem;
    surface_t pixels;
    uint16_t *palette;
    int palette_colors;
} sprite_t;

typedef int rdpq_tile_t;
enum { TILE0 = 0 };

typedef struct {
    int tmem_addr;
    int palette;
} rdpq_texparms_t;

typedef enum { TLUT_RGBA16 = 1 } rdpq_tlut_t;
typedef enum { MIPMAP_NONE = 0 } rdpq_mipmap_t;

sprite_t *sprite_load(const char *path);
void sprite_free(sprite_t *sprite);
int sprite_get_lod_count(const sprite_t *sprite);
bool sprite_is_shq(const sprite_t *sprite);
bool sprite_get_texparms(const sprite_t *sprite, rdpq_texparms_t *parameters);
surface_t sprite_get_detail_pixels(const sprite_t *sprite, int *level, int *blend);
tex_format_t sprite_get_format(const sprite_t *sprite);
bool sprite_fits_tmem(const sprite_t *sprite);
uint16_t *sprite_get_palette(const sprite_t *sprite);
int sprite_get_palette_used_colors(const sprite_t *sprite);
surface_t sprite_get_pixels(const sprite_t *sprite);

surface_t surface_make_sub(
    const surface_t *surface,
    unsigned x,
    unsigned y,
    unsigned width,
    unsigned height
);
tex_format_t surface_get_format(const surface_t *surface);

bool rdpq_tex_can_upload(const surface_t *surface);
int rdpq_tex_upload(
    rdpq_tile_t tile,
    const surface_t *surface,
    const rdpq_texparms_t *parameters
);
int rdpq_sprite_upload(
    rdpq_tile_t tile,
    const sprite_t *sprite,
    const rdpq_texparms_t *parameters
);
void rdpq_mode_tlut(rdpq_tlut_t mode);
void rdpq_mode_mipmap(rdpq_mipmap_t mode, int levels);
void rdpq_tex_upload_tlut(const uint16_t *palette, int first, int count);

bool rspq_block_is_recording(void);
void rspq_block_atexit(void (*callback)(void *), void *context);
void rspq_wait(void);

#endif
