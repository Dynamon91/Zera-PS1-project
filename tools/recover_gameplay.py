"""Audit original scenes and progression IL without executing Unity/game code.

This report is evidence for porting, not a claim that these features run on PS1.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import dnfile
from dncil.cil.body.reader import read_method_body_from_bytes
from dncil.clr.token import StringToken, Token
import UnityPy

ROOT = Path(__file__).resolve().parents[1]
METHODS = {
    'NewZera.GameControl': {'Save', 'Load', 'SaveData', 'LoadData', 'DisplayPercentage', 'Check', 'checkArrays'},
    'NewZera.Checkpoint': {'Update', 'OnTriggerEnter', 'checkpoint'},
    'NewZera.GaiaQuickSave': {'OnTriggerEnter', 'checkpoint'},
    'NewZera.Relic': {'OnCollected', 'ResetCollection'},
    'NewZera.Essence': {'OnCollected', 'ResetCollection'},
    'NewZera.getLevelComplete': {'Update'},
}


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def assembly_evidence(assembly):
    pe = dnfile.dnPE(str(assembly))
    names, owners = {}, {}
    nested = {id(r.NestedClass.row): r.EnclosingClass.row
              for r in pe.net.mdtables.NestedClass.rows}

    def typename(row):
        if id(row) not in names:
            parent = nested.get(id(row))
            prefix = typename(parent) + '/' if parent else (str(row.TypeNamespace) + '.' if str(row.TypeNamespace) else '')
            names[id(row)] = prefix + str(row.TypeName)
        return names[id(row)]

    for row in pe.net.mdtables.TypeDef.rows:
        typename(row)
        for member in list(row.FieldList) + list(row.MethodList):
            owners[id(member.row)] = typename(row)

    def symbol(row):
        if hasattr(row, 'Method'):  # MethodSpec: preserve generic instantiation signature.
            return symbol(row.Method.row) + '<' + row.Instantiation.value.hex() + '>'
        if hasattr(row, 'TypeName'):
            return typename(row)
        if hasattr(row, 'Class'):
            return symbol(row.Class.row) + '::' + str(row.Name)
        if hasattr(row, 'Name'):
            return owners.get(id(row), '') + '::' + str(row.Name)
        if hasattr(row, 'Signature'):
            return 'signature:' + row.Signature.value.hex()
        raise ValueError('Unsupported metadata symbol: ' + type(row).__name__)

    def operand(value):
        if isinstance(value, StringToken):
            return {'string': pe.net.user_strings.get(value.rid).value}
        if isinstance(value, Token):
            table = pe.net.mdtables.tables[value.table]
            return {'token': value.value, 'symbol': symbol(table.rows[value.rid - 1])}
        if value is None or isinstance(value, (int, float, str, list)):
            return value
        return str(value)  # Local/argument indices as rendered by dncil.

    methods, schemas = [], {}
    for row in pe.net.mdtables.TypeDef.rows:
        owner = typename(row)
        if owner in ('NewZera.GameControl/PlayerData', 'CollectableSave'):
            schemas[owner] = [{'name': str(f.row.Name), 'signature': f.row.Signature.value.hex()}
                              for f in row.FieldList]
        selected = METHODS.get(owner, set())
        if owner.startswith(('NewZera.Checkpoint/<checkpoint>', 'NewZera.GaiaQuickSave/<checkpoint>',
                             'NewZera.GameControl/<checkArrays>')):
            selected = {'MoveNext'}
        for index in row.MethodList:
            method = index.row
            if str(method.Name) not in selected:
                continue
            if not method.Rva:
                raise ValueError('Selected method has no body: ' + owner)
            body = read_method_body_from_bytes(pe.get_data(method.Rva))
            methods.append({'owner': owner, 'name': str(method.Name),
                            'method_token': 0x06000000 | index.row_index,
                            'body_sha256': hashlib.sha256(body.raw_bytes).hexdigest(),
                            'instructions': [{'offset': i.offset,
                                              'opcode': i.opcode.name, 'operand': operand(i.operand)}
                                             for i in body.instructions]})
    found = {(m['owner'], m['name']) for m in methods}
    missing = {(o, m) for o, ms in METHODS.items() for m in ms} - found
    if missing:
        raise ValueError('Missing required original methods: ' + repr(sorted(missing)))
    return methods, schemas


def recover(data):
    data = Path(data)
    assembly = data / 'Managed/Assembly-CSharp.dll'
    methods, schemas = assembly_evidence(assembly)
    env = UnityPy.load(str(data))
    build = [o for o in env.objects if o.type.name == 'BuildSettings']
    if len(build) != 1:
        raise ValueError('Expected one BuildSettings object')
    settings = build[0].read_typetree()
    if settings['m_Version'] != '2019.4.18f1':
        raise ValueError('Unexpected Unity version')
    files = {f.name: f for f in env.files.values() if hasattr(f, 'objects')}
    scenes = []
    for number, source in enumerate(settings['scenes']):
        name = 'level' + str(number)
        scene = files[name]
        counts = Counter()
        for obj in scene.objects.values():
            if obj.type.name != 'MonoBehaviour':
                continue
            component = obj.read(check_read=False)
            if component.m_Script.path_id:
                script = component.m_Script.read()
                key = '.'.join(filter(None, (script.m_Namespace, script.m_ClassName)))
                counts[key] += 1
        scenes.append({'scene': name, 'build_index': number, 'source_scene': source,
                       'name': Path(source).stem, 'object_count': len(scene.objects),
                       'script_component_counts': dict(sorted(counts.items()))})
    sources = {'Managed/Assembly-CSharp.dll', build[0].assets_file.name}
    sources.update(s['scene'] for s in scenes)
    return {'schema_version': 1, 'unity_version': settings['m_Version'],
            'source_file_sha256': {n: digest(data / n) for n in sorted(sources)},
            'asset_counts': dict(sorted(Counter(o.type.name for o in env.objects).items())),
            'scenes': scenes, 'save_field_signatures': schemas, 'methods': methods,
            'limitations': ['Static serialized scene counts, not runtime active objects or final content totals',
                            'IL is decoded evidence, not executed or automatically translated gameplay',
                            'Instruction branch operands retain dncil body-relative offsets including headers',
                            'No original binary save is deserialized or game code executed',
                            'This recovery does not enable levels, checkpoint behavior or saves on PS1']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'reports/gameplay_recovery.json')
    parser.add_argument('--check', action='store_true', help='Regenerate in memory and reject report drift')
    args = parser.parse_args()
    report = recover(args.data)
    if args.check:
        if json.loads(args.output.read_text()) != report:
            raise ValueError('Gameplay recovery differs from the supplied original data')
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'scenes': [s['name'] for s in report['scenes']],
                      'methods': len(report['methods']), 'check': args.check}))


if __name__ == '__main__':
    main()
