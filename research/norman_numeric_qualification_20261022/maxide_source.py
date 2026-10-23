"""Acquire exact close baseline implementation for later faithful/corrected comparison."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/norman_numeric_qualification/root_sources'
OUT.mkdir(parents=True, exist_ok=True)
url = 'https://raw.githubusercontent.com/thomasmaxwellnorman/Perturbseq_GI/3b25109aeb9c0c2026bd70abd50304a0ad4e5395/maxide.py'
response = requests.get(url, timeout=60)
data = response.content
(OUT / 'maxide.body').write_bytes(data)
receipt = {'url': url, 'status': response.status_code, 'bytes': len(data),
           'sha256': hashlib.sha256(data).hexdigest(), 'utc': datetime.now(timezone.utc).isoformat()}
(OUT / 'maxide.receipt.json').write_text(json.dumps(receipt, indent=2))
print(json.dumps(receipt))
