#include <stdint.h>
#include <string.h>
#include "dialogue.h"
#include "../previews/levium/src/levium_dialogue.h"
static int abs_i(int n){return n<0?-n:n;}
void dialogue_clear(Dialogue *d){*d=(Dialogue){0};}
int dialogue_in_range(const Player *p){
 if(p->state!=GROUND || p->dash_ticks)return 0;
 /* Source trigger is a horizontal capsule, despite local direction=Y.
    Intersect it with the provisional vertical PS1 player capsule (r=24). */
 int64_t x=p->x/FP,z=p->z/FP;
 int64_t ax=LEVIUM_RANGE_A_X,az=LEVIUM_RANGE_A_Z;
 int64_t dx=LEVIUM_RANGE_B_X-ax,dz=LEVIUM_RANGE_B_Z-az,len=dx*dx+dz*dz;
 int64_t dot=(x-ax)*dx+(z-az)*dz;if(dot<0)dot=0;if(dot>len)dot=len;
 int64_t qx=ax+(len?dx*dot/len:0),qz=az+(len?dz*dot/len:0);
 int64_t low=p->y/FP+24,high=p->y/FP+96,cy=LEVIUM_RANGE_Y;
 int64_t dy=cy<low?low-cy:cy>high?cy-high:0;
 int64_t rx=x-qx,rz=z-qz,radius=LEVIUM_RANGE_RADIUS+24;
 if(rx< -radius || rx>radius || rz< -radius || rz>radius || dy>radius)return 0;
 return rx*rx+rz*rz+dy*dy<=radius*radius;
}
const char *dialogue_page(const Dialogue *d){return levium_pages[d->page];}
int dialogue_input(Dialogue *d,const Player *p,int interact,int advance){
 d->prompt=d->phase==DIALOGUE_NONE && dialogue_in_range(p);
 if(d->phase==DIALOGUE_NONE){
  if(!d->prompt || !interact)return 0;
  d->phase=DIALOGUE_APPROACH;d->ticks=0;d->prompt=0;return 1;
 }
 if(d->phase==DIALOGUE_TALK){
  d->ticks++;int length=(int)strlen(dialogue_page(d));if(d->visible_chars<length)d->visible_chars+=2;if(d->visible_chars>length)d->visible_chars=length;
  if(advance && d->ticks>5){
   if(d->visible_chars<length)d->visible_chars=length;
   else if((!d->visited && d->page+1<LEVIUM_FIRST_PAGES)){d->page++;d->visible_chars=0;d->ticks=0;}
   else{d->visited=1;d->completions++;d->phase=DIALOGUE_NONE;d->prompt=dialogue_in_range(p);}
  }
 }
 return 1;
}
Input dialogue_approach_input(const Player *p){
 int x=p->x/FP,z=p->z/FP;
 return (Input){.x=x<LEVIUM_TALK_X-6?1:x>LEVIUM_TALK_X+6?-1:0,.z=z<LEVIUM_TALK_Z-6?1:z>LEVIUM_TALK_Z+6?-1:0,.camera_c=4096};
}
void dialogue_after_approach(Dialogue *d,const Player *p){
 if(d->phase!=DIALOGUE_APPROACH)return;
 d->ticks++;
 if(abs_i(p->x/FP-LEVIUM_TALK_X)<=8 && abs_i(p->z/FP-LEVIUM_TALK_Z)<=8 && p->state==GROUND){d->phase=DIALOGUE_TALK;d->page=d->visited?LEVIUM_FIRST_PAGES:0;d->visible_chars=0;d->ticks=0;}
 /* Allow recovery if provisional collision prevents reaching the authored point. */
 else if(d->ticks>180){d->phase=DIALOGUE_NONE;d->prompt=0;}
}
