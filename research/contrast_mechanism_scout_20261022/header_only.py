"""Read only the first CSV line of two newly identified public study files."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,csv,io
import requests
root=Path('D:/MAESTRO/log/20261022/contrast_mechanism_scout')
meta=json.loads((root/'sources/batchie_prospective_metadata.body').read_text())
records=[]
for item in meta['files']:
    label=item['key'].split('.')[0].lower()
    url=item['links']['self']
    rec=dict(file=item['key'],url=url,utc=datetime.now(timezone.utc).isoformat(),request_range='bytes=0-2047',scope='First CSV line only. No outcome rows decoded, parsed, converted or fitted.',advertised_full_bytes=item['size'],advertised_full_checksum=item['checksum'])
    try:
        with requests.get(url,headers={'Range':'bytes=0-2047'},stream=True,timeout=60) as response:
            rec.update(status=response.status_code,headers=dict(response.headers),final_url=response.url)
            first=response.raw.readline(8192)
        (root/'sources'/(label+'.header')).write_bytes(first)
        rec.update(retained_header_bytes=len(first),header_sha256=hashlib.sha256(first).hexdigest(),columns=next(csv.reader(io.StringIO(first.decode('utf-8-sig')))))
        rec['full_checksum_verified']=False
        rec['transport_buffer_bytes']='NOT_MEASURED; connection closed after first-line read'
    except Exception as exc:rec['error_type']=type(exc).__name__
    (root/'sources'/(label+'.header.receipt.json')).write_text(json.dumps(rec,indent=2),encoding='utf-8')
    records.append(rec)
(root/'HEADER_QUALIFICATION.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print(json.dumps([{k:v for k,v in r.items() if k!='headers'} for r in records],indent=2))
