#ifndef ATLAS_FORMAT_H
#define ATLAS_FORMAT_H
#include <stdint.h>
typedef struct {int16_t v[3][3];uint8_t color[3][3],flags;} AtlasTriangle;
typedef struct {const char *name;int entry[3],yaw;} AtlasScene;
typedef struct {int scene,tx,tz,center[3],count,sector,sectors,ymin,ymax;} AtlasTile;
_Static_assert(sizeof(AtlasTriangle)==28,"Atlas disk ABI");
#endif
