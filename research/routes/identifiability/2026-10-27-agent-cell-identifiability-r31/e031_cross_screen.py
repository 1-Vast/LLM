"""E031: cross-screen replication of GDSC synergy, with the within-screen concentration
change as the attribution baseline.

Pre-registered in PROTOCOL_E031.md. Reads the local Jaaks 2022 GDSC files only.

Baseline: inside the original screen every (cell, combination) has two anchor concentrations,
so the agreement between those two values isolates the concentration effect.
Cross-screen: original mean vs validation mean on the 4,725 overlapping (cell, combination).
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
BASE = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare"
ORIG = BASE / "Original screen_All tissues_fitted data.csv"
VAL = BASE / "Validation screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r31"
METRIC = "SYNERGY_DELTA_AUC"
N_BOOT = 1000
SEED = 20261027
USE = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_CONC", "LIBRARY_CONC", METRIC, "Synergy"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def pearson(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    a, b = a[m], b[m]
    if len(a) < 50 or np.std(a) == 0 or np.std(b) == 0:
        return float("nan"), 0
    return float(np.corrcoef(a, b)[0, 1]), int(len(a))


def boot_ci(x, y, n=N_BOOT, seed_off=0):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    rng = np.random.default_rng(SEED + seed_off)
    vals = []
    for _ in range(n):
        idx = rng.integers(0, len(x), len(x))
        if np.std(x[idx]) > 0 and np.std(y[idx]) > 0:
            vals.append(float(np.corrcoef(x[idx], y[idx])[0, 1]))
    return [float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))] if vals else None


def prep(path):
    d = pd.read_csv(path, low_memory=False, usecols=USE)
    d[METRIC] = pd.to_numeric(d[METRIC], errors="coerce")
    d = d[np.isfinite(d[METRIC])].copy()
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["CELL_LINE_NAME"].astype(str) + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    return d


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    o = prep(ORIG)
    v = prep(VAL)

    # ---- baseline: within the original screen, the two anchor concentrations ----
    g = o.groupby("key")
    conc = g["ANCHOR_CONC"].nunique()
    two = conc[conc == 2].index
    d2 = o[o["key"].isin(two)]
    grp = (d2.groupby(["key", "ANCHOR_CONC"], as_index=False)
             .agg(**{"v": (METRIC, "mean"), "b": ("syn", "mean")})
             .sort_values(["key", "ANCHOR_CONC"]))
    lo = grp.groupby("key").first()
    hi = grp.groupby("key").last()
    base_r, base_n = pearson(lo["v"].to_numpy(), hi["v"].to_numpy())
    base_ci = boot_ci(lo["v"].to_numpy(), hi["v"].to_numpy(), seed_off=1)
    base_agree = float(np.mean((lo["b"] > 0.5) == (hi["b"] > 0.5)))
    per = lo  # kept only for the audit count

    # ---- cross-screen: means on the overlapping keys ----
    om = o.groupby("key")[METRIC].mean()
    vm = v.groupby("key")[METRIC].mean()
    both = om.index.intersection(vm.index)
    cross_r, cross_n = pearson(om.loc[both].to_numpy(), vm.loc[both].to_numpy())
    cross_ci = boot_ci(om.loc[both].to_numpy(), vm.loc[both].to_numpy(), seed_off=2)
    ob = o.groupby("key")["syn"].mean().reindex(both)
    vb = v.groupby("key")["syn"].mean().reindex(both)
    cross_agree = float(np.mean((ob > 0.5) == (vb > 0.5)))

    res = {"kind": "cross_screen_replication_with_concentration_baseline",
           "input_sha256": {ORIG.name: sha256(ORIG), VAL.name: sha256(VAL)},
           "settings": {"metric": METRIC, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"original_keys": int(o["key"].nunique()), "validation_keys": int(v["key"].nunique()),
                     "overlap_keys": int(len(both)),
                     "baseline_keys_with_two_concentrations": int(len(per))},
           "baseline_within_screen_concentration": {"pearson": base_r, "n": base_n, "ci95": base_ci,
                                                    "synergy_bool_agreement": base_agree},
           "cross_screen": {"pearson": cross_r, "n": cross_n, "ci95": cross_ci,
                            "synergy_bool_agreement": cross_agree},
           "files": {}}

    ratio = cross_r / base_r if (base_r and np.isfinite(base_r) and base_r != 0) else None
    aratio = cross_agree / base_agree if base_agree else None
    res["attribution"] = {"corr_ratio_cross_over_baseline": ratio,
                          "agreement_ratio": aratio}
    h076 = bool(np.isfinite(cross_r) and cross_r > 0.30)
    h077 = bool(ratio is not None and ratio >= 0.70)
    h078 = bool(cross_agree > 0.70 and (aratio is None or aratio >= 0.70))
    res["decisions"] = {"H076_cross_screen_replicates": h076, "H077_no_extra_screen_decay": h077,
                        "H078_binary_replicates": h078}
    res["decisions"]["verdict"] = ("cross_screen_replication_without_extra_decay" if h076 and h077 else
                                   "replication_present_but_screen_adds_decay" if h076 else
                                   "no_cross_screen_replication")
    res["limits"] = [
        "The two screens use DIFFERENT concentrations, so the cross-screen comparison bundles a concentration change and a screen change.",
        "The validation screen covers only 4,725 keys and may be a selected subset, not a random one.",
        "SYNERGY_DELTA_AUC is a model-fitted quantity.",
        "No mechanistic, clinical or drug-choice claim.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r31/PROTOCOL_E031.md",
                "research/2026-10-27-agent-cell-identifiability-r31/e031_cross_screen.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E031_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    print("original keys=%d validation keys=%d overlap=%d | baseline keys=%d" % (
        res["audit"]["original_keys"], res["audit"]["validation_keys"],
        res["audit"]["overlap_keys"], res["audit"]["baseline_keys_with_two_concentrations"]))
    print("baseline (same screen, two concentrations): r=%.4f CI=[%.4f,%.4f] n=%d bool-agree=%.3f" % (
        base_r, base_ci[0], base_ci[1], base_n, base_agree))
    print("cross-screen:                                r=%.4f CI=[%.4f,%.4f] n=%d bool-agree=%.3f" % (
        cross_r, cross_ci[0], cross_ci[1], cross_n, cross_agree))
    print("ratio=%.3f | agreement ratio=%.3f" % (ratio, aratio))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
