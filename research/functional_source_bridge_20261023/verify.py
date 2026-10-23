"""Verify actual source bytes, independent seals and bounded identity claims."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'log/20261023/functional_source_bridge'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def seal(path):
    obj=json.loads(path.read_text(encoding='utf-8'))
    rows=obj if isinstance(obj,list) else obj['files']
    if isinstance(rows,dict):
        rows=[dict(path=p,sha256=h) for p,h in rows.items()]
    for row in rows:
        p=Path(row['path'])
        if not p.is_absolute():
            p=ROOT/p
        assert sha(p)==row['sha256'],(str(path),str(p))
    return len(rows)


if __name__=='__main__':
    target=OUT/'VERIFICATION.json'
    assert not target.exists()
    paths=[ROOT/'log/20261023/hcc_link_recovery/VERIFICATION.json',
           OUT/'growth/EVIDENCE.json',OUT/'frontier/VERIFICATION.json']
    paths+=sorted(OUT.rglob('*seal.json'))+sorted(OUT.rglob('*SEAL.json'))
    checked=[dict(path=p.relative_to(ROOT).as_posix(),files=seal(p)) for p in paths]
    count=0
    for p in OUT.rglob('*.receipt.json'):
        row=json.loads(p.read_text(encoding='utf-8'))
        body=p.with_name(p.name.replace('.receipt.json','.body'))
        assert body.is_file() and sha(body)==row['sha256'],str(p)
        assert body.stat().st_size==row.get('bytes',row.get('body_bytes')),str(p)
        count+=1
    assert count==19,count
    root=json.loads((OUT/'root/IDENTITY_JOIN.json').read_text())
    independent=json.loads((OUT/'growth/IDENTITY_JOIN_INDEPENDENT.json').read_text())
    for key in ['state_columns','state_unique','function_rows','function_unique','matched','state_only','function_only']:
        assert root[key]==independent[key],key
    assert root['matched']==1593 and len(root['function_only'])==7
    files={p.relative_to(ROOT).as_posix():sha(p) for base in [OUT,ROOT/'research/functional_source_bridge_20261023']
           for p in sorted(base.rglob('*')) if p.is_file() and p!=target}
    audit=dict(scope='source identity and selected code operations; not biological performance or full archive hashes',
               prior_seals=checked,http_receipts=count,files=files,goal='ACTIVE / NOT_ACHIEVED')
    target.write_text(json.dumps(audit,indent=2),encoding='utf-8')
    assert all(sha(ROOT/p)==h for p,h in files.items())
    print(json.dumps(dict(files=len(files),drift=0,http_receipts=count,matched_identifiers=1593)))
