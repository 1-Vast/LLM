"""Persistent case state for resumable, evidence-bounded MAESTRO work.

File summary
- Path: src/agent/cases.py
- Purpose: Version case plans and gate real results by idempotency and budget.
- Core points:
  - `CaseStore` versions plans and enforces result idempotency and budget limits.
  - `MeasurementResult` is a real measurement result gated by condition and replicate checks.
- Interfaces: `CaseStore`, `open_case`, `record_plan`, `record_decision`, `import_measurement`, `snapshot`, `CaseSnapshot`, `MeasurementResult`, `ResultImport`, `CaseState`
- Depends on: maestro.models, agent.storage
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Mapping, Sequence

from maestro.models import DecisionStatus, EvidenceAction, EvidenceKind
from .storage import connect


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
