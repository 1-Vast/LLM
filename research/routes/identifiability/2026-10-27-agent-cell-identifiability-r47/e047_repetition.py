"""E047: does the mix advantage really grow with the number of cells through which the same
combination repeats inside the candidate pool?

Pre-registered in PROTOCOL_E046.md. Pool size is held at about 4,000 keys; only the
repetition depth r varies.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r47"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
REPS = (1, 2, 4, 8)
POOL_TARGET = 4000
KS = (50, 100)
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
        combo=("combo", "first"), tissue=("Tissue", "first"), ap=("ANCHOR_PATHWAY", "first"),
        lp=("LIBRARY_PATHWAY", "first"), synergy=(METRIC, "mean"), syn=("syn", "mean"))
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
    combo = d["combo"].to_numpy()

    by_combo = {}
    for c in pd.unique(combo):
        by_combo[c] = np.where(combo == c)[0]
    eligible = [c for c, idx in by_combo.items() if len(idx) >= 8]
    rng = np.random.default_rng(SEED)

    rows = []
    for r in REPS:
        n_combos = max(50, POOL_TARGET // r)
        for rep in range(REPEATS):
            rng.shuffle(eligible)
            pool_idx, used = [], set()
            for c in eligible:
                if len(pool_idx) >= POOL_TARGET:
                    break
                idx = by_combo[c]
                pick = rng.choice(idx, size=min(r, len(idx)), replace=False)
                pool_idx.extend(pick.tolist())
                used.update(pick.tolist())
            pool = np.array(sorted(set(pool_idx)))
            tr = np.array([i for i in range(len(y)) if i not in used])
            if len(tr) < 5000 or len(pool) < 1000:
                continue
            Xtr, ytr = X[tr], y[tr]
            mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
            sd[sd == 0] = 1.0
            Xs = (Xtr - mu) / sd
            Xp = (X[pool] - mu) / sd
            A = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
            Ainv = np.linalg.inv(A)
            w = Ainv @ Xs.T @ (ytr - ytr.mean())
            pred = ytr.mean() + Xp @ w
            var = np.einsum("ij,jk,ik->i", Xp, Ainv, Xp)
            rp = pd.Series(pred).rank(pct=True).to_numpy()
            rv = pd.Series(var).rank(pct=True).to_numpy()
            mix = rp + rv
            for k in KS:
                for strat, sc in (("exploit", rp), ("mix", mix)):
                    idx = np.argsort(-sc)[:k]
                    rows.append({"r": r, "rep": rep, "k": k, "strategy": strat,
                                 "hit": float(syn[pool][idx].mean()),
                                 "n_pool": int(len(pool)), "n_combos_in_pool": int(len(set(combo[pool])))})

    rr = pd.DataFrame(rows)
    res = {"kind": "mix_advantage_versus_repetition_depth_in_pool",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"lambda": LAMBDA, "reps": list(REPS), "pool_target": POOL_TARGET,
                        "ks": list(KS), "repeats": REPEATS, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(d)), "combos": int(len(by_combo)),
                     "eligible_combos": len(eligible)},
           "by_r": {}, "files": {}}

    for r in REPS:
        ent = {"by_k": {}}
        for k in KS:
            sub = rr[(rr.r == r) & (rr.k == k)]
            m = sub[sub.strategy == "mix"].set_index("rep")["hit"]
            e = sub[sub.strategy == "exploit"].set_index("rep")["hit"]
            ent["by_k"][str(k)] = {
                "search": paired(m[m.index.isin(SEARCH)], e[e.index.isin(SEARCH)], 111 + r),
                "eval": paired(m[m.index.isin(EVAL)], e[e.index.isin(EVAL)], 211 + r),
                "mix_minus_exploit_all": paired(m, e, 311 + r),
                "exploit_hit": float(e.mean()), "mix_hit": float(m.mean())}
        ent["n_pool_median"] = float(rr[rr.r == r]["n_pool"].median())
        ent["n_combos_median"] = float(rr[rr.r == r]["n_combos_in_pool"].median())
        res["by_r"][str(r)] = ent

    diffs = {r: res["by_r"][str(r)]["by_k"]["50"]["mix_minus_exploit_all"]["mean_diff"] for r in REPS}
    h121 = bool(all(diffs[REPS[i]] <= diffs[REPS[i + 1]] + 1e-9 for i in range(len(REPS) - 1))
                and (diffs[REPS[-1]] - diffs[REPS[0]]) > 0)
    pair = None
    a = rr[(rr.r == REPS[-1]) & (rr.k == 50) & (rr.strategy == "mix")].set_index("rep")["hit"]
    av = rr[(rr.r == REPS[-1]) & (rr.k == 50) & (rr.strategy == "exploit")].set_index("rep")["hit"]
    b = rr[(rr.r == REPS[0]) & (rr.k == 50) & (rr.strategy == "mix")].set_index("rep")["hit"]
    bv = rr[(rr.r == REPS[0]) & (rr.k == 50) & (rr.strategy == "exploit")].set_index("rep")["hit"]
    d_hi = (a - av)
    d_lo = (b - bv)
    j = pd.concat([d_hi.rename("a"), d_lo.rename("b")], axis=1).dropna()
    if len(j) >= 3:
        dd = (j["a"] - j["b"]).to_numpy(float)
        rng2 = np.random.default_rng(SEED + 99)
        boots = [float(np.mean(rng2.choice(dd, size=len(dd), replace=True))) for _ in range(N_BOOT)]
        pair = {"diff_of_diffs": float(dd.mean()),
                "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}
    res["r8_minus_r1"] = pair
    c1 = res["by_r"]["1"]["by_k"]["50"]["mix_minus_exploit_all"]
    h122 = bool(c1 and c1["ci95"][0] <= 0 <= c1["ci95"][1])
    res["decisions"] = {"H121_mix_grows_with_repetition": h121, "H122_no_advantage_at_r1": h122}
    res["decisions"]["verdict"] = (
        "repetition_mechanism_supported" if h121 and pair and pair["ci95"][0] > 0 else
        "mechanism_not_supported" if not h121 else
        "monotone_but_pairwise_ci_includes_zero")
    res["limits"] = [
        "Single dataset, pathway features only, two k values.",
        "r also changes the number of distinct combinations in the pool (4000/r), so repetition and combination diversity are not fully separated.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r47/PROTOCOL_E046.md",
                "research/2026-10-27-agent-cell-identifiability-r47/e047_repetition.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E047_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    rr.to_csv(OUT / "E047_rows.csv", index=False)

    print("keys=%d combos=%d eligible=%d" % (res["audit"]["keys"], res["audit"]["combos"], len(eligible)))
    for r in REPS:
        e = res["by_r"][str(r)]
        k50 = e["by_k"]["50"]
        print("  r=%d pool=%.0f combos=%.0f | k=50 exploit=%.4f mix=%.4f | all %+.4f [%+.4f,%+.4f] | search %+.4f eval %+.4f" % (
            r, e["n_pool_median"], e["n_combos_median"], k50["exploit_hit"], k50["mix_hit"],
            k50["mix_minus_exploit_all"]["mean_diff"], k50["mix_minus_exploit_all"]["ci95"][0],
            k50["mix_minus_exploit_all"]["ci95"][1], k50["search"]["mean_diff"], k50["eval"]["mean_diff"]))
    print("  r8 - r1:", json.dumps(pair, ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
