"""Write WORLD_PROTOCOL.json from development results only, then WORLD_FREEZE.json with its hash.

Run once, after world_dev.py and before any evaluation-line observation is built or read.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import world_models as wm  # noqa: E402


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if (HERE / "WORLD_FREEZE.json").exists():
        raise FileExistsError("world protocol already frozen")
    dev = json.loads((HERE / "world_dev" / "DEV_RESULTS.json").read_text(encoding="utf-8"))
    gs = dev["M2"]["selected_gamma_S"]
    protocol = {
        "study": "zeroshot_context_20261007", "created_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_lines": wm.SPLIT["evaluation"], "development_lines": wm.SPLIT["development"],
        "split_sha256": sha(HERE / "SPLIT.json"),
        "training_contexts": wm.TRAIN_FILES,
        "eligibility": {"min_treated_cells": wm.MIN_TREATED, "min_reference_cells": wm.MIN_REFERENCE,
                        "min_panel_contexts": wm.MIN_PANEL_LINES, "min_panel_cells": wm.MIN_PANEL_CELLS},
        "endpoint": "per (label, plate) group: mean over sampled full-QC treated cells minus mean over reference-half same-plate DMSO cells, 2,000 native X_hvg coordinates",
        "error": "depth-corrected squared error averaged over coordinates (subtracts the forecast's own panel sampling variance and the held-out observation's sampling variance)",
        "choices": {"M0_variant": dev["M0"]["selected"], "M1_family": dev["M1"]["selected_family"],
                    "gamma_K": dev["M1"]["selected_gamma_K"], "gamma_S": gs, "gamma_S_on_M1": dev["M21"]["selected_gamma_S"],
                    "krr_lambda": dev["krr_lambda"]["selected"], "gamma_for_controls": gs if gs > 0 else 1.0},
        "delta_min": dev["delta_min"]["value"], "delta_min_formula": dev["delta_min"]["formula"],
        "permutation_seed": 20261007,
        "H1_criteria": ["mean(M2 - M0) <= -delta_min", "drug-clustered 95% CI of M2 - M0 below zero",
                        "M2 - M0 below zero in every evaluation line", "CI of M21 - M1 below zero",
                        "CI of M2(controls gamma) - line-swap below zero"],
        "controls": {"line_swap": "devS of the next evaluation line in SPLIT order",
                     "permutation": "devS permuted within (dose, plate) strata, seed 20261007"},
        "development_results_sha256": sha(HERE / "world_dev" / "DEV_RESULTS.json"),
        "code_sha256": {p.name: sha(p) for p in sorted(HERE.glob("*.py")) if not p.name.startswith("test_")},
        "state_forecast_receipts_sha256": {p.name: sha(p) for p in sorted((HERE / "state_forecasts").glob("*.receipt.json"))},
        "extraction_receipts_sha256": {p.name: sha(p) for p in sorted((HERE / "extract").glob("*.receipt.json"))},
        "evaluation_observations_built_before_freeze": False,
    }
    (HERE / "WORLD_PROTOCOL.json").write_text(json.dumps(protocol, indent=1), encoding="utf-8")
    freeze = {"protocol_sha256": sha(HERE / "WORLD_PROTOCOL.json"), "frozen_utc": datetime.now(timezone.utc).isoformat(),
              "evaluation_lines_read": False}
    (HERE / "WORLD_FREEZE.json").write_text(json.dumps(freeze, indent=1), encoding="utf-8")
    print(json.dumps({"choices": protocol["choices"], "delta_min": protocol["delta_min"], **freeze}, indent=1))


if __name__ == "__main__":
    main()
