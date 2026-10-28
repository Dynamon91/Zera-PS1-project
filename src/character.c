#include "character.h"
#include "player.h"
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
