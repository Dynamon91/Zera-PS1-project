#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../src/stream_world.h"
#include "../src/world.h"
#include "../src/dialogue.h"
#include "../previews/levium/src/levium_dialogue.h"
static FILE *data;
static int read_data(int sector,int count,void *dest,void *u){(void)u;return !fseek(data,sector*2048,SEEK_SET) && fread(dest,2048,count,data)==(size_t)count;}
static void load(Player *p){Player snapshot=*p;assert(stream_cache_load(p->x/FP,p->z/FP,0,read_data,0));assert(!memcmp(&snapshot,p,sizeof(*p)));}
int main(void){
 Dialogue d;dialogue_clear(&d);Player p;player_init(&p);assert(!dialogue_input(&d,&p,1,1));
 data=fopen("previews/cosmic/assets/COLLIDE.DAT","rb");assert(data);load(&p);int reached=0;
 for(int k=0;k<1200;k++){
  Input in={.x=1,.camera_c=4096};if(p.x/FP>4500)in.z=p.z/FP<LEVIUM_RANGE_Z-5?1:p.z/FP>LEVIUM_RANGE_Z+5?-1:0;
  load(&p);assert(!player_tick(&p,in));load(&p);
  if(dialogue_in_range(&p)){reached=1;break;}
 }
 assert(reached);printf("Source trigger reached at %d,%d,%d\n",p.x/FP,p.y/FP,p.z/FP);
 Player grounded=p;p.state=JUMP;assert(!dialogue_in_range(&p));p=grounded;p.dash_ticks=1;assert(!dialogue_in_range(&p));p=grounded;
 assert(dialogue_input(&d,&p,1,0) && d.phase==DIALOGUE_APPROACH);
 for(int k=0;k<100 && d.phase==DIALOGUE_APPROACH;k++){
  Input in=dialogue_approach_input(&p);assert(!player_tick(&p,in));load(&p);dialogue_after_approach(&d,&p);
 }
 assert(d.phase==DIALOGUE_TALK && d.page==0);fprintf(stderr,"Authored talk point reached at %d,%d,%d\n",p.x/FP,p.y/FP,p.z/FP);
 int floor;assert(world_floor(p.x/FP,p.z/FP,p.y/FP+8,&floor) && floor==p.y/FP && floor==-425);
 Player fixed=p;
 for(int page=0;page<LEVIUM_FIRST_PAGES;page++){
  assert(d.page==page);
  for(int k=0;k<150;k++)dialogue_input(&d,&p,0,0);
  assert(d.visible_chars==(int)strlen(dialogue_page(&d)));dialogue_input(&d,&p,0,1);assert(!memcmp(&fixed,&p,sizeof(p)));
 }
 assert(d.phase==DIALOGUE_NONE && d.visited && d.completions==1);
 assert(dialogue_input(&d,&p,1,0));dialogue_after_approach(&d,&p);assert(d.phase==DIALOGUE_TALK && d.page==LEVIUM_FIRST_PAGES);
 for(int k=0;k<30;k++)dialogue_input(&d,&p,0,0);dialogue_input(&d,&p,0,1);assert(d.phase==0 && d.completions==2);
 dialogue_clear(&d);assert(!d.visited && !d.completions);fclose(data);puts("Levium continuous route, source trigger/talk point, first and repeat dialogue passed");return 0;
}
