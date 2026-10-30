"""Validate streamed solid-collider sectors and independently check source transforms."""
import argparse,hashlib,json,math,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def check(data=None,area=None):
 root=Path(area) if area else ROOT/'previews/walk';r=json.loads((root/'reports/stream_collision.json').read_text());blob=(root/'assets/COLLIDE.DAT').read_bytes();header=(root/'src/collision_catalog.h').read_text()
 assert sha(root/'assets/COLLIDE.DAT')==r['data_sha256'] and sha(root/'src/collision_catalog.h')==r['catalog_sha256']
 assert r['physics_scale']==80 and r['render_scale']==40
 assert blob[:8]==b'ZCOL0001' and struct.unpack_from('<II',blob,24)==(1280,len(r['tiles']))
 tag=bytes(map(int,re.search(r'stream_collision_tag\[16\]=\{([^}]+)\}',header).group(1).split(',')));assert tag==blob[8:24]
 assert int(re.search(r'STREAM_COLLISION_CAPACITY (\d+)',header).group(1))==r['capacity']
 rows=header.split('static const StreamTile stream_collision_tiles[]={')[1].split('};')[0].strip().splitlines();assert len(rows)==len(r['tiles'])
 counts={};previous=2048
 for row,t in zip(rows,r['tiles']):
  assert list(map(int,re.findall(r'-?\d+',row)))==[t['tx'],t['tz'],*t['center'],t['triangles'],t['sector'],t['sectors']]
  start=t['sector']*2048;end=start+t['sectors']*2048;assert start==previous and end<=len(blob)
  assert struct.unpack_from('<4i',blob,start)==(int(r['scene'][5:])-2,t['tx'],t['tz'],t['triangles'])
  payload=blob[start+16:start+16+20*t['triangles']];assert hashlib.sha256(payload).hexdigest()==t['sha256']
  for v in struct.iter_unpack('<9hH',payload):
   assert v[-1] in (1,2,3)
   for k in range(3):assert -640<=v[k*3]<=640 and -640<=v[k*3+2]<=640
  assert (t['tx'],t['tz']) not in counts;counts[t['tx'],t['tz']]=t['triangles'];previous=end
 assert previous==len(blob) and sum(counts.values())==r['exported_triangles']
 centers={(x+dx,z+dz) for x,z in counts for dx in range(-2,3) for dz in range(-2,3)}
 maximum=max(sum(counts.get((x+dx,z+dz),0) for dx in range(-2,3) for dz in range(-2,3)) for x,z in centers)
 assert maximum==r['maximum_resident_triangles']<=r['capacity']<=20000
 assert r['partition_area_relative_error']<1e-9 and r['quantized_lost_area_fraction']<1e-5
 atlas=json.loads((ROOT/'previews/atlas/reports/world_atlas.json').read_text());assert atlas['scale']==40;origin=next(s['source_origin'] for s in atlas['scenes'] if s['scene']==r['scene']);assert origin==r['source_origin']
 if data is not None:source_check(Path(data),r)
 return {'scene':r['scene'],'source_triangles':r['source_triangles'],'sectors':len(r['tiles']),'maximum_resident_triangles':maximum,'capacity':r['capacity'],'data_sha256':r['data_sha256'],'convex_instances':sum(i['convex'] for i in r['instances']),'original_source_checked':data is not None}
def source_check(data,r):
 import UnityPy,numpy as np
 from UnityPy.helpers.MeshHelper import MeshHandler
 for name,digest in r['source_files_sha256'].items():assert sha(data/name)==digest
 e=UnityPy.load(str(data));f=next(f for f in e.files.values() if getattr(f,'name',None)==r['scene']);cache={}
 def wm(t):
  key=(t.object_reader.assets_file.name,t.object_reader.path_id)
  if key not in cache:
   p,q,s=t.m_LocalPosition,t.m_LocalRotation,t.m_LocalScale;x,y,z,w=q.x,q.y,q.z,q.w;k=2/(x*x+y*y+z*z+w*w)
   rot=np.array([[1-k*(y*y+z*z),k*(x*y-z*w),k*(x*z+y*w)],[k*(x*y+z*w),1-k*(x*x+z*z),k*(y*z-x*w)],[k*(x*z-y*w),k*(y*z+x*w),1-k*(x*x+y*y)]])
   m=np.eye(4);m[:3,:3]=rot@np.diag([s.x,s.y,s.z]);m[:3,3]=[p.x,p.y,p.z]
   if t.m_Father.path_id:m=wm(t.m_Father.read())@m
   cache[key]=m
  return cache[key]
 origin=next(wm(o.read())[:3,3] for o in f.objects.values() if o.type.name=='Transform' and o.read().m_GameObject.read().m_Name.startswith('_StartSpawnPoint'));assert np.max(abs(origin-r['source_origin']))<1e-7
 for inst in r['instances']:
  d=f.objects[inst['component']].read();assert d.m_Enabled and not d.m_IsTrigger and bool(d.m_Convex)==inst['convex']
  go=d.m_GameObject.read();assert go.m_Name==inst['object'];assert d.m_Mesh.path_id==inst['mesh_id'] and d.m_Mesh.deref().assets_file.name==inst['mesh_file']
  t=next(c.component.read() for c in go.m_Component if c.component.deref().type.name=='Transform');ancestor=t
  while True:
   assert ancestor.m_GameObject.read().m_IsActive
   if not ancestor.m_Father.path_id:break
   ancestor=ancestor.m_Father.read()
  assert ancestor.m_GameObject.read().m_Name==inst['root'];matrix=wm(t);assert np.max(abs(matrix-np.array(inst['matrix'])))<1e-6
  mesh=d.m_Mesh.read();h=MeshHandler(mesh);h.process();v=np.array(h.m_Vertices)[:,:3]@matrix[:3,:3].T+matrix[:3,3];v=(v-origin)*80;v[:,0]*=-1;idx=np.array(h.m_IndexBuffer);count=0
  for sub in mesh.m_SubMeshes:
   if sub.topology!=0:continue
   begin=sub.firstByte//(2 if mesh.m_IndexFormat==0 else 4);points=v[idx[begin:begin+sub.indexCount].reshape(-1,3)]
   normals=np.cross(points[:,1]-points[:,0],points[:,2]-points[:,0]);count+=int(np.count_nonzero((normals*normals).sum(1)>1e-12))
  assert count==inst['source_triangles']
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data',type=Path);p.add_argument('--area',type=Path);a=p.parse_args();print(json.dumps(check(a.data,a.area),indent=2))
