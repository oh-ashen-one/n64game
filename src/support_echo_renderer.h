#ifndef N64GAME_SUPPORT_ECHO_RENDERER_H
#define N64GAME_SUPPORT_ECHO_RENDERER_H

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
#include "support_echo_render_assets.h"

typedef enum {
    N64GAME_SUPPORT_ECHO_MOTION_IDLE = 0,
    N64GAME_SUPPORT_ECHO_MOTION_REPOSITION,
    N64GAME_SUPPORT_ECHO_MOTION_HIT,
} N64GameSupportEchoMotion;

typedef struct {
    T3DModel *model;
    T3DSkeleton skeleton;
    T3DSkeleton idle_pose;
    T3DSkeleton reposition_pose;
    T3DSkeleton hit_pose;
    T3DAnim idle_anim;
    T3DAnim reposition_anim;
    T3DAnim hit_anim;
    SupportEchoRenderAssets assets;
    rspq_block_t *draw_block;
    N64GameSupportEchoMotion motion;
    bool ready;
} SupportEchoInstance;

typedef struct {
    SupportEchoInstance instances[N64GAME_SUPPORT_ECHO_COUNT];
    T3DMat4FP *model_matrices;
    T3DMat4FP *shadow_matrices;
    T3DVertPacked *shadow_vertices;
    uint32_t buffer_count;
    uint32_t observed_event_serial;
    bool observed_event_serial_valid;
    bool ready;
} SupportEchoRenderer;

/* All three retained distance models are mandatory; initialization fails shut. */
bool support_echo_renderer_init(
    SupportEchoRenderer *renderer,
    uint32_t buffer_count
);

/* Advances fixed-step idle and event-driven reposition/hit clips once per frame. */
bool support_echo_renderer_update(
    SupportEchoRenderer *renderer,
    const N64GameBattle *battle
);

bool support_echo_renderer_draw_shadow(
    SupportEchoRenderer *renderer,
    N64GameSupportEchoKind kind,
    uint32_t frame_index,
    float x,
    float floor_y,
    float z,
    float radius
);

bool support_echo_renderer_draw(
    SupportEchoRenderer *renderer,
    N64GameSupportEchoKind kind,
    uint32_t frame_index,
    float x,
    float y,
    float z,
    float scale,
    float yaw
);

void support_echo_renderer_destroy(SupportEchoRenderer *renderer);

#endif
