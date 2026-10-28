#include <stdint.h>
#include "surface.h"
int surface_height(const short (*triangles)[9],int count,int x,int z,int ceiling,int *height){
 int found=0,best=0;
 for(int i=0;i<count;i++){
  const short *t=triangles[i];
  /* Closed bounds preserve triangle edges and avoid most 64-bit divisions. */
  if((x<t[0] && x<t[3] && x<t[6]) || (x>t[0] && x>t[3] && x>t[6]) ||
     (z<t[2] && z<t[5] && z<t[8]) || (z>t[2] && z>t[5] && z>t[8]))continue;
  int64_t den=(int64_t)(t[5]-t[8])*(t[0]-t[6])+(int64_t)(t[6]-t[3])*(t[2]-t[8]);
  if(!den)continue;
  int64_t a=(int64_t)(t[5]-t[8])*(x-t[6])+(int64_t)(t[6]-t[3])*(z-t[8]);
  int64_t b=(int64_t)(t[8]-t[2])*(x-t[6])+(int64_t)(t[0]-t[6])*(z-t[8]);
  int64_t c=den-a-b;
  if(den<0){den=-den;a=-a;b=-b;c=-c;}
  if(a<0 || b<0 || c<0)continue;
  int h=(a*t[1]+b*t[4]+c*t[7])/den;
  if(h<=ceiling && (!found || h>best)){best=h;found=1;}
 }
 if(found)*height=best;
 return found;
}
