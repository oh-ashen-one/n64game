#ifndef N64GAME_STORY_CAST_RENDERER_H
#define N64GAME_STORY_CAST_RENDERER_H

#include <stdbool.h>
#include <stdint.h>

#include <libdragon.h>

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wconversion"
#include <t3d/t3d.h>
#include <t3d/t3danim.h>
#include <t3d/t3dskeleton.h>
#pragma GCC diagnostic pop

#include "n64game_core.h"

enum {
    N64GAME_STORY_CAST_MAX_CUES = 3,
};

typedef enum {
    N64GAME_STORY_CAST_SERA = 0,
    N64GAME_STORY_CAST_TAVI,
    N64GAME_STORY_CAST_BEACON,
    N64GAME_STORY_CAST_COUNT,
} StoryCastKind;

typedef struct {
    T3DModel *model;
    T3DSkeleton skeleton;
    T3DSkeleton idle_pose;
    T3DSkeleton cue_poses[N64GAME_STORY_CAST_MAX_CUES];
    T3DAnim idle_anim;
    T3DAnim cue_anims[N64GAME_STORY_CAST_MAX_CUES];
    rspq_block_t *draw_block;
    uint8_t cue_count;
    uint8_t active_cue;
    bool ready;
} StoryCastInstance;

typedef struct {
    StoryCastInstance instances[N64GAME_STORY_CAST_COUNT];
    T3DMat4FP *model_matrices;
    uint32_t buffer_count;
    N64GameDialogue observed_dialogue;
    uint8_t observed_dialogue_page;
    bool observed_dialogue_valid;
    bool ready;
} StoryCastRenderer;

/* Every retained cast model and animation stream is mandatory. */
bool story_cast_renderer_init(StoryCastRenderer *renderer, uint32_t buffer_count);

/* Detects dialogue edges at 30 Hz and samples cast poses at a fixed 15 Hz. */
bool story_cast_renderer_update(
    StoryCastRenderer *renderer,
    const N64GameCore *game
);

bool story_cast_renderer_draw(
    StoryCastRenderer *renderer,
    StoryCastKind kind,
    uint32_t frame_index,
    float x,
    float y,
    float z,
    float scale,
    float yaw
);

void story_cast_renderer_destroy(StoryCastRenderer *renderer);

#endif
