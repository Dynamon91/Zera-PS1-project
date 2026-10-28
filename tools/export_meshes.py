"""Export Unity meshes to OBJ for the offline PS1 reduction stage."""
import argparse,json,re
from pathlib import Path
import UnityPy
p=argparse.ArgumentParser();p.add_argument('data');p.add_argument('out');a=p.parse_args()
out=Path(a.out);out.mkdir(parents=True,exist_ok=True);E=UnityPy.load(a.data);manifest=[]
for o in E.objects:
 if o.type.name!='Mesh':continue
 d=o.read();name=re.sub(r'[^a-zA-Z0-9_-]','_',d.m_Name) or 'mesh'
 f=re.sub(r'[^a-zA-Z0-9_-]','_',o.assets_file.name)+'_'+str(o.path_id)+'_'+name+'.obj'
 try:
  text=d.export()
  if not isinstance(text,str):raise ValueError('UnityPy returned no OBJ geometry')
  (out/f).write_text(text)
  manifest.append({'source':o.assets_file.name,'path_id':o.path_id,'name':d.m_Name,'obj':f,'vertices':text.count('\nv '),'faces':text.count('\nf ')})
 except Exception as e:manifest.append({'source':o.assets_file.name,'path_id':o.path_id,'error':str(e)})
(out/'manifest.json').write_text(json.dumps(manifest,indent=2));print('Mesh exports:',len(manifest),'errors:',sum('error' in x for x in manifest))
