"""Feedback-gain attribution on Beat AML: the same four probe reads, then which prior and which update.

File summary
- Path: research/feedback_attribution_20261017/attribution.py
- Purpose: run the pre-registered groups of PROTOCOL.md on Beat AML 2.0 (exposed, development
  evidence) and write per-sample records; `--summary` applies the registered analysis and writes
  RESULTS.json once.
- Core points:
  - Outer folds are the confirmation's five patient-disjoint folds; the Virtual Cell
    (`virtual_cell.bridged_transfer.BridgedTransferModel`) is refitted on each fold's source
    patients at one fixed common rank, the same for every group.
  - Every group of a configuration shares the same four probe queries per sample and their hits;
    groups differ only in how they choose the other twelve. The probe queries count against every
    group's budget, including the groups that ignore their readouts (A, C, S).
  - Primary probes: the top four of the population item prior (source event rate x source
    coverage). They use no RNA, so the no-RNA groups receive no RNA-chosen information.
  - Groups (the twelve follow-up queries):
    - A_item: the population item prior, no update.
    - A: the model's population state (no RNA), no update.
    - B: the population state, updated by the probe readouts.
    - C: the RNA (basal-expression) state, no update.
    - D: the RNA state, updated by the probe readouts.
    - E_pop, E_rna: the population or RNA state, updated through overall sensitivity only
      (`coherent.global_posterior`).
    - F: as D, with the returned readouts deranged within the sample (`coherent.derange`).
    - S_ridge, S_gbm: drug-specific state models on the same 30 basal PCs (ridge; gradient-boosted
      trees), no update; event probability from the brief's residual variance formula.
    - *_coh: A, B, C, D and E_rna scored with the coherent scorer instead of the promoted one.
  - Planner arms (own first rounds, so compared on all 16 queries; coherent scorer, RNA state):
    vc0_coh (no intermediate experiment), x2_coh, x4_coh, x8_coh (exploit-first with k fixed),
    plan_l0 and plan_l05 (`planner.choose_design` per sample, round cost 0 or 0.05 hits).
  - Tasks: ``archive`` (all 165 inhibitors; an unmeasured pair is a spent query with no hit;
    availability weight = source archive coverage), ``design`` (the menu is the sample's
    scheduled panel; a scheduled pair with no record is a failed assay; weight = source success
    rate given scheduled), ``panel80`` (archive rules on the 93 inhibitors scheduled for at least
    80% of samples).
- Interfaces: ``python -B attribution.py <config>``, ``python -B attribution.py --summary``.
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np

from common import (CACHE, HERE, basal_pcs, hash_unit, holm, load_domain, outer_folds, paired,
                    schedule_matrix, sha256, tie, write_json)
from coherent import CoherentScorer, derange, global_posterior
from planner import choose_design, design_values

from agent.bridge_design import nominate  # noqa: E402  (src on sys.path via common)
from virtual_cell.bridged_transfer import RIDGE_ALPHAS, BridgedTransferModel, normal_cdf  # noqa: E402

BUDGET, K = 16, 4
MIN_MEASURED, IMPUTE = 100, 15
GROUPS = ("A_item", "A", "B", "C", "D", "E_pop", "E_rna", "F")
STRONG = ("S_ridge", "S_gbm")
COHERENT = ("A_coh", "B_coh", "C_coh", "D_coh", "E_rna_coh")
PLAN_FIXED = {"vc0_coh": 0, "x2_coh": 2, "x4_coh": 4, "x8_coh": 8}
PLAN_ADAPTIVE = {"plan_l0": 0.0, "plan_l05": 0.05}
K_OPTIONS = (2, 4, 8)
DRAWS = 128
ROUNDS = {"A_item": 1, "A": 1, "C": 1, "S_ridge": 1, "S_gbm": 1, "A_coh": 1, "C_coh": 1,
          "B": 2, "D": 2, "E_pop": 2, "E_rna": 2, "F": 2, "B_coh": 2, "D_coh": 2, "E_rna_coh": 2}
CONFIGS = {
    "primary": {"rank": 20, "task": "archive", "probes": "pop", "extras": True},
    "rank10": {"rank": 10, "task": "archive", "probes": "pop", "extras": False},
    "rank40": {"rank": 40, "task": "archive", "probes": "pop", "extras": False},
    "probes_vc": {"rank": 20, "task": "archive", "probes": "vc", "extras": False},
    "design": {"rank": 20, "task": "design", "probes": "pop", "extras": False},
    "panel80": {"rank": 20, "task": "panel80", "probes": "pop", "extras": False},
}
PANEL80 = 0.8


# ---------- strong state baselines ----------
def _ridge_loo(P1: np.ndarray, y: np.ndarray):
    best = None
    pen = np.diag([0.0] + [1.0] * (P1.shape[1] - 1))
    for alpha in RIDGE_ALPHAS:
        A = P1.T @ P1 + alpha * pen
        B = np.linalg.solve(A, P1.T @ y)
        H = np.einsum("ij,jk,ik->i", P1, np.linalg.inv(A), P1)
        loo = (y - P1 @ B) / (1 - H)
        err = float((loo ** 2).mean())
        if best is None or err < best[0]:
            best = (err, B, loo)
    return best[1], best[2]


def strong_state(d, src, tgt, model, gbm: bool):
    """Event probabilities of drug-specific state models for the fold's targets (targets x items)."""

    Y = d["Y"]
    P = basal_pcs(d["X"], rows=src)
    P1 = np.column_stack([np.ones(len(P)), P])
    Gs = np.nanmedian(Y[src], axis=1)
    bG, rG = _ridge_loo(P1[src], Gs)
    predG = P1[tgt] @ bG
    D = Y.shape[1]
    out = {"S_ridge": np.zeros((len(tgt), D))}
    if gbm:
        out["S_gbm"] = np.zeros((len(tgt), D))
        from sklearn.ensemble import HistGradientBoostingRegressor
        inner = hash_unit(d["groups"][src], "gbm-oof")
        inner = np.floor(inner * 3).astype(int)
    c = model.med - 3.0 * model.mad
    for j in range(D):
        if not model.threshold_ok[j]:
            continue
        rows = np.flatnonzero(np.isfinite(Y[src, j]))
        if len(rows) < 30:
            for name in out:
                out[name][:, j] = model.source_event_rate[j]
            continue
        y = Y[src[rows], j]
        preds = {}
        bj, rj = _ridge_loo(P1[src[rows]], y)
        preds["S_ridge"] = (P1[tgt] @ bj, rj)
        if gbm:
            oof = np.empty(len(rows))
            for f in range(3):
                tr, te = inner[rows] != f, inner[rows] == f
                m = HistGradientBoostingRegressor(max_iter=150, learning_rate=0.05, max_leaf_nodes=8,
                                                  min_samples_leaf=20, l2_regularization=1.0, random_state=0)
                oof[te] = m.fit(P[src[rows]][tr], y[tr]).predict(P[src[rows]][te])
            m = HistGradientBoostingRegressor(max_iter=150, learning_rate=0.05, max_leaf_nodes=8,
                                              min_samples_leaf=20, l2_regularization=1.0, random_state=0)
            preds["S_gbm"] = (m.fit(P[src[rows]], y).predict(P[tgt]), y - oof)
        b = model.b[j]
        for name, (py, r) in preds.items():
            rg = rG[rows]
            var = r.var() + b * b * rg.var() - 2 * b * np.mean((r - r.mean()) * (rg - rg.mean()))
            mean = py - model.a[j] - b * predG
            out[name][:, j] = normal_cdf((c[j] - mean) / np.sqrt(max(var, 1e-9)))
    return out


# ---------- one configuration ----------
def _seed(key: str) -> int:
    return int(hash_unit([key], "planner")[0] * 1e12)


def run(config: str, d: dict | None = None, sched: np.ndarray | None = None) -> list[dict]:
    """Records of one configuration; ``d`` and ``sched`` default to Beat AML (tests pass synthetic ones)."""

    cfg = CONFIGS[config]
    d = load_domain() if d is None else d
    Y, X, ev = d["Y"], d["X"], d["events"]
    fid = outer_folds(d["groups"])
    order = tie(d["items"])
    sched = schedule_matrix(d) if sched is None else sched
    hc = sched.mean(0) >= PANEL80
    recs = []
    for k in range(5):
        t0 = time.time()
        src, tgt = np.flatnonzero(fid != k), np.flatnonzero(fid == k)
        model = BridgedTransferModel(rank=cfg["rank"], abs_gate=None, min_measured=MIN_MEASURED,
                                     impute_iters=IMPUTE).fit(Y[src], X[src])
        sc = CoherentScorer(model, Y[src])
        if cfg["task"] == "design":
            rec_s, sch_s = np.isfinite(Y[src]) & sched[src], sched[src]
            q = (rec_s.sum(0) + 0.5) / (sch_s.sum(0) + 1.0)
        else:
            q = model.measured_rate
        pop = model.prior(None)
        strong = strong_state(d, src, tgt, model, gbm=True) if cfg["extras"] else {}
        for ti, c in enumerate(tgt):
            key = str(d["contexts"][c])
            menu = sched[c] if cfg["task"] == "design" else hc if cfg["task"] == "panel80" else np.ones(len(q), bool)
            ban = np.flatnonzero(~menu)

            def pick(score, n, exclude=()):
                s = np.where(menu, score, -np.inf)
                out = nominate(s, n, list(exclude), order)
                return out[np.isfinite(s[out])]

            st_rna = model.prior(X[c])
            item = q * model.source_event_rate
            P_ = pick(item if cfg["probes"] == "pop" else q * model.event_prob(st_rna), K)
            yP = Y[c, P_]
            truth = ev[c]
            rec = {"context": key, "group": str(d["groups"][c]), "fold": int(k), "events": int(truth.sum()),
                   "probe": P_.tolist(), "probe_hits": int(truth[P_].sum()),
                   "probe_returned": int(np.isfinite(yP).sum()), "menu": int(menu.sum())}

            def follow(name, score):
                picks = pick(score, BUDGET - len(P_), P_)
                rec["h_" + name] = int(truth[picks].sum())
                rec["w_" + name] = int((~np.isfinite(Y[c, picks])).sum())

            src_score = lambda st: q * model.event_prob(st)  # noqa: E731
            coh_score = lambda st: q * sc.event_prob(st)  # noqa: E731
            st_B = model.posterior(pop, P_, yP)
            st_D = model.posterior(st_rna, P_, yP)
            follow("A_item", item)
            follow("A", src_score(pop))
            follow("B", src_score(st_B))
            follow("C", src_score(st_rna))
            follow("D", src_score(st_D))
            follow("E_pop", src_score(global_posterior(model, sc.g, pop, P_, yP)))
            follow("E_rna", src_score(global_posterior(model, sc.g, st_rna, P_, yP)))
            follow("F", src_score(model.posterior(st_rna, P_, derange(yP, order[P_]))))
            if not cfg["extras"]:
                recs.append(rec)
                continue
            for name, probs in strong.items():
                follow(name, q * probs[ti])
            follow("A_coh", coh_score(pop))
            follow("B_coh", coh_score(st_B))
            follow("C_coh", coh_score(st_rna))
            follow("D_coh", coh_score(st_D))
            follow("E_rna_coh", coh_score(global_posterior(model, sc.g, st_rna, P_, yP)))

            vals = design_values(model, sc.event_prob, st_rna, q, BUDGET, K_OPTIONS, order, DRAWS,
                                 np.random.default_rng(_seed(key)), menu=menu)
            by_k = {v.k: v for v in vals}
            rec["design_values"] = {str(v.k): {"evsi": v.evsi, "evsi_se": v.evsi_se, "oc": v.opportunity_cost,
                                               "direct": v.direct, "returned_share": v.returned_share}
                                    for v in vals}

            def execute(kk):
                if kk == 0:
                    wells = pick(coh_score(st_rna), BUDGET)
                    return int(truth[wells].sum()), int((~np.isfinite(Y[c, wells])).sum())
                B = by_k[kk].bridge
                st1 = model.posterior(st_rna, B, Y[c, B])
                fin = pick(coh_score(st1), BUDGET - len(B), B)
                wells = np.concatenate([B, fin])
                return int(truth[wells].sum()), int((~np.isfinite(Y[c, wells])).sum())

            for name, kk in PLAN_FIXED.items():
                rec["t_" + name], rec["w_" + name] = execute(kk) if kk in by_k else (None, None)
            for name, lam in PLAN_ADAPTIVE.items():
                shifted = [v if v.k == 0 else type(v)(**{**v.__dict__, "round_cost": lam, "delta": v.delta - lam})
                           for v in vals]
                kk = choose_design(shifted).k
                rec["k_" + name] = int(kk)
                rec["t_" + name], rec["w_" + name] = execute(kk)
            recs.append(rec)
        print(f"{config} fold {k}: {len(tgt)} targets, {time.time() - t0:.0f} s", flush=True)
    return recs


# ---------- registered analysis ----------
PRIMARY = {"H1": ("B", "A"), "H2": ("D", "B"), "H3": ("C", "A"), "H4": ("D", "E_rna")}
SECONDARY = [("D", "F"), ("D", "C"), ("B", "C"), ("E_rna", "C"), ("E_pop", "A"), ("B", "E_pop"),
             ("B", "A_item"), ("C", "A_item"), ("D", "A_item"), ("A", "A_item"),
             ("S_ridge", "A_item"), ("S_gbm", "A_item"), ("C", "S_ridge"), ("C", "S_gbm"),
             ("A_coh", "A"), ("B_coh", "B"), ("C_coh", "C"), ("D_coh", "D"), ("E_rna_coh", "E_rna"),
             ("B_coh", "A_coh"), ("D_coh", "B_coh"), ("C_coh", "A_coh"), ("D_coh", "E_rna_coh")]
PLANNER_CONTRASTS = [("x4_coh", "vc0_coh"), ("x2_coh", "vc0_coh"), ("x8_coh", "vc0_coh"),
                     ("plan_l0", "x4_coh"), ("plan_l0", "vc0_coh"), ("plan_l05", "x4_coh"), ("plan_l05", "vc0_coh")]
MIN_USEFUL = 0.05
ALPHA = 0.025


def _levels(st, rounds_a, rounds_b, positive=None):
    lo, hi = st["ci95"]
    dr = rounds_a - rounds_b
    return {"mean": st["mean"], "ci95": [lo, hi], "p_one_sided": st["p_one_sided"],
            "improved": st["positive_contexts"], "worsened": st["negative_contexts"],
            "positive": bool(lo > 0) if positive is None else bool(positive),
            "exceeds_min_useful": bool(lo > MIN_USEFUL),
            "extra_rounds": dr,
            "net_of_round_cost_lower": lo - MIN_USEFUL * dr,
            "net_positive_at_0.05_per_round": bool(lo - MIN_USEFUL * dr > 0)}


def contrast(recs, a, b, prefix="h_"):
    diff = np.array([r[prefix + a] - r[prefix + b] for r in recs], float)
    return paired(diff, [r["group"] for r in recs])


def decisions(prim):
    def lo(h):
        return prim[h]["ci95"][0]

    def hi(h):
        return prim[h]["ci95"][1]

    q1 = ("RNA_COMPLEMENTS_FEEDBACK" if prim["H2"]["positive"] else
          "NO_RNA_FEEDBACK_SUFFICES" if prim["H1"]["positive"] and hi("H2") < MIN_USEFUL else "INCONCLUSIVE")
    qr = ("RNA_PRIOR_HAS_INDEPENDENT_VALUE" if prim["H3"]["positive"] else
          "RNA_PRIOR_ADDS_LESS_THAN_MIN_USEFUL" if hi("H3") < MIN_USEFUL else "INCONCLUSIVE")
    q2 = ("STRUCTURE_BEATS_CALIBRATION" if prim["H4"]["positive"] else
          "GLOBAL_CALIBRATION_SUFFICES" if hi("H4") < MIN_USEFUL and prim["E_rna-C"]["ci95"][0] > 0 else
          "INCONCLUSIVE")
    return {"Q1_feedback_without_rna": q1, "Q_rna_prior": qr, "Q2_structure_vs_calibration": q2}


def summarise() -> dict:
    """The registered analysis, written once to RESULTS.json."""

    if (HERE / "RESULTS.json").exists():
        raise SystemExit("RESULTS_EXIST: the registered analysis already ran")
    out = analyse()
    write_json(HERE / "RESULTS.json", out)
    return out


def analyse() -> dict:
    """The registered analysis from the cached records (pure; `verify.py` recomputes it)."""

    out = {"status": "DEVELOPMENT (Beat AML is exposed)", "configs": {}}
    for name in CONFIGS:
        path = CACHE / f"records_{name}.json"
        recs = json.loads(path.read_text(encoding="utf-8"))
        groups = [g for g in GROUPS + STRONG + COHERENT if "h_" + g in recs[0]]
        res = {"records_sha256": sha256(path), "samples": len(recs), "patients": len({r["group"] for r in recs}),
               "mean_follow_up_hits": {g: float(np.mean([r["h_" + g] for r in recs])) for g in groups},
               "mean_total_hits": {g: float(np.mean([r["probe_hits"] + r["h_" + g] for r in recs])) for g in groups},
               "follow_up_unmeasured_per_sample": {g: float(np.mean([r["w_" + g] for r in recs])) for g in groups},
               "probe_hits_per_sample": float(np.mean([r["probe_hits"] for r in recs])),
               "probe_returned_share": float(np.mean([r["probe_returned"] for r in recs]) / K)}
        stats = {h: contrast(recs, a, b) for h, (a, b) in PRIMARY.items()}
        adj = holm({h: s["p_one_sided"] for h, s in stats.items()})
        prim = {}
        for h, (a, b) in PRIMARY.items():
            ok = adj[h] < ALPHA and stats[h]["ci95"][0] > 0
            prim[h] = {"contrast": f"{a}-{b}", "p_holm": adj[h], **_levels(stats[h], ROUNDS[a], ROUNDS[b], ok)}
        sec = {}
        for a, b in SECONDARY:
            if "h_" + a in recs[0] and "h_" + b in recs[0]:
                sec[f"{a}-{b}"] = _levels(contrast(recs, a, b), ROUNDS[a], ROUNDS[b])
        prim["E_rna-C"] = sec["E_rna-C"]
        res["primary"] = {h: prim[h] for h in PRIMARY}
        res["decisions"] = decisions(prim)
        res["secondary"] = sec
        if "t_plan_l0" in recs[0]:
            arms = list(PLAN_FIXED) + list(PLAN_ADAPTIVE)
            res["planner"] = {
                "mean_total_hits": {a: float(np.mean([r["t_" + a] for r in recs])) for a in arms},
                "unmeasured_per_sample": {a: float(np.mean([r["w_" + a] for r in recs])) for a in arms},
                "k_chosen": {a: {str(kk): int(sum(r["k_" + a] == kk for r in recs)) for kk in (0,) + K_OPTIONS}
                             for a in PLAN_ADAPTIVE},
                "mean_rounds": {a: float(np.mean([1 + (r["k_" + a] > 0) for r in recs])) for a in PLAN_ADAPTIVE},
                "contrasts": {}}
            rounds = {**{a: 1 + (kk > 0) for a, kk in PLAN_FIXED.items()}}
            for a, b in PLANNER_CONTRASTS:
                st = contrast(recs, a, b, prefix="t_")
                ra = rounds.get(a, res["planner"]["mean_rounds"].get(a))
                rb = rounds.get(b, res["planner"]["mean_rounds"].get(b))
                res["planner"]["contrasts"][f"{a}-{b}"] = _levels(st, ra, rb)
            ev = {str(kk): float(np.mean([r["design_values"][str(kk)]["evsi"] for r in recs])) for kk in K_OPTIONS}
            oc = {str(kk): float(np.mean([r["design_values"][str(kk)]["oc"] for r in recs])) for kk in K_OPTIONS}
            res["planner"]["mean_model_evsi"] = ev
            res["planner"]["mean_model_opportunity_cost"] = oc
        out["configs"][name] = res
    out["parity_probes_vc"] = parity_probes_vc()
    out["tuned"] = summarise_tuned()
    return out


TUNED_CONTRASTS = [("exploit_t", "vc0_t"), ("look_t", "exploit_t"), ("look_t", "vc0_t"), ("hybrid_c", "exploit_t"),
                   ("cs_l05", "exploit_t"), ("cs_l05", "vc0_t"), ("cs_l0", "exploit_t"), ("exploit_t", "b_exploit@20"),
                   ("vc0_t", "vc0@20")]


def summarise_tuned() -> dict:
    path = CACHE / "records_tuned.json"
    t = json.loads(path.read_text(encoding="utf-8"))
    recs = t["records"]
    rounds = {"vc0_t": 1, "exploit_t": 2, "look_t": 2, "b_exploit@20": 2, "vc0@20": 1}
    for name in ("hybrid_c", "cs_l05", "cs_l0"):
        procs = [t["choices"][str(r["fold"])][name]["procedure"] for r in recs]
        rounds[name] = float(np.mean([1 if p == "vc0" else 2 for p in procs]))
    arms = ["vc0_t", "exploit_t", "look_t", "hybrid_c", "cs_l05", "cs_l0"]
    out = {"records_sha256": sha256(path), "inner_parity_with_confirmation": t["inner_parity_with_confirmation"],
           "mean_hits": {a: float(np.mean([r[a] for r in recs])) for a in arms},
           "mean_rounds": {a: rounds[a] for a in arms},
           "choices": {k: {"tuned_ranks": v["tuned_ranks"],
                           "hybrid_c": [v["hybrid_c"]["procedure"], v["hybrid_c"]["rank"]],
                           **{n: [v[n]["procedure"], v[n]["rank"], v[n]["candidates"]] for n in ("cs_l05", "cs_l0")}}
                       for k, v in t["choices"].items()},
           "contrasts": {}}
    for a, b in TUNED_CONTRASTS:
        diff = np.array([r[a] - r[b] for r in recs], float)
        out["contrasts"][f"{a}-{b}"] = _levels(paired(diff, [r["group"] for r in recs]), rounds[a], rounds[b])
    return out


def parity_probes_vc() -> dict:
    """With vc0's own top four as probes, D is the confirmed exploit-first system and C + probes is vc0.

    Checked on the folds where the confirmation also ran at rank 20.
    """

    from common import SOURCE_STUDY
    from common import ROOT
    conf = json.loads((SOURCE_STUDY / "RESULTS.json").read_text(encoding="utf-8"))["choices"]
    folds20 = [int(k) for k, v in conf.items() if v["rank"] == 20]
    old = {r["context"]: r for r in
           json.loads((ROOT / "tmp/context_transfer_20261017/confirm_records.json").read_text(encoding="utf-8"))}
    recs = json.loads((CACHE / "records_probes_vc.json").read_text(encoding="utf-8"))
    rows = [r for r in recs if r["fold"] in folds20]
    bad_d = [r["context"] for r in rows if r["probe_hits"] + r["h_D"] != old[r["context"]]["b_exploit"]]
    bad_c = [r["context"] for r in rows if r["probe_hits"] + r["h_C"] != old[r["context"]]["vc0"]]
    return {"folds": folds20, "samples": len(rows), "D_equals_confirmed_b_exploit": not bad_d,
            "C_plus_probes_equals_confirmed_vc0": not bad_c, "mismatches": bad_d[:10] + bad_c[:10]}


def main():
    if sys.argv[1:] == ["--summary"]:
        out = summarise()
        for name, res in out["configs"].items():
            print(name, json.dumps({h: (round(v["mean"], 4), [round(x, 4) for x in v["ci95"]], round(v["p_holm"], 4),
                                        v["positive"]) for h, v in res["primary"].items()}), res["decisions"])
        print(json.dumps(out["parity_probes_vc"]))
        return
    name = sys.argv[1]
    recs = run(name)
    write_json(CACHE / f"records_{name}.json", recs)


if __name__ == "__main__":
    main()
