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
 /* A triangular wall rises along Z. Its old full-height rectangle blocks
    below the actual face; clipping the face to the body leaves that path free. */
 const short triangular[]={0,0,0,0,400,0,0,400,400};
 const short reverse_triangle[]={0,400,400,0,400,0,0,0,0};
 const short rectangle[]={0,0,0,400,0,400};
 x=-5;z=300;assert(collision_push(&x,&z,-40,300,0,120,24,rectangle));
 x=-5;z=300;assert(!collision_triangle_push(&x,&z,-40,300,0,120,24,triangular));assert(x==-5 && z==300);
 x=-5;z=300;assert(!collision_triangle_push(&x,&z,-40,300,0,120,24,reverse_triangle));
 x=-5;z=300;assert(collision_triangle_push(&x,&z,-40,300,250,120,24,triangular));assert(x<=-24);
 x=5;z=300;assert(collision_triangle_push(&x,&z,40,300,250,120,24,reverse_triangle));assert(x>=24);
 x=-5;z=300;assert(!collision_triangle_push(&x,&z,-40,300,500,120,24,triangular));
 const short slope[]={0,0,0,100,400,0,0,0,400};
 x=5;z=50;assert(collision_triangle_push(&x,&z,-40,50,0,120,24,slope));assert(x<0);
 x=500;z=500;assert(!collision_triangle_push(&x,&z,490,500,0,120,24,slope));
 const short original_slope[]={574,0,181,574,0,-190,547,265,-161};
 const short old_slope_proxy[]={547,-161,547,185,0,265};
 x=530;z=0;assert(collision_push(&x,&z,500,0,0,120,24,old_slope_proxy));
 x=530;z=0;assert(!collision_triangle_push(&x,&z,500,0,0,120,24,original_slope));assert(x==530 && z==0);
 x=545;z=0;assert(collision_triangle_push(&x,&z,500,0,0,120,24,original_slope));assert(x<=538 && x>=536);
 /* Large short-coordinate edges must not overflow distance/root arithmetic. */
 const short large_wall[]={-32768,-32768,32767,32767,0,400};
 x=-5;z=5;assert(collision_push(&x,&z,-40,40,0,120,24,large_wall));assert(x< -16 && z>16);
 return 0;
}
