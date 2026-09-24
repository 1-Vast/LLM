"""Safe provider-call accounting for bounded evaluation runs.

File summary
- Path: src/evaluation/tracking.py
- Purpose: Wrap a JSON completer to record only safe provider-call metadata.
- Core points:
  - `TrackingCompleter` logs model and usage metadata only, never prompts or credentials.
- Interfaces: `TrackingCompleter`, `complete_json`
- Depends on: (standard library only)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TrackingCompleter:
    """Record model and usage metadata without retaining prompts, outputs, or credentials."""

    client: Any
    calls: list[dict[str, Any]] = field(default_factory=list)

    def complete_json(self, messages, **kwargs):
        data, response = self.client.complete_json(messages, **kwargs)
        self.calls.append({
            "model": response.model,
            "finish_reason": response.finish_reason,
            "usage": dict(response.usage),
        })
        return data, response
