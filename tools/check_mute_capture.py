"""Verify mute/restore from actual emulator state and captured PCM."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import wave
import numpy as np

root=Path(__file__).resolve().parent.parent
directory=Path(sys.argv[1])
report=json.loads((directory/'capture.json').read_text())
assert report['frames_run']==1200
samples={s['frame']:s for s in report['state_samples']}
assert samples[650]['audio_muted']==1 and samples[850]['audio_muted']==0
assert samples[650]['audio_music_ready']==1 and samples[850]['audio_music_ready']==1
assert samples[850]['audio_refills']>samples[520]['audio_refills'], 'stream stopped'
assert all(s.get('audio_cd_errors',0)==0 for s in samples.values())
with wave.open(str(directory/'audio.wav'),'rb') as wav:
    assert wav.getframerate()==44100 and wav.getnchannels()==2 and wav.getsampwidth()==2
    pcm=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').reshape(-1,2).astype(np.float64)
def rms(start,end):
    block=pcm[start*735:end*735]
    assert len(block)==(end-start)*735
    return float(np.sqrt(np.mean(block*block)))
silent=rms(580,700);restored=rms(820,900)
assert silent<1, f'mute RMS {silent}'
assert restored>10, f'restored RMS {restored}'
result={'source_commit':os.environ['GITHUB_SHA'],'bin_sha256':report['bin_sha256'],
        'muted_rms':silent,'restored_rms':restored,'units':'signed 16-bit PCM amplitude',
        'emulator':report['emulator'],'validation':'HLE emulator recording; no hardware test'}
out=root/'docs/screenshots/audio';out.mkdir(parents=True,exist_ok=True)
for name in ('frame_0650.png','frame_0850.png','capture.json'):
    shutil.copyfile(directory/name,out/name)
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
text=f'''# Audio on/off — native verification

Source: `{result['source_commit']}`. Build hash: `{result['bin_sha256']}`.

| Muted | Restored |
| --- | --- |
| ![Audio OFF](screenshots/audio/frame_0650.png) | ![Audio ON](screenshots/audio/frame_0850.png) |

Captured PCM RMS: muted **{silent:.3f}**, restored **{restored:.3f}** (signed 16-bit amplitude).
Music remained initialized and disc refills continued during the test.
The setting persists for this session through respawn and return to title;
it is not a memory-card setting. This is an emulator check, not hardware validation.
The source ZIP retains its labeled WIP08 disc; the new playable build is in the
corresponding Native PS1 preview artifact.
'''
(root/'docs/AUDIO.md').write_text(text)
print(json.dumps(result))
