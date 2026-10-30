"""E043: group split by combination, so candidate-pool combinations are absent from training
(at alpha=0) or partly present (0<alpha<1). This finally moves prediction strength into the
low regime and lets the intermediate-band claim be tested.

Pre-registered in PROTOCOL_E043.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r43"
METRIC = "SYNERGY_DELTA_AUC"
LAMBDA = 1.0
KS = (10, 20, 30, 50, 75, 100, 150, 200)
ALPHAS = (1.00, 0.75, 0.50, 0.25, 0.00)
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


def rank_corr(a, b):
    a = pd.Series(a).rank().to_numpy()
    b = pd.Series(b).rank().to_numpy()
    a = a - a.mean()
    b = b - b.mean()
    den = np.sqrt((a ** 2).sum() * (b ** 2).sum())
    return float((a * b).sum() / den) if den > 0 else np.nan


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
        combo=("combo", "first"), ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        tissue=("Tissue", "first"), synergy=(METRIC, "mean"), syn=("syn", "mean"))
    d["syn"] = d["syn"] > 0.5
    for c in ("ap", "lp", "tissue"):
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

    combos = pd.unique(combo)
    rng = np.random.default_rng(SEED)
    pool_target = 21600

    rows = []
    for alpha in ALPHAS:
        for rep in range(REPEATS):
            order = rng.permutation(len(combos))
            n_held = int(0.20 * len(combos))
            held = set(combos[order[:n_held]])
            seen = set(combos[order[n_held:]])
            # keys per combo
            key_combo = combo
            want_from_seen = int(pool_target * alpha)
            want_from_held = pool_target - want_from_seen
            # sample combo groups to reach the target sizes
            seen_list = [c for c in seen]
            held_list = [c for c in held]
            rng.shuffle(seen_list)
            rng.shuffle(held_list)
            pool_combos, n_seen_keys = [], 0
            for c in seen_list:
                if n_seen_keys >= want_from_seen:
                    break
                pool_combos.append(c)
                n_seen_keys += int((combo == c).sum())
            n_held_keys = 0
            for c in held_list:
                if n_held_keys >= want_from_held:
                    break
                pool_combos.append(c)
                n_held_keys += int((combo == c).sum())
            pool_set = set(pool_combos)
            pool_mask = np.array([c in pool_set for c in combo])
            tr = np.where(~pool_mask)[0]
            pool = np.where(pool_mask)[0]
            if len(tr) < 5000 or len(pool) < 2000:
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
            rho = rank_corr(pred, y[pool])
            rp = pd.Series(pred).rank(pct=True).to_numpy()
            rv = pd.Series(var).rank(pct=True).to_numpy()
            mix = rp + rv
            for k in KS:
                for strat, sc in (("exploit", rp), ("mix", mix)):
                    idx = np.argsort(-sc)[:k]
                    rows.append({"alpha": alpha, "rep": rep, "k": k, "strategy": strat,
                                 "hit": float(syn[pool][idx].mean())})
            rows.append({"alpha": alpha, "rep": rep, "k": 0, "strategy": "rho", "hit": float(rho)})

    r = pd.DataFrame(rows)
    res = {"kind": "group_split_by_combination_strength_ladder",
           "input_sha256": {ORIG.name: sha256(ORIG)},
           "settings": {"lambda": LAMBDA, "ks": list(KS), "alphas": list(ALPHAS),
                        "repeats": REPEATS, "pool_target": pool_target, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(d)), "combos": int(len(combos)),
                     "synergy_rate": float(syn.mean()), "features": int(X.shape[1])},
           "by_alpha": {}, "files": {}}

    for alpha in ALPHAS:
        sub_all = r[r.alpha == alpha]
        rhos = sub_all[sub_all.strategy == "rho"]["hit"]
        ent = {"prediction_rho": {"mean": float(rhos.mean()), "median": float(rhos.median())},
               "reps_used": int(rhos.size), "by_k": {}}
        sig = []
        for k in KS:
            sub = sub_all[sub_all.k == k]
            if not len(sub):
                continue
            m = sub[sub.strategy == "mix"].set_index("rep")["hit"]
            e = sub[sub.strategy == "exploit"].set_index("rep")["hit"]
            s = paired(m[m.index.isin(SEARCH)], e[e.index.isin(SEARCH)], 81)
            v = paired(m[m.index.isin(EVAL)], e[e.index.isin(EVAL)], 82)
            ent["by_k"][str(k)] = {"search": s, "eval": v,
                                   "exploit_hit": float(e.mean()), "mix_hit": float(m.mean())}
            if s and v and s["ci95"][0] > 0 and v["ci95"][0] > 0:
                sig.append(k)
        ent["ks_with_both_halves_positive"] = sig
        res["by_alpha"][str(alpha)] = ent

    keys = [str(a) for a in ALPHAS]
    rhos = {k: res["by_alpha"][k]["prediction_rho"]["mean"] for k in keys}
    h112 = bool(all(rhos[keys[i]] >= rhos[keys[i + 1]] - 1e-9 for i in range(len(keys) - 1))
                and (rhos[keys[0]] - rhos[keys[-1]]) > 0.10)
    mid = keys[1:-1]
    mid_any = any(len(res["by_alpha"][k]["ks_with_both_halves_positive"]) > 0 for k in mid)
    strong_any = len(res["by_alpha"][keys[0]]["ks_with_both_halves_positive"]) > 0
    weak_none = len(res["by_alpha"][keys[-1]]["ks_with_both_halves_positive"]) == 0
    h113 = bool(strong_any and mid_any and weak_none)
    weak = res["by_alpha"][keys[-1]]
    h114 = bool(all(abs(weak["by_k"][str(k)]["eval"]["mean_diff"]) < 0.01 for k in KS if str(k) in weak["by_k"]))
    res["decisions"] = {"H112_strength_swept": h112, "H113_lower_boundary_exists": h113,
                        "H114_weak_end_no_difference": h114}
    res["decisions"]["verdict"] = ("intermediate_band_confirmed_with_lower_boundary" if h112 and h113 else
                                   "manipulation_failed_again" if not h112 else
                                   "band_not_confirmed")
    res["limits"] = [
        "Single dataset; alpha also shifts the composition of the pool (seen vs held combinations).",
        "Retrospective candidate pool; SYNERGY_DELTA_AUC is a model-fitted quantity.",
        "No mechanistic, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r43/PROTOCOL_E043.md",
                "research/2026-10-27-agent-cell-identifiability-r43/e043_group_split.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E043_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E043_rows.csv", index=False)

    print("keys=%d combos=%d" % (res["audit"]["keys"], res["audit"]["combos"]))
    for a in ALPHAS:
        e = res["by_alpha"][str(a)]
        print("  alpha=%.2f rho=%.4f reps=%d | ks both-halves-positive: %s" % (
            a, e["prediction_rho"]["mean"], e["reps_used"], e["ks_with_both_halves_positive"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
