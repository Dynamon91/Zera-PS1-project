"""Validate controller-only checkpoint activation, respawns and new-game clearing."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]


def check(folder):
    folder=Path(folder);capture=json.loads((folder/'capture.json').read_text())
    config=json.loads((ROOT/'previews/checkpoint/reports/checkpoint_config.json').read_text())
    assert capture['content']=='zera_checkpoint_preview.cue' and capture['frames_run']==1750
    rows=capture['state_samples'];samples={r['frame']:r for r in rows}
    assert len(samples)==len(rows) and samples[1749]['frame']==1749
    assert all(r['audio_cd_errors']==0 and r['player_respawn_events']==0 for r in rows)
    entry=config['test_entry'];spawn=config['spawn']
    assert samples[359]['checkpoint_id']==0
    assert samples[359]['x_fp']==entry[0]*256 and samples[359]['menu_screen']==1
    activated=next(r for r in rows if r['checkpoint_id'])
    assert activated['checkpoint_id']==config['component_path_id']==6752
    dx=activated['x_fp']//256-config['trigger'][0];dz=activated['z_fp']//256-config['trigger'][2]
    assert dx*dx+dz*dz<=160*160 and activated['state']==0
    assert samples[760]['x_fp']>160*256
    for frame in (760,850,1060,1220):
        r=samples[frame]
        assert r['checkpoint_id']==6752 and r['checkpoint_activations']==1
        assert [r['checkpoint_x'],r['checkpoint_y'],r['checkpoint_z']]==spawn
    for frame in (850,1220):
        r=samples[frame]
        assert r['menu_screen']==1 and r['state']==0
        assert r['x_fp']==spawn[0]*256 and r['z_fp']==spawn[2]*256 and abs(r['y_fp']-spawn[1]*256)<=2*256
        assert r['yaw']==r['checkpoint_yaw']==config['camera_yaw']
    assert samples[1060]['x_fp']>160*256
    assert samples[1600]['menu_screen']==0 and samples[1749]['menu_screen']==1
    for frame in (1600,1749):
        assert samples[frame]['checkpoint_id']==0 and samples[frame]['checkpoint_activations']==0
        assert samples[frame]['x_fp']==entry[0]*256 and samples[frame]['z_fp']==entry[2]*256
    assert samples[1749]['audio_music_ready']==1
    binary=folder.parent/'zera_checkpoint_preview.bin'
    assert hashlib.sha256(binary.read_bytes()).hexdigest()==capture['bin_sha256']
    files=['src/checkpoint.c','src/checkpoint.h','src/main.c','src/player.c','src/world.c','src/surface.c',
           'previews/checkpoint/src/checkpoint_config.h','previews/checkpoint/assets/world_chunk_source.json',
           'tools/scenarios/checkpoint_preview.json']
    return {'schema_version':1,'bin_sha256':capture['bin_sha256'],'emulator':capture['emulator'],
            'frames':1750,'component_path_id':6752,'select_respawn':True,'pause_respawn':True,
            'new_game_clears':True,'camera_yaw':config['camera_yaw'],
            'source_files_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},
            'milestones':[samples[f] for f in (359,760,850,1060,1220,1600,1749)],
            'limitations':['Provisional proximity trigger, original Kiwi interaction absent','Session state only; no memory-card persistence',
                           'Dedicated area with test entry; no continuous route from original level start demonstrated',
                           'Adapted orbit direction, not full original camera transform','HLE validation only']}


if __name__=='__main__':
    print(json.dumps(check(sys.argv[1]),indent=2))
