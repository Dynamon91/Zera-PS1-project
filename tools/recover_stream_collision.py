"""Recover complete active Dreary Valley solid MeshColliders into CD sectors.
Physics retains the established 80 units/Unity unit; atlas rendering uses 40.
"""
import json,hashlib,math,struct
from collections import Counter,defaultdict
from pathlib import Path
import argparse,numpy as np,UnityPy
from scipy.spatial.transform import Rotation
from UnityPy.helpers.MeshHelper import MeshHandler
from recover_world_atlas import clip,digest
ROOT=Path(__file__).resolve().parents[1];CELL=1280;RECORD=struct.Struct('<9hH')

def recover(data,out,scene="level3"):
 e=UnityPy.load(str(data));f=next(f for f in e.files.values() if getattr(f,'name',None)==scene);cache={};meshes={};deps={scene}
 def wm(t):
  key=(t.object_reader.assets_file.name,t.object_reader.path_id)
  if key not in cache:
   p,q,s=t.m_LocalPosition,t.m_LocalRotation,t.m_LocalScale;m=np.eye(4);m[:3,:3]=Rotation.from_quat([q.x,q.y,q.z,q.w]).as_matrix()@np.diag([s.x,s.y,s.z]);m[:3,3]=[p.x,p.y,p.z]
   if t.m_Father.path_id:m=wm(t.m_Father.read())@m
   cache[key]=m
  return cache[key]
 def tf(go):return next(c.component.read() for c in go.m_Component if c.component.deref().type.name=='Transform')
 start=next(o.read() for o in f.objects.values() if o.type.name=='Transform' and o.read().m_GameObject.read().m_Name.startswith('_StartSpawnPoint'))
 origin=wm(start)[:3,3];chunks=defaultdict(list);instances=[];excluded=Counter();source_area=partition_area=lost_area=0.;source_count=0;minimum=0
 for o in sorted(f.objects.values(),key=lambda o:o.path_id):
  if o.type.name!='MeshCollider':continue
  d=o.read();go=d.m_GameObject.read();t=tf(go);ancestor=t;active=bool(d.m_Enabled)
  while True:
   active=active and bool(ancestor.m_GameObject.read().m_IsActive)
   if not ancestor.m_Father.path_id:break
   ancestor=ancestor.m_Father.read()
  root=ancestor.m_GameObject.read().m_Name
  if not active or d.m_IsTrigger or not d.m_Mesh.path_id:excluded['disabled_trigger_or_empty']+=1;continue
  if root in ['_Zera','_Kiwi','NPCs','HUD Bits'] or go.m_Name.startswith('Lava'):excluded['actor_or_lava']+=1;continue
  key=(d.m_Mesh.deref().assets_file.name,d.m_Mesh.path_id);deps.add(key[0])
  if key not in meshes:
   m=d.m_Mesh.read();h=MeshHandler(m);h.process();meshes[key]=(m,np.array(h.m_Vertices),np.array(h.m_IndexBuffer))
  mesh,v,idx=meshes[key];matrix=wm(t);world=v[:,:3]@matrix[:3,:3].T+matrix[:3,3];q=(world-origin)*80;q[:,0]*=-1
  added=0
  for sub in mesh.m_SubMeshes:
   if sub.topology!=0:continue
   begin=sub.firstByte//(2 if mesh.m_IndexFormat==0 else 4)
   for ids in idx[begin:begin+sub.indexCount].reshape(-1,3):
    tri=q[ids];normal=np.cross(tri[1]-tri[0],tri[2]-tri[0]);n2=normal@normal
    if n2<1e-12:continue
    steep=2*normal[1]**2<normal[0]**2+normal[2]**2
    flags=(1 if go.m_Name.startswith('Walkable') or not steep else 0)|(2 if steep else 0)
    source_count+=1;added+=1;source_area+=math.sqrt(n2)/2;minimum=min(minimum,int(np.floor(tri[:,1].min())))
    lo=np.floor(tri[:,[0,2]].min(0)/CELL).astype(int);hi=np.maximum(lo,np.floor((tri[:,[0,2]].max(0)-1e-7)/CELL).astype(int))
    for tz in range(lo[1],hi[1]+1):
     for tx in range(lo[0],hi[0]+1):
      poly=list(tri)
      for axis,tile in [(0,tx),(2,tz)]:
       poly=clip(poly,axis,tile*CELL,1)
       if poly:poly=clip(poly,axis,(tile+1)*CELL,-1)
       if not poly:break
      for k in range(1,len(poly)-1):
       a=np.array([poly[0],poly[k],poly[k+1]]);area=float(np.linalg.norm(np.cross(a[1]-a[0],a[2]-a[0]))/2);partition_area+=area
       xyz=np.rint(a).astype(int)
       if not np.any(np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0])):lost_area+=area;continue
       chunks[tx,tz].append((xyz,flags))
  if added:instances.append({'component':o.path_id,'object':go.m_Name,'root':root,'mesh_file':key[0],'mesh_id':key[1],'matrix':matrix.tolist(),'source_triangles':added,'convex':bool(d.m_Convex)})
 rows=[];payloads=[]
 for (tx,tz),triangles in sorted(chunks.items()):
  ys=[int(y) for v,_ in triangles for y in v[:,1]];center=[tx*CELL+CELL//2,((min(ys)+max(ys))//2//256)*256,tz*CELL+CELL//2];payload=bytearray()
  for xyz,flags in triangles:
   local=xyz-np.array(center)
   if abs(local).max()>32767:raise ValueError('Collider sector exceeds signed local coordinates')
   payload+=RECORD.pack(*local.ravel(),flags)
  rows.append({'tx':tx,'tz':tz,'center':center,'triangles':len(triangles),'sha256':hashlib.sha256(payload).hexdigest()});payloads.append(payload)
 counts={(r['tx'],r['tz']):r['triangles'] for r in rows};centers={(x+dx,z+dz) for x,z in counts for dx in range(-2,3) for dz in range(-2,3)}
 maximum=max(sum(counts.get((x+dx,z+dz),0) for dx in range(-2,3) for dz in range(-2,3)) for x,z in centers);capacity=math.ceil(maximum/256)*256
 if capacity>20000:raise ValueError('Collision RAM budget exceeded')
 tag=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).digest()[:16];blob=bytearray(b'ZCOL0001'+tag+struct.pack('<II',CELL,len(rows)));blob+=bytes(2048-len(blob))
 for r,payload in zip(rows,payloads):
  raw=struct.pack('<4i',int(scene[5:])-2,r['tx'],r['tz'],r['triangles'])+payload;r['sector']=len(blob)//2048;r['sectors']=(len(raw)+2047)//2048;blob+=raw+bytes((-len(raw))%2048)
 for sub in ['src','assets','reports']:(out/sub).mkdir(parents=True,exist_ok=True)
 (out/'assets/COLLIDE.DAT').write_bytes(blob)
 s='/* Active original level3 MeshColliders, physics units 80, positive Y up. */\n#define STREAM_CELL 1280\n#define STREAM_COLLISION_CAPACITY %d\n#define STREAM_COLLISION_TILES %d\n#define STREAM_FALL_LIMIT %d\n'%(capacity,len(rows),minimum-700)
 if scene!='level3':s=s.replace('level3',scene)+f'#define STREAM_SCENE_ID {int(scene[5:])-2}\n'
 s+='static const unsigned char stream_collision_tag[16]={'+','.join(map(str,tag))+'};\n'
 s+='static const StreamTile stream_collision_tiles[]={\n'+''.join('{%d,%d,{%d,%d,%d},%d,%d,%d},\n'%(r['tx'],r['tz'],*r['center'],r['triangles'],r['sector'],r['sectors']) for r in rows)+'};\n'
 (out/'src/collision_catalog.h').write_text(s)
 paths={}
 deps.update(p.relative_to(data).as_posix() for p in data.rglob('*.resS'))
 for name in deps:
  matches=[p for p in data.rglob(name) if p.is_file()]
  if len(matches)!=1:raise ValueError('Source not unique: '+name)
  paths[matches[0].relative_to(data).as_posix()]=digest(matches[0])
 report={'scene':scene,'source_origin':origin.tolist(),'physics_scale':80,'render_scale':40,'cell':CELL,'source_triangles':source_count,'exported_triangles':sum(r['triangles'] for r in rows),'maximum_resident_triangles':maximum,'capacity':capacity,'fall_limit':minimum-700,'partition_area_relative_error':abs(source_area-partition_area)/source_area,'quantized_lost_area_fraction':lost_area/source_area,'instances':instances,'excluded':dict(excluded),'tiles':rows,'source_files_sha256':paths,'data_sha256':digest(out/'assets/COLLIDE.DAT'),'catalog_sha256':digest(out/'src/collision_catalog.h'),'limitations':['Active solid MeshColliders only; box/sphere colliders and runtime motion absent','Lava and actor colliders excluded; original hazards/behaviors not implemented','Convex cooking is not reproduced; raw source MeshCollider triangles are used']}
 (out/'reports/stream_collision.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['source_triangles','exported_triangles','maximum_resident_triangles','capacity','fall_limit']}))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('data',type=Path);p.add_argument('--scene',choices=['level2','level3'],default='level3');p.add_argument('--output',type=Path,default=ROOT/'previews/walk');a=p.parse_args();recover(a.data,a.output,a.scene)
