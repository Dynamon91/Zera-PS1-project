#include "character.h"
#include "player.h"
#include <stdint.h>
int character_facing_step(int facing,int x,int z,int yaw,int active){
 if(!active || (!x && !z))return facing;
 int direction=z>0?(x>0?512:x<0?-512:0):z<0?(x>0?1536:x<0?-1536:2048):(x>0?1024:-1024);
 int target=(direction-(yaw&4095))&4095;
 int turn=(target-(facing&4095))&4095;if(turn>2048)turn-=4096;
 if(turn>128)turn=128;if(turn<-128)turn=-128;
 return ((facing&4095)+turn)&4095;
}
int character_animation(int state,int moved){
 return state==GLIDE?3:state!=GROUND?2:moved?1:0;
}

int character_visible_step(int visible,int distance){
 return distance >= (visible?CHARACTER_HIDE_DISTANCE:CHARACTER_SHOW_DISTANCE);
}
int character_front_face(const short xy[6]){
 return (int64_t)(xy[2]-xy[0])*(xy[5]-xy[1])-(int64_t)(xy[3]-xy[1])*(xy[4]-xy[0])>0;
}
void character_link_face(CharacterDrawFace *faces,short *head,short index){
 short *link=head;
 while(*link>=0 && faces[*link].key<=faces[index].key)link=&faces[*link].next;
 faces[index].next=*link;*link=index;
}
