#include <assert.h>
#include "../src/relics.h"
#include "../src/world.h"
int main(void){
 Relics r;relics_clear(&r);Player p;player_init(&p);int jumped=0,saw_glide=0;
 for(int i=0;i<650 && !r.count;i++){
  int x=p.x/FP,z=p.z/FP;int target=z> -3200?400:-49;
  Input in={.z=z> -3794?-1:0,.camera_c=4096};
  if(z<=-1400)in.x=x<target-10?1:x>target+10?-1:0;
  if(z<=-2100 && !jumped && p.state==GROUND){in.jump_pressed=1;jumped=1;}
  in.jump_held=jumped;
  assert(!player_tick(&p,in));saw_glide|=p.state==GLIDE;
  relics_update(&r,&p,1);
 }
 assert(jumped && saw_glide && r.mask==1 && r.count==1 && r.value==1);
 assert(p.z/FP< -3700 && p.y/FP<0);
 assert(!relics_update(&r,&p,1));
 int jump2=0;
 for(int i=0;i<700 && r.count<2;i++){
  int x=p.x/FP,z=p.z/FP,target=z> -5700?-49:-980;
  Input in={.x=x<target-10?1:x>target+10?-1:0,.z=z> -6473?-1:0,.camera_c=4096};
  if(z<=-6300 && !jump2 && p.state==GROUND){in.jump_pressed=1;jump2=1;}
  in.jump_held=jump2;assert(!player_tick(&p,in));relics_update(&r,&p,1);
 }
 assert(jump2 && r.mask==3 && r.count==2 && r.value==17);
 assert(!relics_update(&r,&p,1));
 player_init(&p);assert(r.count==2 && r.value==17); /* Respawn preserves both. */
 relics_clear(&r);assert(!r.count && !r.mask && !r.value);
 p.x=relic_positions[0][0]*FP;p.y=(relic_positions[0][1]-32)*FP;p.z=relic_positions[0][2]*FP;
 assert(!relics_update(&r,&p,0) && !r.count);assert(relics_update(&r,&p,1)==1);
 return 0;
}
