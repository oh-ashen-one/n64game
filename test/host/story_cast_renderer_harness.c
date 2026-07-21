#include <assert.h>
#include <limits.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "story_cast_renderer.h"

enum {
    TEST_MODEL_COUNT = 3,
    TEST_MAX_ANIMATIONS = 4,
};

struct T3DModel {
    const char *path;
    const char *animation_names[TEST_MAX_ANIMATIONS];
    T3DChunkAnim animations[TEST_MAX_ANIMATIONS];
    T3DChunkSkeleton skeleton;
    uint32_t animation_count;
    unsigned kind;
    bool loaded;
};

static const char *const EXPECTED_PATHS[TEST_MODEL_COUNT] = {
    "rom:/chr/chr.sera_venn/sera_venn_distance.t3dm",
    "rom:/chr/chr.tavi/tavi_distance.t3dm",
    "rom:/prop/prop.annex.beacon_decoder/annex_beacon_decoder.t3dm",
};

static const char *const EXPECTED_NAMES[TEST_MODEL_COUNT][TEST_MAX_ANIMATIONS] = {
    {"idle_a", "diagnostic_scan", "explain_starter", "react_fracture"},
    {"idle_a", "greet", "listen", "reaction"},
    {"idle_aim", "beacon_acquire", "fracture", NULL},
};

static const uint16_t EXPECTED_BONES[TEST_MODEL_COUNT] = {22U, 20U, 10U};
static const uint32_t EXPECTED_COUNTS[TEST_MODEL_COUNT] = {4U, 4U, 3U};

static T3DModel models[TEST_MODEL_COUNT];
static T3DBone skeleton_bones[TEST_MODEL_COUNT];
static T3DMat4FP skeleton_matrices[TEST_MODEL_COUNT];
static rspq_block_t blocks[TEST_MODEL_COUNT];
static T3DModel *recording_model;
static unsigned bad_model_kind = UINT_MAX;
static bool fail_malloc;
static float cue_duration = 3.0f;
static unsigned allocation_count;
static unsigned free_count;
static unsigned model_load_count;
static unsigned model_free_count;
static unsigned block_begin_count;
static unsigned block_free_count;
static unsigned block_run_count;
static unsigned wait_count;
static unsigned skeleton_use_count;
static unsigned matrix_build_count;
static unsigned blend_count;
static unsigned wrong_fixed_delta_count;

static void reset_stub_state(float duration)
{
    memset(models, 0, sizeof(models));
    memset(skeleton_bones, 0, sizeof(skeleton_bones));
    memset(skeleton_matrices, 0, sizeof(skeleton_matrices));
    memset(blocks, 0, sizeof(blocks));
    recording_model = NULL;
    bad_model_kind = UINT_MAX;
    fail_malloc = false;
    cue_duration = duration;
    allocation_count = 0U;
    free_count = 0U;
    model_load_count = 0U;
    model_free_count = 0U;
    block_begin_count = 0U;
    block_free_count = 0U;
    block_run_count = 0U;
    wait_count = 0U;
    skeleton_use_count = 0U;
    matrix_build_count = 0U;
    blend_count = 0U;
    wrong_fixed_delta_count = 0U;
}

void debugf(const char *format, ...) { (void)format; }

void *malloc_uncached(size_t size)
{
    if (fail_malloc) {
        return NULL;
    }
    ++allocation_count;
    return malloc(size);
}

void free_uncached(void *pointer)
{
    ++free_count;
    free(pointer);
}

void rspq_block_begin(void)
{
    ++block_begin_count;
    recording_model = NULL;
}

rspq_block_t *rspq_block_end(void)
{
    assert(recording_model != NULL);
    rspq_block_t *const block = &blocks[recording_model->kind];
    block->identifier = recording_model->kind + 1U;
    recording_model = NULL;
    return block;
}

void rspq_block_free(rspq_block_t *block)
{
    assert(block != NULL);
    ++block_free_count;
}

void rspq_block_run(rspq_block_t *block)
{
    assert(block != NULL && block->identifier != 0U);
    ++block_run_count;
}

void rspq_wait(void) { ++wait_count; }

uint32_t t3d_model_get_animation_count(const T3DModel *model)
{
    assert(model != NULL);
    if (model->kind == bad_model_kind) {
        return 0U;
    }
    return model->animation_count;
}

const T3DChunkSkeleton *t3d_model_get_skeleton(const T3DModel *model)
{
    assert(model != NULL);
    return &model->skeleton;
}

T3DChunkAnim *t3d_model_get_animation(const T3DModel *model, const char *name)
{
    assert(model != NULL && name != NULL);
    for (uint32_t index = 0U; index < model->animation_count; ++index) {
        if (strcmp(model->animation_names[index], name) == 0) {
            return (T3DChunkAnim *)&model->animations[index];
        }
    }
    return NULL;
}

T3DModel *t3d_model_load(const char *path)
{
    assert(path != NULL);
    for (unsigned kind = 0U; kind < TEST_MODEL_COUNT; ++kind) {
        if (strcmp(path, EXPECTED_PATHS[kind]) != 0) {
            continue;
        }
        T3DModel *const model = &models[kind];
        assert(!model->loaded);
        model->path = EXPECTED_PATHS[kind];
        model->animation_count = EXPECTED_COUNTS[kind];
        model->skeleton.boneCount = EXPECTED_BONES[kind];
        model->kind = kind;
        model->loaded = true;
        for (uint32_t index = 0U; index < model->animation_count; ++index) {
            model->animation_names[index] = EXPECTED_NAMES[kind][index];
            model->animations[index] = (T3DChunkAnim){
                .duration = index == 0U ? 2.0f : cue_duration,
                .filePath = EXPECTED_NAMES[kind][index],
            };
        }
        ++model_load_count;
        return model;
    }
    return NULL;
}

void t3d_model_free(T3DModel *model)
{
    assert(model != NULL && model->loaded);
    model->loaded = false;
    ++model_free_count;
}

void t3d_model_draw_custom(
    const T3DModel *model,
    T3DModelDrawConf configuration
)
{
    assert(model != NULL);
    assert(configuration.userData == NULL);
    assert(configuration.dynTextureCb == NULL);
    assert(configuration.matrices == t3d_segment_placeholder(
        T3D_SEGMENT_SKELETON
    ));
    recording_model = (T3DModel *)model;
}

T3DSkeleton t3d_skeleton_create_buffered(const T3DModel *model, int buffers)
{
    assert(model != NULL && buffers > 0);
    return (T3DSkeleton){
        .bones = &skeleton_bones[model->kind],
        .boneMatricesFP = &skeleton_matrices[model->kind],
        .skeletonRef = &model->skeleton,
    };
}

T3DSkeleton t3d_skeleton_clone(
    const T3DSkeleton *skeleton,
    bool use_matrices
)
{
    assert(skeleton != NULL && !use_matrices);
    T3DSkeleton clone = *skeleton;
    clone.boneMatricesFP = NULL;
    clone.update_count = 0U;
    return clone;
}

void t3d_skeleton_blend(
    const T3DSkeleton *result,
    const T3DSkeleton *left,
    const T3DSkeleton *right,
    float factor
)
{
    assert(result != NULL && left != NULL && right != NULL);
    assert(factor >= 0.0f && factor <= 1.0f);
    ++blend_count;
}

void t3d_skeleton_update(T3DSkeleton *skeleton)
{
    assert(skeleton != NULL);
    ++skeleton->update_count;
}

void t3d_skeleton_destroy(T3DSkeleton *skeleton)
{
    assert(skeleton != NULL);
    memset(skeleton, 0, sizeof(*skeleton));
}

void t3d_skeleton_use(const T3DSkeleton *skeleton)
{
    assert(skeleton != NULL && skeleton->boneMatricesFP != NULL);
    ++skeleton_use_count;
}

T3DAnim t3d_anim_create(const T3DModel *model, const char *name)
{
    T3DChunkAnim *const definition = t3d_model_get_animation(model, name);
    if (definition == NULL) {
        return (T3DAnim){0};
    }
    return (T3DAnim){
        .animRef = definition,
        .file = (FILE *)(uintptr_t)1U,
        .isPlaying = UINT8_C(1),
        .isLooping = UINT8_C(1),
    };
}

void t3d_anim_attach(T3DAnim *animation, const T3DSkeleton *skeleton)
{
    assert(animation != NULL && animation->animRef != NULL);
    assert(skeleton != NULL && skeleton->bones != NULL);
}

void t3d_anim_update(T3DAnim *animation, float delta_seconds)
{
    assert(animation != NULL && animation->animRef != NULL);
    if (fabsf(delta_seconds - (2.0f / 30.0f)) > 0.000001f) {
        ++wrong_fixed_delta_count;
    }
    if (animation->isPlaying == 0U) {
        return;
    }
    ++animation->update_count;
    animation->time += delta_seconds;
    if (animation->time >= animation->animRef->duration) {
        animation->time -= animation->animRef->duration;
        if (animation->isLooping == 0U) {
            animation->isPlaying = UINT8_C(0);
        }
    }
}

void t3d_anim_set_time(T3DAnim *animation, float time)
{
    assert(animation != NULL);
    ++animation->set_time_count;
    animation->time = time;
}

void t3d_anim_destroy(T3DAnim *animation)
{
    assert(animation != NULL);
    memset(animation, 0, sizeof(*animation));
}

void t3d_mat4fp_from_srt_euler(
    T3DMat4FP *matrix,
    const float scales[3],
    const float rotations[3],
    const float translation[3]
)
{
    assert(matrix != NULL && scales != NULL && rotations != NULL &&
           translation != NULL);
    ++matrix_build_count;
}

void t3d_matrix_push(const T3DMat4FP *matrix) { assert(matrix != NULL); }
void t3d_matrix_pop(int count) { assert(count == 1); }

static void assert_renderer_cleared(const StoryCastRenderer *renderer)
{
    assert(renderer != NULL);
    assert(!renderer->ready);
    assert(renderer->model_matrices == NULL);
    assert(renderer->buffer_count == 0U);
    assert(!renderer->observed_dialogue_valid);
    for (unsigned index = 0U;
         index < (unsigned)N64GAME_STORY_CAST_COUNT;
         ++index) {
        assert(renderer->instances[index].model == NULL);
        assert(renderer->instances[index].draw_block == NULL);
        assert(!renderer->instances[index].ready);
    }
}

static void test_init_draw_destroy_and_partial_failure(void)
{
    reset_stub_state(3.0f);
    StoryCastRenderer renderer = {0};
    N64GameCore game = {0};
    assert(!story_cast_renderer_init(NULL, 2U));
    assert(!story_cast_renderer_init(&renderer, 0U));
    assert(!story_cast_renderer_init(
        &renderer, (uint32_t)INT_MAX + UINT32_C(1)
    ));
    assert(!story_cast_renderer_update(&renderer, &game));
    assert(!story_cast_renderer_draw(
        &renderer, N64GAME_STORY_CAST_SERA, 0U,
        0.0f, 0.0f, 0.0f, 1.0f, 0.0f
    ));

    assert(story_cast_renderer_init(&renderer, 2U));
    assert(renderer.ready && renderer.buffer_count == 2U);
    assert(allocation_count == 1U);
    assert(model_load_count == TEST_MODEL_COUNT);
    assert(block_begin_count == TEST_MODEL_COUNT);
    for (unsigned index = 0U;
         index < (unsigned)N64GAME_STORY_CAST_COUNT;
         ++index) {
        const StoryCastInstance *const instance = &renderer.instances[index];
        assert(instance->ready);
        assert(instance->active_cue == UINT8_MAX);
        assert(instance->cue_count ==
               (uint8_t)(EXPECTED_COUNTS[index] - UINT32_C(1)));
        assert(instance->skeleton.update_count == 2U);
    }
    assert(!story_cast_renderer_init(&renderer, 2U));
    assert(story_cast_renderer_draw(
        &renderer, N64GAME_STORY_CAST_SERA, 0U,
        1.0f, 2.0f, 3.0f, 0.75f, 0.25f
    ));
    assert(story_cast_renderer_draw(
        &renderer, N64GAME_STORY_CAST_BEACON, 1U,
        -1.0f, 0.0f, 4.0f, 1.25f, -0.5f
    ));
    assert(block_run_count == 2U && skeleton_use_count == 2U);
    assert(matrix_build_count == 2U);
    assert(!story_cast_renderer_draw(
        &renderer, N64GAME_STORY_CAST_COUNT, 0U,
        0.0f, 0.0f, 0.0f, 1.0f, 0.0f
    ));
    assert(!story_cast_renderer_draw(
        &renderer, N64GAME_STORY_CAST_TAVI, 2U,
        0.0f, 0.0f, 0.0f, 1.0f, 0.0f
    ));
    assert(!story_cast_renderer_draw(
        &renderer, N64GAME_STORY_CAST_TAVI, 0U,
        0.0f, 0.0f, 0.0f, 0.0f, 0.0f
    ));
    assert(!story_cast_renderer_draw(
        &renderer, N64GAME_STORY_CAST_TAVI, 0U,
        NAN, 0.0f, 0.0f, 1.0f, 0.0f
    ));
    story_cast_renderer_destroy(&renderer);
    assert_renderer_cleared(&renderer);
    assert(free_count == 1U);
    assert(model_free_count == TEST_MODEL_COUNT);
    assert(block_free_count == TEST_MODEL_COUNT);
    assert(wait_count == 1U);

    reset_stub_state(3.0f);
    bad_model_kind = 1U;
    renderer = (StoryCastRenderer){0};
    assert(!story_cast_renderer_init(&renderer, 2U));
    assert_renderer_cleared(&renderer);
    assert(allocation_count == 1U && free_count == 1U);
    assert(model_load_count == 2U && model_free_count == 2U);
    assert(block_free_count == 1U && wait_count == 1U);

    reset_stub_state(3.0f);
    fail_malloc = true;
    renderer = (StoryCastRenderer){0};
    assert(!story_cast_renderer_init(&renderer, 2U));
    assert_renderer_cleared(&renderer);
    assert(allocation_count == 0U && free_count == 0U);
    assert(model_load_count == 0U && wait_count == 1U);
}

static void set_dialogue(
    N64GameCore *game,
    N64GameDialogue dialogue,
    uint8_t page
)
{
    game->dialogue = dialogue;
    game->dialogue_page = page;
}

static bool update_story_renderer(
    StoryCastRenderer *renderer,
    N64GameCore *game
)
{
    const bool updated = story_cast_renderer_update(renderer, game);
    ++game->scene_ticks;
    return updated;
}

/* Subsequent behavior tests advance one real 30 Hz scene tick per call. */
#define story_cast_renderer_update(renderer_, game_) \
    update_story_renderer((renderer_), (game_))

static void test_dialogue_edge_dispatch_and_duplicate_suppression(void)
{
    reset_stub_state(3.0f);
    StoryCastRenderer renderer = {0};
    N64GameCore game = {0};
    assert(story_cast_renderer_init(&renderer, 2U));
    assert(story_cast_renderer_update(&renderer, &game));

    StoryCastInstance *const sera =
        &renderer.instances[N64GAME_STORY_CAST_SERA];
    StoryCastInstance *const tavi =
        &renderer.instances[N64GAME_STORY_CAST_TAVI];
    StoryCastInstance *const beacon =
        &renderer.instances[N64GAME_STORY_CAST_BEACON];

    const uint32_t sera_explain_origin = sera->cue_anims[1].set_time_count;
    set_dialogue(&game, N64GAME_DIALOGUE_SERA_INTRO, UINT8_C(1));
    assert(story_cast_renderer_update(&renderer, &game));
    assert(sera->active_cue == UINT8_C(1));
    assert(sera->cue_anims[1].set_time_count == sera_explain_origin + 1U);
    assert(story_cast_renderer_update(&renderer, &game));
    assert(sera->cue_anims[1].set_time_count == sera_explain_origin + 1U);

    set_dialogue(&game, N64GAME_DIALOGUE_SERA_INTRO, UINT8_C(2));
    assert(story_cast_renderer_update(&renderer, &game));
    assert(sera->active_cue == UINT8_C(1));
    assert(t3d_anim_is_playing(&sera->cue_anims[1]));

    set_dialogue(&game, N64GAME_DIALOGUE_SERA_TRIAL, UINT8_C(0));
    assert(story_cast_renderer_update(&renderer, &game));
    assert(sera->active_cue == UINT8_C(0));

    set_dialogue(&game, N64GAME_DIALOGUE_TAVI_INTRO, UINT8_C(0));
    assert(story_cast_renderer_update(&renderer, &game));
    assert(tavi->active_cue == UINT8_C(0));
    assert(sera->active_cue == UINT8_C(0));

    const uint32_t tavi_listen_origin = tavi->cue_anims[1].set_time_count;
    const uint32_t beacon_acquire_origin = beacon->cue_anims[0].set_time_count;
    set_dialogue(&game, N64GAME_DIALOGUE_BEACON_HOOK, UINT8_C(0));
    assert(story_cast_renderer_update(&renderer, &game));
    assert(tavi->active_cue == UINT8_C(1));
    assert(beacon->active_cue == UINT8_C(0));
    assert(tavi->cue_anims[1].set_time_count == tavi_listen_origin + 1U);
    assert(beacon->cue_anims[0].set_time_count == beacon_acquire_origin + 1U);
    assert(story_cast_renderer_update(&renderer, &game));
    assert(tavi->cue_anims[1].set_time_count == tavi_listen_origin + 1U);
    assert(beacon->cue_anims[0].set_time_count == beacon_acquire_origin + 1U);

    const uint32_t sera_react_origin = sera->cue_anims[2].set_time_count;
    const uint32_t tavi_react_origin = tavi->cue_anims[2].set_time_count;
    const uint32_t beacon_fracture_origin = beacon->cue_anims[1].set_time_count;
    set_dialogue(&game, N64GAME_DIALOGUE_BEACON_HOOK, UINT8_C(4));
    assert(story_cast_renderer_update(&renderer, &game));
    assert(sera->active_cue == UINT8_C(2));
    assert(tavi->active_cue == UINT8_C(2));
    assert(beacon->active_cue == UINT8_C(1));
    assert(sera->cue_anims[2].set_time_count == sera_react_origin + 1U);
    assert(tavi->cue_anims[2].set_time_count == tavi_react_origin + 1U);
    assert(beacon->cue_anims[1].set_time_count == beacon_fracture_origin + 1U);
    assert(story_cast_renderer_update(&renderer, &game));
    assert(sera->cue_anims[2].set_time_count == sera_react_origin + 1U);

    set_dialogue(&game, N64GAME_DIALOGUE_BEACON_HOOK, UINT8_C(3));
    assert(story_cast_renderer_update(&renderer, &game));
    assert(sera->active_cue == UINT8_C(2));
    assert(tavi->active_cue == UINT8_C(2));
    assert(beacon->active_cue == UINT8_C(1));
    set_dialogue(&game, N64GAME_DIALOGUE_BEACON_HOOK, UINT8_C(4));
    assert(story_cast_renderer_update(&renderer, &game));
    assert(sera->cue_anims[2].set_time_count == sera_react_origin + 2U);
    assert(tavi->cue_anims[2].set_time_count == tavi_react_origin + 2U);
    assert(beacon->cue_anims[1].set_time_count ==
           beacon_fracture_origin + 2U);
    assert(wrong_fixed_delta_count == 0U);
    story_cast_renderer_destroy(&renderer);
}

static void test_fixed_step_one_shot_completion_without_uncued_cancel(void)
{
    reset_stub_state(0.11f);
    StoryCastRenderer renderer = {0};
    N64GameCore game = {0};
    assert(story_cast_renderer_init(&renderer, 2U));
    StoryCastInstance *const sera =
        &renderer.instances[N64GAME_STORY_CAST_SERA];

    set_dialogue(&game, N64GAME_DIALOGUE_SERA_TRIAL, UINT8_C(0));
    assert(story_cast_renderer_update(&renderer, &game));
    assert(sera->active_cue == UINT8_C(0));
    const uint32_t started_count = sera->cue_anims[0].set_time_count;

    set_dialogue(&game, N64GAME_DIALOGUE_SERA_TRIAL, UINT8_C(1));
    assert(story_cast_renderer_update(&renderer, &game));
    assert(sera->active_cue == UINT8_C(0));
    assert(sera->cue_anims[0].set_time_count == started_count);
    assert(story_cast_renderer_update(&renderer, &game));
    assert(sera->active_cue == UINT8_MAX);
    assert(sera->cue_anims[0].update_count == 2U);
    for (unsigned index = 0U;
         index < (unsigned)N64GAME_STORY_CAST_COUNT;
         ++index) {
        assert(renderer.instances[index].idle_anim.update_count == 2U);
        assert(renderer.instances[index].skeleton.update_count == 4U);
    }
    assert(wrong_fixed_delta_count == 0U);
    assert(blend_count == TEST_MODEL_COUNT + TEST_MODEL_COUNT * 2U);
    story_cast_renderer_destroy(&renderer);
}

int main(void)
{
    test_init_draw_destroy_and_partial_failure();
    test_dialogue_edge_dispatch_and_duplicate_suppression();
    test_fixed_step_one_shot_completion_without_uncued_cancel();
    puts("story cast renderer behavior harness: PASS");
    return 0;
}
