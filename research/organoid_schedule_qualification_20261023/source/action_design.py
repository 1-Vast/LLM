"""Project sequential design columns; never select/convert response columns."""
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / 'log/20261023/organoid_schedule_qualification/root/zenodo_archive.body'
OUT = ROOT / 'log/20261023/organoid_schedule_qualification/source/ACTION_PROJECTION.json'

if __name__ == '__main__':
    result = {'archive_sha256': hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(), 'members': {}}
    with zipfile.ZipFile(ARCHIVE) as z:
        for name in z.namelist():
            if '/sequential/data/' not in name or not name.endswith('.csv'):
                continue
            rows = csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig')))
            result['members'][name] = [{k: r[k] for k in ('seq', 't0', 't1', 'gen', 'number')} for r in rows]
    assert not OUT.exists()
    OUT.write_text(json.dumps(result, indent=2), encoding='utf-8')
