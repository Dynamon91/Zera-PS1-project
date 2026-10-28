"""Validate codec block flags, quantization quality, and shipped stream layout."""
from pathlib import Path
import tempfile,subprocess,json,struct
import numpy as np
from spu_codec import decode
P=Path(__file__).resolve().parents[1]
known=bytearray(16);known[2]=0x1f
assert list(decode(known)[:2])==[-4096,4096]
with tempfile.TemporaryDirectory() as d:
 d=Path(d);encoder=d/'encode';subprocess.run(['cc','-O2','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(P/'tools/encode_spu.c'),'-o',str(encoder)],check=True)
 t=np.arange(22050)/22050;pcm=np.rint(12000*np.sin(2*np.pi*350*t)+3000*np.sin(2*np.pi*1300*t)).astype('<i2');(d/'tone.pcm').write_bytes(pcm.tobytes())
 import os
 env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0')
 for chunk in (0,4096):
  subprocess.run([str(encoder),str(d/'tone.pcm'),str(d/'tone.adpcm'),str(chunk)],check=True,env=env)
  data=(d/'tone.adpcm').read_bytes();v=decode(data)[:len(pcm)].astype(float);snr=10*np.log10(np.mean(pcm.astype(float)**2)/np.mean((v-pcm)**2));assert snr>25,snr
  if chunk:
   assert len(data)%4096==0
   for off in range(0,len(data),16):assert data[off+1]==(3 if (off+16)%4096==0 else 0)
  else:assert len(data)%64==0 and 1 in data[1::16]
raw=(P/'assets/audio/MUSIC.VAG').read_bytes();assert raw[:4]==b'VAGi';assert struct.unpack_from('<I',raw,8)[0]==4096;assert struct.unpack_from('>I',raw,12)[0]==len(raw)-2048;assert struct.unpack_from('>I',raw,16)[0]==22050;assert struct.unpack_from('<H',raw,30)[0]==1
r=json.loads((P/'reports/audio_conversion.json').read_text());assert all(x['snr_db']>25 for x in r['effects'])
assert 0x6000+sum(x['adpcm_bytes'] for x in r['effects'] if x['name']!='cosmic_core')<0x80000
print('Codec, flags, stream header, quality and SPU allocation checks passed')
