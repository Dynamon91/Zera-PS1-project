#include "trial.h"
void trial_clear(Trial *t){t->collected=0;t->active=0;t->count=0;t->completed=0;t->ticks=0;}
void trial_start(Trial *t){trial_clear(t);t->active=1;}
int trial_update(Trial *t,const Player *p,int active){
 if(!active || !t->active || t->completed)return 0;
 t->ticks++;int found=0;
 for(int i=0;i<TRIAL_PICKUPS;i++){
  if(t->collected&(1u<<i))continue;
  int dx=p->x/FP-trial_positions[i][0],dz=p->z/FP-trial_positions[i][2],dy=p->y/FP+60-trial_positions[i][1];
  if(dy<-90 || dy>90)continue;
  if((int64_t)dx*dx+(int64_t)dz*dz>44*44)continue;
  t->collected|=1u<<i;t->count++;found++;
 }
 if(t->count==TRIAL_PICKUPS)t->completed=1;
 return found;
}
