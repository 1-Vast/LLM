"""Parse the authenticated archive DOCX; suppress all table body rows."""
import hashlib
import io
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from attachment import OUT, NS

if __name__ == '__main__':
    target = OUT/'ATTACHMENT_SCHEMA.json'
    assert not target.exists()
    with zipfile.ZipFile(OUT/'epmc_supplements.zip') as archive:
        body = archive.read('mmc2.docx')
    assert len(body) == 65340 and hashlib.md5(body).hexdigest() == '31b73eb3fd2aa42c679bb87fbac135c0'
    (OUT/'mmc2_authenticated.docx').write_bytes(body)
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        document = ET.fromstring(archive.read('word/document.xml'))
        captions = []
        for p in document.findall('.//w:body/w:p', NS):
            text = ''.join(t.text or '' for t in p.findall('.//w:t', NS))
            if re.match(r'^\s*(Table\s*S?\d|Supplementary\s+(Table|Methods)|Supplemental\s+Table)', text, re.I):
                captions.append(text[:700])
        headers = []
        for index, table in enumerate(document.findall('.//w:tbl', NS)):
            rows = table.findall('./w:tr', NS)
            cells = rows[0].findall('./w:tc', NS) if rows else []
            headers.append({'table_index': index, 'rows': len(rows), 'first_row': [
                ''.join(t.text or '' for t in cell.findall('.//w:t', NS))[:250] for cell in cells]})
        metadata = {'md5_matches_primary_jats': True, 'captions': captions, 'tables': headers,
                    'embedded_objects': [{'path': info.filename, 'bytes': info.file_size}
                        for info in archive.infolist() if 'embedding' in info.filename]}
    target.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata, indent=2))
