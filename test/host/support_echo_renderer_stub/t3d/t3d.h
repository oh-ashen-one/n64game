#ifndef N64GAME_TEST_SUPPORT_ECHO_T3D_H
#define N64GAME_TEST_SUPPORT_ECHO_T3D_H

#include <stdint.h>

#include "t3danim.h"

#define T3D_SEGMENT_SKELETON 1
#define T3D_FLAG_TEXTURED UINT32_C(1)
#define T3D_FLAG_DEPTH UINT32_C(2)

typedef struct { float v[3]; } fm_vec3_t;

typedef struct {
    int16_t posA[3];
    uint16_t normA;
    uint32_t rgbaA;
    int16_t stA[2];
    int16_t posB[3];
    uint16_t normB;
    uint32_t rgbaB;
    int16_t stB[2];
} T3DVertPacked;

static inline const void *t3d_segment_placeholder(int segment)
{
    return (const void *)(uintptr_t)(unsigned)segment;
}

uint16_t t3d_vert_pack_normal(const fm_vec3_t *normal);
void t3d_mat4fp_from_srt_euler(
    T3DMat4FP *matrix,
    const float scales[3],
    const float rotations[3],
    const float translation[3]
);
void t3d_state_set_drawflags(uint32_t flags);
void t3d_matrix_push(const T3DMat4FP *matrix);
void t3d_matrix_pop(int count);
void t3d_vert_load(const T3DVertPacked *vertices, int destination, int count);
void t3d_tri_draw(int first, int second, int third);
void t3d_tri_sync(void);

#endif
