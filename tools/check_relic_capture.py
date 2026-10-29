"""Controller-only collection route, respawn preservation and title clearing."""
import hashlib,json,os,shutil,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];folder=Path(sys.argv[1]);j=json.loads((folder/'capture.json').read_text());rows=j['state_samples']
assert j['frames_run']==5700
r=next(s for s in rows if s['frame']==1900)
assert (r['relic_mask'],r['relic_count'],r['relic_value'])==(1,1,8),r
assert r['state']==0 and r['player_respawn_events']==0
second=next(s for s in rows if s['frame']==3300)
assert (second['relic_mask'],second['relic_count'],second['relic_value'])==(3,2,16)
third=next(s for s in rows if s['frame']==4700)
assert (third['relic_mask'],third['relic_count'],third['relic_value'])==(7,3,20)
s=next(s for s in rows if s['frame']==5000)
assert (s['relic_mask'],s['relic_count'],s['relic_value'])==(7,3,20)
assert s['x_fp']==0 and s['z_fp']==0
restart=next(s for s in rows if s['frame']==5150)
assert (restart['relic_mask'],restart['relic_count'],restart['relic_value'])==(0,0,0)
assert (restart['x_fp'],restart['y_fp'],restart['z_fp'],restart['state'],restart['launch_active'])==(0,0,0,0,0)
assert restart['menu_screen']==1
assert next(s for s in rows if s['frame']==5420)['menu_screen']==0
assert all(s['relic_value']==0 for s in rows if s['frame']>=5420)
assert rows[-1]['menu_screen']==1 and rows[-1]['audio_cd_errors']==0
h=hashlib.sha256((folder.parent/'zera_launchpad_preview.bin').read_bytes()).hexdigest();assert h==j['bin_sha256']
out=root/'docs/screenshots/relics';out.mkdir(parents=True,exist_ok=True)
for n in [359,850,1300,1900,2450,3300,4000,4700,5000,5150,5420,5699]:shutil.copyfile(folder/f'frame_{n:04d}.png',out/f'frame_{n:04d}.png')
replay=root/'docs/screenshots/replay';replay.mkdir(parents=True,exist_ok=True)
shutil.copyfile(folder/'frame_4700.png',replay/'after.png')
shutil.copyfile(folder/'frame_5150.png',replay/'restart.png')
shutil.copyfile(folder/'capture.json',out/'capture.json')
v={'source_commit':os.environ['GITHUB_SHA'],'bin_sha256':h,'collected_native':3,'value_native':20,'respawn_preserved':True,'title_cleared':True,'area_restart_verified':True,'early_restart_ignored':True,'automatic_respawns':0,'validation':'Input-only HLE original-position collection prototype; provisional pickup volume and material, session-only progress'}
(out/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
