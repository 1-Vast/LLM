"""Research-only categorical feedback with durable, exact execution identity.

This ledger owns prediction/result pairing and scores, not biological facts,
budgets, or hypothesis updates. It does not replace CaseStore. References to
state and execution evidence must be authenticated by the caller.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

from maestro.case_memory import RealMeasurement
from maestro.case_update import (
    OutcomeQualification, qualify_result,
    score_reading_distribution as categorical_score,
    validate_reading_distribution as validate_distribution,
)


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)



@dataclass(frozen=True)
class FeedbackLink:
    case_id: str
    case_version: int
    plan_id: str
    action_id: str
    attempt_id: str
    prediction_id: str

    def __post_init__(self):
        if isinstance(self.case_version, bool) or not isinstance(self.case_version, int) or self.case_version < 1:
            raise ValueError("positive case_version required")
        if any(not isinstance(v, str) or not v.strip() for k, v in asdict(self).items() if k != "case_version"):
            raise ValueError("complete case/plan/action/attempt/prediction identity required")

    @property
    def key(self) -> str:
        return _json(asdict(self))

    @property
    def execution_key(self) -> str:
        return _json({k: v for k, v in asdict(self).items() if k != "prediction_id"})


class FeedbackStore:
    """Append-only SQLite receipts; retries are equal-content idempotent.

    A single result per exact execution link is accepted. Conflicting retries
    and replacement results require a separate explicit correction workflow,
    which this prototype intentionally does not implement.
    """
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS astra_predictions (
                    link TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS astra_attempts (
                    link TEXT PRIMARY KEY REFERENCES astra_predictions(link),
                    execution_key TEXT NOT NULL UNIQUE,
                    payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS astra_feedback (
                    result_id TEXT PRIMARY KEY,
                    link TEXT NOT NULL UNIQUE REFERENCES astra_attempts(link),
                    payload TEXT NOT NULL);
            """)

    @contextmanager
    def _connection(self):
        db = sqlite3.connect(self.path)
        db.execute("PRAGMA foreign_keys = ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _insert(db, table: str, link: FeedbackLink, payload: dict) -> bool:
        # Table names are internal constants; all external values use bindings.
        existing = db.execute(f"SELECT payload FROM {table} WHERE link = ?", (link.key,)).fetchone()
        encoded = _json(payload)
        if existing:
            if existing[0] != encoded:
                raise ValueError("conflicting immutable record")
            return False
        if table == "astra_attempts":
            if db.execute("SELECT 1 FROM astra_attempts WHERE execution_key=?", (link.execution_key,)).fetchone():
                raise ValueError("execution already bound to a different prediction")
            db.execute("INSERT INTO astra_attempts(link,execution_key,payload) VALUES (?,?,?)",
                       (link.key, link.execution_key, encoded))
        else:
            db.execute(f"INSERT INTO {table}(link,payload) VALUES (?,?)", (link.key, encoded))
        return True

    def register_prediction(self, link: FeedbackLink, probabilities: Mapping[str, float], *,
                            model_version: str, state_id: str, target_id: str,
                            outcome_mode: str = "valid_measurement") -> bool:
        if outcome_mode != "valid_measurement":
            raise ValueError("only conditional valid-measurement forecasts supported")
        if any(not isinstance(v, str) or not v.strip() for v in (model_version, state_id, target_id)):
            raise ValueError("model, immutable state reference and target required")
        payload = dict(link=asdict(link), probabilities=validate_distribution(probabilities),
                       model_version=model_version, state_id=state_id, target_id=target_id,
                       outcome_mode=outcome_mode)
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            return self._insert(db, "astra_predictions", link, payload)

    def register_attempt(self, link: FeedbackLink, *, execution_source: str) -> bool:
        """Record a caller-confirmed executed attempt, never merely a plan."""
        if not isinstance(execution_source, str) or not execution_source.strip():
            raise ValueError("execution evidence reference required")
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            if not db.execute("SELECT 1 FROM astra_predictions WHERE link=?", (link.key,)).fetchone():
                raise ValueError("no exact prediction identity")
            return self._insert(db, "astra_attempts", link, dict(execution_source=execution_source))

    def accept_result(self, link: FeedbackLink, result_id: str, measurement: RealMeasurement, *,
                      qc_passed: bool, detected: bool | None, conditions_matched: bool,
                      eliminated: tuple[str, ...] = ()) -> dict:
        if not isinstance(result_id, str) or not result_id.strip() or measurement.action_id != link.action_id:
            raise ValueError("result identity/action mismatch")
        if not measurement.source or measurement.label_kind != "measured_outcome":
            raise ValueError("sourced real measurement required")
        if (type(qc_passed) is not bool or type(conditions_matched) is not bool
                or (detected is not None and type(detected) is not bool)):
            raise ValueError("explicit QC, condition and detection flags required")
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            forecast = db.execute("SELECT payload FROM astra_predictions WHERE link=?", (link.key,)).fetchone()
            if not forecast or not db.execute("SELECT 1 FROM astra_attempts WHERE link=?", (link.key,)).fetchone():
                raise ValueError("no exact executed prediction/attempt link")
            probabilities = json.loads(forecast[0])["probabilities"]
            valid_units = type(measurement.independent_units) is int and measurement.independent_units >= 1
            qualified = qualify_result(measurement, qc_passed=qc_passed, detected=detected,
                                       eliminated=eliminated if conditions_matched and valid_units else ())
            usable = bool(qc_passed and conditions_matched and valid_units and measurement.status.biological)
            score = categorical_score(probabilities, measurement.outcome_label) if usable and measurement.outcome_label is not None else None
            payload = dict(link=asdict(link), result_id=result_id, measurement=asdict(measurement),
                           qc_passed=qc_passed, conditions_matched=conditions_matched,
                           detected=detected, qualification=qualified.value,
                           mechanism_discriminating=qualified is OutcomeQualification.QUALIFIED,
                           eliminated=list(eliminated) if qualified is OutcomeQualification.QUALIFIED else [],
                           score=score, score_status="scored" if score else "not_scorable")
            encoded = _json(payload)
            prior = db.execute("SELECT payload FROM astra_feedback WHERE result_id=? OR link=?",
                               (result_id, link.key)).fetchone()
            if prior:
                if prior[0] != encoded:
                    raise ValueError("conflicting result identity or content")
                return dict(json.loads(prior[0]), duplicate=True)
            db.execute("INSERT INTO astra_feedback(result_id,link,payload) VALUES (?,?,?)",
                       (result_id, link.key, encoded))
            return dict(payload, duplicate=False)

    def get_feedback(self, result_id: str) -> dict | None:
        with self._connection() as db:
            row = db.execute("SELECT payload FROM astra_feedback WHERE result_id=?", (result_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def scores(self, case_id: str) -> tuple[dict, ...]:
        with self._connection() as db:
            rows = db.execute("SELECT payload FROM astra_feedback ORDER BY result_id").fetchall()
        return tuple(record for row in rows if (record := json.loads(row[0]))["link"]["case_id"] == case_id)
