#include <assert.h>
#include "../src/world.h"
#include "../src/world_walls.h"
#include "../src/camera.h"
int main(void){
 int h=123;assert(world_height(0,0,&h) && h==0);
 assert(!world_height(-5000,0,&h));assert(!world_height(0,5000,&h));
 int x=0,z=0;
 for(int n=0;n<1000;n++){int ox=x,oz=z;x+=7;z+=7;world_move(ox,oz,&x,&z,-38);}
 assert(x>0 && x<1000 && z>0 && z<1000);
 for(int n=0;n<20;n++){int nx=x+7,nz=z+7;world_move(x,z,&nx,&nz,-38);assert(nx==x && nz==z);}
 assert(world_camera_fraction(0,80,0,0,0,0)==4096);
 /* Close-proxy pullback must respect the world query, below the old floor.
    Use actual recovered proxies so this checks world/camera integration. */
 int close_cases=0;
 for(int i=0;i<WORLD_WALL_COUNT;i++){
  const short *w=world_walls[i];
  int mx=(w[0]+w[2])/2,mz=(w[1]+w[3])/2,my=(w[4]+w[5])/2;
  int fraction=world_camera_fraction(mx-100,my,mz,200,0,0);
  if(fraction<2000){
   int distance=camera_distance_step(CAMERA_DISTANCE,fraction,0);
   assert(distance==CAMERA_DISTANCE*fraction/4096);
   assert(distance<420);
   close_cases++;
  }
 }
 assert(close_cases>300);
 return 0;
}
