"""Verify the committed source recovery checkpoint, without requiring UnityPy."""
import json
import math
from pathlib import Path
import re


def check(report):
    assert report['schema_version'] == 1
    scenes = {s['scene']: s for s in report['scenes']}
    assert len(scenes) == len(report['scenes']) == 8
    expected = {'level2': (1, 0, 0), 'level3': (38, 5, 3),
                'level4': (61, 5, 5), 'level5': (34, 5, 3), 'level6': (59, 5, 2)}
    total = 0
    for name, scene in scenes.items():
        counts = tuple(sum(e['kind'] == k for e in scene['entries']) for k in ('Relic', 'Essence', 'Checkpoint'))
        assert counts == expected.get(name, (0, 0, 0))
        assert sum(counts) == len(scene['entries'])
        if name in expected:
            assert len(scene['start_spawns']) == 1
        ids = set()
        for entry in scene['entries']:
            assert entry['component_path_id'] not in ids
            ids.add(entry['component_path_id'])
            assert len(entry['serialized_object_sha256']) == 64
            assert entry['script']['class'] == 'NewZera.' + entry['kind']
            assert entry['hierarchy'][-1] == entry['name']
            matrix = entry['source_world_matrix']
            assert len(matrix) == 4 and all(len(row) == 4 for row in matrix)
            assert matrix[3] == [0, 0, 0, 1]
            assert all(math.isfinite(v) for row in matrix for v in row)
            assert entry['source_world_position'] == [matrix[k][3] for k in range(3)]
            if entry['kind'] in ('Relic', 'Essence'):
                assert entry['value'] in (1, 2, 4, 8, 16, 32)
                named = re.match(r'_Relic_(\d+)', entry['name'])
                if named:
                    assert entry['value'] == int(named[1])
            else:
                for field in ('new_spawn_point', 'new_camera_point'):
                    ref = entry[field]
                    assert ref['path_id'] != 0 and ref['type'] in ('Transform', 'GameObject')
                    target = ref['target']
                    key = 'transform_path_id' if ref['type'] == 'Transform' else 'game_object_path_id'
                    assert target[key] == ref['path_id']
        for kind in ('Relic', 'Essence'):
            assert scene['serialized_' + kind.lower() + '_value_sum'] == sum(e['value'] for e in scene['entries'] if e['kind'] == kind)
        assert len(report['source_file_sha256'][name]) == 64
        total += len(scene['entries'])
    assert total == 226
    print('Original progression recovery verified: 193 relics, 20 essences, 13 checkpoints; 26 checkpoint target references')


if __name__ == '__main__':
    check(json.loads((Path(__file__).resolve().parents[1] / 'reports/progression_recovery.json').read_text()))
