"""Post-opening correction: score the locked choices under the registered endpoint (disclosed in DEVIATIONS.json).

File summary
- Path: research/selective_hit_triage_20261013/evaluate_registered.py
- Purpose: repair one implementation error in the frozen outcome reader, without editing any frozen
  file, and rescore every registered arm and contrast.
- The error: `outcomes.qualified_outcomes` guesses the unit of CTRP v2 `pred_pv_high_conc` per split:
  - it assumes percent when any value exceeds 2;
  - the test split holds 4 overgrowth curves (maximum 2.66), so every test viability was divided by
    100;
  - the "top-dose viability at most 50%" half of the VALIDATED rule therefore always passed, and
    every compound read as PAN_ACTIVE;
  - the development split (maximum 1.93) was read correctly.
- The fix leaves no free choice: the column is a fraction, as development already used.
- Core points:
  - The frozen reader still opens the outcomes, so the freeze and archive checks run.
  - `fraction_viability` re-reads the archive with the frozen reader's own grouping. It gives the
    exact mean top-dose viability per pair as a fraction. Restoring by x100 cannot be used: raw
    values sit exactly on 0.5, and the round trip blurs them.
  - Every pair must agree with the frozen reader: same compounds, lines and AUC z, and fraction
    equal to as-run x scale to 1e-12. Otherwise READER_MISMATCH.
  - Validated and pan-active flags are then recomputed with the frozen ENDPOINT thresholds.
  - Then the frozen `evaluate.build` runs unchanged.
  - Write-once: TEST_RESULTS_REGISTERED.json. A rerun must reproduce it. TEST_RESULTS.json
    (as run, AUC-z-only endpoint) is kept as written.
- Interfaces: `fraction_viability`, `registered_outcomes`, `main`.
"""
from __future__ import annotations

import io
import json
import zipfile

import numpy as np
import pandas as pd

from arms import load_table
from census import CCLE, CTRP_ZIP, HERE, strip_name
from evaluate import Truth, build
from outcomes import ENDPOINT, qualified_outcomes, require_freeze
from test_choose import load_choices

TARGET = HERE / "TEST_RESULTS_REGISTERED.json"


def fraction_viability(role: str) -> dict:
    """{(core, line): mean pred_pv_high_conc as a fraction}, grouped exactly as outcomes.qualified_outcomes groups it."""
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    census = {r["core"]: r for r in json.loads((HERE / "CENSUS.json").read_text(encoding="utf-8"))["compounds"]}
    allowed = {int(census[c]["ctrp_master_cpd_id"]): c for c in split[role]}
    z = zipfile.ZipFile(CTRP_ZIP)
    curves = pd.read_csv(io.BytesIO(z.read("v20.data.curves_post_qc.txt")), sep="	", encoding="latin-1",
                         usecols=["experiment_id", "master_cpd_id", "pred_pv_high_conc"])
    curves = curves[curves["master_cpd_id"].isin(allowed)]
    exp = pd.read_csv(io.BytesIO(z.read("v20.meta.per_experiment.txt")), sep="	", encoding="latin-1")
    ccl = pd.read_csv(io.BytesIO(z.read("v20.meta.per_cell_line.txt")), sep="	", encoding="latin-1")
    info = pd.read_csv(CCLE / "sample_info.csv")
    strip_to_depmap: dict = {}
    for d, s in zip(info["DepMap_ID"], info["stripped_cell_line_name"]):
        strip_to_depmap.setdefault(strip_name(s), set()).add(d)
    ccl_line = {}
    for k, name in zip(ccl["master_ccl_id"], ccl["ccl_name"]):
        ids = strip_to_depmap.get(strip_name(name), set())
        ccl_line[int(k)] = next(iter(ids)) if len(ids) == 1 else f"CTRP:{int(k)}"
    exp_line = {int(e): ccl_line[int(c)] for e, c in zip(exp["experiment_id"], exp["master_ccl_id"])}
    curves = curves.assign(line=[exp_line[int(e)] for e in curves["experiment_id"]])
    pv = curves.groupby(["master_cpd_id", "line"])["pred_pv_high_conc"].mean()
    return {(allowed[int(k)], line): float(v) for (k, line), v in pv.items()}


def registered_outcomes(role: str = "test") -> tuple[dict, dict]:
    """Outcomes with exact fraction viabilities and the registered flags recomputed, plus a change summary."""
    out = qualified_outcomes(role)
    exact = fraction_viability(role)
    changed = {"compounds_rescaled": 0, "validated_before": 0, "validated_after": 0, "pan_active_before": 0,
               "pan_active_after": 0, "pairs_on_viability_threshold": 0}
    seen = 0
    for core, rec in out.items():
        scale = rec["viability_scale"]
        changed["pan_active_before"] += int(rec["pan_active"])
        changed["compounds_rescaled"] += int(scale != 1.0)
        pv = []
        for line, r in rec["lines"].items():
            v = exact[(core, line)]
            seen += 1
            if abs(v / scale - r["top_viability"]) > 1e-12 * max(1.0, abs(v)):
                raise SystemExit(f"READER_MISMATCH: {core} {line}")
            changed["validated_before"] += int(r["validated"])
            changed["pairs_on_viability_threshold"] += int(v == ENDPOINT["top_dose_viability_max"])
            r["top_viability"] = v
            r["validated"] = bool(r["auc_z"] <= ENDPOINT["auc_robust_z_max"] and v <= ENDPOINT["top_dose_viability_max"])
            changed["validated_after"] += int(r["validated"])
            pv.append(v)
        rec["pan_active"] = bool(np.median(pv) <= ENDPOINT["pan_active_median_viability_max"])
        rec["viability_scale"] = 1.0
        changed["pan_active_after"] += int(rec["pan_active"])
    kept = {k for k in exact if k[0] in out}
    if seen != len(kept):
        raise SystemExit("READER_MISMATCH: pair sets differ")
    return out, changed


def main() -> None:
    require_freeze()
    choices = load_choices()
    t = load_table()
    outcomes, changed = registered_outcomes("test")
    res = build(t, Truth(t, outcomes), choices)
    res = {**res, "label": "TEST results under the registered endpoint (post-opening unit correction, see DEVIATIONS.json)",
           "as_run_label": res["label"], "correction": changed}
    text = json.dumps(res, indent=1) + "\n"
    if TARGET.exists():
        if TARGET.read_text(encoding="utf-8").replace("\r\n", "\n") != text:
            raise SystemExit("RESULTS_MISMATCH: recomputed results differ from TEST_RESULTS_REGISTERED.json")
        print("REPRODUCED TEST_RESULTS_REGISTERED.json")
    else:
        TARGET.write_bytes(text.encode())
        print("WROTE TEST_RESULTS_REGISTERED.json")
    print(json.dumps(changed))


if __name__ == "__main__":
    main()
