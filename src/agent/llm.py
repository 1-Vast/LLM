"""Minimal, dependency-free client for the configured OpenAI-compatible endpoint.

File summary
- Path: src/agent/llm.py
- Purpose: Call the configured chat/JSON/vision model through Chat Completions.
- Core points:
  - `DeepSeekChatClient` calls text, JSON, and vision models through Chat Completions.
  - It owns no tool execution; model tool requests need an explicit MAESTRO adapter.
  - Errors retain no request secrets; only safe metadata is kept locally.
- Interfaces: `DeepSeekChatClient`, `complete`, `complete_json`, `LLMResponse`, `LLMError`, `LLMProtocolError`, `LLMTransportError`, `retry_after_seconds`
- Depends on: agent.configuration
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from time import sleep
from typing import Any, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .configuration import MAESTROSettings


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
        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(stripped)):
            character = stripped[index]
            if in_string:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    in_string = False
                continue
            if character == '"':
                in_string = True
            elif character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(stripped[start : index + 1])
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
