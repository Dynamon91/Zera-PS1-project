#include <stdint.h>
#include "clip.h"
static int plane(const ClipCamera *c,const ClipVertex *v,int p){
 int z=(c->m[2][0]*v->x+c->m[2][1]*v->y+c->m[2][2]*v->z)/4096+c->t[2];
 if(p==0)return z-96;
 if(p<=2){
  int x=(c->m[0][0]*v->x+c->m[0][1]*v->y+c->m[0][2]*v->z)/4096+c->t[0];
  return p==1?x*256+z*192:z*192-x*256;
 }
 int y=(c->m[1][0]*v->x+c->m[1][1]*v->y+c->m[1][2]*v->z)/4096+c->t[1];
 return p==3?y*256+z*142:z*162-y*256;
}
unsigned int clip_code(const ClipCamera *c,const ClipVertex *v){
 int x=(c->m[0][0]*v->x+c->m[0][1]*v->y+c->m[0][2]*v->z)/4096+c->t[0];
 int y=(c->m[1][0]*v->x+c->m[1][1]*v->y+c->m[1][2]*v->z)/4096+c->t[1];
 int z=(c->m[2][0]*v->x+c->m[2][1]*v->y+c->m[2][2]*v->z)/4096+c->t[2];
 unsigned int out=0;if(z<96)out|=1;if(x*256+z*192<0)out|=2;if(z*192-x*256<0)out|=4;if(y*256+z*142<0)out|=8;if(z*162-y*256<0)out|=16;return out;
}
static ClipVertex intersect(ClipVertex a,ClipVertex b,int da,int db){
 int f=(int64_t)da*4096/(da-db);ClipVertex v;
 v.x=a.x+(int64_t)(b.x-a.x)*f/4096;v.y=a.y+(int64_t)(b.y-a.y)*f/4096;v.z=a.z+(int64_t)(b.z-a.z)*f/4096;
 v.u=a.u+(int64_t)(b.u-a.u)*f/4096;v.v=a.v+(int64_t)(b.v-a.v)*f/4096;return v;
}
int clip_triangle_known(const ClipCamera *c,const ClipVertex in[3],const unsigned int codes[3],ClipVertex out[10]){
 unsigned int a=codes[0],b=codes[1],d=codes[2],mask=a|b|d;
 if(a&b&d)return 0;
 if(!mask){for(int i=0;i<3;i++)out[i]=in[i];return 3;}
 ClipVertex buffers[2][10];int n=3,active=0;
 for(int i=0;i<3;i++)buffers[0][i]=in[i];
 for(int p=0;p<5;p++){
  if(!(mask&(1u<<p)))continue;
  int count=0;ClipVertex *src=buffers[active],*dst=buffers[active^1];
  /* Adjacent edges share endpoints. Keep each signed distance instead of
     transforming both endpoints again for every edge. Preserve world-space
     interpolation and integer rounding exactly. */
  int first=plane(c,&src[0],p),da=first;
  for(int i=0;i<n;i++){
   ClipVertex a=src[i],b=src[(i+1)%n];
   int db=i+1<n?plane(c,&b,p):first;
   if(da>=0){if(count>=10)return 0;dst[count++]=a;}
   if((da>=0)!=(db>=0)){if(count>=10)return 0;dst[count++]=intersect(a,b,da,db);}
   da=db;
  }
  n=count;active^=1;if(!n)return 0;
 }
 for(int i=0;i<n;i++)out[i]=buffers[active][i];
 return n;
}

int clip_triangle(const ClipCamera *c,const ClipVertex in[3],ClipVertex out[10]){
 unsigned int codes[3]={clip_code(c,&in[0]),clip_code(c,&in[1]),clip_code(c,&in[2])};
 return clip_triangle_known(c,in,codes,out);
}
