"""Read official sample-level metadata to resolve biological/library units."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

OUT=Path(__file__).resolve().parents[2]/'log/20261023/post_anchor_mechanism/root_sources'
url='https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE289454&targ=all&form=text&view=full'
receipt=dict(url=url,utc=datetime.now(timezone.utc).isoformat(),scope='sample metadata only; no expression/lineage numeric payload')
try:
    response=requests.get(url,timeout=40)
    body=response.content
    (OUT/'aml_samples.body').write_bytes(body)
    receipt.update(status=response.status_code,bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
    samples=[]
    if response.ok:
        for line in response.text.splitlines():
            if line.startswith('^SAMPLE = '):samples.append(dict(id=line.split(' = ',1)[1],fields=[]))
            elif samples and line.startswith(('!Sample_title =','!Sample_source_name_ch1 =',
                '!Sample_characteristics_ch1 =','!Sample_supplementary_file =',
                '!Sample_description =','!Sample_data_processing =')):
                samples[-1]['fields'].append(line)
    receipt['samples']=samples
except Exception as error:receipt.update(error_type=type(error).__name__,error=str(error))
(OUT/'aml_samples.receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
