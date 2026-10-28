#include <assert.h>
#include "../src/collision.h"
int main(void){
 const short wall[]={0,-200,0,200,0,250};int x=-5,z=0;
 assert(collision_push(&x,&z,-40,0,0,120,24,wall));assert(x<=-24 && z==0);
 x=5;z=0;assert(collision_push(&x,&z,40,0,0,120,24,wall));assert(x>=24);
 x=-5;z=70;assert(collision_push(&x,&z,-40,50,0,120,24,wall));assert(x<=-24 && z==70);
 x=-5;z=0;assert(!collision_push(&x,&z,-40,0,300,120,24,wall));assert(x==-5);
 x=0;z=0;assert(collision_push(&x,&z,-40,0,0,120,24,wall));assert(x<=-24);
 x=-50;z=0;assert(!collision_push(&x,&z,-60,0,0,120,24,wall));
 assert(collision_ray(-100,80,0,200,0,0,wall)==2048);
 assert(collision_ray(-100,400,0,200,0,0,wall)==4096);
 assert(collision_ray(-100,80,300,200,0,0,wall)==4096);
 assert(collision_ray(-100,80,0,0,0,100,wall)==4096);
 assert(collision_ray(100,80,0,-200,0,0,wall)==2048);
 /* Camera rays along the wall, including entry from either endpoint. */
 assert(collision_ray(0,80,-400,0,0,400,wall)==2048);
 assert(collision_ray(0,80,400,0,0,-400,wall)==2048);
 assert(collision_ray(0,80,0,0,0,100,wall)==0);
 assert(collision_ray(1,80,-400,0,0,400,wall)==4096);
 assert(collision_ray(0,400,-400,0,0,400,wall)==4096);
 assert(collision_ray(0,80,-400,0,0,-400,wall)==4096);
 /* Vertical entry, zero-length rays, and disjoint height/segment intervals. */
 assert(collision_ray(0,400,0,0,-268,0,wall)==2048);
 assert(collision_ray(0,-150,0,0,268,0,wall)==2048);
 assert(collision_ray(0,80,0,0,0,0,wall)==0);
 assert(collision_ray(0,80,300,0,-200,0,wall)==4096);
 assert(collision_ray(0,400,-400,0,-134,800,wall)==4096);
 const short diagonal[]={-100,-100,100,100,0,250};
 const short reversed[]={100,100,-100,-100,0,250};
 assert(collision_ray(-200,80,-200,400,0,400,diagonal)==1024);
 assert(collision_ray(-200,80,-200,400,0,400,reversed)==1024);
 /* Entry rounds up rather than returning a point just before the wall. */
 assert(collision_ray(0,80,-201,0,0,3,wall)==1366);
 return 0;
}
