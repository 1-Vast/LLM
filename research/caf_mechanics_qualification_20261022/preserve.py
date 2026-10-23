"""Verify all finalized predecessor phases including the latest proposal round."""
import hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'log/20261022/caf_mechanics_qualification'

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def verify():
    spec=importlib.util.spec_from_file_location('renewal_predecessor',ROOT/'research/post_rna_mechanism_renewal_20261022/preserve.py')
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);prior=old.verify()
    manifest=ROOT/'log/20261022/post_rna_mechanism_renewal/FINAL_FILE_INVENTORY.json'
    hashes=dict(prior['manifest_sha256']);hashes[manifest.relative_to(ROOT).as_posix()]=sha(manifest)
    checks=prior['checks']
    for row in json.loads(manifest.read_text())['files']:
        path=ROOT/row['path'];checks.append(dict(path=row['path'],passed=path.is_file() and path.stat().st_size==row['bytes'] and sha(path)==row['sha256']))
    return dict(utc=datetime.now(timezone.utc).isoformat(),passed=prior['passed'] and all(row['passed'] for row in checks),checks=checks,manifest_sha256=hashes)

if __name__=='__main__':
    result=verify()
    with (P/'BASELINE_PRESERVATION.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps(dict(passed=result['passed'],files=len(result['checks']))));assert result['passed']
