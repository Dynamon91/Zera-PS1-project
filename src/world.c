#include "world.h"
#include "player.h"
#ifdef ZERA_LEVEL3_PREVIEW
#include "surface.h"
#ifdef ZERA_CHECKPOINT_PREVIEW
#include "../previews/checkpoint/src/world_floors.h"
#elif defined(ZERA_LAUNCH_PREVIEW)
#include "../previews/launchpad/src/world_floors.h"
#else
#include "../previews/level3/src/world_floors.h"
#endif
#endif
#ifdef ZERA_LEVEL3_PREVIEW
#ifdef ZERA_CHECKPOINT_PREVIEW
#include "../previews/checkpoint/src/world_height.h"
#elif defined(ZERA_LAUNCH_PREVIEW)
#include "../previews/launchpad/src/world_height.h"
#else
#include "../previews/level3/src/world_height.h"
#endif
#else
#include "world_height.h"
#endif
int world_fall_limit(void){
 static int ready=0,limit;
 if(!ready){
  int lowest=0;
  for(int z=0;z<WORLD_N;z++)for(int x=0;x<WORLD_N;x++){
   int height=world_heights[z][x];
   if(height!=-32768 && height<lowest)lowest=height;
  }
#ifdef ZERA_LEVEL3_PREVIEW
  for(int i=0;i<WORLD_FLOOR_COUNT;i++)for(int k=1;k<9;k+=3)if(world_floors[i][k]<lowest)lowest=world_floors[i][k];
#endif
  limit=lowest-700;ready=1;
 }
 return limit;
}
int world_height(int x,int z,int *height){
 x-=WORLD_ORIGIN;z-=WORLD_ORIGIN;
 if(x<0 || z<0 || x>=(WORLD_N-1)*WORLD_STEP || z>=(WORLD_N-1)*WORLD_STEP)return 0;
 int ix=x/WORLD_STEP,iz=z/WORLD_STEP,fx=x%WORLD_STEP,fz=z%WORLD_STEP;
 int a=world_heights[iz][ix],b=world_heights[iz][ix+1],c=world_heights[iz+1][ix],d=world_heights[iz+1][ix+1];
 if(fx+fz<=WORLD_STEP){
  if(a==-32768 || b==-32768 || c==-32768)return 0;
  *height=a+((b-a)*fx+(c-a)*fz)/WORLD_STEP;
 }else{
  if(b==-32768 || c==-32768 || d==-32768)return 0;
  *height=d+((c-d)*(WORLD_STEP-fx)+(b-d)*(WORLD_STEP-fz))/WORLD_STEP;
 }
 return 1;
}
#include "collision.h"
#ifdef ZERA_LEVEL3_PREVIEW
#ifdef ZERA_CHECKPOINT_PREVIEW
#include "../previews/checkpoint/src/world_wall_triangles.h"
#elif defined(ZERA_LAUNCH_PREVIEW)
#include "../previews/launchpad/src/world_wall_triangles.h"
#else
#include "../previews/level3/src/world_wall_triangles.h"
#endif
#endif
#ifdef ZERA_LEVEL3_PREVIEW
#ifdef ZERA_CHECKPOINT_PREVIEW
#include "../previews/checkpoint/src/world_walls.h"
#elif defined(ZERA_LAUNCH_PREVIEW)
#include "../previews/launchpad/src/world_walls.h"
#else
#include "../previews/level3/src/world_walls.h"
#endif
#else
#include "world_walls.h"
#endif
void world_move(int oldx,int oldz,int *x,int *z,int feet){
 int dx=*x-oldx,dz=*z-oldz,max=dx<0?-dx:dx,t=dz<0?-dz:dz;if(t>max)max=t;
 int steps=(max+7)/8;if(steps<1)steps=1;if(steps>16)steps=16;
 int px=oldx,pz=oldz;
 for(int s=0;s<steps;s++){
  int ox=px,oz=pz;
  px+=dx*(s+1)/steps-dx*s/steps;pz+=dz*(s+1)/steps-dz*s/steps;
  for(int pass=0;pass<2;pass++){
#ifdef ZERA_LEVEL3_PREVIEW
   for(int i=0;i<WORLD_WALL_TRIANGLE_COUNT;i++)collision_triangle_push(&px,&pz,ox,oz,feet,PLAYER_HEIGHT,24,world_wall_triangles[i]);
#else
   for(int i=0;i<WORLD_WALL_COUNT;i++)collision_push(&px,&pz,ox,oz,feet,PLAYER_HEIGHT,24,world_walls[i]);
#endif
  }
 }
 *x=px;*z=pz;
}
int world_camera_fraction(int x,int y,int z,int dx,int dy,int dz){
 int best=4096;
 for(int i=0;i<WORLD_WALL_COUNT;i++){
  int t=collision_ray(x,y,z,dx,dy,dz,world_walls[i]);if(t<best)best=t;
 }
 /* Keep a small clearance before the intersected proxy. */
 if(best<4096){best-=160;if(best<0)best=0;}
 return best;
}

int world_floor(int x,int z,int ceiling,int *height){
#ifdef ZERA_LEVEL3_PREVIEW
 if(x<WORLD_ORIGIN || z<WORLD_ORIGIN || x>=-WORLD_ORIGIN || z>=-WORLD_ORIGIN)return 0;
 return surface_height(world_floors,WORLD_FLOOR_COUNT,x,z,ceiling,height);
#else
 (void)ceiling;return world_height(x,z,height);
#endif
}
int world_ceiling(int x,int z,int minimum,int *height){
#ifdef ZERA_LEVEL3_PREVIEW
 if(x<WORLD_ORIGIN || z<WORLD_ORIGIN || x>=-WORLD_ORIGIN || z>=-WORLD_ORIGIN)return 0;
 return surface_ceiling(world_floors,WORLD_FLOOR_COUNT,x,z,minimum,height);
#else
 (void)x;(void)z;(void)minimum;(void)height;return 0;
#endif
}
