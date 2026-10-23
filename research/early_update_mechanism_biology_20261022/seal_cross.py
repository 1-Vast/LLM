"""Seal post-independent cross-review with exact peer/math evidence bindings."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json

root=Path('D:/MAESTRO')
out=root/'log/20261022/early_update_mechanism/biology'
phase=out.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=json.loads((out/'INDEPENDENT_SEAL.json').read_text(encoding='utf-8'))
for item in prior['files']:
    assert sha(root/item['path'])==item['sha256'],'Independent evidence changed'
sources=[phase/'frontier/PROPOSAL.md',phase/'recursive/PROPOSAL.md',phase/'api/RESPONSE.md',
         phase/'API_FALSIFIER_RESULT.json',phase/'ROOT_MATH_RESULT.json']
paths=[out/'CROSS_REVIEW.md',Path(__file__).resolve()]
seal=out/'CROSS_REVIEW_SEAL.json'
assert not seal.exists()
seal.write_text(json.dumps(dict(created_utc=datetime.now(timezone.utc).isoformat(),
    independent_files_verified=len(prior['files']),independent_seal_sha256=sha(out/'INDEPENDENT_SEAL.json'),
    other_drafts_read_after_independent_seal=True,peer_questions_and_responses_exchanged=True,
    new_public_requests=0,new_biological_values_read=False,new_experiment_run=False,
    files=[dict(path=str(p.relative_to(root)),sha256=sha(p)) for p in paths],
    reviewed_sources=[dict(path=str(p.relative_to(root)),sha256=sha(p)) for p in sources]),indent=2),encoding='utf-8')
print(json.dumps(dict(report_sha256=sha(paths[0]),seal_sha256=sha(seal),independent_files_unchanged=len(prior['files']))))
