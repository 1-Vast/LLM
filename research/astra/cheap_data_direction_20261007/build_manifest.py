"""Inventory actual source receipts and exact research artifacts without fetching outcomes."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    files = sorted(path for path in HERE.rglob("*") if path.is_file()
                   and path.name != "RUN_MANIFEST.json" and "__pycache__" not in path.parts)
    receipts = []
    for path in sorted(HERE.glob("*_RECEIPTS.json")):
        receipts.extend(json.loads(path.read_text(encoding="utf-8")))
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Affordable-data qualification, primary-literature review and independent development audit",
        "new_asset": "44,235-byte Enrichr Hallmark library; 39 verified native coordinates",
        "new_outcome_dataset_downloads": 0,
        "retrieval_attempts": len(receipts),
        "successful_responses": sum(row["status"] == 200 for row in receipts),
        "successful_payload_bytes": sum(row.get("bytes", 0) for row in receipts if row["status"] == 200),
        "billing_and_wire_overhead": "Not estimated; counts are successful retained response payloads",
        "reused_observations": "45 training-reference, two exposed development and three previously exposed exploratory task-transfer contexts; no fresh outcome holdout",
        "sealed_outcomes_opened": False,
        "model_checkpoint": "arcinstitute/ST-HVG-Tahoe@ca6b751972493f8448e3256d1340ae70ad43e1e7 zeroshot final.ckpt",
        "scientific_limits": "RNA target direction only; neither phenotype/mechanism calibration nor independently confirmed agent advantage",
        "commands": [
            "D:/anaconda/envs/maestro/python.exe research/astra/cheap_data_direction_20261007/verify_direction.py",
            "D:/anaconda/envs/maestro/python.exe research/astra/cheap_data_direction_20261007/verify_followups.py",
            "D:/anaconda/envs/maestro/python.exe research/astra/cheap_data_direction_20261007/summarize_frontier.py",
            "D:/anaconda/envs/maestro/python.exe research/astra/cheap_data_direction_20261007/verify_transfer.py",
            "D:/anaconda/envs/maestro/python.exe research/astra/cheap_data_direction_20261007/build_manifest.py",
        ],
        "immutable_outputs": "Verifier refuses overwrite; use a new verified artifact name for future independent audit",
        "artifacts": [
            {"path": path.relative_to(HERE).as_posix(), "bytes": path.stat().st_size,
             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in files
        ],
    }
    target = HERE / "RUN_MANIFEST.json"
    with target.open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, allow_nan=False); handle.write("\n")
    print(json.dumps({key: value for key, value in manifest.items() if key != "artifacts"}, indent=2))


if __name__ == "__main__":
    main()
