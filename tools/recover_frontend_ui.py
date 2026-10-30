"""Recover original Unity UI.Text tail strings with serialized offsets and source hashes."""
import argparse,hashlib,json,re,struct,textwrap
from pathlib import Path
import UnityPy
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def recover(data):
 data=Path(data);env=UnityPy.load(str(data));scene=next(f for f in env.files.values() if getattr(f,'name',None)=='level1');entries=[];deps={'level1'}
 for o in sorted(scene.objects.values(),key=lambda o:o.path_id):
  if o.type.name!='MonoBehaviour':continue
  d=o.read(check_read=False)
  if not d.m_Script.path_id:continue
  script=d.m_Script.read()
  if script.m_Namespace!='UnityEngine.UI' or script.m_ClassName!='Text':continue
  deps.add(d.m_Script.deref().assets_file.name);raw=o.get_raw_data();candidates=[]
  # UI.Text serializes its m_Text string last; accept only a complete aligned tail.
  for offset in range(32,len(raw)-3,4):
   length=struct.unpack_from('<i',raw,offset)[0]
   if length<=0 or length>len(raw)-offset-4 or (offset+4+length+3)//4*4!=len(raw):continue
   try:text=raw[offset+4:offset+4+length].decode('utf8')
   except UnicodeError:continue
   if all(c.isprintable() or c in '\r\n\t' for c in text):candidates.append((offset,text))
  assert len(candidates)==1,(o.path_id,candidates)
  offset,text=candidates[0];go=d.m_GameObject.read();path=[go.m_Name];active=bool(go.m_IsActive)
  tf=next(c.component.read() for c in go.m_Component if c.component.deref().type.name in ('Transform','RectTransform'))
  while tf.m_Father.path_id:
   tf=tf.m_Father.read();parent=tf.m_GameObject.read();path.append(parent.m_Name);active=active and bool(parent.m_IsActive)
  entries.append({'component':o.path_id,'name':go.m_Name,'hierarchy':list(reversed(path)),'active_in_serialized_hierarchy':active,'text_offset':offset,'text':text,'payload_sha256':sha(raw)})
 assert len(entries)==65
 credits=next(e for e in entries if e['name']=='credits')
 changelog=[e for e in entries if any('changelog' in n.lower() for n in e['hierarchy']) and len(e['text'])>100]
 assert changelog
 def pages(text):
  lines=[]
  for para in text.replace('\r\n','\n').replace('\r','\n').split('\n'):
   lines+=textwrap.wrap(para,36,replace_whitespace=True) or ['']
  while lines and not lines[0]:lines.pop(0)
  while lines and not lines[-1]:lines.pop()
  return ['\n'.join(lines[i:i+18]) for i in range(0,len(lines),18)]
 cp=pages(credits['text']);lp=[]
 for entry in changelog:lp+=pages(entry['text'])
 header='/* Original credits/changelog, wrapped to 36 columns for the PS1 font. */\n'
 for name,values in [('credits',cp),('changelog',lp)]:
  header+=f'#define FRONT_{name.upper()}_PAGES {len(values)}\nstatic const char * const frontend_{name}_pages[]={{\n'+''.join(json.dumps(v,ensure_ascii=True)+',\n' for v in values)+'};\n'
 report={'scene':'level1','source_files_sha256':{n:sha((data/n).read_bytes()) for n in sorted(deps)},'entries':entries,'credits_component':credits['component'],'changelog_components':[e['component'] for e in changelog],'credits_pages':len(cp),'changelog_pages':len(lp),'catalog_sha256':sha(header.encode()),'limitations':['UI.Text string tails recovered using the original UI.Text schema; button UnityEvents and timeline bindings are not decoded','Includes serialized inactive menu pages and historical patch notes, not proof of currently implemented mechanics','Wrapping/page navigation adapted to the PS1 font; original scroll and visual layout not reproduced']}
 return report,header
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('data',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args();r,h=recover(a.data)
 report=ROOT/'reports/frontend_ui.json';header=ROOT/'previews/frontend/src/frontend_text.h'
 if a.check:assert json.loads(report.read_text())==r;assert header.read_text()==h
 else:report.write_text(json.dumps(r,indent=2)+'\n');header.write_text(h)
 print(json.dumps({'text_components':len(r['entries']),'credits_pages':r['credits_pages'],'changelog_pages':r['changelog_pages'],'check':a.check}))
