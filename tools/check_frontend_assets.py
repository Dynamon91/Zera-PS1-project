"""Check the complete startup bank, generated catalog, SPU layout and source hashes."""
import argparse,hashlib,json,math,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def check(data=None):
 area=ROOT/'previews/frontend';r=json.loads((area/'reports/frontend_assets.json').read_text());blob=(area/'assets/FRONT.DAT').read_bytes();h=(area/'src/frontend_assets.h').read_text()
 assert sha(blob)==r['data_sha256'] and sha(h.encode())==r['catalog_sha256']
 assert blob[:8]==b'ZFE00001' and blob[8:24]==hashlib.sha256(blob[2048:]).digest()[:16]
 assert bytes(map(int,re.search(r'frontend_tag\[16\]=\{([^}]+)',h).group(1).split(',')))==blob[8:24]
 logo=r['logo'];assert struct.unpack_from('<6I',blob,24)==(logo['width'],logo['height'],logo['fps'],logo['frames'],logo['duration_ticks'],logo['frame_bytes'])
 assert logo['width']==160 and logo['height']==90 and logo['fps']==8 and logo['frame_bytes']==7232
 assert abs(logo['frames']/logo['fps']-logo['duration_ticks']/60)<.15
 previous=1;address=0x1010;rows=[];samples=[]
 for s in r['sections']:
  assert s['sector']==previous and s['bytes']<=s['sectors']*2048 and s['sectors']==math.ceil(s['bytes']/2048)
  start=s['sector']*2048;payload=blob[start:start+s['bytes']];assert sha(payload)==s['sha256'];previous+=s['sectors']
  if 'address' in s:
   assert s['address']==address and s['bytes']%64==0 and s['rate']==22050 and s['snr_db']>20
   assert all(payload[i]>>4<=4 and payload[i]&15<=12 for i in range(0,len(payload),16))
   last=(math.ceil(s['pcm_samples']/28)-1)*16
   if s['loop']:assert s['name']=='menu' and payload[1]==6 and payload[last+1]==3
   else:assert payload[last+17]==1
   address+=s['bytes'];rows.append([s['sector'],s['sectors'],s['bytes'],s['address'],s['rate'],int(s['loop'])]);samples.append(s['name'])
  elif s['name']=='logo_frames':
   assert len(payload)==logo['frames']*logo['frame_bytes']
   for f in range(logo['frames']):assert all(0<v<0x8000 for v in struct.unpack_from('<16H',payload,f*logo['frame_bytes']))
  else:assert s['name']=='title' and len(payload)==256*144*2
 assert len(blob)==previous*2048 and address==r['spu_end'] and address<0x80000
 assert samples==['logo','menu','ui_move','ui_accept','jump','land','dash','flap','pickup']
 catalog=h.split('frontend_samples[]={')[1].split('};')[0].strip().splitlines();assert [list(map(int,re.findall(r'\d+',line))) for line in catalog]==rows
 sections={s['name']:s for s in r['sections']}
 constants=dict(re.findall(r'#define (FRONT_\w+) (\d+)',h))
 assert int(constants['FRONT_STAGING_BYTES'])==sections['logo_frames']['sectors']*2048
 for prefix,name in [('LOGO','logo_frames'),('TITLE','title')]:
  assert int(constants[f'FRONT_{prefix}_SECTOR'])==sections[name]['sector'] and int(constants[f'FRONT_{prefix}_SECTORS'])==sections[name]['sectors']
 if data:
  for name,digest in r['source_files_sha256'].items():assert sha((Path(data)/name).read_bytes())==digest,name
 return {'data_sha256':r['data_sha256'],'logo':logo,'spu_end':address,'source_hashes_checked':data is not None,'audio_samples':samples}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data',type=Path);a=p.parse_args();print(json.dumps(check(a.data),indent=2))
