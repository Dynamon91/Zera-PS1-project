#include <stddef.h>
#include <stdint.h>
#include "stream_world.h"
#include "world.h"
#include "surface.h"
#include "collision.h"
#include "player.h"
#define CELL 1280
static const StreamView *loaded;static int loaded_count,safety=-700;
void stream_world_bind(const StreamView *views,int count,int fall_limit){loaded=views;loaded_count=count;safety=fall_limit;}
int world_fall_limit(void){return safety;}
static int support(int x,int z,int limit,int above,int *height){
 int found=0,best=0;
 for(int n=0;n<loaded_count;n++){
  const StreamView *v=&loaded[n];int lx=x-v->center[0],lz=z-v->center[2];
  if(lx< -CELL/2 || lx>CELL/2 || lz< -CELL/2 || lz>CELL/2)continue;
  for(int i=0;i<v->count;i++){
   const StreamTriangle *t=&v->triangles[i];if(!above && !(t->flags&1))continue;
   int h;int ok=above?surface_ceiling(&t->v,1,lx,lz,limit-v->center[1],&h):surface_height(&t->v,1,lx,lz,limit-v->center[1],&h);
   if(!ok)continue;h+=v->center[1];
   if(!found || (above?h<best:h>best)){found=1;best=h;}
  }
 }
 if(found)*height=best;return found;
}
int world_floor(int x,int z,int ceiling,int *height){return support(x,z,ceiling,0,height);}
int world_ceiling(int x,int z,int minimum,int *height){return support(x,z,minimum,1,height);}
int world_height(int x,int z,int *height){return world_floor(x,z,0x3fffffff,height);}
void world_move(int oldx,int oldz,int *x,int *z,int feet){
 int dx=*x-oldx,dz=*z-oldz,max=dx<0?-dx:dx,t=dz<0?-dz:dz;if(t>max)max=t;
 int steps=(max+7)/8;if(steps<1)steps=1;if(steps>16)steps=16;
 int px=oldx,pz=oldz;
 for(int s=0;s<steps;s++){
  int ox=px,oz=pz;px+=dx*(s+1)/steps-dx*s/steps;pz+=dz*(s+1)/steps-dz*s/steps;
  for(int pass=0;pass<2;pass++)for(int n=0;n<loaded_count;n++){
   const StreamView *v=&loaded[n];int lx=px-v->center[0],lz=pz-v->center[2];
   if(lx< -CELL/2-24 || lx>CELL/2+24 || lz< -CELL/2-24 || lz>CELL/2+24)continue;
   for(int i=0;i<v->count;i++)if(v->triangles[i].flags&2)
    collision_triangle_push(&lx,&lz,ox-v->center[0],oz-v->center[2],feet-v->center[1],PLAYER_HEIGHT,24,v->triangles[i].v);
   px=lx+v->center[0];pz=lz+v->center[2];
  }
 }
 *x=px;*z=pz;
}
int world_camera_fraction(int x,int y,int z,int dx,int dy,int dz){
 int best=4096;
 for(int n=0;n<loaded_count;n++){
  const StreamView *v=&loaded[n];int lx=x-v->center[0],lz=z-v->center[2];
  if((lx< -CELL/2 && lx+dx< -CELL/2) || (lx>CELL/2 && lx+dx>CELL/2) ||
     (lz< -CELL/2 && lz+dz< -CELL/2) || (lz>CELL/2 && lz+dz>CELL/2))continue;
  for(int i=0;i<v->count;i++){
   const short *t=v->triangles[i].v;if(!(v->triangles[i].flags&2))continue;
   int a=0,b=3;int64_t longest=-1;short low=t[1],high=t[1];
   for(int k=0;k<3;k++){
    int j=(k+1)%3;int ex=t[k*3]-t[j*3],ez=t[k*3+2]-t[j*3+2];int64_t length=(int64_t)ex*ex+(int64_t)ez*ez;
    if(length>longest){longest=length;a=k*3;b=j*3;}
    if(t[k*3+1]<low)low=t[k*3+1];if(t[k*3+1]>high)high=t[k*3+1];
   }
   short wall[6]={t[a],t[a+2],t[b],t[b+2],low,high};
   int fraction=collision_ray(lx,y-v->center[1],lz,dx,dy,dz,wall);if(fraction<best)best=fraction;
  }
 }
 if(best<4096){best-=160;if(best<0)best=0;}return best;
}
