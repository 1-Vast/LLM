"""Read only exact official metadata URLs. Do not load any response matrix."""
from pathlib import Path
import hashlib
import json
import urllib.request
import datetime

HERE = Path(__file__).resolve().parent
OUT = HERE / 'sources'
OUT.mkdir(exist_ok=True)

def fetch(url, filename, limit=3_000_000):
    request = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO-public-metadata-audit/1.0'})
    receipt = {'url': url, 'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'limit_bytes': limit, 'response_values_read': False}
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            receipt.update(status=response.status, final_url=response.url,
                           content_type=response.headers.get('Content-Type'))
            data = response.read(limit + 1)
            if len(data) > limit:
                raise ValueError('Metadata size cap exceeded; not saved')
        (OUT / filename).write_bytes(data)
        receipt.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), saved=filename)
    except Exception as error:
        receipt['error'] = str(error)
        data = None
    (OUT / (filename + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return data

if __name__ == '__main__':
    for record_id in ('12764821', '12765294', '13871987'):
        raw = fetch('https://zenodo.org/api/records/' + record_id, 'zenodo_' + record_id + '.json')
        if raw:
            obj = json.loads(raw)
            print(json.dumps({'id': record_id, 'title': obj.get('metadata', {}).get('title'),
                              'description': obj.get('metadata', {}).get('description'),
                              'files': [{k: f.get(k) for k in ('key', 'size', 'links')} for f in obj.get('files', [])]}, ensure_ascii=False))
