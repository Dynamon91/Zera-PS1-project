#ifndef LAUNCH_H
#define LAUNCH_H
#include "player.h"
/* Bounded PS1 coordinates in FP=256; normalized time uses Q16. */
typedef struct {int start[3],end[3],trigger[3],radius,step,arc;} LaunchConfig;
typedef struct {int active,time,started,completed,cancelled;} Launch;
int launch_can_start(const Launch *l,const Player *p,const LaunchConfig *c);
int launch_begin(Launch *l,Player *p,const LaunchConfig *c);
/* One simulation tick; returns 1 at the clamped endpoint. No world calls. */
int launch_tick(Launch *l,Player *p,const LaunchConfig *c);
void launch_cancel(Launch *l);
#endif
