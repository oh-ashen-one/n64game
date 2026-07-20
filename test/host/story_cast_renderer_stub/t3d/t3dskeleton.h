#ifndef N64GAME_TEST_STORY_CAST_T3DSKELETON_H
#define N64GAME_TEST_STORY_CAST_T3DSKELETON_H

#include <stdbool.h>
#include <stdint.h>

#include "t3dmodel.h"

typedef struct {
    float values[16];
} T3DMat4FP;

typedef struct {
    int unused;
} T3DBone;

typedef struct {
    T3DBone *bones;
    T3DMat4FP *boneMatricesFP;
    const T3DChunkSkeleton *skeletonRef;
    uint32_t update_count;
} T3DSkeleton;

T3DSkeleton t3d_skeleton_create_buffered(const T3DModel *model, int buffers);
T3DSkeleton t3d_skeleton_clone(const T3DSkeleton *skeleton, bool use_matrices);
void t3d_skeleton_blend(
    const T3DSkeleton *result,
    const T3DSkeleton *left,
    const T3DSkeleton *right,
    float factor
);
void t3d_skeleton_update(T3DSkeleton *skeleton);
void t3d_skeleton_destroy(T3DSkeleton *skeleton);
void t3d_skeleton_use(const T3DSkeleton *skeleton);

#endif
