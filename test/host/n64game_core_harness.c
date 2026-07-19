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
    TEST_SAVE_OFFSET_CHECKSUM = 60,
    TEST_SAVE_FLAG_REWARD = UINT8_C(1) << 3,
    TEST_SAVE_FLAG_COMPLETE = UINT8_C(1) << 4,
};

static void update_pressed(N64GameCore *game, N64GameInputButton button)
{
    n64game_core_update(game, (N64GameInput){.pressed = (uint16_t)button});
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

static void test_name_annex_and_ending_flow(void)
{
    N64GameCore game;
    n64game_core_init(&game);
    assert(game.scene == N64GAME_SCENE_BOOT);
    for (unsigned tick = 0U; tick < 30U; ++tick) {
        n64game_core_update(&game, (N64GameInput){0});
    }
    assert(game.scene == N64GAME_SCENE_OPENING_SLATE);
    update_pressed(&game, N64GAME_INPUT_START);
    assert(game.opening_cinematic_seen);
    assert(game.scene == N64GAME_SCENE_NAME_ENTRY);

    game.name_cursor = 27U;
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    assert(game.scene == N64GAME_SCENE_ANNEX);
    assert(game.name_length == 3U);
    assert(strcmp(game.player_name, "ARI") == 0);

    n64game_core_set_player_position(&game, -38 * 256, -8 * 256);
    assert(strcmp(n64game_core_interaction_label(&game), "TALK TO SERA") == 0);
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    dismiss_dialogue(&game);
    assert(game.quest == N64GAME_QUEST_RETRIEVE_RELAY);

    n64game_core_set_player_position(&game, 34 * 256, 20 * 256);
    assert(strcmp(n64game_core_interaction_label(&game), "TAKE FIELD RELAY") == 0);
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    dismiss_dialogue(&game);
    assert(game.relay_unlocked);
    assert(game.save_requested);
    assert(game.quest == N64GAME_QUEST_RETURN_TO_SERA);

    game.save_requested = false;
    n64game_core_set_player_position(&game, -38 * 256, -8 * 256);
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    dismiss_dialogue(&game);
    assert(game.scene == N64GAME_SCENE_BATTLE);
    assert(game.battle.phase == N64GAME_BATTLE_COMMAND);

    game.battle.actors[2].hp = 20;
    game.battle.actors[3].hp = 20;
    game.battle.resonance = N64GAME_RESONANCE_MAX;
    assert(n64game_battle_commit_finisher(&game.battle));
    resolve_round(&game.battle);
    assert(game.battle.phase == N64GAME_BATTLE_VICTORY);
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    assert(game.scene == N64GAME_SCENE_ANNEX);
    assert(game.battle_won && game.battle_reward_claimed && !game.save_requested);
    dismiss_dialogue(&game);
    assert(game.quest == N64GAME_QUEST_BEACON_OVERLOOK);
    assert(game.save_requested);

    game.save_requested = false;
    n64game_core_set_player_position(&game, 74 * 256, 40 * 256);
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    dismiss_dialogue(&game);
    assert(game.scene == N64GAME_SCENE_END_CHAPTER);
    assert(game.quest == N64GAME_QUEST_COMPLETE);
    assert(game.slice_complete && game.save_requested);
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
    n64game_core_set_player_position(&game, 5 * 256, -34 * 256);
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
    const N64GameInput start = {.pressed = N64GAME_INPUT_START};

    n64game_core_update_controller(&game, start, false, false);
    assert(game.scene_ticks == 17U && game.play_ticks == 23U && !game.paused);
    n64game_core_update_controller(&game, start, true, true);
    assert(game.scene_ticks == 17U && game.play_ticks == 23U && !game.paused);
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
    assert(battle.actors[3].guard_stage == 1);
    assert(battle.resonance == 32U);

    assert(n64game_battle_commit_action(&battle, 0U, 0U, 2U));
    assert(n64game_battle_commit_action(&battle, 1U, 0U, 2U));
    battle.actors[2].hp = 0;
    const int16_t other_hp = battle.actors[3].hp;
    resolve_round(&battle);
    assert(battle.actors[3].hp < other_hp);

    N64GameCore game;
    n64game_core_init(&game);
    game.scene = N64GAME_SCENE_BATTLE;
    n64game_battle_begin(&game.battle);
    game.battle.phase = N64GAME_BATTLE_DEFEAT;
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    assert(game.battle.phase == N64GAME_BATTLE_COMMAND);
    assert(game.battle.actors[0].hp == game.battle.actors[0].max_hp);
    game.battle.phase = N64GAME_BATTLE_DEFEAT;
    update_pressed(&game, N64GAME_INPUT_CANCEL);
    assert(game.scene == N64GAME_SCENE_ANNEX);
    assert(game.quest == N64GAME_QUEST_RETURN_TO_SERA);
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
    n64game_core_set_player_position(&game, -38 * 256, -8 * 256);
    update_pressed(&game, N64GAME_INPUT_CONFIRM);
    assert(game.dialogue == N64GAME_DIALOGUE_SERA_TRIAL);
    dismiss_dialogue(&game);
    assert(game.scene == N64GAME_SCENE_BATTLE);
    assert(game.battle.phase == N64GAME_BATTLE_COMMAND);
    assert(game.battle.command_actor == 1U);

    n64game_core_init(&game);
    game.scene = N64GAME_SCENE_ANNEX;
    game.quest = N64GAME_QUEST_RETURN_TO_SERA;
    game.relay_unlocked = true;
    game.party_hp[0] = 0;
    game.party_hp[1] = 0;
    n64game_core_set_player_position(&game, -38 * 256, -8 * 256);
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

    uint8_t bytes[N64GAME_SAVE_BYTES];
    N64GameCore decoded;
    uint32_t sequence = 0U;

    game.scene = N64GAME_SCENE_ANNEX;
    game.quest = N64GAME_QUEST_RETURN_TO_SERA;
    assert(n64game_save_encode(&game, UINT32_C(75), bytes));
    assert(n64game_save_decode(bytes, &decoded, &sequence));
    assert(sequence == 75U && decoded.quest == N64GAME_QUEST_RETURN_TO_SERA);

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
    test_name_annex_and_ending_flow();
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
