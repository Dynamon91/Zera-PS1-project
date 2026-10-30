"""Convert the original logo movie, title texture and menu audio to resident PS1 media."""
import argparse,hashlib,json,math,struct,subprocess,tempfile
from pathlib import Path
import UnityPy
import numpy as np
from PIL import Image
from spu_codec import decode
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def rgb15(image):
 a=np.asarray(image.convert('RGB'),dtype=np.uint16);v=(a[:,:,0]>>3)|((a[:,:,1]>>3)<<5)|((a[:,:,2]>>3)<<10);v[v==0]=1
 return v.astype('<u2').tobytes()
def prepare(data):
 data=Path(data);out=ROOT/'previews/frontend';(out/'assets').mkdir(parents=True,exist_ok=True);(out/'src').mkdir(exist_ok=True);(out/'reports').mkdir(exist_ok=True)
 env=UnityPy.load(str(data));files={f.name:f for f in env.files.values() if hasattr(f,'objects')}
 dependencies={'sharedassets0.assets','sharedassets1.assets','resources.assets','sharedassets0.resource'}
 with tempfile.TemporaryDirectory(prefix='zera-frontend-convert-') as temp:
  temp=Path(temp);clip=files['sharedassets0.assets'].objects[77].read_typetree();ref=clip['m_ExternalResources'];assert ref['m_Source']=='sharedassets0.resource'
  movie=(data/ref['m_Source']).read_bytes()[ref['m_Offset']:ref['m_Offset']+ref['m_Size']];assert len(movie)==ref['m_Size'];(temp/'logo.m4v').write_bytes(movie)
  raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(temp/'logo.m4v'),'-vf','fps=8,scale=160:90:flags=lanczos','-f','rawvideo','-pix_fmt','rgb24','-threads','1','pipe:1'])
  frame_count=len(raw)//(160*90*3);assert len(raw)==frame_count*160*90*3 and abs(frame_count-clip['m_FrameCount']/clip['m_FrameRate']*8)<=1
  frames=bytearray()
  for k in range(frame_count):
   image=Image.frombytes('RGB',(160,90),raw[k*43200:(k+1)*43200]).quantize(colors=16,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
   palette=image.getpalette();palette=(palette+[0]*48)[:48]
   pal=Image.new('RGB',(16,1));pal.putdata([tuple(palette[i:i+3]) for i in range(0,48,3)]);frames+=rgb15(pal)
   pixels=np.asarray(image).reshape(-1);assert max(pixels)<16;frames+=(pixels[0::2]|(pixels[1::2]<<4)).tobytes()
  duration_ticks=math.ceil(clip['m_FrameCount']/clip['m_FrameRate']*60)
  title=files['sharedassets0.assets'].objects[18].read().image.convert('RGBA');title.thumbnail((256,144),Image.Resampling.LANCZOS)
  canvas=Image.new('RGBA',(256,144),(0,0,0,255));canvas.alpha_composite(title,((256-title.width)//2,(144-title.height)//2));title_blob=rgb15(canvas)
  # Main RAM staging is shared with world geometry, so logo playback does not add a second resident world buffer.
  bank=bytearray(2048);sections=[]
  def append(name,payload):
   sector=len(bank)//2048;bank.extend(payload);bank.extend(bytes((-len(bank))%2048));entry={'name':name,'sector':sector,'sectors':len(bank)//2048-sector,'bytes':len(payload),'sha256':sha(payload)};sections.append(entry);return entry
  title_section=append('title',title_blob);samples=[];spu_address=0x1010
  encoder=temp/'encode';subprocess.run(['cc','-O2',str(ROOT/'tools/encode_spu.c'),'-o',str(encoder)],check=True)
  inputs=[('logo',None),('menu',('sharedassets1.assets',25))]+[(name,('resources.assets',pid)) for name,pid in [('ui_move',560),('ui_accept',567),('jump',575),('land',592),('dash',608),('flap',573),('pickup',566)]]
  for name,source in inputs:
   src=temp/'logo.m4v'
   if source:
    sound=files[source[0]].objects[source[1]].read();src=temp/(name+'.wav');src.write_bytes(next(iter(sound.samples.values())))
    resource=getattr(sound,'m_Resource',None)
    if resource:
     resource_name=Path(resource.m_Source).name
     if (data/resource_name).is_file():dependencies.add(resource_name)
   pcm=temp/(name+'.pcm');adpcm=temp/(name+'.adpcm')
   subprocess.run(['ffmpeg','-v','error','-y','-i',str(src),'-vn','-ac','1','-ar','22050','-af','volume=0.65','-f','s16le',str(pcm)],check=True)
   subprocess.run([str(encoder),str(pcm),str(adpcm),'0'],check=True);payload=bytearray(adpcm.read_bytes());raw_pcm=np.frombuffer(pcm.read_bytes(),dtype='<i2');length=len(raw_pcm)
   decoded=decode(payload)[:length].astype(float);signal=raw_pcm.astype(float);snr=10*math.log10(max(1,float(np.mean(signal**2)))/max(1e-9,float(np.mean((signal-decoded)**2))))
   if name=='menu':
    payload=payload[:math.ceil(length/28)*16];payload[1]=6;payload[-15]=3;payload.extend(bytes((-len(payload))%64))
   entry=append(name,payload);entry.update(address=spu_address,rate=22050,loop=name=='menu',pcm_samples=length,snr_db=round(snr,2),source=source);samples.append(entry);spu_address+=len(payload)
  assert spu_address<0x80000
  logo_section=append('logo_frames',frames)
  tag=hashlib.sha256(bank[2048:]).digest()[:16];bank[:8]=b'ZFE00001';bank[8:24]=tag
  struct.pack_into('<6I',bank,24,160,90,8,frame_count,duration_ticks,7232)
  (out/'assets/FRONT.DAT').write_bytes(bank)
  h='/* Generated original startup media. */\n#ifndef FRONTEND_ASSETS_H\n#define FRONTEND_ASSETS_H\n'
  for name,value in [('FRONT_LOGO_WIDTH',160),('FRONT_LOGO_HEIGHT',90),('FRONT_LOGO_FPS',8),('FRONT_LOGO_FRAMES',frame_count),('FRONT_LOGO_TICKS',duration_ticks),('FRONT_FRAME_BYTES',7232),('FRONT_LOGO_SECTOR',logo_section['sector']),('FRONT_LOGO_SECTORS',logo_section['sectors']),('FRONT_STAGING_BYTES',logo_section['sectors']*2048),('FRONT_TITLE_SECTOR',title_section['sector']),('FRONT_TITLE_SECTORS',title_section['sectors'])]:h+=f'#define {name} {value}\n'
  h+='static const unsigned char frontend_tag[16]={'+','.join(map(str,tag))+'};\n'
  h+='static const struct {int sector,sectors,size,address,rate,loop;} frontend_samples[]={\n'+''.join('{'+','.join(map(str,[e['sector'],e['sectors'],e['bytes'],e['address'],e['rate'],int(e['loop'])]))+'},\n' for e in samples)+'};\n#endif\n'
  (out/'src/frontend_assets.h').write_text(h)
  report={'source_files_sha256':{n:sha((data/n).read_bytes()) for n in sorted(dependencies)},'original_movie_sha256':sha(movie),'logo':{'frames':frame_count,'width':160,'height':90,'fps':8,'duration_ticks':duration_ticks,'frame_bytes':7232,'format':'per-frame 16-color RGB555 palette + 4-bit indexed pixels'},'sections':sections,'spu_end':spu_address,'data_sha256':sha(bank),'catalog_sha256':sha(h.encode()),'limitations':['Logo resampled from original 1200x675 movie to 160x90 at 8 fps, 16 colors per frame','All audio downmixed to mono 22050 Hz SPU ADPCM','Full Glass Arp track repeats at file boundary; no authored seamless loop markers recovered','Title logo retained; menu layout and available actions are a PS1 adaptation, not full original UI equivalence']}
  (out/'reports/frontend_assets.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'logo_frames':frame_count,'data_bytes':len(bank),'staging_bytes':logo_section['sectors']*2048,'spu_end':spu_address}))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('data',type=Path);a=p.parse_args();prepare(a.data)
