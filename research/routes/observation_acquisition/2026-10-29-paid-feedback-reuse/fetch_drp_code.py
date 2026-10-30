"""Bounded public retrieval of an already primary-verified official code link."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import urllib.request

HERE = Path(__file__).resolve().parent / "sources"
HERE.mkdir(exist_ok=True)
REPO = "abbiAR/-Strategic-Cell-Line-and-Compound-Selection-Using-Drug-Response-Profiles"


def get(url, name, cap):
    dest = HERE / name
    receipt = HERE / (name + ".receipt.json")
    assert not dest.exists() and not receipt.exists(), "No retry or replacement"
    record = {"url": url, "started_utc": datetime.now(timezone.utc).isoformat(),
              "timeout_seconds": 30, "max_bytes": cap, "retries": 0,
              "purpose": "Known official DRP code identity/version; read only, not execution"}
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "MAESTRO-evidence-research", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read(cap+1)
            assert len(data) <= cap, "Download cap exceeded"
            record.update(status=response.status, final_url=response.url,
                          content_type=response.headers.get("Content-Type"), bytes=len(data),
                          sha256=hashlib.sha256(data).hexdigest())
        dest.write_bytes(data)
    except Exception as exc:
        record.update(error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        receipt.write_text(json.dumps(record, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        print(json.dumps(record))
    return data


if __name__ == "__main__":
    meta = json.loads(get("https://api.github.com/repos/"+REPO, "drp_repo.json", 600000))
    commit = json.loads(get("https://api.github.com/repos/"+REPO+"/commits/"+meta["default_branch"], "drp_commit.json", 1000000))
    get("https://api.github.com/repos/"+REPO+"/tarball/"+commit["sha"], "drp_code.tar.gz", 10000000)
