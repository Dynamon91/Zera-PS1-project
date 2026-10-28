#ifndef COLLISION_H
#define COLLISION_H
/* World-unit positions; wall = x0,z0,x1,z1,y_min,y_max. */
int collision_push(int *x,int *z,int oldx,int oldz,int feet,int height,int radius,const short wall[6]);
int collision_ray(int x,int y,int z,int dx,int dy,int dz,const short wall[6]);
#endif
