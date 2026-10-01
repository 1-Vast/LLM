"""Persistent case state, scoped memories, result reflection, and secret-safe run records."""
from __future__ import annotations

import sqlite3
import hashlib
import json
import re
import uuid
from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Sequence

from maestro.models import DecisionStatus, EvidenceAction, EvidenceKind


@contextmanager
def connect(path: Path, *, rows: bool = True) -> Iterator[sqlite3.Connection]:
    """Yield a connection inside one transaction and close it afterwards."""

    connection = sqlite3.connect(path)
    if rows:
        connection.row_factory = sqlite3.Row
    try:
        with connection:
            yield connection
    finally:
        connection.close()


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
            affected = {identifier}
            changed = True
            while changed:
                changed = False
                for child, parents in known.items():
                    if child not in affected and any(parent in affected for parent in parents):
                        affected.add(child)
                        changed = True
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


def _refusal(code: str, message: str) -> ValueError:
    """A refused import that carries a machine-readable reason beside its message.

    The ledger has always raised ``ValueError`` and several callers match on the message text,
    so the class and the wording stay exactly as they were; the code rides along as an
    attribute, which is what the replay runner counts when it reports refusals by name instead
    of as an unclassified ledger error.
    """

    error = ValueError(message)
    error.code = code  # type: ignore[attr-defined]
    return error


class CaseState(str, Enum):
    INTAKE = "intake"
    NEEDS_REPAIR = "needs_repair"
    AWAITING_RESULT = "awaiting_result"
    RESULT_QC_FAILED = "result_qc_failed"
    NEXT_ROUND = "next_round"
    DEFERRED = "deferred"
    COMPLETED = "completed"


@dataclass(frozen=True)
class CaseSnapshot:
    """A point-in-time view of a case's state, plan version, and budget."""

    case_id: str
    state: CaseState
    plan_version: int
    budget: float | None
    spent: float
    remaining_budget: float | None
    stop_reason: str | None


@dataclass(frozen=True)
class MeasurementResult:
    """A real result linked to a planned action and its experimental conditions.

    ``independent_units`` counts independent experimental units, not rows or
    cells.  ``None`` means the count is unknown; it is never silently replaced
    by a record count or a default, because duplicated rows would otherwise
    masquerade as independent biological support (audit F08).
    """

    action_identifier: str
    statement: str
    source_id: str
    context_identifier: str | None
    time_hours: float | None
    independent_units: int | None
    quality_passed: bool
    conditions: Mapping[str, str] = field(default_factory=dict)
    metrics: Mapping[str, str] = field(default_factory=dict)
    record_count: int = 1
    biological_replicates: int | None = None
    evidence_kind: EvidenceKind = EvidenceKind.REAL_MEASUREMENT
    interpretation_fields: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    result_id: str | None = None


@dataclass(frozen=True)
class ResultImport:
    """The outcome of importing one result: its snapshot and whether it was newly created."""

    snapshot: CaseSnapshot
    result_id: str
    created: bool


class CaseStore:
    """SQLite-backed state transitions with plan-version and result idempotency checks."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def open_case(self, case_id: str, *, budget: float | None = None) -> CaseSnapshot:
        if not case_id.strip():
            raise ValueError("case_id is required.")
        if budget is not None and budget < 0:
            raise ValueError("Budget must be nonnegative.")
        with self._connection() as connection:
            connection.execute(
                """INSERT OR IGNORE INTO cases(
                    case_id, state, plan_version, budget, spent, stop_reason, updated_at
                ) VALUES (?, ?, 0, ?, 0, NULL, ?)""",
                (case_id, CaseState.INTAKE.value, budget, _now()),
            )
            row = connection.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)).fetchone()
            if budget is not None and row["budget"] is not None and row["budget"] != budget:
                raise ValueError("An existing case budget cannot be changed implicitly.")
        return self._snapshot(row)

    def snapshot(self, case_id: str) -> CaseSnapshot:
        with self._connection() as connection:
            return self._snapshot(self._case_row(connection, case_id))

    def recorded_action_identifiers(self, case_id: str) -> tuple[str, ...]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT action_identifier FROM results WHERE case_id = ? ORDER BY created_at, action_identifier",
                (case_id,),
            ).fetchall()
        return tuple(row["action_identifier"] for row in rows)

    def record_prediction(self, case_id: str, plan_version: int, action_id: str, request_id: str,
                          payload: Mapping[str, Any], *, attempt_id: str | None = None) -> bool:
        """Opt-in immutable prediction envelope for one already committed action.

        This records no execution or biological evidence. ``attempt_id`` remains
        unknown unless supplied from an external execution receipt. Runtime
        prediction restoration and scoring are not automatically enabled.
        """
        if (type(plan_version) is not int or plan_version < 1
                or any(not isinstance(value, str) or not value.strip() for value in (case_id, action_id, request_id))
                or (attempt_id is not None and (not isinstance(attempt_id, str) or not attempt_id.strip()))):
            raise ValueError("Exact plan/request identity required.")
        if not isinstance(payload, Mapping) or not payload:
            raise ValueError("A nonempty prediction envelope is required.")
        encoded = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), allow_nan=False)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            plan = connection.execute(
                "SELECT status FROM planned_actions WHERE case_id=? AND plan_version=? AND action_identifier=?",
                (case_id, plan_version, action_id),
            ).fetchone()
            if plan is None:
                raise ValueError("Prediction action is not an exact committed plan.")
            existing = connection.execute(
                "SELECT * FROM prediction_records WHERE case_id=? AND plan_version=? AND action_identifier=?",
                (case_id, plan_version, action_id),
            ).fetchone()
            if existing:
                if (existing["request_id"], existing["attempt_id"], existing["payload_json"]) != (request_id, attempt_id, encoded):
                    raise ValueError("Prediction identity or content is immutable.")
                return False
            if plan["status"] != "planned":
                raise ValueError("Prediction must be recorded before the result.")
            case = self._case_row(connection, case_id)
            if case["plan_version"] != plan_version or case["state"] != CaseState.AWAITING_RESULT.value:
                raise ValueError("Prediction plan is not the active awaiting plan.")
            connection.execute(
                """INSERT INTO prediction_records(case_id,plan_version,action_identifier,request_id,
                attempt_id,payload_json) VALUES (?,?,?,?,?,?)""",
                (case_id, plan_version, action_id, request_id, attempt_id, encoded),
            )
        return True

    @staticmethod
    def _prediction_for_result(connection, case_id: str, result_id: str):
        return connection.execute(
            """SELECT p.* FROM results r JOIN prediction_records p
            ON p.case_id=r.case_id AND p.plan_version=r.plan_version
            AND p.action_identifier=r.action_identifier WHERE r.case_id=? AND r.result_id=?""",
            (case_id, result_id),
        ).fetchone()

    def prediction_for_result(self, case_id: str, result_id: str) -> dict[str, Any] | None:
        """Resolve using the accepted result's original plan, never latest action."""
        with self._connection() as connection:
            row = self._prediction_for_result(connection, case_id, result_id)
        if row is None:
            return None
        record = dict(row)
        record["payload"] = json.loads(record.pop("payload_json"))
        return record

    def record_prediction_score(self, case_id: str, result_id: str, request_id: str,
                                score: Mapping[str, Any], *, conditions_matched: bool) -> bool:
        """Persist caller-computed scoring as a derived view of an accepted result.

        The caller authenticates endpoint interpretation and computes the score.
        This method only checks exact pairing, QC, real evidence and known units;
        it does not fit calibration, update hypotheses, or charge a budget.
        """
        if conditions_matched is not True:
            raise ValueError("Explicit matched conditions required for scoring.")
        if not isinstance(score, Mapping) or not score:
            raise ValueError("Nonempty score payload required.")
        encoded = json.dumps(dict(score), sort_keys=True, separators=(",", ":"), allow_nan=False)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            prediction = self._prediction_for_result(connection, case_id, result_id)
            if prediction is None or prediction["request_id"] != request_id:
                raise ValueError("No exact accepted result/prediction pair.")
            result = connection.execute("SELECT * FROM results WHERE result_id=? AND case_id=?",
                                        (result_id, case_id)).fetchone()
            if (not result["quality_passed"] or result["evidence_kind"] != EvidenceKind.REAL_MEASUREMENT.value
                    or result["independent_units"] is None or result["independent_units"] < 1):
                raise ValueError("Result is not a qualified real measurement with known units.")
            existing = connection.execute("SELECT * FROM prediction_scores WHERE result_id=?", (result_id,)).fetchone()
            if existing:
                if (existing["case_id"], existing["request_id"], existing["score_json"]) != (case_id, request_id, encoded):
                    raise ValueError("Prediction score identity or content is immutable.")
                return False
            connection.execute(
                "INSERT INTO prediction_scores(result_id,case_id,request_id,score_json) VALUES (?,?,?,?)",
                (result_id, case_id, request_id, encoded),
            )
        return True

    def prediction_scores(self, case_id: str) -> tuple[dict[str, Any], ...]:
        """Read only this case's derived scores, including original plan identity."""
        with self._connection() as connection:
            rows = connection.execute(
                """SELECT s.*,r.plan_version,r.action_identifier FROM prediction_scores s
                JOIN results r ON r.result_id=s.result_id WHERE s.case_id=? ORDER BY s.rowid""", (case_id,),
            ).fetchall()
        records = []
        for row in rows:
            record = dict(row)
            record["score"] = json.loads(record.pop("score_json"))
            records.append(record)
        return tuple(records)

    def record_plan(
        self,
        case_id: str,
        actions: Sequence[EvidenceAction],
        *,
        ready_to_measure: bool,
        context_identifier: str | None,
        stop_reason: str | None = None,
    ) -> CaseSnapshot:
        """Version an action bundle once; an awaiting identical bundle is resumed instead of duplicated."""

        with self._connection() as connection:
            case = self._case_row(connection, case_id)
            selected = tuple(actions)
            if case["state"] == CaseState.AWAITING_RESULT.value:
                existing = tuple(
                    row["action_identifier"]
                    for row in connection.execute(
                        """SELECT action_identifier FROM planned_actions
                        WHERE case_id = ? AND plan_version = ? AND status = 'planned'
                        ORDER BY action_identifier""",
                        (case_id, case["plan_version"]),
                    ).fetchall()
                )
                if existing:
                    return self._snapshot(case)
            next_version = case["plan_version"] + 1
            state = CaseState.AWAITING_RESULT if ready_to_measure and selected else CaseState.NEEDS_REPAIR
            if (
                selected
                and case["budget"] is not None
                and case["spent"] + sum(action.cost for action in selected) > case["budget"]
            ):
                state = CaseState.DEFERRED
                stop_reason = "Planned action exceeds the remaining case budget."
                selected = ()
            if stop_reason:
                state = CaseState.DEFERRED
            connection.execute(
                """UPDATE cases SET state = ?, plan_version = ?, stop_reason = ?, updated_at = ?
                WHERE case_id = ?""",
                (state.value, next_version, stop_reason, _now(), case_id),
            )
            for action in selected:
                connection.execute(
                    """INSERT INTO planned_actions(
                        case_id, plan_version, action_identifier, cost, context_identifier, time_hours, status
                        , expected_conditions_json
                    ) VALUES (?, ?, ?, ?, ?, ?, 'planned', ?)""",
                    (
                        case_id,
                        next_version,
                        action.identifier,
                        action.cost,
                        context_identifier,
                        action.time_hours,
                        json.dumps(dict(action.expected_conditions), ensure_ascii=True, sort_keys=True),
                    ),
                )
            updated = self._case_row(connection, case_id)
        return self._snapshot(updated)

    def record_decision(self, case_id: str, *, status: str) -> CaseSnapshot:
        """Move a case to the terminal state its development decision implies.

        Leaving a decided case in ``awaiting_result`` is what let the in-memory
        trace and the persisted state disagree.  A decision that ends the loop
        must also end the case's waiting state.
        """

        state = {
            DecisionStatus.DECIDED.value: CaseState.COMPLETED,
            DecisionStatus.DEFERRED.value: CaseState.DEFERRED,
            DecisionStatus.CONTRADICTED.value: CaseState.NEEDS_REPAIR,
        }.get(status, CaseState.NEXT_ROUND)
        with self._connection() as connection:
            connection.execute(
                "UPDATE cases SET state = ?, stop_reason = ?, updated_at = ? WHERE case_id = ?",
                (state.value, f"decision:{status}", _now(), case_id),
            )
            updated = self._case_row(connection, case_id)
        return self._snapshot(updated)

    def import_measurement(self, case_id: str, result: MeasurementResult) -> ResultImport:
        """Record one result for the current plan after condition and replicate validation."""

        if not result.source_id.strip() or not result.statement.strip():
            raise ValueError("Measurement results require a source_id and statement.")
        if not isinstance(result.quality_passed, bool):
            raise ValueError("Measurement quality_passed must be a boolean.")
        if result.independent_units is not None and (
            not isinstance(result.independent_units, int) or isinstance(result.independent_units, bool)
            or result.independent_units < 1
        ):
            raise ValueError("Independent experimental units must be positive integers when known.")
        if not isinstance(result.record_count, int) or isinstance(result.record_count, bool) or result.record_count < 1:
            raise ValueError("At least one source record is required as an integer count.")
        if result.biological_replicates is not None and (
            not isinstance(result.biological_replicates, int) or isinstance(result.biological_replicates, bool)
            or result.biological_replicates < 1
        ):
            raise ValueError("Biological replicate count must be a positive integer when known.")
        result_id = result.result_id or str(uuid.uuid4())
        with self._connection() as connection:
            case = self._case_row(connection, case_id)
            existing = connection.execute(
                "SELECT * FROM results WHERE result_id = ?", (result_id,)
            ).fetchone()
            if existing:
                if not self._same_result(existing, result, case_id):
                    raise ValueError("A result identifier already exists with different content.")
                return ResultImport(self._snapshot(case), result_id, False)
            if case["state"] != CaseState.AWAITING_RESULT.value:
                raise ValueError("Case is not awaiting a planned measurement result.")
            plan = connection.execute(
                """SELECT * FROM planned_actions WHERE case_id = ? AND plan_version = ?
                AND action_identifier = ? AND status = 'planned'""",
                (case_id, case["plan_version"], result.action_identifier),
            ).fetchone()
            if plan is None:
                raise ValueError("Result action is not part of the current planned case version.")
            self._validate_conditions(plan, result)
            budget = case["budget"]
            spent = case["spent"] + plan["cost"]
            if budget is not None and spent > budget:
                raise ValueError("Importing this result would exceed the case budget.")
            pending = connection.execute(
                """SELECT COUNT(*) FROM planned_actions WHERE case_id = ? AND plan_version = ?
                AND status = 'planned' AND action_identifier != ?""",
                (case_id, case["plan_version"], result.action_identifier),
            ).fetchone()[0]
            next_state = (
                CaseState.AWAITING_RESULT
                if pending and result.quality_passed
                else CaseState.NEXT_ROUND
                if result.quality_passed
                else CaseState.RESULT_QC_FAILED
            )
            connection.execute(
                """INSERT INTO results(
                    result_id, case_id, plan_version, action_identifier, statement, source_id,
                    context_identifier, time_hours, independent_units, quality_passed, conditions_json,
                    metrics_json, record_count, biological_replicates, evidence_kind, limitations, created_at
                    , interpretation_fields_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    result_id,
                    case_id,
                    case["plan_version"],
                    result.action_identifier,
                    result.statement,
                    result.source_id,
                    result.context_identifier,
                    result.time_hours,
                    result.independent_units,
                    int(result.quality_passed),
                    json.dumps(dict(result.conditions), ensure_ascii=True, sort_keys=True),
                    json.dumps(dict(result.metrics), ensure_ascii=True, sort_keys=True),
                    result.record_count,
                    result.biological_replicates,
                    result.evidence_kind.value,
                    json.dumps(result.limitations, ensure_ascii=True),
                    _now(),
                    json.dumps(result.interpretation_fields, ensure_ascii=True),
                ),
            )
            connection.execute(
                """UPDATE planned_actions SET status = 'result_recorded'
                WHERE case_id = ? AND plan_version = ? AND action_identifier = ?""",
                (case_id, case["plan_version"], result.action_identifier),
            )
            connection.execute(
                """UPDATE cases SET state = ?, spent = ?, updated_at = ? WHERE case_id = ?""",
                (next_state.value, spent, _now(), case_id),
            )
            updated = self._case_row(connection, case_id)
        return ResultImport(self._snapshot(updated), result_id, True)

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS cases (
                    case_id TEXT PRIMARY KEY, state TEXT NOT NULL, plan_version INTEGER NOT NULL,
                    budget REAL, spent REAL NOT NULL, stop_reason TEXT, updated_at TEXT NOT NULL
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS planned_actions (
                    case_id TEXT NOT NULL, plan_version INTEGER NOT NULL, action_identifier TEXT NOT NULL,
                    cost REAL NOT NULL, context_identifier TEXT, time_hours REAL, status TEXT NOT NULL,
                    expected_conditions_json TEXT NOT NULL DEFAULT '{}',
                    PRIMARY KEY(case_id, plan_version, action_identifier)
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS results (
                    result_id TEXT PRIMARY KEY, case_id TEXT NOT NULL, plan_version INTEGER NOT NULL,
                    action_identifier TEXT NOT NULL, statement TEXT NOT NULL, source_id TEXT NOT NULL,
                    context_identifier TEXT, time_hours REAL, independent_units INTEGER,
                    quality_passed INTEGER NOT NULL, conditions_json TEXT NOT NULL DEFAULT '{}',
                    metrics_json TEXT NOT NULL DEFAULT '{}', record_count INTEGER NOT NULL DEFAULT 1,
                    biological_replicates INTEGER, evidence_kind TEXT NOT NULL DEFAULT 'real_measurement',
                    limitations TEXT NOT NULL, created_at TEXT NOT NULL,
                    interpretation_fields_json TEXT NOT NULL DEFAULT '[]'
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS prediction_records (
                    case_id TEXT NOT NULL, plan_version INTEGER NOT NULL, action_identifier TEXT NOT NULL,
                    request_id TEXT NOT NULL, attempt_id TEXT, payload_json TEXT NOT NULL,
                    PRIMARY KEY(case_id,plan_version,action_identifier),
                    FOREIGN KEY(case_id,plan_version,action_identifier)
                        REFERENCES planned_actions(case_id,plan_version,action_identifier))"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS prediction_scores (
                    result_id TEXT PRIMARY KEY REFERENCES results(result_id), case_id TEXT NOT NULL,
                    request_id TEXT NOT NULL, score_json TEXT NOT NULL)"""
            )
            plan_columns = {row["name"] for row in connection.execute("PRAGMA table_info(planned_actions)")}
            if "expected_conditions_json" not in plan_columns:
                connection.execute(
                    "ALTER TABLE planned_actions ADD COLUMN expected_conditions_json TEXT NOT NULL DEFAULT '{}'"
                )
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(results)")}
            if "conditions_json" not in columns:
                connection.execute(
                    "ALTER TABLE results ADD COLUMN conditions_json TEXT NOT NULL DEFAULT '{}'"
                )
            for name, definition in (
                ("metrics_json", "TEXT NOT NULL DEFAULT '{}" + "'"),
                ("record_count", "INTEGER NOT NULL DEFAULT 1"),
                ("biological_replicates", "INTEGER"),
                ("evidence_kind", "TEXT NOT NULL DEFAULT 'real_measurement'"),
                ("interpretation_fields_json", "TEXT NOT NULL DEFAULT '[]'"),
            ):
                if name not in columns:
                    connection.execute(f"ALTER TABLE results ADD COLUMN {name} {definition}")

    @staticmethod
    def _validate_conditions(plan: sqlite3.Row, result: MeasurementResult) -> None:
        """Refuse a result that does not match the action that was planned, by name.

        The message text is unchanged; each refusal now also carries a machine-readable
        ``code``, so a caller that counts refusals records *which* condition disagreed instead
        of reporting an unclassified ledger error. A mismatch here is usually a record whose
        release spells a condition differently from the plan, which is a real disagreement and
        not something to resolve silently.
        """

        if plan["context_identifier"] and result.context_identifier != plan["context_identifier"]:
            raise _refusal("result_context_mismatch", "Result context does not match the planned context.")
        if plan["time_hours"] is not None and result.time_hours != plan["time_hours"]:
            raise _refusal("result_time_mismatch", "Result time point does not match the planned action.")
        expected = json.loads(plan["expected_conditions_json"])
        for name, value in expected.items():
            if result.conditions.get(name) != value:
                raise _refusal(
                    f"result_condition_mismatch:{name}",
                    f"Result condition '{name}' does not match the planned action.",
                )

    @staticmethod
    def _same_result(row: sqlite3.Row, result: MeasurementResult, case_id: str) -> bool:
        return (
            row["case_id"] == case_id
            and row["action_identifier"] == result.action_identifier
            and row["statement"] == result.statement
            and row["source_id"] == result.source_id
            and row["context_identifier"] == result.context_identifier
            and row["time_hours"] == result.time_hours
            and row["independent_units"] == result.independent_units
            and bool(row["quality_passed"]) is result.quality_passed
            and row["conditions_json"] == json.dumps(dict(result.conditions), ensure_ascii=True, sort_keys=True)
            and row["metrics_json"] == json.dumps(dict(result.metrics), ensure_ascii=True, sort_keys=True)
            and row["record_count"] == result.record_count
            and row["biological_replicates"] == result.biological_replicates
            and row["evidence_kind"] == result.evidence_kind.value
            and row["limitations"] == json.dumps(result.limitations, ensure_ascii=True)
            and row["interpretation_fields_json"] == json.dumps(result.interpretation_fields, ensure_ascii=True)
        )

    def _case_row(self, connection: sqlite3.Connection, case_id: str) -> sqlite3.Row:
        row = connection.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)).fetchone()
        if row is None:
            raise ValueError(f"Unknown case: {case_id}")
        return row

    @staticmethod
    def _snapshot(row: sqlite3.Row) -> CaseSnapshot:
        budget = row["budget"]
        spent = row["spent"]
        return CaseSnapshot(
            case_id=row["case_id"],
            state=CaseState(row["state"]),
            plan_version=row["plan_version"],
            budget=budget,
            spent=spent,
            remaining_budget=None if budget is None else budget - spent,
            stop_reason=row["stop_reason"],
        )

    def _connection(self):
        return connect(self.path)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
