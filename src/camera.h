#ifndef CAMERA_H
#define CAMERA_H
#define CAMERA_DISTANCE 850
/* Q12 unobstructed fraction. Retract immediately, recover only when active.
   Zero is valid: no readability floor may move the camera past a wall. */
int camera_distance_step(int current,int fraction,int paused);
#endif
