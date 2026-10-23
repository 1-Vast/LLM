"""Small exact-byte primary acquisition; all bodies and receipts stay in log/."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/next_mechanism/frontier/sources'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('name')
    parser.add_argument('url')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    receipt = {'url': args.url, 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        response = requests.get(args.url, timeout=55, headers={'User-Agent': 'MAESTRO public primary research contact-not-provided'})
        body = response.content
        (OUT / f'{args.name}.body').write_bytes(body)
        receipt.update(status=response.status_code, final_url=response.url, bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), content_type=response.headers.get('Content-Type'))
        print(json.dumps(receipt))
    except Exception as exc:
        receipt.update(error=type(exc).__name__, detail=str(exc))
        print(json.dumps(receipt))
    receipt['ended_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (OUT / f'{args.name}.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
