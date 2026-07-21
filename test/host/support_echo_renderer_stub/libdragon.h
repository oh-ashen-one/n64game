#ifndef N64GAME_TEST_SUPPORT_ECHO_LIBDRAGON_H
#define N64GAME_TEST_SUPPORT_ECHO_LIBDRAGON_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define assertf(condition, ...) do { if (!(condition)) abort(); } while (0)
#define RGBA32(r, g, b, a) \
    ((uint32_t)(r) << 24 | (uint32_t)(g) << 16 | \
     (uint32_t)(b) << 8 | (uint32_t)(a))

#define PRIM 1
#define TEX0 2
#define RDPQ_COMBINER1(...) UINT64_C(0)
#define RDPQ_BLENDER_MULTIPLY UINT64_C(0)

typedef struct sprite_s { int unused; } sprite_t;
typedef struct surface_s { void *buffer; } surface_t;
typedef struct rspq_block_s { int unused; } rspq_block_t;
typedef int rdpq_tile_t;
typedef struct rdpq_texparms_s { int unused; } rdpq_texparms_t;

enum {
    TILE0 = 0,
    TLUT_NONE = 0,
    FILTER_BILINEAR = 1,
};

void debugf(const char *format, ...);
void *malloc_uncached(size_t size);
void free_uncached(void *pointer);
void rspq_block_begin(void);
rspq_block_t *rspq_block_end(void);
void rspq_block_free(rspq_block_t *block);
void rspq_block_run(rspq_block_t *block);
void rspq_wait(void);
void rdpq_set_mode_standard(void);
void rdpq_mode_tlut(int mode);
void rdpq_mode_filter(int mode);
void rdpq_mode_zbuf(bool compare, bool write);
void rdpq_mode_combiner(uint64_t mode);
void rdpq_mode_blender(uint64_t mode);
void rdpq_set_prim_color(uint32_t color);

#endif
