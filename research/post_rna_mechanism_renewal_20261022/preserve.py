"""Verify all finalized predecessors, including the completed RNA pilot."""
import hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'log/20261022/post_rna_mechanism_renewal'
OLD=ROOT/'research/tggates_rna_feedback_pilot_20261022/preserve.py'

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def verify():
    spec=importlib.util.spec_from_file_location('rna_predecessor_preserve',OLD)
    previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
    prior=previous.verify();checks=prior['checks']
    manifest=ROOT/'log/20261022/tggates_rna_feedback_pilot/FINAL_FILE_INVENTORY.json'
    hashes=dict(prior['manifest_sha256']);hashes[manifest.relative_to(ROOT).as_posix()]=sha(manifest)
    for row in json.loads(manifest.read_text())['files']:
        path=ROOT/row['path']
        checks.append(dict(path=row['path'],passed=path.is_file() and path.stat().st_size==row['bytes'] and sha(path)==row['sha256']))
    return dict(utc=datetime.now(timezone.utc).isoformat(),passed=prior['passed'] and all(c['passed'] for c in checks),checks=checks,manifest_sha256=hashes)

def main():
    P.mkdir(parents=True,exist_ok=True);result=verify()
    with (P/'BASELINE_PRESERVATION.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps(dict(passed=result['passed'],files=len(result['checks']))));assert result['passed']

if __name__=='__main__':main()
