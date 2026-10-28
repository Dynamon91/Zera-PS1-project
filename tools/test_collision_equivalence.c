#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "../src/collision.h"
int reference_collision_ray(int,int,int,int,int,int,const short[6]);
static uint32_t state=0x5a455241;
static int sample(int extent){state=state*1664525u+1013904223u;return (int)(state%(2u*extent+1u))-extent;}
int main(void){
 unsigned int hits=0;
 for(int test=0;test<100000;test++){
  short wall[6];for(int k=0;k<4;k++)wall[k]=sample(5000);
  wall[4]=sample(2000);wall[5]=wall[4]+1+(state%1500);
  int x=sample(6000),y=sample(4000),z=sample(6000);
  int dx=sample(3000),dy=sample(3000),dz=sample(3000);
  /* Exercise exact line overlap, vertical and point rays as well as random rays. */
  if(test%4==0){x=wall[0];z=wall[1];dx=wall[2]-x;dz=wall[3]-z;}
  if(test%7==0)dx=dz=0;
  if(test%11==0)dy=0;
  int actual=collision_ray(x,y,z,dx,dy,dz,wall);
  assert(actual==reference_collision_ray(x,y,z,dx,dy,dz,wall));
  if(actual<4096)hits++;
 }
 assert(hits>1000);
 printf("Camera ray equivalence: 100000 cases, %u intersections\n",hits);
 return 0;
}
