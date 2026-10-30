"""E023: can an unseen compound *pair* be predicted from compound main effects?

Pre-registered in PROTOCOL_E023.md. Reads only PAIR_SCREEN.csv.

Unit = (layout, cell) with ~351 compound pairs. Model y ~ mu + a_A + a_B with a fixed
ridge penalty (lambda = 1.0, no tuning). Leave-one-pair-out predictions come from the
hat-matrix identity resid_loo_i = e_i / (1 - H_ii), so no refitting is needed.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r23"
ANCHORS = {"high control", "low control"}
LAMBDA = 1.0
TOP = 10
N_BOOT = 1000
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def spearman(a, b) -> float:
    if len(a) < 8:
        return float("nan")
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    ra -= ra.mean()
    rb -= rb.mean()
    den = math.sqrt(float((ra ** 2).sum()) * float((rb ** 2).sum()))
    return float((ra * rb).sum() / den) if den > 0 else float("nan")


def loo_ridge(X: np.ndarray, y: np.ndarray, lam: float = LAMBDA):
    """Return leave-one-out predictions and leverages for ridge with an intercept."""
    n, p = X.shape
    xm = X.mean(axis=0)
    Xc = X - xm
    ym = y.mean()
    yc = y - ym
    A = Xc.T @ Xc + lam * np.eye(p)
    Ainv = np.linalg.inv(A)
    H = Xc @ Ainv @ Xc.T
    h = np.clip(np.diag(H), 0.0, 1.0 - 1e-9)
    fit = ym + H @ yc
    resid = y - fit
    loo_resid = resid / (1.0 - h)
    return y - loo_resid, h


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    df = pd.read_csv(CSV, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: "row_id"})
    for c in ("Drug 1", "Drug 2", "Cell line", "file", "Well"):
        df[c] = df[c].astype(str).str.strip()
    df["failed_qc"] = df["Failed QC"].astype(str).str.strip().str.lower().isin(["true", "1"])
    df["y"] = pd.to_numeric(df["Viability"], errors="coerce")
    df["c1"] = pd.to_numeric(df["Conc 1 (uM)"], errors="coerce")
    df["c2"] = pd.to_numeric(df["Conc 2 (uM)"], errors="coerce")
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    ok = df[(~df["anchor"]) & (~df["failed_qc"]) & df["y"].notna()]

    meta = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], g["c1"].round(9), g["Drug 2"], g["c2"].round(9))))
        meta[fname] = {"cell": g["Cell line"].iloc[0],
                       "h": hashlib.sha1(repr(layout).encode()).hexdigest(),
                       "qc": float(g["failed_qc"].mean()),
                       "npairs": int(g.groupby(["Drug 1", "Drug 2"]).ngroups)}
    groups = {}
    for f, s in meta.items():
        groups.setdefault(s["h"], {}).setdefault(s["cell"], []).append(f)

    rows = []
    for h, cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 2:
            continue
        if max(meta[f]["npairs"] for c in good for f in cells[c]) < 100:
            continue
        per_cell = {}
        for c in good:
            vs = []
            for f in cells[c]:
                s = ok[ok["file"] == f]
                v = s.groupby(["Drug 1", "Drug 2"])["y"].mean()
                if len(v) >= 100:
                    vs.append(v)
            if vs:
                per_cell[c] = pd.concat(vs, axis=1).mean(axis=1)
        for c, ser in per_cell.items():
            ser = ser.dropna()
            if len(ser) < 150:
                continue
            pairs = list(ser.index)
            y = ser.to_numpy(float)
            comps = sorted({d for p in pairs for d in p})
            cidx = {d: i for i, d in enumerate(comps)}
            X = np.zeros((len(pairs), len(comps)))
            for i, (a, b) in enumerate(pairs):
                X[i, cidx[a]] += 1.0
                X[i, cidx[b]] += 1.0
            loo, lev = loo_ridge(X, y)
            rho = spearman(loo, y)
            # precision@10 on the LOO predictions
            k = min(TOP, len(y) - 1)
            p10 = len(set(np.argsort(loo)[:k]) & set(np.argsort(y)[:k])) / k
            # coverage of each pair = number of other pairs containing either compound
            deg = X.sum(axis=0)
            cov = np.array([deg[cidx[a]] + deg[cidx[b]] for a, b in pairs])
            # cross-cell control
            others = [x for x in per_cell if x != c]
            mo = pd.concat([per_cell[o] for o in others], axis=1).reindex(ser.index).mean(axis=1).to_numpy(float)
            rho_cross = spearman(mo, y) if np.isfinite(mo).all() else float("nan")
            rows.append({"layout": h[:12], "cell": c, "n_pairs": len(y), "n_compounds": len(comps),
                         "rho_additive": rho, "precision10_additive": p10,
                         "rho_cross_cell": rho_cross, "mean_leverage": float(lev.mean()),
                         "cov_q1": float(np.quantile(cov, 0.25)), "y": y, "loo": loo, "cov": cov})

    d = pd.DataFrame([{k: v for k, v in r.items() if k not in ("y", "loo", "cov")} for r in rows])
    res = {"kind": "unseen_compound_pair_from_compound_main_effects",
           "input_sha256": sha256(CSV),
           "settings": {"lambda": LAMBDA, "top": TOP, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"units": len(rows), "layouts": int(d["layout"].nunique()) if len(d) else 0,
                     "median_pairs": float(d["n_pairs"].median()) if len(d) else None,
                     "median_compounds": float(d["n_compounds"].median()) if len(d) else None},
           "files": {}}

    def summ(col):
        v = d[col].dropna().to_numpy(float)
        if not len(v):
            return None
        rng = np.random.default_rng(SEED + 21)
        boots = [float(np.mean(rng.choice(v, size=len(v), replace=True))) for _ in range(N_BOOT)]
        return {"n": int(len(v)), "mean": float(v.mean()), "median": float(np.median(v)),
                "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}

    if len(d):
        res["additive_loo"] = summ("rho_additive")
        res["additive_precision10"] = summ("precision10_additive")
        res["cross_cell_control"] = summ("rho_cross_cell")
        # coverage bins: pool standardised residuals by coverage tercile
        loo_all, y_all, cov_all = [], [], []
        for r in rows:
            loo_all.append(r["loo"])
            y_all.append(r["y"])
            cov_all.append(r["cov"])
        loo_all = np.concatenate(loo_all)
        y_all = np.concatenate(y_all)
        cov_all = np.concatenate(cov_all)
        q = np.quantile(cov_all, [1 / 3, 2 / 3])
        bins = np.digitize(cov_all, q)
        bin_rho = {}
        for b in range(3):
            m = bins == b
            if m.sum() > 20:
                bin_rho[str(b)] = {"n": int(m.sum()), "rho": spearman(loo_all[m], y_all[m]),
                                   "cov_range": [float(cov_all[m].min()), float(cov_all[m].max())]}
        res["by_coverage_tercile"] = bin_rho
        a = res["additive_loo"]
        h052 = bool(a["median"] > 0.15 and a["ci95"][0] > 0)
        h053 = bool(a["median"] >= 0.35)
        if len(bin_rho) == 3:
            lo, hi = bin_rho["0"]["rho"], bin_rho["2"]["rho"]
            h054 = bool(hi - lo > 0)
        else:
            h054 = False
        res["by_coverage_summary"] = {"low_minus_high": (bin_rho["2"]["rho"] - bin_rho["0"]["rho"])
                                      if len(bin_rho) == 3 else None}
    else:
        h052 = h053 = h054 = False
    res["decisions"] = {"H052_beats_constant": h052, "H053_substantial": h053,
                        "H054_improves_with_coverage": h054}
    res["decisions"]["verdict"] = ("unseen_pair_predictable" if h052 and h053 else
                                   "detectable_but_weak" if h052 else
                                   "unseen_pair_not_predictable")
    res["limits"] = [
        "This is an unseen COMBINATION (both compounds seen elsewhere), not an unseen drug.",
        "The additive model is the hypothesis under test, not a premise; no interaction terms are fitted.",
        "Lambda is fixed at 1.0 with no tuning, so the result is conservative by construction.",
        "No dose dimension; functional viability only; exploratory.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r23/PROTOCOL_E023.md",
                "research/2026-10-27-agent-cell-identifiability-r23/e023_unseen_pair.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E023_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(d):
        d.to_csv(OUT / "E023_units.csv", index=False)

    print("units=%d layouts=%d median_pairs=%s median_compounds=%s" % (
        len(rows), res["audit"]["layouts"], res["audit"]["median_pairs"], res["audit"]["median_compounds"]))
    for k in ("additive_loo", "additive_precision10", "cross_cell_control"):
        if k in res and res[k]:
            print("  %-22s %s" % (k, json.dumps({kk: (round(vv, 4) if isinstance(vv, float) else vv)
                                                 for kk, vv in res[k].items() if kk != "ci95"}) + " ci=" + str([round(x, 4) for x in res[k]["ci95"]])))
    print("  by coverage tercile:", json.dumps(res.get("by_coverage_tercile"), ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
