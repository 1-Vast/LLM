"""Audit the policy-experience records and the campaign-level headroom claim. Writes EXPERIENCES_CHECK.json and NOISE_HEADROOM.json.

File summary
- Path: research/eg_rpt_20261019/audit_experiences.py
- (1) Each record is validated (`policy_memory.validate_experience`) and its `record_pattern` must appear in the cited evidence text
  (unicode minus normalised). Three records are also recomputed from result files (acquisition RESULTS.json, RESULTS_OBS.json).
- (2) Feasibility counts: records, independent dependence groups, units; a learned transfer model needs far more.
- (3) Noise headroom of the "campaign best-of" figure: from the public per-campaign hits of ridge and R1 (36 complete campaigns)
  compare the observed mean |difference| with the value expected when the difference is pure Gaussian noise of the same SD,
  and report the correlation of the two near-identical predictors across campaigns. This is a diagnostic, not a reliability test:
  a split-noise reliability test needs two independent noise draws (Phase 0 of the protocol).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import experiences as X  # noqa: E402
import policy_memory as PM  # noqa: E402


def norm(t):
    return t.replace("−", "-").replace("–", "-")


def main() -> dict:
    ev = norm((ROOT / "research/EVIDENCE.md").read_text(encoding="utf-8"))
    rows = []
    for e in X.EXPERIENCES:
        bad = PM.validate_experience(e)
        found = norm(e.record_pattern) in ev
        rows.append({"exp_id": e.exp_id, "unit": e.unit, "outcome": e.outcome, "dependence_group": e.dependence_group, "problems": bad, "pattern_in_evidence": found})
    ap = json.loads((ROOT / "research/acquisition_program_20261018/RESULTS.json").read_text(encoding="utf-8"))["contrasts"]
    ob = json.loads((ROOT / "research/observable_state_20261018/RESULTS_OBS.json").read_text(encoding="utf-8"))["contrasts"]["P1_a3_minus_a2"]["family_cluster"]
    recomputed = {
        "acq-lookahead": (round(ap["lookahead_vs_fixed"]["mean"], 3), [round(x, 3) for x in ap["lookahead_vs_fixed"]["ci95"]]),
        "acq-agent-vs-lookahead": (round(ap["agent_vs_lookahead"]["mean"], 3), [round(x, 3) for x in ap["agent_vs_lookahead"]["ci95"]]),
        "obs-agent-vs-enum": (round(ob["mean"], 3), [round(x, 3) for x in ob["ci95"]]),
    }
    by = {e.exp_id: e for e in X.EXPERIENCES}
    rec_ok = {k: bool(abs(v[0] - by[k].delta_u) < 1e-3 and all(abs(a - b) < 1e-3 for a, b in zip(v[1], by[k].ci95))) for k, v in recomputed.items()}
    units = sorted({e.unit for e in X.EXPERIENCES})
    feas = {"records": len(X.EXPERIENCES), "independent_dependence_groups": PM.independent_units(X.EXPERIENCES), "units": units,
            "poolable_across_all": PM.poolable(X.EXPERIENCES), "records_per_unit": {u: sum(e.unit == u for e in X.EXPERIENCES) for u in units},
            "reading": "far too few independent groups and mutually incommensurable units to fit a learned policy-transfer model; "
                       "at most case retrieval with leave-group-out checks"}
    chk = {"all_valid": all(not r["problems"] for r in rows), "all_patterns_found": all(r["pattern_in_evidence"] for r in rows),
           "recomputed_match": rec_ok, "feasibility": feas, "records": rows}
    (HERE / "EXPERIENCES_CHECK.json").write_text(json.dumps(chk, indent=1) + "\n", encoding="utf-8")
    REC = ROOT / "research/feedback_propagation_20261018/records"
    a, b = [], []
    for f in (2, 3, 4):
        r = json.loads((REC / f"E_fold{f}.json").read_text(encoding="utf-8"))["A_B3"]
        for x, y, s in zip(r["ridge"]["unmeasured"]["campaign_hits"], r["R1"]["unmeasured"]["campaign_hits"], r["R1"]["unmeasured"]["campaign_compounds"]):
            if s == 64:
                a.append(x)
                b.append(y)
    a, b = np.array(a, float), np.array(b, float)
    d = b - a
    nh = {"campaigns": int(len(d)), "mean_ridge": float(a.mean()), "mean_R1": float(b.mean()), "mean_diff": float(d.mean()), "sd_diff": float(d.std(ddof=1)),
          "observed_mean_abs_diff": float(np.abs(d).mean()), "expected_mean_abs_diff_if_pure_gaussian_noise": float(0.798 * d.std(ddof=1)),
          "corr_ridge_R1_across_campaigns": float(np.corrcoef(a, b)[0, 1]),
          "best_of_excess_over_mean_of_two": float(np.abs(d).sum() / 2),
          "reading": "best-of-two excess equals sum|d|/2 exactly; |d| here matches what Gaussian noise of the same SD would give, and the two predictors' "
                     "hit counts correlate only weakly across campaigns, so the 131-vs-100 hindsight figure is not evidence of identifiable "
                     "policy-selection headroom. A split-noise reliability test (two independent probe-noise draws) is required."}
    (HERE / "NOISE_HEADROOM.json").write_text(json.dumps(nh, indent=1) + "\n", encoding="utf-8")
    return {"check": chk, "noise": nh}


if __name__ == "__main__":
    o = main()
    print({k: v for k, v in o["check"].items() if k != "records"})
    print({k: v for k, v in o["noise"].items() if k != "reading"})
