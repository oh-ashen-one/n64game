#ifndef N64GAME_SAVE_H
#define N64GAME_SAVE_H

#include "n64game_core.h"

#define N64GAME_SAVE_BYTES 64
#define N64GAME_SAVE_BODY_BYTES 60
#define N64GAME_SAVE_FOOTER_BYTES 4
#define N64GAME_SAVE_SLOT_COUNT 2
#define N64GAME_SAVE_VERSION UINT16_C(2)

uint32_t n64game_save_checksum(const uint8_t bytes[N64GAME_SAVE_BYTES]);
bool n64game_save_encode(
    const N64GameCore *game,
    uint32_t sequence,
    uint8_t bytes[N64GAME_SAVE_BYTES]
);
bool n64game_save_decode(
    const uint8_t bytes[N64GAME_SAVE_BYTES],
    N64GameCore *game_out,
    uint32_t *sequence_out
);
bool n64game_save_select_latest(
    const uint8_t slots[N64GAME_SAVE_SLOT_COUNT][N64GAME_SAVE_BYTES],
    N64GameCore *game_out,
    uint32_t *sequence_out,
    uint8_t *slot_out
);

#endif
