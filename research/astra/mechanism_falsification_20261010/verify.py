"""Independent verification of block M's sealed run (writes VERIFIED.json).

1. freeze precedence: RESULTS.json is later than FREEZE.json and every frozen file keeps its hash;
2. arithmetic: coverage and mean set size of every arm x policy x budget recomputed with pandas from
   ROWS.json, and the registered contrasts recomputed from the rows with an independent bootstrap
   implementation (same seed, so the intervals must agree to rounding);
3. poisoning: the per-option-set arm's fixed design rerun on noise with the confirmation drugs'
   missingness pattern: the observed option sequences must be identical (the fixed design reads no
   values), while coverage and set sizes must change;
4. exact rerun: a second run of the arms set, naive and perm_classes reproduces their summaries
   exactly (the episode-calibrated arm is deterministic by the same seeds but too slow to repeat).
Runs go to data/external/lincs_l1000_gse92742/derived/block_m_verify_runs (git-ignored).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
RUNS = HERE.parents[2] / "data/external/lincs_l1000_gse92742/derived/block_m_verify_runs"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_freeze() -> dict:
    fr = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    mism = [f for f, h in fr["files"].items() if not (HERE / f).exists() or sha(HERE / f) != h]
    res_m = (HERE / "RESULTS.json").stat().st_mtime
    fr_m = (HERE / "FREEZE.json").stat().st_mtime
    return {"frozen_utc": fr["frozen_utc"], "hash_mismatches": mism, "results_after_freeze": bool(res_m > fr_m),
            "pass": not mism and res_m > fr_m}


def rows_frame(rows: dict, B: int) -> pd.DataFrame:
    recs = []
    for arm, rs in rows.items():
        for r in rs:
            if not r["steps"]:
                continue
            for k in range(1, B + 1):
                st = r["steps"][min(k, len(r["steps"])) - 1]
                recs.append({"arm": arm, "policy": r["policy"], "B": k, "drug": r["drug"], "moa": r["moa"],
                             "covered": st["covered"], "set_size": st["set_size"]})
    return pd.DataFrame(recs)


def check_arithmetic(R: dict, rows: dict) -> dict:
    B = R["budget"]
    df = rows_frame(rows, B)
    bad = []
    g = df.groupby(["arm", "policy", "B"]).agg(cov=("covered", "mean"), size=("set_size", "mean"), n=("drug", "size"))
    for (arm, pol, k), v in g.iterrows():
        rep = R["arms"][arm]["by_policy"][pol][f"B{k}"]["all"]
        if abs(rep["coverage"] - v["cov"]) > 1e-12 or abs(rep["mean_set"] - v["size"]) > 1e-9 or rep["n"] != v["n"]:
            bad.append([arm, pol, int(k)])
    # contrasts: independent cluster bootstrap (classes as clusters) of the mean paired difference
    P = json.loads((HERE / "PROTOCOL_CONFIG.json").read_text(encoding="utf-8"))
    sealed_ref = None
    cbad = []
    for c in P["contrasts"]:
        a = df[(df.arm == c["a"][0]) & (df.policy == c["a"][1]) & (df.B == B)].set_index("drug")
        b = df[(df.arm == c["b"][0]) & (df.policy == c["b"][1]) & (df.B == B)].set_index("drug")
        if c.get("stratum") in ("knowledge_only", "referenced"):
            if sealed_ref is None:
                split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
                sealed_ref = {v["moa"] for v in split["drugs"].values() if v["role"] == "reference"}
            keep = a.moa.isin(sealed_ref) if c["stratum"] == "referenced" else ~a.moa.isin(sealed_ref)
            a = a[keep]
        j = a.join(b[["set_size"]], rsuffix="_b", how="inner")
        d = (j.set_size - j.set_size_b).to_numpy(float)
        cl = j.moa.to_numpy()
        est = float(d.mean())
        rep = R["contrasts"][c["name"]]
        uniq = np.unique(cl)
        groups = {u: np.where(cl == u)[0] for u in uniq}
        rng = np.random.default_rng(20261010)
        draws = []
        for _ in range(2000):
            pick = rng.integers(0, len(uniq), size=len(uniq))
            idx = np.concatenate([groups[uniq[i]] for i in pick])
            draws.append(d[idx].mean())
        lo, hi = np.percentile(draws, [2.5, 97.5])
        if abs(est - rep["mean_difference"]) > 1e-9 or abs(lo - rep["ci95"][0]) > 1e-6 or abs(hi - rep["ci95"][1]) > 1e-6:
            cbad.append(c["name"])
    return {"summary_mismatches": bad, "contrast_mismatches": cbad, "pass": not bad and not cbad}


def check_poison_and_rerun(R: dict) -> dict:
    import evaluate as EV
    rerun_dir = RUNS / "rerun"
    poison_dir = RUNS / "poison"
    rerun_arms = ["set", "naive", "perm_classes"]
    rr = EV.main(out_dir=rerun_dir, with_llm=False, arms_filter=rerun_arms, sections=())
    same = {a: rr["arms"][a]["by_policy"] == R["arms"][a]["by_policy"] for a in rerun_arms}
    main_name = "set"  # the fixed design of the per-option-set arm reads no values when choosing options
    pr = EV.main(out_dir=poison_dir, poison_seed=7, with_llm=False, arms_filter=[main_name], sections=())
    rows_main = json.loads((HERE / "ROWS.json").read_text(encoding="utf-8"))[main_name]
    rows_poison = json.loads((poison_dir / "ROWS.json").read_text(encoding="utf-8"))[main_name]
    seq = lambda rows: {r["drug"]: [s["option"] for s in r["steps"]] for r in rows if r["policy"] == "fixed"}
    a, b = seq(rows_main), seq(rows_poison)
    # the fixed design stops early on a single survivor, so compare the common prefix
    design_same = all(a[d][:min(len(a[d]), len(b[d]))] == b[d][:min(len(a[d]), len(b[d]))] for d in a)
    B = f"B{R['budget']}"
    out_changed = pr["arms"][main_name]["by_policy"]["fixed"][B]["all"] != R["arms"][main_name]["by_policy"]["fixed"][B]["all"]
    return {"rerun_identical": same, "poison_fixed_design_identical": bool(design_same), "poison_outcomes_changed": bool(out_changed),
            "pass": all(same.values()) and design_same and out_changed}


def main() -> dict:
    R = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
    rows = json.loads((HERE / "ROWS.json").read_text(encoding="utf-8"))
    out = {"freeze": check_freeze(), "arithmetic": check_arithmetic(R, rows)}
    out["poison_and_rerun"] = check_poison_and_rerun(R)
    out["pass"] = all(v["pass"] for v in out.values() if isinstance(v, dict))
    (HERE / "VERIFIED.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
