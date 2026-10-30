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
  assert(world_floor(p.x/FP,p.z/FP,p.y/FP+48,&height) && p.y==height*FP);
  assert(p.x/FP==in.x*500 && p.z/FP==in.z*500);
 }
 /* Actual recovered overlap: the legacy grid chooses the upper surface,
    while support selection keeps a player below it on the lower floor. */
 int lower,upper;
 assert(world_floor(360,-440,48,&lower) && lower==0);
 assert(world_floor(360,-440,300,&upper) && upper==266);
 assert(world_height(360,-440,&height) && height>200);
 assert(world_floor(550,0,48,&lower) && lower==0);
 assert(world_floor(550,0,300,&upper) && upper==261);
 Player under;player_init(&under);
 for(int i=0;i<50;i++)assert(!player_tick(&under,(Input){.x=1,.camera_c=4096}));
 assert(under.x==500*FP && under.z==0 && under.y==0 && under.state==GROUND);
 /* Original wall slopes from X=574 at Y=0 to X=547 at Y=265.
    The body-height slice reaches X=562, rather than the old full-height 547. */
 Player wall;player_init(&wall);
 for(int i=0;i<150;i++)assert(!player_tick(&wall,(Input){.x=1,.camera_c=4096}));
 assert(wall.x/FP>=537 && wall.x/FP<=538 && wall.z==0 && wall.y==0 && wall.state==GROUND);
 /* Jump under an actual recovered overhead collider and land below it. */
 int roof;
 assert(world_ceiling(550,0,PLAYER_HEIGHT,&roof) && roof==261);
 assert(!world_ceiling(99999,0,0,&roof));
 /* X=550 is inside the actual sloped wall. It is a query fixture, not a
    valid starting point for the player head-sweep test (covered separately). */
 Menu m;menu_init(&m);assert(menu_update(&m,UI_ACCEPT)==MENU_RESET);
 /* Walk the recovered corridor beyond the former -1280 boundary. */
 Player corridor;player_init(&corridor);
 for(int i=0;i<200;i++)assert(!player_tick(&corridor,(Input){.z=-1,.camera_c=4096}));
 assert(corridor.x==0 && corridor.z==-2000*FP && corridor.state==GROUND);
 assert(world_floor(0,-2000,corridor.y/FP+48,&height) && corridor.y==height*FP);
 menu_update(&m,UI_START);menu_update(&m,UI_UP);
 assert(m.screen==MENU_PAUSE && m.selection==5);
 assert(menu_update(&m,UI_ACCEPT)==0 && m.muted);
 return 0;
}
