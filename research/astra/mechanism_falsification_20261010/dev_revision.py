"""Development run of the open-world test (H6) on the open tier.

H0 = the library: classes with reference drugs. Every development drug runs a falsification episode
against H0 alone (falsify design, budget B, no early stop). Outcomes per stratum (query class in the
library or outside it): HYPOTHESIS_SET_EXHAUSTED rate and final set size. For out-of-library
queries whose library set is exhausted, revision proposals are drawn from the classes outside the
library:

* compiled: the five outside classes with the largest conformal p-value on the same observations
  (agent hypotheses compiled by the knowledge compiler);
* compiled_permuted: the same with EMHs permuted across classes (control);
* agent (optional, --agent): the LLM reads the observations and proposes five classes;
* random: expected success of five uniform draws, times the true class's survival.

Success = the true class is proposed and its p-value exceeds alpha on the same observations.
Usage: python dev_revision.py <name> [config json] --budget 3 [--agent]
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

import agent_arms as AA
import dev_agent as DA
import revision as RV
import study as S

HERE = Path(__file__).resolve().parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("config", nargs="?", default="{}")
    ap.add_argument("--budget", type=int, default=3)
    ap.add_argument("--agent", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    data = S.load_tier("open")
    cfg = S.Config(**json.loads(a.config))
    b = S.build(data, cfg)
    fz = S.falsifier(b)
    bp = S.build(data, replace(cfg, permute_emh=True))
    fzp = S.falsifier(bp)
    library = np.array([i for i, m in enumerate(b.models) if m.kind != "knowledge"])
    outside = np.array([i for i, m in enumerate(b.models) if m.kind == "knowledge"])
    lib_names = set(fz.names[library])
    arms = AA.AgentArms(sorted(fz.names), data["genes"], data["options"], DA.noise_hint(data)) if a.agent else None
    q = np.where(data["role"] == "development")[0]
    rows = []
    for qi in q:
        true = str(data["moa"][qi])
        avail = S.available(data, qi)
        ep = RV.library_episode(fz, b.Z_open[qi], avail, library, a.budget, seed=int(cfg.seed + qi))
        row = {"drug": str(data["drug"][qi]), "moa": true, "in_library": true in lib_names, "status": ep.status,
               "observed": [data["options"][o] for o in ep.observed], "final_set": len(ep.surviving[-1]) if ep.surviving else None}
        if not row["in_library"]:
            prop, p = RV.compiled_ranking(fz, b.Z_open[qi], ep.observed, outside)
            ti = int(np.where(fz.names[outside] == true)[0][0])
            row["p_true_outside"] = float(p[ti])
            row["n_outside_surviving"] = int((p > fz.alpha).sum())
            row["compiled"] = prop
            row["compiled_success"] = bool(true in prop and p[ti] > fz.alpha)
            row["rank_true_compiled"] = float((p > p[ti]).sum() + ((p == p[ti]).sum() + 1) / 2)  # mid-rank over ties
            propp, pp = RV.compiled_ranking(fzp, bp.Z_open[qi], ep.observed, outside)
            tip = int(np.where(fzp.names[outside] == true)[0][0])
            row["compiled_permuted_success"] = bool(true in propp and pp[tip] > fzp.alpha)
            row["random_success_expected"] = float(min(5, len(outside)) / len(outside) * (p[ti] > fz.alpha))
            if arms is not None and ep.status == "HYPOTHESIS_SET_EXHAUSTED":
                zg = {o: data["x"][qi, o] for o in ep.observed}
                prop_a, meta = arms.revise(str(qi), zg, ep.observed, sorted(lib_names))
                row["agent"] = prop_a
                row["agent_success"] = bool(true in prop_a and p[ti] > fz.alpha)
                row["agent_meta"] = {"status": meta["status"], "dropped_names": meta["dropped_names"]}
        rows.append(row)
    summ = {}
    for key, rs in (("in_library", [r for r in rows if r["in_library"]]), ("outside", [r for r in rows if not r["in_library"]])):
        summ[key] = {"n": len(rs), "exhausted": float(np.mean([r["status"] == "HYPOTHESIS_SET_EXHAUSTED" for r in rs])),
                     "mean_final_set": float(np.mean([r["final_set"] for r in rs if r["final_set"] is not None]))}
    out_rows = [r for r in rows if not r["in_library"]]
    ex = [r for r in out_rows if r["status"] == "HYPOTHESIS_SET_EXHAUSTED"]
    for name, rs in (("all_outside", out_rows), ("exhausted_outside", ex)):
        if not rs:
            continue
        s = {"n": len(rs), "compiled": float(np.mean([r["compiled_success"] for r in rs])),
             "compiled_permuted": float(np.mean([r["compiled_permuted_success"] for r in rs])),
             "random_expected": float(np.mean([r["random_success_expected"] for r in rs])),
             "true_survives_outside": float(np.mean([r["p_true_outside"] > fz.alpha for r in rs])),
             "median_rank_true": float(np.median([r["rank_true_compiled"] for r in rs]))}
        ag = [r for r in rs if "agent_success" in r]
        if ag:
            s["agent"] = float(np.mean([r["agent_success"] for r in ag]))
            s["agent_n"] = len(ag)
        summ[name] = s
    res = {"name": a.name, "config": asdict(cfg), "budget": a.budget, "n_library": int(len(library)),
           "n_outside": int(len(outside)), "summary": summ, "seconds": round(time.time() - t0, 1),
           "ledger_total_usd": round(arms.ledger.total_usd, 4) if arms else None, "rows": rows}
    (HERE / "development" / f"{a.name}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
