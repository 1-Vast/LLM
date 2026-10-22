"""Verify this bounded scout and preserve its independent pre-review position."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/mse_mechanism_renewal'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
predecessors = json.loads((OUT / 'PREDECESSOR_SNAPSHOT.json').read_text(encoding='utf-8'))['predecessor_files']
for name, expected in predecessors.items():
    assert sha(Path(name)) == expected, name
sources = []
for path in sorted((OUT / 'sources').glob('*.receipt.json')):
    r = json.loads(path.read_text(encoding='utf-8'))
    body = OUT / 'sources' / (r['label'] + '.body')
    assert len(body.read_bytes()) == r['bytes']
    assert sha(body) == r['sha256']
    sources.append(dict(label=r['label'], status=r['status'], bytes=r['bytes']))
calls = []
for name in ['api_constructive', 'api_critique']:
    folder = OUT / name
    r = json.loads((folder / 'RECEIPT.json').read_text(encoding='utf-8'))
    prompt = (folder / 'PROMPT.md').read_text(encoding='utf-8')
    assert hashlib.sha256(prompt.encode()).hexdigest() == r['prompt_sha256']
    assert sha(folder / 'RESPONSE.md') == r['response_sha256']
    assert r['status'] == 'COMPLETE' and r['finish_reason'] == 'stop'
    assert r['logical_requests'] == 1
    calls.append(dict(directory=name, model=r['model'], usage=r['usage'],
                      response_sha256=r['response_sha256']))
algebra = json.loads((OUT / 'ALGEBRA_RESULT.json').read_text(encoding='utf-8'))
assert len(algebra['checks']) == 4 and all(c['passed'] for c in algebra['checks'])
verification = dict(utc=datetime.now(timezone.utc).isoformat(), status='PASS',
                    predecessors_unchanged=len(predecessors), source_receipts=sources,
                    api=calls, total_provider_tokens=sum(c['usage']['total_tokens'] for c in calls),
                    algebra_checks=4, mse_numeric_reads=0, biological_fits=0,
                    new_peer_mechanism_positions_read=0,
                    metadata_correction_received_after_both_calls=True)
with (OUT / 'INITIAL_VERIFICATION.json').open('x', encoding='utf-8') as f:
    json.dump(verification, f, indent=2)
files = sorted(p for p in OUT.rglob('*') if p.is_file())
files += sorted(Path(__file__).parent.glob('*.py'))
seal = dict(utc=datetime.now(timezone.utc).isoformat(), scope='Independent bounded single-candidate scout before peer review',
            decision='NO_VIABLE_NEW_CORE', files={str(p): sha(p) for p in files})
with (OUT / 'INDEPENDENT_SEAL.json').open('x', encoding='utf-8') as f:
    json.dump(seal, f, indent=2)
print(json.dumps(dict(status='PASS', files_sealed=len(files), predecessors_unchanged=len(predecessors),
                      algebra_checks=4, provider_tokens=verification['total_provider_tokens'])))
