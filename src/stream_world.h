#ifndef STREAM_WORLD_H
#define STREAM_WORLD_H
#include <stdint.h>
typedef struct {int16_t v[9];uint16_t flags;} StreamTriangle;
typedef struct {int tx,tz,center[3],count,sector,sectors;} StreamTile;
typedef struct {const StreamTriangle *triangles;int count,center[3],tx,tz;} StreamView;
_Static_assert(sizeof(StreamTriangle)==20,"Collision CD ABI");
void stream_world_bind(const StreamView *views,int count,int fall_limit);
typedef int (*StreamRead)(int sector,int sectors,void *destination,void *user);
/* Units remain the established 80/Unity unit, independent of render scale. */
int stream_cache_needs_load(int x,int z,int force);
int stream_cache_load(int x,int z,int force,StreamRead read,void *user);
extern volatile int walk_collision_ready,walk_collision_loads,walk_collision_tiles,walk_collision_triangles;
#endif
