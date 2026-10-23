"""Inspect names and table schema; do not emit numeric response rows."""
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/organoid_schedule_qualification/root'

if __name__ == '__main__':
    data = (OUT / 'zenodo_archive.body').read_bytes()
    metadata = json.loads((OUT / 'zenodo_metadata.body').read_text())
    published = metadata['files'][0]
    assert len(data) == published['size']
    assert 'md5:' + hashlib.md5(data).hexdigest() == published['checksum']
    result = dict(archive_sha256=hashlib.sha256(data).hexdigest(), published_md5_matches=True,
                  numeric_response_rows_emitted=False, members=[])
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for member in archive.infolist():
            item = dict(name=member.filename, bytes=member.file_size)
            if member.filename.lower().endswith('.csv'):
                raw = archive.read(member)
                rows = list(csv.reader(io.StringIO(raw.decode('utf-8-sig'))))
                item.update(header=rows[0] if rows else [], nonheader_rows=max(0, len(rows)-1),
                            row_widths=sorted(set(map(len, rows[1:]))),
                            sha256=hashlib.sha256(raw).hexdigest())
            result['members'].append(item)
    target = OUT / 'ZENODO_STRUCTURE.json'
    assert not target.exists()
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
