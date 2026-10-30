"""Generate checkpoint constants from recovered original transforms and terrain."""
import hashlib
import json
import math
from pathlib import Path
from audit_preview_collectibles import floor_layers

ROOT=Path(__file__).resolve().parents[1]


def prepare(area_name='checkpoint'):
    source=ROOT/'reports/progression_recovery.json'
    original=json.loads(source.read_text())
    area=ROOT/'previews'/area_name
    world_path=area/'assets/world_chunk_source.json'
    world=json.loads(world_path.read_text());report=world['report']
    assert report['scene']=='level3'
    for name,value in report['source_files_sha256'].items():
        if name in original['source_file_sha256']:
            assert original['source_file_sha256'][name]==value
    config=next(e for s in original['scenes'] if s['scene']=='level3' for e in s['entries']
                if e['kind']=='Checkpoint' and e['component_path_id']==report.get('checkpoint_component_path_id',6752))
    assert config['component_enabled'] and config['active_in_serialized_hierarchy']
    origin=report['spawn'];scale=report['world_scale'];ground=report['ground_height']
    def position(p):return [round(-(p[0]-origin[0])*scale),round((p[1]-ground)*scale),round((p[2]-origin[2])*scale)]
    spawn=position(config['new_spawn_point']['target']['source_world_position'])
    trigger=position(config['source_world_position'])
    camera=position(config['new_camera_point']['target']['source_world_position'])
    source_spawn=config['new_spawn_point']['target']['source_world_position']
    source_camera=config['new_camera_point']['target']['source_world_position']
    # Derive direction before integer quantization, independently of patch origin.
    yaw=round(math.atan2(-(source_camera[0]-source_spawn[0]),-(source_camera[2]-source_spawn[2]))*4096/(2*math.pi))&4095
    entry_x=-400 if area_name=='checkpoint' else 0
    layers=floor_layers(world['floor_triangles'],entry_x,0)
    entry=[entry_x,max(h for h in layers if h<=48),0]
    if area_name=='checkpoint':assert abs(entry[1]-spawn[1])<=80
    result={'component_path_id':config['component_path_id'],'scene':'level3','spawn':spawn,'trigger':trigger,
            'original_camera_position':camera,'camera_yaw':yaw,'test_entry':entry,
            'source_recovery_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'world_source_sha256':hashlib.sha256(world_path.read_bytes()).hexdigest(),
            'adaptations':[('Test entry is 400 PS1 units left of the original checkpoint, on recovered floor; not an original level spawn' if area_name=='checkpoint' else 'Retains original converted level start; continuous route checked separately'),
                           'Grounded proximity radius 160 and vertical tolerance 80 replace the unported Kiwi interaction',
                           'Original camera horizontal direction adapted to existing orbit camera; distance/pitch remain provisional',
                           'Session-only checkpoint, no memory-card save']}
    fields=[config['component_path_id'],*spawn,yaw,*trigger]
    header='/* Original checkpoint spawn/trigger; adapted orbit yaw and test entry. */\n'
    header+='static const CheckpointConfig checkpoint_config={'+','.join(map(str,fields))+'};\n'
    for axis,value in zip('XYZ',entry):header+=f'#define CHECKPOINT_ENTRY_{axis} ({value})\n'
    return result,header


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');parser.add_argument('--area',choices=['checkpoint','level3'],default='checkpoint');args=parser.parse_args()
    result,header=prepare(args.area);area=ROOT/'previews'/args.area
    if args.check:
        assert (area/'src/checkpoint_config.h').read_text()==header
        assert json.loads((area/'reports/checkpoint_config.json').read_text())==result
    else:
        (area/'src/checkpoint_config.h').write_text(header)
        (area/'reports/checkpoint_config.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
