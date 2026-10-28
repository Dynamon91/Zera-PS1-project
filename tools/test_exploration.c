#include <assert.h>
#include "../src/player.h"
#include "../src/world.h"
int main(void){
 Player p;player_init(&p);
 /* Default 45-degree camera: Right+Down walks toward world +X.
    This source-ground route was outside the old +/-1280 patch. */
 for(int tick=0;tick<600;tick++){
  int moving=p.x/FP<2200;
  Input i={.x=moving,.z=-moving,.camera_c=2896,.camera_s=2896};
  assert(!player_tick(&p,i));
 }
 int height;
 assert(p.x/FP>=2200 && p.x/FP<2560 && p.z==0);
 assert(p.state==GROUND && world_height(p.x/FP,p.z/FP,&height));
 assert(p.y==height*FP);
 return 0;
}
