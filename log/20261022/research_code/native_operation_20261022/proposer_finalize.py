from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

root = Path('D:/MAESTRO')
out = root / 'log/20261022/native_operation/proposer'
seal = json.loads((out / 'INITIAL_SEAL.json').read_text(encoding='utf-8'))
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
checks = []
for record in seal['own_artifacts']:
    checks.append({'path': record['path'], 'unchanged': digest(Path(record['path'])) == record['sha256']})
if not all(row['unchanged'] for row in checks):
    raise RuntimeError('Initial sealed artifact changed')
peers = [
    root / 'log/20261022/native_operation/improver/OPPOSING_STENCIL_INITIAL.md',
    root / 'log/20261022/native_operation/improver/OPPOSING_STENCIL_SEAL.json',
    root / 'log/20261022/native_operation/improver/INDEPENDENT_INITIAL.md',
    root / 'log/20261022/native_operation/biology/INDEPENDENT_POSITION.md',
    root / 'log/20261022/native_operation/root/SOURCE_READING.md',
    root / 'log/20261022/intervention_dynamics_renewal/advocate/ADVOCATE.md',
]
files = sorted(p for p in out.rglob('*') if p.is_file())
files += sorted((root / 'research/native_operation_20261022').glob('proposer_*.py'))
def records(paths):
    return [{'path': str(p), 'bytes': p.stat().st_size, 'sha256': digest(p)} for p in paths]
payload = dict(utc=datetime.now(timezone.utc).isoformat(), initial_artifact_checks=checks,
               postseal_read_inputs=records(peers), own_final_artifacts=records(files),
               exact_algebra_cases=29, predictive_fits=0, biological_assay_fields_read=0,
               new_wet_lab_experiments=0, reserve_accesses=0, deepseek_calls=0,
               decision='STOP literal candidate as novel core; retain scoped conventional hypothesis',
               goal='ACTIVE / NOT_ACHIEVED')
with (out / 'FINAL_SEAL.json').open('x', encoding='utf-8') as f:
    json.dump(payload, f, indent=2)
print(json.dumps({'final_seal': str(out / 'FINAL_SEAL.json'), 'sha256': digest(out / 'FINAL_SEAL.json'), 'initial_artifacts_unchanged': len(checks), 'final_artifacts': len(files)}))
