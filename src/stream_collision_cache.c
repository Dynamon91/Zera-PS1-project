#include <stddef.h>
#include <string.h>
#include "stream_world.h"
#ifdef ZERA_CAMPAIGN_ENTRY
#include "../previews/cosmic/src/collision_catalog.h"
#else
#include "../previews/walk/src/collision_catalog.h"
#define STREAM_SCENE_ID 1
#endif
#define VIEW_COUNT 25
#define RESERVE 128
_Alignas(4) static StreamTriangle buffer[STREAM_COLLISION_CAPACITY+RESERVE];
_Static_assert(RESERVE*sizeof(StreamTriangle)>=2048+16,"CD read padding");
static StreamView views[VIEW_COUNT];static int last_x,last_z;
volatile int walk_collision_ready=0,walk_collision_loads=0,walk_collision_tiles=0,walk_collision_triangles=0;
static int cell(int x){int q=x/STREAM_CELL;if(x<0 && x%STREAM_CELL)q--;return q;}
int stream_cache_needs_load(int x,int z,int force){return force || !walk_collision_ready || cell(x)!=last_x || cell(z)!=last_z;}
int stream_cache_load(int x,int z,int force,StreamRead read,void *user){
 int tx=cell(x),tz=cell(z);
 if(!stream_cache_needs_load(x,z,force))return 1;
 walk_collision_ready=0;walk_collision_tiles=0;walk_collision_triangles=0;stream_world_bind(NULL,0,STREAM_FALL_LIMIT);
 for(int i=0;i<STREAM_COLLISION_TILES;i++){
  const StreamTile *t=&stream_collision_tiles[i];
  if(t->tx<tx-2 || t->tx>tx+2 || t->tz<tz-2 || t->tz>tz+2)continue;
  if(walk_collision_tiles>=VIEW_COUNT || t->count>STREAM_COLLISION_CAPACITY-walk_collision_triangles ||
     (size_t)t->sectors*2048>sizeof(buffer)-walk_collision_triangles*sizeof(StreamTriangle))return 0;
  void *dest=&buffer[walk_collision_triangles];
  if(!read(t->sector,t->sectors,dest,user))return 0;
  int32_t h[4];memcpy(h,dest,sizeof(h));
  if(h[0]!=STREAM_SCENE_ID || h[1]!=t->tx || h[2]!=t->tz || h[3]!=t->count)return 0;
  memmove(dest,(const unsigned char*)dest+16,t->count*sizeof(StreamTriangle));
  StreamView *v=&views[walk_collision_tiles++];v->triangles=dest;v->count=t->count;v->tx=t->tx;v->tz=t->tz;
  for(int k=0;k<3;k++)v->center[k]=t->center[k];
  walk_collision_triangles+=t->count;
 }
 last_x=tx;last_z=tz;
 stream_world_bind(views,walk_collision_tiles,STREAM_FALL_LIMIT);walk_collision_loads++;walk_collision_ready=1;return 1;
}
