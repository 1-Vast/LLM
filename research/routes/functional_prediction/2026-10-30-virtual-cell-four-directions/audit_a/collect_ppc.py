"""Bounded source-only acquisition for the PPC eligibility audit; no model execution."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
DATA = Path('D:/MAESTRO/data/external/virtual_cell_four_directions_20261030/ppc')
LOG = ROOT / 'requests.jsonl'
MAX_TOTAL = 80_000_000


def fetch(url: str, filename: str, purpose: str, max_bytes: int) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    used = sum(p.stat().st_size for p in DATA.rglob('*') if p.is_file())
    if used + max_bytes > MAX_TOTAL:
        raise RuntimeError(f'Declared request budget exceeds 80 MB: {used} + {max_bytes}')
    target = DATA / filename
    if target.exists():
        raise FileExistsError(target)
    rec = {'utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'url': url,
           'filename': filename, 'purpose': purpose, 'limit_bytes': max_bytes}
    try:
        with requests.get(url, timeout=60, stream=True) as response:
            rec.update(status=response.status_code, final_url=response.url,
                       content_type=response.headers.get('Content-Type'),
                       content_length=response.headers.get('Content-Length'))
            chunks = []
            size = 0
            for chunk in response.iter_content(65536):
                size += len(chunk)
                if size > max_bytes:
                    raise RuntimeError(f'Response exceeds per-request bound: {max_bytes}')
                chunks.append(chunk)
            payload = b''.join(chunks)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            rec.update(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
    except Exception as exc:
        rec['error'] = repr(exc)
    with LOG.open('a', encoding='utf-8') as output:
        output.write(json.dumps(rec, ensure_ascii=False) + '\n')
    print(json.dumps(rec, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('filename')
    parser.add_argument('purpose')
    parser.add_argument('--max-bytes', type=int, default=2_000_000)
    args = parser.parse_args()
    fetch(args.url, args.filename, args.purpose, args.max_bytes)
