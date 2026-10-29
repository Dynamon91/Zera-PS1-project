#ifndef RELICS_H
#define RELICS_H
#include "player.h"
#define RELIC_COUNT 3
/* Source placement/value data; provisional PS1 pickup volume. */
static const int relic_positions[RELIC_COUNT][3]={{-256,1927,786},{678,1927,497},{-141,106,-804}};
static const int relic_values[RELIC_COUNT]={8,8,4};
typedef struct {int mask,count,value;} Relics;
void relics_clear(Relics *r);
int relics_update(Relics *r,const Player *p,int active);
#endif
