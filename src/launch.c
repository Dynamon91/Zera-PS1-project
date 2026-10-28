#include <stdint.h>
#include "launch.h"
int launch_can_start(const Launch *l,const Player *p,const LaunchConfig *c){
 if(l->active || p->state!=GROUND || c->step<=0 || c->step>65536 || c->radius<=0 || c->radius>32767*FP)return 0;
 int64_t dx=(int64_t)p->x-c->trigger[0],dy=(int64_t)p->y-c->trigger[1],dz=(int64_t)p->z-c->trigger[2];
 if(dx>c->radius || dx< -c->radius || dy>c->radius || dy< -c->radius || dz>c->radius || dz< -c->radius)return 0;
 return dx*dx+dy*dy+dz*dz<=(int64_t)c->radius*c->radius;
}
int launch_begin(Launch *l,Player *p,const LaunchConfig *c){
 if(!launch_can_start(l,p,c))return 0;
 l->active=1;l->time=0;l->started++;
 p->x=c->start[0];p->y=c->start[1];p->z=c->start[2];p->vy=0;p->dash_ticks=0;p->state=JUMP;
 return 1;
}
int launch_tick(Launch *l,Player *p,const LaunchConfig *c){
 if(!l->active)return 0;
 int u=l->time+c->step;if(u>65536)u=65536;
 int oldy=p->y;
 p->x=c->start[0]+((int64_t)c->end[0]-c->start[0])*u/65536;
 p->z=c->start[2]+((int64_t)c->end[2]-c->start[2])*u/65536;
 p->y=c->start[1]+((int64_t)c->end[1]-c->start[1])*u/65536+
       (int64_t)c->arc*u*(65536-u)/INT64_C(4294967296);
 p->vy=p->y-oldy;p->state=p->vy>0?JUMP:FALL;l->time=u;
 if(u==65536){l->active=0;l->completed++;p->vy=0;p->state=FALL;return 1;}
 return 0;
}
void launch_cancel(Launch *l){if(l->active)l->cancelled++;l->active=0;l->time=0;}
