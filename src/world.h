#ifndef WORLD_H
#define WORLD_H
/* X/Z and returned Y are integer world units, positive Y up. */
int world_height(int x,int z,int *height);
void world_move(int oldx,int oldz,int *x,int *z,int feet);
int world_camera_fraction(int x,int y,int z,int dx,int dy,int dz);
#endif
