"""One-shot confirmation on Beat AML 2.0 (primary AML patient samples).

File summary
- Path: research/context_transfer_20261017/confirm.py
- Purpose: apply the system frozen on PRISM development, unchanged, to an untouched domain, and
  write RESULTS.json exactly once.
- Core points:
  - Refuses (FREEZE_MISMATCH) unless every FREEZE.json digest matches; refuses (RESULTS_EXIST) if
    RESULTS.json is already present.
  - Outer folds by patient. In each fold the agent selects the Virtual Cell rank and its
    procedure by replaying candidates on that fold's source patients only
    (procedure.menu_records with inner folds by patient, then procedure.choose with the frozen
    "hybrid" rule chosen by RULE_CHOICE.md). Every arm of the fold then runs at the selected rank.
  - `maestro` is the full system: the selected procedure. Primary contrasts P1-P6 with Holm
    adjustment and the verdict rules of PROTOCOL.md s6-s7; secondary analyses and the process
    report (error taxonomy, recovery, sub-task completion, costs) follow.
  - The `llm` arm (secondary, paid) is gated: it runs only with `--llm` and only after the
    deterministic analysis shows the Virtual Cell's value on this domain (claim C1 or C2).
    Otherwise it is recorded as NOT_RUN with a named reason. Every call is cached; spend is
    reported separately.
- Interfaces: `python -B confirm.py [--llm]`.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time

import numpy as np

from common import CACHE, HERE, ROOT, folds, paired, sha256, write_json

FROZEN = {
    "budget": 16,
    "k_bridge": 4,
    "impute_iters": 15,
    "ranks": [5, 10, 20, 40],
    "procedures": ["vc0", "b_exploit", "b_lookahead"],
    "selection_rule": "hybrid",
    "z_bridge": 1.645,
    "fold_salt": "context-transfer-subject",
    "min_useful": 0.05,
    "noninferiority_margin": 0.05,
    "alpha": 0.025,
}
PRIMARY = [("P1", "maestro", "vc0"), ("P2", "maestro", "b_exploit"),
           ("P3", "maestro", "match_panel"), ("P4", "vc0", "knn"), ("P6", "maestro", "b_lookahead")]
SECONDARY = [("b_lookahead", "vc0"), ("b_exploit", "vc0"), ("b_lookahead", "b_exploit"),
             ("b_lookahead", "b_info"), ("b_lookahead", "b_panel"), ("vc0", "item"), ("knn", "item"),
             ("vc0", "vc0_xshuffle"), ("maestro", "maestro_yshuffle"), ("llm", "b_lookahead"),
             ("llm", "maestro"), ("match_panel", "vc0"), ("maestro", "knn"),
             ("maestro@1", "maestro@inf"), ("maestro@2", "maestro@inf"), ("maestro@4", "maestro@inf"),
             ("maestro_bma", "maestro@inf")]
REPAIR_GRID = (1.0, 2.0, 4.0, float("inf"))
INF = float("inf")
# autonomy level of each arm on the six-level spectrum of Zhao et al. 2026 (REVIEW.md s10)
AUTONOMY = {"random": "L0", "item": "L0", "knn": "L0", "vc0": "L0", "vc0_xshuffle": "L0 control",
            "b_random": "L1", "b_exploit": "L1", "b_panel": "L1", "match_panel": "L1",
            "b_info": "L2", "b_lookahead": "L2", "maestro": "L3 (source-verified procedure choice)",
            "maestro_yshuffle": "L3 control", "llm": "L1/L2 hybrid"}
ARMS = ("random", "item", "knn", "vc0", "b_random", "b_exploit", "b_panel", "b_info", "b_lookahead",
        "match_panel", "maestro", "vc0_xshuffle")


def require_freeze() -> dict:
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    bad = []
    for rel, expected in freeze["sha256"].items():
        p = ROOT / rel
        if not p.exists():
            bad.append(rel)
            continue
        raw = p.read_bytes()
        if expected not in {hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()}:
            bad.append(rel)
    if bad:
        raise SystemExit(f"FREEZE_MISMATCH: {bad}")
    return freeze


def holm(ps: dict) -> dict:
    keys = sorted(ps, key=lambda k: ps[k])
    m = len(keys)
    adj, running = {}, 0.0
    for i, k in enumerate(keys):
        running = max(running, min(1.0, (m - i) * ps[k]))
        adj[k] = running
    return adj


def verdict(stat, p_adj, alpha, min_useful):
    lo, hi = stat["ci95"]
    if p_adj < alpha and lo > 0:
        return "SUPPORTED"
    if hi < 0:
        return "HARMFUL"
    if hi < min_useful:
        return "NOT_SUPPORTED"
    return "INCONCLUSIVE"


def noninferiority(recs, groups, margin):
    """P5: maestro against the best fixed procedure in hindsight (chosen on target outcomes)."""

    means = {p: float(np.mean([r[p] for r in recs])) for p in FROZEN["procedures"]}
    best = max(means, key=lambda p: (means[p], p == "vc0"))
    diff = np.array([r["maestro"] - r[best] for r in recs], float)
    st = paired(diff + margin, groups)
    lo, hi = st["ci95"]
    return {"contrast": f"maestro-{best} (best fixed in hindsight)", "best_fixed": best,
            "fixed_means": means, "mean": float(diff.mean()), "ci95": [lo - margin, hi - margin],
            "margin": margin, "p_one_sided": st["p_one_sided"], "n_contexts": st["n_contexts"],
            "n_clusters": st["n_clusters"]}


def fold_kw(fid, k, rank, data_beataml):
    return dict(rank=rank, abs_gate=None, min_measured=data_beataml.MIN_MEASURED, fold_ids=fid,
                context_filter=fid == k, impute_iters=FROZEN["impute_iters"], repair_threshold=INF)


def run_fold(d, fid, k, choice, data_beataml, replay):
    rank, proc = choice["rank"], choice["procedure"]
    kw = fold_kw(fid, k, rank, data_beataml)
    recs = replay.run(d, FROZEN["budget"], FROZEN["k_bridge"], arms=ARMS, maestro_rule="lookahead",
                      repair_grid=REPAIR_GRID, **kw)
    if proc == "vc0":
        ctrl = None
    else:
        rule = "exploit" if proc == "b_exploit" else "lookahead"
        ctrl = {r["context"]: r["maestro_yshuffle"] for r in
                replay.run(d, FROZEN["budget"], FROZEN["k_bridge"], arms=("maestro_yshuffle",),
                           maestro_rule=rule, **kw)}
    for r in recs:
        r["lookahead_norepair"] = r.pop("maestro")
        r["maestro"] = r[proc]
        r["maestro_procedure"], r["maestro_rank"] = proc, rank
        r["maestro_yshuffle"] = r["vc0"] if ctrl is None else ctrl[r["context"]]
        r["maestro_rounds"] = 1 if proc == "vc0" else 2
    return recs


def main():
    use_llm = "--llm" in sys.argv
    require_freeze()
    if (HERE / "RESULTS.json").exists():
        raise SystemExit("RESULTS_EXIST: confirmation already ran once")
    import data_beataml
    import procedure
    import replay

    if (procedure.Z_BRIDGE != FROZEN["z_bridge"] or list(procedure.RANKS) != FROZEN["ranks"]
            or list(procedure.PROCEDURES) != FROZEN["procedures"]):
        raise SystemExit("FREEZE_MISMATCH: procedure constants differ from FROZEN")

    t0 = time.time()
    d = data_beataml.load()
    fid = folds(d["groups"], FROZEN["fold_salt"])
    choices, recs = {}, []
    for k in range(5):
        menu = procedure.menu_records(d, fid, FROZEN["budget"], FROZEN["k_bridge"], None,
                                      data_beataml.MIN_MEASURED, FROZEN["impute_iters"], by_group=True,
                                      ranks=tuple(FROZEN["ranks"]), outer=False, only_folds={k})
        ch = procedure.choose(menu[k]["inner"], FROZEN["selection_rule"])
        choices[k] = ch
        print("fold", k, "rank", ch["rank"], "procedure", ch["procedure"], flush=True)
        recs.extend(run_fold(d, fid, k, ch, data_beataml, replay))
    groups = [r["group"] for r in recs]
    arms = list(ARMS) + ["maestro_yshuffle", "oracle"]
    res = {"frozen": FROZEN, "choices": choices,
           "domain": {"contexts": len(recs), "clusters": len(set(groups)),
                      "events_per_context": float(np.mean([r["events"] for r in recs])),
                      "contexts_with_events": int(sum(r["events"] > 0 for r in recs)),
                      "mean_hits": {a: float(np.mean([r[a] for r in recs])) for a in arms}}}

    stats, raw_p = {}, {}
    for hid, a, b in PRIMARY:
        diff = np.array([r[a] - r[b] for r in recs], float)
        stats[hid] = {"contrast": f"{a}-{b}", **paired(diff, groups)}
        raw_p[hid] = stats[hid]["p_one_sided"]
    stats["P5"] = noninferiority(recs, groups, FROZEN["noninferiority_margin"])
    raw_p["P5"] = stats["P5"]["p_one_sided"]
    adj = holm(raw_p)
    for hid in stats:
        stats[hid]["p_holm"] = adj[hid]
        if hid == "P5":
            ok = adj[hid] < FROZEN["alpha"] and stats[hid]["ci95"][0] > -FROZEN["noninferiority_margin"]
            stats[hid]["verdict"] = "NON_INFERIOR" if ok else "NOT_SHOWN"
        else:
            stats[hid]["verdict"] = verdict(stats[hid], adj[hid], FROZEN["alpha"], FROZEN["min_useful"])
    res["primary"] = stats
    claims = {"C1_virtual_cell_transfer": stats["P4"]["verdict"] == "SUPPORTED",
              "C2_virtual_cell_beyond_pilot_matching": stats["P3"]["verdict"] == "SUPPORTED",
              "C3_agent_adaptivity": stats["P5"]["verdict"] == "NON_INFERIOR",
              "C4_agent_beats_fixed_pipelines": "SUPPORTED" in (stats["P1"]["verdict"], stats["P2"]["verdict"],
                                                                stats["P6"]["verdict"])}
    res["claims"] = claims
    res["framework_verdict"] = ("CONFIRMED" if all(claims.values()) else
                                "PARTIAL" if any(claims.values()) else "NOT_CONFIRMED")

    gate_open = claims["C1_virtual_cell_transfer"] or claims["C2_virtual_cell_beyond_pilot_matching"]
    res["llm_arm"] = {"requested": use_llm, "gate": "C1 or C2 holds", "gate_open": bool(gate_open),
                      "status": "RUN" if use_llm and gate_open else "NOT_RUN",
                      "reason": None if use_llm and gate_open else
                      ("LLM_NOT_REQUESTED" if not use_llm else "LLM_GATE_CLOSED: no Virtual Cell value shown")}
    llm = None
    if use_llm and gate_open:
        from llm_arm import LLMBridge
        muts = data_beataml.mutations()
        llm = LLMBridge(CACHE / "llm_ledger.jsonl")

        def context_text(c):
            genes = muts.get(str(d["contexts"][c]), [])
            return {"system": "primary acute myeloid leukaemia sample from a patient, tested ex vivo "
                              "on a single-agent kinase/targeted inhibitor panel (AUC; lower is more sensitive)",
                    "mutated_genes_wes": genes[:60]}

        by_context = {r["context"]: r for r in recs}
        for k in range(5):
            for r in replay.run(d, FROZEN["budget"], FROZEN["k_bridge"], arms=("llm",), maestro_rule="lookahead",
                                llm=llm, context_text=context_text, item_names=d["items"],
                                **fold_kw(fid, k, choices[k]["rank"], data_beataml)):
                by_context[r["context"]].update({x: r[x] for x in ("llm", "llm_wasted", "llm_bridge_hits",
                                                                   "llm_refusal")})
        arms.append("llm")
        res["domain"]["mean_hits"]["llm"] = float(np.mean([r["llm"] for r in recs]))

    sec = {}
    for a, b in SECONDARY:
        if a in recs[0] and b in recs[0]:
            sec[f"{a}-{b}"] = paired(np.array([r[a] - r[b] for r in recs], float), groups)
    res["secondary"] = sec
    res["misfit_auroc_prior_failure"] = misfit_auroc(recs)
    res["errors"] = error_report(recs, arms, FROZEN["k_bridge"])
    res["autonomy"] = {a: AUTONOMY.get(a) for a in arms if a in AUTONOMY}
    res["costs"] = {"wells_per_context": FROZEN["budget"], "wet_lab_wells_purchased": 0,
                    "human_interventions": 0,
                    "assay_rounds": {**{a: (1 if a in ("random", "item", "knn", "vc0", "vc0_xshuffle") else 2)
                                        for a in arms if a not in ("maestro", "oracle")},
                                     "maestro": float(np.mean([r["maestro_rounds"] for r in recs]))}}
    if llm is not None:
        res["llm_spend"] = llm.spend()

    sub = {}
    for frac in (0.25, 0.5):
        rows = []
        for k in range(5):
            rows += replay.run(d, FROZEN["budget"], FROZEN["k_bridge"], arms=("vc0", "knn"),
                               rank=choices[k]["rank"], abs_gate=None, min_measured=data_beataml.MIN_MEASURED,
                               fold_ids=fid, context_filter=fid == k, impute_iters=FROZEN["impute_iters"],
                               source_fraction=frac)
        sub[str(frac)] = {a: float(np.mean([r[a] for r in rows])) for a in ("vc0", "knn")}
    sub["1.0"] = {a: res["domain"]["mean_hits"][a] for a in ("vc0", "knn")}
    res["source_scaling"] = sub
    res["seconds"] = time.time() - t0
    res["input_sha256"] = d["input_sha256"].tolist()
    write_json(CACHE / "confirm_records.json", recs)
    res["records_sha256"] = sha256(CACHE / "confirm_records.json")
    write_json(HERE / "RESULTS.json", res)
    print(json.dumps({"primary": {k: (v["mean"], v["ci95"], v["p_holm"], v["verdict"]) for k, v in stats.items()},
                      "claims": claims, "framework": res["framework_verdict"],
                      "means": res["domain"]["mean_hits"]}, indent=1))


def error_report(recs, arms, k_bridge):
    """Error taxonomy, recovery and sub-task completion (REVIEW.md s10.2)."""

    fail = np.array([r["vc0"] < r["item"] for r in recs])
    out = {"environment_wasted_wells_per_context": {a: float(np.mean([r[a + "_wasted"] for r in recs]))
                                                     for a in arms if a + "_wasted" in recs[0]},
           "model_prior_failure_rate": float(fail.mean()), "model_prior_failures": int(fail.sum())}
    rec_rate = {}
    for a in ("maestro", "b_lookahead", "b_exploit", "b_panel", "match_panel", "knn", "llm"):
        if a in recs[0] and fail.any():
            rec_rate[a] = float(np.mean([r[a] >= r["item"] for r, f in zip(recs, fail) if f]))
    out["recovery_rate_given_prior_failure"] = rec_rate
    bm = np.array([r.get("bridge_measured", np.nan) for r in recs], float)
    if np.isfinite(bm).any():
        out["subtask_lookahead_bridge_wells_measured"] = float(np.nanmean(bm) / max(k_bridge, 1))
        out["subtask_contexts_with_any_bridge_readout"] = float(np.nanmean(bm > 0))
    if "llm" in recs[0]:
        codes = [r.get("llm_refusal") for r in recs]
        out["planning_llm_invalid_selection"] = int(sum(c == "llm_invalid_selection" for c in codes))
        out["tool_llm_protocol_error"] = int(sum(c == "llm_protocol_error" for c in codes))
        out["subtask_llm_valid_selection"] = float(np.mean([c is None for c in codes]))
    return out


def misfit_auroc(recs):
    y = np.array([r["vc0"] < r["item"] for r in recs])
    s = np.array([r.get("misfit", np.nan) for r in recs], float)
    ok = np.isfinite(s)
    y, s = y[ok], s[ok]
    if y.sum() == 0 or (~y).sum() == 0:
        return None
    from scipy.stats import rankdata
    rk = rankdata(s)
    return float((rk[y].sum() - y.sum() * (y.sum() + 1) / 2) / (y.sum() * (~y).sum()))


if __name__ == "__main__":
    main()
