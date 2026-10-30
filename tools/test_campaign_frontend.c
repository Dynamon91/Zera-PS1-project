#include <assert.h>
#include "../src/frontend.h"
static void down(Frontend *f,int n){while(n--)frontend_update(f,UI_DOWN);}
int main(void){
 Frontend f;frontend_init(&f);assert(f.music_volume==4 && f.sfx_volume==4 && f.sensitivity==2);
 frontend_finish_logo(&f);down(&f,3);frontend_update(&f,UI_ACCEPT);assert(f.screen==FRONT_CREDITS);
 frontend_update(&f,UI_DOWN);assert(f.page==0);frontend_update(&f,UI_BACK);down(&f,4);frontend_update(&f,UI_ACCEPT);assert(f.screen==FRONT_CHANGELOG);
 for(int k=0;k<200;k++)frontend_update(&f,UI_DOWN);assert(f.page==70);frontend_update(&f,UI_BACK);
 down(&f,1);frontend_update(&f,UI_ACCEPT);assert(f.screen==FRONT_OPTIONS);
 down(&f,1);frontend_update(&f,UI_ACCEPT);assert(f.screen==FRONT_AUDIO_OPTIONS);
 for(int k=0;k<8;k++)frontend_update(&f,FRONT_LEFT);assert(!f.music_volume);
 frontend_update(&f,FRONT_RIGHT);assert(f.music_volume==1);down(&f,1);frontend_update(&f,FRONT_LEFT);assert(f.sfx_volume==3);
 frontend_update(&f,UI_BACK);down(&f,2);frontend_update(&f,UI_ACCEPT);assert(f.screen==FRONT_GAMEPLAY_OPTIONS);
 frontend_update(&f,UI_ACCEPT);assert(f.camera_mode==1);down(&f,1);
 for(int k=0;k<8;k++)frontend_update(&f,FRONT_RIGHT);assert(f.sensitivity==4);
 frontend_update(&f,UI_BACK);frontend_update(&f,UI_BACK);assert(f.screen==FRONT_TITLE);
 assert(frontend_update(&f,UI_ACCEPT)==FRONT_NEW_GAME && f.screen==FRONT_PLAY);
 frontend_update(&f,UI_START);assert(f.screen==FRONT_PAUSE);down(&f,2);frontend_update(&f,UI_ACCEPT);assert(f.screen==FRONT_OPTIONS && f.return_to==FRONT_PAUSE);
 frontend_update(&f,UI_BACK);frontend_update(&f,UI_START);assert(f.screen==FRONT_PLAY && f.camera_mode==1 && f.sensitivity==4);
 frontend_update(&f,UI_START);frontend_update(&f,UI_UP);assert(frontend_update(&f,UI_ACCEPT)==FRONT_RETURN_TITLE && f.music_volume==1 && f.sfx_volume==3);
 return 0;
}
