"""Audit original LaunchPad placements and IL; does not implement PS1 gameplay.
Requires UnityPy 1.25.4, dnfile, dncil, numpy and scipy.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

import dnfile
from dncil.cil.body import CilMethodBody
from dncil.cil.body.reader import CilMethodBodyReaderBytes
import numpy as np
from scipy.spatial.transform import Rotation
import UnityPy
from UnityPy.classes import PPtr


def recover(data):
    data = Path(data)
    assembly = data / 'Managed/Assembly-CSharp.dll'
    pe = dnfile.dnPE(str(assembly))
    typ = next(t for t in pe.net.mdtables.TypeDef.rows
               if str(t.TypeNamespace) == 'NewZera' and str(t.TypeName) == 'LaunchPad')
    public = [(str(f.row.Name), f.row.Signature.value.hex()) for f in typ.FieldList if f.row.Flags.fdPublic]
    expected = [('landingPoint', '06113d'), ('kiwiPoint', '061235'), ('layers', '061180b5'),
                ('travelTime', '060c'), ('travelSpeed', '060c'), ('glideLockRange', '060c')]
    if public != expected:
        raise ValueError('Unexpected LaunchPad public field layout')
    # Resolve TypeDefOrRef encoded signatures independently of field names.
    resolved = {}
    for field in typ.FieldList:
        sig = field.row.Signature.value
        if sig[1] not in (0x11, 0x12):
            continue
        coded = sig[2] if sig[2] < 0x80 else ((sig[2] & 0x3f) << 8) | sig[3]
        table = (pe.net.mdtables.TypeDef, pe.net.mdtables.TypeRef, pe.net.mdtables.TypeSpec)[coded & 3]
        row = table.rows[(coded >> 2) - 1]
        resolved[str(field.row.Name)] = str(row.TypeNamespace) + '.' + str(row.TypeName)
    assert resolved['landingPoint'] == 'UnityEngine.Vector3'
    assert resolved['kiwiPoint'] == 'UnityEngine.Transform'
    assert resolved['layers'] == 'UnityEngine.LayerMask'

    def operand(value):
        if isinstance(value, float) and not math.isfinite(value):
            return str(value)
        if value is None or isinstance(value, (str, int, float)):
            return value
        if hasattr(value, 'table'):
            name = {1: 'TypeRef', 2: 'TypeDef', 4: 'Field', 6: 'MethodDef', 10: 'MemberRef'}.get(value.table)
            if name:
                row = getattr(pe.net.mdtables, name).rows[value.rid - 1]
                label = str(getattr(row, 'Name', getattr(row, 'TypeName', '?')))
                return {'token': f'0x{value.value:08x}', 'name': label}
        return str(value)

    methods = {}
    for t in pe.net.mdtables.TypeDef.rows:
        if t is not typ and str(t.TypeName) != '<LaunchMotion>d__11':
            continue
        for method in t.MethodList:
            m = method.row
            if t is not typ and str(m.Name) != 'MoveNext':
                continue
            body = CilMethodBody(CilMethodBodyReaderBytes(pe.get_data(m.Rva)))
            methods[str(t.TypeName) + '.' + str(m.Name)] = {
                'rva': m.Rva,
                'instructions': [{'offset': i.offset, 'opcode': i.opcode.name, 'operand': operand(i.operand)}
                                 for i in body.instructions]}

    env = UnityPy.load(str(data))
    dependencies = {'Managed/Assembly-CSharp.dll'}
    cache = {}

    def transform(go):
        return next(c.component.read() for c in go.m_Component if c.component.deref().type.name == 'Transform')

    def matrix(t):
        key = (t.object_reader.assets_file.name, t.object_reader.path_id)
        if key not in cache:
            p, q, s = t.m_LocalPosition, t.m_LocalRotation, t.m_LocalScale
            m = np.eye(4)
            m[:3, :3] = Rotation.from_quat([q.x, q.y, q.z, q.w]).as_matrix() @ np.diag([s.x, s.y, s.z])
            m[:3, 3] = [p.x, p.y, p.z]
            if t.m_Father.path_id:
                m = matrix(t.m_Father.read()) @ m
            cache[key] = m
        return cache[key]

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

    scenes = []
    for f in sorted(env.files.values(), key=lambda f: getattr(f, 'name', '')):
        if not getattr(f, 'name', '').startswith('level') or not hasattr(f, 'objects'):
            continue
        if f.unity_version != '2019.4.18f1':
            raise ValueError('Unverified Unity layout')
        dependencies.add(f.name)
        entries = []
        for o in f.objects.values():
            if o.type.name != 'MonoBehaviour':
                continue
            d = o.read(check_read=False)
            if not d.m_Script.path_id:
                continue
            script = d.m_Script.read()
            if (script.m_Namespace, script.m_ClassName) != ('NewZera', 'LaunchPad'):
                continue
            dependencies.add(d.m_Script.deref().assets_file.name)
            raw = o.get_raw_data()
            size = struct.unpack_from('<i', raw, 28)[0]
            if size < 0 or 32 + size > len(raw):
                raise ValueError('Invalid component header')
            offset = (32 + size + 3) & ~3
            if len(raw) != offset + 40:
                raise ValueError('Unexpected LaunchPad serialized payload size')
            landing = list(struct.unpack_from('<3f', raw, offset))
            file_id, path_id = struct.unpack_from('<iq', raw, offset + 12)
            target = PPtr(m_FileID=file_id, m_PathID=path_id, assetsfile=f).read()
            if target.object_reader.type.name != 'Transform':
                raise ValueError('Invalid kiwiPoint target')
            dependencies.add(target.object_reader.assets_file.name)
            mask, time, speed, lock = struct.unpack_from('<ifff', raw, offset + 24)
            entry = describe(d.m_GameObject.read())
            entry.update({'component_path_id': o.path_id, 'component_enabled': bool(d.m_Enabled),
                          'serialized_payload_offset': offset, 'serialized_payload_size': 40,
                          'serialized_object_sha256': hashlib.sha256(raw).hexdigest(),
                          'landing_point': landing,
                          'kiwi_point': {'file_id': file_id, 'path_id': path_id, 'target': describe(target.m_GameObject.read())},
                          'layer_mask': mask, 'travel_time': time, 'travel_speed': speed, 'glide_lock_range': lock})
            entries.append(entry)
        scenes.append({'scene': f.name, 'entries': sorted(entries, key=lambda e: e['component_path_id'])})
    hashes = {}
    for name in sorted(dependencies):
        matches = [p for p in data.rglob(name) if p.is_file()]
        if len(matches) != 1:
            raise ValueError('Ambiguous dependency: ' + name)
        p = matches[0]
        hashes[p.relative_to(data).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return {'schema_version': 1, 'source_file_sha256': hashes,
            'public_field_signatures': public, 'resolved_field_types': resolved,
            'coordinate_system': 'Original Unity world coordinates, not PS1 coordinates',
            'limitations': ['Serialized placements and compiled method audit; no PS1 launch gameplay enabled',
                           'Runtime gravity, companion interaction, state transitions and collision require integration validation',
                           'landingPoint is a world-space Vector3, not a transform reference',
                           'travelTime is an arc parameter; normalized time advances by fixedDeltaTime / travelTime * travelSpeed'],
            'scenes': scenes, 'methods': methods}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'reports/launchpad_recovery.json')
    args = parser.parse_args()
    args.output.write_text(json.dumps(recover(args.data), indent=2, allow_nan=False) + '\n')
