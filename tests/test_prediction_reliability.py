"""Revocable virtual-cell dependence and source-cluster accounting.

File summary
- Path: tests/test_prediction_reliability.py
- Purpose: Test revocable prediction dependence and source-cluster collapse.
- Core points:
  - `PredictionReliabilityLedger` keeps full weight on small samples and revokes on misses.
  - A prediction is only a tie-breaker; revocation never edits the evidence ledger.
- Interfaces: `test_*` functions
- Depends on: maestro
"""
from dataclasses import replace

import pytest

from maestro import (
    PredictionReliabilityLedger,
    SourceCluster,
    SourceClusterIndex,
    build_index,
)
from maestro.reliability import ScoredPrediction


def test_a_small_sample_stays_provisional_and_keeps_full_weight():
    ledger = PredictionReliabilityLedger()
    ledger.record_pair(
        model_version="state-v1",
        readout="viability",
        predicted_value=-0.4,
        realized_value=0.2,
        interval=(-0.5, -0.3),
    )
    summary = ledger.summarize("state-v1", "viability")
    assert summary.provisional
    assert summary.weight == 1.0
    assert not summary.revoked


def test_repeated_interval_misses_down_weight_the_readout():
    ledger = PredictionReliabilityLedger(minimum_records=3)
    for index in range(4):
        ledger.record_pair(
            model_version="state-v1",
            readout="viability",
            predicted_value=-0.4,
            realized_value=0.9,
            interval=(-0.5, -0.3),
        )
    summary = ledger.summarize("state-v1", "viability")
    assert not summary.provisional
    assert summary.miss_rate == 1.0
    assert 0.0 <= summary.weight < 1.0


def test_consecutive_misses_revoke_the_dependence_entirely():
    ledger = PredictionReliabilityLedger(minimum_records=3, revoke_after_consecutive_misses=3)
    for index in range(3):
        ledger.record_pair(
            model_version="state-v1",
            readout="viability",
            predicted_value=-0.4,
            realized_value=0.9,
            interval=(-0.5, -0.3),
        )
    assert ledger.is_revoked("state-v1", "viability")
    assert ledger.weight("state-v1", "viability") == 0.0


def test_well_calibrated_predictions_keep_their_influence():
    ledger = PredictionReliabilityLedger(minimum_records=3)
    for index in range(4):
        ledger.record_pair(
            model_version="state-v1",
            readout="viability",
            predicted_value=-0.4,
            realized_value=-0.35,
            interval=(-0.5, -0.3),
        )
    summary = ledger.summarize("state-v1", "viability")
    assert summary.weight == 1.0
    assert summary.miss_rate == 0.0


def test_revocation_is_scoped_to_one_readout_and_model():
    ledger = PredictionReliabilityLedger(minimum_records=3, revoke_after_consecutive_misses=3)
    for index in range(3):
        ledger.record_pair(
            model_version="state-v1",
            readout="viability",
            predicted_value=-0.4,
            realized_value=0.9,
            interval=(-0.5, -0.3),
        )
        ledger.record_pair(
            model_version="state-v1",
            readout="expression",
            predicted_value=1.0,
            realized_value=1.1,
            interval=(0.8, 1.2),
        )
    assert ledger.is_revoked("state-v1", "viability")
    assert not ledger.is_revoked("state-v1", "expression")
    assert not ledger.is_revoked("state-v2", "viability")


def test_unscored_predictions_do_not_revoke_anything():
    ledger = PredictionReliabilityLedger()
    ledger.record_pair(
        model_version="state-v1",
        readout="viability",
        predicted_value=-0.4,
        realized_value=None,
        interval=(-0.5, -0.3),
    )
    assert ledger.weight("state-v1", "viability") == 1.0
    assert not ledger.is_revoked("state-v1", "viability")


def test_source_clusters_count_one_original_experiment_once():
    index = SourceClusterIndex(
        [
            SourceCluster("experiment-1", frozenset({"paper-a", "paper-b"})),
            SourceCluster("experiment-2", frozenset({"paper-c"})),
        ]
    )
    assert index.cluster_of("paper-a") == "experiment-1"
    assert index.count_independent(["paper-a", "paper-b", "paper-c"]) == 2
    assert index.count_independent(["paper-a", "paper-b"]) == 1
    assert index.cluster_of("unregistered") == "unregistered"


def test_build_index_accepts_plain_mappings():
    index = build_index([{"cluster_id": "exp-1", "source_ids": ["a", "b"], "note": "shared dataset"}])
    assert index.independent({"a", "b"}) == frozenset({"exp-1"})
    assert index.cluster_members("exp-1") == frozenset({"a", "b"})


def test_record_pair_preserves_result_provenance():
    ledger = PredictionReliabilityLedger()
    entry = ledger.record_pair(
        model_version="state-v1",
        readout="viability",
        predicted_value=-0.4,
        realized_value=-0.35,
        source_cluster="experiment-1",
        result_id="result-1",
        time_hours=24.0,
        condition_fingerprint="dose-1",
    )
    assert entry.source_cluster == "experiment-1"
    assert entry.result_id == "result-1"
    assert entry.time_hours == 24.0
    assert entry.condition_fingerprint == "dose-1"


@pytest.mark.parametrize("result_id", [None, "result-1"])
def test_repeated_source_under_new_requests_does_not_increase_sample_size(result_id):
    ledger = PredictionReliabilityLedger()
    first = ledger.record_pair(
        model_version="state-v1",
        readout="viability",
        context_identifier="cell-a",
        predicted_value=-0.4,
        realized_value=0.9,
        interval=(-0.5, -0.3),
        source_cluster="experiment-1",
        result_id=result_id,
        time_hours=24.0,
        condition_fingerprint="dose-1",
        request_id="request-1",
        action_identifier="action-1",
    )
    for index in range(2, 5):
        repeated = ledger.record_pair(
            model_version="state-v1",
            readout="viability",
            context_identifier="cell-a",
            predicted_value=-0.2,
            realized_value=0.8,
            interval=(-0.3, -0.1),
            source_cluster="experiment-1",
            result_id=f"result-{index}" if result_id else None,
            time_hours=24.0,
            condition_fingerprint="dose-1",
            request_id=f"request-{index}",
            action_identifier=f"action-{index}",
        )
        assert repeated is first
    assert ledger.records == (first,)
    summary = ledger.summarize("state-v1", "viability", "cell-a")
    assert summary.records == summary.scored == 1
    assert summary.provisional
    assert summary.weight == 1.0
    assert not summary.revoked


def test_result_id_deduplicates_even_when_source_context_and_time_change():
    ledger = PredictionReliabilityLedger()
    first = ledger.record_pair(
        model_version="state-v1",
        readout="viability",
        predicted_value=1.0,
        realized_value=1.0,
        result_id="result-1",
    )
    repeated = replace(
        first,
        request_id="new-request",
        context_identifier="cell-a",
        source_cluster="experiment-2",
        time_hours=48.0,
        condition_fingerprint="dose-2",
    )
    assert ledger.record(repeated) is first
    assert ledger.records == (first,)
    distinct = replace(first, result_id="result-2")
    assert ledger.record(distinct) is distinct
    assert len(ledger.records) == 2


@pytest.mark.parametrize("identity", [{"result_id": "result-1"}, {"source_cluster": "experiment-1"}])
@pytest.mark.parametrize("change", [{"model_version": "state-v2"}, {"readout": "expression"}])
def test_result_and_source_deduplication_are_scoped_to_model_and_readout(identity, change):
    ledger = PredictionReliabilityLedger()
    first = ledger.record_pair(
        model_version="state-v1",
        readout="viability",
        predicted_value=1.0,
        realized_value=1.0,
        **identity,
    )
    distinct = replace(first, **change)
    assert ledger.record(distinct) is distinct
    assert len(ledger.records) == 2


@pytest.mark.parametrize(
    "change",
    [
        {"context_identifier": "cell-b"},
        {"context_identifier": None},
        {"source_cluster": "experiment-2"},
        {"time_hours": 48.0},
        {"time_hours": None},
        {"condition_fingerprint": "dose-2"},
        {"condition_fingerprint": None},
    ],
)
def test_different_source_context_time_or_condition_remains_independent(change):
    ledger = PredictionReliabilityLedger()
    first = ledger.record_pair(
        model_version="state-v1",
        readout="viability",
        context_identifier="cell-a",
        predicted_value=1.0,
        realized_value=1.0,
        source_cluster="experiment-1",
        time_hours=24.0,
        condition_fingerprint="dose-1",
    )
    distinct = replace(first, **change)
    assert ledger.record(distinct) is distinct
    assert len(ledger.records) == 2


@pytest.mark.parametrize("source_cluster", [None, ""])
def test_legacy_records_without_result_or_source_identity_still_append(source_cluster):
    ledger = PredictionReliabilityLedger()
    entry = ScoredPrediction("state-v1", "viability", None, 1.0, (0.0, 2.0), 1.0)
    entry = replace(entry, source_cluster=source_cluster)
    for _ in range(3):
        assert ledger.record(entry) is entry
    assert ledger.records == (entry, entry, entry)


@pytest.mark.parametrize(
    "ungraded",
    [
        {"predicted_value": None},
        {"realized_value": None},
        {"interval": None},
        {"interval": None, "descriptive_interval": (-0.5, -0.3)},
        {"interval": (float("nan"), -0.3)},
        {"interval": (-0.3, -0.5)},
    ],
)
def test_ungraded_records_do_not_satisfy_the_calibration_minimum(ungraded):
    ledger = PredictionReliabilityLedger(minimum_records=3, revoke_after_consecutive_misses=3)
    miss = ScoredPrediction("state-v1", "viability", None, -0.4, (-0.5, -0.3), 0.9)
    ledger.record(miss)
    ledger.record(miss)
    for _ in range(3):
        ledger.record(replace(miss, **ungraded))
    summary = ledger.summarize("state-v1", "viability")
    assert summary.records == 5
    assert summary.interval_hits == 0
    assert summary.miss_rate == 1.0
    assert summary.consecutive_misses == 2
    assert summary.provisional
    assert summary.weight == 1.0
    assert not summary.revoked
    ledger.record(miss)
    summary = ledger.summarize("state-v1", "viability")
    assert not summary.provisional
    assert summary.revoked
    assert summary.weight == 0.0


@pytest.mark.parametrize("field", ["predicted_value", "realized_value"])
@pytest.mark.parametrize("value", [None, float("nan"), float("inf"), -float("inf"), True, False, "1.0"])
def test_nonfinite_boolean_and_nonnumeric_values_are_not_scored(field, value):
    ledger = PredictionReliabilityLedger(minimum_records=1)
    entry = ScoredPrediction("state-v1", "viability", None, 1.0, (0.0, 2.0), 1.0)
    entry = ledger.record(replace(entry, **{field: value}))
    assert not entry.scored
    assert entry.interval_hit is None
    summary = ledger.summarize("state-v1", "viability")
    assert summary.records == 1
    assert summary.scored == summary.interval_hits == 0
    assert summary.miss_rate is None
    assert summary.provisional
    assert summary.weight == 1.0
    assert not summary.revoked


@pytest.mark.parametrize("value", [0, 1, 1.5, 2.0])
def test_finite_numeric_values_are_scored_and_interval_boundaries_are_inclusive(value):
    entry = ScoredPrediction("state-v1", "viability", None, value, (0.0, 2.0), value)
    assert entry.scored
    assert entry.interval_hit is True


@pytest.mark.parametrize(
    "interval",
    [
        (float("nan"), 2.0),
        (0.0, float("nan")),
        (-float("inf"), 2.0),
        (0.0, float("inf")),
        (float("inf"), 2.0),
        (0.0, -float("inf")),
        (2.0, 0.0),
        (False, 2.0),
        (0.0, True),
        ("0.0", 2.0),
    ],
)
def test_invalid_intervals_are_ungraded_instead_of_counted_as_misses(interval):
    ledger = PredictionReliabilityLedger(minimum_records=1)
    entry = ledger.record_pair(
        model_version="state-v1",
        readout="viability",
        predicted_value=1.0,
        realized_value=1.0,
        interval=interval,
    )
    assert entry.scored
    assert entry.interval_hit is None
    summary = ledger.summarize("state-v1", "viability")
    assert summary.scored == 1
    assert summary.miss_rate is None
    assert summary.consecutive_misses == 0
    assert summary.provisional
    assert summary.weight == 1.0
    assert not summary.revoked


def test_unknown_context_does_not_pollute_a_specific_cell_scope():
    ledger = PredictionReliabilityLedger()
    unknown = ScoredPrediction("state-v1", "viability", None, -0.4, (-0.5, -0.3), 0.9)
    for _ in range(3):
        ledger.record(unknown)
    ledger.record(replace(unknown, context_identifier="cell-a", realized_value=-0.4))
    summary = ledger.summarize("state-v1", "viability", "cell-a")
    assert summary.records == summary.scored == summary.interval_hits == 1
    assert summary.miss_rate == 0.0
    assert summary.consecutive_misses == 0
    assert summary.provisional
    assert summary.weight == 1.0
    assert not summary.revoked
    for context in ("cell-b", ""):
        summary = ledger.summarize("state-v1", "viability", context)
        assert summary.records == summary.scored == 0
        assert summary.miss_rate is None
        assert summary.provisional
        assert ledger.weight("state-v1", "viability", context) == 1.0
        assert not ledger.is_revoked("state-v1", "viability", context)
    assert ledger.summarize("state-v1", "viability").records == 4
