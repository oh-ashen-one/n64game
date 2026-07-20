#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "n64game_core.h"
#include "n64game_save.h"

enum {
    TEST_SAVE_OFFSET_SCENE = 21,
    TEST_SAVE_OFFSET_QUEST = 22,
    TEST_SAVE_OFFSET_FLAGS = 23,
    TEST_SAVE_OFFSET_ANNEX_SECTOR = 29,
    TEST_SAVE_OFFSET_EXAMINE_FLAGS = 30,
    TEST_SAVE_OFFSET_RELAY_PAGES = 31,
    TEST_SAVE_OFFSET_ACTIVE_CONTROL_TICKS = 36,
    TEST_SAVE_OFFSET_SETTINGS = 42,
    TEST_SAVE_OFFSET_CHECKSUM = 60,
    TEST_SAVE_FLAG_REWARD = UINT8_C(1) << 3,
    TEST_SAVE_FLAG_COMPLETE = UINT8_C(1) << 4,
    TEST_ALL_ANNEX_SECTORS = (UINT8_C(1) << N64GAME_ANNEX_SECTOR_COUNT) - 1U,
    TEST_ALL_EXAMINES = UINT8_C(0x0F),
    TEST_ALL_RELAY_PAGES = N64GAME_RELAY_PAGE_PARTY |
        N64GAME_RELAY_PAGE_MESSAGES |
        N64GAME_RELAY_PAGE_RESONANCE |
        N64GAME_RELAY_PAGE_SAVE,
};

static void update_pressed(N64GameCore *game, N64GameInputButton button)
{
    n64game_core_update(game, (N64GameInput){.pressed = (uint16_t)button});
}

static void route_note_sector(const N64GameCore *game, uint8_t *sectors_seen)
{
    if (game->scene == N64GAME_SCENE_ANNEX) {
        assert(game->annex_sector < N64GAME_ANNEX_SECTOR_COUNT);
        *sectors_seen |= (uint8_t)(UINT8_C(1) << game->annex_sector);
    }
}

static void route_tick(
    N64GameCore *game,
    N64GameInput input,
    uint8_t *sectors_seen
)
{
    n64game_core_update_controller(game, input, true, false);
    route_note_sector(game, sectors_seen);
}

static void route_press(
    N64GameCore *game,
    N64GameInputButton button,
    uint8_t *sectors_seen
)
{
    route_tick(
        game,
        (N64GameInput){.pressed = (uint16_t)button},
        sectors_seen
    );
}

static int64_t magnitude_i32(int32_t value)
{
    return value < 0 ? -(int64_t)value : (int64_t)value;
}

static int8_t route_stick_axis(int32_t delta_q8)
{
    const int64_t distance = magnitude_i32(delta_q8);
    if (distance <= 192) {
        return 0;
    }
    int32_t magnitude = (int32_t)(distance / 96);
    if (magnitude < 12) {
        magnitude = 12;
    } else if (magnitude > INT8_MAX) {
        magnitude = INT8_MAX;
    }
    return (int8_t)(delta_q8 < 0 ? -magnitude : magnitude);
}

static void route_move_to(
    N64GameCore *game,
    int32_t target_x_q8,
    int32_t target_z_q8,
    uint8_t *sectors_seen
)
{
    unsigned guard = 0U;
    while (magnitude_i32(target_x_q8 - game->player_x_q8) > 192 ||
           magnitude_i32(target_z_q8 - game->player_z_q8) > 192 ||
           game->player_velocity_x_q8 != 0 || game->player_velocity_z_q8 != 0) {
        const int8_t stick_x = route_stick_axis(target_x_q8 - game->player_x_q8);
        const int8_t stick_z = route_stick_axis(target_z_q8 - game->player_z_q8);
        route_tick(
            game,
            (N64GameInput){
                .held = N64GAME_INPUT_CANCEL,
                .stick_x = stick_x,
                .stick_y = (int8_t)-stick_z,
            },
            sectors_seen
        );
        assert(game->scene == N64GAME_SCENE_ANNEX);
        if (++guard >= 2400U) {
            fprintf(
                stderr,
                "route stuck at (%ld,%ld), target (%ld,%ld), sector %u\n",
                (long)game->player_x_q8,
                (long)game->player_z_q8,
                (long)target_x_q8,
                (long)target_z_q8,
                (unsigned)game->annex_sector
            );
            assert(guard < 2400U);
        }
    }
    assert(n64game_annex_position_valid(game->player_x_q8, game->player_z_q8));
}

static void route_move_to_world(
    N64GameCore *game,
    int world_x,
    int world_z,
    uint8_t *sectors_seen
)
{
    route_move_to(game, world_x * 256, world_z * 256, sectors_seen);
}

static void route_move_to_interaction(
    N64GameCore *game,
    N64GameAnnexInteraction interaction,
    uint8_t *sectors_seen
)
{
    int32_t x_q8 = 0;
    int32_t z_q8 = 0;
    assert(n64game_annex_interaction_point(interaction, &x_q8, &z_q8));
    route_move_to(game, x_q8, z_q8, sectors_seen);
    assert(n64game_annex_interaction_at(
        game->player_x_q8, game->player_z_q8
    ) == interaction);
}

static void route_dismiss_dialogue(N64GameCore *game, uint8_t *sectors_seen)
{
    unsigned guard = 0U;
    assert(game->dialogue != N64GAME_DIALOGUE_NONE);
    while (game->dialogue != N64GAME_DIALOGUE_NONE &&
           game->scene == N64GAME_SCENE_ANNEX) {
        route_press(game, N64GAME_INPUT_CONFIRM, sectors_seen);
        assert(++guard < 8U);
    }
}

static void focused_set_interaction_position(
    N64GameCore *game,
    N64GameAnnexInteraction interaction
)
{
    int32_t x_q8 = 0;
    int32_t z_q8 = 0;
    assert(n64game_annex_interaction_point(interaction, &x_q8, &z_q8));
    n64game_core_set_player_position(game, x_q8, z_q8);
}

static void rewrite_save_checksum(uint8_t bytes[N64GAME_SAVE_BYTES])
{
    const uint32_t checksum = n64game_save_checksum(bytes);
    bytes[TEST_SAVE_OFFSET_CHECKSUM] = (uint8_t)(checksum >> 24);
    bytes[TEST_SAVE_OFFSET_CHECKSUM + 1U] = (uint8_t)(checksum >> 16);
    bytes[TEST_SAVE_OFFSET_CHECKSUM + 2U] = (uint8_t)(checksum >> 8);
    bytes[TEST_SAVE_OFFSET_CHECKSUM + 3U] = (uint8_t)checksum;
}

static void dismiss_dialogue(N64GameCore *game)
{
    const uint8_t pages = n64game_dialogue_page_count(game->dialogue);
    assert(pages > 0U);
    for (uint8_t page = 0U; page < pages; ++page) {
        update_pressed(game, N64GAME_INPUT_CONFIRM);
    }
    assert(game->dialogue == N64GAME_DIALOGUE_NONE ||
           game->scene != N64GAME_SCENE_ANNEX);
}

static void resolve_round(N64GameBattle *battle)
{
    unsigned guard = 0U;
    while (battle->phase == N64GAME_BATTLE_PRESENT) {
        assert(n64game_battle_resolve_next(battle));
        assert(++guard < 8U);
    }
}

typedef struct {
    const char *name;
    N64GameAffinity affinity;
    N64GameTargetRule target;
    N64GameMoveEffect effect;
    uint8_t power;
    uint8_t resonance;
    uint8_t chance;
    uint8_t stage_rounds;
    uint8_t cooldown_rounds;
    bool once;
} ExpectedMove;

static void inject_action(
    N64GameBattle *battle,
    uint8_t actor,
    uint8_t move,
    uint8_t target
)
{
    const N64GameMoveDef *const definition = n64game_move_def(
        battle->actors[actor].id, move
    );
    assert(definition != NULL);
    battle->phase = N64GAME_BATTLE_PRESENT;
    battle->queue_count = 2U;
    battle->queue_cursor = 0U;
    battle->queue[0] = (N64GameBattleAction){
        .actor = actor,
        .move = move,
        .target = target,
        .priority = definition->priority,
        .valid = true,
    };
    battle->queue[1] = (N64GameBattleAction){0};
    assert(n64game_battle_resolve_next(battle));
    assert(battle->phase == N64GAME_BATTLE_PRESENT);
    assert(battle->queue_cursor == 1U);
}

static void test_canonical_retained_move_definitions_and_effects(void)
{
    static const ExpectedMove EXPECTED[N64GAME_BATTLE_ACTOR_COUNT]
        [N64GAME_BATTLE_MOVE_COUNT] = {
        [N64GAME_ECHO_QUARRUNE] = {
            {"RIDGE RAM", N64GAME_AFFINITY_STRATA, N64GAME_TARGET_ONE_ENEMY,
             N64GAME_EFFECT_DAMAGE, 28, 6, 0, 0, 0, false},
            {"BRACE RELAY", N64GAME_AFFINITY_STRATA, N64GAME_TARGET_ONE_ALLY,
             N64GAME_EFFECT_GUARD_UP, 0, 14, 0, 2, 0, false},
            {"GROUNDING RING", N64GAME_AFFINITY_STRATA, N64GAME_TARGET_ALL_ENEMIES,
             N64GAME_EFFECT_DAMAGE_GROUND, 14, 6, 0, 0, 0, false},
            {"STEADY PULSE", N64GAME_AFFINITY_STRATA, N64GAME_TARGET_ONE_ALLY,
             N64GAME_EFFECT_HEAL_CLEAR_STAGGER, 12, 0, 0, 0, 0, true},
        },
        [N64GAME_ECHO_AYSELOR] = {
            {"SIROCCO SLICE", N64GAME_AFFINITY_GALE, N64GAME_TARGET_ONE_ENEMY,
             N64GAME_EFFECT_DAMAGE, 26, 6, 0, 0, 0, false},
            {"LIFT CURRENT", N64GAME_AFFINITY_GALE, N64GAME_TARGET_ONE_ALLY,
             N64GAME_EFFECT_SPEED_UP, 0, 14, 0, 2, 0, false},
            {"DAZZLE WAKE", N64GAME_AFFINITY_GALE, N64GAME_TARGET_ALL_ENEMIES,
             N64GAME_EFFECT_DAMAGE_STAGGER_CHANCE, 12, 6, 35, 0, 0, false},
            {"GUIDING DRAFT", N64GAME_AFFINITY_GALE, N64GAME_TARGET_ONE_ALLY,
             N64GAME_EFFECT_EMPOWER_NEXT_DAMAGE, 0, 12, 0, 0, 0, false},
        },
        [N64GAME_ECHO_GYRECLAST] = {
            {"AUGER KNUCKLE", N64GAME_AFFINITY_STRATA, N64GAME_TARGET_ONE_ENEMY,
             N64GAME_EFFECT_DAMAGE, 27, 0, 0, 0, 0, false},
            {"DUST SCREEN", N64GAME_AFFINITY_STRATA, N64GAME_TARGET_ALL_ENEMIES,
             N64GAME_EFFECT_POWER_DOWN, 0, 0, 0, 1, 0, false},
            {"FAULT PIN", N64GAME_AFFINITY_STRATA, N64GAME_TARGET_ONE_ENEMY,
             N64GAME_EFFECT_DAMAGE_STAGGER, 18, 0, 100, 0, 2, false},
            {"CARAPACE BRACE", N64GAME_AFFINITY_STRATA, N64GAME_TARGET_SELF,
             N64GAME_EFFECT_GUARD_UP, 0, 0, 0, 2, 0, false},
        },
        [N64GAME_ECHO_KIVARRAX] = {
            {"CROSSWIND CUT", N64GAME_AFFINITY_GALE, N64GAME_TARGET_ONE_ENEMY,
             N64GAME_EFFECT_DAMAGE, 25, 0, 0, 0, 0, false},
            {"SLIPSTREAM", N64GAME_AFFINITY_GALE, N64GAME_TARGET_ONE_ALLY,
             N64GAME_EFFECT_SPEED_UP, 0, 0, 0, 2, 0, false},
            {"PRESSURE DROP", N64GAME_AFFINITY_GALE, N64GAME_TARGET_ONE_ENEMY,
             N64GAME_EFFECT_GUARD_DOWN, 0, 0, 0, 2, 0, false},
            {"TALON SWEEP", N64GAME_AFFINITY_GALE, N64GAME_TARGET_ALL_ENEMIES,
             N64GAME_EFFECT_DAMAGE, 12, 0, 0, 0, 0, false},
        },
    };

    for (uint8_t actor = 0U; actor < N64GAME_BATTLE_ACTOR_COUNT; ++actor) {
        for (uint8_t move = 0U; move < N64GAME_BATTLE_MOVE_COUNT; ++move) {
            const N64GameMoveDef *const actual = n64game_move_def(
                (N64GameEchoform)actor, move
            );
            const ExpectedMove *const expected = &EXPECTED[actor][move];
            assert(actual != NULL);
            assert(strcmp(actual->name, expected->name) == 0);
            assert(actual->affinity == expected->affinity);
            assert(actual->target_rule == expected->target);
            assert(actual->effect == expected->effect);
            assert(actual->power == expected->power);
            assert(actual->resonance_gain == expected->resonance);
            assert(actual->effect_chance_percent == expected->chance);
            assert(actual->stage_rounds == expected->stage_rounds);
            assert(actual->cooldown_rounds == expected->cooldown_rounds);
            assert(actual->once_per_encounter == expected->once);
            assert(actual->priority == 0);
        }
    }
    assert(n64game_move_def((N64GameEchoform)N64GAME_BATTLE_ACTOR_COUNT, 0U) == NULL);
    assert(n64game_move_def(N64GAME_ECHO_QUARRUNE, N64GAME_BATTLE_MOVE_COUNT) == NULL);

    N64GameBattle battle;
    n64game_battle_begin(&battle);
    assert(battle.actors[2].affinity == N64GAME_AFFINITY_STRATA);
    assert(battle.actors[3].affinity == N64GAME_AFFINITY_GALE);

    inject_action(&battle, 1U, 3U, 0U);
    assert(battle.actors[0].empowered_damage);
    assert(battle.actors[0].empowered_by_partner);
    assert(battle.actors[0].partner_setup_round == 1U);
    assert(battle.resonance == 12U);
    const int16_t gyreclast_hp = battle.actors[2].hp;
    inject_action(&battle, 0U, 0U, 2U);
    assert(gyreclast_hp - battle.actors[2].hp == 37);
    assert(!battle.actors[0].empowered_damage);
    assert(!battle.actors[0].empowered_by_partner);
    assert(battle.actors[0].partner_setup_round == 0U);
    assert(battle.resonance == 30U);

    n64game_battle_begin(&battle);
    battle.actors[1].hp = 50;
    battle.actors[1].stagger_rounds = 1U;
    inject_action(&battle, 0U, 3U, 1U);
    assert(battle.actors[1].hp == 62);
    assert(battle.actors[1].stagger_rounds == 0U);
    assert(battle.resonance == 8U);
    assert(!n64game_battle_target_legal(&battle, 0U, 3U, 1U));
    assert(battle.actors[1].partner_setup_round == 1U);
    inject_action(&battle, 1U, 0U, 3U);
    assert(battle.resonance == 26U);
    assert(battle.actors[1].partner_setup_round == 0U);

    n64game_battle_begin(&battle);
    for (unsigned use = 0U; use < 2U; ++use) {
        inject_action(&battle, 0U, 1U, 1U);
    }
    assert(battle.actors[1].guard_stage == N64GAME_BATTLE_STAGE_MAX);
    assert(battle.actors[1].guard_stage_expires_round == 3U);
    battle.round = 2U;
    inject_action(&battle, 0U, 1U, 1U);
    assert(!battle.last_event.skipped);
    assert(battle.actors[1].guard_stage == N64GAME_BATTLE_STAGE_MAX);
    assert(battle.actors[1].guard_stage_expires_round == 4U);
    assert(battle.resonance == 42U);
    for (unsigned use = 0U; use < 5U; ++use) {
        inject_action(&battle, 3U, 2U, 1U);
    }
    assert(battle.actors[1].guard_stage == N64GAME_BATTLE_STAGE_MIN);
    assert(!battle.last_event.skipped);

    n64game_battle_begin(&battle);
    battle.actors[1].hp = 0;
    inject_action(&battle, 0U, 1U, 1U);
    assert(battle.last_event.target == 0U);
    assert(battle.actors[0].guard_stage == 1);
    assert(battle.resonance == 0U);
    assert(battle.actors[0].partner_setup_round == 0U);

    n64game_battle_begin(&battle);
    inject_action(&battle, 0U, 1U, 1U);
    assert(battle.actors[1].partner_setup_round == 1U);
    inject_action(&battle, 1U, 0U, 3U);
    assert(battle.resonance == 32U);
    assert(battle.linked_followthrough_round == 1U);
    inject_action(&battle, 1U, 0U, 3U);
    assert(battle.resonance == 38U);

    n64game_battle_begin(&battle);
    inject_action(&battle, 0U, 1U, 1U);
    battle.round = 2U;
    inject_action(&battle, 1U, 0U, 3U);
    assert(battle.resonance == 20U);
    assert(battle.linked_followthrough_round == 0U);

    n64game_battle_begin(&battle);
    inject_action(&battle, 1U, 1U, 0U);
    assert(battle.actors[0].speed_stage == 1);
    assert(battle.actors[0].partner_setup_round == 1U);
    inject_action(&battle, 0U, 0U, 2U);
    assert(battle.resonance == 32U);

    n64game_battle_begin(&battle);
    battle.actors[2].power_stage = 2;
    battle.actors[3].power_stage = 2;
    inject_action(&battle, 0U, 2U, N64GAME_TARGET_ALL);
    assert(battle.actors[2].power_stage == 1);
    assert(battle.actors[3].power_stage == 1);

    n64game_battle_begin(&battle);
    inject_action(&battle, 1U, 2U, N64GAME_TARGET_ALL);
    assert(battle.actors[2].stagger_rounds == 1U);
    assert(battle.actors[3].stagger_rounds == 0U);

    n64game_battle_begin(&battle);
    inject_action(&battle, 2U, 2U, 0U);
    assert(battle.actors[0].stagger_rounds == 1U);
    assert(battle.actors[2].move_ready_round[2] == 4U);
    assert(!n64game_battle_target_legal(&battle, 2U, 2U, 0U));
    battle.round = 4U;
    assert(n64game_battle_target_legal(&battle, 2U, 2U, 0U));

    n64game_battle_begin(&battle);
    inject_action(&battle, 2U, 1U, N64GAME_TARGET_ALL);
    inject_action(&battle, 2U, 1U, N64GAME_TARGET_ALL);
    inject_action(&battle, 2U, 1U, N64GAME_TARGET_ALL);
    assert(battle.actors[0].power_stage == N64GAME_BATTLE_STAGE_MIN);
    assert(battle.actors[1].power_stage == N64GAME_BATTLE_STAGE_MIN);
    inject_action(&battle, 3U, 1U, 2U);
    assert(battle.actors[2].speed_stage == 1);
    inject_action(&battle, 2U, 3U, 2U);
    assert(battle.actors[2].guard_stage == 1);
    const int16_t quarrune_hp = battle.actors[0].hp;
    const int16_t ayselor_hp = battle.actors[1].hp;
    inject_action(&battle, 3U, 3U, N64GAME_TARGET_ALL);
    assert(battle.actors[0].hp < quarrune_hp);
    assert(battle.actors[1].hp < ayselor_hp);
}

static void test_input_only_release_route(void)
{
    N64GameCore game;
    uint8_t sectors_seen = 0U;
    n64game_core_init(&game);
    assert(game.scene == N64GAME_SCENE_BOOT);
    for (unsigned tick = 0U; tick < 30U; ++tick) {
        route_tick(&game, (N64GameInput){0}, &sectors_seen);
    }
    assert(game.scene == N64GAME_SCENE_OPENING_SLATE);
    route_press(&game, N64GAME_INPUT_START, &sectors_seen);
    assert(game.opening_cinematic_seen);
    assert(game.scene == N64GAME_SCENE_NAME_ENTRY);

    route_press(&game, N64GAME_INPUT_LEFT, &sectors_seen);
    route_press(&game, N64GAME_INPUT_UP, &sectors_seen);
    assert(game.name_cursor == 27U);
    route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
    assert(game.scene == N64GAME_SCENE_ANNEX);
    assert(game.name_length == 3U);
    assert(strcmp(game.player_name, "ARI") == 0);

    route_move_to_interaction(
        &game, N64GAME_ANNEX_INTERACTION_SERA, &sectors_seen
    );
    assert(strcmp(n64game_core_interaction_label(&game), "TALK TO SERA") == 0);
    route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
    route_dismiss_dialogue(&game, &sectors_seen);
    assert(game.quest == N64GAME_QUEST_RETRIEVE_RELAY);

    route_move_to_interaction(
        &game, N64GAME_ANNEX_INTERACTION_EXAMINE_SIM_RING, &sectors_seen
    );
    assert(strcmp(
        n64game_core_interaction_label(&game), "EXAMINE SIMULATION RING"
    ) == 0);
    route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
    route_dismiss_dialogue(&game, &sectors_seen);
    assert((game.examine_flags & UINT8_C(0x01)) != 0U);

    route_move_to_world(&game, -30, 0, &sectors_seen);
    route_move_to_interaction(
        &game, N64GAME_ANNEX_INTERACTION_TAVI, &sectors_seen
    );
    assert(strcmp(n64game_core_interaction_label(&game), "TALK TO TAVI") == 0);
    route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
    route_dismiss_dialogue(&game, &sectors_seen);
    assert(game.quest == N64GAME_QUEST_RETRIEVE_RELAY);

    route_move_to_interaction(
        &game, N64GAME_ANNEX_INTERACTION_EXAMINE_ATRIUM_MAP, &sectors_seen
    );
    route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
    route_dismiss_dialogue(&game, &sectors_seen);
    assert((game.examine_flags & UINT8_C(0x02)) != 0U);

    route_move_to_world(&game, 24, 14, &sectors_seen);
    route_move_to_interaction(
        &game, N64GAME_ANNEX_INTERACTION_FIELD_RELAY, &sectors_seen
    );
    assert(strcmp(n64game_core_interaction_label(&game), "TAKE FIELD RELAY") == 0);
    route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
    route_dismiss_dialogue(&game, &sectors_seen);
    assert(game.relay_unlocked);
    assert(game.save_requested);
    assert(game.quest == N64GAME_QUEST_RETURN_TO_SERA);

    /* Consume the automatic Relay checkpoint solely through the save API. */
    uint8_t save_bytes[N64GAME_SAVE_BYTES];
    uint32_t save_sequence = 0U;
    const N64GameAnnexSector relay_sector = game.annex_sector;
    assert(n64game_save_encode(&game, UINT32_C(40), save_bytes));
    assert(n64game_save_decode(save_bytes, &game, &save_sequence));
    assert(save_sequence == 40U && game.annex_sector == relay_sector);
    assert(!game.save_requested && game.quest == N64GAME_QUEST_RETURN_TO_SERA);

    route_move_to_interaction(
        &game, N64GAME_ANNEX_INTERACTION_EXAMINE_WORKSHOP_LOG, &sectors_seen
    );
    route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
    route_dismiss_dialogue(&game, &sectors_seen);
    assert((game.examine_flags & UINT8_C(0x04)) != 0U);

    route_move_to_world(&game, 62, 28, &sectors_seen);
    route_move_to_interaction(
        &game, N64GAME_ANNEX_INTERACTION_EXAMINE_OVERLOOK_SCOPE, &sectors_seen
    );
    route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
    route_dismiss_dialogue(&game, &sectors_seen);
    assert(game.examine_flags == TEST_ALL_EXAMINES);
    assert(sectors_seen == TEST_ALL_ANNEX_SECTORS);

    route_press(&game, N64GAME_INPUT_RELAY, &sectors_seen);
    assert(game.menu == N64GAME_MENU_FIELD_RELAY_ROOT && game.paused);
    route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
    assert(game.menu == N64GAME_MENU_PARTY);
    route_press(&game, N64GAME_INPUT_CANCEL, &sectors_seen);

    route_press(&game, N64GAME_INPUT_DOWN, &sectors_seen);
    route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
    assert(game.menu == N64GAME_MENU_MESSAGES);
    route_press(&game, N64GAME_INPUT_CANCEL, &sectors_seen);

    route_press(&game, N64GAME_INPUT_DOWN, &sectors_seen);
    route_press(&game, N64GAME_INPUT_DOWN, &sectors_seen);
    route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
    assert(game.menu == N64GAME_MENU_RESONANCE);
    route_press(&game, N64GAME_INPUT_CANCEL, &sectors_seen);

    route_press(&game, N64GAME_INPUT_DOWN, &sectors_seen);
    route_press(&game, N64GAME_INPUT_DOWN, &sectors_seen);
    route_press(&game, N64GAME_INPUT_DOWN, &sectors_seen);
    route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
    assert(game.menu == N64GAME_MENU_SAVE && !game.save_requested);
    route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
    assert(game.save_requested);
    assert(game.relay_pages_seen == TEST_ALL_RELAY_PAGES);

    const N64GameAnnexSector manual_save_sector = game.annex_sector;
    int32_t safe_x_q8 = 0;
    int32_t safe_z_q8 = 0;
    n64game_annex_safe_anchor(manual_save_sector, &safe_x_q8, &safe_z_q8);
    const uint32_t manual_play_ticks = game.play_ticks;
    const uint32_t manual_control_ticks = game.active_control_ticks;
    assert(n64game_save_encode(&game, UINT32_C(41), save_bytes));
    assert(n64game_save_decode(save_bytes, &game, &save_sequence));
    assert(save_sequence == 41U);
    assert(game.annex_sector == manual_save_sector);
    assert(game.player_x_q8 == safe_x_q8 && game.player_z_q8 == safe_z_q8);
    assert(game.play_ticks == manual_play_ticks);
    assert(game.active_control_ticks == manual_control_ticks);
    assert(game.menu == N64GAME_MENU_CLOSED && !game.paused && !game.save_requested);
    assert(game.examine_flags == TEST_ALL_EXAMINES);
    assert(game.relay_pages_seen == TEST_ALL_RELAY_PAGES);

    route_move_to_world(&game, 62, 28, &sectors_seen);
    route_move_to_world(&game, 52, 14, &sectors_seen);
    route_move_to_world(&game, 24, 14, &sectors_seen);
    route_move_to_world(&game, 0, 0, &sectors_seen);
    route_move_to_interaction(
        &game, N64GAME_ANNEX_INTERACTION_SERA, &sectors_seen
    );
    assert(strcmp(n64game_core_interaction_label(&game), "BEGIN TRIAL") == 0);
    route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
    route_dismiss_dialogue(&game, &sectors_seen);
    assert(game.scene == N64GAME_SCENE_BATTLE);
    assert(game.battle.phase == N64GAME_BATTLE_INTRO);

    while (game.scene_ticks < 45U) {
        route_tick(&game, (N64GameInput){0}, &sectors_seen);
    }
    assert(game.battle.phase == N64GAME_BATTLE_COMMAND);
    unsigned battle_guard = 0U;
    while (game.battle.phase != N64GAME_BATTLE_VICTORY) {
        assert(game.battle.phase != N64GAME_BATTLE_DEFEAT);
        if (game.battle.phase == N64GAME_BATTLE_COMMAND) {
            const uint8_t actor = game.battle.command_actor;
            assert(actor <= 1U && game.battle.actors[actor].hp > 0);
            assert(game.battle_move_cursor == 0U);
            route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
            assert(game.battle_selecting_target);
            route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
        } else {
            assert(game.battle.phase == N64GAME_BATTLE_PRESENT);
            route_tick(&game, (N64GameInput){0}, &sectors_seen);
        }
        assert(++battle_guard < 1600U);
    }
    assert(game.battle.phase == N64GAME_BATTLE_VICTORY);
    assert(game.battle.round <= 8U);
    route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
    assert(game.scene == N64GAME_SCENE_ANNEX);
    assert(game.battle_won && game.battle_reward_claimed && !game.save_requested);
    route_dismiss_dialogue(&game, &sectors_seen);
    assert(game.quest == N64GAME_QUEST_BEACON_OVERLOOK);
    assert(game.save_requested);
    assert(game.party_hp[0] == N64GAME_QUARRUNE_MAX_HP);
    assert(game.party_hp[1] == N64GAME_AYSELOR_MAX_HP);

    /* Reloading preserves the rewarded checkpoint and its full-heal result. */
    assert(n64game_save_encode(&game, UINT32_C(42), save_bytes));
    assert(n64game_save_decode(save_bytes, &game, &save_sequence));
    assert(save_sequence == 42U);
    assert(game.battle_won && game.battle_reward_claimed);
    assert(game.party_hp[0] == N64GAME_QUARRUNE_MAX_HP);
    assert(game.party_hp[1] == N64GAME_AYSELOR_MAX_HP);
    route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
    assert(game.quest == N64GAME_QUEST_BEACON_OVERLOOK);
    assert(game.party_hp[0] == N64GAME_QUARRUNE_MAX_HP);
    assert(game.party_hp[1] == N64GAME_AYSELOR_MAX_HP);

    route_move_to_world(&game, -24, 0, &sectors_seen);
    route_move_to_world(&game, 24, 14, &sectors_seen);
    route_move_to_world(&game, 52, 14, &sectors_seen);
    route_move_to_world(&game, 62, 28, &sectors_seen);
    route_move_to_interaction(
        &game, N64GAME_ANNEX_INTERACTION_BEACON, &sectors_seen
    );
    assert(strcmp(n64game_core_interaction_label(&game), "TRACE BEACON") == 0);
    route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
    route_dismiss_dialogue(&game, &sectors_seen);
    assert(game.scene == N64GAME_SCENE_END_CHAPTER);
    assert(game.quest == N64GAME_QUEST_COMPLETE);
    assert(game.slice_complete && game.save_requested);
    assert(game.examine_flags == TEST_ALL_EXAMINES);
    assert(game.relay_pages_seen == TEST_ALL_RELAY_PAGES);
    assert(sectors_seen == TEST_ALL_ANNEX_SECTORS);
    assert(game.active_control_ticks > 0U);
    assert(game.menu == N64GAME_MENU_POST_CHAPTER_ROOT);
    route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
    assert(game.menu == N64GAME_MENU_MESSAGES);
    route_press(&game, N64GAME_INPUT_CANCEL, &sectors_seen);
    route_press(&game, N64GAME_INPUT_RIGHT, &sectors_seen);
    route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
    assert(game.menu == N64GAME_MENU_PARTY);
    route_press(&game, N64GAME_INPUT_CANCEL, &sectors_seen);
    route_press(&game, N64GAME_INPUT_RIGHT, &sectors_seen);
    route_press(&game, N64GAME_INPUT_RIGHT, &sectors_seen);
    route_press(&game, N64GAME_INPUT_CONFIRM, &sectors_seen);
    assert(game.menu == N64GAME_MENU_RESONANCE);
    route_press(&game, N64GAME_INPUT_CANCEL, &sectors_seen);
    assert(game.menu == N64GAME_MENU_POST_CHAPTER_ROOT);
    assert(n64game_save_encode(&game, UINT32_C(43), save_bytes));
    assert(n64game_save_decode(save_bytes, &game, &save_sequence));
    assert(save_sequence == 43U && game.slice_complete);
    assert(game.menu == N64GAME_MENU_POST_CHAPTER_ROOT && game.paused);
}

static void test_annex_acceleration_run_and_collision(void)
{
    N64GameCore walking;
    N64GameCore running;
    n64game_core_init(&walking);
    n64game_core_init(&running);
    walking.scene = N64GAME_SCENE_ANNEX;
    running.scene = N64GAME_SCENE_ANNEX;

    const int32_t start_x_q8 = walking.player_x_q8;
    n64game_core_update(&walking, (N64GameInput){.stick_x = INT8_MAX});
    assert(walking.player_velocity_x_q8 > 0);
    assert(walking.player_velocity_x_q8 < 384);
    for (unsigned tick = 1U; tick < 12U; ++tick) {
        n64game_core_update(&walking, (N64GameInput){.stick_x = INT8_MAX});
    }
    for (unsigned tick = 0U; tick < 12U; ++tick) {
        n64game_core_update(
            &running,
            (N64GameInput){
                .held = N64GAME_INPUT_CANCEL,
                .stick_x = INT8_MAX,
            }
        );
    }
    assert(walking.player_x_q8 > start_x_q8);
    assert(running.player_x_q8 > walking.player_x_q8);
    const int32_t moving_velocity_q8 = walking.player_velocity_x_q8;
    n64game_core_update(&walking, (N64GameInput){0});
    assert(walking.player_velocity_x_q8 < moving_velocity_q8);

    n64game_core_set_player_position(&walking, 0, 30 * 256);
    for (unsigned tick = 0U; tick < 80U; ++tick) {
        n64game_core_update(
            &walking,
            (N64GameInput){
                .held = N64GAME_INPUT_CANCEL,
                .stick_y = -INT8_MAX,
            }
        );
    }
    assert(walking.player_z_q8 == 32 * 256);
    assert(n64game_annex_position_valid(
        walking.player_x_q8, walking.player_z_q8
    ));
}

static void test_manual_save_requires_a_fresh_menu_entry(void)
{
    N64GameCore game;
    n64game_core_init(&game);
    game.scene = N64GAME_SCENE_ANNEX;
    game.relay_unlocked = true;
    update_pressed(&game, N64GAME_INPUT_RELAY);
    for (unsigned item = 0U; item < 3U; ++item) {
        update_pressed(&game, N64GAME_INPUT_DOWN);
    }
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    assert(game.menu == N64GAME_MENU_SAVE);
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    assert(game.save_requested && game.manual_save_latched);

    /* Simulate main consuming the request; the same Save page cannot repeat it. */
    game.save_requested = false;
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    assert(!game.save_requested && game.manual_save_latched);

    update_pressed(&game, N64GAME_INPUT_CANCEL);
    for (unsigned item = 0U; item < 3U; ++item) {
        update_pressed(&game, N64GAME_INPUT_DOWN);
    }
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    assert(game.menu == N64GAME_MENU_SAVE && !game.manual_save_latched);
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    assert(game.save_requested && game.manual_save_latched);
}

static void test_opening_slate_natural_timing_is_exact(void)
{
    N64GameCore game;
    n64game_core_init(&game);
    for (unsigned tick = 0U; tick < 30U; ++tick) {
        n64game_core_update(&game, (N64GameInput){0});
    }
    assert(game.scene == N64GAME_SCENE_OPENING_SLATE && game.scene_ticks == 0U);
    for (unsigned tick = 0U; tick < 105U; ++tick) {
        n64game_core_update(&game, (N64GameInput){0});
    }
    assert(game.scene == N64GAME_SCENE_OPENING_SLATE && game.scene_ticks == 105U);
    n64game_core_update(&game, (N64GameInput){0});
    assert(game.scene == N64GAME_SCENE_NAME_ENTRY);
    assert(game.opening_cinematic_seen && game.scene_ticks == 0U);
}

static void test_name_editing_movement_pause_and_optional_dialogue(void)
{
    N64GameCore game;
    n64game_core_init(&game);
    game.scene = N64GAME_SCENE_NAME_ENTRY;
    game.name_cursor = 1U;
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    assert(strcmp(game.player_name, "B") == 0);
    update_pressed(&game, N64GAME_INPUT_CANCEL);
    assert(game.name_length == 0U);
    game.name_cursor = 0U;
    update_pressed(&game, N64GAME_INPUT_LEFT);
    assert(game.name_cursor == 6U);

    game.name_cursor = 27U;
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    focused_set_interaction_position(&game, N64GAME_ANNEX_INTERACTION_TAVI);
    assert(strcmp(n64game_core_interaction_label(&game), "TALK TO TAVI") == 0);
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    dismiss_dialogue(&game);
    assert(game.quest == N64GAME_QUEST_MEET_SERA);

    const int32_t before = game.player_x_q8;
    n64game_core_update(&game, (N64GameInput){.stick_x = INT8_MAX});
    assert(game.player_x_q8 > before);
    update_pressed(&game, N64GAME_INPUT_PAUSE);
    const int32_t paused = game.player_x_q8;
    n64game_core_update(&game, (N64GameInput){.stick_x = INT8_MAX});
    assert(game.player_x_q8 == paused);
}

static void test_controller_disconnect_freezes_and_reconnect_clears_edges(void)
{
    N64GameCore game;
    n64game_core_init(&game);
    game.scene = N64GAME_SCENE_ANNEX;
    game.scene_ticks = 17U;
    game.play_ticks = 23U;
    game.player_velocity_x_q8 = 160;
    game.player_velocity_z_q8 = -96;
    const N64GameInput start = {.pressed = N64GAME_INPUT_START};

    n64game_core_update_controller(&game, start, false, false);
    assert(game.scene_ticks == 17U && game.play_ticks == 23U && !game.paused);
    assert(game.player_velocity_x_q8 == 0 && game.player_velocity_z_q8 == 0);
    game.player_velocity_x_q8 = 160;
    game.player_velocity_z_q8 = -96;
    n64game_core_update_controller(&game, start, true, true);
    assert(game.scene_ticks == 17U && game.play_ticks == 23U && !game.paused);
    assert(game.player_velocity_x_q8 == 0 && game.player_velocity_z_q8 == 0);
    n64game_core_update_controller(&game, start, true, false);
    assert(game.scene_ticks == 18U && game.play_ticks == 24U && game.paused);

    game.paused = false;
    game.scene = N64GAME_SCENE_BATTLE;
    n64game_battle_begin(&game.battle);
    assert(n64game_battle_commit_action(&game.battle, 0U, 0U, 2U));
    assert(n64game_battle_commit_action(&game.battle, 1U, 0U, 3U));
    game.battle_present_delay = 19U;
    n64game_core_update_controller(&game, (N64GameInput){0}, false, false);
    assert(game.battle_present_delay == 19U && game.battle.queue_cursor == 0U);
    n64game_core_update_controller(&game, (N64GameInput){0}, true, true);
    assert(game.battle_present_delay == 19U && game.battle.queue_cursor == 0U);
    n64game_core_update_controller(&game, (N64GameInput){0}, true, false);
    assert(game.battle_present_delay == 0U && game.battle.queue_cursor == 1U);
}

static void test_battle_legality_order_retarget_and_retry(void)
{
    N64GameBattle battle;
    n64game_battle_begin(&battle);
    assert(!n64game_battle_commit_finisher(&battle));
    assert(!n64game_battle_commit_action(&battle, 1U, 0U, 2U));
    assert(!n64game_battle_commit_action(&battle, 0U, 0U, 1U));
    assert(!n64game_battle_commit_action(&battle, 0U, 2U, 2U));
    assert(n64game_battle_commit_action(&battle, 0U, 1U, 1U));
    assert(n64game_battle_commit_action(&battle, 1U, 0U, 3U));
    resolve_round(&battle);
    assert(battle.phase == N64GAME_BATTLE_COMMAND);
    assert(battle.actors[1].guard_stage == 1);
    assert(battle.actors[2].speed_stage == 1);
    assert(battle.resonance == 20U);

    assert(n64game_battle_commit_action(&battle, 0U, 0U, 2U));
    assert(n64game_battle_commit_action(&battle, 1U, 0U, 2U));
    battle.actors[2].hp = 0;
    const int16_t other_hp = battle.actors[3].hp;
    resolve_round(&battle);
    assert(battle.actors[3].hp < other_hp);

    N64GameCore game;
    n64game_core_init(&game);
    game.scene = N64GAME_SCENE_BATTLE;
    game.party_hp[0] = 51;
    game.party_hp[1] = 44;
    game.prebattle_resonance = 17U;
    n64game_battle_begin(&game.battle);
    game.battle.resonance = 83U;
    game.battle.phase = N64GAME_BATTLE_DEFEAT;
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    assert(game.battle.phase == N64GAME_BATTLE_COMMAND);
    assert(game.battle.actors[0].hp == 51 && game.battle.actors[1].hp == 44);
    assert(game.battle.resonance == 17U);
    game.battle.resonance = 74U;
    game.battle.phase = N64GAME_BATTLE_DEFEAT;
    update_pressed(&game, N64GAME_INPUT_CANCEL);
    assert(game.scene == N64GAME_SCENE_ANNEX);
    assert(game.quest == N64GAME_QUEST_RETURN_TO_SERA);
    assert(game.battle.phase == N64GAME_BATTLE_INACTIVE);
    assert(game.battle.resonance == 17U);
}

static void test_battle_controller_selection_and_presentation_cadence(void)
{
    N64GameCore game;
    n64game_core_init(&game);
    game.scene = N64GAME_SCENE_BATTLE;
    game.scene_ticks = 45U;
    n64game_battle_begin(&game.battle);

    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    assert(game.battle_selecting_target);
    assert(game.battle_target_cursor == 2U);
    update_pressed(&game, N64GAME_INPUT_CANCEL);
    assert(!game.battle_selecting_target);

    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    assert(game.battle.command_actor == 1U);
    assert(game.battle.phase == N64GAME_BATTLE_COMMAND);
    assert(game.battle.player_actions[0].valid);

    update_pressed(&game, N64GAME_INPUT_CANCEL);
    assert(game.battle.command_actor == 0U);
    assert(!game.battle.player_actions[0].valid);
    assert(!game.battle_selecting_target);

    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    assert(game.battle_selecting_target);
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    assert(game.battle.command_actor == 1U);
    assert(game.battle.player_actions[0].valid);

    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    assert(game.battle_selecting_target);
    update_pressed(&game, N64GAME_INPUT_RIGHT);
    assert(game.battle_target_cursor == 3U);
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    assert(game.battle.phase == N64GAME_BATTLE_PRESENT);
    assert(!game.battle_selecting_target);

    for (unsigned tick = 0U; tick < 19U; ++tick) {
        n64game_core_update(&game, (N64GameInput){0});
    }
    assert(game.battle.queue_cursor == 0U);
    n64game_core_update(&game, (N64GameInput){0});
    assert(game.battle.queue_cursor == 1U);
}

static void test_trial_entry_selects_a_living_player_or_defeats(void)
{
    N64GameCore game;
    n64game_core_init(&game);
    game.scene = N64GAME_SCENE_ANNEX;
    game.quest = N64GAME_QUEST_RETURN_TO_SERA;
    game.relay_unlocked = true;
    game.party_hp[0] = 0;
    game.party_hp[1] = 31;
    focused_set_interaction_position(&game, N64GAME_ANNEX_INTERACTION_SERA);
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    assert(game.dialogue == N64GAME_DIALOGUE_SERA_TRIAL);
    dismiss_dialogue(&game);
    assert(game.scene == N64GAME_SCENE_BATTLE);
    assert(game.battle.phase == N64GAME_BATTLE_INTRO);
    for (unsigned tick = 0U; tick < 45U; ++tick) {
        n64game_core_update(&game, (N64GameInput){0});
    }
    assert(game.battle.phase == N64GAME_BATTLE_COMMAND);
    assert(game.battle.command_actor == 1U);

    n64game_core_init(&game);
    game.scene = N64GAME_SCENE_ANNEX;
    game.quest = N64GAME_QUEST_RETURN_TO_SERA;
    game.relay_unlocked = true;
    game.party_hp[0] = 0;
    game.party_hp[1] = 0;
    focused_set_interaction_position(&game, N64GAME_ANNEX_INTERACTION_SERA);
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    dismiss_dialogue(&game);
    assert(game.scene == N64GAME_SCENE_BATTLE);
    assert(game.battle.phase == N64GAME_BATTLE_DEFEAT);
}

static void test_direct_damage_strategy_can_win_with_one_survivor(void)
{
    N64GameBattle battle;
    n64game_battle_begin(&battle);
    unsigned rounds = 0U;
    while (battle.phase == N64GAME_BATTLE_COMMAND) {
        const uint8_t first_enemy = battle.actors[2].hp > 0 ? 2U : 3U;
        if (battle.command_actor == 0U) {
            assert(n64game_battle_commit_action(&battle, 0U, 0U, first_enemy));
        }
        if (battle.phase == N64GAME_BATTLE_COMMAND && battle.command_actor == 1U) {
            const uint8_t second_enemy = battle.actors[3].hp > 0 ? 3U : 2U;
            assert(n64game_battle_commit_action(&battle, 1U, 0U, second_enemy));
        }
        resolve_round(&battle);
        assert(++rounds <= 8U);
    }
    assert(battle.phase == N64GAME_BATTLE_VICTORY);
    assert(battle.actors[0].hp > 0 || battle.actors[1].hp > 0);
}

static void test_save_round_trip_and_corruption_deaths(void)
{
    N64GameCore game;
    n64game_core_init(&game);
    memcpy(game.player_name, "SOL", 4U);
    game.name_length = 3U;
    game.opening_cinematic_seen = true;
    game.relay_unlocked = true;
    n64game_battle_begin(&game.battle);
    game.party_hp[0] = 61;
    game.party_hp[1] = 55;
    game.battle.resonance = 44U;
    game.annex_sector = N64GAME_ANNEX_WORKSHOP;
    n64game_annex_safe_anchor(
        game.annex_sector, &game.player_x_q8, &game.player_z_q8
    );
    game.examine_flags = UINT8_C(0x0B);
    game.relay_pages_seen = TEST_ALL_RELAY_PAGES;
    game.settings_flags = N64GAME_SETTING_INVERT_Y | N64GAME_SETTING_RUMBLE;
    game.play_ticks = 900U;
    game.active_control_ticks = 600U;

    uint8_t bytes[N64GAME_SAVE_BYTES];
    N64GameCore decoded;
    uint32_t sequence = 0U;

    game.scene = N64GAME_SCENE_ANNEX;
    game.quest = N64GAME_QUEST_RETURN_TO_SERA;
    assert(n64game_save_encode(&game, UINT32_C(75), bytes));
    assert(n64game_save_decode(bytes, &decoded, &sequence));
    assert(sequence == 75U && decoded.quest == N64GAME_QUEST_RETURN_TO_SERA);
    assert(decoded.annex_sector == N64GAME_ANNEX_WORKSHOP);
    assert(decoded.examine_flags == UINT8_C(0x0B));
    assert(decoded.relay_pages_seen == TEST_ALL_RELAY_PAGES);
    assert(decoded.settings_flags == (N64GAME_SETTING_INVERT_Y | N64GAME_SETTING_RUMBLE));
    assert(decoded.play_ticks == 900U && decoded.active_control_ticks == 600U);

    bytes[TEST_SAVE_OFFSET_ANNEX_SECTOR] = (uint8_t)N64GAME_ANNEX_SECTOR_COUNT;
    rewrite_save_checksum(bytes);
    assert(!n64game_save_decode(bytes, &decoded, &sequence));
    assert(n64game_save_encode(&game, UINT32_C(75), bytes));
    bytes[TEST_SAVE_OFFSET_EXAMINE_FLAGS] |= UINT8_C(0x80);
    rewrite_save_checksum(bytes);
    assert(!n64game_save_decode(bytes, &decoded, &sequence));
    assert(n64game_save_encode(&game, UINT32_C(75), bytes));
    bytes[TEST_SAVE_OFFSET_RELAY_PAGES] |= UINT8_C(0x80);
    rewrite_save_checksum(bytes);
    assert(!n64game_save_decode(bytes, &decoded, &sequence));
    assert(n64game_save_encode(&game, UINT32_C(75), bytes));
    bytes[TEST_SAVE_OFFSET_SETTINGS] |= UINT8_C(0x80);
    rewrite_save_checksum(bytes);
    assert(!n64game_save_decode(bytes, &decoded, &sequence));
    assert(n64game_save_encode(&game, UINT32_C(75), bytes));
    bytes[TEST_SAVE_OFFSET_ACTIVE_CONTROL_TICKS] = UINT8_C(0x7F);
    rewrite_save_checksum(bytes);
    assert(!n64game_save_decode(bytes, &decoded, &sequence));
    assert(n64game_save_encode(&game, UINT32_C(75), bytes));

    bytes[TEST_SAVE_OFFSET_QUEST] = (uint8_t)N64GAME_QUEST_RESONANCE_TRIAL;
    rewrite_save_checksum(bytes);
    assert(!n64game_save_decode(bytes, &decoded, &sequence));
    assert(n64game_save_encode(&game, UINT32_C(75), bytes));
    bytes[TEST_SAVE_OFFSET_QUEST] = (uint8_t)N64GAME_QUEST_BEACON_OVERLOOK;
    rewrite_save_checksum(bytes);
    assert(!n64game_save_decode(bytes, &decoded, &sequence));

    game.quest = N64GAME_QUEST_BEACON_OVERLOOK;
    game.battle_won = true;
    game.battle_reward_claimed = true;
    assert(n64game_save_encode(&game, UINT32_C(76), bytes));
    assert(n64game_save_decode(bytes, &decoded, &sequence));
    assert(sequence == 76U && decoded.quest == N64GAME_QUEST_BEACON_OVERLOOK);
    bytes[TEST_SAVE_OFFSET_FLAGS] ^= TEST_SAVE_FLAG_REWARD;
    rewrite_save_checksum(bytes);
    assert(!n64game_save_decode(bytes, &decoded, &sequence));

    game.scene = N64GAME_SCENE_END_CHAPTER;
    game.quest = N64GAME_QUEST_COMPLETE;
    game.slice_complete = true;
    assert(n64game_save_encode(&game, UINT32_C(77), bytes));
    assert(n64game_save_decode(bytes, &decoded, &sequence));
    assert(sequence == 77U);
    assert(strcmp(decoded.player_name, "SOL") == 0);
    assert(decoded.slice_complete && decoded.battle_reward_claimed);
    assert(decoded.party_hp[0] == 61);
    assert(decoded.battle.resonance == 44U);
    assert(decoded.menu == N64GAME_MENU_POST_CHAPTER_ROOT && decoded.paused);

    bytes[TEST_SAVE_OFFSET_SCENE] = (uint8_t)N64GAME_SCENE_ANNEX;
    rewrite_save_checksum(bytes);
    assert(!n64game_save_decode(bytes, &decoded, &sequence));
    assert(n64game_save_encode(&game, UINT32_C(77), bytes));
    bytes[TEST_SAVE_OFFSET_FLAGS] ^= TEST_SAVE_FLAG_COMPLETE;
    rewrite_save_checksum(bytes);
    assert(!n64game_save_decode(bytes, &decoded, &sequence));
    assert(n64game_save_encode(&game, UINT32_C(77), bytes));

    bytes[25] ^= UINT8_C(1);
    assert(!n64game_save_decode(bytes, &decoded, &sequence));
    bytes[25] ^= UINT8_C(1);
    bytes[40] = UINT8_C(1);
    rewrite_save_checksum(bytes);
    assert(!n64game_save_decode(bytes, &decoded, &sequence));
    bytes[40] = 0U;
    game.battle_reward_claimed = false;
    assert(!n64game_save_encode(&game, 78U, bytes));
    game.battle_reward_claimed = true;
    game.player_name[0] = 'a';
    assert(!n64game_save_encode(&game, 79U, bytes));
}

static void test_save_journal_survives_each_copy_on_write_boundary(void)
{
    N64GameCore game;
    n64game_core_init(&game);
    memcpy(game.player_name, "ARI", 4U);
    game.name_length = 3U;
    game.opening_cinematic_seen = true;
    game.relay_unlocked = true;
    game.scene = N64GAME_SCENE_ANNEX;
    game.quest = N64GAME_QUEST_RETURN_TO_SERA;

    uint8_t slots[N64GAME_SAVE_SLOT_COUNT][N64GAME_SAVE_BYTES];
    assert(n64game_save_encode(&game, UINT32_C(10), slots[0]));
    game.quest = N64GAME_QUEST_BEACON_OVERLOOK;
    game.battle_won = true;
    game.battle_reward_claimed = true;
    assert(n64game_save_encode(&game, UINT32_C(11), slots[1]));

    N64GameCore selected_game;
    uint32_t selected_sequence = 0U;
    uint8_t selected_slot = 0U;
    assert(n64game_save_select_latest(
        slots, &selected_game, &selected_sequence, &selected_slot
    ));
    assert(selected_slot == 1U && selected_sequence == 11U);

    game.scene = N64GAME_SCENE_END_CHAPTER;
    game.quest = N64GAME_QUEST_COMPLETE;
    game.slice_complete = true;
    uint8_t replacement[N64GAME_SAVE_BYTES];
    assert(n64game_save_encode(&game, UINT32_C(12), replacement));

    for (size_t index = 0U; index < N64GAME_SAVE_FOOTER_BYTES; ++index) {
        slots[0][N64GAME_SAVE_BODY_BYTES + index] = (uint8_t)(
            replacement[N64GAME_SAVE_BODY_BYTES + index] ^ UINT8_C(0xFF)
        );
    }
    assert(n64game_save_select_latest(
        slots, &selected_game, &selected_sequence, &selected_slot
    ));
    assert(selected_slot == 1U && selected_sequence == 11U);

    memcpy(slots[0], replacement, N64GAME_SAVE_BODY_BYTES);
    assert(n64game_save_select_latest(
        slots, &selected_game, &selected_sequence, &selected_slot
    ));
    assert(selected_slot == 1U && selected_sequence == 11U);

    memcpy(
        slots[0] + N64GAME_SAVE_BODY_BYTES,
        replacement + N64GAME_SAVE_BODY_BYTES,
        N64GAME_SAVE_FOOTER_BYTES
    );
    assert(n64game_save_select_latest(
        slots, &selected_game, &selected_sequence, &selected_slot
    ));
    assert(selected_slot == 0U && selected_sequence == 12U && selected_game.slice_complete);

    assert(n64game_save_encode(&game, UINT32_MAX, slots[0]));
    assert(n64game_save_encode(&game, 0U, slots[1]));
    assert(n64game_save_select_latest(
        slots, &selected_game, &selected_sequence, &selected_slot
    ));
    assert(selected_slot == 1U && selected_sequence == 0U);
}

int main(void)
{
    test_canonical_retained_move_definitions_and_effects();
    test_input_only_release_route();
    test_annex_acceleration_run_and_collision();
    test_manual_save_requires_a_fresh_menu_entry();
    test_opening_slate_natural_timing_is_exact();
    test_name_editing_movement_pause_and_optional_dialogue();
    test_controller_disconnect_freezes_and_reconnect_clears_edges();
    test_battle_legality_order_retarget_and_retry();
    test_battle_controller_selection_and_presentation_cadence();
    test_trial_entry_selects_a_living_player_or_defeats();
    test_direct_damage_strategy_can_win_with_one_survivor();
    test_save_round_trip_and_corruption_deaths();
    test_save_journal_survives_each_copy_on_write_boundary();
    puts("n64game core harness: PASS");
    return 0;
}
