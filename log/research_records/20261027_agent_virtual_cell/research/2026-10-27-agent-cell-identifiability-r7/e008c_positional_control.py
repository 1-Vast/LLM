"""E008c: is the drug-pair reversal propensity a positional artefact?

The plate layout is identical across cell lines, so any well-position effect that varies
by plate/day would make a specific unit pair flip more often in every cell - which would
look exactly like transferable "drug-pair fragility" without being pharmacology.

Checks:
  1. Do reversal-prone unit pairs cluster positionally (same row, same column, distance)?
  2. Restricted to pairs that are NOT in the same row and NOT in the same column, does the
     drug-pair propensitstill transfer (AUC) and still beat spacing?
  3. Same-row-only and same-column-only pairs, reported separately.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
CSV = ROOT / "research" / "eight_directions_20261026" / "evidence_audit" / "raw" / "PAIR_SCREEN.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r7"
ANCHORS = {"high control", "low control"}
FLOOR = 0.10
PAIRS_PER_LAYOUT = 300
ALPHA_SHRINK = 5.0
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def auc(y, s) -> float:
    y = np.asarray(y, bool)
    if y.all() or (~y).all():
        return float("nan")
    r = pd.Series(s).rank().to_numpy()
    n1, n0 = int(y.sum()), int((~y).sum())
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def rc(well: str):
    m = re.match(r"^([A-P])(\d+)$", str(well).strip().upper())
    return (ord(m.group(1)) - ord("A"), int(m.group(2)) - 1) if m else (None, None)


def build():
    df = pd.read_csv(CSV, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: "row_id"})
    for c in ("Drug 1", "Drug 2", "Cell line", "file", "Well"):
        df[c] = df[c].astype(str).str.strip()
    df["iteration"] = pd.to_numeric(df["Iteration"], errors="coerce")
    df["failed_qc"] = df["Failed QC"].astype(str).str.strip().str.lower().isin(["true", "1"])
    df["y"] = pd.to_numeric(df["Viability"], errors="coerce")
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    df["dmso"] = (df["Drug 1"].str.lower() == "dmso") | (df["Drug 2"].str.lower() == "dmso")
    meta = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], pd.to_numeric(g["Conc 1 (uM)"]).round(9),
                                  g["Drug 2"], pd.to_numeric(g["Conc 2 (uM)"]).round(9))))
        meta[fname] = {"cell": g["Cell line"].iloc[0],
                       "iteration": int(g["iteration"].iloc[0]) if pd.notna(g["iteration"].iloc[0]) else -1,
                       "h": hashlib.sha1(repr(layout).encode()).hexdigest(),
                       "combo": {w: (str(d1).lower() != "dmso" and str(d2).lower() != "dmso")
                                 for w, (d1, c1, d2, c2) in
                                 {w: (d1, c1, d2, c2) for w, d1, c1, d2, c2 in layout}.items()},
                       "qc": float(g["failed_qc"].mean())}

    def vec(fname, units):
        sub = df[(df["file"] == fname) & (~df["failed_qc"]) & df["y"].notna() & (~df["anchor"])]
        return sub.drop_duplicates("Well").set_index("Well")["y"].reindex(units).to_numpy(dtype=float)

    groups = {}
    for f, s in meta.items():
        groups.setdefault((s["iteration"], s["h"]), {}).setdefault(s["cell"], []).append(f)
    rng = np.random.default_rng(SEED)
    layouts = []
    for (it, h), cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        if len(cells) < 3:
            continue
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 3:
            continue
        first = cells[good[0]][0]
        units = [u for u in sorted(meta[first]["combo"]) if meta[first]["combo"][u]]
        V = {c: [vec(f, units) for f in cells[c]] for c in good}
        nu = len(units)
        iu, ju = np.triu_indices(nu, 1)
        sel = rng.choice(iu.size, min(PAIRS_PER_LAYOUT, iu.size), replace=False)
        Y = np.vstack([np.nanmean(np.vstack(V[c]), axis=0) for c in good])
        layouts.append({"iteration": it, "hash": h[:12], "cells": good, "units": units,
                        "iu": iu[sel], "ju": ju[sel], "Y": Y})
    return df, layouts


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    _, layouts = build()
    rate_rows, subset_rows = [], []
    pooled = {}
    for L in layouts:
        cells, Y, iu, ju = L["cells"], L["Y"], L["iu"], L["ju"]
        nc = len(cells)
        S = np.sign(Y[:, iu] - Y[:, ju])
        gap = np.abs(Y[:, iu] - Y[:, ju])
        ok = (gap >= FLOOR) & np.isfinite(gap)
        # per-unit-pair reversal rate across all cell pairs (for positional correlation)
        rev_counts = np.zeros(iu.size)
        tot_counts = np.zeros(iu.size)
        for a in range(nc):
            for b in range(a + 1, nc):
                m = ok[a] & ok[b]
                rev_counts[m] += (S[a, m] != S[b, m])
                tot_counts[m] += 1
        for p in range(iu.size):
            if tot_counts[p] >= 3:
                r0, c0 = rc(L["units"][iu[p]])
                r1, c1 = rc(L["units"][ju[p]])
                rate_rows.append({"layout": f"{L['iteration']}/{L['hash']}", "rate": rev_counts[p] / tot_counts[p],
                                  "same_row": int(r0 == r1), "same_col": int(c0 == c1),
                                  "dcol": abs(c0 - c1), "drow": abs(r0 - r1), "n": tot_counts[p]})
        # AUC within restricted subsets, same leave-two-cells-out protocol
        for subset in ("all", "neither_same_row_nor_col", "same_row", "same_col"):
            preds, ys = [], []
            for a in range(nc):
                for b in range(a + 1, nc):
                    tr = [i for i in range(nc) if i not in (a, b)]
                    if len(tr) < 3:
                        continue
                    R, P = [], []
                    for ii in range(len(tr)):
                        for jj in range(ii + 1, len(tr)):
                            x, y_ = tr[ii], tr[jj]
                            m = ok[x] & ok[y_]
                            if m.sum() == 0:
                                continue
                            R.append((S[x, m] != S[y_, m]).astype(float))
                            P.append(np.where(m)[0])
                    if not R:
                        continue
                    R = np.concatenate(R)
                    P = np.concatenate(P)
                    m_te = ok[a] & ok[b]
                    if m_te.sum() < 20 or R.sum() == 0:
                        continue
                    p0 = float(R.mean())
                    cnt = np.bincount(P, minlength=iu.size).astype(float)
                    rev = np.bincount(P, weights=R, minlength=iu.size)
                    rate = (rev + ALPHA_SHRINK * p0) / (cnt + ALPHA_SHRINK)
                    te = np.where(m_te)[0]
                    y_te = (S[a, te] != S[b, te]).astype(float)
                    s_te = rate[te]
                    if subset == "all":
                        sel = np.ones(te.size, bool)
                    else:
                        sr = np.array([rc(L["units"][iu[q]])[0] == rc(L["units"][ju[q]])[0] for q in te])
                        sc_ = np.array([rc(L["units"][iu[q]])[1] == rc(L["units"][ju[q]])[1] for q in te])
                        sel = {"neither_same_row_nor_col": (~sr) & (~sc_),
                               "same_row": sr & (~sc_), "same_col": sc_ & (~sr)}[subset]
                    if sel.sum() >= 10 and 0 < y_te[sel].sum() < sel.sum():
                        preds.append(s_te[sel])
                        ys.append(y_te[sel])
            if preds:
                acc = pooled.setdefault(subset, {"p": [], "y": [], "per_layout": []})
                pp, yy2 = np.concatenate(preds), np.concatenate(ys)
                acc["p"].append(pp)
                acc["y"].append(yy2)
                layid = "%s/%s" % (L["iteration"], L["hash"]); acc["per_layout"].append({"layout": layid, "n": int(yy2.size), "auc": auc(yy2, pp)})
    for subset, acc in pooled.items():
        P = np.concatenate(acc["p"])
        Yv = np.concatenate(acc["y"])
        subset_rows.append({"subset": subset, "n": int(Yv.size), "baseline": float(Yv.mean()),
                            "auc_pooled": auc(Yv, P),
                            "per_layout_auc": acc["per_layout"]})

    rr = pd.DataFrame(rate_rows)
    corr = {
        "spearman_rate_vs_dcol": float(rr[["rate", "dcol"]].corr(method="spearman").iloc[0, 1]),
        "spearman_rate_vs_drow": float(rr[["rate", "drow"]].corr(method="spearman").iloc[0, 1]),
        "mean_rate_same_row": float(rr[rr["same_row"] == 1]["rate"].mean()),
        "mean_rate_diff_row": float(rr[rr["same_row"] == 0]["rate"].mean()),
        "mean_rate_same_col": float(rr[rr["same_col"] == 1]["rate"].mean()),
        "mean_rate_diff_col": float(rr[rr["same_col"] == 0]["rate"].mean()),
        "n_pairs": int(len(rr)),
    }
    res = {"kind": "positional_confound_checks",
           "input_sha256": sha256(CSV), "floor": FLOOR,
           "positional_correlations": corr,
           "auc_by_subset": subset_rows,
           "limits": [
               "Rate per unit pair is computed across all cell pairs, so the correlation with position is descriptive, not a test.",
               "The 'neither same row nor column' subset is the one that removes the most obvious positional artefacts; it still shares plate and day.",
           ],
           "files": {}}
    for rel in ("research/2026-10-27-agent-cell-identifiability-r7/e008c_positional_control.py",
                str(CSV.relative_to(ROOT))):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E008C_POSITIONAL.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    print("positional correlations (n=%d pairs):" % corr["n_pairs"])
    for k in ("spearman_rate_vs_dcol", "spearman_rate_vs_drow", "mean_rate_same_row", "mean_rate_diff_row",
              "mean_rate_same_col", "mean_rate_diff_col"):
        print("  %-24s %.4f" % (k, corr[k]))
    print("AUC by positional subset:")
    for s in subset_rows:
        pl = s.get("per_layout_auc") or []
        print("  %-26s n=%6d baseline=%.4f AUC=%.4f | per-layout %s" % (
            s["subset"], s["n"], s["baseline"], s["auc_pooled"],
            ",".join("%.2f" % x["auc"] for x in pl)))


if __name__ == "__main__":
    main()
