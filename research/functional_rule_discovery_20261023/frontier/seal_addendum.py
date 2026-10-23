import hashlib,json
from pathlib import Path
out=Path('log/20261023/functional_rule_discovery/frontier')
for sealname in ['INDEPENDENT_SEAL.json','CROSS_SEAL.json']:
    for e in json.loads((out/sealname).read_text(encoding='utf-8'))['files']:
        assert hashlib.sha256(Path(e['path']).read_bytes()).hexdigest()==e['sha256']
paths=[p for p in out.iterdir() if p.is_file() and p.name!='ADDENDUM_SEAL.json']
paths+=list(Path('research/functional_rule_discovery_20261023/frontier').glob('*.py'))
items=[dict(path=p.as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(paths)]
(out/'ADDENDUM_SEAL.json').write_text(json.dumps(dict(scope='late constructive reciprocal; old12/15entries verified unchanged',files=items),indent=2),encoding='utf-8')
print(len(items))
