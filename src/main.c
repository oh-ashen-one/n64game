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
#include "n64game_telemetry.h"

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
    N64GameCore active_game;
    N64GameCore pending_game;
    uint8_t settle_frames;
    bool faulted;
    bool pending;
    bool writes_chapter_completion;
    bool chapter_completion_verified;
} SaveWriter;

static uint32_t telemetry_invalid_samples(const N64GameTelemetry *telemetry)
{
    return telemetry->invalid_frame_intervals + telemetry->invalid_scene_samples +
        telemetry->invalid_transitions + telemetry->invalid_heap_samples;
}

static void telemetry_emit_session(
    const N64GameTelemetry *telemetry,
    uint32_t *sequence,
    uint64_t boot_ticks,
    uint64_t ready_ticks
)
{
    debugf(
        "N64G_TELEM schema=1 seq=%lu event=session status=INSTRUMENTATION_ONLY "
        "ticks_per_second=%lu target_fps=30 budget_ticks=%lu tolerance_ticks=%lu "
        "boot_ticks=%llu ready_ticks=%llu heap_baseline_bytes=%ld\n",
        (unsigned long)(*sequence)++,
        (unsigned long)telemetry->ticks_per_second,
        (unsigned long)telemetry->frame_budget_ticks,
        (unsigned long)telemetry->frame_tolerance_ticks,
        (unsigned long long)boot_ticks,
        (unsigned long long)ready_ticks,
        (long)telemetry->heap_baseline_bytes
    );
}

static void telemetry_emit_transition(
    const N64GameTelemetry *telemetry,
    uint32_t *sequence,
    uint64_t wall_ticks,
    N64GameScene from,
    N64GameScene to,
    bool resumed,
    const N64GameCore *game,
    int32_t free_heap_bytes
)
{
    debugf(
        "N64G_TELEM schema=1 seq=%lu event=transition status=INSTRUMENTATION_ONLY "
        "wall_ticks=%llu cause=%s from=%u to=%u transition_count=%lu "
        "play_ticks=%lu active_control_ticks=%lu free_heap_bytes=%ld "
        "heap_low_water_bytes=%ld submitted_frames=%lu measured_intervals=%lu "
        "invalid_samples=%lu\n",
        (unsigned long)(*sequence)++,
        (unsigned long long)wall_ticks,
        resumed ? "continue_resume" : "core",
        (unsigned int)from,
        (unsigned int)to,
        (unsigned long)telemetry->transition_count,
        (unsigned long)game->play_ticks,
        (unsigned long)game->active_control_ticks,
        (long)free_heap_bytes,
        (long)telemetry->heap_low_water_bytes,
        (unsigned long)telemetry->total.submitted_frames,
        (unsigned long)telemetry->total.measured_intervals,
        (unsigned long)telemetry_invalid_samples(telemetry)
    );
}

static void telemetry_emit_scene_summary(
    const N64GameTelemetry *telemetry,
    uint32_t *sequence,
    uint64_t wall_ticks,
    N64GameScene scene
)
{
    const N64GameTelemetryFrameStats *const stats = &telemetry->scenes[(unsigned)scene];
    debugf(
        "N64G_TELEM schema=1 seq=%lu event=scene_summary "
        "status=INSTRUMENTATION_ONLY wall_ticks=%llu scene=%u "
        "submitted_frames=%lu measured_intervals=%lu over_budget_frames=%lu "
        "missed_deadlines=%lu max_frame_ticks=%lu max_over_budget_streak=%lu "
        "invalid_samples=%lu\n",
        (unsigned long)(*sequence)++,
        (unsigned long long)wall_ticks,
        (unsigned int)scene,
        (unsigned long)stats->submitted_frames,
        (unsigned long)stats->measured_intervals,
        (unsigned long)stats->over_budget_frames,
        (unsigned long)stats->missed_deadlines,
        (unsigned long)stats->max_frame_ticks,
        (unsigned long)stats->max_over_budget_streak,
        (unsigned long)telemetry_invalid_samples(telemetry)
    );
}

static void telemetry_emit_save_load(
    uint32_t *sequence,
    uint64_t wall_ticks,
    bool save_available,
    uint8_t valid_slot_mask,
    bool continue_available,
    uint8_t active_slot,
    uint32_t save_sequence,
    const N64GameCore *continue_game
)
{
    if (continue_available) {
        debugf(
            "N64G_TELEM schema=1 seq=%lu event=save_load "
            "status=INSTRUMENTATION_ONLY wall_ticks=%llu eeprom_present=1 "
            "valid_slot_mask=%u outcome=selected selected_slot=%u save_sequence=%lu "
            "checkpoint_scene=%u checkpoint_quest=%u\n",
            (unsigned long)(*sequence)++,
            (unsigned long long)wall_ticks,
            (unsigned int)valid_slot_mask,
            (unsigned int)active_slot,
            (unsigned long)save_sequence,
            (unsigned int)continue_game->scene,
            (unsigned int)continue_game->quest
        );
    } else {
        debugf(
            "N64G_TELEM schema=1 seq=%lu event=save_load "
            "status=INSTRUMENTATION_ONLY wall_ticks=%llu eeprom_present=%u "
            "valid_slot_mask=%u outcome=%s selected_slot=NONE save_sequence=NONE "
            "checkpoint_scene=NONE checkpoint_quest=NONE\n",
            (unsigned long)(*sequence)++,
            (unsigned long long)wall_ticks,
            save_available ? 1U : 0U,
            (unsigned int)valid_slot_mask,
            save_available ? "none" : "unavailable"
        );
    }
}

static void telemetry_emit_save_write(
    uint32_t *sequence,
    uint64_t wall_ticks,
    const char *outcome,
    const char *reason,
    bool slot_known,
    uint8_t slot,
    bool sequence_known,
    uint32_t save_sequence,
    bool chapter_completion,
    const N64GameCore *game
)
{
    if (slot_known && sequence_known) {
        debugf(
            "N64G_TELEM schema=1 seq=%lu event=save_write "
            "status=INSTRUMENTATION_ONLY wall_ticks=%llu outcome=%s reason=%s "
            "slot=%u save_sequence=%lu chapter_completion=%u checkpoint_scene=%u "
            "checkpoint_quest=%u\n",
            (unsigned long)(*sequence)++,
            (unsigned long long)wall_ticks,
            outcome,
            reason,
            (unsigned int)slot,
            (unsigned long)save_sequence,
            chapter_completion ? 1U : 0U,
            (unsigned int)game->scene,
            (unsigned int)game->quest
        );
    } else {
        debugf(
            "N64G_TELEM schema=1 seq=%lu event=save_write "
            "status=INSTRUMENTATION_ONLY wall_ticks=%llu outcome=%s reason=%s "
            "slot=NONE save_sequence=NONE chapter_completion=%u "
            "checkpoint_scene=%u checkpoint_quest=%u\n",
            (unsigned long)(*sequence)++,
            (unsigned long long)wall_ticks,
            outcome,
            reason,
            chapter_completion ? 1U : 0U,
            (unsigned int)game->scene,
            (unsigned int)game->quest
        );
    }
}

static void telemetry_emit_summary(
    const N64GameTelemetry *telemetry,
    uint32_t *sequence,
    uint64_t wall_ticks,
    const N64GameCore *game,
    int32_t free_heap_bytes
)
{
    debugf(
        "N64G_TELEM schema=1 seq=%lu event=summary status=INSTRUMENTATION_ONLY "
        "wall_ticks=%llu scene=%u submitted_frames=%lu measured_intervals=%lu "
        "over_budget_frames=%lu missed_deadlines=%lu max_frame_ticks=%lu "
        "max_over_budget_streak=%lu play_ticks=%lu active_control_ticks=%lu "
        "free_heap_bytes=%ld heap_low_water_bytes=%ld invalid_samples=%lu\n",
        (unsigned long)(*sequence)++,
        (unsigned long long)wall_ticks,
        (unsigned int)game->scene,
        (unsigned long)telemetry->total.submitted_frames,
        (unsigned long)telemetry->total.measured_intervals,
        (unsigned long)telemetry->total.over_budget_frames,
        (unsigned long)telemetry->total.missed_deadlines,
        (unsigned long)telemetry->total.max_frame_ticks,
        (unsigned long)telemetry->total.max_over_budget_streak,
        (unsigned long)game->play_ticks,
        (unsigned long)game->active_control_ticks,
        (long)free_heap_bytes,
        (long)telemetry->heap_low_water_bytes,
        (unsigned long)telemetry_invalid_samples(telemetry)
    );
}

static void telemetry_emit_chapter_stable(
    const N64GameTelemetry *telemetry,
    uint32_t *sequence,
    uint64_t boot_ticks,
    uint64_t stable_ticks,
    const N64GameCore *game,
    uint32_t save_sequence
)
{
    debugf(
        "N64G_TELEM schema=1 seq=%lu event=chapter_stable "
        "status=INSTRUMENTATION_ONLY wall_ticks=%llu duration_ticks=%llu "
        "play_ticks=%lu active_control_ticks=%lu save_verified=1 save_sequence=%lu "
        "submitted_frames=%lu measured_intervals=%lu over_budget_frames=%lu "
        "missed_deadlines=%lu max_frame_ticks=%lu max_over_budget_streak=%lu "
        "heap_low_water_bytes=%ld invalid_samples=%lu\n",
        (unsigned long)(*sequence)++,
        (unsigned long long)stable_ticks,
        (unsigned long long)(stable_ticks - boot_ticks),
        (unsigned long)game->play_ticks,
        (unsigned long)game->active_control_ticks,
        (unsigned long)save_sequence,
        (unsigned long)telemetry->total.submitted_frames,
        (unsigned long)telemetry->total.measured_intervals,
        (unsigned long)telemetry->total.over_budget_frames,
        (unsigned long)telemetry->total.missed_deadlines,
        (unsigned long)telemetry->total.max_frame_ticks,
        (unsigned long)telemetry->total.max_over_budget_streak,
        (long)telemetry->heap_low_water_bytes,
        (unsigned long)telemetry_invalid_samples(telemetry)
    );
}

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
    writer->active_game = *game;
    writer->active_game.save_requested = false;
    writer->writes_chapter_completion =
        game->scene == N64GAME_SCENE_END_CHAPTER && game->slice_complete &&
        game->final_save_state == N64GAME_FINAL_SAVE_PENDING;
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

static void save_writer_retry_faulted_attempt(SaveWriter *writer)
{
    /* Only the explicit end-chapter retry edge calls this reset. */
    writer->phase = SAVE_WRITE_IDLE;
    writer->settle_frames = 0U;
    writer->faulted = false;
    writer->pending = false;
    writer->writes_chapter_completion = false;
    writer->chapter_completion_verified = false;
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
        writer->writes_chapter_completion = false;
        return false;
    }
    *continue_game = verified_game;
    *save_sequence = writer->sequence;
    *active_slot = writer->target_slot;
    if (writer->writes_chapter_completion) {
        writer->chapter_completion_verified = true;
    }
    writer->writes_chapter_completion = false;
    writer->phase = SAVE_WRITE_IDLE;
    return true;
}

int main(void)
{
    const uint64_t boot_ticks = get_ticks();
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

    N64GameRenderer renderer;
    assertf(
        n64game_renderer_init_bootstrap(&renderer),
        "N64GAME loading renderer allocation failed"
    );
    n64game_renderer_draw_loading(&renderer, N64GAME_LOADING_RUNTIME);

    joypad_init();
    t3d_init((T3DInitParams){});
    n64game_renderer_draw_loading(&renderer, N64GAME_LOADING_ANNEX_ASSETS);
    assertf(
        n64game_renderer_finish_init(&renderer),
        "N64GAME renderer allocation failed"
    );

    N64GameCore game;
    N64GameCore continue_game;
    n64game_core_init(&game);
    n64game_core_init(&continue_game);

    n64game_renderer_draw_loading(&renderer, N64GAME_LOADING_SAVE_DATA);
    const eeprom_type_t save_type = eeprom_present();
    const bool save_available = save_type != EEPROM_NONE;
    uint32_t save_sequence = 0U;
    uint8_t active_save_slot = 0U;
    uint8_t valid_save_slot_mask = 0U;
    bool continue_available = false;
    if (save_available) {
        uint8_t stored_slots[N64GAME_SAVE_SLOT_COUNT][N64GAME_SAVE_BYTES];
        eeprom_read_bytes(stored_slots, 0U, sizeof(stored_slots));
        for (uint8_t slot = 0U; slot < N64GAME_SAVE_SLOT_COUNT; ++slot) {
            N64GameCore decoded_game;
            uint32_t decoded_sequence = 0U;
            if (n64game_save_decode(
                    stored_slots[slot], &decoded_game, &decoded_sequence
                )) {
                valid_save_slot_mask |= (uint8_t)(UINT8_C(1) << slot);
            }
        }
        continue_available = n64game_save_select_latest(
            stored_slots, &continue_game, &save_sequence, &active_save_slot
        );
    }
    n64game_renderer_draw_loading(&renderer, N64GAME_LOADING_READY);

    heap_stats_t heap_stats;
    sys_get_heap_stats(&heap_stats);
    N64GameTelemetry telemetry;
    assertf(
        n64game_telemetry_init(
            &telemetry,
            (uint32_t)TICKS_PER_SECOND,
            heap_stats.free,
            heap_stats.fragmented
        ),
        "N64GAME telemetry initialization failed"
    );
    uint32_t telemetry_sequence = 0U;
    telemetry_emit_session(
        &telemetry, &telemetry_sequence, boot_ticks, get_ticks()
    );
    telemetry_emit_save_load(
        &telemetry_sequence,
        get_ticks(),
        save_available,
        valid_save_slot_mask,
        continue_available,
        active_save_slot,
        save_sequence,
        &continue_game
    );

    SaveWriter save_writer = {0};
    bool controller_was_connected = false;
    bool chapter_completion_emitted = false;

    for (;;) {
        joypad_poll();
        const bool controller_connected = joypad_is_connected(JOYPAD_PORT_1);
        const bool clear_edge_frame = controller_connected && !controller_was_connected;
        controller_was_connected = controller_connected;
        const N64GameInput input = controller_connected ?
            read_game_input() : (N64GameInput){0};
        const N64GameScene scene_before = game.scene;
        const N64GameFinalSaveState final_save_before_update = game.final_save_state;
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
        const bool explicit_final_save_retry =
            scene_before == N64GAME_SCENE_END_CHAPTER &&
            final_save_before_update == N64GAME_FINAL_SAVE_FAILED &&
            game.final_save_state == N64GAME_FINAL_SAVE_PENDING &&
            game.save_requested;
        if (explicit_final_save_retry && save_available && save_writer.faulted) {
            save_writer_retry_faulted_attempt(&save_writer);
        }
        const bool pumping_chapter_completion = save_writer.writes_chapter_completion;
        const bool save_faulted_before_pump = save_writer.faulted;
        const uint8_t pumped_save_slot = save_writer.target_slot;
        const uint32_t pumped_save_sequence = save_writer.sequence;
        bool write_verified = false;
        bool final_save_attempted = false;
        bool final_save_accepted = false;
        if (save_available && !save_writer.faulted) {
            write_verified = save_writer_pump(
                &save_writer, &continue_game, &save_sequence, &active_save_slot
            );
            if (write_verified) {
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
                final_save_attempted =
                    game.final_save_state == N64GAME_FINAL_SAVE_PENDING;
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
                final_save_accepted = accepted;
            }
        }
        const bool final_save_unavailable =
            !save_available && game.final_save_state == N64GAME_FINAL_SAVE_PENDING &&
            game.save_requested;
        const bool final_save_request_rejected =
            game.final_save_state == N64GAME_FINAL_SAVE_PENDING &&
            final_save_attempted && !final_save_accepted;
        if (write_verified && pumping_chapter_completion &&
            game.final_save_state == N64GAME_FINAL_SAVE_PENDING) {
            n64game_core_set_final_save_result(&game, true);
        } else if (game.final_save_state == N64GAME_FINAL_SAVE_PENDING &&
                   ((!save_available && game.save_requested) ||
                    (!save_faulted_before_pump && save_writer.faulted) ||
                    (save_writer.faulted && game.save_requested) ||
                    (final_save_attempted && !final_save_accepted))) {
            n64game_core_set_final_save_result(&game, false);
        }

        const bool write_verification_failed =
            !save_faulted_before_pump && save_writer.faulted;
        if (write_verified) {
            telemetry_emit_save_write(
                &telemetry_sequence,
                get_ticks(),
                "verified",
                "none",
                true,
                pumped_save_slot,
                true,
                pumped_save_sequence,
                pumping_chapter_completion,
                &continue_game
            );
        } else if (write_verification_failed) {
            telemetry_emit_save_write(
                &telemetry_sequence,
                get_ticks(),
                "failed",
                "verification",
                true,
                pumped_save_slot,
                true,
                pumped_save_sequence,
                pumping_chapter_completion,
                &save_writer.active_game
            );
        } else if (final_save_unavailable) {
            telemetry_emit_save_write(
                &telemetry_sequence,
                get_ticks(),
                "failed",
                "eeprom_unavailable",
                false,
                0U,
                false,
                0U,
                true,
                &game
            );
        } else if (final_save_request_rejected) {
            telemetry_emit_save_write(
                &telemetry_sequence,
                get_ticks(),
                "failed",
                "request_rejected",
                false,
                0U,
                false,
                0U,
                true,
                &game
            );
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

        const uint32_t frame_tick = TICKS_READ();
        (void)n64game_telemetry_record_frame(&telemetry, game.scene, frame_tick);
        const bool transition_observed = scene_before != game.scene;
        const bool summary_due = telemetry.total.submitted_frames != 0U &&
            telemetry.total.submitted_frames %
                N64GAME_TELEMETRY_SUMMARY_FRAMES == 0U;
        const bool chapter_stable = game.scene == N64GAME_SCENE_END_CHAPTER &&
            game.slice_complete &&
            game.final_save_state == N64GAME_FINAL_SAVE_VERIFIED &&
            save_writer.chapter_completion_verified &&
            continue_available && !save_busy && !game.save_requested;
        const bool periodic_heap_sample_due =
            telemetry.total.submitted_frames != 0U &&
            telemetry.total.submitted_frames %
                N64GAME_TELEMETRY_HEAP_SAMPLE_FRAMES == 0U;
        const bool heap_sample_due = transition_observed || summary_due ||
            periodic_heap_sample_due ||
            (chapter_stable && !chapter_completion_emitted);
        if (heap_sample_due) {
            sys_get_heap_stats(&heap_stats);
            (void)n64game_telemetry_sample_heap(
                &telemetry, heap_stats.free, heap_stats.fragmented
            );
        }
        const uint64_t wall_ticks = get_ticks();
        if (transition_observed &&
            n64game_telemetry_record_transition(&telemetry, scene_before, game.scene)) {
            telemetry_emit_scene_summary(
                &telemetry,
                &telemetry_sequence,
                wall_ticks,
                scene_before
            );
            telemetry_emit_transition(
                &telemetry,
                &telemetry_sequence,
                wall_ticks,
                scene_before,
                game.scene,
                resume_now,
                &game,
                heap_stats.free
            );
        }
        if (summary_due) {
            telemetry_emit_summary(
                &telemetry,
                &telemetry_sequence,
                wall_ticks,
                &game,
                heap_stats.free
            );
        }
        if (chapter_stable && !chapter_completion_emitted) {
            telemetry_emit_scene_summary(
                &telemetry,
                &telemetry_sequence,
                wall_ticks,
                N64GAME_SCENE_END_CHAPTER
            );
            telemetry_emit_chapter_stable(
                &telemetry,
                &telemetry_sequence,
                boot_ticks,
                wall_ticks,
                &game,
                save_sequence
            );
            chapter_completion_emitted = true;
        }
    }
}
