"""Bounded diagnostic: does untreated baseline expression add decision value on O'Neil?

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws2_predecision_state/state_diagnostic.py
- Purpose: the state gate failed (one DepMap profile per line, so state is confounded with line
  identity; public availability postdates both screens). Per the spec, only a BOUNDED diagnostic
  is run, on O'Neil (development, exposed). Baseline expression is used to weight history lines
  (line similarity) in the frozen world model's prior, and is compared with controls that keep
  everything else identical.
- Core points:
  - Lines: O'Neil lines with an EXACT/ALIAS DepMap match and an expression row (35; OCUBM has
    no expression row; COLO320DM sibling, EFM192B and UWB1289BRCA1 unmapped). The library is
    restricted to these lines for every arm, so comparisons are matched.
  - Inputs held fixed: history features H (pair mean, drug means in other lines), identity drug
    kernel, in-context feedback. The varied input is only the line similarity that weights
    history in three similarity features S (cols 3-5):
      base     : H only (no state)
      expr     : S from expression similarity (RBF on z-scored top-2,000-variance genes)
      expr_shuf: the same, profiles permuted among lines WITHIN tissue (20 seeds): background-
                 conditional state shuffle
      tissue   : S from same-tissue indicator (background / identity proxy)
      mono     : S from single-agent profile similarity (the registered functional context)
      knn_expr : simple predictor with identical inputs: similarity-weighted pair mean (no ridge,
                 no feedback), the static retrieval analogue of `history`
  - Endpoints per target line: prior Spearman; hits in the prior's top 10% (static selection);
    wm_static and wm_full campaign hits (registered spec); action contrasts against base:
    top-budget set changes (hits entering minus hits leaving) and concordance on candidate pairs
    the two rankings order differently. Bootstrap over target lines.
- Interfaces: `python state_diagnostic.py` -> outputs/state_diagnostic.json
- Depends on: numpy, pandas, scipy; common.py; outputs/depmap_mapping.csv.
"""
from __future__ import annotations

import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from scipy import stats

from common import (ONEIL, OUT, ROOT, MaskedWorld, WorldConfig, _rbf_similarity, _zscore_columns, bootstrap_ci,
                    columns_for, load, prior_metrics, run_arm, sha256_file, write_json)

DEPMAP = ROOT / "data/raw/depmap"
N_GENES = 2000
SHUFFLE_SEEDS = 20
PAIR_SAMPLE = 20000

_STATE: dict = {}


def build_state():
    lib = load(ONEIL)
    mapping = pd.read_csv(OUT / "depmap_mapping.csv")
    m = mapping[(mapping.screen == "oneil") & mapping.match_class.isin(["EXACT", "ALIAS"]) & mapping.expression]
    ids = dict(zip(m.screen_line, m.depmap_model_id))
    tissue = dict(zip(mapping[mapping.screen == "oneil"].screen_line, mapping[mapping.screen == "oneil"].screen_tissue))
    expr = pd.read_csv(DEPMAP / "OmicsExpressionProteinCodingGenesTPMLogp1.csv", index_col=0)
    lines = [l for l in lib.lines if l in ids]
    X = expr.loc[[ids[l] for l in lines]].to_numpy(float)
    keep = X.mean(axis=0) > 1.0
    X = X[:, keep]
    top = np.argsort(-X.var(axis=0))[:N_GENES]
    Z = _zscore_columns(X[:, top])
    n_lines = len(lib.lines)
    pos = {l: lib.lines.index(l) for l in lines}

    def embed(sim_small):
        full = np.zeros((n_lines, n_lines))
        idx = [pos[l] for l in lines]
        full[np.ix_(idx, idx)] = sim_small
        np.fill_diagonal(full, 0.0)
        return full

    sims = {"expr": embed(_rbf_similarity(Z))}
    t = np.array([tissue[l] for l in lines])
    sims["tissue"] = embed((t[:, None] == t[None, :]).astype(float))
    shuffled = []
    for seed in range(SHUFFLE_SEEDS):
        rng = np.random.default_rng([20261003, seed])
        perm = np.arange(len(lines))
        for group in np.unique(t):
            members = np.flatnonzero(t == group)
            perm[members] = members[rng.permutation(members.size)]
        shuffled.append(embed(_rbf_similarity(Z[perm])))
    mask = np.isin(lib.c, [pos[l] for l in lines])
    sub = lib.subset(mask, "oneil_depmap_expr")
    # how much of expression similarity is tissue? (correlation of off-diagonal entries)
    small_expr = _rbf_similarity(Z)
    small_tissue = (t[:, None] == t[None, :]).astype(float)
    off = ~np.eye(len(lines), dtype=bool)
    meta = {"lines": lines, "n_lines": len(lines), "tissues": dict(zip(*np.unique(t, return_counts=True))),
            "genes_after_expression_filter": int(keep.sum()), "genes_used": N_GENES,
            "corr_expr_similarity_vs_same_tissue": float(np.corrcoef(small_expr[off], small_tissue[off])[0, 1]),
            "profiles_per_line": 1, "experiments": int(mask.sum()), "hits": int((sub.y > 10).sum())}
    return sub, sims, shuffled, [pos[l] for l in lines], meta


def _init(state):
    _STATE.update(state)


def _world(lib, line, sim, columns):
    return MaskedWorld(lib, line, WorldConfig(context=True), columns=columns, identity_kernel=True, line_sim=sim)


def _contrast(base_scores, scores, y, budget, rng):
    hits = y > 10
    top_b = set(np.argsort(-base_scores, kind="stable")[:budget])
    top_s = set(np.argsort(-scores, kind="stable")[:budget])
    enter, leave = list(top_s - top_b), list(top_b - top_s)
    i = rng.integers(0, y.size, PAIR_SAMPLE)
    j = rng.integers(0, y.size, PAIR_SAMPLE)
    ok = (i != j) & (y[i] != y[j])
    i, j = i[ok], j[ok]
    disagree = np.sign(base_scores[i] - base_scores[j]) != np.sign(scores[i] - scores[j])
    correct = np.sign(scores[i] - scores[j]) == np.sign(y[i] - y[j])
    return {"top_changed": len(enter), "hits_enter": int(hits[enter].sum()) if enter else 0,
            "hits_leave": int(hits[leave].sum()) if leave else 0,
            "disagree_share": float(disagree.mean()),
            "concordance_on_disagreements": float(correct[disagree].mean()) if disagree.any() else None}


def run_line(line: int) -> dict:
    lib, sims, shuffled = _STATE["lib"], _STATE["sims"], _STATE["shuffled"]
    y = lib.y[lib.c == line]
    rng = np.random.default_rng([line, 77])
    H, HS = columns_for("H"), columns_for("HS")
    worlds = {"base": _world(lib, line, None, H), "expr": _world(lib, line, sims["expr"], HS),
              "tissue": _world(lib, line, sims["tissue"], HS), "mono": _world(lib, line, None, HS)}
    out = {"line": line, "arms": {}}
    base_prior = worlds["base"].prior_target
    budget = int(np.ceil(0.1 * y.size))
    for name, w in worlds.items():
        rec = {"prior": prior_metrics(w, y), "wm_static": run_arm(lib, w, "wm_static", line)["exploit"]["hits"],
               "wm_full": run_arm(lib, w, "wm_full", line)["exploit"]["hits"]}
        if name != "base":
            rec["contrast_vs_base"] = _contrast(base_prior, w.prior_target, y, budget, rng)
        out["arms"][name] = rec
    out["history"] = run_arm(lib, worlds["base"], "history", line)["exploit"]["hits"]
    # simple predictor with identical inputs: similarity-weighted pair mean column of the expr world
    knn = worlds["expr"].X_target[:, 3]
    hits = y > 10
    out["arms"]["knn_expr"] = {"prior": {"spearman": float(stats.spearmanr(knn, y).correlation),
                                         "hits_top_budget": int(hits[np.argsort(-knn, kind="stable")[:budget]].sum())},
                               "contrast_vs_base": _contrast(base_prior, knn, y, budget, rng)}
    shuf = []
    for s, sim in enumerate(shuffled):
        w = _world(lib, line, sim, HS)
        shuf.append({"prior": prior_metrics(w, y), "wm_static": run_arm(lib, w, "wm_static", line)["exploit"]["hits"],
                     "wm_full": run_arm(lib, w, "wm_full", line)["exploit"]["hits"],
                     "contrast_vs_base": _contrast(base_prior, w.prior_target, y, budget, rng)})
    out["arms"]["expr_shuf"] = shuf
    # does expression change the FINAL selections relative to base with feedback?
    from common import selected_rows
    sel_b = set(selected_rows(lib, worlds["base"], "wm_full", line).tolist())
    sel_e = set(selected_rows(lib, worlds["expr"], "wm_full", line).tolist())
    out["wm_full_selection_overlap_expr_vs_base"] = len(sel_b & sel_e) / max(len(sel_b), 1)
    return out


def summarise(per_line):
    lines = sorted(r["line"] for r in per_line)
    by = {r["line"]: r for r in per_line}

    def val(arm, key, l):
        rec = by[l]["arms"][arm]
        if arm == "expr_shuf":
            return float(np.mean([_get(r, key) for r in rec]))
        return float(_get(rec, key))

    def _get(rec, key):
        cur = rec
        for k in key.split("."):
            cur = cur[k]
        return cur

    out = {"totals": {}, "contrasts": {}}
    arms = ["base", "expr", "expr_shuf", "tissue", "mono"]
    for arm in arms:
        out["totals"][arm] = {k: float(sum(val(arm, k, l) for l in lines)) for k in ("wm_static", "wm_full", "prior.hits_top_budget")}
        out["totals"][arm]["prior_spearman_median"] = float(np.median([val(arm, "prior.spearman", l) for l in lines]))
    out["totals"]["knn_expr"] = {"prior.hits_top_budget": float(sum(by[l]["arms"]["knn_expr"]["prior"]["hits_top_budget"] for l in lines)),
                                 "prior_spearman_median": float(np.median([by[l]["arms"]["knn_expr"]["prior"]["spearman"] for l in lines]))}
    out["totals"]["history"] = float(sum(by[l]["history"] for l in lines))
    for key in ("wm_static", "wm_full", "prior.hits_top_budget", "prior.spearman"):
        for ref in ("base", "expr_shuf", "tissue", "mono"):
            d = np.array([val("expr", key, l) - val(ref, key, l) for l in lines])
            out["contrasts"][f"expr-{ref}:{key}"] = {"mean_per_line": float(d.mean()), "ci95": bootstrap_ci(d)}
    for key in ("prior.hits_top_budget",):
        d = np.array([by[l]["arms"]["knn_expr"]["prior"]["hits_top_budget"] - val("expr", key, l) for l in lines])
        out["contrasts"][f"knn_expr-expr:{key}"] = {"mean_per_line": float(d.mean()), "ci95": bootstrap_ci(d)}
    for arm in ("expr", "tissue", "mono", "knn_expr", "expr_shuf"):
        def c(l, k):
            rec = by[l]["arms"][arm]
            if arm == "expr_shuf":
                vals = [r["contrast_vs_base"][k] for r in rec if r["contrast_vs_base"][k] is not None]
                return float(np.mean(vals)) if vals else np.nan
            v = rec["contrast_vs_base"][k]
            return np.nan if v is None else float(v)
        net = np.array([c(l, "hits_enter") - c(l, "hits_leave") for l in lines])
        conc = np.array([c(l, "concordance_on_disagreements") for l in lines])
        out["contrasts"][f"{arm}:top_budget_swap_net_hits_vs_base"] = {
            "mean_per_line": float(net.mean()), "ci95": bootstrap_ci(net),
            "items_changed_total": float(sum(c(l, "top_changed") for l in lines))}
        out["contrasts"][f"{arm}:concordance_on_disagreements_vs_base"] = {
            "median": float(np.nanmedian(conc)), "mean": float(np.nanmean(conc)),
            "ci95": bootstrap_ci(conc[np.isfinite(conc)]),
            "disagree_share_median": float(np.median([c(l, "disagree_share") for l in lines]))}
    out["wm_full_selection_overlap_expr_vs_base_median"] = float(np.median([by[l]["wm_full_selection_overlap_expr_vs_base"] for l in lines]))
    return out


def main() -> int:
    started = time.time()
    sub, sims, shuffled, line_idx, meta = build_state()
    state = {"lib": sub, "sims": sims, "shuffled": shuffled}
    with ProcessPoolExecutor(max_workers=16, initializer=_init, initargs=(state,)) as pool:
        per_line = list(pool.map(run_line, line_idx))
    summary = summarise(per_line)
    payload = {"purpose": "WS2 bounded state diagnostic on O'Neil (development, exposed); gate failed beforehand",
               "expression_sha256": sha256_file(DEPMAP / "OmicsExpressionProteinCodingGenesTPMLogp1.csv"),
               "library_sha256": sha256_file(ONEIL), "meta": meta, "summary": summary, "per_line": per_line,
               "shuffle_seeds": SHUFFLE_SEEDS, "wall_seconds": round(time.time() - started, 1)}
    path = write_json("state_diagnostic.json", payload)
    print(path)
    print(meta)
    for k, v in summary["totals"].items():
        print("total", k, v)
    for k, v in summary["contrasts"].items():
        print(k, v)
    print("overlap", summary["wm_full_selection_overlap_expr_vs_base_median"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
