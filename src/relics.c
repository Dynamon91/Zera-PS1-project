#include <stdint.h>
#include "relics.h"
void relics_clear(Relics *r){r->mask=r->count=r->value=0;}
int relics_update(Relics *r,const Player *p,int active){
 if(!active)return 0;
 int found=0;
 for(int i=0;i<RELIC_COUNT;i++){
  if(r->mask&(1<<i))continue;
  int64_t dx=(int64_t)p->x/FP-relic_positions[i][0],dz=(int64_t)p->z/FP-relic_positions[i][2];
  int64_t dy=(int64_t)p->y/FP+32-relic_positions[i][1];
  if(dy< -64 || dy>64 || dx< -44 || dx>44 || dz< -44 || dz>44 || dx*dx+dz*dz>44*44)continue;
  r->mask|=1<<i;r->count++;r->value+=relic_values[i];found++;
 }
 return found;
}
