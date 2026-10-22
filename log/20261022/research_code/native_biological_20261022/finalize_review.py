from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

root = Path('D:/MAESTRO')
out = root / 'log/20261022/native_operation/biology'
checks = []
for name, key in [('INDEPENDENT_SEAL.json', 'artifacts'), ('CROSS_CRITIQUE_SEAL.json', 'files')]:
    seal = json.loads((out / name).read_text(encoding='utf8'))
    for item in seal[key]:
        p = Path(item['path'])
        checks.append({'path': str(p), 'unchanged': hashlib.sha256(p.read_bytes()).hexdigest() == item['sha256']})
assert all(x['unchanged'] for x in checks)
target = out / 'FINAL_REVIEW_SEAL.json'
assert not target.exists()
paths = [p for d in [out, root / 'research/native_biological_20261022']
         for p in sorted(d.iterdir()) if p.is_file()]
target.write_text(json.dumps({
    'utc': datetime.now(timezone.utc).isoformat(),
    'initial_artifact_and_critique_checks': checks,
    'all_original_checks_passed': True,
    'new_source_requests_during_cross_review': 0,
    'biological_scalar_decodes': 0,
    'biological_fits': 0,
    'final_artifacts': [{'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],
}, indent=2), encoding='utf8')
print(json.dumps({'seal_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                  'original_checks': len(checks), 'final_artifacts': len(paths)}))
