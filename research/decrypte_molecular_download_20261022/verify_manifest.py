"""Verify download bytes and protected-partition exclusion, without data decoding."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PHASE=ROOT/'log/20261022/decrypte_molecular_increment'
manifest=json.loads((PHASE/'DOWNLOAD_MANIFEST.json').read_text())
parts=json.loads((ROOT/'log/20261022/decrypte_feedback_pilot/PARTITIONS.json').read_text())['partitions']
records=manifest['records']
assert len(records)==48
assert {r['drug'] for r in records}==set(parts['development'])
assert not ({r['drug'] for r in records}&set(parts['selection']+parts['later']))
checked=[]
for r in records:
    path=ROOT/r['path']
    assert path.stat().st_size==r['bytes']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==r['sha256']
    if r['status']=='downloaded_unparsed':
        assert r['http_code']=='200' and 1024<r['bytes']<=16*1024*1024
    elif r['status']=='failed_preserved':
        assert r['http_code']=='429' and r['bytes']==227
    else:
        assert r['status']=='reused_archived_unparsed' and r['drug']=='(+)-JQ-1'
    checked.append({'drug':r['drug'],'status':r['status'],'path':r['path'],'sha256':r['sha256']})
result={'scope':'48 current manifest paths/hash/status and disjoint-partition checks only; no numerical decoding',
    'status':'PASS','usable':sum(r['status']!='failed_preserved' for r in records),'failed':sum(r['status']=='failed_preserved' for r in records),'checked':checked}
(PHASE/'downloads/DOWNLOAD_VERIFICATION.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='checked'}))
