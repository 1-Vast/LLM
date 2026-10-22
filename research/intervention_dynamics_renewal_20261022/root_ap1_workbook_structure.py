"""Acquire a pinned source workbook and count XML structure, never cell values."""
from collections import Counter
import base64
import hashlib
import io
import json
import posixpath
import xml.etree.ElementTree as ET
import zipfile

import root_search as scout

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
SHA = 'c4efab68e8dce4e517d45a8812e813f3ae571e6e'
SIZE = 2777650


def census(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if sum(i.file_size for i in archive.infolist()) > 60_000_000:
            raise ValueError('uncompressed_source_cap')
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        relationships = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        targets = {r.attrib['Id']: r for r in relationships}
        records = []
        for sheet in workbook.findall('m:sheets/m:sheet', NS):
            rel = targets[sheet.attrib[RID]]
            if rel.attrib.get('TargetMode') == 'External':
                raise ValueError('external_sheet_relationship')
            target = rel.attrib['Target']
            target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
            root = ET.fromstring(archive.read(target))
            cells = root.findall('.//m:sheetData/m:row/m:c', NS)
            dimension = root.find('m:dimension', NS)
            records.append({'sheet': sheet.attrib['name'],
                'dimension': dimension.attrib.get('ref') if dimension is not None else None,
                'cell_types': dict(Counter(c.attrib.get('t', 'n') for c in cells)),
                'formula_count': sum(c.find('m:f', NS) is not None for c in cells),
                'cell_count': len(cells), 'unique_coordinates': len({c.attrib['r'] for c in cells})})
        return records


def main():
    url = 'https://api.github.com/repos/arjunrajlaboratory/cellularmemory/git/blobs/'+SHA
    receipt, body = scout.get('ap1_main_workbook', url, cap=4_000_000)
    if receipt.get('status') != 200 or 'error_type' in receipt:
        print('AP1_WORKBOOK_ACCESS_FAILED_RETAINED')
        return 1
    try:
        blob = json.loads(body)
        if blob.get('encoding') != 'base64' or blob.get('sha') != SHA or blob.get('size') != SIZE:
            raise ValueError('blob_metadata_mismatch')
        raw = base64.b64decode(blob['content'])
        actual = hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
        if len(raw) != SIZE or actual != SHA:
            raise ValueError('git_blob_mismatch')
        path = scout.OUT/'AP1_mainfigures_sourcedata_AutoRecovered.raw.xlsx'
        with path.open('xb') as handle:
            handle.write(raw)
        records = census(raw)
        result = {'status': 'STRUCTURE_ONLY_CENSUS_COMPLETE', 'decoded_bytes': len(raw),
                  'git_blob_sha1': actual, 'sha256': hashlib.sha256(raw).hexdigest(),
                  'source_path': str(path), 'cell_values_interpreted': False,
                  'publisher_equivalence': 'NOT_AUTHENTICATED', 'sheets': records}
        scout.write(scout.OUT/'AP1_WORKBOOK_STRUCTURE.json', result)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as error:
        scout.write(scout.OUT/'AP1_WORKBOOK_FAILURE.json', {'error_type': type(error).__name__,
                    'reason': str(error) if isinstance(error, ValueError) else 'inspect_local_code'})
        print('AP1_WORKBOOK_QUALIFICATION_FAILURE_RETAINED')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
