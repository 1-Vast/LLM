"""EG-RPT scaffolding: task/policy record, evidence-qualified policy memory, Virtual Cell reliability report, uncertainty decision rule.

File summary
- Path: research/eg_rpt_20261019/policy_memory.py
- Purpose: the minimum typed objects for Evidence-Grounded Research Policy Transfer (EG-RPT). It is a record format and
  a set of pure functions; it contains no learned transfer model. Whether policy utility transfers is an open question.
- Objects
  * `ResearchTask`   tau = (c, d, A, O, B, U): context, intervention, legal actions, observations, budget, utility name.
  * `PolicyExperience` M_i = (tau_i, pi_i, E_i, DeltaU_i, F_i) with units, validation tier, dependence group and
    failure/applicability boundary. `validate_experience` refuses records that cannot support transfer learning.
  * `ReliabilityReport` the Virtual Cell's output beyond a point prediction (uncertainty, model disagreement, scope,
    calibration, refusal/fallback).
  * `choose_under_uncertainty` compares proceed / acquire / test-assumption / baseline with explicit units.
  * `leave_group_out` splits experiences so no dependence group appears on both sides.
- Rules enforced here (each tested): a negative result is stored as a first-class record; utilities in different units are
  never pooled; independence is counted by dependence group, never by record; model disagreement is not experiment value.
"""
from __future__ import annotations

from dataclasses import dataclass, field

TIERS = ("development", "internal_heldout", "external_confirmation", "withdrawn")
OUTCOMES = ("supported", "unconfirmed", "not_supported", "withdrawn", "blocked")
UNITS = ("events_per_64_compounds", "hits_per_16_queries", "selective_r", "percentage_points", "unexpected_hits", "confirmation_rate", "hits_per_line")


@dataclass
class ResearchTask:
    task_id: str
    context: dict          # c: cell identity/lineage/genotype/disease features that were legal at decision time
    intervention: dict     # d: compound/family descriptors
    actions: list          # A: legally available experiments
    observations: list     # O: possible observation types
    budget: dict           # B: itemised {assay_wells, compute, rounds, ...}; hypothetical flags allowed
    utility: str           # U: predeclared terminal utility name


@dataclass
class PolicyExperience:
    exp_id: str
    task_family: str                 # e.g. "A_drug_response"
    task: str                        # short description of tau
    policy: str                      # pi
    baseline: str                    # the strong baseline the DeltaU is measured against
    delta_u: float | None
    ci95: tuple | None
    unit: str
    validation_tier: str
    outcome: str
    dependence_group: str            # shared dataset/lineage/screen: records in a group are NOT independent
    source: str                      # study path
    record_pattern: str              # text that must appear in `source` evidence (for audit_experiences.py)
    failure_mode: str = ""
    applicability: str = ""
    cost: dict = field(default_factory=dict)
    cost_is_hypothetical: bool = True
    ci_note: str = ""                 # required when ci95 is None (why no interval is recorded)


def validate_experience(e: PolicyExperience) -> list:
    bad = []
    if e.validation_tier not in TIERS:
        bad.append("unknown validation_tier")
    if e.outcome not in OUTCOMES:
        bad.append("unknown outcome")
    if e.unit not in UNITS:
        bad.append("unit not in the declared list; utilities in new units must be added explicitly")
    if e.outcome in ("supported", "unconfirmed", "not_supported") and e.delta_u is None:
        bad.append("measured outcome needs delta_u")
    if e.ci95 is None and not e.ci_note.strip():
        bad.append("ci95 missing without a ci_note: records without intervals cannot be used as transfer labels")
    if e.ci95 is not None and not (e.ci95[0] <= (e.delta_u if e.delta_u is not None else e.ci95[0]) <= e.ci95[1]):
        bad.append("delta_u outside its own interval")
    if e.outcome != "supported" and not e.failure_mode.strip():
        bad.append("non-supported records must state the failure mode / applicability boundary")
    if not e.dependence_group or not e.source or not e.record_pattern:
        bad.append("dependence_group, source and record_pattern are required")
    if e.validation_tier == "external_confirmation" and e.outcome == "supported" and e.cost_is_hypothetical:
        bad.append("external confirmation with hypothetical costs cannot support a cost claim")
    return bad


def independent_units(exps) -> int:
    """Independence is the number of dependence groups, not the number of records."""

    return len({e.dependence_group for e in exps})


def poolable(exps) -> bool:
    """Utilities are comparable only inside one unit."""

    return len({e.unit for e in exps}) <= 1


def leave_group_out(exps):
    """Yield (held_out_group, train, test): no dependence group is on both sides."""

    for g in sorted({e.dependence_group for e in exps}):
        yield g, [e for e in exps if e.dependence_group != g], [e for e in exps if e.dependence_group == g]


@dataclass
class ReliabilityReport:
    prediction: float
    interval: tuple                  # calibrated where supported, else None
    interval_is_calibrated: bool
    model_disagreement: float        # spread across reasonable model classes (NOT experiment value)
    in_scope: bool                   # inside the validated applicability scope
    calibration_note: str
    domain_distance: float           # distance to the validation domain, in units of the source's own spread
    fallback: str = "strongest_simple_baseline"

    def refuses(self, max_disagreement: float, max_distance: float) -> bool:
        """Refuse a point claim when out of scope, too far from the validated domain or models disagree too much."""

        return (not self.in_scope) or self.domain_distance > max_distance or self.model_disagreement > max_disagreement


def choose_under_uncertainty(report: ReliabilityReport, *, thresholds: dict, expected_gain: dict, cost: dict, misspec_penalty: dict) -> dict:
    """Compare the four options with one utility unit. thresholds = {max_disagreement, max_distance} are protocol parameters.

    expected_gain/cost/misspec_penalty are dicts over OPTIONS in the SAME unit (e.g. qualified nominations per 64 compounds);
    V(a) = gain - cost - misspec_penalty. Under refusal, 'proceed' is not admissible. The baseline always has gain 0 by
    definition (gains are measured against it), so choosing it is the default when nothing beats zero.
    """

    options = ("proceed", "acquire_information", "test_model_assumption", "baseline")
    refused = report.refuses(thresholds["max_disagreement"], thresholds["max_distance"])
    v = {}
    for o in options:
        if o == "proceed" and refused:
            continue
        g = 0.0 if o == "baseline" else float(expected_gain.get(o, 0.0))
        v[o] = g - float(cost.get(o, 0.0)) - float(misspec_penalty.get(o, 0.0))
    best = max(v, key=lambda o: (v[o], o == "baseline"))
    return {"choice": best, "values": v, "refused_point_claim": refused}
