"""Recover original Relic body meshes/materials for selected scene components."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
import UnityPy
from UnityPy.helpers.MeshHelper import MeshHandler
ROOT=Path(__file__).resolve().parents[1]

def convert(data,components=None,output_root=ROOT):
    data=Path(data);env=UnityPy.load(str(data));scene=next(f for f in env.files.values() if getattr(f,'name','')=='level3')
    cache={}
    def matrix(t):
        key=t.object_reader.path_id
        if key not in cache:
            p,q,s=t.m_LocalPosition,t.m_LocalRotation,t.m_LocalScale
            m=np.eye(4);m[:3,:3]=Rotation.from_quat([q.x,q.y,q.z,q.w]).as_matrix()@np.diag([s.x,s.y,s.z]);m[:3,3]=[p.x,p.y,p.z]
            if t.m_Father.path_id:m=matrix(t.m_Father.read())@m
            cache[key]=m
        return cache[key]
    def transform(go):return next(c.component.read() for c in go.m_Component if c.component.deref().type.name=='Transform')
    def descendants(t):
        yield t
        for child in t.m_Children:yield from descendants(child.read())
    vertices=[];faces=[];colors=[];spans=[];records=[]
    for component_id in (components or [6594,6596,7178]):
        d=scene.objects[component_id].read(check_read=False);script=d.m_Script.read()
        assert (script.m_Namespace,script.m_ClassName)==('NewZera','Relic')
        root=transform(d.m_GameObject.read());origin=matrix(root)[:3,3]
        body=next(t for t in descendants(root) if t.m_GameObject.read().m_Name=='Relic')
        go=body.m_GameObject.read()
        mf=next(c.component.read() for c in go.m_Component if c.component.deref().type.name=='MeshFilter')
        renderer=next(c.component.read() for c in go.m_Component if c.component.deref().type.name=='MeshRenderer')
        assert renderer.m_Enabled and len(renderer.m_Materials)==1
        mesh=mf.m_Mesh.read();h=MeshHandler(mesh);h.process()
        assert len(mesh.m_SubMeshes)==1 and mesh.m_SubMeshes[0].topology==0
        matptr=renderer.m_Materials[0];mat=matptr.read();color=dict(mat.m_SavedProperties.m_Colors)['_Color']
        rgb=np.array([color.r,color.g,color.b]);v=np.array(h.m_Vertices)[:,:3]
        m=matrix(body);world=v@m[:3,:3].T+m[:3,3];local=(world-origin)*80;local[:,0]*=-1;local[:,1]*=-1
        q=np.rint(local).astype(int);assert np.abs(q).max()<32768
        unique=list(dict.fromkeys(map(tuple,q)));lookup={p:i for i,p in enumerate(unique)}
        firstv=len(vertices);firstf=len(faces);vertices+=unique
        for ids in np.array(h.m_IndexBuffer).reshape(-1,3):
            mapped=[lookup[tuple(q[i])]+firstv for i in ids]
            if len(set(mapped))<3:continue
            a,b,c=q[ids];n=np.cross(b-a,c-a);length=np.linalg.norm(n)
            if not length:continue
            # Provisional static facet lighting; original reflective shader is omitted.
            light=.6+.4*abs(float(n@np.array([.3,-.8,.5]))/(length*np.linalg.norm([.3,-.8,.5])))
            faces.append(mapped);colors.append(np.rint(np.clip(rgb*255*light,0,255)).astype(int).tolist())
        spans.append([firstv,len(unique),firstf,len(faces)-firstf])
        records.append({'component_path_id':component_id,'body_transform_path_id':body.object_reader.path_id,
                        'mesh_file':mf.m_Mesh.deref().assets_file.name,'mesh_path_id':mf.m_Mesh.path_id,'mesh_name':mesh.m_Name,
                        'material_path_id':matptr.path_id,'material_name':mat.m_Name,'source_base_rgb':rgb.tolist(),
                        'source_body_world_matrix':m.tolist(),'source_origin':origin.tolist(),
                        'source_vertices':len(v),'source_triangles':len(h.m_IndexBuffer)//3,'packed_vertices':len(unique),'render_triangles':len(faces)-firstf})
    def rows(items):return ''.join('{'+','.join(map(str,p))+'},\n' for p in items)
    header='/* Original Relic body meshes/material base colors; reflective shader omitted. */\n'
    header+='#define RELIC_MODEL_COUNT %d\n#define RELIC_MODEL_MAX_VERTICES %d\n'%(len(spans),max(s[1] for s in spans))
    header+='static const SVECTOR relic_model_vertices[]={\n'+''.join('{%d,%d,%d,0},\n'%p for p in vertices)+'};\n'
    header+='static const unsigned short relic_model_faces[][3]={\n'+rows(faces)+'};\n'
    header+='static const unsigned char relic_model_colors[][3]={\n'+rows(colors)+'};\n'
    header+='static const unsigned short relic_model_spans[%d][4]={\n'%len(spans)+rows(spans)+'};\n'
    output_root=Path(output_root)
    (output_root/'src').mkdir(parents=True,exist_ok=True);(output_root/'reports').mkdir(parents=True,exist_ok=True)
    (output_root/'src/relic_models.h').write_text(header)
    report={'schema_version':1,'instances':records,'source_file_sha256':{name:hashlib.sha256((data/name).read_bytes()).hexdigest() for name in ['level3','resources.assets']},
            'conversion':'Original body world transform relative to original relic origin, scale80, mirrored X/Y for PS1 rendering; integer quantization',
            'limitations':['Static serialized body pose; original runtime rotation not ported','Original base material colors with provisional facet lighting','Reflective/specular shader, flare, shadow and particles omitted','Pickup locations and behavior unchanged']}
    (output_root/'reports/relic_models.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'vertices':len(vertices),'triangles':len(faces),'instances':len(records)}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('data');p.add_argument('--components',type=int,nargs='+');p.add_argument('--output-root',type=Path,default=ROOT)
    a=p.parse_args();convert(a.data,a.components,a.output_root)
