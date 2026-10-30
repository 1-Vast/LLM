"""Bounded read-only source provenance check; author code is never imported."""
from pathlib import Path
import hashlib
import json
import time
import requests

ROOT = Path(__file__).resolve().parent / "wu_source"
ROOT.mkdir(exist_ok=True)
LEDGER = ROOT / "requests.jsonl"


def fetch(url, name):
    started = time.monotonic()
    response = requests.get(url, timeout=30, allow_redirects=False)
    body = response.content
    if len(body) > 10_000_000:
        raise RuntimeError("Source response exceeds 10 MB allocation")
    path = ROOT / name
    path.write_bytes(body)
    record = {"url": url, "status": response.status_code, "bytes": len(body),
              "sha256": hashlib.sha256(body).hexdigest(), "path": str(path),
              "seconds": time.monotonic() - started, "retries": 0}
    with LEDGER.open("a", encoding="utf-8") as out:
        out.write(json.dumps(record) + "\n")
    if response.status_code != 200:
        return None
    return json.loads(body)


if __name__ == "__main__":
    repo = "chenyuwu233/Cancer-Stem-Cells-Drug-induced-Plasticity"
    meta = fetch("https://api.github.com/repos/" + repo, "repository.json")
    if meta:
        branch = meta["default_branch"]
        time.sleep(1.1)
        commit = fetch("https://api.github.com/repos/" + repo + "/commits/" + branch, "commit.json")
        if commit:
            time.sleep(1.1)
            tree = fetch("https://api.github.com/repos/" + repo + "/git/trees/" + commit["sha"] + "?recursive=1", "tree.json")
            if tree:
                rows = [{"path": r["path"], "bytes": r.get("size"), "sha": r["sha"]}
                        for r in tree["tree"] if r["type"] == "blob"]
                print(json.dumps({"commit": commit["sha"], "files": len(rows),
                                  "source_files": [r for r in rows if Path(r["path"]).suffix in [".py", ".R", ".m", ".jl"] or "readme" in r["path"].lower()]}, indent=2))
