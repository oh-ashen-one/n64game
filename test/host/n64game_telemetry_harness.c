#include <assert.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>

#include "n64game_telemetry.h"

int main(void)
{
    N64GameTelemetry telemetry;
    assert(!n64game_telemetry_init(&telemetry, 0U, 700000, 1000));
    assert(!n64game_telemetry_init(&telemetry, 30000000U, 1000, 1001));
    assert(n64game_telemetry_init(&telemetry, 30000000U, 700000, 1000));
    assert(telemetry.frame_budget_ticks == 1000000U);
    assert(telemetry.frame_tolerance_ticks == 30000U);
    assert(telemetry.heap_samples == 1U);

    const uint32_t first = UINT32_MAX - 400000U;
    N64GameTelemetryFrameSample sample = n64game_telemetry_record_frame(
        &telemetry, N64GAME_SCENE_ANNEX, first
    );
    assert(sample.valid && !sample.measured);

    uint32_t tick = first + telemetry.frame_budget_ticks;
    sample = n64game_telemetry_record_frame(&telemetry, N64GAME_SCENE_ANNEX, tick);
    assert(sample.valid && sample.measured && !sample.over_budget);
    assert(sample.delta_ticks == telemetry.frame_budget_ticks);
    assert(sample.missed_deadlines == 0U);

    tick += telemetry.frame_budget_ticks + telemetry.frame_tolerance_ticks + 1U;
    sample = n64game_telemetry_record_frame(&telemetry, N64GAME_SCENE_BATTLE, tick);
    assert(sample.valid && sample.over_budget && sample.missed_deadlines == 0U);

    tick += telemetry.frame_budget_ticks * 2U;
    sample = n64game_telemetry_record_frame(&telemetry, N64GAME_SCENE_BATTLE, tick);
    assert(sample.valid && sample.over_budget && sample.missed_deadlines == 1U);
    assert(telemetry.total.over_budget_frames == 2U);
    assert(telemetry.total.missed_deadlines == 1U);
    assert(telemetry.total.max_over_budget_streak == 2U);
    assert(telemetry.scenes[N64GAME_SCENE_BATTLE].measured_intervals == 2U);

    tick += telemetry.frame_budget_ticks;
    sample = n64game_telemetry_record_frame(&telemetry, N64GAME_SCENE_ANNEX, tick);
    assert(sample.valid && !sample.over_budget);
    assert(telemetry.total.current_over_budget_streak == 0U);
    assert(telemetry.total.submitted_frames == 5U);
    assert(telemetry.total.measured_intervals == 4U);

    assert(n64game_telemetry_sample_heap(&telemetry, 650000, 2000));
    assert(!n64game_telemetry_sample_heap(&telemetry, 660000, 1000));
    assert(telemetry.heap_low_water_bytes == 650000);
    assert(telemetry.heap_fragmented_at_low_water_bytes == 2000);
    assert(!n64game_telemetry_sample_heap(&telemetry, 1000, 1001));
    assert(telemetry.invalid_heap_samples == 1U);

    assert(n64game_telemetry_record_transition(
        &telemetry, N64GAME_SCENE_ANNEX, N64GAME_SCENE_BATTLE
    ));
    assert(!n64game_telemetry_record_transition(
        &telemetry, N64GAME_SCENE_BATTLE, N64GAME_SCENE_BATTLE
    ));
    assert(telemetry.transition_count == 1U && telemetry.invalid_transitions == 1U);

    sample = n64game_telemetry_record_frame(
        &telemetry, (N64GameScene)N64GAME_TELEMETRY_SCENE_COUNT, tick + 1U
    );
    assert(!sample.valid && telemetry.invalid_scene_samples == 1U);

    telemetry.last_frame_tick = 0U;
    telemetry.last_frame_tick_valid = true;
    sample = n64game_telemetry_record_frame(
        &telemetry, N64GAME_SCENE_ANNEX, (uint32_t)INT32_MAX + 1U
    );
    assert(sample.measured && !sample.valid);
    assert(telemetry.invalid_frame_intervals == 1U);

    puts("n64game telemetry harness: PASS");
    return 0;
}
