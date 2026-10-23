"""Read a finite set of exact official metadata sources and a primer-only sheet."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import posixpath
import xml.etree.ElementTree as ET
import zipfile
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/aml_identity_qualification'
OLD = ROOT/'log/20261023/post_anchor_mechanism/root_sources'
CONTRACT = hashlib.sha256((OUT/'MANIFEST_PROTOCOL.md').read_bytes()).hexdigest()
ITEMS = [('pre_biosample', 'https://www.ebi.ac.uk/ena/browser/api/xml/SAMN46795876'),
         ('post_biosample', 'https://www.ebi.ac.uk/ena/browser/api/xml/SAMN46795874'),
         ('zenodo', 'https://zenodo.org/api/records/19303229')]


def get(item):
    name, url = item
    receipt = dict(url=url, utc=datetime.now(timezone.utc).isoformat(), contract_sha256=CONTRACT)
    projection = {}
    try:
        response = requests.get(url, timeout=40)
        (OUT/f'{name}.body').write_bytes(response.content)
        receipt.update(status=response.status_code, bytes=len(response.content),
                       sha256=hashlib.sha256(response.content).hexdigest())
        if response.status_code == 200:
            if name == 'zenodo':
                payload = response.json()
                projection = dict(title=payload.get('metadata', {}).get('title'),
                    files=[{key: row.get(key) for key in ['key', 'size', 'checksum', 'links']}
                           for row in payload.get('files', [])])
            else:
                xml = ET.fromstring(response.content)
                projection = dict(titles=[node.text for node in xml.findall('.//TITLE')],
                    attributes=[dict(tag=node.findtext('TAG'), value=node.findtext('VALUE'))
                                for node in xml.findall('.//SAMPLE_ATTRIBUTE')],
                    external_ids=[dict(node.attrib, value=node.text) for node in xml.findall('.//EXTERNAL_ID')])
    except Exception as error:
        receipt.update(error_type=type(error).__name__, error=str(error))
    (OUT/f'{name}.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return dict(name=name, receipt=receipt, metadata=projection)


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(get, ITEMS))
    ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    rel = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
    path = OLD/'41467_2026_74989_MOESM3_ESM.xlsx'
    cells = []
    with zipfile.ZipFile(path) as archive:
        strings = [''.join(node.itertext()) for node in
                   ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('s:si', ns)]
        relations = {node.attrib['Id']: node.attrib['Target'] for node in
                     ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
        sheets = ET.fromstring(archive.read('xl/workbook.xml')).findall('s:sheets/s:sheet', ns)
        sheet = next(node for node in sheets if node.attrib['name'] == 'Supplemental Data  15')
        member = relations[sheet.attrib[rel]]
        member = member.lstrip('/') if member.startswith('/') else posixpath.normpath('xl/'+member)
        xml = ET.fromstring(archive.read(member))
        assert xml.find('s:dimension', ns).attrib['ref'] == 'A1:D17'
        for cell in xml.findall('s:sheetData/s:row/s:c', ns):
            if cell.find('s:f', ns) is not None:
                continue
            if cell.attrib.get('t') == 's':
                value = strings[int(cell.findtext('s:v', namespaces=ns))]
            elif cell.attrib.get('t') == 'inlineStr':
                value = ''.join(cell.find('s:is', ns).itertext())
            else:
                continue
            cells.append(dict(cell=cell.attrib['r'], text=value))
    output = dict(sources=results, primer_sheet=dict(workbook_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  name=sheet.attrib['name'], text_cells=cells), contract_sha256=CONTRACT)
    (OUT/'MANIFEST_CHECK.json').write_text(json.dumps(output, indent=2), encoding='utf-8')
    print(json.dumps(output, indent=2))
