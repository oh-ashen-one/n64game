#include "n64game_telemetry.h"

#include <limits.h>
#include <string.h>

static bool scene_valid(N64GameScene scene)
{
    return (unsigned)scene < (unsigned)N64GAME_TELEMETRY_SCENE_COUNT;
}

static uint32_t saturating_add_u32(uint32_t value, uint32_t amount)
{
    return amount > UINT32_MAX - value ? UINT32_MAX : value + amount;
}

static void record_frame_stats(
    N64GameTelemetryFrameStats *stats,
    uint32_t delta_ticks,
    bool over_budget,
    uint32_t missed_deadlines
)
{
    stats->measured_intervals = saturating_add_u32(stats->measured_intervals, 1U);
    if (delta_ticks > stats->max_frame_ticks) {
        stats->max_frame_ticks = delta_ticks;
    }
    stats->missed_deadlines = saturating_add_u32(
        stats->missed_deadlines, missed_deadlines
    );
    if (over_budget) {
        stats->over_budget_frames = saturating_add_u32(stats->over_budget_frames, 1U);
        stats->current_over_budget_streak = saturating_add_u32(
            stats->current_over_budget_streak, 1U
        );
        if (stats->current_over_budget_streak > stats->max_over_budget_streak) {
            stats->max_over_budget_streak = stats->current_over_budget_streak;
        }
    } else {
        stats->current_over_budget_streak = 0U;
    }
}

bool n64game_telemetry_init(
    N64GameTelemetry *telemetry,
    uint32_t ticks_per_second,
    int32_t baseline_free_heap_bytes,
    int32_t baseline_fragmented_heap_bytes
)
{
    if (telemetry == NULL || ticks_per_second < N64GAME_TELEMETRY_TARGET_FPS ||
        baseline_free_heap_bytes < 0 || baseline_fragmented_heap_bytes < 0 ||
        baseline_fragmented_heap_bytes > baseline_free_heap_bytes) {
        return false;
    }
    *telemetry = (N64GameTelemetry){0};
    telemetry->ticks_per_second = ticks_per_second;
    telemetry->frame_budget_ticks = (
        ticks_per_second + N64GAME_TELEMETRY_TARGET_FPS - 1U
    ) / N64GAME_TELEMETRY_TARGET_FPS;
    /* One millisecond keeps normal NTSC 30 Hz cadence out of the over-budget bucket. */
    telemetry->frame_tolerance_ticks = (ticks_per_second + 999U) / 1000U;
    telemetry->heap_baseline_bytes = baseline_free_heap_bytes;
    telemetry->heap_low_water_bytes = baseline_free_heap_bytes;
    telemetry->heap_fragmented_at_low_water_bytes = baseline_fragmented_heap_bytes;
    telemetry->heap_samples = 1U;
    return true;
}

N64GameTelemetryFrameSample n64game_telemetry_record_frame(
    N64GameTelemetry *telemetry,
    N64GameScene scene,
    uint32_t frame_tick
)
{
    N64GameTelemetryFrameSample sample = {0};
    if (telemetry == NULL || !scene_valid(scene)) {
        if (telemetry != NULL) {
            telemetry->invalid_scene_samples = saturating_add_u32(
                telemetry->invalid_scene_samples, 1U
            );
        }
        return sample;
    }

    N64GameTelemetryFrameStats *const scene_stats = &telemetry->scenes[(unsigned)scene];
    telemetry->total.submitted_frames = saturating_add_u32(
        telemetry->total.submitted_frames, 1U
    );
    scene_stats->submitted_frames = saturating_add_u32(scene_stats->submitted_frames, 1U);
    if (!telemetry->last_frame_tick_valid) {
        telemetry->last_frame_tick = frame_tick;
        telemetry->last_frame_tick_valid = true;
        sample.valid = true;
        return sample;
    }

    const uint32_t delta_ticks = frame_tick - telemetry->last_frame_tick;
    telemetry->last_frame_tick = frame_tick;
    sample.measured = true;
    sample.delta_ticks = delta_ticks;
    if (delta_ticks > (uint32_t)INT32_MAX) {
        telemetry->invalid_frame_intervals = saturating_add_u32(
            telemetry->invalid_frame_intervals, 1U
        );
        return sample;
    }

    sample.valid = true;
    sample.over_budget = delta_ticks >
        telemetry->frame_budget_ticks + telemetry->frame_tolerance_ticks;
    const uint32_t rounded_periods = (
        delta_ticks + telemetry->frame_budget_ticks / 2U
    ) / telemetry->frame_budget_ticks;
    sample.missed_deadlines = rounded_periods > 1U ? rounded_periods - 1U : 0U;
    record_frame_stats(
        &telemetry->total,
        delta_ticks,
        sample.over_budget,
        sample.missed_deadlines
    );
    record_frame_stats(
        scene_stats,
        delta_ticks,
        sample.over_budget,
        sample.missed_deadlines
    );
    return sample;
}

bool n64game_telemetry_sample_heap(
    N64GameTelemetry *telemetry,
    int32_t free_heap_bytes,
    int32_t fragmented_heap_bytes
)
{
    if (telemetry == NULL) {
        return false;
    }
    if (free_heap_bytes < 0 || fragmented_heap_bytes < 0 ||
        fragmented_heap_bytes > free_heap_bytes) {
        telemetry->invalid_heap_samples = saturating_add_u32(
            telemetry->invalid_heap_samples, 1U
        );
        return false;
    }
    telemetry->heap_samples = saturating_add_u32(telemetry->heap_samples, 1U);
    if (free_heap_bytes < telemetry->heap_low_water_bytes) {
        telemetry->heap_low_water_bytes = free_heap_bytes;
        telemetry->heap_fragmented_at_low_water_bytes = fragmented_heap_bytes;
        return true;
    }
    return false;
}

bool n64game_telemetry_record_transition(
    N64GameTelemetry *telemetry,
    N64GameScene from,
    N64GameScene to
)
{
    if (telemetry == NULL || !scene_valid(from) || !scene_valid(to) || from == to) {
        if (telemetry != NULL) {
            telemetry->invalid_transitions = saturating_add_u32(
                telemetry->invalid_transitions, 1U
            );
        }
        return false;
    }
    telemetry->transition_count = saturating_add_u32(telemetry->transition_count, 1U);
    return true;
}
