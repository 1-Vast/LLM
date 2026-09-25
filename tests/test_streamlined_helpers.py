"""Shared helpers that replaced duplicated premise checks and connection handling.

File summary
- Path: tests/test_streamlined_helpers.py
- Purpose: pin the helpers that now carry logic previously repeated across modules:
  premise measurement checks on the model types, and the SQLite connection helper.
- Core points: assertions here are contract tests, not biological results; each test pins
  one boundary that must not silently move.
- Interfaces: pytest tests only
- Depends on: agent.storage, agent.cases, maestro.models
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from agent.cases import CaseStore
from agent.storage import connect
from maestro.models import EvidenceAction, FunctionalInterventionProfile, MeasurementStatus


def test_unmeasured_names_every_field_without_a_measurement_in_order():
    profile = FunctionalInterventionProfile(
        mode="drug",
        functional_states={"target_activity": MeasurementStatus.MEASURED},
        protein_abundance=MeasurementStatus.ESTIMATED,
        measured_fields={"engagement:target": MeasurementStatus.MEASURED, "attribution:x": MeasurementStatus.UNKNOWN},
    )
    names = ("functional:target_activity", "protein_abundance", "engagement:target", "attribution:x", "unlisted")
    assert profile.unmeasured(names) == ("protein_abundance", "attribution:x", "unlisted")
    assert profile.is_measured("functional:target_activity")
    assert not profile.is_measured("protein_abundance")  # an estimate is not a measurement


def test_required_premises_are_prerequisites_then_the_interpretation_gate():
    gated = EvidenceAction("a", "A", 1.0, ("h",), prerequisites=("p1", "p2"), interpretation_gate="gate")
    assert gated.required_premises == ("p1", "p2", "gate")
    assert EvidenceAction("b", "B", 1.0, ("h",)).required_premises == ()


def test_a_connection_commits_on_success_rolls_back_on_error_and_always_closes(tmp_path: Path):
    path = tmp_path / "store.sqlite"
    with connect(path) as connection:
        connection.execute("CREATE TABLE t (value TEXT)")
        connection.execute("INSERT INTO t VALUES ('kept')")
    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")  # closed, not merely committed

    with pytest.raises(RuntimeError):
        with connect(path) as connection:
            connection.execute("INSERT INTO t VALUES ('discarded')")
            raise RuntimeError("abort")
    with connect(path) as connection:
        rows = [row["value"] for row in connection.execute("SELECT value FROM t")]
    assert rows == ["kept"]
    with connect(path, rows=False) as connection:
        assert connection.execute("SELECT value FROM t").fetchone() == ("kept",)


def test_a_store_leaves_no_connection_open_after_an_operation(tmp_path: Path, monkeypatch):
    opened: list[sqlite3.Connection] = []
    real_connect = sqlite3.connect

    def tracking_connect(*args, **kwargs):
        connection = real_connect(*args, **kwargs)
        opened.append(connection)
        return connection

    monkeypatch.setattr(sqlite3, "connect", tracking_connect)
    store = CaseStore(tmp_path / "cases.sqlite")
    store.open_case("case", budget=2.0)
    assert opened
    for connection in opened:
        with pytest.raises(sqlite3.ProgrammingError):
            connection.execute("SELECT 1")
