#ifndef CAMERA_H
#define CAMERA_H
#define CAMERA_DISTANCE 850
/* Q12 unobstructed fraction. Retract immediately, recover only when active.
   Zero is valid: no readability floor may move the camera past a wall. */
int camera_distance_step(int current,int fraction,int paused);
/* Stationary fallback: prefer a 45-degree side view only for a substantial
   clearance gain. Caller handles pause, input priority and cooldown. */
int camera_orbit_offset(int current,int left,int right);
#endif
