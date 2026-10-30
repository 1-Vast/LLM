"""Resolve a verified title/author preprint lead once; keep version provenance."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib
import json
import time
import urllib.error
import urllib.request

out = Path(__file__).resolve().parent / "sources/public_version_check"
assert not (out / "preprint_receipt.json").exists(), "No automatic replay"
url = "https://doi.org/10.64898/2026.06.09.731253"
receipt = {"url": url, "timeout_seconds": 25, "max_bytes": 10000000, "retries": 0,
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "identity_basis": "EuropePMC title-first-author match; full version identity not yet verified"}
try:
    with urllib.request.urlopen(url, timeout=25) as response:
        raw = response.read(10000001)
        assert len(raw) <= 10000000
        receipt.update(status=response.status, final_url=response.url, content_type=response.headers.get("Content-Type"), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    (out / "preprint_response.html").write_bytes(raw)
    class Metadata(HTMLParser):
        def __init__(self): super().__init__(); self.meta=[]; self.links=[]
        def handle_starttag(self, tag, attrs):
            d = dict(attrs)
            if tag == "meta" and d.get("name", "").startswith("citation_"): self.meta.append(d)
            if tag == "a" and any(term in d.get("href", "").lower() for term in ("suppl", "dc1", "media-")): self.links.append(d["href"])
    parser = Metadata(); parser.feed(raw.decode("utf-8", errors="replace"))
    receipt.update(citation_meta=parser.meta, supplementary_links=parser.links)
except urllib.error.HTTPError as error:
    raw = error.read(1000000)
    (out / "preprint_error_response.bin").write_bytes(raw)
    receipt.update(status=error.code, final_url=error.url, error=str(error), content_type=error.headers.get("Content-Type"), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
except Exception as error:
    receipt["error"] = type(error).__name__ + ": " + str(error)
(out / "preprint_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt, ensure_ascii=False, indent=2))
