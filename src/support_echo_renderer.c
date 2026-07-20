#include "support_echo_renderer.h"

#include <math.h>
#include <stddef.h>

enum {
    SUPPORT_ANIMATION_COUNT = 3,
    SHADOW_LOCAL_RADIUS = 16,
    AYSELOR_BONE_COUNT = 18,
    GYRECLAST_BONE_COUNT = 18,
    KIVARRAX_BONE_COUNT = 20,
};

typedef struct {
    const char *debug_name;
    const char *model_path;
    uint16_t bone_count;
} SupportEchoProfile;

static const char *const ANIMATION_NAMES[SUPPORT_ANIMATION_COUNT] = {
    "idle_a",
    "reposition",
    "hit",
};

static const SupportEchoProfile PROFILES[N64GAME_SUPPORT_ECHO_COUNT] = {
    [N64GAME_SUPPORT_ECHO_AYSELOR] = {
        .debug_name = "ayselor",
        .model_path = "rom:/echo/echo.ayselor/ayselor_distance.t3dm",
        .bone_count = AYSELOR_BONE_COUNT,
    },
    [N64GAME_SUPPORT_ECHO_GYRECLAST] = {
        .debug_name = "gyreclast",
        .model_path = "rom:/echo/echo.gyreclast/gyreclast_distance.t3dm",
        .bone_count = GYRECLAST_BONE_COUNT,
    },
    [N64GAME_SUPPORT_ECHO_KIVARRAX] = {
        .debug_name = "kivarrax",
        .model_path = "rom:/echo/echo.kivarrax/kivarrax_distance.t3dm",
        .bone_count = KIVARRAX_BONE_COUNT,
    },
};

static bool model_contract_ok(
    const T3DModel *model,
    const SupportEchoProfile *profile
)
{
    if (model == NULL || profile == NULL ||
        t3d_model_get_animation_count(model) != SUPPORT_ANIMATION_COUNT) {
        return false;
    }
    const T3DChunkSkeleton *const skeleton = t3d_model_get_skeleton(model);
    if (skeleton == NULL || skeleton->boneCount != profile->bone_count) {
        return false;
    }
    for (size_t index = 0U; index < SUPPORT_ANIMATION_COUNT; ++index) {
        const T3DChunkAnim *const animation = t3d_model_get_animation(
            model, ANIMATION_NAMES[index]
        );
        if (animation == NULL || animation->duration <= 0.0f ||
            animation->filePath == NULL || animation->filePath[0] == '\0') {
            return false;
        }
    }
    return true;
}

static bool skeleton_contract_ok(
    const T3DSkeleton *skeleton,
    uint16_t bone_count
)
{
    return skeleton != NULL &&
        skeleton->bones != NULL &&
        skeleton->boneMatricesFP != NULL &&
        skeleton->skeletonRef != NULL &&
        skeleton->skeletonRef->boneCount == bone_count;
}

static bool pose_contract_ok(const T3DSkeleton *pose, uint16_t bone_count)
{
    return pose != NULL &&
        pose->bones != NULL &&
        pose->skeletonRef != NULL &&
        pose->skeletonRef->boneCount == bone_count;
}

static bool animation_stream_ok(const T3DAnim *animation)
{
    return animation != NULL &&
        animation->animRef != NULL &&
        animation->file != NULL;
}

static bool setup_instance(
    SupportEchoInstance *instance,
    N64GameSupportEchoKind kind,
    uint32_t buffer_count
)
{
    const SupportEchoProfile *const profile = &PROFILES[kind];
    if (!support_echo_render_assets_load(&instance->assets, kind)) {
        debugf("[%s] render-asset load failed\n", profile->debug_name);
        return false;
    }

    instance->model = t3d_model_load(profile->model_path);
    if (!model_contract_ok(instance->model, profile)) {
        debugf("[%s] model contract failed: %s\n",
               profile->debug_name, profile->model_path);
        return false;
    }

    instance->skeleton = t3d_skeleton_create_buffered(
        instance->model, (int)buffer_count
    );
    if (!skeleton_contract_ok(&instance->skeleton, profile->bone_count)) {
        debugf("[%s] skeleton contract or allocation failed\n",
               profile->debug_name);
        return false;
    }

    instance->idle_pose = t3d_skeleton_clone(&instance->skeleton, false);
    instance->reposition_pose = t3d_skeleton_clone(&instance->skeleton, false);
    instance->hit_pose = t3d_skeleton_clone(&instance->skeleton, false);
    if (!pose_contract_ok(&instance->idle_pose, profile->bone_count) ||
        !pose_contract_ok(&instance->reposition_pose, profile->bone_count) ||
        !pose_contract_ok(&instance->hit_pose, profile->bone_count)) {
        debugf("[%s] animation-pose allocation failed\n", profile->debug_name);
        return false;
    }

    instance->idle_anim = t3d_anim_create(instance->model, ANIMATION_NAMES[0]);
    instance->reposition_anim = t3d_anim_create(
        instance->model, ANIMATION_NAMES[1]
    );
    instance->hit_anim = t3d_anim_create(instance->model, ANIMATION_NAMES[2]);
    if (!animation_stream_ok(&instance->idle_anim) ||
        !animation_stream_ok(&instance->reposition_anim) ||
        !animation_stream_ok(&instance->hit_anim)) {
        debugf("[%s] animation-stream load failed\n", profile->debug_name);
        return false;
    }

    t3d_anim_attach(&instance->idle_anim, &instance->idle_pose);
    t3d_anim_attach(&instance->reposition_anim, &instance->reposition_pose);
    t3d_anim_attach(&instance->hit_anim, &instance->hit_pose);
    t3d_anim_set_looping(&instance->reposition_anim, false);
    t3d_anim_set_looping(&instance->hit_anim, false);
    t3d_anim_set_time(&instance->idle_anim, 0.0f);
    t3d_anim_set_time(&instance->reposition_anim, 0.0f);
    t3d_anim_set_time(&instance->hit_anim, 0.0f);
    /*
     * Streams remain at their unopened origins until the first positive fixed
     * step. Advancing a Tiny3D stream by exactly zero can normalize the
     * calloc-initialized quaternion preceding a first nonzero-time keyframe.
     */
    t3d_anim_set_playing(&instance->reposition_anim, false);
    t3d_anim_set_playing(&instance->hit_anim, false);
    t3d_skeleton_blend(
        &instance->skeleton, &instance->idle_pose, &instance->idle_pose, 0.0f
    );
    for (uint32_t index = 0U; index < buffer_count; ++index) {
        t3d_skeleton_update(&instance->skeleton);
    }

    rspq_block_begin();
    t3d_model_draw_custom(
        instance->model,
        (T3DModelDrawConf){
            .userData = &instance->assets,
            .dynTextureCb = support_echo_render_assets_dynamic_texture_cb,
            .matrices = (const T3DMat4FP *)t3d_segment_placeholder(
                T3D_SEGMENT_SKELETON
            ),
        }
    );
    instance->draw_block = rspq_block_end();
    if (instance->draw_block == NULL ||
        !support_echo_render_assets_callback_ok(&instance->assets)) {
        debugf(
            "[%s] recorded draw contract failed: callbacks=%u fault=%u\n",
            profile->debug_name,
            (unsigned int)instance->assets.successful_body_callbacks,
            instance->assets.callback_fault ? 1U : 0U
        );
        return false;
    }

    instance->motion = N64GAME_SUPPORT_ECHO_MOTION_IDLE;
    instance->ready = true;
    return true;
}

static void setup_shadow_vertices(T3DVertPacked *vertices)
{
    const uint16_t up = t3d_vert_pack_normal(
        &(fm_vec3_t){{0.0f, 1.0f, 0.0f}}
    );
    vertices[0] = (T3DVertPacked){
        .posA = {-SHADOW_LOCAL_RADIUS, 0, -SHADOW_LOCAL_RADIUS},
        .normA = up,
        .rgbaA = UINT32_C(0xFFFFFFFF),
        .stA = {0, 0},
        .posB = {SHADOW_LOCAL_RADIUS, 0, -SHADOW_LOCAL_RADIUS},
        .normB = up,
        .rgbaB = UINT32_C(0xFFFFFFFF),
        .stB = {32 << 5, 0},
    };
    vertices[1] = (T3DVertPacked){
        .posA = {SHADOW_LOCAL_RADIUS, 0, SHADOW_LOCAL_RADIUS},
        .normA = up,
        .rgbaA = UINT32_C(0xFFFFFFFF),
        .stA = {32 << 5, 32 << 5},
        .posB = {-SHADOW_LOCAL_RADIUS, 0, SHADOW_LOCAL_RADIUS},
        .normB = up,
        .rgbaB = UINT32_C(0xFFFFFFFF),
        .stB = {0, 32 << 5},
    };
}

bool support_echo_renderer_init(
    SupportEchoRenderer *renderer,
    uint32_t buffer_count
)
{
    if (renderer == NULL || buffer_count == 0U ||
        renderer->model_matrices != NULL ||
        renderer->shadow_matrices != NULL ||
        renderer->shadow_vertices != NULL || renderer->ready) {
        return false;
    }
    if ((size_t)buffer_count > SIZE_MAX / N64GAME_SUPPORT_ECHO_COUNT ||
        (size_t)buffer_count * N64GAME_SUPPORT_ECHO_COUNT >
            SIZE_MAX / sizeof(T3DMat4FP)) {
        return false;
    }
    const size_t matrix_count =
        (size_t)buffer_count * N64GAME_SUPPORT_ECHO_COUNT;
    renderer->model_matrices = malloc_uncached(
        sizeof(T3DMat4FP) * matrix_count
    );
    renderer->shadow_matrices = malloc_uncached(
        sizeof(T3DMat4FP) * matrix_count
    );
    renderer->shadow_vertices = malloc_uncached(sizeof(T3DVertPacked) * 2U);
    renderer->buffer_count = buffer_count;
    if (renderer->model_matrices == NULL ||
        renderer->shadow_matrices == NULL ||
        renderer->shadow_vertices == NULL) {
        support_echo_renderer_destroy(renderer);
        return false;
    }
    setup_shadow_vertices(renderer->shadow_vertices);

    for (unsigned index = 0U;
         index < (unsigned)N64GAME_SUPPORT_ECHO_COUNT;
         ++index) {
        if (!setup_instance(
                &renderer->instances[index],
                (N64GameSupportEchoKind)index,
                buffer_count
            )) {
            support_echo_renderer_destroy(renderer);
            return false;
        }
    }
    renderer->ready = true;
    return true;
}

static float clamp_unit(float value)
{
    if (value < 0.0f) {
        return 0.0f;
    }
    if (value > 1.0f) {
        return 1.0f;
    }
    return value;
}

static void start_motion(
    SupportEchoInstance *instance,
    N64GameSupportEchoMotion motion
)
{
    T3DAnim *animation = motion == N64GAME_SUPPORT_ECHO_MOTION_HIT ?
        &instance->hit_anim : &instance->reposition_anim;
    t3d_anim_set_time(animation, 0.0f);
    t3d_anim_set_playing(animation, true);
    instance->motion = motion;
}

static void reset_motion(SupportEchoInstance *instance)
{
    t3d_anim_set_playing(&instance->reposition_anim, false);
    t3d_anim_set_playing(&instance->hit_anim, false);
    instance->motion = N64GAME_SUPPORT_ECHO_MOTION_IDLE;
}

static void apply_battle_event(
    SupportEchoRenderer *renderer,
    const N64GameBattle *battle
)
{
    const N64GameBattleEvent *const event = &battle->last_event;
    if (!event->happened || event->skipped ||
        event->actor >= N64GAME_BATTLE_ACTOR_COUNT) {
        return;
    }

    if (event->actor >= 1U) {
        start_motion(
            &renderer->instances[event->actor - 1U],
            N64GAME_SUPPORT_ECHO_MOTION_REPOSITION
        );
    }
    if (event->hp_delta >= 0) {
        return;
    }
    if (event->target == N64GAME_TARGET_ALL) {
        const bool actor_side = battle->actors[event->actor].player_side;
        for (uint8_t actor = 1U; actor < N64GAME_BATTLE_ACTOR_COUNT; ++actor) {
            if (battle->actors[actor].player_side != actor_side) {
                start_motion(
                    &renderer->instances[actor - 1U],
                    N64GAME_SUPPORT_ECHO_MOTION_HIT
                );
            }
        }
    } else if (event->target >= 1U &&
               event->target < N64GAME_BATTLE_ACTOR_COUNT) {
        start_motion(
            &renderer->instances[event->target - 1U],
            N64GAME_SUPPORT_ECHO_MOTION_HIT
        );
    }
}

static void update_instance(SupportEchoInstance *instance)
{
    static const float FIXED_DELTA_SECONDS = 1.0f / 30.0f;
    static const float BLEND_SECONDS = 0.10f;
    t3d_anim_update(&instance->idle_anim, FIXED_DELTA_SECONDS);

    T3DSkeleton *motion_pose = &instance->idle_pose;
    float motion_blend = 0.0f;
    if (instance->motion != N64GAME_SUPPORT_ECHO_MOTION_IDLE) {
        T3DAnim *const motion_anim =
            instance->motion == N64GAME_SUPPORT_ECHO_MOTION_HIT ?
                &instance->hit_anim : &instance->reposition_anim;
        motion_pose = instance->motion == N64GAME_SUPPORT_ECHO_MOTION_HIT ?
            &instance->hit_pose : &instance->reposition_pose;
        t3d_anim_update(motion_anim, FIXED_DELTA_SECONDS);
        if (t3d_anim_is_playing(motion_anim)) {
            const float time = t3d_anim_get_time(motion_anim);
            const float remaining = t3d_anim_get_length(motion_anim) - time;
            const float blend_in = clamp_unit(time / BLEND_SECONDS);
            const float blend_out = clamp_unit(remaining / BLEND_SECONDS);
            motion_blend = fminf(blend_in, blend_out);
        } else {
            instance->motion = N64GAME_SUPPORT_ECHO_MOTION_IDLE;
        }
    }
    t3d_skeleton_blend(
        &instance->skeleton,
        &instance->idle_pose,
        motion_pose,
        motion_blend
    );
    t3d_skeleton_update(&instance->skeleton);
}

bool support_echo_renderer_update(
    SupportEchoRenderer *renderer,
    const N64GameBattle *battle
)
{
    if (renderer == NULL || !renderer->ready || battle == NULL) {
        return false;
    }
    if (!renderer->observed_event_serial_valid ||
        renderer->observed_event_serial != battle->event_serial) {
        if (renderer->observed_event_serial_valid &&
            battle->event_serial == 0U) {
            for (unsigned index = 0U;
                 index < (unsigned)N64GAME_SUPPORT_ECHO_COUNT;
                 ++index) {
                reset_motion(&renderer->instances[index]);
            }
        }
        renderer->observed_event_serial = battle->event_serial;
        renderer->observed_event_serial_valid = true;
        apply_battle_event(renderer, battle);
    }
    for (unsigned index = 0U;
         index < (unsigned)N64GAME_SUPPORT_ECHO_COUNT;
         ++index) {
        update_instance(&renderer->instances[index]);
    }
    return true;
}

static bool draw_arguments_ok(
    const SupportEchoRenderer *renderer,
    N64GameSupportEchoKind kind,
    uint32_t frame_index
)
{
    return renderer != NULL && renderer->ready &&
        (unsigned)kind < (unsigned)N64GAME_SUPPORT_ECHO_COUNT &&
        frame_index < renderer->buffer_count &&
        renderer->instances[kind].ready;
}

bool support_echo_renderer_draw_shadow(
    SupportEchoRenderer *renderer,
    N64GameSupportEchoKind kind,
    uint32_t frame_index,
    float x,
    float floor_y,
    float z,
    float radius
)
{
    if (!draw_arguments_ok(renderer, kind, frame_index) || radius <= 0.0f) {
        return false;
    }
    const size_t matrix_slot =
        (size_t)kind * (size_t)renderer->buffer_count + frame_index;
    const float shadow_scale = radius / (float)SHADOW_LOCAL_RADIUS;
    const float scales[3] = {shadow_scale, 1.0f, shadow_scale};
    const float rotations[3] = {0.0f, 0.0f, 0.0f};
    const float translation[3] = {x, floor_y + 0.15f, z};
    t3d_mat4fp_from_srt_euler(
        &renderer->shadow_matrices[matrix_slot], scales, rotations, translation
    );

    rdpq_set_mode_standard();
    rdpq_mode_tlut(TLUT_NONE);
    rdpq_mode_filter(FILTER_BILINEAR);
    rdpq_mode_zbuf(true, false);
    rdpq_mode_combiner(
        RDPQ_COMBINER1((0, 0, 0, PRIM), (PRIM, 0, TEX0, 0))
    );
    rdpq_mode_blender(RDPQ_BLENDER_MULTIPLY);
    rdpq_set_prim_color(RGBA32(7, 11, 15, 150));
    const rdpq_texparms_t parameters = {0};
    if (!support_echo_render_assets_upload_blob_shadow(
            &renderer->instances[kind].assets, TILE0, &parameters
        )) {
        return false;
    }
    t3d_state_set_drawflags(T3D_FLAG_TEXTURED | T3D_FLAG_DEPTH);
    t3d_matrix_push(&renderer->shadow_matrices[matrix_slot]);
    t3d_vert_load(renderer->shadow_vertices, 0, 4);
    t3d_matrix_pop(1);
    t3d_tri_draw(0, 1, 2);
    t3d_tri_draw(0, 2, 3);
    t3d_tri_sync();
    return true;
}

bool support_echo_renderer_draw(
    SupportEchoRenderer *renderer,
    N64GameSupportEchoKind kind,
    uint32_t frame_index,
    float x,
    float y,
    float z,
    float scale,
    float yaw
)
{
    if (!draw_arguments_ok(renderer, kind, frame_index) || scale <= 0.0f) {
        return false;
    }
    SupportEchoInstance *const instance = &renderer->instances[kind];
    const size_t matrix_slot =
        (size_t)kind * (size_t)renderer->buffer_count + frame_index;
    const float scales[3] = {scale, scale, scale};
    const float rotations[3] = {0.0f, yaw, 0.0f};
    const float translation[3] = {x, y, z};
    t3d_mat4fp_from_srt_euler(
        &renderer->model_matrices[matrix_slot], scales, rotations, translation
    );
    t3d_skeleton_use(&instance->skeleton);
    t3d_matrix_push(&renderer->model_matrices[matrix_slot]);
    rspq_block_run(instance->draw_block);
    t3d_matrix_pop(1);
    return true;
}

static void destroy_instance(SupportEchoInstance *instance)
{
    if (instance->draw_block != NULL) {
        rspq_block_free(instance->draw_block);
        instance->draw_block = NULL;
    }
    t3d_anim_destroy(&instance->hit_anim);
    t3d_anim_destroy(&instance->reposition_anim);
    t3d_anim_destroy(&instance->idle_anim);
    t3d_skeleton_destroy(&instance->hit_pose);
    t3d_skeleton_destroy(&instance->reposition_pose);
    t3d_skeleton_destroy(&instance->idle_pose);
    t3d_skeleton_destroy(&instance->skeleton);
    if (instance->model != NULL) {
        t3d_model_free(instance->model);
        instance->model = NULL;
    }
    if (instance->assets.lifetime != NULL) {
        (void)support_echo_render_assets_unload(&instance->assets);
    }
    *instance = (SupportEchoInstance){0};
}

void support_echo_renderer_destroy(SupportEchoRenderer *renderer)
{
    if (renderer == NULL) {
        return;
    }
    rspq_wait();
    for (unsigned index = 0U;
         index < (unsigned)N64GAME_SUPPORT_ECHO_COUNT;
         ++index) {
        destroy_instance(&renderer->instances[index]);
    }
    if (renderer->shadow_vertices != NULL) {
        free_uncached(renderer->shadow_vertices);
    }
    if (renderer->shadow_matrices != NULL) {
        free_uncached(renderer->shadow_matrices);
    }
    if (renderer->model_matrices != NULL) {
        free_uncached(renderer->model_matrices);
    }
    *renderer = (SupportEchoRenderer){0};
}
