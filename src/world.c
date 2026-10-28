#include "world.h"
#include "world_height.h"
int world_fall_limit(void){
 static int ready=0,limit;
 if(!ready){
  int lowest=0;
  for(int z=0;z<WORLD_N;z++)for(int x=0;x<WORLD_N;x++){
   int height=world_heights[z][x];
   if(height!=-32768 && height<lowest)lowest=height;
  }
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
#include "world_walls.h"
void world_move(int oldx,int oldz,int *x,int *z,int feet){
 int dx=*x-oldx,dz=*z-oldz,max=dx<0?-dx:dx,t=dz<0?-dz:dz;if(t>max)max=t;
 int steps=(max+7)/8;if(steps<1)steps=1;if(steps>16)steps=16;
 int px=oldx,pz=oldz;
 for(int s=0;s<steps;s++){
  int ox=px,oz=pz;
  px+=dx*(s+1)/steps-dx*s/steps;pz+=dz*(s+1)/steps-dz*s/steps;
  for(int pass=0;pass<2;pass++)for(int i=0;i<WORLD_WALL_COUNT;i++)collision_push(&px,&pz,ox,oz,feet,120,24,world_walls[i]);
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
