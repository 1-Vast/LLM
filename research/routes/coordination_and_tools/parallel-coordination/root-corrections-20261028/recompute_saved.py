"""Audit saved records and exact finite expectations; never run research models."""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
RUN = ROOT / "research/2026-10-28-m3-stage3-run"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def summarize(values):
    values = np.asarray(values, dtype=float)
    mean = float(values.mean())
    se = float(values.std(ddof=1) / np.sqrt(len(values)))
    radius = float(stats.t.ppf(0.975, len(values) - 1)) * se
    p = float(stats.t.cdf(mean / se, len(values) - 1)) if se else (0.0 if mean < 0 else 1.0)
    return {"mean_DeltaR": mean, "CI95_t": [mean - radius, mean + radius],
            "SE": se, "p_one_sided_t": p, "n_clusters": len(values)}


def main():
    saved = read(RUN / "m3_stage3.json")
    arms = {a["arm_id"]: a for a in saved["per_arm"]}
    candidate = "A_candidate_score_tilt"
    # This field holds R_arm-R_standard, despite its saved name.
    offsets = {k: np.asarray(v["per_replicate_regret"], dtype=float) for k, v in arms.items()}
    comparisons = [{"baseline": k, **summarize(offsets[candidate] - offsets[k])}
                   for k in arms if k != candidate]
    order = sorted(range(len(comparisons)), key=lambda i: comparisons[i]["p_one_sided_t"])
    previous = 0.0
    for rank, i in enumerate(order):
        previous = max(previous, min(1.0, (len(order) - rank) * comparisons[i]["p_one_sided_t"]))
        comparisons[i]["p_holm"] = previous
    baseline_regret = 1.0 - saved["headroom_mde"]["headroom"]
    env = saved["environment"]
    pop, mu, pi, old_b = [np.asarray(env[k], dtype=float) for k in ("p_h", "mu", "pi_2", "b")]
    m = np.asarray(env["m_wrong"], dtype=float)
    unnormalized = pop[:, None] * pi ** 2 * (mu * (1 - mu) + (mu - m) ** 2) / old_b
    actual_w = unnormalized / unnormalized.sum(axis=1, keepdims=True)
    target = float(np.sum(pop[:, None] * pi * mu))
    base = float(np.sum(pop[:, None] * pi * m))
    wrong = base + float(np.sum(pop[:, None] * actual_w * (pi / old_b) * (mu - m)))
    correct = base + float(np.sum(pop[:, None] * actual_w * (pi / actual_w) * (mu - m)))
    diag = read(ROOT / "research/2026-10-28-m1-stage2-fail-diag/diag_m1_s2.json")
    m1 = read(ROOT / "research/2026-10-28-m1-stage2-rerun/m1_stage2_rerun.json")
    a = read(ROOT / "research/2026-10-28-agent-a-program-evidence/verification_v1.json")
    files = [RUN / "m3_stage3.json", RUN / "run_m3_stage3.py",
             ROOT / "research/2026-10-28-m1-stage2-fail-diag/diag_m1_s2.json",
             ROOT / "research/2026-10-28-m1-stage2-rerun/m1_stage2_rerun.json",
             ROOT / "research/2026-10-28-agent-a-program-evidence/verification_v1.json"]
    result = {
        "scope": "Saved-data reanalysis and exact nine-cell expectation arithmetic; no model execution or training.",
        "original_m3_verdict_preserved": saved["verdict"],
        "p_value_direction_audit": "Original one_sided_p uses upper-tail erfc(t/sqrt(2)); improvement D<0 requires lower tail. Reanalysis below uses t.cdf.",
        "corrected_candidate_comparison_family": comparisons,
        "saved_per_replicate_regret_semantics": "Actually D_arm=R_arm-R_standard; raw baseline vectors were not persisted here.",
        "headroom": {"saved_wrong_value": saved["headroom_mde"]["headroom"],
                     "baseline_regret_inferred_from_saved_value_and_source": baseline_regret,
                     "maximum_improvement_on_this_evaluation_batch": baseline_regret,
                     "delta": saved["primary"]["delta"],
                     "frozen_mean_gain_gate_unreachable_on_saved_batch": baseline_regret < saved["primary"]["delta"]},
        "propensity_exact_check": {"original_b": old_b.tolist(), "actual_w": actual_w.tolist(),
                                   "target_value": target, "DR_using_old_b": wrong,
                                   "bias_using_old_b": wrong - target,
                                   "DR_using_actual_w": correct, "correct_identity_gap": correct - target,
                                   "note": "The executed learner is not an exact DR estimator; this checks its claimed H against the actual sampling law."},
        "m1": {"corrected_run_verdict": m1["verdict"], "H1_pass": sum(r["pass"] for r in m1["H1"]),
               "A_snapshot_hash": a["M1"]["sha256"],
               "snapshot_is_invalid_C215": a["M1"]["sha256"].upper() == m1["previous_invalid_run"]["sha256"],
               "oracle_q95_ge_tolerance": sum(r["oracle_true_vs_true_TV"]["q95"] >= r["tolerance"] for r in diag["rows"]),
               "multinomial_q95_ge_tolerance": sum(r["floor_MC_TV"]["q95"] >= r["tolerance"] for r in diag["rows"]),
               "tolerance_below_oracle_q05": sum(r["tolerance"] < r["oracle_true_vs_true_TV"]["q05"] for r in diag["rows"]),
               "fidelity_abs_delta_above_005": sum(abs(r["delta_TV"]) > 0.005 for r in diag["fidelity_check"])},
        "source_snapshot": [{"path": p.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in files],
        "interpretation": "Keep frozen outputs. The M3 run does not implement the claimed targeting contract and contains an unreachable gain gate and comparison-map error. M1 failed its frozen gate, but q95 is not an impossibility lower bound."
    }
    assert len(comparisons) == 6
    assert abs(result["propensity_exact_check"]["correct_identity_gap"]) < 1e-12
    primary = next(c for c in comparisons if c["baseline"] == "A_standard_DR_TMLE")
    assert abs(primary["mean_DeltaR"] - saved["primary"]["mean_DeltaR"]) < 1e-12
    (OUT / "saved_result_corrections.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"headroom": result["headroom"], "propensity_exact_check": result["propensity_exact_check"],
                      "m1": result["m1"], "comparisons": comparisons}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
