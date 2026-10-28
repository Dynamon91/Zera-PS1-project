#include <assert.h>
#include "../src/player.h"
#include "../src/world.h"
#include "../src/menu.h"
int main(void){
 int height=99;assert(world_height(0,0,&height) && height==0);
 for(int direction=0;direction<4;direction++){
  Player p;player_init(&p);Input in={0};in.camera_c=4096;
  in.x=direction==0?1:direction==1?-1:0;
  in.z=direction==2?1:direction==3?-1:0;
  for(int k=0;k<50;k++)assert(!player_tick(&p,in));
  assert(p.state==GROUND);
  assert(world_height(p.x/FP,p.z/FP,&height) && p.y==height*FP);
  assert(p.x/FP==in.x*500 && p.z/FP==in.z*500);
 }
 Menu m;menu_init(&m);assert(menu_update(&m,UI_ACCEPT)==MENU_RESET);
 menu_update(&m,UI_START);menu_update(&m,UI_UP);
 assert(m.screen==MENU_PAUSE && m.selection==5);
 assert(menu_update(&m,UI_ACCEPT)==0 && m.muted);
 return 0;
}
