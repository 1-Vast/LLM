"""One bounded paced correction for archived HTTP429 failures; stop on recurrence."""
import datetime as dt
import json
from pathlib import Path
import time
from download_development import fetch, ROOT, PHASE, OUT

manifest=PHASE/'DOWNLOAD_MANIFEST.json'
metadata=json.loads(manifest.read_text())
records=metadata['records']
for row in records:
    row['path']=row['body_path']
failed=[r for r in records if r['status']=='failed_preserved']
assert all(r['http_code']=='429' for r in failed)
assert all(r['attempt']==1 for r in failed)
metadata.update(complete=False,rate_limit_correction='one sequential second attempt, minimum 10 seconds between starts, stop immediately on any non200')
def save():
    temp=manifest.with_suffix('.tmp')
    temp.write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    temp.replace(manifest)
save()
last=0
for original in failed:
    pause=max(0,10-(time.monotonic()-last))
    time.sleep(pause)
    last=time.monotonic()
    retry=fetch(original['index']+1000,original)
    retry['attempt']=2
    retry['previous_attempt']={'body_path':original['body_path'],'sha256':original['sha256'],'receipt_path':str((OUT/f"{original['index']:03d}.receipt.json").relative_to(ROOT)).replace('\\','/'),'http_code':'429'}
    receipt=OUT/f"{retry['index']:03d}.receipt.json"
    receipt.write_text(json.dumps(retry,indent=2),encoding='utf-8')
    records[records.index(original)]=retry
    save()
    print(json.dumps({'drug':retry['drug'],'status':retry['status'],'http':retry['http_code']}),flush=True)
    if retry['status']!='downloaded_unparsed':
        metadata['rate_limit_correction_stopped']=True
        break
metadata.update(complete=all(r['status'] in ('downloaded_unparsed','reused_archived_unparsed') for r in records),success_count=sum(r['status'] in ('downloaded_unparsed','reused_archived_unparsed') for r in records))
save()
