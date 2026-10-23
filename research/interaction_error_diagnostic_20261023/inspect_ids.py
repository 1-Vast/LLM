"""Inspect identifiers only; do not cast score cells or read other worksheets."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'log/20261023/update_law_search/task/interaction_supplement.body'
OUT = ROOT / 'log/20261023/interaction_error_diagnostic'
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def identifiers():
    with zipfile.ZipFile(DATA) as archive:
        strings = ET.fromstring(archive.read('xl/sharedStrings.xml'))
        shared = [''.join(s.itertext()) for s in strings]
        sheet = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
    rows = []
    for row in sheet.findall('m:sheetData/m:row', NS)[1:]:
        ids = []
        for cell in row:
            col = ''.join(c for c in cell.attrib['r'] if c.isalpha())
            if col not in ('A', 'B'):
                continue
            value = cell.find('m:v', NS)
            if value is None:
                text = ''.join(cell.itertext())
            elif cell.attrib.get('t') == 's':
                text = shared[int(value.text)]
            else:
                text = value.text
            ids.append((col, text))
        assert [c for c, _ in ids] == ['A', 'B'], ids
        rows.append(tuple(v for _, v in ids))
    return rows


if __name__ == '__main__':
    pairs = identifiers()
    groups = Counter(tuple(sorted(pair)) for pair in pairs)
    counts = Counter(gene for pair in pairs for gene in pair)
    result = dict(data_sha256=hashlib.sha256(DATA.read_bytes()).hexdigest(),
                  rows=len(pairs), canonical_pairs=len(groups),
                  multiplicities=dict(Counter(groups.values())),
                  self_pairs=sum(a == b for a, b in pairs),
                  ids=sorted(counts),
                  scope='Identifiers only, no score value casting; XML bytes are not secure blinding')
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / 'IDENTIFIERS.json'
    assert not target.exists()
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'ids'}))
