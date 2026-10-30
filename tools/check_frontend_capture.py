"""Verify original startup media, menu flow, pause freeze and audio in native captures."""
import argparse,hashlib,json,wave
from pathlib import Path
import numpy as np
from PIL import Image

def check(folder,kind):
 folder=Path(folder);j=json.loads((folder/'capture.json').read_text());rows=j['state_samples'];last=rows[-1]
 assert j['content']=='zera_gameplay.cue' and hashlib.sha256((folder.parent/'zera_gameplay.bin').read_bytes()).hexdigest()==j['bin_sha256']
 assert all(r['atlas_errors']==0 and r['front_media_errors']==0 and r['player_respawn_events']==0 and r['atlas_budget_drops']==0 for r in rows)
 assert last['front_media_ready']==1 and j['audio_output']['clipped_samples']==0
 with wave.open(str(folder/'audio.wav')) as wav:
  assert wav.getframerate()==44100 and wav.getnchannels()==2 and wav.getsampwidth()==2
  audio=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').astype(float)
 ratio=len(audio)/j['frames_run']
 def rms(start,end):
  a=audio[int(start*ratio):int(end*ratio)];return float(np.sqrt(np.mean(a*a)))
 def at(frame):return min(rows,key=lambda r:abs(r['frame']-frame))
 def title_pixels(frame):
  pixels=np.asarray(Image.open(folder/f'frame_{frame:04d}.png'));assert int((pixels[:130]>120).sum())>12000
 if kind=='boot':
  assert last['frontend_screen']==1 and last['front_audio_track']==2 and last['simulation_ticks']==0
  logo=[r for r in rows if r['frontend_screen']==0 and r['front_media_ready']]
  assert logo and max(r['front_logo_frame'] for r in logo)>=67 and last['front_logo_frame']==68
  first_title=next(r for r in rows if r['frontend_screen']==1);assert 700<=first_title['frame']<=850
  for frame in [900,1200,1400,1800,2200,2999]:title_pixels(frame)
  assert rms(350,650)>30
  for start in range(950,2800,200):assert rms(start,start+150)>20 # Includes full-track repeats.
 elif kind=='skip':
  assert at(800)['frontend_screen']==1 and at(800)['front_logo_frame']<20
  assert last['frontend_screen']==2 and last['atlas_ready']==last['walk_collision_ready']==1
  assert last['mascot_visible']==1 and last['state']==0 and last['front_audio_track']==0
  assert last['z_fp']==last['x_fp']==0 and last['y_fp']==3*256
 elif kind=='flow':
  assert {r['frontend_screen'] for r in rows}=={0,1,2,3,4,5}
  assert at(1100)['frontend_screen']==4
  paused=[r for r in rows if 1950<=r['frame']<=2250];assert paused and all(r['frontend_screen']==3 for r in paused)
  for field in ['x_fp','y_fp','z_fp','vy_fp','state','simulation_ticks','animation_tick','animation_clip','relic_mask','checkpoint_id']:
   assert len({r[field] for r in paused})==1,field
  assert at(2550)['z_fp']<paused[0]['z_fp']<0 and at(2550)['x_fp']==paused[0]['x_fp']==0
  assert at(3100)['frontend_screen']==2 and at(3100)['z_fp']==0
  assert at(3500)['frontend_screen']==5 and at(3500)['frontend_muted']==1 and rms(3500,3600)==0
  assert at(3750)['frontend_muted']==0 and rms(3705,3715)>5
  assert at(4500)['frontend_screen']==1 and at(4500)['front_audio_track']==2 and rms(4500,4650)>20
  for frame in [900,1100,2050,3500,4500]:title_pixels(frame)
  assert last['frontend_screen']==2 and last['frontend_has_game']==1 and last['state']==0 and last['mascot_visible']==1
  assert last['relic_mask']==last['checkpoint_id']==0 and last['atlas_ready']==last['walk_collision_ready']==1
  assert last['front_sfx_events'][0]>0 and last['front_sfx_events'][1]>0
 else:raise ValueError(kind)
 return {'kind':kind,'bin_sha256':j['bin_sha256'],'frames':j['frames_run'],'emulator':j['emulator'],'audio':j['audio_output'],'final_state':last,'sampled_cd_errors':0,'sampled_gpu_budget_drops':0,'limitations':['HLE only; no hardware or full original menu equivalence certification','Startup movie reduced to 160x90, 8 fps and 16 colors per frame','Campaign entry remains the verified Dreary Valley route; original full campaign/menu/save options pending']}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);p.add_argument('--kind',choices=['boot','flow','skip'],required=True);a=p.parse_args();print(json.dumps(check(a.folder,a.kind),indent=2))
