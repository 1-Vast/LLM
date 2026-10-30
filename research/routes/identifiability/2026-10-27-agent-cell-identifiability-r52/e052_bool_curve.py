"""E051: the full pool-size curve inside one task, from 100 to 21,652 keys.

Pre-registered in PROTOCOL_E050.md. Training set fixed; only the evaluation pool size varies.
Two absolute budgets (k=20 and k=50) to see whether the crossover moves with k.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r52"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
SIZES = (100, 300, 1000, 3000, 10000, 21652)
KS = (20, 50)
REPEATS = 40
SEARCH = list(range(0, 20))
EVAL = list(range(20, 40))
N_BOOT = 2000
SEED = 20261027
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", METRIC, "Synergy"]


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


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d[METRIC] = pd.to_numeric(d[METRIC], errors="coerce")
    d = d[np.isfinite(d[METRIC])].copy()
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["CELL_LINE_NAME"].astype(str) + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    d = d.groupby("key", as_index=False).agg(
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"), tissue=("Tissue", "first"),
        synergy=(METRIC, "mean"), syn=("syn", "mean"))
    d["syn"] = d["syn"] > 0.5
    for c in ("tissue", "ap", "lp"):
        d[c] = d[c].astype(str).fillna("NA")

    blocks = []
    for c in ("tissue", "ap", "lp"):
        lv = sorted(d[c].unique())
        M = np.zeros((len(d), len(lv)))
        vals = d[c].to_numpy()
        for j, v in enumerate(lv):
            M[:, j] = (vals == v).astype(float)
        blocks.append(M)
    X = np.hstack(blocks)
    y = d.synergy.to_numpy(float)
    syn = d.syn.to_numpy(bool)

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        perm = rng.permutation(len(y))
        ntr = int(0.8 * len(y))
        tr, full_pool = perm[:ntr], perm[ntr:]
        Xtr, ytr = X[tr], y[tr]
        mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
        sd[sd == 0] = 1.0
        Xs = (Xtr - mu) / sd
        A = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
        Ainv = np.linalg.inv(A)
        w = Ainv @ Xs.T @ (ytr - ytr.mean())
        for S in SIZES:
            pool = full_pool.copy() if S >= len(full_pool) else rng.choice(full_pool, size=S, replace=False)
            Xp = (X[pool] - mu) / sd
            pred = ytr.mean() + Xp @ w
            var = np.einsum("ij,jk,ik->i", Xp, Ainv, Xp)
            strong = syn[pool]  # base rate about 1.4%, R37/R48/R49 definition
            rp = pd.Series(pred).rank(pct=True).to_numpy()
            rv = pd.Series(var).rank(pct=True).to_numpy()
            mix = rp + rv
            for k in KS:
                if k >= len(pool) // 3:
                    continue
                e_idx = np.argsort(-rp)[:k]
                m_idx = np.argsort(-mix)[:k]
                rows.append({"rep": rep, "S": S, "k": k,
                             "exploit": float(strong[e_idx].mean()),
                             "mix": float(strong[m_idx].mean())})

    r = pd.DataFrame(rows)
    res = {"kind": "pool_size_curve_synergy_boolean_target",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"sizes": list(SIZES), "ks": list(KS), "repeats": REPEATS,
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(y)), "max_pool": int(len(y) - int(0.8 * len(y)))},
           "curve": {}, "files": {}}

    for k in KS:
        ent = {}
        for S in SIZES:
            sub = r[(r.k == k) & (r.S == S)]
            if not len(sub):
                continue
            m = sub.set_index("rep")["mix"]
            e = sub.set_index("rep")["exploit"]
            ent[str(S)] = {"all": paired(m, e, 801 + S % 83 + k),
                           "search": paired(m[m.index.isin(SEARCH)], e[e.index.isin(SEARCH)], 901 + S % 83 + k),
                           "eval": paired(m[m.index.isin(EVAL)], e[e.index.isin(EVAL)], 1001 + S % 83 + k),
                           "exploit_hit": float(e.mean()), "mix_hit": float(m.mean())}
        res["curve"][str(k)] = ent

    def crossover(ent):
        ks = [S for S in SIZES if str(S) in ent]
        sign_change = None
        for i in range(len(ks) - 1):
            a = ent[str(ks[i])]["all"]["mean_diff"]
            b = ent[str(ks[i + 1])]["all"]["mean_diff"]
            if a < 0 <= b:
                sign_change = (ks[i], ks[i + 1])
        return sign_change

    res["crossover"] = {str(k): crossover(res["curve"][str(k)]) for k in KS}

    def monotone(ent):
        ks = [S for S in SIZES if str(S) in ent]
        viol = sum(1 for i in range(len(ks) - 1)
                   if ent[str(ks[i])]["all"]["mean_diff"] > ent[str(ks[i + 1])]["all"]["mean_diff"] + 1e-9)
        return viol

    res["monotonicity_violations"] = {str(k): monotone(res["curve"][str(k)]) for k in KS}
    h129 = all(v <= 1 for v in res["monotonicity_violations"].values())
    h130 = all(res["crossover"][str(k)] is not None for k in KS)
    c20, c50 = res["crossover"]["20"], res["crossover"]["50"]
    h131 = bool(c20 and c50 and c50[1] >= c20[1])
    res["decisions"] = {"H129_monotone": h129, "H130_crossover_exists": h130,
                        "H131_crossover_moves_with_k": h131}
    res["decisions"]["verdict"] = ("quantitative_pool_condition" if h130 else
                                   "monotone_but_no_crossover_observed")
    res["limits"] = [
        "Single dataset; the pool is drawn from the held-out 20% so the maximum is 21,652.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r51/PROTOCOL_E050.md",
                "research/2026-10-27-agent-cell-identifiability-r51/e051_pool_curve.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E052_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E052_rows.csv", index=False)

    print("keys=%d max pool=%d" % (len(y), res["audit"]["max_pool"]))
    for k in KS:
        print("  k=%d" % k)
        for S in SIZES:
            if str(S) in res["curve"][str(k)]:
                c = res["curve"][str(k)][str(S)]["all"]
                print("     S=%-6d exploit=%.4f mix=%.4f | all %+.4f [%+.4f,%+.4f]" % (
                    S, res["curve"][str(k)][str(S)]["exploit_hit"],
                    res["curve"][str(k)][str(S)]["mix_hit"],
                    c["mean_diff"], c["ci95"][0], c["ci95"][1]))
    print("crossover:", json.dumps(res["crossover"], ensure_ascii=False))
    print("violations:", res["monotonicity_violations"])
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
