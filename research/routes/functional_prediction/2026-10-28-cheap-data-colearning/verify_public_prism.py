"""One public repository metadata check; do not download response values."""
from pathlib import Path
import hashlib
import json
import time
import urllib.error
import urllib.request

out = Path(__file__).resolve().parent / "sources/public_prism"
out.mkdir(parents=True, exist_ok=True)
path = out / "receipt.json"
assert not path.exists(), "No automatic retry"
url = "https://api.figshare.com/v2/articles/10355393"
receipt = {"url": url, "purpose": "Check candidate public PRISM19Q4 release identity and direct file availability; metadata only",
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "timeout_seconds": 25,
           "max_bytes": 3000000, "retries": 0}
path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
try:
    with urllib.request.urlopen(url, timeout=25) as response:
        raw = response.read(3000001)
        assert len(raw) <= 3000000
        receipt.update(status=response.status, content_type=response.headers.get("Content-Type"), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    (out / "article.json").write_bytes(raw)
    article = json.loads(raw)
    receipt.update(title=article.get("title"), doi=article.get("doi"), license=article.get("license"),
                   article_url=article.get("url_public_html"),
                   files=[{key: item.get(key) for key in ("id", "name", "size", "download_url", "computed_md5", "is_link_only")} for item in article.get("files", [])])
except urllib.error.HTTPError as error:
    receipt.update(status=error.code, error=str(error))
except Exception as error:
    receipt["error"] = type(error).__name__ + ": " + str(error)
path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt, ensure_ascii=False, indent=2))
