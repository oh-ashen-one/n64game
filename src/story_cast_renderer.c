#include "story_cast_renderer.h"

#include <limits.h>
#include <math.h>
#include <stddef.h>

enum {
    SERA_BONE_COUNT = 22,
    TAVI_BONE_COUNT = 20,
    BEACON_BONE_COUNT = 10,
    NO_ACTIVE_CUE = UINT8_MAX,
};

typedef struct {
    const char *debug_name;
    const char *model_path;
    const char *idle_name;
    const char *cue_names[N64GAME_STORY_CAST_MAX_CUES];
    uint16_t bone_count;
    uint8_t cue_count;
} StoryCastProfile;

static const StoryCastProfile PROFILES[N64GAME_STORY_CAST_COUNT] = {
    [N64GAME_STORY_CAST_SERA] = {
        .debug_name = "sera",
        .model_path = "rom:/chr/chr.sera_venn/sera_venn_distance.t3dm",
        .idle_name = "idle_a",
        .cue_names = {
            "diagnostic_scan",
            "explain_starter",
            "react_fracture",
        },
        .bone_count = SERA_BONE_COUNT,
        .cue_count = UINT8_C(3),
    },
    [N64GAME_STORY_CAST_TAVI] = {
        .debug_name = "tavi",
        .model_path = "rom:/chr/chr.tavi/tavi_distance.t3dm",
        .idle_name = "idle_a",
        .cue_names = {
            "greet",
            "listen",
            "reaction",
        },
        .bone_count = TAVI_BONE_COUNT,
        .cue_count = UINT8_C(3),
    },
    [N64GAME_STORY_CAST_BEACON] = {
        .debug_name = "beacon",
        .model_path =
            "rom:/prop/prop.annex.beacon_decoder/annex_beacon_decoder.t3dm",
        .idle_name = "idle_aim",
        .cue_names = {
            "beacon_acquire",
            "fracture",
            NULL,
        },
        .bone_count = BEACON_BONE_COUNT,
        .cue_count = UINT8_C(2),
    },
};

static bool animation_definition_ok(
    const T3DModel *model,
    const char *name
)
{
    if (name == NULL || name[0] == '\0') {
        return false;
    }
    const T3DChunkAnim *const animation = t3d_model_get_animation(model, name);
    return animation != NULL && animation->duration > 0.0f &&
        animation->filePath != NULL && animation->filePath[0] != '\0';
}

static bool model_contract_ok(
    const T3DModel *model,
    const StoryCastProfile *profile
)
{
    if (model == NULL || profile == NULL ||
        t3d_model_get_animation_count(model) !=
            UINT32_C(1) + (uint32_t)profile->cue_count) {
        return false;
    }
    const T3DChunkSkeleton *const skeleton = t3d_model_get_skeleton(model);
    if (skeleton == NULL || skeleton->boneCount != profile->bone_count ||
        !animation_definition_ok(model, profile->idle_name)) {
        return false;
    }
    for (uint8_t index = 0U; index < profile->cue_count; ++index) {
        if (!animation_definition_ok(model, profile->cue_names[index])) {
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
    return skeleton != NULL && skeleton->bones != NULL &&
        skeleton->boneMatricesFP != NULL && skeleton->skeletonRef != NULL &&
        skeleton->skeletonRef->boneCount == bone_count;
}

static bool pose_contract_ok(const T3DSkeleton *pose, uint16_t bone_count)
{
    return pose != NULL && pose->bones != NULL && pose->skeletonRef != NULL &&
        pose->skeletonRef->boneCount == bone_count;
}

static bool animation_stream_ok(const T3DAnim *animation)
{
    return animation != NULL && animation->animRef != NULL &&
        animation->file != NULL;
}

static bool setup_instance(
    StoryCastInstance *instance,
    StoryCastKind kind,
    uint32_t buffer_count
)
{
    const StoryCastProfile *const profile = &PROFILES[(unsigned)kind];
    instance->model = t3d_model_load(profile->model_path);
    if (!model_contract_ok(instance->model, profile)) {
        debugf(
            "[%s] story-cast model contract failed: %s\n",
            profile->debug_name,
            profile->model_path
        );
        return false;
    }

    instance->skeleton = t3d_skeleton_create_buffered(
        instance->model, (int)buffer_count
    );
    if (!skeleton_contract_ok(&instance->skeleton, profile->bone_count)) {
        debugf("[%s] story-cast skeleton allocation failed\n",
               profile->debug_name);
        return false;
    }

    instance->idle_pose = t3d_skeleton_clone(&instance->skeleton, false);
    if (!pose_contract_ok(&instance->idle_pose, profile->bone_count)) {
        debugf("[%s] story-cast idle-pose allocation failed\n",
               profile->debug_name);
        return false;
    }
    for (uint8_t index = 0U; index < profile->cue_count; ++index) {
        instance->cue_poses[index] = t3d_skeleton_clone(
            &instance->skeleton, false
        );
        if (!pose_contract_ok(
                &instance->cue_poses[index], profile->bone_count
            )) {
            debugf("[%s] story-cast cue-pose allocation failed\n",
                   profile->debug_name);
            return false;
        }
    }

    instance->idle_anim = t3d_anim_create(
        instance->model, profile->idle_name
    );
    if (!animation_stream_ok(&instance->idle_anim)) {
        debugf("[%s] story-cast idle stream failed\n", profile->debug_name);
        return false;
    }
    t3d_anim_attach(&instance->idle_anim, &instance->idle_pose);
    t3d_anim_set_looping(&instance->idle_anim, true);
    t3d_anim_set_playing(&instance->idle_anim, true);
    t3d_anim_set_time(&instance->idle_anim, 0.0f);

    for (uint8_t index = 0U; index < profile->cue_count; ++index) {
        instance->cue_anims[index] = t3d_anim_create(
            instance->model, profile->cue_names[index]
        );
        if (!animation_stream_ok(&instance->cue_anims[index])) {
            debugf("[%s] story-cast cue stream failed\n",
                   profile->debug_name);
            return false;
        }
        t3d_anim_attach(
            &instance->cue_anims[index], &instance->cue_poses[index]
        );
        t3d_anim_set_looping(&instance->cue_anims[index], false);
        t3d_anim_set_time(&instance->cue_anims[index], 0.0f);
        t3d_anim_set_playing(&instance->cue_anims[index], false);
    }

    t3d_skeleton_blend(
        &instance->skeleton,
        &instance->idle_pose,
        &instance->idle_pose,
        0.0f
    );
    for (uint32_t index = 0U; index < buffer_count; ++index) {
        t3d_skeleton_update(&instance->skeleton);
    }

    rspq_block_begin();
    t3d_model_draw_custom(
        instance->model,
        (T3DModelDrawConf){
            .matrices = (const T3DMat4FP *)t3d_segment_placeholder(
                T3D_SEGMENT_SKELETON
            ),
        }
    );
    instance->draw_block = rspq_block_end();
    if (instance->draw_block == NULL) {
        debugf("[%s] story-cast draw-block recording failed\n",
               profile->debug_name);
        return false;
    }

    instance->cue_count = profile->cue_count;
    instance->active_cue = (uint8_t)NO_ACTIVE_CUE;
    instance->ready = true;
    return true;
}

bool story_cast_renderer_init(
    StoryCastRenderer *renderer,
    uint32_t buffer_count
)
{
    if (renderer == NULL || buffer_count == 0U ||
        buffer_count > (uint32_t)INT_MAX ||
        renderer->model_matrices != NULL || renderer->ready) {
        return false;
    }
    if (buffer_count >
        UINT32_MAX / (uint32_t)N64GAME_STORY_CAST_COUNT) {
        return false;
    }
    const size_t matrix_count =
        (size_t)buffer_count * (size_t)N64GAME_STORY_CAST_COUNT;
    if (matrix_count > SIZE_MAX / sizeof(T3DMat4FP)) {
        return false;
    }
    renderer->model_matrices = malloc_uncached(
        sizeof(T3DMat4FP) * matrix_count
    );
    renderer->buffer_count = buffer_count;
    if (renderer->model_matrices == NULL) {
        story_cast_renderer_destroy(renderer);
        return false;
    }

    for (unsigned index = 0U;
         index < (unsigned)N64GAME_STORY_CAST_COUNT;
         ++index) {
        if (!setup_instance(
                &renderer->instances[index],
                (StoryCastKind)index,
                buffer_count
            )) {
            story_cast_renderer_destroy(renderer);
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

static void start_cue(StoryCastInstance *instance, uint8_t cue)
{
    if (instance == NULL || cue >= instance->cue_count) {
        return;
    }
    if (instance->active_cue < instance->cue_count) {
        t3d_anim_set_playing(
            &instance->cue_anims[instance->active_cue], false
        );
    }
    t3d_anim_set_time(&instance->cue_anims[cue], 0.0f);
    t3d_anim_set_playing(&instance->cue_anims[cue], true);
    instance->active_cue = cue;
}

static void dispatch_dialogue_edge(
    StoryCastRenderer *renderer,
    N64GameDialogue dialogue,
    uint8_t page
)
{
    if (dialogue == N64GAME_DIALOGUE_SERA_INTRO && page == UINT8_C(1)) {
        start_cue(&renderer->instances[N64GAME_STORY_CAST_SERA], UINT8_C(1));
    } else if (dialogue == N64GAME_DIALOGUE_SERA_TRIAL && page == UINT8_C(0)) {
        start_cue(&renderer->instances[N64GAME_STORY_CAST_SERA], UINT8_C(0));
    } else if (dialogue == N64GAME_DIALOGUE_TAVI_INTRO && page == UINT8_C(0)) {
        start_cue(&renderer->instances[N64GAME_STORY_CAST_TAVI], UINT8_C(0));
    } else if (dialogue == N64GAME_DIALOGUE_BEACON_HOOK &&
               page == UINT8_C(0)) {
        start_cue(&renderer->instances[N64GAME_STORY_CAST_TAVI], UINT8_C(1));
        start_cue(&renderer->instances[N64GAME_STORY_CAST_BEACON], UINT8_C(0));
    } else if (dialogue == N64GAME_DIALOGUE_BEACON_HOOK &&
               page == UINT8_C(4)) {
        start_cue(&renderer->instances[N64GAME_STORY_CAST_SERA], UINT8_C(2));
        start_cue(&renderer->instances[N64GAME_STORY_CAST_TAVI], UINT8_C(2));
        start_cue(&renderer->instances[N64GAME_STORY_CAST_BEACON], UINT8_C(1));
    }
}

static void update_instance(
    StoryCastInstance *instance,
    float delta_seconds
)
{
    static const float BLEND_SECONDS = 0.10f;
    t3d_anim_update(&instance->idle_anim, delta_seconds);

    T3DSkeleton *motion_pose = &instance->idle_pose;
    float motion_blend = 0.0f;
    if (instance->active_cue < instance->cue_count) {
        T3DAnim *const cue_anim =
            &instance->cue_anims[instance->active_cue];
        T3DSkeleton *const cue_pose =
            &instance->cue_poses[instance->active_cue];
        t3d_anim_update(cue_anim, delta_seconds);
        if (t3d_anim_is_playing(cue_anim)) {
            const float time = t3d_anim_get_time(cue_anim);
            const float remaining = t3d_anim_get_length(cue_anim) - time;
            const float blend_in = clamp_unit(time / BLEND_SECONDS);
            const float blend_out = clamp_unit(remaining / BLEND_SECONDS);
            motion_pose = cue_pose;
            motion_blend = fminf(blend_in, blend_out);
        } else {
            instance->active_cue = (uint8_t)NO_ACTIVE_CUE;
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

bool story_cast_renderer_update(
    StoryCastRenderer *renderer,
    const N64GameCore *game
)
{
    static const float ANIMATION_DELTA_SECONDS = 2.0f / 30.0f;
    if (renderer == NULL || !renderer->ready || game == NULL) {
        return false;
    }
    if (!renderer->observed_dialogue_valid ||
        renderer->observed_dialogue != game->dialogue ||
        renderer->observed_dialogue_page != game->dialogue_page) {
        renderer->observed_dialogue = game->dialogue;
        renderer->observed_dialogue_page = game->dialogue_page;
        renderer->observed_dialogue_valid = true;
        dispatch_dialogue_edge(renderer, game->dialogue, game->dialogue_page);
    }
    /*
     * Preserve 30 Hz gameplay and cue-edge recognition while sampling the
     * authored NPC animation at a deliberate N64-style 15 Hz cadence.
     */
    if ((game->scene_ticks & UINT32_C(1)) != 0U) {
        return true;
    }
    for (unsigned index = 0U;
         index < (unsigned)N64GAME_STORY_CAST_COUNT;
         ++index) {
        update_instance(
            &renderer->instances[index], ANIMATION_DELTA_SECONDS
        );
    }
    return true;
}

bool story_cast_renderer_draw(
    StoryCastRenderer *renderer,
    StoryCastKind kind,
    uint32_t frame_index,
    float x,
    float y,
    float z,
    float scale,
    float yaw
)
{
    if (renderer == NULL || !renderer->ready ||
        (unsigned)kind >= (unsigned)N64GAME_STORY_CAST_COUNT ||
        frame_index >= renderer->buffer_count || !(scale > 0.0f) ||
        !isfinite(x) || !isfinite(y) || !isfinite(z) || !isfinite(scale) ||
        !isfinite(yaw) || !renderer->instances[kind].ready) {
        return false;
    }
    StoryCastInstance *const instance = &renderer->instances[kind];
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

static void destroy_instance(StoryCastInstance *instance)
{
    if (instance->draw_block != NULL) {
        rspq_block_free(instance->draw_block);
        instance->draw_block = NULL;
    }
    for (unsigned index = 0U;
         index < (unsigned)N64GAME_STORY_CAST_MAX_CUES;
         ++index) {
        t3d_anim_destroy(&instance->cue_anims[index]);
    }
    t3d_anim_destroy(&instance->idle_anim);
    for (unsigned index = 0U;
         index < (unsigned)N64GAME_STORY_CAST_MAX_CUES;
         ++index) {
        t3d_skeleton_destroy(&instance->cue_poses[index]);
    }
    t3d_skeleton_destroy(&instance->idle_pose);
    t3d_skeleton_destroy(&instance->skeleton);
    if (instance->model != NULL) {
        t3d_model_free(instance->model);
        instance->model = NULL;
    }
    *instance = (StoryCastInstance){0};
}

void story_cast_renderer_destroy(StoryCastRenderer *renderer)
{
    if (renderer == NULL) {
        return;
    }
    rspq_wait();
    for (unsigned index = 0U;
         index < (unsigned)N64GAME_STORY_CAST_COUNT;
         ++index) {
        destroy_instance(&renderer->instances[index]);
    }
    if (renderer->model_matrices != NULL) {
        free_uncached(renderer->model_matrices);
    }
    *renderer = (StoryCastRenderer){0};
}
