"""Stable skinning-aware packing shared by mesh and animation conversion."""
import json
from pathlib import Path
import numpy as np


def pack(root):
    root=Path(root)
    vertices=np.array([list(map(float,l.split()[1:4])) for l in (root/'assets/recovered_meshes/resources_assets_314_Cube_001.obj').read_text().splitlines() if l.startswith('v ')])
    skin=json.loads((root/'assets/character_animation_source.json').read_text())
    lo=vertices.min(0);hi=vertices.max(0);scale=160/(hi[1]-lo[1]);center=(lo+hi)/2
    q=np.rint(np.column_stack([(vertices[:,0]-center[0])*scale,-(vertices[:,1]-lo[1])*scale,(vertices[:,2]-center[2])*scale])).astype(int)
    # Coincident bind positions can belong to different animated joints.
    # Preserve distinct nonzero influences instead of welding by position alone.
    keys=[(tuple(q[i]),tuple(sorted((int(b),round(float(w),6)) for b,w in zip(skin['indices'][i],skin['weights'][i]) if w>1e-7))) for i in range(len(q))]
    lookup={};representatives=[];mapping=[]
    for i,key in enumerate(keys):
        if key not in lookup:lookup[key]=len(representatives);representatives.append(i)
        mapping.append(lookup[key])
    return vertices,q,representatives,mapping
