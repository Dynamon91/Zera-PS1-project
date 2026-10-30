"""Check continuous native interaction with Levium, repeat text, pause and state resets."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image

def check(folder,kind):
 folder=Path(folder);j=json.loads((folder/'capture.json').read_text());rows=j['state_samples'];last=rows[-1]
 assert j['content']=='zera_campaign.cue' and hashlib.sha256((folder.parent/'zera_campaign.bin').read_bytes()).hexdigest()==j['bin_sha256']
 assert all(r['atlas_errors']==r['front_media_errors']==r['atlas_budget_drops']==r['player_respawn_events']==0 for r in rows)
 assert last['atlas_scene']==0 and last['frontend_screen']==2 and last['atlas_ready']==last['walk_collision_ready']==1
 talk=[r for r in rows if r['dialogue_phase']==2];assert talk and any(r['levium_drawn']>350 for r in talk)
 assert {r['dialogue_phase'] for r in rows}>={0,1,2}
 assert any(r['x_fp']>4500*256 and r['dialogue_prompt'] for r in rows)
 if kind=='conversation':
  first=[r for r in talk if not r['dialogue_visited']]
  assert {r['dialogue_page'] for r in first}==set(range(6))
  for key in ['x_fp','y_fp','z_fp','vy_fp','state']:
   assert len({r[key] for r in first})==1,key
  assert first[0]['state']==0 and abs(first[0]['x_fp']/256-4816)<=8 and abs(first[0]['z_fp']/256-206)<=8 and first[0]['y_fp']==-425*256
  assert any(r['dialogue_page']==6 and r['dialogue_visited']==1 for r in talk)
  assert max(r['dialogue_completions'] for r in rows)==2
  at=lambda frame:min(rows,key=lambda r:abs(r['frame']-frame))
  assert at(19400)['x_fp']==at(19400)['z_fp']==0 and at(19400)['y_fp']==2*256 and at(19400)['dialogue_visited']==1 and at(19400)['dialogue_completions']==2
  assert last['x_fp']==last['z_fp']==last['dialogue_visited']==last['dialogue_completions']==0 and last['y_fp']==2*256
  assert {'first_dialogue','repeat_dialogue','conversation_complete'}=={e['name'] for e in j['event_captures']}
  for image in ['first_dialogue.png','repeat_dialogue.png']:
   pixels=np.asarray(Image.open(folder/image));upper=pixels[10:135,20:195]
   # Original vertex colors/eye texture must occupy the conversation view, above the scroll.
   assert np.count_nonzero((upper[:,:,1]>130)&(upper[:,:,0]>100))>1000
   assert np.count_nonzero((upper[:,:,2]>100)&(upper[:,:,0]<120))>500
 elif kind=='pause':
  paused=[r for r in rows if 5280<=r['frame']<=5520];assert paused and all(r['frontend_screen']==3 and r['dialogue_phase']==2 for r in paused)
  for key in ['x_fp','y_fp','z_fp','vy_fp','state','dialogue_page','dialogue_chars','dialogue_ticks','simulation_ticks','animation_tick']:
   assert len({r[key] for r in paused})==1,key
  assert last['dialogue_phase']==0 and last['dialogue_visited']==1 and last['dialogue_completions']==1
 else:raise ValueError(kind)
 return {'kind':kind,'frames':j['frames_run'],'bin_sha256':j['bin_sha256'],'emulator':j['emulator'],'maximum_drawn_npc_faces':max(r['levium_drawn'] for r in rows),'maximum_completed_conversations':max(r['dialogue_completions'] for r in rows),'source_sentences_seen':6,'cd_errors':0,'sampled_gpu_budget_drops':0,'automatic_respawns':0,'events':j['event_captures'],'final_state':last,'limitations':['Only original Levium dialogue; no full tutorial/NPC or quest coverage','Original static posed mesh; Idle/Talking animations pending','Source assigns Silence to these sentences; no fabricated voice','HLE only, not hardware certification']}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);p.add_argument('--kind',choices=['conversation','pause'],required=True);a=p.parse_args();print(json.dumps(check(a.folder,a.kind),indent=2))
