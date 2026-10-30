"""Validate controller-only PS1 CD world-atlas captures and streaming changes."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def check(folder,level=None,streaming=False):
    folder=Path(folder);j=json.loads((folder/'capture.json').read_text());rows=j['state_samples'];last=rows[-1]
    assert j['content']=='zera_world_atlas.cue'
    assert hashlib.sha256((folder.parent/'zera_world_atlas.bin').read_bytes()).hexdigest()==j['bin_sha256']
    assert all(r['atlas_errors']==0 for r in rows)
    assert last['atlas_ready']==1
    assert all(r['atlas_budget_drops']==0 for r in rows)
    report=json.loads((ROOT/'previews/atlas/reports/world_atlas.json').read_text())
    assert all(0<=r['atlas_triangle_count']<=report['maximum_resident_triangles'] for r in rows)
    if streaming:
        assert j['frames_run']==5000
        a=next(r for r in rows if r['frame']==900)
        b=next(r for r in rows if r['frame']==2200)
        c=next(r for r in rows if r['frame']==2480)
        assert a['atlas_scene']==b['atlas_scene']==0 and a['atlas_menu']==b['atlas_menu']==0
        assert a['atlas_camera']!=b['atlas_camera'] and b['atlas_load_events']>a['atlas_load_events']
        assert c['atlas_show_inactive']==1
        assert last['atlas_scene']==1 and last['atlas_menu']==0 and last['atlas_loaded_tiles']>0
        assert last['atlas_load_events']>b['atlas_load_events'] and last['atlas_budget_drops']==0
    else:
        assert j['frames_run']==2100 and last['frame']==2099
        assert last['atlas_scene']==level-2 and last['atlas_menu']==0
        assert last['atlas_loaded_tiles']>0 and last['atlas_triangle_count']>0
        assert last['atlas_drawn']>0 and last['atlas_budget_drops']==0
    return {'frames':j['frames_run'],'bin_sha256':j['bin_sha256'],'emulator':j['emulator'],
            'scene':last['atlas_scene'],'loaded_tiles':last['atlas_loaded_tiles'],'resident_triangles':last['atlas_triangle_count'],
            'load_events':last['atlas_load_events'],'cd_errors':0,'final_gpu_budget_drops':0,'peak_sampled_gpu_budget_drops':0,
            'streaming_movement_and_map_change':streaming,'final_state':last,
            'limitation':'HLE free-camera geometry inspection; no player physics or complete level gameplay'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);p.add_argument('--level',type=int);p.add_argument('--streaming',action='store_true');a=p.parse_args()
    if not a.streaming and a.level not in range(2,8):p.error('--level 2..7 or --streaming required')
    print(json.dumps(check(a.folder,a.level,a.streaming),indent=2))
