"""Bounded official source-code receipts; no expression requests."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen


HERE = Path(__file__).resolve().parent
CAP = 5_000_000
COMMIT = "4f4123d9e1ac6a02e2447935ba47b04fc2f061f8"


def main():
    receipts, used = [], 0

    def get(name, url):
        nonlocal used
        receipt = dict(name=name, requested_url=url, retrieved_utc=datetime.now(timezone.utc).isoformat())
        try:
            with urlopen(Request(url, headers={"User-Agent": "MAESTRO-P05R-method-audit/1.0"}), timeout=40) as response:
                body = response.read(CAP-used+1)
                if len(body) > CAP-used:
                    raise ValueError("five_MB_source_method_cap_exceeded")
                receipt.update(http_status=response.status, final_url=response.url)
            used += len(body)
            path = HERE / "sources" / name
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(body)
            receipt.update(status="RECEIVED", path=path.relative_to(HERE).as_posix(), bytes=len(body),
                           sha256=hashlib.sha256(body).hexdigest())
        except Exception as exc:
            receipt.update(status="FETCH_FAILED", error=f"{type(exc).__name__}: {exc}")
        receipts.append(receipt)
        return body if receipt["status"] == "RECEIVED" else None

    tree = get("OFFICIAL_TREE.json", f"https://api.github.com/repos/goodarzilab/tahoe100m_analysis/git/trees/{COMMIT}?recursive=1")
    if tree is not None:
        paths = [entry["path"] for entry in json.loads(tree)["tree"]]
        wanted = [path for path in paths if path.endswith("pseudobulk_correlation.py")]
        wanted += [path for path in ("README.md", "docs/METHODS_metrics.md", "CITATION.cff") if path in paths]
        for path in wanted:
            get(path.replace("/", "__"), f"https://raw.githubusercontent.com/goodarzilab/tahoe100m_analysis/{COMMIT}/{path}")
    output = dict(schema="official_method_sources_v1", pinned_commit=COMMIT, network_body_cap=CAP,
                  successful_body_bytes=used, receipts=receipts, treated_expression_bytes=0,
                  notes="Success body bytes only; failed error bodies not retained or measured. No RNA or model inference.")
    (HERE / "FETCH_RECEIPTS.json").write_text(json.dumps(output, indent=2)+"\n", encoding="utf-8")
    for item in receipts:
        print(item["name"], item["status"], item.get("bytes", item.get("error")))


if __name__ == "__main__":
    main()
