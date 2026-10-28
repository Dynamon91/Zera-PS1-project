#ifndef AUDIO_H
#define AUDIO_H
enum {SFX_UI_MOVE,SFX_UI_ACCEPT,SFX_JUMP,SFX_LAND,SFX_DASH,SFX_FLAP,SFX_PICKUP};
void audio_init(void);
void audio_update(int duck);
void audio_play(int sample);
extern volatile int audio_music_ready,audio_underruns,audio_cd_errors,audio_refills,audio_wraps;
extern int audio_sfx_events[7];
#endif
