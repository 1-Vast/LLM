"""Virtual-cell world model: contract, applicability ladder, calibration, billing.

File summary
- Path: tests/test_virtual_cell_world_model.py
- Purpose: World-model contract, applicability ladder, calibration and compute billing.
- Core points: assertions here are contract tests, not biological results; each test pins one boundary that must not silently move.
- Interfaces: `test_prediction_contract_requires_confidence_and_distribution_flag()`, `test_interval_validation_rejects_inverted_bounds()`, `test_support_registry_names_the_reason_it_abstains()`, `test_linear_baseline_predicts_in_domain_and_abstains_outside_it()`, `test_hierarchical_model_needs_enough_dose_points()`, `test_composite_falls_through_and_bills_compute_separately()`
- Depends on: virtual_cell
"""
from pathlib import Path

import numpy as np

from virtual_cell.calibration import CalibrationPair, compare_models, evaluate_exit_conditions, score, stratify
from virtual_cell.world_model import CompositeWorldModel, SimulationCostLedger
from virtual_cell.interface import Interval, SystemContext
from virtual_cell import PredictionRequest, StatePrediction
from virtual_cell.applicability import SupportRecord, SupportRegistry
from virtual_cell.interface import Intervention

SCIPLEX_PATH = Path("data/raw/sciplex3/sciplex_complete_middle_subset.h5ad")




def _request(dose: float = 10.0, context: str = "A549", readout: str = "viability") -> PredictionRequest:
    return PredictionRequest(
        request_id="req-1",
        case_id="case-1",
        contrast_id="contrast-1",
        plan_version=1,
        intervention=Intervention(
            identifier="drug_p",
            mode="drug",
            intended_targets=("TARGET",),
            dose=dose,
            dose_unit="uM",
        ),
        context=SystemContext(identifier=context, description="test context", dataset_id="ds-1", control_dataset_id="ctrl-1"),
        readouts=(readout,),
        model_version="linear_baseline",
    )


def test_prediction_contract_requires_confidence_and_distribution_flag():
    incomplete = StatePrediction(applicable=True, state_change={"a": 1.0}, uncertainty=None, limitations=())
    assert "applicable_confidence_missing" in incomplete.contract_errors()
    assert "in_distribution_missing" in incomplete.contract_errors()
    assert not incomplete.contract_valid

    silent_abstain = StatePrediction(applicable=False, state_change=None, uncertainty=None, limitations=())
    assert silent_abstain.contract_errors() == ("abstain_reason_missing",)

    complete = StatePrediction(
        applicable=True,
        state_change={"a": 1.0},
        uncertainty=0.1,
        limitations=(),
        confidence=0.7,
        in_distribution=True,
    )
    assert complete.contract_valid


def test_interval_validation_rejects_inverted_bounds():
    prediction = StatePrediction(
        applicable=False,
        state_change=None,
        uncertainty=None,
        limitations=(),
        abstain_reason="no_support",
        intervals={"a": Interval(1.0, -1.0)},
    )
    assert "invalid_interval:a" in prediction.contract_errors()


def test_support_registry_names_the_reason_it_abstains():
    registry = SupportRegistry(
        [
            SupportRecord(
                context_id="A549",
                perturbations=frozenset({"drug_p"}),
                modes=frozenset({"drug"}),
                readouts=frozenset({"viability"}),
                dose_range=(0.0, 100.0),
            )
        ]
    )
    assert registry.assess(context_id="A549", perturbation="drug_p", mode="drug", dose=10.0).in_distribution
    unknown = registry.assess(context_id="HUVEC", perturbation="drug_p", mode="drug", dose=10.0)
    assert unknown.reasons == ("context_unregistered",)
    assert unknown.abstain_reason == "context_unregistered"
    far = registry.assess(context_id="A549", perturbation="drug_p", mode="drug", dose=5000.0)
    assert far.reasons == ("dose_out_of_range",)
















def test_calibration_scores_coverage_before_accuracy():
    pairs = [
        CalibrationPair(predicted=1.0, low=0.5, high=1.5, observed=1.1, strata={"mode": "drug"}),
        CalibrationPair(predicted=1.0, low=0.5, high=1.5, observed=3.0, strata={"mode": "drug"}),
        CalibrationPair(predicted=0.0, low=-0.5, high=0.5, observed=0.2, strata={"mode": "ko"}),
    ]
    report = score(pairs)
    assert report.pairs == 3
    assert abs(report.interval_coverage - 2 / 3) < 1e-9
    assert report.mean_absolute_error is not None
    by_mode = stratify(pairs, "mode")
    assert by_mode["drug"].pairs == 2 and by_mode["ko"].pairs == 1


def test_exit_conditions_flag_over_confident_intervals():
    over_confident = [
        CalibrationPair(predicted=0.0, low=-0.01, high=0.01, observed=float(index)) for index in range(12)
    ]
    reasons = evaluate_exit_conditions(score(over_confident))
    assert "over_confident_intervals" in reasons

    too_few = [CalibrationPair(predicted=0.0, low=0.0, high=1.0, observed=0.5)]
    assert evaluate_exit_conditions(score(too_few)) == ("insufficient_scored_predictions",)


def test_module_swap_comparison_reports_per_stratum():
    good = {
        "drug": score([CalibrationPair(predicted=1.0, low=0.5, high=1.5, observed=1.0) for _ in range(8)]),
    }
    poor = {
        "drug": score([CalibrationPair(predicted=1.0, low=1.4, high=1.6, observed=0.0) for _ in range(8)]),
    }
    verdicts = compare_models(good, poor)
    assert verdicts["drug"] == "reference_over_confident"
