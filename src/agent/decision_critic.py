"""Ask a typed decision model about a plan, and turn its answers into advisory findings.

File summary
- Path: src/agent/decision_critic.py
- Purpose: give MAESTRO a second opinion that is structurally unable to invent anything. The
  decision model receives the plan, the registered menu, the deterministic check and the
  menu's dependency topology as one state, and answers a fixed set of typed questions about
  them. It cannot write prose, so it cannot name an unregistered action, assert a mechanism or
  narrate a result.
- Core points:
  - Questions are built from repository objects, never from model text. A choice question's
    options are exactly the registered action identifiers, so an answer outside the menu is
    impossible by construction rather than by checking afterwards.
  - An answer becomes a finding only when it is usable, confident past a declared threshold,
    and its scope still carries weight in the judgment ledger. A revoked scope still produces
    judgments for the record, and produces no findings.
  - Findings are phrased as things to reconsider. The deterministic check remains the authority:
    this layer can ask the planner to look again, and can never adopt a repair by itself.
  - Every answer is also returned as a `TypedJudgment`, which is `model_prediction` and can
    never satisfy a premise or eliminate an explanation.
- Interfaces: `CriticThresholds`, `TypedDecisionCritic`, `CritiqueOutcome`,
  `contrast_questions`, `applicability_question`, `regulator_question`
- Depends on: agent.typesafe, agent.planner (renderers), maestro.judgment, maestro.models
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Mapping, Sequence

from maestro.judgment import JudgmentLedger, JudgmentScope, TypedJudgment
from maestro.stability import (
    DECIDING_SCOPES,
    RELIABLE_REPEATS,
    RepeatedJudgment,
    StabilityLedger,
    StabilitySummary,
    StabilityVerdict,
    canonical_value,
    effective_weight,
)
from maestro.models import ContrastCheck, EvidenceAction, MechanismContrast

from .planner import render_catalogue, render_contrast
from .typesafe import (
    MAX_CHOICE_OPTIONS,
    JevEvaluation,
    QuestionKind,
    TypeSafeJevClient,
    TypedAnswer,
    TypedQuestion,
    choice,
    noul,
    score,
)

NOT_LISTED = "none_of_the_listed_options"
SUFFICIENCY_LEVELS = (
    "No measured evidence supports choosing between the explanations.",
    "Measured evidence provides very limited support for a choice.",
    "Measured evidence provides partial support but leaves a consequential gap.",
    "Measured evidence strongly supports a choice with some uncertainty.",
    "Measured evidence fully supports choosing between the explanations.",
)
SUFFICIENCY_SCALE = len(SUFFICIENCY_LEVELS)

STATE_HEADER = (
    "MAESTRO plan review. You are judging a research plan that is already restricted to a "
    "registered menu of measurements. Answer only the typed questions. Every action identifier "
    "you may choose appears in AVAILABLE_ACTIONS below. Your answers rank and warn; they never "
    "supply a measurement, satisfy a prerequisite, or decide which explanation is true."
)

ADVISORY_LIMITS = (
    "Typed model judgment: planning-only, never a measurement.",
    "A calibrated probability is a statement about this model's own accuracy, not about biology.",
)


@dataclass(frozen=True)
class CriticThresholds:
    """How confident an answer must be before it is allowed to interrupt the planner."""

    noul_probability: float = 0.70
    choice_probability: float = 0.60
    sufficiency_floor: int = 2

    def __post_init__(self) -> None:
        for name in ("noul_probability", "choice_probability"):
            value = getattr(self, name)
            if not 0.5 <= float(value) <= 1.0:
                raise ValueError(f"invalid_threshold:{name}_must_be_between_0.5_and_1.0")
        if not 1 <= self.sufficiency_floor <= SUFFICIENCY_SCALE:
            raise ValueError("invalid_threshold:sufficiency_floor_out_of_range")


@dataclass(frozen=True)
class CritiqueOutcome:
    """What one review produced: advisory findings, judgments for the record, and refusals."""

    findings: tuple[str, ...] = ()
    judgments: tuple[TypedJudgment, ...] = ()
    refusals: tuple[str, ...] = ()
    model_version: str | None = None
    state_digest: str | None = None
    suppressed_by_revocation: bool = False
    repeats: int = 1
    stability: tuple[Mapping[str, object], ...] = ()

    def payload(self) -> dict[str, object]:
        return {
            "model_version": self.model_version,
            "state_digest": self.state_digest,
            "findings": list(self.findings),
            "judgments": [item.as_payload() for item in self.judgments],
            "refusals": list(self.refusals),
            "suppressed_by_revocation": self.suppressed_by_revocation,
            "repeats": self.repeats,
            "stability": [dict(item) for item in self.stability],
        }


def _action_options(actions: Sequence[EvidenceAction]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Registered identifiers as choice options, plus a note when the menu had to be truncated."""

    identifiers = list(dict.fromkeys(action.identifier for action in actions if action.cost >= 0))
    notes: tuple[str, ...] = ()
    limit = MAX_CHOICE_OPTIONS - 1  # one slot is reserved for NOT_LISTED
    if len(identifiers) > limit:
        notes = (f"menu_truncated_for_choice:{len(identifiers)}_to_{limit}",)
        identifiers = identifiers[:limit]
    return tuple(identifiers) + (NOT_LISTED,), notes


def contrast_questions(
    contrast: MechanismContrast, actions: Sequence[EvidenceAction]
) -> tuple[tuple[TypedQuestion, ...], tuple[str, ...]]:
    """The fixed question set for a plan review, with any menu-truncation notes."""

    options, notes = _action_options(actions)
    questions = [
        noul(
            "decision_separation",
            "Do the two explanations, as written, lead to two different development decisions?",
        ),
        noul(
            "plan_discriminates",
            "Would the planned action's declared expected outcomes actually distinguish the two "
            "explanations from one another?",
        ),
        noul(
            "boundary_stated",
            "Does the plan state at least one specific thing that its result would not establish?",
        ),
        score(
            "evidence_sufficiency",
            "How well does the evidence listed in the state support choosing between the two "
            "explanations right now? 1 means not at all, 5 means fully.",
            SUFFICIENCY_SCALE,
            levels=SUFFICIENCY_LEVELS,
        ),
    ]
    if len(options) > 1:
        questions.append(
            choice(
                "best_separating_action",
                "Which listed action would best separate the two explanations, given each action's "
                f"declared outcomes and prerequisites? Answer '{NOT_LISTED}' if none would.",
                options,
            )
        )
    return tuple(questions), notes


def applicability_question(world_model_rows: Sequence[Mapping[str, object]]) -> TypedQuestion | None:
    """One advisory question about relying on this round's virtual-cell answers."""

    if not world_model_rows:
        return None
    return noul(
        "prediction_reliance",
        "Given each prediction's declared validation status, distribution membership and "
        "reliability weight in VIRTUAL_CELL_PREDICTIONS, is it reasonable to let these predictions "
        "break ties between otherwise equal actions?",
    )


def regulator_question(candidates: Sequence[str]) -> TypedQuestion | None:
    """Rank candidate regulators from a supplied network; advisory, never a causal claim."""

    named = list(dict.fromkeys(str(item).strip() for item in candidates if str(item).strip()))
    if len(named) < 1:
        return None
    options = tuple(named[: MAX_CHOICE_OPTIONS - 1]) + (NOT_LISTED,)
    return choice(
        "candidate_regulator",
        "Among the listed regulators, which is most consistent with the response summary in the "
        f"state, treating every network edge as a hypothesis? Answer '{NOT_LISTED}' if none is.",
        options,
    )


def _reproducibility_note(scope: JudgmentScope, summary: StabilitySummary) -> str:
    """What repetition has established about a finding that could move a selection.

    Only scopes that can change which action is bought carry the note. A commentary scope that
    says the same thing twice has told a reader nothing extra, and the sentence would be noise.
    """

    if scope not in DECIDING_SCOPES:
        return ""
    if summary.verdict is StabilityVerdict.UNMEASURED:
        return " Reproducibility unchecked: this preference was asked once, and the source is not deterministic."
    share = f"{summary.agreement:.0%}" if summary.agreement is not None else "unknown"
    if summary.verdict is StabilityVerdict.INSUFFICIENT:
        return (
            f" Reproducibility {share} over {summary.repeats} repeats, too few to rely on"
            f" (at least {RELIABLE_REPEATS} are needed to tell a stable source from an unstable one)."
        )
    return f" Reproducibility {share} over {summary.repeats} repeats."


def _mean(values: Sequence[float]) -> float | None:
    numbers = [float(value) for value in values if value is not None]
    return sum(numbers) / len(numbers) if numbers else None


def _aggregate(
    question: TypedQuestion, answers: Sequence[TypedAnswer], repeated: RepeatedJudgment
) -> TypedAnswer:
    """One answer standing for several evaluations of the same unchanged state.

    A yes/no question is averaged, because with independent calls the mean has the same
    calibration as a single draw and `sigma^2 (1 - 1/n)` less expected Brier - the whole of
    the instability penalty that repetition can remove. A choice or a score is not a quantity
    to average: the mean of option three and option five is not an opinion, so those take the
    answer the source gave most often. With one evaluation every branch returns it unchanged.
    """

    if len(answers) == 1:
        return answers[0]
    confidence = _mean([a.confidence for a in answers if a.confidence is not None])
    if question.kind is QuestionKind.NOUL:
        probability = _mean([a.probability for a in answers if a.probability is not None])
        decided = answers[0].value if probability is None else probability >= 0.5
        return TypedAnswer(
            question.identifier, question.kind, decided, probability, confidence,
        )
    modal = repeated.modal_value
    matching = [a for a in answers if canonical_value(question.kind.value, a.value) == modal]
    chosen = matching[0] if matching else answers[0]
    probability = _mean([a.probability for a in matching if a.probability is not None])
    distribution: dict[str, float] = {}
    for option in {name for answer in answers for name in (answer.distribution or {})}:
        averaged = _mean([(a.distribution or {}).get(option) for a in answers])
        if averaged is not None:
            distribution[option] = averaged
    return TypedAnswer(
        question.identifier, question.kind, chosen.value, probability, confidence, distribution,
    )


class TypedDecisionCritic:
    """Runs one typed review per planning round and reports advisory findings."""

    def __init__(
        self,
        client: TypeSafeJevClient,
        *,
        ledger: JudgmentLedger | None = None,
        stability: StabilityLedger | None = None,
        thresholds: CriticThresholds | None = None,
    ):
        self._client = client
        self._ledger = ledger or JudgmentLedger()
        self._stability = stability or StabilityLedger()
        self._thresholds = thresholds or CriticThresholds()

    @property
    def ledger(self) -> JudgmentLedger:
        return self._ledger

    @property
    def stability(self) -> StabilityLedger:
        return self._stability

    @property
    def model_version(self) -> str:
        return self._client.model

    def review_plan(
        self,
        contrast: MechanismContrast,
        actions: Sequence[EvidenceAction],
        *,
        check: ContrastCheck | None = None,
        topology: Mapping[str, object] | None = None,
        world_model_rows: Sequence[Mapping[str, object]] = (),
        evidence_summary: str = "",
        context_identifier: str | None = None,
        regulator_candidates: Sequence[str] = (),
        repeats: int = 1,
    ) -> CritiqueOutcome:
        """Review one plan; a provider failure produces refusals, never an exception.

        `repeats` asks the same unchanged state more than once. The provider is not
        deterministic, so a single answer says nothing about whether the same answer would come
        back; repeating is the only way to find out, and it is what lets a ranking earn the
        right to move a selection. Each repeat is a paid call, so the default is one and the
        cost is the caller's to choose.
        """

        if repeats < 1:
            raise ValueError("invalid_repeats:at_least_one_evaluation_is_required")
        questions, notes = contrast_questions(contrast, actions)
        extra = [
            question
            for question in (
                applicability_question(world_model_rows),
                regulator_question(regulator_candidates),
            )
            if question is not None
        ]
        asked = tuple(questions) + tuple(extra)
        state = self._state(
            contrast, actions, check, topology, world_model_rows, evidence_summary, regulator_candidates
        )
        evaluations = [self._client.evaluate(state, asked) for _ in range(repeats)]
        return self._interpret(evaluations, contrast, asked, context_identifier, notes)

    def _state(
        self,
        contrast: MechanismContrast,
        actions: Sequence[EvidenceAction],
        check: ContrastCheck | None,
        topology: Mapping[str, object] | None,
        world_model_rows: Sequence[Mapping[str, object]],
        evidence_summary: str,
        regulator_candidates: Sequence[str],
    ) -> str:
        """Assemble the state deterministically from repository objects only."""

        sections = [
            STATE_HEADER,
            "CONTRAST\n" + render_contrast(contrast),
            "AVAILABLE_ACTIONS\n" + render_catalogue(actions),
        ]
        if check is not None:
            sections.append(
                "DETERMINISTIC_CHECK\n"
                + json.dumps(
                    {
                        "ready_for_mechanism_update": check.ready_for_mechanism_update,
                        "reasons": [reason.value for reason in check.reasons],
                        "missing_prerequisites": list(check.missing_prerequisites),
                    },
                    separators=(",", ":"),
                )
            )
        if topology:
            sections.append(
                "ACTION_TOPOLOGY\n" + json.dumps(dict(topology), separators=(",", ":"), allow_nan=False)
            )
        if world_model_rows:
            sections.append(
                "VIRTUAL_CELL_PREDICTIONS (planning-only model output, not measurements)\n"
                + "\n".join(
                    json.dumps(dict(row), separators=(",", ":"), allow_nan=False, sort_keys=True)
                    for row in world_model_rows
                )
            )
        if regulator_candidates:
            sections.append(
                "CANDIDATE_REGULATORS (network edges are hypotheses, not causal claims)\n"
                + json.dumps(list(regulator_candidates), separators=(",", ":"))
            )
        if evidence_summary.strip():
            sections.append("EVIDENCE\n" + evidence_summary.strip())
        return "\n\n".join(sections)

    def _interpret(
        self,
        evaluations: Sequence[JevEvaluation],
        contrast: MechanismContrast,
        questions: Sequence[TypedQuestion],
        context_identifier: str | None,
        notes: Sequence[str],
    ) -> CritiqueOutcome:
        """Turn one or more evaluations of the same state into judgments, findings and verdicts.

        With several evaluations the answer reported is the aggregate, not the last one: the
        mean probability for a yes/no question, because averaging n independent calls removes
        `sigma^2 (1 - 1/n)` of expected Brier, and the modal answer for a choice or a score,
        because those decide by their value rather than by a number that can be averaged.
        """

        by_identifier = {question.identifier: question for question in questions}
        usable = [item for item in evaluations if item.answers]
        primary = usable[0] if usable else (evaluations[0] if evaluations else None)
        if primary is None:
            return CritiqueOutcome(refusals=tuple(notes))

        judgments: list[TypedJudgment] = []
        findings: list[str] = []
        stability_rows: list[Mapping[str, object]] = []
        suppressed = False

        for identifier, question in by_identifier.items():
            answers = [
                item.answers[identifier]
                for item in usable
                if identifier in item.answers and item.answers[identifier].usable
            ]
            if not answers:
                continue
            scope = _scope_for(identifier)
            repeated = RepeatedJudgment(
                question_id=identifier,
                scope=scope,
                kind=question.kind.value,
                model_version=primary.model,
                state_digest=primary.state_digest,
                values=tuple(canonical_value(question.kind.value, a.value) for a in answers),
                probabilities=tuple(a.probability for a in answers if a.probability is not None),
                context_identifier=context_identifier,
            )
            if repeated.repeats > 1:
                self._stability.record(repeated)
                stability_rows.append(repeated.as_payload())

            answer = _aggregate(question, answers, repeated)
            judgment = TypedJudgment(
                question_id=identifier,
                scope=scope,
                kind=question.kind.value,
                value=answer.value,  # type: ignore[arg-type]
                model_version=primary.model,
                state_digest=primary.state_digest,
                probability=answer.probability,
                confidence=answer.confidence,
                limitations=ADVISORY_LIMITS,
                context_identifier=context_identifier,
            )
            judgments.append(judgment)

            if self._ledger.is_revoked(scope, primary.model, context_identifier):
                suppressed = True
                continue
            summary = self._stability.summarize(scope, primary.model, context_identifier)
            if summary.revoked:
                # Measured irreproducibility. This needs no biological outcome to establish,
                # which is the point: it can revoke a source the Brier ledger cannot yet judge.
                suppressed = True
                continue
            finding = self._finding(identifier, question, answer, contrast)
            if finding is not None:
                # Not having asked twice is not the same as having asked twice and disagreed.
                # An unchecked preference is still said, and said as unchecked, because this
                # architecture names what it does not know rather than dropping it.
                findings.append(finding + _reproducibility_note(scope, summary))

        summaries = tuple(
            dict(
                summary.as_payload(),
                calibration_weight=self._ledger.weight(scope, primary.model, context_identifier),
                effective_weight=effective_weight(
                    self._ledger.weight(scope, primary.model, context_identifier),
                    summary.weight,
                ),
            )
            for scope, summary in (
                (scope, self._stability.summarize(scope, primary.model, context_identifier))
                for scope in sorted({_scope_for(name) for name in by_identifier}, key=lambda s: s.value)
            )
        )

        return CritiqueOutcome(
            findings=tuple(findings),
            judgments=tuple(judgments),
            refusals=tuple(
                reason for item in evaluations for reason in item.refusals()
            ) + tuple(notes),
            model_version=primary.model,
            state_digest=primary.state_digest,
            suppressed_by_revocation=suppressed,
            repeats=len(evaluations),
            stability=tuple(stability_rows) + summaries,
        )

    def _finding(
        self,
        identifier: str,
        question: TypedQuestion,
        answer: TypedAnswer,
        contrast: MechanismContrast,
    ) -> str | None:
        """Turn one confident answer into one advisory sentence, or nothing."""

        thresholds = self._thresholds
        if question.kind is QuestionKind.NOUL:
            probability = answer.probability
            says_no = answer.value is False
            confidence_in_no = (1.0 - probability) if probability is not None else None
            if not says_no or confidence_in_no is None or confidence_in_no < thresholds.noul_probability:
                return None
            reported = f"p(no)={confidence_in_no:.2f}"
            messages = {
                "decision_separation": (
                    "A typed decision model judges that the two explanations do not lead to two "
                    f"different development decisions ({reported}). Re-read the proposed_action fields."
                ),
                "plan_discriminates": (
                    "A typed decision model judges that the planned action's declared outcomes would "
                    f"not separate the two explanations ({reported}). Consider another registered action."
                ),
                "boundary_stated": (
                    "A typed decision model judges that the plan states no specific limit on what its "
                    f"result could establish ({reported}). Add one interpretation boundary."
                ),
                "prediction_reliance": (
                    "A typed decision model judges that this round's predictions are not a sound basis "
                    f"for breaking ties ({reported}). Prefer the declared costs and coverage."
                ),
            }
            return messages.get(identifier)

        if question.kind is QuestionKind.CHOICE:
            probability = answer.probability
            if probability is not None and probability < thresholds.choice_probability:
                return None
            selected = str(answer.value)
            reported = f"p={probability:.2f}" if probability is not None else "no probability reported"
            if identifier == "best_separating_action":
                if selected == NOT_LISTED:
                    return (
                        "A typed decision model judges that no listed action would separate the two "
                        f"explanations ({reported}). Treat this as a capability gap, not a plan error."
                    )
                planned = contrast.plan.identifier if contrast.plan is not None else None
                if planned is not None and selected != planned:
                    return (
                        f"A typed decision model prefers the registered action '{selected}' over the "
                        f"planned '{planned}' for separating the two explanations ({reported})."
                    )
                return None
            if identifier == "candidate_regulator" and selected != NOT_LISTED:
                return (
                    f"A typed decision model ranks '{selected}' as the candidate regulator most "
                    f"consistent with the response summary ({reported}). This is a hypothesis to test, "
                    "not a causal finding, and no network edge is evidence."
                )
            return None

        if identifier == "evidence_sufficiency" and isinstance(answer.value, int):
            if answer.value > thresholds.sufficiency_floor:
                return None
            return (
                f"A typed decision model scores current evidence {answer.value}/{SUFFICIENCY_SCALE} for "
                "choosing between the two explanations. Acquire a separating measurement before deciding."
            )
        return None


def _scope_for(identifier: str) -> JudgmentScope:
    if identifier == "best_separating_action":
        return JudgmentScope.ACTION_RANKING
    if identifier == "prediction_reliance":
        return JudgmentScope.APPLICABILITY_ADVISORY
    if identifier == "candidate_regulator":
        return JudgmentScope.HYPOTHESIS_ADVISORY
    return JudgmentScope.PLAN_CRITIQUE
