"""Cross-check the generated PS1 launch constants against the recovered records."""
import hashlib
import json
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=ROOT/'previews/launchpad'
c=json.loads((a/'reports/launch_config.json').read_text())
w=json.loads((a/'reports/world_conversion.json').read_text())
rpath=ROOT/'reports/launchpad_recovery.json';r=json.loads(rpath.read_text())
p=next(e for s in r['scenes'] if s['scene']=='level3' for e in s['entries'] if e['component_path_id']==7246)
assert c['source_report_sha256']==hashlib.sha256(rpath.read_bytes()).hexdigest()
assert c['component_path_id']==w['launchpad_component_path_id']==7246
assert w['spawn']==p['source_world_position']
assert c['travel_time']==p['travel_time'] and c['travel_speed']==p['travel_speed']
assert c['scale']==w['world_scale']==80 and c['simulation_hz']==30
assert c['gravity_y']==-30 and len(c['physics_source_sha256'])==64
sx,_,sz=w['spawn'];g=w['ground_height']
def convert(v):return [round(-(v[0]-sx)*80*256),round((v[1]-g)*80*256),round((v[2]-sz)*80*256)]
assert c['start_fp']==convert(p['source_world_position'])
assert c['end_fp']==convert(p['landing_point'])
assert c['trigger_fp']==convert(p['kiwi_point']['target']['source_world_position'])
assert c['trigger_radius_fp']==3*80*256
assert c['time_step_q16']==round(65536*p['travel_speed']/(30*p['travel_time']))
assert c['arc_fp']==round(-0.5*c['gravity_y']*80*256*p['travel_time']**2)
facing=round(math.atan2(c['end_fp'][0]-c['start_fp'][0],c['end_fp'][2]-c['start_fp'][2])*4096/(2*math.pi))&4095
assert c['facing']==facing
def vector(v):return '{'+','.join(map(str,v))+'}'
expected='/* Recovered original level3 LaunchPad 7246; positions in FP=256. */\n#define LAUNCH_FACING '+str(facing)+'\nstatic const LaunchConfig launch_config={'+','.join([vector(c['start_fp']),vector(c['end_fp']),vector(c['trigger_fp']),str(c['trigger_radius_fp']),str(c['time_step_q16']),str(c['arc_fp'])])+'};\n'
assert (a/'src/launch_config.h').read_text()==expected
for key in ('start_fp','end_fp'):
 assert max(abs(c[key][0]),abs(c[key][2]))<w['source_radius_units']*80*256
for name,digest in w['source_files_sha256'].items():
 if name in r['source_file_sha256']:assert digest==r['source_file_sha256'][name]
audit=json.loads((a/'reports/gravity_reference_audit.json').read_text())
assert audit['assembly_sha256']==r['source_file_sha256']['Managed/Assembly-CSharp.dll']
assert audit['set_gravity_member_references']==[]
print('Launch asset provenance, coordinate conversion, Q16 trajectory and compiled header verified')
