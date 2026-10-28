#include <assert.h>
#include <limits.h>
#include "../src/surface.h"
int main(void){
 const short layers[][9]={{-100,0,-100,100,0,-100,0,0,100},{-100,200,-100,0,200,100,100,200,-100}};
 int h=999;
 assert(surface_height(layers,2,0,0,48,&h) && h==0);
 assert(surface_height(layers,2,0,0,208,&h) && h==200);
 assert(!surface_height(layers,2,0,0,-1,&h) && h==200);
 assert(!surface_height(layers,2,200,0,INT_MAX,&h));
 assert(surface_height(layers,2,-100,-100,INT_MAX,&h) && h==200);
 const short slope[][9]={{-100,-100,-100,100,100,-100,0,0,100}};
 assert(surface_height(slope,1,50,-50,INT_MAX,&h) && h==50);
 const short vertical[][9]={{0,0,0,0,200,0,0,0,100}};
 assert(!surface_height(vertical,1,0,0,INT_MAX,&h));
 /* Large short-coordinate triangles require 64-bit weights and products. */
 const short large[][9]={{-32768,-30000,-32768,32767,30000,-32768,0,0,32767}};
 assert(surface_height(large,1,0,0,INT_MAX,&h) && h==0);
 return 0;
}
