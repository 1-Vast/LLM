"""Bounded, no-retry source GETs; all request evidence saved in log/."""
import hashlib
import json
import pathlib
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

OUT = pathlib.Path('log/20261022/intervention_dynamics_renewal/skeptic')
CAP = 3_000_000


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(name, url):
    OUT.mkdir(parents=True, exist_ok=True)
    ledger_path = OUT / 'NETWORK.json'
    ledger = json.loads(ledger_path.read_text(encoding='utf-8')) if ledger_path.exists() else []
    if len(ledger) >= 6:
        raise RuntimeError('Six-GET ceiling reached')
    entry = {'request': len(ledger) + 1, 'name': name, 'url': url,
             'utc': datetime.now(timezone.utc).isoformat()}
    req = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO-method-review/1.0'})
    opener = urllib.request.build_opener(NoRedirect())
    try:
        response = opener.open(req, timeout=45)
    except urllib.error.HTTPError as exc:
        response = exc
    except Exception as exc:
        entry.update(status=None, error=str(exc), bytes=0)
        ledger.append(entry)
        ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(entry, ensure_ascii=False))
        return
    with response:
        entry['status'] = response.code
        entry['content_type'] = response.headers.get('Content-Type')
        entry['location'] = response.headers.get('Location')
        data = response.read(CAP)
        # Do not make a second read beyond the declared per-response byte cap.
        entry['bytes'] = len(data)
        entry['at_cap_possibly_truncated'] = len(data) == CAP
        entry['sha256'] = hashlib.sha256(data).hexdigest()
        entry['path'] = str(OUT / (name + '.body'))
        (OUT / (name + '.body')).write_bytes(data)
    ledger.append(entry)
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(entry, ensure_ascii=False))


if __name__ == '__main__':
    fetch(sys.argv[1], sys.argv[2])
