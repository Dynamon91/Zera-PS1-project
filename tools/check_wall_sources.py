"""Check generated wall data and optionally its original static MeshColliders."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def check(data=None):
    original=json.loads((ROOT/'reports/progression_recovery.json').read_text())
    if data is not None:
        import UnityPy
        import numpy as np
        from scipy.spatial.transform import Rotation
        data=Path(data)
        env=UnityPy.load(str(data))
        scene=next(f for f in env.files.values() if getattr(f,'name','')=='level3')
        matrices={}
        def matrix(t):
            key=(t.object_reader.assets_file.name,t.object_reader.path_id)
            if key not in matrices:
                p,q,s=t.m_LocalPosition,t.m_LocalRotation,t.m_LocalScale
                m=np.eye(4)
                m[:3,:3]=Rotation.from_quat([q.x,q.y,q.z,q.w]).as_matrix()@np.diag([s.x,s.y,s.z])
                m[:3,3]=[p.x,p.y,p.z]
                if t.m_Father.path_id:m=matrix(t.m_Father.read())@m
                matrices[key]=m
            return matrices[key]
    result={'schema_version':1,'originals_verified':data is not None,'areas':[]}
    for name in ('level3','launchpad','checkpoint'):
        area=ROOT/f'previews/{name}'
        world_path=area/'assets/world_chunk_source.json'
        world=json.loads(world_path.read_text());report=world['report']
        assert json.loads((area/'reports/world_conversion.json').read_text())==report
        source=report['wall_collision_source']
        assert source['type']=='original enabled solid static MeshColliders'
        assert report['source_files_sha256']['level3']==original['source_file_sha256']['level3']
        instances=source['instances'];ids=[e['component_path_id'] for e in instances]
        assert len(ids)==len(set(ids)) and instances
        assert any(e['object'].startswith('Walls') for e in instances)
        assert not any(e['object'].startswith('Lava') for e in instances)
        walls=world['walls'];assert walls and len(walls)==report['wall_proxies']
        assert walls==sorted(walls) and len({tuple(w) for w in walls})==len(walls)
        assert all(len(w)==6 and all(isinstance(v,int) and -32768<=v<=32767 for v in w)
                   and w[:2]!=w[2:4] and w[4]<=w[5] for w in walls)
        header=(area/'src/world_walls.h').read_text()
        count=int(re.search(r'#define WORLD_WALL_COUNT (\d+)',header).group(1))
        decoded=[list(map(int,row.split(','))) for row in re.findall(r'\{(-?\d+(?:,-?\d+){5})\}',header)]
        assert count==len(walls) and decoded==walls
        triangles=world['wall_triangles'];assert triangles and triangles==sorted(triangles)
        triangle_header=(area/'src/world_wall_triangles.h').read_text()
        triangle_count=int(re.search(r'#define WORLD_WALL_TRIANGLE_COUNT (\d+)',triangle_header).group(1))
        decoded_triangles=[list(map(int,row.split(','))) for row in re.findall(r'\{(-?\d+(?:,-?\d+){8})\}',triangle_header)]
        assert triangle_count==len(triangles) and decoded_triangles==triangles
        assert all(len(t)==9 and all(isinstance(v,int) and -32768<=v<=32767 for v in t) for t in triangles)
        if data is not None:
            for filename,digest in report['source_files_sha256'].items():
                path=(data/filename).resolve();assert path.is_relative_to(data.resolve())
                with path.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==digest
            for e in instances:
                obj=scene.objects[e['component_path_id']];assert obj.type.name=='MeshCollider'
                collider=obj.read();assert collider.m_Enabled and not collider.m_IsTrigger
                go=collider.m_GameObject.read();assert go.m_Name==e['object']
                assert collider.m_Mesh.path_id==e['mesh_id'] and collider.m_Mesh.deref().assets_file.name==e['source_file']
                t=next(c.component.read() for c in go.m_Component if c.component.deref().type.name=='Transform')
                assert np.allclose(matrix(t),e['source_world_matrix'],rtol=0,atol=1e-9)
                while True:
                    assert t.m_GameObject.read().m_IsActive
                    if not t.m_Father.path_id:break
                    t=t.m_Father.read()
                allowed={'DrearyValley'}
                if name=='launchpad':allowed.add('_Trampoline (1)')
                assert t.m_GameObject.read().m_Name in allowed
        result['areas'].append({'area':name,'wall_count':len(walls),'source_colliders':len(instances),
                                'world_sha256':hashlib.sha256(world_path.read_bytes()).hexdigest(),
                                'header_sha256':hashlib.sha256(header.encode()).hexdigest()})
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('data',nargs='?',type=Path);args=parser.parse_args()
    print(json.dumps(check(args.data),indent=2))
