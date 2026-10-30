"""E053: turn the pool-size finding into a callable predicate and test it honestly.

The threshold is learned on the search half only and evaluated on the held-out half, against
always-exploit, always-mix and random at the same budget. Pre-registered in PROTOCOL_E052.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r53"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
SIZES = (100, 300, 1000, 3000, 10000, 21652)
K = 20
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
            yp = y[pool]
            strong = yp >= np.quantile(yp, 0.90)
            rp = pd.Series(pred).rank(pct=True).to_numpy()
            rv = pd.Series(var).rank(pct=True).to_numpy()
            mix = rp + rv
            e_idx = np.argsort(-rp)[:K]
            m_idx = np.argsort(-mix)[:K]
            rand_idx = rng.choice(len(pool), size=K, replace=False)
            rows.append({"rep": rep, "S": S,
                         "exploit": float(strong[e_idx].mean()),
                         "mix": float(strong[m_idx].mean()),
                         "random": float(strong[rand_idx].mean())})

    r = pd.DataFrame(rows)
    # learn the threshold on the search half only
    srch = r[r.rep.isin(SEARCH)].groupby("S")[["exploit", "mix"]].mean()
    srch["diff"] = srch["mix"] - srch["exploit"]
    positive = [S for S in SIZES if S in srch.index and srch.loc[S, "diff"] > 0]
    s_star = min(positive) if positive else None
    # apply the predicate on the eval half
    ev = r[r.rep.isin(EVAL)].copy()
    if s_star is None:
        ev["predicate"] = ev["exploit"]
    else:
        ev["predicate"] = np.where(ev["S"] > s_star, ev["mix"], ev["exploit"])
    ev["oracle"] = ev[["exploit", "mix"]].max(axis=1)

    per_size = ev.groupby("S")[["exploit", "mix", "random", "predicate", "oracle"]].mean()
    res = {"kind": "callable_pool_size_predicate_versus_baselines",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"sizes": list(SIZES), "k": K, "repeats": REPEATS,
                        "search_halves": "reps 0-19", "eval_halves": "reps 20-39",
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(y)), "threshold_learned_on": "search half only",
                     "S_star": s_star},
           "search_half_by_size": {str(S): {"exploit": float(srch.loc[S, "exploit"]),
                                            "mix": float(srch.loc[S, "mix"]),
                                            "diff": float(srch.loc[S, "diff"])}
                                   for S in SIZES if S in srch.index},
           "eval_by_size": {str(S): {c: float(per_size.loc[S, c]) for c in
                                     ("exploit", "mix", "random", "predicate", "oracle")}
                            for S in SIZES if S in per_size.index},
           "files": {}}

    res["comparisons"] = {
        "predicate_minus_exploit": paired(ev["predicate"], ev["exploit"], 1201),
        "predicate_minus_mix": paired(ev["predicate"], ev["mix"], 1202),
        "predicate_minus_random": paired(ev["predicate"], ev["random"], 1203),
        "predicate_minus_oracle": paired(ev["predicate"], ev["oracle"], 1204),
        "mix_minus_random": paired(ev["mix"], ev["random"], 1205),
    }
    c = res["comparisons"]
    h135 = bool(c["predicate_minus_exploit"]["ci95"][0] > 0)
    h136 = bool(c["predicate_minus_mix"]["ci95"][0] > -0.005)
    h137 = bool(c["predicate_minus_oracle"]["mean_diff"] < 0)
    res["decisions"] = {"H135_predicate_beats_always_exploit": h135,
                        "H136_predicate_not_worse_than_always_mix": h136,
                        "H137_predicate_below_oracle": h137}
    res["decisions"]["verdict"] = ("predicate_has_decision_value" if h135 else
                                   "predicate_has_no_decision_value")
    res["limits"] = [
        "Single dataset; the threshold is chosen from only six candidate pool sizes.",
        "Search and eval halves come from the same distribution and differ only by split.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r53/PROTOCOL_E052.md",
                "research/2026-10-27-agent-cell-identifiability-r53/e053_predicate.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E053_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E053_rows.csv", index=False)

    print("S* learned on search half:", s_star)
    print("search half:")
    for S in SIZES:
        if str(S) in res["search_half_by_size"]:
            x = res["search_half_by_size"][str(S)]
            print("   S=%-6d exploit=%.4f mix=%.4f | diff %+.4f" % (S, x["exploit"], x["mix"], x["diff"]))
    print("eval half:")
    for S in SIZES:
        if str(S) in res["eval_by_size"]:
            x = res["eval_by_size"][str(S)]
            print("   S=%-6d exploit=%.4f mix=%.4f random=%.4f | predicate=%.4f oracle=%.4f" % (
                S, x["exploit"], x["mix"], x["random"], x["predicate"], x["oracle"]))
    for k, v in c.items():
        print("  %-26s %+.4f [%+.4f,%+.4f]" % (k, v["mean_diff"], v["ci95"][0], v["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
