"""Executable worked example (synthetic): two competing explanations, the same prospective probe, two feedback outcomes, different posterior support and
downstream decisions. Also shows an unresolved mismatch. Output: WORKED_EXAMPLE.json. Not biological evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import iv_core as C  # noqa: E402
from iv_gates import Gate  # noqa: E402

N = 12
NAMES = [f"pair{k:02d}" for k in range(N)]
BASE = np.array([0.80, 0.79, 0.78, 0.77, 0.76, 0.75, 0.74, 0.73, 0.72, 0.71, 0.70, 0.69])        # prior-ranked activity (A_ref + z1)
SIGMA = 0.02
DECOY = 10                                                                                      # a noisy pair that no explanation speaks about
DIAG = 11                                                                                       # the pair on which the two explanations disagree


def comp(pid, effect, w, extra_var=None):
    mu = np.zeros(N)
    for k, v in effect.items():
        mu[k] = v
    var = np.full(N, SIGMA ** 2)
    var[DECOY] = 0.08 ** 2                                                                       # large variance everywhere at the decoy
    if extra_var:
        var = var * extra_var
    return {"prog": pid, "mean": mu, "var": var, "logw": np.log(w), "Vz": None}


def build():
    """Hypotheses given what the first measurement showed (an anomaly: pair08 is raised by about +0.10):
       A kinase-axis gate ON : raises pair07 and pair08 by 0.12 and the diagnostic pair11 by 0.15
       B transport gate ON   : raises pair08 and pair09 by 0.10 and leaves pair11 unchanged
       N null                : nothing is raised (the anomaly would be noise);  U unexplained: wide variance everywhere."""
    comps = [comp("A_kinase_axis", {7: 0.12, 8: 0.12, DIAG: 0.15}, 0.3), comp("B_transport", {8: 0.10, 9: 0.10}, 0.3), comp("N_null", {}, 0.3),
             comp("U_unexplained", {}, 0.1, extra_var=16.0)]
    bel = C.Belief(BASE.copy(), comps)
    bel.observe(8, 0.10)                                                                         # the anomaly that both explanations account for
    return bel


def run(outcome_label, y_diag):
    bel = build()
    pool = np.ones(N, bool)
    rng = np.random.default_rng(0)
    legal = np.zeros(N, bool)
    legal[[DECOY, DIAG]] = True                                                                  # only these two measurements are available
    recorded = {8: BASE[8] + 0.10}
    p, rec = C.pick("kg", bel, legal, pool, recorded, rng, np.arange(N) // 3)
    before = {"program_weights_after_anomaly": {k: round(v, 4) for k, v in rec["program_weights"].items()}, "probe": NAMES[p], "kg_score": rec["kg_score"],
              "competing_predictions_for_probe": {k: {a: round(b, 4) for a, b in v.items()} for k, v in rec["competing_predictions_for_probe"].items()},
              "alternatives": [{"pair": NAMES[a["pair"]], "kg": a["kg"]} for a in rec["alternatives"]],
              "nominations_that_could_change": [NAMES[q] for q in rec["nominations_that_could_change"]], "current_shortlist": [NAMES[q] for q in rec["current_shortlist"]]}
    var_pick = int(np.nonzero(legal)[0][np.argmax(bel.mixture()[1][legal])])
    bel.observe(p, y_diag - BASE[p])
    pw = bel.program_weights()
    mean, _ = bel.mixture()
    score = BASE + mean
    score[8], score[p] = recorded[8], y_diag
    nom = C.top_k(score)
    # the baseline that probes the highest-variance legal pair instead
    bel2 = build()
    bel2.observe(var_pick, 0.0)
    pw2 = bel2.program_weights()
    return {"outcome": outcome_label, "observed_value_at_probe": round(float(y_diag), 4), "before_probe": before,
            "variance_only_rule_would_probe": NAMES[var_pick], "weights_if_variance_probe_taken": {k: round(v, 4) for k, v in pw2.items()},
            "after_probe": {"program_weights": {k: round(v, 4) for k, v in pw.items()}, "unresolved_mismatch": bool(pw.get("U_unexplained", 0) > 0.5),
                            "nominated": [NAMES[q] for q in nom]}}


def main():
    out = {"note": "synthetic illustration of the update rule and the decision consequence; no biological claim",
           "same_probe_two_outcomes": [run("A is right (probe raised)", BASE[DIAG] + 0.15), run("B is right (probe unchanged)", BASE[DIAG] + 0.0)],
           "unresolved_mismatch": run("neither explains it (probe fell)", BASE[DIAG] - 0.25)}
    a, b = out["same_probe_two_outcomes"]
    pa, pb = a["after_probe"]["program_weights"], b["after_probe"]["program_weights"]
    out["checks"] = {"same_probe": a["before_probe"]["probe"] == b["before_probe"]["probe"] == NAMES[DIAG],
                     "variance_only_probe_is_the_decoy": a["variance_only_rule_would_probe"] == NAMES[DECOY],
                     "A_support_after_A_outcome": pa.get("A_kinase_axis", 0), "A_support_after_B_outcome": pb.get("A_kinase_axis", 0),
                     "B_support_after_B_outcome": pb.get("B_transport", 0), "posterior_differs": pa != pb,
                     "decisions_differ": a["after_probe"]["nominated"] != b["after_probe"]["nominated"],
                     "mismatch_flagged": out["unresolved_mismatch"]["after_probe"]["unresolved_mismatch"],
                     "variance_probe_leaves_posterior_unchanged": max(abs(a["weights_if_variance_probe_taken"][k] - a["before_probe"]["program_weights_after_anomaly"][k]) for k in a["weights_if_variance_probe_taken"]) < 0.08}
    (HERE / "WORKED_EXAMPLE.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps(out["checks"], indent=1))
    return out


if __name__ == "__main__":
    main()
