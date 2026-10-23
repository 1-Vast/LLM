from pathlib import Path
import hashlib
import json

root = Path('D:/MAESTRO')
paths = [root / 'log/20261023/action_rule_search/biology/FRONTIER_CROSS.md',
         root / 'log/20261023/action_rule_search/frontier/INDEPENDENT.md', Path(__file__)]
rows = []
for p in paths:
    b = p.read_bytes()
    rows.append({'path': str(p), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()})
(root / 'log/20261023/action_rule_search/biology/FRONTIER_CROSS_SEAL.json').write_text(
    json.dumps({'files': rows}, indent=2), encoding='utf-8')
print('Frontier cross boundary review sealed.')
