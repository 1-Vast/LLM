"""Whole fit/commit boundaries, and missing assays do not create free evidence."""
import numpy as np
from threadpoolctl import threadpool_limits

from research.context_probe_20261011 import run as R


def packet():
    rng = np.random.default_rng(193)
    basal = rng.normal(size=(42, 15))
    response = basal[:, :3] @ rng.normal(size=(3, 36)) + rng.normal(size=(42, 36)) * 0.2
    return {"basal": basal, "y": response, "role": np.array(["reference"] * 18 + ["development"] * 12 + ["evaluation"] * 12),
            "context_id": np.array([f"context_{i}" for i in range(42)]),
            "lineage": np.array([f"lineage_{i % 4}" for i in range(42)]),
            "drug_id": np.array([f"drug_{i}" for i in range(36)])}


def test_unpurchased_evaluation_poison_cannot_change_fit_choices_or_commits():
    data = packet()
    with threadpool_limits(limits=1):
        model, probes, terminal, frozen = R.fit_and_choose(data)
        predictions, records = R.create_commits(data, model, probes, terminal, frozen)
        poisoned = {k: value.copy() for k, value in data.items()}
        index = np.flatnonzero(data["role"] == "evaluation")
        poisoned["y"][np.ix_(index, terminal)] = np.nan
        poisoned_model, other_probes, other_terminal, other_frozen = R.fit_and_choose(poisoned)
        other_predictions, other_records = R.create_commits(poisoned, poisoned_model, other_probes, other_terminal, other_frozen)
    assert other_frozen == frozen
    assert other_records == records
    np.testing.assert_array_equal(predictions, other_predictions)


def test_missing_fixed_probe_forces_same_prior_and_still_charges_full_attempt():
    data = packet()
    with threadpool_limits(limits=1):
        model, probes, terminal, frozen = R.fit_and_choose(data)
        index = np.flatnonzero(data["role"] == "evaluation")[0]
        data["y"][index, probes[0]] = np.nan
        predictions, records = R.create_commits(data, model, probes, terminal, frozen)
    for record, prediction in zip(records[:len(R.ARMS)], predictions[0]):
        np.testing.assert_array_equal(prediction, predictions[0, 0])
        assert record["selected_indices"] == records[0]["selected_indices"]
        assert not set(record["selected_indices"]).intersection(probes)
        if record["arm"] != "zero_purchase":
            assert record["measurements"] == 8 and record["turnarounds"] == 1 and record["resource"] == 10
            assert record["update_status"] == "missing_probe_fallback"


def test_missing_terminal_is_unscored_and_cannot_trigger_replacement():
    chosen = np.arange(10)
    truth = np.arange(20, dtype=float)
    truth[3] = np.nan
    assert R.utility(truth, chosen) is None
    assert np.array_equal(chosen, np.arange(10))
