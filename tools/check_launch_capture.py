"""Verify actual launchpad gameplay using controller-only input and read-only RAM."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
folder=Path(sys.argv[1]);capture=json.loads((folder/'capture.json').read_text())
assert capture['content']=='zera_launchpad_preview.cue' and capture['frames_run']==2200
config=json.loads((ROOT/'previews/launchpad/reports/launch_config.json').read_text())
rows=capture['state_samples'];last=rows[-1]
assert last['launch_started']==3 and last['launch_completed']==2 and last['launch_cancelled']==1,last
assert not last['launch_active'] and last['state']==0 and last['menu_screen']==1
assert last['player_respawn_events']==0 and last['audio_cd_errors']==0
assert last['x_fp']==config['end_fp'][0] and last['z_fp']==config['end_fp'][2]
assert last['y_fp']==1895*256
flight=[s for s in rows if s['launch_active']]
assert len(flight)>=3
for s in flight:
 u=s['launch_time'];start=config['start_fp'];end=config['end_fp']
 expected=[start[k]+int((end[k]-start[k])*u/65536) for k in range(3)]
 expected[1]+=config['arc_fp']*u*(65536-u)//4294967296
 assert [s['x_fp'],s['y_fp'],s['z_fp']]==expected,(s,expected)
 assert s['dash_ticks']==0
 assert s['camera_height']==int(s['y_fp']/256), 'flight camera lost vertical tracking'
paused=[s for s in rows if 480<=s['frame']<=570]
assert len(paused)>=3 and all(s['menu_screen']==2 and s['launch_active'] for s in paused)
assert len({(s['simulation_ticks'],s['launch_time'],s['x_fp'],s['y_fp'],s['z_fp']) for s in paused})==1
reset=next(s for s in rows if s['frame']==1200)
assert reset['launch_cancelled']==1 and not reset['launch_active']
assert (reset['x_fp'],reset['y_fp'],reset['z_fp'])==(0,0,0)
assert any(s['frame']<1000 and s['launch_completed']==1 and s['state']==0 for s in rows)
stable=[s for s in rows if s['frame']>=1900]
assert len({(s['x_fp'],s['y_fp'],s['z_fp'],s['state']) for s in stable})==1
binary=folder.parent/'zera_launchpad_preview.bin'
assert hashlib.sha256(binary.read_bytes()).hexdigest()==capture['bin_sha256']
out=ROOT/'docs/screenshots/launchpad';out.mkdir(parents=True,exist_ok=True)
for frame in [359,420,480,570,700,850,1200,1400,1650,2199]:
 shutil.copyfile(folder/f'frame_{frame:04d}.png',out/f'frame_{frame:04d}.png')
shutil.copyfile(folder/'capture.json',out/'capture.json')
result={'source_commit':os.environ['GITHUB_SHA'],'bin_sha256':capture['bin_sha256'],'scene':'level3','component_path_id':7246,
        'launches_started':last['launch_started'],'launches_completed':last['launch_completed'],'launches_cancelled':last['launch_cancelled'],
        'paused_samples':len(paused),'trajectory_samples':len(flight),'camera_tracked_samples':len(flight),'final_position_fp':[last['x_fp'],last['y_fp'],last['z_fp']],
        'grounded':True,'automatic_respawns':0,'validation':'Controller-only HLE prototype: original arc, paused flight, Select cancellation, retry and stable landing; manual Triangle activation substitutes for companion/Somersault behavior'}
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
