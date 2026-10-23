"""Read pinned official source text only; never import downloaded code."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

OUT = Path('log/20261023/dose_update_qualification/rhaister')
OUT.mkdir(parents=True, exist_ok=True)
SHA = '75fed20a1d97b05a09bf25c5341762141882106a'
FILES = ['docs/architecture.md', 'rhaister/prepare_sensitivity.py',
         'rhaister/train_sensitivity.py', 'rhaister/train.py',
         'scripts/baseline_sensitivity.py', 'splits/EmeraldBay/dataset.toml',
         'splits/EmeraldBay/split_0/split.toml']
for name in FILES:
    url = f'https://huggingface.co/tahoebio/Rhaister/resolve/{SHA}/{name}'
    dest = OUT / (name.replace('/', '__') + '.body')
    receipt = {'url': url, 'repo_sha': SHA, 'utc': datetime.now(timezone.utc).isoformat()}
    try:
        with urlopen(Request(url, headers={'User-Agent': 'MAESTRO-source-audit/1'}), timeout=45) as response:
            body = response.read()
            receipt.update(status=response.status, final_url=response.url,
                           headers=dict(response.headers), bytes=len(body),
                           sha256=hashlib.sha256(body).hexdigest())
        dest.write_bytes(body)
    except Exception as exc:
        receipt['error'] = repr(exc)
    dest.with_suffix('.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(name, receipt.get('status'), receipt.get('bytes'), receipt.get('error', ''))
