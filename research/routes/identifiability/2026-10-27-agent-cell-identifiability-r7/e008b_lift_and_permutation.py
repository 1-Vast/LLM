"""E008b: does the drug-pair signal survive a base-rate-aware look and a label-permutation control?

With a 2% event rate an AUC of 0.92 can still be useless in practice. Three additions:
  1. lift / precision at the top-k% of scores (practically meaningful for experiment choice);
  2. calibration (predicted vs observed reversal rate in score bins);
  3. permutation control: the drug-pair rate vector is shuffled within the layout, so the
     pairwise structure is destroyed but everything else (support, shrinkage, spacing) is
     identical. If AUC(M2) stays high under that shuffle, the pipeline leaks.
"""

from __future__ import annotations

import hashlib
import json
import math
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
N_PERM = 20
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def auc(y: np.ndarray, s: np.ndarray) -> float:
    y = np.asarray(y, bool)
    if y.all() or (~y).all():
        return float("nan")
    r = pd.Series(s).rank().to_numpy()
    n1 = int(y.sum())
    n0 = int((~y).sum())
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def logit_fit(X, y, l2=1.0, iters=200):
    n, d = X.shape
    Xb = np.hstack([np.ones((n, 1)), X])
    w = np.zeros(d + 1)
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-np.clip(Xb @ w, -30, 30)))
        W = np.clip(p * (1 - p), 1e-6, None)
        H = Xb.T @ (Xb * W[:, None])
        reg = np.zeros_like(H)
        reg[1:, 1:] = l2 * np.eye(d)
        try:
            step = np.linalg.solve(H + reg + 1e-8 * np.eye(d + 1), Xb.T @ (y - p))
        except np.linalg.LinAlgError:
            break
        w += step
        if np.max(np.abs(step)) < 1e-8:
            break
    return w


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
    rng = np.random.default_rng(SEED + 7)

    rows_obs, rows_perm = [], []
    perm_aucs = []
    for L in layouts:
        cells, Y, iu, ju = L["cells"], L["Y"], L["iu"], L["ju"]
        nc = len(cells)
        S = np.sign(Y[:, iu] - Y[:, ju])
        gap = np.abs(Y[:, iu] - Y[:, ju])
        ok = (gap >= FLOOR) & np.isfinite(gap)
        for a in range(nc):
            for b in range(a + 1, nc):
                tr = [i for i in range(nc) if i not in (a, b)]
                r_tr, p_tr = [], []
                for ii in range(len(tr)):
                    for jj in range(ii + 1, len(tr)):
                        x, y_ = tr[ii], tr[jj]
                        m = ok[x] & ok[y_]
                        if m.sum() == 0:
                            continue
                        r_tr.append((S[x, m] != S[y_, m]).astype(float))
                        p_tr.append(np.where(m)[0])
                if not r_tr:
                    continue
                R = np.concatenate(r_tr)
                P = np.concatenate(p_tr)
                m_te = ok[a] & ok[b]
                if m_te.sum() < 20 or R.sum() == 0:
                    continue
                r_te = (S[a, m_te] != S[b, m_te]).astype(float)
                p_te = np.where(m_te)[0]
                p0 = float(R.mean())
                cnt = np.bincount(P, minlength=S.shape[1]).astype(float)
                rev = np.bincount(P, weights=R, minlength=S.shape[1])
                rate = (rev + ALPHA_SHRINK * p0) / (cnt + ALPHA_SHRINK)
                rows_obs.append({"layout": f"{L['iteration']}/{L['hash']}", "cells": f"{cells[a]}|{cells[b]}",
                                 "score": rate[p_te], "y": r_te, "n": int(m_te.sum())})
                # permutation control: shuffle the per-unit-pair counts within this layout
                perm_idx = rng.permutation(S.shape[1])
                cnt_p = cnt[perm_idx]
                rev_p = rev[perm_idx]
                rate_p = (rev_p + ALPHA_SHRINK * p0) / (cnt_p + ALPHA_SHRINK)
                rows_perm.append({"score": rate_p[p_te], "y": r_te})
    # ---- aggregate ----
    sc = np.concatenate([r["score"] for r in rows_obs])
    yy = np.concatenate([r["y"] for r in rows_obs])
    auc_obs = auc(yy, sc)
    lift = []
    base = float(yy.mean())
    order = np.argsort(-sc)
    for frac in (0.01, 0.02, 0.05, 0.10, 0.20):
        k = max(1, int(frac * yy.size))
        sel = order[:k]
        prec = float(yy[sel].mean())
        lift.append({"top_fraction": frac, "n": int(k), "precision": prec, "baseline": base,
                     "lift": prec / base if base > 0 else None,
                     "recall": float(yy[sel].sum() / yy.sum()) if yy.sum() else None})
    # calibration in score deciles
    qs = pd.qcut(sc, 10, labels=False, duplicates="drop")
    calib = []
    for q in range(int(qs.max()) + 1):
        m = qs == q
        calib.append({"decile": q, "n": int(m.sum()), "mean_predicted": float(sc[m].mean()),
                      "observed": float(yy[m].mean())})
    perm_sc = np.concatenate([r["score"] for r in rows_perm])
    perm_y = np.concatenate([r["y"] for r in rows_perm])
    auc_perm = auc(perm_y, perm_sc)

    res = {"kind": "e008_base_rate_and_permutation_checks",
           "input_sha256": sha256(CSV), "floor": FLOOR,
           "n_observations": int(yy.size), "baseline_reversal_rate": base,
           "auc_observed_drugpair": auc_obs,
           "auc_permuted_drugpair_labels": auc_perm,
           "permutation_note": ("the same pipeline on shuffled drug-pair labels; a value near 0.5 "
                                "confirms the 0.92 did not come from support, shrinkage or spacing"),
           "lift_table": lift, "calibration_deciles": calib,
           "files": {}}
    for rel in ("research/2026-10-27-agent-cell-identifiability-r7/e008b_lift_and_permutation.py",
                str(CSV.relative_to(ROOT))):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E008B_CHECKS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    print("n=%d baseline=%.4f | AUC observed=%.4f | AUC permuted labels=%.4f" % (yy.size, base, auc_obs, auc_perm))
    for l in lift:
        print("  top %4.0f%%: n=%6d precision=%.4f lift=%.2fx recall=%.3f" % (
            100 * l["top_fraction"], l["n"], l["precision"], l["lift"] or float("nan"), l["recall"] or float("nan")))
    print("  calibration (decile mean_pred -> observed):")
    for c in calib:
        print("    %2d n=%6d pred=%.4f obs=%.4f" % (c["decile"], c["n"], c["mean_predicted"], c["observed"]))


if __name__ == "__main__":
    main()
