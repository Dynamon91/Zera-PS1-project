#include <assert.h>
#include "../src/camera.h"
int main(void){
 /* A close proxy used to be ignored by the 420-unit readability floor. */
 assert(camera_distance_step(850,1024,0)==212);
 assert(camera_distance_step(850,0,0)==0);
 assert(camera_distance_step(850,1024,1)==212);
 assert(camera_distance_step(212,4096,1)==212);
 assert(camera_distance_step(212,4096,0)==220);
 assert(camera_distance_step(848,4096,0)==850);
 assert(camera_distance_step(211,1024,0)==212);
 assert(camera_distance_step(-1,-1,0)==0);
 assert(camera_distance_step(1000,5000,1)==850);
 /* Repeated recovery never crosses the current obstruction. */
 int distance=0;
 for(int n=0;n<200;n++){
  distance=camera_distance_step(distance,2048,0);
  assert(distance<=425);
 }
 assert(distance==425);
 for(int fraction=0;fraction<=4096;fraction++){
  int limit=CAMERA_DISTANCE*fraction/4096;
  assert(camera_distance_step(850,fraction,0)<=limit);
  assert(camera_distance_step(850,fraction,1)<=limit);
 }
 return 0;
}
