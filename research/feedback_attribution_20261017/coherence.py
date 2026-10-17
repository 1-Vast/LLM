"""Development diagnostic: is the promoted event score coherent, and is it calibrated on Beat AML?

File summary
- Path: research/feedback_attribution_20261017/coherence.py
- Purpose: PROTOCOL.md s7. Reported in full, not a hypothesis test.
- Parts:
  - ``counterexample``: the one-factor, three-item model where the promoted score falls from
    0.163 to 0.000178 after one readout, whatever its value.
  - ``martingale``: on held-out Beat AML samples (outer folds, rank 20, the confirmed exploit
    bridge), E over model-drawn readouts of score(posterior) minus score(prior), for the promoted
    score and the coherent score.
  - ``calibration``: on measured held-out pairs, the promoted score, the coherent (linear-G) score
    and the joint Monte Carlo score for the exact endpoint, against realised events. This uses
    outcomes. Before and after the four bridge readouts (the probed items are excluded after).
  - ``ranking``: how much the two scores disagree on the top 16.
- Interfaces: ``python -B coherence.py`` writes COHERENCE.json.
"""
from __future__ import annotations

import json

import numpy as np

from common import DOMAIN_CACHE, HERE, ROOT, hash_unit, load_domain, outer_folds, sha256, tie, write_json
from coherent import CoherentScorer, martingale_gap, mc_event_prob

from agent.bridge_design import nominate  # noqa: E402
from virtual_cell.bridged_transfer import BridgedTransferModel, BridgeState  # noqa: E402

RANK, K, BUDGET = 20, 4, 16
GAP_DRAWS, MC_DRAWS = 64, 1000


def counterexample() -> dict:
    from test_science import one_factor_three_items
    m = one_factor_three_items()
    st = BridgeState(np.zeros(1), np.eye(1), np.array([], int))
    post = {str(y): float(m.event_prob(m.posterior(st, [0], [y]))[1]) for y in (-4, -2, 0, 2, 4)}
    gap = martingale_gap(m, m.event_prob, st, [0], 4000, np.random.default_rng(1))
    return {"model": "f ~ N(0,1); y_d = f + e_d, e_d ~ N(0, 0.04), d = 1..3; a = 0, b = 1, med = 0, MAD = 1/3",
            "prior_event_prob_item2": float(m.event_prob(st)[1]), "posterior_after_item1": post,
            "expected_posterior_minus_prior_item2": float(gap[1])}


def metrics(p, y):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return {"pairs": int(len(y)), "events": int(y.sum()), "mean_predicted": float(p.mean()),
            "observed_rate": float(y.mean()), "brier": float(((p - y) ** 2).mean()),
            "log_loss": float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())}


def auroc(y, s):
    from scipy.stats import rankdata
    y = y.astype(bool)
    r = rankdata(s)
    n1, n0 = y.sum(), (~y).sum()
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def main() -> None:
    d = load_domain()
    Y, X, ev = d["Y"], d["X"], d["events"]
    fid = outer_folds(d["groups"])
    order = tie(d["items"])
    gaps = {"promoted": [], "coherent": []}
    top_gaps = {"promoted": [], "coherent": []}
    cal = {k: {"p": [], "y": []} for k in ("promoted_prior", "coherent_prior", "mc_prior",
                                            "promoted_post", "coherent_post")}
    overlap, spearman = [], []
    for k in range(5):
        src, tgt = np.flatnonzero(fid != k), np.flatnonzero(fid == k)
        model = BridgedTransferModel(rank=RANK, abs_gate=None, min_measured=100, impute_iters=15).fit(Y[src], X[src])
        sc = CoherentScorer(model, Y[src])
        q = model.measured_rate
        for c in tgt:
            seed = int(hash_unit([str(d["contexts"][c])], "coherence")[0] * 1e12)
            rng = np.random.default_rng(seed)
            st = model.prior(X[c])
            ps, pc = model.event_prob(st), sc.event_prob(st)
            B = nominate(q * ps, K, [], order)
            top = np.argsort(-(q * ps))[:50]
            for name, fn in (("promoted", model.event_prob), ("coherent", sc.event_prob)):
                g = martingale_gap(model, fn, st, B, GAP_DRAWS, rng)
                gaps[name].append(float(np.delete(g, B).mean()))
                top_gaps[name].append(float(g[np.setdiff1d(top, B)].mean()))
            pm = mc_event_prob(model, st, MC_DRAWS, rng)
            meas = np.isfinite(Y[c]) & model.threshold_ok
            for name, p in (("promoted_prior", ps), ("coherent_prior", pc), ("mc_prior", pm)):
                cal[name]["p"].append(p[meas])
                cal[name]["y"].append(ev[c][meas])
            st1 = model.posterior(st, B, Y[c, B])
            rest = meas.copy()
            rest[B] = False
            for name, p in (("promoted_post", model.event_prob(st1)), ("coherent_post", sc.event_prob(st1))):
                cal[name]["p"].append(p[rest])
                cal[name]["y"].append(ev[c][rest])
            t1 = set(nominate(q * ps, BUDGET, [], order).tolist())
            t2 = set(nominate(q * pc, BUDGET, [], order).tolist())
            overlap.append(len(t1 & t2) / BUDGET)
            from scipy.stats import spearmanr
            spearman.append(float(spearmanr(q * ps, q * pc).statistic))
        print("fold", k, flush=True)
    calib = {}
    for name, v in cal.items():
        p, y = np.concatenate(v["p"]), np.concatenate(v["y"]).astype(float)
        calib[name] = {**metrics(p, y), "auroc_pooled": auroc(y, p)}
    out = {
        "status": "DEVELOPMENT DIAGNOSTIC (Beat AML exposed); PROTOCOL.md s7",
        "inputs_sha256": {str(DOMAIN_CACHE.relative_to(ROOT)).replace("\\", "/"): sha256(DOMAIN_CACHE)},
        "rank": RANK, "bridge": "confirmed exploit-first top 4 (promoted score)",
        "counterexample": counterexample(),
        "martingale": {name: {"mean_gap_all_unprobed": float(np.mean(v)),
                              "mean_gap_top50_unprobed": float(np.mean(top_gaps[name])),
                              "draws_per_sample": GAP_DRAWS}
                       for name, v in gaps.items()},
        "mean_prior_event_prob": {"promoted": calib["promoted_prior"]["mean_predicted"],
                                  "coherent": calib["coherent_prior"]["mean_predicted"]},
        "calibration_measured_pairs": calib,
        "ranking": {"top16_overlap_promoted_vs_coherent": float(np.mean(overlap)),
                    "spearman_promoted_vs_coherent": float(np.mean(spearman))},
    }
    write_json(HERE / "COHERENCE.json", out)
    print(json.dumps({k: out[k] for k in ("counterexample", "martingale", "ranking")}, indent=1))
    print(json.dumps(calib, indent=1))


if __name__ == "__main__":
    main()
