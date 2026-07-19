// SPDX-License-Identifier: MIT
// Native N64 entry point for the Meridian Annex vertical slice.

#include <assert.h>
#include <stdbool.h>
#include <limits.h>
#include <stdint.h>

#include <libdragon.h>

#include "n64game_core.h"
#include "n64game_render.h"
#include "n64game_save.h"

typedef enum {
    SAVE_WRITE_IDLE = 0,
    SAVE_WRITE_INVALIDATING,
    SAVE_WRITE_BODY,
    SAVE_WRITE_FOOTER,
} SaveWritePhase;

enum {
    SAVE_SETTLE_FRAMES = 2,
};

typedef struct {
    SaveWritePhase phase;
    uint8_t target_slot;
    uint32_t sequence;
    uint8_t bytes[N64GAME_SAVE_BYTES];
    N64GameCore pending_game;
    uint8_t settle_frames;
    bool faulted;
    bool pending;
} SaveWriter;

static N64GameInput read_game_input(void)
{
    const joypad_buttons_t buttons = joypad_get_buttons_pressed(JOYPAD_PORT_1);
    const joypad_inputs_t inputs = joypad_get_inputs(JOYPAD_PORT_1);
    uint16_t pressed = 0U;
    uint16_t held = 0U;
    if (buttons.d_up) {
        pressed |= N64GAME_INPUT_UP;
    }
    if (buttons.d_down) {
        pressed |= N64GAME_INPUT_DOWN;
    }
    if (buttons.d_left) {
        pressed |= N64GAME_INPUT_LEFT;
    }
    if (buttons.d_right) {
        pressed |= N64GAME_INPUT_RIGHT;
    }
    if (buttons.a) {
        pressed |= N64GAME_INPUT_CONFIRM;
    }
    if (buttons.b) {
        pressed |= N64GAME_INPUT_CANCEL;
    }
    if (buttons.start) {
        pressed |= N64GAME_INPUT_START;
    }
    if (buttons.z) {
        pressed |= N64GAME_INPUT_PAUSE;
    }
    if (buttons.c_down) {
        pressed |= N64GAME_INPUT_RELAY;
    }
    if (inputs.btn.a) {
        held |= N64GAME_INPUT_CONFIRM;
    }
    if (inputs.btn.b) {
        held |= N64GAME_INPUT_CANCEL;
    }
    if (inputs.btn.start) {
        held |= N64GAME_INPUT_START;
    }
    if (inputs.btn.z) {
        held |= N64GAME_INPUT_PAUSE;
    }
    if (inputs.btn.c_down) {
        held |= N64GAME_INPUT_RELAY;
    }
    int8_t stick_x = inputs.stick_x;
    int8_t stick_y = inputs.stick_y;
    if (inputs.btn.d_left) {
        stick_x = -INT8_MAX;
    } else if (inputs.btn.d_right) {
        stick_x = INT8_MAX;
    }
    if (inputs.btn.d_up) {
        stick_y = INT8_MAX;
    } else if (inputs.btn.d_down) {
        stick_y = -INT8_MAX;
    }
    return (N64GameInput){
        .pressed = pressed,
        .held = held,
        .stick_x = stick_x,
        .stick_y = stick_y,
    };
}

static bool input_pressed(N64GameInput input, N64GameInputButton button)
{
    return (input.pressed & (uint16_t)button) != 0U;
}

static size_t save_slot_offset(uint8_t slot)
{
    return (size_t)slot * N64GAME_SAVE_BYTES;
}

static bool save_writer_begin(
    SaveWriter *writer,
    const N64GameCore *game,
    uint32_t current_sequence,
    bool active_slot_valid,
    uint8_t active_slot
)
{
    if (writer->phase != SAVE_WRITE_IDLE || writer->faulted) {
        return false;
    }
    writer->sequence = current_sequence + 1U;
    writer->target_slot = active_slot_valid ? (uint8_t)(active_slot ^ UINT8_C(1)) : 0U;
    if (!n64game_save_encode(game, writer->sequence, writer->bytes)) {
        return false;
    }
    uint8_t invalid_footer[N64GAME_SAVE_FOOTER_BYTES];
    for (size_t index = 0U; index < N64GAME_SAVE_FOOTER_BYTES; ++index) {
        invalid_footer[index] = (uint8_t)(
            writer->bytes[N64GAME_SAVE_BODY_BYTES + index] ^ UINT8_C(0xFF)
        );
    }
    eeprom_write_bytes(
        invalid_footer,
        save_slot_offset(writer->target_slot) + N64GAME_SAVE_BODY_BYTES,
        sizeof(invalid_footer)
    );
    writer->phase = SAVE_WRITE_INVALIDATING;
    writer->settle_frames = 0U;
    return true;
}

static bool save_writer_queue(SaveWriter *writer, const N64GameCore *game)
{
    if (writer->faulted) {
        return false;
    }
    uint8_t validation_bytes[N64GAME_SAVE_BYTES];
    if (!n64game_save_encode(game, 0U, validation_bytes)) {
        return false;
    }
    /* Coalesce to the newest request-time snapshot while a write is active. */
    writer->pending_game = *game;
    writer->pending_game.save_requested = false;
    writer->pending = true;
    return true;
}

static bool save_writer_pump(
    SaveWriter *writer,
    N64GameCore *continue_game,
    uint32_t *save_sequence,
    uint8_t *active_slot
)
{
    if (writer->phase == SAVE_WRITE_IDLE) {
        return false;
    }
    if (eeprom_is_busy()) {
        writer->settle_frames = 0U;
        return false;
    }
    if (++writer->settle_frames < SAVE_SETTLE_FRAMES) {
        return false;
    }
    writer->settle_frames = 0U;
    const size_t offset = save_slot_offset(writer->target_slot);
    if (writer->phase == SAVE_WRITE_INVALIDATING) {
        eeprom_write_bytes(writer->bytes, offset, N64GAME_SAVE_BODY_BYTES);
        writer->phase = SAVE_WRITE_BODY;
        return false;
    }
    if (writer->phase == SAVE_WRITE_BODY) {
        eeprom_write_bytes(
            writer->bytes + N64GAME_SAVE_BODY_BYTES,
            offset + N64GAME_SAVE_BODY_BYTES,
            N64GAME_SAVE_FOOTER_BYTES
        );
        writer->phase = SAVE_WRITE_FOOTER;
        return false;
    }

    uint8_t verified_bytes[N64GAME_SAVE_BYTES];
    N64GameCore verified_game;
    uint32_t verified_sequence = 0U;
    eeprom_read_bytes(verified_bytes, offset, sizeof(verified_bytes));
    if (!n64game_save_decode(verified_bytes, &verified_game, &verified_sequence) ||
        verified_sequence != writer->sequence) {
        writer->faulted = true;
        writer->phase = SAVE_WRITE_IDLE;
        return false;
    }
    *continue_game = verified_game;
    *save_sequence = writer->sequence;
    *active_slot = writer->target_slot;
    writer->phase = SAVE_WRITE_IDLE;
    return true;
}

int main(void)
{
    debug_init_emulog();
    debug_init_usblog();
    assertf(
        dfs_init(DFS_DEFAULT_LOCATION) == DFS_ESUCCESS,
        "N64GAME ROM filesystem initialization failed"
    );
    display_init(
        RESOLUTION_320x240,
        DEPTH_16_BPP,
        3,
        GAMMA_NONE,
        FILTERS_RESAMPLE_ANTIALIAS_DEDITHER
    );
    display_set_fps_limit(30.0f);
    rdpq_init();
    joypad_init();
    t3d_init((T3DInitParams){});

    N64GameRenderer renderer;
    assertf(n64game_renderer_init(&renderer), "N64GAME renderer allocation failed");

    N64GameCore game;
    N64GameCore continue_game;
    n64game_core_init(&game);
    n64game_core_init(&continue_game);

    const eeprom_type_t save_type = eeprom_present();
    const bool save_available = save_type != EEPROM_NONE;
    uint32_t save_sequence = 0U;
    uint8_t active_save_slot = 0U;
    bool continue_available = false;
    if (save_available) {
        uint8_t stored_slots[N64GAME_SAVE_SLOT_COUNT][N64GAME_SAVE_BYTES];
        eeprom_read_bytes(stored_slots, 0U, sizeof(stored_slots));
        continue_available = n64game_save_select_latest(
            stored_slots, &continue_game, &save_sequence, &active_save_slot
        );
    }
    SaveWriter save_writer = {0};
    bool controller_was_connected = false;

    for (;;) {
        joypad_poll();
        const bool controller_connected = joypad_is_connected(JOYPAD_PORT_1);
        const bool clear_edge_frame = controller_connected && !controller_was_connected;
        controller_was_connected = controller_connected;
        const N64GameInput input = controller_connected ?
            read_game_input() : (N64GameInput){0};
        const bool resume_now = game.scene == N64GAME_SCENE_OPENING_SLATE &&
            controller_connected && !clear_edge_frame && continue_available &&
            input_pressed(input, N64GAME_INPUT_START);
        if (resume_now) {
            game = continue_game;
        } else {
            n64game_core_update_controller(
                &game, input, controller_connected, clear_edge_frame
            );
        }

        if (save_available && !save_writer.faulted) {
            if (save_writer_pump(
                    &save_writer, &continue_game, &save_sequence, &active_save_slot)) {
                continue_available = true;
            }
            if (save_writer.phase == SAVE_WRITE_IDLE && save_writer.pending) {
                const N64GameCore pending_game = save_writer.pending_game;
                save_writer.pending = false;
                (void)save_writer_begin(
                    &save_writer, &pending_game, save_sequence,
                    continue_available, active_save_slot
                );
            }
            if (game.save_requested) {
                bool accepted = false;
                if (save_writer.phase == SAVE_WRITE_IDLE && !save_writer.pending) {
                    accepted = save_writer_begin(
                        &save_writer, &game, save_sequence,
                        continue_available, active_save_slot
                    );
                } else {
                    accepted = save_writer_queue(&save_writer, &game);
                }
                if (accepted) {
                    game.save_requested = false;
                }
            }
        }

        const bool save_busy = save_writer.phase != SAVE_WRITE_IDLE ||
            save_writer.pending || eeprom_is_busy();
        const bool save_usable = save_available && !save_writer.faulted;
        n64game_renderer_draw(
            &renderer,
            &game,
            save_busy,
            save_usable,
            continue_available,
            controller_connected
        );
    }
}
