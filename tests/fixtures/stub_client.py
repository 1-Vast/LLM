"""A deterministic stand-in for the language-model client.

File summary
- Path: tools/shared/stub_client.py
- Purpose: let an offline caller drive code that expects an LLM client, without a
  provider, a key, a network call or a paid request.
- Core points:
  - A sequence of responses is consumed in order; a single mapping is returned for
    every call. Both shapes occur in practice, and one class covers them so the
    same stand-in is not re-written per module.
  - `calls` records `(messages, kwargs)` per call. A test asserts on it when the
    property under test is *what the caller sent*, not what the client answered.
  - This is not a model and not a measurement: it answers with the fixed value it
    was constructed with, so a passing test says something about the caller only.
- Interfaces: `StubClient`
- Depends on: (standard library only)
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence


class StubClient:
    """Return declared responses, in order or always, and record what was sent."""

    def __init__(self, responses: Mapping[str, Any] | Sequence[Mapping[str, Any]] | Any, *,
                 repeat: bool | None = None) -> None:
        fixed = repeat if repeat is not None else self._is_single(responses)
        self._single: Any = responses if fixed else None
        self._repeat = bool(fixed)
        self.responses: list[Any] = [] if fixed else list(responses)
        self.calls: list[tuple[Any, dict[str, Any]]] = []

    @staticmethod
    def _is_single(responses: object) -> bool:
        """A mapping, a string or anything non-iterable is one answer, not a queue."""

        if isinstance(responses, (str, bytes, bytearray, Mapping)):
            return True
        return not hasattr(responses, "__iter__")

    def complete_json(self, messages, **kwargs):
        """The client contract: return `(payload, raw_response)`."""

        self.calls.append((messages, kwargs))
        if self._repeat:
            return self._single, object()
        if not self.responses:
            raise AssertionError(
                "StubClient ran out of responses: the caller made more model calls than the test declared."
            )
        return self.responses.pop(0), object()
