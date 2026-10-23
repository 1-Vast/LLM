"""Retrieve one candidate attachment; emit structure/captions, not table bodies."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/hcc_task_qualification'
URL = 'https://pmc.ncbi.nlm.nih.gov/articles/instance/12205652/bin/mmc2.docx'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

if __name__ == '__main__':
    target = OUT/'mmc2.docx'
    assert not target.exists()
    start = datetime.now(timezone.utc).isoformat()
    response = requests.get(URL, timeout=45, headers={'User-Agent': 'MAESTRO-source-qualification'})
    target.write_bytes(response.content)
    receipt = {'url': URL, 'final_url': response.url, 'status': response.status_code,
               'utc_start': start, 'utc_end': datetime.now(timezone.utc).isoformat(),
               'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest(),
               'content_type': response.headers.get('Content-Type'),
               'is_zip': zipfile.is_zipfile(io.BytesIO(response.content))}
    (OUT/'ATTACHMENT_RECEIPT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    if not response.ok or not receipt['is_zip']:
        print(json.dumps({'status': 'FAILED_ATTACHMENT_CONTAINER', 'receipt': receipt}, indent=2))
        raise SystemExit(1)
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        document = ET.fromstring(archive.read('word/document.xml'))
        captions = []
        for p in document.findall('.//w:body/w:p', NS):
            text = ''.join(p.itertext()) if False else ''.join(t.text or '' for t in p.findall('.//w:t', NS))
            if re.match(r'^\s*(Table\s*S?\d|Supplementary\s+(Table|Methods)|Supplemental\s+Table)', text, re.I):
                captions.append(text[:700])
        tables = document.findall('.//w:tbl', NS)
        headers = []
        for index, table in enumerate(tables):
            rows = table.findall('./w:tr', NS)
            cells = rows[0].findall('./w:tc', NS) if rows else []
            headers.append({'table_index': index, 'rows': len(rows),
                            'first_row': [''.join(t.text or '' for t in cell.findall('.//w:t', NS))[:250]
                                          for cell in cells]})
        metadata = {'captions': captions, 'tables': headers,
                    'embedded_objects': [{'path': info.filename, 'bytes': info.file_size}
                                         for info in archive.infolist() if 'embedding' in info.filename]}
    (OUT/'ATTACHMENT_SCHEMA.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata, indent=2))
