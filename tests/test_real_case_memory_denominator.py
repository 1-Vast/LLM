"""Real frozen readings establish a valid-readout target, not an attempts denominator."""
from collections import Counter
import json

import pytest

from research.dual_core_followup import denominator as audit


@pytest.fixture(scope="module")
def real_run(tmp_path_factory):
    out = tmp_path_factory.mktemp("real_denominator") / "run"
    calls = Counter()
    original_forecast = audit.CaseMemoryOutcomeForecaster.forecast
    original_selector = audit.select_discriminating_action

    def forecast(model, contrast, actions, evidence, user_state=None):
        assert (out / "predeclared.json").is_file()
        assert evidence is not None and not evidence.updates
        calls[f"forecast:{user_state.outcome_mode}"] += 1
        return original_forecast(model, contrast, actions, evidence, user_state)

    def selector(candidates, actions, profile, budget, forecasts, consequences, **kwargs):
        assert (out / "predeclared.json").is_file()
        calls["production_selector"] += 1
        return original_selector(candidates, actions, profile, budget, forecasts, consequences, **kwargs)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(audit.CaseMemoryOutcomeForecaster, "forecast", forecast)
        patch.setattr(audit, "select_discriminating_action", selector)
        summary = audit.run(out, command=["pytest", "tests/test_real_case_memory_denominator.py"])
    rows = [json.loads(line) for line in (out / "query_paths.jsonl").read_text().splitlines()]
    return out, summary, rows, calls


def test_real_population_preserves_unit_reading_query_denominators(real_run):
    out, summary, rows, _ = real_run
    assert summary["population"] == {
        "test_independent_units": 26, "test_unit_cell_readings": 28, "contrast_queries": 112,
        "reference_independent_units": 65, "reference_proxy_labels": 976,
    }
    assert len({(row["unit"], row["cell"]) for row in rows}) == 28
    assert len({(row["unit"], row["cell"], row["own"], row["decoy"]) for row in rows}) == 112
    assert summary["reference_sampling_frames"] == {"valid_only": 976}
    assert summary["frozen_inputs_unchanged"] and not summary["calibration_loaded_or_fitted"]
    assert (out / "ledger.json").is_file()


def test_both_forecasters_and_production_selector_really_execute(real_run):
    _, _, _, calls = real_run
    # support_report reuses the public forecast API; each target is called twice per query.
    assert calls == {"forecast:valid_readout": 224, "forecast:attempted_experiment": 224,
                     "production_selector": 224}


def test_real_valid_only_records_cannot_supply_attempted_experiment_distribution(real_run):
    _, summary, rows, _ = real_run
    attempted = summary["targets"]["attempted_experiment"]
    assert attempted["available"] == 0 and attempted["refusals"] == {"insufficient_outcome_support": 112}
    assert attempted["queries_with_selected_action"] == 0
    for row in rows:
        valid = row["targets"]["valid_readout"]
        if valid["available"]:
            assert valid["returned_outcome_mode"] == "valid_readout"
            assert all("qc_failed" not in branch["probabilities"] for branch in valid["forecast"]["branches"])
            assert valid["selector_reasons"] == ["forecast_refused:experiment_validity_probability_required"]
        assert not valid["selected_actions"]
        assert row["targets"]["attempted_experiment"]["selector_reasons"] == ["forecast_refused:insufficient_outcome_support"]
        assert row["evidence_before_sha256"] == row["evidence_after_sha256"] and row["observations_unchanged"]
    assert summary["qc_success_probability"] is summary["terminal_benefit"] is None


def test_frozen_input_mismatch_stops_before_running_models(monkeypatch):
    modified = {**audit.FROZEN_SHA256, audit.PACK: "0" * 64}
    monkeypatch.setattr(audit, "FROZEN_SHA256", modified)
    with pytest.raises(ValueError, match="frozen_source_hash_mismatch"):
        audit.source_records(audit.ROOT)


def test_existing_output_cannot_be_overwritten(real_run):
    out, _, _, _ = real_run
    before = audit.file_sha(out / "predeclared.json")
    with pytest.raises(FileExistsError):
        audit.run(out)
    assert audit.file_sha(out / "predeclared.json") == before
