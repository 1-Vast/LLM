"""Download frozen 48-development resources without decoding biological values."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2]
PHASE=ROOT/'log/20261022/decrypte_molecular_increment'
OUT=PHASE/'downloads'
JOIN=ROOT/'log/20261022/decrypte_feedback_pilot/MOLECULAR_DOWNLOAD_JOIN.json'
PART=ROOT/'log/20261022/decrypte_feedback_pilot/PARTITIONS.json'
OLD=ROOT/'log/20261022/decrypte_feedback_pilot/molecular'
MAX_BYTES=16*1024*1024

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def fetch(index, row):
    key=f'{index:03d}'
    body=OUT/(key+'.body')
    receipt=OUT/(key+'.receipt.json')
    headers=OUT/(key+'.headers')
    if any(p.exists() for p in (body,receipt,headers)):
        raise RuntimeError('Refuse overwrite '+key)
    record=dict(row, index=index, request_utc=now(), decoded_scope='no biological rows or headers decoded',
                tls='Windows curl Schannel default verification', max_bytes=MAX_BYTES, max_seconds=60,
                attempt=1, body_path=body.relative_to(ROOT).as_posix(), path=body.relative_to(ROOT).as_posix(),
                headers_path=headers.relative_to(ROOT).as_posix())
    start=time.monotonic()
    result=subprocess.run(['curl.exe','--silent','--show-error','--location','--max-time','60',
        '--max-filesize',str(MAX_BYTES),'--dump-header',str(headers),'--output',str(body),
        '--write-out','%{http_code}',row['url']],capture_output=True,text=True,timeout=70)
    record.update(elapsed_seconds=time.monotonic()-start, completed_utc=now(),exit_code=result.returncode,
                  stderr=result.stderr,http_code=result.stdout.strip())
    if body.exists():
        record.update(bytes=body.stat().st_size,sha256=sha(body))
    record['status']='downloaded_unparsed' if result.returncode==0 and result.stdout.strip()=='200' and 0<body.stat().st_size<=MAX_BYTES else 'failed_preserved'
    receipt.write_text(json.dumps(record,indent=2),encoding='utf-8')
    return record

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=PHASE/'DOWNLOAD_MANIFEST.json'
    if manifest.exists():
        raise RuntimeError('Refuse overwrite existing run')
    joins=json.loads(JOIN.read_text())['records']
    partitions=json.loads(PART.read_text())['partitions']
    rows=[r for r in joins if r['partition']=='development']
    assert len(rows)==48 and {r['drug'] for r in rows}==set(partitions['development'])
    assert not ({r['drug'] for r in rows}&set(partitions['selection']+partitions['later']))
    assert len({r['descriptor'] for r in rows})==48
    assert all('/TXTs_Classified/' in r['descriptor'] and '/sequence/' not in r['descriptor'] and r['repository_bytes']<=MAX_BYTES for r in rows)
    old_body=OLD/'jurkat_jq1.body'
    old_receipt=json.loads((OLD/'jurkat_jq1.receipt.json').read_text())
    assert sha(old_body)==old_receipt['sha256']
    jq=next(r for r in rows if r['drug']=='(+)-JQ-1')
    assert jq['descriptor']==old_receipt['descriptor']
    records=[dict(jq,status='reused_archived_unparsed',body_path=old_body.relative_to(ROOT).as_posix(),path=old_body.relative_to(ROOT).as_posix(),
        bytes=old_body.stat().st_size,sha256=sha(old_body),
        original_receipt_path=(OLD/'jurkat_jq1.receipt.json').relative_to(ROOT).as_posix(),
        decoded_scope='existing source qualification header only; no new decode')]
    metadata={'scope':'48 development files only, 47 requests plus one archived reuse; no molecular values decoded',
       'started_utc':now(),'partition_sha256':sha(PART),'join_sha256':sha(JOIN),
       'workers':4,'records':records,'complete':False}
    def save():
        metadata['records']=sorted(records,key=lambda r:r['drug'])
        temp=manifest.with_suffix('.tmp')
        temp.write_text(json.dumps(metadata,indent=2),encoding='utf-8')
        temp.replace(manifest)
    save()
    pending=[r for r in rows if r['drug']!='(+)-JQ-1']
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(fetch,i,r):r for i,r in enumerate(pending,1)}
        for future in as_completed(futures):
            record=future.result()
            records.append(record)
            save()
            print(json.dumps({'completed':len(records),'drug':record['drug'],'status':record['status'],'bytes':record.get('bytes')},ensure_ascii=False),flush=True)
    metadata.update(complete=True,completed_utc=now(),
       success_count=sum(r['status'] in ('downloaded_unparsed','reused_archived_unparsed') for r in records))
    save()
    print(json.dumps({'complete':True,'success_count':metadata['success_count']}),flush=True)

if __name__=='__main__':
    main()
