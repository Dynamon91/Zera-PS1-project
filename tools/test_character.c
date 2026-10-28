#include <assert.h>
#include <stdint.h>
#include "../src/animator.h"
typedef struct {short vx,vy,vz,pad;} SVECTOR;
#include "../src/zera_mesh.h"
#include "../src/mascot_materials.h"
#include "../src/mascot_texture.h"
int main(void){
 (void)zera_vertices;(void)zera_face_colors;
 assert(ANIM_VERTICES==412 && ZERA_FACE_COUNT==MASCOT_FACE_COUNT);
 int spots=0,eyes=0,gradient=0;
 unsigned char seen[MASCOT_FACE_COUNT]={0};int previous=2;
 for(int i=0;i<MASCOT_FACE_COUNT;i++){int face=mascot_draw_order[i];assert(face<MASCOT_FACE_COUNT && !seen[face]);seen[face]=1;assert(mascot_material[face]<=previous);previous=mascot_material[face];}
 for(int i=0;i<ZERA_FACE_COUNT;i++){
  for(int k=0;k<3;k++)assert(zera_faces[i][k]<ANIM_VERTICES);
  int material=mascot_material[i];assert(material>=0 && material<=2);
  spots+=material==1;eyes+=material==2;
  const unsigned char *c=mascot_corner_colors[i];
  if(c[0]!=c[3] || c[1]!=c[4] || c[2]!=c[5])gradient++;
  if(material==1)for(int k=0;k<6;k++)assert(mascot_uv[i][k]<=128);
  if(material==2)for(int k=0;k<3;k++)assert(mascot_uv[i][k*2]>=128 && mascot_uv[i][k*2+1]<128);
 }
 assert(spots==96 && eyes==16 && gradient>100);
 assert(sizeof(mascot_texture)==256*128 && sizeof(mascot_clut)==512);
 assert((mascot_clut[0]&65535)==0);
 for(int i=1;i<256;i++)assert(((mascot_clut[i/2]>>((i&1)*16))&65535)!=0);
 int transparent=0,opaque=0;
 for(unsigned int i=0;i<sizeof(mascot_texture)/sizeof(mascot_texture[0]);i++)for(int k=0;k<4;k++){
  if((mascot_texture[i]>>(k*8))&255)opaque++;else transparent++;
 }
 assert(transparent>0 && opaque>transparent);
 return 0;
}
