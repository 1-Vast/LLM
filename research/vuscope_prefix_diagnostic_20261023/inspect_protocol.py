"""Read experimental schedule metadata; no response trajectory/ATP values."""
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

import openpyxl

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/vuscope_prefix_diagnostic'
ARCHIVE = ROOT / 'log/20261023/functional_transition_law/root_sources/release.zip.body'

if __name__ == '__main__':
    target = OUT / 'PROTOCOL_METADATA.json'
    assert not target.exists()
    with ZipFile(ARCHIVE) as archive:
        names = [n for n in archive.namelist() if '/input/protocols/' in n and n.endswith('.xlsx')]
        assert len(names) == 1
        workbook = openpyxl.load_workbook(BytesIO(archive.read(names[0])), read_only=True, data_only=True)
        sheets = {}
        for sheet in workbook:
            rows = list(sheet.values)
            sheets[sheet.title] = dict(rows=len(rows), columns=sheet.max_column, header=list(rows[0]),
                                       records=[list(row) for row in rows[1:]])
    target.write_text(json.dumps(dict(member=names[0], sheets=sheets), default=str, indent=2), encoding='utf-8')
    print(json.dumps({k: dict(rows=v['rows'], columns=v['columns'], header=v['header'], sample=v['records'][:2]) for k, v in sheets.items()}, default=str, indent=2))
