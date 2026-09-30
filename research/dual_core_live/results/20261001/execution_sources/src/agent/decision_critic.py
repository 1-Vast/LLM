"""Typed decision-provider contracts and advisory review; judgments never become measurements."""
from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass, field
from enum import Enum
from http.client import HTTPException
from pathlib import Path
from time import sleep
from typing import Any, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from .llm import LLMProtocolError, decode_response_object, read_dotenv, retry_after_seconds
from maestro.judgment import JudgmentLedger, JudgmentScope, TypedJudgment
from maestro.judgment import DECIDING_SCOPES, RELIABLE_REPEATS, RepeatedJudgment, StabilityLedger, StabilitySummary, StabilityVerdict, canonical_value, effective_weight
from maestro.models import ContrastCheck, EvidenceAction, MechanismContrast
from .planner import render_catalogue, render_contrast


# Provider limits taken from the published description of the model. They are enforced here so
# an oversized request is refused locally instead of being billed and rejected remotely.
MAX_CHOICE_OPTIONS = 255
MIN_CHOICE_OPTIONS = 2
MIN_SCORE_SCALE = 2
MAX_SCORE_SCALE = 10
MAX_QUESTIONS = 64

DEFAULT_ENDPOINT = "https://api.typesafe.ai"
EVALUATE_PATH = "/v1/systemone"

_RETRY_STATUS = frozenset({408, 409, 425, 429, 500, 502, 503, 504})
_MAX_ATTEMPTS = 3
_BACKOFF_SECONDS = 1.5
_MAX_RETRY_AFTER_SECONDS = 60.0


class JevError(RuntimeError):
    """A provider failure whose message deliberately contains no request secrets."""


class JevProtocolError(JevError):
    """The provider returned a response incompatible with the declared contract."""


class JevTransportError(JevError):
    """A transport or rate-limit failure that a retry may resolve."""


@dataclass(frozen=True)
class TypeSafeSettings:
    """Endpoint, model and secret for the decision model; absent settings disable the feature."""

    api_key: str
    endpoint: str
    model: str
    timeout_seconds: float = 30.0

    def __repr__(self) -> str:
        return (
            "TypeSafeSettings(api_key='<redacted>', endpoint={!r}, model={!r}, timeout_seconds={!r})"
        ).format(self.endpoint, self.model, self.timeout_seconds)

    @property
    def evaluate_url(self) -> str:
        """The full evaluate URL, whether the configured endpoint is a base or a full path."""

        base = self.endpoint.rstrip("/")
        return base if "/v1/" in base else base + EVALUATE_PATH

    @classmethod
    def from_workspace(cls, workspace: Path) -> "TypeSafeSettings | None":
        """Load the optional TypeSafe block; return ``None`` when it is not configured.

        The process environment wins over the dotenv file, matching `MAESTROSettings`. A partly
        configured block (a key with no model, for example) is treated as absent rather than
        half-enabled, because a half-configured decision critic would fail on the first call.
        """

        dotenv = read_dotenv(workspace / ".env")

        def setting(name: str) -> str:
            return (os.environ.get(name) or dotenv.get(name) or "").strip()

        api_key, endpoint, model = (
            setting("TYPESAFE_API_KEY"),
            setting("TYPESAFE_ENDPOINT") or DEFAULT_ENDPOINT,
            setting("TYPESAFE_MODEL"),
        )
        if not api_key or not model:
            return None
        timeout = setting("TYPESAFE_TIMEOUT_SECONDS")
        try:
            seconds = float(timeout) if timeout else 30.0
        except ValueError:
            seconds = 30.0
        if not math.isfinite(seconds) or seconds <= 0:
            seconds = 30.0
        return cls(api_key=api_key, endpoint=endpoint, model=model, timeout_seconds=seconds)


class QuestionKind(str, Enum):
    """The three primitives the decision model accepts; there is no free-text kind."""

    NOUL = "noul"
    CHOICE = "choice"
    SCORE = "score"


@dataclass(frozen=True)
class TypedQuestion:
    """One typed question, validated before any request is built."""

    identifier: str
    kind: QuestionKind
    instructions: str
    options: tuple[str, ...] = ()
    scale: int | None = None
    levels: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.identifier.strip() or not self.instructions.strip():
            raise ValueError("invalid_question:identifier_and_instructions_required")
        if not isinstance(self.kind, QuestionKind):
            raise ValueError("invalid_question:unknown_kind")
        if self.kind is QuestionKind.CHOICE:
            if not MIN_CHOICE_OPTIONS <= len(self.options) <= MAX_CHOICE_OPTIONS:
                raise ValueError(
                    f"invalid_question:choice_needs_{MIN_CHOICE_OPTIONS}_to_{MAX_CHOICE_OPTIONS}_options"
                )
            if len(set(self.options)) != len(self.options) or any(not str(o).strip() for o in self.options):
                raise ValueError("invalid_question:choice_options_must_be_unique_and_named")
            if self.scale is not None or self.levels:
                raise ValueError("invalid_question:choice_has_no_scale_or_levels")
        elif self.kind is QuestionKind.SCORE:
            if self.options:
                raise ValueError("invalid_question:score_has_no_options")
            if not isinstance(self.scale, int) or isinstance(self.scale, bool):
                raise ValueError("invalid_question:score_needs_an_integer_scale")
            if not MIN_SCORE_SCALE <= self.scale <= MAX_SCORE_SCALE:
                raise ValueError(f"invalid_question:score_scale_{MIN_SCORE_SCALE}_to_{MAX_SCORE_SCALE}")
            if self.levels and (len(self.levels) != self.scale or any(not level.strip() for level in self.levels)):
                raise ValueError("invalid_question:score_levels_must_match_scale")
        elif self.options or self.scale is not None or self.levels:
            raise ValueError("invalid_question:noul_takes_no_options_scale_or_levels")

    def payload(self) -> dict[str, Any]:
        body: dict[str, Any] = {"type": self.kind.value, "instructions": self.instructions}
        if self.kind is QuestionKind.CHOICE:
            body["criteria"] = dict.fromkeys(self.options)
        if self.kind is QuestionKind.SCORE:
            body["criteria"] = list(self.levels or (
                f"Level {index} of {self.scale}" for index in range(1, (self.scale or 0) + 1)
            ))
        return body


def noul(identifier: str, instructions: str) -> TypedQuestion:
    """A yes/no question; the answer carries the probability of yes."""

    return TypedQuestion(identifier, QuestionKind.NOUL, instructions)


def choice(identifier: str, instructions: str, options: Sequence[str]) -> TypedQuestion:
    """A single selection from a declared, closed list of options."""

    return TypedQuestion(identifier, QuestionKind.CHOICE, instructions, options=tuple(options))


def score(identifier: str, instructions: str, scale: int, *, levels: Sequence[str] = ()) -> TypedQuestion:
    """A position on an ordered scale from 1 to ``scale``."""

    return TypedQuestion(identifier, QuestionKind.SCORE, instructions, scale=scale, levels=tuple(levels))


# The documented fields are accepted alongside earlier aliases; unknown shapes still fail closed.
RESPONSE_ALIASES: Mapping[str, tuple[str, ...]] = {
    "value": ("value", "answer", "selected", "choice", "score", "result"),
    "probability": ("noul", "probability", "p", "yes_probability", "confidence_probability"),
    "confidence": ("confidence", "certainty"),
    "distribution": ("probabilities", "distribution", "option_probabilities", "scores"),
    "answers": ("answers", "results", "outputs"),
    "usage": ("usage", "tokens"),
}


def _first(payload: Mapping[str, Any], names: Sequence[str]) -> Any:
    for name in names:
        if name in payload:
            return payload[name]
    return None


def _unit(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) and 0.0 <= number <= 1.0 else None


@dataclass(frozen=True)
class TypedAnswer:
    """One answer, or a named refusal explaining why it cannot be used."""

    identifier: str
    kind: QuestionKind
    value: str | int | bool | None = None
    probability: float | None = None
    confidence: float | None = None
    distribution: Mapping[str, float] = field(default_factory=dict)
    refusal: str | None = None

    @property
    def usable(self) -> bool:
        return self.refusal is None and self.value is not None

    @classmethod
    def refused(cls, question: TypedQuestion, reason: str) -> "TypedAnswer":
        return cls(question.identifier, question.kind, refusal=reason)

    @classmethod
    def parse(cls, question: TypedQuestion, payload: Any) -> "TypedAnswer":
        """Read one answer, refusing anything the contract does not cover."""

        if not isinstance(payload, Mapping):
            return cls.refused(question, f"answer_not_an_object:{type(payload).__name__}")
        keys = ",".join(sorted(str(k) for k in payload))
        raw_value = _first(payload, RESPONSE_ALIASES["value"])
        confidence = _unit(_first(payload, RESPONSE_ALIASES["confidence"]))
        probability = _unit(_first(payload, RESPONSE_ALIASES["probability"]))

        if question.kind is QuestionKind.NOUL:
            if probability is None and isinstance(raw_value, (int, float)) and not isinstance(raw_value, bool):
                probability = _unit(raw_value)
            if isinstance(raw_value, bool):
                decided = raw_value
            elif probability is not None:
                decided = probability >= 0.5
            else:
                return cls.refused(question, f"noul_without_probability_or_boolean;keys={keys}")
            return cls(question.identifier, question.kind, decided, probability, confidence)

        if question.kind is QuestionKind.CHOICE:
            distribution: dict[str, float] = {}
            raw_distribution = _first(payload, RESPONSE_ALIASES["distribution"])
            if isinstance(raw_distribution, Mapping):
                for option, weight in raw_distribution.items():
                    number = _unit(weight)
                    if str(option) not in question.options:
                        return cls.refused(question, f"choice_distribution_names_an_unlisted_option:{option}")
                    if number is None:
                        return cls.refused(question, f"choice_probability_out_of_range:{option}")
                    distribution[str(option)] = number
            selected = str(raw_value) if isinstance(raw_value, str) else None
            if selected is None and distribution:
                selected = max(distribution, key=lambda name: (distribution[name], name))
            if selected is None:
                return cls.refused(question, f"choice_without_a_selected_option;keys={keys}")
            if selected not in question.options:
                return cls.refused(question, f"choice_outside_the_declared_options:{selected}")
            if probability is None:
                probability = distribution.get(selected)
            return cls(question.identifier, question.kind, selected, probability, confidence, distribution)

        documented_score = "score" in payload
        raw_value = payload["score"] if documented_score else raw_value
        if not isinstance(raw_value, (int, float)) or isinstance(raw_value, bool):
            return cls.refused(question, f"score_without_a_number;keys={keys}")
        number = float(raw_value)
        lower, upper = (0, (question.scale or 0) - 1) if documented_score else (1, question.scale or 0)
        if not math.isfinite(number) or not lower <= number <= upper:
            return cls.refused(question, f"score_outside_{lower}_to_{upper}:{raw_value}")
        return cls(
            question.identifier, question.kind,
            int(round(number + (1 if documented_score else 0))), probability, confidence,
        )


@dataclass(frozen=True)
class JevEvaluation:
    """The result of one evaluation: answers keyed by question id, plus what was judged."""

    model: str
    state_digest: str
    answers: Mapping[str, TypedAnswer]
    usage: Mapping[str, int] = field(default_factory=dict)
    refusal: str | None = None

    @property
    def usable_answers(self) -> Mapping[str, TypedAnswer]:
        return {key: answer for key, answer in self.answers.items() if answer.usable}

    def refusals(self) -> tuple[str, ...]:
        reasons = [f"{key}:{answer.refusal}" for key, answer in self.answers.items() if answer.refusal]
        return tuple(reasons + ([self.refusal] if self.refusal else []))


def state_digest(state: str) -> str:
    return hashlib.sha256(state.encode("utf-8")).hexdigest()


class TypeSafeJevClient:
    """Ask the decision model a bounded set of typed questions about one state."""

    def __init__(self, settings: TypeSafeSettings):
        self._settings = settings

    @property
    def settings(self) -> TypeSafeSettings:
        return self._settings

    @property
    def model(self) -> str:
        return self._settings.model

    def evaluate(self, state: str, questions: Sequence[TypedQuestion]) -> JevEvaluation:
        """Evaluate one state against typed questions; a failure is a refusal, not an exception.

        The whole evaluation is advisory, so a provider outage must not end a MAESTRO turn.
        Transport and protocol failures are returned as a refused evaluation with no answers.
        """

        digest = state_digest(state)
        if not isinstance(state, str) or not state.strip():
            return JevEvaluation(self.model, digest, {}, refusal="empty_state")
        if not questions:
            return JevEvaluation(self.model, digest, {}, refusal="no_questions")
        if len(questions) > MAX_QUESTIONS:
            return JevEvaluation(self.model, digest, {}, refusal=f"too_many_questions:{len(questions)}")
        identifiers = [question.identifier for question in questions]
        if len(set(identifiers)) != len(identifiers):
            return JevEvaluation(self.model, digest, {}, refusal="duplicate_question_identifier")

        body = {
            "model": self._settings.model,
            "state": state,
            "questions": {question.identifier: question.payload() for question in questions},
        }
        try:
            payload = self._send(body)
        except JevError as error:
            return JevEvaluation(self.model, digest, {}, refusal=f"{type(error).__name__}:{error}")
        if not isinstance(payload, Mapping):
            return JevEvaluation(self.model, digest, {}, refusal="JevProtocolError:response_must_be_object")

        raw_answers = _first(payload, RESPONSE_ALIASES["answers"])
        if not isinstance(raw_answers, Mapping):
            keys = ",".join(sorted(str(k) for k in payload)) if isinstance(payload, Mapping) else ""
            return JevEvaluation(self.model, digest, {}, refusal=f"response_without_answers;keys={keys}")
        answers = {
            question.identifier: (
                TypedAnswer.parse(question, raw_answers[question.identifier])
                if question.identifier in raw_answers
                else TypedAnswer.refused(question, "answer_missing_from_response")
            )
            for question in questions
        }
        raw_usage = _first(payload, RESPONSE_ALIASES["usage"])
        usage = (
            {str(k): int(v) for k, v in raw_usage.items() if isinstance(v, int) and not isinstance(v, bool)}
            if isinstance(raw_usage, Mapping)
            else {}
        )
        served = payload.get("model") if isinstance(payload, Mapping) else None
        return JevEvaluation(str(served or self.model), digest, answers, usage)

    def _send(self, body: Mapping[str, Any]) -> Any:
        """One request, retrying only transport and rate-limit failures."""

        request = Request(
            self._settings.evaluate_url,
            data=json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._settings.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        last: JevError | None = None
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            requested_delay: float | None = None
            try:
                with urlopen(request, timeout=self._settings.timeout_seconds) as response:
                    return decode_response_object(response.read())
            except HTTPError as error:
                if error.code not in _RETRY_STATUS:
                    raise JevError(f"request failed with HTTP status {error.code}") from error
                last = JevTransportError(f"retryable HTTP status {error.code}")
                requested_delay = retry_after_seconds(error)
            except URLError:
                last = JevTransportError("the configured endpoint could not be reached")
            except TimeoutError:
                last = JevTransportError("the request timed out")
            except (HTTPException, ConnectionError) as error:
                # A dropped or reset connection (http.client.RemoteDisconnected, ConnectionResetError)
                # is neither an HTTPError nor a URLError; without this branch it escaped evaluate()
                # as a raw exception and ended a 2026-09-26 run, against this client's contract.
                last = JevTransportError(f"the connection failed: {type(error).__name__}")
            except LLMProtocolError as error:
                raise JevProtocolError(str(error)) from error
            if attempt < _MAX_ATTEMPTS:
                delay = _BACKOFF_SECONDS * (2 ** (attempt - 1))
                if requested_delay is not None:
                    delay = min(max(delay, requested_delay), _MAX_RETRY_AFTER_SECONDS)
                sleep(delay)
        raise last or JevTransportError("the request failed for an unrecorded transport reason")


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
        versions = sorted({item.model for item in usable})
        states = {item.state_digest for item in usable}
        if len(versions) > 1 or len(states) > 1:
            reasons = tuple(reason for item in evaluations for reason in item.refusals()) + tuple(notes)
            if len(versions) > 1:
                reasons += ("mixed_model_versions:" + ",".join(versions),)
            if len(states) > 1:
                reasons += ("mixed_state_digests",)
            return CritiqueOutcome(refusals=reasons, repeats=len(evaluations))

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
