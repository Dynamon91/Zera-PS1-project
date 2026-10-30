#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../src/stream_world.h"
#include "../src/player.h"
#include "../src/world.h"
static FILE *file;static int fail_read;
static int read_data(int sector,int sectors,void *dest,void *user){
 (void)user;if(fail_read)return 0;
 return !fseek(file,sector*2048,SEEK_SET) && fread(dest,2048,sectors,file)==(size_t)sectors;
}
int main(void){
 file=fopen("previews/walk/assets/COLLIDE.DAT","rb");assert(file);
 assert(stream_cache_load(0,0,1,read_data,NULL));int floor;assert(world_floor(0,0,20,&floor));
 printf("Original spawn ground: %d\n",floor);assert(floor>=2 && floor<=4);
 Player p;player_init(&p);Input in={0};in.camera_c=4096;
 for(int k=0;k<2;k++)assert(!player_tick(&p,in));assert(p.state==GROUND);
 int loads=walk_collision_loads;in.z=-1;
 for(int k=0;k<200;k++){
  assert(stream_cache_load(p.x/FP,p.z/FP,0,read_data,NULL));assert(!player_tick(&p,in));
  Player saved=p;assert(stream_cache_load(p.x/FP,p.z/FP,0,read_data,NULL));assert(!memcmp(&p,&saved,sizeof(p)));
 }
 printf("Route end: %d,%d,%d; loads %d\n",p.x/FP,p.y/FP,p.z/FP,walk_collision_loads);
 assert(p.x==0 && p.z==-2000*FP && p.state==GROUND && walk_collision_loads>=loads+2);
 /* Refill while airborne must preserve position, velocity and jump state. */
 player_init(&p);assert(stream_cache_load(0,0,1,read_data,NULL));in=(Input){.z=-1,.camera_c=4096};int was_held=0,air_reload=0;
 for(int k=0;k<200;k++){
  in.jump_held=p.z/FP<=-1180 && p.z/FP>=-1600;in.jump_pressed=in.jump_held && !was_held;was_held=in.jump_held;
  assert(!player_tick(&p,in));Player snapshot=p;int generation=walk_collision_loads;
  assert(stream_cache_load(p.x/FP,p.z/FP,0,read_data,NULL));assert(!memcmp(&snapshot,&p,sizeof(p)));
  if(walk_collision_loads>generation && p.state!=GROUND){air_reload++;printf("Airborne refill: z=%d y=%d state=%d vy=%d\n",p.z/FP,p.y/FP,p.state,p.vy/FP);}
 }
 assert(air_reload>0 && p.state==GROUND && p.z==-2000*FP);
 Player saved=p;fail_read=1;assert(!stream_cache_load(0,0,1,read_data,NULL));assert(!walk_collision_ready && !world_floor(0,0,100,&floor));assert(!memcmp(&p,&saved,sizeof(p)));
 fail_read=0;assert(stream_cache_load(0,0,1,read_data,NULL));
 player_init(&p);in=(Input){.x=1,.camera_c=4096};for(int k=0;k<100;k++)assert(!player_tick(&p,in));
 printf("Original sloped wall stops X %d\n",p.x/FP);assert(p.x/FP>=536 && p.x/FP<=539);
 /* Shifted sector queries must not truncate world coordinates to int16. */
 const StreamTriangle triangles[]={
  {{-100,0,-100,100,0,-100,100,0,100},1},{{-100,0,-100,100,0,100,-100,0,100},1},
  {{-100,140,-100,100,140,100,100,140,-100},1},
  {{70,0,-100,70,160,-100,70,160,100},2},{{70,0,-100,70,160,100,70,0,100},2}};
 const StreamView view={triangles,5,{100000,40000,-100000},0,0};stream_world_bind(&view,1,-700);
 assert(world_floor(100000,-100000,40010,&floor) && floor==40000);
 assert(world_ceiling(100000,-100000,40120,&floor) && floor==40140);
 int x=100100,z=-100000;world_move(100000,-100000,&x,&z,40000);assert(x<=100046);
 assert(world_camera_fraction(100000,40050,-100000,100,0,0)<4096);
 player_init(&p);p.x=100000*FP;p.y=40000*FP;p.z=-100000*FP;
 in=(Input){.jump_pressed=1,.camera_c=4096};assert(!player_tick(&p,in));in.jump_pressed=0;assert(!player_tick(&p,in));
 assert(p.y==40020*FP && p.vy==0 && p.state==FALL);

 fclose(file);puts("Streamed original floor/wall route, seam continuity, failed-load recovery and shifted queries passed");return 0;
}
