"""Verify on-foot streamed terrain using input-only HLE captures and read-only RAM."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def check(folder,kind):
 folder=Path(folder);j=json.loads((folder/'capture.json').read_text());rows=j['state_samples'];last=rows[-1]
 assert j['content'] in ('zera_stream_walk.cue','zera_gameplay.cue')
 assert hashlib.sha256((folder.parent/Path(j['content']).with_suffix('.bin')).read_bytes()).hexdigest()==j['bin_sha256']
 assert all(r['atlas_errors']==0 and r['player_respawn_events']==0 and r['atlas_budget_drops']==0 for r in rows)
 assert last['atlas_menu']==0 and last['atlas_scene']==1 and last['atlas_ready']==last['walk_collision_ready']==1
 assert last['state']==0 and last['mascot_visible']==1 and last['atlas_drawn']>0
 states=sorted({r['state'] for r in rows});clips=sorted({r['animation_clip'] for r in rows})
 if kind in ['ground','air']:
  assert [last[k] for k in ['x_fp','y_fp','z_fp']]==[0,-14*256,-2000*256]
  assert last['walk_collision_loads']>=3 and last['atlas_load_events']>=3
  assert any(r['animation_clip']==1 and r['debug_actual_moving']==1 for r in rows)
  assert any(r['frame']>3500 and r['state']==0 and r['animation_clip']==0 for r in rows)
 if kind=='wall':
  assert 535*256<=last['x_fp']<=538*256 and last['z_fp']==0
  blocked=[r for r in rows if 3000<=r['frame']<=3500]
  assert blocked and all(r['debug_input_x']==1 and r['debug_actual_moving']==0 and r['animation_clip']==0 and r['yaw']==0 for r in blocked)
  assert any(r['mascot_visible']==0 and r['camera_distance']<320 for r in rows)
  assert last['camera_distance']>=400 and last['mascot_visible']==1
 if kind=='jump':
  assert states==[0,1,2,3] and set(clips)>={0,2,3}
  assert max(r['y_fp'] for r in rows)==156*256 and last['y_fp']==3*256
 if kind=='air':
  assert states==[0,1,2,3] and clips==[0,1,2,3]
  airborne=[r for r in rows if r['walk_collision_ready'] and r['walk_collision_loads']>=3 and r['state']==1 and r['vy_fp']>0 and r['z_fp']<=-1290*256]
  assert airborne
  events={e['name']:e for e in j['event_captures']};assert 'airborne_sector' in events
  event=events['airborne_sector'];assert event['position_fp'][2]<=-1290*256 and event['position_fp'][1]>50*256
 return {'kind':kind,'frames':j['frames_run'],'bin_sha256':j['bin_sha256'],'emulator':j['emulator'],'states':states,'clips':clips,
 'final_state':last,'automatic_respawns':0,'cd_errors':0,'sampled_gpu_budget_drops':0,'events':j['event_captures'],
 'limitation':'One original spawn route and wall/jump cases; not certification of every route or Unity capsule fidelity'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);p.add_argument('--kind',choices=['ground','wall','jump','air'],required=True);a=p.parse_args();print(json.dumps(check(a.folder,a.kind),indent=2))
