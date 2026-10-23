"""Copy verified Apache-2.0 author model source to research; keep evidence in log."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / 'log/20261022/naiad_direct_baseline/root_sources'
OUT = Path(__file__).resolve().parent / 'vendor'
OUT.mkdir(exist_ok=True)
for name, target in [('naiad__models.py', 'naiad_models.py'), ('LICENSE', 'LICENSE')]:
    raw = (SOURCES / (name + '.body')).read_bytes()
    receipt = json.loads((SOURCES / (name + '.receipt.json')).read_text())
    assert receipt['status'] == 200 and hashlib.sha256(raw).hexdigest() == receipt['sha256']
    (OUT / target).write_bytes(raw)
(OUT / 'ATTRIBUTION.txt').write_text('NAIAD authors, NeptuneBio/NAIAD revision9207e9e855e865160a196a6989392f6db622b0d6; Apache-2.0. Exact models.py and LICENSE copied unchanged. Adapter outside vendor is MAESTRO research code.\n')
print('Verified exact pinned author models and license copied to research/vendor')
