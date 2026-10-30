#ifndef RELICS_H
#define RELICS_H
#include "player.h"
#if defined(ZERA_STREAM_RELICS)
#include "../previews/walk/src/relic_layout.h"
#elif defined(ZERA_CORRIDOR_RELICS)
#include "../previews/level3/src/relic_layout.h"
#else
#define RELIC_COUNT 3
/* Source placement/value data; provisional PS1 pickup volume. */
static const int relic_positions[RELIC_COUNT][3]={{-256,1927,786},{678,1927,497},{-141,106,-804}};
static const int relic_values[RELIC_COUNT]={8,8,4};
#endif
typedef struct {int mask,count,value;} Relics;
void relics_clear(Relics *r);
int relics_update(Relics *r,const Player *p,int active);
#endif
