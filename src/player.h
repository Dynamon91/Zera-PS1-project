#ifndef PLAYER_H
#define PLAYER_H
#include <stdint.h>
#define FP 256
/* Provisional body clearance, shared with the wall collision proxy. */
#define PLAYER_HEIGHT 120
typedef enum {GROUND,JUMP,FALL,GLIDE,DASH} PlayerState;
typedef struct {int32_t x,y,z,vy; int dash_ticks; PlayerState state;} Player;
typedef struct {int x,z,jump_pressed,jump_held,dash_pressed; int camera_c,camera_s;} Input;
void player_init(Player *p);
/* Return nonzero when the safety plane respawns the player this tick. */
int player_tick(Player *p, Input i);
#endif
