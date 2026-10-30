"""E034: sequential active learning on GDSC - does feedback between batches improve selection?

Pre-registered in PROTOCOL_E034.md. Reads only the local Jaaks 2022 GDSC file.

Each round selects k=50 keys from a held-out candidate pool, reveals their true synergy,
merges them into the training set, refits the ridge, and selects again. Four strategies are
run independently over 5 rounds and 10 random splits.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r34"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
K = 50
ROUNDS = 5
REPEATS = 10
N_BOOT = 1000
SEED = 20261027
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", METRIC, "Synergy"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


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
    for c in ("ap", "lp", "tissue"):
        d[c] = d[c].astype(str).fillna("NA")

    pa, pl, ti = sorted(d.ap.unique()), sorted(d.lp.unique()), sorted(d.tissue.unique())
    X = np.zeros((len(d), len(pa) + len(pl) + len(ti)))
    for k, v in enumerate(pa):
        X[:, k] = (d.ap == v).to_numpy(float)
    o = len(pa)
    for k, v in enumerate(pl):
        X[:, o + k] = (d.lp == v).to_numpy(float)
    o2 = o + len(pl)
    for k, v in enumerate(ti):
        X[:, o2 + k] = (d.tissue == v).to_numpy(float)
    y = d.synergy.to_numpy(float)
    syn = d.syn.to_numpy(bool)

    rng = np.random.default_rng(SEED)
    rows = []
    for rep in range(REPEATS):
        n = len(d)
        perm = rng.permutation(n)
        ntr = int(0.8 * n)
        tr0, pool0 = perm[:ntr], perm[ntr:]
        for strat in ("random", "exploit", "explore", "mix"):
            tr = list(tr0)
            pool = list(pool0)
            for rnd in range(1, ROUNDS + 1):
                Xtr = X[tr]
                ytr = y[tr]
                mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
                sd[sd == 0] = 1.0
                Xs = (Xtr - mu) / sd
                A = Xs.T @ Xs + LAMBDA * np.eye(Xs.shape[1])
                Ainv = np.linalg.inv(A)
                w = Ainv @ Xs.T @ (ytr - ytr.mean())
                Xp = (X[pool] - mu) / sd
                pred = ytr.mean() + Xp @ w
                var = np.einsum("ij,jk,ik->i", Xp, Ainv, Xp)
                if strat == "random":
                    idx = rng.permutation(len(pool))[:K]
                elif strat == "exploit":
                    idx = np.argsort(-pred)[:K]
                elif strat == "explore":
                    idx = np.argsort(-var)[:K]
                else:
                    idx = np.argsort(-(pd.Series(pred).rank(pct=True).to_numpy()
                                       + pd.Series(var).rank(pct=True).to_numpy()))[:K]
                sel = [pool[i] for i in idx]
                hits = float(syn[sel].mean())
                best = float(y[sel].max())
                rows.append({"rep": rep, "strategy": strat, "round": rnd, "k": K,
                             "hit_rate": hits, "best": best,
                             "pool_syn_rate": float(syn[pool].mean())})
                tr = tr + sel
                sel_set = set(sel)
                pool = [p for p in pool if p not in sel_set]

    r = pd.DataFrame(rows)
    res = {"kind": "sequential_active_learning_on_gdsc",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"lambda": LAMBDA, "k": K, "rounds": ROUNDS, "repeats": REPEATS,
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(d)), "synergy_rate": float(syn.mean()),
                     "pool_size": int(len(d) - int(0.8 * len(d))), "repeats": REPEATS},
           "by_round": {}, "cumulative": {}, "files": {}}

    def paired(a, b, metric, by="rep"):
        A = a.groupby(by)[metric].mean()
        B = b.groupby(by)[metric].mean()
        j = pd.concat([A.rename("a"), B.rename("b")], axis=1).dropna()
        if len(j) < 3:
            return None
        dif = (j["a"] - j["b"]).to_numpy(float)
        rng2 = np.random.default_rng(SEED + 11)
        boots = [float(np.mean(rng2.choice(dif, size=len(dif), replace=True))) for _ in range(N_BOOT)]
        return {"n": int(len(dif)), "mean_diff": float(dif.mean()),
                "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
                "a": float(j["a"].mean()), "b": float(j["b"].mean())}

    for rnd in range(1, ROUNDS + 1):
        sub = r[r["round"] == rnd]
        res["by_round"][str(rnd)] = {
            "hit_rate": {s: float(g["hit_rate"].mean()) for s, g in sub.groupby("strategy")},
            "best": {s: float(g["best"].mean()) for s, g in sub.groupby("strategy")},
            "pool_syn_rate": float(sub["pool_syn_rate"].mean()),
            "mix_minus_exploit": paired(sub[sub.strategy == "mix"], sub[sub.strategy == "exploit"], "hit_rate"),
            "explore_minus_exploit": paired(sub[sub.strategy == "explore"], sub[sub.strategy == "exploit"], "hit_rate"),
        }
    # cumulative over rounds
    cum = r.groupby(["rep", "strategy"]).agg(hit_rate=("hit_rate", "mean")).reset_index()
    res["cumulative"] = {s: float(g["hit_rate"].mean()) for s, g in cum.groupby("strategy")}
    res["cumulative"]["mix_minus_exploit"] = paired(cum[cum.strategy == "mix"], cum[cum.strategy == "exploit"], "hit_rate")
    res["cumulative"]["explore_minus_exploit"] = paired(cum[cum.strategy == "explore"], cum[cum.strategy == "exploit"], "hit_rate")
    res["cumulative"]["exploit_minus_random"] = paired(cum[cum.strategy == "exploit"], cum[cum.strategy == "random"], "hit_rate")

    e = r[r.strategy == "exploit"]
    first = e[e["round"] == 1].groupby("rep")["hit_rate"].mean()
    last = e[e["round"] == ROUNDS].groupby("rep")["hit_rate"].mean()
    j = pd.concat([last.rename("last"), first.rename("first")], axis=1).dropna()
    dif = (j["last"] - j["first"]).to_numpy(float)
    rng3 = np.random.default_rng(SEED + 12)
    boots = [float(np.mean(rng3.choice(dif, size=len(dif), replace=True))) for _ in range(N_BOOT)] if len(dif) else []
    res["feedback_gain"] = {"n": int(len(dif)), "mean": float(dif.mean()) if len(dif) else None,
                            "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))] if boots else None,
                            "first_round": float(j["first"].mean()) if len(j) else None,
                            "last_round": float(j["last"].mean()) if len(j) else None}

    h085 = bool(res["feedback_gain"]["ci95"] and res["feedback_gain"]["ci95"][0] > 0)
    best_explore = min(
        [v for s in ("explore", "mix") for k2, v in [(s, res["cumulative"][s])]],
        key=lambda x: x)  # lowest; replaced below
    cm = res["cumulative"]
    h086 = bool((cm["mix_minus_exploit"] and cm["mix_minus_exploit"]["ci95"][0] > 0)
                or (cm["explore_minus_exploit"] and cm["explore_minus_exploit"]["ci95"][0] > 0))
    g1 = res["by_round"]["1"].get("mix_minus_exploit")
    g5 = res["by_round"][str(ROUNDS)].get("mix_minus_exploit")
    h087 = bool(g1 and g5 and g5["mean_diff"] > g1["mean_diff"])
    res["decisions"] = {"H085_feedback_improves_exploit": h085,
                        "H086_exploration_valuable_sequentially": h086,
                        "H087_gap_widens_with_rounds": h087}
    res["decisions"]["verdict"] = ("sequential_exploration_has_value" if h086 else
                                   "sequential_feedback_does_not_change_the_answer")
    res["limits"] = [
        "The candidate pool's ground truth is already measured (retrospective reveal), not newly generated.",
        "Only k=50 and five rounds; other budgets untested.",
        "Features are pathway/tissue annotation only; SYNERGY_DELTA_AUC is a model-fitted quantity.",
        "No mechanistic, clinical or drug-choice claim.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r34/PROTOCOL_E034.md",
                "research/2026-10-27-agent-cell-identifiability-r34/e034_sequential_al.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E034_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E034_rows.csv", index=False)

    print("keys=%d pool=%d synergy rate=%.4f | k=%d rounds=%d" % (
        res["audit"]["keys"], res["audit"]["pool_size"], res["audit"]["synergy_rate"], K, ROUNDS))
    for rnd, v in res["by_round"].items():
        print("  round %s pool=%.4f | %s" % (rnd, v["pool_syn_rate"],
              " ".join("%s=%.4f" % (s, x) for s, x in v["hit_rate"].items())))
    print("  cumulative:", {s: round(x, 4) for s, x in cm.items() if isinstance(x, float)})
    print("  feedback gain (exploit last-first):", json.dumps(res["feedback_gain"], ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
