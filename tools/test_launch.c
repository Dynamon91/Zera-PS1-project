#include <assert.h>
#include <limits.h>
#include <stdint.h>
#include "../src/launch.h"
#include "../src/world.h"
#include "../previews/launchpad/src/launch_config.h"
int main(void){
 Launch l={0};Player p;player_init(&p);
 assert(launch_can_start(&l,&p,&launch_config));
 p.x=INT_MAX;assert(!launch_begin(&l,&p,&launch_config));
 p.x=INT_MIN;assert(!launch_begin(&l,&p,&launch_config));
 player_init(&p);p.state=JUMP;assert(!launch_begin(&l,&p,&launch_config));
 player_init(&p);assert(launch_begin(&l,&p,&launch_config));
 assert(!launch_begin(&l,&p,&launch_config));
 int ticks=0,apex=p.y,descended=0;
 while(l.active){
  int done=launch_tick(&l,&p,&launch_config);ticks++;
  double u=l.time/65536.0;
  double expected=launch_config.start[1]+(launch_config.end[1]-launch_config.start[1])*u+launch_config.arc*u*(1-u);
  double error=p.y-expected;assert(error<2 && error> -2);
  if(p.y>apex)apex=p.y;
  if(p.vy<0)descended=1;
  assert(ticks<=38 && done==!l.active);
 }
 assert(ticks==38 && apex>launch_config.end[1] && descended);
 assert(l.completed==1 && l.started==1 && l.time==65536);
 assert(p.x==launch_config.end[0] && p.y==launch_config.end[1] && p.z==launch_config.end[2]);
 assert(!launch_tick(&l,&p,&launch_config));
 int h;assert(world_floor(p.x/FP,p.z/FP,p.y/FP+8,&h));
 assert(h==1895 && h*FP>=p.y-48*FP);p.y=h*FP;p.state=GROUND;
 int x=p.x,z=p.z;
 for(int i=0;i<120;i++){assert(!player_tick(&p,(Input){0}));assert(p.state==GROUND);}
 assert(p.x==x && p.z==z && p.y==1895*FP);
 assert(!launch_begin(&l,&p,&launch_config)); /* landing is outside trigger */
 player_init(&p);assert(launch_begin(&l,&p,&launch_config));
 for(int i=0;i<8;i++)launch_tick(&l,&p,&launch_config);
 launch_cancel(&l);player_init(&p);
 assert(!l.active && l.time==0 && l.cancelled==1 && l.completed==1);
 assert(!launch_tick(&l,&p,&launch_config));assert(p.x==0 && p.y==0 && p.z==0);
 assert(launch_begin(&l,&p,&launch_config));
 while(l.active)launch_tick(&l,&p,&launch_config);
 assert(l.started==3 && l.completed==2 && l.cancelled==1);
 /* Closed sphere boundary and component rejection before squared distance. */
 LaunchConfig c=launch_config;c.trigger[0]=c.trigger[1]=c.trigger[2]=0;c.radius=100;
 player_init(&p);p.x=100;assert(launch_can_start(&l,&p,&c));
 p.y=1;assert(!launch_can_start(&l,&p,&c));
 c.step=0;assert(!launch_can_start(&l,&p,&c));
 return 0;
}
