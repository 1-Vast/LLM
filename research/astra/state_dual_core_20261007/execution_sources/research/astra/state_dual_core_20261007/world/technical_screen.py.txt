"""A distinct exploratory disjoint-cell screen, not an independent culture test.

Freeze the new cell split before reading its values. This does not overwrite H1
outcomes or change the earlier registered world-model prediction endpoint.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

import h5py
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
sys.path.insert(0, str(ROOT / "src"))
from virtual_cell.state_runner import _column

def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

started = time.perf_counter()
contract = json.loads((OUT / "contract.json").read_text())
old_plan = json.loads((OUT / "metadata_freeze.json").read_text())
path = Path(contract["hashes"]["dataset"]["path"])
with h5py.File(path, "r") as f:
    ids = _column(f["obs"], f["obs"].attrs["_index"])
    records = []
    for condition in old_plan["conditions"]:
        if condition["dose_uM"] != 5.0:
            continue
        ordered = sorted(condition["treated_rows"], key=lambda i: hashlib.sha256(("technical-screen-v1:" + str(ids[i])).encode()).hexdigest())
        screen, validation = sorted(ordered[::2]), sorted(ordered[1::2])
        assert len(screen) >= 2 and len(validation) >= 2 and not set(screen) & set(validation)
        records.append({**{k: v for k, v in condition.items() if k != "treated_rows"},
                        "screen_rows": screen, "validation_rows": validation,
                        "screen_cell_ids": [str(ids[i]) for i in screen],
                        "validation_cell_ids": [str(ids[i]) for i in validation],
                        "screen_n": len(screen), "validation_n": len(validation)})
    freeze = {"created_at_utc": datetime.now(timezone.utc).isoformat(),
              "purpose": "exploratory technical screen acquisition after cross-dose menu failed development gate",
              "protocol_status": "distinct secondary decision task; H1 protocol and outcomes unchanged",
              "source_sha256": contract["hashes"]["dataset"]["sha256"],
              "source_previously_exposed": True,
              "split_rule": "SHA256(technical-screen-v1:+source_cell_id), alternating disjoint halves",
              "reference": "same fixed held-out reference control half as original outcome, shared across screen/validation",
              "endpoint": "RMS mean native X_hvg difference from fixed same-plate reference mean",
              "independence": "cell-disjoint technical validation only; same drug/culture source and shared denominator",
              "decision_unit": "chemical-group candidate comparisons; cell halves are not independent biological replicates",
              "rows": records, "source_code_sha256": sha(Path(__file__))}
    freeze_path = OUT / "technical_screen_freeze.json"
    if freeze_path.exists():
        raise FileExistsError("preserve completed technical screen freeze; reproduce in separate study copy")
    write(freeze_path, freeze)
    write(OUT / "technical_screen_freeze_receipt.json", {"sha256": sha(freeze_path),
          "created_before_split_values_read": True, "existing_full_outcomes_previously_read": True})
    # First numerical reads for the newly frozen cell split occur below.
    reference = {plate: np.asarray(f["obsm"]["X_hvg"][c["reference_rows"]]).mean(0)
                 for plate, c in old_plan["controls"].items()}
    values = {}
    for which in ("screen", "validation"):
        deltas = np.asarray([np.asarray(f["obsm"]["X_hvg"][r[which + "_rows"]]).mean(0) - reference[r["plate"]]
                             for r in records])
        values[which] = np.sqrt(np.mean(deltas ** 2, axis=1))
        np.savez_compressed(OUT / ("technical_" + which + "_values.npz"),
                            **{which + "_magnitude": values[which], which + "_delta": deltas,
                               "condition_id": np.asarray([r["condition_id"] for r in records])})
pd.DataFrame([{k: v for k, v in r.items() if not k.endswith("_rows") and not k.endswith("_cell_ids")}
              for r in records]).to_csv(OUT / "technical_screen_metadata.csv", index=False)
write(OUT / "technical_screen_receipt.json", {"freeze_sha256": sha(freeze_path),
      "metadata_sha256": sha(OUT / "technical_screen_metadata.csv"),
      "screen_sha256": sha(OUT / "technical_screen_values.npz"),
      "validation_sha256": sha(OUT / "technical_validation_values.npz"),
      "chemical_groups": len(records), "min_screen_cells": min(r["screen_n"] for r in records),
      "min_validation_cells": min(r["validation_n"] for r in records), "all_cells_disjoint": True,
      "elapsed_seconds": time.perf_counter() - started, "api_calls": 0, "api_cost_usd": 0.0,
      "downloaded_bytes": 0, "new_wet_measurements": 0, "local_financial_cost_usd": None})
print(json.dumps({"completed": True, "chemical_groups": len(records), "all_cells_disjoint": True,
                  "freeze_sha256": sha(freeze_path), "evaluation_values_printed": False}))
