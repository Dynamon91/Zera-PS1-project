#include <assert.h>
typedef struct {short vx,vy,vz,pad;} SVECTOR;
#include "../previews/level3/src/relic_models.h"
int main(void){
 assert(RELIC_MODEL_COUNT==2);
 for(int id=0;id<2;id++){
 const unsigned short *s=relic_model_spans[id];assert(s[0]==id*105 && s[2]==id*206 && s[1]==105 && s[3]==206);
 for(int i=s[2];i<s[2]+s[3];i++){
  for(int k=0;k<3;k++)assert(relic_model_faces[i][k]>=s[0] && relic_model_faces[i][k]<s[0]+s[1]);
  assert(relic_model_faces[i][0]!=relic_model_faces[i][1] && relic_model_faces[i][1]!=relic_model_faces[i][2]);
  if(id==0)assert(relic_model_colors[i][0]>relic_model_colors[i][1] && relic_model_colors[i][2]==0);
  else assert(relic_model_colors[i][2]>relic_model_colors[i][0] && relic_model_colors[i][0]>relic_model_colors[i][1]);
 }
 }
 assert(sizeof(relic_model_vertices)/sizeof(relic_model_vertices[0])==210);
 assert(sizeof(relic_model_faces)/sizeof(relic_model_faces[0])==412);
 return 0;
}
