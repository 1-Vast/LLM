"""Feasibility F0 (exploratory; exposed GSE92742 x PRISM drugs only; no model calls).

Question: in a campaign that screens new compounds to find ones that selectively kill a target
lineage, is there headroom over simple rules? Does the virtual cell (L1000 transcriptional
transfer) help, and does in-campaign feedback through it add anything?

Units: the 1,403 block-N drugs (all exposed after block N). Each seed splits them into a
reference library (70%, profiles known) and a new-compound pool (30%, profiles hidden). A
campaign is (seed, target lineage). Screening a pool compound reveals its PRISM primary profile.

Selectivity for lineage T: s_T(c) = mean_{l in T} LFC(c, l) - mean_{l not in T} LFC(c, l).
Hit: s_T <= -0.5 and mean_{l in T} LFC <= -0.5 (exploratory definition, checked here).

Kernels: L5 (mean cosine over the 5 phase-2-compatible 24 h options), L18 (all 18 options),
chemistry (Morgan Tanimoto), targets (Hub Jaccard). Prediction: similarity-weighted mean of the
k=5 most similar known compounds' s_T (block N's transfer applied to s_T).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BLOCK_N = ROOT / "research/astra/mechanism_routing_20261011"
sys.path.insert(0, str(BLOCK_N))
import predictors as PR  # noqa: E402

PHASE2_OPTIONS = ["A375|24 h", "HA1E|24 h", "HT29|24 h", "MCF7|24 h", "PC3|24 h"]
MIN_LINES = 20
SEEDS = range(5)
POOL_FRAC = 0.3
BUDGET_FRAC = 0.10
BATCH = 6
K = 5


def l1000_sim(W, opts):
    X = W.Xf[:, opts]                         # (n, o, g)
    have = W.l1000_have[:, opts]
    nrm = np.linalg.norm(X, axis=2)
    Xn = X / np.maximum(nrm, 1e-12)[..., None]
    n = len(X)
    s = np.zeros((n, n), np.float32)
    c = np.zeros((n, n), np.float32)
    for o in range(X.shape[1]):
        m = have[:, o] & (nrm[:, o] > 0)
        so = (Xn[:, o] @ Xn[:, o].T).astype(np.float32)
        mm = np.outer(m, m)
        s += np.where(mm, so, 0)
        c += mm
    with np.errstate(invalid="ignore", divide="ignore"):
        out = np.where(c > 0, s / np.maximum(c, 1), np.nan)
    np.fill_diagonal(out, np.nan)
    return out


def chem_sim(W):
    from rdkit import DataStructs
    n = len(W.drug)
    out = np.full((n, n), np.nan, np.float32)
    fps = W.fps
    ok = [i for i in range(n) if fps[i] is not None]
    okfps = [fps[i] for i in ok]
    for a, i in enumerate(ok):
        out[i, ok] = DataStructs.BulkTanimotoSimilarity(fps[i], okfps)
    np.fill_diagonal(out, np.nan)
    return out


def target_sim(W):
    n = len(W.drug)
    out = np.full((n, n), np.nan, np.float32)
    ts = [set(t) for t in W.targets]
    for i in range(n):
        if not ts[i]:
            continue
        for j in range(n):
            if ts[j]:
                out[i, j] = len(ts[i] & ts[j]) / len(ts[i] | ts[j])
    np.fill_diagonal(out, np.nan)
    return out


def predict(S, known, cand, y, k=K):
    """Similarity-weighted mean of y over the k most similar known compounds (NaN when no similarity)."""
    sub = S[np.ix_(cand, known)]
    out = np.full(len(cand), np.nan)
    top = np.zeros(len(cand))
    for r in range(len(cand)):
        s = sub[r]
        ok = np.isfinite(s)
        if not ok.any():
            continue
        idx = np.argsort(-np.where(ok, s, -np.inf))[:k]
        w = np.clip(s[idx], 0, None)
        vals = y[known[idx]]
        good = np.isfinite(vals)
        if not good.any():
            continue
        w, vals = w[good], vals[good]
        out[r] = float(np.sum(w * vals) / w.sum()) if w.sum() > 0 else float(np.mean(vals))
        top[r] = float(np.nanmax(s))
    return out, top


def run(policy, S, ref, pool, y, hit, budget, rng, moa=None):
    known = list(ref)
    chosen: list[int] = []
    left = list(pool)
    if policy == "random":
        chosen = list(rng.choice(pool, size=budget, replace=False))
    elif policy == "oracle":
        chosen = list(np.array(pool)[np.argsort(y[pool])[:budget]])
    elif policy == "class_mean":
        ref_arr = np.array(ref)
        prior = np.nanmean(y[ref_arr])
        score = []
        for c in pool:
            m = ref_arr[moa[ref_arr] == moa[c]]
            score.append(np.nanmean(y[m]) if len(m) else prior)
        score = np.array(score) + 1e-9 * rng.standard_normal(len(pool))
        chosen = list(np.array(pool)[np.argsort(score)[:budget]])
    elif policy.startswith("static"):
        p, _ = predict(S, np.array(known), np.array(pool), y)
        p = np.where(np.isfinite(p), p, np.nanmean(y[ref])) + 1e-9 * rng.standard_normal(len(pool))
        chosen = list(np.array(pool)[np.argsort(p)[:budget]])
    elif policy.startswith("adapt"):
        while len(chosen) < budget:
            cand = np.array(left)
            p, _ = predict(S, np.array(known), cand, y)
            p = np.where(np.isfinite(p), p, np.nanmean(y[known])) + 1e-9 * rng.standard_normal(len(cand))
            take = cand[np.argsort(p)[: min(BATCH, budget - len(chosen))]]
            for c in take:
                chosen.append(int(c))
                left.remove(int(c))
                known.append(int(c))
    return int(hit[chosen].sum())


def main():
    t0 = time.time()
    W = PR.load_world("sealed")
    info = pd.read_csv(ROOT / "data/external/prism_19q4/raw/primary-screen-cell-line-info.csv").set_index("row_name")
    tissue = np.array([info.at[l, "primary_tissue"] if l in info.index else "na" for l in W.lines])
    lineages = [t for t, n in pd.Series(tissue).value_counts().items() if n >= MIN_LINES and t != "na"]
    opts = [list(W.options).index(o) for o in PHASE2_OPTIONS]
    kern = {"L5": l1000_sim(W, opts), "L18": l1000_sim(W, list(range(len(W.options)))),
            "chem": chem_sim(W), "target": target_sim(W)}
    print("kernels", round(time.time() - t0, 1), "s", flush=True)
    P = W.P.astype(float)
    S2 = W.S2.astype(float)
    desc = {}
    stats = {}
    for T in lineages:
        inT = tissue == T
        s = np.nanmean(P[:, inT], 1) - np.nanmean(P[:, ~inT], 1)
        mT = np.nanmean(P[:, inT], 1)
        hit = (s <= -0.5) & (mT <= -0.5)
        s2 = np.nanmean(S2[:, inT], 1) - np.nanmean(S2[:, ~inT], 1)
        has2 = np.isfinite(s2)
        rep = float(np.mean(s2[hit & has2] <= -0.25)) if (hit & has2).sum() else np.nan
        rep0 = float(np.mean(s2[~hit & has2] <= -0.25)) if (~hit & has2).sum() else np.nan
        desc[T] = {"n_lines": int(inT.sum()), "n_hits": int(hit.sum()), "hit_rate": round(float(hit.mean()), 4),
                   "n_hits_with_secondary": int((hit & has2).sum()), "secondary_rep_hits": rep, "secondary_rep_nonhits": rep0,
                   "corr_primary_secondary_s": float(np.corrcoef(s[has2], s2[has2])[0, 1]) if has2.sum() > 10 else None}
        stats[T] = (s, hit)
    print(json.dumps(desc, indent=1), flush=True)
    policies = ["random", "class_mean", "static_L5", "adapt_L5", "static_L18", "adapt_L18", "static_chem", "adapt_chem",
                "static_target", "adapt_target", "oracle"]
    rows = []
    n = len(W.drug)
    for seed in SEEDS:
        rng = np.random.default_rng(20261011 + seed)
        perm = rng.permutation(n)
        pool = list(perm[: int(POOL_FRAC * n)])
        ref = list(perm[int(POOL_FRAC * n):])
        budget = int(round(BUDGET_FRAC * len(pool)))
        for T in lineages:
            s, hit = stats[T]
            npool = int(hit[pool].sum())
            if npool == 0:
                continue
            row = {"seed": seed, "T": T, "pool_hits": npool, "budget": budget}
            for pol in policies:
                S = kern.get(pol.split("_")[-1]) if "_" in pol and pol != "class_mean" else None
                row[pol] = run(pol, S, ref, pool, s, hit, budget, np.random.default_rng(seed), moa=W.moa)
            rows.append(row)
        print("seed", seed, round(time.time() - t0, 1), flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(HERE / "f0_rows.csv", index=False)
    tot = {p: int(df[p].sum()) for p in policies}
    tot["pool_hits"] = int(df.pool_hits.sum())
    cap = int(np.minimum(df.pool_hits, df.budget).sum())
    tot["capacity"] = cap
    print(json.dumps(tot, indent=1))
    # interaction: feedback gain under VC vs under chemistry, campaign-level bootstrap by (seed, T) cluster on T
    def boot(diff, groups, B=4000, rng=np.random.default_rng(7)):
        g = np.unique(groups)
        est = []
        for _ in range(B):
            pick = rng.choice(g, size=len(g), replace=True)
            est.append(np.sum([diff[groups == x].sum() for x in pick]))
        return float(np.sum(diff)), [float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))]
    contrasts = {
        "VC_static_vs_chem_static": df.static_L5 - df.static_chem,
        "VC_static_vs_class_mean": df.static_L5 - df.class_mean,
        "VC_static_vs_random": df.static_L5 - df.random,
        "feedback_VC": df.adapt_L5 - df.static_L5,
        "feedback_chem": df.adapt_chem - df.static_chem,
        "feedback_target": df.adapt_target - df.static_target,
        "interaction_VCxfeedback_vs_chem": (df.adapt_L5 - df.static_L5) - (df.adapt_chem - df.static_chem),
        "L18_vs_L5_static": df.static_L18 - df.static_L5,
    }
    out = {"descriptive": desc, "totals": tot, "contrasts": {}}
    for k, v in contrasts.items():
        out["contrasts"][k] = boot(v.to_numpy(float), df["T"].to_numpy())
        print(k, out["contrasts"][k])
    out["seconds"] = round(time.time() - t0, 1)
    (HERE / "f0_headroom.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
