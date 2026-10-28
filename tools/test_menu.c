#include <assert.h>
#include "../src/menu.h"
int main(void){
 Menu m;menu_init(&m);assert(m.screen==MENU_TITLE && !m.debug);
 menu_update(&m,UI_UP);assert(m.selection==2);menu_update(&m,UI_ACCEPT);assert(m.debug && m.screen==MENU_TITLE);
 menu_update(&m,UI_UP);menu_update(&m,UI_ACCEPT);assert(m.screen==MENU_CONTROLS);
 menu_update(&m,UI_BACK);assert(m.screen==MENU_TITLE && m.selection==1);
 menu_update(&m,UI_UP);assert(menu_update(&m,UI_START)&MENU_RESET);assert(m.screen==MENU_PLAY);
 menu_update(&m,UI_START);assert(m.screen==MENU_PAUSE && m.selection==0);
 menu_update(&m,UI_DOWN);assert(menu_update(&m,UI_ACCEPT)&MENU_RESET);assert(m.screen==MENU_PLAY);
 menu_update(&m,UI_START);menu_update(&m,UI_DOWN);menu_update(&m,UI_DOWN);menu_update(&m,UI_ACCEPT);assert(m.screen==MENU_CONTROLS);
 menu_update(&m,UI_ACCEPT);assert(m.screen==MENU_PAUSE && m.selection==2);
 menu_update(&m,UI_DOWN);assert(menu_update(&m,UI_ACCEPT)&MENU_RESET);assert(m.screen==MENU_TITLE);
 menu_update(&m,UI_ACCEPT);menu_update(&m,UI_START);menu_update(&m,UI_BACK);assert(m.screen==MENU_PLAY);
 menu_update(&m,UI_START);menu_update(&m,UI_UP);assert(m.selection==5);
 int action=menu_update(&m,UI_ACCEPT);assert((action&(MENU_RESET|MENU_TRIAL))==(MENU_RESET|MENU_TRIAL) && m.screen==MENU_PLAY);
 return 0;
}
