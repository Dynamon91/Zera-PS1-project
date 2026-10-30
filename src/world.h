#ifndef WORLD_H
#define WORLD_H
/* X/Z and returned Y are integer world units, positive Y up. */
int world_height(int x,int z,int *height);
/* Level3: select original collider support below ceiling; level2 retains heightfield. */
int world_floor(int x,int z,int ceiling,int *height);
/* Level3 overhead surface; level2 has no triangle-based ceiling data. */
int world_ceiling(int x,int z,int minimum,int *height);
void world_move(int oldx,int oldz,int *x,int *z,int feet);
int world_camera_fraction(int x,int y,int z,int dx,int dy,int dz);
/* Safety plane below the lowest recovered support data. */
int world_fall_limit(void);
#endif
