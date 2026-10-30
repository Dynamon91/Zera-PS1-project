"""Validate original Levium asset integrity, text, topology and independent source skinning."""
import argparse,hashlib,json,math,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(data=None):
 root=ROOT/'previews/levium';r=json.loads((root/'reports/levium.json').read_text());model=(root/'src/levium_model.h').read_text();script=(root/'src/levium_dialogue.h').read_text()
 assert sha(root/'src/levium_model.h')==r['model_header_sha256'] and sha(root/'src/levium_dialogue.h')==r['dialogue_header_sha256']
 def array(name):return list(map(int,re.findall(r'-?\d+',model.split(name+'[]')[1].split('={',1)[1].split('};')[0])))
 vertices=array('levium_vertices');faces=array('levium_faces');colors=array('levium_colors');uv=array('levium_uv');materials=array('levium_material')
 assert len(vertices)==r['mesh']['vertices']*3==3240 and len(faces)==r['mesh']['faces']*3==2718
 assert len(colors)==906*9 and len(uv)==906*6 and len(materials)==906 and set(materials)=={0,1,2}
 assert min(faces)>=0 and max(faces)<1080 and all(-32768<v<32768 for v in vertices)
 assert all(0<=c<=255 for c in colors+uv)
 assert r['mesh']['weight_sum_error']<1e-5 and r['mesh']['independent_skin_error']<1e-10 and r['mesh']['bones']==45
 assert r['component']==6279 and r['renderer']==5551 and r['mesh']['file']=='sharedassets2.assets' and r['mesh']['path_id']==82
 assert len(r['first']['sentences'])==6 and r['repeat']['sentences']==['Be careful out there.']
 assert len(r['pages'])==7
 strip=lambda s:re.sub(r'\s+','',s)
 assert strip(''.join(r['pages'][:6]))==strip(''.join(r['first']['sentences'])) and r['pages'][6]=='Be careful out there.'
 actual_pages=json.loads('['+script.split('levium_pages[]={')[1].split('};')[0]+']');assert actual_pages==r['pages']
 assert all(v['name']=='Silence' for v in r['voice_references'])
 voice=json.loads((root/'reports/voice_check.json').read_text());assert voice['source_clip']=={'file':'resources.assets','path_id':583,'name':'Silence'} and voice['decoded_peak_pcm16']<=1
 assert voice['source_files_sha256']['resources.assets']==r['source_files_sha256']['resources.assets']
 callback=r['completion_callbacks'][0];assert callback['target']==[0,6279] and callback['method']=='NewDialogue' and callback['state']==2
 assert r['trigger']['axis_endpoints']==[[4920,-300,202],[4899,-300,269]]
 update=next(m for m in r['methods'] if m['owner']=='NewZera.NPCDialogue' and m['name']=='Update')
 assert any(i['opcode']=='isinst' and i['operand'].get('symbol')=='NewZera.Zera.States.Ground' for i in update['instructions'])
 assert any(i['opcode']=='callvirt' and isinstance(i['operand'],dict) and i['operand'].get('symbol')=='UnityEngine.Events.UnityEvent::Invoke' for i in update['instructions'])
 if data is not None:
  import UnityPy,numpy as np
  from UnityPy.helpers.MeshHelper import MeshHandler
  for name,digest in {**r['source_files_sha256'],**voice['source_files_sha256']}.items():assert sha(Path(data)/name)==digest,name
  env=UnityPy.load(str(data));f=next(f for f in env.files.values() if getattr(f,'name',None)=='level2');sm=f.objects[5551].read();mesh=sm.m_Mesh.read();h=MeshHandler(mesh);h.process();cache={}
  def matrix(t):
   key=t.object_reader.path_id
   if key not in cache:
    p,q,s=t.m_LocalPosition,t.m_LocalRotation,t.m_LocalScale;x,y,z,w=q.x,q.y,q.z,q.w;k=2/(x*x+y*y+z*z+w*w)
    rot=np.array([[1-k*(y*y+z*z),k*(x*y-z*w),k*(x*z+y*w)],[k*(x*y+z*w),1-k*(x*x+z*z),k*(y*z-x*w)],[k*(x*z-y*w),k*(y*z+x*w),1-k*(x*x+y*y)]])
    m=np.eye(4);m[:3,:3]=rot@np.diag([s.x,s.y,s.z]);m[:3,3]=[p.x,p.y,p.z]
    if t.m_Father.path_id:m=matrix(t.m_Father.read())@m
    cache[key]=m
   return cache[key]
  bind=np.array([[[getattr(m,f'e{a}{b}') for b in range(4)] for a in range(4)] for m in mesh.m_BindPose]);world=[matrix(p.read()) for p in sm.m_Bones];weights=h.m_BoneWeights;indices=h.m_BoneIndices;points=[]
  for i,v in enumerate(h.m_Vertices):
   point=np.array([*v,1.]);q=np.zeros(4)
   for lane in range(4):q+=weights[i][lane]*(world[indices[i][lane]]@bind[indices[i][lane]]@point)
   points.append((q[:3]-r['source_position'])*[-80,-80,80])
  assert np.max(abs(np.rint(points).astype(int)-np.array(vertices).reshape(-1,3)))<=1
  assert sha(Path(data)/'level2')==r['source_files_sha256']['level2']
 return {'vertices':1080,'faces':906,'bones':45,'source_checked':data is not None,'dialogue_sentences':6,'first_pages':6,'repeat_pages':1,'model_header_sha256':r['model_header_sha256'],'limitations':r['limitations']}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data',type=Path);a=p.parse_args();print(json.dumps(check(a.data),indent=2))
