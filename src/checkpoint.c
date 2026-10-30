#include <stdint.h>
#include "checkpoint.h"
void checkpoint_clear(Checkpoint *c){*c=(Checkpoint){0};}
int checkpoint_update(Checkpoint *c,const CheckpointConfig *config,const Player *p,int enabled){
 if(!enabled || p->state!=GROUND || c->active==config->id)return 0;
 int64_t dx=(int64_t)p->x/FP-config->trigger_x,dz=(int64_t)p->z/FP-config->trigger_z;
 int64_t dy=(int64_t)p->y/FP-config->trigger_y;
 if(dx< -160 || dx>160 || dz< -160 || dz>160 || dy< -80 || dy>80 || dx*dx+dz*dz>160*160)return 0;
 c->active=config->id;c->x=config->x;c->y=config->y;c->z=config->z;c->yaw=config->yaw;c->activations++;
 return 1;
}
int checkpoint_respawn(const Checkpoint *c,Player *p){
 if(!c->active)return 0;
 player_init(p);p->x=c->x*FP;p->y=c->y*FP;p->z=c->z*FP;
 return 1;
}
