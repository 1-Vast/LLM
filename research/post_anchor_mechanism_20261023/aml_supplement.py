"""One official supplementary-package route after CDN transport failures."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile
import requests

OUT=Path(__file__).resolve().parents[2]/'log/20261023/post_anchor_mechanism/root_sources'
url='https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13457605/supplementaryFiles'
rec=dict(url=url,utc=datetime.now(timezone.utc).isoformat(),limit_bytes=30_000_000,
         inspection='archive members and nested workbook sheet identities only; no worksheet cells')
try:
    with requests.get(url,timeout=45,stream=True) as response:
        rec.update(status=response.status_code,content_type=response.headers.get('Content-Type'))
        payload=bytearray()
        for part in response.iter_content(65536):
            if len(payload)+len(part)>rec['limit_bytes']:
                rec.update(stopped='SIZE_CAP',retained_prefix_bytes=len(payload))
                break
            payload.extend(part)
        else:
            rec['complete']=True
    body=bytes(payload)
    (OUT/'aml_supplement_package.body').write_bytes(body)
    rec.update(bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
    if rec.get('complete') and rec.get('status')==200 and zipfile.is_zipfile(io.BytesIO(body)):
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            rec['members']=[dict(name=i.filename,size=i.file_size) for i in archive.infolist()]
            rec['workbooks']=[]
            for info in archive.infolist():
                if info.filename.lower().endswith('.xlsx') and info.file_size<15_000_000:
                    workbook_bytes=archive.read(info.filename)
                    filename=Path(info.filename).name
                    (OUT/filename).write_bytes(workbook_bytes)
                    with zipfile.ZipFile(io.BytesIO(workbook_bytes)) as workbook:
                        xml=ET.fromstring(workbook.read('xl/workbook.xml'))
                    rec['workbooks'].append(dict(filename=filename,sha256=hashlib.sha256(workbook_bytes).hexdigest(),
                        sheets=[dict(s.attrib) for s in xml.findall('{*}sheets/{*}sheet')]))
except Exception as error:rec.update(error_type=type(error).__name__,error=str(error))
(OUT/'aml_supplement_package.receipt.json').write_text(json.dumps(rec,indent=2),encoding='utf-8')
print(json.dumps(rec,indent=2))
