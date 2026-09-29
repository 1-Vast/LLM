"""Arms for the closed-loop replay: the belief planner over case-memory worlds, and the comparison arms.

File summary
- Path: research/maestro_vc_v1/arms.py
- Purpose: build every pre-registered arm as a `research/protocol_v2/runner.run_episode` arm. All arms
  share the runner's menu, budget, QC rule, registered validator and `EvidenceState`; they differ only
  in how they choose the next measurement.
- Core points:
  - `cm_belief_arm` is `research/belief_planning/arms.py::belief_arm` with two differences: it reads a
    case-memory world installed for the fold, and it may start from the world's advisory
    `hypothesis_prior` instead of 0.5/0.5. With `prior=False` and a world that has no extension its
    decisions are identical to `belief_arm` (a test checks this on real episodes).
  - The prior is planning belief only. It never enters `EvidenceState`, never eliminates a hypothesis
    and is recorded in the step note as `historical_analogy`. Only a real, QC-passed, eliminating
    reading moves the candidate set.
  - `anchored` (baseline-safe) follows `belief_arm(anchor=True)`: the arm leaves the expert order only
    when the planner's advantage exceeds `deviation_z` standard errors.
  - Comparison arms are the repository's own: `fixed` (expert order), `random_legal`, `coverage`
    (`cost_only`: the budgeted expected-coverage selector without virtual-cell priorities), `scalar_vc`
    (`magnitude`: the same selector with the virtual cell's scalar predicted magnitude as priority),
    `belief_class` and `belief_similarity` (the current research planner without and with the structural
    kernel), and the block-7 `vc_incontext` arm, which conditions forecasts on purchased prompts.
  - `oracle` reads hidden outcomes and is an upper bound, never a competitor.
- Interfaces: `install`, `cm_belief_arm`, `build_arms`, `ARM_ROLES`
- Depends on: research/scientific_case_memory/world.py, research/belief_planning, research/dual_core,
  research/external_validation/arms.py, research/protocol_v2
"""
from __future__ import annotations

from maestro.acquisition import outcome_consequences
from research.belief_planning import arms as BA
from research.belief_planning import world as W
from research.belief_planning.planner import plan_measurement, update_belief

P, C, E, V = BA.P, BA.C, BA.E, BA.V

ARM_ROLES = {
    "fixed": "primary_comparator",
    "random_legal": "lower_bound",
    "coverage": "current_production_selector_without_vc",
    "scalar_vc": "scalar_virtual_cell_priority",
    "belief_class": "no_case_memory",
    "belief_similarity": "similarity_only_retrieval_current_planner",
    "cm_similarity_unitout": "control_unit_out_fit",
    "cm_full": "adaptation_aware_retrieval",
    "cm_full_prior": "adaptation_aware_retrieval_with_retrieved_prior",
    "cm_full_prior_anchored": "adaptation_aware_retrieval_baseline_safe",
    "cm_nofail": "ablation_no_failure_or_negative_cases",
    "prior_only": "retrieved_prior_without_reading_terms",
    "vc_incontext": "hypothesis_conditional_virtual_cell_purchased_prompts",
    "oracle": "upper_bound",
}
CM_WORLDS = {"cm_similarity_unitout": "similarity_unitout", "cm_full": "cm_full", "cm_full_prior": "cm_full_prior",
             "cm_full_prior_anchored": "cm_full_prior", "cm_nofail": "cm_nofail", "prior_only": "prior_only"}


def install(view, worlds: dict) -> None:
    """Put case-memory worlds where `belief_arm`'s `world_for` looks for them (its own cache, unchanged code)."""
    cache = view.extra.setdefault("belief_worlds", {})
    for name, world in worlds.items():
        cache[(name, "true", ())] = world


def _cm_state(view, world, compound, h1, h2, executed, menu, setting, *, prior: bool):
    real = tuple((tuple(s["key"]), W.label_of(s["outcome"])) for s in executed)
    if prior:
        unit = _unit(view, compound)
        belief = dict(world.hypothesis_prior(compound, h1, h2, unit))
    else:
        belief = {h1: 0.5, h2: 0.5}
    for i, (key, label) in enumerate(real):
        belief = update_belief(belief, world.forecast(key, h1, h2, compound, real[:i]), label)
    by_id = {C.action_id(k): k for k in setting.keys}
    done = [tuple(s["key"]) for s in executed]

    def legal(hyp):
        keys = done + [by_id[a] for a, _ in hyp]
        if len(keys) >= setting.max_measurements:
            return ()
        left = setting.budget_days - sum(setting.days(k) for k in keys)
        steps = [{"key": list(k)} for k in keys]
        return tuple(P.make_action(k, h1, h2, setting) for k in P.legal_menu(setting, steps, left))

    if [a.identifier for a in legal(())] != [C.action_id(k) for k in menu]:
        raise AssertionError("planner legality differs from the runner's menu")

    def forecast(action, hyp):
        return world.forecast(by_id[action.identifier], h1, h2, compound,
                              real + tuple((by_id[a], lab) for a, lab in hyp))

    return real, belief, legal, forecast, by_id


def _unit(view, compound):
    comp = view.data.compounds.drop_duplicates("compound").set_index("compound")
    for col in ("component", "skeleton"):
        if col in comp.columns and compound in comp.index and isinstance(comp.at[compound, col], str):
            return comp.at[compound, col]
    return None


def cm_belief_arm(world_name: str, *, prior: bool, anchor: bool = False, price: float = BA.PRICE,
                  z: float = BA.DEVIATION_Z):
    """The belief-expectimax planner over an installed case-memory world."""

    def arm(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
        if not ctx.params.get("eliminates"):
            return BA._stop("registered_validator_cannot_eliminate")
        world = ctx.extra["belief_worlds"][(world_name, "true", ())]
        real, belief, legal, forecast, by_id = _cm_state(ctx, world, compound, h1, h2, executed, menu, setting,
                                                         prior=prior)
        consequences = outcome_consequences(V.registered_rules(h1, h2))
        depth = setting.max_measurements - len(executed)
        baseline = None
        if anchor:
            fixed_key, _ = P.fixed(ctx, compound, h1, h2, executed, menu, remaining, setting, state)
            baseline = C.action_id(fixed_key) if fixed_key is not None else None
        plan = plan_measurement((h1, h2), belief, legal, forecast, consequences, horizon=depth, price=price,
                                wrong_risk_cap=None, baseline=baseline, deviation_z=z if anchor else None)
        note = {"evidence_kind": "model_prediction", "planner": "belief_expectimax", "world": world_name,
                "prior_used": bool(prior), "prior_evidence_class": "historical_analogy" if prior else None,
                "belief": {h: round(p, 6) for h, p in belief.items()}, "anchor": plan.anchor, "baseline": baseline,
                "history_labels": [lab for _, lab in real]}
        if plan.chosen is None:
            return BA._stop(f"belief_{plan.reason}", **note, refusals=dict(plan.refusals))
        key = by_id[plan.chosen]
        chosen = world.forecast(key, h1, h2, compound, real)
        note.update({
            "expected_utility": plan.value.utility, "p_correct_plan": plan.value.p_correct,
            "p_wrong_plan": plan.value.p_wrong, "p_wrong_upper_plan": plan.value.p_wrong_upper,
            "expected_measurements": plan.value.measurements, "contingent": dict(plan.contingent),
            "basis": chosen.basis, "model_version": chosen.model_version,
            "support_report": world.support_report(key, h1, h2, compound),
            "prediction_by_hypothesis": {
                b.hypothesis: {"probabilities": dict(b.probabilities), "support": b.support,
                               "p_correct": b.probabilities.get(W.MATCH_H1 if b.hypothesis == h1 else W.MATCH_H2, 0.0),
                               "p_wrong": b.probabilities.get(W.MATCH_H2 if b.hypothesis == h1 else W.MATCH_H1, 0.0)}
                for b in chosen.branches}})
        return key, note

    return arm


class ScalarMagnitude:
    """The virtual cell's scalar prediction: the norm of the similarity-weighted mean shift of the five most
    similar training references at a condition. It is the served rung's rule (`episodes.Magnitude`) rebuilt on
    the public view so it works for both datasets; unlike the served rung it is applied at every time point.
    It says how large a response will be, never which hypothesis it supports."""

    def __init__(self, view):
        self.fp, self.pos = view.extra["fingerprints"]
        self.tables = view.ft.tables

    def predict(self, compound, key):
        import numpy as np

        table = self.tables.get(tuple(key))
        row = self.pos.get(compound, -1)
        if table is None or row < 0 or not self.fp[row].any() or not len(table.names):
            return None
        x = self.fp[row]
        rows = np.array([self.pos.get(n, -1) for n in table.names])
        ok = rows >= 0
        if not ok.any():
            return None
        fp = self.fp[np.maximum(rows, 0)]
        inter = fp @ x
        union = fp.sum(1) + x.sum() - inter
        sim = np.where(ok & (union > 0), inter / np.maximum(union, 1e-9), -1.0)
        top = np.argsort(-sim)[:5]
        top = top[sim[top] >= 0]
        if not len(top):
            return None
        w = np.maximum(sim[top], 1e-6)
        w = w / w.sum()
        return float(np.linalg.norm(w @ np.asarray(table.Y)[top]))


def scalar_vc_arm():
    from research.external_validation import arms as A

    def arm(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
        mag = ctx.extra.setdefault("scalar_magnitude", ScalarMagnitude(ctx))
        priorities = {C.action_id(k): v for k, v in ((k, mag.predict(compound, k)) for k in menu) if v is not None}
        key, note = A._budgeted(ctx, h1, h2, menu, remaining, setting, priorities or None)
        return key, {**note, "vc_channel": "scalar_magnitude"}

    return arm


def build_arms(names, real_ctx, view, *, vc_incontext=None):
    """Instantiate the named arms for one fold. `vc_incontext` is a prebuilt block-7 arm (needs its executor)."""
    from research.external_validation import arms as A

    factories = {
        "fixed": lambda: A.fixed,
        "random_legal": lambda: A.random_legal,
        "coverage": lambda: A.cost_only,
        "scalar_vc": lambda: scalar_vc_arm(),
        "belief_class": lambda: BA.belief_arm(vc="masked"),
        "belief_similarity": lambda: BA.belief_arm(),
        "cm_similarity_unitout": lambda: cm_belief_arm("cm_similarity_unitout", prior=False),
        "cm_full": lambda: cm_belief_arm("cm_full", prior=False),
        "cm_full_prior": lambda: cm_belief_arm("cm_full_prior", prior=True),
        "cm_full_prior_anchored": lambda: cm_belief_arm("cm_full_prior", prior=True, anchor=True),
        "cm_nofail": lambda: cm_belief_arm("cm_nofail", prior=False),
        "prior_only": lambda: cm_belief_arm("prior_only", prior=True),
        "vc_incontext": lambda: vc_incontext,
        "oracle": lambda: A.make_oracle(real_ctx, E.execute),
    }
    return {n: factories[n]() for n in names}
