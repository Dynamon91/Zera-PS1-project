"""Extract a bounded original level2 spawn-area mesh and heightfield.
The collision adaptation is a single-valued heightfield, not full Unity physics.
"""
import sys,json,math,argparse,hashlib
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from PIL import Image
import UnityPy
from UnityPy.helpers.MeshHelper import MeshHandler
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('data')
parser.add_argument('--radius',type=float,default=16.0)
parser.add_argument('--scene',choices=['level2','level3'],default='level2')
parser.add_argument('--launchpad',type=int,help='Center a separate level3 preview on this original LaunchPad component')
parser.add_argument('--output-root',type=Path,help='Separate generated project root for a preview')
parser.add_argument('--checkpoint',type=int,help='Center a separate level3 preview on a recovered checkpoint spawn')
parser.add_argument('--bounds',type=float,nargs=4,metavar=('XMIN','XMAX','ZMIN','ZMAX'),help='Optional source-unit extraction bounds relative to spawn, within radius')
args=parser.parse_args()
if args.checkpoint is not None and (args.scene!='level3' or args.output_root is None or args.launchpad is not None):parser.error('checkpoint requires level3, separate output root and no launchpad')
if args.radius<=0 or abs(args.radius*80/40-round(args.radius*80/40))>1e-6:parser.error('radius must be positive and align to the 40-unit collision grid')
if args.bounds is not None:
 if not all(math.isfinite(v) and abs(v)<=args.radius and abs(v*2-round(v*2))<1e-6 for v in args.bounds) or args.bounds[0]>=args.bounds[1] or args.bounds[2]>=args.bounds[3]:parser.error('bounds must be ordered half-unit coordinates within radius')
 if not args.bounds[0]<=0<=args.bounds[1] or not args.bounds[2]<=0<=args.bounds[3]:parser.error('bounds must contain spawn')
P=args.output_root or Path(__file__).resolve().parents[1]
for folder in ('src','assets','reports'):(P/folder).mkdir(parents=True,exist_ok=True)
E=UnityPy.load(args.data);F=next(f for f in E.files.values() if getattr(f,'name',None)==args.scene)
source_asset_files={args.scene}
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
 source_asset_files.add(key[0])
 if key not in meshcache:
  d=ptr.read();h=MeshHandler(d);h.process();verts=np.array(h.m_Vertices)[:,:3];idx=np.array(h.m_IndexBuffer,dtype=int)
  colors=np.array(h.m_Colors) if h.m_Colors else np.tile([90,130,75,255],(len(verts),1))
  meshcache[key]=(verts,idx,colors,d,np.array(h.m_UV0)[:,:2] if h.m_UV0 else np.zeros((len(verts),2)))
 return meshcache[key]
def transform(t,v):m=wm(t);return v@m[:3,:3].T+m[:3,3]
def go_transform(go):return next(c.component.read() for c in go.m_Component if c.component.deref().type.name=='Transform')
launch_root=None
if args.launchpad is not None:
 if args.scene!='level3' or args.output_root is None:parser.error('launchpad requires level3 and a separate output root')
 component=F.objects[args.launchpad].read(check_read=False)
 script=component.m_Script.read()
 if (script.m_Namespace,script.m_ClassName)!=('NewZera','LaunchPad'):raise ValueError('Not an original LaunchPad')
 launch_root=go_transform(component.m_GameObject.read()).object_reader.path_id
spawn=next(wm(o.read())[:3,3] for o in F.objects.values() if o.type.name=='Transform' and o.read().m_GameObject.read().m_Name.startswith('_StartSpawnPoint'))
if launch_root is not None:spawn=wm(F.objects[launch_root].read())[:3,3]
if args.checkpoint is not None:
 recovery=json.loads((Path(__file__).resolve().parents[1]/'reports/progression_recovery.json').read_text())
 for name in ('level3','Managed/Assembly-CSharp.dll'):
  if hashlib.sha256((Path(args.data)/name).read_bytes()).hexdigest()!=recovery['source_file_sha256'][name]:raise ValueError('Checkpoint recovery source mismatch: '+name)
 checkpoint=next(e for scene in recovery['scenes'] if scene['scene']=='level3' for e in scene['entries'] if e['kind']=='Checkpoint' and e['component_path_id']==args.checkpoint)
 spawn=np.array(checkpoint['new_spawn_point']['target']['source_world_position'])
SCALE=80;R=args.radius;scene=[];collision=[];blocking=[];wall_instances=[];instances=[]
extents=args.bounds or [-R,R,-R,R]
lower=np.array([spawn[0]+extents[0],spawn[2]+extents[2]])
upper=np.array([spawn[0]+extents[1],spawn[2]+extents[3]])
limits={0:(lower[0],upper[0]),2:(lower[1],upper[1])}
for o in F.objects.values():
 if o.type.name not in ('MeshFilter','MeshCollider'):continue
 d=o.read();go=d.m_GameObject.read()
 if not d.m_Mesh.path_id:continue
 t=go_transform(go);root=t
 while root.m_Father.path_id:root=root.m_Father.read()
 is_launch_object=root.object_reader.path_id==launch_root
 if o.type.name=='MeshCollider':
  if args.scene=='level3':
   if root.m_GameObject.read().m_Name!='DrearyValley' and not is_launch_object:continue
   if go.m_Name.startswith('Lava') or not d.m_Enabled or d.m_IsTrigger:continue
   ancestor=t;active=True
   while True:
    active=active and bool(ancestor.m_GameObject.read().m_IsActive)
    if not ancestor.m_Father.path_id:break
    ancestor=ancestor.m_Father.read()
   if not active:continue
  elif not go.m_Name.startswith('Walkable') and not is_launch_object:continue
 renderer=None;batch_first=0;batch_count=0
 if o.type.name=='MeshFilter':
  if root.m_GameObject.read().m_Name not in (('Islands','Tutorial') if args.scene=='level2' else ('DrearyValley',)) and not is_launch_object:continue
  if args.scene=='level3' and go.m_Name.startswith('Lava'):continue
  renderer=next((c.component.read() for c in go.m_Component if c.component.deref().type.name=='MeshRenderer'),None)
  if renderer is None or not renderer.m_Enabled:continue
  batch_first=renderer.m_StaticBatchInfo.firstSubMesh
  batch_count=renderer.m_StaticBatchInfo.subMeshCount
  if batch_count and renderer.m_StaticBatchRoot.path_id:
   raise RuntimeError('Non-scene static batch root requires separate conversion')
 v,idx,col,mesh,uv=meshdata(d.m_Mesh)
 applied_matrix=np.eye(4) if batch_count else wm(t)
 v=v@applied_matrix[:3,:3].T+applied_matrix[:3,3]
 if len(v)==0:continue
 selected=range(batch_first,batch_first+batch_count) if batch_count else range(len(mesh.m_SubMeshes))
 if any(si>=len(mesh.m_SubMeshes) for si in selected):raise RuntimeError('Invalid static-batch submesh range')
 selected_ids=[]
 for si in selected:
  sub=mesh.m_SubMeshes[si]
  if sub.topology!=0:continue
  start=sub.firstByte//(2 if mesh.m_IndexFormat==0 else 4)
  selected_ids.extend(idx[start:start+sub.indexCount])
 if not selected_ids:continue
 bounds=v[selected_ids]
 if np.any(bounds[:,[0,2]].max(0)<lower) or np.any(bounds[:,[0,2]].min(0)>upper):continue
 added=0;material_tiles=[]
 if renderer:
  for mp in renderer.m_Materials:
   material=mp.read();key=(mp.deref().assets_file.name,mp.path_id)
   source_asset_files.add(key[0])
   if key not in tile_ids:
    tex=next((t.m_Texture for k,t in material.m_SavedProperties.m_TexEnvs if k=='_MainTex' and t.m_Texture.path_id),None)
    if tex:source_asset_files.add(tex.deref().assets_file.name)
    im=tex.read().image.convert('RGB').resize((64,64)) if tex else Image.new('RGB',(64,64),'white')
    tile_ids[key]=len(tiles);tiles.append(im);texture_names.append(material.m_Name)
   material_tiles.append(tile_ids[key])
 for local_si,si in enumerate(selected):
  sub=mesh.m_SubMeshes[si]
  if sub.topology!=0:continue
  start=sub.firstByte//(2 if mesh.m_IndexFormat==0 else 4)
  for ids in idx[start:start+sub.indexCount].reshape(-1,3):
   a=v[ids]
   if np.any(a[:,[0,2]].max(0)<lower) or np.any(a[:,[0,2]].min(0)>upper):continue
   if o.type.name=='MeshCollider':
    blocking.append(a)
    if go.m_Name.startswith('Walkable') or is_launch_object:collision.append(a)
   else:scene.append((np.column_stack([a,uv[ids]]),col[ids,:3].mean(0),material_tiles[min(local_si,len(material_tiles)-1)]));added+=1
 if added:instances.append({'object':go.m_Name,'mesh':mesh.m_Name,'triangles_before_clipping':added,'source_file':d.m_Mesh.deref().assets_file.name,'mesh_id':d.m_Mesh.path_id,'transform_path_id':t.object_reader.path_id,'source_world_matrix':applied_matrix.tolist(),'original_object_world_matrix':wm(t).tolist(),'static_batch_first_submesh':batch_first,'static_batch_submesh_count':batch_count,'source_world_bounds':[bounds.min(0).tolist(),bounds.max(0).tolist()]})
 if o.type.name=='MeshCollider':wall_instances.append({'component_path_id':o.path_id,'object':go.m_Name,'mesh_id':d.m_Mesh.path_id,'source_file':d.m_Mesh.deref().assets_file.name,'source_world_matrix':applied_matrix.tolist()})
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
  poly=clip(poly,axis,limits[axis][0],1)
  if not poly:break
  poly=clip(poly,axis,limits[axis][1],-1)
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
STEP=40;ORIGIN=-round(R*SCALE);N=2*(-ORIGIN)//STEP+1;grid=[]
for iz in range(N):
 row=[]
 for ix in range(N):
  x=spawn[0]-(ORIGIN+ix*STEP)/SCALE;z=spawn[2]+(ORIGIN+iz*STEP)/SCALE
  h=heights(x,z) if lower[0]<=x<=upper[0] and lower[1]<=z<=upper[1] else []
  row.append(round((float(h.max())-ground)*SCALE) if len(h) else -32768)
 grid.append(row)
assert grid[N//2][N//2]==0
used=sorted(set(tile_indices));remap={old:new for new,old in enumerate(used)}
tiles=[tiles[i] for i in used];texture_names=[texture_names[i] for i in used];tile_indices=[remap[i] for i in tile_indices]
assert len(tiles)<=16, 'expanded area exceeds the current atlas capacity'
# Partition rendering only. Collision proxies retain the unpartitioned surface,
# so optimizing draw cells does not alter the recovered collision adaptation.
wall_source_tri=[]
if args.scene=='level3':
 for a in blocking:
  poly=list(a)
  for axis in (0,2):
   poly=clip(poly,axis,limits[axis][0],1)
   if poly:poly=clip(poly,axis,limits[axis][1],-1)
   if not poly:break
  for j in range(1,len(poly)-1):
   pts=np.array([poly[0],poly[j],poly[j+1]])
   q=np.rint(np.column_stack([-(pts[:,0]-spawn[0])*SCALE,80-(pts[:,1]-ground)*SCALE,(pts[:,2]-spawn[2])*SCALE])).astype(int)
   if np.abs(q).max()>32767:raise ValueError('Collider wall exceeds short coordinates')
   wall_source_tri.append(q)
else:wall_source_tri=tri.copy()
patch_triangle_count=len(tri)
cell_size=640;cell_origin=-round(R*SCALE);cell_count=math.ceil(2*R*SCALE/cell_size)
buckets={}
for a,color,tc,tile in zip(tri,colors,uvs,tile_indices):
 poly=np.column_stack([a,tc]).astype(float)
 lo=poly[:,[0,2]].min(axis=0);hi=poly[:,[0,2]].max(axis=0)
 first=np.maximum(0,np.minimum(cell_count-1,np.floor((lo-cell_origin)/cell_size).astype(int)))
 upper=np.where(hi>lo,hi-1e-6,hi)
 last=np.maximum(first,np.minimum(cell_count-1,np.floor((upper-cell_origin)/cell_size).astype(int)))
 for cz in range(first[1],last[1]+1):
  for cx in range(first[0],last[0]+1):
   part=list(poly)
   for axis,index in ((0,cx),(2,cz)):
    part=clip(part,axis,cell_origin+index*cell_size,1)
    if part:part=clip(part,axis,min(round(R*SCALE),cell_origin+(index+1)*cell_size),-1)
    if not part:break
   for k in range(1,len(part)-1):
    pts=np.array([part[0],part[k],part[k+1]])
    xyz=np.rint(pts[:,:3]).astype(int)
    if not np.any(np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0])):continue
    uv=np.rint(pts[:,3:5]).astype(int).clip(0,255)
    buckets.setdefault((cz,cx),[]).append((xyz,color,uv,tile))
tri=[];colors=[];uvs=[];tile_indices=[];cells=[]
for (cz,cx),items in sorted(buckets.items()):
 start=len(tri)
 for xyz,color,tc,tile in items:
  tri.append(xyz);colors.append(color);uvs.append(tc);tile_indices.append(tile)
 cells.append([cell_origin+cx*cell_size,cell_origin+cz*cell_size,
               min(round(R*SCALE),cell_origin+(cx+1)*cell_size),
               min(round(R*SCALE),cell_origin+(cz+1)*cell_size),start,len(items),min(int(a[:,1].min()) for a,_,_,_ in items),max(int(a[:,1].max()) for a,_,_,_ in items)])
assert len(tri)<6000,len(tri)
s=f'/* Original {args.scene} spawn-area geometry; clipped offline. */\n'
s+='static const unsigned char world_colors[][3]={\n'+''.join('{%d,%d,%d},\n'%tuple(c) for c in colors)+'};\n'
s+='static const unsigned char world_uv[][6]={\n'+''.join('{'+','.join(map(str,u.flatten()))+'},\n' for u in uvs)+'};\n'
s+='static const unsigned char world_tile[]={'+','.join(map(str,tile_indices))+'};\n'
unique=list(dict.fromkeys(tuple(map(int,v)) for a in tri for v in a));lookup={v:i for i,v in enumerate(unique)}
s+='static const SVECTOR world_unique[]={'+''.join('{%d,%d,%d,0},'%v for v in unique)+'};\n'
s+='static const unsigned short world_corner_ids[][3]={'+''.join('{'+','.join(str(lookup[tuple(map(int,v))]) for v in a)+'},' for a in tri)+'};\n'
s+='#define WORLD_UNIQUE_COUNT %d\n'%len(unique)
s+='#define WORLD_TRIANGLE_COUNT %d\n'%len(tri)
s+='#define WORLD_CELL_COUNT %d\n'%len(cells)
s+='static const short world_cells[][8]={'+''.join('{'+','.join(map(str,c))+'},' for c in cells)+'};\n'
(P/'src/world_mesh.h').write_text(s)
# Conservative vertical-wall proxies: level3 uses solid static MeshColliders;
# level2 retains render-derived geometry. Longest XZ edge and vertical interval.
walls=set();wall_triangles=set()
for a in wall_source_tri:
 g=a.copy();g[:,1]=80-g[:,1]
 normal=np.cross(g[1]-g[0],g[2]-g[0])
 if 2*int(normal[1])**2 >= int(normal[0])**2+int(normal[2])**2:continue
 wall_triangles.add(tuple(map(int,g.flatten())))
 edges=[(g[i],g[(i+1)%3]) for i in range(3)]
 a,b=max(edges,key=lambda e:int(e[0][0]-e[1][0])**2+int(e[0][2]-e[1][2])**2)
 if np.sum((a[[0,2]]-b[[0,2]])**2)<16:continue
 ends=sorted([(int(a[0]),int(a[2])),(int(b[0]),int(b[2]))])
 walls.add((*ends[0],*ends[1],int(g[:,1].min()),int(g[:,1].max())))
walls=sorted(walls)
wall_triangles=sorted(wall_triangles)
if args.scene=='level3':
 (P/'src/world_wall_triangles.h').write_text('/* Original steep collider triangles; positive Y up. */\n#define WORLD_WALL_TRIANGLE_COUNT %d\nstatic const short world_wall_triangles[][9]={\n'%len(wall_triangles)+''.join('{'+','.join(map(str,t))+'},\n' for t in wall_triangles)+'};\n')
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
s=('#define WORLD_N %d\n#define WORLD_STEP %d\n#define WORLD_ORIGIN (%d)\nstatic const short world_heights[WORLD_N][WORLD_N]={\n'%(N,STEP,ORIGIN))+''.join('{'+','.join(map(str,row))+'},\n' for row in grid)+'};\n'
(P/'src/world_height.h').write_text(s)
report={'scene':args.scene,'area':'original bounded spawn vicinity','spawn':spawn.tolist(),'ground_height':ground,'source_radius_units':R,'world_scale':SCALE,'render_triangles':len(tri),'texture_materials':texture_names,'texture_format':'8-bit indexed 256x256 atlas, 64x64 repeating tiles','source_collision_triangles':len(collision),'wall_proxies':len(walls),'instances':instances,'heightfield':{'size':N,'step':STEP,'origin':ORIGIN,'missing_sentinel':-32768},'limitations':['single-valued heightfield','conservative steep-triangle wall proxies; not full capsule/triangle collision','original main textures; custom Unity shader effects omitted','actors and effects omitted', 'lava geometry and hazard behavior omitted','heightfield samples capped at spawn height + 6 source units','not full original level']}
source_hashes={}
if args.bounds is not None:report['source_bounds_units']=args.bounds
if args.scene=='level3':
 report['wall_collision_source']={'type':'original enabled solid static MeshColliders','instances':wall_instances,'source_triangles':len(blocking),'clipped_triangles':len(wall_source_tri),'exclusions':['Lava','triggers','disabled components or hierarchies','actors outside the converted static environment']}
for name in sorted(source_asset_files):
 matches=list(Path(args.data).rglob(name))
 if len(matches)!=1:raise RuntimeError('Cannot resolve source provenance file: '+name)
 path=matches[0];source_hashes[path.relative_to(args.data).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
if launch_root is not None:
 report['launchpad_component_path_id']=args.launchpad
 report['area']='original launchpad vicinity; dedicated traversal prototype'
if args.checkpoint is not None:
 report['checkpoint_component_path_id']=args.checkpoint
 report['area']='original checkpoint spawn vicinity; dedicated respawn prototype'
report['source_patch_triangles_before_render_partition']=patch_triangle_count
report['render_cells']={'size_world_units':cell_size,'count':len(cells),'draw_radius_world_units':1280}
report['source_files_sha256']=source_hashes
report['converter_unitypy_version']=UnityPy.__version__
floor_triangles=[]
if args.scene=='level3':
 for triangle in collision:
  poly=list(triangle)
  for axis in (0,2):
   poly=clip(poly,axis,limits[axis][0],1)
   if poly:poly=clip(poly,axis,limits[axis][1],-1)
   if not poly:break
  for i in range(1,len(poly)-1):
   pts=np.array([poly[0],poly[i],poly[i+1]])
   q=np.rint(np.column_stack([-(pts[:,0]-spawn[0])*SCALE,(pts[:,1]-ground)*SCALE,(pts[:,2]-spawn[2])*SCALE])).astype(int)
   if np.abs(q).max()>32767:raise RuntimeError('Floor triangle exceeds short coordinates')
   a,b,c=q
   if (b[2]-c[2])*(a[0]-c[0])+(c[0]-b[0])*(a[2]-c[2])==0:continue
   floor_triangles.append(q.tolist())
 assert floor_triangles
 (P/'src/world_floors.h').write_text('/* Original walkable collider triangles, bounded XZ; positive Y up. */\n#define WORLD_FLOOR_COUNT %d\nstatic const short world_floors[][9]={\n'%len(floor_triangles)+''.join('{'+','.join(str(v) for p in a for v in p)+'},\n' for a in floor_triangles)+'};\n')
 report['floor_surfaces']={'triangles':len(floor_triangles),'height_cap':None,'selection':'highest original collider surface at or below player step/landing ceiling','limitations':['point support only; no capsule sweep or overhead ceiling collision','integer-quantized original triangles']}

(P/'reports/world_conversion.json').write_text(json.dumps(report,indent=2))
(P/'assets/world_chunk_source.json').write_text(json.dumps({'report':report,'triangles':[a.tolist() for a in tri],'colors':[c.tolist() for c in colors],'heightfield':grid,'walls':walls,'wall_triangles':wall_triangles,'render_cells':cells,'floor_triangles':floor_triangles}))
print('World triangles:',len(tri),'collision source:',len(collision),'spawn ground:',ground,'instances:',len(instances))
