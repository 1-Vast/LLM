"""Retrieve one authenticated data record and inspect file metadata."""
from discover import OUT
import hashlib
import json
import requests
import xml.etree.ElementTree as ET

if __name__ == '__main__':
    url = 'https://zenodo.org/api/records/17722905'
    response = requests.get(url, timeout=90)
    with (OUT / 'hfim_record.body').open('xb') as f:
        f.write(response.content)
    receipt = {'url': url, 'status': response.status_code, 'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}
    (OUT / 'hfim_record.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    data = response.json()
    summary = {'receipt': receipt, 'doi': data.get('doi'), 'metadata': data.get('metadata'), 'files': data.get('files')}
    (OUT / 'hfim_manifest.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({'receipt': receipt, 'metadata': data.get('metadata'), 'files': [{'key': f.get('key'), 'size': f.get('size'), 'checksum': f.get('checksum'), 'links': f.get('links')} for f in data.get('files', [])]}))
    root = ET.fromstring((OUT / 'microfluidic_hfim_fulltext.body').read_bytes())
    print(json.dumps({'publication': [ET.tostring(x, encoding='unicode') for x in root.iter('pub-date')], 'supplements': [ET.tostring(x, encoding='unicode') for x in root.iter('supplementary-material')]}))
