"""Validate full-world sector coverage, disk ABI, provenance and resident bounds."""
import argparse, hashlib, json, math, struct, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def check(root=ROOT/'previews/atlas',data=None):
    root=Path(root);r=json.loads((root/'reports/world_atlas.json').read_text());blob=(root/'assets/WORLD.DAT').read_bytes()
    assert hashlib.sha256(blob).hexdigest()==r['data_file_sha256']
    header=(root/'src/atlas_catalog.h').read_text()
    assert digest(root/'src/atlas_catalog.h')==r['catalog_sha256']
    tag=bytes(map(int,re.search(r'atlas_tag\[16\]=\{([^}]+)\}',header).group(1).split(',')))
    assert blob[8:24]==tag
    assert int(re.search(r'#define ATLAS_TRIANGLE_CAPACITY (\d+)',header).group(1))==r['maximum_resident_triangles']
    catalog_rows=header.split('static const AtlasTile atlas_tiles[]={')[1].split('};')[0].strip().splitlines()
    assert len(catalog_rows)==len(r['tiles'])
    for line,tile in zip(catalog_rows,r['tiles']):
        values=list(map(int,re.findall(r'-?\d+',line)))
        assert values==[tile['scene_id'],tile['tx'],tile['tz'],*tile['center'],tile['triangles'],tile['sector'],tile['sectors'],*tile['y_bounds']]
    assert blob[:8]==b'ZATL0001' and len(blob)==r['data_bytes'] and len(blob)%2048==0
    assert struct.unpack_from('<II',blob,24)==(6,r['sector_size_world_units'])
    assert [s['scene'] for s in r['scenes']]==['level2','level3','level4','level5','level6','level7']
    assert r['triangle_bytes']==28 and len({(t['scene_id'],t['tx'],t['tz']) for t in r['tiles']})==len(r['tiles'])
    previous_end=2048
    tri=struct.Struct('<9h10B');cell=r['sector_size_world_units']
    for t in r['tiles']:
        start=t['sector']*2048;end=start+t['sectors']*2048
        assert start==previous_end and 0<=start<end<=len(blob)
        assert struct.unpack_from('<4i',blob,start)==(t['scene_id'],t['tx'],t['tz'],t['triangles'])
        size=t['triangles']*28;payload=blob[start+16:start+16+size]
        assert t['sectors']==math.ceil((size+16)/2048)
        assert hashlib.sha256(payload).hexdigest()==t['payload_sha256']
        active=0;opaque=0
        for row in tri.iter_unpack(payload):
            assert row[-1]&~7==0;active+=row[-1]&1;opaque+=bool(row[-1]&1 and not row[-1]&6)
            for k in range(3):
                assert -cell//2<=row[k*3]<=cell//2
                assert -cell//2<=row[k*3+2]<=cell//2
                assert t['y_bounds'][0]<=row[k*3+1]+t['center'][1]<=t['y_bounds'][1]
        assert active==t['initial_triangles'] and opaque==t['opaque_initial_triangles'];previous_end=end
    assert previous_end==len(blob)
    for i,s in enumerate(r['scenes']):
        tiles=[t for t in r['tiles'] if t['scene_id']==i];counts={(t['tx'],t['tz']):t['triangles'] for t in tiles}
        assert len(tiles)==s['sectors'] and sum(t['triangles'] for t in tiles)==s['exported_triangles']
        assert sum(inst['triangles'] for inst in s['instances'])==s['source_triangles']
        maximum=max(sum(counts.get((tx+dx,tz+dz),0) for dx in [-1,0,1] for dz in [-1,0,1]) for tx,tz in counts)
        assert maximum==s['maximum_3x3_triangles']
        centers={(tx+dx,tz+dz) for tx,tz in counts for dx in range(-2,3) for dz in range(-2,3)}
        maximum5=max(sum(counts.get((tx+dx,tz+dz),0) for dx in range(-2,3) for dz in range(-2,3)) for tx,tz in centers)
        assert maximum5==s['maximum_5x5_triangles']<=r['maximum_resident_triangles']<=30000
        assert s['partition_relative_error']<1e-9
        assert s['quantized_lost_surface_fraction']<0.00001
    if data is not None:check_original(Path(data),r)
    return {'scenes':6,'sectors':len(r['tiles']),'source_triangles':sum(s['source_triangles'] for s in r['scenes']),
            'data_sha256':r['data_file_sha256'],'maximum_resident_triangles':r['maximum_resident_triangles'],
            'original_source_checked':data is not None,
            'coverage':'Full supported static geometry, including inactive states; actors/UI/sky/skinned and gameplay excluded'}

def check_original(data,r):
    import UnityPy
    import numpy as np
    for path,sha in r['source_files_sha256'].items():assert digest(data/path)==sha,path
    env=UnityPy.load(str(data));cache={}
    def matrix(t):
        key=(t.object_reader.assets_file.name,t.object_reader.path_id)
        if key not in cache:
            p,q,s=t.m_LocalPosition,t.m_LocalRotation,t.m_LocalScale
            x,y,z,w=q.x,q.y,q.z,q.w;k=2/(x*x+y*y+z*z+w*w)
            rot=np.array([[1-k*(y*y+z*z),k*(x*y-z*w),k*(x*z+y*w)],
                          [k*(x*y+z*w),1-k*(x*x+z*z),k*(y*z-x*w)],
                          [k*(x*z-y*w),k*(y*z+x*w),1-k*(x*x+y*y)]])
            m=np.eye(4);m[:3,:3]=rot@np.diag([s.x,s.y,s.z]);m[:3,3]=[p.x,p.y,p.z]
            if t.m_Father.path_id:m=matrix(t.m_Father.read())@m
            cache[key]=m
        return cache[key]
    for s in r['scenes']:
        F=next(f for f in env.files.values() if getattr(f,'name',None)==s['scene'])
        for inst in s['instances']:
            d=F.objects[inst['component_path_id']].read();assert d.m_Mesh.path_id==inst['mesh_id']
            assert d.m_Mesh.deref().assets_file.name==inst['mesh_file']
            go=d.m_GameObject.read();assert go.m_Name==inst['object']
            ren=next(c.component.read() for c in go.m_Component if c.component.deref().type.name=='MeshRenderer')
            t=F.objects[inst['transform_id']].read();active=bool(ren.m_Enabled);ancestor=t
            while True:
                active=active and bool(ancestor.m_GameObject.read().m_IsActive)
                if not ancestor.m_Father.path_id:break
                ancestor=ancestor.m_Father.read()
            assert bool(active)==inst['initially_visible']
            assert ancestor.m_GameObject.read().m_Name==inst['root']
            expected=np.eye(4) if ren.m_StaticBatchInfo.subMeshCount else matrix(t)
            assert np.max(np.abs(expected-np.array(inst['applied_matrix'])))<1e-6
            mesh=d.m_Mesh.read();count=0
            selection=list(range(ren.m_StaticBatchInfo.firstSubMesh,ren.m_StaticBatchInfo.firstSubMesh+ren.m_StaticBatchInfo.subMeshCount)) if inst['static_batch'] else list(range(len(mesh.m_SubMeshes)))
            for si in selection:
                sub=mesh.m_SubMeshes[si]
                if sub.topology==0:count+=sub.indexCount//3
            assert count==inst['triangles']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data',type=Path);a=p.parse_args();print(json.dumps(check(data=a.data),indent=2))
