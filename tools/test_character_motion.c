#include <assert.h>
#include "../src/character.h"
#include "../src/player.h"
int main(void){
 const int input[][3]={{0,1,0},{1,1,512},{1,0,1024},{1,-1,1536},{0,-1,2048},{-1,-1,2560},{-1,0,3072},{-1,1,3584}};
 for(int yaw=0;yaw<4096;yaw+=256)for(int k=0;k<8;k++){
  int facing=0,target=(input[k][2]-yaw)&4095;
  for(int n=0;n<32;n++){
   int next=character_facing_step(facing,input[k][0],input[k][1],yaw,1);
   int delta=(next-facing)&4095;if(delta>2048)delta-=4096;
   assert(delta>=-128 && delta<=128);facing=next;
  }
  assert(facing==target);
 }
 assert(character_facing_step(4090,0,1,0,1)==0);
 assert(character_facing_step(10,0,1,6,1)==4090);
 assert(character_facing_step(3000,1,0,0,0)==3000);
 assert(character_facing_step(3000,0,0,0,1)==3000);
 /* L1 can change the view to zero after movement used yaw=512. Facing must
    still converge to direction1024 - movementYaw512, not newViewYaw0. */
 int f=0;for(int n=0;n<4;n++)f=character_facing_step(f,1,0,512,1);
 assert(f==512);
 assert(character_animation(GROUND,0)==0 && character_animation(GROUND,1)==1);
 assert(character_animation(JUMP,0)==2 && character_animation(FALL,1)==2);
 assert(character_animation(GLIDE,0)==3);
 assert(character_visible_step(1,850)==1);
 assert(character_visible_step(1,CHARACTER_HIDE_DISTANCE)==1);
 assert(character_visible_step(1,CHARACTER_HIDE_DISTANCE-1)==0);
 assert(character_visible_step(0,CHARACTER_SHOW_DISTANCE-1)==0);
 assert(character_visible_step(0,CHARACTER_SHOW_DISTANCE)==1);
 assert(character_visible_step(1,-10)==0);
 int visible=1,changes=0;
 for(int n=0;n<100;n++){
  int next=character_visible_step(visible,CHARACTER_HIDE_DISTANCE+(n&1?1:-1));
  changes+=next!=visible;visible=next;
 }
 assert(changes==1 && !visible);
 visible=character_visible_step(visible,CHARACTER_SHOW_DISTANCE);
 for(int n=0;n<100;n++)visible=character_visible_step(visible,CHARACTER_SHOW_DISTANCE+(n&1?1:-1));
 assert(visible);
 return 0;
}
