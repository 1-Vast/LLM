"""Evaluation policies: consolidated module responsibilities."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
import json
from pathlib import Path
from random import Random
from typing import Any, Callable, Mapping, Protocol, Sequence
from agent.orchestrator import MAESTROOrchestrator
from maestro.models import DevelopmentAction, MeasurementStatus, RepairKind
from maestro import FunctionalInterventionProfile, MAESTROAgent, MechanismHypothesis
from maestro.repair import RepairController, RepairLedger
from maestro.models import EvidenceKind
from .cases import EvidenceMenuItem, PublicCase, ReplayCase, ReplayView, RevealedEvidence, measurement_result_from_reveal
from .costs import SpendLedger


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


SHUFFLE_SEED = 20260914
_MAX_DRAWS = 10_000


def with_prediction_values(view: ReplayView, values: Mapping[str, float]) -> ReplayView:
    """The same view with some declared prediction values replaced, and nothing else changed."""

    actions = tuple(
        replace(item, prediction_value=float(values[item.action.identifier]))
        if item.action.identifier in values
        else item
        for item in view.case.actions
    )
    return replace(view, case=replace(view.case, actions=actions))


def shuffled_assignment(case: PublicCase, *, seed: int = SHUFFLE_SEED) -> Mapping[str, float]:
    """Reassign the available actions' declared values by a seeded derangement.

    Positions are deranged, so no available action keeps its own slot. Unavailable actions
    keep their values: moving a value onto an action that can never run would change how
    much value the policy can act on, not only where it sits.
    """

    available = sorted(
        (item for item in case.actions if item.available), key=lambda item: item.action.identifier
    )
    values = [item.prediction_value for item in available]
    count = len(values)
    if count < 2:
        return {item.action.identifier: item.prediction_value for item in available}
    rng = Random(f"{seed}:{case.identifier}")
    order = list(range(count))
    for _ in range(_MAX_DRAWS):
        rng.shuffle(order)
        if all(position != index for index, position in enumerate(order)):
            break
    else:  # pragma: no cover - a derangement of two or more positions is found almost surely
        order = list(range(1, count)) + [0]
    return {item.action.identifier: values[order[index]] for index, item in enumerate(available)}


def is_identity(case: PublicCase, *, seed: int = SHUFFLE_SEED) -> bool:
    """Whether the shuffle leaves every available action with the value it declared."""

    original = {item.action.identifier: item.prediction_value for item in case.actions if item.available}
    return dict(shuffled_assignment(case, seed=seed)) == original


class ShuffledPredictionValuePolicy(PredictionValuePolicy):
    """Section 37 row six for the declared-value heuristic: the same policy, values moved.

    If this arm acquires the same evidence and reaches the same verdicts as the
    unshuffled heuristic, the declared values did not change what the policy bought.
    """

    name = "prediction_value_shuffled"

    def __init__(self, *, seed: int = SHUFFLE_SEED):
        self._seed = seed

    def next_action(self, view: ReplayView) -> str | None:
        return super().next_action(with_prediction_values(view, shuffled_assignment(view.case, seed=self._seed)))


class ShuffledPredictionFullSystemPolicy(MAESTROCorePolicy):
    """Section 37 row six for the full system: the same loop, its prediction input deranged.

    The row asks whether the full system's behaviour depends on the prediction input being
    the right way round. On a package whose full system reads no prediction, this arm is
    expected to match the unshuffled one exactly - and that identity is the measurement, not
    a failure of the control: it says the input is not in the loop, which is what audit
    finding F14 claims and what a shuffle over an unread input can show.
    """

    name = "maestro_core_shuffled_predictions"

    def __init__(self, *args, seed: int = SHUFFLE_SEED, **kwargs):
        super().__init__(*args, **kwargs)
        self._seed = seed

    def next_action(self, view: ReplayView) -> str | None:
        return super().next_action(
            with_prediction_values(view, shuffled_assignment(view.case, seed=self._seed))
        )


class RemovedPredictionValuePolicy(PredictionValuePolicy):
    """The remove-the-model control: every declared prediction value reads as zero.

    The ranking then falls back to the heuristic's own tie-break, cheapest first and then
    by identifier, so the arm is the same selector with its prediction input switched off.
    """

    name = "prediction_value_removed"

    def next_action(self, view: ReplayView) -> str | None:
        return super().next_action(
            with_prediction_values(view, {item.action.identifier: 0.0 for item in view.case.actions})
        )


REPAIR_PROPOSAL_PROMPT = (
    "You are the repair operator of a scientific decision agent. You are given one case: two "
    "competing explanations of a discordance, the evidence already in hand, the measurements "
    "the menu can buy, the premises the menu cannot supply, and a registry of measurement "
    "capabilities with their declared types and coverage.\n\n"
    "The framework's rule, which you must respect: a decision that names a cause is licensed "
    "only when every explanation still compatible with the observations would take the same "
    "decision. A premise the menu cannot supply is what stops the case from deciding.\n\n"
    "Propose exactly one repair, as one JSON object and nothing else:\n"
    '  {"operator": "register_supplier", "capability": "<registry identifier>", '
    '"supplies": "<premise field>", "compound": "<compound>", "entity": "<gene symbol>", '
    '"rationale": "<one sentence>"}\n\n'
    "The capability must be one the registry lists, it must declare the premise you name, and "
    "its declared quantity, context and units must satisfy that premise's requirement. You do "
    "not choose what the result would mean: the case declares that."
)


class ProposalPolicy(Protocol):
    """A replay policy that can also propose repairs before it acquires evidence."""

    name: str

    def propose_repairs(self, view: ReplayView) -> Sequence[Mapping[str, object]]: ...


def _subject(view: ReplayView, premise: str) -> tuple[str, str] | None:
    """The gene and compound an engagement-style premise is declared to be about.

    The premise registry states the subject as ``GENE@compound``; that declaration is public,
    so a policy reads the subject from the case rather than guessing which compound a premise
    concerns.
    """

    requirement = (view.case.premise_registry or {}).get(premise)
    entity = getattr(requirement, "entity", None)
    if not entity or "@" not in entity:
        return None
    gene, compound = entity.split("@", 1)
    return gene, compound


def _separating(view: ReplayView, premise: str) -> bool:
    template = (view.case.repair_outcome_templates or {}).get(premise) or {}
    return len(set(template.values())) > 1


def _gated_menu_premises(view: ReplayView) -> set[str]:
    """Premises that make a registered menu action interpretable rather than legal."""

    return {
        item.action.interpretation_gate
        for item in view.case.actions
        if item.available and item.action.interpretation_gate is not None
    }


def _offers_for(view: ReplayView, premise: str) -> list[Mapping[str, object]]:
    offers = [entry for entry in view.capabilities if entry.get("supplies") == premise]
    return sorted(offers, key=lambda entry: (float(entry.get("cost", 0.0)), str(entry.get("identifier"))))


def _admissible_offers(view: ReplayView, premise: str) -> list[Mapping[str, object]]:
    """Offers whose *declaration* already matches what the premise requires.

    The comparison is the one the framework will make, on public fields: an estimate offered
    for a premise that requires a direct measurement, a different quantity, a different
    context or different units cannot discharge it, and a directed agent can see that before
    proposing. Offers that survive are proposed in price order; if the filter empties the
    list, the cheapest offer is proposed anyway so the refusal is recorded by name rather than
    the agent quietly proposing nothing.
    """

    requirement = (view.case.premise_registry or {}).get(premise)
    offers = _offers_for(view, premise)
    if requirement is None or not requirement.is_typed:
        return offers
    kept: list[Mapping[str, object]] = []
    for offer in offers:
        quantity = str(offer.get("quantity", ""))
        if requirement.quantity.value not in ("unspecified", quantity):
            continue
        if requirement.require_direct_measurement and bool(offer.get("is_estimate")):
            continue
        if requirement.context_identifier and offer.get("context_identifier") != requirement.context_identifier:
            continue
        if requirement.units and offer.get("units") not in (None, requirement.units):
            continue
        kept.append(offer)
    return kept or offers[:1]


class RegistryRepairRulePolicy(ExpertWorkflowPolicy):
    """Directed repair over the registry: name the missing premise, propose a capability.

    One proposal round per case. The premise is chosen by what its measurement could do, not
    by what is cheapest to buy: a premise whose declared template separates the explanations
    comes first, a premise that only unlocks a gated menu readout second.
    """

    name = "registry_repair_rule"

    def __init__(self) -> None:
        self._proposed: set[str] = set()

    def next_action(self, view: ReplayView) -> str | None:
        """Buy the premise the repair named, before spending the budget on anything else.

        Directed repair that proposes a premise and then lets a fixed acquisition order spend
        the budget elsewhere has not repaired anything. An admitted repair whose declared
        outcomes separate the explanations is therefore taken first; everything after that is
        the inherited order, so the arm differs from the expert baseline in the repair step
        alone.
        """

        pair = {item["identifier"] for item in view.case.hypotheses[:2]}
        admitted = [
            item
            for item in view.available_actions()
            if item.action.identifier.startswith("repair__")
            and pair.issubset(item.action.expected_outcomes)
            and len({item.action.expected_outcomes[name] for name in pair}) == 2
        ]
        if admitted:
            return min(admitted, key=lambda item: (item.action.cost, item.action.identifier)).action.identifier
        return super().next_action(view)

    def propose_repairs(self, view: ReplayView) -> Sequence[Mapping[str, object]]:
        if view.case.identifier in self._proposed:
            return ()
        self._proposed.add(view.case.identifier)
        missing = list(view.case.missing_premises())
        gates = _gated_menu_premises(view)
        ordered = sorted(
            missing,
            key=lambda premise: (
                0 if _separating(view, premise) else (1 if premise in gates else 2),
                premise,
            ),
        )
        proposals: list[Mapping[str, object]] = []
        for premise in ordered:
            subject = _subject(view, premise)
            if subject is None:
                continue
            gene, compound = subject
            for offer in _admissible_offers(view, premise)[:2]:
                proposals.append(
                    {
                        "operator": "register_supplier",
                        "capability": offer["identifier"],
                        "supplies": premise,
                        "compound": compound,
                        "entity": gene,
                        "rationale": (
                            f"The plan cannot read its evidence without '{premise}', and this capability "
                            "declares that premise for this subject in this context."
                        ),
                    }
                )
        return tuple(proposals)


class RegistryExpandedSelectionPolicy(OutcomeAwareSelectionPolicy):
    """Control: admit every compilable capability first, then select once.

    This is the strongest honest alternative to proposing: it has the whole catalogue in the
    menu from the start and never checks a plan or edits it. A tie with the rule arm means
    the registry's content, not the proposal step, is what carries the difference.
    """

    name = "registry_expanded_selection"

    def __init__(self) -> None:
        self._proposed: set[str] = set()

    def propose_repairs(self, view: ReplayView) -> Sequence[Mapping[str, object]]:
        if view.case.identifier in self._proposed:
            return ()
        self._proposed.add(view.case.identifier)
        proposals: list[Mapping[str, object]] = []
        for premise in view.case.missing_premises():
            subject = _subject(view, premise)
            if subject is None:
                continue
            gene, compound = subject
            for offer in _offers_for(view, premise):
                proposals.append(
                    {
                        "operator": "register_supplier",
                        "capability": offer["identifier"],
                        "supplies": premise,
                        "compound": compound,
                        "entity": gene,
                        "rationale": "Catalogue expansion control: every compilable capability is admitted.",
                    }
                )
        return tuple(proposals)


class RegistryRandomProposalPolicy(ExpertWorkflowPolicy):
    """Control: a seeded random proposal, so typed admission is what filters it.

    It draws a capability, a premise and a subject independently, which is exactly the
    behaviour a registry with no direction would produce. Its refusals are the measurement:
    a proposal that names the wrong quantity, context or compound is refused by name.
    """

    name = "registry_repair_random"

    def __init__(self, *, seed: int = 20260914, attempts: int = 1) -> None:
        self._seed = seed
        self._attempts = attempts
        self._proposed: set[str] = set()

    def propose_repairs(self, view: ReplayView) -> Sequence[Mapping[str, object]]:
        if view.case.identifier in self._proposed or not view.capabilities:
            return ()
        self._proposed.add(view.case.identifier)
        random = Random(f"{self._seed}:{view.case.identifier}")
        premises = list(view.case.premise_registry or {}) or list(view.case.missing_premises())
        subjects: list[tuple[str, str]] = []
        for premise in view.case.premise_registry or {}:
            subject = _subject(view, premise)
            if subject is not None:
                subjects.append(subject)
        if not premises or not subjects:
            return ()
        proposals: list[Mapping[str, object]] = []
        for _ in range(self._attempts):
            offer = random.choice(sorted(view.capabilities, key=lambda entry: str(entry.get("identifier"))))
            premise = random.choice(sorted(premises))
            gene, compound = random.choice(sorted(subjects))
            proposals.append(
                {
                    "operator": "register_supplier",
                    "capability": offer["identifier"],
                    "supplies": premise,
                    "compound": compound,
                    "entity": gene,
                    "rationale": "Random control: the registry is sampled without direction.",
                }
            )
        return tuple(proposals)


class LLMRegistryRepairPolicy(ExpertWorkflowPolicy):
    """The configured model proposes one repair per case in the framework's operator language.

    The model chooses the capability, the premise and the subject. It never supplies an
    outcome model, a price or a reliability that scoring reads: those come from the case and
    the registry, so the measurement is the model's judgement and not its arithmetic.
    """

    name = "registry_repair_llm"

    def __init__(self, client: JSONCompleter, *, max_tokens: int = 1200) -> None:
        self._client = client
        self._max_tokens = max_tokens
        self._proposed: set[str] = set()
        self.transcripts: list[Mapping[str, object]] = []

    def propose_repairs(self, view: ReplayView) -> Sequence[Mapping[str, object]]:
        if view.case.identifier in self._proposed:
            return ()
        self._proposed.add(view.case.identifier)
        statement = self._statement(view)
        try:
            payload, response = self._client.complete_json(
                [
                    {"role": "system", "content": REPAIR_PROPOSAL_PROMPT},
                    {"role": "user", "content": json.dumps(statement, ensure_ascii=False, sort_keys=True)},
                ],
                max_tokens=self._max_tokens,
            )
        except Exception as error:  # a provider failure is data, not a crash
            self.transcripts.append(
                {"case": view.case.identifier, "error": f"{type(error).__name__}: {str(error)[:200]}"}
            )
            return ()
        self.transcripts.append(
            {
                "case": view.case.identifier,
                "proposal": payload,
                "model": getattr(response, "model", ""),
                "usage": dict(getattr(response, "usage", {}) or {}),
                "finish_reason": getattr(response, "finish_reason", None),
            }
        )
        return (payload,) if isinstance(payload, dict) else ()

    def _statement(self, view: ReplayView) -> Mapping[str, Any]:
        return {
            "case": view.case.identifier,
            "context_identifier": view.case.context_identifier,
            "hypotheses": list(view.case.hypotheses),
            "initial_evidence": [
                {"identifier": item.identifier, "statement": item.statement, "source_id": item.source_id}
                for item in view.case.initial_evidence
            ],
            "menu": list(view.public_contract()),
            "missing_premises": list(view.case.missing_premises()),
            "premise_requirements": {
                name: {
                    "quantity": requirement.quantity.value,
                    "entity": requirement.entity,
                    "units": requirement.units,
                    "context_identifier": requirement.context_identifier,
                    "requires_direct_measurement": requirement.require_direct_measurement,
                }
                for name, requirement in (view.case.premise_registry or {}).items()
            },
            "declared_outcome_templates": {
                name: dict(template) for name, template in (view.case.repair_outcome_templates or {}).items()
            },
            "capability_registry": list(view.capabilities),
            "remaining_budget": view.remaining_budget,
            "case_limitations": list(view.case.limitations),
        }


EXPLICIT_HYPOTHESES_PROMPT = (
    "You are deciding one experimental case, and you must show your hypothesis bookkeeping.\n\n"
    "Return one JSON object and nothing else:\n"
    '  {"posterior": {"<explanation identifier>": <probability>, ...}, '
    '"value_of_information": {"<action identifier>": <expected reduction in decision loss>, ...}, '
    '"action": "<action identifier or null>", "rationale": "<one sentence>"}\n\n'
    "The posterior must cover exactly the registered explanations and sum to 1. The value of "
    "information must cover every action you were offered. Set \"action\" to the identifier you "
    "would buy now, or to null if no action is worth its cost, in which case the case will be "
    "decided on what you already have. A decision that names a cause is supported only when "
    "every explanation still compatible with the evidence would accept it."
)


class ExplicitHypothesesLLMPolicy:
    """Row 4: the same model as row 3, with the posterior and the value of information enforced."""

    name = "explicit_hypotheses_llm"

    def __init__(
        self,
        client: JSONCompleter,
        *,
        ledger: SpendLedger | None = None,
        # The configured model reasons before it answers, and reasoning counts against this
        # budget: a trivial object cost 437 completion tokens in the reachability probe, and
        # this row's object at 4000 returned `finish_reason=length` with no content. The budget
        # is a cap, not a charge; only tokens actually produced are paid for.
        max_tokens: int = 16000,
        estimate_usd: float = 0.016,
    ) -> None:
        self._client = client
        self._ledger = ledger
        self._max_tokens = max_tokens
        self._estimate = estimate_usd
        self.turns: list[Mapping[str, Any]] = []

    def next_action(self, view: ReplayView) -> str | None:
        candidates = [item for item in view.available_actions() if _prerequisites_met(item, view)]
        if not candidates:
            return None
        allowed = {item.action.identifier for item in candidates}
        registered = {str(entry["identifier"]) for entry in view.case.hypotheses}
        statement = self._statement(view, candidates)
        label = f"row4:{view.case.identifier}:{len(view.revealed)}"
        if self._ledger is not None:
            self._ledger.reserve(label, self._estimate)
        try:
            payload, response = self._client.complete_json(
                [
                    {"role": "system", "content": EXPLICIT_HYPOTHESES_PROMPT},
                    {"role": "user", "content": json.dumps(statement, ensure_ascii=False, sort_keys=True, default=str)},
                ],
                max_tokens=self._max_tokens,
            )
        except Exception as error:  # a provider failure is data, not a crash
            detail = str(error)[:300]
            if self._ledger is not None:
                self._ledger.charge(
                    label,
                    None,
                    status="failed",
                    reserved_usd=self._estimate,
                    note=f"{type(error).__name__}: {detail}; charged at reservation",
                )
            self.turns.append(
                {
                    "case": view.case.identifier,
                    "refusal": f"provider_failure:{type(error).__name__}",
                    "detail": detail,
                }
            )
            return None
        if self._ledger is not None:
            self._ledger.charge(label, dict(response.usage), status="ok", reserved_usd=self._estimate)
        refusal = self._contract_refusal(payload, registered, allowed)
        self.turns.append(
            {
                "case": view.case.identifier,
                "posterior": payload.get("posterior"),
                "value_of_information": payload.get("value_of_information"),
                "action": payload.get("action"),
                "refusal": refusal,
            }
        )
        if refusal is not None:
            return None
        action = payload.get("action")
        return str(action) if isinstance(action, str) and action in allowed else None

    def decide(self, view: ReplayView) -> DecisionSubmission | None:
        if not view.revealed:
            return None
        return _request_submission(self._client, view)

    @staticmethod
    def _statement(view: ReplayView, candidates) -> Mapping[str, Any]:
        """What this row's turn actually needs, and nothing else.

        The full public contract, the unavailable actions and every record's metrics and
        limitations are what a decision step reads; a selection step needs the explanations,
        what has already been observed, and what each purchasable action is declared to show
        under each explanation. Sending the rest made the model reason past a twelve-thousand
        token budget and return no content at all, which is a failure of the prompt rather
        than of the row.
        """

        return {
            "case": view.case.identifier,
            "registered_explanations": [
                {"identifier": str(item["identifier"]), "description": str(item["description"])[:200]}
                for item in view.case.hypotheses
            ],
            "observed_so_far": [
                {"action": record.action_identifier, "outcome": record.outcome, "statement": record.statement[:240]}
                for record in view.revealed
            ],
            "purchasable_actions": [
                {
                    "identifier": item.action.identifier,
                    "cost": item.action.cost,
                    "declared_outcome_by_explanation": dict(item.action.expected_outcomes),
                }
                for item in candidates
            ],
            "remaining_budget": view.remaining_budget,
        }

    @staticmethod
    def _contract_refusal(
        payload: Mapping[str, Any], registered: set[str], allowed: set[str]
    ) -> str | None:
        """Name the contract violation rather than silently treating the turn as a pass."""

        posterior = payload.get("posterior")
        if not isinstance(posterior, dict) or set(posterior) != registered:
            return "posterior_does_not_cover_the_registered_explanations"
        try:
            total = sum(float(value) for value in posterior.values())
        except (TypeError, ValueError):
            return "posterior_is_not_numeric"
        if abs(total - 1.0) > 1e-6:
            return f"posterior_not_normalised:{total:.6f}"
        values = payload.get("value_of_information")
        if not isinstance(values, dict) or not allowed.issubset(set(values)):
            return "value_of_information_does_not_cover_the_offered_actions"
        action = payload.get("action")
        if action is not None and (not isinstance(action, str) or action not in allowed):
            return f"action_not_executable:{action}"
        return None


# A reliability estimated from very few development cases would swing between 0 and 1 on one
# record, so the estimate is smoothed towards "declared" with a one-observation prior. The
# prior is declared here and reported with the fitted table.
SMOOTHING_PRIOR_SUCCESSES = 1.0
SMOOTHING_PRIOR_TRIALS = 2.0
WRONG_DECISION_LOSS = 10.0
DEFERRAL_LOSS = 4.0


def fit_action_reliability(
    cases: Sequence[tuple[ReplayCase, Mapping[str, RevealedEvidence]]],
    *,
    development_cases: Sequence[str],
) -> Mapping[str, float]:
    """How often each action's record carried an outcome the case declared for an explanation.

    Fitted on the development split only. An action never observed there is absent from the
    table, and the policy then falls back to the declared model for it, which is recorded.
    """

    allowed = set(development_cases)
    successes: dict[str, float] = {}
    trials: dict[str, float] = {}
    for case, outcomes in cases:
        if case.public.identifier not in allowed:
            continue
        for identifier, record in outcomes.items():
            item = case.public.action(identifier)
            if item is None:
                continue
            declared = set(item.action.expected_outcomes.values())
            if not declared:
                continue
            trials[identifier] = trials.get(identifier, 0.0) + 1.0
            if record.outcome in declared:
                successes[identifier] = successes.get(identifier, 0.0) + 1.0
    return {
        identifier: (successes.get(identifier, 0.0) + SMOOTHING_PRIOR_SUCCESSES)
        / (count + SMOOTHING_PRIOR_TRIALS)
        for identifier, count in sorted(trials.items())
    }


def _outcome_model(
    item, hypotheses: Sequence[str], reliability: float
) -> Mapping[str, Mapping[str, float]]:
    """The fitted model: the declared outcome with probability ``reliability``, the rest spread."""

    declared = {name: item.action.expected_outcomes.get(name) for name in hypotheses}
    labels = sorted({label for label in declared.values() if label})
    model: dict[str, dict[str, float]] = {}
    for name in hypotheses:
        own = declared.get(name)
        if own is None or len(labels) < 2:
            model[name] = {label: 1.0 / len(labels) for label in labels} if labels else {}
            continue
        others = [label for label in labels if label != own]
        model[name] = {own: reliability}
        for label in others:
            model[name][label] = (1.0 - reliability) / len(others)
    return model


def _bayes_loss(belief: Mapping[str, float], decisions: Mapping[str, str]) -> float:
    """Expected loss of the best terminal act under a belief over the two explanations."""

    options = {*decisions.values(), "defer"}
    best = min(
        sum(
            weight * (0.0 if decisions.get(name) == option else WRONG_DECISION_LOSS)
            for name, weight in belief.items()
        )
        if option != "defer"
        else DEFERRAL_LOSS
        for option in options
    )
    return best


def expected_value_of_information(
    view: ReplayView, item, reliability: float
) -> float:
    """Expected reduction in decision loss from buying one action, under the fitted model."""

    hypotheses = [str(entry["identifier"]) for entry in view.case.hypotheses[:2]]
    decisions = {str(entry["identifier"]): str(entry["development_action"]) for entry in view.case.hypotheses[:2]}
    if len(hypotheses) < 2:
        return 0.0
    belief = {name: 1.0 / len(hypotheses) for name in hypotheses}
    for record in view.revealed:
        observed = view.case.action(record.action_identifier)
        if observed is None:
            continue
        declared = observed.action.expected_outcomes
        if not set(hypotheses).issubset(declared) or len({declared[name] for name in hypotheses}) < 2:
            continue
        updated = {
            name: belief[name] * (0.9 if declared[name] == record.outcome else 0.1) for name in hypotheses
        }
        total = sum(updated.values())
        if total > 0:
            belief = {name: value / total for name, value in updated.items()}
    before = _bayes_loss(belief, decisions)
    model = _outcome_model(item, hypotheses, reliability)
    labels = sorted({label for name in hypotheses for label in model[name]})
    after = 0.0
    for label in labels:
        mass = sum(belief[name] * model[name].get(label, 0.0) for name in hypotheses)
        if mass <= 0:
            continue
        posterior = {
            name: belief[name] * model[name].get(label, 0.0) / mass for name in hypotheses
        }
        after += mass * _bayes_loss(posterior, decisions)
    return before - after


@dataclass
class SimpleModelVOIPolicy(ExpertWorkflowPolicy):
    """Row 2: buy the action with the best value of information per unit cost, or stop."""

    reliability: Mapping[str, float] = field(default_factory=dict)
    default_reliability: float = 0.5
    name: str = "simple_model_voi"

    def next_action(self, view: ReplayView) -> str | None:
        candidates = [item for item in view.available_actions() if _prerequisites_met(item, view)]
        best: tuple[float, str] | None = None
        for item in candidates:
            reliability = float(self.reliability.get(item.action.identifier, self.default_reliability))
            value = expected_value_of_information(view, item, reliability)
            cost = max(float(item.action.cost), 1e-9)
            if value <= cost:
                # Buying it costs more than the decision it could improve. Refusing to buy is
                # the value-of-information answer, not a failure to find an action.
                continue
            score = value / cost
            if best is None or (score, item.action.identifier) > (best[0], best[1]):
                best = (score, item.action.identifier)
        return best[1] if best is not None else None
