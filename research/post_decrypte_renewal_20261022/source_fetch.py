"""Retain explicitly selected primary design documents, no response tables."""
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/post_decrypte_renewal/root/primary'
SOURCES = {'retriever': 'https://cdn.elifesciences.org/preprints/102442/elife-preprint-102442-v2.xml',
           'almanac': 'https://dtp.cancer.gov/discovery_development/nci-60/almanac.htm'}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    for name,url in SOURCES.items():
        body = b''
        record = {'url':url,'utc':datetime.now(timezone.utc).isoformat()}
        try:
            try:
                response = urlopen(Request(url, headers={'User-Agent':'MAESTRO-research/1.0'}),timeout=35)
            except HTTPError as error:
                response = error
            with response:
                record['status'] = response.code
                record['final_url'] = response.url
                body = response.read(5_000_001)
            assert record['status'] == 200 and len(body) <= 5_000_000
            if name == 'retriever':
                root = ET.fromstring(body)
                text = '\n'.join(' '.join(e.itertext()) for e in root.findall('.//body//p'))
                text += '\n' + '\n'.join(' '.join(e.itertext()) for e in root.findall('.//back//sec'))
                (OUT / 'retriever_narrative.txt').write_text(text,encoding='utf-8')
        except Exception as error:
            record['error'] = str(error)
        (OUT / (name+'.body')).write_bytes(body)
        record.update({'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()})
        (OUT / (name+'.receipt.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')
        print(json.dumps(record),flush=True)


if __name__ == '__main__':
    main()
