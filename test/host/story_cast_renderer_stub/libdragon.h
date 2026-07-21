#ifndef N64GAME_TEST_STORY_CAST_LIBDRAGON_H
#define N64GAME_TEST_STORY_CAST_LIBDRAGON_H

#include <stddef.h>

typedef struct rspq_block_s {
    unsigned identifier;
} rspq_block_t;

void debugf(const char *format, ...);
void *malloc_uncached(size_t size);
void free_uncached(void *pointer);
void rspq_block_begin(void);
rspq_block_t *rspq_block_end(void);
void rspq_block_free(rspq_block_t *block);
void rspq_block_run(rspq_block_t *block);
void rspq_wait(void);

#endif
