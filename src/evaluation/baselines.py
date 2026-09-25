"""Comparable policies that see public material and only evaluator-authorized results.

File summary
- Path: src/evaluation/baselines.py
- Purpose: Define ablation and baseline policies that replay frozen evaluation cases.
- Core points:
  - Baselines (expert, random edit, ordinary LLM) share MAESTRO's public action menu.
  - `MAESTROCorePolicy` runs the deterministic contrast with bounded directed repair.
  - Policies never see scoring rules or private outcomes; predictions are not real measurement results.
- Interfaces: `ExpertWorkflowPolicy`, `PredictionValuePolicy`, `LLMActionPolicy`, `MAESTROCorePolicy`, `RepairDisabledPolicy`, `RandomLegalEditPolicy`, `OutcomeAwareSelectionPolicy`, `MAESTROOrchestratorPolicy`, `DecisionSubmission`
- Depends on: agent.cases, agent.orchestrator, maestro, evaluation.cases
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from random import Random
from typing import Any, Callable, Mapping, Protocol, Sequence

from agent.orchestrator import MAESTROOrchestrator
from maestro import (
    DevelopmentAction,
    FunctionalInterventionProfile,
    MAESTROAgent,
    MeasurementStatus,
    MechanismHypothesis,
    RepairController,
    RepairKind,
    RepairLedger,
)

from maestro.models import EvidenceKind

from .cases import EvidenceMenuItem, ReplayView, RevealedEvidence, measurement_result_from_reveal


@dataclass(frozen=True)
class DecisionSubmission:
    """An auditable policy decision with its evidence, rationale, and validation errors."""

    decision: DevelopmentAction | None
    evidence_ids: tuple[str, ...]
    rationale: str
    limitations: tuple[str, ...]
    needs_more_evidence: bool
    origin: str
    validation_errors: tuple[str, ...] = ()
    submitted_payload: Mapping[str, Any] | None = None
    format_attempts: int = 1
    decision_ready: bool = True
    additional_evidence_available: bool | None = None
    required_missing_premises: tuple[str, ...] = ()


class ReplayPolicy(Protocol):
    name: str

    def next_action(self, view: ReplayView) -> str | None: ...

    def decide(self, view: ReplayView) -> DecisionSubmission | None: ...


class JSONCompleter(Protocol):
    def complete_json(self, messages: list[dict[str, Any]], **kwargs: Any) -> tuple[dict[str, Any], Any]: ...


def profile_from_view(view: ReplayView) -> FunctionalInterventionProfile:
    """Build the intervention profile from the qualified revealed fields of one view.

    Every policy derives the profile the same way, from the view rather than
    from an accumulator, so a premise cannot be measured for one policy and
    unknown for another. Functional fields keep their dedicated slot; every
    other qualified namespace enters ``measured_fields``, which is what lets a
    case declare a prerequisite this module does not know about. A record that
    fails the admission gate contributes nothing, so a derived summary or a
    quality-failed result never marks a premise measured.
    """

    qualified = [
        field
        for outcome in view.revealed
        if outcome.admits_biological_fields
        for field in outcome.interpretation_fields
    ]
    functional = {
        field.removeprefix("functional:"): MeasurementStatus.MEASURED
        for field in qualified
        if field.startswith("functional:")
    }
    other = {
        field: MeasurementStatus.MEASURED for field in qualified if not field.startswith("functional:")
    }
    return FunctionalInterventionProfile(
        mode="drug",
        functional_states=functional,
        measured_fields=other,
        context_identifier=view.case.context_identifier,
    )


class ExpertWorkflowPolicy:
    """Fixed public-menu baseline; it never receives scoring rules or private outcomes."""

    name = "fixed_expert"

    def next_action(self, view: ReplayView) -> str | None:
        # Every policy is filtered by the same executability rule, so a fixed
        # order is compared on which evidence it prefers, not on whether it
        # happens to propose an action whose premise is not yet measured.
        candidates = [item for item in view.available_actions() if _prerequisites_met(item, view)]
        order = ("functional_target_activity", "mode_matched_comparator", "broad_transcriptome")
        available = {item.action.identifier for item in candidates}
        selected = next((identifier for identifier in order if identifier in available), None)
        if selected is not None:
            return selected
        hypothesis_ids = {item["identifier"] for item in view.case.hypotheses}
        return next((item.action.identifier for item in candidates if set(item.action.distinguishes) == hypothesis_ids), None)

    def decide(self, view: ReplayView) -> DecisionSubmission | None:
        return _declared_outcome_decision(view, origin="interpretation_rule")


class PredictionValuePolicy(ExpertWorkflowPolicy):
    """Uncalibrated declared-score heuristic, not a trained prediction model."""

    name = "prediction_value_heuristic"

    def next_action(self, view: ReplayView) -> str | None:
        candidates = [item for item in view.available_actions() if _prerequisites_met(item, view)]
        if not candidates:
            return None
        return max(candidates, key=lambda item: (item.prediction_value / max(item.action.cost, 1e-9), -item.action.cost, item.action.identifier)).action.identifier


class LLMActionPolicy:
    """Ordinary LLM baseline with the same action menu and result-access boundary."""

    name = "ordinary_llm"

    def __init__(self, client: JSONCompleter):
        self._client = client

    def next_action(self, view: ReplayView) -> str | None:
        candidates = [item for item in view.available_actions() if _prerequisites_met(item, view)]
        if not candidates:
            return None
        data, _ = self._client.complete_json([
            {"role": "system", "content": "Choose one action_identifier from the supplied public menu. Return JSON only."},
            {"role": "user", "content": str(_public_prompt(view, candidates))},
        ])
        identifier = data.get("action_identifier") if isinstance(data, dict) else None
        return identifier if isinstance(identifier, str) and any(item.action.identifier == identifier for item in candidates) else None

    def decide(self, view: ReplayView) -> DecisionSubmission | None:
        if not view.revealed:
            return None
        return _request_submission(self._client, view)


class MAESTROCorePolicy(ExpertWorkflowPolicy):
    """Deterministic contrast and bounded directed repair, with no virtual-cell prediction."""

    name = "maestro_core"

    def __init__(self, controller: MAESTROAgent | None = None, *, max_repair_attempts: int = 3):
        self._controller = controller or MAESTROAgent()
        self._repair = RepairController(self._controller, max_attempts=max_repair_attempts)
        self._ledgers: dict[str, RepairLedger] = {}
        self._promises: dict[str, list[tuple[str, tuple[str, ...]]]] = {}
        self._active_case: str | None = None

    def next_action(self, view: ReplayView) -> str | None:
        self._active_case = view.case.identifier
        hypotheses = tuple(MechanismHypothesis(item["identifier"], item["description"], DevelopmentAction(item["development_action"])) for item in view.case.hypotheses[:2])
        if len(hypotheses) < 2:
            return None
        actions = tuple(item.action for item in view.available_actions())
        contrast = self._controller.construct_contrast("replay-contrast", hypotheses, (), actions)
        if contrast is None:
            return None
        profile = self._profile(view)
        check = self._controller.check_contrast(contrast, profile)
        if check.ready_for_mechanism_update and contrast.plan is not None:
            return contrast.plan.identifier
        ledger = self._ledgers.setdefault(view.case.identifier, RepairLedger())
        outcome = self._repair.run(contrast, check, actions, profile, ledger=ledger)
        if (
            outcome.proposal is not None
            and outcome.proposal.kind is RepairKind.DEFER
            and not outcome.check.ready_for_mechanism_update
        ):
            # The repair layer found no registered edit that could make this
            # contrast decide. Executing the compiled plan anyway would spend
            # the budget on a measurement already known not to separate the
            # explanations, which is the waste deferral exists to avoid.
            return None
        proposed = outcome.proposal.replacement_action if outcome.proposal is not None else None
        # While the plan still fails its check, the proposed replacement is the
        # step the loop wants to take; the current plan is only preferred once
        # the check passes, because otherwise it is the plan already known to fail.
        composed = outcome.proposal.composed_plan if outcome.proposal is not None else None
        if composed is not None:
            # A composed plan names the supplier that makes its readout
            # interpretable. The generic chain would substitute the *cheapest*
            # registered supplier instead, silently discarding the choice the
            # repair made for its declared detection power. Naming the plan's own
            # gate first keeps the executed step identical to the proposed plan,
            # and naming the readout first once the premise is measured keeps a
            # satisfied plan from re-buying its own gate.
            premise = composed.readout.interpretation_gate
            unmet = premise is not None and not profile.is_measured(premise)
            candidates = (composed.gate, composed.readout) if unmet else (composed.readout, composed.gate)
        else:
            candidates = (
                (outcome.contrast.plan, proposed)
                if outcome.check.ready_for_mechanism_update
                else (proposed, outcome.contrast.plan)
            )
        step = self._select_step(candidates, profile, actions)
        if step is None:
            return None
        self._record_promise(view.case.identifier, outcome, step)
        return step.identifier

    def _select_step(self, candidates, profile, actions):
        """Pick the action to execute, substituting a supplier for a blocked premise."""

        return self._controller.next_executable_action(candidates, profile, actions)

    def _record_promise(self, case_identifier: str, outcome, step) -> None:
        """Keep what the adopted repair claimed of the step actually taken.

        The promise is attached to the action that will run, so a later real
        result scores the claim that was acted on rather than an edit that was
        proposed and then superseded.
        """

        proposal = outcome.proposal
        if proposal is None:
            return
        plan = proposal.composed_plan
        if plan is not None:
            # A composed repair promises two things in two stages, and the stage
            # that ran is the one whose promise can be scored: the gate promises
            # the premise the check named, and the readout promises the
            # observation mapping the contrast needs. Recording only the second
            # would leave the gate's claim unscored forever, because the gate
            # result arrives first.
            if step.identifier == plan.gate.identifier:
                fields = tuple(dict.fromkeys(proposal.promised_fields or plan.gate.supplies))
            elif step.identifier == plan.readout.identifier:
                fields = tuple(dict.fromkeys(plan.readout.supplies or proposal.promised_fields))
            else:
                fields = tuple(step.supplies)
        elif proposal.replacement_action is None:
            return
        else:
            fields = (
                tuple(proposal.promised_fields)
                if proposal.replacement_action.identifier == step.identifier
                else tuple(step.supplies)
            )
        if not fields:
            return
        promises = self._promises.setdefault(case_identifier, [])
        entry = (step.identifier, fields)
        if entry not in promises:
            promises.append(entry)

    def observe(self, outcome: RevealedEvidence) -> None:
        """Score an outstanding repair promise against the qualified result that arrived.

        A promise is closed only when the result is admitted as a measurement
        and actually carries the promised field. An adopted repair whose result
        fails quality control, or returns a different field, is recorded as an
        unclosed promise rather than as a success.
        """

        if self._active_case is None:
            return
        promises = self._promises.get(self._active_case)
        if not promises:
            return
        supplied = set(outcome.interpretation_fields) if outcome.admits_biological_fields else set()
        ledger = self._ledgers.get(self._active_case)
        remaining = []
        for action_identifier, fields in promises:
            if action_identifier != outcome.action_identifier:
                remaining.append((action_identifier, fields))
                continue
            closed = bool(fields) and set(fields).issubset(supplied)
            if ledger is not None:
                ledger.resolve_latest(closed)
        self._promises[self._active_case] = remaining

    def repair_summary(self, case_identifier: str) -> dict[str, int]:
        """Report attempts, adoptions, and promises actually scored by a real result."""

        ledger = self._ledgers.get(case_identifier)
        if ledger is None:
            return {"attempts": 0, "adopted": 0, "scored": 0, "closed": 0}
        return {
            "attempts": len(ledger.records),
            "adopted": ledger.adopted_count,
            "scored": ledger.scored_count,
            "closed": ledger.resolved_count,
        }

    def repair_trajectory(self, case_identifier: str) -> tuple[dict[str, object], ...]:
        ledger = self._ledgers.get(case_identifier)
        return ledger.trajectory() if ledger else ()

    @staticmethod
    def _profile(view: ReplayView) -> FunctionalInterventionProfile:
        return profile_from_view(view)


class RepairDisabledPolicy(MAESTROCorePolicy):
    """Section 9.3 ablation: contrast compilation is kept, directed repair is switched off.

    If this policy matches the repairing policy, the repair itself is not what
    produced the difference.
    """

    name = "repair_disabled"

    def __init__(self, controller: MAESTROAgent | None = None):
        super().__init__(controller, max_repair_attempts=0)

    def _select_step(self, candidates, profile, actions):
        """Execute the compiled plan or nothing: no substitution is a repair either.

        Supplying a blocked plan's missing premise is a directed edit. Letting
        the ablation keep it would measure "repair minus one repair rule" and
        report it as the no-repair control.
        """

        for candidate in candidates:
            if candidate is None:
                continue
            if not profile.unmeasured(candidate.prerequisites):
                return candidate
        return None


class OutcomeAwareSelectionPolicy(ExpertWorkflowPolicy):
    """One-shot control: pick a declared-separating action, never repair a plan.

    This is the strongest honest alternative to directed repair. It reads the
    same public declarations the repair reads, but selects once instead of
    checking a plan and editing it. If it matches the repairing policy, the
    repair adds nothing beyond a better one-shot selector on this benchmark,
    and the core claim must be reported as unsupported here.
    """

    name = "outcome_aware_selection"

    def next_action(self, view: ReplayView) -> str | None:
        pair = {item["identifier"] for item in view.case.hypotheses[:2]}
        candidates = [
            item
            for item in view.available_actions()
            if _prerequisites_met(item, view)
            and pair.issubset(item.action.expected_outcomes)
            and len({item.action.expected_outcomes[name] for name in pair}) == 2
        ]
        if candidates:
            return min(candidates, key=lambda item: (item.action.cost, item.action.identifier)).action.identifier
        # Nothing separates yet: supply a prerequisite that a separating action needs.
        blocked = [
            item
            for item in view.available_actions()
            if pair.issubset(item.action.expected_outcomes)
            and len({item.action.expected_outcomes[name] for name in pair}) == 2
        ]
        needed = {field for item in blocked for field in item.action.prerequisites}
        suppliers = [
            item
            for item in view.available_actions()
            if _prerequisites_met(item, view) and set(item.action.supplies) & needed
        ]
        if suppliers:
            return min(suppliers, key=lambda item: (item.action.cost, item.action.identifier)).action.identifier
        return None


class RandomLegalEditPolicy(ExpertWorkflowPolicy):
    """Section 9.3 control: the same number of edits, drawn at random from the legal menu.

    It shares the menu, prerequisite filter, and attempt bound with the repairing
    policy, so a difference is attributable to *which* edit was chosen rather
    than to how many edits were made.  The seed is fixed for reproducibility.
    """

    name = "random_legal_edit"

    def __init__(self, *, seed: int = 20260910, attempts: int = 3):
        self._seed = seed
        self._attempts = attempts
        self._tried: dict[str, set[str]] = {}
        self._rng: dict[str, Random] = {}

    def _random_for(self, case_identifier: str) -> Random:
        return self._rng.setdefault(case_identifier, Random(f"{self._seed}:{case_identifier}"))

    def next_action(self, view: ReplayView) -> str | None:
        candidates = [item for item in view.available_actions() if _prerequisites_met(item, view)]
        if not candidates:
            return None
        tried = self._tried.setdefault(view.case.identifier, set())
        remaining = [item for item in candidates if item.action.identifier not in tried]
        if not remaining or len(tried) >= self._attempts:
            return None
        chosen = self._random_for(view.case.identifier).choice(
            sorted(remaining, key=lambda item: item.action.identifier)
        )
        tried.add(chosen.action.identifier)
        return chosen.action.identifier


class MAESTROOrchestratorPolicy:
    """Production planner in an evaluator-owned isolated runtime directory."""

    name = "maestro_orchestrator"

    def __init__(
        self,
        controller: MAESTROOrchestrator | None = None,
        decision_client: JSONCompleter | None = None,
        runtime_factory: Callable[[Path], MAESTROOrchestrator] | None = None,
    ):
        self._controller = controller
        self._decision_client = decision_client
        self._runtime_factory = runtime_factory
        self._active_view: ReplayView | None = None
        self.name = "maestro_llm" if decision_client is not None else "maestro_llm_ruled"

    def next_action(self, view: ReplayView) -> str | None:
        if self._controller is None:
            raise RuntimeError("MAESTRO replay policy has no isolated controller runtime.")
        self._active_view = view
        profile = profile_from_view(view)
        registered = tuple(MechanismHypothesis(item["identifier"], item["description"], DevelopmentAction(item["development_action"])) for item in view.case.hypotheses)
        turn = self._controller.run(
            self._replay_message(view), available_actions=tuple(item.action for item in view.available_actions()),
            intervention_profile=profile, case_id=view.case.identifier, budget=view.case.budget,
            expected_hypothesis_identifiers=tuple(item.identifier for item in registered),
            expected_hypotheses=registered,
        )
        executable = [action.identifier for action in turn.selected_actions if _prerequisites_met(_item_for(action.identifier, view), view)]
        return executable[0] if executable else None

    def decide(self, view: ReplayView) -> DecisionSubmission | None:
        if not view.revealed:
            return None
        if self._decision_client is None:
            return _declared_outcome_decision(view, origin="interpretation_rule")
        return _request_submission(self._decision_client, view)

    def _replay_message(self, view: ReplayView) -> str:
        evidence = "\n".join(
            f"[{item.identifier}] {item.statement}\nsource={item.source_id}; conditions={dict(item.conditions)}; limitations={list(item.limitations)}"
            for item in view.case.initial_evidence
        )
        hypotheses = "\n".join(
            f"[{item['identifier']}] description={item['description']}; proposed_action={item['development_action']}"
            for item in view.case.hypotheses
        )
        readouts = sorted({item.action.readout for item in view.case.actions if item.action.readout})
        return (
            "Evaluate this frozen replay case. Use only listed public evidence and evaluator-authorized revealed results. "
            "A source-availability hypothesis is not a drug-effect or target-engagement hypothesis. "
            "Do not invent facts, change registered hypothesis meanings, or use predictions as measurements.\n"
            f"case={view.case.identifier}; context={view.case.context_identifier}; remaining_budget={view.remaining_budget}\n"
            "TASK FIELDS\n"
            "task_type=mechanism_diagnosis; "
            "phenotype_endpoint=pooled viability over the screened dose range, reported as a fitted "
            "dose-response curve (AUC with its fit quality); "
            f"registered_readouts={readouts}\n"
            f"REGISTERED HYPOTHESES\n{hypotheses}\nPUBLIC EVIDENCE\n{evidence}\n"
            f"CASE LIMITATIONS\n{list(view.case.limitations)}"
        )

    def observe(self, outcome: RevealedEvidence) -> None:
        if self._active_view is None:
            raise RuntimeError("A replay result was delivered before MAESTRO selected an action.")
        result = measurement_result_from_reveal(outcome, result_id=None)
        self._controller.record_revealed_result(result)

    def for_case(self, directory: Path) -> "MAESTROOrchestratorPolicy":
        if self._runtime_factory is None:
            return self
        return MAESTROOrchestratorPolicy(
            controller=self._runtime_factory(directory),
            decision_client=self._decision_client,
        )


def _declared_outcome_decision(view: ReplayView, *, origin: str) -> DecisionSubmission | None:
    """Apply the case's own declared observation-to-hypothesis mapping to the revealed results.

    This makes the contrast's interpretation rule executable for a decision, not
    only for a readiness check: a registered action declares what it expects to
    observe under each explanation, and a revealed result then keeps or removes
    each explanation. Only the public declaration and the revealed record are
    used; no private scoring rule is consulted.

    The rule deliberately refuses in three situations rather than guessing: no
    separating observation has been acquired, both explanations remain
    compatible, or no explanation survives. The last case is a contradicted
    explanation set, which is a reason to revise the premise, not a licence to
    pick the nearest label.
    """

    hypotheses = {item["identifier"]: item for item in view.case.hypotheses}
    surviving = set(hypotheses)
    used: list[str] = []
    limitations: list[str] = []
    supplied_fields = {
        field
        for record in view.revealed
        if record.admits_biological_fields
        for field in record.interpretation_fields
    }
    for outcome in view.revealed:
        item = view.case.action(outcome.action_identifier)
        if item is None or not outcome.record_validated:
            continue
        gate = item.action.interpretation_gate
        if gate is not None and gate not in supplied_fields:
            # The assay ran and returned a qualified result, and it still moves no belief:
            # without its declared interpretation premise the outcome label cannot be read as
            # evidence for either explanation. Reading it anyway is the failure the gate exists
            # to make expressible.
            limitations.append(
                f"The result of '{outcome.action_identifier}' is uninterpretable here: its declared "
                f"interpretation gate '{gate}' has not been measured."
            )
            continue
        if outcome.evidence_kind is EvidenceKind.REAL_MEASUREMENT and not outcome.admits_biological_fields:
            # A measurement that failed its quality check is uninterpretable: it
            # removes no explanation. Reading its outcome label anyway would let
            # a failed assay decide a development action.
            limitations.append(
                f"The measurement behind '{outcome.action_identifier}' failed its declared quality "
                "check, so it constrains nothing."
            )
            continue
        declared = dict(item.action.expected_outcomes)
        if not set(hypotheses).issubset(declared):
            continue
        if len({declared[name] for name in hypotheses}) < 2:
            continue
        compatible = {name for name in hypotheses if declared[name] == outcome.outcome}
        used.append(outcome.action_identifier)
        surviving &= compatible
        limitations.extend(outcome.limitations)
        if outcome.evidence_kind is not EvidenceKind.REAL_MEASUREMENT:
            limitations.append(
                f"The record behind '{outcome.action_identifier}' is a {outcome.evidence_kind.value}, "
                "so it constrains interpretation of existing measurements rather than supplying a new one."
            )

    public_ids = tuple(item.identifier for item in view.case.initial_evidence)
    if not used:
        return None
    if len(surviving) == 1:
        identifier = next(iter(surviving))
        action = DevelopmentAction(hypotheses[identifier]["development_action"])
        return DecisionSubmission(
            action,
            tuple(dict.fromkeys(used)),
            (
                f"The revealed results match the declared expectation of '{identifier}' only, "
                "so the remaining explanation carries its registered development action."
            ),
            tuple(dict.fromkeys(limitations)),
            False,
            origin,
        )
    if not surviving:
        return DecisionSubmission(
            DevelopmentAction.DEFER,
            tuple(dict.fromkeys(used)) or public_ids,
            "No registered explanation matches the revealed observations, so the premise needs revision before any development action.",
            tuple(dict.fromkeys(limitations)),
            False,
            origin,
        )
    return None


def _prerequisites_met(item: EvidenceMenuItem | None, view: ReplayView) -> bool:
    return item is not None and set(item.action.prerequisites).issubset({field for outcome in view.revealed if outcome.admits_biological_fields for field in outcome.interpretation_fields})


def _item_for(identifier: str, view: ReplayView) -> EvidenceMenuItem | None:
    return view.case.action(identifier)


def _public_prompt(view: ReplayView, candidates: Sequence[EvidenceMenuItem]) -> dict[str, Any]:
    return {
        "case_id": view.case.identifier,
        "hypotheses": list(view.case.hypotheses),
        "initial_evidence": [{"identifier": item.identifier, "statement": item.statement, "source_id": item.source_id, "conditions": dict(item.conditions), "limitations": list(item.limitations), "evidence_kind": item.evidence_kind.value} for item in view.case.initial_evidence],
        "case_limitations": list(view.case.limitations),
        "revealed_outcomes": [{"action_identifier": item.action_identifier, "outcome_label": item.outcome, "statement": item.statement, "source_id": item.source_id, "conditions": dict(item.conditions), "metrics": dict(item.metrics), "record_validated": item.record_validated, "biological_quality": item.biological_quality, "interpretation_fields": list(item.interpretation_fields), "limitations": list(item.limitations), "evidence_kind": item.evidence_kind.value} for item in view.revealed],
        "remaining_budget": view.remaining_budget,
        # The immutable public contract. It lists every registered action's
        # declaration and never shrinks, so a terminal policy at zero budget
        # can still read what its own acquired outcome labels were declared to
        # mean. The deterministic interpretation rule reads exactly these
        # declarations from the case; withholding them here compared an LLM
        # against a rule that had strictly more information at the one step
        # where the decision is made.
        "public_actions": list(view.public_contract()),
        # The shrinking executable menu, which is a different object.
        "actions": [
            {
                "identifier": item.action.identifier,
                "description": item.action.description,
                "cost": item.action.cost,
                "kind": item.action.kind.value,
                "readout": item.action.readout,
                "prerequisites": list(item.action.prerequisites),
                "supplies": list(item.action.supplies),
                "expected_outcome_by_hypothesis": dict(item.action.expected_outcomes),
            }
            for item in candidates
        ],
        "unavailable_actions": [
            {"identifier": item.action.identifier, "description": item.action.description, "cost": item.action.cost}
            for item in view.case.actions
            if not item.available
        ],
    }


def _decision_prompt() -> str:
    return """Return JSON only. Based only on supplied public evidence and revealed outcomes, return
{"decision":"continue|revise_intervention|change_intervention_mode|preserve_multi_target_activity|remove_multi_target_activity|revise_attribution|defer|stop|null", "evidence_ids":["revealed action id"], "rationale":"...", "limitations":["..."], "decision_ready":true|false, "required_missing_premises":["..."]}.
Set decision_ready to true when the evidence you already hold supports a terminal decision, and
supply that decision with the evidence ids it rests on. That further evidence still exists on the
menu does not make a supported decision premature: say so in limitations instead. Set
decision_ready to false only when a premise you name in required_missing_premises is genuinely
missing, and then submit decision null.
Do not invent evidence. A retrieved curve is not target engagement. Use decision "defer" when the
revealed limitations prevent attribution but you are nonetheless ready to conclude that."""


def _request_submission(client: JSONCompleter, view: ReplayView) -> DecisionSubmission:
    """Permit one format-only retry without revealing a scoring answer or private result."""

    errors: tuple[str, ...] = ()
    for attempt in range(1, 3):
        system = _decision_prompt()
        if not view.available_actions():
            system += (
                " No further evidence can be acquired in this case: the menu is exhausted or"
                " unaffordable. Set decision_ready to true and submit the terminal decision"
                " the acquired evidence supports, naming what remains unresolved in limitations."
            )
        if errors:
            system += " The previous submission was invalid only for: " + ", ".join(errors) + ". Correct the JSON contract without changing evidence access."
        data, _ = client.complete_json([
            {"role": "system", "content": system},
            {"role": "user", "content": str(_public_prompt(view, list(view.available_actions())))},
        ])
        submission = _parse_submission(data, view, format_attempts=attempt)
        if not submission.validation_errors or attempt == 2:
            return submission
        errors = submission.validation_errors
    raise AssertionError("Submission retry loop must return within two attempts.")


def _parse_submission(data: Any, view: ReplayView, *, format_attempts: int = 1) -> DecisionSubmission:
    """Return an auditable invalid submission instead of collapsing parse failures to ``None``."""

    payload = _submission_payload(data)
    errors: list[str] = []
    if not isinstance(data, dict):
        return DecisionSubmission(None, (), "", (), False, "agent", ("invalid_payload",), payload, format_attempts)

    value = data.get("decision")
    decision: DevelopmentAction | None
    if value is None:
        decision = None
    elif isinstance(value, str):
        try:
            decision = DevelopmentAction(value)
        except ValueError:
            decision = None
            errors.append("invalid_decision")
    else:
        decision = None
        errors.append("invalid_decision")

    raw_evidence_ids = data.get("evidence_ids")
    if not isinstance(raw_evidence_ids, list) or not all(isinstance(item, str) and item for item in raw_evidence_ids):
        evidence_ids: tuple[str, ...] = ()
        errors.append("invalid_evidence_ids")
    else:
        evidence_ids = tuple(raw_evidence_ids)
        # A decision licensed by the public premise has no revealed result to
        # cite. Requiring one would force every policy to buy something before
        # it could submit anything, which is a spending bias, not a contract.
        citable = set(view.observed) | {item.identifier for item in view.case.initial_evidence}
        if not set(evidence_ids).issubset(citable):
            errors.append("unrevealed_evidence_id")

    rationale = data.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        rationale = ""
        errors.append("invalid_rationale")
    else:
        rationale = rationale.strip()

    raw_limitations = data.get("limitations")
    if not isinstance(raw_limitations, list) or not all(isinstance(item, str) for item in raw_limitations):
        limitations: tuple[str, ...] = ()
        errors.append("invalid_limitations")
    else:
        limitations = tuple(raw_limitations)

    # Readiness to decide, the existence of further evidence, and an unmet
    # premise are three separate facts. The previous contract carried one
    # boolean for all three, so "I can decide now, and more evidence also
    # exists" was unrepresentable and scored as a contract violation.
    raw_missing = data.get("required_missing_premises")
    if raw_missing is None:
        required_missing: tuple[str, ...] = ()
    elif isinstance(raw_missing, list) and all(isinstance(item, str) for item in raw_missing):
        required_missing = tuple(item for item in raw_missing if item.strip())
    else:
        required_missing = ()
        errors.append("invalid_required_missing_premises")

    raw_ready = data.get("decision_ready")
    legacy = data.get("needs_more_evidence")
    if type(raw_ready) is bool:
        decision_ready = raw_ready
    elif raw_ready is not None:
        decision_ready = decision is not None
        errors.append("invalid_decision_ready")
    elif type(legacy) is bool:
        # A policy speaking the older schema is read, not rejected: a decision
        # submitted alongside a request for more evidence is a ready decision
        # that also notes the menu is open.
        decision_ready = decision is not None
    else:
        decision_ready = decision is not None
        errors.append("invalid_decision_ready")

    if decision_ready:
        if decision is None:
            errors.append("missing_terminal_decision")
        elif not evidence_ids:
            errors.append("missing_terminal_evidence_ids")
    else:
        if decision is not None:
            errors.append("decision_submitted_while_not_ready")
        if not required_missing:
            errors.append("deferred_without_naming_a_missing_premise")

    return DecisionSubmission(
        decision, evidence_ids, rationale, limitations, not decision_ready, "agent",
        tuple(dict.fromkeys(errors)), payload, format_attempts,
        decision_ready=decision_ready,
        additional_evidence_available=bool(view.available_actions()),
        required_missing_premises=required_missing,
    )


def _submission_payload(data: Any) -> Mapping[str, Any]:
    """Persist only the decision-schema fields, never prompts, credentials, or evaluator state."""

    if not isinstance(data, dict):
        return {"payload_type": type(data).__name__}
    return {
        "decision": data.get("decision"),
        "evidence_ids": data.get("evidence_ids"),
        "rationale": data.get("rationale"),
        "limitations": data.get("limitations"),
        "needs_more_evidence": data.get("needs_more_evidence"),
        "decision_ready": data.get("decision_ready"),
        "required_missing_premises": data.get("required_missing_premises"),
    }
