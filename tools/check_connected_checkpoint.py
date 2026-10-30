"""Verify the original start -> two relics -> checkpoint -> preserved respawns."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def check(folder):
    folder=Path(folder);j=json.loads((folder/'capture.json').read_text());rows=j['state_samples'];s={r['frame']:r for r in rows}
    assert j['content']=='zera_level3_preview.cue' and j['frames_run']==11200
    assert all(r['player_respawn_events']==0 and r['audio_cd_errors']==0 for r in rows)
    assert s[359]['checkpoint_id']==0 and s[359]['relic_mask']==0 and s[359]['x_fp']==0 and s[359]['z_fp']==0
    first=next(r for r in rows if r['relic_mask']==3)
    active=next(r for r in rows if r['checkpoint_id']==6752)
    assert active['frame']>first['frame'] and active['relic_count']==2 and active['relic_value']==17 and active['state']==0
    assert s[10050]['sfx_events'][2]>=4
    assert active['sfx_events'][1]==first['sfx_events'][1]+1
    config=json.loads((ROOT/'previews/level3/reports/checkpoint_config.json').read_text())
    assert config['component_path_id']==6752 and config['spawn']==[1356,-115,-7101] and config['camera_yaw']==1447
    dx=int(active['x_fp']/256)-config['trigger'][0];dz=int(active['z_fp']/256)-config['trigger'][2]
    assert dx*dx+dz*dz<=160*160 and abs(int(active['y_fp']/256)-config['trigger'][1])<=80
    for frame in (10050,10300,10580,10720):
        r=s[frame];assert (r['relic_mask'],r['relic_count'],r['relic_value'])==(3,2,17)
        assert r['checkpoint_id']==6752 and r['checkpoint_activations']==1 and r['checkpoint_yaw']==1447
        assert [r['checkpoint_x'],r['checkpoint_y'],r['checkpoint_z']]==config['spawn']
        assert r['sfx_events'][6]==2 and r['menu_screen']==1
    for frame in (10300,10720):
        r=s[frame];assert [r['x_fp']//256,r['y_fp']//256,r['z_fp']//256]==[1356,-113,-7101] and r['state']==0
    assert abs(s[10580]['x_fp']-1356*256)>160*256
    assert any(r['yaw']==1447 and r['x_fp']==1356*256 for r in rows if 10210<=r['frame']<=10250)
    for frame in (11000,11199):
        r=s[frame];assert r['checkpoint_id']==0 and r['checkpoint_activations']==0 and r['relic_mask']==0 and r['relic_value']==0
        assert r['x_fp']==0 and r['z_fp']==0
    assert s[11000]['menu_screen']==0 and s[11199]['menu_screen']==1 and s[11199]['audio_music_ready']==1
    events={e['name']:e for e in j['event_captures']}
    assert events['two_relics']['frame']<events['checkpoint_active']['frame']<events['checkpoint_return']['frame']
    assert events['checkpoint_active']['checkpoint_id']==events['checkpoint_return']['checkpoint_id']==6752
    assert events['checkpoint_return']['relic_mask']==3
    binary=folder.parent/'zera_level3_preview.bin';assert hashlib.sha256(binary.read_bytes()).hexdigest()==j['bin_sha256']
    files=['src/main.c','src/checkpoint.c','src/checkpoint.h','src/relics.c','previews/level3/src/checkpoint_config.h','previews/level3/reports/checkpoint_config.json','tools/scenarios/connected_checkpoint.json']
    return {'schema_version':1,'checkpoint_id':6752,'relic_count':2,'relic_value':17,'frames':11200,'bin_sha256':j['bin_sha256'],
            'emulator':j['emulator'],'automatic_respawns':0,'select_respawn_preserves':True,'pause_respawn_preserves':True,'title_clears_all':True,
            'restored_camera_yaw':1447,'spawn_position':[1356,-115,-7101],'grounded_position':[1356,-113,-7101],
            'event_captures':j['event_captures'],'image_sha256':{n:hashlib.sha256((folder/(n+'.png')).read_bytes()).hexdigest() for n in events},
            'source_files_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},
            'milestones':[s[f] for f in (359,10050,10300,10580,10720,11000,11199)],
            'limitations':['Grounded proximity activation substitutes original Kiwi interaction; plant/fruit animations absent','Adapted orbit yaw only, not full original camera or character pose','Session only; no memory-card persistence','HLE only; frame rate, retail BIOS and hardware not certified'],
            'next_milestone':'Recover and render the original checkpoint plant in the connected area'}
if __name__=='__main__':print(json.dumps(check(sys.argv[1]),indent=2))
