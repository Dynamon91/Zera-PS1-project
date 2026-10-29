#include <assert.h>
#include <limits.h>
#include "../src/relics.h"
int main(void){
 Relics r;relics_clear(&r);Player p={0};
 p.x=-256*FP;p.y=1895*FP;p.z=786*FP;
 assert(!relics_update(&r,&p,0));assert(relics_update(&r,&p,1)==1);
 assert(r.mask==1 && r.count==1 && r.value==8);assert(!relics_update(&r,&p,1));
 p.y=73*FP;assert(!relics_update(&r,&p,1));
 p.x=678*FP;p.y=1895*FP;p.z=497*FP;assert(relics_update(&r,&p,1)==1);
 p.x=-141*FP;p.y=1895*FP;p.z=-804*FP;assert(!relics_update(&r,&p,1));
 p.y=74*FP;assert(relics_update(&r,&p,1)==1);assert(r.count==3 && r.value==20);
 p.x=INT_MAX;p.z=INT_MIN;assert(!relics_update(&r,&p,1));
 relics_clear(&r);assert(r.mask==0 && r.value==0 && r.count==0);
 return 0;
}
