"""Author-linked GEO series metadata only; never access expression or read counts."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/update_signal_reassessment/root_sources'
assert not (OUT / 'geo203240.body').exists()
response = requests.get('https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi',
                        params={'acc': 'GSE203240', 'targ': 'self', 'form': 'text', 'view': 'full'}, timeout=60)
(OUT / 'geo203240.body').write_bytes(response.content)
(OUT / 'geo203240.receipt.json').write_text(json.dumps({
    'url': response.url, 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
    'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2), encoding='utf-8')
response.raise_for_status()
keys = ('!Series_title', '!Series_summary', '!Series_overall_design', '!Series_type',
        '!Series_sample_id', '!Series_supplementary_file', '!Series_relation')
lines = [line for line in response.text.splitlines() if line.startswith(keys)]
assert lines, 'No GEO series metadata parsed; retain body and stop'
(OUT / 'GEO203240_METADATA.json').write_text(json.dumps(lines, indent=2), encoding='utf-8')
print(json.dumps(lines, indent=2))
