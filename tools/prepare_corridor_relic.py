"""Generate active lower-corridor relics from verified source placements/models."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def prepare():
    audit=ROOT/'reports/preview_collectibles.json';r=json.loads(audit.read_text())
    area=ROOT/'previews/level3';world=area/'assets/world_chunk_source.json'
    preview=next(p for p in r['previews'] if p['preview']=='level3')
    assert preview['world_source_sha256']==hashlib.sha256(world.read_bytes()).hexdigest()
    items=[next(e for e in preview['entries'] if e['component_path_id']==id) for id in (6606,6898)]
    assert [e['value'] for e in items]==[1,16]
    assert [e['item_height_above_floor'] for e in items]==[56,103]
    assert all(e['kind']=='Relic' and e['source_component_enabled'] and e['source_hierarchy_active'] for e in items)
    item=items[0]
    model_path=area/'reports/relic_models.json';model=json.loads(model_path.read_text())
    assert [e['component_path_id'] for e in model['instances']]==[6606,6898]
    assert all(m['source_origin']==e['source_world_position'] for m,e in zip(model['instances'],items))
    source=json.loads((ROOT/'reports/progression_recovery.json').read_text())
    assert model['source_file_sha256']['level3']==source['source_file_sha256']['level3']
    position=item['ps1_position']
    header='/* Original level3 relics 6606 and 6898; pickup volume remains provisional. */\n#define RELIC_COUNT 2\n#define RELIC_TOTAL_VALUE 17\n'
    header+='static const int relic_positions[RELIC_COUNT][3]={'+','.join('{'+','.join(map(str,e['ps1_position']))+'}' for e in items)+'};\n'
    header+='static const int relic_values[RELIC_COUNT]={1,16};\n'
    report={'component_path_id':6606,'value':1,'position':position,'source_position':item['source_world_position'],
            'floor_y':item['highest_floor_below_item'],'source_audit_sha256':hashlib.sha256(audit.read_bytes()).hexdigest(),
            'model_report_sha256':hashlib.sha256(model_path.read_bytes()).hexdigest(),
            'items':[{'component_path_id':e['component_path_id'],'position':e['ps1_position'],'value':e['value'],'height_above_floor':e['item_height_above_floor']} for e in items],
            'limitations':['Only these two relics are enabled in the corridor','Provisional pickup radius/height; original homing and effects absent','Session collection only; no memory-card persistence']}
    return header,report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    header,report=prepare();area=ROOT/'previews/level3'
    if a.check:
        assert (area/'src/relic_layout.h').read_text()==header
        assert json.loads((area/'reports/corridor_relic_layout.json').read_text())==report
    else:
        (area/'src/relic_layout.h').write_text(header)
        (area/'reports/corridor_relic_layout.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
