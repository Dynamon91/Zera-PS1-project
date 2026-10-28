#include <assert.h>
#include "../src/clip.h"
int main(void){
 ClipCamera c={{{4096,0,0},{0,4096,0},{0,0,4096}},{0,0,0}};ClipVertex out[10];
 ClipVertex in[3]={{-50,-50,400,0,0},{50,-50,400,64,0},{0,50,400,32,64}};
 assert(clip_triangle(&c,in,out)==3);
 for(int i=0;i<3;i++)in[i].z=0;
 assert(clip_triangle(&c,in,out)==0);
 in[0]=(ClipVertex){-50,-50,0,0,0};in[1]=(ClipVertex){50,-50,400,64,0};in[2]=(ClipVertex){0,50,400,32,64};
 int n=clip_triangle(&c,in,out);assert(n>=3 && n<=8);
 for(int i=0;i<n;i++){assert(out[i].z>=94);assert(out[i].u>=0 && out[i].u<=64);assert(out[i].v>=0 && out[i].v<=64);}
 in[0]=(ClipVertex){-2000,-50,400,0,0};in[1]=(ClipVertex){2000,-50,400,64,0};in[2]=(ClipVertex){0,2000,400,32,64};
 n=clip_triangle(&c,in,out);assert(n>=3 && n<=8);
 for(int i=0;i<n;i++){assert(out[i].x>=-302 && out[i].x<=302);assert(out[i].y>=-224 && out[i].y<=255);}
 for(int i=0;i<3;i++)in[i].x=2000;
 assert(clip_triangle(&c,in,out)==0);
 return 0;
}
