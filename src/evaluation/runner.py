"""Independent, resumable evaluation execution over a per-run CaseStore ledger.

File summary
- Path: src/evaluation/runner.py
- Purpose: Run one policy over frozen cases and score it against private rules.
- Core points:
  - `EvaluationRunner` runs a policy in an isolated state tree; CaseStore is the only budget ledger.
  - A replayed query imports a real measurement result into the isolated CaseStore.
  - Every acquisition step records the executable candidates, the choice and the candidates passed over, so a difference between arms can be attributed.
  - Laboratory cost, named refusal codes and the always-hidden final-test verdict are reported beside the licensing verdict.
- Interfaces: `EvaluationRunner`, `run_case`, `evaluate`, `PolicyResult`, `EvaluationReport`, `ReplayStep`
- Depends on: agent.cases, maestro.models, evaluation.baselines, evaluation.cases, evaluation.scoring, evaluation.lab_cost
"""
from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping

from agent.cases import CaseStore
from agent.llm import LLMError
from agent.planner import PlannerContractError
from maestro.models import DevelopmentAction

from .baselines import DecisionSubmission, ReplayPolicy
from .capabilities import CapabilityRegistry
from .cases import ReplayCase, ReplayEnvironment, RevealedEvidence, measurement_result_from_reveal
from .lab_cost import TURNAROUND_CONVENTION
from .repair_replay import registry_extended_case, run_proposal_round
from .scoring import DecisionVerdict, FinalTestVerdict, score_submission


@dataclass(frozen=True)
class ReplayStep:
    """One acquisition step: what could run, what the policy chose, what it passed over.

    Report section 25 names ``rejected_actions[]`` as the trajectory field most often
    omitted and most needed: without the candidates a policy passed over, a difference
    between arms cannot be attributed to new information, to a model, or to the rule.
    ``outcome`` is ``acquired``, ``stopped``, ``blocked_prerequisites``,
    ``outside_menu`` or ``refused:<code>``.
    """

    index: int
    candidates: tuple[str, ...]
    chosen: str | None
    rejected: tuple[str, ...]
    remaining_budget: float
    outcome: str


@dataclass(frozen=True)
class PolicyResult:
    """Per-case outcome for one policy: actions, decision, and scoring verdict."""

    policy: str
    case_id: str
    run_id: str
    mode: str
    selected_actions: tuple[str, ...]
    revealed: tuple[RevealedEvidence, ...]
    spent: float
    decision: DevelopmentAction | None
    decision_origin: str
    submission_valid: bool
    submission_errors: tuple[str, ...]
    submission_payload: Mapping[str, object] | None
    format_attempts: int
    decision_supported: bool
    autonomous_decision_supported: bool
    scoring_reason: str
    query_coverage: bool
    qualified_evidence_coverage: bool
    stop_reason: str
    verdict: str = DecisionVerdict.CORRECT.value
    licensed_decisions: tuple[str, ...] = ()
    reachable_decisions: tuple[str, ...] = ()
    decisive_evidence_acquired: bool = False
    required_cost: float = 0.0
    waste_cost: float = 0.0
    cited_evidence_valid: bool = True
    rejected_actions: tuple[str, ...] = ()
    repair_attempts: int = 0
    repairs_adopted: int = 0
    repair_promises_scored: int = 0
    repair_promises_closed: int = 0
    refusal_code: str | None = None
    trace: tuple[ReplayStep, ...] = ()
    wells_spent: int | None = None
    turnaround_days_spent: float | None = None
    lab_cost_refusal: str | None = None
    new_measurements: int = 0
    record_retrievals: int = 0
    final_test_verdict: str = FinalTestVerdict.PARTITION_ABSENT.value
    final_test_records: tuple[str, ...] = ()
    # What this policy proposed as a repair, what compiled, and what was refused by name.
    repair_proposals: tuple[Mapping[str, object], ...] = ()
    admitted_repairs: tuple[str, ...] = ()
    # The same submission scored against what the capability registry makes reachable, which
    # is the same question for every arm whether or not it proposed anything. Reported beside
    # the frozen-menu verdict, never instead of it.
    verdict_registry_extended: str | None = None
    reachable_registry_extended: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvaluationReport:
    """Aggregated scoring across all cases for one evaluated policy."""

    policy: str
    run_id: str
    mode: str
    cases: int
    supported_decisions: int
    autonomous_supported_decisions: int
    fallback_decisions: int
    invalid_submissions: int
    query_coverage: int
    qualified_evidence_coverage: int
    mean_cost: float
    verdicts: Mapping[str, int]
    wrong_decision_rate: float
    decisive_evidence_rate: float
    mean_waste_cost: float
    rejected_action_count: int
    repair_attempts: int
    repairs_adopted: int
    repair_promises_scored: int
    repair_promises_closed: int
    results: tuple[PolicyResult, ...]
    lab_cost: Mapping[str, object] = field(default_factory=dict)
    final_test_verdicts: Mapping[str, int] = field(default_factory=dict)
    refusal_codes: Mapping[str, int] = field(default_factory=dict)
    repair_proposal_codes: Mapping[str, int] = field(default_factory=dict)
    admitted_repair_count: int = 0
    verdicts_registry_extended: Mapping[str, int] = field(default_factory=dict)


class EvaluationRunner:
    """Run one policy in an isolated state tree; CaseStore is the sole budget ledger."""

    def __init__(
        self,
        *,
        run_id: str = "test-run",
        state_root: Path | None = None,
        mode: str = "regression",
        maximum_steps: int = 8,
        capability_registry: CapabilityRegistry | None = None,
    ):
        if mode not in {"regression", "decision"}:
            raise ValueError("Evaluation mode must be 'regression' or 'decision'.")
        _safe_component(run_id, "run_id")
        self._run_id = run_id
        self._state_root = state_root or Path(tempfile.mkdtemp(prefix="maestro-evaluation-"))
        self._mode = mode
        self._maximum_steps = maximum_steps
        # Without a registry the proposal round is not offered at all, so every package
        # evaluated before this existed keeps its exact behaviour.
        self._registry = capability_registry

    def case_directory(self, policy: ReplayPolicy, case: ReplayCase) -> Path | None:
        for value, name in ((policy.name, "policy"), (case.public.identifier, "case_id")):
            _safe_component(value, name)
        root = self._state_root.resolve()
        destination = (root / self._run_id / policy.name / case.public.identifier).resolve()
        if root not in destination.parents:
            raise ValueError("Evaluation output path escapes the configured state root.")
        destination.mkdir(parents=True, exist_ok=True)
        return destination

    def run_case(self, policy: ReplayPolicy, case: ReplayCase, outcomes: Mapping[str, RevealedEvidence]) -> PolicyResult:
        """Run one case, recording a provider failure instead of discarding the run.

        A transport failure or a malformed model proposal part-way through a
        sixty-case comparison is an operational event, not a policy decision. It
        is recorded as an invalid submission for that case so the run continues
        and the report shows exactly which cases were lost.
        """

        try:
            return self._run_case(policy, case, outcomes)
        except (LLMError, PlannerContractError) as error:
            acquired, spent = self._recorded_progress(policy, case)
            return _provider_failure(
                policy, case, self._run_id, self._mode, str(error),
                revealed=tuple(outcomes[name] for name in acquired if name in outcomes),
                spent=spent,
                selected_actions=acquired,
            )

    def _recorded_progress(self, policy: ReplayPolicy, case: ReplayCase) -> tuple[tuple[str, ...], float]:
        """Read back what the isolated ledger already paid for before the failure."""

        try:
            store = CaseStore(self.case_directory(policy, case) / "cases.sqlite")
            snapshot = store.open_case(case.public.identifier, budget=case.public.budget)
            return store.recorded_action_identifiers(case.public.identifier), float(snapshot.spent)
        except Exception:  # pragma: no cover - a failed ledger must not mask the provider error
            return (), 0.0

    def _run_case(self, policy: ReplayPolicy, case: ReplayCase, outcomes: Mapping[str, RevealedEvidence]) -> PolicyResult:
        directory = self.case_directory(policy, case)
        active_policy = _policy_for_case(policy, directory)
        store = CaseStore(directory / "cases.sqlite")
        snapshot = store.open_case(case.public.identifier, budget=case.public.budget)
        restored = store.recorded_action_identifiers(case.public.identifier)
        environment = ReplayEnvironment(
            case,
            outcomes,
            restored_action_ids=restored,
            restored_spent=snapshot.spent,
            capabilities=self._registry.public_payload() if self._registry is not None else (),
        )
        # The proposal round runs before any acquisition: a policy names the premise its plan
        # is missing and proposes a registered capability for it. Compilation is the framework's
        # typed admission, so an inadmissible proposal is refused by name and costs nothing.
        proposals = run_proposal_round(active_policy, environment, self._registry)
        selected = list(restored)
        rejected: list[str] = []
        submission: DecisionSubmission | None = None
        stop_reason = "maximum_steps"
        trace: list[ReplayStep] = []
        refusal_code: str | None = None

        for step_index in range(self._maximum_steps):
            view = environment.view()
            if self._mode == "decision":
                candidate = active_policy.decide(view)
                if candidate is not None and not candidate.needs_more_evidence:
                    submission = candidate
                    stop_reason = "policy_decision"
                    break
            else:
                rule = _matched_rule(case, view.observed)
                if rule is not None:
                    submission = DecisionSubmission(rule.decision, (), "Private regression rule triggered after qualified evidence acquisition.", (), False, "rule")
                    stop_reason = "rule_triggered"
                    break

            # The executable candidates are read before the policy chooses, so the trace
            # names what was passed over rather than what remained afterwards.
            candidates = tuple(item.action.identifier for item in view.executable_actions())
            action_id = active_policy.next_action(view)
            if action_id is None:
                trace.append(ReplayStep(step_index, candidates, None, candidates, view.remaining_budget, "stopped"))
                # Exhausting the menu is not itself a decision. The policy is
                # asked once more, now that no further evidence can be
                # acquired, so a deferral recorded here is the policy's own
                # rather than a fallback imposed by the loop.
                final = active_policy.decide(view)
                if final is not None and final.decision is not None:
                    submission = final
                    stop_reason = "policy_decision_without_further_evidence"
                else:
                    submission = DecisionSubmission(DevelopmentAction.DEFER, (), "No executable public action remains within the budget.", (), False, "fallback")
                    stop_reason = "no_executable_action"
                break
            # The menu is the environment's, not the case the run started from: an admitted
            # repair is on it, and looking it up on the original case would declare a policy's
            # own compiled action to be outside the menu and end the case.
            action = environment.case.public.action(action_id)
            if action is None:
                trace.append(ReplayStep(step_index, candidates, action_id, candidates, view.remaining_budget, "outside_menu"))
                submission = DecisionSubmission(DevelopmentAction.DEFER, (), "Policy selected an action outside the public menu.", (), False, "fallback")
                stop_reason = "invalid_action"
                break
            passed_over = tuple(name for name in candidates if name != action_id)
            if _unmet_prerequisites(action.action.prerequisites, view):
                trace.append(
                    ReplayStep(step_index, candidates, action_id, passed_over, view.remaining_budget, "blocked_prerequisites")
                )
                # Proposing an assay whose interpretation premise is not yet
                # measured is a planning error, not a protocol violation: it is
                # recorded, charged nothing, and the policy keeps its turn.
                # Ending the case here would score prerequisite ordering as a
                # fatal fault for every policy that does not pre-filter.
                rejected.append(action_id)
                continue
            try:
                store.record_plan(
                    case.public.identifier,
                    (action.action,),
                    ready_to_measure=True,
                    context_identifier=_planned_context(action.action, environment.case),
                )
                outcome = environment.query(action_id)
                imported = store.import_measurement(case.public.identifier, _measurement_result(case, outcome, self._run_id))
                if not imported.created:
                    raise ValueError("A new replay query unexpectedly resolved to an existing result.")
                if abs(imported.snapshot.spent - environment.spent) > 1e-9:
                    raise ValueError("ReplayEnvironment and CaseStore spent budget disagree.")
            except ValueError as error:
                # A replay refusal carries its code; a ledger error from the case store does
                # not, and is counted as unclassified rather than dressed up as one.
                refusal_code = getattr(error, "code", None) or "unclassified"
                trace.append(
                    ReplayStep(step_index, candidates, action_id, passed_over, view.remaining_budget, f"refused:{refusal_code}")
                )
                submission = DecisionSubmission(DevelopmentAction.DEFER, (), str(error), (), False, "fallback")
                stop_reason = "invalid_action"
                break
            trace.append(ReplayStep(step_index, candidates, action_id, passed_over, view.remaining_budget, "acquired"))
            observe = getattr(active_policy, "observe", None)
            if callable(observe):
                observe(outcome)
            selected.append(action_id)

        view = environment.view()
        if submission is None and self._mode == "decision":
            submission = active_policy.decide(view)
        if submission is None:
            submission = DecisionSubmission(DevelopmentAction.DEFER, (), "No valid terminal decision was submitted.", (), False, "fallback")
        score = score_submission(
            environment.case,
            environment.outcomes,
            decision=submission.decision,
            observed=view.observed,
            evidence_ids=submission.evidence_ids,
            spent=environment.spent,
            submission_valid=not submission.validation_errors,
        )
        # The same submission against what the registry makes reachable for *any* arm. It is
        # arm-independent by construction, so "this policy deferred while a repair could have
        # licensed a decision" is a measured statement rather than a comparison of menus.
        extended_case, extended_outcomes = registry_extended_case(case, outcomes, self._registry)
        extended_score = (
            score_submission(
                extended_case,
                extended_outcomes,
                decision=submission.decision,
                observed=view.observed,
                evidence_ids=submission.evidence_ids,
                spent=environment.spent,
                submission_valid=not submission.validation_errors,
            )
            if extended_case is not case
            else score
        )
        supported = score.correct and (self._mode == "regression" or score.cited_evidence_valid)
        critical = environment.case.scoring.critical_actions
        queried = {item.action_identifier for item in view.revealed}
        qualified = {item.action_identifier for item in view.revealed if item.record_validated}
        repair = _repair_telemetry(active_policy, case.public.identifier)
        return PolicyResult(
            policy=active_policy.name, case_id=case.public.identifier, run_id=self._run_id, mode=self._mode,
            selected_actions=tuple(selected), revealed=view.revealed, spent=environment.spent,
            decision=submission.decision, decision_origin=submission.origin, decision_supported=supported,
            submission_valid=not submission.validation_errors,
            submission_errors=submission.validation_errors,
            submission_payload=submission.submitted_payload,
            format_attempts=submission.format_attempts,
            autonomous_decision_supported=supported and submission.origin == "agent" and not submission.validation_errors,
            scoring_reason=score.reason,
            query_coverage=critical.issubset(queried), qualified_evidence_coverage=critical.issubset(qualified),
            stop_reason=stop_reason,
            verdict=score.verdict.value,
            licensed_decisions=score.licensed,
            reachable_decisions=score.reachable,
            decisive_evidence_acquired=score.decisive_evidence_acquired,
            required_cost=score.required_cost,
            waste_cost=score.waste_cost,
            cited_evidence_valid=score.cited_evidence_valid,
            rejected_actions=tuple(rejected),
            refusal_code=refusal_code,
            trace=tuple(trace),
            wells_spent=score.lab_cost_spent.wells if score.lab_cost_spent is not None else None,
            turnaround_days_spent=score.lab_cost_spent.turnaround_days if score.lab_cost_spent is not None else None,
            lab_cost_refusal=score.lab_cost_spent.refusal if score.lab_cost_spent is not None else None,
            new_measurements=score.lab_cost_spent.new_measurements if score.lab_cost_spent is not None else 0,
            record_retrievals=score.lab_cost_spent.record_retrievals if score.lab_cost_spent is not None else 0,
            final_test_verdict=score.final_test,
            final_test_records=score.final_test_records,
            repair_proposals=tuple(record.payload() for record in proposals),
            admitted_repairs=environment.admitted_repairs,
            verdict_registry_extended=extended_score.verdict.value,
            reachable_registry_extended=extended_score.reachable,
            **repair,
        )

    def evaluate(self, policy: ReplayPolicy, cases: Iterable[tuple[ReplayCase, Mapping[str, RevealedEvidence]]]) -> EvaluationReport:
        results = tuple(self.run_case(policy, case, outcomes) for case, outcomes in cases)
        total = len(results) or 1
        verdicts: dict[str, int] = {}
        for result in results:
            verdicts[result.verdict] = verdicts.get(result.verdict, 0) + 1
        wrong = sum(result.verdict != DecisionVerdict.CORRECT.value for result in results)
        # Laboratory totals are summed over priced cases only and say how many cases that
        # is; a refused case is counted as refused, never added in as zero wells.
        priced = [result for result in results if result.wells_spent is not None]
        refused = [result for result in results if result.lab_cost_refusal is not None]
        final_tests: dict[str, int] = {}
        refusals: dict[str, int] = {}
        proposal_codes: dict[str, int] = {}
        extended_verdicts: dict[str, int] = {}
        for result in results:
            final_tests[result.final_test_verdict] = final_tests.get(result.final_test_verdict, 0) + 1
            if result.refusal_code:
                refusals[result.refusal_code] = refusals.get(result.refusal_code, 0) + 1
            for record in result.repair_proposals:
                code = str(record.get("refusal") or ("admitted" if record.get("admitted") else "compiled_not_admitted"))
                proposal_codes[code] = proposal_codes.get(code, 0) + 1
            if result.verdict_registry_extended:
                extended_verdicts[result.verdict_registry_extended] = (
                    extended_verdicts.get(result.verdict_registry_extended, 0) + 1
                )
        lab_cost = {
            "turnaround_convention": TURNAROUND_CONVENTION,
            "cases_priced": len(priced),
            "cases_refused": len(refused),
            "cases_unscored": len(results) - len(priced) - len(refused),
            "wells_over_priced_cases": sum(int(result.wells_spent or 0) for result in priced) if priced else None,
            "turnaround_days_over_priced_cases": (
                round(sum(float(result.turnaround_days_spent or 0.0) for result in priced), 6) if priced else None
            ),
            "new_measurements": sum(result.new_measurements for result in results),
            "record_retrievals": sum(result.record_retrievals for result in results),
        }
        return EvaluationReport(
            policy=policy.name, run_id=self._run_id, mode=self._mode, cases=len(results),
            supported_decisions=sum(result.decision_supported for result in results),
            autonomous_supported_decisions=sum(result.autonomous_decision_supported for result in results),
            fallback_decisions=sum(result.decision_origin == "fallback" for result in results),
            invalid_submissions=sum(not result.submission_valid for result in results),
            query_coverage=sum(result.query_coverage for result in results),
            qualified_evidence_coverage=sum(result.qualified_evidence_coverage for result in results),
            mean_cost=sum(result.spent for result in results) / len(results) if results else 0.0,
            verdicts=dict(sorted(verdicts.items())),
            wrong_decision_rate=wrong / total,
            decisive_evidence_rate=sum(result.decisive_evidence_acquired for result in results) / total,
            mean_waste_cost=sum(result.waste_cost for result in results) / total,
            rejected_action_count=sum(len(result.rejected_actions) for result in results),
            repair_attempts=sum(result.repair_attempts for result in results),
            repairs_adopted=sum(result.repairs_adopted for result in results),
            repair_promises_scored=sum(result.repair_promises_scored for result in results),
            repair_promises_closed=sum(result.repair_promises_closed for result in results),
            results=results,
            lab_cost=lab_cost,
            final_test_verdicts=dict(sorted(final_tests.items())),
            refusal_codes=dict(sorted(refusals.items())),
            repair_proposal_codes=dict(sorted(proposal_codes.items())),
            admitted_repair_count=sum(len(result.admitted_repairs) for result in results),
            verdicts_registry_extended=dict(sorted(extended_verdicts.items())),
        )


def _measurement_result(case: ReplayCase, outcome: RevealedEvidence, run_id: str) -> MeasurementResult:
    return measurement_result_from_reveal(
        outcome, result_id=f"evaluation:{run_id}:{case.public.identifier}:{outcome.action_identifier}"
    )


def _provider_failure(
    policy: ReplayPolicy,
    case: ReplayCase,
    run_id: str,
    mode: str,
    message: str,
    *,
    revealed: tuple[RevealedEvidence, ...] = (),
    spent: float = 0.0,
    selected_actions: tuple[str, ...] = (),
) -> PolicyResult:
    """Record a case lost to a provider failure, distinct from any policy behaviour.

    The ledger is finalised from what actually happened before the failure.
    Reporting zero spend erased acquisitions that had already been paid for
    and made a campaign's cost accounting understate the real total.
    """

    return PolicyResult(
        policy=policy.name, case_id=case.public.identifier, run_id=run_id, mode=mode,
        selected_actions=selected_actions, revealed=revealed, spent=spent, decision=None,
        decision_origin="provider_error",
        submission_valid=False, submission_errors=("provider_unavailable",), submission_payload=None,
        format_attempts=0, decision_supported=False, autonomous_decision_supported=False,
        scoring_reason=message, query_coverage=bool(selected_actions),
        qualified_evidence_coverage=False,
        stop_reason="provider_error", verdict=DecisionVerdict.INVALID_SUBMISSION.value,
    )


def _planned_context(action, case: ReplayCase) -> str | None:
    """Return the context a planned action is executed in, as the action declares it.

    A cross-context evidence review has no single biological context, and an
    orthogonal control is deliberately executed in another one. Planning both
    in the case's context would make the store reject a valid record, so the
    declaration is read instead of assumed.
    """

    if not action.context_bound:
        return None
    return action.execution_context or case.public.context_identifier


def _unmet_prerequisites(prerequisites: tuple[str, ...], view) -> tuple[str, ...]:
    """Prerequisite fields that no qualified revealed result has supplied yet."""

    supplied = {
        field
        for outcome in view.revealed
        if outcome.admits_biological_fields
        for field in outcome.interpretation_fields
    }
    return tuple(name for name in prerequisites if name not in supplied)


def _repair_telemetry(policy: ReplayPolicy, case_id: str) -> dict[str, int]:
    """Read a policy's own repair ledger when it keeps one, without requiring it."""

    summary = getattr(policy, "repair_summary", None)
    if not callable(summary):
        return {"repair_attempts": 0, "repairs_adopted": 0, "repair_promises_scored": 0, "repair_promises_closed": 0}
    values = summary(case_id)
    return {
        "repair_attempts": int(values.get("attempts", 0)),
        "repairs_adopted": int(values.get("adopted", 0)),
        "repair_promises_scored": int(values.get("scored", 0)),
        "repair_promises_closed": int(values.get("closed", 0)),
    }


def _matched_rule(case: ReplayCase, observed: Mapping[str, RevealedEvidence]):
    return next((rule for rule in case.scoring.decision_rules if rule.matches(observed)), None)


def _policy_for_case(policy: ReplayPolicy, directory: Path | None) -> ReplayPolicy:
    factory = getattr(policy, "for_case", None)
    return factory(directory) if callable(factory) else policy


def _safe_component(value: str, name: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value):
        raise ValueError(f"{name} contains unsupported path characters.")
