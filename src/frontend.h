#ifndef FRONTEND_H
#define FRONTEND_H
#include "menu.h"
enum {FRONT_LOGO,FRONT_TITLE,FRONT_PLAY,FRONT_PAUSE,FRONT_CONTROLS,FRONT_OPTIONS,FRONT_CREDITS,FRONT_AUDIO_OPTIONS,FRONT_GAMEPLAY_OPTIONS,FRONT_CHANGELOG};
enum {FRONT_NEW_GAME=1,FRONT_RESPAWN=2,FRONT_RETURN_TITLE=4};
enum {FRONT_LEFT=32,FRONT_RIGHT=64};
typedef struct {int screen,selection,return_to,muted,has_game;
#ifdef ZERA_CAMPAIGN_ENTRY
 int music_volume,sfx_volume,camera_mode,sensitivity,page;
#endif
} Frontend;
void frontend_init(Frontend *f);
void frontend_finish_logo(Frontend *f);
int frontend_update(Frontend *f,unsigned pressed);
#endif
