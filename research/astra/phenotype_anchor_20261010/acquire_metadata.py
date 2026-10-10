"""Re-acquire pinned Tahoe-100M drug/cell metadata; refuse any byte change from the 2026-10-01 receipt."""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "data/external/tahoe_phenotype_20261010/metadata"
PRIOR = ROOT / "tools/datasets/audit_results/20261001_state_prospective/knowledge_sources/receipts.json"
WANTED = ("tahoe_drugs", "tahoe_cells")


def main():
    prior = {r["id"]: r for r in json.loads(PRIOR.read_text(encoding="utf-8"))}
    OUT.mkdir(parents=True, exist_ok=True)
    receipts = []
    for key in WANTED:
        url, expected = prior[key]["url"], prior[key]["sha256"]
        started = time.perf_counter()
        body = requests.get(url, timeout=120).content
        actual = hashlib.sha256(body).hexdigest()
        if actual != expected:
            raise SystemExit(f"{key}: sha256 {actual} differs from pinned {expected}")
        path = OUT / f"{key}.parquet"
        path.write_bytes(body)
        receipts.append({"id": key, "url": url, "sha256": actual, "bytes": len(body), "path": str(path.relative_to(ROOT)),
                         "seconds": round(time.perf_counter() - started, 3), "retrieved_utc": datetime.now(timezone.utc).isoformat()})
    (HERE / "METADATA_RECEIPTS.json").write_text(json.dumps(receipts, indent=1), encoding="utf-8")
    print(json.dumps(receipts, indent=1))


if __name__ == "__main__":
    main()
