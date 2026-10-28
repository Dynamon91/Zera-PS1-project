#ifndef ANIMATOR_H
#define ANIMATOR_H
#include <stdint.h>
#include "character_config.h"
#define ANIM_BLEND_TICKS 6
typedef struct {int16_t x,y,z,pad;} AnimPoint;
typedef struct {int clip,tick,blend_tick;AnimPoint from[ANIM_VERTICES],local[ANIM_VERTICES];} Animator;
void animator_init(Animator *a);
void animator_update(Animator *a,int clip,int active);
#endif
