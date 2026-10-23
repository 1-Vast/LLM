"""One unauthenticated primary-source metadata request with immutable receipts."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import requests

parser = argparse.ArgumentParser()
parser.add_argument('name')
parser.add_argument('url')
args = parser.parse_args()
out = Path(__file__).resolve().parents[2] / 'log/20261022/az_chemical_identity'
out.mkdir(parents=True, exist_ok=True)
body_path = out / (args.name + '.body')
receipt_path = out / (args.name + '.http.json')
if body_path.exists() or receipt_path.exists():
    raise SystemExit('Refusing to overwrite an existing HTTP capture')
receipt = {'url': args.url, 'utc': datetime.now(timezone.utc).isoformat(),
           'authentication': False, 'automatic_redirects': False,
           'purpose': 'Author supplementary chemical identity metadata only',
           'body_cap_bytes': 8 * 1024 * 1024}
try:
    response = requests.get(args.url, timeout=40, allow_redirects=False, stream=True,
                            headers={'User-Agent': 'MAESTRO-primary-metadata-audit/1.0'})
    body = b''
    for chunk in response.iter_content(65536):
        body += chunk
        if len(body) > receipt['body_cap_bytes']:
            raise ValueError('Metadata body cap exceeded')
    receipt.update(status=response.status_code,
                   headers={key: value for key, value in response.headers.items()
                            if key.lower() not in ('set-cookie', 'cookie', 'authorization')},
                   sha256=hashlib.sha256(body).hexdigest(), bytes=len(body))
    body_path.write_bytes(body)
except Exception as error:
    receipt['error'] = repr(error)
receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipt, ensure_ascii=False))
