"""Read only matrix protein headers and old source node identifiers."""
import csv
import hashlib
from io import BytesIO
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/ptpc_update_opportunity'
SOURCE = ROOT / 'log/20261022/generative_repair_renewal/source/archive_followup'
TAG = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'


def main():
    source = SOURCE / 'archive.body'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == 'efdcbdab1f67d23e963208b3957164a95ff9a4485141b9e61aa852457a42e133'
    with zipfile.ZipFile(source) as outer:
        body = outer.read('TableS8_PTPC_info_0703.xlsx')
    with zipfile.ZipFile(BytesIO(body)) as book:
        shared = ET.fromstring(book.read('xl/sharedStrings.xml')).findall(TAG + 'si') if 'xl/sharedStrings.xml' in book.namelist() else []
        rels = {x.attrib['Id']: x.attrib['Target'] for x in ET.fromstring(book.read('xl/_rels/workbook.xml.rels'))}
        sheets = ET.fromstring(book.read('xl/workbook.xml')).find(TAG + 'sheets')
        selected = next(x for x in sheets if x.attrib['name'] == 'C_protein_Matrix')
        part = rels[selected.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
        part = part.lstrip('/') if part.startswith('/') else 'xl/' + part
        headers = []
        with book.open(part) as stream:
            for _, row in ET.iterparse(stream, events=('end',)):
                if row.tag != TAG + 'row':
                    continue
                assert row.attrib['r'] == '1'
                for cell in row:
                    assert cell.find(TAG + 'f') is None
                    node = cell.find(TAG + 'v')
                    if cell.attrib.get('t') == 's':
                        text = ''.join(t.text or '' for t in shared[int(node.text)].iter(TAG + 't'))
                    elif cell.attrib.get('t') == 'inlineStr':
                        text = ''.join(t.text or '' for t in cell.iter(TAG + 't'))
                    else:
                        text = node.text if node is not None else ''
                    headers.append({'cell': cell.attrib['r'], 'identifier': text})
                break
    assert headers[0]['identifier'] == 'Sample_ID'
    old_path = ROOT / 'data/external/ptv1_proteintalks_20261021/drive/allcelltype_drugpair_crossdrug_node_Index.csv'
    with old_path.open(newline='', encoding='utf-8-sig') as stream:
        old = [r[0] for r in csv.reader(stream)]
    new = [r['identifier'] for r in headers[1:]]
    assert all(new) and len(new) == len(set(new))
    result = {'scope': 'Header identity only; no abundance or labels read',
              'S8_workbook_sha256': hashlib.sha256(body).hexdigest(),
              'old_nodes_sha256': hashlib.sha256(old_path.read_bytes()).hexdigest(),
              'old_count': len(old), 'new_count': len(new),
              'exact_common_count': len(set(old) & set(new)),
              'headers': headers, 'old_ordered_nodes': old}
    target = OUT / 'HEADER_COMPATIBILITY.json'
    assert not target.exists()
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('headers', 'old_ordered_nodes')}))


if __name__ == '__main__':
    main()
