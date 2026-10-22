"""Independently verify retained source bytes and the scoped gain counterexample."""
from pathlib import Path
from fractions import Fraction
import hashlib
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/frontier_mechanism_renewal'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

seal = json.loads((OUT / 'INDEPENDENT_INITIAL_SEAL.json').read_text())
checks = [{'kind': 'initial_binding', 'path': name, 'passed': sha(Path(name)) == expected}
          for name, expected in seal['files'].items()]
receipts = sorted((OUT / 'sources').glob('*.receipt.json'))
for path in receipts:
    receipt = json.loads(path.read_text())
    body = path.with_name(path.name.replace('.receipt.json', '.body'))
    checks.append({'kind': 'http_body', 'path': body.relative_to(ROOT).as_posix(),
                   'passed': receipt['status'] == 200 and body.stat().st_size == receipt['bytes'] and sha(body) == receipt['sha256']})
algebra = json.loads((OUT / 'ALGEBRA_RESULT.json').read_text())
for example in algebra['examples']:
    truth = Fraction(example['query_y'])
    before = truth * truth / 2
    after = (truth - 1) * (truth - 1) / 2
    checks.append({'kind': 'exact_gain', 'query_y': str(truth), 'passed': before - after == Fraction(example['query_gain'])})
assert len(receipts) == 13
assert all(row['passed'] for row in checks)
result = {'utc': datetime.now(timezone.utc).isoformat(), 'status': 'PASS', 'checks': checks,
          'initial_bound_files': len(seal['files']), 'http_sources': len(receipts),
          'scientific_limit': 'A finite support cannot universally identify update gain; this does not rule out population learning or biologically structured support.'}
with (OUT / 'INDEPENDENT_SOURCE_AUDIT.json').open('x', encoding='utf-8') as handle:
    json.dump(result, handle, indent=2)
print(json.dumps({'status': result['status'], 'checks': len(checks), 'http_sources': len(receipts)}))
