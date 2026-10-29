#include <assert.h>
typedef struct {short vx,vy,vz,pad;} SVECTOR;
#include "../src/relic_models.h"
int main(void){
 unsigned v=0,f=0;
 for(int id=0;id<RELIC_MODEL_COUNT;id++){
  const unsigned short *s=relic_model_spans[id];assert(s[0]==v && s[2]==f && s[1]<=RELIC_MODEL_MAX_VERTICES);
  assert(s[1]>20 && s[3]>100 && s[3]<300);
  for(unsigned i=s[2];i<s[2]+s[3];i++){
   for(int k=0;k<3;k++)assert(relic_model_faces[i][k]>=s[0] && relic_model_faces[i][k]<s[0]+s[1]);
   assert(relic_model_faces[i][0]!=relic_model_faces[i][1]);
   if(id<2)assert(relic_model_colors[i][0]==0 && relic_model_colors[i][2]>relic_model_colors[i][1]);
   else assert(relic_model_colors[i][1]>relic_model_colors[i][0] && relic_model_colors[i][2]==0);
  }
  for(unsigned i=s[0];i<s[0]+s[1];i++)assert(relic_model_vertices[i].vx> -200 && relic_model_vertices[i].vx<200 && relic_model_vertices[i].vy> -200 && relic_model_vertices[i].vy<200);
  v+=s[1];f+=s[3];
 }
 assert(v==sizeof(relic_model_vertices)/sizeof(relic_model_vertices[0]));
 assert(f==sizeof(relic_model_faces)/sizeof(relic_model_faces[0]));
 return 0;
}
