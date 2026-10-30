"""E108: does a stronger prior raise the bar for personalisation?

The minimal-evidence threshold was measured against drug marginals (R76/R77: about 5-8% of the
pool). The best predictor is now identity+pathway, so the same question is re-asked against that
stronger prior: personal data must now beat a better baseline.

Pre-registered in PROTOCOL_E103.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r108"
LAMBDA = 1.0
K = 20
MS = (10, 25, 50, 100, 200)
DRAWS = 30
N_BOOT = 2000
SEED = 20261027
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME",
       "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", "Synergy"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def paired(a, b, off):
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    if len(j) < 3:
        return None
    dif = (j["a"] - j["b"]).to_numpy(float)
    rng = np.random.default_rng(SEED + off)
    boots = [float(np.mean(rng.choice(dif, size=len(dif), replace=True))) for _ in range(N_BOOT)]
    return {"n": int(len(dif)), "mean_diff": float(dif.mean()),
            "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}


def onehot(vals, levels):
    idx = {v: j for j, v in enumerate(levels)}
    M = np.zeros((len(vals), len(levels)))
    for t, v in enumerate(vals):
        j = idx.get(v)
        if j is not None:
            M[t, j] = 1.0
    return M


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    g = d.groupby("key", as_index=False).agg(
        cell=("CELL_LINE_NAME", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        tissue=("Tissue", "first"), syn=("syn", "mean"))
    g["syn"] = g["syn"] > 0.5
    for c in ("cell", "a", "b", "ap", "lp", "tissue"):
        g[c] = g[c].astype(str).fillna("NA")

    A = g["a"].to_numpy(); B = g["b"].to_numpy(); CELL = g["cell"].to_numpy()
    drugs = sorted(set(A) | set(B)); cells = sorted(set(CELL))
    Xid = np.hstack([onehot(A, drugs), onehot(B, drugs)])
    Xpa = np.hstack([onehot(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                     onehot(g["lp"].to_numpy(), sorted(g["lp"].unique())),
                     onehot(g["tissue"].to_numpy(), sorted(g["tissue"].unique()))])
    Xcombo = np.hstack([Xid, Xpa])
    y = g["syn"].to_numpy(bool)

    rng = np.random.default_rng(SEED)
    rows = []
    for _ in range(DRAWS):
        held = cells[int(rng.integers(0, len(cells)))]
        po = np.where(CELL == held)[0]
        tr = np.where(CELL != held)[0]
        if len(po) < 600 or len(tr) < 50000:
            continue
        ytr = y[tr].astype(float)
        # prior 1: marginal (two-way additive)
        grand = float(ytr.mean())
        dm = {}
        for i in tr:
            dm.setdefault(A[i], []).append(y[i])
            dm.setdefault(B[i], []).append(y[i])
        deff = {k: float(np.mean(v)) - grand for k, v in dm.items()}
        base_marg = np.array([deff.get(A[i], 0.0) + deff.get(B[i], 0.0) + grand for i in po])
        # prior 2: identity+pathway ridge
        Xt = Xcombo[tr]
        mu, sd = Xt.mean(axis=0), Xt.std(axis=0); sd[sd == 0] = 1.0
        Z = (Xt - mu) / sd
        w = np.linalg.solve(Z.T @ Z + LAMBDA * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
        base_combo = ytr.mean() + ((Xcombo[po] - mu) / sd) @ w

        perm = rng.permutation(len(po))
        for m in MS:
            if m >= len(po) // 2:
                continue
            meas = po[perm[:m]]
            rest = po[perm[m:]]
            row = {"cell": held, "m": m, "n_rest": len(rest), "base_rate": float(y[rest].mean())}
            for nm, base in (("marginal", base_marg), ("combo", base_combo)):
                idx = {v: j for j, v in enumerate(po)}
                sc_base_rest = np.array([base[idx[i]] for i in rest])
                res_meas = np.array([y[i] - base[idx[i]] for i in meas])
                # cell-level residual correction: a single offset estimated from the m measured keys
                off = float(res_meas.mean())
                sc_pers = sc_base_rest + off
                row[nm + "_prior"] = float(y[rest][np.argsort(-sc_base_rest)[:K]].mean())
                row[nm + "_pers"] = float(y[rest][np.argsort(-sc_pers)[:K]].mean())
                row[nm + "_offset"] = off
            rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "does_a_stronger_prior_raise_the_personalisation_bar",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "ms": list(MS), "draws": DRAWS, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "units": int(len(r))},
           "by_m": {}, "files": {}}

    for m in MS:
        sub = r[r.m == m]
        if len(sub) < 5:
            continue
        res["by_m"][str(m)] = {
            "n": int(len(sub)),
            "marginal_prior": float(sub["marginal_prior"].mean()),
            "marginal_pers": float(sub["marginal_pers"].mean()),
            "combo_prior": float(sub["combo_prior"].mean()),
            "combo_pers": float(sub["combo_pers"].mean()),
            "combo_prior_minus_marginal_prior": paired(sub["combo_prior"], sub["marginal_prior"], 34001 + m),
            "combo_pers_minus_combo_prior": paired(sub["combo_pers"], sub["combo_prior"], 34101 + m)}

    def first_sig(nm_prior, nm_pers, off0):
        for m in MS:
            e = res["by_m"].get(str(m))
            if not e:
                continue
            c = paired(r[r.m == m][nm_pers], r[r.m == m][nm_prior], off0 + m)
            if c and c["ci95"][0] > 0:
                return m
        return None

    first_marg = first_sig("marginal_prior", "marginal_pers", 35001)
    first_combo = first_sig("combo_prior", "combo_pers", 36001)
    res["thresholds"] = {"marginal": first_marg, "combo": first_combo}
    h279 = bool(first_combo is not None and first_marg is not None and first_combo > first_marg)
    h280 = bool(first_combo is not None and first_marg is not None and first_combo < first_marg)
    h281 = bool(first_combo == first_marg)
    res["decisions"] = {"H279_bar_raised": h279, "H280_bar_lowered": h280, "H281_same": h281}
    res["decisions"]["verdict"] = (
        "stronger_prior_raises_the_bar" if h279 else
        "stronger_prior_lowers_the_bar" if h280 else
        "threshold_unchanged")
    res["limits"] = [
        "The personalisation arm is a single cell-level offset estimated from the m measured keys; other constructions may shift the threshold.",
        "Only five m values, so the threshold resolution is coarse.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r108/PROTOCOL_E103.md",
                "research/2026-10-27-agent-cell-identifiability-r108/e108_prior_strength.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E108_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E108_rows.csv", index=False)

    print("units=%d thresholds: marginal=%s combo=%s" % (len(r), first_marg, first_combo))
    for m in MS:
        e = res["by_m"].get(str(m))
        if not e:
            continue
        d1 = e["combo_prior_minus_marginal_prior"]; d2 = e["combo_pers_minus_combo_prior"]
        print("  m=%-4d marg prior %.4f pers %.4f | combo prior %.4f pers %.4f" % (
            m, e["marginal_prior"], e["marginal_pers"], e["combo_prior"], e["combo_pers"]))
        print("      comboPrior-margPrior %+.4f [%+.4f,%+.4f] | comboPers-comboPrior %+.4f [%+.4f,%+.4f]" % (
            d1["mean_diff"], d1["ci95"][0], d1["ci95"][1], d2["mean_diff"], d2["ci95"][0], d2["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
