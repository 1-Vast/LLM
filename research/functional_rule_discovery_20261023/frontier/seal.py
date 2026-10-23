import hashlib,json
from pathlib import Path
out=Path('log/20261023/functional_rule_discovery/frontier')
paths=[p for p in out.iterdir() if p.is_file() and p.name!='INDEPENDENT_SEAL.json']
paths+=list(Path('research/functional_rule_discovery_20261023/frontier').glob('*.py'))
entries=[dict(path=p.as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(paths)]
(out/'INDEPENDENT_SEAL.json').write_text(json.dumps(dict(scope='independent original before current peer report reads',files=entries),indent=2),encoding='utf-8')
print(len(entries))
