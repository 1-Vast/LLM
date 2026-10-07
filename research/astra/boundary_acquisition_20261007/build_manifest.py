"""Manifest canonical/superseded worker assets without changing science records."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def main():
    excluded={'RUN_MANIFEST.json','FINAL_VERIFICATION.json','README.md','NEXT_EXPERIMENT.md'}
    worker_top={'register.py','method.py','execute.py','test_boundary.py','DRAFT_PROTOCOL.json',
        'PROTOCOL.json','FREEZE.json','AUDIT_RUNNER_FREEZE.json','run_registered.py',
        'SUPERSEDED_AUDIT_RECEIPT.json','SOURCE_ORDERING_RECEIPT.json',
        'reconstruct_review.py','REVIEW_DELTA_RECONSTRUCTION.json','study_tests.xml',
        'REPORT.md','build_manifest.py'}
    worker_directories={'packet1','packet2','run1'}
    assets=[]
    for path in sorted(HERE.rglob('*')):
        if (not path.is_file() or '__pycache__' in path.parts or path.name in excluded
                or path.name.endswith(('-wal','-shm'))):continue
        relative=path.relative_to(HERE)
        if not ((len(relative.parts)==1 and path.name in worker_top)
                or relative.parts[0] in worker_directories):continue
        assets.append(dict(path=str(path.relative_to(ROOT)).replace('\\','/'),bytes=path.stat().st_size,
                           sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    manifest=dict(created_utc=datetime.now(timezone.utc).isoformat(),schema='boundary_worker_run_manifest_v1',
        canonical_packet='packet2',canonical_run='run1',superseded_packet='packet1 audit-only build; no policy replay',
        protocol_sha256=hashlib.sha256((HERE/'PROTOCOL.json').read_bytes()).hexdigest(),
        assets=assets,upstream_pins_in='PROTOCOL.json',
        root_managed_excluded=sorted(excluded),
        science=dict(episodes=60,paidprofiles=765,commoncap=780,exposed_target_contexts=5,
                     STATE_weights_changed=False,api_calls=0,new_wet_experiments=0,fresh_inference=0))
    with (HERE/'RUN_MANIFEST.json').open('w',encoding='utf-8') as f:
        json.dump(manifest,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
    print(json.dumps(dict(assets=len(assets),bytes=sum(r['bytes'] for r in assets))))


if __name__=='__main__':main()
