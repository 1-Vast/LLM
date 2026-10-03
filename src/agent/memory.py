"""Scoped derived memories, result reflection, and secret-safe run records."""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from maestro.models import EvidenceKind
from maestro.handoff import RoundRecord, json_loads, review_run, write_round
# Historical imports remain aliases to the single fact implementation.
from .case_store import CaseState, CaseSnapshot, MeasurementResult, ResultImport, CaseStore, connect, _now


class MemoryKind(str, Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


class EpistemicStatus(str, Enum):
    PROPOSED = "proposed"
    RETRIEVED = "retrieved"
    MEASURED = "measured"
    VERIFIED = "verified"
    DERIVED = "derived"


@dataclass(frozen=True)
class MemoryScope:
    """Access boundary applied before ranking stored experience."""

    case_id: str | None = None
    task_type: str | None = None
    dataset_partitions: tuple[str, ...] = ()
    biological_context: str | None = None
    allowed_origins: tuple[str, ...] = ()
    created_after: str | None = None
    created_before: str | None = None
    allow_cross_case: bool = False


@dataclass(frozen=True)
class MemoryEntry:
    """One stored memory record with its kind, content, and epistemic status."""

    identifier: str
    kind: MemoryKind
    content: str
    status: EpistemicStatus
    provenance: str
    session_id: str
    created_at: str
    scope: MemoryScope = MemoryScope()
    parent_ids: tuple[str, ...] = ()
    retracted: bool = False


class MemoryStore:
    """SQLite-backed memory designed to retrieve experience without upgrading it to fact."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def remember(
        self,
        content: str,
        *,
        kind: MemoryKind,
        status: EpistemicStatus,
        provenance: str,
        session_id: str,
        scope: MemoryScope | None = None,
        parent_ids: tuple[str, ...] = (),
    ) -> MemoryEntry:
        entry = MemoryEntry(
            identifier=str(uuid.uuid4()),
            kind=kind,
            content=content.strip(),
            status=status,
            provenance=provenance.strip(),
            session_id=session_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            scope=scope or MemoryScope(),
            parent_ids=tuple(parent_ids),
        )
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO memories(
                    id, kind, content, status, provenance, session_id, created_at, scope_json, parent_ids, retracted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    entry.identifier,
                    entry.kind.value,
                    entry.content,
                    entry.status.value,
                    entry.provenance,
                    entry.session_id,
                    entry.created_at,
                    _scope_json(entry.scope),
                    ",".join(entry.parent_ids),
                ),
            )
        return entry

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        kinds: Iterable[MemoryKind] | None = None,
        scope: MemoryScope | None = None,
    ) -> tuple[MemoryEntry, ...]:
        """Retrieve lexical matches deterministically; callers retain the recorded status."""

        allowed = tuple(kind.value for kind in kinds) if kinds else ()
        sql = "SELECT id, kind, content, status, provenance, session_id, created_at, scope_json, parent_ids, retracted FROM memories"
        arguments: list[str] = []
        clauses = ["retracted = 0"]
        if allowed:
            clauses.append("kind IN (" + ",".join("?" for _ in allowed) + ")")
            arguments.extend(allowed)
        sql += " WHERE " + " AND ".join(clauses)
        with self._connection() as connection:
            rows = connection.execute(sql, arguments).fetchall()
        query_terms = set(_terms(query))
        ranked = []
        for row in rows:
            if not _scope_matches(_scope_from_json(row[7]), scope, row[4], row[6]):
                continue
            score = _lexical_score(query_terms, row[2])
            if score > 0:
                ranked.append((score, row))
        ranked.sort(key=lambda item: (item[0], item[1][6]), reverse=True)
        return tuple(_row_to_entry(row) for _, row in ranked[:limit])

    def retract(self, identifier: str) -> tuple[str, ...]:
        """Mark a memory and its derived descendants inactive without deleting history."""

        with self._connection() as connection:
            rows = connection.execute("SELECT id, parent_ids FROM memories WHERE retracted = 0").fetchall()
            known = {row[0]: tuple(item for item in row[1].split(",") if item) for row in rows}
            if identifier not in known:
                raise ValueError(f"Unknown active memory: {identifier}")
            children = {}
            for child, parents in known.items():
                for parent in parents:
                    children.setdefault(parent, []).append(child)
            affected = {identifier}
            pending = [identifier]
            while pending:
                for child in children.get(pending.pop(), ()):
                    if child not in affected:
                        affected.add(child)
                        pending.append(child)
            connection.executemany("UPDATE memories SET retracted = 1 WHERE id = ?", ((item,) for item in affected))
        return tuple(sorted(affected))

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    content TEXT NOT NULL,
                    status TEXT NOT NULL,
                    provenance TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    scope_json TEXT NOT NULL DEFAULT '{}',
                    parent_ids TEXT NOT NULL DEFAULT '',
                    retracted INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(memories)").fetchall()}
            for name, definition in (
                ("scope_json", "TEXT NOT NULL DEFAULT '{}" + "'"),
                ("parent_ids", "TEXT NOT NULL DEFAULT ''"),
                ("retracted", "INTEGER NOT NULL DEFAULT 0"),
            ):
                if name not in columns:
                    connection.execute(f"ALTER TABLE memories ADD COLUMN {name} {definition}")

    def _connection(self):
        return connect(self.path, rows=False)


def _terms(text: str) -> tuple[str, ...]:
    """Return conservative lexical units for Latin identifiers and CJK requests.

    Whole CJK runs are intentionally retained rather than guessed into words.  This
    supports an exact bilingual query without introducing a tokenizer dependency or
    silently translating scientific identifiers.
    """

    return tuple(re.findall(r"[A-Za-z0-9_]{2,}|[\u4e00-\u9fff]{2,}", text.lower()))


def _lexical_score(query_terms: set[str], text: str) -> float:
    if not query_terms:
        return 0.0
    content_terms = set(_terms(text))
    return len(query_terms & content_terms) / len(query_terms)


def _row_to_entry(row: tuple[str, str, str, str, str, str, str, str, str, int]) -> MemoryEntry:
    return MemoryEntry(
        identifier=row[0],
        kind=MemoryKind(row[1]),
        content=row[2],
        status=EpistemicStatus(row[3]),
        provenance=row[4],
        session_id=row[5],
        created_at=row[6],
        scope=_scope_from_json(row[7]),
        parent_ids=tuple(item for item in row[8].split(",") if item),
        retracted=bool(row[9]),
    )


def _scope_json(scope: MemoryScope) -> str:
    return json.dumps(
        {
            "case_id": scope.case_id,
            "task_type": scope.task_type,
            "dataset_partitions": scope.dataset_partitions,
            "biological_context": scope.biological_context,
            "allowed_origins": scope.allowed_origins,
            "created_after": scope.created_after,
            "created_before": scope.created_before,
            "allow_cross_case": scope.allow_cross_case,
        },
        ensure_ascii=True,
        sort_keys=True,
    )


def _scope_from_json(value: str) -> MemoryScope:
    try:
        data = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        data = {}
    if not isinstance(data, Mapping):
        data = {}
    return MemoryScope(
        case_id=data.get("case_id") if isinstance(data.get("case_id"), str) else None,
        task_type=data.get("task_type") if isinstance(data.get("task_type"), str) else None,
        dataset_partitions=tuple(item for item in data.get("dataset_partitions", ()) if isinstance(item, str)),
        biological_context=data.get("biological_context") if isinstance(data.get("biological_context"), str) else None,
        allowed_origins=tuple(item for item in data.get("allowed_origins", ()) if isinstance(item, str)),
        created_after=data.get("created_after") if isinstance(data.get("created_after"), str) else None,
        created_before=data.get("created_before") if isinstance(data.get("created_before"), str) else None,
        allow_cross_case=bool(data.get("allow_cross_case", False)),
    )


def _scope_matches(
    entry: MemoryScope,
    requested: MemoryScope | None,
    provenance: str,
    created_at: str,
) -> bool:
    if requested is None:
        return True
    if requested.allowed_origins and provenance not in requested.allowed_origins:
        return False
    if requested.case_id:
        if entry.case_id is None:
            return requested.allow_cross_case
        if entry.case_id != requested.case_id and not (requested.allow_cross_case and entry.allow_cross_case):
            return False
    if requested.task_type and entry.task_type and entry.task_type != requested.task_type:
        return False
    if requested.biological_context and entry.biological_context and entry.biological_context != requested.biological_context:
        return False
    if requested.dataset_partitions and entry.dataset_partitions and not set(requested.dataset_partitions).intersection(entry.dataset_partitions):
        return False
    if requested.created_after and created_at < requested.created_after:
        return False
    if requested.created_before and created_at > requested.created_before:
        return False
    return True


@dataclass(frozen=True)
class ReflectionRecord:
    """A post-observation reflection pairing an outcome class with a bounded next step."""

    case_id: str
    action_identifier: str
    result_id: str
    outcome_class: str
    next_step: str
    limitations: tuple[str, ...]

    def render(self) -> str:
        return (
            f"Post-observation reflection for action '{self.action_identifier}': "
            f"outcome_class={self.outcome_class}; next_step={self.next_step}; "
            f"limitations={'; '.join(self.limitations) or 'none'}."
        )


def reflect_on_result(case_id: str, result_id: str, result: MeasurementResult) -> ReflectionRecord:
    """Classify execution state without promoting a result to a mechanism verdict."""

    if not result.quality_passed:
        outcome_class = "record_quality_failed"
        next_step = "Do not use this record to update the mechanism contrast; obtain a qualified replacement result."
    elif result.evidence_kind.value != "real_measurement":
        outcome_class = "non_measurement_record_received"
        next_step = "Retain source limitations; use only the record's declared interpretation fields."
    elif not result.interpretation_fields:
        outcome_class = "measurement_without_interpretation_premise"
        next_step = "Keep the result as evidence, but do not unlock a prerequisite or mechanism update."
    else:
        outcome_class = "qualified_result_received"
        next_step = "Replan using only the explicit interpretation fields and remaining registered actions."
    return ReflectionRecord(
        case_id=case_id,
        action_identifier=result.action_identifier,
        result_id=result_id,
        outcome_class=outcome_class,
        next_step=next_step,
        limitations=result.limitations,
    )


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

    def round(self, record: RoundRecord, *, stage: str, case_id: str | None = None,
              plan_version: int | None = None) -> bool:
        """Persist a derived round view; never mutate case facts or evidence state."""
        if stage not in ("plan", "result"):
            raise ValueError("Round stage must be plan or result.")
        if case_id is not None and (not case_id.strip() or type(plan_version) is not int or plan_version < 1):
            raise ValueError("round_case_plan_binding_required")
        path = self.root / "rounds" / f"{record.session_id}.{stage}.json"
        if stage == "result":
            if not record.execution.result_id:
                self.event("round_record_rejected", {"session_id": record.session_id,
                           "reason": "result_record_identity_missing"}, session_id=record.session_id)
                return False
            identity = hashlib.sha256(record.execution.result_id.encode("utf-8")).hexdigest()
            path = self.root / "rounds" / f"{record.session_id}.result.{identity}.json"
        try:
            digest = write_round(path, record, immutable=True)
        except ValueError as error:
            self.event("round_record_rejected", {"session_id": record.session_id, "reason": str(error)},
                       session_id=record.session_id)
            return False
        payload = {"path": str(path), "sha256": digest}
        if case_id is not None:
            payload.update(case_id=case_id, plan_version=plan_version)
        if stage == "plan":
            kind = "round_record_written"
            payload["layers"] = 4
        else:
            kind = "round_result_recorded"
            payload.update(result_id=record.execution.result_id,
                           contradiction_flag=record.execution.contradiction_flag)
        self.event(kind, payload, session_id=record.session_id)
        return True

    def review_case(self, case_id: str, store: CaseStore) -> Mapping[str, Any]:
        """Rebuild only authenticated historical views; never rerun evidence rules or models.

        Missing derived result views remain an explicit blocker. CaseStore facts
        can still be received after restart without pretending a scientific review exists.
        Each unique view is a byte snapshot within this call; later calls reauthenticate.
        """
        records = {}
        ownership = {row["result_id"]: row for row in store.result_identities(case_id)}
        seen_results = set()
        bindings = {}
        digests = {}  # Invocation-local authenticated bytes; never trusted across reviews.
        resolved_root = self.root.resolve()
        with self.events_path.open(encoding="utf-8") as stream:
            for line in stream:
                event = json.loads(line)
                payload = event.get("payload", {})
                if event.get("kind") not in ("round_record_written", "round_result_recorded") or payload.get("case_id") != case_id:
                    continue
                stage = "result" if event["kind"] == "round_result_recorded" else "plan"
                session = event["session_id"]
                version = payload.get("plan_version")
                if type(version) is not int or version < 1:
                    raise ValueError("round_audit_plan_binding_missing")
                if session in bindings and bindings[session] != version:
                    raise ValueError("round_audit_plan_binding_conflict")
                bindings[session] = version
                result_id = payload.get("result_id") if stage == "result" else None
                if stage == "result" and (not isinstance(result_id, str) or not result_id):
                    raise ValueError("round_audit_result_identity_missing")
                suffix = "plan" if stage == "plan" else "result." + hashlib.sha256(result_id.encode("utf-8")).hexdigest()
                expected_name = f"{session}.{suffix}.json"
                logged = Path(payload["path"])
                if logged.name != expected_name or logged.parent.name != "rounds":
                    raise ValueError("round_audit_path_mismatch")
                path = self.root / "rounds" / expected_name
                if not path.resolve().is_relative_to(resolved_root):
                    raise ValueError("round_audit_path_outside_root")
                key = (session, stage, result_id)
                if key in records:
                    if digests[key] != payload["sha256"]:
                        raise ValueError("round_audit_hash_mismatch")
                    record = records[key]
                else:
                    raw = path.read_bytes()
                    digest = hashlib.sha256(raw).hexdigest()
                    if digest != payload["sha256"]:
                        raise ValueError("round_audit_hash_mismatch")
                    record = RoundRecord.from_payload(json_loads(raw.decode("utf-8")))
                    digests[key] = digest
                if record.session_id != session or record.execution.result_id != result_id:
                    raise ValueError("round_audit_identity_mismatch")
                if stage == "result":
                    fact = ownership.get(result_id)
                    if fact is None or fact["plan_version"] != version:
                        raise ValueError("round_audit_case_plan_mismatch")
                    seen_results.add(result_id)
                records[key] = record
        if not records:
            raise ValueError("case_audit_binding_missing")
        if seen_results != set(ownership):
            raise ValueError("case_audit_incomplete_results")
        sessions_with_results = {key[0] for key in records if key[1] == "result"}
        if any((session, "plan", None) not in records for session in sessions_with_results):
            raise ValueError("case_audit_original_plan_missing")
        views = tuple(record for key, record in records.items()
                      if key[1] == "result" or key[0] not in sessions_with_results)
        return {**dict(review_run(views)), "case_id": case_id,
                "basis": "authenticated saved round views; original interpretation retained",
                "pending_actions": store.pending_actions(case_id), "budget": store.budget_status(case_id)}

    def explain_failure(self, session_id: str) -> Mapping[str, Any] | None:
        """Return the first recorded tool failure for a session without inferring biology."""

        if not self.events_path.is_file():
            return None
        with self.events_path.open(encoding="utf-8") as stream:
            for line in stream:
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
