"""When to trust the virtual cell: trust scores and selective-prediction scoring (block N).

For each query drug the virtual cell predicts a selective killing profile by transcriptional
transfer (``L``). Its utility is the selective r it achieves. A trust score ranks drugs so that a
user acts on the most trusted predictions first and screens the rest. Scores:

* non-LLM (virtual cell's own evidence): ``top_sim`` (similarity of the nearest transcriptional
  neighbour), ``mean5_sim``, ``moa_agree5`` (share of the top-5 neighbours with the modal class),
  ``l1000_norm`` (largest response norm of the query); ``vc`` = mean rank of top_sim, mean5_sim and
  l1000_norm.
* agent: ``keep`` (number of offered neighbours the agent judges to share the cytotoxic mechanism,
  arm adjudicate_lit), ``kill`` (expected killing: none < weak < selective < broad, from the same
  call), ``kill_prior`` (expected killing from route_lit, which does not see the virtual cell);
  ``agent`` = mean rank of keep and kill.
* combined: ``vc+agent`` = mean of the vc and agent ranks. No weight is fitted.

Scores: Spearman(trust, utility); mean utility of the most-trusted 25% and 50%; the area under the
utility-coverage curve (mean of the mean utilities of the top 10%, 20%, ..., 100%).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.stats import rankdata, spearmanr

KILL = {"none": 0.0, "weak": 1.0, "selective": 2.0, "broad": 3.0}


def rank01(v):
    v = np.asarray(v, float)
    out = np.full(len(v), np.nan)
    ok = np.isfinite(v)
    out[ok] = (rankdata(v[ok]) - 0.5) / ok.sum()
    return np.where(ok, out, 0.5)  # missing evidence gets the median rank


def scores_for(world, i, regime, adjud: dict | None, route: dict | None) -> dict:
    nb = world.neighbours(i, regime)
    sims = np.array([s for _, _, s, _ in nb])
    moas = [m for _, m, _, _ in nb[:5]]
    s = {"top_sim": float(sims[0]) if len(sims) else np.nan, "mean5_sim": float(sims[:5].mean()) if len(sims) else np.nan,
         "moa_agree5": max(moas.count(m) for m in set(moas)) / 5 if moas else np.nan,
         "l1000_norm": float(np.nanmax(np.where(world.l1000_have[i], world.l1000_norm[i], np.nan)))}
    ok_a = adjud is not None and adjud.get("status") == "ok"
    s["keep"] = float(len(adjud["claims"]["keep_neighbours"])) if ok_a else np.nan
    s["kill"] = KILL.get(adjud["claims"]["expected_killing"], np.nan) if ok_a else np.nan
    ok_r = route is not None and route.get("status") == "ok"
    s["kill_prior"] = KILL.get(route["claims"]["expected_killing"], np.nan) if ok_r else np.nan
    return s


def composite(df):
    df = df.copy()
    df["vc"] = np.mean([rank01(df[c]) for c in ("top_sim", "mean5_sim", "l1000_norm")], axis=0)
    df["agent"] = np.mean([rank01(df[c]) for c in ("keep", "kill")], axis=0)
    df["vc+agent"] = (rankdata(df["vc"]) + rankdata(df["agent"])) / 2
    df["vc+kill_prior"] = (rankdata(df["vc"]) + rankdata(rank01(df["kill_prior"]))) / 2
    return df


def coverage_curve(trust, utility, fracs=np.arange(0.1, 1.01, 0.1)):
    order = np.argsort(-np.asarray(trust, float), kind="stable")
    u = np.asarray(utility, float)[order]
    return np.array([u[: max(1, int(round(f * len(u))))].mean() for f in fracs])


def evaluate(trust, utility) -> dict:
    t, u = np.asarray(trust, float), np.asarray(utility, float)
    curve = coverage_curve(t, u)
    return {"spearman": float(spearmanr(t, u).statistic), "top25": float(coverage_curve(t, u, [0.25])[0]),
            "top50": float(coverage_curve(t, u, [0.5])[0]), "aucc": float(curve.mean())}


def bootstrap_diff(df, a, b, clusters, metric="aucc", n_boot=1000, seed=20261011):
    """Cluster bootstrap (mechanism classes) of metric(trust a) - metric(trust b)."""
    keys, inv = np.unique(clusters, return_inverse=True)
    groups = [np.where(inv == k)[0] for k in range(len(keys))]
    rng = np.random.default_rng(seed)
    est = evaluate(df[a], df["utility"])[metric] - evaluate(df[b], df["utility"])[metric]
    draws = []
    for _ in range(n_boot):
        idx = np.concatenate([groups[g] for g in rng.integers(0, len(groups), len(groups))])
        sub = df.iloc[idx]
        draws.append(evaluate(sub[a], sub["utility"])[metric] - evaluate(sub[b], sub["utility"])[metric])
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return [float(est), float(lo), float(hi)]


def load_claims(out_dir: Path, arm: str, regime: str, drug: str, slug) -> dict | None:
    p = out_dir / arm / regime / f"{slug(drug)}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
