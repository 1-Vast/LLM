"""Append-only, secret-safe provenance records for MAESTRO runs and experiments.

File summary
- Path: src/agent/audit.py
- Purpose: Write reproducible, credential-redacted run and experiment logs.
- Core points:
  - `RunLogger` appends JSONL event and experiment streams to a dated log directory.
  - `_safe` redacts credential-like text before any record is written to disk.
- Interfaces: `RunLogger`, `event`, `experiment`, `content_digest`
- Depends on: (standard library only)
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


_SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer)\s*([:=])\s*[^\s,;]+"
)
_SECRET_FIELD = re.compile(r"(?i)(^|[_-])(api[_-]?key|authorization|token|secret|password)([_-]|$)")


def _safe(value: Any) -> Any:
    """Recursively redact credential-looking text before it reaches a log file."""

    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]" if _SECRET_FIELD.search(str(key)) else _safe(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, str):
        return _SECRET_PATTERN.sub(r"\1\2[REDACTED]", value)
    return value


class RunLogger:
    """Maintains the requested dated experiment log directory and JSONL event stream."""

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.events_path = root / "events.jsonl"
        self.experiments_path = root / "experiments.jsonl"

    def event(self, kind: str, payload: Mapping[str, Any], *, session_id: str) -> None:
        self._append(self.events_path, kind, payload, session_id)

    def experiment(self, kind: str, payload: Mapping[str, Any], *, session_id: str) -> None:
        self._append(self.experiments_path, kind, payload, session_id)

    def explain_failure(self, session_id: str) -> Mapping[str, Any] | None:
        """Return the first recorded tool failure for a session without inferring biology."""

        if not self.events_path.is_file():
            return None
        for line in self.events_path.read_text(encoding="utf-8").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("session_id") != session_id or event.get("kind") != "dataset_tool_failed":
                continue
            payload = event.get("payload")
            if not isinstance(payload, Mapping):
                continue
            trace = payload.get("failure_trace")
            if isinstance(trace, Mapping):
                return {
                    "first_invalid_transition": trace.get("first_invalid_transition"),
                    "violated_contracts": trace.get("violated_contracts", ()),
                    "affected_claims": trace.get("affected_claims", ()),
                    "candidate_causes": trace.get("candidate_causes", ()),
                    "recovery_actions": trace.get("recovery_actions", ()),
                }
            return {
                "first_invalid_transition": "unknown",
                "violated_contracts": (),
                "affected_claims": (),
                "candidate_causes": (str(payload.get("error", "unknown tool failure")),),
                "recovery_actions": (),
            }
        return None

    @staticmethod
    def content_digest(text: str) -> str:
        """Link reproducibility records without duplicating full prompts unnecessarily."""

        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _append(
        self, path: Path, kind: str, payload: Mapping[str, Any], session_id: str
    ) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "kind": kind,
            "payload": _safe(dict(payload)),
        }
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
