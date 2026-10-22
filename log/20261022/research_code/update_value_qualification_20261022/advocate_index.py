"""Verify newly fetched and reused primary-source receipts, without biological data."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/update_value_qualification/advocate"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    target = OUT / "SOURCE_INDEX.json"
    if target.exists():
        raise RuntimeError("Do not overwrite source qualification history")
    receipts = [json.loads(line) for line in (OUT / "HTTP_RECEIPTS.jsonl").read_text().splitlines()]
    for receipt in receipts:
        path = ROOT / receipt["body_path"]
        if sha(path) != receipt["sha256"] or path.stat().st_size != receipt["bytes"]:
            raise ValueError("Saved public-source receipt mismatch")
    ns = {"a": "http://www.w3.org/2005/Atom"}
    atom = ET.fromstring((OUT / "predecessor_metadata.body").read_bytes())
    metadata = [{key: entry.findtext("a:" + key, namespaces=ns)
                 for key in ("id", "title", "published", "updated", "summary")}
                for entry in atom.findall("a:entry", ns)]
    reuse = [
        "log/20261022/az_paid_reference_gate/DECISION.md",
        "log/20261022/rsi_later_task_literature/DECISION.md",
        "log/20261022/update_value_qualification/PROTOCOL.md",
        "log/20261022/rsi_later_task_literature/data/cellflow_dataset_code.body",
        "log/20261022/rsi_later_task_literature/data/cellflow_dataset_code.http.json",
        "log/20261022/rsi_later_task_literature/data/cellflow_asset_manifest.body",
        "log/20261022/rsi_later_task_literature/data/cellflow_asset_manifest.http.json",
        "log/20261022/rsi_later_task_literature/advocate/INDEPENDENT.md",
        "log/20261022/rsi_later_task_literature/skeptic/INDEPENDENT.md",
    ]
    reuse_hashes = {name: sha(ROOT / name) for name in reuse}
    for body, receipt in ((reuse[3], reuse[4]), (reuse[5], reuse[6])):
        expected = json.loads((ROOT / receipt).read_text())["sha256"]
        if reuse_hashes[body] != expected:
            raise ValueError("Reused author-source body changed since original receipt")
    result = {"utc": datetime.now(timezone.utc).isoformat(), "new_http_gets": len(receipts),
              "new_body_hashes_verified": len(receipts), "receipts": receipts,
              "metadata": metadata, "reused_local_sources": reuse_hashes,
              "body_claim_scope": "Three original papers inspected as ar5iv HTML transcriptions, not numerical reproductions. Latest versions independently checked in arXiv metadata. 2026 learned-optimizer metadata and the existing prior audit are reused; its body was not fetched anew.",
              "research_data_or_targets_read": False, "new_model_fits": 0,
              "deepseek_or_other_provider_calls": 0}
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"new_gets": len(receipts), "statuses": [r["status"] for r in receipts],
                      "hashes_verified": len(receipts), "metadata_works": len(metadata),
                      "reused_author_bodies_verified": 2}))


if __name__ == "__main__":
    main()
