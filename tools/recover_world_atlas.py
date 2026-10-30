"""Export all six world scenes into bounded CD sectors, never a spawn crop.

Only MeshFilter/MeshRenderer geometry is handled. Actors, UI, sky shells and
skinned geometry are inventoried separately. Initial and inactive static states
are retained, flagged independently. Texture colors are baked, not a shader port.
"""
import argparse
from collections import Counter, defaultdict
import hashlib, json, math, struct
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
import UnityPy
from UnityPy.helpers.MeshHelper import MeshHandler
from atlas_materials import material_flags

ROOT=Path(__file__).resolve().parents[1]
SCENES=[('level2','Cosmic Core'),('level3','Dreary Valley'),('level4','Crystal Rift'),('level5','Mystic Towers'),('level6','Frigid Bluffs'),('level7','Secret')]
SCALE=40
TRI=struct.Struct('<9h10B')
MAGIC=b'ZATL0001'

def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def clip(poly,axis,bound,sign):
    out=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        ia=(a[axis]-bound)*sign>=0;ib=(b[axis]-bound)*sign>=0
        if ia:out.append(a)
        if ia!=ib:out.append(a+(b-a)*(bound-a[axis])/(b[axis]-a[axis]))
    return out

def recover(data,out,cell):
    env=UnityPy.load(str(data));dependencies=set();matcache={};shadercache={};meshcache={};transformcache={};reports=[];allchunks=[];catalog=[]
    def wm(t):
        key=(t.object_reader.assets_file.name,t.object_reader.path_id)
        if key not in transformcache:
            p,q,s=t.m_LocalPosition,t.m_LocalRotation,t.m_LocalScale
            m=np.eye(4);m[:3,:3]=Rotation.from_quat([q.x,q.y,q.z,q.w]).as_matrix()@np.diag([s.x,s.y,s.z]);m[:3,3]=[p.x,p.y,p.z]
            if t.m_Father.path_id:m=wm(t.m_Father.read())@m
            transformcache[key]=m
        return transformcache[key]
    def transform(go):
        return next((c.component.read() for c in go.m_Component if c.component.deref().type.name=='Transform'),None)
    def meshdata(ptr):
        key=(ptr.deref().assets_file.name,ptr.path_id);dependencies.add(key[0])
        if key not in meshcache:
            mesh=ptr.read();h=MeshHandler(mesh);h.process()
            v=np.asarray(h.m_Vertices,dtype=float)[:,:3] if h.m_Vertices else np.empty((0,3));idx=np.asarray(h.m_IndexBuffer or [],dtype=int)
            colors=np.asarray(h.m_Colors,dtype=float)[:,:3] if h.m_Colors else np.full((len(v),3),255.)
            uv=np.asarray(h.m_UV0,dtype=float)[:,:2] if h.m_UV0 else np.zeros((len(v),2))
            meshcache[key]=(mesh,v,idx,colors,uv)
        return meshcache[key]
    def material(ptr):
        if not ptr.path_id:return np.array([1.,0.,1.]),None,'missing material (Unity magenta)',4,{'name':'missing','tags':{}}
        key=(ptr.deref().assets_file.name,ptr.path_id);dependencies.add(key[0])
        if key not in matcache:
            m=ptr.read();tint=np.ones(3);texture=None;alpha=1.
            floats=dict(m.m_SavedProperties.m_Floats)
            for k,c in m.m_SavedProperties.m_Colors:
                if k=='_Color':tint=np.array([c.r,c.g,c.b]);alpha=c.a
            for k,t in m.m_SavedProperties.m_TexEnvs:
                if k=='_MainTex' and t.m_Texture.path_id:
                    dependencies.add(t.m_Texture.deref().assets_file.name)
                    texture=np.asarray(t.m_Texture.read().image.convert('RGB'))
                    break
            shader_key=(m.m_Shader.deref().assets_file.name,m.m_Shader.path_id);dependencies.add(shader_key[0])
            if shader_key not in shadercache:
                parsed=m.m_Shader.read_typetree().get('m_ParsedForm',{})
                tags={str(k).lower():str(v) for ss in parsed.get('m_SubShaders',[]) for k,v in ss.get('m_Tags',{}).get('tags',[])}
                shadercache[shader_key]={'name':parsed.get('m_Name','unknown'),'tags':tags}
            shader_info=shadercache[shader_key]
            effect=material_flags(alpha,shader_info['tags'],m.m_CustomRenderQueue,floats)
            matcache[key]=(tint,texture,m.m_Name,effect,shader_info)
        return matcache[key]
    for sceneid,(scene,name) in enumerate(SCENES):
        F=next(f for f in env.files.values() if getattr(f,'name',None)==scene);dependencies.add(scene)
        markers=[o.read() for o in F.objects.values() if o.type.name=='Transform' and (o.read().m_GameObject.read().m_Name.startswith('_StartSpawnPoint') or (scene=='level7' and o.read().m_GameObject.read().m_Name=='StartSpawn'))]
        starts=[wm(t)[:3,3] for t in markers]
        origin=starts[0] if starts else np.zeros(3)
        source_tris=[];instances=[];excluded=Counter();skinned=sum(o.type.name=='SkinnedMeshRenderer' for o in F.objects.values())
        for o in sorted(F.objects.values(),key=lambda o:o.path_id):
            if o.type.name!='MeshFilter':continue
            d=o.read();go=d.m_GameObject.read();t=transform(go)
            if t is None:excluded['UI_RectTransform']+=1;continue
            root=t;active=bool(go.m_IsActive)
            while root.m_Father.path_id:
                root=root.m_Father.read();active=active and bool(root.m_GameObject.read().m_IsActive)
            rootname=root.m_GameObject.read().m_Name
            if rootname in ['HUD Bits','_Zera','_Kiwi','NPCs','Kly'] or 'Sky' in rootname or rootname=='Skybox':excluded['actor_UI_or_sky']+=1;continue
            renderer=next((c.component.read() for c in go.m_Component if c.component.deref().type.name=='MeshRenderer'),None)
            if renderer is None or not d.m_Mesh.path_id:excluded['no_mesh_renderer_or_mesh']+=1;continue
            mesh,v,idx,colors,uv=meshdata(d.m_Mesh)
            if not len(v):excluded['empty_mesh']+=1;continue
            first=renderer.m_StaticBatchInfo.firstSubMesh;count=renderer.m_StaticBatchInfo.subMeshCount
            if count and renderer.m_StaticBatchRoot.path_id:raise ValueError('Unexpected non-scene batch root')
            selected=list(range(first,first+count)) if count else list(range(len(mesh.m_SubMeshes)))
            if any(i>=len(mesh.m_SubMeshes) for i in selected):raise ValueError('Bad static batch range')
            matrix=np.eye(4) if count else wm(t);world=v@matrix[:3,:3].T+matrix[:3,3]
            flags=int(active and renderer.m_Enabled);added=0;selected_record=[]
            for local,si in enumerate(selected):
                sub=mesh.m_SubMeshes[si]
                if sub.topology!=0:excluded['non_triangle_submesh']+=1;continue
                begin=sub.firstByte//(2 if mesh.m_IndexFormat==0 else 4)
                faces=idx[begin:begin+sub.indexCount].reshape(-1,3)
                tint,texture,matname,effect,shader_info=material(renderer.m_Materials[min(local,len(renderer.m_Materials)-1)]) if renderer.m_Materials else (np.ones(3),None,'none',0,{'name':'none','tags':{}})
                selected_record.append({'submesh':si,'index_start':int(begin),'index_count':int(sub.indexCount),'material':matname,'material_flags':effect,'shader':shader_info})
                for ids in faces:
                    xyz=world[ids];rgb=colors[ids]*tint
                    if texture is not None:
                        # One source texture sample per corner, repeating UVs.
                        tc=uv[ids]%1;h,w=texture.shape[:2]
                        tex=texture[np.minimum(h-1,((1-tc[:,1])*h).astype(int)),np.minimum(w-1,(tc[:,0]*w).astype(int))]
                        rgb=rgb*tex/255
                    q=(xyz-origin)*SCALE;q[:,0]*=-1;q[:,1]*=-1
                    if not np.isfinite(q).all():raise ValueError('Non-finite world geometry')
                    source_tris.append((np.column_stack([q,np.clip(rgb,0,255)]),flags|effect));added+=1
            if added:instances.append({'component_path_id':o.path_id,'object':go.m_Name,'root':rootname,'mesh_file':d.m_Mesh.deref().assets_file.name,'mesh_id':d.m_Mesh.path_id,'transform_id':t.object_reader.path_id,'applied_matrix':matrix.tolist(),'static_batch':bool(count),'submeshes':selected_record,'initially_visible':bool(flags),'triangles':added})
        if not source_tris:raise ValueError('Empty world '+scene)
        bounds=np.array([p[:,:3] for p,_ in source_tris]);lo=bounds.min((0,1));hi=bounds.max((0,1))
        if not starts:origin_kind='world-origin; initial view selected from exported geometry'
        else:origin_kind='original start spawn'
        chunks=defaultdict(list);partition_area=0.;discarded_fragments=0;lost_area=0.
        source_area=float(sum(np.linalg.norm(np.cross(p[1,:3]-p[0,:3],p[2,:3]-p[0,:3]))/2 for p,_ in source_tris))
        for poly0,flags in source_tris:
            lower=np.floor(poly0[:,[0,2]].min(0)/cell).astype(int);upper=np.floor((poly0[:,[0,2]].max(0)-1e-7)/cell).astype(int);upper=np.maximum(lower,upper)
            for tz in range(lower[1],upper[1]+1):
                for tx in range(lower[0],upper[0]+1):
                    poly=list(poly0)
                    for axis,tile in [(0,tx),(2,tz)]:
                        poly=clip(poly,axis,tile*cell,1)
                        if poly:poly=clip(poly,axis,(tile+1)*cell,-1)
                        if not poly:break
                    for j in range(1,len(poly)-1):
                        p=np.array([poly[0],poly[j],poly[j+1]])
                        partition_area+=float(np.linalg.norm(np.cross(p[1,:3]-p[0,:3],p[2,:3]-p[0,:3]))/2)
                        xyz=np.rint(p[:,:3]).astype(int)
                        if not np.any(np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0])):
                            discarded_fragments+=1;lost_area+=float(np.linalg.norm(np.cross(p[1,:3]-p[0,:3],p[2,:3]-p[0,:3]))/2);continue
                        chunks[tx,tz].append((xyz,np.rint(p[:,3:]).astype(int),flags))
        scenechunks=[]
        for (tx,tz),triangles in sorted(chunks.items()):
            cx=tx*cell+cell//2;cz=tz*cell+cell//2
            ys=[int(v) for xyz,_,_ in triangles for v in xyz[:,1]];cy=((min(ys)+max(ys))//2//256)*256
            payload=bytearray()
            for xyz,col,flags in triangles:
                local=xyz-np.array([cx,cy,cz])
                if np.abs(local).max()>32767:raise ValueError('Sector coordinate overflow')
                payload+=TRI.pack(*local.ravel(),*col.ravel(),flags)
            row={'scene_id':sceneid,'tx':tx,'tz':tz,'center':[cx,cy,cz],'y_bounds':[min(ys),max(ys)],'triangles':len(triangles),'initial_triangles':sum(flags&1 for _,_,flags in triangles),'opaque_initial_triangles':sum((flags&1)!=0 and (flags&6)==0 for _,_,flags in triangles),'payload_sha256':hashlib.sha256(payload).hexdigest()}
            scenechunks.append(row);allchunks.append((row,bytes(payload)))
        counts={(c['tx'],c['tz']):c['triangles'] for c in scenechunks}
        maximum=max(sum(counts.get((tx+dx,tz+dz),0) for dx in [-1,0,1] for dz in [-1,0,1]) for tx,tz in counts)
        centers={(tx+dx,tz+dz) for tx,tz in counts for dx in range(-2,3) for dz in range(-2,3)}
        maximum5=max(sum(counts.get((tx+dx,tz+dz),0) for dx in range(-2,3) for dz in range(-2,3)) for tx,tz in centers)
        if maximum5>30000:raise ValueError(f'{scene}: neighborhood {maximum} exceeds RAM; reduce cell size')
        if starts:
            forward=wm(markers[0])[:3,2];direction=np.array([-forward[0],forward[2]]);direction/=np.linalg.norm(direction)
            entry=[round(-direction[0]*640),-600,round(-direction[1]*640)]
            entry_yaw=round(math.atan2(-direction[0],direction[1])*4096/(2*math.pi))&4095
        else:
            entry_yaw=0
            chosen=min(scenechunks,key=lambda c:abs(c['tx'])+abs(c['tz']));entry=[chosen['center'][0],chosen['center'][1]-max(120,cell//4),chosen['center'][2]-cell//2]
        row={'scene':scene,'name':name,'source_origin':origin.tolist(),'origin_kind':origin_kind,'entry':entry,'entry_yaw':entry_yaw,'world_bounds':[lo.tolist(),hi.tolist()],'source_surface_area':source_area,'partition_surface_area':partition_area,'partition_relative_error':abs(source_area-partition_area)/max(1,source_area),'quantized_degenerate_fragments':discarded_fragments,'quantized_lost_surface_area':lost_area,'quantized_lost_surface_fraction':lost_area/max(1,source_area),'mesh_instances':len(instances),'source_triangles':len(source_tris),'exported_triangles':sum(c['triangles'] for c in scenechunks),'sectors':len(scenechunks),'maximum_3x3_triangles':maximum,'maximum_5x5_triangles':maximum5,'excluded_meshfilters':dict(excluded),'skinned_renderers_not_exported':skinned,'instances':instances}
        reports.append(row);catalog.append({'name':name,'scene':scene,'entry':entry,'yaw':entry_yaw})
        print(scene,name,len(source_tris),'source triangles;',len(scenechunks),'sectors; neighborhood',maximum,flush=True)
    out.mkdir(parents=True,exist_ok=True)
    for d in ['assets','src','reports']:(out/d).mkdir(exist_ok=True)
    tag=hashlib.sha256(json.dumps([r for r,_ in allchunks],sort_keys=True).encode()).digest()[:16]
    blob=bytearray(MAGIC+tag+struct.pack('<II',len(catalog),cell));blob+=bytes(2048-len(blob))
    for row,payload in allchunks:
        raw=struct.pack('<4i',row['scene_id'],row['tx'],row['tz'],row['triangles'])+payload
        row['sector']=len(blob)//2048;row['sectors']=(len(raw)+2047)//2048
        blob+=raw+bytes((-len(raw))%2048)
    (out/'assets/WORLD.DAT').write_bytes(blob)
    header='/* Generated original-scene CD catalog; sector-local int16 geometry. */\n'
    capacity=math.ceil(max(r['maximum_5x5_triangles'] for r in reports)/256)*256
    header+='#define ATLAS_SCENES 6\n#define ATLAS_CELL %d\n#define ATLAS_TILE_COUNT %d\n#define ATLAS_TRIANGLE_CAPACITY %d\n#define ATLAS_NEIGHBOR_RADIUS 2\n'%(cell,len(allchunks),capacity)
    header+='static const unsigned char atlas_tag[16]={'+','.join(map(str,tag))+'};\n'
    header+='static const AtlasScene atlas_scenes[]={\n'+''.join('{"%s",{%d,%d,%d},%d},\n'%(s['name'],*s['entry'],s['yaw']) for s in catalog)+'};\n'
    header+='static const AtlasTile atlas_tiles[]={\n'+''.join('{%d,%d,%d,{%d,%d,%d},%d,%d,%d,%d,%d},\n'%(r['scene_id'],r['tx'],r['tz'],*r['center'],r['triangles'],r['sector'],r['sectors'],*r['y_bounds']) for r,_ in allchunks)+'};\n'
    (out/'src/atlas_catalog.h').write_text(header)
    dependencies|={'globalgamemanagers'}
    dependencies.update(p.relative_to(data).as_posix() for p in data.rglob('*.resS'))
    paths={}
    for n in sorted(dependencies):
        p=data/n
        if not p.is_file():
            matches=[p for p in data.rglob(n) if p.is_file()]
            if len(matches)!=1:raise ValueError('Source path not unique: '+n)
            p=matches[0]
        paths[n]=p.relative_to(data).as_posix()
    hashes={paths[n]:digest(data/paths[n]) for n in sorted(paths)}
    report={'schema_version':1,'scale':SCALE,'sector_size_world_units':cell,'triangle_bytes':28,'data_file_sha256':digest(out/'assets/WORLD.DAT'),'catalog_sha256':digest(out/'src/atlas_catalog.h'),'source_path_mapping':paths,'maximum_resident_triangles':capacity,'data_bytes':len(blob),'source_files_sha256':hashes,'scenes':reports,'tiles':[r for r,_ in allchunks],'flag_bits':{'1':'renderer and hierarchy initially enabled','2':'transparent shader queue/RenderType or material blending','4':'zero alpha or missing material'},'default_view':'Opaque initially enabled geometry; other states retained for optional inspection','coverage':'Every triangle submesh of supported non-actor 3D MeshRenderers in level2..level7, including flagged inactive states; no XZ crop','limitations':['No skinned meshes, actors, UI, sky shells or particle renderers','Only serialized static poses; object behavior and original scene transitions absent','Textures sampled into corner colors; source shaders, full textures and transparency absent','Fly-camera inspection only; physics and gameplay are not integrated']}
    (out/'reports/world_atlas.json').write_text(json.dumps(report,indent=2)+'\n')
    print('CD data',len(blob),'bytes',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('data',type=Path);p.add_argument('--output',type=Path,default=ROOT/'previews/atlas');p.add_argument('--cell',type=int,default=640);a=p.parse_args()
    if a.cell<80 or a.cell%80:p.error('cell must be a positive multiple of 80, at least 80')
    recover(a.data,a.output,a.cell)
