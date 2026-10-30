#ifndef FRONTEND_MEDIA_H
#define FRONTEND_MEDIA_H
#include <stddef.h>
typedef int (*FrontendRead)(int sector,int count,void *target);
int frontend_media_load(FrontendRead read,void *staging,size_t size);
void frontend_media_logo(int tick);
void frontend_media_track(int track);
void frontend_media_effect(int effect);
void frontend_media_mute(int muted);
void frontend_media_levels(int music,int effects);
extern volatile int front_media_ready,front_audio_track,front_logo_frame,front_media_errors;
extern int front_sfx_events[7];
#endif
