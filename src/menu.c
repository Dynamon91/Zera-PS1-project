#include "menu.h"
void menu_init(Menu *m){m->screen=MENU_TITLE;m->selection=0;m->return_to=MENU_TITLE;m->debug=0;}
int menu_update(Menu *m,unsigned p){
 if(m->screen==MENU_CONTROLS){
  if(p&(UI_ACCEPT|UI_BACK|UI_START))m->screen=m->return_to;
  return 0;
 }
 if(m->screen==MENU_PLAY){
  if(p&UI_START){m->screen=MENU_PAUSE;m->selection=0;}
  return 0;
 }
 if(m->screen==MENU_PAUSE && (p&(UI_BACK|UI_START))){m->screen=MENU_PLAY;return 0;}
 int count=m->screen==MENU_TITLE?3:6;
 if(p&UI_UP)m->selection=(m->selection+count-1)%count;
 if(p&UI_DOWN)m->selection=(m->selection+1)%count;
 if(m->screen==MENU_TITLE && (p&UI_START))p|=UI_ACCEPT;
 if(!(p&UI_ACCEPT))return 0;
 if(m->screen==MENU_TITLE){
  switch(m->selection){
   case 0:m->screen=MENU_PLAY;return MENU_RESET;
   case 1:m->return_to=MENU_TITLE;m->screen=MENU_CONTROLS;break;
   default:m->debug=!m->debug;break;
  }
 }else{
  switch(m->selection){
   case 0:m->screen=MENU_PLAY;break;
   case 1:m->screen=MENU_PLAY;return MENU_RESET;
   case 2:m->return_to=MENU_PAUSE;m->screen=MENU_CONTROLS;break;
   case 3:m->screen=MENU_TITLE;m->selection=0;return MENU_RESET;
   case 4:m->debug=!m->debug;break;
   default:m->screen=MENU_PLAY;return MENU_RESET|MENU_TRIAL;
  }
 }
 return 0;
}
