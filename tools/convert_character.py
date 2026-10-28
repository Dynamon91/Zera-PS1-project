"""Convert identified Zera bind-pose OBJ into compact integer C data."""
from pathlib import Path
import json
from character_packing import pack
p=Path(__file__).resolve().parents[1]
f=p/'assets/recovered_meshes/resources_assets_314_Cube_001.obj'
v=[];faces=[];mat=0;mats={}
for l in f.read_text().splitlines():
 s=l.split()
 if not s:continue
 if s[0]=='v':v.append(tuple(map(float,s[1:4])))
 elif s[0]=='g' and s[1].startswith('Cube_001_'):mat=int(s[1].rsplit('_',1)[1])
 elif s[0]=='f':
  ids=[int(x.split('/')[0])-1 for x in s[1:]]
  for j in range(1,len(ids)-1):faces.append((ids[0],ids[j],ids[j+1],mat))
colors=json.loads((p/'assets/zera_vertex_colors.json').read_text())
facecolors=[tuple(sum(colors[j][k] for j in f[:3])//3 for k in range(3)) for f in faces]
lo=[min(x[i] for x in v) for i in range(3)];hi=[max(x[i] for x in v) for i in range(3)]
scale=160/(hi[1]-lo[1]);cx=(lo[0]+hi[0])/2;cz=(lo[2]+hi[2])/2
q=[(round((x-cx)*scale),round(-(y-lo[1])*scale),round((z-cz)*scale)) for x,y,z in v]
# Preserve coincident vertices when their animated joint influences differ.
_,packed,representatives,mapping=pack(p)
uniq=[tuple(packed[i]) for i in representatives]
faces=[(mapping[a],mapping[b],mapping[c],m) for a,b,c,m in faces]
(p/'src/character_config.h').write_text('#ifndef CHARACTER_CONFIG_H\n#define CHARACTER_CONFIG_H\n#define ANIM_VERTICES %d\n#endif\n'%len(uniq))
(p/'assets/character_packing.json').write_text(json.dumps({'source_vertices':len(v),'packed_vertices':len(uniq),'representatives':representatives,'mapping':mapping,'rule':'quantized bind position plus sorted nonzero bone influences, weights rounded to 6 decimals'},indent=2)+'\n')
s='/* Recovered Zera mesh: resources.assets object 314, bind pose. */\n'
s+='static const SVECTOR zera_vertices[] = {\n'+''.join('{%d,%d,%d,0},\n'%x for x in uniq)+'};\n'
s+='static const unsigned short zera_faces[][4] = {\n'+''.join('{%d,%d,%d,%d},\n'%x for x in faces)+'};\n'
s+='static const unsigned char zera_face_colors[][3] = {\n'+''.join('{%d,%d,%d},\n'%c for c in facecolors)+'};\n'
s+='#define ZERA_FACE_COUNT %d\n'%len(faces)
(p/'src/zera_mesh.h').write_text(s)
(p/'reports/character_conversion.json').write_text(json.dumps({'source_file':str(f.relative_to(p)),'identified_by':'SkinnedMeshRenderer child Cube_001 of Zera under _Zera','source_vertices':len(v),'packed_vertices':len(uniq),'triangles':len(faces),'animation':'offline original clip skinning; see animation_conversion.json','texture':'original mascot materials; see mascot_materials.json','colors':'original vertex colors; per-corner Gouraud data exported by convert_mascot_materials.py','bounds':{'min':lo,'max':hi}},indent=2))
print(len(uniq),'vertices,',len(faces),'triangles')
