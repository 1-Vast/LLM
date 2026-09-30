"""The belief-planning agent as a runner arm, and its attribution controls.

File summary
- Path: research/belief_planning/arms.py
- Purpose: wrap `research.belief_planning.planner.plan_measurement` and the `world.ReferenceWorld` forecaster as an
  arm for `sequence_audit.policies.run_matched`. The runner still owns the menu, budget, QC rule,
  evidence update and stopping on elimination.
- Core points:
  - State. The agent's state is rebuilt at every call from the real steps the runner recorded:
    the history of (condition, registered reading label), and the belief that follows from it by
    Bayes' rule under the same world model. Forecasts never touch `EvidenceState`.
  - Lookahead. The planner uses the runner's own legality rule (`policies.legal_menu`) inside the
    lookahead, and checks that the menu it would offer now equals the runner's.
  - Controls:
    - `vc`: on, masked or permuted (another held-out compound's structural similarities).
    - `feedback`:
      - true;
      - withheld: the agent knows a measurement ran and removed nothing, not what it read;
      - permuted: the label of a partner held-out compound's real reading at the same condition
        under the same contrast. This is a control that reads another episode's outcome and is
        flagged `reads_other_episode_outcomes`.
  - Notes record the chosen plan's forecast `p_correct` / `p_wrong` / conservative `p_wrong_upper`,
    the belief, the contingent next action for each reading, and whether the virtual cell
    reached the forecast (`used_vc`).
- Interfaces: `belief_arm`, `belief_state`, `world_for`, `PRICE`
- Depends on: research/belief_planning/world.py, research/sequence_audit/policies.py, research/belief_planning/planner.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for sub in ("sequence_audit", "acquisition_link", "dynamic_world_model"):
    sys.path.insert(0, str(ROOT / "research" / sub))

import policies as P  # noqa: E402

from maestro.acquisition import outcome_consequences  # noqa: E402
from .planner import plan_measurement, update_belief  # noqa: E402

from . import world as W  # noqa: E402

C, E, V = P.C, P.E, P.V
PRICE = 0.02
"""The registered utility price of one measurement (the 2026-09-27 ladder's `myopic_edv` price)."""


def fingerprints(compounds):
    """Morgan radius-2, 2048-bit fingerprints by compound; a missing or unparsable structure is all-zero."""
    from rdkit import Chem, RDLogger
    from rdkit.Chem import rdFingerprintGenerator
    RDLogger.DisableLog("rdApp.*")
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    comp = compounds.drop_duplicates("compound")
    rows, pos = [], {}
    for name, smiles in zip(comp.compound, comp.smiles):
        mol = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) and smiles else None
        pos[name] = len(rows)
        rows.append(gen.GetFingerprintAsNumPy(mol).astype(np.float32) if mol is not None else np.zeros(2048, np.float32))
    return np.asarray(rows), pos


def world_for(ctx, vc: str, feedback: str, overrides=None) -> W.ReferenceWorld:
    """One world model per (context, controls), built from the context's training tables only."""
    worlds = ctx.extra.setdefault("belief_worlds", {})
    key = (vc, feedback, tuple(sorted((overrides or {}).items())))
    if key not in worlds:
        if "fingerprints" not in ctx.extra:
            ctx.extra["fingerprints"] = fingerprints(ctx.data.compounds)
        fp, pos = ctx.extra["fingerprints"]
        training = ctx.extra["training_compounds"]
        # hyperparameters are fitted once per context on training references and shared by every control
        fitted = ctx.extra.get("world_hyperparameters")
        comp = ctx.data.compounds.drop_duplicates("compound").set_index("compound")
        unit = "component" if "component" in comp.columns else "skeleton"
        groups = {c: g for c, g in comp[unit].items() if isinstance(g, str)} if ctx.extra.get("group_readings", True) else None
        world = W.ReferenceWorld(ctx.ft, ctx.params, training, fingerprints=fp, positions=pos, vc=vc,
                                 feedback=feedback, partner=ctx.extra.get("vc_partner"), hyperparameters=fitted,
                                 groups=groups)
        ctx.extra["world_hyperparameters"] = world.hyperparameters
        if overrides:
            world.hyperparameters = {**world.hyperparameters, **overrides}
        worlds[key] = world
    return worlds[key]


def _stop(reason, **extra):
    return None, {"reason": reason, **extra}


DEVIATION_Z = 1.6448536269514722
"""One-sided 95% normal quantile: the anchored agent leaves the expert order only on this much evidence."""


def _contaminated(forecast, eps: float):
    """The forecast mixed with a uniform reading distribution: P_eps(y|h) = (1 - eps) P(y|h) + eps / |labels|."""
    from maestro.acquisition import OutcomeBranch, OutcomeForecast
    if forecast.refusal or eps <= 0:
        return forecast
    branches = []
    for b in forecast.branches:
        labels = tuple(b.probabilities)
        branches.append(OutcomeBranch(b.hypothesis, {k: (1 - eps) * float(v) + eps / len(labels)
                                                      for k, v in b.probabilities.items()}, b.support))
    return OutcomeForecast(forecast.action_identifier, tuple(branches), basis=f"{forecast.basis}|contaminated:{eps:g}",
                           model_version=forecast.model_version)


def belief_state(ctx, compound, h1, h2, executed, menu, setting, *, vc: str = "on", feedback: str = "true",
                 overrides=None, contamination: float = 0.0):
    """Everything the planner needs at one decision point, rebuilt from the runner's real steps.

    Returns ``(world, real, belief, legal, forecast, by_id)``. Shared by `belief_arm` and the
    protocol-v2 arms so every planner arm plans from the identical state. ``contamination`` > 0
    bounds the likelihood ratio of each *real* reading in the belief update (a contamination
    mixture; protocol v2's robustness arm). It does not change the forecasts used for planning.
    """
    world = world_for(ctx, vc, feedback, overrides)
    real = tuple((tuple(s["key"]), W.label_of(s["outcome"])) for s in executed)
    if feedback == "permuted":
        other = ctx.extra["feedback_partner_reading"]
        real = tuple((k, lab if lab == W.QC_FAILED else other(compound, k, h1, h2)) for k, lab in real)
    belief = {h1: 0.5, h2: 0.5}
    for i, (key, label) in enumerate(real):
        forecast = world.forecast(key, h1, h2, compound, real[:i])
        if feedback == "withheld" and label != W.QC_FAILED:
            keep = (W.UNRESOLVED, W.ABSENT)
            like = {h: sum(forecast.branch_for(h).probabilities.get(x, 0.0) for x in keep) for h in belief}
            total = sum(belief[h] * like[h] for h in belief)
            belief = {h: belief[h] * like[h] / total for h in belief} if total > 0 else belief
        else:
            belief = update_belief(belief, _contaminated(forecast, contamination) if contamination else forecast, label)
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

    return world, real, belief, legal, forecast, by_id


def belief_arm(*, vc: str = "on", feedback: str = "true", price: float = PRICE, cap: float | None = None,
               horizon: int | None = None, overrides=None, anchor: bool = False, z: float = DEVIATION_Z,
               contamination: float = 0.0):
    """The agent: plan over the remaining measurements, act, and replan from each real reading."""

    def arm(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
        if not ctx.params.get("eliminates"):
            return _stop("registered_validator_cannot_eliminate")
        world, real, belief, legal, forecast, by_id = belief_state(ctx, compound, h1, h2, executed, menu, setting,
                                                                   vc=vc, feedback=feedback, overrides=overrides,
                                                                   contamination=contamination)
        consequences = outcome_consequences(V.registered_rules(h1, h2))
        depth = setting.max_measurements - len(executed) if horizon is None else min(horizon, setting.max_measurements - len(executed))
        baseline = None
        if anchor:
            fixed_key, _ = P.fixed(ctx, compound, h1, h2, executed, menu, remaining, setting, state)
            baseline = C.action_id(fixed_key) if fixed_key is not None else None
        plan = plan_measurement((h1, h2), belief, legal, forecast, consequences, horizon=depth,
                                price=price, wrong_risk_cap=cap, baseline=baseline,
                                deviation_z=z if anchor else None)
        used_vc = any("vc" in (world.forecast(k, h1, h2, compound, real).basis.split(":")[-1].split("/"))
                      for k in menu) if vc != "masked" else False
        note = {"evidence_kind": "model_prediction", "planner": "belief_expectimax", "vc": vc, "feedback": feedback,
                "belief": {h: round(p, 6) for h, p in belief.items()}, "used_vc": bool(used_vc),
                "anchor": plan.anchor, "baseline": baseline,
                "history_labels": [lab for _, lab in real]}
        if plan.chosen is None:
            return _stop(f"belief_{plan.reason}", **note, refusals=dict(plan.refusals))
        key = by_id[plan.chosen]
        chosen = world.forecast(key, h1, h2, compound, real)
        note.update({
            "expected_utility": plan.value.utility, "p_correct_plan": plan.value.p_correct,
            "p_wrong_plan": plan.value.p_wrong, "p_wrong_upper_plan": plan.value.p_wrong_upper,
            "expected_measurements": plan.value.measurements, "contingent": dict(plan.contingent),
            "wrong_loss_used": plan.wrong_loss_used, "basis": chosen.basis,
            "prediction_by_hypothesis": {
                b.hypothesis: {"probabilities": dict(b.probabilities), "support": b.support,
                               "p_correct": b.probabilities.get(W.MATCH_H1 if b.hypothesis == h1 else W.MATCH_H2, 0.0),
                               "p_wrong": b.probabilities.get(W.MATCH_H2 if b.hypothesis == h1 else W.MATCH_H1, 0.0)}
                for b in chosen.branches},
        })
        if feedback == "permuted":
            note["reads_other_episode_outcomes"] = True
        return key, note

    return arm
