"""Bounded primary-source retrieval; never retrieves numerical assay tables."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import urllib.request

p = argparse.ArgumentParser()
p.add_argument("name")
p.add_argument("url")
a = p.parse_args()
out = Path("log/20261023/post_anchor_mechanism/constructive")
out.mkdir(parents=True, exist_ok=True)
target = out / (a.name + ".body")
assert not target.exists()
start = time.time()
try:
    with urllib.request.urlopen(a.url, timeout=45) as r:
        body = r.read()
        status, final = r.status, r.url
except Exception as e:
    body = getattr(e, "read", lambda: b"")()
    status, final = getattr(e, "code", None), a.url
    failure = repr(e)
else:
    failure = None
target.write_bytes(body)
receipt = dict(url=a.url, final_url=final, status=status, error=failure,
               start_unix=start, wall=time.time()-start, bytes=len(body),
               sha256=hashlib.sha256(body).hexdigest())
(out / (a.name + ".receipt.json")).write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(json.dumps(receipt))
