#include "player.h"
#include "world.h"
void player_init(Player *p){p->x=p->y=p->z=p->vy=p->dash_ticks=0;p->state=GROUND;}
/* Provisional tuning at 30 Hz, not recovered original constants. */
void player_tick(Player *p,Input i){
 int speed=10*FP,ox=p->x,oz=p->z,oy=p->y;
 if(i.jump_pressed && p->state==GROUND){p->vy=18*FP;p->state=JUMP;}
 if(i.dash_pressed && !p->dash_ticks)p->dash_ticks=8;
 if(p->dash_ticks){speed=24*FP;p->dash_ticks--;}
 if(i.x && i.z)speed=speed*181/256;
 int c=i.camera_c,s=i.camera_s;if(!c && !s)c=4096;
 p->x+=(i.x*speed*c-i.z*speed*s)/4096;
 p->z+=(i.x*speed*s+i.z*speed*c)/4096;
 int wx=p->x/FP,wz=p->z/FP,tx=wx,tz=wz;
 world_move(ox/FP,oz/FP,&wx,&wz,oy/FP);
 if(wx!=tx)p->x=wx*FP;
 if(wz!=tz)p->z=wz*FP;
 int height=0,hasfloor=world_height(p->x/FP,p->z/FP,&height);height*=FP;
 /* Heightfield columns prevent stepping into a rise taller than 48 units. */
 if(hasfloor && height>oy+48*FP){
  p->x=ox;p->z=oz;height=0;hasfloor=world_height(ox/FP,oz/FP,&height);height*=FP;
 }
 if(p->state==GROUND){
  if(hasfloor && height>=oy-24*FP){p->y=height;p->vy=0;}
  else p->state=FALL;
 }
 if(p->state!=GROUND){
  p->vy-=FP;
  if(i.jump_held && p->vy<0){if(p->vy < -3*FP)p->vy=-3*FP;p->state=GLIDE;}
  else p->state=p->vy>0?JUMP:FALL;
  p->y+=p->vy;
  if(hasfloor && p->vy<=0 && oy>=height-8*FP && p->y<=height){p->y=height;p->vy=0;p->state=GROUND;}
 }
 if(p->y < -700*FP)player_init(p);
}
