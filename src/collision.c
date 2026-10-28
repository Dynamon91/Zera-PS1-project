#include <stdint.h>
#include "collision.h"
static int root(unsigned int n){
 unsigned int x=0,bit=1u<<30;
 while(bit>n)bit>>=2;
 while(bit){if(n>=x+bit){n-=x+bit;x=(x>>1)+bit;}else x>>=1;bit>>=2;}
 return (int)x;
}
int collision_push(int *x,int *z,int ox,int oz,int feet,int height,int radius,const short w[6]){
 if(feet+height<=w[4] || feet+8>=w[5])return 0;
 int minx=w[0]<w[2]?w[0]:w[2],maxx=w[0]>w[2]?w[0]:w[2];
 int minz=w[1]<w[3]?w[1]:w[3],maxz=w[1]>w[3]?w[1]:w[3];
 if(*x<minx-radius || *x>maxx+radius || *z<minz-radius || *z>maxz+radius)return 0;
 int dx=w[2]-w[0],dz=w[3]-w[1];int64_t len=(int64_t)dx*dx+(int64_t)dz*dz;
 if(!len)return 0;
 int64_t dot=(int64_t)(*x-w[0])*dx+(int64_t)(*z-w[1])*dz;
 if(dot<0)dot=0;
 if(dot>len)dot=len;
 int cx=w[0]+dot*dx/len,cz=w[1]+dot*dz/len;
 int nx=*x-cx,nz=*z-cz,dist2=nx*nx+nz*nz;
 if(dist2>=radius*radius)return 0;
 if(!dist2){
  int side=((int64_t)(ox-w[0])*(-dz)+(int64_t)(oz-w[1])*dx)>=0?1:-1;
  int length=root((unsigned)len);if(!length)return 0;
  *x=cx+side*(-dz)*(radius+1)/length;*z=cz+side*dx*(radius+1)/length;
 }else{
  int dist=root(dist2);if(!dist)dist=1;
  *x=cx+nx*(radius+1)/dist;*z=cz+nz*(radius+1)/dist;
 }
 return 1;
}
/* Intersect a Q12 parameter interval with one closed coordinate slab. */
static int ray_slab(int start,int delta,int low,int high,int *enter,int *exit){
 if(!delta)return start>=low && start<=high;
 int64_t d=delta,a=(int64_t)low-start,b=(int64_t)high-start;
 if(d<0){d=-d;int64_t tmp=a;a=-b;b=-tmp;}
 a*=4096;b*=4096;
 /* C division truncates toward zero; round entry up and exit down. */
 int64_t first=a/d+(a%d>0),last=b/d-(b%d<0);
 if(first>*exit || last<*enter)return 0;
 if(first>*enter)*enter=(int)first;
 if(last<*exit)*exit=(int)last;
 return *enter<=*exit;
}
/* Return Q12 fraction of a segment crossing inside the wall's vertical span. */
int collision_ray(int x,int y,int z,int dx,int dy,int dz,const short w[6]){
 int sx=w[2]-w[0],sz=w[3]-w[1];
 int64_t den=(int64_t)dx*sz-(int64_t)dz*sx;
 if(!den){
  /* Parallel rays can still overlap the wall. Include vertical rays whose
     X/Z projection is a point on the segment; reject separate parallel lines. */
  if((int64_t)(x-w[0])*sz-(int64_t)(z-w[1])*sx)return 4096;
  int enter=0,exit=4096;
  int minx=w[0]<w[2]?w[0]:w[2],maxx=w[0]>w[2]?w[0]:w[2];
  int minz=w[1]<w[3]?w[1]:w[3],maxz=w[1]>w[3]?w[1]:w[3];
  if(!ray_slab(x,dx,minx,maxx,&enter,&exit) ||
     !ray_slab(z,dz,minz,maxz,&enter,&exit) ||
     !ray_slab(y,dy,w[4]-16,w[5]+16,&enter,&exit))return 4096;
  return enter;
 }
 int ax=w[0]-x,az=w[1]-z;
 int64_t t=(int64_t)ax*sz-(int64_t)az*sx,u=(int64_t)ax*dz-(int64_t)az*dx;
 if(den<0){den=-den;t=-t;u=-u;}
 if(t<0 || t>den || u<0 || u>den)return 4096;
 int f=t*4096/den,hy=y+(int64_t)dy*f/4096;
 if(hy<w[4]-16 || hy>w[5]+16)return 4096;
 return f;
}
