#ifndef CHARACTER_H
#define CHARACTER_H
/* Q12 full turn: use the same camera yaw as this tick's movement command. */
int character_facing_step(int facing,int input_x,int input_z,int movement_yaw,int active);
/* Actual horizontal displacement chooses ground locomotion; air state wins. */
int character_animation(int state,int moved);
/* Hide when the camera enters the mascot; separate restore distance prevents
   visibility oscillation around a wall. Distances are provisional world units. */
#define CHARACTER_HIDE_DISTANCE 320
#define CHARACTER_SHOW_DISTANCE 400
int character_visible_step(int visible,int camera_distance);
/* Projected mascot faces: exact depth resolves ties inside a coarse PS1 OT
   bucket. Keys sort near first because GPU primitives are prepended. */
typedef struct {int key;short xy[6],next,face;} CharacterDrawFace;
int character_front_face(const short xy[6]);
void character_link_face(CharacterDrawFace *faces,short *head,short index);
#endif
