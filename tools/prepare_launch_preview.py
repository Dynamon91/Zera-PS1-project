"""Generate fixed-point launch parameters from recovered source and PhysicsManager."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import UnityPy
import dnfile

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data',type=Path)
    args=parser.parse_args()
    area=ROOT/'previews/launchpad'
    world=json.loads((area/'reports/world_conversion.json').read_text())
    original=json.loads((ROOT/'reports/launchpad_recovery.json').read_text())
    pad=next(e for s in original['scenes'] if s['scene']=='level3' for e in s['entries'] if e['component_path_id']==world['launchpad_component_path_id'])
    env=UnityPy.load(str(args.data/'globalgamemanagers'))
    settings=next(o for o in env.objects if o.type.name=='PhysicsManager')
    gravity=settings.read_typetree()['m_Gravity']['y']
    assert gravity<0
    sx,_,sz=world['spawn'];ground=world['ground_height'];scale=world['world_scale']
    def convert(v):return [round(-(v[0]-sx)*scale*256),round((v[1]-ground)*scale*256),round((v[2]-sz)*scale*256)]
    start=convert(pad['source_world_position']);end=convert(pad['landing_point']);trigger=convert(pad['kiwi_point']['target']['source_world_position'])
    step=round(65536*pad['travel_speed']/(30*pad['travel_time']))
    arc=round(-0.5*gravity*scale*256*pad['travel_time']**2)
    facing=round(math.atan2(end[0]-start[0],end[2]-start[2])*4096/(2*math.pi))&4095
    report={'scene':'level3','component_path_id':pad['component_path_id'],'source_report_sha256':hashlib.sha256((ROOT/'reports/launchpad_recovery.json').read_bytes()).hexdigest(),
            'physics_source_sha256':hashlib.sha256((args.data/'globalgamemanagers').read_bytes()).hexdigest(),'physics_manager_path_id':settings.path_id,
            'gravity_y':gravity,'travel_time':pad['travel_time'],'travel_speed':pad['travel_speed'],
            'scale':scale,'fractional_position_scale':256,'normalized_time_scale':65536,'simulation_hz':30,
            'start_fp':start,'end_fp':end,'trigger_fp':trigger,'trigger_radius_fp':3*scale*256,'time_step_q16':step,'arc_fp':arc,'facing':facing,
            'adaptations':['Triangle while grounded near the original companion target replaces unported Somersault/companion trigger',
                           '30 Hz integer trajectory; final endpoint clamped exactly before floor support selection',
                           'Kinematic flight ignores wall proxies, matching source kinematic intent; full original collision/state behavior is not ported',
                           'Existing jump/land effects and jump animation are placeholders for original boing/launch animations']}
    (area/'reports/launch_config.json').write_text(json.dumps(report,indent=2)+'\n')
    def vector(v):return '{'+','.join(map(str,v))+'}'
    (area/'src/launch_config.h').write_text('/* Recovered original level3 LaunchPad 7246; positions in FP=256. */\n'
        +'#define LAUNCH_FACING '+str(facing)+'\n'
        +'static const LaunchConfig launch_config={'+','.join([vector(start),vector(end),vector(trigger),str(3*scale*256),str(step),str(arc)])+'};\n')
    assembly=args.data/'Managed/Assembly-CSharp.dll'
    pe=dnfile.dnPE(str(assembly))
    audit={'assembly_sha256':hashlib.sha256(assembly.read_bytes()).hexdigest(),
           'set_gravity_member_references':[str(r.Name) for r in pe.net.mdtables.MemberRef.rows if str(r.Name)=='set_gravity'],
           'scope':'Assembly-CSharp.dll metadata only; does not audit other assemblies or native components'}
    (area/'reports/gravity_reference_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':main()
