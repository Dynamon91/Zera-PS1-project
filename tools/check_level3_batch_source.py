"""Cross-check converted batch bounds against independent original collider meshes."""
import argparse
import json
from pathlib import Path
import numpy as np
import UnityPy
from UnityPy.helpers.MeshHelper import MeshHandler

p=argparse.ArgumentParser(description=__doc__);p.add_argument('data');args=p.parse_args()
root=Path(__file__).resolve().parents[1]
report=json.loads((root/'previews/level3/reports/world_conversion.json').read_text())
env=UnityPy.load(args.data);scene=next(f for f in env.files.values() if getattr(f,'name','')=='level3')
results=[]
for instance in report['instances']:
 if not instance['object'].startswith('Walkable'):continue
 t=scene.objects[instance['transform_path_id']].read();go=t.m_GameObject.read()
 collider=next(c.component.read() for c in go.m_Component if c.component.deref().type.name=='MeshCollider')
 h=MeshHandler(collider.m_Mesh.read());h.process();v=np.array(h.m_Vertices)[:,:3]
 m=np.array(instance['original_object_world_matrix']);v=v@m[:3,:3].T+m[:3,3]
 bounds=np.array([v.min(0),v.max(0)]);batch=np.array(instance['source_world_bounds'])
 error=float(np.abs(bounds-batch).max())
 assert error<.1,(instance['object'],error)
 results.append({'object':instance['object'],'collider_mesh_path_id':collider.m_Mesh.path_id,
                 'collider_source_file':collider.m_Mesh.deref().assets_file.name,
                 'batch_vs_collider_bounds_max_error_source_units':error})
expected=sum(i['object'].startswith('Walkable') for i in report['instances'])
assert len(results)==expected and expected>=2
assert {'Walkable.001','Walkable.002'}<={r['object'] for r in results}
out={'validation':'Independent collider-local mesh transformed by original object hierarchy vs scene-space static-batch render bounds',
     'tolerance_source_units':.1,'results':results}
(root/'previews/level3/reports/batch_validation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
