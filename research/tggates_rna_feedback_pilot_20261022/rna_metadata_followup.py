"""Primary HTML/catalogue/paper metadata follow-up only; no expression payloads."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import xml.etree.ElementTree as ET
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261022/tggates_rna_feedback_pilot/rna_sources'


def main():
    urls = [('official_human_invitro_directory', 'https://dbarchive.biosciencedbc.jp/data/open-tggates/LATEST/Human/in_vitro/'),
            ('biostudies_E_MTAB_798', 'https://www.ebi.ac.uk/biostudies/api/v1/studies/E-MTAB-798'),
            ('TXG_MAPr_primary', 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8536636/fullTextXML')]
    for name, url in urls:
        receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'url': url,
                   'method': 'GET', 'logical_request': 1, 'RNA_numerical_payload_allowed': False}
        start = time.monotonic()
        try:
            response = requests.get(url, timeout=30, stream=True)
            pieces, length = [], 0
            for chunk in response.iter_content(65536):
                length += len(chunk)
                if length > 4*1024*1024:
                    raise ValueError('Metadata cap')
                pieces.append(chunk)
            body = b''.join(pieces)
            with (OUT/(name+'.body')).open('xb') as stream:
                stream.write(body)
            receipt.update(status=response.status_code, final_url=response.url, bytes=len(body),
                           sha256=hashlib.sha256(body).hexdigest(), headers=dict(response.headers))
            if response.status_code == 200 and name == 'TXG_MAPr_primary':
                xml = ET.fromstring(body)
                paragraphs = [' '.join(''.join(node.itertext()).split()) for node in xml.iter()
                              if node.tag.rsplit('}',1)[-1] in ('p', 'ext-link')]
                selected = [p for p in paragraphs if any(word in p.lower() for word in
                            ('availability', 'download', 'jointly normalized', 'github', 'figshare', 'data are', 'data is'))]
                with (OUT/(name+'.metadata_text.json')).open('x', encoding='utf-8') as stream:
                    json.dump(selected, stream, ensure_ascii=False, indent=2)
        except Exception as exc:
            receipt.update(error_type=type(exc).__name__)
        receipt['elapsed_seconds'] = time.monotonic()-start
        with (OUT/(name+'.http.json')).open('x', encoding='utf-8') as stream:
            json.dump(receipt, stream, indent=2)
        print(json.dumps({k:receipt.get(k) for k in ('url','status','bytes','error_type')}))


if __name__ == '__main__':
    main()
