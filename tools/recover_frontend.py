"""Recover original startup/menu IL and native audio/video references; no game code execution."""
import argparse,hashlib,json
from pathlib import Path
import dnfile
import UnityPy
import recover_gameplay
ROOT=Path(__file__).resolve().parents[1]
CLASSES={'AnyKey','LoadTitle','MainMenuCodes','MenuBack','MenuGroup','FadeOut','NewZera.LoadSceneOnClick','NewZera.settings'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def recover(data):
 data=Path(data);assembly=data/'Managed/Assembly-CSharp.dll'
 pe=dnfile.dnPE(str(assembly));selected={}
 for row in pe.net.mdtables.TypeDef.rows:
  owner='.'.join(filter(None,[str(row.TypeNamespace),str(row.TypeName)]))
  if owner in CLASSES:selected[owner]={str(m.row.Name) for m in row.MethodList if m.row.Rva and str(m.row.Name) not in ('.ctor','.cctor')}
 assert set(selected)==CLASSES
 previous=recover_gameplay.METHODS
 try:
  recover_gameplay.METHODS=selected
  methods,_=recover_gameplay.assembly_evidence(assembly)
 finally:recover_gameplay.METHODS=previous
 env=UnityPy.load(str(data));dependencies={'Managed/Assembly-CSharp.dll'}
 def reference(pointer):
  if not pointer.path_id:return None
  reader=pointer.deref();dependencies.add(reader.assets_file.name)
  value=reader.read(check_read=False)
  return {'file':reader.assets_file.name,'path_id':reader.path_id,'type':reader.type.name,'name':getattr(value,'m_Name',None)}
 scenes=[]
 for name in ['level0','level1']:
  scene=next(f for f in env.files.values() if getattr(f,'name',None)==name);dependencies.add(name)
  entries=[];counts={}
  for obj in scene.objects.values():
   if obj.type.name=='MonoBehaviour':
    d=obj.read(check_read=False)
    if d.m_Script.path_id:
     script=d.m_Script.read();key='.'.join(filter(None,[script.m_Namespace,script.m_ClassName]));counts[key]=counts.get(key,0)+1
   if obj.type.name not in ['VideoPlayer','AudioSource','PlayableDirector']:continue
   d=obj.read();tree=obj.read_typetree();go=d.m_GameObject.read()
   entry={'path_id':obj.path_id,'type':obj.type.name,'game_object':go.m_Name,'self_active':bool(go.m_IsActive),'enabled':bool(tree.get('m_Enabled',1))}
   if obj.type.name=='AudioSource':
    entry.update(clip=reference(d.m_audioClip),play_on_awake=tree['m_PlayOnAwake'],loop=tree['Loop'],volume=tree['m_Volume'])
   elif obj.type.name=='VideoPlayer':
    entry.update(clip=reference(d.m_VideoClip),url=tree['m_Url'],play_on_awake=tree['m_PlayOnAwake'],loop=tree['m_Looping'],audio_output_mode=tree['m_AudioOutputMode'])
    if d.m_VideoClip.path_id:
     clip=d.m_VideoClip.deref().read_typetree()
     resource=clip.get('m_ExternalResources',{}).get('m_Source')
     if resource:
      assert Path(resource).name==resource
      dependencies.add(resource)
     entry['video_metadata']={k:v for k,v in clip.items() if k in ['m_OriginalPath','m_Width','m_Height','m_FrameCount','m_FrameRate','m_AudioChannelCount','m_AudioSampleRate','m_ExternalResources']}
   else:entry['playable_asset']=reference(d.m_PlayableAsset)
   entries.append(entry)
  scenes.append({'scene':name,'script_counts':dict(sorted(counts.items())),'native_media':entries})
 return {'source_files_sha256':{n:sha(data/n) for n in sorted(dependencies)},'scenes':scenes,'methods':methods,
         'limitations':['Static source evidence only; no new PS1 startup/menu implementation','Object self-active flag is not hierarchy activity or runtime playback','UI text, sprites, button events, timelines and coroutine state machines require further decoding','Media references and metadata do not prove successful PS1 conversion or audio/video synchronization']}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('data',type=Path);p.add_argument('--output',type=Path,default=ROOT/'reports/frontend_recovery.json');p.add_argument('--check',action='store_true');a=p.parse_args();r=recover(a.data)
 if a.check:assert json.loads(a.output.read_text())==r
 else:a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'scenes':len(r['scenes']),'methods':len(r['methods']),'videos':sum(e['type']=='VideoPlayer' for s in r['scenes'] for e in s['native_media']),'check':a.check}))
