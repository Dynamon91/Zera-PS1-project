#ifndef CHECKPOINT_H
#define CHECKPOINT_H
#include "player.h"
typedef struct {int id,x,y,z,yaw,trigger_x,trigger_y,trigger_z;} CheckpointConfig;
typedef struct {int active,x,y,z,yaw,activations;} Checkpoint;
void checkpoint_clear(Checkpoint *c);
/* Provisional grounded proximity trigger; original Kiwi interaction is not ported. */
int checkpoint_update(Checkpoint *c,const CheckpointConfig *config,const Player *p,int enabled);
int checkpoint_respawn(const Checkpoint *c,Player *p);
#endif
