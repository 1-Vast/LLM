"""Summarize archived request receipts, never molecular data rows."""
import collections
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PHASE=ROOT/'log/20261022/decrypte_molecular_increment'
OUT=PHASE/'downloads'
manifest=PHASE/'DOWNLOAD_MANIFEST.json'
inventory=json.loads(manifest.read_text())
assert inventory['complete'] and inventory['success_count']==48
receipts=[]
for path in sorted(OUT.glob('*.receipt.json')):
    r=json.loads(path.read_text())
    r['receipt_path']=path.relative_to(ROOT).as_posix()
    r['receipt_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    receipts.append(r)
def group(rows):
    return {'requests':len(rows),'http_status_counts':dict(collections.Counter(r['http_code'] for r in rows)),
            'received_bytes':sum(r.get('bytes',0) for r in rows),
            'sum_request_elapsed_seconds':sum(r['elapsed_seconds'] for r in rows)}
first=min(dt.datetime.fromisoformat(r['request_utc']) for r in receipts)
last=max(dt.datetime.fromisoformat(r['completed_utc']) for r in receipts)
cooled=sorted((r for r in receipts if r['index']>=2000),key=lambda r:r['request_utc'])
gaps=[(dt.datetime.fromisoformat(b['request_utc'])-dt.datetime.fromisoformat(a['request_utc'])).total_seconds() for a,b in zip(cooled,cooled[1:])]
result={'scope':'new phase requests only; preexisting JQ1 resource reused without network request',
  'metadata_only':True,'total':group(receipts),
  'initial':group([r for r in receipts if r['index']<1000]),
  'explicit_retry':group([r for r in receipts if 1000<=r['index']<2000]),
  'cooled_resume':group(cooled),
  'earliest_request_utc':first.isoformat(),'latest_completed_utc':last.isoformat(),
  'request_wall_span_seconds':(last-first).total_seconds(),
  'cooled_minimum_start_spacing_seconds':min(gaps),
  'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),
  'usable_current_body_bytes':sum(r['bytes'] for r in inventory['records']),
  'new_success_body_bytes':sum(r['bytes'] for r in receipts if r['http_code']=='200'),
  'failed_body_bytes':sum(r['bytes'] for r in receipts if r['http_code']!='200'),
  'native_usd_cost':'unavailable; no invented dollar estimate','native_tokens':'not applicable to HTTP downloads; no API inference calls',
  'exposure_incident':'downloads/EXPOSURE_INCIDENT.md; CHDI00465983 prefreeze development all-dose exposure; other successful bodies unparsed by downloading agent',
  'requests':[{k:r[k] for k in ('drug','index','attempt','http_code','bytes','request_utc','completed_utc','receipt_path','receipt_sha256')} for r in receipts]}
assert result['total']['requests']==86
assert result['total']['http_status_counts']=={'200':47,'429':39}
assert result['cooled_minimum_start_spacing_seconds']>=29.99
(OUT/'DOWNLOAD_COST_SUMMARY.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='requests'},indent=2))
