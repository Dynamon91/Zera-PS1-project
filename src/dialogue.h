#ifndef DIALOGUE_H
#define DIALOGUE_H
#include "player.h"
enum {DIALOGUE_NONE,DIALOGUE_APPROACH,DIALOGUE_TALK};
typedef struct {int phase,page,visited,completions,prompt,ticks,visible_chars;} Dialogue;
void dialogue_clear(Dialogue *d);
int dialogue_in_range(const Player *p);
/* Returns 1 when the controller is owned by the conversation. */
int dialogue_input(Dialogue *d,const Player *p,int interact,int advance);
Input dialogue_approach_input(const Player *p);
void dialogue_after_approach(Dialogue *d,const Player *p);
const char *dialogue_page(const Dialogue *d);
#endif
