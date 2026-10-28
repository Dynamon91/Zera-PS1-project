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
 return 0;
}
