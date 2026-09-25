"""Client for the TypeSafe Jev decision model, which answers typed questions instead of writing text.

File summary
- Path: src/agent/typesafe.py
- Purpose: let MAESTRO ask a calibrated decision model a small set of *typed* questions about a
  state it already holds, and receive one structured answer per question. Jev returns a choice,
  a score or a yes/no probability; it does not generate prose, so it cannot propose a plan, name
  an action that is not on the menu, or narrate a mechanism.
- Core points:
  - Three question kinds exist and nothing else: `noul` (yes/no with a probability), `choice`
    (one option from a declared list, with a probability per option) and `score` (an ordered
    scale). Each is validated before the request is built, so a malformed question never leaves
    this process.
  - Parsing fails closed. A missing or out-of-range field becomes a named refusal on that one
    answer, listing the keys the provider actually returned; it never becomes a guessed value.
    The documented Jev fields and earlier aliases are accepted; an unrecognised shape is refused.
  - The API key is read from the environment or `.env` and is never placed in a log, an
    exception or a `repr`.
  - Every evaluation carries a digest of the exact state that was judged, so a later record
    cannot be re-attached to different text.
- Interfaces: `TypeSafeSettings`, `TypeSafeJevClient`, `QuestionKind`, `TypedQuestion`,
  `TypedAnswer`, `JevEvaluation`, `JevError`, `JevProtocolError`, `JevTransportError`,
  `noul`, `choice`, `score`
- Depends on: agent.configuration, agent.llm (transport retry helper only)
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from time import sleep
from typing import Any, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .configuration import read_dotenv
from .llm import retry_after_seconds

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
                    return json.loads(response.read().decode("utf-8"))
            except HTTPError as error:
                if error.code not in _RETRY_STATUS:
                    raise JevError(f"request failed with HTTP status {error.code}") from error
                last = JevTransportError(f"retryable HTTP status {error.code}")
                requested_delay = retry_after_seconds(error)
            except URLError:
                last = JevTransportError("the configured endpoint could not be reached")
            except TimeoutError:
                last = JevTransportError("the request timed out")
            except json.JSONDecodeError as error:
                raise JevProtocolError("the response was not readable JSON") from error
            if attempt < _MAX_ATTEMPTS:
                delay = _BACKOFF_SECONDS * (2 ** (attempt - 1))
                if requested_delay is not None:
                    delay = min(max(delay, requested_delay), _MAX_RETRY_AFTER_SECONDS)
                sleep(delay)
        raise last or JevTransportError("the request failed for an unrecorded transport reason")
