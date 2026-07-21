#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "support_echo_renderer.h"

struct T3DModel { int unused; };

static T3DChunkAnim idle_definitions[N64GAME_SUPPORT_ECHO_COUNT];
static T3DChunkAnim reposition_definitions[N64GAME_SUPPORT_ECHO_COUNT];
static T3DChunkAnim hit_definitions[N64GAME_SUPPORT_ECHO_COUNT];

void debugf(const char *format, ...) { (void)format; }
void *malloc_uncached(size_t size) { return malloc(size); }
void free_uncached(void *pointer) { free(pointer); }
void rspq_block_begin(void) {}
rspq_block_t *rspq_block_end(void) { static rspq_block_t block; return &block; }
void rspq_block_free(rspq_block_t *block) { (void)block; }
void rspq_block_run(rspq_block_t *block) { (void)block; }
void rspq_wait(void) {}
void rdpq_set_mode_standard(void) {}
void rdpq_mode_tlut(int mode) { (void)mode; }
void rdpq_mode_filter(int mode) { (void)mode; }
void rdpq_mode_zbuf(bool compare, bool write) { (void)compare; (void)write; }
void rdpq_mode_combiner(uint64_t mode) { (void)mode; }
void rdpq_mode_blender(uint64_t mode) { (void)mode; }
void rdpq_set_prim_color(uint32_t color) { (void)color; }

uint32_t t3d_model_get_animation_count(const T3DModel *model)
{
    (void)model;
    return 3U;
}

const T3DChunkSkeleton *t3d_model_get_skeleton(const T3DModel *model)
{
    static const T3DChunkSkeleton skeleton = {.boneCount = 20U};
    (void)model;
    return &skeleton;
}

T3DChunkAnim *t3d_model_get_animation(const T3DModel *model, const char *name)
{
    static T3DChunkAnim animation = {.duration = 1.0f, .filePath = "stub"};
    (void)model;
    (void)name;
    return &animation;
}

T3DModel *t3d_model_load(const char *path)
{
    static T3DModel model;
    (void)path;
    return &model;
}

void t3d_model_free(T3DModel *model) { (void)model; }
void t3d_model_draw_custom(const T3DModel *model, T3DModelDrawConf configuration)
{
    (void)model;
    (void)configuration;
}

T3DSkeleton t3d_skeleton_create_buffered(const T3DModel *model, int buffers)
{
    static T3DBone bone;
    static T3DMat4FP matrix;
    static const T3DChunkSkeleton definition = {.boneCount = 20U};
    (void)model;
    (void)buffers;
    return (T3DSkeleton){
        .bones = &bone,
        .boneMatricesFP = &matrix,
        .skeletonRef = &definition,
    };
}

T3DSkeleton t3d_skeleton_clone(const T3DSkeleton *skeleton, bool use_matrices)
{
    T3DSkeleton clone = *skeleton;
    (void)use_matrices;
    clone.boneMatricesFP = NULL;
    return clone;
}

void t3d_skeleton_blend(
    const T3DSkeleton *result,
    const T3DSkeleton *left,
    const T3DSkeleton *right,
    float factor
)
{
    (void)result;
    (void)left;
    (void)right;
    assert(factor >= 0.0f && factor <= 1.0f);
}

void t3d_skeleton_update(T3DSkeleton *skeleton) { ++skeleton->update_count; }
void t3d_skeleton_destroy(T3DSkeleton *skeleton) { memset(skeleton, 0, sizeof(*skeleton)); }
void t3d_skeleton_use(const T3DSkeleton *skeleton) { (void)skeleton; }

T3DAnim t3d_anim_create(const T3DModel *model, const char *name)
{
    static T3DChunkAnim definition = {.duration = 1.0f, .filePath = "stub"};
    (void)model;
    (void)name;
    return (T3DAnim){
        .animRef = &definition,
        .file = (FILE *)(uintptr_t)1U,
        .isPlaying = UINT8_C(1),
        .isLooping = UINT8_C(1),
    };
}

void t3d_anim_attach(T3DAnim *animation, const T3DSkeleton *skeleton)
{
    (void)animation;
    (void)skeleton;
}

void t3d_anim_update(T3DAnim *animation, float delta_seconds)
{
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
    ++animation->set_time_count;
    animation->time = time;
}

void t3d_anim_destroy(T3DAnim *animation) { memset(animation, 0, sizeof(*animation)); }

uint16_t t3d_vert_pack_normal(const fm_vec3_t *normal) { (void)normal; return 0U; }
void t3d_mat4fp_from_srt_euler(
    T3DMat4FP *matrix,
    const float scales[3],
    const float rotations[3],
    const float translation[3]
)
{
    (void)matrix;
    (void)scales;
    (void)rotations;
    (void)translation;
}
void t3d_state_set_drawflags(uint32_t flags) { (void)flags; }
void t3d_matrix_push(const T3DMat4FP *matrix) { (void)matrix; }
void t3d_matrix_pop(int count) { (void)count; }
void t3d_vert_load(const T3DVertPacked *vertices, int destination, int count)
{
    (void)vertices;
    (void)destination;
    (void)count;
}
void t3d_tri_draw(int first, int second, int third)
{
    (void)first;
    (void)second;
    (void)third;
}
void t3d_tri_sync(void) {}

bool support_echo_render_assets_load(
    SupportEchoRenderAssets *assets,
    N64GameSupportEchoKind kind
)
{
    (void)assets;
    (void)kind;
    return true;
}

void support_echo_render_assets_dynamic_texture_cb(
    void *user_data,
    const T3DMaterial *material,
    rdpq_texparms_t *tile_parameters,
    rdpq_tile_t tile
)
{
    (void)user_data;
    (void)material;
    (void)tile_parameters;
    (void)tile;
}

bool support_echo_render_assets_upload_blob_shadow(
    SupportEchoRenderAssets *assets,
    rdpq_tile_t tile,
    const rdpq_texparms_t *tile_parameters
)
{
    (void)assets;
    (void)tile;
    (void)tile_parameters;
    return true;
}

bool support_echo_render_assets_callback_ok(const SupportEchoRenderAssets *assets)
{
    (void)assets;
    return true;
}

bool support_echo_render_assets_unload(SupportEchoRenderAssets *assets)
{
    (void)assets;
    return true;
}

static void initialize_renderer(
    SupportEchoRenderer *renderer,
    float reposition_duration,
    float hit_duration
)
{
    memset(renderer, 0, sizeof(*renderer));
    renderer->ready = true;
    renderer->buffer_count = 2U;
    for (unsigned index = 0U;
         index < (unsigned)N64GAME_SUPPORT_ECHO_COUNT;
         ++index) {
        idle_definitions[index] = (T3DChunkAnim){
            .duration = 2.0f,
            .filePath = "idle",
        };
        reposition_definitions[index] = (T3DChunkAnim){
            .duration = reposition_duration,
            .filePath = "reposition",
        };
        hit_definitions[index] = (T3DChunkAnim){
            .duration = hit_duration,
            .filePath = "hit",
        };
        SupportEchoInstance *const instance = &renderer->instances[index];
        instance->ready = true;
        instance->motion = N64GAME_SUPPORT_ECHO_MOTION_IDLE;
        instance->idle_anim = (T3DAnim){
            .animRef = &idle_definitions[index],
            .isPlaying = UINT8_C(1),
            .isLooping = UINT8_C(1),
        };
        instance->reposition_anim = (T3DAnim){
            .animRef = &reposition_definitions[index],
        };
        instance->hit_anim = (T3DAnim){
            .animRef = &hit_definitions[index],
        };
    }
}

static N64GameBattle initialized_battle(void)
{
    N64GameBattle battle = {0};
    battle.actors[0].player_side = true;
    battle.actors[1].player_side = true;
    battle.actors[2].player_side = false;
    battle.actors[3].player_side = false;
    return battle;
}

static void set_damage_event(
    N64GameBattle *battle,
    uint32_t serial,
    uint8_t actor,
    uint8_t target
)
{
    battle->event_serial = serial;
    battle->last_event = (N64GameBattleEvent){
        .happened = true,
        .actor = actor,
        .target = target,
        .hp_delta = -8,
    };
}

static void test_target_all_side_mapping_and_duplicate_suppression(void)
{
    SupportEchoRenderer renderer;
    initialize_renderer(&renderer, 1.0f, 1.0f);
    N64GameBattle battle = initialized_battle();

    set_damage_event(&battle, 1U, 0U, N64GAME_TARGET_ALL);
    assert(support_echo_renderer_update(&renderer, &battle));
    assert(renderer.instances[0].motion == N64GAME_SUPPORT_ECHO_MOTION_IDLE);
    assert(renderer.instances[1].motion == N64GAME_SUPPORT_ECHO_MOTION_HIT);
    assert(renderer.instances[2].motion == N64GAME_SUPPORT_ECHO_MOTION_HIT);
    assert(renderer.instances[1].hit_anim.set_time_count == 1U);
    assert(renderer.instances[2].hit_anim.set_time_count == 1U);

    set_damage_event(&battle, 1U, 2U, 1U);
    assert(support_echo_renderer_update(&renderer, &battle));
    assert(renderer.instances[0].motion == N64GAME_SUPPORT_ECHO_MOTION_IDLE);
    assert(renderer.instances[1].hit_anim.set_time_count == 1U);
    assert(renderer.instances[2].hit_anim.set_time_count == 1U);

    set_damage_event(&battle, 2U, 2U, N64GAME_TARGET_ALL);
    assert(support_echo_renderer_update(&renderer, &battle));
    assert(renderer.instances[0].motion == N64GAME_SUPPORT_ECHO_MOTION_HIT);
    assert(renderer.instances[1].motion == N64GAME_SUPPORT_ECHO_MOTION_REPOSITION);
    assert(renderer.instances[2].motion == N64GAME_SUPPORT_ECHO_MOTION_HIT);
}

static void test_reset_and_serial_reuse(void)
{
    SupportEchoRenderer renderer;
    initialize_renderer(&renderer, 1.0f, 1.0f);
    N64GameBattle battle = initialized_battle();

    set_damage_event(&battle, 7U, 3U, 1U);
    assert(support_echo_renderer_update(&renderer, &battle));
    assert(renderer.instances[0].motion == N64GAME_SUPPORT_ECHO_MOTION_HIT);
    assert(renderer.instances[2].motion == N64GAME_SUPPORT_ECHO_MOTION_REPOSITION);

    battle.event_serial = 0U;
    battle.last_event = (N64GameBattleEvent){0};
    assert(support_echo_renderer_update(&renderer, &battle));
    for (unsigned index = 0U;
         index < (unsigned)N64GAME_SUPPORT_ECHO_COUNT;
         ++index) {
        assert(renderer.instances[index].motion == N64GAME_SUPPORT_ECHO_MOTION_IDLE);
        assert(!t3d_anim_is_playing(&renderer.instances[index].reposition_anim));
        assert(!t3d_anim_is_playing(&renderer.instances[index].hit_anim));
    }

    set_damage_event(&battle, 0U, 2U, 1U);
    assert(support_echo_renderer_update(&renderer, &battle));
    for (unsigned index = 0U;
         index < (unsigned)N64GAME_SUPPORT_ECHO_COUNT;
         ++index) {
        assert(renderer.instances[index].motion == N64GAME_SUPPORT_ECHO_MOTION_IDLE);
    }

    set_damage_event(&battle, 1U, 2U, 1U);
    assert(support_echo_renderer_update(&renderer, &battle));
    assert(renderer.instances[0].motion == N64GAME_SUPPORT_ECHO_MOTION_HIT);
    assert(renderer.instances[1].motion == N64GAME_SUPPORT_ECHO_MOTION_REPOSITION);
}

static void test_one_shot_completion_and_knockout_hit_window(void)
{
    SupportEchoRenderer renderer;
    initialize_renderer(&renderer, 0.07f, 0.11f);
    N64GameBattle battle = initialized_battle();
    battle.actors[3].hp = 0;

    set_damage_event(&battle, 1U, 0U, 3U);
    assert(support_echo_renderer_update(&renderer, &battle));
    assert(renderer.instances[2].motion == N64GAME_SUPPORT_ECHO_MOTION_HIT);
    assert(renderer.instances[2].hit_anim.set_time_count == 1U);
    assert(support_echo_renderer_update(&renderer, &battle));
    assert(renderer.instances[2].motion == N64GAME_SUPPORT_ECHO_MOTION_HIT);
    assert(support_echo_renderer_update(&renderer, &battle));
    assert(renderer.instances[2].motion == N64GAME_SUPPORT_ECHO_MOTION_HIT);
    assert(renderer.instances[2].hit_anim.set_time_count == 1U);
    assert(support_echo_renderer_update(&renderer, &battle));
    assert(renderer.instances[2].motion == N64GAME_SUPPORT_ECHO_MOTION_IDLE);

    battle.last_event = (N64GameBattleEvent){
        .happened = true,
        .actor = 1U,
        .target = 1U,
    };
    battle.event_serial = 2U;
    assert(support_echo_renderer_update(&renderer, &battle));
    assert(renderer.instances[0].motion == N64GAME_SUPPORT_ECHO_MOTION_REPOSITION);
    assert(support_echo_renderer_update(&renderer, &battle));
    assert(renderer.instances[0].motion == N64GAME_SUPPORT_ECHO_MOTION_REPOSITION);
    assert(support_echo_renderer_update(&renderer, &battle));
    assert(renderer.instances[0].motion == N64GAME_SUPPORT_ECHO_MOTION_IDLE);
    assert(renderer.instances[0].reposition_anim.set_time_count == 1U);
}

static void test_ambient_update_resets_battle_motion_and_updates_one_actor(void)
{
    SupportEchoRenderer renderer;
    initialize_renderer(&renderer, 1.0f, 1.0f);
    N64GameBattle battle = initialized_battle();

    set_damage_event(&battle, 4U, 0U, N64GAME_TARGET_ALL);
    assert(support_echo_renderer_update(&renderer, &battle));
    const uint32_t skeleton_updates[N64GAME_SUPPORT_ECHO_COUNT] = {
        renderer.instances[0].skeleton.update_count,
        renderer.instances[1].skeleton.update_count,
        renderer.instances[2].skeleton.update_count,
    };
    const uint32_t idle_updates[N64GAME_SUPPORT_ECHO_COUNT] = {
        renderer.instances[0].idle_anim.update_count,
        renderer.instances[1].idle_anim.update_count,
        renderer.instances[2].idle_anim.update_count,
    };

    assert(support_echo_renderer_update_ambient(
        &renderer, N64GAME_SUPPORT_ECHO_AYSELOR
    ));
    assert(!renderer.observed_event_serial_valid);
    for (unsigned index = 0U;
         index < (unsigned)N64GAME_SUPPORT_ECHO_COUNT;
         ++index) {
        assert(renderer.instances[index].motion ==
               N64GAME_SUPPORT_ECHO_MOTION_IDLE);
        assert(!t3d_anim_is_playing(&renderer.instances[index].reposition_anim));
        assert(!t3d_anim_is_playing(&renderer.instances[index].hit_anim));
        const uint32_t expected_delta =
            index == (unsigned)N64GAME_SUPPORT_ECHO_AYSELOR ? 1U : 0U;
        assert(renderer.instances[index].skeleton.update_count ==
               skeleton_updates[index] + expected_delta);
        assert(renderer.instances[index].idle_anim.update_count ==
               idle_updates[index] + expected_delta);
    }
}

int main(void)
{
    test_target_all_side_mapping_and_duplicate_suppression();
    test_reset_and_serial_reuse();
    test_one_shot_completion_and_knockout_hit_window();
    test_ambient_update_resets_battle_motion_and_updates_one_actor();
    puts("support Echoform renderer behavior harness: PASS");
    return 0;
}
