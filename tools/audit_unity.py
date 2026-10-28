"""Inventory a compiled Unity Data directory; no execution of game code."""
import argparse,collections,json
from pathlib import Path
import UnityPy,dnfile
p=argparse.ArgumentParser();p.add_argument('data');p.add_argument('out');a=p.parse_args()
out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
env=UnityPy.load(a.data);counts=collections.Counter();items=[];errors=[]
for o in env.objects:
 counts[o.type.name]+=1
 if o.type.name not in ('Mesh','Texture2D','AnimationClip','AudioClip','GameObject','MonoScript'):continue
 try:
  d=o.read();r={'type':o.type.name,'name':getattr(d,'m_Name',''),'path_id':o.path_id,'file':o.assets_file.name}
  for k in ('m_Width','m_Height','m_VertexCount','m_Length','m_Frequency','m_Channels','m_SampleRate','m_StopTime'):
   if hasattr(d,k):r[k]=getattr(d,k)
  items.append(r)
 except Exception as e:errors.append(str(e))
assemblies=[]
for f in Path(a.data).glob('Managed/Assembly-CSharp*.dll'):
 pe=dnfile.dnPE(str(f))
 for t in pe.net.mdtables.TypeDef.rows:
  assemblies.append({'assembly':f.name,'namespace':str(t.TypeNamespace),'name':str(t.TypeName),'methods':[str(x.row.Name) for x in t.MethodList],'fields':[str(x.row.Name) for x in t.FieldList]})
r={'counts':dict(counts),'objects':items,'types':assemblies,'errors':errors}
(out/'unity_inventory.json').write_text(json.dumps(r,indent=2))
print(json.dumps(dict(counts),indent=2));print('Errors:',len(errors))
