"""Cache selected primary full texts, never experimental outcome matrices."""
import datetime
import hashlib
import json
from pathlib import Path
import urllib.request
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'log/20261023/feedback_shift_mechanism/source'


def get(item):
    name,pmcid=item
    url=f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML'
    receipt=dict(url=url,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    try:
        with urllib.request.urlopen(url,timeout=45) as response:
            raw=response.read();receipt['status']=response.status
        (OUT/(name+'.body')).write_bytes(raw)
        receipt.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        root=ET.fromstring(raw)
        paragraphs=[' '.join(''.join(e.itertext()).split()) for e in root.findall('.//body//p')]
        refs=[e.get('href') or e.get('{http://www.w3.org/1999/xlink}href') for e in root.findall('.//ext-link')]
        projection={'paragraphs':paragraphs,'links':refs}
        (OUT/(name+'.projection.json')).write_text(json.dumps(projection,indent=2),encoding='utf-8')
        print(json.dumps(dict(name=name,receipt=receipt)))
    except Exception as e:
        receipt['error']=repr(e);print(json.dumps(receipt))
    (OUT/(name+'.receipt.json')).write_text(json.dumps(receipt,indent=2),encoding='utf-8')


if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(get,[('euopenscreen','PMC12084007'),('myotoxicity','PMC11957314')]))
