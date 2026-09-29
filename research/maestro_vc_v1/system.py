"""The closed-loop decision-support system: from a user's real data to a next step, and back.

File summary
- Path: research/maestro_vc_v1/system.py
- Purpose: implement the ten-step workflow of the design for the transcriptomic mechanism-contrast
  problem. A user supplies a compound, two competing mechanism classes and the readings already
  obtained; the system states what is known, retrieves precedents, forecasts per hypothesis, chooses
  the next measurement by terminal-decision value, explains what each result would change, abstains
  when it cannot separate the hypotheses, and, when a real result arrives, updates the memory.
- Core points:
  - Order. `assess` (typed statuses, missing conditions, out-of-distribution check) then `graph`
    (layered hypotheses, registered and advisory) then `retrieve` (four stages, with reasons) then
    `forecast` (per action and hypothesis, `insufficient_support` when refused) then `plan` (expectimax
    over the remaining budget on the registered evidence rules) then `answer` (the sections 9.1 to 9.7
    of the design, as data and as markdown).
  - Evidence rules are the repository's. The candidate set is an `EvidenceState`; only a real, QC-passed,
    eliminating reading removes a hypothesis (`evidence_update` from the registered `InterpretationTable`).
    The retrieved prior and every forecast are advisory and appear in the answer under their own class.
  - Six kinds of statement are kept apart in the answer: measured fact, qualified evidence, model
    prediction, historical analogy, mechanistic inference, speculation.
  - Abstention is a named result: no chosen action (`belief_<reason>`), a chosen action whose
    reference support is below the registered minimum, a target outside the structural applicability
    domain, or a retrieved prior that the forecasts contradict. The answer then states the current
    limitation, the missing evidence, why it matters, the smallest informative action, the possible
    outcomes and the rule after each.
  - `ingest` closes the loop: a real result passes through the registered rules, becomes an evidence
    card and a calibration entry (the probability the system gave the realised reading), and the
    compound's case is superseded, never edited; once one hypothesis survives the case is closed and
    becomes a reference case in the next memory snapshot.
  - Calibration status is stated, not implied. The development replay measured that wrong-elimination
    forecasts on chosen actions run low; `CALIBRATION_NOTE` says so and is replaced by the measured
    figures when the analysis exists.
- Interfaces: `UserProblem`, `DecisionSupport`, `Report`, `CALIBRATION_NOTE`
- Depends on: research/scientific_case_memory, research/belief_planning (planner, world),
  research/dynamic_world_model (registered evidence update), research/sequence_audit (menu legality)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np

from maestro.acquisition import outcome_consequences
from research.belief_planning import world as W
from research.belief_planning.planner import plan_measurement, update_belief
from research.scientific_case_memory import adaptation_model as AM
from research.scientific_case_memory import case_retrieval as CR
from research.scientific_case_memory import case_schema as S
from research.scientific_case_memory import evidence_cards as EC
from research.scientific_case_memory import hypothesis_graph as HG
from research.scientific_case_memory import world as CW

CALIBRATION_NOTE = ("Forecast probabilities of a wrong elimination have not been calibrated on held-out units. In the "
                    "development replay they ran low on the actions a planner chose; read a forecast wrong-elimination "
                    "probability as a floor, not an estimate.")
LABEL_TEXT = {W.MATCH_H1: "profile matches hypothesis 1", W.MATCH_H2: "profile matches hypothesis 2",
              W.UNRESOLVED: "response matches neither class better", W.ABSENT: "no detectable response",
              W.QC_FAILED: "measurement fails its quality rule"}
OUTCOME_OF_LABEL = {W.MATCH_H1: "eliminate_b", W.MATCH_H2: "eliminate_a", W.UNRESOLVED: "ambiguous",
                    W.ABSENT: "undetected", W.QC_FAILED: "quality_failed"}
LABEL_OF_OUTCOME = {v: k for k, v in OUTCOME_OF_LABEL.items()}
STATUS_OF_OUTCOME = {"eliminate_a": S.MeasurementStatus.QUALIFIED, "eliminate_b": S.MeasurementStatus.QUALIFIED,
                     "ambiguous": S.MeasurementStatus.AMBIGUOUS, "undetected": S.MeasurementStatus.UNDETECTED,
                     "quality_failed": S.MeasurementStatus.QC_FAILED}


@dataclass(frozen=True)
class UserProblem:
    """What a user provides. `history` holds real readings already obtained, each a dict with `key`
    (cell line, hours, nM), `outcome` (registered runner outcome) and `agreement`."""

    name: str
    smiles: str | None
    hypotheses: tuple[str, str]
    history: tuple[Mapping, ...] = ()
    user_goal: str = "decide which mechanism class the compound belongs to"
    constraints: tuple[str, ...] = ()
    unit: str | None = None


@dataclass
class Report:
    assessment: dict
    graph: dict
    precedents: dict
    forecasts: list
    plan: dict
    recommendation: dict
    branches: list
    confidence: dict
    abstention: dict | None
    calibration_note: str = CALIBRATION_NOTE

    def payload(self) -> dict:
        return {"assessment": self.assessment, "graph": self.graph, "precedents": self.precedents,
                "forecasts": self.forecasts, "plan": self.plan, "recommendation": self.recommendation,
                "branches": self.branches, "confidence": self.confidence, "abstention": self.abstention,
                "calibration_note": self.calibration_note}


class DecisionSupport:
    def __init__(self, inputs, snapshot, *, config: str = "cm_full_prior", price: float = 0.02,
                 calibration_note: str = CALIBRATION_NOTE):
        from research.scientific_case_memory import protocol_library as PL
        from research.sequence_audit import policies as P

        self.inputs, self.snapshot, self.price, self.calibration_note = inputs, snapshot, price, calibration_note
        self.P, self.setting = P, inputs.setting
        ctx = inputs.ctx
        self.world = CW.CaseMemoryWorld(snapshot.index, ctx.params, inputs.training, config=CW.CONFIGS[config],
                                        context=AM.Context(inputs.dataset, "transcriptome"), adaptation=snapshot.adaptation)
        self.protocol = {p.action_id: p for p in snapshot_protocol(inputs)}
        self.keys = {PL.action_id(k): tuple(k) for k in ctx.tier.keys}
        self.pool = tuple(ctx.tier.pool)

    # ------------------------------------------------------------------ 1. what is known
    def assess(self, problem: UserProblem) -> dict:
        world = self.world
        added = world.add_query_compound(problem.name, problem.smiles)
        history = []
        for step in problem.history:
            status = STATUS_OF_OUTCOME[step["outcome"]]
            history.append({"action_id": _aid(step["key"]), "status": status.value, "outcome": step["outcome"],
                            "reading": LABEL_OF_OUTCOME[step["outcome"]],
                            "replicate_agreement": step.get("agreement"), "usable_for_mechanism": status is S.MeasurementStatus.QUALIFIED})
        done = {h["action_id"] for h in history}
        planned = [a for a in self.keys if a in self.protocol and self.protocol[a].available]
        missing = [a for a in planned if a not in done]
        sim = world._neighbourhood(problem.name, problem.unit)[0]
        best = float(sim.max()) if len(sim) and world.pos.get(problem.name, -1) >= 0 else float("nan")
        in_domain = bool(np.isfinite(best) and best >= CR.SIM_FLOOR)
        cannot = ["target engagement, proximal function and pathway state were not measured; the transcriptome is one observed layer",
                  "a class label is a curated annotation of reference compounds, not ground truth",
                  "nothing here says whether the compound engages a target"]
        if not in_domain:
            cannot.append("the compound has no structural precedent above the applicability floor; class-level frequencies are all "
                          "the memory can offer")
        if any(h["status"] == "qc_failed" for h in history):
            cannot.append("a measurement failed its quality rule and constrains no hypothesis")
        return {"history": history, "missing_conditions": missing, "in_distribution": in_domain,
                "nearest_precedent_similarity": None if not np.isfinite(best) else round(best, 3),
                "structure_available": world.pos.get(problem.name, -1) >= 0, "structure_registered_now": bool(added),
                "trustworthy": [h["action_id"] for h in history if h["status"] in ("qualified", "undetected", "ambiguous")],
                "cannot_be_inferred": cannot,
                "leakage_checks": {"user_compound_in_reference_memory": problem.name in self.snapshot.index.cases,
                                   "same_unit_precedents_excluded": True}}

    # ------------------------------------------------------------------ 2. graph
    def graph(self, problem: UserProblem, assessment: dict) -> HG.HypothesisGraph:
        h1, h2 = problem.hypotheses
        statuses = {"engagement": S.MeasurementStatus.NOT_PLANNED, "function": S.MeasurementStatus.NOT_PLANNED,
                    "pathway": S.MeasurementStatus.NOT_PLANNED, "cell_state": S.MeasurementStatus.NOT_PLANNED,
                    "phenotype": S.MeasurementStatus.NOT_PLANNED,
                    "assay": S.MeasurementStatus.QUALIFIED if any(h["usable_for_mechanism"] for h in assessment["history"])
                    else S.MeasurementStatus.AMBIGUOUS if assessment["history"] else S.MeasurementStatus.NOT_PLANNED}
        base = HG.template_for(problem.name, problem.name, None, self.inputs.dataset, "transcriptome shift", statuses,
                               action_ids=list(self.keys))
        hyps = [HG.Hypothesis("H_a", f"The compound acts through the mechanism class '{h1}'.", tuple(base.hypotheses[0].path),
                              ("the reference compounds of this class are a valid template",), {}, False,
                              next_test="the condition the planner recommends"),
                HG.Hypothesis("H_b", f"The compound acts through the mechanism class '{h2}'.", tuple(base.hypotheses[0].path),
                              ("the reference compounds of this class are a valid template",), {}, False),
                HG.Hypothesis("H_other", "The compound acts through neither class; both templates are wrong.",
                              ("intervention", "assay"), ("the pool of classes is incomplete",), {}, True),
                HG.Hypothesis("H_artifact", "The reading reflects a detection or batch artifact, not the compound.",
                              ("intervention", "assay"), ("the release's control design cannot absorb the batch",), {}, True),
                HG.Hypothesis("H_irrelevant", "The molecular response is real but irrelevant to any phenotype of interest.",
                              ("intervention", "assay"), (), {}, True)]
        return HG.HypothesisGraph(list(base.nodes.values()), base.edges, base.hyperedges, hyps)

    # ------------------------------------------------------------------ 3-4. retrieval and forecast
    def _menu(self, problem: UserProblem, executed: Sequence[Mapping]):
        steps = [{"key": list(s["key"])} for s in executed]
        left = self.setting.budget_days - sum(self.setting.days(tuple(s["key"])) for s in executed)
        if len(steps) >= self.setting.max_measurements:
            return [], left
        return list(self.P.legal_menu(self.setting, steps, left)), left

    def precedents(self, problem: UserProblem, key: tuple, top_k: int = 3) -> dict:
        world = self.world
        row = world.pos.get(problem.name, -1)
        fp = world.fp[row] if row >= 0 else None
        query = CR.RetrievalQuery(problem.name, key, problem.hypotheses,
                                  AM.Context(self.inputs.dataset, "transcriptome", key[0], float(key[1]), float(key[2])), fp,
                                  problem.unit, {"assay": self.snapshot.cases()[0].context_fingerprint["assay"]})
        out = world.retriever.retrieve(query, top_k=top_k)
        out["hypothesis_prior"] = world.hypothesis_prior(problem.name, *problem.hypotheses, unit=problem.unit)
        return out

    def forecasts(self, problem: UserProblem, menu, real) -> tuple[list, dict]:
        world = self.world
        h1, h2 = problem.hypotheses
        records, refusals = [], {}
        for key in menu:
            aid = _aid(key)
            f = world.forecast(tuple(key), h1, h2, problem.name, real)
            if f.refusal:
                refusals[aid] = "insufficient_support"
                records.append({"action_id": aid, "refusal": "insufficient_support", "detail": f.refusal})
                continue
            support = world.support_report(tuple(key), h1, h2, problem.name)
            sim = world._neighbourhood(problem.name, problem.unit)[0]
            best = float(sim.max()) if len(sim) and world.pos.get(problem.name, -1) >= 0 else float("nan")
            for b in f.branches:
                n = max(int(b.support), 0)
                p_hit = sum(v for k, v in b.probabilities.items() if k in (W.MATCH_H1, W.MATCH_H2))
                width = math.sqrt(max(p_hit * (1 - p_hit), 1e-9) / (n + 2))
                records.append({
                    "action_id": aid, "hypothesis": b.hypothesis, "probabilities": {k: round(v, 4) for k, v in b.probabilities.items()},
                    "predicted_state_transition": self._transition(key, b.hypothesis, problem),
                    "outcome_probability": round(p_hit, 4), "uncertainty_interval": [round(max(0.0, p_hit - 1.645 * width), 4),
                                                                                     round(min(1.0, p_hit + 1.645 * width), 4)],
                    "support": n, "low_support": bool(support.get(b.hypothesis, {}).get("low_support", n < CW.MIN_SUPPORT)),
                    "applicability": "in_domain" if np.isfinite(best) and best >= CR.SIM_FLOOR else "class_level_only",
                    "out_of_distribution": bool(not np.isfinite(best) or best < CR.SIM_FLOOR),
                    "calibration_status": "uncalibrated_on_held_out_units", "model_version": f.model_version,
                    "basis": f.basis, "evidence_class": S.EvidenceClass.MODEL_PREDICTION.value})
        return records, refusals

    def _transition(self, key, hypothesis, problem) -> dict:
        """The class's mean measured state change at a condition: a case-based state prediction, not a simulation."""
        t = self.inputs.ctx.ft.tables.get(tuple(key))
        if t is None:
            return {"available": False}
        rows = [i for i, k in enumerate(t.klass) if k == hypothesis]
        if not rows:
            return {"available": False, "reason": "no reference of this class measured here"}
        Y = np.asarray(t.Y)[rows]
        mean = Y.mean(0)
        return {"available": True, "references": len(rows), "mean_shift_norm": round(float(np.linalg.norm(mean)), 4),
                "direction_consistency": round(float(np.mean([_cos(y, mean) for y in Y])), 3),
                "note": "mean measured shift of the class's reference compounds at this condition"}

    # ------------------------------------------------------------------ 5. plan
    def plan(self, problem: UserProblem, real, belief, menu):
        world = self.world
        h1, h2 = problem.hypotheses
        by_id = {_aid(k): tuple(k) for k in self.setting.keys}
        done = [tuple(s["key"]) for s in problem.history]

        def legal(hyp):
            keys = done + [by_id[a] for a, _ in hyp]
            if len(keys) >= self.setting.max_measurements:
                return ()
            left = self.setting.budget_days - sum(self.setting.days(k) for k in keys)
            return tuple(self.P.make_action(k, h1, h2, self.setting)
                         for k in self.P.legal_menu(self.setting, [{"key": list(k)} for k in keys], left))

        def forecast(action, hyp):
            return world.forecast(by_id[action.identifier], h1, h2, problem.name,
                                  real + tuple((by_id[a], lab) for a, lab in hyp))

        consequences = outcome_consequences(self.P.V.registered_rules(h1, h2))
        depth = self.setting.max_measurements - len(done)
        if depth <= 0 or not menu:
            return None, consequences
        return plan_measurement((h1, h2), belief, legal, forecast, consequences, horizon=depth, price=self.price), consequences

    # ------------------------------------------------------------------ 6. the answer
    def answer(self, problem: UserProblem) -> Report:
        h1, h2 = problem.hypotheses
        assessment = self.assess(problem)
        graph = self.graph(problem, assessment)
        real = tuple((tuple(s["key"]), LABEL_OF_OUTCOME[s["outcome"]]) for s in problem.history)
        prior = self.world.hypothesis_prior(problem.name, h1, h2, problem.unit)
        belief = dict(prior)
        for i, (key, label) in enumerate(real):
            belief = update_belief(belief, self.world.forecast(key, h1, h2, problem.name, real[:i]), label)
        state = self._evidence_state(problem)
        menu, left = self._menu(problem, problem.history)
        plan, consequences = self.plan(problem, real, belief, menu)
        forecasts, refusals = self.forecasts(problem, menu, real)
        ledger = self._ledger(problem, forecasts, prior)
        candidates = sorted(state.candidates)
        abst = self._abstention(problem, assessment, plan, forecasts, refusals, state, prior, belief, menu)
        recommendation, branches = {}, []
        if plan is not None and plan.chosen is not None:
            key = self.keys[plan.chosen]
            recommendation = self._recommend(problem, key, plan, forecasts, real)
            precedents = self.precedents(problem, key)
            branches = self._branches(problem, key, plan, consequences, belief, forecasts, prior)
        else:
            key0 = self.keys[menu and _aid(menu[0]) or next(iter(self.keys))]
            precedents = self.precedents(problem, key0)
        confidence = self._confidence(ledger, assessment, forecasts, precedents, prior, graph)
        return Report(assessment, graph.payload(), _precedent_payload(precedents), forecasts,
                      plan.payload() if plan is not None else {"status": "no_plan", "reason":
                                                                "no measurement is legal or the budget is spent"},
                      recommendation, branches, confidence, abst, self.calibration_note)

    def _evidence_state(self, problem: UserProblem):
        """The candidate set after the registered rules have read the real history (only qualified readings act)."""
        from research.dynamic_world_model import common as C
        from research.sequence_audit import policies as P

        h1, h2 = problem.hypotheses
        actions = {tuple(k): P.make_action(tuple(k), h1, h2, self.setting) for k in self.setting.keys}
        contrast = P.E.contrast_for(h1, h2, list(actions.values()))
        state = P.EvidenceState.open(contrast.hypotheses)
        for step in problem.history:
            key = tuple(step["key"])
            qc = step["outcome"] != "quality_failed"
            state, _, _ = C.evidence_update(state, contrast, actions[key], key, {"outcome": step["outcome"]}, h1, h2,
                                            qc=qc, agreement=float(step.get("agreement") or float("nan")),
                                            source=f"user:{problem.name}")
        return state

    def _ledger(self, problem, forecasts, prior) -> EC.EvidenceLedger:
        ledger = EC.EvidenceLedger()
        state_steps = []
        for i, s in enumerate(problem.history):
            outcome = s["outcome"]
            step = {"state": {"eliminate_a": "measured_eliminating", "eliminate_b": "measured_eliminating",
                              "ambiguous": "measured_ambiguous", "undetected": "measured_undetected",
                              "quality_failed": "quality_failed"}[outcome], "action": _aid(s["key"]),
                    "qc": outcome != "quality_failed", "readout": {"ambiguous": "ambiguous", "undetected": "undetected"}.get(outcome),
                    "eliminated": [problem.hypotheses[1] if outcome == "eliminate_b" else problem.hypotheses[0]]
                    if outcome in ("eliminate_a", "eliminate_b") else []}
            card = EC.card_from_step(problem.name, step, problem.hypotheses, i)
            if card is not None:
                ledger.add(card)
            state_steps.append(step)
        seen = set()
        for f in forecasts:
            if f.get("refusal") or f["action_id"] in seen:
                continue
            seen.add(f["action_id"])
            ledger.add(EC.EvidenceCard(f"forecast:{f['action_id']}", S.EvidenceClass.MODEL_PREDICTION,
                                       f"Forecast readings of {f['action_id']} under each hypothesis (support {f['support']}).",
                                       f["model_version"], f["action_id"]))
        if abs(prior[problem.hypotheses[0]] - 0.5) > 0.05:
            ledger.add(EC.EvidenceCard("prior", S.EvidenceClass.HISTORICAL_ANALOGY,
                                       f"Structural precedents favour '{max(prior, key=prior.get)}' "
                                       f"({max(prior.values()):.2f}); advisory only.", "case_memory"))
        return ledger

    def _recommend(self, problem, key, plan, forecasts, real) -> dict:
        aid = _aid(key)
        p = self.protocol[aid]
        h1, h2 = problem.hypotheses
        expected = {}
        for f in forecasts:
            if f.get("action_id") == aid and "hypothesis" in f:
                top = sorted(f["probabilities"].items(), key=lambda kv: -kv[1])[:2]
                expected[f["hypothesis"]] = {LABEL_TEXT[k]: v for k, v in top}
                expected[f["hypothesis"]]["probability_of_an_eliminating_reading"] = f["outcome_probability"]
        ev = plan.evaluations.get(aid)
        expert = self._expert_order_action(problem)
        return {"action": aid, "expert_order_action": expert,
                "differs_from_expert_order": bool(expert is not None and expert != aid),
                "purpose": f"separate '{h1}' from '{h2}' by the registered profile-similarity rule",
                "expected_result_by_hypothesis": expected, "control_requirements": list(p.controls),
                "time_h": key[1], "dose_nM": key[2], "cell_line": key[0], "readout": p.readout,
                "cost_wells": p.cost_wells, "assay_days": p.duration_days,
                "detection_power": round(p.detection_power, 3) if p.detection_power is not None
                else "not claimed (fewer than 8 references)",
                "prerequisites": list(p.prerequisites) or ["none; a time not earlier than one already measured"],
                "stopping_condition": p.stopping_condition,
                "forecast_value": None if ev is None else {"expected_utility": round(ev.utility, 4), "p_correct": round(ev.p_correct, 4),
                                                           "p_wrong": round(ev.p_wrong, 4), "p_wrong_upper": round(ev.p_wrong_upper, 4),
                                                           "expected_measurements": round(ev.measurements, 3)}}

    def _expert_order_action(self, problem: UserProblem) -> str | None:
        """The fixed expert order's next condition, the baseline a planner must justify leaving."""
        menu, _ = self._menu(problem, problem.history)
        allowed = {tuple(k) for k in menu}
        for key in self.setting.fixed_order:
            if tuple(key) in allowed:
                return _aid(key)
        return None

    def _branches(self, problem, key, plan, consequences, belief, forecasts, prior) -> list:
        aid = _aid(key)
        h1, h2 = problem.hypotheses
        mixed = {}
        for f in forecasts:
            if f.get("action_id") == aid and "hypothesis" in f:
                for lab, pr in f["probabilities"].items():
                    mixed[lab] = mixed.get(lab, 0.0) + belief.get(f["hypothesis"], 0.0) * pr
        favoured = max(prior, key=prior.get) if abs(prior[h1] - 0.5) > 0.05 else None
        out = []
        for label in (W.MATCH_H1, W.MATCH_H2, W.UNRESOLVED, W.ABSENT, W.QC_FAILED):
            removes = sorted(consequences.get(label, frozenset()))
            nxt = plan.contingent.get(label)
            entry = {"if_reading": LABEL_TEXT[label], "probability": round(mixed.get(label, 0.0), 4), "removes": removes}
            if label in (W.MATCH_H1, W.MATCH_H2):
                survivor = h1 if label == W.MATCH_H1 else h2
                contradict = favoured is not None and favoured != survivor
                entry.update({"case": "contradictory_to_precedent" if contradict else "positive",
                              "then": f"the registered rule removes '{h2 if label == W.MATCH_H1 else h1}'; '{survivor}' is the one "
                                      f"compatible hypothesis" + ("; the structural precedents favoured the other class, so "
                                                                  "keep the disagreement in the record and confirm with an "
                                                                  "orthogonal measurement before acting" if contradict else ""),
                              "next_action": None if not contradict else "an orthogonal assay of the surviving class"})
            elif label == W.UNRESOLVED:
                entry.update({"case": "ambiguous", "then": "no hypothesis is removed; the profile is detected but matches neither class better",
                              "next_action": nxt or "orthogonal assay or a stronger dose"})
            elif label == W.ABSENT:
                entry.update({"case": "negative", "then": "no hypothesis is removed; absence cannot separate a failed perturbation "
                                                            "from a mechanism inert at this condition",
                              "next_action": nxt or "defer: no legal measurement remains"})
            else:
                entry.update({"case": "technically_invalid", "then": "do not update any biological hypothesis; a failed measurement "
                                                                       "updates detection feasibility only",
                              "next_action": nxt or "repeat once if budget remains, otherwise defer"})
            out.append(entry)
        out.append({"if_reading": "no result returned", "case": "missing_result", "probability": None,
                    "then": "hold the state; nothing is updated and the plan is unchanged", "next_action": aid})
        return out

    def _abstention(self, problem, assessment, plan, forecasts, refusals, state, prior, belief, menu) -> dict | None:
        reasons = []
        if state.resolved:
            return None
        if plan is None or plan.chosen is None:
            reasons.append("no_action_chosen:" + (plan.reason if plan is not None and plan.reason else "no_legal_measurement"))
        low = [f for f in forecasts if f.get("low_support")]
        if plan is not None and plan.chosen and any(f.get("low_support") for f in forecasts if f.get("action_id") == plan.chosen):
            reasons.append("chosen_action_rests_on_fewer_than_six_reference_units")
        if not assessment["in_distribution"]:
            reasons.append("target_outside_structural_applicability_domain")
        if refusals:
            reasons.append("forecast_refused_for:" + ",".join(sorted(refusals)))
        if not reasons:
            return None
        h1, h2 = problem.hypotheses
        eliminating = [f["outcome_probability"] for f in forecasts if "hypothesis" in f]
        undecidable = (plan is not None and plan.chosen is None and eliminating and max(eliminating) < 0.05
                       and not any(f.get("low_support") for f in forecasts if "hypothesis" in f))
        if undecidable:
            limitation = (f"no legal condition has a non-negligible chance of producing a reading that removes a hypothesis "
                          f"(the largest forecast probability is {max(eliminating):.3f}); the forecasts are supported, so this is a "
                          "finding about the menu, not a gap in the memory")
            missing = "a condition or assay outside the current menu with a validated discriminating profile"
            why = "buying a measurement that cannot change the decision only spends wells and days"
            action = ("extend the menu (another cell line, a longer exposure, or a functional or engagement assay); if a "
                      f"measurement must be taken, the expert order's next condition, {self._expert_order_action(problem)}")
        else:
            limitation = "the memory cannot forecast a decisive reading reliably here"
            missing = ("a reading at a condition where at least one hypothesis's references are numerous and "
                       "structurally close to the compound")
            why = "a forecast resting on class-level frequencies alone cannot rank actions by their value for the decision"
            action = (f"the expert order's next condition, {self._expert_order_action(problem)}, because the ranking of actions "
                      "by forecast value is not reliable here")
        return {"reasons": reasons, "current_limitation": limitation,
                "missing_evidence": missing,
                "why_it_matters": why,
                "minimum_informative_next_action": action,
                "possible_outcomes": ["a qualified reading that removes one of the two classes",
                                      "an unresolved or absent reading that removes nothing"],
                "decision_rule_after_each": {"qualified": "the registered rule removes the other class; decide",
                                             "not_qualified": "no update; use the remaining budget, then defer"},
                "low_support_forecasts": len(low)}

    def _confidence(self, ledger, assessment, forecasts, precedents, prior, graph) -> dict:
        sections = ledger.sections()
        kish = max((e["kish"] for e in precedents["hypotheses"].values()), default=0.0)
        weak = f"{kish:.1f}" if kish < 2.0 and abs(prior[next(iter(prior))] - 0.5) > 0.05 else None
        return {"measured_fact": [c.statement for c in sections["measured_fact"]],
                "qualified_evidence": [c.statement for c in sections["qualified_evidence"]],
                "model_prediction": [c.statement for c in sections["model_prediction"]],
                "historical_analogy": [c.statement + (f" It rests on {weak} effective structural precedents (fewer than two): weak."
                                                      if weak is not None else "")
                                       for c in sections["historical_analogy"]] or
                                      [f"{len(precedents['hypotheses'][h]['cases'])} structural precedents retrieved for '{h}'"
                                       for h in precedents["hypotheses"]],
                "mechanistic_inference": [f"{e.source} to {e.target}: {e.relation_type} ({e.evidence_strength})"
                                          for e in graph.edges if e.evidence_strength in ("predicted", "speculative")][:4] +
                                         [f"layers with no measurement: {', '.join(graph.unmeasured_layers())}"],
                "speculation": [h.claim for h in graph.hypotheses if h.advisory]}

    # ------------------------------------------------------------------ 10. closing the loop
    def ingest(self, problem: UserProblem, report: Report, key: tuple, outcome: str, *, agreement: float | None = None,
               store=None, created_at: str = "2026-09-29") -> dict:
        """A real result arrives: register it, grade the forecast, and supersede the compound's case."""
        h1, h2 = problem.hypotheses
        aid = _aid(key)
        real = tuple((tuple(s["key"]), LABEL_OF_OUTCOME[s["outcome"]]) for s in problem.history)
        label = LABEL_OF_OUTCOME[outcome]
        f = self.world.forecast(tuple(key), h1, h2, problem.name, real)
        prior = self.world.hypothesis_prior(problem.name, h1, h2, problem.unit)
        belief = dict(prior)
        for i, (k, lab) in enumerate(real):
            belief = update_belief(belief, self.world.forecast(k, h1, h2, problem.name, real[:i]), lab)
        given = sum(belief[b.hypothesis] * b.probabilities.get(label, 0.0) for b in f.branches) if not f.refusal else None
        new_history = tuple(problem.history) + ({"key": tuple(key), "outcome": outcome, "agreement": agreement},)
        updated = UserProblem(problem.name, problem.smiles, problem.hypotheses, new_history, problem.user_goal,
                              problem.constraints, problem.unit)
        state = self._evidence_state(updated)
        step = {"state": {"eliminate_a": "measured_eliminating", "eliminate_b": "measured_eliminating",
                          "ambiguous": "measured_ambiguous", "undetected": "measured_undetected",
                          "quality_failed": "quality_failed"}[outcome], "action": aid, "qc": outcome != "quality_failed",
                "readout": {"ambiguous": "ambiguous", "undetected": "undetected"}.get(outcome),
                "eliminated": sorted(set(problem.hypotheses) - set(state.candidates)) if outcome.startswith("eliminate") else []}
        card = EC.card_from_step(problem.name, step, problem.hypotheses, len(new_history))
        entry = None if given is None else S.CalibrationEntry(f.model_version, aid, float(given), 1.0, "reading_probability",
                                                              self.snapshot.snapshot_id)
        closed = state.resolved
        case = None
        if store is not None:
            case = self._case(updated, state, entry, created_at, closed)
            if case.case_id in store:
                store.supersede(store.get(case.case_id), **{k: getattr(case, k) for k in (
                    "initial_observations", "real_measurements", "qualified_evidence", "hypothesis_updates", "final_decision",
                    "next_action", "calibration_history", "failure_modes", "case_kind", "context_fingerprint")})
                case = store.get(case.case_id)
            else:
                store.append(case)
        return {"candidates": sorted(state.candidates), "eliminated": sorted(state.eliminated), "resolved": closed,
                "evidence_card": card, "calibration_entry": entry,
                "probability_given_to_realised_reading": None if given is None else round(float(given), 4),
                "case_id": case.case_id if case else None, "case_version": case.case_version if case else None,
                "biological_update_allowed": card is not None and card.evidence_class is S.EvidenceClass.QUALIFIED_EVIDENCE}

    def _case(self, problem: UserProblem, state, entry, created_at, closed) -> S.Case:
        h1, h2 = problem.hypotheses
        obs, meas, cards = [], [], []
        for s in problem.history:
            status = STATUS_OF_OUTCOME[s["outcome"]]
            aid = _aid(s["key"])
            obs.append(S.Observation(aid, status, "transcriptome", s["key"][0], float(s["key"][1]), float(s["key"][2]),
                                     None, None, s.get("agreement"), status is not S.MeasurementStatus.UNDETECTED
                                     if status.biological else None))
            if status.biological:
                meas.append(S.Measurement(aid, status, LABEL_OF_OUTCOME[s["outcome"]], 1, f"user:{problem.name}"))
            if status is S.MeasurementStatus.QUALIFIED:
                cards.append({"action_id": aid, "statement": f"{aid} removed a hypothesis",
                              "evidence_class": S.EvidenceClass.QUALIFIED_EVIDENCE.value})
        klass = next(iter(state.candidates)) if closed else None
        fp = {"dataset": self.inputs.dataset, "assay": "transcriptome", "context": f"{self.inputs.dataset}:{self.inputs.tier}",
              "compound": problem.name, "unit": problem.unit or problem.name, "hypothesis_class": klass, "is_training": False,
              "smiles": problem.smiles, "snapshot": self.snapshot.snapshot_id}
        first = self.snapshot.cases()[0]
        return S.Case(
            case_id=f"user:{self.inputs.dataset}:{self.inputs.tier}:{problem.name}", case_version=1,
            case_kind=S.CaseKind.CANONICAL, problem_type=S.ProblemType.MECHANISM_CONTRAST_TRANSCRIPTOMIC,
            problem_statement=f"Which of '{h1}' and '{h2}' does {problem.name} act through?", user_question=problem.user_goal,
            raw_data_references=first.raw_data_references, data_quality_report={"usable": bool(meas)}, context_fingerprint=fp,
            initial_observations=tuple(obs), initial_hypotheses=(S.HypothesisClaim("H_a", h1), S.HypothesisClaim("H_b", h2)),
            candidate_actions=first.candidate_actions, retrieved_knowledge=(), virtual_cell_predictions=(),
            predicted_outcome_branches=(), real_measurements=tuple(meas), measurement_quality={}, qualified_evidence=tuple(cards),
            hypothesis_updates=(), final_decision={"status": "decided" if closed else "open",
                                                   "basis": "the registered evidence rules left one compatible hypothesis" if closed
                                                   else "candidate set still holds more than one hypothesis",
                                                   "candidates": sorted(state.candidates)},
            next_action={}, failure_modes=(), adaptation_map=(),
            calibration_history=(entry,) if entry is not None else (),
            provenance={"builder": "maestro_vc_v1.system", "sources": dict(first.provenance["sources"]),
                        "created_at": created_at, "snapshot": self.snapshot.snapshot_id})

    # ------------------------------------------------------------------ rendering
    def render(self, problem: UserProblem, report: Report) -> str:
        a, r = report.assessment, report.recommendation
        h1, h2 = problem.hypotheses
        lines = [f"# Decision support: {problem.name}", "", f"Question: {problem.user_goal}. Competing classes: **{h1}** and **{h2}**.", "",
                 "## 1. Current data assessment", ""]
        if a["history"]:
            lines += [f"- {h['action_id']}: {h['status']} ({LABEL_TEXT[h['reading']]})" for h in a["history"]]
        else:
            lines.append("- No reading has been obtained yet.")
        lines += [f"- Conditions not yet measured: {len(a['missing_conditions'])}",
                  f"- In distribution: {'yes' if a['in_distribution'] else 'no'} (nearest structural precedent similarity "
                  f"{a['nearest_precedent_similarity']})"]
        lines += ["- Cannot be inferred: " + "; ".join(a["cannot_be_inferred"]), "", "## 2. Competing hypotheses", ""]
        for h in report.graph["hypotheses"]:
            lines.append(f"- **{h['hypothesis_id']}** ({'advisory' if h['advisory'] else 'registered'}): {h['claim']}")
        lines += ["", "## 3. Retrieved precedent cases", ""]
        for hyp, entry in report.precedents["hypotheses"].items():
            lines.append(f"- For '{hyp}': {len(entry['cases'])} precedents, effective number {entry['kish']:.1f}"
                         f"{'' if entry['usable'] else ' (' + str(entry['reason']) + ')'}")
            for c in entry["cases"]:
                lines.append(f"  - {c['case_id']}: {c['why']}; matches {', '.join(c['matches']) or 'none'}; "
                             f"adaptation cost {c['adaptation']['cost']:.2f} ({c['adaptation']['basis']})")
        lines += ["- Retrieved prior over the two classes (advisory): " +
                  ", ".join(f"{k} {v:.2f}" for k, v in report.precedents["hypothesis_prior"].items()),
                  "", "## 4. Virtual-cell forecast", ""]
        shown = set()
        for f in report.forecasts:
            if "hypothesis" not in f or f["action_id"] != (r.get("action") if r else f["action_id"]) or (f["action_id"], f["hypothesis"]) in shown:
                continue
            shown.add((f["action_id"], f["hypothesis"]))
            lines.append(f"- {f['action_id']} if '{f['hypothesis']}': eliminating reading {f['outcome_probability']:.2f} "
                         f"{f['uncertainty_interval']}, support {f['support']} units, {f['applicability']}, {f['calibration_status']}")
        lines += ["", f"Calibration: {report.calibration_note}", "", "## 5. Recommended next action", ""]
        if r:
            lines += [f"- Action: **{r['action']}** ({r['cell_line']}, {r['time_h']:g} h, {r['dose_nM']:g} nM)",
                      f"- Purpose: {r['purpose']}",
                      f"- Cost: {r['cost_wells']:g} wells plus shared controls, {r['assay_days']:g} assay days; detection power: {r['detection_power']}",
                      f"- Controls: {'; '.join(r['control_requirements'])}", f"- Prerequisites: {'; '.join(r['prerequisites'])}",
                      f"- Stopping: {r['stopping_condition']}"]
            for hyp, e in r["expected_result_by_hypothesis"].items():
                lines.append(f"- If '{hyp}': " + "; ".join(f"{k} {v:.2f}" for k, v in e.items()))
            lines.append(f"- The fixed expert order would measure {r['expert_order_action']} next"
                         + (" (the planner departs from it)" if r["differs_from_expert_order"] else " (the planner agrees)"))
            if report.abstention:
                lines.append("- **Provisional.** " + "; ".join(report.abstention["reasons"]) + ". The ranking of actions by "
                             "forecast value is not reliable here; the expert order is the safer default.")
        else:
            lines.append("- No action is recommended; see abstention.")
        lines += ["", "## 6. Branching interpretation plan", ""]
        if not report.branches:
            lines.append("- No measurement is recommended, so there is nothing to branch on; the rules after each outcome are in the abstention below.")
        for b in report.branches:
            lines.append(f"- **{b['case']}** ({b['if_reading']}, p={b['probability'] if b['probability'] is not None else 'n/a'}): "
                         f"{b['then']}; next: {b['next_action']}")
        lines += ["", "## 7. Confidence and abstention", ""]
        for k, v in report.confidence.items():
            lines.append(f"- {k.replace('_', ' ')}: " + (" | ".join(v[:3]) if v else "none"))
        if report.abstention:
            ab = report.abstention
            lines += ["", "**Abstention.** " + "; ".join(ab["reasons"]), f"- Current limitation: {ab['current_limitation']}",
                      f"- Missing evidence: {ab['missing_evidence']}", f"- Why it matters: {ab['why_it_matters']}",
                      f"- Minimum informative next action: {ab['minimum_informative_next_action']}"]
        return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------------------- helpers
def _aid(key) -> str:
    line, t, dose = key
    return f"{line}|{int(t):03d}h|{int(dose):05d}nM"


def _cos(a, b) -> float:
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    return float(a @ b / (na * nb)) if na > 1e-12 and nb > 1e-12 else 0.0


def snapshot_protocol(inputs):
    from research.scientific_case_memory import build_cases as BC

    return BC._protocol(inputs)


def _precedent_payload(p: dict) -> dict:
    out = {"stage1": p["stage1"], "hypothesis_prior": {k: round(v, 4) for k, v in p["hypothesis_prior"].items()}, "hypotheses": {}}
    for h, entry in p["hypotheses"].items():
        out["hypotheses"][h] = {"kish": entry["kish"], "usable": entry["usable"], "reason": entry.get("reason"),
                                "cases": [{"case_id": c.case_id, "score": round(c.score, 3), "why": c.why,
                                           "components": {k: round(v, 3) for k, v in c.components.items()},
                                           "reading": c.reading, "reading_kind": c.reading_kind, "matches": list(c.matches),
                                           "differences": dict(c.differences), "adaptation": dict(c.adaptation)}
                                          for c in entry["cases"]]}
    return out
