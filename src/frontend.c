#include "frontend.h"
void frontend_init(Frontend *f){*f=(Frontend){.screen=FRONT_LOGO};
#ifdef ZERA_CAMPAIGN_ENTRY
 f->music_volume=f->sfx_volume=4;f->sensitivity=2;
#endif
}
void frontend_finish_logo(Frontend *f){if(f->screen==FRONT_LOGO){f->screen=FRONT_TITLE;f->selection=0;}}
#ifndef ZERA_CAMPAIGN_ENTRY
int frontend_update(Frontend *f,unsigned p){
 if(f->screen==FRONT_LOGO){if(p)frontend_finish_logo(f);return 0;}
 if(f->screen==FRONT_PLAY){if(p&UI_START){f->screen=FRONT_PAUSE;f->selection=0;}return 0;}
 if(f->screen==FRONT_CONTROLS){if(p&(UI_BACK|UI_ACCEPT|UI_START)){f->screen=f->return_to;f->selection=0;}return 0;}
 if(f->screen==FRONT_OPTIONS){
  if(p&(UI_BACK|UI_START)){f->screen=f->return_to;f->selection=0;return 0;}
  if(p&(UI_UP|UI_DOWN))f->selection^=1;
  if(p&UI_ACCEPT){if(!f->selection)f->muted=!f->muted;else{f->screen=f->return_to;f->selection=0;}}
  return 0;
 }
 if(f->screen==FRONT_PAUSE && (p&(UI_BACK|UI_START))){f->screen=FRONT_PLAY;return 0;}
 int count=f->screen==FRONT_TITLE?3:5;
 if(p&UI_UP)f->selection=(f->selection+count-1)%count;
 if(p&UI_DOWN)f->selection=(f->selection+1)%count;
 if(!(p&UI_ACCEPT))return 0;
 if(f->screen==FRONT_TITLE){
  if(f->selection==0){f->screen=FRONT_PLAY;f->has_game=1;return FRONT_NEW_GAME;}
  f->return_to=FRONT_TITLE;f->screen=f->selection==1?FRONT_OPTIONS:FRONT_CONTROLS;f->selection=0;
 }else{
  switch(f->selection){
   case 0:f->screen=FRONT_PLAY;break;
   case 1:f->screen=FRONT_PLAY;return FRONT_RESPAWN;
   case 2:case 3:f->return_to=FRONT_PAUSE;f->screen=f->selection==2?FRONT_OPTIONS:FRONT_CONTROLS;f->selection=0;break;
   case 4:f->screen=FRONT_TITLE;f->selection=0;f->has_game=0;return FRONT_RETURN_TITLE;
  }
 }
 return 0;
}

#else
#include "../previews/frontend/src/frontend_text.h"
static int adjust(int n,int delta,int low,int high){n+=delta;return n<low?low:n>high?high:n;}
static int back(unsigned p){return p&(UI_BACK|UI_START);}
int frontend_update(Frontend *f,unsigned p){
 if(f->screen==FRONT_LOGO){if(p)frontend_finish_logo(f);return 0;}
 if(f->screen==FRONT_PLAY){if(p&UI_START){f->screen=FRONT_PAUSE;f->selection=0;}return 0;}
 if(f->screen==FRONT_CONTROLS){if(back(p) || (p&UI_ACCEPT)){f->screen=f->return_to;f->selection=0;}return 0;}
 if(f->screen==FRONT_CREDITS || f->screen==FRONT_CHANGELOG){
  int count=f->screen==FRONT_CREDITS?FRONT_CREDITS_PAGES:FRONT_CHANGELOG_PAGES;
  if(back(p)){f->screen=f->return_to;f->selection=0;return 0;}
  if(p&(UI_DOWN|FRONT_RIGHT|UI_ACCEPT))f->page=adjust(f->page,1,0,count-1);
  if(p&(UI_UP|FRONT_LEFT))f->page=adjust(f->page,-1,0,count-1);
  return 0;
 }
 if(f->screen==FRONT_AUDIO_OPTIONS || f->screen==FRONT_GAMEPLAY_OPTIONS){
  if(back(p)){f->screen=FRONT_OPTIONS;f->selection=0;return 0;}
  if(p&UI_UP)f->selection=(f->selection+2)%3;
  if(p&UI_DOWN)f->selection=(f->selection+1)%3;
  int delta=p&FRONT_LEFT?-1:p&(FRONT_RIGHT|UI_ACCEPT)?1:0;
  if(f->selection==2 && (p&UI_ACCEPT)){f->screen=FRONT_OPTIONS;f->selection=0;return 0;}
  if(delta && f->selection<2){
   if(f->screen==FRONT_AUDIO_OPTIONS){int *value=f->selection?&f->sfx_volume:&f->music_volume;*value=adjust(*value,delta,0,4);}
   else if(f->selection==0)f->camera_mode^=1;
   else f->sensitivity=adjust(f->sensitivity,delta,1,4);
  }
  return 0;
 }
 if(f->screen==FRONT_OPTIONS){
  if(back(p)){f->screen=f->return_to;f->selection=0;return 0;}
  if(p&UI_UP)f->selection=(f->selection+3)%4;
  if(p&UI_DOWN)f->selection=(f->selection+1)%4;
  if(p&UI_ACCEPT){
   if(f->selection==0)f->muted=!f->muted;
   else if(f->selection==3){f->screen=f->return_to;f->selection=0;}
   else{f->screen=f->selection==1?FRONT_AUDIO_OPTIONS:FRONT_GAMEPLAY_OPTIONS;f->selection=0;}
  }
  return 0;
 }
 if(f->screen==FRONT_PAUSE && back(p)){f->screen=FRONT_PLAY;return 0;}
 if(p&UI_UP)f->selection=(f->selection+4)%5;
 if(p&UI_DOWN)f->selection=(f->selection+1)%5;
 if(!(p&UI_ACCEPT))return 0;
 if(f->screen==FRONT_TITLE){
  if(f->selection==0){f->screen=FRONT_PLAY;f->has_game=1;return FRONT_NEW_GAME;}
  f->return_to=FRONT_TITLE;f->page=0;
  f->screen=f->selection==1?FRONT_OPTIONS:f->selection==2?FRONT_CONTROLS:f->selection==3?FRONT_CREDITS:FRONT_CHANGELOG;f->selection=0;
 }else{
  switch(f->selection){
   case 0:f->screen=FRONT_PLAY;break;
   case 1:f->screen=FRONT_PLAY;return FRONT_RESPAWN;
   case 2:case 3:f->return_to=FRONT_PAUSE;f->screen=f->selection==2?FRONT_OPTIONS:FRONT_CONTROLS;f->selection=0;break;
   case 4:f->screen=FRONT_TITLE;f->selection=0;f->has_game=0;return FRONT_RETURN_TITLE;
  }
 }
 return 0;
}
#endif
