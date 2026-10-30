"""Verify that the shipped credits/changelog preserve all recovered source text."""
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def check():
 r=json.loads((ROOT/'reports/frontend_ui.json').read_text());h=(ROOT/'previews/frontend/src/frontend_text.h').read_text()
 assert hashlib.sha256(h.encode()).hexdigest()==r['catalog_sha256'] and len(r['entries'])==65
 entries={e['component']:e for e in r['entries']}
 def catalog(name):
  block=h.split('frontend_'+name+'_pages[]={')[1].split('};')[0]
  return [json.loads(line.rstrip(',')) for line in block.strip().splitlines()]
 credits=catalog('credits');changelog=catalog('changelog')
 assert len(credits)==r['credits_pages']==1 and len(changelog)==r['changelog_pages']==71
 flatten=lambda s:re.sub(r'\s+','',s)
 assert flatten(''.join(credits))==flatten(entries[r['credits_component']]['text'])
 assert flatten(''.join(changelog))==flatten(''.join(entries[i]['text'] for i in r['changelog_components']))
 assert 'Cyreides' in credits[0] and 'Netrum' in credits[0] and 'Freesound.org' in credits[0]
 assert all(len(line)<=36 for page in credits+changelog for line in page.splitlines())
 return {'text_components':65,'credits_pages':len(credits),'changelog_pages':len(changelog),'all_recovered_page_text_preserved':True}
if __name__=='__main__':print(json.dumps(check(),indent=2))
