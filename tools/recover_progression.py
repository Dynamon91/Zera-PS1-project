"""Recover serialized progression placements without executing original game code.

This is a source-data audit, not a conversion to PS1 gameplay or Unity physics.
Requires UnityPy 1.25.4, dnfile, numpy and scipy.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

import dnfile
import numpy as np
from scipy.spatial.transform import Rotation
import UnityPy


def recover(data):
    data = Path(data)
    assembly = data / 'Managed/Assembly-CSharp.dll'
    pe = dnfile.dnPE(str(assembly))
    signatures = {}
    for t in pe.net.mdtables.TypeDef.rows:
        if str(t.TypeNamespace) == 'NewZera' and str(t.TypeName) in ('Relic', 'Essence', 'Checkpoint'):
            fields = [(str(f.row.Name), f.row.Signature.value.hex()) for f in t.FieldList]
            signatures[str(t.TypeName)] = fields
    for name in ('Relic', 'Essence'):
        if signatures[name][0] != ('value', '0608'):
            raise ValueError(f'Unexpected {name} field order/type')
    if [f[0] for f in signatures['Checkpoint'][:2]] != ['newSpawnPoint', 'newCamPoint']:
        raise ValueError('Unexpected checkpoint reference order')
    env = UnityPy.load(str(data))
    dependencies = {'Managed/Assembly-CSharp.dll'}
    transforms = {}

    def matrix(t):
        key = (t.object_reader.assets_file.name, t.object_reader.path_id)
        if key not in transforms:
            p, q, s = t.m_LocalPosition, t.m_LocalRotation, t.m_LocalScale
            m = np.eye(4)
            m[:3, :3] = Rotation.from_quat([q.x, q.y, q.z, q.w]).as_matrix() @ np.diag([s.x, s.y, s.z])
            m[:3, 3] = [p.x, p.y, p.z]
            if t.m_Father.path_id:
                m = matrix(t.m_Father.read()) @ m
            transforms[key] = m
        return transforms[key]

    def transform(go):
        return next(c.component.read() for c in go.m_Component if c.component.deref().type.name == 'Transform')

    def describe(go):
        t = transform(go)
        chain, active = [], True
        current = t
        while True:
            obj = current.m_GameObject.read()
            chain.append(obj.m_Name)
            active = active and bool(obj.m_IsActive)
            if not current.m_Father.path_id:
                break
            current = current.m_Father.read()
        return {'name': go.m_Name, 'game_object_path_id': go.object_reader.path_id,
                'transform_path_id': t.object_reader.path_id, 'hierarchy': list(reversed(chain)),
                'active_in_serialized_hierarchy': active, 'source_world_matrix': matrix(t).tolist(),
                'source_world_position': matrix(t)[:3, 3].tolist()}

    def reference(f, raw, offset):
        file_id, path_id = struct.unpack_from('<iq', raw, offset)
        result = {'file_id': file_id, 'path_id': path_id}
        if not path_id:
            return result
        from UnityPy.classes import PPtr
        ptr = PPtr(m_FileID=file_id, m_PathID=path_id, assetsfile=f)
        obj = ptr.read()
        dependencies.add(obj.object_reader.assets_file.name)
        result['type'] = obj.object_reader.type.name
        if result['type'] == 'Transform':
            result['target'] = describe(obj.m_GameObject.read())
        elif result['type'] == 'GameObject':
            result['target'] = describe(obj)
        else:
            raise ValueError('Checkpoint reference is not a scene transform/object')
        return result

    scenes = []
    for f in sorted(env.files.values(), key=lambda f: getattr(f, 'name', '')):
        if not getattr(f, 'name', '').startswith('level') or not hasattr(f, 'objects'):
            continue
        if f.unity_version != '2019.4.18f1':
            raise ValueError('Serialized layout is only verified for Unity 2019.4.18f1')
        dependencies.add(f.name)
        entries, spawns = [], []
        for o in f.objects.values():
            if o.type.name == 'GameObject':
                go = o.read()
                if go.m_Name.startswith('_StartSpawnPoint'):
                    spawns.append(describe(go))
            if o.type.name != 'MonoBehaviour':
                continue
            d = o.read(check_read=False)
            if not d.m_Script.path_id:
                continue
            script = d.m_Script.read()
            if script.m_Namespace != 'NewZera' or script.m_ClassName not in signatures:
                continue
            dependencies.add(d.m_Script.deref().assets_file.name)
            raw = o.get_raw_data()
            # Standard 2019 MonoBehaviour header: GO PPtr, enabled/alignment,
            # script PPtr and aligned UTF-8 name. Custom data follows the name.
            name_size = struct.unpack_from('<i', raw, 28)[0]
            if name_size < 0 or 32 + name_size > len(raw):
                raise ValueError('Invalid MonoBehaviour name length')
            offset = (32 + name_size + 3) & ~3
            entry = describe(d.m_GameObject.read())
            entry.update({'kind': script.m_ClassName, 'component_path_id': o.path_id,
                          'component_enabled': bool(d.m_Enabled), 'serialized_payload_offset': offset,
                          'serialized_object_sha256': hashlib.sha256(raw).hexdigest(),
                          'script': {'file': d.m_Script.deref().assets_file.name,
                                     'path_id': d.m_Script.path_id,
                                     'class': script.m_Namespace + '.' + script.m_ClassName}})
            if script.m_ClassName in ('Relic', 'Essence'):
                entry['value'] = struct.unpack_from('<i', raw, offset)[0]
                if not 0 < entry['value'] <= 1024:
                    raise ValueError('Unexpected collectible value')
            else:
                entry['new_spawn_point'] = reference(f, raw, offset)
                entry['new_camera_point'] = reference(f, raw, offset + 12)
            entries.append(entry)
        count = Counter(e['kind'] for e in entries)
        active = Counter(e['kind'] for e in entries if e['component_enabled'] and e['active_in_serialized_hierarchy'])
        scenes.append({'scene': f.name, 'unity_version': f.unity_version,
                       'start_spawns': spawns, 'serialized_component_counts': dict(count),
                       'initially_enabled_component_counts': dict(active),
                       'serialized_relic_value_sum': sum(e.get('value', 0) for e in entries if e['kind'] == 'Relic'),
                       'serialized_essence_value_sum': sum(e.get('value', 0) for e in entries if e['kind'] == 'Essence'),
                       'entries': entries})
    hashes = {}
    for name in sorted(dependencies):
        matches = [p for p in data.rglob(name) if p.is_file()]
        if len(matches) != 1:
            raise ValueError(f'Ambiguous source dependency: {name}')
        p = matches[0]
        hashes[p.relative_to(data).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return {'schema_version': 1, 'source': 'Zera Myths Awaken Win 64 5.2 pre-release 5 (1).zip',
            'source_file_sha256': hashes, 'field_signatures': signatures,
            'coordinate_system': 'Original Unity world coordinates; no PS1 grounding/scale adaptation applied',
            'limitations': ['Serialized scene components only; runtime-created objects and container contents may differ',
                           'Counts and value sums are not asserted level-completion totals',
                           'Serialized hierarchy state is not proof of runtime availability',
                           'Start spawns are named scene candidates; runtime spawn selection is not decoded',
                           'No original collection, saving, trigger volumes or checkpoint behavior is implemented by this report'],
            'scenes': scenes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'reports/progression_recovery.json')
    args = parser.parse_args()
    result = recover(args.data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps([{k: s[k] for k in ('scene', 'serialized_component_counts', 'initially_enabled_component_counts', 'serialized_relic_value_sum')} for s in result['scenes']], indent=2))


if __name__ == '__main__':
    main()
