"""A bounded repair loop and an auditable repair ledger.

File summary
- Path: src/maestro/repair.py
- Purpose: Directed repair with a ledger that separates adoption from an actually closed gap.
- Core points:
  - `RepairController` re-checks after each edit and stops on repetition or no progress.
  - `RepairLedger` records every edit; adoption is not the same as the gap closing.
  - `gap_resolved` is set only by a real, qualified result, scored apart from adoption.
- Interfaces: `RepairController`, `run`, `RepairLedger`, `repair`, `RepairRecord`, `RepairOutcome`, `EXPECTED_GAIN`
- Depends on: maestro.models, virtual_cell.interface
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Mapping, Sequence

from .models import (
    ContrastCheck,
    EvidenceAction,
    FunctionalInterventionProfile,
    MeasurementStatus,
    MechanismContrast,
    NonDiscriminabilityReason,
    RepairKind,
    RepairProposal,
)

if TYPE_CHECKING:
    from virtual_cell.interface import StatePrediction


EXPECTED_GAIN: Mapping[RepairKind, str] = {
    RepairKind.ADD_FUNCTIONAL_MEASUREMENT: (
        "Make the intervention-implementation premise measurable so a null phenotype becomes interpretable."
    ),
    RepairKind.ADD_PREREQUISITE_MEASUREMENT: (
        "Supply the declared prerequisite so the planned result can be interpreted at all."
    ),
    RepairKind.CHANGE_READOUT_OR_TIME: (
        "Replace the readout or time point with one that separates the two explanations."
    ),
    RepairKind.MATCH_INTERVENTION_MODE: (
        "Make the compared interventions comparable in mode, spectrum, and time course."
    ),
    RepairKind.REMOVE_MODEL_DEPENDENCE: (
        "Drop an unsupported model dependency and return the branch to a real measurement."
    ),
    RepairKind.DEFER: "Declare the evidence that would restore a decision instead of editing the plan.",
}


@dataclass(frozen=True)
class RepairRecord:
    """One attempted edit, kept whether or not it was adopted."""

    attempt: int
    fingerprint: str
    kind: RepairKind
    action_identifier: str | None
    triggered_by: tuple[NonDiscriminabilityReason, ...]
    modified_fields: tuple[str, ...]
    expected_gain: str
    adopted: bool
    resolved_reasons: tuple[NonDiscriminabilityReason, ...]
    remaining_reasons: tuple[NonDiscriminabilityReason, ...]
    gap_resolved: bool | None = None
    stop_reason: str | None = None
    contrast_identifier: str | None = None
    promised_fields: tuple[str, ...] = ()
    result_id: str | None = None

    def as_trajectory(self) -> dict[str, object]:
        """A learning-oriented row: state, failure, edit, real outcome, decision."""

        return {
            "attempt": self.attempt,
            "fingerprint": self.fingerprint,
            "contrast_identifier": self.contrast_identifier,
            "kind": self.kind.value,
            "action_identifier": self.action_identifier,
            "triggered_by": [reason.value for reason in self.triggered_by],
            "modified_fields": list(self.modified_fields),
            "expected_gain": self.expected_gain,
            "adopted": self.adopted,
            "resolved_reasons": [reason.value for reason in self.resolved_reasons],
            "remaining_reasons": [reason.value for reason in self.remaining_reasons],
            "gap_resolved": self.gap_resolved,
            "stop_reason": self.stop_reason,
            "promised_fields": list(self.promised_fields),
            "result_id": self.result_id,
        }


class RepairLedger:
    """Append-only repair history for one case, used for auditing and later learning."""

    def __init__(self) -> None:
        self._records: list[RepairRecord] = []
        self._fingerprints: set[str] = set()

    @property
    def records(self) -> tuple[RepairRecord, ...]:
        return tuple(self._records)

    def register(self, record: RepairRecord) -> RepairRecord:
        self._records.append(record)
        if record.action_identifier is not None:
            self._fingerprints.add(record.fingerprint)
        return record

    def has_fingerprint(self, fingerprint: str) -> bool:
        return fingerprint in self._fingerprints

    def resolve(self, attempt: int, gap_resolved: bool) -> RepairRecord | None:
        """Record whether a real result closed the gap this edit promised to close.

        Attempt numbers restart at one for every repair cycle, so the *latest*
        unresolved record carrying the number is the one meant.  Prefer
        `resolve_fingerprint` when the caller knows which edit it is scoring.
        """

        for index in range(len(self._records) - 1, -1, -1):
            record = self._records[index]
            if record.attempt == attempt and record.gap_resolved is None:
                updated = replace(record, gap_resolved=gap_resolved)
                self._records[index] = updated
                return updated
        return None

    def resolve_fingerprint(
        self, fingerprint: str, gap_resolved: bool, *, result_id: str | None = None,
        target: RepairRecord | None = None,
    ) -> RepairRecord | None:
        """Score the most recent unresolved attempt with this exact edit fingerprint."""

        for index in range(len(self._records) - 1, -1, -1):
            record = self._records[index]
            if record.fingerprint == fingerprint and record.gap_resolved is None and (
                record is target if target is not None else record.adopted
            ):
                updated = replace(record, gap_resolved=gap_resolved, result_id=result_id)
                self._records[index] = updated
                return updated
        return None

    def resolve_latest(self, gap_resolved: bool) -> RepairRecord | None:
        if not self._records:
            return None
        return self.resolve(self._records[-1].attempt, gap_resolved)

    @property
    def adopted_count(self) -> int:
        return sum(1 for record in self._records if record.adopted)

    @property
    def resolved_count(self) -> int:
        return sum(1 for record in self._records if record.gap_resolved is True)

    @property
    def scored_count(self) -> int:
        return sum(1 for record in self._records if record.gap_resolved is not None)

    def success_rate(self) -> float | None:
        """Adopted repairs confirmed by a real result; ``None`` when nothing is scored yet."""

        if self.scored_count == 0:
            return None
        return self.resolved_count / self.scored_count

    def trajectory(self) -> tuple[dict[str, object], ...]:
        return tuple(record.as_trajectory() for record in self._records)


@dataclass(frozen=True)
class RepairOutcome:
    contrast: MechanismContrast
    check: ContrastCheck
    proposal: RepairProposal | None
    records: tuple[RepairRecord, ...]
    stop_reason: str


class RepairController:
    """Run repair, re-check, and stop on repetition or lack of progress."""

    def __init__(self, agent, *, max_attempts: int = 3):
        if max_attempts < 0:
            raise ValueError("max_attempts must be nonnegative.")
        self._agent = agent
        self._max_attempts = max_attempts

    @property
    def max_attempts(self) -> int:
        return self._max_attempts

    def run(
        self,
        contrast: MechanismContrast,
        check: ContrastCheck,
        actions: Sequence[EvidenceAction],
        profile: FunctionalInterventionProfile,
        prediction: "StatePrediction | None" = None,
        *,
        ledger: RepairLedger | None = None,
        action_predictions: Mapping[str, "StatePrediction"] | None = None,
    ) -> RepairOutcome:
        ledger = ledger or RepairLedger()
        initial_action = contrast.plan.identifier if contrast.plan is not None else None

        def prediction_for(candidate: MechanismContrast):
            identifier = candidate.plan.identifier if candidate.plan is not None else None
            if action_predictions is not None:
                return action_predictions.get(identifier)
            return prediction if identifier == initial_action else None

        state = _evidence_state(profile)
        current_contrast, current_check = contrast, check
        records: list[RepairRecord] = []
        proposal: RepairProposal | None = None
        first_proposal: RepairProposal | None = None
        adopted_proposal: RepairProposal | None = None
        stop_reason = "ready" if current_check.ready_for_mechanism_update else "max_attempts_reached"

        for attempt in range(1, self._max_attempts + 1):
            if current_check.ready_for_mechanism_update:
                stop_reason = "ready"
                break
            proposal = self._agent.repair_contrast(current_contrast, current_check, actions)
            if first_proposal is None:
                first_proposal = proposal
            fingerprint = _fingerprint(proposal, current_check, state)
            if proposal.replacement_action is None and proposal.composed_plan is None:
                records.append(
                    ledger.register(
                        RepairRecord(
                            attempt=attempt,
                            fingerprint=fingerprint,
                            kind=proposal.kind,
                            action_identifier=None,
                            triggered_by=tuple(current_check.reasons),
                            modified_fields=proposal.modified_fields,
                            expected_gain=EXPECTED_GAIN.get(proposal.kind, ""),
                            adopted=False,
                            resolved_reasons=(),
                            remaining_reasons=tuple(current_check.reasons),
                            stop_reason="no_registered_repair",
                            contrast_identifier=current_contrast.identifier,
                            promised_fields=proposal.promised_fields,
                        )
                    )
                )
                stop_reason = "no_registered_repair"
                break
            if proposal.composed_plan is not None:
                # A composed plan is a real edit with a prospective promise, not a
                # deferral: it keeps the contrast's own readout and buys the premise
                # that makes it interpretable, at a cost the sequence cannot reach.
                # The gap is not closed by proposing it — that needs the gate's real
                # result — so the record is adopted with no resolved reason and the
                # promise ledger scores it later.
                repaired = replace(current_contrast, plan=proposal.composed_plan.readout)
                recheck = self._agent.check_contrast(repaired, profile, prediction_for(repaired))
                records.append(
                    ledger.register(
                        RepairRecord(
                            attempt=attempt,
                            fingerprint=fingerprint,
                            kind=proposal.kind,
                            action_identifier=proposal.composed_plan.gate.identifier,
                            triggered_by=tuple(current_check.reasons),
                            modified_fields=proposal.modified_fields,
                            expected_gain=EXPECTED_GAIN.get(proposal.kind, ""),
                            adopted=True,
                            resolved_reasons=(),
                            remaining_reasons=tuple(recheck.reasons),
                            stop_reason="composed_plan_executable",
                            contrast_identifier=current_contrast.identifier,
                            promised_fields=proposal.promised_fields,
                        )
                    )
                )
                adopted_proposal = proposal
                current_contrast, current_check = repaired, recheck
                stop_reason = "composed_plan_executable"
                break
            if ledger.has_fingerprint(fingerprint):
                records.append(
                    ledger.register(
                        RepairRecord(
                            attempt=attempt,
                            fingerprint=fingerprint,
                            kind=proposal.kind,
                            action_identifier=proposal.replacement_action.identifier,
                            triggered_by=tuple(current_check.reasons),
                            modified_fields=proposal.modified_fields,
                            expected_gain=EXPECTED_GAIN.get(proposal.kind, ""),
                            adopted=False,
                            resolved_reasons=(),
                            remaining_reasons=tuple(current_check.reasons),
                            stop_reason="repair_cycle_detected",
                            contrast_identifier=current_contrast.identifier,
                            promised_fields=proposal.promised_fields,
                        )
                    )
                )
                stop_reason = "repair_cycle_detected"
                break

            repaired = replace(current_contrast, plan=proposal.replacement_action)
            recheck = self._agent.check_contrast(repaired, profile, prediction_for(repaired))
            resolved = tuple(
                reason for reason in current_check.reasons if reason not in recheck.reasons
            )
            progressed = bool(resolved) or recheck.ready_for_mechanism_update
            record = ledger.register(
                RepairRecord(
                    attempt=attempt,
                    fingerprint=fingerprint,
                    kind=proposal.kind,
                    action_identifier=proposal.replacement_action.identifier,
                    triggered_by=tuple(current_check.reasons),
                    modified_fields=proposal.modified_fields,
                    expected_gain=EXPECTED_GAIN.get(proposal.kind, ""),
                    adopted=progressed,
                    resolved_reasons=resolved,
                    remaining_reasons=tuple(recheck.reasons),
                    stop_reason=None if progressed else "no_progress",
                    contrast_identifier=current_contrast.identifier,
                    promised_fields=proposal.promised_fields,
                )
            )
            records.append(record)
            if progressed and adopted_proposal is None:
                adopted_proposal = proposal
            if not progressed:
                stop_reason = "no_progress"
                break
            current_contrast, current_check = repaired, recheck
            if current_check.ready_for_mechanism_update:
                stop_reason = "ready"
                break
            if attempt == self._max_attempts:
                stop_reason = "max_attempts_reached"

        return RepairOutcome(
            contrast=current_contrast,
            check=current_check,
            # The adopted edit is the one that actually removed a failure; later attempts that
            # only circled back are recorded but are not presented as the plan's repair.
            proposal=adopted_proposal or first_proposal,
            records=tuple(records),
            stop_reason=stop_reason,
        )


def _fingerprint(
    proposal: RepairProposal, check: ContrastCheck, evidence_state: str = ""
) -> str:
    """Identify a repair as a (evidence state, failure, edit) triple.

    Cycle detection must not fire when the same edit is proposed again *after
    new evidence has arrived*: that is a legitimate next step, not a loop. The
    measured evidence state is therefore part of the identity, so a repeat is
    only a repeat while nothing has been measured in between.
    """

    if proposal.replacement_action is not None:
        action = proposal.replacement_action.identifier
    elif proposal.composed_plan is not None:
        # Two different composed plans are two different edits even when the
        # failure they answer is the same, so the plan's own identifier is the
        # edit, not the placeholder "none".
        action = proposal.composed_plan.identifier
    else:
        action = "none"
    reasons = ",".join(sorted(reason.value for reason in check.reasons))
    return f"{evidence_state}|{proposal.kind.value}|{action}|{reasons}"


def _evidence_state(profile: FunctionalInterventionProfile) -> str:
    """A stable label for everything the profile currently records as measured."""

    measured = [
        f"functional:{name}"
        for name, status in profile.functional_states.items()
        if status is MeasurementStatus.MEASURED
    ]
    measured.extend(
        name for name, status in profile.measured_fields.items() if status is MeasurementStatus.MEASURED
    )
    if profile.protein_abundance is MeasurementStatus.MEASURED:
        measured.append("protein_abundance")
    return ",".join(sorted(measured))
