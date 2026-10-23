"""Outcome-blind metadata/source-code audit; no phenotype payload access."""
from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261021/autonomous_rsi_round1/data_auditor_sources"
COMMIT = "ca4872de0f1f0a4f203bee41271a6512b314a076"
MAX_BYTES = 1_000_000


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "RECEIPTS.json").exists():
        raise RuntimeError("Audit already recorded; inspect saved source snapshots")
    receipts = []
    def get(url, filename):
        response = requests.get(url, timeout=40)
        data = response.content
        if sum(x["bytes"] for x in receipts) + len(data) > MAX_BYTES:
            raise RuntimeError("Metadata/source-code payload budget exceeded")
        response.raise_for_status()
        (OUT / filename).write_bytes(data)
        receipts.append({"url": url, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        (OUT / "RECEIPTS.json").write_text(json.dumps(receipts, indent=2), encoding="utf-8")
        return response.json() if filename.endswith(".json") else data.decode("utf-8")
    zenodo = get("https://zenodo.org/api/records/17067683", "ZENODO.json")
    files = [{"name": x["key"], "bytes": x["size"], "checksum": x["checksum"], "url": x["links"]["self"]} for x in zenodo["files"]]
    (OUT / "FILE_CATALOGUE.json").write_text(json.dumps(files, indent=2), encoding="utf-8")
    tree = get(f"https://api.github.com/repos/broadinstitute/2024_09_09_Axiom_OASIS/git/trees/{COMMIT}?recursive=1", "TREE.json")
    paths = [x["path"] for x in tree["tree"] if x["type"] == "blob" and x["path"].startswith("0_prepare_data/") and x["path"].endswith(".py")]
    for path in paths:
        get(f"https://raw.githubusercontent.com/broadinstitute/2024_09_09_Axiom_OASIS/{COMMIT}/{path}", path.replace("/", "__"))
    reservation = json.loads((ROOT / "log/20261021/oasis_evaluation_contract/RESERVATION_v2.json").read_text())
    role = {x["compound_id"]: x["role"] for x in reservation["mapping"]}
    paired = json.loads((ROOT / "log/20261021/oasis_identity_qualification/PAIRED_IDENTITIES.json").read_text())
    raw = json.loads((ROOT / "log/20261021/oasis_identity_qualification/IDENTITY_ROWS.json").read_text())
    summary = {}
    for current in ("dev", "selection", "reserve", "quarantine"):
        rows = [x for x in paired if x["is_oasis"] and not x["is_dmso"] and role.get(x["compound_id"]) == current]
        actions = collections.Counter((x["compound_id"], x["dose_um"]) for x in rows)
        summary[current] = {"paired_unique_wells": len(rows), "paired_actions": len(actions), "labels": len({x["compound_id"] for x in rows}), "physical_wells_per_action": dict(collections.Counter(actions.values()))}
    unique_raw = {(x["source"], x["plate"], x["well_normalized"]): x for x in raw}
    dev_plates = {(x["batch"], x["plate"]) for x in paired if role.get(x["compound_id"]) == "dev"}
    controls = [x for x in unique_raw.values() if str(x["compound_name"]).upper() == "DMSO" and (str(x["source"]).removeprefix("assayworks_"), x["plate"]) in dev_plates]
    summary["controls_on_dev_plates"] = {"physical_wells": len(controls), "plates": len({(x["source"], x["plate"]) for x in controls}), "control_counts_per_plate": dict(collections.Counter(collections.Counter((x["source"], x["plate"]) for x in controls).values()))}
    summary["scope"] = "Existing exported identity rows only; no raw outcome/count/morphology values opened"
    (OUT / "IDENTITY_FEASIBILITY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"files": files, "identity_summary": summary, "source_bytes": sum(x["bytes"] for x in receipts)}, indent=2))


if __name__ == "__main__":
    main()
