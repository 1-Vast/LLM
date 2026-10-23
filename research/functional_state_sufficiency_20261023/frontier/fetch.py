import sys, pathlib, datetime, hashlib, json
import requests

out = pathlib.Path('log/20261023/functional_state_sufficiency/frontier')
name, url = sys.argv[1:]
r = requests.get(url, timeout=70)
body = r.content
(out / (name + '.body')).write_bytes(body)
(out / (name + '.receipt.json')).write_text(json.dumps(dict(url=url, final_url=r.url, status=r.status_code, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), bytes=len(body), sha256=hashlib.sha256(body).hexdigest()), indent=2), encoding='utf-8')
print(r.status_code, len(body))
