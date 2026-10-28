#ifndef CLIP_H
#define CLIP_H
/* World coordinates, fixed-point rotation matrix (4096 == 1). */
typedef struct {int x,y,z,u,v;} ClipVertex;
typedef struct {int m[3][3],t[3];} ClipCamera;
unsigned int clip_code(const ClipCamera *camera,const ClipVertex *v);
int clip_triangle_known(const ClipCamera *camera,const ClipVertex input[3],const unsigned int codes[3],ClipVertex output[10]);
int clip_triangle(const ClipCamera *camera,const ClipVertex input[3],ClipVertex output[10]);
#endif
