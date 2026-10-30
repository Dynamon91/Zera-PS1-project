"""Verify a continuous controller-only route beyond the former level3 boundary."""
import hashlib,json,sys
from pathlib import Path
from audit_preview_collectibles import floor_layers
ROOT=Path(__file__).resolve().parents[1]
def check(folder):
    folder=Path(folder);capture=json.loads((folder/'capture.json').read_text())
    assert capture['content']=='zera_level3_preview.cue' and capture['frames_run']==2400
    rows=capture['state_samples'];last=rows[-1]
    assert last['frame']==2399 and last['menu_screen']==1 and last['state']==0
    assert last['x_fp']==0 and -2010*256<=last['z_fp']<=-2000*256
    assert all(r['player_respawn_events']==0 and r['audio_cd_errors']==0 for r in rows)
    assert all(rows[i]['z_fp']<=rows[i-1]['z_fp'] for i in range(1,len(rows)))
    assert any(r['z_fp']< -1280*256 for r in rows)
    assert last['scenario_movement_stopped'] and last['audio_music_ready']==1
    world=json.loads((ROOT/'previews/level3/assets/world_chunk_source.json').read_text())
    layers=floor_layers(world['floor_triangles'],0,last['z_fp']//256)
    floor=max(h for h in layers if h<=last['y_fp']//256+48)
    assert floor*256==last['y_fp']
    binary=folder.parent/'zera_level3_preview.bin';assert hashlib.sha256(binary.read_bytes()).hexdigest()==capture['bin_sha256']
    return {'frames':2400,'bin_sha256':capture['bin_sha256'],'emulator':capture['emulator'],
            'final_position':[0,floor,last['z_fp']//256],'previous_boundary_z':-1280,'automatic_respawns':0,
            'validation':'Continuous controller-only walk from original start, beyond previous patch, grounded on recovered original colliders',
            'limitations':['This scenario demonstrates only the first 2000 units; later relic/checkpoint routes have separate checks','Full original level progression remains incomplete','HLE only; performance and hardware not certified']}
if __name__=='__main__':print(json.dumps(check(sys.argv[1]),indent=2))
