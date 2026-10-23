from pathlib import Path
import hashlib
import json

root = Path('D:/MAESTRO')
out = root / 'log/20261023/action_rule_search/biology'
paths = [out / 'CROSS.md', out / 'POSTSEAL_SOURCE_ADDENDUM.md',
         root / 'research/biological_residual_gate_20261019/REPORT.md',
         root / 'log/20261023/action_rule_search/constructive/INDEPENDENT.md',
         root / 'log/20261023/action_rule_search/constructive/INDEPENDENT_SEAL.json',
         Path(__file__)]
records = []
for p in paths:
    b = p.read_bytes()
    records.append({'path': str(p), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()})
(out / 'CROSS_SEAL.json').write_text(json.dumps({'files': records}, indent=2), encoding='utf-8')
print('Cross review sealed; original independent files preserved.')
