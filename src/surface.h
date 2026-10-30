#ifndef SURFACE_H
#define SURFACE_H
/* Triangles store three XYZ vertices, integer units, positive Y up.
   Return the highest projected surface no higher than ceiling. */
int surface_height(const short (*triangles)[9],int count,int x,int z,int ceiling,int *height);
/* Return the lowest projected surface at or above minimum. */
int surface_ceiling(const short (*triangles)[9],int count,int x,int z,int minimum,int *height);
#endif
