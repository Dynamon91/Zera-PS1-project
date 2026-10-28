#include <assert.h>
#include "../src/clip.h"
typedef struct {short vx,vy,vz,pad;} SVECTOR;
#include "../src/world_mesh.h"
int main(void){
 (void)world_colors;(void)world_tile;
 int end=0;
 for(int cell=0;cell<WORLD_CELL_COUNT;cell++){
  const short *b=world_cells[cell];assert(b[4]==end && b[5]>0);
  end+=b[5];assert(end<=WORLD_TRIANGLE_COUNT);
  for(int i=b[4];i<end;i++)for(int k=0;k<3;k++){
   assert(world_corner_ids[i][k]<WORLD_UNIQUE_COUNT);
   const SVECTOR *v=&world_unique[world_corner_ids[i][k]];
   assert(v->vx>=b[0] && v->vx<=b[2] && v->vz>=b[1] && v->vz<=b[3]);
   assert(v->vy>=b[6] && v->vy<=b[7]);
  }
 }
 assert(end==WORLD_TRIANGLE_COUNT);
 const int turns[][2]={{4096,0},{0,4096},{-4096,0},{0,-4096},{2896,2896},{2896,-2896}};
 for(int point=0;point<3;point++)for(int turn=0;turn<6;turn++){
  int x=point==1?2200:point==2?-1800:0,z=point==2?1200:0;
  int c=turns[turn][0],s=turns[turn][1];
  ClipCamera camera={{{c,0,s},{0,4096,0},{-s,0,c}},
                     {-(c*x+s*z)/4096,100,850-(-s*x+c*z)/4096}};
  for(int cell=0;cell<WORLD_CELL_COUNT;cell++){
   const short *b=world_cells[cell];unsigned common=~0u;
   for(int k=0;k<8;k++){
    ClipVertex v={k&1?b[2]:b[0],k&2?b[7]:b[6],k&4?b[3]:b[1],0,0};
    common &= clip_code(&camera,&v);
   }
   if(!common)continue;
   /* Independently run the full clipper: a rejected box must not hide a face. */
   for(int i=b[4];i<b[4]+b[5];i++){
    ClipVertex in[3],out[10];
    for(int k=0;k<3;k++){
     const SVECTOR *v=&world_unique[world_corner_ids[i][k]];
     in[k]=(ClipVertex){v->vx,v->vy,v->vz,world_uv[i][k*2],world_uv[i][k*2+1]};
    }
    assert(clip_triangle(&camera,in,out)==0);
   }
  }
 }
 return 0;
}
