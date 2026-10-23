"""Strict identity/presence extraction; no response magnitude conversion."""
from collections import Counter
import json
from pathlib import Path
import posixpath
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/decrypte_source_qualification'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RNS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def main():
    with zipfile.ZipFile(OUT / 'supplement.xlsx') as z:
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        relationships = {r.attrib['Id']: r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        sheet = next(s for s in wb.findall('s:sheets/s:sheet', NS) if s.attrib['name'] == 'TableS1 - Cpd via info')
        target = relationships[sheet.attrib[RNS]]
        member = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
        ss = ET.fromstring(z.read('xl/sharedStrings.xml'))
        rows = []
        with z.open(member) as source:
            for _, row in ET.iterparse(source, events=('end',)):
                if row.tag != '{' + NS['s'] + '}row':
                    continue
                index = int(row.attrib['r'])
                if index == 1:
                    row.clear()
                    continue
                cells = {''.join(c for c in e.attrib['r'] if c.isalpha()): e for e in row.findall('s:c', NS)}
                item = {'row': index}
                for col, key in [('A', 'drug'), ('B', 'cell'), ('U', 'assay')]:
                    e = cells.get(col)
                    if e is None:
                        item[key] = None
                    elif e.attrib.get('t') == 's':
                        item[key] = ''.join(ss[int(e.find('s:v', NS).text)].itertext())
                    else:
                        raise ValueError(f'Unexpected identity type at {col}{index}')
                item['response_structure'] = {}
                for col in 'JKLMNOPQRST':
                    e = cells.get(col)
                    item['response_structure'][col] = {'present': e is not None and e.find('s:v', NS) is not None,
                        'type': e.attrib.get('t', 'n') if e is not None else None,
                        'formula': e is not None and e.find('s:f', NS) is not None}
                rows.append(item)
                row.clear()
    keys = Counter((r['drug'], r['cell'], r['assay']) for r in rows)
    result = {'sheet': sheet.attrib['name'], 'member': member, 'rows': rows,
              'summary': {'row_count': len(rows), 'drugs': len(set(r['drug'] for r in rows)),
                          'cells': dict(Counter(r['cell'] for r in rows)),
                          'assays': dict(Counter(r['assay'] for r in rows)),
                          'duplicate_keys': [list(k) + [v] for k, v in keys.items() if v > 1],
                          'missing_response_cells': sum(not c['present'] for r in rows for c in r['response_structure'].values()),
                          'formula_response_cells': sum(c['formula'] for r in rows for c in r['response_structure'].values())}}
    (OUT / 'IDENTITIES.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result['summary'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
