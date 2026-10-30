"""Regression: custom source shaders can be transparent despite _Mode == 0."""
from atlas_materials import material_flags
opaque_defaults={'_Mode':0.,'_ZWrite':1.,'_DstBlend':0.}
# Original Godray and Glass shader tags override stale Standard-shader defaults.
assert material_flags(1,{'QUEUE':'Transparent-1'},-1,opaque_defaults)==2
assert material_flags(1,{'QUEUE':'Transparent','RenderType':'Transparent'},-1,opaque_defaults)==2
# Original Frigid Bluffs terrain must stay visible; cutout is not blended alpha.
assert material_flags(1,{'RenderType':'Opaque'},-1,opaque_defaults)==0
assert material_flags(1,{'Queue':'AlphaTest','RenderType':'TransparentCutout'},-1,opaque_defaults)==0
assert material_flags(0,{'RenderType':'Opaque'},-1,opaque_defaults)==4
assert material_flags(1,{},3000,opaque_defaults)==2
assert material_flags(1,{},-1,{'_Mode':3})==2
print('Original shader transparency and opaque terrain regressions passed')
