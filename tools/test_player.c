#include <assert.h>
#include "../src/player.h"
static int terrain;
int world_fall_limit(void){return terrain==4?-1500:-700;}
void world_move(int ox,int oz,int *x,int *z,int feet){(void)ox;(void)oz;(void)x;(void)z;(void)feet;}
int world_height(int x,int z,int *h){
 (void)z;
 if(terrain==3 && x>40)return 0;
 *h=terrain==4?-800:terrain==1?x/2:terrain==2 && x>0?100:0;
 return 1;
}
int world_floor(int x,int z,int ceiling,int *h){if(terrain==5){*h=ceiling>=200?200:0;return ceiling>=0;}return world_height(x,z,h);}
int main(void){
 Player p;player_init(&p);assert(p.state==GROUND);
 player_tick(&p,(Input){.jump_pressed=1});assert(p.y>0 && p.state==JUMP);
 for(int n=0;n<120;n++)player_tick(&p,(Input){0});
 assert(p.y==0 && p.state==GROUND);
 player_tick(&p,(Input){.jump_pressed=1,.jump_held=1});
 for(int n=0;n<25;n++)player_tick(&p,(Input){.jump_held=1});
 assert(p.state==GLIDE && p.vy==-3*FP);
 player_init(&p);player_tick(&p,(Input){.x=1,.dash_pressed=1});assert(p.x==24*FP);
 player_init(&p);player_tick(&p,(Input){.x=1,.camera_s=4096});assert(p.x==0 && p.z==10*FP);
 player_init(&p);player_tick(&p,(Input){.z=1,.camera_s=4096});assert(p.x==-10*FP && p.z==0);
 terrain=1;player_init(&p);player_tick(&p,(Input){.x=1});assert(p.y==5*FP && p.state==GROUND);
 terrain=2;player_init(&p);player_tick(&p,(Input){.x=1});assert(p.x==0 && p.y==0);
 terrain=3;player_init(&p);
 for(int n=0;n<6;n++)player_tick(&p,(Input){.x=1});
 assert(p.state==FALL && p.y<0);
 for(int n=0;n<100;n++)player_tick(&p,(Input){0});
 assert(p.state==GROUND && p.x==0 && p.y==0);
 /* Stacked support: a jump below an upper floor must return to the lower one;
    falling from above must land on the upper one rather than pass through. */
 terrain=5;player_init(&p);player_tick(&p,(Input){.jump_pressed=1});
 for(int n=0;n<100;n++)player_tick(&p,(Input){0});
 assert(p.state==GROUND && p.y==0);
 p.y=300*FP;p.vy=0;p.state=FALL;
 for(int n=0;n<100;n++)player_tick(&p,(Input){0});
 assert(p.state==GROUND && p.y==200*FP);
 /* Valid low ground must not trigger the old spawn-relative safety plane. */
 terrain=4;player_init(&p);
 for(int n=0;n<100;n++)player_tick(&p,(Input){0});
 assert(p.state==GROUND && p.y==-800*FP);
 terrain=3;p.x=100*FP;p.y=-699*FP;p.state=FALL;p.vy=-10*FP;
 assert(player_tick(&p,(Input){0})==1);
 assert(p.state==GROUND && p.x==0 && p.y==0);
 return 0;
}
