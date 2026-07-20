#ifndef N64GAME_TEST_SUPPORT_ECHO_T3DMODEL_H
#define N64GAME_TEST_SUPPORT_ECHO_T3DMODEL_H

#include <stdint.h>

#include <libdragon.h>

typedef struct T3DModel T3DModel;

typedef struct {
    uint16_t boneCount;
} T3DChunkSkeleton;

typedef struct {
    float duration;
    const char *filePath;
} T3DChunkAnim;

typedef struct {
    int unused;
} T3DMaterial;

typedef struct {
    void *userData;
    void (*dynTextureCb)(
        void *, const T3DMaterial *, rdpq_texparms_t *, rdpq_tile_t
    );
    const void *matrices;
} T3DModelDrawConf;

uint32_t t3d_model_get_animation_count(const T3DModel *model);
const T3DChunkSkeleton *t3d_model_get_skeleton(const T3DModel *model);
T3DChunkAnim *t3d_model_get_animation(const T3DModel *model, const char *name);
T3DModel *t3d_model_load(const char *path);
void t3d_model_free(T3DModel *model);
void t3d_model_draw_custom(const T3DModel *model, T3DModelDrawConf configuration);

#endif
