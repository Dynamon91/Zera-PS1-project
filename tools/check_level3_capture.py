"""Verify the separate level3 disc using controller input and read-only RAM samples."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
root=Path(__file__).resolve().parents[1]
source=Path(sys.argv[1]);capture=json.loads((source/'capture.json').read_text())
assert capture['content']=='zera_level3_preview.cue' and capture['frames_run']==1600
last=capture['state_samples'][-1]
assert last['frame']==1599 and last['menu_screen']==1 and last['state']==0
assert 500<=last['x_fp']//256<=510 and abs(last['z_fp'])<256
assert last['player_respawn_events']==0 and last['simulation_ticks']>=50
assert last['audio_cd_errors']==0
world=json.loads((root/'previews/level3/assets/world_chunk_source.json').read_text())
report=world['report'];assert report['scene']=='level3'
grid=world['heightfield'];layout=report['heightfield'];step=layout['step']
x=int(last['x_fp']/256)-layout['origin'];z=int(last['z_fp']/256)-layout['origin'];ix,fx=divmod(x,step);iz,fz=divmod(z,step)
a,b,c,d=grid[iz][ix],grid[iz][ix+1],grid[iz+1][ix],grid[iz+1][ix+1]
if fx+fz<=step:
 assert -32768 not in (a,b,c);height=a+int(((b-a)*fx+(c-a)*fz)/step)
else:
 assert -32768 not in (b,c,d);height=d+int(((c-d)*(step-fx)+(b-d)*(step-fz))/step)
assert last['y_fp']==height*256
binary=source.parent/'zera_level3_preview.bin';assert hashlib.sha256(binary.read_bytes()).hexdigest()==capture['bin_sha256']
out=root/'docs/screenshots/level3';out.mkdir(parents=True,exist_ok=True)
shutil.copyfile(root/'docs/screenshots/wip09/frame_0359.png',out/'before_level2.png')
for frame in [359,1599]:shutil.copyfile(source/f'frame_{frame:04d}.png',out/f'level3_{frame:04d}.png')
shutil.copyfile(source/'capture.json',out/'capture.json')
result={'source_commit':os.environ['GITHUB_SHA'],'bin_sha256':capture['bin_sha256'],'scene':'level3',
        'final_position':[last['x_fp']//256,height,last['z_fp']//256],'grounded':True,'automatic_respawns':0,
        'render_triangles':report['render_triangles'],'source_patch_triangles':report['source_patch_triangles_before_render_partition'],
        'validation':'Separate level3 bounded terrain preview; input-only HLE smoke test; no original progression implemented'}
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
(root/'docs/LEVEL3.md').write_text(f'''# Original level3 terrain preview

A second PS1 disc now opens a bounded patch around the original level3 named
start spawn at (44, 22.82, 111) in Unity coordinates. It uses original static
terrain and vertex colors/main texture, with {result['source_patch_triangles']} globally clipped source triangles
and {result['render_triangles']} cell-partitioned render triangles. The extraction square is 32×32
source units; this is an early terrain preview, not a complete level.

| Existing WIP09 level2 start | New level3 start |
| --- | --- |
| ![Level2](screenshots/level3/before_level2.png) | ![Level3](screenshots/level3/level3_0359.png) |

Actual emulator captures show two different original areas, not a frame-matched
fidelity comparison. The new controller-only 1600-video-frame scenario walks to
**{tuple(result['final_position'])}** and finishes grounded, with zero automatic
respawns. Host tests separately walk 500 world units in all four directions.

![Level3 after walking](screenshots/level3/level3_1599.png)

## Run the separate preview

Extract `native/Zera_PS1_WIP09_Native.zip` from the source package and open
`build/zera_level3_preview.cue` with its BIN beside it. The established
`build/zera_wip09.cue` still opens the level2 build. To build locally, use the
existing CMake preset; it now produces both disc images.

The preview title identifies level3, and its pause menu omits the six-token
trial because that new test layout belongs to the level2 patch. The main
character, animation, controls and audio are shared adaptations. Original relics,
essences, checkpoints, lava hazards, enemies, level flow and saving are not active.
The heightfield remains single-valued and capped at spawn+6 source units.
Only the source area's static environment root is converted; lava is omitted.

## Static batch recovery

The source uses Unity scene-space static batches. Conversion selects only each
renderer’s declared `firstSubMesh`/`subMeshCount`, applies no individual-object
transform to scene-space vertices, and maps material slots relative to that
range. Non-scene batch roots are rejected. Two walkable render bounds are checked
against separately stored collider-local meshes transformed by their original
hierarchy; maximum differences are below 0.041 source units. This cross-check
supports the batch transform/submesh interpretation, not full Unity physics.

[Source conversion and hashes](../previews/level3/reports/world_conversion.json) ·
[Collider comparison](../previews/level3/reports/batch_validation.json) ·
[Native verification](screenshots/level3/verification.json).

```sh
python3 tools/convert_world.py "/path/to/Zera Myths Awaken_Data" --scene level3 --radius 16 --output-root previews/level3
python3 tools/check_level3_batch_source.py "/path/to/Zera Myths Awaken_Data"
```

Native source tested: `{result['source_commit']}`. HLE interpreter/software-GPU
verification is not retail BIOS or physical-hardware validation. Completion
remains the provisional **29%** while this separate content preview is integrated.
''')
print(json.dumps(result))
