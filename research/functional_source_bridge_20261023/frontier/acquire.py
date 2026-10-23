from pathlib import Path
import datetime, hashlib, json, urllib.request, urllib.error

ROOT = Path('log/20261023/functional_source_bridge/frontier')
ROOT.mkdir(parents=True, exist_ok=True)

def fetch(name, url):
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'MAESTRO source qualification/1.0'}), timeout=60) as r:
            body, status, final, headers = r.read(), r.status, r.url, dict(r.headers)
    except urllib.error.HTTPError as e:
        body, status, final, headers = e.read(), e.code, e.url, dict(e.headers)
    except Exception as e:
        receipt = {'url': url, 'start': start, 'end': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'error': repr(e), 'body_bytes': None}
        (ROOT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        print(json.dumps(receipt))
        return
    (ROOT / (name + '.body')).write_bytes(body)
    receipt = {'url': url, 'final_url': final, 'status': status, 'headers': headers, 'start': start, 'end': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'body_bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
    (ROOT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k != 'headers'}))

if __name__ == '__main__':
    import sys
    fetch(sys.argv[1], sys.argv[2])
