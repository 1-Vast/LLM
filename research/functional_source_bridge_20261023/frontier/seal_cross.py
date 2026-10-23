from pathlib import Path
import hashlib, json
root = Path('log/20261023/functional_source_bridge/frontier')
paths = [root / 'CROSS.md', Path(__file__)]
checks = []
for seal in ('VERIFICATION.json', 'ADDENDUM_SEAL.json'):
    content = json.loads((root / seal).read_text(encoding='utf8'))
    records = content['files'] if isinstance(content, dict) else content
    checks += [{'seal': seal, 'path': r['path'], 'matches': hashlib.sha256(Path(r['path']).read_bytes()).hexdigest() == r['sha256']} for r in records]
assert all(r['matches'] for r in checks)
(root / 'CROSS_SEAL.json').write_text(json.dumps({'files': [{'path': p.as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths], 'prior_checks': checks}, indent=2), encoding='utf8')
print({'prior_files_checked': len(checks), 'drift': 0})
