"""E032: same-keys comparison of within-screen vs cross-screen agreement.

Pre-registered in PROTOCOL_E032.md. Restricts both arms to the 4,725 overlapping keys so
subset composition cannot confound the comparison.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
BASE = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare"
ORIG = BASE / "Original screen_All tissues_fitted data.csv"
VAL = BASE / "Validation screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r32"
METRIC = "SYNERGY_DELTA_AUC"
N_BOOT = 1000
SEED = 20261027
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_CONC", METRIC, "Synergy"]


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
    if len(a) < 30 or np.std(a) == 0 or np.std(b) == 0:
        return float("nan"), int(len(a))
    return float(np.corrcoef(a, b)[0, 1]), int(len(a))


def boot(x, y, off):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    rng = np.random.default_rng(SEED + off)
    vals = []
    for _ in range(N_BOOT):
        i = rng.integers(0, len(x), len(x))
        if np.std(x[i]) > 0 and np.std(y[i]) > 0:
            vals.append(float(np.corrcoef(x[i], y[i])[0, 1]))
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
    om = o.groupby("key")[METRIC].mean()
    vm = v.groupby("key")[METRIC].mean()
    keys = om.index.intersection(vm.index)

    # same-keys within-screen arm: the two anchor concentrations, restricted to these keys
    ok = o[o["key"].isin(keys)]
    g = (ok.groupby(["key", "ANCHOR_CONC"], as_index=False)
           .agg(v=(METRIC, "mean"), b=("syn", "mean"))
           .sort_values(["key", "ANCHOR_CONC"]))
    nconc = g.groupby("key").size()
    two = nconc[nconc == 2].index
    gg = g[g["key"].isin(two)]
    lo = gg.groupby("key").first()
    hi = gg.groupby("key").last()
    within_r, within_n = pearson(lo["v"].to_numpy(), hi["v"].to_numpy())
    within_ci = boot(lo["v"].to_numpy(), hi["v"].to_numpy(), 1)
    within_agree = float(np.mean((lo["b"] > 0.5) == (hi["b"] > 0.5)))

    # same-keys cross-screen arm
    cross_r, cross_n = pearson(om.loc[keys].to_numpy(), vm.loc[keys].to_numpy())
    cross_ci = boot(om.loc[keys].to_numpy(), vm.loc[keys].to_numpy(), 2)
    ob = o.groupby("key")["syn"].mean().reindex(keys)
    vb = v.groupby("key")["syn"].mean().reindex(keys)
    cross_agree = float(np.mean((ob > 0.5) == (vb > 0.5)))

    # composition of the subset vs everything
    full_tissue = o.drop_duplicates("CELL_LINE_NAME").set_index("CELL_LINE_NAME")["Tissue"]
    sub_cells = pd.Index([k.split("|")[0] for k in keys]).unique()
    comp_tissue = full_tissue.reindex(sub_cells).value_counts(normalize=True).round(3).to_dict()
    full_comp = full_tissue.value_counts(normalize=True).round(3).to_dict()

    res = {"kind": "same_keys_within_vs_cross_screen",
           "input_sha256": {ORIG.name: sha256(ORIG), VAL.name: sha256(VAL)},
           "settings": {"n_boot": N_BOOT, "seed": SEED},
           "audit": {"overlap_keys": int(len(keys)),
                     "same_keys_with_two_concentrations": int(within_n),
                     "cells_in_subset": int(len(sub_cells)),
                     "cells_total": int(full_tissue.shape[0])},
           "same_keys": {
               "within_screen": {"pearson": within_r, "n": within_n, "ci95": within_ci,
                                 "bool_agreement": within_agree},
               "cross_screen": {"pearson": cross_r, "n": cross_n, "ci95": cross_ci,
                                "bool_agreement": cross_agree},
               "ratio": (cross_r / within_r) if within_r and np.isfinite(within_r) else None},
           "composition": {"subset_tissue_share": comp_tissue, "full_tissue_share": full_comp},
           "files": {}}

    ratio = res["same_keys"]["ratio"]
    h079 = bool(ratio is not None and ratio >= 0.70)
    diff_full = within_r - 0.6096
    h080 = bool(abs(diff_full) <= 0.05)
    h081 = bool(comp_tissue != full_comp)
    res["decisions"] = {"H079_no_extra_decay_same_keys": h079,
                        "H080_subset_not_easier": h080,
                        "H081_composition_differs": h081}
    res["decisions"]["within_minus_full_baseline"] = float(diff_full)
    res["decisions"]["verdict"] = ("cross_screen_decay_holds_on_same_keys" if h079
                                   else "screen_level_decay_confirmed_on_same_keys")
    res["limits"] = [
        "Even at identical keys the two screens use different concentrations, so this removes the subset confound, not the concentration confound.",
        "SYNERGY_DELTA_AUC is a model-fitted quantity.",
        "No mechanistic, clinical or drug-choice claim.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r32/PROTOCOL_E032.md",
                "research/2026-10-27-agent-cell-identifiability-r32/e032_same_keys.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E032_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    print("overlap keys=%d | same keys with 2 concs=%d | cells in subset=%d/%d" % (
        res["audit"]["overlap_keys"], res["audit"]["same_keys_with_two_concentrations"],
        res["audit"]["cells_in_subset"], res["audit"]["cells_total"]))
    print("SAME KEYS  within-screen: r=%.4f CI=[%.4f,%.4f] n=%d agree=%.3f" % (
        within_r, within_ci[0], within_ci[1], within_n, within_agree))
    print("SAME KEYS  cross-screen:  r=%.4f CI=[%.4f,%.4f] n=%d agree=%.3f" % (
        cross_r, cross_ci[0], cross_ci[1], cross_n, cross_agree))
    print("ratio=%.3f | within minus full baseline=%+.4f" % (ratio, diff_full))
    print("composition subset:", json.dumps(comp_tissue, ensure_ascii=False))
    print("composition full:  ", json.dumps(full_comp, ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
