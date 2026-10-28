#ifndef CHARACTER_H
#define CHARACTER_H
/* Q12 full turn: use the same camera yaw as this tick's movement command. */
int character_facing_step(int facing,int input_x,int input_z,int movement_yaw,int active);
/* Actual horizontal displacement chooses ground locomotion; air state wins. */
int character_animation(int state,int moved);
#endif
