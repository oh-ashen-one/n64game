#ifndef N64GAME_CORE_H
#define N64GAME_CORE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "n64game_annex.h"

#define N64GAME_NAME_CAPACITY 8
#define N64GAME_BATTLE_ACTOR_COUNT 4
#define N64GAME_BATTLE_MOVE_COUNT 4
#define N64GAME_BATTLE_QUEUE_CAPACITY 4
#define N64GAME_RESONANCE_MAX 100
#define N64GAME_QUARRUNE_MAX_HP 92
#define N64GAME_AYSELOR_MAX_HP 78
#define N64GAME_BATTLE_STAGE_MIN (-2)
#define N64GAME_BATTLE_STAGE_MAX 2
#define N64GAME_TARGET_ALL UINT8_C(0xFF)
#define N64GAME_MOVE_FINISHER UINT8_C(4)
#define N64GAME_CALIBRATION_STEP_COUNT UINT8_C(3)

typedef enum {
    N64GAME_SCENE_BOOT = 0,
    N64GAME_SCENE_OPENING_SLATE,
    N64GAME_SCENE_NAME_ENTRY,
    N64GAME_SCENE_ANNEX,
    N64GAME_SCENE_BATTLE,
    N64GAME_SCENE_END_CHAPTER,
} N64GameScene;

typedef enum {
    N64GAME_QUEST_MEET_SERA = 0,
    N64GAME_QUEST_MEET_TAVI,
    N64GAME_QUEST_RETRIEVE_RELAY,
    N64GAME_QUEST_CALIBRATE_RELAY,
    N64GAME_QUEST_READY_FOR_TRIAL,
    N64GAME_QUEST_RESONANCE_TRIAL,
    N64GAME_QUEST_BEACON_OVERLOOK,
    N64GAME_QUEST_COMPLETE,
} N64GameQuest;

typedef enum {
    N64GAME_DIALOGUE_NONE = 0,
    N64GAME_DIALOGUE_SERA_INTRO,
    N64GAME_DIALOGUE_TAVI_INTRO,
    N64GAME_DIALOGUE_TAVI_REPEAT,
    N64GAME_DIALOGUE_RELAY,
    N64GAME_DIALOGUE_SERA_TRIAL,
    N64GAME_DIALOGUE_BATTLE_VICTORY,
    N64GAME_DIALOGUE_BEACON_HOOK,
    N64GAME_DIALOGUE_EXAMINE_SIM_RING,
    N64GAME_DIALOGUE_EXAMINE_ATRIUM_MAP,
    N64GAME_DIALOGUE_EXAMINE_WORKSHOP_LOG,
    N64GAME_DIALOGUE_EXAMINE_OVERLOOK_SCOPE,
} N64GameDialogue;

typedef enum {
    N64GAME_INPUT_UP = UINT16_C(1) << 0,
    N64GAME_INPUT_DOWN = UINT16_C(1) << 1,
    N64GAME_INPUT_LEFT = UINT16_C(1) << 2,
    N64GAME_INPUT_RIGHT = UINT16_C(1) << 3,
    N64GAME_INPUT_CONFIRM = UINT16_C(1) << 4,
    N64GAME_INPUT_CANCEL = UINT16_C(1) << 5,
    N64GAME_INPUT_START = UINT16_C(1) << 6,
    N64GAME_INPUT_PAUSE = UINT16_C(1) << 7,
    N64GAME_INPUT_RELAY = UINT16_C(1) << 8,
} N64GameInputButton;

typedef struct {
    uint16_t pressed;
    uint16_t held;
    int8_t stick_x;
    int8_t stick_y;
} N64GameInput;

typedef enum {
    N64GAME_MENU_CLOSED = 0,
    N64GAME_MENU_PAUSE_ROOT,
    N64GAME_MENU_FIELD_RELAY_ROOT,
    N64GAME_MENU_PARTY,
    N64GAME_MENU_MESSAGES,
    N64GAME_MENU_RESONANCE,
    N64GAME_MENU_SAVE,
    N64GAME_MENU_HELP,
    N64GAME_MENU_RELAY_CALIBRATION,
    N64GAME_MENU_POST_CHAPTER_ROOT,
} N64GameMenu;

typedef enum {
    N64GAME_FINAL_SAVE_NONE = 0,
    N64GAME_FINAL_SAVE_PENDING,
    N64GAME_FINAL_SAVE_FAILED,
    N64GAME_FINAL_SAVE_CONFIRM_UNSAVED,
    N64GAME_FINAL_SAVE_VERIFIED,
    N64GAME_FINAL_SAVE_ACCEPTED_UNSAVED,
} N64GameFinalSaveState;

typedef enum {
    N64GAME_RELAY_PAGE_PARTY = UINT8_C(1) << 0,
    N64GAME_RELAY_PAGE_MESSAGES = UINT8_C(1) << 1,
    N64GAME_RELAY_PAGE_RESONANCE = UINT8_C(1) << 2,
    N64GAME_RELAY_PAGE_SAVE = UINT8_C(1) << 3,
} N64GameRelayPageFlag;

typedef enum {
    N64GAME_SETTING_INVERT_X = UINT8_C(1) << 0,
    N64GAME_SETTING_INVERT_Y = UINT8_C(1) << 1,
    N64GAME_SETTING_RUMBLE = UINT8_C(1) << 2,
} N64GameSettingFlag;

typedef enum {
    N64GAME_ECHO_QUARRUNE = 0,
    N64GAME_ECHO_AYSELOR,
    N64GAME_ECHO_GYRECLAST,
    N64GAME_ECHO_KIVARRAX,
} N64GameEchoform;

typedef enum {
    N64GAME_AFFINITY_STRATA = 0,
    N64GAME_AFFINITY_GALE,
    N64GAME_AFFINITY_CURRENT,
    N64GAME_AFFINITY_EMBER,
} N64GameAffinity;

typedef enum {
    N64GAME_TARGET_ONE_ENEMY = 0,
    N64GAME_TARGET_ALL_ENEMIES,
    N64GAME_TARGET_ONE_ALLY,
    N64GAME_TARGET_SELF,
} N64GameTargetRule;

typedef enum {
    N64GAME_EFFECT_DAMAGE = 0,
    N64GAME_EFFECT_DAMAGE_STAGGER_CHANCE,
    N64GAME_EFFECT_DAMAGE_STAGGER,
    N64GAME_EFFECT_DAMAGE_GROUND,
    N64GAME_EFFECT_GUARD_UP,
    N64GAME_EFFECT_SPEED_UP,
    N64GAME_EFFECT_EMPOWER_NEXT_DAMAGE,
    N64GAME_EFFECT_HEAL_CLEAR_STAGGER,
    N64GAME_EFFECT_POWER_DOWN,
    N64GAME_EFFECT_GUARD_DOWN,
    N64GAME_EFFECT_FINISHER,
} N64GameMoveEffect;

typedef struct {
    const char *name;
    N64GameAffinity affinity;
    N64GameTargetRule target_rule;
    N64GameMoveEffect effect;
    uint8_t power;
    uint8_t resonance_gain;
    int8_t priority;
    uint8_t effect_chance_percent;
    uint8_t stage_rounds;
    uint8_t cooldown_rounds;
    bool once_per_encounter;
} N64GameMoveDef;

typedef struct {
    N64GameEchoform id;
    N64GameAffinity affinity;
    int16_t hp;
    int16_t max_hp;
    int16_t power;
    int16_t guard;
    int16_t speed;
    int8_t power_stage;
    int8_t guard_stage;
    int8_t speed_stage;
    uint8_t power_stage_expires_round;
    uint8_t guard_stage_expires_round;
    uint8_t speed_stage_expires_round;
    uint8_t stagger_rounds;
    uint8_t used_move_mask;
    uint8_t move_ready_round[N64GAME_BATTLE_MOVE_COUNT];
    uint8_t partner_setup_round;
    bool player_side;
    bool empowered_damage;
    bool empowered_by_partner;
} N64GameBattleActor;

typedef struct {
    uint8_t actor;
    uint8_t move;
    uint8_t target;
    int8_t priority;
    bool valid;
} N64GameBattleAction;

typedef enum {
    N64GAME_BATTLE_INACTIVE = 0,
    N64GAME_BATTLE_INTRO,
    N64GAME_BATTLE_COMMAND,
    N64GAME_BATTLE_PRESENT,
    N64GAME_BATTLE_VICTORY,
    N64GAME_BATTLE_DEFEAT,
} N64GameBattlePhase;

typedef struct {
    bool happened;
    bool skipped;
    uint8_t actor;
    uint8_t move;
    uint8_t target;
    int16_t hp_delta;
    bool affinity_advantage;
    bool knockout;
} N64GameBattleEvent;

typedef struct {
    N64GameBattlePhase phase;
    N64GameBattleActor actors[N64GAME_BATTLE_ACTOR_COUNT];
    N64GameBattleAction player_actions[2];
    N64GameBattleAction queue[N64GAME_BATTLE_QUEUE_CAPACITY];
    N64GameBattleEvent last_event;
    uint8_t command_actor;
    uint8_t queue_count;
    uint8_t queue_cursor;
    uint8_t round;
    uint8_t resonance;
    uint8_t linked_followthrough_round;
    uint32_t random_state;
    uint32_t event_serial;
    bool reward_applied;
} N64GameBattle;

typedef struct {
    N64GameScene scene;
    N64GameQuest quest;
    N64GameDialogue dialogue;
    N64GameBattle battle;
    uint32_t scene_ticks;
    uint32_t play_ticks;
    uint32_t active_control_ticks;
    int32_t player_x_q8;
    int32_t player_z_q8;
    int32_t player_velocity_x_q8;
    int32_t player_velocity_z_q8;
    int16_t party_hp[2];
    N64GameAnnexSector annex_sector;
    N64GameMenu menu;
    N64GameMenu menu_parent;
    uint8_t name_cursor;
    uint8_t name_length;
    uint8_t dialogue_page;
    uint8_t battle_move_cursor;
    uint8_t battle_target_cursor;
    uint8_t battle_present_delay;
    uint8_t menu_cursor;
    uint8_t examine_flags;
    uint8_t relay_pages_seen;
    uint8_t settings_flags;
    uint8_t prebattle_resonance;
    uint8_t calibration_step;
    uint8_t calibration_cursor;
    char player_name[N64GAME_NAME_CAPACITY + 1];
    bool opening_cinematic_seen;
    bool relay_acquired;
    bool relay_unlocked;
    bool battle_won;
    bool battle_reward_claimed;
    bool slice_complete;
    bool paused;
    bool battle_selecting_target;
    bool save_requested;
    bool manual_save_latched;
    bool calibration_error;
    N64GameFinalSaveState final_save_state;
} N64GameCore;

void n64game_core_init(N64GameCore *game);
void n64game_core_update(N64GameCore *game, N64GameInput input);
void n64game_core_update_controller(
    N64GameCore *game,
    N64GameInput input,
    bool controller_connected,
    bool clear_edge_frame
);
void n64game_core_set_player_position(N64GameCore *game, int32_t x_q8, int32_t z_q8);
bool n64game_core_can_interact(const N64GameCore *game);
const char *n64game_core_interaction_label(const N64GameCore *game);
uint8_t n64game_dialogue_page_count(N64GameDialogue dialogue);
uint8_t n64game_core_calibration_target(uint8_t step);
void n64game_core_set_final_save_result(N64GameCore *game, bool verified);

const N64GameMoveDef *n64game_move_def(N64GameEchoform actor, uint8_t move);
void n64game_battle_begin(N64GameBattle *battle);
bool n64game_battle_commit_action(
    N64GameBattle *battle,
    uint8_t actor,
    uint8_t move,
    uint8_t target
);
bool n64game_battle_commit_finisher(N64GameBattle *battle);
bool n64game_battle_resolve_next(N64GameBattle *battle);
bool n64game_battle_target_legal(
    const N64GameBattle *battle,
    uint8_t actor,
    uint8_t move,
    uint8_t target
);

#endif
