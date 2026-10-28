"""Convert recovered Unity WAVs to native SPU sample data and a stream file.
Run encode_spu.c on the host first; pass its executable as the optional argument.
"""
from pathlib import Path
import subprocess,sys,struct,json,wave,math
import numpy as np
P=Path(__file__).resolve().parents[1];src=P/'assets/audio_source';dst=P/'assets/audio';dst.mkdir(exist_ok=True)
encoder=sys.argv[1] if len(sys.argv)>1 else '/tmp/encode_spu';report=[];header='/* Original game effects, mono 22050 Hz SPU ADPCM, DMA-padded. */\n';names=['ui_move','ui_accept','jump','land','dash','flap','pickup']
from spu_codec import decode
for name in names+['cosmic_core']:
 pcm=dst/(name+'.pcm');adpcm=dst/(name+'.adpcm');music=name=='cosmic_core'
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(src/(name+'.wav')),'-ac','1','-ar','22050','-af','volume=0.65' if music else 'volume=0.8','-f','s16le',str(pcm)],check=True)
 subprocess.run([encoder,str(pcm),str(adpcm),'4096' if music else '0'],check=True)
 data=adpcm.read_bytes();raw=np.frombuffer(pcm.read_bytes(),dtype='<i2').astype(float);decoded=decode(data)[:len(raw)].astype(float)
 noise=np.mean((raw-decoded)**2);snr=10*math.log10(max(1,np.mean(raw**2))/max(noise,1e-9))
 report.append({'name':name,'sample_rate':22050,'channels':1,'pcm_samples':len(raw),'adpcm_bytes':len(data),'snr_db':round(snr,2),'source_file':name+'.wav'})
 if music:
  # VAGi: mono interleaved stream header occupies a complete CD sector.
  vag=bytearray(2048);vag[:4]=b'VAGi';struct.pack_into('<I',vag,8,4096);struct.pack_into('>II',vag,12,len(data),22050);struct.pack_into('<H',vag,30,1);vag[32:43]=b'cosmic_core'
  (dst/'MUSIC.VAG').write_bytes(vag+data)
 else:
  assert len(data)%64==0
  words=[int.from_bytes(data[i:i+4],'little') for i in range(0,len(data),4)]
  header+='static const uint32_t sfx_'+name+'[]={'+','.join(hex(x) for x in words)+'};\n'
 pcm.unlink();adpcm.unlink()
header+='static const struct {const uint32_t *data;unsigned size;} sfx_samples[]={'+','.join('{sfx_%s,sizeof(sfx_%s)}'%(n,n) for n in names)+'};\n'
(P/'src/audio_samples.h').write_text(header);(P/'reports/audio_conversion.json').write_text(json.dumps({'effects':report,'format':'SPU ADPCM, exhaustive filter/shift encoding','music':'full cosmic_core track, downmixed to mono 22050 Hz; disc-streamed; padded full-track repeat, no authored seamless loop markers'},indent=2))
print(json.dumps(report,indent=2))
