"""Publish actual mascot captures and verify animation/control smoke coverage."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
root=Path(__file__).resolve().parents[1];folder=Path(sys.argv[1])
j=json.loads((folder/'capture.json').read_text());assert j['frames_run']==2200
samples=j['state_samples'];clips={s['animation_clip'] for s in samples if s.get('menu_screen')==1}
assert clips>={0,1,2,3},clips
assert samples[-1]['player_respawn_events']==0 and samples[-1]['state']==0
states={s['state'] for s in samples if s.get('menu_screen')==1}
assert states>={0,1,3},states
moving_camera=[s for s in samples if s.get('debug_actual_moving') and s.get('debug_movement_yaw')!=s.get('yaw') and s.get('debug_input_x')==1 and s.get('debug_input_z')==0]
assert moving_camera,'no simultaneous camera/movement coverage'
aligned=[s for s in moving_camera if ((1024-s['debug_movement_yaw'])&4095)==s['facing']]
assert aligned,'mascot never converged to the same yaw basis as movement'
wall=json.loads((folder.parent/'native-preview/capture.json').read_text())
blocked=[s for s in wall['state_samples'] if s.get('menu_screen')==1 and s.get('state')==0 and (s.get('debug_input_x') or s.get('debug_input_z')) and s.get('debug_actual_moving')==0 and s.get('animation_clip')==0]
assert blocked,'no idle-while-blocked coverage'
close=[s for s in wall['state_samples'] if s.get('camera_distance',850)<320]
assert close and all(s.get('mascot_visible')==0 for s in close)
restored=[s for s in wall['state_samples'] if s['frame']>close[0]['frame'] and s.get('camera_distance',0)>=400 and s.get('mascot_visible')==1]
assert restored,'mascot did not reappear after camera clearance returned'
assert all(s.get('mascot_visible')==1 for s in samples if s.get('camera_distance',0)>=400)


binary=folder.parent/'zera_wip09.bin';assert hashlib.sha256(binary.read_bytes()).hexdigest()==j['bin_sha256']
materials=json.loads((root/'reports/mascot_materials.json').read_text());packing=json.loads((root/'assets/character_packing.json').read_text())
assert packing['packed_vertices']==412 and materials['textured_spot_faces']==96 and materials['textured_eye_faces']==16
out=root/'docs/screenshots/mascot';out.mkdir(parents=True,exist_ok=True)
for frame in [359,950,1150,1250,1380,1500,2199]:shutil.copyfile(folder/f'frame_{frame:04d}.png',out/f'frame_{frame:04d}.png')
shutil.copyfile(folder/'capture.json',out/'capture.json')
result={'source_commit':os.environ['GITHUB_SHA'],'bin_sha256':j['bin_sha256'],'frames':2200,'animation_clips_observed':sorted(clips),'player_states_observed':sorted(states),'automatic_respawns':0,'camera_movement_aligned_samples':len(aligned),'blocked_idle_samples':len(blocked),'close_camera_hidden_samples':len(close),'clear_camera_restored_samples':len(restored),'packed_vertices':412,'triangles':806,'textured_spot_faces':96,'textured_eye_faces':16,'validation':'Input-only HLE animation/material smoke test; not an original-Unity visual fidelity certification'}
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
