"""Recover generic Unity transform curves and bake skinning offline.
Input: extracted Unity Data folder. Output: source sidecar and fixed-point frames.
Uses streamed cubic coefficients, dense samples and constant channels. Only
position, quaternion, scale and Euler transform bindings are supported.
"""
import sys,json,math,struct,zlib
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
import UnityPy
from UnityPy.helpers.MeshHelper import MeshHandler
P=Path(__file__).resolve().parents[1]
E=UnityPy.load(sys.argv[1]);objects=list(E.objects)
sm=next(o.read() for o in objects if o.type.name=='SkinnedMeshRenderer' and o.read().m_Mesh.path_id==314 and o.read().m_Mesh.deref().assets_file.name=='resources.assets')
mesh=sm.m_Mesh.read();h=MeshHandler(mesh);h.process()
root=sm.m_GameObject.read().m_Component[0].component.read()
while root.m_GameObject.read().m_Name!='Zera':root=root.m_Father.read()
root_id=root.object_reader.path_id
nodes={}
def gather(t):
 id=t.object_reader.path_id
 if id==root_id:return
 if id in nodes:return
 gather(t.m_Father.read())
 parent=t.m_Father.path_id
 path=t.m_GameObject.read().m_Name
 if parent!=root_id:path=nodes[parent]['path']+'/'+path
 nodes[id]={'parent':parent,'path':path,'pos':[t.m_LocalPosition.x,t.m_LocalPosition.y,t.m_LocalPosition.z],'quat':[t.m_LocalRotation.x,t.m_LocalRotation.y,t.m_LocalRotation.z,t.m_LocalRotation.w],'scale':[t.m_LocalScale.x,t.m_LocalScale.y,t.m_LocalScale.z]}
for b in sm.m_Bones:gather(b.read())
mt=sm.m_GameObject.read().m_Component[0].component.read();gather(mt)
def gather_children(t):
 for child in t.m_Children:
  ct=child.read();gather(ct);gather_children(ct)
gather_children(root)
crc={zlib.crc32(n['path'].encode()):i for i,n in nodes.items()}
# Also hash root as empty path.
crc[0]=root_id
bind=np.array([[[getattr(m,f'e{r}{c}') for c in range(4)] for r in range(4)] for m in mesh.m_BindPose])
verts=np.array(h.m_Vertices);v4=np.concatenate([verts,np.ones((len(verts),1))],axis=1)
weights=np.array(h.m_BoneWeights);indices=np.array(h.m_BoneIndices,dtype=int)
bones=[b.path_id for b in sm.m_Bones]
def matrix(pos,quat,scale):
 m=np.eye(4);m[:3,:3]=Rotation.from_quat(quat).as_matrix()@np.diag(scale);m[:3,3]=pos;return m

def globals_for(values):
 glob={root_id:np.eye(4)}
 for id,n in nodes.items():
  pos=values.get((id,1),n['pos']);scale=values.get((id,3),n['scale'])
  if (id,4) in values:
   x,y,z=values[id,4];q=Rotation.from_euler('zxy',[z,x,y],degrees=True).as_quat()
  else:q=values.get((id,2),n['quat'])
  q=np.array(q);q=q/np.linalg.norm(q)
  glob[id]=glob[n['parent']]@matrix(pos,q,scale)
 return glob
base=globals_for({})
check=np.array([np.linalg.inv(base[mt.object_reader.path_id])@base[b]@bind[j] for j,b in enumerate(bones)])
print('Default-pose bind identity max error',float(np.max(np.abs(check-np.eye(4)))))

weight_error=float(np.max(np.abs(weights.sum(axis=1)-1)))
assert weight_error<1e-4
# Source OBJ uses mirrored X, matching convert_character.py.
objv=[]
for l in (P/'assets/recovered_meshes/resources_assets_314_Cube_001.obj').read_text().splitlines():
 if l.startswith('v '):objv.append(tuple(map(float,l.split()[1:4])))
objv=np.array(objv);lo=objv.min(axis=0);hi=objv.max(axis=0);scale=160/(hi[1]-lo[1]);center=(lo+hi)/2
q=np.rint(np.column_stack([(objv[:,0]-center[0])*scale,-(objv[:,1]-lo[1])*scale,(objv[:,2]-center[2])*scale])).astype(int)
keys=list(dict.fromkeys(map(tuple,q)));rep=np.array([next(i for i,x in enumerate(q) if tuple(x)==k) for k in keys]);assert len(rep)==411
allframes=[];meta=[];sourceclips=[];unmatched=set()
for clipid in [522,525,523,521]:
 clip=next(o.read() for o in objects if o.assets_file.name=='resources.assets' and o.path_id==clipid)
 c=clip.m_MuscleClip.m_Clip.data;data=struct.pack('<%dI'%len(c.m_StreamedClip.data),*c.m_StreamedClip.data)
 curves=[[] for _ in range(c.m_StreamedClip.curveCount)];off=0
 while off<len(data):
  t,n=struct.unpack_from('<fi',data,off);off+=8
  for _ in range(n):
   idx,*coef=struct.unpack_from('<i4f',data,off);off+=20;curves[idx].append((t,coef))
 dense=c.m_DenseClip;const=c.m_ConstantClip.data
 channels=[]
 for b in clip.m_ClipBindingConstant.genericBindings:
  count={1:3,2:4,3:3,4:3}.get(b.attribute,1)
  node=crc.get(b.path)
  if node is None:unmatched.add(b.path)
  channels.append((node,b.attribute,count))
 count=sum(x[2] for x in channels)
 assert count==len(curves)+dense.m_CurveCount+len(const),(count,len(curves),len(const))
 duration=clip.m_MuscleClip.m_StopTime;frames=max(2,math.ceil(duration*12));start=len(allframes)
 sourceclips.append({'name':clip.m_Name,'object_id':clipid,'duration':duration,'bindings':channels,'streamed':curves,'dense':{'count':dense.m_CurveCount,'samples':dense.m_SampleArray,'rate':dense.m_SampleRate},'constant':const})
 for frame in range(frames):
  t=duration*frame/frames;vals=[]
  for keys1 in curves:
   # Select interval, evaluating serialized cubic at elapsed time.
   valid=[k for k in keys1 if k[0]<=t];kt,co=valid[-1] if valid else keys1[0];dt=t-kt if math.isfinite(kt) and abs(kt)<1e20 else 0
   vals.append(((co[0]*dt+co[1])*dt+co[2])*dt+co[3])
  if dense.m_CurveCount:
   ix=min(dense.m_FrameCount-1,max(0,round((t-dense.m_BeginTime)*dense.m_SampleRate)))
   vals.extend(dense.m_SampleArray[ix*dense.m_CurveCount:(ix+1)*dense.m_CurveCount])
  vals.extend(const);values={};ix=0
  for id,attr,n in channels:
   if id is not None and id!=root_id:values[id,attr]=vals[ix:ix+n]
   ix+=n
  glob=globals_for(values);invmesh=np.linalg.inv(glob[mt.object_reader.path_id]);skin=np.array([glob[b]@bind[j] for j,b in enumerate(bones)])
  result=np.zeros((len(verts),4))
  for slot in range(4):result+=np.einsum('nij,nj->ni',skin[indices[:,slot]],v4)*weights[:,slot,None]
  v=result[:,:3];v[:,0]*=-1
  allframes.append(v[rep].copy())
 meta.append({'name':clip.m_Name,'first':start,'frames':frames,'duration':duration})
 print(clip.m_Name,frames,'frames')
assert not unmatched,unmatched
# Normalize all clips together in animator-root space, grounding the idle feet.
ref=allframes[0];reflo=ref.min(axis=0);refhi=ref.max(axis=0)
scale=160/(refhi[1]-reflo[1]);cx=(reflo[0]+refhi[0])/2;cz=(reflo[2]+refhi[2])/2
allframes=[np.rint(np.column_stack([(v[:,0]-cx)*scale,-(v[:,1]-reflo[1])*scale,(v[:,2]-cz)*scale])).astype(int) for v in allframes]
assert all(np.isfinite(f).all() and np.abs(f).max()<16000 for f in allframes)
s='/* Original Unity clip skinning baked offline at ~12 Hz. */\nstatic const AnimPoint zera_anim[][411]={\n'
for f in allframes:s+='{'+''.join('{%d,%d,%d,0},'%tuple(v) for v in f)+'},\n'
s+='};\nstatic const unsigned short zera_anim_start[]={'+','.join(str(x['first']) for x in meta)+'};\n'
s+='static const unsigned short zera_anim_count[]={'+','.join(str(x['frames']) for x in meta)+'};\n'
s+='static const unsigned short zera_anim_ticks[]={'+','.join(str(round(x['duration']*30)) for x in meta)+'};\n'
(P/'src/zera_anim.h').write_text(s)
(P/'assets/character_animation_source.json').write_text(json.dumps({'nodes':nodes,'bones':bones,'bind':bind.tolist(),'vertices':verts.tolist(),'weights':weights.tolist(),'indices':indices.tolist(),'clips':sourceclips}))
(P/'reports/animation_conversion.json').write_text(json.dumps({'clips':meta,'total_frames':len(allframes),'weight_sum_max_error':weight_error,'packed_vertices':411,'unmatched_bindings':list(unmatched),'default_pose_differs_from_bind_pose':True,'normalization':'animator-root space; idle foot height; same scale for all clips','method':'offline linear blend skinning, sampled transform curves, ~12 Hz integer vertex frames','limitations':['original transition graph not recovered','texture overlays omitted','root motion ignored','no original-Unity visual reference comparison yet']},indent=2))
