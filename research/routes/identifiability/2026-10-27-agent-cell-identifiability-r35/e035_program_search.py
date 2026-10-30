"""E035: program search under equal budget.

Pre-registered in PROTOCOL_E035.md. Searches a 54-program weighted-rank space on splits
1-5 and evaluates the winner on the untouched splits 6-10, against fixed strategies.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r35"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
K = 50
REPEATS = 10
SEARCH_SPLITS = range(0, 5)
EVAL_SPLITS = range(5, 10)
N_BOOT = 1000
SEED = 20261027
A_GRID = (0.5, 1.0)
B_GRID = (0.0, 0.5, 1.0)
C_GRID = (0.0, 0.5, 1.0)
D_GRID = (0.0, 0.5, 1.0)
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
        cell=("CELL_LINE_NAME", "first"), combo=("combo", "first"),
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
    combo_arr = d["combo"].to_numpy()
    tissue_arr = d["tissue"].to_numpy()

    programs = [{"a": a, "b": b, "c": c, "d": dd}
                for a, b, c, dd in itertools.product(A_GRID, B_GRID, C_GRID, D_GRID)]
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
        # static diversity proxies, computed from the pool and the training set only
        combo_counts = pd.Series(combo_arr[pool]).map(pd.Series(combo_arr[pool]).value_counts()).to_numpy(float)
        train_tissue_share = pd.Series(tissue_arr[tr]).value_counts(normalize=True)
        tissue_share = pd.Series(tissue_arr[pool]).map(train_tissue_share).fillna(0.0).to_numpy(float)
        r_pred = pd.Series(pred).rank(pct=True).to_numpy()
        r_var = pd.Series(var).rank(pct=True).to_numpy()
        r_rare = pd.Series(-combo_counts).rank(pct=True).to_numpy()
        r_tiss = pd.Series(-tissue_share).rank(pct=True).to_numpy()
        for pi, p in enumerate(programs):
            score = p["a"] * r_pred + p["b"] * r_var + p["c"] * r_rare + p["d"] * r_tiss
            idx = np.argsort(-score)[:K]
            rows.append({"rep": rep, "program": pi, "a": p["a"], "b": p["b"], "c": p["c"], "d": p["d"],
                         "hit_rate": float(syn[pool][idx].mean())})
        for name, sc in (("exploit", r_pred), ("explore", r_var), ("random", None)):
            idx = rng.permutation(len(pool))[:K] if sc is None else np.argsort(-sc)[:K]
            rows.append({"rep": rep, "program": -1, "a": np.nan, "b": np.nan, "c": np.nan, "d": np.nan,
                         "hit_rate": float(syn[pool][idx].mean()), "fixed": name})

    r = pd.DataFrame(rows)
    fixed = r[r["program"] == -1].copy()
    progs = r[r["program"] >= 0].copy()

    search = progs[progs.rep.isin(list(SEARCH_SPLITS))]
    evals = progs[progs.rep.isin(list(EVAL_SPLITS))]
    per_prog_search = search.groupby("program")["hit_rate"].mean()
    best_prog = int(per_prog_search.idxmax())
    search_range = float(np.quantile(per_prog_search, 0.9) - np.quantile(per_prog_search, 0.1))

    best_row = progs[progs.program == best_prog].iloc[0]
    eval_best = evals[evals.program == best_prog].groupby("rep")["hit_rate"].mean()
    f = fixed[fixed.rep.isin(list(EVAL_SPLITS))]
    eval_exploit = f[f.get("fixed") == "exploit"].groupby("rep")["hit_rate"].mean()
    eval_random = f[f.get("fixed") == "random"].groupby("rep")["hit_rate"].mean()
    eval_explore = f[f.get("fixed") == "explore"].groupby("rep")["hit_rate"].mean()

    def paired(a, b, off):
        j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
        if len(j) < 3:
            return None
        dif = (j["a"] - j["b"]).to_numpy(float)
        rng2 = np.random.default_rng(SEED + off)
        boots = [float(np.mean(rng2.choice(dif, size=len(dif), replace=True))) for _ in range(N_BOOT)]
        return {"n": int(len(dif)), "mean_diff": float(dif.mean()),
                "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
                "a": float(j["a"].mean()), "b": float(j["b"].mean())}

    res = {"kind": "program_search_under_equal_budget",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"lambda": LAMBDA, "k": K, "repeats": REPEATS, "search_splits": list(SEARCH_SPLITS),
                        "eval_splits": list(EVAL_SPLITS), "n_programs": len(programs), "seed": SEED},
           "audit": {"keys": int(len(d)), "synergy_rate": float(syn.mean()),
                     "search_splits": list(SEARCH_SPLITS), "eval_splits": list(EVAL_SPLITS)},
           "search": {"best_program": {"a": float(best_row["a"]), "b": float(best_row["b"]),
                                       "c": float(best_row["c"]), "d": float(best_row["d"])},
                      "best_search_hit_rate": float(per_prog_search.max()),
                      "search_hit_range_p10_p90": search_range,
                      "program_rank_in_eval": None},
           "eval": {"searched_program": paired(eval_best, eval_exploit, 21),
                    "vs_random": paired(eval_best, eval_random, 22),
                    "exploit": float(eval_exploit.mean()), "random": float(eval_random.mean()),
                    "explore": float(eval_explore.mean()),
                    "searched_program_mean": float(eval_best.mean())},
           "files": {}}

    rank_in_eval = progs[progs.rep.isin(list(EVAL_SPLITS))].groupby("program")["hit_rate"].mean()
    res["search"]["program_rank_in_eval"] = int((rank_in_eval > rank_in_eval[best_prog]).sum() + 1)
    res["search"]["n_programs"] = int(len(rank_in_eval))
    res["search"]["eval_best_program"] = int(rank_in_eval.idxmax())
    res["search"]["eval_best_hit"] = float(rank_in_eval.max())

    c1 = res["eval"]["searched_program"]
    c2 = res["eval"]["vs_random"]
    h088 = bool(c1 and c1["ci95"][0] > 0)
    h089 = bool(c2 and c2["ci95"][0] > 0)
    h090 = bool(search_range > 0.02)
    res["decisions"] = {"H088_search_beats_best_fixed": h088, "H089_beats_random": h089,
                        "H090_program_space_has_spread": h090}
    res["decisions"]["verdict"] = ("program_search_adds_value" if h088 else
                                   "fixed_rule_is_enough_no_search_gain")
    res["limits"] = [
        "One-shot program selection, not meta-learning across tasks.",
        "Only four static ranking features and 54 programs; a larger space may behave differently.",
        "The candidate pool's ground truth is already measured (retrospective).",
        "Annotation features only; SYNERGY_DELTA_AUC is a model-fitted quantity.",
        "No mechanistic, clinical or drug-choice claim.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r35/PROTOCOL_E035.md",
                "research/2026-10-27-agent-cell-identifiability-r35/e035_program_search.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E035_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E035_rows.csv", index=False)

    print("keys=%d programs=%d | search splits=%s eval splits=%s" % (
        res["audit"]["keys"], len(programs), list(SEARCH_SPLITS), list(EVAL_SPLITS)))
    print("best searched program:", res["search"]["best_program"],
          "search hit=%.4f" % res["search"]["best_search_hit_rate"],
          "| eval rank %d/%d, eval hit=%.4f" % (res["search"]["program_rank_in_eval"],
                                                res["search"]["n_programs"], res["eval"]["searched_program_mean"]))
    print("eval fixed: exploit=%.4f random=%.4f explore=%.4f" % (
        res["eval"]["exploit"], res["eval"]["random"], res["eval"]["explore"]))
    print("search space spread (p90-p10 of search hit)=%.4f" % search_range)
    print("searched - exploit:", json.dumps(c1, ensure_ascii=False))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
