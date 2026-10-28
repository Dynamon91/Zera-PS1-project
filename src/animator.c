#include "animator.h"
#include "zera_anim.h"
static void sample(int clip,int tick,AnimPoint *out){
 int duration=zera_anim_ticks[clip];
 int phase=clip==2?(tick<duration?tick:duration-1):tick%duration;
 int sub=phase*zera_anim_count[clip]*256/duration;
 int frame=sub/256,next=frame+1;if(next>=zera_anim_count[clip])next=clip==2?frame:0;
 for(int i=0;i<ANIM_VERTICES;i++){
  const AnimPoint *a=&zera_anim[zera_anim_start[clip]+frame][i],*b=&zera_anim[zera_anim_start[clip]+next][i];
  out[i].x=a->x+(b->x-a->x)*(sub&255)/256;
  out[i].y=a->y+(b->y-a->y)*(sub&255)/256;
  out[i].z=a->z+(b->z-a->z)*(sub&255)/256;out[i].pad=0;
 }
}
void animator_init(Animator *a){
 a->clip=0;a->tick=0;a->blend_tick=ANIM_BLEND_TICKS;sample(0,0,a->local);
 for(int i=0;i<ANIM_VERTICES;i++)a->from[i]=a->local[i];
}
void animator_update(Animator *a,int clip,int active){
 if(!active)return;
 if(clip<0 || clip>3)clip=0;
 if(clip!=a->clip){
  for(int i=0;i<ANIM_VERTICES;i++)a->from[i]=a->local[i];
  a->clip=clip;a->tick=0;a->blend_tick=0;
 }
 sample(a->clip,a->tick,a->local);
 if(a->blend_tick<ANIM_BLEND_TICKS){
  int weight=++a->blend_tick;
  for(int i=0;i<ANIM_VERTICES;i++){
   AnimPoint *p=&a->local[i];const AnimPoint *f=&a->from[i];
   p->x=f->x+(p->x-f->x)*weight/ANIM_BLEND_TICKS;
   p->y=f->y+(p->y-f->y)*weight/ANIM_BLEND_TICKS;
   p->z=f->z+(p->z-f->z)*weight/ANIM_BLEND_TICKS;
  }
 }
 if(a->clip==2){if(a->tick<zera_anim_ticks[2]-1)a->tick++;}
 else a->tick=(a->tick+1)%zera_anim_ticks[a->clip];
}
