"""E036: locate and out-of-sample validate the budget boundary where the 50/50 mix
beats pure exploitation.

Pre-registered in PROTOCOL_E036.md. The boundary k* is chosen on splits 1-5 and validated
on splits 6-10.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r36"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
KS = (10, 20, 30, 50, 75, 100, 150, 200, 300)
REPEATS = 10
SEARCH = list(range(0, 5))
EVAL = list(range(5, 10))
N_BOOT = 2000
SEED = 20261027
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME", "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", METRIC, "Synergy"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def paired(a, b, off, seeds=SEED):
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    if len(j) < 3:
        return None
    dif = (j["a"] - j["b"]).to_numpy(float)
    rng = np.random.default_rng(seeds + off)
    boots = [float(np.mean(rng.choice(dif, size=len(dif), replace=True))) for _ in range(N_BOOT)]
    return {"n": int(len(dif)), "mean_diff": float(dif.mean()),
            "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
            "a": float(j["a"].mean()), "b": float(j["b"].mean())}


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
        tr, pool = perm[:ntr], perm[ntr:]
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
            if k >= len(pool) // 4:
                continue
            for name, sc in (("exploit", rp), ("mix", mix), ("explore", rv)):
                idx = np.argsort(-sc)[:k]
                rows.append({"rep": rep, "k": k, "strategy": name,
                             "hit": float(syn[pool][idx].mean())})
            idx = rng.permutation(len(pool))[:k]
            rows.append({"rep": rep, "k": k, "strategy": "random",
                         "hit": float(syn[pool][idx].mean())})

    r = pd.DataFrame(rows)
    res = {"kind": "mix_versus_exploit_budget_boundary",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"lambda": LAMBDA, "ks": list(KS), "repeats": REPEATS,
                        "search_splits": SEARCH, "eval_splits": EVAL, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(d)), "synergy_rate": float(syn.mean()),
                     "ks_evaluated": sorted(int(x) for x in r["k"].unique())},
           "by_k": {}, "files": {}}

    for k in sorted(r["k"].unique()):
        sub = r[r["k"] == k]
        srch = sub[sub.rep.isin(SEARCH)]
        ev = sub[sub.rep.isin(EVAL)]
        ent = {
            "all": {s: float(g["hit"].mean()) for s, g in sub.groupby("strategy")},
            "search_splits_mix_minus_exploit": paired(
                srch[srch.strategy == "mix"].set_index("rep")["hit"],
                srch[srch.strategy == "exploit"].set_index("rep")["hit"], 31),
            "eval_splits_mix_minus_exploit": paired(
                ev[ev.strategy == "mix"].set_index("rep")["hit"],
                ev[ev.strategy == "exploit"].set_index("rep")["hit"], 32),
        }
        res["by_k"][str(int(k))] = ent

    # choose k* on the search splits: smallest k whose search-split CI lower bound > 0
    kstar = None
    for k in sorted(r["k"].unique()):
        c = res["by_k"][str(int(k))]["search_splits_mix_minus_exploit"]
        if c and c["ci95"][0] > 0:
            kstar = int(k)
            break
    res["boundary"] = {"k_star_from_search_splits": kstar}
    if kstar is not None:
        ev = res["by_k"][str(kstar)]["eval_splits_mix_minus_exploit"]
        res["boundary"]["eval_at_k_star"] = ev
        h091 = True
        h092 = bool(ev and ev["ci95"][0] > 0)
        below = [res["by_k"][str(int(k))]["all"]["mix"] - res["by_k"][str(int(k))]["all"]["exploit"]
                 for k in sorted(r["k"].unique()) if int(k) < kstar]
        h093 = bool(all(x <= 0 for x in below)) if below else None
    else:
        h091 = h092 = h093 = False
    res["decisions"] = {"H091_boundary_exists": h091, "H092_boundary_transfers": h092,
                        "H093_exploit_better_below": h093}
    res["decisions"]["verdict"] = ("budget_conditioned_rule_validated" if h092 else
                                   "boundary_not_transferable" if h091 else
                                   "no_usable_boundary")
    res["limits"] = [
        "One task (GDSC one-shot budgeted selection) and one mix weight (50/50).",
        "The candidate pool's ground truth is already measured (retrospective).",
        "Annotation features only; SYNERGY_DELTA_AUC is a model-fitted quantity.",
        "No mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r36/PROTOCOL_E036.md",
                "research/2026-10-27-agent-cell-identifiability-r36/e036_budget_boundary.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E036_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E036_rows.csv", index=False)

    print("keys=%d ks=%s" % (res["audit"]["keys"], res["audit"]["ks_evaluated"]))
    print("  k    exploit    mix    explore  random | search mix-exp        eval mix-exp")
    for k in sorted(r["k"].unique()):
        e = res["by_k"][str(int(k))]
        s = e["search_splits_mix_minus_exploit"]
        v = e["eval_splits_mix_minus_exploit"]
        print("  %-4d %7.4f %6.4f %7.4f %6.4f | %+.4f [%+.3f,%+.3f]   %+.4f [%+.3f,%+.3f]" % (
            k, e["all"]["exploit"], e["all"]["mix"], e["all"]["explore"], e["all"]["random"],
            s["mean_diff"], s["ci95"][0], s["ci95"][1], v["mean_diff"], v["ci95"][0], v["ci95"][1]))
    print("boundary:", json.dumps(res["boundary"], ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
