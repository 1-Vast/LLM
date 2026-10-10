"""Independent verification of block K (writes VERIFIED.json).

1. freeze precedence: every sealed extraction receipt is later than FREEZE.json, and every frozen
   file still has its frozen hash;
2. gate arithmetic: ceiling, forecast increment and decision recomputed from GATE.json per-drug values;
3. poisoning: sealed 5-day outcomes replaced by noise -> predictions and selections bit-identical,
   while outcome-dependent metrics change;
4. exact rerun: a second evaluation reproduces RESULTS.json and PREDICTIONS.npz exactly;
5. arithmetic: M1 per-drug correlations and M3 utilities recomputed with scipy/pandas from the saved
   predictions and an independently loaded outcome table.
Runs use directories under data/external/kinetic_horizon_20261010/verify_runs (no temp-dir cleanup).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
RUNS = HERE.parents[2] / "data/external/kinetic_horizon_20261010/verify_runs"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_freeze() -> dict:
    fr = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    t0 = fr["frozen_utc"]
    mism = [f for f, h in fr["files"].items() if sha(HERE / f) != h]
    receipts = {}
    for p in ["PRISM_CONFIRMATION_RECEIPT.json", "PRISM_MIX_SEALED_RECEIPT.json", "mixseq/A_treated_sealed.json", "mixseq/C_treated.json", "mixseq/D_treated.json"]:
        q = HERE / p
        receipts[p] = json.loads(q.read_text())["utc"] if q.exists() else None
    late = {p: (u is not None and u > t0) for p, u in receipts.items()}
    heldout_sealed = not (HERE / "PRISM_HELDOUT_RECEIPT.json").exists()
    return {"frozen_utc": t0, "hash_mismatches": mism, "sealed_receipts_utc": receipts, "all_after_freeze": all(late.values()),
            "tahoe_zeroshot_prism_still_sealed": heldout_sealed, "pass": not mism and all(late.values()) and heldout_sealed}


def check_gate() -> dict:
    import gate as G
    g = json.loads((HERE / "GATE.json").read_text(encoding="utf-8"))
    m = g["mix_24h_to_5d"]
    per = m["per_drug"]
    b = np.mean([v["B"] for v in per.values()])
    o = np.mean([v["oracle_B_plus_Rmag"] for v in per.values()])
    f = np.mean([per[d]["wm_B_plus_Smag"] - per[d]["B"] for d in G.STATE_DRUGS])
    dec = G.decide(o - b, f)[0]
    t = g["tahoe_24h_to_5d"]
    ok = abs(o - b - m["ceiling"]) < 1e-12 and abs(f - m["forecast_increment"]) < 1e-12 and dec == m["decision"] \
        and G.decide(t["ceiling"], float("nan"))[0] == t["decision"]
    return {"mix_ceiling": o - b, "mix_forecast": f, "mix_decision": dec, "tahoe_decision": t["decision"], "pass": bool(ok)}


def run(tag: str, seed=None):
    import evaluate as EV
    out = RUNS / tag
    EV.main(out_dir=out, poison_seed=seed)
    return out


def load_pred(d: Path) -> dict:
    with np.load(d / "PREDICTIONS.npz", allow_pickle=False) as z:
        return {k: z[k].copy() for k in z.files}


def same(a: dict, b: dict) -> dict:
    return {k: bool(np.array_equal(a[k], b[k], equal_nan=a[k].dtype.kind == "f")) for k in a}


def check_arithmetic(main_dir: Path) -> dict:
    import gate as G
    res = json.loads((main_dir / "RESULTS.json").read_text())["M"]
    pr = load_pred(main_dir)
    sp = json.loads((HERE / "MIXSEQ_SPLIT.json").read_text())
    with np.load(HERE.parents[2] / "data/external/kinetic_horizon_20261010/prism_mix_sealed.npz", allow_pickle=False) as z:
        tab = pd.DataFrame(z["secondary_mean"], index=z["files"], columns=z["drugs"])
    lines = list(pr["M_lines"])
    assert lines == sp["pool_A_confirmation"]
    errs = []
    for j, d in enumerate(G.MIX_DRUGS_LATE):
        y = tab.loc[lines, d].to_numpy()
        B, R = pr["M_B"][:, j], pr["M_Rmag"][:, j]
        ok = np.isfinite(y) & np.isfinite(B) & np.isfinite(R)
        zb = (B - np.nanmean(B)) / np.nanstd(B); zr = (R - np.nanmean(R)) / np.nanstd(R)
        rb = pearsonr(B[ok], y[ok])[0]; rc = pearsonr((zb + zr)[ok], y[ok])[0]
        errs.append(abs(rb - res["M1_measurement_complements_prior"]["per_drug"][d]["B"]))
        errs.append(abs(rc - res["M1_measurement_complements_prior"]["per_drug"][d]["B_plus_Rmag"]))
        for pol, score in (("P0_prior", B), ("P2_prior_plus_24h_measurement", zb + zr)):
            s = pd.Series(score, index=lines)[ok]
            chosen = s.sort_values(kind="stable").index[:10]
            u = -tab.loc[list(chosen), d].mean()
            errs.append(abs(u - res["M3_decisions"]["per_drug"][d][pol]))
    return {"max_abs_error": float(np.max(errs)), "n_checks": len(errs), "pass": bool(np.max(errs) < 1e-9)}


def main() -> dict:
    out = {"freeze": check_freeze(), "gate": check_gate()}
    main_dir = HERE
    a = run("rerun")
    out["exact_rerun"] = {"results_identical": json.loads((a / "RESULTS.json").read_text()) == json.loads((main_dir / "RESULTS.json").read_text()),
                          "predictions_identical": all(same(load_pred(main_dir), load_pred(a)).values())}
    out["exact_rerun"]["pass"] = out["exact_rerun"]["results_identical"] and out["exact_rerun"]["predictions_identical"]
    p = run("poison", seed=987654321)
    sm = same(load_pred(main_dir), load_pred(p))
    m_main = json.loads((main_dir / "RESULTS.json").read_text())["M"]["M1_measurement_complements_prior"]["mean_increment"]
    m_pois = json.loads((p / "RESULTS.json").read_text())["M"]["M1_measurement_complements_prior"]["mean_increment"]
    out["poisoning"] = {"predictions_identical": sm, "metric_changed": bool(m_main != m_pois), "pass": all(sm.values()) and m_main != m_pois}
    out["arithmetic"] = check_arithmetic(main_dir)
    out["all_pass"] = all(v.get("pass", False) for v in out.values() if isinstance(v, dict))
    (HERE / "VERIFIED.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    return out


if __name__ == "__main__":
    r = main()
    print(json.dumps({k: (v["pass"] if isinstance(v, dict) else v) for k, v in r.items()}, indent=1))
