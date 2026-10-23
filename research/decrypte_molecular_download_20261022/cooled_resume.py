"""One five-minute-cooled probe, then sequential 30-second-spaced requests."""
import datetime as dt
import json
from pathlib import Path
import time
from download_development import fetch, ROOT, PHASE, OUT

manifest=PHASE/'DOWNLOAD_MANIFEST.json'
snapshot=OUT/'MANIFEST_BEFORE_COOLED_PROBE.json'
if snapshot.exists():
    raise RuntimeError('Refuse second execution')
snapshot.write_bytes(manifest.read_bytes())
metadata=json.loads(manifest.read_text())
records=metadata['records']
pending=[r for r in records if r['status']=='failed_preserved']
probe=next(r for r in pending if r['drug']=='CHM-1')
pending=[probe]+[r for r in pending if r is not probe]
assert len(pending)==38 and probe['attempt']==2
earliest=dt.datetime(2026,10,22,10,56,11,tzinfo=dt.timezone.utc)
def utc():
    return dt.datetime.now(dt.timezone.utc)
def wait_until(target):
    while (remaining:=(target-utc()).total_seconds())>0:
        print(json.dumps({'state':'cooldown_live','until_utc':target.isoformat(),'remaining_seconds':round(remaining)}),flush=True)
        time.sleep(min(20,remaining))
def save():
    temp=manifest.with_suffix('.tmp')
    temp.write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    temp.replace(manifest)
metadata.update(complete=False,cooled_resume={'earliest_probe_utc':earliest.isoformat(),
  'minimum_start_spacing_seconds':30,'first_non200_stop':True,'status':'cooling',
  'source_snapshot_path':snapshot.relative_to(ROOT).as_posix()},
  decoded_scope='CHDI00465983 accidentally exposed full-dose development payload; no other molecular numerical decoding by download agent')
save()
wait_until(earliest)
next_start=utc()
for original in pending:
    wait_until(next_start)
    started=utc()
    metadata['cooled_resume']['status']='requesting'
    save()
    base=original['index']%1000
    retry=fetch(2000+base,original)
    retry['attempt']=original['attempt']+1
    retry['previous_attempt']={'body_path':original['body_path'],'sha256':original['sha256'],
      'receipt_path':(OUT/f"{original['index']:03d}.receipt.json").relative_to(ROOT).as_posix(),
      'http_code':original['http_code'],'previous_attempt':original.get('previous_attempt')}
    (OUT/f"{retry['index']:03d}.receipt.json").write_text(json.dumps(retry,indent=2),encoding='utf-8')
    records[records.index(original)]=retry
    metadata['success_count']=sum(r['status'] in ('downloaded_unparsed','reused_archived_unparsed') for r in records)
    save()
    print(json.dumps({'drug':retry['drug'],'status':retry['status'],'http':retry['http_code'],'success_count':metadata['success_count']}),flush=True)
    if retry['status']!='downloaded_unparsed':
        metadata['cooled_resume']['status']='stopped_non200'
        metadata['cooled_resume']['stopped_utc']=utc().isoformat()
        save()
        break
    next_start=started+dt.timedelta(seconds=30)
else:
    metadata['cooled_resume'].update(status='complete',completed_utc=utc().isoformat())
metadata['complete']=all(r['status'] in ('downloaded_unparsed','reused_archived_unparsed') for r in records)
save()
