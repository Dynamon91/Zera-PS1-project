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
x=int(last['x_fp']/256);z=int(last['z_fp']/256)
heights=[];all_heights=[]
for triangle in world['floor_triangles']:
 a,b,c=triangle
 den=(b[2]-c[2])*(a[0]-c[0])+(c[0]-b[0])*(a[2]-c[2])
 wa=(b[2]-c[2])*(x-c[0])+(c[0]-b[0])*(z-c[2])
 wb=(c[2]-a[2])*(x-c[0])+(a[0]-c[0])*(z-c[2]);wc=den-wa-wb
 if den<0:den=-den;wa=-wa;wb=-wb;wc=-wc
 if not den or min(wa,wb,wc)<0:continue
 h=int((wa*a[1]+wb*b[1]+wc*c[1])/den);all_heights.append(h)
 if h<=last['y_fp']//256+48:heights.append(h)
assert heights
height=max(heights)
assert height==0
assert last['y_fp']==height*256
binary=source.parent/'zera_level3_preview.bin';assert hashlib.sha256(binary.read_bytes()).hexdigest()==capture['bin_sha256']
out=root/'docs/screenshots/level3';out.mkdir(parents=True,exist_ok=True)
shutil.copyfile(root/'docs/screenshots/wip09/frame_0359.png',out/'before_level2.png')
for frame in [359,1599]:shutil.copyfile(source/f'frame_{frame:04d}.png',out/f'level3_{frame:04d}.png')
shutil.copyfile(source/'capture.json',out/'capture.json')
result={'source_commit':os.environ['GITHUB_SHA'],'bin_sha256':capture['bin_sha256'],'scene':'level3',
        'final_position':[last['x_fp']//256,height,last['z_fp']//256],'grounded':True,'automatic_respawns':0,
        'floor_support':'original uncapped collider triangles selected by player height','overhead_surface_heights':sorted(set(v for v in all_heights if v>height)),'render_triangles':report['render_triangles'],'source_patch_triangles':report['source_patch_triangles_before_render_partition'],
        'validation':'Separate level3 bounded terrain preview; input-only HLE smoke test; no original progression implemented'}
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
bounds=report.get('source_bounds_units',[-report['source_radius_units'],report['source_radius_units']]*2)
footprint=f"{bounds[1]-bounds[0]:g}×{bounds[3]-bounds[2]:g}"
(root/'docs/LEVEL3.md').write_text(f'''# Original level3 terrain preview

A second PS1 disc now opens a bounded patch around the original level3 named
start spawn at (44, 22.82, 111) in Unity coordinates. It uses original static
terrain and vertex colors/main texture, with {result['source_patch_triangles']} globally clipped source triangles
and {result['render_triangles']} cell-partitioned render triangles. The extraction region is {footprint}
source units; this is an early terrain preview, not a complete level.
The extended route beyond the previous patch is documented in [Dreary Valley corridor](DREARY_CORRIDOR.md).

| Existing WIP09 level2 start | New level3 start |
| --- | --- |
| ![Level2](screenshots/level3/before_level2.png) | ![Level3](screenshots/level3/level3_0359.png) |

Actual emulator captures show two different original areas, not a frame-matched
fidelity comparison. The new controller-only 1600-video-frame scenario walks to
**{tuple(result['final_position'])}** and finishes grounded, with zero automatic
respawns. Host tests separately walk 500 world units in all four directions. They also
verify height selection at actual overlapping collider surfaces; the native
walking route does not demonstrate a traversable underpass.

![Level3 after walking](screenshots/level3/level3_1599.png)

## Run the separate preview

Extract `native/Zera_PS1_WIP09_Native.zip` from the source package and open
`build/zera_level3_preview.cue` with its BIN beside it. The established
`build/zera_wip09.cue` still opens the level2 build. To build locally, use the
existing CMake preset; it now produces both disc images.

The preview title identifies level3, and its pause menu omits the six-token
trial because that new test layout belongs to the level2 patch. The main
character, animation, controls and audio are shared adaptations. Original relic
6606 and 6898 now have session collection ([evidence](TWO_CORRIDOR_RELICS.md)). Other original
relics, essences, lava hazards, enemies, complete level flow and
saving remain inactive in this disc.
Checkpoint 6752 now connects to the lower relic route with provisional proximity
activation ([evidence](CONNECTED_CHECKPOINT.md)); original Kiwi interaction is absent.
Floor support now uses original uncapped collider triangles and selects the
highest support below the player's step/landing ceiling. The legacy diagnostic
heightfield remains single-valued; it no longer determines level3 player support.
This supports stacked surfaces. Current source also stops upward head motion
against projected overhead collider triangles; see [validation and limits](CEILINGS.md).
Full capsule collision is still absent and steep-wall proxies remain conservative.
Only the source area's static environment root is converted; lava is omitted.
Current level3 walls now come from the original enabled, non-trigger static
MeshColliders, including `Walls.*`, instead of the render mesh. See
[wall provenance and tests](WALL_COLLIDERS.md). Vertical proxies remain an approximation.

## Static batch recovery

The source uses Unity scene-space static batches. Conversion selects only each
renderer’s declared `firstSubMesh`/`subMeshCount`, applies no individual-object
transform to scene-space vertices, and maps material slots relative to that
range. Non-scene batch roots are rejected. All converted walkable render bounds are checked
against separately stored collider-local meshes transformed by their original
hierarchy; maximum differences are below 0.041 source units. This cross-check
supports the batch transform/submesh interpretation, not full Unity physics.

[Source conversion and hashes](../previews/level3/reports/world_conversion.json) ·
[Collider comparison](../previews/level3/reports/batch_validation.json) ·
[Native verification](screenshots/level3/verification.json).

```sh
python3 tools/convert_world.py "/path/to/Zera Myths Awaken_Data" --scene level3 --radius 96 --bounds -24 24 -96 16 --output-root previews/level3
python3 tools/check_level3_batch_source.py "/path/to/Zera Myths Awaken_Data"
```

Native source tested: `{result['source_commit']}`. HLE interpreter/software-GPU
verification is not retail BIOS or physical-hardware validation. Completion
remains the provisional **29%** while this separate content preview is integrated.
''')
print(json.dumps(result))
