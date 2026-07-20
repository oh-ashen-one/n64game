#ifndef N64GAME_TEST_STORY_CAST_T3D_H
#define N64GAME_TEST_STORY_CAST_T3D_H

#include <stdint.h>

#include "t3danim.h"

#define T3D_SEGMENT_SKELETON 1

static inline const void *t3d_segment_placeholder(int segment)
{
    return (const void *)(uintptr_t)(unsigned)segment;
}

void t3d_mat4fp_from_srt_euler(
    T3DMat4FP *matrix,
    const float scales[3],
    const float rotations[3],
    const float translation[3]
);
void t3d_matrix_push(const T3DMat4FP *matrix);
void t3d_matrix_pop(int count);

#endif
