"""Recover a low-poly source mesh for a separately labeled PS1 pickup trial.
The six trial placements are new; they do not reproduce original placements.
"""
from pathlib import Path
import sys,json,numpy as np
import UnityPy
from UnityPy.helpers.MeshHelper import MeshHandler
P=Path(__file__).resolve().parents[1];E=UnityPy.load(sys.argv[1]);o=next(o for o in E.objects if o.assets_file.name=='resources.assets' and o.path_id==400);m=o.read();h=MeshHandler(m);h.process()
v=np.array(h.m_Vertices)[:,:3];v[:,0]*=-1;v-=((v.min(0)+v.max(0))/2);v*=24/np.linalg.norm(v,axis=1).max();q=np.rint(v).astype(int);unique=list(dict.fromkeys(map(tuple,q)));lookup={v:i for i,v in enumerate(unique)}
faces=[]
for a,b,c in np.array(h.m_IndexBuffer).reshape(-1,3):
 ids=(lookup[tuple(q[a])],lookup[tuple(q[b])],lookup[tuple(q[c])])
 if len(set(ids))==3:faces.append(ids)
s='/* Recovered resources.assets object 400; trial material is provisional. */\nstatic const SVECTOR pickup_vertices[]={'+''.join('{%d,%d,%d,0},'%x for x in unique)+'};\nstatic const unsigned short pickup_faces[][3]={'+''.join('{%d,%d,%d},'%x for x in faces)+'};\n#define PICKUP_VERTEX_COUNT %d\n#define PICKUP_FACE_COUNT %d\n'%(len(unique),len(faces))
(P/'src/pickup_mesh.h').write_text(s)
grid=json.loads((P/'assets/world_chunk_source.json').read_text())['heightfield']
def height(x,z):
 x+=1280;z+=1280;i,j=x//40,z//40;fx,fz=x%40,z%40;a,b,c,d=grid[j][i],grid[j][i+1],grid[j+1][i],grid[j+1][i+1]
 assert -32768 not in (a,b,c,d)
 # Integer truncation matches the C heightfield interpolation.
 return a+int(((b-a)*fx+(c-a)*fz)/40) if fx+fz<=40 else d+int(((c-d)*(40-fx)+(b-d)*(40-fz))/40)
positions=[(x,height(x,x)+55,x) for x in [70,140,210,280,350,420]]
(P/'src/trial_layout.h').write_text('/* New PS1 trial placements, not original level progression. */\n#define TRIAL_PICKUPS 6\nstatic const short trial_positions[TRIAL_PICKUPS][3]={'+''.join('{%d,%d,%d},'%p for p in positions)+'};\n')
(P/'reports/pickup_conversion.json').write_text(json.dumps({'source_mesh':{'file':'resources.assets','path_id':400,'name':m.m_Name,'vertices':len(unique),'triangles':len(faces)},'material':'new gold trial material; original shader omitted','placements':'new test layout, not recovered original placements','positions':positions,'rule':'collect six tokens once per trial; one point each; no original reward/progression implied'},indent=2))
print('Pickup mesh:',len(unique),'vertices',len(faces),'triangles; trial positions:',positions)
