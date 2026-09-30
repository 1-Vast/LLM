"""Configured chat providers, reviewed replay responses, and bounded figure inspection."""
from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import json
import math
import re
from http.client import HTTPException
from time import sleep
from typing import Any, Mapping, Protocol, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import copy
import hashlib
import base64


class JsonCompleter(Protocol):
    def complete_json(self, messages: list[dict[str, Any]], **kwargs: Any) -> tuple[dict[str, Any], Any]: ...


class ConfigurationError(RuntimeError):
    """Raised when a required runtime setting is unavailable."""


def read_dotenv(path: Path) -> dict[str, str]:
    """Read simple dotenv assignments without exporting or logging secret values."""

    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


@dataclass(frozen=True)
class MAESTROSettings:
    """Settings required by the text and vision clients.

    The key is intentionally not represented in logs, exceptions, or ``repr``.
    """

    api_key: str
    base_url: str
    chat_model: str
    vision_model: str
    log_directory: Path
    timeout_seconds: float = 90.0
    max_tokens: int = 4_000

    def __repr__(self) -> str:
        return ("MAESTROSettings(api_key='<redacted>', base_url={!r}, chat_model={!r}, "
                "vision_model={!r}, log_directory={!r}, timeout_seconds={!r}, max_tokens={!r})").format(
                    self.base_url, self.chat_model, self.vision_model, self.log_directory,
                    self.timeout_seconds, self.max_tokens)

    @classmethod
    def from_workspace(cls, workspace: Path, *, require_provider: bool = True) -> "MAESTROSettings":
        """Load settings; an explicitly supplied offline client needs no provider credentials."""

        environment = read_dotenv(workspace / ".env")
        required = (
            "DEEPSEEK_API_KEY",
            "DEEPSEEK_BASE_URL",
            "DEEPSEEK_MODEL",
            "DEEPSEEK_VISION_MODEL",
        )

        # The process environment wins over the dotenv file, for the presence
        # check as well as the value: a deployment that exports its settings and
        # ships no .env is fully configured, not missing four settings.
        def setting(name: str) -> str:
            return (os.environ.get(name) or environment.get(name) or "").strip()

        missing = [name for name in required if not setting(name)]
        if missing and require_provider:
            raise ConfigurationError(
                "Missing required MAESTRO provider settings: " + ", ".join(missing)
            )
        model = setting("DEEPSEEK_MODEL").strip()
        aliases = {"deepseek-4.1flash", "deepseek-v4.1-flash", "deepseek-v4-flash"}
        if model.lower() in aliases:
            model = "deepseek-flash"
        vision = setting("DEEPSEEK_VISION_MODEL").strip()
        if vision.lower() in aliases or vision.lower() == "deepseek-v4-flash-vision-exp":
            vision = "deepseek-flash"
        return cls(
            api_key=setting("DEEPSEEK_API_KEY"),
            base_url=setting("DEEPSEEK_BASE_URL").rstrip("/"),
            chat_model=model,
            vision_model=vision,
            log_directory=_log_directory(workspace, setting("MAESTRO_LOG_DIRECTORY")),
        )


def _log_directory(workspace: Path, configured: str) -> Path:
    """The run-record directory: ``MAESTRO_LOG_DIRECTORY`` if set, else the dated default.

    A relative setting is read against the workspace, so the same dotenv file
    means the same directory whichever directory the command is started from.
    """

    if not configured:
        return workspace / "log" / "20260910"
    path = Path(configured).expanduser()
    return path if path.is_absolute() else workspace / path


class LLMError(RuntimeError):
    """A provider failure whose message deliberately contains no request secrets."""


class LLMProtocolError(LLMError):
    """The provider returned a response incompatible with the declared contract."""


class LLMTransportError(LLMError):
    """A transport or rate-limit failure that a retry may resolve."""


# A completion request carries no side effect, so repeating one after a transport
# failure is safe. Retries are bounded and apply only to transport and
# rate-limit conditions: an authentication or request-shape rejection is a real
# answer and is raised immediately rather than hammered.
_RETRY_STATUS = frozenset({408, 409, 425, 429, 500, 502, 503, 504})
_MAX_ATTEMPTS = 4
_BACKOFF_SECONDS = 1.5
# A provider's Retry-After is honoured up to this bound; a longer wait is the
# provider saying "not now", and the caller should see the failure instead.
_MAX_RETRY_AFTER_SECONDS = 60.0


def retry_after_seconds(error: HTTPError) -> float | None:
    """The delay a rate-limited response asks for, when it states one in seconds."""

    headers = getattr(error, "headers", None)
    value = headers.get("Retry-After") if headers is not None else None
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        return None
    return seconds if math.isfinite(seconds) and seconds >= 0 else None


_FENCE = re.compile(r"\A\s*```(?:json)?\s*|\s*```\s*\Z", re.IGNORECASE)


def json_object_from_text(text: str) -> object:
    """Parse one JSON object from a reply that may be fenced or padded with prose.

    A provider asked for an object sometimes returns it inside a code fence, or followed by a
    sentence. Neither changes what the model decided, so the object is extracted rather than
    the turn discarded; anything that is still not parseable raises, and the caller reports
    what came back instead of guessing.
    """

    stripped = _FENCE.sub("", text.strip())
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    start = stripped.find("{")
    if start >= 0:
        result, _ = json.JSONDecoder().raw_decode(stripped, start)
        return result
    raise json.JSONDecodeError("no JSON object found in the reply", stripped or text, 0)


@dataclass(frozen=True)
class LLMResponse:
    """Normalized response metadata used for reproducible local audit records."""

    content: str
    model: str
    finish_reason: str | None
    usage: Mapping[str, int]


class DeepSeekChatClient:
    """Call text, JSON, and vision-capable models through Chat Completions.

    This class intentionally owns no tool execution.  Model-generated tool
    requests must be validated and dispatched by an explicit MAESTRO adapter.
    """

    def __init__(self, settings: MAESTROSettings):
        self._settings = settings
        self._usage_total: dict[str, int] = {}
        self._call_count = 0

    @property
    def settings(self) -> MAESTROSettings:
        return self._settings

    @property
    def provider_usage(self) -> dict[str, int]:
        """Tokens this client has been charged for, summed over every call it has made.

        Each call site destructures `complete_json` as `data, _`, so the per-response usage was
        parsed and then dropped and no run could say what it had spent. The client is the one
        object every call passes through, so it is where the tally belongs.
        """

        return dict(self._usage_total, calls=self._call_count)

    def complete(
        self,
        messages: Sequence[Mapping[str, Any]],
        *,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        json_output: bool = False,
        thinking_enabled: bool | None = None,
    ) -> LLMResponse:
        """Execute one completion while retaining only safe metadata locally."""

        payload: dict[str, Any] = {
            "model": model or self._settings.chat_model,
            "messages": list(messages),
            "temperature": temperature,
            "max_tokens": max_tokens or self._settings.max_tokens,
        }
        if json_output:
            payload["response_format"] = {"type": "json_object"}
        if thinking_enabled is not None:
            if type(thinking_enabled) is not bool:
                raise ValueError("thinking_enabled must be boolean or None")
            payload["thinking"] = {"type": "enabled" if thinking_enabled else "disabled"}
        request = Request(
            self._chat_endpoint(),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._settings.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        body = self._send(request)

        try:
            choice = body["choices"][0]
            content = choice["message"]["content"]
            if not isinstance(content, str):
                raise TypeError("message content is not text")
        except (KeyError, IndexError, TypeError) as error:
            # A reply can lack usable text in several different ways - no choice at all, a
            # choice with a null content, or a message carrying only a refusal or reasoning
            # field - and they call for different responses. The sentence is unchanged; what
            # follows it records which one happened, so a run's ledger says why it was charged.
            choices = body.get("choices") or []
            first = choices[0] if choices else {}
            message = first.get("message") if isinstance(first, dict) else {}
            keys = sorted(message) if isinstance(message, dict) else []
            failure = LLMProtocolError(
                "LLM response does not contain a text completion."
                f" choices={len(choices)}; finish_reason={first.get('finish_reason') if isinstance(first, dict) else None};"
                f" message_keys={keys}; usage={body.get('usage')}"
            )
            failure.code = (  # type: ignore[attr-defined]
                "no_choice_returned"
                if not choices
                else "message_without_text_content"
            )
            raise failure from error
        usage = body.get("usage") or {}
        counted = {key: int(value) for key, value in usage.items() if isinstance(value, int)}
        for key, value in counted.items():
            self._usage_total[key] = self._usage_total.get(key, 0) + value
        self._call_count += 1
        return LLMResponse(
            content=content,
            model=str(body.get("model") or payload["model"]),
            finish_reason=choice.get("finish_reason"),
            usage=counted,
        )

    def _send(self, request: Request) -> dict[str, Any]:
        """Execute one request, retrying only transport and rate-limit failures."""

        last: LLMError | None = None
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            requested_delay: float | None = None
            try:
                with urlopen(request, timeout=self._settings.timeout_seconds) as response:
                    return json.loads(response.read().decode("utf-8"))
            except HTTPError as error:
                if error.code not in _RETRY_STATUS:
                    raise LLMError(f"LLM request failed with HTTP status {error.code}.") from error
                last = LLMTransportError(f"LLM request failed with retryable HTTP status {error.code}.")
                requested_delay = retry_after_seconds(error)
            except URLError:
                last = LLMTransportError("LLM request could not reach the configured endpoint.")
            except TimeoutError:
                last = LLMTransportError("LLM request timed out.")
            except (HTTPException, ConnectionError) as error:
                # A dropped or reset connection is neither an HTTPError nor a URLError; it is a
                # transport failure a retry may resolve, and after the retries it is an LLMError.
                last = LLMTransportError(f"LLM request lost its connection: {type(error).__name__}.")
            except json.JSONDecodeError as error:
                raise LLMError("LLM request returned an unreadable response.") from error
            if attempt < _MAX_ATTEMPTS:
                delay = _BACKOFF_SECONDS * (2 ** (attempt - 1))
                if requested_delay is not None:
                    delay = min(max(delay, requested_delay), _MAX_RETRY_AFTER_SECONDS)
                sleep(delay)
        raise last or LLMTransportError("LLM request failed for an unrecorded transport reason.")

    def complete_json(
        self,
        messages: Sequence[Mapping[str, Any]],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
    ) -> tuple[dict[str, Any], LLMResponse]:
        """Request and validate one JSON-object response."""

        selected_model = model or self._settings.chat_model
        # DeepSeek V4.1 Flash is exposed as ``deepseek-flash``. Its compatible
        # Chat Completions surface rejects OpenAI's response_format=json_object;
        # use a strict prompt and validate locally instead. Thinking is disabled
        # so a small routing budget cannot be consumed without answer content.
        deepseek_flash = selected_model.lower() in {"deepseek-flash", "deepseek-4.1flash", "deepseek-v4.1-flash", "deepseek-v4-flash"}
        request_messages = list(messages)
        if deepseek_flash:
            request_messages.append({"role": "system", "content": "Return exactly one JSON object and no prose. Do not use markdown fences."})
        response = self.complete(
            request_messages, model="deepseek-flash" if deepseek_flash else selected_model,
            max_tokens=max_tokens, json_output=not deepseek_flash,
            thinking_enabled=False if deepseek_flash else None,
        )
        try:
            result = json_object_from_text(response.content)
        except json.JSONDecodeError as error:
            # The sentence is unchanged; what follows it is what makes a failure diagnosable
            # from a recorded run: whether the reply was truncated, and what it actually began
            # with. Without it a protocol failure and a budget failure look identical.
            prefix = " ".join(response.content.split())[:160]
            truncated = response.finish_reason == "length" and not response.content.strip()
            failure = LLMProtocolError(
                "LLM did not return valid JSON."
                f" finish_reason={response.finish_reason}; content starts: {prefix!r}"
            )
            # A model that reasons before it answers can spend the whole completion budget and
            # return nothing. That is a budget fault, not a malformed answer, and a caller that
            # counts refusals by name must be able to tell them apart.
            failure.code = "truncated_without_content" if truncated else "unparseable_content"  # type: ignore[attr-defined]
            raise failure from error
        if not isinstance(result, dict):
            raise LLMProtocolError("LLM JSON response must be an object.")
        return result, response

    def _chat_endpoint(self) -> str:
        base = self._settings.base_url
        if base.endswith("/chat/completions"):
            return base
        return base + "/chat/completions"


# The phrase each agent component uses to introduce itself in its system prompt.
COMPONENTS: Mapping[str, str] = {
    "task_triage": "scientific task triage component",
    "contrast_planner": "mechanism-contrast planner",
    "repair_planner": "directed contrast-repair planner",
    "tool_router": "local dataset-tool router",
    "figure_inspection": "scientific figure-inspection component",
}


class TemplateCompleterError(RuntimeError):
    """The agent asked for something the reviewed template does not answer."""


@dataclass(frozen=True)
class TemplateResponse:
    """The response metadata a metered completer expects, with zero usage."""

    model: str = "reviewed-template"
    finish_reason: str = "template"
    usage: Mapping[str, int] = field(
        default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    )


class TemplateCompleter:
    """Serve reviewed JSON answers, in order, per agent component."""

    def __init__(self, responses: Mapping[str, Sequence[Mapping[str, Any]] | Mapping[str, Any]], *, repeat_last: bool = True):
        unknown = set(responses) - set(COMPONENTS)
        if unknown:
            raise TemplateCompleterError(f"Template names unknown components: {sorted(unknown)}")
        self._queues: dict[str, list[Mapping[str, Any]]] = {}
        for component, answers in responses.items():
            queue = [answers] if isinstance(answers, Mapping) else list(answers)
            if not queue:
                raise TemplateCompleterError(f"Template for '{component}' is empty.")
            self._queues[component] = queue
        self._positions = {component: 0 for component in self._queues}
        self._repeat_last = repeat_last
        self.calls: list[dict[str, Any]] = []

    @classmethod
    def from_file(cls, path: Path) -> "TemplateCompleter":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping) or not isinstance(payload.get("responses"), Mapping):
            raise TemplateCompleterError("A template file must be an object with a 'responses' object.")
        completer = cls(payload["responses"], repeat_last=bool(payload.get("repeat_last", True)))
        completer.source_sha256 = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        return completer

    source_sha256: str | None = None

    def complete_json(self, messages: list[dict[str, Any]], **kwargs: Any) -> tuple[dict[str, Any], TemplateResponse]:
        del kwargs
        system = next((str(item.get("content", "")) for item in messages if item.get("role") == "system"), "")
        component = next((name for name, phrase in COMPONENTS.items() if phrase in system), None)
        if component is None:
            raise TemplateCompleterError("The calling component is not one the template recognises.")
        if component not in self._queues:
            raise TemplateCompleterError(f"The reviewed template has no answer for '{component}'.")
        queue = self._queues[component]
        position = self._positions[component]
        if position >= len(queue):
            if not self._repeat_last:
                raise TemplateCompleterError(f"The reviewed template has no further answer for '{component}'.")
            position = len(queue) - 1
        answer = copy.deepcopy(dict(queue[position]))
        self._positions[component] = self._positions[component] + 1
        digest = hashlib.sha256(json.dumps(answer, sort_keys=True).encode("utf-8")).hexdigest()
        self.calls.append({"component": component, "answer_index": position, "answer_sha256": digest})
        return answer, TemplateResponse()


_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}
_MAX_INLINE_BYTES = 32 * 1024 * 1024




@dataclass(frozen=True)
class VisualInspection:
    """A vision-model reading of one image, kept distinct from measured evidence."""

    path: Path
    observations: tuple[str, ...]
    quality_concerns: tuple[str, ...]
    decision_relevance: str
    limitations: tuple[str, ...]


class VisualInspector:
    """Reads figures only when supplied, and never converts a plot into biological truth."""

    def __init__(self, client: JsonCompleter, vision_model: str):
        self._client = client
        self._vision_model = vision_model

    def inspect(self, paths: tuple[Path, ...], *, question: str) -> tuple[VisualInspection, ...]:
        return tuple(self._inspect_one(path, question=question) for path in paths)

    def _inspect_one(self, path: Path, *, question: str) -> VisualInspection:
        mime_type = _MIME_TYPES.get(path.suffix.lower())
        if mime_type is None:
            raise ValueError(f"Unsupported visual asset type: {path.suffix}")
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.stat().st_size > _MAX_INLINE_BYTES:
            raise ValueError("Visual asset exceeds the inline vision request size limit.")
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        prompt = """You are MAESTRO's scientific figure-inspection component. Return JSON only.
Describe only what is visible in the image: axes, labels, groups, annotations, visible
patterns, and image-quality concerns. Do not claim causality, target engagement, or
mechanistic truth from an image alone. State how the figure can inform the next evidence
question and what source data or controls are still needed.
Return {\"observations\":[\"...\"],\"quality_concerns\":[\"...\"],
\"decision_relevance\":\"...\",\"limitations\":[\"...\"]}."""
        data, _ = self._client.complete_json(
            [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Research question: " + question},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{encoded}",
                                "detail": "high",
                            },
                        },
                    ],
                },
            ],
            model=self._vision_model,
        )
        return VisualInspection(
            path=path,
            observations=_text_items(data.get("observations")),
            quality_concerns=_text_items(data.get("quality_concerns")),
            decision_relevance=str(data.get("decision_relevance") or "No relevance stated."),
            limitations=_text_items(data.get("limitations")),
        )


def _text_items(value: Any) -> tuple[str, ...]:
    return tuple(item.strip() for item in value if isinstance(item, str) and item.strip()) if isinstance(value, list) else ()
