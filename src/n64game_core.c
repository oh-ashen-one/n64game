#include "n64game_core.h"

#include <limits.h>
#include <stdio.h>
#include <string.h>

enum {
    BOOT_TICKS = 30,
    SLATE_TICKS = 106,
    NAME_COLUMNS = 7,
    NAME_SLOT_BACK = 26,
    NAME_SLOT_CONFIRM = 27,
    ANNEX_STICK_DEADZONE = 12,
    ANNEX_WALK_SPEED_Q8 = 384,
    ANNEX_RUN_SPEED_Q8 = 640,
    ANNEX_ACCEL_Q8 = 64,
    ANNEX_DECEL_Q8 = 96,
};

static const N64GameMoveDef MOVES[N64GAME_BATTLE_ACTOR_COUNT][N64GAME_BATTLE_MOVE_COUNT] = {
    [N64GAME_ECHO_QUARRUNE] = {
        { "RIDGE RAM", N64GAME_AFFINITY_STRATA, N64GAME_TARGET_ONE_ENEMY,
          N64GAME_EFFECT_DAMAGE, 24, 12, 0 },
        { "BRACE RELAY", N64GAME_AFFINITY_STRATA, N64GAME_TARGET_ONE_ALLY,
          N64GAME_EFFECT_GUARD, 0, 20, 1 },
        { "GROUNDING RING", N64GAME_AFFINITY_STRATA, N64GAME_TARGET_ALL_ENEMIES,
          N64GAME_EFFECT_DAMAGE, 13, 10, 0 },
        { "STEADY PULSE", N64GAME_AFFINITY_STRATA, N64GAME_TARGET_ONE_ALLY,
          N64GAME_EFFECT_HEAL, 18, 14, 0 },
    },
    [N64GAME_ECHO_AYSELOR] = {
        { "GALE CUT", N64GAME_AFFINITY_GALE, N64GAME_TARGET_ONE_ENEMY,
          N64GAME_EFFECT_DAMAGE, 22, 12, 0 },
        { "UPDRAFT LINK", N64GAME_AFFINITY_GALE, N64GAME_TARGET_ONE_ALLY,
          N64GAME_EFFECT_GUARD, 0, 18, 1 },
        { "DAZZLE WAKE", N64GAME_AFFINITY_GALE, N64GAME_TARGET_ALL_ENEMIES,
          N64GAME_EFFECT_DAMAGE_STAGGER, 11, 12, 0 },
        { "MENDING DRAFT", N64GAME_AFFINITY_GALE, N64GAME_TARGET_ONE_ALLY,
          N64GAME_EFFECT_HEAL, 16, 14, 0 },
    },
    [N64GAME_ECHO_GYRECLAST] = {
        { "CURRENT BORE", N64GAME_AFFINITY_CURRENT, N64GAME_TARGET_ONE_ENEMY,
          N64GAME_EFFECT_DAMAGE, 20, 0, 0 },
        { "VOLT SHELTER", N64GAME_AFFINITY_CURRENT, N64GAME_TARGET_ONE_ALLY,
          N64GAME_EFFECT_GUARD, 0, 0, 1 },
        { "ARC WASH", N64GAME_AFFINITY_CURRENT, N64GAME_TARGET_ALL_ENEMIES,
          N64GAME_EFFECT_DAMAGE, 10, 0, 0 },
        { "RETURN LOOP", N64GAME_AFFINITY_CURRENT, N64GAME_TARGET_ONE_ALLY,
          N64GAME_EFFECT_HEAL, 14, 0, 0 },
    },
    [N64GAME_ECHO_KIVARRAX] = {
        { "KILN STRIKE", N64GAME_AFFINITY_EMBER, N64GAME_TARGET_ONE_ENEMY,
          N64GAME_EFFECT_DAMAGE, 21, 0, 0 },
        { "FURNACE VEIL", N64GAME_AFFINITY_EMBER, N64GAME_TARGET_ONE_ALLY,
          N64GAME_EFFECT_GUARD, 0, 0, 1 },
        { "CINDER FAN", N64GAME_AFFINITY_EMBER, N64GAME_TARGET_ALL_ENEMIES,
          N64GAME_EFFECT_DAMAGE_STAGGER, 10, 0, 0 },
        { "EMBER MEND", N64GAME_AFFINITY_EMBER, N64GAME_TARGET_ONE_ALLY,
          N64GAME_EFFECT_HEAL, 13, 0, 0 },
    },
};

static bool pressed(N64GameInput input, N64GameInputButton button)
{
    return (input.pressed & (uint16_t)button) != 0U;
}

static bool held(N64GameInput input, N64GameInputButton button)
{
    return (input.held & (uint16_t)button) != 0U;
}

static int32_t approach_i32(int32_t current, int32_t target, int32_t amount)
{
    if (current < target) {
        const int32_t next = current + amount;
        return next > target ? target : next;
    }
    if (current > target) {
        const int32_t next = current - amount;
        return next < target ? target : next;
    }
    return current;
}

static void set_scene(N64GameCore *game, N64GameScene scene)
{
    game->scene = scene;
    game->scene_ticks = 0U;
    game->paused = false;
    game->menu = N64GAME_MENU_CLOSED;
    game->menu_parent = N64GAME_MENU_CLOSED;
    game->menu_cursor = 0U;
    game->manual_save_latched = false;
    game->player_velocity_x_q8 = 0;
    game->player_velocity_z_q8 = 0;
}

static void begin_dialogue(N64GameCore *game, N64GameDialogue dialogue)
{
    game->dialogue = dialogue;
    game->dialogue_page = 0U;
}

static void restore_prebattle_snapshot(N64GameCore *game)
{
    n64game_battle_begin(&game->battle);
    game->battle.resonance = game->prebattle_resonance;
    game->battle_move_cursor = 0U;
    game->battle_target_cursor = 0U;
    game->battle_present_delay = 0U;
    game->battle_selecting_target = false;
    game->battle.actors[0].hp = game->party_hp[0];
    game->battle.actors[1].hp = game->party_hp[1];
    if (game->battle.actors[0].hp > 0) {
        game->battle.phase = N64GAME_BATTLE_COMMAND;
        game->battle.command_actor = 0U;
    } else if (game->battle.actors[1].hp > 0) {
        game->battle.phase = N64GAME_BATTLE_COMMAND;
        game->battle.command_actor = 1U;
    } else {
        game->battle.phase = N64GAME_BATTLE_DEFEAT;
    }
}

static void finish_dialogue(N64GameCore *game)
{
    const N64GameDialogue dialogue = game->dialogue;
    game->dialogue = N64GAME_DIALOGUE_NONE;
    game->dialogue_page = 0U;
    switch (dialogue) {
    case N64GAME_DIALOGUE_SERA_INTRO:
        game->quest = N64GAME_QUEST_RETRIEVE_RELAY;
        break;
    case N64GAME_DIALOGUE_RELAY:
        game->relay_unlocked = true;
        game->quest = N64GAME_QUEST_RETURN_TO_SERA;
        game->save_requested = true;
        break;
    case N64GAME_DIALOGUE_SERA_TRIAL:
        game->quest = N64GAME_QUEST_RESONANCE_TRIAL;
        game->prebattle_resonance = game->battle.resonance;
        restore_prebattle_snapshot(game);
        if (game->battle.phase == N64GAME_BATTLE_COMMAND) {
            game->battle.phase = N64GAME_BATTLE_INTRO;
        }
        set_scene(game, N64GAME_SCENE_BATTLE);
        break;
    case N64GAME_DIALOGUE_BATTLE_VICTORY:
        game->quest = N64GAME_QUEST_BEACON_OVERLOOK;
        game->party_hp[0] = N64GAME_QUARRUNE_MAX_HP;
        game->party_hp[1] = N64GAME_AYSELOR_MAX_HP;
        game->save_requested = true;
        break;
    case N64GAME_DIALOGUE_BEACON_HOOK:
        game->quest = N64GAME_QUEST_COMPLETE;
        game->slice_complete = true;
        game->save_requested = true;
        set_scene(game, N64GAME_SCENE_END_CHAPTER);
        game->menu = N64GAME_MENU_POST_CHAPTER_ROOT;
        game->menu_parent = N64GAME_MENU_POST_CHAPTER_ROOT;
        game->paused = true;
        break;
    case N64GAME_DIALOGUE_TAVI_OPTIONAL:
    case N64GAME_DIALOGUE_EXAMINE_SIM_RING:
    case N64GAME_DIALOGUE_EXAMINE_ATRIUM_MAP:
    case N64GAME_DIALOGUE_EXAMINE_WORKSHOP_LOG:
    case N64GAME_DIALOGUE_EXAMINE_OVERLOOK_SCOPE:
    case N64GAME_DIALOGUE_NONE:
        break;
    }
}

static void update_dialogue(N64GameCore *game, N64GameInput input)
{
    if (!pressed(input, N64GAME_INPUT_CONFIRM) && !pressed(input, N64GAME_INPUT_CANCEL)) {
        return;
    }
    const uint8_t page_count = n64game_dialogue_page_count(game->dialogue);
    if (game->dialogue_page + 1U < page_count) {
        ++game->dialogue_page;
    } else {
        finish_dialogue(game);
    }
}

static void update_name_entry(N64GameCore *game, N64GameInput input)
{
    const int row = (int)game->name_cursor / NAME_COLUMNS;
    const int column = (int)game->name_cursor % NAME_COLUMNS;
    int next_row = row;
    int next_column = column;
    if (pressed(input, N64GAME_INPUT_UP)) {
        next_row = (row + 3) % 4;
    } else if (pressed(input, N64GAME_INPUT_DOWN)) {
        next_row = (row + 1) % 4;
    }
    if (pressed(input, N64GAME_INPUT_LEFT)) {
        next_column = (column + NAME_COLUMNS - 1) % NAME_COLUMNS;
    } else if (pressed(input, N64GAME_INPUT_RIGHT)) {
        next_column = (column + 1) % NAME_COLUMNS;
    }
    game->name_cursor = (uint8_t)(next_row * NAME_COLUMNS + next_column);

    if (pressed(input, N64GAME_INPUT_CANCEL) && game->name_length > 0U) {
        --game->name_length;
        game->player_name[game->name_length] = '\0';
    }
    if (!pressed(input, N64GAME_INPUT_CONFIRM)) {
        return;
    }
    if (game->name_cursor < NAME_SLOT_BACK) {
        if (game->name_length < N64GAME_NAME_CAPACITY) {
            game->player_name[game->name_length] = (char)('A' + game->name_cursor);
            ++game->name_length;
            game->player_name[game->name_length] = '\0';
        }
    } else if (game->name_cursor == NAME_SLOT_BACK) {
        if (game->name_length > 0U) {
            --game->name_length;
            game->player_name[game->name_length] = '\0';
        }
    } else if (game->name_cursor == NAME_SLOT_CONFIRM) {
        if (game->name_length == 0U) {
            memcpy(game->player_name, "ARI", 4U);
            game->name_length = 3U;
        }
        game->quest = N64GAME_QUEST_MEET_SERA;
        game->player_x_q8 = -12 * 256;
        game->player_z_q8 = -8 * 256;
        set_scene(game, N64GAME_SCENE_ANNEX);
    }
}

static void close_menu(N64GameCore *game)
{
    game->menu = N64GAME_MENU_CLOSED;
    game->menu_parent = N64GAME_MENU_CLOSED;
    game->menu_cursor = 0U;
    game->paused = false;
    game->manual_save_latched = false;
}

static void open_root_menu(N64GameCore *game, N64GameMenu menu)
{
    game->menu = menu;
    game->menu_parent = menu;
    game->menu_cursor = 0U;
    game->paused = true;
    game->player_velocity_x_q8 = 0;
    game->player_velocity_z_q8 = 0;
}

static void open_submenu(
    N64GameCore *game,
    N64GameMenu menu,
    N64GameRelayPageFlag relay_page
)
{
    game->menu = menu;
    game->menu_cursor = 0U;
    if (menu == N64GAME_MENU_SAVE) {
        game->manual_save_latched = false;
    }
    if (game->menu_parent == N64GAME_MENU_FIELD_RELAY_ROOT) {
        game->relay_pages_seen |= (uint8_t)relay_page;
    }
}

static uint8_t root_menu_item_count(N64GameMenu menu)
{
    return menu == N64GAME_MENU_FIELD_RELAY_ROOT ? 5U : 4U;
}

static void update_annex_menu(N64GameCore *game, N64GameInput input)
{
    if (pressed(input, N64GAME_INPUT_START) || pressed(input, N64GAME_INPUT_PAUSE)) {
        close_menu(game);
        return;
    }
    if (pressed(input, N64GAME_INPUT_CANCEL)) {
        if (game->menu == N64GAME_MENU_PAUSE_ROOT ||
            game->menu == N64GAME_MENU_FIELD_RELAY_ROOT) {
            close_menu(game);
        } else {
            game->menu = game->menu_parent;
            game->menu_cursor = 0U;
        }
        return;
    }

    if (game->menu == N64GAME_MENU_PAUSE_ROOT ||
        game->menu == N64GAME_MENU_FIELD_RELAY_ROOT) {
        const uint8_t item_count = root_menu_item_count(game->menu);
        if (pressed(input, N64GAME_INPUT_UP)) {
            game->menu_cursor = (uint8_t)((game->menu_cursor + item_count - 1U) % item_count);
        } else if (pressed(input, N64GAME_INPUT_DOWN)) {
            game->menu_cursor = (uint8_t)((game->menu_cursor + 1U) % item_count);
        }
        if (!pressed(input, N64GAME_INPUT_CONFIRM)) {
            return;
        }
        if (game->menu == N64GAME_MENU_PAUSE_ROOT) {
            switch (game->menu_cursor) {
            case 0U:
                open_submenu(game, N64GAME_MENU_PARTY, N64GAME_RELAY_PAGE_PARTY);
                break;
            case 1U:
                open_submenu(game, N64GAME_MENU_HELP, N64GAME_RELAY_PAGE_PARTY);
                break;
            case 2U:
                if (game->relay_unlocked) {
                    open_submenu(game, N64GAME_MENU_SAVE, N64GAME_RELAY_PAGE_SAVE);
                }
                break;
            case 3U:
                close_menu(game);
                break;
            default:
                break;
            }
        } else {
            switch (game->menu_cursor) {
            case 0U:
                open_submenu(game, N64GAME_MENU_PARTY, N64GAME_RELAY_PAGE_PARTY);
                break;
            case 1U:
                open_submenu(game, N64GAME_MENU_MESSAGES, N64GAME_RELAY_PAGE_MESSAGES);
                break;
            case 2U:
                open_submenu(game, N64GAME_MENU_RESONANCE, N64GAME_RELAY_PAGE_RESONANCE);
                break;
            case 3U:
                open_submenu(game, N64GAME_MENU_SAVE, N64GAME_RELAY_PAGE_SAVE);
                break;
            case 4U:
                close_menu(game);
                break;
            default:
                break;
            }
        }
        return;
    }

    if (game->menu == N64GAME_MENU_SAVE && pressed(input, N64GAME_INPUT_CONFIRM)) {
        if (!game->manual_save_latched) {
            game->save_requested = true;
            game->relay_pages_seen |= N64GAME_RELAY_PAGE_SAVE;
            game->manual_save_latched = true;
        }
        return;
    }
    if (pressed(input, N64GAME_INPUT_CONFIRM)) {
        game->menu = game->menu_parent;
        game->menu_cursor = 0U;
    }
}

static N64GameDialogue examine_dialogue(N64GameAnnexInteraction interaction)
{
    switch (interaction) {
    case N64GAME_ANNEX_INTERACTION_EXAMINE_SIM_RING:
        return N64GAME_DIALOGUE_EXAMINE_SIM_RING;
    case N64GAME_ANNEX_INTERACTION_EXAMINE_ATRIUM_MAP:
        return N64GAME_DIALOGUE_EXAMINE_ATRIUM_MAP;
    case N64GAME_ANNEX_INTERACTION_EXAMINE_WORKSHOP_LOG:
        return N64GAME_DIALOGUE_EXAMINE_WORKSHOP_LOG;
    case N64GAME_ANNEX_INTERACTION_EXAMINE_OVERLOOK_SCOPE:
        return N64GAME_DIALOGUE_EXAMINE_OVERLOOK_SCOPE;
    case N64GAME_ANNEX_INTERACTION_NONE:
    case N64GAME_ANNEX_INTERACTION_SERA:
    case N64GAME_ANNEX_INTERACTION_FIELD_RELAY:
    case N64GAME_ANNEX_INTERACTION_TAVI:
    case N64GAME_ANNEX_INTERACTION_BEACON:
    case N64GAME_ANNEX_INTERACTION_COUNT:
        return N64GAME_DIALOGUE_NONE;
    }
    return N64GAME_DIALOGUE_NONE;
}

static uint8_t examine_flag(N64GameAnnexInteraction interaction)
{
    const unsigned first = (unsigned)N64GAME_ANNEX_INTERACTION_EXAMINE_SIM_RING;
    const unsigned value = (unsigned)interaction;
    if (value < first || value >= (unsigned)N64GAME_ANNEX_INTERACTION_COUNT) {
        return 0U;
    }
    return (uint8_t)(UINT8_C(1) << (value - first));
}

static void update_annex_movement(N64GameCore *game, N64GameInput input)
{
    const int32_t speed = held(input, N64GAME_INPUT_CANCEL) ?
        ANNEX_RUN_SPEED_Q8 : ANNEX_WALK_SPEED_Q8;
    const int32_t stick_x = (game->settings_flags & N64GAME_SETTING_INVERT_X) != 0U ?
        -(int32_t)input.stick_x : (int32_t)input.stick_x;
    const int32_t stick_y = (game->settings_flags & N64GAME_SETTING_INVERT_Y) != 0U ?
        -(int32_t)input.stick_y : (int32_t)input.stick_y;
    int32_t target_x = 0;
    int32_t target_z = 0;
    if (stick_x <= -ANNEX_STICK_DEADZONE || stick_x >= ANNEX_STICK_DEADZONE) {
        target_x = stick_x * speed / INT8_MAX;
    }
    if (stick_y <= -ANNEX_STICK_DEADZONE || stick_y >= ANNEX_STICK_DEADZONE) {
        target_z = -stick_y * speed / INT8_MAX;
    }
    if (target_x != 0 && target_z != 0) {
        target_x = target_x * 181 / 256;
        target_z = target_z * 181 / 256;
    }
    const int32_t x_step = target_x == 0 ? ANNEX_DECEL_Q8 : ANNEX_ACCEL_Q8;
    const int32_t z_step = target_z == 0 ? ANNEX_DECEL_Q8 : ANNEX_ACCEL_Q8;
    game->player_velocity_x_q8 = approach_i32(
        game->player_velocity_x_q8, target_x, x_step
    );
    game->player_velocity_z_q8 = approach_i32(
        game->player_velocity_z_q8, target_z, z_step
    );
    n64game_annex_move_swept(
        &game->player_x_q8,
        &game->player_z_q8,
        game->player_velocity_x_q8,
        game->player_velocity_z_q8
    );
    game->annex_sector = n64game_annex_sector_for_position(
        game->player_x_q8, game->player_z_q8, game->annex_sector
    );
}

static void update_annex(N64GameCore *game, N64GameInput input)
{
    if (game->dialogue != N64GAME_DIALOGUE_NONE) {
        update_dialogue(game, input);
        return;
    }
    if (game->menu != N64GAME_MENU_CLOSED) {
        update_annex_menu(game, input);
        return;
    }
    if (pressed(input, N64GAME_INPUT_PAUSE) || pressed(input, N64GAME_INPUT_START)) {
        open_root_menu(game, N64GAME_MENU_PAUSE_ROOT);
        return;
    }
    if (pressed(input, N64GAME_INPUT_RELAY) && game->relay_unlocked) {
        open_root_menu(game, N64GAME_MENU_FIELD_RELAY_ROOT);
        return;
    }

    update_annex_movement(game, input);
    if (!pressed(input, N64GAME_INPUT_CONFIRM)) {
        return;
    }

    const N64GameAnnexInteraction interaction = n64game_annex_interaction_at(
        game->player_x_q8, game->player_z_q8
    );
    if (game->quest == N64GAME_QUEST_MEET_SERA &&
        interaction == N64GAME_ANNEX_INTERACTION_SERA) {
        begin_dialogue(game, N64GAME_DIALOGUE_SERA_INTRO);
    } else if (game->quest == N64GAME_QUEST_RETRIEVE_RELAY &&
               interaction == N64GAME_ANNEX_INTERACTION_FIELD_RELAY) {
        begin_dialogue(game, N64GAME_DIALOGUE_RELAY);
    } else if (game->quest == N64GAME_QUEST_RETURN_TO_SERA &&
               interaction == N64GAME_ANNEX_INTERACTION_SERA) {
        begin_dialogue(game, N64GAME_DIALOGUE_SERA_TRIAL);
    } else if (game->quest == N64GAME_QUEST_BEACON_OVERLOOK &&
               interaction == N64GAME_ANNEX_INTERACTION_BEACON) {
        begin_dialogue(game, N64GAME_DIALOGUE_BEACON_HOOK);
    } else if (interaction == N64GAME_ANNEX_INTERACTION_TAVI) {
        begin_dialogue(game, N64GAME_DIALOGUE_TAVI_OPTIONAL);
    } else if (interaction == N64GAME_ANNEX_INTERACTION_FIELD_RELAY &&
               game->relay_unlocked) {
        open_root_menu(game, N64GAME_MENU_FIELD_RELAY_ROOT);
    } else {
        const N64GameDialogue examine = examine_dialogue(interaction);
        if (examine != N64GAME_DIALOGUE_NONE) {
            game->examine_flags |= examine_flag(interaction);
            begin_dialogue(game, examine);
        }
    }
}

static void update_post_chapter_menu(N64GameCore *game, N64GameInput input)
{
    if (game->menu != N64GAME_MENU_POST_CHAPTER_ROOT) {
        if (pressed(input, N64GAME_INPUT_CONFIRM) ||
            pressed(input, N64GAME_INPUT_CANCEL) ||
            pressed(input, N64GAME_INPUT_START) ||
            pressed(input, N64GAME_INPUT_PAUSE)) {
            game->menu = N64GAME_MENU_POST_CHAPTER_ROOT;
            game->menu_parent = N64GAME_MENU_POST_CHAPTER_ROOT;
            game->menu_cursor = 0U;
        }
        return;
    }
    if (pressed(input, N64GAME_INPUT_LEFT) || pressed(input, N64GAME_INPUT_UP)) {
        game->menu_cursor = (uint8_t)((game->menu_cursor + 2U) % 3U);
    } else if (pressed(input, N64GAME_INPUT_RIGHT) || pressed(input, N64GAME_INPUT_DOWN)) {
        game->menu_cursor = (uint8_t)((game->menu_cursor + 1U) % 3U);
    }
    if (!pressed(input, N64GAME_INPUT_CONFIRM)) {
        return;
    }
    switch (game->menu_cursor) {
    case 0U:
        open_submenu(game, N64GAME_MENU_MESSAGES, N64GAME_RELAY_PAGE_MESSAGES);
        break;
    case 1U:
        open_submenu(game, N64GAME_MENU_PARTY, N64GAME_RELAY_PAGE_PARTY);
        break;
    case 2U:
        open_submenu(game, N64GAME_MENU_RESONANCE, N64GAME_RELAY_PAGE_RESONANCE);
        break;
    default:
        break;
    }
}

static uint8_t first_legal_target(
    const N64GameBattle *battle,
    uint8_t actor,
    uint8_t move,
    uint8_t start,
    int direction
)
{
    uint8_t candidate = start;
    for (unsigned attempt = 0U; attempt < N64GAME_BATTLE_ACTOR_COUNT; ++attempt) {
        const int next = ((int)candidate + direction + N64GAME_BATTLE_ACTOR_COUNT) %
            N64GAME_BATTLE_ACTOR_COUNT;
        candidate = (uint8_t)next;
        if (n64game_battle_target_legal(battle, actor, move, candidate)) {
            return candidate;
        }
    }
    return N64GAME_TARGET_ALL;
}

static void reset_battle_selection(N64GameCore *game)
{
    game->battle_move_cursor = 0U;
    game->battle_target_cursor = 0U;
    game->battle_selecting_target = false;
}

static void update_battle_command(N64GameCore *game, N64GameInput input)
{
    N64GameBattle *const battle = &game->battle;
    const uint8_t actor = battle->command_actor;
    const bool finisher_available = actor == 0U &&
        battle->resonance == N64GAME_RESONANCE_MAX &&
        battle->actors[0].hp > 0 && battle->actors[1].hp > 0;
    const uint8_t choice_count = finisher_available ? 5U : 4U;

    if (game->battle_selecting_target) {
        if (pressed(input, N64GAME_INPUT_CANCEL)) {
            game->battle_selecting_target = false;
            return;
        }
        int direction = 0;
        if (pressed(input, N64GAME_INPUT_LEFT) || pressed(input, N64GAME_INPUT_UP)) {
            direction = -1;
        } else if (pressed(input, N64GAME_INPUT_RIGHT) || pressed(input, N64GAME_INPUT_DOWN)) {
            direction = 1;
        }
        if (direction != 0) {
            const uint8_t target = first_legal_target(
                battle, actor, game->battle_move_cursor,
                game->battle_target_cursor, direction
            );
            if (target != N64GAME_TARGET_ALL) {
                game->battle_target_cursor = target;
            }
        }
        if (pressed(input, N64GAME_INPUT_CONFIRM) &&
            n64game_battle_commit_action(
                battle, actor, game->battle_move_cursor, game->battle_target_cursor
            )) {
            reset_battle_selection(game);
            game->battle_present_delay = 0U;
        }
        return;
    }

    if (pressed(input, N64GAME_INPUT_CANCEL)) {
        if (actor == 1U && battle->player_actions[0].valid) {
            battle->player_actions[0] = (N64GameBattleAction){0};
            battle->command_actor = 0U;
            reset_battle_selection(game);
        }
        return;
    }

    if (pressed(input, N64GAME_INPUT_UP)) {
        game->battle_move_cursor = (uint8_t)(
            (game->battle_move_cursor + choice_count - 1U) % choice_count
        );
    } else if (pressed(input, N64GAME_INPUT_DOWN)) {
        game->battle_move_cursor = (uint8_t)((game->battle_move_cursor + 1U) % choice_count);
    }
    if (!pressed(input, N64GAME_INPUT_CONFIRM)) {
        return;
    }
    if (game->battle_move_cursor == N64GAME_MOVE_FINISHER) {
        if (n64game_battle_commit_finisher(battle)) {
            reset_battle_selection(game);
            game->battle_present_delay = 0U;
        }
        return;
    }
    const N64GameMoveDef *const move = n64game_move_def(
        battle->actors[actor].id, game->battle_move_cursor
    );
    if (move == NULL) {
        return;
    }
    if (move->target_rule == N64GAME_TARGET_ALL_ENEMIES) {
        if (n64game_battle_commit_action(
                battle, actor, game->battle_move_cursor, N64GAME_TARGET_ALL)) {
            reset_battle_selection(game);
            game->battle_present_delay = 0U;
        }
    } else if (move->target_rule == N64GAME_TARGET_SELF) {
        if (n64game_battle_commit_action(battle, actor, game->battle_move_cursor, actor)) {
            reset_battle_selection(game);
            game->battle_present_delay = 0U;
        }
    } else {
        const uint8_t target = first_legal_target(
            battle, actor, game->battle_move_cursor, UINT8_C(3), 1
        );
        if (target != N64GAME_TARGET_ALL) {
            game->battle_target_cursor = target;
            game->battle_selecting_target = true;
        }
    }
}

void n64game_core_init(N64GameCore *game)
{
    if (game == NULL) {
        return;
    }
    *game = (N64GameCore){
        .scene = N64GAME_SCENE_BOOT,
        .quest = N64GAME_QUEST_MEET_SERA,
        .party_hp = {N64GAME_QUARRUNE_MAX_HP, N64GAME_AYSELOR_MAX_HP},
        .annex_sector = N64GAME_ANNEX_ATRIUM,
    };
    n64game_annex_safe_anchor(
        game->annex_sector, &game->player_x_q8, &game->player_z_q8
    );
}

static bool player_control_available(const N64GameCore *game)
{
    if (game->scene == N64GAME_SCENE_NAME_ENTRY) {
        return true;
    }
    if (game->scene == N64GAME_SCENE_ANNEX) {
        return game->dialogue == N64GAME_DIALOGUE_NONE;
    }
    if (game->scene == N64GAME_SCENE_BATTLE) {
        return game->battle.phase == N64GAME_BATTLE_COMMAND ||
            game->battle.phase == N64GAME_BATTLE_VICTORY ||
            game->battle.phase == N64GAME_BATTLE_DEFEAT;
    }
    return false;
}

void n64game_core_update(N64GameCore *game, N64GameInput input)
{
    if (game == NULL) {
        return;
    }
    ++game->scene_ticks;
    if (game->scene != N64GAME_SCENE_BOOT && game->scene != N64GAME_SCENE_END_CHAPTER) {
        ++game->play_ticks;
    }
    if (player_control_available(game)) {
        ++game->active_control_ticks;
    }
    switch (game->scene) {
    case N64GAME_SCENE_BOOT:
        if (game->scene_ticks >= BOOT_TICKS) {
            set_scene(game, N64GAME_SCENE_OPENING_SLATE);
        }
        break;
    case N64GAME_SCENE_OPENING_SLATE:
        if (game->scene_ticks >= SLATE_TICKS ||
            pressed(input, N64GAME_INPUT_CONFIRM) ||
            pressed(input, N64GAME_INPUT_START)) {
            game->opening_cinematic_seen = true;
            set_scene(game, N64GAME_SCENE_NAME_ENTRY);
        }
        break;
    case N64GAME_SCENE_NAME_ENTRY:
        update_name_entry(game, input);
        break;
    case N64GAME_SCENE_ANNEX:
        update_annex(game, input);
        break;
    case N64GAME_SCENE_BATTLE:
        if (game->battle.phase == N64GAME_BATTLE_INTRO) {
            if (game->scene_ticks >= 45U) {
                game->battle.phase = N64GAME_BATTLE_COMMAND;
            }
        } else if (game->battle.phase == N64GAME_BATTLE_PRESENT) {
            if (++game->battle_present_delay >= 20U) {
                game->battle_present_delay = 0U;
                (void)n64game_battle_resolve_next(&game->battle);
                if (game->battle.phase == N64GAME_BATTLE_COMMAND) {
                    reset_battle_selection(game);
                }
            }
        } else if (game->battle.phase == N64GAME_BATTLE_COMMAND && game->scene_ticks >= 45U) {
            update_battle_command(game, input);
        } else if (game->battle.phase == N64GAME_BATTLE_VICTORY &&
                   pressed(input, N64GAME_INPUT_CONFIRM)) {
            game->battle_won = true;
            if (!game->battle_reward_claimed) {
                game->battle_reward_claimed = true;
            }
            set_scene(game, N64GAME_SCENE_ANNEX);
            begin_dialogue(game, N64GAME_DIALOGUE_BATTLE_VICTORY);
        } else if (game->battle.phase == N64GAME_BATTLE_DEFEAT) {
            if (pressed(input, N64GAME_INPUT_CONFIRM)) {
                restore_prebattle_snapshot(game);
            } else if (pressed(input, N64GAME_INPUT_CANCEL)) {
                restore_prebattle_snapshot(game);
                game->battle.phase = N64GAME_BATTLE_INACTIVE;
                game->quest = N64GAME_QUEST_RETURN_TO_SERA;
                set_scene(game, N64GAME_SCENE_ANNEX);
            }
        }
        break;
    case N64GAME_SCENE_END_CHAPTER:
        update_post_chapter_menu(game, input);
        break;
    }
}

void n64game_core_update_controller(
    N64GameCore *game,
    N64GameInput input,
    bool controller_connected,
    bool clear_edge_frame
)
{
    if (!controller_connected || clear_edge_frame) {
        if (game != NULL && game->scene == N64GAME_SCENE_ANNEX) {
            game->player_velocity_x_q8 = 0;
            game->player_velocity_z_q8 = 0;
        }
        return;
    }
    n64game_core_update(game, input);
}

void n64game_core_set_player_position(N64GameCore *game, int32_t x_q8, int32_t z_q8)
{
    if (game == NULL) {
        return;
    }
    if (n64game_annex_position_valid(x_q8, z_q8)) {
        game->player_x_q8 = x_q8;
        game->player_z_q8 = z_q8;
        game->annex_sector = n64game_annex_sector_for_position(
            x_q8, z_q8, game->annex_sector
        );
    } else {
        n64game_annex_safe_anchor(
            game->annex_sector, &game->player_x_q8, &game->player_z_q8
        );
    }
    game->player_velocity_x_q8 = 0;
    game->player_velocity_z_q8 = 0;
}

bool n64game_core_can_interact(const N64GameCore *game)
{
    return n64game_core_interaction_label(game) != NULL;
}

const char *n64game_core_interaction_label(const N64GameCore *game)
{
    if (game == NULL || game->scene != N64GAME_SCENE_ANNEX ||
        game->menu != N64GAME_MENU_CLOSED || game->paused ||
        game->dialogue != N64GAME_DIALOGUE_NONE) {
        return NULL;
    }
    const N64GameAnnexInteraction interaction = n64game_annex_interaction_at(
        game->player_x_q8, game->player_z_q8
    );
    if (game->quest == N64GAME_QUEST_MEET_SERA &&
        interaction == N64GAME_ANNEX_INTERACTION_SERA) {
        return "TALK TO SERA";
    }
    if (game->quest == N64GAME_QUEST_RETRIEVE_RELAY &&
        interaction == N64GAME_ANNEX_INTERACTION_FIELD_RELAY) {
        return "TAKE FIELD RELAY";
    }
    if (game->quest == N64GAME_QUEST_RETURN_TO_SERA &&
        interaction == N64GAME_ANNEX_INTERACTION_SERA) {
        return "BEGIN TRIAL";
    }
    if (game->quest == N64GAME_QUEST_BEACON_OVERLOOK &&
        interaction == N64GAME_ANNEX_INTERACTION_BEACON) {
        return "TRACE BEACON";
    }
    if (interaction == N64GAME_ANNEX_INTERACTION_TAVI) {
        return "TALK TO TAVI";
    }
    if (interaction == N64GAME_ANNEX_INTERACTION_FIELD_RELAY && game->relay_unlocked) {
        return "OPEN FIELD RELAY";
    }
    if (interaction >= N64GAME_ANNEX_INTERACTION_EXAMINE_SIM_RING &&
        interaction < N64GAME_ANNEX_INTERACTION_COUNT) {
        return n64game_annex_interaction_label(interaction);
    }
    return NULL;
}

uint8_t n64game_dialogue_page_count(N64GameDialogue dialogue)
{
    static const uint8_t PAGE_COUNTS[] = { 0, 3, 2, 2, 2, 2, 4, 1, 1, 1, 1 };
    if ((unsigned)dialogue >= sizeof(PAGE_COUNTS) / sizeof(PAGE_COUNTS[0])) {
        return 0U;
    }
    return PAGE_COUNTS[dialogue];
}

const N64GameMoveDef *n64game_move_def(N64GameEchoform actor, uint8_t move)
{
    if ((unsigned)actor >= N64GAME_BATTLE_ACTOR_COUNT || move >= N64GAME_BATTLE_MOVE_COUNT) {
        return NULL;
    }
    return &MOVES[actor][move];
}

static const char *scene_code(N64GameScene scene)
{
    switch (scene) {
    case N64GAME_SCENE_BOOT: return "BOOT";
    case N64GAME_SCENE_OPENING_SLATE: return "SLATE";
    case N64GAME_SCENE_NAME_ENTRY: return "NAME";
    case N64GAME_SCENE_ANNEX: return "ANNEX";
    case N64GAME_SCENE_BATTLE: return "BATTLE";
    case N64GAME_SCENE_END_CHAPTER: return "END";
    }
    return "UNKNOWN";
}

static const char *quest_code(N64GameQuest quest)
{
    switch (quest) {
    case N64GAME_QUEST_MEET_SERA: return "MEET_SERA";
    case N64GAME_QUEST_RETRIEVE_RELAY: return "GET_RELAY";
    case N64GAME_QUEST_RETURN_TO_SERA: return "RETURN";
    case N64GAME_QUEST_RESONANCE_TRIAL: return "TRIAL";
    case N64GAME_QUEST_BEACON_OVERLOOK: return "BEACON";
    case N64GAME_QUEST_COMPLETE: return "COMPLETE";
    }
    return "UNKNOWN";
}

static uint8_t bit_count8(uint8_t value)
{
    uint8_t count = 0U;
    while (value != 0U) {
        count = (uint8_t)(count + (uint8_t)(value & UINT8_C(1)));
        value = (uint8_t)(value >> 1);
    }
    return count;
}

void n64game_core_certification_summary(
    const N64GameCore *game,
    char *timing,
    size_t timing_size,
    char *state,
    size_t state_size,
    char *coverage,
    size_t coverage_size
)
{
    if (game == NULL) {
        if (timing != NULL && timing_size > 0U) {
            timing[0] = '\0';
        }
        if (state != NULL && state_size > 0U) {
            state[0] = '\0';
        }
        if (coverage != NULL && coverage_size > 0U) {
            coverage[0] = '\0';
        }
        return;
    }

    const uint32_t play_seconds = game->play_ticks / UINT32_C(30);
    const uint32_t active_seconds = game->active_control_ticks / UINT32_C(30);
    if (timing != NULL && timing_size > 0U) {
        (void)snprintf(
            timing,
            timing_size,
            "TIME %02u:%02u / CTRL %02u:%02u",
            (unsigned)(play_seconds / UINT32_C(60)),
            (unsigned)(play_seconds % UINT32_C(60)),
            (unsigned)(active_seconds / UINT32_C(60)),
            (unsigned)(active_seconds % UINT32_C(60))
        );
    }
    if (state != NULL && state_size > 0U) {
        (void)snprintf(
            state,
            state_size,
            "STATE %s / %s",
            scene_code(game->scene),
            quest_code(game->quest)
        );
    }
    if (coverage != NULL && coverage_size > 0U) {
        (void)snprintf(
            coverage,
            coverage_size,
            "EXAM %u/4 RELAY %u/4 %s",
            (unsigned)bit_count8(game->examine_flags),
            (unsigned)bit_count8(game->relay_pages_seen),
            game->slice_complete ? "HOOK" : "OPEN"
        );
    }
}

static void clear_buffer(char *buffer, size_t size)
{
    if (buffer != NULL && size > 0U) {
        buffer[0] = '\0';
    }
}

static unsigned kib_rounded(uint32_t bytes)
{
    return (unsigned)((bytes + UINT32_C(512)) / UINT32_C(1024));
}

void n64game_core_performance_summary(
    const N64GameCertificationTelemetry *telemetry,
    char *fps,
    size_t fps_size,
    char *heap,
    size_t heap_size,
    char *resources,
    size_t resources_size
)
{
    if (telemetry == NULL || !telemetry->valid) {
        clear_buffer(fps, fps_size);
        clear_buffer(heap, heap_size);
        clear_buffer(resources, resources_size);
        return;
    }

    if (fps != NULL && fps_size > 0U) {
        (void)snprintf(
            fps,
            fps_size,
            "FPS %02u.%u MIN %02u.%u",
            (unsigned)(telemetry->fps_x10 / UINT16_C(10)),
            (unsigned)(telemetry->fps_x10 % UINT16_C(10)),
            (unsigned)(telemetry->fps_min_x10 / UINT16_C(10)),
            (unsigned)(telemetry->fps_min_x10 % UINT16_C(10))
        );
    }
    if (heap != NULL && heap_size > 0U) {
        (void)snprintf(
            heap,
            heap_size,
            "HEAP %uK MIN %uK BASE %uK",
            kib_rounded(telemetry->free_heap_bytes),
            kib_rounded(telemetry->free_heap_min_bytes),
            kib_rounded(telemetry->heap_baseline_bytes)
        );
    }
    if (resources != NULL && resources_size > 0U) {
        (void)snprintf(
            resources,
            resources_size,
            "FRAME %uUS / RES %u",
            (unsigned)telemetry->frame_us,
            (unsigned)telemetry->resource_count
        );
    }
}

static N64GameBattleActor make_actor(
    N64GameEchoform id,
    N64GameAffinity affinity,
    int16_t hp,
    int16_t power,
    int16_t guard,
    int16_t speed,
    bool player_side
)
{
    return (N64GameBattleActor){
        .id = id,
        .affinity = affinity,
        .hp = hp,
        .max_hp = hp,
        .power = power,
        .guard = guard,
        .speed = speed,
        .player_side = player_side,
    };
}

void n64game_battle_begin(N64GameBattle *battle)
{
    if (battle == NULL) {
        return;
    }
    *battle = (N64GameBattle){
        .phase = N64GAME_BATTLE_INTRO,
        .actors = {
            make_actor(N64GAME_ECHO_QUARRUNE, N64GAME_AFFINITY_STRATA,
                       N64GAME_QUARRUNE_MAX_HP, 12, 10, 36, true),
            make_actor(N64GAME_ECHO_AYSELOR, N64GAME_AFFINITY_GALE,
                       N64GAME_AYSELOR_MAX_HP, 14, 7, 54, true),
            make_actor(N64GAME_ECHO_GYRECLAST, N64GAME_AFFINITY_CURRENT, 84, 12, 9, 42, false),
            make_actor(N64GAME_ECHO_KIVARRAX, N64GAME_AFFINITY_EMBER, 86, 14, 8, 48, false),
        },
        .round = 1U,
    };
}

static bool alive(const N64GameBattleActor *actor)
{
    return actor->hp > 0;
}

static bool same_side(const N64GameBattleActor *left, const N64GameBattleActor *right)
{
    return left->player_side == right->player_side;
}

bool n64game_battle_target_legal(
    const N64GameBattle *battle,
    uint8_t actor,
    uint8_t move,
    uint8_t target
)
{
    if (battle == NULL || actor >= N64GAME_BATTLE_ACTOR_COUNT ||
        move >= N64GAME_BATTLE_MOVE_COUNT || !alive(&battle->actors[actor])) {
        return false;
    }
    const N64GameMoveDef *const definition = n64game_move_def(battle->actors[actor].id, move);
    if (definition == NULL) {
        return false;
    }
    if (definition->target_rule == N64GAME_TARGET_ALL_ENEMIES) {
        return target == N64GAME_TARGET_ALL;
    }
    if (target >= N64GAME_BATTLE_ACTOR_COUNT || !alive(&battle->actors[target])) {
        return false;
    }
    switch (definition->target_rule) {
    case N64GAME_TARGET_ONE_ENEMY:
        return !same_side(&battle->actors[actor], &battle->actors[target]);
    case N64GAME_TARGET_ONE_ALLY:
        return same_side(&battle->actors[actor], &battle->actors[target]);
    case N64GAME_TARGET_SELF:
        return actor == target;
    case N64GAME_TARGET_ALL_ENEMIES:
        return false;
    }
    return false;
}

static N64GameBattleAction enemy_action(const N64GameBattle *battle, uint8_t actor)
{
    uint8_t move = 0U;
    uint8_t target = 0U;
    if (actor == 2U && battle->round == 1U && alive(&battle->actors[3])) {
        move = 1U;
        target = 3U;
    } else if (battle->actors[actor].hp * 3 < battle->actors[actor].max_hp &&
               alive(&battle->actors[actor])) {
        move = 3U;
        target = actor;
    } else {
        const int16_t left_hp = battle->actors[0].hp;
        const int16_t right_hp = battle->actors[1].hp;
        target = (uint8_t)((right_hp > 0 && (left_hp <= 0 || right_hp < left_hp)) ? 1U : 0U);
    }
    const N64GameMoveDef *const definition = n64game_move_def(battle->actors[actor].id, move);
    return (N64GameBattleAction){
        .actor = actor,
        .move = move,
        .target = target,
        .priority = definition->priority,
        .valid = true,
    };
}

static int16_t action_speed(const N64GameBattle *battle, const N64GameBattleAction *action)
{
    const N64GameBattleActor *const actor = &battle->actors[action->actor];
    return (int16_t)(actor->speed - (actor->stagger_rounds > 0U ? 16 : 0));
}

static bool action_precedes(
    const N64GameBattle *battle,
    const N64GameBattleAction *left,
    const N64GameBattleAction *right
)
{
    if (left->priority != right->priority) {
        return left->priority > right->priority;
    }
    const int16_t left_speed = action_speed(battle, left);
    const int16_t right_speed = action_speed(battle, right);
    if (left_speed != right_speed) {
        return left_speed > right_speed;
    }
    return left->actor < right->actor;
}

static void build_queue(N64GameBattle *battle)
{
    battle->queue_count = 0U;
    battle->queue_cursor = 0U;
    for (size_t index = 0U; index < 2U; ++index) {
        if (battle->player_actions[index].valid) {
            battle->queue[battle->queue_count++] = battle->player_actions[index];
        }
    }
    battle->queue[battle->queue_count++] = enemy_action(battle, 2U);
    battle->queue[battle->queue_count++] = enemy_action(battle, 3U);
    for (uint8_t index = 1U; index < battle->queue_count; ++index) {
        N64GameBattleAction action = battle->queue[index];
        uint8_t position = index;
        while (position > 0U && action_precedes(battle, &action, &battle->queue[position - 1U])) {
            battle->queue[position] = battle->queue[position - 1U];
            --position;
        }
        battle->queue[position] = action;
    }
    battle->phase = N64GAME_BATTLE_PRESENT;
}

bool n64game_battle_commit_action(
    N64GameBattle *battle,
    uint8_t actor,
    uint8_t move,
    uint8_t target
)
{
    if (battle == NULL || battle->phase != N64GAME_BATTLE_COMMAND ||
        actor != battle->command_actor || actor > 1U ||
        !n64game_battle_target_legal(battle, actor, move, target)) {
        return false;
    }
    const N64GameMoveDef *const definition = n64game_move_def(battle->actors[actor].id, move);
    battle->player_actions[actor] = (N64GameBattleAction){
        .actor = actor,
        .move = move,
        .target = target,
        .priority = definition->priority,
        .valid = true,
    };
    if (actor == 0U && alive(&battle->actors[1])) {
        battle->command_actor = 1U;
    } else {
        build_queue(battle);
    }
    return true;
}

bool n64game_battle_commit_finisher(N64GameBattle *battle)
{
    if (battle == NULL || battle->phase != N64GAME_BATTLE_COMMAND ||
        battle->command_actor != 0U || battle->resonance < N64GAME_RESONANCE_MAX ||
        !alive(&battle->actors[0]) || !alive(&battle->actors[1])) {
        return false;
    }
    battle->player_actions[0] = (N64GameBattleAction){
        .actor = 0U,
        .move = N64GAME_MOVE_FINISHER,
        .target = N64GAME_TARGET_ALL,
        .priority = 2,
        .valid = true,
    };
    battle->player_actions[1] = (N64GameBattleAction){0};
    battle->resonance = 0U;
    build_queue(battle);
    return true;
}

static bool affinity_advantage(N64GameAffinity attack, N64GameAffinity defense)
{
    return (attack == N64GAME_AFFINITY_STRATA && defense == N64GAME_AFFINITY_CURRENT) ||
        (attack == N64GAME_AFFINITY_CURRENT && defense == N64GAME_AFFINITY_EMBER) ||
        (attack == N64GAME_AFFINITY_EMBER && defense == N64GAME_AFFINITY_GALE) ||
        (attack == N64GAME_AFFINITY_GALE && defense == N64GAME_AFFINITY_STRATA);
}

static uint8_t first_living_target(const N64GameBattle *battle, bool player_side)
{
    for (uint8_t index = 0U; index < N64GAME_BATTLE_ACTOR_COUNT; ++index) {
        if (battle->actors[index].player_side == player_side && alive(&battle->actors[index])) {
            return index;
        }
    }
    return N64GAME_TARGET_ALL;
}

static bool side_defeated(const N64GameBattle *battle, bool player_side)
{
    return first_living_target(battle, player_side) == N64GAME_TARGET_ALL;
}

static void add_resonance(N64GameBattle *battle, uint8_t amount)
{
    const unsigned total = (unsigned)battle->resonance + amount;
    battle->resonance = (uint8_t)(total > N64GAME_RESONANCE_MAX ? N64GAME_RESONANCE_MAX : total);
}

static int16_t apply_damage(
    N64GameBattle *battle,
    uint8_t actor_index,
    uint8_t target_index,
    const N64GameMoveDef *move
)
{
    const N64GameBattleActor *const actor = &battle->actors[actor_index];
    N64GameBattleActor *const target = &battle->actors[target_index];
    int32_t damage_value = (int32_t)move->power + (int32_t)actor->power -
        (int32_t)target->guard - (int32_t)target->guard_stage * 3;
    if (damage_value < 1) {
        damage_value = 1;
    }
    const bool advantage = affinity_advantage(move->affinity, target->affinity);
    if (advantage) {
        damage_value += damage_value / 2;
    }
    if (damage_value > target->hp) {
        damage_value = target->hp;
    }
    const int16_t damage = (int16_t)damage_value;
    target->hp = (int16_t)(target->hp - damage);
    battle->last_event = (N64GameBattleEvent){
        .happened = true,
        .actor = actor_index,
        .move = (uint8_t)(move - MOVES[actor->id]),
        .target = target_index,
        .hp_delta = (int16_t)-damage,
        .affinity_advantage = advantage,
        .knockout = target->hp == 0,
    };
    if (move->effect == N64GAME_EFFECT_DAMAGE_STAGGER && target->hp > 0) {
        target->stagger_rounds = 2U;
    }
    return damage;
}

static void apply_action(N64GameBattle *battle, const N64GameBattleAction *action)
{
    battle->last_event = (N64GameBattleEvent){0};
    if (!alive(&battle->actors[action->actor])) {
        battle->last_event = (N64GameBattleEvent){
            .happened = true,
            .skipped = true,
            .actor = action->actor,
            .move = action->move,
        };
        return;
    }
    if (action->move == N64GAME_MOVE_FINISHER) {
        for (uint8_t target = 2U; target < 4U; ++target) {
            if (alive(&battle->actors[target])) {
                const int16_t damage = battle->actors[target].hp < 36 ?
                    battle->actors[target].hp : 36;
                battle->actors[target].hp = (int16_t)(battle->actors[target].hp - damage);
                battle->last_event = (N64GameBattleEvent){
                    .happened = true,
                    .actor = 0U,
                    .move = N64GAME_MOVE_FINISHER,
                    .target = N64GAME_TARGET_ALL,
                    .hp_delta = (int16_t)-damage,
                    .knockout = battle->actors[target].hp == 0,
                };
            }
        }
        return;
    }

    const N64GameMoveDef *const move = n64game_move_def(
        battle->actors[action->actor].id, action->move
    );
    if (move == NULL) {
        return;
    }
    if (move->target_rule == N64GAME_TARGET_ALL_ENEMIES) {
        const bool target_side = !battle->actors[action->actor].player_side;
        for (uint8_t target = 0U; target < N64GAME_BATTLE_ACTOR_COUNT; ++target) {
            if (battle->actors[target].player_side == target_side && alive(&battle->actors[target])) {
                (void)apply_damage(battle, action->actor, target, move);
            }
        }
    } else {
        uint8_t target = action->target;
        if (!n64game_battle_target_legal(battle, action->actor, action->move, target)) {
            const bool desired_side = move->target_rule == N64GAME_TARGET_ONE_ENEMY ?
                !battle->actors[action->actor].player_side : battle->actors[action->actor].player_side;
            target = first_living_target(battle, desired_side);
        }
        if (target == N64GAME_TARGET_ALL) {
            battle->last_event = (N64GameBattleEvent){
                .happened = true,
                .skipped = true,
                .actor = action->actor,
                .move = action->move,
            };
            return;
        }
        if (move->effect == N64GAME_EFFECT_DAMAGE ||
            move->effect == N64GAME_EFFECT_DAMAGE_STAGGER) {
            (void)apply_damage(battle, action->actor, target, move);
        } else if (move->effect == N64GAME_EFFECT_GUARD) {
            if (battle->actors[target].guard_stage < 3) {
                ++battle->actors[target].guard_stage;
                battle->last_event = (N64GameBattleEvent){
                    .happened = true, .actor = action->actor, .move = action->move,
                    .target = target,
                };
            } else {
                battle->last_event = (N64GameBattleEvent){
                    .happened = true, .skipped = true, .actor = action->actor,
                    .move = action->move, .target = target,
                };
            }
        } else if (move->effect == N64GAME_EFFECT_HEAL) {
            int16_t healing = move->power;
            const int16_t missing = (int16_t)(battle->actors[target].max_hp - battle->actors[target].hp);
            if (healing > missing) {
                healing = missing;
            }
            battle->actors[target].hp = (int16_t)(battle->actors[target].hp + healing);
            battle->last_event = (N64GameBattleEvent){
                .happened = true,
                .skipped = healing == 0,
                .actor = action->actor,
                .move = action->move,
                .target = target,
                .hp_delta = healing,
            };
        }
    }
    if (battle->actors[action->actor].player_side && battle->last_event.happened &&
        !battle->last_event.skipped) {
        add_resonance(battle, move->resonance_gain);
        if (battle->last_event.affinity_advantage) {
            add_resonance(battle, 4U);
        }
    }
}

bool n64game_battle_resolve_next(N64GameBattle *battle)
{
    if (battle == NULL || battle->phase != N64GAME_BATTLE_PRESENT ||
        battle->queue_cursor >= battle->queue_count) {
        return false;
    }
    apply_action(battle, &battle->queue[battle->queue_cursor++]);
    if (side_defeated(battle, false)) {
        battle->phase = N64GAME_BATTLE_VICTORY;
        return true;
    }
    if (side_defeated(battle, true)) {
        battle->phase = N64GAME_BATTLE_DEFEAT;
        return true;
    }
    if (battle->queue_cursor == battle->queue_count) {
        for (size_t index = 0U; index < N64GAME_BATTLE_ACTOR_COUNT; ++index) {
            if (battle->actors[index].stagger_rounds > 0U) {
                --battle->actors[index].stagger_rounds;
            }
        }
        ++battle->round;
        battle->command_actor = first_living_target(battle, true);
        battle->queue_count = 0U;
        battle->queue_cursor = 0U;
        battle->player_actions[0] = (N64GameBattleAction){0};
        battle->player_actions[1] = (N64GameBattleAction){0};
        battle->phase = N64GAME_BATTLE_COMMAND;
    }
    return true;
}
