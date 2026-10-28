"""Recover Zera's source mascot textures and per-corner material/color data.
Eye alpha is adapted to PS1 cutout transparency; custom Unity shaders are omitted.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
import UnityPy
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('data');args=p.parse_args()
env=UnityPy.load(args.data)
sm=next(o.read() for o in env.objects if o.assets_file.name=='level2' and o.type.name=='SkinnedMeshRenderer' and o.read().m_Mesh.path_id==314 and o.read().m_Mesh.deref().assets_file.name=='resources.assets')
out=root/'assets/character_textures';out.mkdir(exist_ok=True)
materials=[];textures={}
for i,ptr in enumerate(sm.m_Materials):
 m=ptr.read();entry={'slot':i,'name':m.m_Name,'file':ptr.deref().assets_file.name,'path_id':ptr.path_id}
 for key,tex in m.m_SavedProperties.m_TexEnvs:
  if key!='_MainTex' or not tex.m_Texture.path_id:continue
  t=tex.m_Texture.read();image=t.image.convert('RGBA');image.save(out/(t.m_Name+'.png'))
  entry['main_texture']={'name':t.m_Name,'file':tex.m_Texture.deref().assets_file.name,'path_id':tex.m_Texture.path_id,'size':list(image.size),'wrap_u':t.m_TextureSettings.m_WrapU,'wrap_v':t.m_TextureSettings.m_WrapV}
  textures[i]=image
 materials.append(entry)
assert materials[1]['name']=='Spots' and materials[3]['name']=='Eyes'
assert textures[1].size==(256,256) and textures[3].size==(64,64)
atlas=np.full((128,256,4),255,dtype=np.uint8)
atlas[:128,:128]=np.array(textures[1].resize((128,128),Image.Resampling.NEAREST))
# Source eyes repeat. Two periods with 32px wrap padding preserve UVs outside 0..1.
atlas[:128,128:256]=np.pad(np.array(textures[3]),((32,32),(32,32),(0,0)),mode='wrap')
opaque=atlas[:,:,3]>=128
rgb=Image.fromarray(atlas[:,:,:3]).quantize(colors=255,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
indices=np.array(rgb,dtype=np.uint8).astype(np.uint16)+1
indices[~opaque]=0;indices=indices.astype(np.uint8)
palette=rgb.getpalette()[:255*3];palette += [0]*(255*3-len(palette))
clut=[0]
for i in range(255):
 r,g,b=palette[i*3:i*3+3];clut.append((r>>3)|((g>>3)<<5)|((b>>3)<<10) or 1)
preview=Image.fromarray(indices,mode='P');preview.putpalette([0,0,0]+palette);preview.info['transparency']=0;preview.save(out/'mascot_atlas.png')
raw=indices.tobytes();words=[int.from_bytes(raw[i:i+4],'little') for i in range(0,len(raw),4)]
clutwords=[clut[i]|(clut[i+1]<<16) for i in range(0,256,2)]
s='/* Original mascot main textures: 8-bit 256x128 atlas; source eye alpha adapted to cutout. */\n'
s+='static const uint32_t mascot_texture[]={'+','.join(hex(v) for v in words)+'};\n'
s+='static const uint32_t mascot_clut[]={'+','.join(hex(v) for v in clutwords)+'};\n'
(root/'src/mascot_texture.h').write_text(s)
colors=json.loads((root/'assets/zera_vertex_colors.json').read_text());uv=[];faces=[];slot=0
for line in (root/'assets/recovered_meshes/resources_assets_314_Cube_001.obj').read_text().splitlines():
 f=line.split()
 if not f:continue
 if f[0]=='vt':uv.append(tuple(map(float,f[1:3])))
 if f[0]=='g' and f[1].startswith('Cube_001_'):slot=int(f[1].rsplit('_',1)[1])
 if f[0]=='f':
  corners=[tuple(int(v)-1 for v in x.split('/')[:2]) for x in f[1:]]
  for k in range(1,len(corners)-1):faces.append((slot,[corners[0],corners[k],corners[k+1]]))
color_data=[];uv_data=[];kinds=[]
for slot,face in faces:
 color_data.append([int(v) for vertex,_ in face for v in colors[vertex][:3]])
 kind=1 if slot==1 else 2 if slot==3 else 0;kinds.append(kind)
 coords=[]
 for _,ti in face:
  u,v=uv[ti]
  if kind==1:coords.extend([round(u*128),round((1-v)*128)])
  elif kind==2:coords.extend([round(160+u*64),round(32+(1-v)*64)])
  else:coords.extend([0,0])
 assert all(0<=v<=255 for v in coords)
 uv_data.append(coords)
s='/* Source per-corner colors and UVs; face order matches zera_mesh.h. */\n'
s+='static const unsigned char mascot_corner_colors[][9]={'+''.join('{'+','.join(map(str,c))+'},' for c in color_data)+'};\n'
s+='static const unsigned char mascot_uv[][6]={'+''.join('{'+','.join(map(str,c))+'},' for c in uv_data)+'};\n'
s+='static const unsigned char mascot_material[]={'+','.join(map(str,kinds))+'};\n'
s+='static const unsigned short mascot_draw_order[]={'+','.join(map(str,sorted(range(len(faces)),key=lambda i:(kinds[i],i),reverse=True)))+'};\n'
s+='#define MASCOT_FACE_COUNT %d\n'%len(faces)
(root/'src/mascot_materials.h').write_text(s)
source_files={'level2','resources.assets'}|{m['file'] for m in materials}
hashes={}
for name in source_files:
 files=[p for p in Path(args.data).rglob(name) if p.is_file()];assert len(files)==1
 hashes[name]=hashlib.sha256(files[0].read_bytes()).hexdigest()
report={'renderer_scene':'level2','renderer_path_id':sm.object_reader.path_id,'materials':materials,'source_file_sha256':hashes,'rendered_faces':len(faces),'textured_spot_faces':kinds.count(1),'textured_eye_faces':kinds.count(2),'flat_material_faces':kinds.count(0),'atlas':{'size':[256,128],'format':'8-bit indexed','palette_entries':256,'transparent_index':0,'eye_alpha_threshold':128,'vram_texture':[640,0,128,128],'vram_clut':[512,257,256,1]},'limitations':['nearest-neighbor downsampled spots, 256 to 128 texels','255 opaque palette colors shared with eyes','eye alpha thresholded to cutout; no soft blending','equal-depth ordering favors spots and eyes over body; painter sorting remains approximate','custom Unity shader and lighting behavior omitted']}
(root/'reports/mascot_materials.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['rendered_faces','textured_spot_faces','textured_eye_faces']}))
