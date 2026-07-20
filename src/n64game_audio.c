#include <stdint.h>
#include <stddef.h>

#include <libdragon.h>

#include "n64game_audio.h"

#define N64GAME_AUDIO_SAMPLE_RATE 22050
#define N64GAME_AUDIO_LATENCY_MS 80
#define N64GAME_AUDIO_PHASE_ONE UINT64_C(4294967296)

static volatile uint32_t n64game_audio_phase = 0U;
static volatile uint32_t n64game_audio_phase_inc = 0U;
static volatile int32_t n64game_audio_samples_left = 0;
static volatile int32_t n64game_audio_samples_total = 1;
static volatile int32_t n64game_audio_peak = 0;

static uint32_t phase_increment(unsigned frequency_hz)
{
    return (uint32_t)(
        (N64GAME_AUDIO_PHASE_ONE * (uint64_t)frequency_hz) /
        (uint64_t)N64GAME_AUDIO_SAMPLE_RATE
    );
}

static void audio_fill(short *buffer, size_t numsamples)
{
    uint32_t phase = n64game_audio_phase;
    const uint32_t phase_inc = n64game_audio_phase_inc;
    int32_t samples_left = n64game_audio_samples_left;
    const int32_t samples_total = n64game_audio_samples_total;
    const int32_t peak = n64game_audio_peak;

    for (size_t index = 0; index < numsamples; ++index) {
        int16_t sample = 0;
        if (samples_left > 0 && samples_total > 0 && peak > 0) {
            phase += phase_inc;
            const int32_t envelope = peak * samples_left / samples_total;
            sample = (phase & UINT32_C(0x80000000)) != 0U ?
                (int16_t)envelope : (int16_t)-envelope;
            --samples_left;
        }
        buffer[index * 2U] = sample;
        buffer[index * 2U + 1U] = sample;
    }

    n64game_audio_phase = phase;
    n64game_audio_samples_left = samples_left > 0 ? samples_left : 0;
}

void n64game_audio_init(void)
{
    audio_init(
        N64GAME_AUDIO_SAMPLE_RATE,
        AUDIO_INIT_LATENCY_MS(N64GAME_AUDIO_LATENCY_MS)
    );
    audio_set_buffer_callback(audio_fill);
}

void n64game_audio_trigger(N64GameAudioCue cue)
{
    unsigned frequency_hz = 660U;
    int32_t duration_samples = N64GAME_AUDIO_SAMPLE_RATE / 32;
    int32_t peak = 2800;

    switch (cue) {
    case N64GAME_AUDIO_CUE_NAVIGATE:
        frequency_hz = 880U;
        duration_samples = N64GAME_AUDIO_SAMPLE_RATE / 55;
        peak = 1900;
        break;
    case N64GAME_AUDIO_CUE_CONFIRM:
        frequency_hz = 1320U;
        duration_samples = N64GAME_AUDIO_SAMPLE_RATE / 32;
        peak = 2600;
        break;
    case N64GAME_AUDIO_CUE_CANCEL:
        frequency_hz = 440U;
        duration_samples = N64GAME_AUDIO_SAMPLE_RATE / 28;
        peak = 2300;
        break;
    case N64GAME_AUDIO_CUE_RELAY:
        frequency_hz = 990U;
        duration_samples = N64GAME_AUDIO_SAMPLE_RATE / 18;
        peak = 3000;
        break;
    case N64GAME_AUDIO_CUE_TRANSITION:
        frequency_hz = 550U;
        duration_samples = N64GAME_AUDIO_SAMPLE_RATE / 16;
        peak = 2500;
        break;
    }

    n64game_audio_phase_inc = phase_increment(frequency_hz);
    n64game_audio_samples_total = duration_samples;
    n64game_audio_samples_left = duration_samples;
    n64game_audio_peak = peak;
}
