"""One permitted, bounded source-file GET, no redirects or retries."""
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request
from datetime import datetime, timezone

BASE = Path('log/20261022/intervention_dynamics_renewal/melanoma_sequence')
URL = 'https://zenodo.org/api/records/18962045/files/Suppl%20Data%2003.xlsx/content'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    BASE.mkdir(parents=True, exist_ok=True)
    receipt_path = BASE / 'RECEIPT.json'
    if receipt_path.exists():
        raise RuntimeError('One-GET acquisition already attempted; no repeat allowed')
    receipt = {'method': 'GET', 'url': URL, 'utc_start': datetime.now(timezone.utc).isoformat(),
               'timeout_seconds': 25, 'cap_bytes': 100000, 'redirects': False, 'retries': 0}
    # Persist attempted state before touching the network.
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    try:
        opener = urllib.request.build_opener(NoRedirect())
        req = urllib.request.Request(URL, headers={'User-Agent': 'MAESTRO-readonly-source-audit/1.0'})
        try:
            response = opener.open(req, timeout=25)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            body = response.read(100000)
            receipt.update(status=response.code, content_type=response.headers.get('Content-Type'),
                           location=response.headers.get('Location'), bytes=len(body),
                           at_cap_possibly_truncated=len(body) == 100000,
                           md5=hashlib.md5(body).hexdigest(), sha256=hashlib.sha256(body).hexdigest())
            path = BASE / ('Suppl Data 03.xlsx' if response.code == 200 else 'RESPONSE.body')
            path.write_bytes(body)
            receipt['body_file'] = str(path)
            receipt['manifest_size_match'] = len(body) == 13994
            receipt['manifest_md5_match'] = receipt['md5'] == '61e96850942060d93915800cd08946dc'
    except Exception as exc:
        receipt['error'] = repr(exc)
    receipt['utc_end'] = datetime.now(timezone.utc).isoformat()
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
