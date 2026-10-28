"""Validate the recovered launchpad audit without UnityPy or the original build."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(report, progression):
    assert report['schema_version'] == 1
    expected = {'level0': 0, 'level1': 0, 'level2': 2, 'level3': 2,
                'level4': 1, 'level5': 1, 'level6': 3, 'level7': 0}
    assert {s['scene']: len(s['entries']) for s in report['scenes']} == expected
    for name, digest in report['source_file_sha256'].items():
        assert digest == progression['source_file_sha256'][name]
    for scene in report['scenes']:
        ids = set()
        for e in scene['entries']:
            assert e['component_path_id'] not in ids
            ids.add(e['component_path_id'])
            assert e['serialized_payload_offset'] == 32 and e['serialized_payload_size'] == 40
            assert len(e['serialized_object_sha256']) == 64
            assert e['hierarchy'][-1] == e['name']
            assert e['travel_time'] > 0 and e['travel_speed'] > 0
            assert e['glide_lock_range'] == 0.5
            assert -(2**31) <= e['layer_mask'] < 2**31
            for obj in (e, e['kiwi_point']['target']):
                m = obj['source_world_matrix']
                assert len(m) == 4 and all(len(row) == 4 for row in m)
                assert m[3] == [0, 0, 0, 1]
                assert all(math.isfinite(v) for row in m for v in row)
                assert obj['source_world_position'] == [m[k][3] for k in range(3)]
            assert e['kiwi_point']['path_id'] == e['kiwi_point']['target']['transform_path_id']
            assert len(e['landing_point']) == 3 and all(math.isfinite(v) for v in e['landing_point'])
    motion = report['methods']['<LaunchMotion>d__11.MoveNext']['instructions']
    def seq(start, end):
        return [(i['opcode'], i['operand'].get('name') if isinstance(i['operand'], dict) else i['operand'])
                for i in motion if start <= i['offset'] <= end]
    # Guard the evidence behind the documented arc and normalized-time advance.
    assert seq(0x106, 0x138) == [
        ('ldloc.1', None), ('ldfld', 'traversalTime'), ('ldloc.1', None), ('ldfld', 'traversalTime'),
        ('ldc.r4', 1.0), ('sub', None), ('mul', None), ('ldc.r4', 0.5), ('mul', None),
        ('call', 'get_gravity'), ('ldfld', 'y'), ('mul', None), ('ldloc.1', None),
        ('ldfld', 'travelTime'), ('mul', None), ('ldloc.1', None), ('ldfld', 'travelTime'),
        ('mul', None), ('add', None)]
    assert seq(0x14c, 0x165) == [
        ('ldfld', 'traversalTime'), ('call', 'get_fixedDeltaTime'), ('ldloc.1', None),
        ('ldfld', 'travelTime'), ('div', None), ('ldloc.1', None), ('ldfld', 'travelSpeed'),
        ('mul', None), ('add', None), ('stfld', 'traversalTime')]
    preview = json.loads((ROOT / 'previews/level3/reports/world_conversion.json').read_text())
    pads = next(s['entries'] for s in report['scenes'] if s['scene'] == 'level3')
    sx, _, sz = preview['spawn']
    radius = preview['source_radius_units']
    assert all(max(abs(e['source_world_position'][0]-sx), abs(e['source_world_position'][2]-sz)) > radius for e in pads)
    print('Original launchpad audit verified: 9 placements, 9 companion targets, arc and time-step IL; level3 pads outside current patch')


if __name__ == '__main__':
    check(json.loads((ROOT / 'reports/launchpad_recovery.json').read_text()),
          json.loads((ROOT / 'reports/progression_recovery.json').read_text()))
