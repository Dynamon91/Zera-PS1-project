"""Verify blocking against the recovered solid collider plane, using controller input."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]


def check(folder):
    folder=Path(folder);capture=json.loads((folder/'capture.json').read_text())
    assert capture['content']=='zera_level3_preview.cue' and capture['frames_run']==1100
    world=json.loads((ROOT/'previews/level3/assets/world_chunk_source.json').read_text())
    assert [547,-161,547,185,0,265] in world['walls']
    assert [574,0,181,574,0,-190,547,265,-161] in world['wall_triangles']
    rows=capture['state_samples'];late=[r for r in rows if 950<=r['frame']<=1080]
    assert len(late)==27
    for r in late:
        assert r['debug_input_x']==1 and r['debug_input_z']==0 and r['yaw']==0
        assert 537*256<=r['x_fp']<=538*256 and r['z_fp']==0 and r['y_fp']==0
        assert r['state']==0 and r['menu_screen']==1
    assert any(r['debug_actual_moving']==1 and r['x_fp']<500*256 for r in rows)
    assert all(r['player_respawn_events']==0 and r['audio_cd_errors']==0 for r in rows)
    final=rows[-1];assert final['frame']==1099 and final['audio_music_ready']==1
    assert 537*256<=final['x_fp']<=538*256 and final['z_fp']==0
    binary=folder.parent/'zera_level3_preview.bin'
    assert hashlib.sha256(binary.read_bytes()).hexdigest()==capture['bin_sha256']
    return {'frames':1100,'bin_sha256':capture['bin_sha256'],'emulator':capture['emulator'],
            'wall_x_at_ground':574,'wall_x_at_head':562,'previous_proxy_x':547,'player_radius':24,'final_position':[final['x_fp']/256,final['y_fp']/256,final['z_fp']/256],
            'blocked_while_holding_right':True,'automatic_respawns':0,
            'limitations':['One sloped wall route in a bounded patch','Height-clipped triangle projection, not a continuous capsule sweep','HLE only; does not demonstrate the path to the original checkpoint']}


if __name__=='__main__':print(json.dumps(check(sys.argv[1]),indent=2))
