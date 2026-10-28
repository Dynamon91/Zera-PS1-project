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
binary=folder.parent/'zera_wip09.bin';assert hashlib.sha256(binary.read_bytes()).hexdigest()==j['bin_sha256']
materials=json.loads((root/'reports/mascot_materials.json').read_text());packing=json.loads((root/'assets/character_packing.json').read_text())
assert packing['packed_vertices']==412 and materials['textured_spot_faces']==96 and materials['textured_eye_faces']==16
out=root/'docs/screenshots/mascot';out.mkdir(parents=True,exist_ok=True)
for frame in [359,950,1150,1250,1380,1500,2199]:shutil.copyfile(folder/f'frame_{frame:04d}.png',out/f'frame_{frame:04d}.png')
shutil.copyfile(folder/'capture.json',out/'capture.json')
result={'source_commit':os.environ['GITHUB_SHA'],'bin_sha256':j['bin_sha256'],'frames':2200,'animation_clips_observed':sorted(clips),'player_states_observed':sorted(states),'automatic_respawns':0,'packed_vertices':412,'triangles':806,'textured_spot_faces':96,'textured_eye_faces':16,'validation':'Input-only HLE animation/material smoke test; not an original-Unity visual fidelity certification'}
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
