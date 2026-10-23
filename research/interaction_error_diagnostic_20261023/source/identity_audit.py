"""Inspect only SCHEMATIC target-ID cells; never select a score-cell value."""
from collections import Counter
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[3]
ASSET = ROOT / 'log/20261023/update_law_search/task/interaction_supplement.body'
OUT = ROOT / 'log/20261023/interaction_error_diagnostic/source/ID_AUDIT_v2.json'
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def main():
    pairs = []
    with ZipFile(ASSET) as archive:
        shared = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            for item in ET.fromstring(archive.read('xl/sharedStrings.xml')):
                shared.append(''.join(item.itertext()))
        with archive.open('xl/worksheets/sheet1.xml') as stream:
            for _, row in ET.iterparse(stream, events=('end',)):
                if row.tag != '{' + NS['m'] + '}row':
                    continue
                ids = {}
                for cell in row:
                    coordinate = cell.attrib.get('r', '')
                    column = coordinate.rstrip('0123456789')
                    if column not in ('A', 'B'):
                        continue
                    kind = cell.attrib.get('t')
                    value = cell.find('m:v', NS)
                    if kind == 's':
                        assert value is not None
                        ids[column] = shared[int(value.text)]
                    elif kind == 'inlineStr':
                        ids[column] = ''.join(cell.find('m:is', NS).itertext())
                    else:
                        raise ValueError(f'Nontext target-ID cell: {coordinate}/{kind}')
                assert set(ids) == {'A', 'B'}
                if row.attrib['r'] == '1':
                    assert ids == {'A': 'target_a_id', 'B': 'target_b_id'}
                else:
                    pairs.append((ids['A'], ids['B']))
                row.clear()
    ordered = Counter(pairs)
    canonical = Counter(tuple(sorted(pair)) for pair in pairs)
    names = sorted({name for pair in pairs for name in pair})
    known_controls = [name for name in names if name in ('AAVS', 'nontargeting')]
    result = dict(
        source_sha256=hashlib.sha256(ASSET.read_bytes()).hexdigest(),
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='Only A/B ID values selected; other column values never selected/cast/emitted. XML bytes contain all columns.',
        rows=len(pairs), distinct_ordered=len(ordered), distinct_unordered=len(canonical),
        ordered_multiplicity_histogram=dict(Counter(ordered.values())),
        canonical_row_multiplicity_histogram=dict(Counter(canonical.values())),
        mirrored_nonself_groups=sum(a != b and (a, b) in ordered and (b, a) in ordered
                                    for a, b in canonical),
        diagonal_ids=sorted(a for a, b in canonical if a == b),
        target_a_ids=sorted({a for a, _ in pairs}), target_b_ids=sorted({b for _, b in pairs}),
        known_control_ids=known_controls,
        known_control_rows=sum(a in known_controls or b in known_controls for a, b in pairs),
        note='String sorting is an analysis key only, not a chemical/gene alias or independent guide audit.',
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    assert not OUT.exists(), 'Preserve original identity audit'
    OUT.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
