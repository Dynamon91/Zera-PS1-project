"""Extract a bounded original level2 spawn-area mesh and heightfield.
The collision adaptation is a single-valued heightfield, not full Unity physics.
"""
import sys,json,math
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from PIL import Image
import UnityPy
from UnityPy.helpers.MeshHelper import MeshHandler
P=Path(__file__).resolve().parents[1];E=UnityPy.load(sys.argv[1]);F=next(f for f in E.files.values() if getattr(f,'name',None)=='level2')
cache={};meshcache={};tiles=[];tile_ids={};texture_names=[]
def wm(t):
 id=t.object_reader.path_id
 if id in cache:return cache[id]
 q=t.m_LocalRotation;s=t.m_LocalScale;p=t.m_LocalPosition
 m=np.eye(4);m[:3,:3]=Rotation.from_quat([q.x,q.y,q.z,q.w]).as_matrix()@np.diag([s.x,s.y,s.z]);m[:3,3]=[p.x,p.y,p.z]
 if t.m_Father.path_id:m=wm(t.m_Father.read())@m
 cache[id]=m;return m

def meshdata(ptr):
 key=(ptr.deref().assets_file.name,ptr.path_id)
 if key not in meshcache:
  d=ptr.read();h=MeshHandler(d);h.process();verts=np.array(h.m_Vertices)[:,:3];idx=np.array(h.m_IndexBuffer,dtype=int)
  colors=np.array(h.m_Colors) if h.m_Colors else np.tile([90,130,75,255],(len(verts),1))
  meshcache[key]=(verts,idx,colors,d,np.array(h.m_UV0)[:,:2] if h.m_UV0 else np.zeros((len(verts),2)))
 return meshcache[key]
def transform(t,v):m=wm(t);return v@m[:3,:3].T+m[:3,3]
def go_transform(go):return next(c.component.read() for c in go.m_Component if c.component.deref().type.name=='Transform')
spawn=next(wm(o.read())[:3,3] for o in F.objects.values() if o.type.name=='Transform' and o.read().m_GameObject.read().m_Name=='_StartSpawnPoint')
SCALE=80;R=16.;scene=[];collision=[];instances=[]
for o in F.objects.values():
 if o.type.name not in ('MeshFilter','MeshCollider'):continue
 d=o.read();go=d.m_GameObject.read()
 if not d.m_Mesh.path_id:continue
 if o.type.name=='MeshCollider' and not go.m_Name.startswith('Walkable'):continue
 try:v,idx,col,mesh,uv=meshdata(d.m_Mesh);t=go_transform(go);v=transform(t,v)
 except Exception:continue
 if len(v)==0:continue
 if np.any(v[:,[0,2]].max(0)<spawn[[0,2]]-R) or np.any(v[:,[0,2]].min(0)>spawn[[0,2]]+R):continue
 root=t
 while root.m_Father.path_id:root=root.m_Father.read()
 # Include original static environment, omitting actors, UI, water and effects.
 if o.type.name=='MeshFilter' and root.m_GameObject.read().m_Name not in ('Islands','Tutorial'):continue
 if o.type.name=='MeshFilter':
  renderer=next((c.component.read() for c in go.m_Component if c.component.deref().type.name=='MeshRenderer'),None)
  if renderer is None or not renderer.m_Enabled:continue
  if renderer.m_StaticBatchInfo.subMeshCount:raise RuntimeError('Static batched source requires separate conversion')
 added=0
 material_tiles=[]
 if o.type.name=='MeshFilter':
  for mp in renderer.m_Materials:
   material=mp.read();key=(mp.deref().assets_file.name,mp.path_id)
   if key not in tile_ids:
    tex=next((t.m_Texture for k,t in material.m_SavedProperties.m_TexEnvs if k=='_MainTex' and t.m_Texture.path_id),None)
    im=tex.read().image.convert('RGB').resize((64,64)) if tex else Image.new('RGB',(64,64),'white')
    tile_ids[key]=len(tiles);tiles.append(im);texture_names.append(material.m_Name)
   material_tiles.append(tile_ids[key])
 for si,sub in enumerate(mesh.m_SubMeshes):
  if sub.topology!=0:continue
  start=sub.firstByte//(2 if mesh.m_IndexFormat==0 else 4)
  for ids in idx[start:start+sub.indexCount].reshape(-1,3):
   a=v[ids]
   if np.any(a[:,[0,2]].max(0)<spawn[[0,2]]-R) or np.any(a[:,[0,2]].min(0)>spawn[[0,2]]+R):continue
   if o.type.name=='MeshCollider':collision.append(a)
   else:scene.append((np.column_stack([a,uv[ids]]),col[ids,:3].mean(0),material_tiles[min(si,len(material_tiles)-1)]));added+=1
 if added:instances.append({'object':go.m_Name,'mesh':mesh.m_Name,'triangles_before_clipping':added,'source_file':d.m_Mesh.deref().assets_file.name,'mesh_id':d.m_Mesh.path_id})
collision=np.array(collision)
def heights(x,z):
 a,b,c=collision[:,0],collision[:,1],collision[:,2]
 den=(b[:,2]-c[:,2])*(a[:,0]-c[:,0])+(c[:,0]-b[:,0])*(a[:,2]-c[:,2])
 ok=np.abs(den)>1e-8;den=np.where(ok,den,1)
 u=((b[:,2]-c[:,2])*(x-c[:,0])+(c[:,0]-b[:,0])*(z-c[:,2]))/den
 v=((c[:,2]-a[:,2])*(x-c[:,0])+(a[:,0]-c[:,0])*(z-c[:,2]))/den
 y=u*a[:,1]+v*b[:,1]+(1-u-v)*c[:,1]
 valid=ok&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1+1e-6)&(y<=spawn[1]+6)
 return y[valid]
hits=heights(spawn[0],spawn[2]);hits=hits[hits<=spawn[1]+1];assert len(hits),'No source ground under spawn';ground=float(hits.max())
# Clip rendering triangles to an XZ square without inventing surface geometry.
def clip(poly,axis,bound,sign):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  ia=(a[axis]-bound)*sign>=0;ib=(b[axis]-bound)*sign>=0
  if ia:out.append(a)
  if ia!=ib:out.append(a+(b-a)*(bound-a[axis])/(b[axis]-a[axis]))
 return out
tri=[];colors=[];uvs=[];tile_indices=[]
for a,color,tile in scene:
 poly=list(a)
 for axis in (0,2):
  poly=clip(poly,axis,spawn[axis]-R,1)
  if not poly:break
  poly=clip(poly,axis,spawn[axis]+R,-1)
  if not poly:break
 for j in range(1,len(poly)-1):
  pts=np.array([poly[0],poly[j],poly[j+1]])
  q=np.rint(np.column_stack([-(pts[:,0]-spawn[0])*SCALE,80-(pts[:,1]-ground)*SCALE,(pts[:,2]-spawn[2])*SCALE])).astype(int)
  if np.abs(q).max()>15000:continue
  # Texture coordinates use a 64-texel repeating texture window. Rebase each
  # triangle by whole periods to avoid crossing an 8-bit coordinate wrap.
  tc=pts[:,3:5].copy();tc[:,1]=1-tc[:,1];tc-=np.floor(tc.min(axis=0))
  if np.ptp(tc,axis=0).max()>3.9:raise RuntimeError('UV span exceeds 8-bit range; subdivide source triangle')
  tc=np.rint(tc*64).astype(int).clip(0,255)
  tri.append(q);colors.append(np.clip(color,0,255).astype(int));uvs.append(tc);tile_indices.append(tile)
assert len(tri)<3000,len(tri)
N=65;STEP=40;ORIGIN=-1280;grid=[]
for iz in range(N):
 row=[]
 for ix in range(N):
  x=spawn[0]-(ORIGIN+ix*STEP)/SCALE;z=spawn[2]+(ORIGIN+iz*STEP)/SCALE
  h=heights(x,z);row.append(round((float(h.max())-ground)*SCALE) if len(h) else -32768)
 grid.append(row)
assert grid[N//2][N//2]==0
used=sorted(set(tile_indices));remap={old:new for new,old in enumerate(used)}
tiles=[tiles[i] for i in used];texture_names=[texture_names[i] for i in used];tile_indices=[remap[i] for i in tile_indices]
s='/* Original level2 spawn-area geometry; clipped offline. */\n'
s+='static const SVECTOR world_triangles[][3]={\n'+''.join('{'+''.join('{%d,%d,%d,0},'%tuple(v) for v in a)+'},\n' for a in tri)+'};\n'
s+='static const unsigned char world_colors[][3]={\n'+''.join('{%d,%d,%d},\n'%tuple(c) for c in colors)+'};\n'
s+='static const unsigned char world_uv[][6]={\n'+''.join('{'+','.join(map(str,u.flatten()))+'},\n' for u in uvs)+'};\n'
s+='static const unsigned char world_tile[]={'+','.join(map(str,tile_indices))+'};\n'
unique=list(dict.fromkeys(tuple(map(int,v)) for a in tri for v in a));lookup={v:i for i,v in enumerate(unique)}
s+='static const SVECTOR world_unique[]={'+''.join('{%d,%d,%d,0},'%v for v in unique)+'};\n'
s+='static const unsigned short world_corner_ids[][3]={'+''.join('{'+','.join(str(lookup[tuple(map(int,v))]) for v in a)+'},' for a in tri)+'};\n'
s+='#define WORLD_UNIQUE_COUNT %d\n'%len(unique)
s+='#define WORLD_TRIANGLE_COUNT %d\n'%len(tri)
(P/'src/world_mesh.h').write_text(s)
# Conservative vertical-wall proxies from steep triangles in this collision-
# matched walkable mesh. Longest XZ edge plus the triangle's vertical interval.
walls=set()
for a in tri:
 g=a.copy();g[:,1]=80-g[:,1]
 normal=np.cross(g[1]-g[0],g[2]-g[0])
 if 2*int(normal[1])**2 >= int(normal[0])**2+int(normal[2])**2:continue
 edges=[(g[i],g[(i+1)%3]) for i in range(3)]
 a,b=max(edges,key=lambda e:int(e[0][0]-e[1][0])**2+int(e[0][2]-e[1][2])**2)
 if np.sum((a[[0,2]]-b[[0,2]])**2)<16:continue
 ends=sorted([(int(a[0]),int(a[2])),(int(b[0]),int(b[2]))])
 walls.add((*ends[0],*ends[1],int(g[:,1].min()),int(g[:,1].max())))
walls=sorted(walls)
(P/'src/world_walls.h').write_text('/* Steep original terrain, conservative vertical proxies. */\n#define WORLD_WALL_COUNT %d\nstatic const short world_walls[][6]={\n'%len(walls)+''.join('{'+','.join(map(str,w))+'},\n' for w in walls)+'};\n')

assert len(tiles)<=16
atlas=Image.new('RGB',(256,256),'white')
for i,im in enumerate(tiles):atlas.paste(im,((i%4)*64,(i//4)*64))
indexed=atlas.quantize(colors=256,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.FLOYDSTEINBERG)
(P/'assets/world_textures').mkdir(exist_ok=True)
indexed.save(P/'assets/world_textures/world_atlas.png')
palette=indexed.getpalette();palette+= [0]*(768-len(palette));clut=[]
for i in range(256):
 rr,gg,bb=palette[i*3:i*3+3];clut.append((rr>>3)|((gg>>3)<<5)|((bb>>3)<<10) or 1)
tex=indexed.tobytes();words=[int.from_bytes(tex[i:i+4],'little') for i in range(0,len(tex),4)]
clutwords=[clut[i]|(clut[i+1]<<16) for i in range(0,256,2)]
(P/'src/world_texture.h').write_text('/* Original textures: 8-bit indexed 256x256 atlas + BGR555 CLUT. */\nstatic const uint32_t world_texture[]={'+','.join(hex(x) for x in words)+'};\nstatic const uint32_t world_clut[]={'+','.join(hex(x) for x in clutwords)+'};\n')
s='#define WORLD_N 65\n#define WORLD_STEP 40\n#define WORLD_ORIGIN (-1280)\nstatic const short world_heights[WORLD_N][WORLD_N]={\n'+''.join('{'+','.join(map(str,row))+'},\n' for row in grid)+'};\n'
(P/'src/world_height.h').write_text(s)
report={'scene':'level2','area':'original overworld spawn vicinity','spawn':spawn.tolist(),'ground_height':ground,'source_radius_units':R,'world_scale':SCALE,'render_triangles':len(tri),'texture_materials':texture_names,'texture_format':'8-bit indexed 256x256 atlas, 64x64 repeating tiles','source_collision_triangles':len(collision),'wall_proxies':len(walls),'instances':instances,'heightfield':{'size':N,'step':STEP,'origin':ORIGIN,'missing_sentinel':-32768},'limitations':['single-valued heightfield','conservative steep-triangle wall proxies; not full capsule/triangle collision','original main textures; custom Unity shader effects omitted','actors and effects omitted','not full original level']}
(P/'reports/world_conversion.json').write_text(json.dumps(report,indent=2))
(P/'assets/world_chunk_source.json').write_text(json.dumps({'report':report,'triangles':[a.tolist() for a in tri],'colors':[c.tolist() for c in colors],'heightfield':grid,'walls':walls}))
print('World triangles:',len(tri),'collision source:',len(collision),'spawn ground:',ground,'instances:',len(instances))
