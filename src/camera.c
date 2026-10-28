#include "camera.h"
int camera_distance_step(int current,int fraction,int paused){
 if(fraction<0)fraction=0;
 if(fraction>4096)fraction=4096;
 if(current<0)current=0;
 if(current>CAMERA_DISTANCE)current=CAMERA_DISTANCE;
 int desired=CAMERA_DISTANCE*fraction/4096;
 if(desired<current)return desired;
 if(!paused){
  current+=8;
  if(current>desired)current=desired;
 }
 return current;
}
