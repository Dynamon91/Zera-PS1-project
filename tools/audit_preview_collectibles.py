"""Map original collectibles into converted previews; does not enable collection."""
import hashlib
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def floor_layers(triangles,x,z):
    values=set()
    for a,b,c in triangles:
        den=(b[2]-c[2])*(a[0]-c[0])+(c[0]-b[0])*(a[2]-c[2])
        if not den:continue
        wa=(b[2]-c[2])*(x-c[0])+(c[0]-b[0])*(z-c[2])
        wb=(c[2]-a[2])*(x-c[0])+(a[0]-c[0])*(z-c[2]);wc=den-wa-wb
        if den<0:den=-den;wa=-wa;wb=-wb;wc=-wc
        if min(wa,wb,wc)<0:continue
        # Integer truncation agrees with the C surface-height API.
        numerator=wa*a[1]+wb*b[1]+wc*c[1]
        values.add((abs(numerator)//den)*(1 if numerator>=0 else -1))
    return sorted(values)

def build():
    source=ROOT/'reports/progression_recovery.json'
    recovery=json.loads(source.read_text())
    previews=[]
    for name in ['level3','launchpad']:
        path=ROOT/f'previews/{name}/assets/world_chunk_source.json'
        world=json.loads(path.read_text());r=world['report']
        scene=next(s for s in recovery['scenes'] if s['scene']==r['scene'])
        sx,sy,sz=r['spawn'];radius=r['source_radius_units'];scale=r['world_scale'];ground=r['ground_height']
        entries=[]
        for e in scene['entries']:
            if e['kind'] not in ('Relic','Essence'):continue
            x,y,z=e['source_world_position']
            if abs(x-sx)>radius or abs(z-sz)>radius:continue
            p=[round(-(x-sx)*scale),round((y-ground)*scale),round((z-sz)*scale)]
            layers=floor_layers(world['floor_triangles'],p[0],p[2])
            below=[h for h in layers if h<=p[1]]
            entries.append({'kind':e['kind'],'component_path_id':e['component_path_id'],'name':e['name'],
                            'value':e['value'],'source_world_position':[x,y,z],'ps1_position':p,
                            'source_component_enabled':e['component_enabled'],
                            'source_hierarchy_active':e['active_in_serialized_hierarchy'],
                            'floor_layers_at_quantized_xz':layers,
                            'highest_floor_below_item':max(below) if below else None,
                            'item_height_above_floor':p[1]-max(below) if below else None})
        previews.append({'preview':name,'scene':r['scene'],'world_source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                         'entries':sorted(entries,key=lambda e:e['component_path_id'])})
    return {'schema_version':1,'progression_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'position_conversion':'XZ mirrored/scaled relative to preview origin; Y relative to recovered ground, rounded to integer world units',
            'limitations':['Spatial inclusion and point support are not a traversable-route or pickup proof',
                           'Collection, inventory and saving are not enabled by this audit',
                           'Original source hierarchy flags do not prove runtime availability'],
            'previews':previews}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
    result=build();path=ROOT/'reports/preview_collectibles.json'
    launch=next(r for r in result['previews'] if r['preview']=='launchpad')
    assert [(e['component_path_id'],e['value']) for e in launch['entries']]==[(6594,8),(6596,8),(7178,4)]
    assert [e['item_height_above_floor'] for e in launch['entries']]==[32,32,32]
    assert not next(r for r in result['previews'] if r['preview']=='level3')['entries']
    header=(ROOT/'src/relics.h').read_text()
    positions=re.search(r'relic_positions\[RELIC_COUNT\]\[3\]=\{(.*?)\};',header,re.S).group(1)
    runtime=[list(map(int,row.split(','))) for row in re.findall(r'\{([^{}]+)\}',positions)]
    values=list(map(int,re.search(r'relic_values\[RELIC_COUNT\]=\{([^}]+)\}',header).group(1).split(',')))
    assert runtime==[e['ps1_position'] for e in launch['entries']]
    assert values==[e['value'] for e in launch['entries']]
    if args.check:
        assert json.loads(path.read_text())==result,'Preview collectible audit drifted; regenerate and review'
    else:path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'launchpad_collectibles':len(launch['entries']),'values':[e['value'] for e in launch['entries']], 'check':args.check}))
