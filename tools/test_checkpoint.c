#include <assert.h>
#include <limits.h>
#include "../src/checkpoint.h"
#include "../src/world.h"
#include "../previews/checkpoint/src/checkpoint_config.h"
int main(void){
 Checkpoint c;checkpoint_clear(&c);Player p;player_init(&p);
 p.x=CHECKPOINT_ENTRY_X*FP;p.y=CHECKPOINT_ENTRY_Y*FP;p.z=CHECKPOINT_ENTRY_Z*FP;
 assert(!checkpoint_respawn(&c,&p) && p.x==CHECKPOINT_ENTRY_X*FP);
 assert(!checkpoint_update(&c,&checkpoint_config,&p,1));
 for(int i=0;i<80;i++){
  assert(!player_tick(&p,(Input){.x=1,.camera_c=4096}));
  checkpoint_update(&c,&checkpoint_config,&p,1);
 }
 assert(c.active==6752 && c.activations==1 && p.x>=300*FP && p.state==GROUND);
 p.vy=100*FP;p.dash_ticks=7;
 assert(checkpoint_respawn(&c,&p));
 assert(p.x==checkpoint_config.x*FP && p.y==checkpoint_config.y*FP && p.z==checkpoint_config.z*FP);
 assert(!p.vy && !p.dash_ticks && p.state==GROUND && c.yaw==1447 && c.activations==1);
 assert(!player_tick(&p,(Input){0}) && p.y==0);
 /* Automatic fall uses the same saved target, without clearing activation. */
 p.y=(world_fall_limit()-1)*FP;p.state=FALL;p.vy=-FP;
 assert(player_tick(&p,(Input){0}));assert(checkpoint_respawn(&c,&p));
 assert(p.x==0 && p.z==0 && c.active==6752 && c.activations==1);
 checkpoint_clear(&c);player_init(&p);
 assert(!checkpoint_update(&c,&checkpoint_config,&p,0));
 p.state=JUMP;assert(!checkpoint_update(&c,&checkpoint_config,&p,1));
 p.state=GROUND;p.x=INT_MAX;p.z=INT_MIN;
 assert(!checkpoint_update(&c,&checkpoint_config,&p,1));
 p.x=160*FP;p.z=0;assert(checkpoint_update(&c,&checkpoint_config,&p,1));
 assert(!checkpoint_update(&c,&checkpoint_config,&p,1) && c.activations==1);
 CheckpointConfig next={.id=9000,.x=-100,.y=20,.z=50,.yaw=1024,.trigger_x=160};
 assert(checkpoint_update(&c,&next,&p,1) && c.activations==2);
 assert(checkpoint_respawn(&c,&p) && p.x==-100*FP && p.y==20*FP && p.z==50*FP && c.yaw==1024);
 checkpoint_clear(&c);assert(!c.active && !c.activations && !checkpoint_respawn(&c,&p));
 return 0;
}
