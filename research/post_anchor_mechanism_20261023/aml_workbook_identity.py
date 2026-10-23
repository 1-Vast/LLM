"""Acquire author-named source workbooks; inspect sheet identities only."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile
import requests

OUT=Path(__file__).resolve().parents[2]/'log/20261023/post_anchor_mechanism/root_sources'
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def fetch(number):
    filename=f'41467_2026_74989_MOESM{number}_ESM.xlsx'
    url='https://static-content.springer-cdn.com/esm/art%3A10.1038%2Fs41467-026-74989-8/MediaObjects/'+filename
    rec=dict(url=url,utc=datetime.now(timezone.utc).isoformat(),inspection='workbook sheet identities only; no worksheet cells')
    try:
        r=requests.get(url,timeout=40)
        body=r.content
        (OUT/filename).write_bytes(body)
        rec.update(status=r.status_code,bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
        if r.ok and zipfile.is_zipfile(io.BytesIO(body)):
            with zipfile.ZipFile(io.BytesIO(body)) as archive:
                workbook=ET.fromstring(archive.read('xl/workbook.xml'))
                rec['sheets']=[dict(s.attrib) for s in workbook.findall('s:sheets/s:sheet',NS)]
                rec['members']=[dict(name=i.filename,size=i.file_size) for i in archive.infolist()
                                if i.filename.startswith('xl/worksheets/sheet') and i.filename.endswith('.xml')]
    except Exception as error:rec.update(error_type=type(error).__name__,error=str(error))
    (OUT/f'aml_workbook{number}.receipt.json').write_text(json.dumps(rec,indent=2),encoding='utf-8')
    return rec
if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=2) as pool: print(json.dumps(list(pool.map(fetch,[3,6])),indent=2))
