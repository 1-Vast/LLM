"""Small primary-source lineage follow-up; no feature/response downloads."""
import hashlib
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261021/autonomous_rsi_round1/data_auditor_lineage"
COMMIT = "ca4872de0f1f0a4f203bee41271a6512b314a076"
PATHS = ["1_snakemake/Snakefile", "1_snakemake/inputs/conf/cpcnn.json", "1_snakemake/preprocessing/normalize.py"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "RECEIPTS.json").exists():
        raise RuntimeError("Source lineage receipts already exist")
    receipts = []
    urls = [(f"https://raw.githubusercontent.com/broadinstitute/2024_09_09_Axiom_OASIS/{COMMIT}/{p}", p.replace("/", "__")) for p in PATHS]
    urls.append(("https://zenodo.org/api/records/7114558", "CHECKPOINT_METADATA.json"))
    for url, filename in urls:
        response = requests.get(url, timeout=40)
        response.raise_for_status()
        body = response.content
        if sum(x["bytes"] for x in receipts) + len(body) > 500_000:
            raise RuntimeError("Lineage source budget exceeded")
        (OUT / filename).write_bytes(body)
        receipts.append({"url": url, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
        (OUT / "RECEIPTS.json").write_text(json.dumps(receipts, indent=2), encoding="utf-8")
    print(json.dumps(receipts, indent=2))


if __name__ == "__main__":
    main()
