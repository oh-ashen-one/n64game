#ifndef N64GAME_TEST_STORY_CAST_T3DANIM_H
#define N64GAME_TEST_STORY_CAST_T3DANIM_H

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

#include "t3dskeleton.h"

typedef struct {
    T3DChunkAnim *animRef;
    FILE *file;
    float time;
    uint32_t set_time_count;
    uint32_t update_count;
    uint8_t isPlaying;
    uint8_t isLooping;
} T3DAnim;

T3DAnim t3d_anim_create(const T3DModel *model, const char *name);
void t3d_anim_attach(T3DAnim *animation, const T3DSkeleton *skeleton);
void t3d_anim_update(T3DAnim *animation, float delta_seconds);
void t3d_anim_set_time(T3DAnim *animation, float time);
void t3d_anim_destroy(T3DAnim *animation);

static inline void t3d_anim_set_playing(T3DAnim *animation, bool playing)
{
    animation->isPlaying = playing ? UINT8_C(1) : UINT8_C(0);
}

static inline bool t3d_anim_is_playing(const T3DAnim *animation)
{
    return animation->isPlaying != 0U;
}

static inline void t3d_anim_set_looping(T3DAnim *animation, bool looping)
{
    animation->isLooping = looping ? UINT8_C(1) : UINT8_C(0);
}

static inline float t3d_anim_get_time(const T3DAnim *animation)
{
    return animation->time;
}

static inline float t3d_anim_get_length(const T3DAnim *animation)
{
    return animation->animRef->duration;
}

#endif
