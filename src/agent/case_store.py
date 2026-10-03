"""Authoritative case plans, execution facts, results and declared budget use."""
from __future__ import annotations

import sqlite3
import hashlib
import json
import uuid
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Sequence

from maestro.models import DecisionStatus, EvidenceAction, EvidenceActionKind, EvidenceKind
from maestro.composition import finite_number, validate_action_menu


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
    plan_version: int | None = None


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
        if budget is not None and (not finite_number(budget) or budget < 0):
            raise ValueError("Budget must be finite and nonnegative.")
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

    def pending_actions(self, case_id: str) -> tuple[dict[str, Any], ...]:
        """Read committed receipt fields, not reconstructed executable action definitions."""
        with self._connection() as connection:
            self._case_row(connection, case_id)
            rows = connection.execute(
                """SELECT plan_version,action_identifier,status,cost,context_identifier,time_hours,
                expected_conditions_json,action_kind,attempt_id,execution_source FROM planned_actions
                WHERE case_id=? AND status IN ('planned','started') ORDER BY plan_version,action_identifier""",
                (case_id,)).fetchall()
        receipts = []
        for row in rows:
            receipt = dict(row)
            receipt["case_id"] = case_id
            receipt["expected_conditions"] = json.loads(receipt.pop("expected_conditions_json"))
            receipts.append(receipt)
        return tuple(receipts)

    def result_identities(self, case_id: str) -> tuple[dict[str, Any], ...]:
        """Read persisted result ownership for auditing; do not interpret the measurements."""
        with self._connection() as connection:
            self._case_row(connection, case_id)
            rows = connection.execute(
                "SELECT result_id,plan_version,action_identifier FROM results WHERE case_id=? ORDER BY result_id",
                (case_id,)).fetchall()
        return tuple(dict(row) for row in rows)

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
        payloads without a registered runtime schema remain opt-in research records.
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

    def result_plan_version(self, case_id: str, result_id: str) -> int | None:
        """Resolve an accepted result to its immutable plan, including on reimport."""
        with self._connection() as connection:
            row = connection.execute("SELECT plan_version FROM results WHERE case_id=? AND result_id=?",
                                     (case_id, result_id)).fetchone()
        return row["plan_version"] if row is not None else None

    def measurement(self, case_id: str, result_id: str) -> MeasurementResult:
        """Read the accepted fact for an idempotent projection; never infer missing fields."""
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM results WHERE case_id=? AND result_id=?",
                                     (case_id, result_id)).fetchone()
        if row is None:
            raise ValueError("Unknown accepted case result.")
        return MeasurementResult(
            action_identifier=row["action_identifier"], statement=row["statement"], source_id=row["source_id"],
            context_identifier=row["context_identifier"], time_hours=row["time_hours"],
            independent_units=row["independent_units"], quality_passed=bool(row["quality_passed"]),
            conditions=json.loads(row["conditions_json"]), metrics=json.loads(row["metrics_json"]),
            record_count=row["record_count"], biological_replicates=row["biological_replicates"],
            evidence_kind=EvidenceKind(row["evidence_kind"]),
            interpretation_fields=tuple(json.loads(row["interpretation_fields_json"])),
            limitations=tuple(json.loads(row["limitations"])), result_id=row["result_id"],
            plan_version=row["plan_version"],
        )

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

    def prediction_scores(self, case_id: str | None = None) -> tuple[dict[str, Any], ...]:
        """Read derived scores in commit order, optionally for one isolated case."""
        with self._connection() as connection:
            rows = connection.execute(
                """SELECT s.*,r.plan_version,r.action_identifier FROM prediction_scores s
                JOIN results r ON r.result_id=s.result_id """
                + ("WHERE s.case_id=? " if case_id is not None else "") + "ORDER BY s.rowid",
                (case_id,) if case_id is not None else (),
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
        validate_action_menu(actions, 0.0)
        with self._connection() as connection:
            case = self._case_row(connection, case_id)
            selected = tuple(actions)
            if case["state"] == CaseState.AWAITING_RESULT.value:
                existing = tuple(
                    row["action_identifier"]
                    for row in connection.execute(
                        """SELECT action_identifier FROM planned_actions
                        WHERE case_id = ? AND plan_version = ? AND status IN ('planned','started')
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
                        , expected_conditions_json, action_kind
                    ) VALUES (?, ?, ?, ?, ?, ?, 'planned', ?, ?)""",
                    (
                        case_id,
                        next_version,
                        action.identifier,
                        action.cost,
                        context_identifier,
                        action.time_hours,
                        json.dumps(dict(action.expected_conditions), ensure_ascii=True, sort_keys=True),
                        action.kind.value,
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

    def cancel_unexecuted_action(self, case_id: str, plan_version: int, action_id: str, *, reason: str) -> CaseSnapshot:
        """Close an explicitly unexecuted arm; failed attempts must import a QC-failed receipt."""
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("cancellation_reason_required")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            case = self._case_row(connection, case_id)
            action = connection.execute(
                "SELECT status, closure_reason FROM planned_actions WHERE case_id=? AND plan_version=? AND action_identifier=?",
                (case_id, plan_version, action_id)).fetchone()
            if action is not None and action["status"] == "cancelled" and action["closure_reason"] == reason:
                return self._snapshot(case)
            if (case["plan_version"] != plan_version or case["state"] != CaseState.AWAITING_RESULT.value
                    or action is None or action["status"] != "planned"):
                raise ValueError("only_an_active_unexecuted_action_can_be_cancelled")
            connection.execute(
                "UPDATE planned_actions SET status='cancelled',closure_reason=? WHERE case_id=? AND plan_version=? AND action_identifier=?",
                (reason, case_id, plan_version, action_id))
            pending = connection.execute(
                "SELECT 1 FROM planned_actions WHERE case_id=? AND plan_version=? AND status IN ('planned','started') LIMIT 1",
                (case_id, plan_version)).fetchone()
            failed = connection.execute(
                "SELECT 1 FROM results WHERE case_id=? AND plan_version=? AND quality_passed=0 LIMIT 1",
                (case_id, plan_version)).fetchone()
            state = CaseState.AWAITING_RESULT if pending else CaseState.RESULT_QC_FAILED if failed else CaseState.NEXT_ROUND
            connection.execute("UPDATE cases SET state=?,updated_at=? WHERE case_id=?", (state.value, _now(), case_id))
            return self._snapshot(self._case_row(connection, case_id))

    def start_action(self, case_id: str, plan_version: int, action_id: str, *, attempt_id: str, source: str) -> CaseSnapshot:
        """Record an externally reported attempt; the source is a receipt, not model evidence."""
        if any(not isinstance(value, str) or not value.strip() for value in (attempt_id, source)):
            raise ValueError("execution_attempt_and_source_required")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            case = self._case_row(connection, case_id)
            arm = connection.execute(
                "SELECT status,attempt_id,execution_source FROM planned_actions WHERE case_id=? AND plan_version=? AND action_identifier=?",
                (case_id, plan_version, action_id)).fetchone()
            if arm is not None and arm["status"] == "started" and (arm["attempt_id"], arm["execution_source"]) == (attempt_id, source):
                return self._snapshot(case)
            if (case["plan_version"] != plan_version or case["state"] != CaseState.AWAITING_RESULT.value
                    or arm is None or arm["status"] != "planned"):
                raise ValueError("only_an_active_planned_action_can_start")
            if connection.execute("SELECT 1 FROM planned_actions WHERE attempt_id=?", (attempt_id,)).fetchone():
                raise ValueError("duplicate_execution_attempt")
            connection.execute(
                "UPDATE planned_actions SET status='started',attempt_id=?,execution_source=? WHERE case_id=? AND plan_version=? AND action_identifier=?",
                (attempt_id, source, case_id, plan_version, action_id))
            return self._snapshot(case)

    def action_states(self, case_id: str, plan_version: int) -> tuple[dict[str, Any], ...]:
        """Read authoritative arm status; cost is declared budget use, not a monetary invoice."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT action_identifier,status,cost,closure_reason,attempt_id,execution_source,action_kind FROM planned_actions WHERE case_id=? AND plan_version=? ORDER BY action_identifier",
                (case_id, plan_version)).fetchall()
        return tuple(dict(row) for row in rows)

    def budget_status(self, case_id: str) -> dict[str, Any]:
        """Separate pending commitments from recorded use; neither is a monetary invoice."""
        with self._connection() as connection:
            case = self._case_row(connection, case_id)
            reserved = connection.execute(
                "SELECT COALESCE(SUM(cost),0) FROM planned_actions WHERE case_id=? AND status IN ('planned','started')",
                (case_id,)).fetchone()[0]
        return {"budget": case["budget"], "recorded_use": case["spent"], "reserved": reserved,
                "uncommitted": None if case["budget"] is None else case["budget"] - case["spent"] - reserved,
                "basis": "declared action budget units; failed results counted; monetary charges unknown"}

    def import_measurement(self, case_id: str, result: MeasurementResult) -> ResultImport:
        """Record one result for the current plan after condition and replicate validation."""
        if result.evidence_kind not in (EvidenceKind.REAL_MEASUREMENT, EvidenceKind.DERIVED_ANALYSIS, EvidenceKind.RETRIEVED_SOURCE):
            raise ValueError("only_real_measurements_enter_execution_results")
        if result.plan_version is not None and (type(result.plan_version) is not int or result.plan_version < 1):
            raise ValueError("invalid_result_plan_version")
        if result.time_hours is not None and (not finite_number(result.time_hours) or result.time_hours < 0):
            raise ValueError("invalid_result_time")
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
            connection.execute("BEGIN IMMEDIATE")
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
            if result.plan_version is not None and result.plan_version != case["plan_version"]:
                raise ValueError("result_plan_version_mismatch")
            if result.plan_version is None:
                versions = connection.execute(
                    "SELECT COUNT(*) FROM planned_actions WHERE case_id=? AND action_identifier=?",
                    (case_id, result.action_identifier),
                ).fetchone()[0]
                if versions > 1:
                    raise ValueError("ambiguous_result_plan_version")
            plan = connection.execute(
                """SELECT * FROM planned_actions WHERE case_id = ? AND plan_version = ?
                AND action_identifier = ? AND status IN ('planned','started')""",
                (case_id, case["plan_version"], result.action_identifier),
            ).fetchone()
            if plan is None:
                raise ValueError("Result action is not part of the current planned case version.")
            if (result.evidence_kind is not EvidenceKind.REAL_MEASUREMENT
                    and plan["action_kind"] != EvidenceActionKind.EVIDENCE_REVIEW.value):
                raise ValueError("nonmeasurement_record_requires_registered_evidence_review")
            self._validate_conditions(plan, result)
            budget = case["budget"]
            spent = case["spent"] + plan["cost"]
            if budget is not None and spent > budget:
                raise ValueError("Importing this result would exceed the case budget.")
            pending = connection.execute(
                """SELECT COUNT(*) FROM planned_actions WHERE case_id = ? AND plan_version = ?
                AND status IN ('planned','started') AND action_identifier != ?""",
                (case_id, case["plan_version"], result.action_identifier),
            ).fetchone()[0]
            previous_failure = connection.execute(
                "SELECT 1 FROM results WHERE case_id = ? AND plan_version = ? AND quality_passed = 0 LIMIT 1",
                (case_id, case["plan_version"]),
            ).fetchone() is not None
            next_state = (
                CaseState.AWAITING_RESULT
                if pending
                else CaseState.RESULT_QC_FAILED
                if previous_failure or not result.quality_passed
                else CaseState.NEXT_ROUND
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
                """UPDATE planned_actions SET status = ?
                WHERE case_id = ? AND plan_version = ? AND action_identifier = ?""",
                ("result_recorded" if result.quality_passed else "qc_failed", case_id, case["plan_version"], result.action_identifier),
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
            if "closure_reason" not in plan_columns:
                connection.execute("ALTER TABLE planned_actions ADD COLUMN closure_reason TEXT")
            for name in ("attempt_id", "execution_source", "action_kind"):
                if name not in plan_columns:
                    connection.execute(f"ALTER TABLE planned_actions ADD COLUMN {name} TEXT")
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
            and (result.plan_version is None or result.plan_version == row["plan_version"])
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
