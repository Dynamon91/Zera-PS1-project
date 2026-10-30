#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../src/stream_world.h"
#include "../src/world.h"
#include "../src/player.h"
static FILE *data;static int fail;
static int read_data(int sector,int count,void *dest,void *user){(void)user;return !fail && !fseek(data,sector*2048,SEEK_SET) && fread(dest,2048,count,data)==(size_t)count;}
static void load(Player *p){Player saved=*p;assert(stream_cache_load(p->x/FP,p->z/FP,0,read_data,NULL));assert(!memcmp(&saved,p,sizeof(*p)));}
int main(void){
 data=fopen("previews/cosmic/assets/COLLIDE.DAT","rb");assert(data);
 Player p;player_init(&p);load(&p);int h;assert(world_floor(0,0,48,&h) && h==2);
 assert(!player_tick(&p,(Input){0}) && p.y==2*FP);
 int initial=walk_collision_loads;
 for(int k=0;k<200;k++){load(&p);assert(!player_tick(&p,(Input){.z=1,.camera_s=-4096}));load(&p);}
 printf("Cosmic ground end: %d,%d,%d; loads %d\n",p.x/FP,p.y/FP,p.z/FP,walk_collision_loads);
 assert(p.x==2000*FP && p.y==-233*FP && p.z==0 && p.state==GROUND && walk_collision_loads>initial);
 player_init(&p);load(&p);assert(!player_tick(&p,(Input){0}));int held=0,air_loads=0;
 for(int k=0;k<200;k++){
  Input in={.z=1,.camera_s=-4096};in.jump_held=p.x/FP>=1180 && p.x/FP<=1600;in.jump_pressed=in.jump_held && !held;held=in.jump_held;
  assert(!player_tick(&p,in));int count=walk_collision_loads;load(&p);
  if(walk_collision_loads>count && p.state!=GROUND){air_loads++;assert(p.vy>0);}
 }
 for(int k=0;k<100 && p.state!=GROUND;k++)assert(!player_tick(&p,(Input){0}));
 assert(air_loads==1 && p.x==2000*FP && p.state==GROUND && p.y==-233*FP);
 Player snapshot=p;fail=1;assert(!stream_cache_load(0,0,1,read_data,NULL) && !walk_collision_ready);assert(!memcmp(&snapshot,&p,sizeof(p)));fail=0;load(&p);
 player_init(&p);load(&p);assert(!player_tick(&p,(Input){0}) && p.y==2*FP);
 fclose(data);puts("Cosmic source floor, crossing in air, landing, failed read and respawn passed");return 0;
}
