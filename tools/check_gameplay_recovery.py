"""Check recovered gameplay evidence without UnityPy, dnfile or original assets."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def check(report, progression):
    assert report['schema_version'] == 1
    assert report['unity_version'] == '2019.4.18f1'
    assert [s['name'] for s in report['scenes']] == [
        'SplashLoad', 'Main Menu', 'Cosmic Core', 'Dreary Valley',
        'Crystal Rift', 'Mystic Towers', 'Frigid Bluffs', 'Secret']
    for i, scene in enumerate(report['scenes']):
        assert scene['scene'] == 'level' + str(i) and scene['build_index'] == i
        assert scene['object_count'] > 0
        assert all(v > 0 for v in scene['script_component_counts'].values())
        recovered = progression['scenes'][i]
        assert recovered['scene'] == scene['scene']
        for kind in ('Relic', 'Essence', 'Checkpoint'):
            assert scene['script_component_counts'].get('NewZera.' + kind, 0) == recovered['serialized_component_counts'].get(kind, 0)
    for name, value in report['source_file_sha256'].items():
        assert re.fullmatch('[0-9a-f]{64}', value)
        if name in progression['source_file_sha256']:
            assert value == progression['source_file_sha256'][name]
    methods = {(m['owner'], m['name']): m for m in report['methods']}
    assert len(methods) == len(report['methods']) == 20
    for method in methods.values():
        assert re.fullmatch('[0-9a-f]{64}', method['body_sha256'])
        instructions = method['instructions']
        offsets = {i['offset'] for i in instructions}
        assert len(offsets) == len(instructions)
        assert [i['offset'] for i in instructions] == sorted(offsets)
        for i in instructions:
            op = i['opcode']
            if op == 'switch':
                assert set(i['operand']) <= offsets
            elif op.startswith(('br', 'beq', 'bge', 'bgt', 'ble', 'blt', 'bne', 'leave')):
                assert i['operand'] in offsets

    def symbols(owner, method):
        return [i['operand']['symbol'] for i in methods[(owner, method)]['instructions']
                if isinstance(i['operand'], dict) and 'symbol' in i['operand']]

    completion = symbols('NewZera.GameControl/<checkArrays>d__61', 'MoveNext')
    for name in ('relics', 'essences', 'enemytype1', 'enemytype2', 'snappies', 'containers', 'everythingCollected'):
        assert 'NewZera.GameControl::' + name in completion
    assert 'NewZera.GameControl::Save' in symbols('NewZera.getLevelComplete', 'Update')
    checkpoint = symbols('NewZera.Checkpoint/<checkpoint>d__10', 'MoveNext')
    assert 'NewZera.ZC::currentSpawnPoint' in checkpoint
    assert 'NewZera.ZC::currentCamSpawnPoint' in checkpoint
    assert 'System.Runtime.Serialization.Formatters.Binary.BinaryFormatter::Serialize' in symbols('NewZera.GameControl', 'Save')
    assert [f['name'] for f in report['save_field_signatures']['CollectableSave']] == [
        'relics', 'essences', 'enemytype1', 'enemytype2', 'snappy', 'containers', 'completed', 'exitedGateway']
    assert 'WholeGameRelicCount' in [f['name'] for f in report['save_field_signatures']['NewZera.GameControl/PlayerData']]
    print('Gameplay evidence verified: 8 scenes, 20 method bodies, save schemas, completion arrays and checkpoint targets')


if __name__ == '__main__':
    check(json.loads((ROOT / 'reports/gameplay_recovery.json').read_text()),
          json.loads((ROOT / 'reports/progression_recovery.json').read_text()))
