#include <stdint.h>
#include "collision.h"
static int root(uint64_t n){
 uint64_t x=0,bit=UINT64_C(1)<<62;
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
 int nx=*x-cx,nz=*z-cz;int64_t dist2=(int64_t)nx*nx+(int64_t)nz*nz;
 if(dist2>=radius*radius)return 0;
 if(!dist2){
  int side=((int64_t)(ox-w[0])*(-dz)+(int64_t)(oz-w[1])*dx)>=0?1:-1;
  int length=root((uint64_t)len);if(!length)return 0;
  *x=cx+side*(-dz)*(radius+1)/length;*z=cz+side*dx*(radius+1)/length;
 }else{
  int dist=root(dist2);if(!dist)dist=1;
  *x=cx+nx*(radius+1)/dist;*z=cz+nz*(radius+1)/dist;
 }
 return 1;
}
typedef struct {int x,y,z;} WallPoint;
static int clip_height(const WallPoint *in,int count,WallPoint *out,int y,int above){
 int n=0;
 for(int i=0;i<count;i++){
  WallPoint a=in[i],b=in[(i+1)%count];int ia=above?a.y>=y:a.y<=y,ib=above?b.y>=y:b.y<=y;
  if(ia)out[n++]=a;
  if(ia!=ib){
   out[n++]=(WallPoint){a.x+(int)((int64_t)(b.x-a.x)*(y-a.y)/(b.y-a.y)),y,
                         a.z+(int)((int64_t)(b.z-a.z)*(y-a.y)/(b.y-a.y))};
  }
 }
 return n;
}
int collision_triangle_push(int *x,int *z,int ox,int oz,int feet,int height,int radius,const short t[9]){
 int minx=t[0],maxx=t[0],miny=t[1],maxy=t[1],minz=t[2],maxz=t[2];
 for(int k=3;k<9;k+=3){
  if(t[k]<minx)minx=t[k];
  if(t[k]>maxx)maxx=t[k];
  if(t[k+1]<miny)miny=t[k+1];
  if(t[k+1]>maxy)maxy=t[k+1];
  if(t[k+2]<minz)minz=t[k+2];
  if(t[k+2]>maxz)maxz=t[k+2];
 }
 if(*x<minx-radius || *x>maxx+radius || *z<minz-radius || *z>maxz+radius ||
    feet+height<=miny || feet+8>=maxy)return 0;
 WallPoint a[8],b[8];for(int i=0;i<3;i++)a[i]=(WallPoint){t[3*i],t[3*i+1],t[3*i+2]};
 int n=clip_height(a,3,b,feet+8,1);if(n<2)return 0;
 n=clip_height(b,n,a,feet+height,0);if(n<2)return 0;
 /* A sloped wall projects to an area. Resolve an interior point toward its
    closest boundary; segment-only handling would miss its interior. */
 int positive=0,negative=0;int64_t area=0,best=INT64_MAX;int bx=*x,bz=*z;
 for(int i=0;i<n;i++){
  WallPoint p=a[i],q=a[(i+1)%n];
  int64_t dx=q.x-p.x,dz=q.z-p.z,len=dx*dx+dz*dz;
  int64_t cross=dx*(*z-p.z)-dz*(*x-p.x);positive|=cross>0;negative|=cross<0;
  area+=(int64_t)p.x*q.z-(int64_t)q.x*p.z;
  if(!len)continue;
  int64_t dot=(int64_t)(*x-p.x)*dx+(int64_t)(*z-p.z)*dz;
  if(dot<0)dot=0;
  if(dot>len)dot=len;
  int cx=p.x+(int)(dot*dx/len),cz=p.z+(int)(dot*dz/len);
  int64_t dist=(int64_t)(cx-*x)*(cx-*x)+(int64_t)(cz-*z)*(cz-*z);
  if(dist<best){best=dist;bx=cx;bz=cz;}
 }
 if(area && !(positive && negative) && best>0 && best!=INT64_MAX){
  int distance=root((uint64_t)best);if(!distance)distance=1;
  *x=bx+(int)((int64_t)(bx-*x)*(radius+1)/distance);
  *z=bz+(int)((int64_t)(bz-*z)*(radius+1)/distance);return 1;
 }
 int changed=0;
 for(int i=0;i<n;i++){
  WallPoint p=a[i],q=a[(i+1)%n];if(p.x==q.x && p.z==q.z)continue;
  short wall[6]={(short)p.x,(short)p.z,(short)q.x,(short)q.z,(short)miny,(short)maxy};
  changed|=collision_push(x,z,ox,oz,feet,height,radius,wall);
 }
 return changed;
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
 /* Reject disjoint segment bounds before 64-bit intersection arithmetic.
    Closed bounds retain endpoint, collinear and zero-length intersections. */
 int endx=x+dx,endz=z+dz,endy=y+dy;
 int minx=w[0]<w[2]?w[0]:w[2],maxx=w[0]>w[2]?w[0]:w[2];
 int minz=w[1]<w[3]?w[1]:w[3],maxz=w[1]>w[3]?w[1]:w[3];
 if((x<minx && endx<minx) || (x>maxx && endx>maxx) ||
    (z<minz && endz<minz) || (z>maxz && endz>maxz) ||
    (y<w[4]-16 && endy<w[4]-16) || (y>w[5]+16 && endy>w[5]+16))return 4096;
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
