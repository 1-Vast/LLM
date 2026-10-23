"""Fetch pinned author implementation defining cell/guide QC semantics."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/norman_functional_contract/root_sources'
url = 'https://raw.githubusercontent.com/thomasmaxwellnorman/Perturbseq_GI/3b25109aeb9c0c2026bd70abd50304a0ad4e5395/perturbseq/cell_population.py'
response = requests.get(url, timeout=60)
data = response.content
(OUT / 'cell_population.body').write_bytes(data)
record = {'url': url, 'status': response.status_code, 'bytes': len(data),
          'sha256': hashlib.sha256(data).hexdigest(), 'utc': datetime.now(timezone.utc).isoformat()}
(OUT / 'cell_population.receipt.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record))
