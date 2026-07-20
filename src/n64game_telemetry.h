#ifndef N64GAME_TELEMETRY_H
#define N64GAME_TELEMETRY_H

#include <stdbool.h>
#include <stdint.h>

#include "n64game_core.h"

enum {
    N64GAME_TELEMETRY_SCHEMA_VERSION = 1,
    N64GAME_TELEMETRY_TARGET_FPS = 30,
    N64GAME_TELEMETRY_HEAP_SAMPLE_FRAMES = 30,
    N64GAME_TELEMETRY_SUMMARY_FRAMES = 300,
    N64GAME_TELEMETRY_SCENE_COUNT = N64GAME_SCENE_END_CHAPTER + 1,
};

typedef struct {
    uint32_t submitted_frames;
    uint32_t measured_intervals;
    uint32_t over_budget_frames;
    uint32_t missed_deadlines;
    uint32_t max_frame_ticks;
    uint32_t current_over_budget_streak;
    uint32_t max_over_budget_streak;
} N64GameTelemetryFrameStats;

typedef struct {
    bool measured;
    bool valid;
    bool over_budget;
    uint32_t delta_ticks;
    uint32_t missed_deadlines;
} N64GameTelemetryFrameSample;

typedef struct {
    uint32_t ticks_per_second;
    uint32_t frame_budget_ticks;
    uint32_t frame_tolerance_ticks;
    uint32_t last_frame_tick;
    uint32_t transition_count;
    uint32_t invalid_frame_intervals;
    uint32_t invalid_scene_samples;
    uint32_t invalid_transitions;
    uint32_t heap_samples;
    uint32_t invalid_heap_samples;
    int32_t heap_baseline_bytes;
    int32_t heap_low_water_bytes;
    int32_t heap_fragmented_at_low_water_bytes;
    bool last_frame_tick_valid;
    N64GameTelemetryFrameStats total;
    N64GameTelemetryFrameStats scenes[N64GAME_TELEMETRY_SCENE_COUNT];
} N64GameTelemetry;

bool n64game_telemetry_init(
    N64GameTelemetry *telemetry,
    uint32_t ticks_per_second,
    int32_t baseline_free_heap_bytes,
    int32_t baseline_fragmented_heap_bytes
);
N64GameTelemetryFrameSample n64game_telemetry_record_frame(
    N64GameTelemetry *telemetry,
    N64GameScene scene,
    uint32_t frame_tick
);
bool n64game_telemetry_sample_heap(
    N64GameTelemetry *telemetry,
    int32_t free_heap_bytes,
    int32_t fragmented_heap_bytes
);
bool n64game_telemetry_record_transition(
    N64GameTelemetry *telemetry,
    N64GameScene from,
    N64GameScene to
);

#endif
