#include "n64game_save.h"

#include <string.h>

enum {
    OFFSET_MAGIC = 0,
    OFFSET_VERSION = 4,
    OFFSET_SIZE = 6,
    OFFSET_SEQUENCE = 8,
    OFFSET_NAME_LENGTH = 12,
    OFFSET_NAME = 13,
    OFFSET_SCENE = 21,
    OFFSET_QUEST = 22,
    OFFSET_FLAGS = 23,
    OFFSET_PLAYER_HP = 24,
    OFFSET_RESONANCE = 28,
    OFFSET_CHECKSUM = 60,
};

enum {
    SAVE_FLAG_OPENING = UINT8_C(1) << 0,
    SAVE_FLAG_RELAY = UINT8_C(1) << 1,
    SAVE_FLAG_BATTLE = UINT8_C(1) << 2,
    SAVE_FLAG_REWARD = UINT8_C(1) << 3,
    SAVE_FLAG_COMPLETE = UINT8_C(1) << 4,
};

static void put_u16(uint8_t *bytes, size_t offset, uint16_t value)
{
    bytes[offset] = (uint8_t)(value >> 8);
    bytes[offset + 1U] = (uint8_t)value;
}

static uint16_t get_u16(const uint8_t *bytes, size_t offset)
{
    return (uint16_t)((uint16_t)bytes[offset] << 8) | bytes[offset + 1U];
}

static void put_u32(uint8_t *bytes, size_t offset, uint32_t value)
{
    bytes[offset] = (uint8_t)(value >> 24);
    bytes[offset + 1U] = (uint8_t)(value >> 16);
    bytes[offset + 2U] = (uint8_t)(value >> 8);
    bytes[offset + 3U] = (uint8_t)value;
}

static uint32_t get_u32(const uint8_t *bytes, size_t offset)
{
    return (uint32_t)bytes[offset] << 24 |
        (uint32_t)bytes[offset + 1U] << 16 |
        (uint32_t)bytes[offset + 2U] << 8 |
        bytes[offset + 3U];
}

uint32_t n64game_save_checksum(const uint8_t bytes[N64GAME_SAVE_BYTES])
{
    uint32_t checksum = UINT32_C(2166136261);
    for (size_t index = 0U; index < OFFSET_CHECKSUM; ++index) {
        checksum ^= bytes[index];
        checksum *= UINT32_C(16777619);
    }
    return checksum;
}

static bool valid_name(const N64GameCore *game)
{
    if (game->name_length == 0U || game->name_length > N64GAME_NAME_CAPACITY ||
        game->player_name[game->name_length] != '\0') {
        return false;
    }
    for (uint8_t index = 0U; index < game->name_length; ++index) {
        if (game->player_name[index] < 'A' || game->player_name[index] > 'Z') {
            return false;
        }
    }
    return true;
}

static bool valid_progress(const N64GameCore *game)
{
    if (!game->opening_cinematic_seen || !valid_name(game) ||
        game->party_hp[0] < 0 || game->party_hp[0] > N64GAME_QUARRUNE_MAX_HP ||
        game->party_hp[1] < 0 || game->party_hp[1] > N64GAME_AYSELOR_MAX_HP ||
        game->battle.resonance > N64GAME_RESONANCE_MAX) {
        return false;
    }

    const bool relay_checkpoint =
        game->scene == N64GAME_SCENE_ANNEX &&
        game->quest == N64GAME_QUEST_RETURN_TO_SERA &&
        game->relay_unlocked &&
        !game->battle_won &&
        !game->battle_reward_claimed &&
        !game->slice_complete;
    const bool victory_checkpoint =
        game->scene == N64GAME_SCENE_ANNEX &&
        game->quest == N64GAME_QUEST_BEACON_OVERLOOK &&
        game->relay_unlocked &&
        game->battle_won &&
        game->battle_reward_claimed &&
        !game->slice_complete;
    const bool complete_checkpoint =
        game->scene == N64GAME_SCENE_END_CHAPTER &&
        game->quest == N64GAME_QUEST_COMPLETE &&
        game->relay_unlocked &&
        game->battle_won &&
        game->battle_reward_claimed &&
        game->slice_complete;
    return relay_checkpoint || victory_checkpoint || complete_checkpoint;
}

bool n64game_save_encode(
    const N64GameCore *game,
    uint32_t sequence,
    uint8_t bytes[N64GAME_SAVE_BYTES]
)
{
    if (game == NULL || bytes == NULL || !valid_progress(game)) {
        return false;
    }
    memset(bytes, 0, N64GAME_SAVE_BYTES);
    memcpy(bytes + OFFSET_MAGIC, "N64G", 4U);
    put_u16(bytes, OFFSET_VERSION, N64GAME_SAVE_VERSION);
    put_u16(bytes, OFFSET_SIZE, N64GAME_SAVE_BYTES);
    put_u32(bytes, OFFSET_SEQUENCE, sequence);
    bytes[OFFSET_NAME_LENGTH] = game->name_length;
    memcpy(bytes + OFFSET_NAME, game->player_name, game->name_length);
    bytes[OFFSET_SCENE] = (uint8_t)game->scene;
    bytes[OFFSET_QUEST] = (uint8_t)game->quest;
    bytes[OFFSET_FLAGS] =
        (game->opening_cinematic_seen ? SAVE_FLAG_OPENING : 0U) |
        (game->relay_unlocked ? SAVE_FLAG_RELAY : 0U) |
        (game->battle_won ? SAVE_FLAG_BATTLE : 0U) |
        (game->battle_reward_claimed ? SAVE_FLAG_REWARD : 0U) |
        (game->slice_complete ? SAVE_FLAG_COMPLETE : 0U);
    put_u16(bytes, OFFSET_PLAYER_HP, (uint16_t)game->party_hp[0]);
    put_u16(bytes, OFFSET_PLAYER_HP + 2U, (uint16_t)game->party_hp[1]);
    bytes[OFFSET_RESONANCE] = game->battle.resonance;
    put_u32(bytes, OFFSET_CHECKSUM, n64game_save_checksum(bytes));
    return true;
}

bool n64game_save_decode(
    const uint8_t bytes[N64GAME_SAVE_BYTES],
    N64GameCore *game_out,
    uint32_t *sequence_out
)
{
    if (bytes == NULL || game_out == NULL || sequence_out == NULL ||
        memcmp(bytes + OFFSET_MAGIC, "N64G", 4U) != 0 ||
        get_u16(bytes, OFFSET_VERSION) != N64GAME_SAVE_VERSION ||
        get_u16(bytes, OFFSET_SIZE) != N64GAME_SAVE_BYTES ||
        get_u32(bytes, OFFSET_CHECKSUM) != n64game_save_checksum(bytes)) {
        return false;
    }
    const uint8_t name_length = bytes[OFFSET_NAME_LENGTH];
    if (name_length == 0U || name_length > N64GAME_NAME_CAPACITY ||
        bytes[OFFSET_SCENE] > N64GAME_SCENE_END_CHAPTER ||
        bytes[OFFSET_QUEST] > N64GAME_QUEST_COMPLETE ||
        bytes[OFFSET_RESONANCE] > N64GAME_RESONANCE_MAX) {
        return false;
    }
    for (size_t index = OFFSET_NAME + name_length; index < OFFSET_SCENE; ++index) {
        if (bytes[index] != 0U) {
            return false;
        }
    }
    for (size_t index = OFFSET_RESONANCE + 1U; index < OFFSET_CHECKSUM; ++index) {
        if (bytes[index] != 0U) {
            return false;
        }
    }
    N64GameCore decoded;
    n64game_core_init(&decoded);
    decoded.name_length = name_length;
    memcpy(decoded.player_name, bytes + OFFSET_NAME, name_length);
    decoded.player_name[name_length] = '\0';
    decoded.scene = (N64GameScene)bytes[OFFSET_SCENE];
    decoded.quest = (N64GameQuest)bytes[OFFSET_QUEST];
    const uint8_t flags = bytes[OFFSET_FLAGS];
    if ((flags & UINT8_C(0xE0)) != 0U) {
        return false;
    }
    decoded.opening_cinematic_seen = (flags & SAVE_FLAG_OPENING) != 0U;
    decoded.relay_unlocked = (flags & SAVE_FLAG_RELAY) != 0U;
    decoded.battle_won = (flags & SAVE_FLAG_BATTLE) != 0U;
    decoded.battle_reward_claimed = (flags & SAVE_FLAG_REWARD) != 0U;
    decoded.slice_complete = (flags & SAVE_FLAG_COMPLETE) != 0U;
    decoded.party_hp[0] = (int16_t)get_u16(bytes, OFFSET_PLAYER_HP);
    decoded.party_hp[1] = (int16_t)get_u16(bytes, OFFSET_PLAYER_HP + 2U);
    decoded.battle.resonance = bytes[OFFSET_RESONANCE];
    if (!valid_progress(&decoded)) {
        return false;
    }
    decoded.save_requested = false;
    *game_out = decoded;
    *sequence_out = get_u32(bytes, OFFSET_SEQUENCE);
    return true;
}

static bool sequence_is_newer(uint32_t candidate, uint32_t current)
{
    const uint32_t delta = candidate - current;
    return delta != 0U && delta < UINT32_C(0x80000000);
}

bool n64game_save_select_latest(
    const uint8_t slots[N64GAME_SAVE_SLOT_COUNT][N64GAME_SAVE_BYTES],
    N64GameCore *game_out,
    uint32_t *sequence_out,
    uint8_t *slot_out
)
{
    if (slots == NULL || game_out == NULL || sequence_out == NULL || slot_out == NULL) {
        return false;
    }
    N64GameCore candidates[N64GAME_SAVE_SLOT_COUNT];
    uint32_t sequences[N64GAME_SAVE_SLOT_COUNT] = {0U};
    const bool valid_first = n64game_save_decode(slots[0], &candidates[0], &sequences[0]);
    const bool valid_second = n64game_save_decode(slots[1], &candidates[1], &sequences[1]);
    if (!valid_first && !valid_second) {
        return false;
    }
    const uint8_t selected = valid_second &&
        (!valid_first || sequence_is_newer(sequences[1], sequences[0])) ? 1U : 0U;
    *game_out = candidates[selected];
    *sequence_out = sequences[selected];
    *slot_out = selected;
    return true;
}
