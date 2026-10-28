#include <assert.h>
#include <string.h>
#include <limits.h>
#include "../src/trial.h"
int main(void){
 Trial t,copy;Player p={0};trial_clear(&t);assert(!trial_update(&t,&p,1));trial_start(&t);
 p.x=trial_positions[0][0]*FP;p.z=trial_positions[0][2]*FP;p.y=(trial_positions[0][1]-55)*FP;
 copy=t;assert(!trial_update(&t,&p,0));assert(!memcmp(&t,&copy,sizeof(t)));
 assert(trial_update(&t,&p,1)==1 && t.count==1);assert(!trial_update(&t,&p,1) && t.count==1);
 p.x=INT_MAX;p.z=INT_MIN;p.y=0;assert(!trial_update(&t,&p,1));
 p.x=trial_positions[1][0]*FP;p.z=trial_positions[1][2]*FP;p.y=1000*FP;assert(!trial_update(&t,&p,1));
 for(int i=1;i<TRIAL_PICKUPS;i++){p.x=trial_positions[i][0]*FP;p.z=trial_positions[i][2]*FP;p.y=(trial_positions[i][1]-55)*FP;assert(trial_update(&t,&p,1)==1);}
 assert(t.count==TRIAL_PICKUPS && t.completed && t.collected==63);copy=t;assert(!trial_update(&t,&p,1));assert(!memcmp(&t,&copy,sizeof(t)));
 assert(t.best_valid && t.best_ticks==t.ticks);int first=t.best_ticks;
 trial_start(&t);assert(t.active && !t.count && !t.completed && !t.collected);
 assert(t.best_valid && t.best_ticks==first && t.ticks==0);
 /* A slower completion preserves the previous record. */
 t.ticks=first+10;
 for(int i=0;i<TRIAL_PICKUPS;i++){p.x=trial_positions[i][0]*FP;p.z=trial_positions[i][2]*FP;p.y=(trial_positions[i][1]-55)*FP;trial_update(&t,&p,1);}
 assert(t.completed && t.best_ticks==first);
 /* A faster completion replaces it; completed time then freezes. */
 trial_start(&t);
 for(int i=0;i<TRIAL_PICKUPS;i++){p.x=trial_positions[i][0]*FP;p.z=trial_positions[i][2]*FP;p.y=(trial_positions[i][1]-55)*FP;trial_update(&t,&p,1);}
 assert(t.completed && t.best_ticks==TRIAL_PICKUPS && t.best_ticks<first);
 copy=t;assert(!trial_update(&t,&p,1));assert(!memcmp(&t,&copy,sizeof(t)));
 trial_clear(&t);assert(!t.active && !t.best_valid && !t.best_ticks);
 return 0;
}
