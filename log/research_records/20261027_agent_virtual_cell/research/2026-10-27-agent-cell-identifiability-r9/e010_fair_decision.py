"""E010: fair decision-AL test with a heteroscedastic prior and a precision-weighted update.

Pre-registered in PROTOCOL_E010.md. Reads only PAIR_SCREEN.csv.

Fixes the three defects that invalidated R8:
  (i)  per-unit prior sd  ->  VOI no longer collapses into exploitation;
  (ii) precision-weighted posterior update instead of replacing the prior with a noisy
       single-cell measurement, so buying cannot reduce precision;
  (iii) the implementation check H016 (regret non-increasing in k for exploitation).
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
CSV = ROOT / "research" / "eight_directions_20261026" / "evidence_audit" / "raw" / "PAIR_SCREEN.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r9"
ANCHORS = {"high control", "low control"}
FLOOR = 0.10
K_GRID = (1, 2, 4, 8)
SIGMA_MEAS = 0.028
SIGMA_FLOOR = 0.01
N_RANDOM = 20
N_BOOT = 1000
PAIRS_SAMPLE = 400
W_INSTAB = 0.5
SEED = 20261027
SHA = "56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def zs(x):
    s = np.nanstd(x)
    return (x - np.nanmean(x)) / (s if s > 1e-9 else 1.0)


def normal_pdf(x):
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


def normal_cdf(x):
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def build():
    df = pd.read_csv(CSV, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={df.columns[0]: "row_id"})
    for c in ("Drug 1", "Drug 2", "Cell line", "file", "Well"):
        df[c] = df[c].astype(str).str.strip()
    df["iteration"] = pd.to_numeric(df["Iteration"], errors="coerce")
    df["failed_qc"] = df["Failed QC"].astype(str).str.strip().str.lower().isin(["true", "1"])
    df["y"] = pd.to_numeric(df["Viability"], errors="coerce")
    df["anchor"] = df["Drug 1"].isin(ANCHORS) | df["Drug 2"].isin(ANCHORS)
    df["dmso"] = (df["Drug 1"].str.lower() == "dmso") | (df["Drug 2"].str.lower() == "dmso")
    meta = {}
    for fname, g in df[~df["anchor"]].groupby("file", sort=True):
        layout = tuple(sorted(zip(g["Well"], g["Drug 1"], pd.to_numeric(g["Conc 1 (uM)"]).round(9),
                                  g["Drug 2"], pd.to_numeric(g["Conc 2 (uM)"]).round(9))))
        meta[fname] = {"cell": g["Cell line"].iloc[0],
                       "iteration": int(g["iteration"].iloc[0]) if pd.notna(g["iteration"].iloc[0]) else -1,
                       "h": hashlib.sha1(repr(layout).encode()).hexdigest(),
                       "combo": {w: (str(d1).lower() != "dmso" and str(d2).lower() != "dmso")
                                 for w, (d1, c1, d2, c2) in
                                 {w: (d1, c1, d2, c2) for w, d1, c1, d2, c2 in layout}.items()},
                       "qc": float(g["failed_qc"].mean())}

    def vec(fname, units):
        sub = df[(df["file"] == fname) & (~df["failed_qc"]) & df["y"].notna() & (~df["anchor"])]
        return sub.drop_duplicates("Well").set_index("Well")["y"].reindex(units).to_numpy(dtype=float)

    groups = {}
    for f, s in meta.items():
        groups.setdefault((s["iteration"], s["h"]), {}).setdefault(s["cell"], []).append(f)
    rng = np.random.default_rng(SEED)
    layouts = []
    for (it, h), cells in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        good = [c for c in sorted(cells) if max(meta[f]["qc"] for f in cells[c]) <= 0.20]
        if len(good) < 4:
            continue
        first = cells[good[0]][0]
        units = [u for u in sorted(meta[first]["combo"]) if meta[first]["combo"][u]]
        V = {c: [vec(f, units) for f in cells[c]] for c in good}
        Y = {c: np.nanmean(np.vstack(V[c]), axis=0) for c in good}
        nu = len(units)
        iu, ju = np.triu_indices(nu, 1)
        sel = rng.choice(iu.size, min(PAIRS_SAMPLE, iu.size), replace=False)
        layouts.append({"iteration": it, "hash": h[:12], "cells": good, "units": units,
                        "Y": Y, "iu": iu[sel], "ju": ju[sel]})
    return df, layouts


def instability(M, iu, ju, nu):
    Mo = M[:, iu] - M[:, ju]
    gapo = np.abs(Mo)
    sgn = np.sign(Mo)
    oko = np.isfinite(gapo) & (gapo >= FLOOR)
    pair_rev = np.zeros(iu.size)
    pair_obs = np.zeros(iu.size)
    for a in range(M.shape[0]):
        for b in range(a + 1, M.shape[0]):
            m = oko[a] & oko[b]
            if m.sum() == 0:
                continue
            pair_rev[m] += (sgn[a, m] != sgn[b, m])
            pair_obs[m] += 1
    with np.errstate(invalid="ignore", divide="ignore"):
        prate = np.where(pair_obs > 0, pair_rev / np.maximum(pair_obs, 1), np.nan)
    inst = np.zeros(nu)
    for p in range(iu.size):
        if np.isfinite(prate[p]):
            inst[iu[p]] += prate[p]
            inst[ju[p]] += prate[p]
    wcount = np.bincount(np.concatenate([iu, ju]), minlength=nu).astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(wcount > 0, inst / np.maximum(wcount, 1), 0.0)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256(CSV) == SHA
    df, layouts = build()
    rng = np.random.default_rng(SEED + 5)

    rows = []
    for L in layouts:
        cells, nu = L["cells"], len(L["units"])
        lay = "%s/%s" % (L["iteration"], L["hash"])
        for c in cells:
            others = [x for x in cells if x != c]
            if len(others) < 3:
                continue
            Yc = L["Y"][c]
            M = np.vstack([L["Y"][x] for x in others])
            n_u = np.sum(np.isfinite(M), axis=0)
            with np.errstate(invalid="ignore"):
                p = np.nanmean(M, axis=0)
                s_u = np.nanstd(M, axis=0, ddof=1)
            pooled = float(np.nanmedian(s_u[np.isfinite(s_u)]))
            s_u = np.where(np.isfinite(s_u) & (n_u >= 3), s_u, pooled)
            # predictive variance for a NEW cell: cross-cell variance plus the uncertainty
            # of the mean. Using s/sqrt(n) alone would be the standard error of the mean and
            # would make the prior far more precise than it can be for a held-out cell.
            sig_prior = np.maximum(np.sqrt(s_u ** 2 * (1.0 + 1.0 / np.maximum(n_u, 1))), SIGMA_FLOOR)
            inst = instability(M, L["iu"], L["ju"], nu)

            valid = np.isfinite(p) & np.isfinite(Yc)
            if valid.sum() < 20:
                continue
            idx = np.where(valid)[0]
            p, truth = p[idx], Yc[idx]
            sig_prior, inst_v = sig_prior[idx], inst[idx]
            n = idx.size
            best_true = float(np.min(truth))
            rank_true = np.argsort(np.argsort(truth))
            prec_prior = 1.0 / sig_prior ** 2
            prec_meas = 1.0 / SIGMA_MEAS ** 2
            w = prec_prior / (prec_prior + prec_meas)
            s_ei = (1.0 - w) * SIGMA_MEAS

            def posterior(mu, var, bought):
                mu = mu.copy()
                var = var.copy()
                for j in bought:
                    mu[j] = (mu[j] * prec_prior[j] + truth[j] * prec_meas) / (prec_prior[j] + prec_meas)
                    var[j] = 1.0 / (prec_prior[j] + prec_meas)
                return mu, var

            def decide(mu, var, draws=200):
                """Bayes decision under 0-1 loss: pick the arm with the highest P(it is best).
                With heterogeneous posterior variances, argmin of the posterior mean is NOT the
                Bayes rule: it rewards high-variance unmeasured arms and penalises precisely
                measured ones."""
                sd = np.sqrt(np.maximum(var, 1e-12))
                z = rng.normal(size=(draws, mu.size))
                samp = mu[None, :] + z * sd[None, :]
                winners = np.argmin(samp, axis=1)
                counts = np.bincount(winners, minlength=mu.size)
                return int(np.argmax(counts)), counts / draws

            def ei_scores(mu, var):
                out = np.empty(n)
                for j in range(n):
                    m_other = np.min(np.delete(mu, j)) if n > 1 else np.inf
                    z = (m_other - p[j]) / max(s_ei[j], 1e-6)
                    out[j] = (m_other - p[j]) * normal_cdf(z) + s_ei[j] * normal_pdf(z)
                return out

            for k in K_GRID:
                if k >= n:
                    continue
                # greedy EI batch
                bought, mu_g, var_g = [], p.copy(), sig_prior ** 2
                while len(bought) < k:
                    sc = ei_scores(mu_g, var_g)
                    if bought:
                        sc[bought] = -np.inf
                    j = int(np.argmax(sc))
                    bought.append(j)
                    mu_g[j] = p[j]
                    var_g[j] = 1.0 / (prec_prior[j] + prec_meas)
                arms = {
                    "none": [],
                    "exploit": list(np.argsort(p)[:k]),
                    "uncertain": list(np.argsort(-sig_prior)[:k]),
                    "instab": list(np.argsort(-inst_v)[:k]),
                    "ei": bought,
                }
                combo = zs(-p) + W_INSTAB * zs(inst_v)
                arms["instab_ei"] = list(np.argsort(-combo)[:k])
                for name, sel in arms.items():
                    mu, va = posterior(p.copy(), sig_prior ** 2, sel)
                    ch, pbest = decide(mu, va)
                    top3 = list(np.argsort(-pbest)[:3])
                    rows.append({"layout": lay, "cell": c, "k": k, "strategy": name,
                                 "hit_top1": int(rank_true[ch] < 3),
                                 "regret": float(truth[ch] - best_true),
                                 "top3_utility": float(np.mean(truth[top3])), "n_units": int(n)})
                hits, regs, t3 = [], [], []
                for _ in range(N_RANDOM):
                    sel = list(rng.choice(n, k, replace=False))
                    mu, va = posterior(p.copy(), sig_prior ** 2, sel)
                    ch, pbest = decide(mu, va)
                    hits.append(int(rank_true[ch] < 3))
                    regs.append(float(truth[ch] - best_true))
                    t3.append(float(np.mean(truth[np.argsort(-pbest)[:3]])))
                rows.append({"layout": lay, "cell": c, "k": k, "strategy": "random",
                             "hit_top1": float(np.mean(hits)), "regret": float(np.mean(regs)),
                             "top3_utility": float(np.mean(t3)), "n_units": int(n)})

    r = pd.DataFrame(rows)
    res = {"kind": "fair_decision_al_test_bayes_decision_rule",
           "input_sha256": sha256(CSV),
           "settings": {"k_grid": list(K_GRID), "sigma_meas": SIGMA_MEAS, "sigma_floor": SIGMA_FLOOR,
                        "n_random": N_RANDOM, "n_boot": N_BOOT, "w_instab": W_INSTAB, "seed": SEED},
           "audit": {"layouts_used": int(r["layout"].nunique()),
                     "heldout_cells": int(r.groupby(["layout", "cell"]).ngroups),
                     "observations": int(len(r))},
           "by_k": {}, "paired": {}, "files": {}}
    for k in K_GRID:
        sub = r[r["k"] == k]
        if sub.empty:
            continue
        res["by_k"][str(k)] = {
            s: {"n_cells": int(len(d)), "hit_top1": float(d["hit_top1"].mean()),
                "regret_mean": float(d["regret"].mean()), "regret_median": float(d["regret"].median()),
                "top3_utility_mean": float(d["top3_utility"].mean())}
            for s, d in sub.groupby("strategy")}

    def paired(k, a, b, metric):
        sa = r[(r["k"] == k) & (r["strategy"] == a)][["layout", "cell", metric]]
        sb = r[(r["k"] == k) & (r["strategy"] == b)][["layout", "cell", metric]]
        m = sa.merge(sb, on=["layout", "cell"], suffixes=("_a", "_b"))
        if m.empty:
            return None
        m["d"] = m[metric + "_a"] - m[metric + "_b"]
        lays = sorted(m["layout"].unique())
        rng2 = np.random.default_rng(SEED + 3)
        boots = []
        for _ in range(N_BOOT):
            pick = rng2.choice(lays, size=len(lays), replace=True)
            sel = pd.concat([m[m["layout"] == q] for q in pick])
            if len(sel):
                boots.append(float(sel["d"].mean()))
        return {"n": int(len(m)), "mean_diff": float(m["d"].mean()),
                "ci95_layout_clustered": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))] if boots else None,
                "frac_better_than_baseline": float((m["d"] < 0).mean()) if metric == "regret" else float((m["d"] > 0).mean())}

    for k in K_GRID:
        blk = {}
        for a in ("ei", "instab", "instab_ei", "uncertain", "random"):
            blk[a + "_vs_exploit_regret"] = paired(k, a, "exploit", "regret")
            blk[a + "_vs_exploit_hit"] = paired(k, a, "exploit", "hit_top1")
        res["paired"][str(k)] = blk

    def meets(k, a):
        d = res["paired"].get(str(k), {}).get(a + "_vs_exploit_regret")
        return bool(d and d["mean_diff"] <= -0.02 and d["ci95_layout_clustered"] and d["ci95_layout_clustered"][1] < 0)

    h014 = any(meets(k, "ei") for k in K_GRID)
    h015 = all(((res["paired"].get(str(k), {}).get("instab_vs_exploit_regret") or {}).get("mean_diff", 0) > -0.02)
               for k in K_GRID if str(k) in res["by_k"])
    exploit_regrets = [res["by_k"][str(k)]["exploit"]["regret_mean"] for k in K_GRID if str(k) in res["by_k"]]
    h016 = all(exploit_regrets[i + 1] <= exploit_regrets[i] + 1e-9 for i in range(len(exploit_regrets) - 1))
    ei_gaps = [res["paired"][str(k)]["ei_vs_exploit_regret"]["mean_diff"] for k in K_GRID if str(k) in res["by_k"]]
    res["decisions"] = {
        "H014_ei_beats_exploit": h014,
        "H015_instability_still_has_no_positive_value": h015,
        "H016_implementation_check_regret_nonincreasing": h016,
        "ei_gap_by_k": ei_gaps,
        "indistinguishable_from_exploit": bool(all(abs(g) < 0.005 for g in ei_gaps)),
        "verdict": ("ei_has_independent_value" if h014 else
                    "no_strategy_separable_from_exploitation"),
    }
    res["limits"] = [
        "One layout batch; cross-batch transfer impossible here (see R7 challenge).",
        "Exploratory: plates already used as scoring endpoints and cross-cell comparisons cross days.",
        "A GP over units is not identifiable (no metric on units); a hierarchical empirical-Bayes prior plays that role instead.",
        "sigma_meas is a constant taken from replicate noise, not estimated per unit.",
        "Functional viability only; no mechanism, target engagement, selectivity or clinical claim.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r9/PROTOCOL_E010.md",
                "research/2026-10-27-agent-cell-identifiability-r9/e010_fair_decision.py",
                str(CSV.relative_to(ROOT))):
        p_ = ROOT / rel
        if p_.exists():
            res["files"][rel] = sha256(p_)
    (OUT / "E010_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    r.to_csv(OUT / "E010_per_cell.csv", index=False)

    print("layouts=%d cells=%d obs=%d" % (res["audit"]["layouts_used"], res["audit"]["heldout_cells"], res["audit"]["observations"]))
    for k in K_GRID:
        if str(k) not in res["by_k"]:
            continue
        print("k=%d" % k)
        for s, v in sorted(res["by_k"][str(k)].items(), key=lambda kv: kv[1]["regret_mean"]):
            print("   %-12s hit=%.3f regret=%.4f top3=%.4f" % (s, v["hit_top1"], v["regret_mean"], v["top3_utility_mean"]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
