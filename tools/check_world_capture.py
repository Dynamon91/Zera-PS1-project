"""Verify controller-only exploration beyond the previous recovered patch."""
import json
import os
from pathlib import Path
import shutil
import sys

root=Path(__file__).resolve().parent.parent
before=Path(sys.argv[1]);after=Path(sys.argv[2])
old=json.loads((before/'capture.json').read_text());new=json.loads((after/'capture.json').read_text())
assert old['frames_run']==3000 and new['frames_run']==3000
assert old['bin_sha256']!=new['bin_sha256']
last=new['state_samples'][-1]
assert last['x_fp']//256>=2200 and abs(last['z_fp'])<256
assert last['state']==0 and last['player_respawn_events']==0
data=json.loads((root/'assets/world_chunk_source.json').read_text())
report=data['report'];grid=data['heightfield'];layout=report['heightfield']
assert report['source_radius_units']==32 and layout['size']==129
x=int(last['x_fp']/256)-layout['origin'];z=int(last['z_fp']/256)-layout['origin']
step=layout['step'];ix,fx=divmod(x,step);iz,fz=divmod(z,step)
a,b,c,d=grid[iz][ix],grid[iz][ix+1],grid[iz+1][ix],grid[iz+1][ix+1]
if fx+fz<=step:
    assert -32768 not in (a,b,c)
    height=a+int(((b-a)*fx+(c-a)*fz)/step)
else:
    assert -32768 not in (b,c,d)
    height=d+int(((c-d)*(step-fx)+(b-d)*(step-fz))/step)
assert last['y_fp']==height*256, 'player is not on the recovered source floor'
out=root/'docs/screenshots/world';out.mkdir(parents=True,exist_ok=True)
for label,source in [('before',before),('after',after)]:
    shutil.copyfile(source/'frame_2999.png',out/(label+'.png'))
    shutil.copyfile(source/'capture.json',out/(label+'_capture.json'))
result={'source_commit':os.environ['GITHUB_SHA'],'bin_sha256':new['bin_sha256'],
        'baseline_bin_sha256':old['bin_sha256'],'previous_radius':16,'new_radius':32,
        'render_triangles':report['render_triangles'],'world_grid_size':layout['size'],
        'final_x':last['x_fp']//256,'final_y':height,'final_z':last['z_fp']//256,
        'grounded_beyond_old_boundary':True,'automatic_respawns':0,
        'emulator':new['emulator'],'validation':'Input-only HLE exploration; not a full level or hardware test'}
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
(root/'docs/WORLD.md').write_text(f'''# Larger recovered original-world patch

The source archive was recovered and the level2 scene was converted with its
original transforms. Radius grows from 16 to 32 source units: a **64×64** source-unit
square rather than 32×32. This is extraction extent, not a claim of four times
the complete game's playable content. Rendering grows from 591 to
**{report['render_triangles']} triangles**, including original Walkable.000 and
Walkable.002. The collision grid grows from 65×65 to 129×129 at the same spacing.
Source file hashes, mesh IDs and world matrices are recorded in
`reports/world_conversion.json`. No replacement environment geometry was invented.

| WIP08 reference, previous patch | Expanded native patch |
| --- | --- |
| ![Previous patch](screenshots/world/before.png) | ![Expanded patch](screenshots/world/after.png) |

Both captures use the same controller scenario, attempting to reach X=2200 and
then stopping via read-only position feedback. Their simulated trajectories and
timing can diverge: the previous patch lacks terrain beyond +/-1280. This is
not a frame-matched visual fidelity claim. The new 3,000-frame run finishes at
**({result['final_x']}, {height}, {result['final_z']})**, grounded on the recovered
heightfield beyond the old boundary, with **zero automatic respawns**.

Source tested: `{result['source_commit']}`. Original scene placements and main
textures are used; custom shaders, actors, water/effects, full original level
flow and authored progression remain omitted. The collision heightfield cannot
represent overlapping floors and is capped at spawn+6 source units. Validation
is an HLE smoke test, not retail-BIOS/hardware or frame-rate certification.
''')
print(json.dumps(result))
