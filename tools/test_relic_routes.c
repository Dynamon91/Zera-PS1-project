#include <assert.h>
#include "../src/player.h"
#include "../src/world.h"
#include "../src/launch.h"
#include "../src/relics.h"
#include "../previews/launchpad/src/launch_config.h"
int main(void){
 Relics r;relics_clear(&r);Launch l={0};Player p;
 for(int phase=0;phase<3;phase++){
  player_init(&p);
  if(phase<2){
   assert(launch_begin(&l,&p,&launch_config));
   while(l.active)launch_tick(&l,&p,&launch_config);
   int h;assert(world_floor(p.x/FP,p.z/FP,p.y/FP+8,&h));p.y=h*FP;p.state=GROUND;
  }
  int targetx=relic_positions[phase][0],targetz=relic_positions[phase][2],jumped=0;
  for(int n=0;n<250 && !(r.mask&(1<<phase));n++){
   int dx=targetx-p.x/FP,dz=targetz-p.z/FP;
   Input in={.x=dx>12?1:dx< -12?-1:0,.z=dz>12?1:dz< -12?-1:0,.camera_c=4096};
   if(phase==2){in.jump_held=1;if(p.z/FP< -430 && !jumped){in.jump_pressed=1;jumped=1;}}
   assert(!player_tick(&p,in));relics_update(&r,&p,1);
   if(phase<2)assert(p.state==GROUND);
  }
  assert(r.mask&(1<<phase));assert(r.count==phase+1);
  if(phase==2)assert(jumped);
 }
 assert(r.mask==7 && r.value==20 && l.completed==2);
 player_init(&p);assert(r.value==20); /* Respawn preserves session state. */
 return 0;
}
