"""Read OOXML identity/header structure; unknown numeric response payloads stay closed."""
import collections
import json
from pathlib import Path, PurePosixPath
import re
import xml.etree.ElementTree as ET
import zipfile

BASE = Path('log/20261022/intervention_dynamics_renewal/melanoma_sequence')
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def text_value(cell, shared):
    if cell.attrib.get('t') == 's':
        index = cell.find('m:v', NS)
        return shared[int(index.text)] if index is not None else ''
    if cell.attrib.get('t') == 'inlineStr':
        return ''.join(v.text or '' for v in cell.findall('.//m:t', NS))
    return None


def main():
    receipt = json.loads((BASE / 'RECEIPT.json').read_text(encoding='utf-8'))
    if not (receipt.get('status') == 200 and receipt.get('manifest_md5_match') and receipt.get('manifest_size_match')):
        raise RuntimeError('Source identity has not passed')
    output = {'stage': 'STRUCTURE_AND_STRING_HEADERS_ONLY', 'numeric_response_values_projected': False, 'sheets': []}
    with zipfile.ZipFile(BASE / 'Suppl Data 03.xlsx') as book:
        shared = []
        if 'xl/sharedStrings.xml' in book.namelist():
            root = ET.fromstring(book.read('xl/sharedStrings.xml'))
            shared = [''.join(v.text or '' for v in item.findall('.//m:t', NS)) for item in root]
        rels = ET.fromstring(book.read('xl/_rels/workbook.xml.rels'))
        targets = {item.attrib['Id']: item.attrib['Target'] for item in rels}
        workbook = ET.fromstring(book.read('xl/workbook.xml'))
        for sheet in workbook.findall('m:sheets/m:sheet', NS):
            target = targets[sheet.attrib[RID]]
            path = target.lstrip('/') if target.startswith('/') else str(PurePosixPath('xl') / target)
            root = ET.fromstring(book.read(path))
            cells = []
            strings = []
            counts = collections.Counter()
            for cell in root.findall('.//m:sheetData/m:row/m:c', NS):
                address = cell.attrib['r']
                kind = cell.attrib.get('t', 'n')
                has_v = cell.find('m:v', NS) is not None
                has_f = cell.find('m:f', NS) is not None
                counts[kind] += 1
                cells.append({'cell': address, 'type': kind, 'has_v_node': has_v, 'has_formula_node': has_f})
                row = int(re.search(r'\d+', address).group())
                column = re.match(r'[A-Z]+', address).group()
                # Header/label window registered before inspecting source layout.
                if row <= 6 or column in ('A', 'B'):
                    value = text_value(cell, shared)
                    if value is not None and value.strip():
                        if re.fullmatch(r'[\s+\-0-9.eE%,]+', value):
                            strings.append({'cell': address, 'value': 'NUMERIC_LIKE_STRING_REDACTED'})
                        else:
                            strings.append({'cell': address, 'value': value})
            output['sheets'].append({'sheet': sheet.attrib['name'], 'xml_path': path,
                                     'dimension': root.find('m:dimension', NS).attrib.get('ref'),
                                     'merges': [v.attrib['ref'] for v in root.findall('m:mergeCells/m:mergeCell', NS)],
                                     'celltype_counts': dict(counts), 'string_header_label_cells': strings,
                                     'cell_structure': cells})
        output['zip_members'] = [{'name': i.filename, 'uncompressed_bytes': i.file_size} for i in book.infolist()]
    (BASE / 'STRUCTURE_AND_STRING_HEADERS.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    brief = {**output, 'sheets': [{k: v for k, v in s.items() if k != 'cell_structure'} for s in output['sheets']]}
    print(json.dumps(brief, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
