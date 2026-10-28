#ifndef MENU_H
#define MENU_H
enum {MENU_TITLE,MENU_PLAY,MENU_PAUSE,MENU_CONTROLS};
enum {UI_UP=1,UI_DOWN=2,UI_ACCEPT=4,UI_BACK=8,UI_START=16};
enum {MENU_RESET=1,MENU_TRIAL=2};
typedef struct {int screen,selection,return_to,debug,muted;} Menu;
void menu_init(Menu *m);
int menu_update(Menu *m,unsigned pressed);
#endif
