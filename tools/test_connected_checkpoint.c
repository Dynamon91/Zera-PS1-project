#include <assert.h>
#include <stdlib.h>
#include "../src/checkpoint.h"
#include "../src/relics.h"
#include "../src/world.h"
#include "../previews/level3/src/checkpoint_config.h"
int main(void){
 Player p;player_init(&p);Relics r;relics_clear(&r);Checkpoint c;checkpoint_clear(&c);
 int j1=0,j2=0,j3=0,j4=0,phase=0;
 for(int i=0;i<2200 && !c.active;i++){
  int x=p.x/FP,z=p.z/FP,tx=1356,tz=-7101;Input in={.camera_c=4096};
  if(r.count<2){
   tx=r.count?(z> -5700?-49:-980):(z> -3200?400:-49);tz=r.count?-6473:-3794;
   if(z<=-1400)in.x=x<tx-10?1:x>tx+10?-1:0;
   in.z=z>tz?-1:0;
   if(!r.count){if(z<=-2100 && !j1 && p.state==GROUND){in.jump_pressed=1;j1=1;}in.jump_held=j1;}
   else{if(z<=-6300 && !j2 && p.state==GROUND){in.jump_pressed=1;j2=1;}in.jump_held=j2;}
  }else{
   if(phase==0){tx=0;tz=-6473;if(abs(x)<20 && abs(z+6473)<20)phase=1;}
   else if(phase==1){tx=0;tz=-5000;if(abs(z+5000)<20)phase=2;}
   else if(phase==2){tx=1000;tz=-5000;if(x>=350 && !j3 && p.state==GROUND){in.jump_pressed=1;j3=1;}if(abs(x-1000)<20)phase=3;}
   else if(phase==3){tx=1000;tz=-7101;if(z<=-6200 && !j4 && p.state==GROUND){in.jump_pressed=1;j4=1;}if(abs(z+7101)<20)phase=4;}
   in.x=x<tx-10?1:x>tx+10?-1:0;in.z=z<tz-10?1:z>tz+10?-1:0;
  }
  assert(!player_tick(&p,in));relics_update(&r,&p,1);checkpoint_update(&c,&checkpoint_config,&p,1);
 }
 assert(c.active==6752 && c.activations==1 && j1 && j2 && j3 && j4);
 assert(r.count==2 && r.mask==3 && r.value==17);
 assert(checkpoint_respawn(&c,&p));assert(p.x==1356*FP && p.y==-115*FP && p.z==-7101*FP && c.yaw==1447);
 assert(!player_tick(&p,(Input){0}) && p.y==-113*FP);
 assert(r.value==17 && r.mask==3);
 p.y=(world_fall_limit()-1)*FP;p.state=FALL;p.vy=-FP;
 assert(player_tick(&p,(Input){0}) && checkpoint_respawn(&c,&p));
 assert(p.x==1356*FP && p.z==-7101*FP && r.value==17 && c.activations==1);
 checkpoint_clear(&c);relics_clear(&r);player_init(&p);assert(!c.active && !r.mask && p.x==0 && p.z==0);
 return 0;
}
