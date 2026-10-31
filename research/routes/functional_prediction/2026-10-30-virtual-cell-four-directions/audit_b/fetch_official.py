"""Bounded official-source retrieval; never fetches LaTest or evaluation labels."""
import concurrent.futures
import hashlib
import json
import pathlib
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

AUDIT = pathlib.Path(__file__).resolve().parent
DOWNLOADS = pathlib.Path("D:/MAESTRO/data/external/virtual_cell_four_directions_20261030/assaybench")
DOWNLOADS.mkdir(parents=True, exist_ok=True)
LOG = AUDIT / "requests.jsonl"


def fetch(item):
    name, url, cap = item
    entry = {"time_utc": datetime.now(timezone.utc).isoformat(), "url": url, "file": name, "cap_bytes": cap}
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "MAESTRO-source-audit/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read(cap + 1)
            entry.update(status=response.status, final_url=response.url, bytes_received=len(body), content_type=response.headers.get("Content-Type"))
        if len(body) > cap:
            entry["outcome"] = "over_cap_not_saved"
        else:
            path = DOWNLOADS / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            entry.update(outcome="saved", sha256=hashlib.sha256(body).hexdigest(), saved_bytes=len(body))
    except Exception as error:
        entry.update(outcome="error", error=repr(error), bytes_received=0)
    return entry


if __name__ == "__main__":
    # Explicit manifests keep source acquisition reviewable and avoid split discovery by reading labels.
    manifest = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        entries = list(pool.map(fetch, manifest))
    with LOG.open("a", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry) + "\n")
            print(json.dumps(entry))
