"""Bind the new diagnostic before its one execution."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/dose_update_qualification'

if __name__ == '__main__':
    target = OUT / 'ALLOCATION_FREEZE.json'
    assert not target.exists() and not (OUT / 'ALLOCATION_RESULT.json').exists()
    names = ['log/20261023/dose_update_qualification/ALLOCATION_PROTOCOL.md',
             'research/dose_update_qualification_20261023/allocation.py',
             'research/dose_update_qualification_20261023/freeze_allocation.py',
             'log/20261023/dose_update_qualification/sources/quota_primary.body',
             'log/20261023/dose_update_qualification/sources/PRIMARY_REQUESTS.json']
    target.write_text(json.dumps(dict(files={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in names}), indent=2), encoding='utf-8')
    print('Frozen files:', len(names))
