"""Check both original lower-corridor relics in one continuous controller run."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def check(folder):
    folder=Path(folder);j=json.loads((folder/'capture.json').read_text());rows=j['state_samples'];s={r['frame']:r for r in rows}
    assert j['content']=='zera_level3_preview.cue' and j['frames_run']==7400
    assert all(r['player_respawn_events']==0 and r['audio_cd_errors']==0 for r in rows)
    assert s[359]['relic_mask']==0 and s[359]['menu_screen']==1
    first=next(r for r in rows if r['relic_mask']==1)
    assert first['relic_count']==1 and first['relic_value']==1
    second=next(r for r in rows if r['relic_mask']==3)
    assert second['frame']>first['frame'] and second['relic_count']==2 and second['relic_value']==17
    dx=int(second['x_fp']/256)+980;dz=int(second['z_fp']/256)+6473;dy=int(second['y_fp']/256)+32+471
    assert dx*dx+dz*dz<=44*44 and -64<=dy<=64
    for frame in (6500,6700):
        r=s[frame];assert (r['relic_mask'],r['relic_count'],r['relic_value'])==(3,2,17)
        assert r['sfx_events'][6]==2
    assert s[6500]['sfx_events'][2]>=2 and s[6500]['z_fp']< -6400*256
    assert s[6700]['x_fp']==0 and s[6700]['z_fp']==0
    assert s[7200]['menu_screen']==0 and s[7200]['relic_mask']==0
    assert s[7399]['menu_screen']==1 and s[7399]['relic_count']==0 and s[7399]['relic_value']==0
    assert s[7399]['audio_music_ready']==1
    events={e['name']:e for e in j['event_captures']}
    assert [events[n]['relic_mask'] for n in ('first_approach','first_collected','second_approach','second_collected')]==[0,1,1,3]
    assert events['first_collected']['frame']<events['second_collected']['frame']
    assert events['second_collected']['frame']-events['second_collected']['trigger_frame']>=15
    layout=json.loads((ROOT/'previews/level3/reports/corridor_relic_layout.json').read_text())
    assert [(e['component_path_id'],e['position'],e['value']) for e in layout['items']]==[(6606,[-49,-148,-3794],1),(6898,[-980,-471,-6473],16)]
    binary=folder.parent/'zera_level3_preview.bin';assert hashlib.sha256(binary.read_bytes()).hexdigest()==j['bin_sha256']
    images={n:hashlib.sha256((folder/(n+'.png')).read_bytes()).hexdigest() for n in events}
    files=['src/relics.c','src/relics.h','src/main.c','previews/level3/src/relic_layout.h','previews/level3/src/relic_models.h','tools/scenarios/corridor_two_relics.json']
    return {'schema_version':1,'components':[6606,6898],'native_count':2,'native_value':17,'frames':7400,'bin_sha256':j['bin_sha256'],
            'emulator':j['emulator'],'automatic_respawns':0,'respawn_preserves':True,'title_clears':True,'pickup_sounds':2,
            'event_captures':j['event_captures'],'image_sha256':images,
            'source_files_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},
            'milestones':[s[f] for f in (359,6500,6700,7200,7399)],
            'limitations':['Two active relics only, not full level completion','Provisional pickup volume and movement tuning; original homing/effects/shaders absent','Session only; no memory-card save','HLE only, no frame-rate or hardware certification'],
            'next_milestone':'Recover and render the original checkpoint plant in the connected area'}
if __name__=='__main__':print(json.dumps(check(sys.argv[1]),indent=2))
