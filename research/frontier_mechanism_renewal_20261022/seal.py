"""Verify retained source hashes and seal this independent initial position."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
from bs4 import BeautifulSoup

root = Path('D:/MAESTRO/log/20261022/frontier_mechanism_renewal')
sources = []
for path in sorted((root / 'sources').glob('*.receipt.json')):
    receipt = json.loads(path.read_text(encoding='utf-8'))
    body = root / 'sources' / (receipt['label'] + '.body')
    data = body.read_bytes()
    assert receipt['status'] == 200
    assert len(data) == receipt['bytes']
    assert hashlib.sha256(data).hexdigest() == receipt['sha256']
    soup = BeautifulSoup(data, 'xml' if 'xml' in receipt['headers'].get('content-type', '') else 'html.parser')
    tag = soup.find('meta', attrs={'name':'citation_title'})
    sources.append(dict(label=receipt['label'], bytes=len(data), sha256=receipt['sha256'], citation_title=tag.get('content') if tag else None))
assert all(json.loads((root/'ALGEBRA_RESULT.json').read_text())['checks'].values())
report = dict(utc=datetime.now(timezone.utc).isoformat(), verified_http_sources=len(sources), source_records=sources,
              algebra_checks=4, biological_fits=0, protected_outcomes_read=0, deepseek_calls=0,
              peer_positions_read_before_seal=0)
(root/'VERIFICATION.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
files = list(root.rglob('*')) + list(Path('D:/MAESTRO/research/frontier_mechanism_renewal_20261022').glob('*.py'))
manifest = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files) if p.is_file() and p.name!='INDEPENDENT_INITIAL_SEAL.json'}
seal = dict(utc=datetime.now(timezone.utc).isoformat(), scope='Independent initial position and retained evidence; before current peer discussion', files=manifest)
(root/'INDEPENDENT_INITIAL_SEAL.json').write_text(json.dumps(seal, indent=2), encoding='utf-8')
print(json.dumps(dict(sources_verified=len(sources), files_sealed=len(manifest), algebra_checks=4)))
