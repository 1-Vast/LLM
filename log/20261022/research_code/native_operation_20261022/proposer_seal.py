from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

root = Path('D:/MAESTRO')
out = root / 'log/20261022/native_operation/proposer'
inputs = [
    Path('C:/Users/59964/.codex/attachments/45d9c2f9-b12a-4e71-bd4a-9f6cc5eb5ce9/goal-objective.md'),
    root / 'research/REPORT.md',
    root / 'log/20261022/cipa_control_information/PROJECT_CAPABILITY_AUDIT.md',
    root / 'log/20261022/mse_source_gate/DECISION.md',
    root / 'log/20261022/mse_source_gate/CONTINUATION.md',
    root / 'log/20261022/intervention_schedule_qualification/DECISION.md',
]
own = list((out / 'sources').glob('*')) + [out / 'INDEPENDENT_INITIAL.md', out / 'FAILURES.md']
own += list((root / 'research/native_operation_20261022').glob('proposer_*.py'))
def records(paths):
    return [{'path': str(p), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)]
payload = {'utc': datetime.now(timezone.utc).isoformat(), 'current_peer_files_read': [], 'inputs': records(inputs), 'own_artifacts': records(own), 'requested_model': 'gpt-6-astra', 'requested_effort': 'high', 'independent_backend_attestation': False, 'assay_conversions': 0, 'predictive_fits': 0}
with (out / 'INITIAL_SEAL.json').open('x', encoding='utf-8') as f:
    json.dump(payload, f, indent=2)
print(json.dumps({'seal': str(out / 'INITIAL_SEAL.json'), 'sha256': hashlib.sha256((out / 'INITIAL_SEAL.json').read_bytes()).hexdigest(), 'artifacts': len(own), 'inputs': len(inputs)}))
