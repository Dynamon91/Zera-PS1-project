"""Verify source relics, checkpoint return and new game in input-only PS1 captures."""
import argparse,hashlib,json
from pathlib import Path

def check(folder):
 folder=Path(folder);j=json.loads((folder/'capture.json').read_text());rows=j['state_samples']
 assert j['content'] in ('zera_stream_walk.cue','zera_gameplay.cue')
 assert hashlib.sha256((folder.parent/Path(j['content']).with_suffix('.bin')).read_bytes()).hexdigest()==j['bin_sha256']
 assert all(r['atlas_errors']==0 and r['player_respawn_events']==0 and r['atlas_budget_drops']==0 for r in rows)
 assert {r['relic_mask'] for r in rows}=={0,1,3}
 assert all((r['relic_count'],r['relic_value'])=={0:(0,0),1:(1,1),3:(2,17)}[r['relic_mask']] for r in rows)
 active=[r for r in rows if r['checkpoint_id']==6752];assert active
 assert all(r['relic_mask']==3 and r['checkpoint_activations']==1 for r in active)
 before=next(r for r in rows if r['frame']==20999);assert before['checkpoint_id']==6752 and before['walk_collision_loads']>=13
 returned=next(r for r in rows if r['frame']==21999)
 assert [returned[k] for k in ['x_fp','y_fp','z_fp','yaw']]==[1356*256,-110*256,-7101*256,1447]
 assert returned['relic_mask']==3 and returned['checkpoint_activations']==1
 assert returned['atlas_ready']==returned['walk_collision_ready']==1 and returned['atlas_menu']==0
 assert returned['atlas_drawn']>0
 last=rows[-1];assert [last[k] for k in ['x_fp','y_fp','z_fp','relic_mask','checkpoint_id','checkpoint_activations']]==[0,3*256,0,0,0,0]
 assert last['atlas_ready']==last['walk_collision_ready']==1 and last['atlas_menu']==0
 events={e['name']:e for e in j['event_captures']}
 assert set(events)=={'first_relic','two_relics','checkpoint_active','checkpoint_return','new_game'}
 assert events['checkpoint_return']['frame']>=21600
 return {'bin_sha256':j['bin_sha256'],'frames':j['frames_run'],'emulator':j['emulator'],'relics':2,'value':17,'checkpoint':6752,
         'automatic_respawns':0,'sampled_cd_errors':0,'sampled_gpu_budget_drops':0,'checkpoint_return':returned,'new_game':last,'events':j['event_captures'],
         'limitations':['Only two relics and checkpoint 6752 connected','Provisional grounded proximity, Kiwi absent','Session-only progress; no memory-card save','Automatic fall return verified in host tests; Select return verified natively']}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);a=p.parse_args();print(json.dumps(check(a.folder),indent=2))
