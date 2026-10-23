import datetime
import hashlib
import json
import pathlib
import urllib.error
import urllib.request

ROOT = pathlib.Path('log/20261023/cross_context_interaction/critic')
ROOT.mkdir(parents=True, exist_ok=True)

def fetch(name, url):
    request = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO research primary-source check'})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read()
            status = response.status
    except urllib.error.HTTPError as error:
        body, status = error.read(), error.code
    except Exception as error:
        receipt = {'url': url, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'error': repr(error)}
        (ROOT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        return receipt
    (ROOT / (name + '.body')).write_bytes(body)
    receipt = {'url': url, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': status, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
    (ROOT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt

if __name__ == '__main__':
    import sys
    print(json.dumps(fetch(sys.argv[1], sys.argv[2])))
