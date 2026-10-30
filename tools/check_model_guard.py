"""Reject unintended changes to the previously corrected and visually inspected model assets."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def check():
 baseline=json.loads((ROOT/'reports/model_baseline.json').read_text())
 for name,digest in baseline['files_sha256'].items():
  actual=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
  if actual!=digest:raise ValueError('Model baseline changed: '+name+'. Regenerate and validate against source transforms, animation and native views before updating the baseline.')
 return {'files':len(baseline['files_sha256']),'baseline_archive':baseline['reference_archive'],'unchanged':True,'limitation':'Integrity guard for these corrected assets; visual/source validation is still required for any intentional new model change'}
if __name__=='__main__':print(json.dumps(check(),indent=2))
