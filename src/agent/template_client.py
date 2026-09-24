"""Deterministic, non-LLM answers for the agent's structured calls.

File summary
- Path: src/agent/template_client.py
- Purpose: run the unchanged agent loop without a language model. Every structured call is answered from a reviewed template keyed by the component that asked, so the same controller, tools, virtual-cell protocol and case store can be exercised and compared with and without an LLM.
- Core points:
  - A call is matched by the component named in its system prompt; a call from an unexpected component raises instead of improvising an answer.
  - Answers are data a person reviewed before the run; nothing is generated, and every served answer is recorded with its digest.
  - Usage is reported as zero tokens, so a metered ledger stays exact when this completer stands in for a paid one.
- Interfaces: `TemplateCompleter`, `TemplateResponse`, `TemplateCompleterError`, `COMPONENTS`
- Depends on: (standard library only)
"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

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
