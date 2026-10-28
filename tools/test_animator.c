#include <assert.h>
#include <string.h>
#include "../src/animator.h"
static Animator a,b;
int main(void){
 animator_init(&a);b=a;animator_update(&a,3,0);assert(!memcmp(&a,&b,sizeof(a)));
 animator_update(&a,1,1);assert(a.clip==1 && a.blend_tick==1);
 int changed=memcmp(a.local,b.local,sizeof(a.local));assert(changed);
 b=a;animator_update(&a,3,0);assert(!memcmp(&a,&b,sizeof(a)));
 animator_update(&a,3,1);assert(a.clip==3 && a.blend_tick==1);
 for(int i=0;i<5;i++)animator_update(&a,3,1);
 assert(a.blend_tick==ANIM_BLEND_TICKS);
 for(int i=0;i<1000;i++)animator_update(&a,2,1);
 b=a;animator_update(&a,2,1);assert(!memcmp(a.local,b.local,sizeof(a.local)));
 animator_init(&a);
 for(int i=0;i<1000;i++){animator_update(&a,(i/13)%4,1);for(int j=0;j<ANIM_VERTICES;j++){assert(a.local[j].x>-1000 && a.local[j].x<1000);assert(a.local[j].y>-1000 && a.local[j].y<1000);assert(a.local[j].z>-1000 && a.local[j].z<1000);}}
 return 0;
}
