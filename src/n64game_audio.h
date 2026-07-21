#ifndef N64GAME_AUDIO_H
#define N64GAME_AUDIO_H

typedef enum {
    N64GAME_AUDIO_CUE_NAVIGATE = 0,
    N64GAME_AUDIO_CUE_CONFIRM,
    N64GAME_AUDIO_CUE_CANCEL,
    N64GAME_AUDIO_CUE_RELAY,
    N64GAME_AUDIO_CUE_TRANSITION,
} N64GameAudioCue;

void n64game_audio_init(void);
void n64game_audio_trigger(N64GameAudioCue cue);

#endif
