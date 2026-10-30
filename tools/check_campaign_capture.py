"""Verify Cosmic Core traversal and the expanded source menu using input-only native captures."""
import argparse,hashlib,json,wave
from pathlib import Path
import numpy as np
from PIL import Image

def check(folder,kind):
 folder=Path(folder);j=json.loads((folder/'capture.json').read_text());rows=j['state_samples'];last=rows[-1]
 assert j['content']=='zera_campaign.cue' and hashlib.sha256((folder.parent/'zera_campaign.bin').read_bytes()).hexdigest()==j['bin_sha256']
 assert all(r['atlas_errors']==r['front_media_errors']==r['atlas_budget_drops']==r['player_respawn_events']==0 for r in rows)
 assert last['frontend_screen']==2 and last['atlas_scene']==0 and last['atlas_ready']==last['walk_collision_ready']==1
 assert last['state']==0 and last['mascot_visible']==1 and last['atlas_drawn']>0
 assert last['relic_mask']==last['checkpoint_id']==0 # Dreary placements must not leak into Cosmic Core.
 states=sorted({r['state'] for r in rows});clips=sorted({r['animation_clip'] for r in rows})
 if kind in ['ground','air']:
  assert [last[k] for k in ['x_fp','y_fp','z_fp']]==[2000*256,-233*256,0]
  assert last['walk_collision_loads']>=2 and last['atlas_load_events']>=2
  assert any(r['animation_clip']==1 and r['debug_actual_moving'] for r in rows)
  assert last['animation_clip']==0 and last['yaw']==3072 and last['facing']==1024
 if kind=='air':
  assert states==[0,1,2,3] and clips==[0,1,2,3]
  assert any(r['x_fp']>=1290*256 and r['walk_collision_loads']>=2 and r['state']==1 and r['vy_fp']>0 and r['walk_collision_ready'] for r in rows)
  event=next(e for e in j['event_captures'] if e['name']=='airborne_sector');assert event['position_fp'][0]>=1290*256 and event['position_fp'][1]>50*256
 if kind=='jump':
  assert states==[0,1,2,3] and {0,2,3}<=set(clips)
  assert max(r['y_fp'] for r in rows)==155*256 and last['x_fp']==last['z_fp']==0 and last['y_fp']==2*256
 if kind=='ui':
  at=lambda frame:min(rows,key=lambda r:abs(r['frame']-frame))
  assert {r['frontend_screen'] for r in rows}=={0,1,2,3,5,6,7,8,9}
  assert at(1150)['frontend_screen']==6 and at(1500)['frontend_screen']==9 and at(1500)['frontend_page']==1
  assert at(2050)['frontend_music_volume']==0 and at(2050)['frontend_sfx_volume']==4
  assert at(2500)['frontend_sfx_volume']==0 and at(2500)['frontend_music_volume']==4
  assert last['frontend_camera_mode']==1 and last['frontend_sensitivity']==4 and last['frontend_music_volume']==last['frontend_sfx_volume']==4
  paused=[r for r in rows if 4200<=r['frame']<=4450];assert paused and all(r['frontend_screen']==3 for r in paused)
  for key in ['x_fp','y_fp','z_fp','vy_fp','state','simulation_ticks','animation_tick','animation_clip']:
   assert len({r[key] for r in paused})==1,key
  assert at(4850)['x_fp']>paused[0]['x_fp']>0 and at(5200)['frontend_screen']==1
  assert [last[k] for k in ['x_fp','y_fp','z_fp','yaw','facing']]==[0,2*256,0,3072,1024]
  with wave.open(str(folder/'audio.wav')) as wav:
   audio=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').astype(float)
  ratio=len(audio)/j['frames_run']
  def rms(a,b):
   v=audio[int(a*ratio):int(b*ratio)];return float(np.sqrt(np.mean(v*v)))
  assert rms(1950,2050)==0 and rms(2280,2300)>20 and rms(5100,5250)>20
  assert j['audio_output']['clipped_samples']==0
  for frame in [900,2970,4300,5200]:assert int((np.asarray(Image.open(folder/f'frame_{frame:04d}.png'))[:130]>120).sum())>12000
 return {'kind':kind,'frames':j['frames_run'],'bin_sha256':j['bin_sha256'],'emulator':j['emulator'],'states':states,'clips':clips,'final_state':last,'events':j['event_captures'],'sampled_cd_errors':0,'sampled_gpu_budget_drops':0,'automatic_respawns':0,'limitations':['First Cosmic Core route only; not full hub/campaign certification','No original NPC/tutorial interactions, cutscene, world music or memory card integrated here','Local HLE verification only']}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);p.add_argument('--kind',choices=['ground','air','jump','ui'],required=True);a=p.parse_args();print(json.dumps(check(a.folder,a.kind),indent=2))
