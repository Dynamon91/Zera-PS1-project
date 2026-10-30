#include <assert.h>
#include "../src/frontend.h"
int main(void){
 Frontend f;frontend_init(&f);assert(f.screen==FRONT_LOGO);
 assert(!frontend_update(&f,UI_ACCEPT) && f.screen==FRONT_TITLE && !f.has_game);
 frontend_finish_logo(&f);assert(f.screen==FRONT_TITLE);
 assert(frontend_update(&f,UI_ACCEPT)==FRONT_NEW_GAME && f.screen==FRONT_PLAY && f.has_game);
 frontend_update(&f,UI_START);assert(f.screen==FRONT_PAUSE);
 frontend_update(&f,UI_DOWN);assert(frontend_update(&f,UI_ACCEPT)==FRONT_RESPAWN && f.screen==FRONT_PLAY);
 frontend_update(&f,UI_START);frontend_update(&f,UI_DOWN);frontend_update(&f,UI_DOWN);frontend_update(&f,UI_ACCEPT);
 assert(f.screen==FRONT_OPTIONS && f.return_to==FRONT_PAUSE);
 frontend_update(&f,UI_ACCEPT);assert(f.muted);frontend_update(&f,UI_BACK);assert(f.screen==FRONT_PAUSE);
 frontend_update(&f,UI_UP);frontend_update(&f,UI_UP);frontend_update(&f,UI_ACCEPT);assert(f.screen==FRONT_CONTROLS);
 frontend_update(&f,UI_BACK);assert(f.screen==FRONT_PAUSE);
 frontend_update(&f,UI_START);assert(f.screen==FRONT_PLAY && f.muted);
 frontend_update(&f,UI_START);frontend_update(&f,UI_UP);assert(frontend_update(&f,UI_ACCEPT)==FRONT_RETURN_TITLE && f.screen==FRONT_TITLE && !f.has_game);
 frontend_update(&f,UI_DOWN);frontend_update(&f,UI_ACCEPT);assert(f.screen==FRONT_OPTIONS);
 frontend_update(&f,UI_ACCEPT);assert(!f.muted);frontend_update(&f,UI_DOWN);frontend_update(&f,UI_ACCEPT);assert(f.screen==FRONT_TITLE);
 assert(frontend_update(&f,UI_ACCEPT)==FRONT_NEW_GAME && f.has_game);
 frontend_init(&f);frontend_finish_logo(&f);assert(f.screen==FRONT_TITLE);
 return 0;
}
