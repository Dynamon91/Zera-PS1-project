"""Recover the selected original clips from an extracted Unity Data directory."""
from pathlib import Path
import sys,json
import UnityPy
P=Path(__file__).resolve().parents[1];out=P/'assets/audio_source';out.mkdir(exist_ok=True)
E=UnityPy.load(sys.argv[1]);manifest=[]
for id,name in [(560,'ui_move'),(567,'ui_accept'),(575,'jump'),(592,'land'),(608,'dash'),(573,'flap'),(566,'pickup'),(584,'cosmic_core')]:
 d=next(o.read() for o in E.objects if o.assets_file.name=='resources.assets' and o.path_id==id)
 samples=d.samples
 if not samples:raise RuntimeError('No decoded samples for '+name)
 data=next(iter(samples.values()));(out/(name+'.wav')).write_bytes(data)
 manifest.append({'name':name,'original_name':d.m_Name,'source':'resources.assets','path_id':id,'duration_seconds':d.m_Length,'source_rate':d.m_Frequency,'source_channels':d.m_Channels})
(P/'reports/audio_sources.json').write_text(json.dumps(manifest,indent=2))
