"""Verify owned sources and API records before sealing the scout's own opinion."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
root=Path('D:/MAESTRO/log/20261022/contrast_mechanism_scout')
checks=[]
for p in sorted((root/'sources').glob('*.receipt.json')):
    r=json.loads(p.read_text(encoding='utf-8'))
    if p.name.endswith('.header.receipt.json'):
        body=p.with_name(p.name.replace('.receipt.json',''))
        assert hashlib.sha256(body.read_bytes()).hexdigest()==r['header_sha256']
        checks.append(dict(file=p.name,status=r['status'],scope='HEADER_ONLY',bytes=len(body.read_bytes())))
    else:
        body=root/'sources'/(r['label']+'.body')
        assert len(body.read_bytes())==r['bytes']
        assert hashlib.sha256(body.read_bytes()).hexdigest()==r['sha256']
        checks.append(dict(file=p.name,status=r['status'],scope='FULL_HTTP_RESPONSE',bytes=r['bytes']))
usage=[]
for folder in ['api','api_direct']:
    d=root/folder
    r=json.loads((d/'RECEIPT.json').read_text(encoding='utf-8'))
    response=d/'RESPONSE.md'
    logical=response.read_text(encoding='utf-8')
    assert hashlib.sha256(logical.encode()).hexdigest()==r['response_sha256']
    usage.append(dict(directory=folder,status=r['status'],model=r['model'],finish_reason=r['finish_reason'],usage=r['usage'],logical_response_sha256=r['response_sha256'],raw_response_sha256=hashlib.sha256(response.read_bytes()).hexdigest(),visible_characters=len(logical)))
report=dict(utc=datetime.now(timezone.utc).isoformat(),sources=checks,api=usage,total_provider_tokens=sum(x['usage']['total_tokens'] for x in usage),biological_fits=0,protected_outcomes=0,opposing_positions_read=0)
(root/'INITIAL_VERIFICATION.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
files=[]
for folder in ['sources','api','api_direct']:
    files.extend(p for p in (root/folder).rglob('*') if p.is_file())
for name in ['INDEPENDENT_INITIAL.md','FAILURES.md','SEARCH_RESULTS.json','TASKBANK_EXCERPTS.txt','SOURCE_INSPECTION.json','HEADER_QUALIFICATION.json','ALGEBRA_RESULT.json','INITIAL_VERIFICATION.json']:
    files.append(root/name)
files.extend(Path('D:/MAESTRO/research/contrast_mechanism_scout_20261022').glob('*.py'))
seal=dict(utc=datetime.now(timezone.utc).isoformat(),scope='Own independent initial opinion; root dispatch and unseen peer/opposing artifacts excluded',files={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)})
(root/'INDEPENDENT_INITIAL_SEAL.json').write_text(json.dumps(seal,indent=2),encoding='utf-8')
print(json.dumps(dict(files_sealed=len(files),source_receipts=len(checks),api_tokens=report['total_provider_tokens'],status='PASS')))
