"""Validate a natural off-map fall and view reset without editing game RAM."""
import json
import os
from pathlib import Path
import shutil
import sys

root=Path(__file__).resolve().parent.parent
directory=Path(sys.argv[1]);report=json.loads((directory/'capture.json').read_text())
assert report['frames_run']==4800
rows=report['state_samples'];last=rows[-1]
lowest=min(r['y_fp']//256 for r in rows)
print(json.dumps({'lowest':lowest,'last':last,'max_x':max(r['x_fp']//256 for r in rows),'checkpoints':[r for r in rows if r['frame'] in [650,1200,1800,2400,3000,3800]]}),flush=True)
assert lowest<-700, 'did not cross the old spawn-relative safety plane'
assert last['player_respawn_events']==1, 'expected one natural fall respawn'
assert last['x_fp']==0 and last['z_fp']==0 and last['y_fp']==0 and last['state']==0
assert last['camera_distance']==850 and last['camera_height']==0, 'stale camera after respawn'
result={'source_commit':os.environ['GITHUB_SHA'],'bin_sha256':report['bin_sha256'],
        'minimum_sampled_y_world_units':lowest,'automatic_respawns':last['player_respawn_events'],
        'final_camera_distance':last['camera_distance'],'final_camera_height':last['camera_height'],
        'emulator':report['emulator'],'validation':'Natural input-only fall in HLE; no hardware test'}
out=root/'docs/screenshots/respawn';out.mkdir(parents=True,exist_ok=True)
shots=[r for r in rows if (directory/f"frame_{r['frame']:04d}.png").is_file()]
fall=min(shots,key=lambda r:r['y_fp'])
shutil.copyfile(directory/f"frame_{fall['frame']:04d}.png",out/'fall.png')
shutil.copyfile(directory/'frame_4799.png',out/'spawn.png')
shutil.copyfile(directory/'capture.json',out/'capture.json')
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
(root/'docs/RESPAWN.md').write_text(f'''# Terrain-relative fall recovery

Native source: `{result['source_commit']}`.

The safety plane is now 700 units below the lowest valid heightfield sample
(-4077 in this recovered patch), instead of -700 relative to spawn.
Host tests check landing on valid ground at -800 and reject missing samples
when deriving the limit. Native input-only testing checks the off-map path:
minimum sampled Y **{lowest}**, one automatic respawn, then player at spawn and
camera restored to distance 850 / height 0. Movement is released using read-only Y feedback after the fall starts. No game RAM is edited.

| Falling | Recovered at spawn |
| --- | --- |
| ![Fall](screenshots/respawn/fall.png) | ![Spawn](screenshots/respawn/spawn.png) |

This changes a provisional safety rule; it does not add new level geometry or
claim fidelity to the original game's death/checkpoint rules. HLE validation
does not establish retail-BIOS or hardware compatibility.
''')
print(json.dumps(result))
