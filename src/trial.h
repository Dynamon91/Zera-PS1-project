#ifndef TRIAL_H
#define TRIAL_H
#include <stdint.h>
#include "player.h"
#include "trial_layout.h"
typedef struct {uint32_t collected;int active,count,completed,ticks,best_ticks,best_valid;} Trial;
void trial_clear(Trial *t);
void trial_start(Trial *t);
int trial_update(Trial *t,const Player *p,int active);
#endif
