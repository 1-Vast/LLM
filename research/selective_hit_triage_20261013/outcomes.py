"""The confirmation endpoint: a validated selective hit in CTRP v2, with a seal on test compounds.

File summary
- Path: research/selective_hit_triage_20261013/outcomes.py
- Purpose: turn CTRP v2 post-QC curves into qualified confirmation outcomes for one split.
- Core points:
  - Endpoint levels are kept apart; this module scores only the third.
    1. PRISM primary activity is the screen being triaged.
    2. PRISM secondary dose-response is a same-platform follow-up an arm may buy.
    3. CTRP v2 is an independent assay platform (CellTiter-Glo, 16 doses, 72 h, separate runs) and
       provides the confirmation.
  - A nominated (compound, line) is a VALIDATED selective hit when all three hold:
    - CTRP has a post-QC curve for the pair (AUC and viability at top dose are averaged over
      experiments);
    - the line's AUC robust z among all CTRP lines for that compound is at most -2;
    - the predicted viability at the highest tested concentration is at most 50%.
  - A pair without a post-QC curve is NOT_EVALUABLE and never counts as a hit.
  - A compound is PAN_ACTIVE when its median top-dose viability over CTRP lines is at most 50%.
    This is the generic-toxicity class, reported but not part of the hit rule.
  - Opening test outcomes requires FREEZE.json with matching digests (FREEZE_MISSING,
    FREEZE_MISMATCH). Development outcomes open at any time.
- Interfaces: `ENDPOINT`, `qualified_outcomes(role)`.
"""
from __future__ import annotations

import hashlib
import io
import json
import zipfile

import numpy as np
import pandas as pd

from census import CCLE, CTRP_SHA256, CTRP_ZIP, HERE, ROOT, sha256, strip_name

ENDPOINT = {"auc_robust_z_max": -2.0, "top_dose_viability_max": 0.5, "pan_active_median_viability_max": 0.5,
            "min_ctrp_lines": 100}


def require_freeze() -> dict:
    path = HERE / "FREEZE.json"
    if not path.exists():
        raise SystemExit("FREEZE_MISSING: freeze the protocol before opening test outcomes")
    freeze = json.loads(path.read_text(encoding="utf-8"))
    for relative, digest in freeze["sha256"].items():
        data = (ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
        if hashlib.sha256(data).hexdigest() != digest:
            raise SystemExit(f"FREEZE_MISMATCH: {relative}")
    return freeze


def qualified_outcomes(role: str) -> dict:
    """Outcomes for every compound of one split: {core: {"lines": {depmap_id: record}, "pan_active": bool}}."""
    if role not in ("development", "test"):
        raise ValueError("role must be development or test")
    if role == "test":
        require_freeze()
    if sha256(CTRP_ZIP) != CTRP_SHA256:
        raise SystemExit("CTRP_ARCHIVE_MISMATCH")
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    census = {r["core"]: r for r in json.loads((HERE / "CENSUS.json").read_text(encoding="utf-8"))["compounds"]}
    allowed = {int(census[c]["ctrp_master_cpd_id"]): c for c in split[role]}
    z = zipfile.ZipFile(CTRP_ZIP)
    curves = pd.read_csv(io.BytesIO(z.read("v20.data.curves_post_qc.txt")), sep="\t", encoding="latin-1",
                         usecols=["experiment_id", "master_cpd_id", "area_under_curve", "pred_pv_high_conc"])
    curves = curves[curves["master_cpd_id"].isin(allowed)]          # other split never materialised
    exp = pd.read_csv(io.BytesIO(z.read("v20.meta.per_experiment.txt")), sep="\t", encoding="latin-1")
    ccl = pd.read_csv(io.BytesIO(z.read("v20.meta.per_cell_line.txt")), sep="\t", encoding="latin-1")
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
    scale = 100.0 if curves["pred_pv_high_conc"].abs().max() > 2.0 else 1.0     # percent or fraction columns
    grouped = curves.groupby(["master_cpd_id", "line"]).agg(auc=("area_under_curve", "mean"),
                                                             pv=("pred_pv_high_conc", "mean"), n=("experiment_id", "size"))
    out = {}
    for k, sub in grouped.groupby(level=0):
        auc, pv = sub["auc"].to_numpy(float), sub["pv"].to_numpy(float) / scale
        if len(auc) < ENDPOINT["min_ctrp_lines"]:
            continue
        med = np.median(auc)
        mad = max(1.4826 * np.median(np.abs(auc - med)), 1e-6)
        zz = (auc - med) / mad
        lines = {}
        for (cpd, line), a, p, zv, n in zip(sub.index, auc, pv, zz, sub["n"]):
            lines[line] = {"auc": float(a), "top_viability": float(p), "auc_z": float(zv), "experiments": int(n),
                           "validated": bool(zv <= ENDPOINT["auc_robust_z_max"] and p <= ENDPOINT["top_dose_viability_max"])}
        out[allowed[int(k)]] = {"lines": lines, "pan_active": bool(np.median(pv) <= ENDPOINT["pan_active_median_viability_max"]),
                                "ctrp_lines": len(auc), "viability_scale": scale}
    return out
