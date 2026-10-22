"""Bounded source fetch; raw responses and integrity receipts only."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[2] / 'log/20261022/biological_decision_scout/sources'


def fetch(label, url, cap=5_000_000):
    ROOT.mkdir(parents=True, exist_ok=True)
    body_path = ROOT / (label + '.body')
    receipt_path = ROOT / (label + '.receipt.json')
    if body_path.exists() or receipt_path.exists():
        raise FileExistsError(label)
    started = datetime.now(timezone.utc).isoformat()
    try:
        response = urlopen(Request(url, headers={'User-Agent': 'MAESTRO-public-research-source-audit/1.0'}), timeout=30)
    except HTTPError as error:
        response = error
    except (URLError, TimeoutError) as error:
        receipt = {'url': url, 'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(),
                   'status': None, 'error': repr(error), 'bytes': 0, 'body_received': False}
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'label': label, **receipt}))
        return b''
    with response:
        body = response.read(cap + 1)
        receipt = {'url': url, 'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(),
                   'status': response.status, 'final_url': response.url, 'bytes': len(body),
                   'sha256': hashlib.sha256(body).hexdigest(), 'truncated': len(body) > cap,
                   'content_type': response.headers.get('Content-Type')}
    body_path.write_bytes(body)
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'label': label, **receipt}))
    return body


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('label')
    parser.add_argument('url')
    args = parser.parse_args()
    fetch(args.label, args.url)
