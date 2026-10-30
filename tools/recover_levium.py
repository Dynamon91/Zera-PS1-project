"""Recover Levium's original dialogue, trigger and posed skinned mesh without running game code."""
import argparse,hashlib,json,math,struct,textwrap
from pathlib import Path
import dnfile,UnityPy,numpy as np
from PIL import Image
from UnityPy.helpers.MeshHelper import MeshHandler
from UnityPy.classes import PPtr
from scipy.spatial.transform import Rotation
import recover_gameplay
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
class Reader:
 def __init__(self,b,p=32):self.b=b;self.p=p
 def i(self):v=struct.unpack_from('<i',self.b,self.p)[0];self.p+=4;return v
 def s(self):
  n=self.i();assert 0<=n<=len(self.b)-self.p
  v=self.b[self.p:self.p+n].decode('utf8');self.p=(self.p+n+3)&~3;return v
 def ptr(self):v=struct.unpack_from('<iq',self.b,self.p);self.p+=12;return list(v)
 def ptrs(self):n=self.i();assert 0<=n<=1000;return [self.ptr() for _ in range(n)]
 def dialogue(self):
  name=self.s();clips=self.ptrs();positions=self.ptrs();n=self.i();assert n==len(clips)==len(positions)
  return {'name':name,'clips':clips,'positions':positions,'sentences':[self.s() for _ in range(n)]}
def recover(data):
 data=Path(data);reference=json.loads((ROOT/'reports/gameplay_recovery.json').read_text())
 for name in ['level2','Managed/Assembly-CSharp.dll']:assert sha((data/name).read_bytes())==reference['source_file_sha256'][name],name
 env=UnityPy.load(str(data));f=next(f for f in env.files.values() if getattr(f,'name',None)=='level2');deps={'level2','Managed/Assembly-CSharp.dll'};cache={}
 def wm(t):
  key=(t.object_reader.assets_file.name,t.object_reader.path_id)
  if key not in cache:
   p,q,s=t.m_LocalPosition,t.m_LocalRotation,t.m_LocalScale;m=np.eye(4);m[:3,:3]=Rotation.from_quat([q.x,q.y,q.z,q.w]).as_matrix()@np.diag([s.x,s.y,s.z]);m[:3,3]=[p.x,p.y,p.z]
   if t.m_Father.path_id:m=wm(t.m_Father.read())@m
   cache[key]=m
  return cache[key]
 def tf(go):return next(c.component.read() for c in go.m_Component if c.component.deref().type.name=='Transform')
 def describe(ptr):
  fid,pid=ptr
  if not pid:return None
  p=PPtr(m_FileID=fid,m_PathID=pid,assetsfile=f);o=p.deref();deps.add(o.assets_file.name);d=o.read(check_read=False)
  result={'file':o.assets_file.name,'path_id':pid,'type':o.type.name}
  if o.type.name=='GameObject':result.update(name=d.m_Name,position=wm(tf(d))[:3,3].tolist(),matrix=wm(tf(d)).tolist())
  elif o.type.name=='AudioClip':result.update(name=d.m_Name,length=d.m_Length)
  return result
 npc=f.objects[6279];d=npc.read(check_read=False);assert d.m_Script.read().m_ClassName=='NPCDialogue';deps.add(d.m_Script.deref().assets_file.name)
 go=d.m_GameObject.read();ancestor=tf(go);assert d.m_Enabled
 while True:
  assert ancestor.m_GameObject.read().m_IsActive
  if not ancestor.m_Father.path_id:break
  ancestor=ancestor.m_Father.read()
 raw=npc.get_raw_data();r=Reader(raw);weak=r.i();hit=r.ptr();was_damaged=r.i();damage_time=r.i();r.p+=12;animator=r.ptr();talk=r.ptr();first=r.dialogue();repeat=r.dialogue();prompt=r.ptr();flags=[r.i() for _ in range(4)];assert flags==[0,0,0,0]
 callbacks=[];n=r.i()
 for _ in range(n):
  target=r.ptr();method=r.s();mode=r.i();obj=r.ptr();objtype=r.s();intarg=r.i();floatarg=r.i();stringarg=r.s();boolarg=r.i();state=r.i()
  callbacks.append({'target':target,'method':method,'mode':mode,'object_argument':obj,'object_type':objtype,'int_argument':intarg,'float_argument_bits':floatarg,'string_argument':stringarg,'bool_argument':boolarg,'state':state})
 essence=r.ptr();assert r.p==len(raw),(r.p,len(raw));assert callbacks[0]['method']=='NewDialogue' and callbacks[0]['target']==[0,6279]
 origin=json.loads((ROOT/'previews/cosmic/reports/stream_collision.json').read_text())['source_origin'];origin=np.array(origin)
 def physical(p):return np.rint((np.array(p)-origin)*np.array([-80,80,80])).astype(int).tolist()
 talk_info=describe(talk);camera=describe(first['positions'][0]);assert all(p==first['positions'][0] for p in first['positions']+repeat['positions'])
 voice=[describe(p) for p in first['clips']+repeat['clips']];assert all(v['name']=='Silence' for v in voice)
 trigger=f.objects[5466];collider=trigger.read();assert collider.m_IsTrigger and collider.m_Enabled and collider.m_Direction==1
 ct=wm(tf(collider.m_GameObject.read()));center=ct@np.array([collider.m_Center.x,collider.m_Center.y,collider.m_Center.z,1]);scale=np.linalg.norm(ct[:3,:3],axis=0);assert abs(scale[0]-scale[2])<1e-6
 radius=float(collider.m_Radius*max(scale[0],scale[2]));height=max(2*radius,float(collider.m_Height*scale[1]));axis=ct[:3,1]/scale[1];segment=axis*(height/2-radius);ends=[physical(center[:3]-segment),physical(center[:3]+segment)];assert abs(axis[1])<1e-7
 sm=f.objects[5551].read();assert sm.m_Mesh.path_id==82 and sm.m_Mesh.deref().assets_file.name=='sharedassets2.assets';mesh=sm.m_Mesh.read();deps.add(sm.m_Mesh.deref().assets_file.name);h=MeshHandler(mesh);h.process();v=np.array(h.m_Vertices);v4=np.column_stack([v,np.ones(len(v))]);weights=np.array(h.m_BoneWeights);indices=np.array(h.m_BoneIndices,dtype=int)
 assert np.max(abs(weights.sum(1)-1))<1e-5 and np.all(weights>=0) and np.max(indices)<len(sm.m_Bones)
 bind=np.array([[[getattr(m,f'e{row}{col}') for col in range(4)] for row in range(4)] for m in mesh.m_BindPose]);boneworld=np.array([wm(p.read()) for p in sm.m_Bones]);skin=boneworld@bind;posed=np.zeros((len(v),4))
 for lane in range(4):posed+=weights[:,lane,None]*np.einsum('nij,nj->ni',skin[indices[:,lane]],v4)
 assert np.max(abs(posed[:,3]-1))<1e-5
 anchor=wm(tf(go))[:3,3];local=(posed[:,:3]-anchor)*np.array([-80,-80,80]);packed=np.rint(local).astype(int);assert abs(packed).max()<32767
 # Independent scalar accumulation for every vertex catches matrix orientation/influence errors.
 slow=[]
 for i,point in enumerate(v4):slow.append(sum(float(weights[i,k])*(boneworld[indices[i,k]]@bind[indices[i,k]]@point) for k in range(4)))
 assert np.max(abs(np.array(slow)-posed))<1e-10
 materials=[];texture=None
 for slot,ptr in enumerate(sm.m_Materials):
  mat=ptr.read();deps.add(ptr.deref().assets_file.name);base=next(c for key,c in mat.m_SavedProperties.m_Colors if key=='_Color');entry={'slot':slot,'name':mat.m_Name,'file':ptr.deref().assets_file.name,'path_id':ptr.path_id,'base_color':[base.r,base.g,base.b,base.a]}
  if slot==1:
   t=next(t.m_Texture for key,t in mat.m_SavedProperties.m_TexEnvs if key=='_MainTex');image=t.read().image.convert('RGBA');deps.add(t.deref().assets_file.name);entry['texture']={'file':t.deref().assets_file.name,'path_id':t.path_id,'size':list(image.size)};texture=image
  materials.append(entry)
 assert materials[0]['name']=='NoTexture' and materials[1]['name']=='Eyes 3' and materials[2]['name']=='Doublesided';assert texture.size==(64,64)
 rgb=texture.convert('RGB').quantize(colors=255,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE);pixels=np.asarray(rgb).astype(np.uint16)+1;pixels[np.asarray(texture)[:,:,3]<128]=0;pixels=pixels.astype(np.uint8);pal=(rgb.getpalette()+[0]*765)[:765];clut=[0]+[((pal[i]>>3)|((pal[i+1]>>3)<<5)|((pal[i+2]>>3)<<10)) or 1 for i in range(0,765,3)]
 colors=np.array(h.m_Colors)[:,:3].astype(float);uv=np.array(h.m_UV0);idx=np.array(h.m_IndexBuffer);faces=[];slots=[];corner_colors=[];corner_uv=[]
 for slot,sub in enumerate(mesh.m_SubMeshes):
  assert sub.topology==0;begin=sub.firstByte//(2 if mesh.m_IndexFormat==0 else 4)
  for face in idx[begin:begin+sub.indexCount].reshape(-1,3):
   assert np.linalg.norm(np.cross(posed[face[1],:3]-posed[face[0],:3],posed[face[2],:3]-posed[face[0],:3]))>1e-12
   faces.append(face.tolist());slots.append(slot);base=np.array(materials[slot]['base_color'][:3]);corner_colors.append(np.clip(np.rint(colors[face]*base),0,255).astype(int).ravel().tolist())
   coords=[]
   for u,w in uv[face]:coords += [int(round(u*64))&255,int(round((1-w)*64))&255]
   corner_uv.append(coords)
 header='/* Original Levium 1, level2 renderer 5551; serialized skinned pose. */\n#include <stdint.h>\n'
 header+=f'#define LEVIUM_VERTICES {len(v)}\n#define LEVIUM_FACES {len(faces)}\n'
 def rows(name,ctype,data):return 'static const '+ctype+' '+name+'[]={\n'+''.join('{'+','.join(map(str,row))+'},\n' for row in data)+'};\n'
 header+='static const short levium_vertices[][3]={'+''.join('{'+','.join(map(str,row))+'},' for row in packed.tolist())+'};\n'
 for name,typ,values,width in [('levium_faces','unsigned short',faces,3),('levium_colors','unsigned char',corner_colors,9),('levium_uv','unsigned char',corner_uv,6)]:header+='static const '+typ+' '+name+f'[][{width}]={{'+''.join('{'+','.join(map(str,row))+'},' for row in values)+'};\n'
 header+='static const unsigned char levium_material[]={'+','.join(map(str,slots))+'};\n'
 words=[int.from_bytes(pixels.tobytes()[i:i+4],'little') for i in range(0,pixels.size,4)];palette=[clut[i]|(clut[i+1]<<16) for i in range(0,256,2)]
 header+='static const uint32_t levium_texture[]={'+','.join(hex(x) for x in words)+'};\nstatic const uint32_t levium_clut[]={'+','.join(hex(x) for x in palette)+'};\n'
 script='/* Original Levium dialogue and transformed interaction capsule. */\n'
 values={'LEVIUM_X':physical(anchor)[0],'LEVIUM_Y':physical(anchor)[1],'LEVIUM_Z':physical(anchor)[2],'LEVIUM_RANGE_X':physical(center[:3])[0],'LEVIUM_RANGE_Y':physical(center[:3])[1],'LEVIUM_RANGE_Z':physical(center[:3])[2],'LEVIUM_RANGE_RADIUS':round(radius*80),'LEVIUM_RANGE_HALF_SEGMENT':round((height/2-radius)*80),'LEVIUM_TALK_X':physical(talk_info['position'])[0],'LEVIUM_TALK_Y':physical(talk_info['position'])[1],'LEVIUM_TALK_Z':physical(talk_info['position'])[2]}
 values['LEVIUM_TALK_FACING']=round(math.atan2(values['LEVIUM_X']-values['LEVIUM_TALK_X'],values['LEVIUM_Z']-values['LEVIUM_TALK_Z'])*4096/(2*math.pi))&4095
 for name,value in values.items():script+=f'#define {name} ({value})\n'
 for endpoint,point in zip('AB',ends):
  for axis,value in zip('XYZ',point):script+=f'#define LEVIUM_RANGE_{endpoint}_{axis} ({value})\n'
 view=np.diag([-1,-1,1])@np.array(camera['matrix'])[:3,:3].T@np.diag([-1,-1,1]);view_q=np.rint(view*4096).astype(int)
 script+='static const short levium_camera_rotation[3][3]={'+','.join('{'+','.join(map(str,row))+'}' for row in view_q.tolist())+'};\n'
 script+='static const int levium_camera_position[3]={'+','.join(map(str,physical(camera['position'])))+'};\n'
 pages=[];sentence_ids=[]
 for i,text in enumerate(first['sentences']):
  lines=textwrap.wrap(text,36);sentence_ids.append([len(pages),math.ceil(len(lines)/6)])
  for start in range(0,len(lines),6):pages.append('\n'.join(lines[start:start+6]))
 repeat_page=len(pages);pages+=['\n'.join(textwrap.wrap(repeat['sentences'][0],36))]
 script+=f'#define LEVIUM_FIRST_PAGES {repeat_page}\n#define LEVIUM_ALL_PAGES {len(pages)}\n'
 script+='static const char *const levium_pages[]={'+','.join(json.dumps(p) for p in pages)+'};\n'
 # Script fields/methods prove the primary -> repeat transition and interaction guards.
 previous=recover_gameplay.METHODS
 try:
  recover_gameplay.METHODS={'NewZera.NPCDialogue':{'Update','OnTriggerEnter','OnTriggerExit','NewDialogue'},'NewZera.DM':{'StartDialogue','DisplayNextSentence','EndDialogue'}};methods,_=recover_gameplay.assembly_evidence(data/'Managed/Assembly-CSharp.dll');methods=[m for m in methods if m['owner'] in recover_gameplay.METHODS]
 finally:recover_gameplay.METHODS=previous
 for n in [mesh.m_StreamData.path if getattr(mesh,'m_StreamData',None) else '']:
  if n:deps.add(Path(n).name)
 report={'component':6279,'renderer':5551,'mesh':{'file':sm.m_Mesh.deref().assets_file.name,'path_id':sm.m_Mesh.path_id,'vertices':len(v),'faces':len(faces),'bones':len(sm.m_Bones),'weight_sum_error':float(np.max(abs(weights.sum(1)-1))),'independent_skin_error':float(np.max(abs(np.array(slow)-posed))),'local_physics_bounds':[packed.min(0).tolist(),packed.max(0).tolist()]},'source_origin':origin.tolist(),'source_position':anchor.tolist(),'physics_position':physical(anchor),'trigger':{'component':5466,'center':physical(center[:3]),'radius':round(radius*80),'half_segment':round((height/2-radius)*80),'source_matrix':ct.tolist(),'axis_endpoints':ends},'talk_point':talk_info,'camera':camera,'first':first,'repeat':repeat,'voice_references':voice,'completion_callbacks':callbacks,'methods':methods,'materials':materials,'pages':pages,'sentence_page_ranges':sentence_ids,'source_payload_sha256':sha(raw),'model_header_sha256':sha(header.encode()),'dialogue_header_sha256':sha(script.encode()),'source_files_sha256':{n:sha((data/n).read_bytes()) for n in sorted(deps)},'limitations':['Serialized posed skin only; original Idle/Talking animations not yet baked','Eye texture alpha adapted to PS1 cutout; custom source shaders and soft alpha omitted','Silence is the actual assigned AudioClip; no invented voice track','Movement-to-talk point, capsule contact and scroll timings require PS1 adaptations','Only this NPC is enabled; source dialogue/callback recovery does not implement every NPC or tutorial cutscene']}
 return report,header,script,texture
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('data',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args();report,model,dialogue,texture=recover(a.data);area=ROOT/'previews/levium'
 for name,content in [('reports/levium.json',json.dumps(report,indent=2)+'\n'),('src/levium_model.h',model),('src/levium_dialogue.h',dialogue)]:
  path=area/name
  if a.check:assert path.read_text()==content,name
  else:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
 if not a.check:(area/'assets').mkdir(exist_ok=True);texture.save(area/'assets/eyes_source.png')
 print(json.dumps({'vertices':report['mesh']['vertices'],'faces':report['mesh']['faces'],'pages':len(report['pages']),'trigger':report['trigger'],'check':a.check}))
