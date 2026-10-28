#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "../src/clip.h"
int reference_clip_triangle(const ClipCamera *,const ClipVertex [3],ClipVertex [10]);
static uint32_t state=0x5a455241;
static int sample(int extent){state=state*1664525u+1013904223u;return (int)(state%(2u*extent+1u))-extent;}
int main(void){
 unsigned int clipped=0,rejected=0;
 for(int test=0;test<50000;test++){
  ClipCamera c;ClipVertex in[3],actual[10],expected[10];
  for(int r=0;r<3;r++){
   c.t[r]=sample(3000);
   for(int k=0;k<3;k++)c.m[r][k]=sample(4096);
  }
  for(int k=0;k<3;k++)in[k]=(ClipVertex){sample(5000),sample(5000),sample(5000),sample(255),sample(255)};
  int n=clip_triangle(&c,in,actual),want=reference_clip_triangle(&c,in,expected);
  assert(n==want);
  for(int k=0;k<n;k++){
   assert(actual[k].x==expected[k].x && actual[k].y==expected[k].y && actual[k].z==expected[k].z);
   assert(actual[k].u==expected[k].u && actual[k].v==expected[k].v);
  }
  if(n==0)rejected++;else if(n!=3 || memcmp(actual,in,sizeof(in)))clipped++;
 }
 assert(clipped>1000 && rejected>1000);
 printf("Clip equivalence: 50000 cases, %u clipped, %u rejected\n",clipped,rejected);
 return 0;
}
