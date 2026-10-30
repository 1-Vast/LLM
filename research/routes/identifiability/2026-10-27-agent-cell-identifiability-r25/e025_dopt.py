"""E025: with the same budget, does D-optimal selection beat random selection?

Pre-registered in PROTOCOL_E025.md. Reads only PAIR_SCREEN.csv.

Design matrix X: 0/1 membership of each compound pair in each compound. Greedy D-optimal
selection maximises log det(X_sel' X_sel + lambda I) one row at a time. The additive model
is then fitted on the selected pairs only and scored on the unselected remainder.
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
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r25"
ANCHORS = {"high control", "low control"}
LAMBDA = 1.0
MS = (5, 10, 25, 50)
REPS = 20
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


def p_at_k(pred, truth, k=TOP):
    n = len(pred)
    kk = min(k, n - 1)
    return len(set(np.argsort(pred)[:kk]) & set(np.argsort(truth)[:kk])) / kk


def design(pairs, cidx):
    X = np.zeros((len(pairs), len(cidx)))
    for i, (a, b) in enumerate(pairs):
        X[i, cidx[a]] += 1.0
        X[i, cidx[b]] += 1.0
    return X


def dopt_select(X, m, lam=LAMBDA):
    """Greedy D-optimal rows: maximise log det of the accumulated information matrix."""
    p = X.shape[1]
    A = lam * np.eye(p)
    Ainv = np.eye(p) / lam
    chosen = []
    avail = np.ones(X.shape[0], dtype=bool)
    for _ in range(min(m, X.shape[0])):
        Xa = X[avail]
        # gain for row x: log(1 + x' Ainv x)
        gains = np.einsum("ij,jk,ik->i", Xa, Ainv, Xa)
        best = int(np.argmax(gains))
        idx = np.where(avail)[0][best]
        x = X[idx]
        Ainv = Ainv - np.outer(Ainv @ x, x @ Ainv) / (1.0 + float(x @ Ainv @ x))
        chosen.append(idx)
        avail[idx] = False
    return np.array(chosen)


def fit_predict(Xtr, ytr, Xte, lam=LAMBDA):
    xm = Xtr.mean(axis=0)
    ym = float(ytr.mean())
    Xc = Xtr - xm
    A = Xc.T @ Xc + lam * np.eye(Xtr.shape[1])
    w = np.linalg.solve(A, Xc.T @ (ytr - ym))
    return ym + (Xte - xm) @ w


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

    rng = np.random.default_rng(SEED)
    rows, base_rows = [], []
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
                per_cell[c] = pd.concat(vs, axis=1).mean(axis=1).dropna()
        for c, ser in per_cell.items():
            if len(ser) < 200:
                continue
            pairs = list(ser.index)
            y = ser.to_numpy(float)
            comps = sorted({d for p in pairs for d in p})
            cidx = {d: i for i, d in enumerate(comps)}
            X = design(pairs, cidx)
            n = len(y)
            for m in MS:
                if m >= n - TOP - 5:
                    continue
                # dopt
                sel = dopt_select(X, m)
                mask = np.ones(n, dtype=bool)
                mask[sel] = False
                pred = fit_predict(X[sel], y[sel], X[mask])
                rows.append({"layout": h[:12], "cell": c, "m": m, "arm": "dopt",
                             "precision10": p_at_k(pred, y[mask]),
                             "spearman": spearman(pred, y[mask])})
                # random (averaged)
                vals, rhos = [], []
                for _ in range(REPS):
                    rsel = rng.choice(n, size=m, replace=False)
                    rmask = np.ones(n, dtype=bool)
                    rmask[rsel] = False
                    rpred = fit_predict(X[rsel], y[rsel], X[rmask])
                    vals.append(p_at_k(rpred, y[rmask]))
                    rhos.append(spearman(rpred, y[rmask]))
                rows.append({"layout": h[:12], "cell": c, "m": m, "arm": "random",
                             "precision10": float(np.mean(vals)), "spearman": float(np.mean(rhos))})
                # m=0 baseline: mean prediction (constant) -> precision@10 of a constant is undefined,
                # so use the cross-cell-free baseline from R22: rank by nothing => chance
                base_rows.append({"layout": h[:12], "cell": c, "m": 0,
                                  "precision10": TOP / (n - TOP), "spearman": 0.0})

    d = pd.DataFrame(rows)
    res = {"kind": "d_optimal_versus_random_selection_same_budget",
           "input_sha256": sha256(CSV),
           "settings": {"lambda": LAMBDA, "ms": list(MS), "reps": REPS, "top": TOP,
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"units": int(d.groupby(["layout", "cell"]).ngroups) if len(d) else 0,
                     "layouts": int(d["layout"].nunique()) if len(d) else 0},
           "by_m": {}, "files": {}}

    def bsum(v, seed_off):
        v = np.asarray(v, float)
        v = v[np.isfinite(v)]
        if not len(v):
            return None
        rng2 = np.random.default_rng(SEED + seed_off)
        boots = [float(np.mean(rng2.choice(v, size=len(v), replace=True))) for _ in range(N_BOOT)]
        return {"n": int(len(v)), "mean": float(v.mean()), "median": float(np.median(v)),
                "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}

    if len(d):
        wide = d.pivot_table(index=["layout", "cell", "m"], columns="arm", values="precision10").reset_index()
        for m in MS:
            sub = wide[wide["m"] == m]
            if not len(sub):
                continue
            res["by_m"][str(m)] = {
                "dopt": bsum(sub["dopt"].to_numpy(float), 41),
                "random": bsum(sub["random"].to_numpy(float), 42),
                "diff": bsum((sub["dopt"] - sub["random"]).to_numpy(float), 43)}
        diffs = {m: res["by_m"][str(m)]["diff"] for m in MS if str(m) in res["by_m"]}
        h058 = bool(diffs and all(diffs[m]["ci95"][0] > 0 for m in MS if m in diffs))
        h058_any = bool(diffs and all(diffs[m]["mean"] > 0 for m in MS if m in diffs))
        base = d.merge(pd.DataFrame(base_rows), on=["layout", "cell", "m"], how="left", suffixes=("", "_base"))
        m10 = res["by_m"].get("10")
        h059 = bool(m10 and (m10["dopt"]["mean"] - 0.029) >= 0.03)
        d10 = diffs.get(10, {}).get("mean") if 10 in diffs else None
        d50 = diffs.get(50, {}).get("mean") if 50 in diffs else None
        h060 = bool(d10 is not None and d50 is not None and d50 <= 0.5 * d10)
    else:
        h058 = h058_any = h059 = h060 = False
    res["decisions"] = {"H058_dopt_beats_random_strict": h058, "H058_dopt_beats_random_pointwise": h058_any,
                        "H059_ten_pairs_worth_3pp": h059, "H060_gain_shrinks_with_budget": h060}
    res["decisions"]["verdict"] = ("selection_beats_volume" if h058_any and h059 else
                                   "selection_helps_but_small" if h058_any else
                                   "selection_has_no_value")
    res["limits"] = [
        "This is a ranking quantity (precision@10), NOT a regret-based decision value; R9's stop condition is untouched.",
        "D-optimality is taken on the additive design only; it is not a globally optimal experimental design.",
        "Unseen COMBINATION, not unseen drug; no dose dimension.",
        "Functional viability only; exploratory.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r25/PROTOCOL_E025.md",
                "research/2026-10-27-agent-cell-identifiability-r25/e025_dopt.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E025_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(d):
        d.to_csv(OUT / "E025_rows.csv", index=False)

    print("units=%d layouts=%d" % (res["audit"]["units"], res["audit"]["layouts"]))
    for m, v in res["by_m"].items():
        print("   m=%-3s dopt=%.3f random=%.3f diff=%+.3f CI=[%.3f,%.3f]" % (
            m, v["dopt"]["mean"], v["random"]["mean"], v["diff"]["mean"],
            v["diff"]["ci95"][0], v["diff"]["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
