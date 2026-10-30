# -*- coding: utf-8 -*-
"""Run deterministic contract corrections and key math audits.

No model execution, no training of the old config, no real data.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import contract as C  # noqa: E402

ROOT = HERE.parent
M3_JSON = ROOT / "2026-10-28-m3-stage3-run" / "m3_stage3.json"
CORR_JSON = ROOT / "parallel-coordination" / "root-corrections-20261028" / "saved_result_corrections.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def recompute_m3_family(m3: dict) -> dict:
    arms = {a["arm_id"]: np.asarray(a["per_replicate_regret"], dtype=float) for a in m3["per_arm"]}
    cand = "A_candidate_score_tilt"
    baselines = {k: v for k, v in arms.items() if k != cand}
    fam = C.six_comparison_family(arms[cand], baselines, delta=0.05)
    return {"candidate": cand, "family": fam, "n": int(arms[cand].size)}


def main() -> None:
    t0 = time.time()
    m3 = json.loads(M3_JSON.read_text(encoding="utf8"))
    corr = json.loads(CORR_JSON.read_text(encoding="utf8"))

    result = {
        "scope": "deterministic contract tests + saved-data reanalysis; no model execution/training; old frozen outputs retained",
        "frozen_outputs_retained": {
            "m3_stage3_verdict": m3.get("verdict"),
            "m3_stage3_sha256": sha256(M3_JSON),
            "m1_c216_unchanged": "design_invalid: projection; H1 0/16",
            "invalid_run_90DE7498_not_reused": True,
        },
        "contract": {
            "comparison": "D_j = R_candidate - R_baseline_j for all 6 baselines including standard; unified Holm; improvement direction D<0; one-sided lower-tail p.",
            "headroom": "maximum possible mean improvement on an evaluated batch = mean baseline regret (regret>=0); NOT 1-regret.",
            "propensity": "if feedback is sampled by w, H must use actual behaviour probability w (and joint density ratio if background changed); DR identity checked in finite env.",
            "learner": "candidate must fit preregistered logit-fluctuation epsilon by the stated loss/optimizer with explicit convergence; sigmoid transform alone is not TMLE.",
            "equivalence": "arms must be checked for identical policies/monotone transforms/affine reparameterisation before being counted as independent methods.",
            "separation": "generator truth, training feedback, validation data and final evaluator must be isolated; raw regret and paired D stored separately; CI from independent repeats, not planning MDE.",
        },
        "gate_cases": {},
        "m3_reanalysis": {},
        "headroom_audit": {},
        "propensity_check": {},
        "learner_check": {},
        "equivalence_audit": {},
        "input_sha256": {},
    }

    # 1) gate deterministic cases
    base10 = np.full(10, 0.10)
    result["gate_cases"]["strong_improvement"] = C.success_gate(np.zeros(10) - base10)
    result["gate_cases"]["no_improvement"] = C.success_gate(np.full(10, 0.10) - base10)
    result["gate_cases"]["worse"] = C.success_gate(np.full(10, 0.12) - base10)

    # 2) six-comparison family (candidate vs all baselines incl standard)
    base = {f"b{i}": np.full(10, 0.10) for i in range(5)}
    base["standard"] = np.full(10, 0.10)
    fam_case = C.six_comparison_family(np.full(10, 0.02), base)
    result["gate_cases"]["six_family_strong"] = {
        "rows": {k: {"mean": v["mean_DeltaR"], "p_holm": v["p_holm"], "pass": v["pass"]}
                 for k, v in fam_case["rows"].items()},
        "all_pass": all(v["pass"] for v in fam_case["rows"].values()),
        "includes_standard": "standard" in fam_case["rows"],
    }

    # 3) M3 saved-data reanalysis (paired D from per-arm arrays vs frozen output)
    re = recompute_m3_family(m3)
    result["m3_reanalysis"] = {
        "n_independent_replicates": re["n"],
        "rows": re["family"]["rows"],
        "original_frozen_primary": m3.get("primary"),
        "original_frozen_verdict": m3.get("verdict"),
        "comparison_to_corrections_reference": corr.get("corrected_candidate_comparison_family"),
        "note": "reanalysis uses saved per-arm D arrays (D_arm = R_arm - R_standard); raw R vectors were not persisted; this audit does not replace the frozen analysis.",
    }

    # 4) headroom audit
    saved_headroom = float(m3.get("headroom_mde", {}).get("headroom", float("nan")))
    baseline_regret_inferred = 1.0 - saved_headroom
    hg = C.headroom_gate(np.full(10, baseline_regret_inferred), delta=0.05)
    result["headroom_audit"] = {
        "saved_headroom_value": saved_headroom,
        "baseline_regret_inferred": baseline_regret_inferred,
        "max_possible_mean_improvement": hg["max_possible_mean_improvement"],
        "delta": hg["delta"],
        "delta_feasible_on_saved_batch": hg["delta_feasible"],
        "note": "0.0203 is inferred from saved headroom and source definition; raw baseline R is not persisted. This batch cannot meet mean<=-0.05 even at zero regret.",
    }

    # 5) propensity/DR finite-env check (constructed, exact algebra; plus saved reference values)
    b_old = np.asarray(corr["propensity_exact_check"]["original_b"], dtype=float)
    w = np.asarray(corr["propensity_exact_check"]["actual_w"], dtype=float)
    pi2 = w.copy()
    m0 = np.zeros((3, 3))
    y = np.full(3, corr["propensity_exact_check"]["target_value"])
    a_obs = np.array([0, 1, 2])
    dr_correct = C.dr_estimator(pi2, w, m0, y, a_obs)
    dr_old = C.dr_estimator(pi2, b_old, m0, y, a_obs)
    result["propensity_check"] = {
        "target_value_constructed": float(np.mean(y)),
        "dr_with_actual_w": dr_correct,
        "dr_with_old_b": dr_old,
        "bias_with_old_b": dr_old - float(np.mean(y)),
        "identity_gap_with_actual_w": C.dr_identity_gap(pi2, w, m0, y, a_obs),
        "saved_published_values": corr["propensity_exact_check"],
        "note": "constructed finite-env identity (pi2=w, m=0, y=const); the saved published numbers come from the original nine-cell tables and are printed for reference, not recomputed here.",
    }

    # 6) learner contract finite check
    rng = np.random.default_rng(11)
    n, A = 400, 3
    logits = rng.normal(size=(n, A))
    H = rng.normal(size=(n, A))
    eps_true = 0.7
    p = C.softmax_rows(logits + eps_true * H)
    a = np.array([rng.choice(A, p=p[i]) for i in range(n)])
    fit = C.logit_fluctuation_fit(logits, H, a)
    result["learner_check"] = {
        "true_epsilon": eps_true,
        "fit": fit,
        "note": "finite synthetic check that a real NLL + L-BFGS fit of the preregistered epsilon recovers the parameter with a small score residual; not a model effect.",
    }

    # 7) equivalence audit (disclosed implementations)
    s = rng.normal(size=(30, 4))
    cand_scores = 0.5 + 0.5 * s
    tmle_like = 1.0 / (1.0 + np.exp(-2.0 * s))
    empirical = np.zeros_like(s)  # same value per action; argmax action 0 for all h
    affine_va = 2.0 * empirical + 1.0
    result["equivalence_audit"] = {
        "candidate_vs_tmle_like_same_decisions": C.decisions_equivalent(cand_scores, tmle_like),
        "candidate_vs_tmle_like_affine": C.affine_equivalent(cand_scores, tmle_like),
        "standard_vs_empirical_same": C.decisions_equivalent(empirical, empirical),
        "value_aware_affine_of_standard": C.affine_equivalent(empirical, affine_va),
        "disclosed_equivalences": {
            "candidate": "0.5 + 0.5*score (no epsilon fit)",
            "A_TMLE_targeting": "sigmoid(2*score) (no target-score/NLL solve)",
            "A_full_history_retrain": "empirical per-cell mean",
            "A_standard_DR_TMLE": "empirical per-cell mean",
            "A_importance_weighting": "weighted mean; with fixed H per cell reduces to same mean",
            "A_value_aware": "positive affine transform of the same mean; same argmax",
            "conclusion": "six arms are not six independent strong algorithms; candidate and TMLE-like are monotone transforms of the same score; full-history/standard/IW collapse to the same empirical mean; value-aware is an affine transform.",
        },
    }

    # 8) input SHAs
    for p in [M3_JSON, CORR_JSON, HERE / "contract.py", HERE / "test_contract.py"]:
        result["input_sha256"][str(p.relative_to(ROOT))] = sha256(p)

    result["verdict"] = {
        "scientific_judgment_changes": [
            "M3 Stage3 frozen no_increment is retained but its interpretation as a qualified M3/TMLE comparison is set aside: comparison family/Holm map, one-sided lower-tail direction, headroom definition, propensity denominator and learner contract are corrected here.",
            "M1 C216 stands (H1 0/16, design_invalid: projection); the C217 'estimation_limit_unreachable' wording is retracted: q95 is not an impossibility bound, oracle q95>=tol is 15/16 (multinomial 16/16), 12/16 tolerances below oracle q05 indicate sampling/tolerance mismatch, model fitting error is not excluded.",
            "Invalid run 90DE7498 (C215) remains invalid and is not cited.",
        ],
        "retained_failures": ["M3 Stage3 frozen no_increment (interpretation qualified)", "M1 frozen H1 0/16 (C216)", "C215 invalid run"],
        "open_question": "Does the corrected learner with a real logit-fluctuation fit and actual behaviour probabilities show any gain over an analytically matching standard estimator once equivalent arms are deduplicated and headroom exceeds delta?",
    }
    result["wall_seconds"] = time.time() - t0

    (HERE / "corrections_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf8")
    print("wrote corrections_result.json")
    print("gate cases:", {k: v.get("gate_pass") for k, v in result["gate_cases"].items() if isinstance(v, dict)})
    print("m3 family:", {k: (round(v["mean_DeltaR"], 5), round(v["p_one_sided_lower"], 5), round(v["p_holm"], 5)) for k, v in result["m3_reanalysis"]["rows"].items()})
    print("headroom:", result["headroom_audit"]["max_possible_mean_improvement"], "feasible:", result["headroom_audit"]["delta_feasible_on_saved_batch"])
    print("propensity:", result["propensity_check"]["dr_with_actual_w"], result["propensity_check"]["dr_with_old_b"], "gap", result["propensity_check"]["identity_gap_with_actual_w"])
    print("learner:", result["learner_check"]["fit"])


if __name__ == "__main__":
    main()
