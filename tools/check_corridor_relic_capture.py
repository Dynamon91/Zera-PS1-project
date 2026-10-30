"""Verify continuous original relic 6606 collection, audio and session behavior."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def check(folder):
    folder=Path(folder);j=json.loads((folder/'capture.json').read_text());rows=j['state_samples'];s={r['frame']:r for r in rows}
    assert j['content']=='zera_level3_preview.cue' and j['frames_run']==4500
    assert all(r['player_respawn_events']==0 and r['audio_cd_errors']==0 for r in rows)
    assert s[359]['relic_count']==0 and s[359]['menu_screen']==1
    assert any(r['state']==1 for r in rows) and any(r['state']==3 for r in rows)
    collected=s[3600];assert (collected['relic_mask'],collected['relic_count'],collected['relic_value'])==(1,1,1)
    assert collected['state']==0 and collected['z_fp']< -3700*256
    assert collected['sfx_events'][6]==1
    assert collected['sfx_events'][2]>=1 and collected['sfx_events'][5]>=1
    respawn=s[3900];assert respawn['x_fp']==0 and respawn['z_fp']==0 and respawn['relic_mask']==1
    assert respawn['relic_count']==1 and respawn['relic_value']==1 and respawn['sfx_events'][6]==1
    assert s[4300]['menu_screen']==0 and s[4300]['relic_mask']==0
    assert s[4499]['menu_screen']==1 and s[4499]['relic_count']==0 and s[4499]['relic_value']==0
    assert s[4499]['audio_music_ready']==1
    events={e['name']:e for e in j['event_captures']};before=events['approach'];after=events['collected']
    assert before['frame']<after['frame'] and before['relic_mask']==0 and after['relic_mask']==1
    assert after['frame']-after['trigger_frame']>=15
    layout=json.loads((ROOT/'previews/level3/reports/corridor_relic_layout.json').read_text())
    assert layout['component_path_id']==6606 and layout['position']==[-49,-148,-3794] and layout['value']==1
    first=next(r for r in rows if r['relic_mask'])
    dx=int(first['x_fp']/256)+49;dz=int(first['z_fp']/256)+3794;dy=int(first['y_fp']/256)+32+148
    assert dx*dx+dz*dz<=44*44 and -64<=dy<=64
    binary=folder.parent/'zera_level3_preview.bin';assert hashlib.sha256(binary.read_bytes()).hexdigest()==j['bin_sha256']
    images={name:hashlib.sha256((folder/(name+'.png')).read_bytes()).hexdigest() for name in ('approach','collected')}
    files=['src/relics.c','src/relics.h','src/main.c','previews/level3/src/relic_layout.h','previews/level3/src/relic_models.h','tools/scenarios/corridor_relic.json']
    return {'schema_version':1,'component_path_id':6606,'native_collected':1,'native_value':1,'frames':4500,
            'bin_sha256':j['bin_sha256'],'emulator':j['emulator'],'automatic_respawns':0,
            'respawn_preserves':True,'title_clears':True,'pickup_sounds':1,'event_captures':j['event_captures'],
            'image_sha256':images,'source_files_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},
            'milestones':[s[f] for f in (359,3600,3900,4300,4499)],
            'limitations':['This scenario verifies only relic 6606; the second relic has a separate scenario','Provisional pickup volume, static pose and facet lighting; original homing/shader/effects absent','Session only; no memory-card persistence','HLE only; no performance or hardware certification'],
            'next_milestone':'Recover and render the original checkpoint plant in the connected area'}
if __name__=='__main__':print(json.dumps(check(sys.argv[1]),indent=2))
