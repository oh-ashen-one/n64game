#include "n64game_core.h"

#include <limits.h>
#include <string.h>

enum {
    BOOT_TICKS = 30,
    SLATE_TICKS = 106,
    NAME_COLUMNS = 7,
    NAME_SLOT_BACK = 26,
    NAME_SLOT_CONFIRM = 27,
    ANNEX_STICK_DEADZONE = 12,
    ANNEX_WALK_SPEED_Q8 = 85,
    ANNEX_RUN_SPEED_Q8 = 154,
    ANNEX_ACCEL_Q8 = 16,
    ANNEX_DECEL_Q8 = 24,
};

static const uint8_t CALIBRATION_TARGETS[N64GAME_CALIBRATION_STEP_COUNT] = {
    2U, 0U, 1U,
};

#define MOVE(name_, affinity_, target_, effect_, power_, resonance_, priority_, chance_, rounds_, cooldown_, once_) \
    { \
        .name = (name_), .affinity = (affinity_), .target_rule = (target_), \
        .effect = (effect_), .power = (power_), .resonance_gain = (resonance_), \
        .priority = (priority_), .effect_chance_percent = (chance_), \
        .stage_rounds = (rounds_), .cooldown_rounds = (cooldown_), \
        .once_per_encounter = (once_), \
    }

static const N64GameMoveDef MOVES[N64GAME_BATTLE_ACTOR_COUNT][N64GAME_BATTLE_MOVE_COUNT] = {
    [N64GAME_ECHO_QUARRUNE] = {
        MOVE("RIDGE RAM", N64GAME_AFFINITY_STRATA, N64GAME_TARGET_ONE_ENEMY,
             N64GAME_EFFECT_DAMAGE, 28, 6, 0, 0, 0, 0, false),
        MOVE("BRACE RELAY", N64GAME_AFFINITY_STRATA, N64GAME_TARGET_ONE_ALLY,
             N64GAME_EFFECT_GUARD_UP, 0, 14, 0, 0, 2, 0, false),
        MOVE("GROUNDING RING", N64GAME_AFFINITY_STRATA, N64GAME_TARGET_ALL_ENEMIES,
             N64GAME_EFFECT_DAMAGE_GROUND, 14, 6, 0, 0, 0, 0, false),
        MOVE("STEADY PULSE", N64GAME_AFFINITY_STRATA, N64GAME_TARGET_ONE_ALLY,
             N64GAME_EFFECT_HEAL_CLEAR_STAGGER, 12, 0, 0, 0, 0, 0, true),
    },
    [N64GAME_ECHO_AYSELOR] = {
        MOVE("SIROCCO SLICE", N64GAME_AFFINITY_GALE, N64GAME_TARGET_ONE_ENEMY,
             N64GAME_EFFECT_DAMAGE, 26, 6, 0, 0, 0, 0, false),
        MOVE("LIFT CURRENT", N64GAME_AFFINITY_GALE, N64GAME_TARGET_ONE_ALLY,
             N64GAME_EFFECT_SPEED_UP, 0, 14, 0, 0, 2, 0, false),
        MOVE("DAZZLE WAKE", N64GAME_AFFINITY_GALE, N64GAME_TARGET_ALL_ENEMIES,
             N64GAME_EFFECT_DAMAGE_STAGGER_CHANCE, 12, 6, 0, 35, 0, 0, false),
        MOVE("GUIDING DRAFT", N64GAME_AFFINITY_GALE, N64GAME_TARGET_ONE_ALLY,
             N64GAME_EFFECT_EMPOWER_NEXT_DAMAGE, 0, 12, 0, 0, 0, 0, false),
    },
    [N64GAME_ECHO_GYRECLAST] = {
        MOVE("AUGER KNUCKLE", N64GAME_AFFINITY_STRATA, N64GAME_TARGET_ONE_ENEMY,
             N64GAME_EFFECT_DAMAGE, 27, 0, 0, 0, 0, 0, false),
        MOVE("DUST SCREEN", N64GAME_AFFINITY_STRATA, N64GAME_TARGET_ALL_ENEMIES,
             N64GAME_EFFECT_POWER_DOWN, 0, 0, 0, 0, 1, 0, false),
        MOVE("FAULT PIN", N64GAME_AFFINITY_STRATA, N64GAME_TARGET_ONE_ENEMY,
             N64GAME_EFFECT_DAMAGE_STAGGER, 18, 0, 0, 100, 0, 2, false),
        MOVE("CARAPACE BRACE", N64GAME_AFFINITY_STRATA, N64GAME_TARGET_SELF,
             N64GAME_EFFECT_GUARD_UP, 0, 0, 0, 0, 2, 0, false),
    },
    [N64GAME_ECHO_KIVARRAX] = {
        MOVE("CROSSWIND CUT", N64GAME_AFFINITY_GALE, N64GAME_TARGET_ONE_ENEMY,
             N64GAME_EFFECT_DAMAGE, 25, 0, 0, 0, 0, 0, false),
        MOVE("SLIPSTREAM", N64GAME_AFFINITY_GALE, N64GAME_TARGET_ONE_ALLY,
             N64GAME_EFFECT_SPEED_UP, 0, 0, 0, 0, 2, 0, false),
        MOVE("PRESSURE DROP", N64GAME_AFFINITY_GALE, N64GAME_TARGET_ONE_ENEMY,
             N64GAME_EFFECT_GUARD_DOWN, 0, 0, 0, 0, 2, 0, false),
        MOVE("TALON SWEEP", N64GAME_AFFINITY_GALE, N64GAME_TARGET_ALL_ENEMIES,
             N64GAME_EFFECT_DAMAGE, 12, 0, 0, 0, 0, 0, false),
    },
};

#undef MOVE

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
        game->battle.command_actor = 0U;
    } else if (game->battle.actors[1].hp > 0) {
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
        game->quest = N64GAME_QUEST_MEET_TAVI;
        break;
    case N64GAME_DIALOGUE_TAVI_INTRO:
        game->quest = N64GAME_QUEST_RETRIEVE_RELAY;
        break;
    case N64GAME_DIALOGUE_RELAY:
        game->relay_acquired = true;
        game->relay_unlocked = false;
        game->quest = N64GAME_QUEST_CALIBRATE_RELAY;
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
        set_scene(game, N64GAME_SCENE_END_CHAPTER);
        game->final_save_state = N64GAME_FINAL_SAVE_PENDING;
        game->save_requested = true;
        game->paused = true;
        break;
    case N64GAME_DIALOGUE_TAVI_REPEAT:
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

static void open_calibration(N64GameCore *game)
{
    open_root_menu(game, N64GAME_MENU_RELAY_CALIBRATION);
    game->calibration_step = 0U;
    game->calibration_cursor = 0U;
    game->calibration_error = false;
}

static void update_calibration(N64GameCore *game, N64GameInput input)
{
    if (pressed(input, N64GAME_INPUT_START) ||
        pressed(input, N64GAME_INPUT_PAUSE) ||
        pressed(input, N64GAME_INPUT_CANCEL)) {
        close_menu(game);
        game->calibration_step = 0U;
        game->calibration_cursor = 0U;
        game->calibration_error = false;
        return;
    }
    if (pressed(input, N64GAME_INPUT_LEFT) || pressed(input, N64GAME_INPUT_UP)) {
        game->calibration_cursor = (uint8_t)((game->calibration_cursor + 2U) % 3U);
        game->calibration_error = false;
    } else if (pressed(input, N64GAME_INPUT_RIGHT) ||
               pressed(input, N64GAME_INPUT_DOWN)) {
        game->calibration_cursor = (uint8_t)((game->calibration_cursor + 1U) % 3U);
        game->calibration_error = false;
    }
    if (!pressed(input, N64GAME_INPUT_CONFIRM)) {
        return;
    }
    if (game->calibration_step >= N64GAME_CALIBRATION_STEP_COUNT ||
        game->calibration_cursor != CALIBRATION_TARGETS[game->calibration_step]) {
        game->calibration_error = true;
        return;
    }
    ++game->calibration_step;
    game->calibration_error = false;
    if (game->calibration_step < N64GAME_CALIBRATION_STEP_COUNT) {
        game->calibration_cursor = 0U;
        return;
    }

    close_menu(game);
    game->relay_unlocked = true;
    game->quest = N64GAME_QUEST_READY_FOR_TRIAL;
    game->save_requested = true;
    begin_dialogue(game, N64GAME_DIALOGUE_SERA_TRIAL);
}

static void update_annex_menu(N64GameCore *game, N64GameInput input)
{
    if (game->menu == N64GAME_MENU_RELAY_CALIBRATION) {
        update_calibration(game, input);
        return;
    }
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
                if (game->relay_unlocked) {
                    open_submenu(game, N64GAME_MENU_PARTY, N64GAME_RELAY_PAGE_PARTY);
                }
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
    } else if (game->quest == N64GAME_QUEST_MEET_TAVI &&
               interaction == N64GAME_ANNEX_INTERACTION_TAVI) {
        begin_dialogue(game, N64GAME_DIALOGUE_TAVI_INTRO);
    } else if (game->quest == N64GAME_QUEST_RETRIEVE_RELAY &&
               interaction == N64GAME_ANNEX_INTERACTION_FIELD_RELAY) {
        begin_dialogue(game, N64GAME_DIALOGUE_RELAY);
    } else if (game->quest == N64GAME_QUEST_CALIBRATE_RELAY &&
               interaction == N64GAME_ANNEX_INTERACTION_EXAMINE_SIM_RING) {
        open_calibration(game);
    } else if (game->quest == N64GAME_QUEST_READY_FOR_TRIAL &&
               interaction == N64GAME_ANNEX_INTERACTION_EXAMINE_SIM_RING) {
        begin_dialogue(game, N64GAME_DIALOGUE_SERA_TRIAL);
    } else if (game->quest == N64GAME_QUEST_BEACON_OVERLOOK &&
               interaction == N64GAME_ANNEX_INTERACTION_BEACON) {
        begin_dialogue(game, N64GAME_DIALOGUE_BEACON_HOOK);
    } else if (interaction == N64GAME_ANNEX_INTERACTION_TAVI) {
        begin_dialogue(game, N64GAME_DIALOGUE_TAVI_REPEAT);
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

static void open_post_chapter_archive(N64GameCore *game)
{
    game->menu = N64GAME_MENU_POST_CHAPTER_ROOT;
    game->menu_parent = N64GAME_MENU_POST_CHAPTER_ROOT;
    game->menu_cursor = 0U;
    game->paused = true;
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

static void update_end_chapter(N64GameCore *game, N64GameInput input)
{
    switch (game->final_save_state) {
    case N64GAME_FINAL_SAVE_PENDING:
        return;
    case N64GAME_FINAL_SAVE_FAILED:
        if (pressed(input, N64GAME_INPUT_CONFIRM)) {
            game->final_save_state = N64GAME_FINAL_SAVE_PENDING;
            game->save_requested = true;
        } else if (pressed(input, N64GAME_INPUT_CANCEL)) {
            game->final_save_state = N64GAME_FINAL_SAVE_CONFIRM_UNSAVED;
        }
        return;
    case N64GAME_FINAL_SAVE_CONFIRM_UNSAVED:
        if (pressed(input, N64GAME_INPUT_CONFIRM)) {
            game->final_save_state = N64GAME_FINAL_SAVE_ACCEPTED_UNSAVED;
            open_post_chapter_archive(game);
        } else if (pressed(input, N64GAME_INPUT_CANCEL)) {
            game->final_save_state = N64GAME_FINAL_SAVE_FAILED;
        }
        return;
    case N64GAME_FINAL_SAVE_VERIFIED:
    case N64GAME_FINAL_SAVE_ACCEPTED_UNSAVED:
        update_post_chapter_menu(game, input);
        return;
    case N64GAME_FINAL_SAVE_NONE:
        return;
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
                game->quest = N64GAME_QUEST_READY_FOR_TRIAL;
                set_scene(game, N64GAME_SCENE_ANNEX);
            }
        }
        break;
    case N64GAME_SCENE_END_CHAPTER:
        update_end_chapter(game, input);
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
    if (game->quest == N64GAME_QUEST_MEET_TAVI &&
        interaction == N64GAME_ANNEX_INTERACTION_TAVI) {
        return "CHECK IN WITH TAVI";
    }
    if (game->quest == N64GAME_QUEST_RETRIEVE_RELAY &&
        interaction == N64GAME_ANNEX_INTERACTION_FIELD_RELAY) {
        return "TAKE FIELD RELAY";
    }
    if (game->quest == N64GAME_QUEST_CALIBRATE_RELAY &&
        interaction == N64GAME_ANNEX_INTERACTION_EXAMINE_SIM_RING) {
        return "CALIBRATE FIELD RELAY";
    }
    if (game->quest == N64GAME_QUEST_READY_FOR_TRIAL &&
        interaction == N64GAME_ANNEX_INTERACTION_EXAMINE_SIM_RING) {
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
    static const uint8_t PAGE_COUNTS[] = { 0, 4, 2, 1, 2, 2, 2, 6, 1, 1, 1, 1 };
    if ((unsigned)dialogue >= sizeof(PAGE_COUNTS) / sizeof(PAGE_COUNTS[0])) {
        return 0U;
    }
    return PAGE_COUNTS[dialogue];
}

uint8_t n64game_core_calibration_target(uint8_t step)
{
    if (step >= N64GAME_CALIBRATION_STEP_COUNT) {
        return 0U;
    }
    return CALIBRATION_TARGETS[step];
}

void n64game_core_set_final_save_result(N64GameCore *game, bool verified)
{
    if (game == NULL || game->scene != N64GAME_SCENE_END_CHAPTER ||
        !game->slice_complete || game->final_save_state != N64GAME_FINAL_SAVE_PENDING) {
        return;
    }
    game->save_requested = false;
    if (verified) {
        game->final_save_state = N64GAME_FINAL_SAVE_VERIFIED;
        open_post_chapter_archive(game);
    } else {
        game->final_save_state = N64GAME_FINAL_SAVE_FAILED;
        game->menu = N64GAME_MENU_CLOSED;
        game->menu_parent = N64GAME_MENU_CLOSED;
        game->menu_cursor = 0U;
        game->paused = true;
    }
}

const N64GameMoveDef *n64game_move_def(N64GameEchoform actor, uint8_t move)
{
    if ((unsigned)actor >= N64GAME_BATTLE_ACTOR_COUNT || move >= N64GAME_BATTLE_MOVE_COUNT) {
        return NULL;
    }
    return &MOVES[actor][move];
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
            make_actor(N64GAME_ECHO_GYRECLAST, N64GAME_AFFINITY_STRATA,
                       84, 12, 9, 42, false),
            make_actor(N64GAME_ECHO_KIVARRAX, N64GAME_AFFINITY_GALE,
                       86, 14, 8, 48, false),
        },
        .round = 1U,
        .random_state = UINT32_C(0x00C0B14E),
    };
    battle->phase = N64GAME_BATTLE_COMMAND;
}

static bool alive(const N64GameBattleActor *actor)
{
    return actor->hp > 0;
}

static bool same_side(const N64GameBattleActor *left, const N64GameBattleActor *right)
{
    return left->player_side == right->player_side;
}

static bool move_available(
    const N64GameBattle *battle,
    uint8_t actor,
    uint8_t move,
    const N64GameMoveDef *definition
)
{
    const N64GameBattleActor *const user = &battle->actors[actor];
    if (definition->once_per_encounter &&
        (user->used_move_mask & (uint8_t)(UINT8_C(1) << move)) != 0U) {
        return false;
    }
    return user->move_ready_round[move] == 0U ||
        battle->round >= user->move_ready_round[move];
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
    if (definition == NULL || !move_available(battle, actor, move, definition)) {
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
    const int16_t left_hp = battle->actors[0].hp;
    const int16_t right_hp = battle->actors[1].hp;
    uint8_t target = (uint8_t)(
        right_hp > 0 && (left_hp <= 0 || right_hp < left_hp) ? 1U : 0U
    );
    if (actor == 2U) {
        if (battle->round == 1U) {
            move = 1U;
            target = N64GAME_TARGET_ALL;
        } else if (battle->round % 3U == 2U &&
                   move_available(battle, actor, 2U, &MOVES[N64GAME_ECHO_GYRECLAST][2])) {
            move = 2U;
        } else if (battle->round % 3U == 0U && battle->actors[actor].guard_stage <= 0) {
            move = 3U;
            target = actor;
        }
    } else {
        if (battle->round == 1U) {
            move = 1U;
            target = alive(&battle->actors[2]) ? 2U : actor;
        } else if (battle->round % 3U == 0U) {
            move = 2U;
        } else if (battle->round % 2U == 0U) {
            move = 3U;
            target = N64GAME_TARGET_ALL;
        }
    }
    if (!n64game_battle_target_legal(battle, actor, move, target)) {
        move = 0U;
        target = (uint8_t)(
            right_hp > 0 && (left_hp <= 0 || right_hp < left_hp) ? 1U : 0U
        );
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
    int16_t speed = (int16_t)(actor->speed + (int16_t)actor->speed_stage * 8);
    if (speed < 1) {
        speed = 1;
    }
    if (actor->stagger_rounds > 0U) {
        speed = (int16_t)((int32_t)speed * 3 / 4);
    }
    return speed;
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

static void sort_queue_from(N64GameBattle *battle, uint8_t start)
{
    for (uint8_t index = (uint8_t)(start + 1U); index < battle->queue_count; ++index) {
        N64GameBattleAction action = battle->queue[index];
        uint8_t position = index;
        while (position > start &&
               action_precedes(battle, &action, &battle->queue[position - 1U])) {
            battle->queue[position] = battle->queue[position - 1U];
            --position;
        }
        battle->queue[position] = action;
    }
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
    sort_queue_from(battle, 0U);
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

static bool affinity_disadvantage(N64GameAffinity attack, N64GameAffinity defense)
{
    return affinity_advantage(defense, attack);
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

static bool damaging_effect(N64GameMoveEffect effect)
{
    return effect == N64GAME_EFFECT_DAMAGE ||
        effect == N64GAME_EFFECT_DAMAGE_STAGGER_CHANCE ||
        effect == N64GAME_EFFECT_DAMAGE_STAGGER ||
        effect == N64GAME_EFFECT_DAMAGE_GROUND;
}

static bool adjust_stage(
    int8_t *stage,
    uint8_t *expires_round,
    int8_t amount,
    uint8_t duration,
    uint8_t round
)
{
    int value = (int)*stage + (int)amount;
    if (value < N64GAME_BATTLE_STAGE_MIN) {
        value = N64GAME_BATTLE_STAGE_MIN;
    } else if (value > N64GAME_BATTLE_STAGE_MAX) {
        value = N64GAME_BATTLE_STAGE_MAX;
    }
    *stage = (int8_t)value;
    if (*stage == 0) {
        *expires_round = 0U;
    } else {
        const unsigned expiration = (unsigned)round + duration;
        *expires_round = (uint8_t)(expiration > UINT8_MAX ? UINT8_MAX : expiration);
    }
    return true;
}

static bool effect_roll(N64GameBattle *battle, uint8_t chance_percent)
{
    battle->random_state = battle->random_state * UINT32_C(1664525) +
        UINT32_C(1013904223);
    return (uint8_t)((battle->random_state >> 16) % 100U) < chance_percent;
}

static int16_t apply_damage(
    N64GameBattle *battle,
    uint8_t actor_index,
    uint8_t target_index,
    const N64GameMoveDef *move,
    bool empowered
)
{
    const N64GameBattleActor *const actor = &battle->actors[actor_index];
    N64GameBattleActor *const target = &battle->actors[target_index];
    int32_t damage_value = (int32_t)move->power + (int32_t)actor->power +
        (int32_t)actor->power_stage * 3 -
        (int32_t)target->guard - (int32_t)target->guard_stage * 3;
    if (damage_value < 1) {
        damage_value = 1;
    }
    if (empowered) {
        damage_value = damage_value * 6 / 5;
    }
    const bool advantage = affinity_advantage(move->affinity, target->affinity);
    if (advantage) {
        damage_value += damage_value / 2;
    } else if (affinity_disadvantage(move->affinity, target->affinity)) {
        damage_value = damage_value * 3 / 4;
        if (damage_value < 1) {
            damage_value = 1;
        }
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
    return damage;
}

static void mark_move_used(
    N64GameBattle *battle,
    const N64GameBattleAction *action,
    const N64GameMoveDef *move
)
{
    N64GameBattleActor *const user = &battle->actors[action->actor];
    user->used_move_mask |= (uint8_t)(UINT8_C(1) << action->move);
    if (move->cooldown_rounds > 0U) {
        const unsigned ready_round = (unsigned)battle->round +
            move->cooldown_rounds + 1U;
        user->move_ready_round[action->move] = (uint8_t)(
            ready_round > UINT8_MAX ? UINT8_MAX : ready_round
        );
    }
}

static void apply_action(N64GameBattle *battle, const N64GameBattleAction *action)
{
    battle->last_event = (N64GameBattleEvent){0};
    if (action->move == N64GAME_MOVE_FINISHER &&
        (!alive(&battle->actors[0]) || !alive(&battle->actors[1]))) {
        battle->resonance = N64GAME_RESONANCE_MAX;
        battle->queue_count = 0U;
        battle->queue_cursor = 0U;
        battle->player_actions[0] = (N64GameBattleAction){0};
        battle->player_actions[1] = (N64GameBattleAction){0};
        battle->command_actor = first_living_target(battle, true);
        battle->phase = battle->command_actor == N64GAME_TARGET_ALL ?
            N64GAME_BATTLE_DEFEAT : N64GAME_BATTLE_COMMAND;
        battle->last_event = (N64GameBattleEvent){
            .happened = true,
            .skipped = true,
            .actor = 0U,
            .move = N64GAME_MOVE_FINISHER,
            .target = N64GAME_TARGET_ALL,
        };
        return;
    }
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
    N64GameBattleActor *const user = &battle->actors[action->actor];
    const bool user_was_staggered = user->stagger_rounds > 0U;
    const bool is_damage = damaging_effect(move->effect);
    const bool empowered = is_damage && user->empowered_damage;
    uint8_t resolved_target = action->target;
    bool any_success = false;
    bool any_advantage = false;
    bool cleared_partner_stagger = false;

    if (move->target_rule == N64GAME_TARGET_ALL_ENEMIES) {
        mark_move_used(battle, action, move);
        const bool target_side = !battle->actors[action->actor].player_side;
        if (move->effect == N64GAME_EFFECT_POWER_DOWN) {
            for (uint8_t target = 0U; target < N64GAME_BATTLE_ACTOR_COUNT; ++target) {
                N64GameBattleActor *const recipient = &battle->actors[target];
                if (recipient->player_side == target_side && alive(recipient) &&
                    adjust_stage(
                        &recipient->power_stage,
                        &recipient->power_stage_expires_round,
                        -1,
                        move->stage_rounds,
                        battle->round
                    )) {
                    any_success = true;
                }
            }
            battle->last_event = (N64GameBattleEvent){
                .happened = true,
                .skipped = !any_success,
                .actor = action->actor,
                .move = action->move,
                .target = N64GAME_TARGET_ALL,
            };
        } else {
            for (uint8_t target = 0U; target < N64GAME_BATTLE_ACTOR_COUNT; ++target) {
                N64GameBattleActor *const recipient = &battle->actors[target];
                if (recipient->player_side != target_side || !alive(recipient)) {
                    continue;
                }
                (void)apply_damage(battle, action->actor, target, move, empowered);
                any_success = true;
                any_advantage = any_advantage || battle->last_event.affinity_advantage;
                if (move->effect == N64GAME_EFFECT_DAMAGE_GROUND &&
                    recipient->power_stage > 0) {
                    --recipient->power_stage;
                    if (recipient->power_stage == 0) {
                        recipient->power_stage_expires_round = 0U;
                    }
                } else if (move->effect == N64GAME_EFFECT_DAMAGE_STAGGER_CHANCE &&
                           recipient->hp > 0 &&
                           effect_roll(battle, move->effect_chance_percent)) {
                    recipient->stagger_rounds = 1U;
                }
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
        resolved_target = target;
        mark_move_used(battle, action, move);
        N64GameBattleActor *const recipient = &battle->actors[target];
        if (is_damage) {
            (void)apply_damage(battle, action->actor, target, move, empowered);
            any_success = true;
            any_advantage = battle->last_event.affinity_advantage;
            if (move->effect == N64GAME_EFFECT_DAMAGE_STAGGER && recipient->hp > 0) {
                recipient->stagger_rounds = 1U;
            }
        } else if (move->effect == N64GAME_EFFECT_GUARD_UP) {
            any_success = adjust_stage(
                &recipient->guard_stage,
                &recipient->guard_stage_expires_round,
                1,
                move->stage_rounds,
                battle->round
            );
        } else if (move->effect == N64GAME_EFFECT_SPEED_UP) {
            any_success = adjust_stage(
                &recipient->speed_stage,
                &recipient->speed_stage_expires_round,
                1,
                move->stage_rounds,
                battle->round
            );
        } else if (move->effect == N64GAME_EFFECT_EMPOWER_NEXT_DAMAGE) {
            any_success = !recipient->empowered_damage ||
                (!recipient->empowered_by_partner && target != action->actor);
            recipient->empowered_damage = true;
            recipient->empowered_by_partner = target != action->actor;
        } else if (move->effect == N64GAME_EFFECT_GUARD_DOWN) {
            any_success = adjust_stage(
                &recipient->guard_stage,
                &recipient->guard_stage_expires_round,
                -1,
                move->stage_rounds,
                battle->round
            );
        } else if (move->effect == N64GAME_EFFECT_HEAL_CLEAR_STAGGER) {
            int16_t healing = move->power;
            const int16_t missing = (int16_t)(recipient->max_hp - recipient->hp);
            if (healing > missing) {
                healing = missing;
            }
            recipient->hp = (int16_t)(recipient->hp + healing);
            const bool cleared_stagger = recipient->stagger_rounds > 0U;
            recipient->stagger_rounds = 0U;
            cleared_partner_stagger = cleared_stagger && target != action->actor;
            any_success = healing > 0 || cleared_stagger;
            battle->last_event.hp_delta = healing;
        }
        if (user->player_side && target != action->actor &&
            ((any_success &&
              (move->effect == N64GAME_EFFECT_GUARD_UP ||
               move->effect == N64GAME_EFFECT_SPEED_UP ||
               move->effect == N64GAME_EFFECT_EMPOWER_NEXT_DAMAGE)) ||
             cleared_partner_stagger)) {
            recipient->partner_setup_round = battle->round;
        }
        if (!is_damage) {
            battle->last_event = (N64GameBattleEvent){
                .happened = true,
                .skipped = !any_success,
                .actor = action->actor,
                .move = action->move,
                .target = target,
                .hp_delta = battle->last_event.hp_delta,
            };
        }
    }

    if (user->player_side && any_success) {
        if (is_damage) {
            add_resonance(battle, move->resonance_gain);
            if (any_advantage) {
                add_resonance(battle, 4U);
            }
            if (user->partner_setup_round == battle->round &&
                battle->linked_followthrough_round != battle->round) {
                add_resonance(battle, 12U);
                battle->linked_followthrough_round = battle->round;
            }
        } else if (resolved_target != action->actor) {
            add_resonance(battle, move->resonance_gain);
        }
        if (cleared_partner_stagger) {
            add_resonance(battle, 8U);
        }
    }
    if (is_damage && any_success && empowered) {
        user->empowered_damage = false;
        user->empowered_by_partner = false;
    }
    if (is_damage && any_success) {
        user->partner_setup_round = 0U;
    }
    if (user_was_staggered) {
        user->stagger_rounds = 0U;
    }
    if (battle->queue_cursor < battle->queue_count) {
        sort_queue_from(battle, battle->queue_cursor);
    }
}

static void clear_expired_stages(N64GameBattleActor *actor, uint8_t round)
{
    if (actor->partner_setup_round != 0U && actor->partner_setup_round != round) {
        actor->partner_setup_round = 0U;
    }
    if (actor->power_stage_expires_round != 0U &&
        round >= actor->power_stage_expires_round) {
        actor->power_stage = 0;
        actor->power_stage_expires_round = 0U;
    }
    if (actor->guard_stage_expires_round != 0U &&
        round >= actor->guard_stage_expires_round) {
        actor->guard_stage = 0;
        actor->guard_stage_expires_round = 0U;
    }
    if (actor->speed_stage_expires_round != 0U &&
        round >= actor->speed_stage_expires_round) {
        actor->speed_stage = 0;
        actor->speed_stage_expires_round = 0U;
    }
}

bool n64game_battle_resolve_next(N64GameBattle *battle)
{
    if (battle == NULL || battle->phase != N64GAME_BATTLE_PRESENT ||
        battle->queue_cursor >= battle->queue_count) {
        return false;
    }
    apply_action(battle, &battle->queue[battle->queue_cursor++]);
    if (battle->phase == N64GAME_BATTLE_COMMAND) {
        return true;
    }
    if (side_defeated(battle, false)) {
        battle->phase = N64GAME_BATTLE_VICTORY;
        return true;
    }
    if (side_defeated(battle, true)) {
        battle->phase = N64GAME_BATTLE_DEFEAT;
        return true;
    }
    if (battle->queue_cursor == battle->queue_count) {
        ++battle->round;
        for (size_t index = 0U; index < N64GAME_BATTLE_ACTOR_COUNT; ++index) {
            clear_expired_stages(&battle->actors[index], battle->round);
        }
        battle->command_actor = first_living_target(battle, true);
        battle->queue_count = 0U;
        battle->queue_cursor = 0U;
        battle->player_actions[0] = (N64GameBattleAction){0};
        battle->player_actions[1] = (N64GameBattleAction){0};
        battle->phase = N64GAME_BATTLE_COMMAND;
    }
    return true;
}
