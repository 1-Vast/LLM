"""Verify every finalized predecessor before and after this new experiment."""
from datetime import datetime,timezone
import hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'log/20261022/cipa_calibration_probe'

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def verify():
    spec=importlib.util.spec_from_file_location('caf_predecessor',ROOT/'research/caf_mechanics_qualification_20261022/preserve.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    result=module.verify()
    for phase in ['caf_mechanics_qualification','next_asset']:
        manifest=ROOT/'log/20261022'/phase/'FINAL_FILE_INVENTORY.json'
        result['manifest_sha256'][manifest.relative_to(ROOT).as_posix()]=sha(manifest)
        for row in json.loads(manifest.read_text())['files']:
            path=ROOT/row['path'];result['checks'].append(dict(path=row['path'],passed=path.is_file() and path.stat().st_size==row['bytes'] and sha(path)==row['sha256']))
    result.update(utc=datetime.now(timezone.utc).isoformat(),passed=result['passed'] and all(x['passed'] for x in result['checks']))
    return result

if __name__=='__main__':
    result=verify()
    with (P/'BASELINE_PRESERVATION.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps(dict(passed=result['passed'],files=len(result['checks']))));assert result['passed'] and len(result['checks'])==6093
