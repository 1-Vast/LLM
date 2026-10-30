#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R203-P1 planning arithmetic only.

No effect run, no model fit, no response/functional reading, no outcome data use.
It only computes:
  - success-gate reachability (T1 example),
  - paired power / required independent units per endpoint family,
  - the Fisher-z-only interpretation of 6,282 / 1,573,
  - two-ledger scope and next-study planning constants.

Output: power_scope.json
"""
from __future__ import annotations

import json
import math
import os
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "power_scope.json")
Z80 = 2.8015852181  # z_.975 + z_.80 (two-sided alpha .05, 80% power)
DELTA_DEFAULT = 0.05


def ceil_int(x: float) -> int:
    return int(math.ceil(x - 1e-12))


def reachability(p0: float, delta: float, n_units: int, upper: float = 1.0) -> Dict[str, Any]:
    max_gain = upper - p0
    required_successes = ceil_int(n_units * (p0 + delta))
    reachable = (delta <= max_gain + 1e-15) and (required_successes <= n_units)
    return {
        "p0_baseline": p0,
        "upper": upper,
        "delta": delta,
        "n_units": n_units,
        "max_gain": round(max_gain, 10),
        "required_successes": required_successes,
        "required_fraction": round((p0 + delta), 10),
        "reachable": reachable,
        "reason": "reachable" if reachable else (
            "delta exceeds ceiling headroom" if delta > max_gain + 1e-15 else
            "required successes exceed available units"
        ),
    }


def paired_cont_n(sd_d: float, delta: float, icc: float = 0.0, cluster_size: int = 1) -> Dict[str, Any]:
    n_ind = ceil_int((Z80 * sd_d / delta) ** 2)
    de = 1.0 + (cluster_size - 1) * icc if cluster_size > 1 else 1.0
    n_cluster_units = ceil_int(n_ind * de)
    return {
        "sd_d": sd_d,
        "delta": delta,
        "n_independent_units_no_cluster": n_ind,
        "icc": icc,
        "cluster_size": cluster_size,
        "design_effect": round(de, 10),
        "n_cluster_units": n_cluster_units,
        "formula": "n_ind=ceil((2.801585*SD_D/delta)^2); n_cluster=ceil(n_ind*(1+(m-1)*ICC))",
    }


def paired_cont_mde(sd_d: float, n_units: int) -> float:
    return Z80 * sd_d / math.sqrt(n_units)


def max_sd_for_delta(delta: float, n_units: int) -> float:
    return delta * math.sqrt(n_units) / Z80


def binary_paired_n(p10: float, p01: float, delta: float) -> Dict[str, Any]:
    # D = m_M - m_C per independent unit; pilot discordant probabilities p10=P(M wrong,C right),
    # p01=P(M right,C wrong). Var(D)= (p10+p01-(p10-p01)^2)/n.
    var_unit = p10 + p01 - (p10 - p01) ** 2
    n = ceil_int((Z80 ** 2) * var_unit / (delta ** 2))
    return {
        "p10": p10,
        "p01": p01,
        "delta": delta,
        "var_unit": round(var_unit, 10),
        "sd_unit": round(math.sqrt(var_unit), 10),
        "n_required": n,
        "formula": "n=ceil(2.801585^2*(p10+p01-(p10-p01)^2)/delta^2)",
    }


def fisher_n(delta: float) -> int:
    return ceil_int(2.0 * (Z80 / delta) ** 2 + 3.0)


def fisher_mde(n: int) -> float:
    if n <= 4:
        return float("inf")
    return Z80 * math.sqrt(2.0 / (n - 3.0))


def main() -> int:
    t1 = reachability(451 / 500, 0.10, 500)
    fisher_05 = fisher_n(0.05)
    fisher_10 = fisher_n(0.10)
    fisher_mde_30 = fisher_mde(30)
    paired_30_mde_05 = paired_cont_mde(0.20, 30)  # illustrative SD_D=.20
    max_sd_30_05 = max_sd_for_delta(0.05, 30)
    max_sd_30_10 = max_sd_for_delta(0.10, 30)

    endpoints = [
        {
            "id": "net_utility",
            "name": "net decision utility",
            "definition": "D_i=U_i(M*)-U_i(C) on the same independent unit; U is the pre-registered net utility (benefit-cost) of the selected action",
            "independent_unit": "independent biological unit (cell line / donor culture / independent differentiation), not well/technical replicate/plan",
            "pairing": "same unit, same decision context; paired D",
            "clustering": "by biological unit; repeated decisions within unit treated as cluster",
            "requires_measured_function": True,
            "requires_real_budget": True,
            "synthetic_can_test_algorithm": True,
            "synthetic_can_claim_pharmacology": False,
            "mde_formula": "2.801585*SD(D)/sqrt(n_ind)",
            "n_formula": "ceil((2.801585*SD(D)/delta)^2) (cluster/ICC inflation applies)",
            "notes": "publication primary for real decision benefit; synthetic only tests algorithm",
        },
        {
            "id": "mis_selection",
            "name": "mis-selection rate",
            "definition": "m_i=1[selected action is not the best registered action]; D_i=m_i(M*)-m_i(C); lower is better",
            "independent_unit": "independent biological unit; one decision per unit (or cluster if repeated)",
            "pairing": "same unit; paired binary D",
            "clustering": "by biological unit",
            "requires_measured_function": True,
            "requires_real_budget": True,
            "synthetic_can_test_algorithm": True,
            "synthetic_can_claim_pharmacology": False,
            "mde_formula": "paired binary; Var(D)=(p10+p01-(p10-p01)^2)/n; MDE=2.801585*SD(D)",
            "n_formula": "ceil(2.801585^2*(p10+p01-(p10-p01)^2)/delta^2)",
            "notes": "ceiling/headroom bind; p0 near 1 makes a rate improvement unreachable",
        },
        {
            "id": "regret",
            "name": "decision regret",
            "definition": "r_i=U_i(best)-U_i(selected); D_i=r_i(M*)-r_i(C); lower is better; normalized to a pre-registered utility scale",
            "independent_unit": "independent biological unit",
            "pairing": "same unit/context",
            "clustering": "by unit; possibly by cell background",
            "requires_measured_function": True,
            "requires_real_budget": True,
            "synthetic_can_test_algorithm": True,
            "synthetic_can_claim_pharmacology": False,
            "mde_formula": "2.801585*SD(D)/sqrt(n_ind)",
            "n_formula": "ceil((2.801585*SD(D)/delta)^2)",
            "notes": "distribution differs from accuracy; do not infer n from accuracy",
        },
        {
            "id": "topk_hit",
            "name": "top-k hit",
            "definition": "h_i=1[best action in top-k of ranked list]; D_i=h_i(M*)-h_i(C); ceiling/headroom bind",
            "independent_unit": "independent biological unit",
            "pairing": "same unit; paired binary",
            "clustering": "by unit",
            "requires_measured_function": True,
            "requires_real_budget": True,
            "synthetic_can_test_algorithm": True,
            "synthetic_can_claim_pharmacology": False,
            "mde_formula": "paired binary McNemar-based variance",
            "n_formula": "same as mis-selection with hit discordance",
            "notes": "top-k hit rate has a ceiling; headroom check first",
        },
        {
            "id": "budget_to_target",
            "name": "budget required to reach decision-quality target",
            "definition": "n_wells_i or cost_i required to reach a pre-registered decision-quality target; paired log/ratio at unit level",
            "independent_unit": "independent biological unit / independent experiment",
            "pairing": "same unit/decision context; paired cost ratio",
            "clustering": "by unit/plate; batch/date as cluster",
            "requires_measured_function": True,
            "requires_real_budget": True,
            "synthetic_can_test_algorithm": True,
            "synthetic_can_claim_pharmacology": False,
            "mde_formula": "no universal closed form; estimate paired log-cost SD or event-time",
            "n_formula": "pilot SD of paired log-cost; or simulation/event-time planning",
            "notes": "appropriate when baseline near ceiling and gain endpoint is unreachable; requires its own pre-registration",
        },
        {
            "id": "mechanism_detection",
            "name": "mechanism detection/identifiability",
            "definition": "detection power/FPR/parameter recovery for a known synthetic ground truth (e.g., joint contradiction)",
            "independent_unit": "synthetic replicate/independent generated unit",
            "pairing": "paired synthetic replicate when comparing algorithms",
            "clustering": "by synthetic generator seed/cluster; no biological unit claim",
            "requires_measured_function": False,
            "requires_real_budget": False,
            "synthetic_can_test_algorithm": True,
            "synthetic_can_claim_pharmacology": False,
            "mde_formula": "simulation/known truth; power/FPR",
            "n_formula": "simulation-based, per generated replicate",
            "notes": "mechanism ledger only; never pharmacology/decision benefit",
        },
    ]

    examples = [
        {"id": "net_utility_sd20_d05", "endpoint": "net_utility", **paired_cont_n(0.20, 0.05)},
        {"id": "net_utility_sd30_d05", "endpoint": "net_utility", **paired_cont_n(0.30, 0.05)},
        {"id": "net_utility_sd20_d05_cluster6_icc05", "endpoint": "net_utility", **paired_cont_n(0.20, 0.05, icc=0.5, cluster_size=6)},
        {"id": "regret_sd15_d05", "endpoint": "regret", **paired_cont_n(0.15, 0.05)},
        {"id": "mis_selection_p10_20_p01_10_d05", "endpoint": "mis_selection", **binary_paired_n(0.20, 0.10, 0.05)},
        {"id": "topk_p10_15_p01_05_d05", "endpoint": "topk_hit", **binary_paired_n(0.15, 0.05, 0.05)},
    ]

    scope = {
        "task": "R203-P1 decision endpoints, reachability, paired power, two ledgers",
        "status": "design_only_NOT_EXECUTED",
        "purpose": "replace universal 6,282-cell decision gate with endpoint-specific reachability/power planning; separate mechanism from pharmacological ledger",
        "fisher_z_only": {
            "formula": "N_req=2*(2.801585/delta)^2+3 (independent correlation Fisher-z planning approximate)",
            "n_delta_05": fisher_05,
            "n_delta_10": fisher_10,
            "mde_at_n30": round(fisher_mde_30, 10),
            "meaning": "only for independent-correlation comparisons; NOT a universal decision-utility or drug-decision gate; 30 cells insufficient for this correlation comparison at delta .05/.10",
            "do_not_use_as": ["net decision utility gate", "mis-selection rate gate", "regret gate", "top-k gate", "budget-to-target gate"],
        },
        "reachability": {
            "formula": "max_gain=U_max-p0; required_successes=ceil(n*(p0+delta)); reachable iff delta<=max_gain AND required_successes<=n",
            "flow": [
                "freeze endpoint, independent unit, population, action set, utility/cost and delta before looking at outcome",
                "estimate baseline p0/U0 and upper bound U_max from a pre-registered pilot or prior resource (not from the target outcome)",
                "compute headroom=max_gain=U_max-p0; if delta>headroom -> unreachable_gate (do not lower delta after seeing results)",
                "estimate paired D variance/SD, ICC/cluster size, discordance; compute MDE80; if MDE80>delta -> precision_insufficient, not algorithm failure",
                "if both pass, register n and analysis; otherwise stop or open a different endpoint (budget-to-target) with a new pre-registration",
            ],
            "T1_example": t1,
            "T1_meaning": "C7_experiment_only 451/500=.902; max_gain=.098<.10; pass would require 501/500; T1 gate is unreachable in this batch, not just underpowered; retain partial_decision_benefit and old CI; no delta change.",
        },
        "paired_power": {
            "continuous_paired": {
                "formula": "MDE80=2.801585*SD(D)/sqrt(n_ind); n_ind=ceil((2.801585*SD(D)/delta)^2)",
                "cluster": "n_cluster=ceil(n_ind*(1+(m-1)*ICC)); use cluster-level D if possible",
                "examples": examples,
            },
            "binary_paired": {
                "formula": "D_i in {-1,0,1}; Var(D)=(p10+p01-(p10-p01)^2)/n; n=ceil(2.801585^2*(p10+p01-(p10-p01)^2)/delta^2)",
                "ceiling": "p0+delta<=1 required; if baseline near ceiling, a rate gain may be unreachable",
            },
            "correlation_fisher_only": {
                "formula": "N_req=2*(2.801585/delta)^2+3; MDE=2.801585*sqrt(2/(N-3))",
                "n30_mde": round(fisher_mde_30, 10),
                "note": "only independent-correlation planning; not general decision",
            },
            "thirty_cell_equivalence": {
                "n": 30,
                "continuous_delta_05_max_sd_d": round(max_sd_30_05, 10),
                "continuous_delta_10_max_sd_d": round(max_sd_30_10, 10),
                "illustrative_sd20_mde": round(paired_30_mde_05, 10),
                "meaning": "30 independent units suffice only if SD(D) is implausibly small or delta is large; for typical net utility/regret SD .15-.30, MDE > .05; technical repeats do not increase independent background n",
                "technical_repeats": "precision only; never independent biological n",
            },
        },
        "endpoint_catalog": endpoints,
        "two_ledgers": {
            "mechanism_verification": {
                "evidence": "synthetic/known ground truth, known noise, formal identifiability, calibration/FPR/power",
                "can_claim": ["formal consistency", "algorithm behavior under known generator", "computational capability"],
                "cannot_claim": ["pharmacology", "real drug decision benefit", "biological mechanism", "independent confirmation", "migration"],
                "budget": "compute only; no wells; no new cultures",
                "stop": "if synthetic calibration or detection/parameter recovery fails -> stop mechanism claim; no rescue by changing generator after results",
            },
            "pharmacological_confirmation": {
                "evidence": "qualified measured functional endpoint (viability/apoptosis/regrowth), exposure/dose, independent cultures/units, independent evaluation, powered decision endpoint",
                "can_claim": ["measured functional effect/decision utility under qualifications", "only after independent validation and power"],
                "cannot_claim": ["mechanism from viability alone", "migration without independent resource", "decision benefit from synthetic-only run"],
                "budget": "real wells/plates/cultures; independent biological units; cost accounting",
                "stop": "if functional endpoint not qualified, headroom<delta, or MDE>delta -> stop; no substitution by synthetic or 6,282-cell rule",
            },
            "separation_rule": "decision utility and pharmacology belong to pharmacological ledger; synthetic results cannot be promoted to it. 6,282 is not a pharmacological decision gate.",
        },
        "next_studies": [
            {
                "id": "R203-N1",
                "ledger": "mechanism_verification",
                "question": "Under a pre-registered synthetic ground truth with a state/sequence-dependent shared operator (not static S-add), does a plan-pair conflict-aware unified-revision policy reduce held-out decision regret vs equal-information/budget baselines?",
                "substantive_difference": "dynamic/state-dependent operator and decision regret, not the stopped static S-add joint-contradiction test; synthetic mechanism ledger only",
                "data": "synthetic generated world with known state transitions/non-additive interactions; no O'Neil response; no pharmacology",
                "algorithm_difference": "plan-pair conflict signal + one-feedback unified revision of state-dependent shared operator vs static S-add/full retrain",
                "equal_information_baselines": ["full-history retrain", "static S-add", "hierarchical/EB", "GP", "random plan-pair selection", "active-learning/decision AL"],
                "endpoints": ["decision regret (primary)", "mis-selection rate", "detection power/FPR on known contradiction", "parameter recovery"],
                "delta_and_mde": "delta_regret=.05 on normalized utility; paired synthetic units; preflight headroom (not at ceiling) + MDE<=.05; n per endpoint",
                "failure_classes": ["data_unavailable", "design_invalid: generator/calibration", "evaluation_cannot_distinguish", "no_increment", "unreachable_gate"],
                "stop": "if generator/calibration fails -> design_invalid; if no detection/regret increment over strong baselines -> stop claim; no post-hoc generator change",
                "not_run": True,
            },
            {
                "id": "R203-N2",
                "ledger": "pharmacological_confirmation",
                "question": "On a new qualified measured functional resource, does the same policy improve net decision utility vs equal-information full-history retraining on paired independent biological units?",
                "substantive_difference": "real measured function/exposure/independent cultures, not T1 synthetic dual-budget or static S-add; pharmacological ledger",
                "data": "new independent measured viability/apoptosis/regrowth resource with exposure/dose and independent cultures; not local; no DeltaEMAX stitching",
                "algorithm_difference": "same policy vs full-history retrain/hierarchical/GP/AL, equal wells+compute",
                "equal_information_baselines": ["full-history retrain", "hierarchical", "GP", "random/AL", "static predictor+optimizer"],
                "endpoints": ["net utility (primary)", "mis-selection", "regret", "top-k", "budget-to-target"],
                "delta_and_mde": "delta=.05 normalized utility; paired independent units; headroom preflight + power/MDE; independent cultures not wells",
                "failure_classes": ["data_unavailable", "unreachable_gate", "evaluation_cannot_distinguish", "no_increment", "no_decision_benefit"],
                "stop": "if no qualified functional endpoint/exposure/independent cultures or headroom<delta or MDE>delta -> stop; do not substitute synthetic or lower delta",
                "not_run": True,
            },
        ],
        "boundaries": [
            "design only; no effect run; no model fit; no response/functional data read",
            "do not lower old thresholds, rewrite old verdicts, promote code, or revive stopped experiments",
            "not a claim of novelty/mechanism/migration/decision benefit",
            "T1 remains partial_decision_benefit; 6,282-cell gate retracted as universal; A.1 static S-add stop retained",
            "technical repeats are not independent biological units; background/cell lines cannot be the only unit for all questions",
            "synthetic mechanism results never become pharmacological evidence",
        ],
        "attestation": {
            "metadata_only": True,
            "effect_run": False,
            "model_fit": False,
            "response_or_functional_data_read": False,
            "old_gates_changed": False,
            "old_verdicts_changed": False,
            "code_promoted": False,
            "stopped_experiments_revived": False,
            "novelty_claim": False,
        },
    }

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(scope, ensure_ascii=False, indent=1, sort_keys=True))
        fh.write("\n")
    print("wrote", OUT)
    print("T1 reachable", t1["reachable"], "required_successes", t1["required_successes"], "max_gain", t1["max_gain"])
    print("Fisher n .05/.10", fisher_05, fisher_10, "MDE n30", round(fisher_mde_30, 4))
    print("net utility SD.2 d.05 n", examples[0]["n_independent_units_no_cluster"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
