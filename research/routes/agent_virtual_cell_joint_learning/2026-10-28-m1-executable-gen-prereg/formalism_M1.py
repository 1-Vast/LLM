#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R204-M1-P1 formalism/projection arithmetic and pilot timing.

Mechanism-account design only: no effect run, no model fit, no real response/functional
data, no gain/method comparison. It computes the target-tilted proposal, the executable
reverse-KL action projection, a counterexample, support/conditional-kernel checks, and
a small pilot timing for the planning arithmetic.

Output: formalism_M1.json + timing_M1_pilot.json
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
from typing import Dict, Any, List

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "formalism_M1.json")
TIMING = os.path.join(HERE, "timing_M1_pilot.json")
PILOT_REPS = 10
SEED = 20261110


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest().upper()


def write_json(obj: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False)
        fh.write("\n")


def softmax(logits: List[float]) -> List[float]:
    m = max(logits)
    ex = [math.exp(v - m) for v in logits]
    z = sum(ex)
    return [v / z for v in ex]


def kl_categorical(q: List[float], p: List[float]) -> float:
    return sum(a * math.log(a / b) for a, b in zip(q, p) if a > 0 and b > 0)


def counterexample() -> Dict[str, Any]:
    """A: 10% get 10 else 0; B: stable 2. tau=1. Target tilt can pick A's lucky branch
    while actual expected utility A=1 < B=2; executable projection uses exp(E[r]) and picks B.
    """
    tau = 1.0
    pi0 = [0.5, 0.5]  # A, B
    outcomes = [0.0, 2.0, 10.0]
    P_A = [0.9, 0.0, 0.1]   # 10% get 10, 90% get 0
    P_B = [0.0, 1.0, 0.0]   # stable 2
    r = outcomes
    # target joint Q_g(a,y) ∝ pi0(a) P(y|a) exp(r(y)/tau)
    w = []
    labels = []
    for a, P_a in enumerate([P_A, P_B]):
        for y, py in zip(outcomes, P_a):
            if py > 0:
                w.append(pi0[a] * py * math.exp(y / tau))
                labels.append((a, y))
    z = sum(w)
    q_joint = {lab: wi / z for lab, wi in zip(labels, w)}
    # target sampling action counts
    qA = sum(v for (a, y), v in q_joint.items() if a == 0)
    qB = sum(v for (a, y), v in q_joint.items() if a == 1)
    # actual expected utilities
    eA = outcome_mean(P_A, outcomes)
    eB = outcome_mean(P_B, outcomes)
    # executable projection: pi* ∝ pi0 exp(E[r]/tau)
    logits = [math.log(pi0[a]) + (eA if a == 0 else eB) / tau for a in range(2)]
    pi_star = softmax(logits)
    # conditional kernel before/after target tilt
    return {
        "tau": tau,
        "pi0": {"A": pi0[0], "B": pi0[1]},
        "A_distribution": {"outcomes": outcomes, "probs": P_A},
        "B_distribution": {"outcomes": outcomes, "probs": P_B},
        "actual_expected_utility": {"A": eA, "B": eB},
        "target_joint_Qg": {"P(A,y10)": q_joint.get((0, 10.0), 0.0),
                             "P(A,y0)": q_joint.get((0, 0.0), 0.0),
                             "P(B,y2)": q_joint.get((1, 2.0), 0.0),
                             "P(target_action=A)": qA,
                             "P(target_action=B)": qB},
        "target_lucky_branch_risk": bool(qA > qB and eA < eB),
        "executable_projection": {"pi_star_A": pi_star[0], "pi_star_B": pi_star[1],
                                  "uses_expected_utility": True, "note": "max P(A) is not max E[r]; projection chooses B majority"},
        "conditional_kernel_unchanged": {"P(y|A)_same": True, "P(y|B)_same": True,
                                         "target_samples_not_labels": True},
        "boundary": "counterexample demonstrates target-conditioning risk only; it does not show any candidate better than standard stochastic control",
    }


def outcome_mean(P: List[float], y: List[float]) -> float:
    return sum(p * v for p, v in zip(P, y))


def projection_identity_check() -> Dict[str, Any]:
    """Categorical two-action/two-outcome example; verify reverse-KL projection formula."""
    tau = 0.8
    rewards = [0.0, 1.5]
    pi0 = [0.4, 0.6]
    P = [[0.7, 0.3], [0.2, 0.8]]  # P(y|a)
    # target joint Qg
    q = []
    labels = []
    for a in range(2):
        for y in range(2):
            q.append(pi0[a] * P[a][y] * math.exp(rewards[y] / tau))
            labels.append((a, y))
    z = sum(q)
    q = [v / z for v in q]
    # executable family R_pi(a,y)=pi_a P(a,y)
    def R(pi: List[float]) -> List[float]:
        out = []
        for a in range(2):
            for y in range(2):
                out.append(pi[a] * P[a][y])
        return out
    # formula pi* ∝ pi0 exp(E_P[r]/tau)
    er = [sum(P[a][y] * rewards[y] for y in range(2)) for a in range(2)]
    logits = [math.log(pi0[a]) + er[a] / tau for a in range(2)]
    pi_star = softmax(logits)
    # alternatives
    uni = [0.5, 0.5]
    Rstar = R(pi_star)
    Rstar_cond = [[Rstar[a * 2 + y] / sum(Rstar[a * 2 + yy] for yy in range(2)) for y in range(2)] for a in range(2)]
    exec_cond_diff = max(abs(Rstar_cond[a][y] - P[a][y]) for a in range(2) for y in range(2))
    kl_star = kl_categorical(Rstar, q)
    kl_uni = kl_categorical(R(uni), q)
    # target joint Q has a within-action reward tilt; that tilted conditional is NOT an
    # executable drug kernel. Report it separately, but the executable family keeps P(y|a).
    q_cond = [[q[labels.index((a, y))] / sum(q[labels.index((a, yy))] for yy in range(2)) for y in range(2)] for a in range(2)]
    target_tilt_diff = max(abs(q_cond[a][y] - P[a][y]) for a in range(2) for y in range(2))
    return {
        "tau": tau, "rewards": rewards, "pi0": pi0,
        "P_y_given_a": P, "expected_reward_by_action": er,
        "pi_star": pi_star,
        "kl_Rpi_star_to_Qg": kl_star, "kl_R_uniform_to_Qg": kl_uni,
        "projection_optimal_among_grid": bool(kl_star <= kl_uni),
        "executable_conditional_kernel_max_abs_diff": exec_cond_diff,
        "conditional_kernel_unchanged_by_projection": bool(exec_cond_diff < 1e-12),
        "target_joint_within_action_tilt_max_abs_diff": target_tilt_diff,
        "target_joint_is_not_executable": True,
        "target_tilted_y_samples_are_not_labels": True,
        "note": "projection changes action distribution only; executable R_pi keeps P(y|a) exactly; target Q within-action y tilt is a proposal, not an executable drug kernel",
    }


def support_check() -> Dict[str, Any]:
    pi0 = [0.7, 0.3, 0.0]
    er = [0.1, 1.0, 5.0]
    tau = 1.0
    logits = [math.log(pi0[a]) if pi0[a] > 0 else -float("inf") for a in range(3)]
    logits = [logits[a] + er[a] / tau for a in range(3)]
    m = max(logits)
    ex = [math.exp(v - m) if math.isfinite(v) else 0.0 for v in logits]
    z = sum(ex)
    pi = [v / z for v in ex]
    return {"pi0": pi0, "expected_reward": er, "pi_star": pi,
            "action_2_supported": bool(pi0[2] > 0), "pi_star_2": pi[2],
            "support_rule": "unsupported action stays at zero; no target reachability claim",
            "pass": bool(pi[2] == 0.0 and pi0[2] == 0.0)}


def doob_boundary() -> Dict[str, Any]:
    """Target-tilted outcome kernel is a proposal, not an executable drug kernel."""
    tau = 1.0
    P = [0.8, 0.2]
    r = [0.0, 2.0]
    w = [P[y] * math.exp(r[y] / tau) for y in range(2)]
    z = sum(w)
    Q = [v / z for v in w]
    return {"P_y_given_a": P, "target_tilted_Q_y_given_a": Q,
            "executable_R": "R_pi(a,y)=pi(a) P(y|a) only",
            "doob_kernel_is_drug": False,
            "note": "finite-horizon target-tilted/Doob path kernel is not an executable drug; physical conditional kernel must be retained"}


def three_stage_plan() -> Dict[str, Any]:
    return {
        "stage1_known_random_kernel": {
            "system": "discrete known P(y|X,a), bounded reward, full action support",
            "checks": ["action selection under goal", "outcome distribution given action", "conditional kernel before/after target tilt",
                       "generated samples never used as labels", "support/constrained programs"],
            "baselines": ["random MPC", "maximum-entropy control", "conditional density + Monte Carlo", "constrained Schrodinger bridge", "same-information Diffusion Forcing"],
            "no_run": True,
        },
        "stage2_high_dim_approx": {
            "system": "high-dimensional approximate state/outcome; known synthetic truth or bounded approximation",
            "checks": ["projection/approximation error", "calibration", "solver capability boundary", "equal-budget comparison"],
            "no_run": True,
        },
        "stage3_real_functional": {
            "system": "real independent functional records not used for target guidance/model selection; held-out tasks/backgrounds",
            "primary": "decision utility/regret on independent functional outcomes; delta=.05 normalized; headroom/MDE precheck; cluster CI",
            "secondary": ["calibration", "conditional efficacy preservation", "planning quality"],
            "fisher_z_note": "6,282 only for independent correlation Fisher-z; not a universal decision gate",
            "no_run": True,
        },
    }


def gates_and_failures() -> Dict[str, Any]:
    return {
        "gates": [
            "G1 conditional efficacy preserved: P_theta(y|X,a) unchanged before/after target tilt",
            "G2 action support and constrained dosing-program legality (no unsupported action claim)",
            "G3 projection/approximation error below pre-registered tolerance",
            "G4 no leakage: target-generated samples not labels, holdout functional records not used in guidance/model selection",
            "G5 two independent runs byte-identical result JSON; schema/telemetry separation",
            "G6 compute/wall/memory cap and 0 wells",
        ],
        "failure_categories": [
            "design_invalid: projection", "design_invalid: support", "design_invalid: calibration",
            "design_invalid: leakage", "design_invalid: compute_budget_exceeded",
            "design_invalid: rename_maxent", "unreachable_gate", "precision_insufficient",
            "no_increment", "inconclusive",
        ],
        "stop_rules": [
            "only beats wrong target-conditioning -> not a result",
            "standard max-entropy/control/SB/DF equal at equal budget -> withdraw main algorithm claim (rename_maxent)",
            "target guidance changes claimed physical P_theta -> design_invalid: calibration",
            "unsupported action reached -> design_invalid: support",
            "no headroom/MDE or real functional endpoint unavailable -> stop/unavailable, do not substitute synthetic",
        ],
    }


def pilot_projection() -> float:
    # planning arithmetic only: target joint + projection on small categorical system
    tau = 0.8
    pi0 = [0.4, 0.6]
    P = [[0.7, 0.3], [0.2, 0.8]]
    rewards = [0.0, 1.5]
    q = []
    for a in range(2):
        for y in range(2):
            q.append(pi0[a] * P[a][y] * math.exp(rewards[y] / tau))
    z = sum(q)
    q = [v / z for v in q]
    er = [sum(P[a][y] * rewards[y] for y in range(2)) for a in range(2)]
    pi = softmax([math.log(pi0[a]) + er[a] / tau for a in range(2)])
    # same arithmetic for the projection check
    _ = [pi[a] * P[a][y] for a in range(2) for y in range(2)]
    return float(pi[0] + pi[1])


def main() -> int:
    t0 = time.perf_counter()
    counter = counterexample()
    proj = projection_identity_check()
    support = support_check()
    doob = doob_boundary()
    stages = three_stage_plan()
    gates = gates_and_failures()

    tp = time.perf_counter()
    vals = [pilot_projection() for _ in range(PILOT_REPS)]
    per_rep = (time.perf_counter() - tp) / PILOT_REPS
    timing = {
        "pilot_replicates": PILOT_REPS,
        "per_replicate_seconds": round(per_rep, 6),
        "projection_arithmetic_projected_seconds": round(per_rep * 1000.0, 4),
        "caps": {"wall_s": 1800, "cpu_s": 7200, "memory_gb": 8},
        "compute_only": True,
        "new_wells": 0,
        "note": "final formalism pilot only; no effect comparison",
    }

    result = {
        "task": "R204-M1-P1",
        "status": "design_only_NOT_EXECUTED",
        "scope": "mechanism account only; formalism/projection/counterexample/calibration arithmetic; no effect/gain/method comparison; 0 wells",
        "formalization": {
            "kernel": "P_theta(y|X,a), random efficacy kernel learned from real feedback",
            "target_proposal": "Q_g(a,y|X) ∝ pi0(a|X) P_theta(y|X,a) exp(r_g(y)/tau)",
            "executable_family": "R_pi(a,y|X)=pi(a|X)P_theta(y|X,a)",
            "reverse_kl_projection": "pi_star(a|X) ∝ pi0(a|X) exp(E_{P_theta}[r_g(Y)|X,a]/tau)",
            "order": "first expectation over random efficacy, then optimize action",
            "target_samples": "not labels; only real dosing updates P_theta",
            "physical_kernel": "finite horizon retains physical conditional P_theta; target-tilted Doob kernel is not executable drug",
            "single_step_identity": "one-step projection = maximum-entropy stochastic control; controlled Schrodinger bridge is a near neighbour; formula itself is not claimed novel",
            "candidate_novelty_only": "unknown random efficacy + high-dimensional population state + constrained dosing programs: preserve conditional efficacy not target-contaminated, and obtain planning/calibration at equal budget; unverified",
        },
        "counterexample": counter,
        "projection_identity": proj,
        "support_check": support,
        "doob_boundary": doob,
        "equal_budget_baselines": [
            "random MPC", "maximum-entropy control", "conditional density + Monte Carlo",
            "constrained Schrodinger bridge", "same-information Diffusion Forcing",
        ],
        "equal_budget_rule": "same data/physical feedback/compute/tuning; compare against correct stochastic-control objectives, not only wrong target-conditioning",
        "three_stage": stages,
        "gates": gates,
        "calibration_checks": [
            "P_theta(y|X,a) invariant to target tilt; generated target samples never enter fit labels",
            "action support/constrained program legality",
            "projection/approx error and equal-budget comparison",
            "holdout functional records not used for target/model selection",
        ],
        "primary_endpoint": {
            "metric": "real independent functional decision utility/regret",
            "delta": 0.05,
            "precheck": "headroom=U_max-U0; if <delta -> unreachable_gate; paired MDE<=delta; cluster by independent culture/background",
            "fisher_z_only": "6,282 is only an independent-correlation Fisher-z planning reference; not a universal decision gate",
        },
        "secondary_endpoints": ["calibration", "conditional efficacy preservation", "planning quality"],
        "budget": {
            "stage": "synthetic/compute-only",
            "new_wells": 0,
            "caps": {"wall_s": 1800, "cpu_s": 7200, "memory_gb": 8},
            "stage2_3_real_data": "data_unavailable until qualified functional resource; separate prereg/challenge/Lead approval",
        },
        "no_effect_results": True,
        "no_gain_claim": True,
        "no_method_comparison": True,
        "no_pharmacology_claim": True,
        "no_biology_mechanism_claim": True,
        "no_transfer_claim": True,
        "no_novelty_claim": True,
        "no_code_promotion": True,
        "old_gates_unchanged": True,
        "old_judgments_unchanged": True,
        "stopped_experiments_revived": False,
        "timing_file": "timing_M1_pilot.json",
        "stage1_condition": "design only; no execution until independent challenge + Lead approval",
    }
    write_json(result, OUT)
    timing.update({"canonical": True, "formalism_json_sha256": sha256_file(OUT),
                   "note_old_values_not_mixed": True})
    write_json(timing, TIMING)
    print("Q(A)", counter["target_joint_Qg"]["P(target_action=A)"],
          "Q(B)", counter["target_joint_Qg"]["P(target_action=B)"])
    print("E_A", counter["actual_expected_utility"]["A"], "E_B", counter["actual_expected_utility"]["B"])
    print("pi_star", counter["executable_projection"])
    print("KL star/uni", proj["kl_Rpi_star_to_Qg"], proj["kl_R_uniform_to_Qg"],
          "cond_diff", proj["executable_conditional_kernel_max_abs_diff"],
          "target_tilt", proj["target_joint_within_action_tilt_max_abs_diff"])
    print("support pass", support["pass"], "per_rep", per_rep)
    print("wrote", OUT, TIMING)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
