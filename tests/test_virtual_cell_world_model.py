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

from virtual_cell import (
    CalibrationPair,
    CompositeWorldModel,
    HierarchicalDoseResponseModel,
    Interval,
    LinearPerturbationBaseline,
    PerturbationTable,
    PredictionRequest,
    SimulationCostLedger,
    StatePrediction,
    SupportRecord,
    SupportRegistry,
    SystemContext,
    compare_models,
    evaluate_exit_conditions,
    score,
    shuffled,
    stratify,
    table_from_anndata,
)
from virtual_cell.interface import Intervention

SCIPLEX_PATH = Path("data/raw/sciplex3/sciplex_complete_middle_subset.h5ad")


def _table() -> PerturbationTable:
    contexts = ("A549", "A549", "A549", "A549", "U2OS", "U2OS", "U2OS", "U2OS")
    perturbations = ("drug_p", "drug_p", "drug_p", "drug_p", "drug_p", "drug_p", "drug_p", "drug_p")
    doses = (0.0, 1.0, 10.0, 100.0, 0.0, 1.0, 10.0, 100.0)
    viability = tuple(float(1.0 - 0.08 * np.log1p(dose)) for dose in doses)
    return PerturbationTable(
        context_ids=contexts,
        perturbations=perturbations,
        modes=("drug",) * 8,
        doses=doses,
        times=(float("nan"),) * 8,
        readouts=("viability",),
        values={"viability": viability},
        source="synthetic",
    )


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


def test_linear_baseline_predicts_in_domain_and_abstains_outside_it():
    model = LinearPerturbationBaseline(_table())
    prediction = model.predict(_request())
    assert prediction.applicable
    assert prediction.contract_valid
    assert prediction.in_distribution is True
    assert prediction.intervals["viability"].low <= prediction.state_change["viability"] <= prediction.intervals["viability"].high

    outside = model.predict(_request(dose=1e6))
    assert not outside.applicable
    assert outside.abstain_reason is not None
    assert "dose_out_of_range" in outside.abstain_reason
    assert outside.contract_valid


def test_hierarchical_model_needs_enough_dose_points():
    model = HierarchicalDoseResponseModel(_table(), minimum_points=4)
    prediction = model.predict(_request())
    assert prediction.applicable
    assert prediction.contract_valid

    sparse = HierarchicalDoseResponseModel(_table(), minimum_points=64)
    abstained = sparse.predict(_request())
    assert not abstained.applicable
    assert "insufficient_dose_points" in (abstained.abstain_reason or "")


def test_composite_falls_through_and_bills_compute_separately():
    ledger = SimulationCostLedger()
    composite = CompositeWorldModel(
        [HierarchicalDoseResponseModel(_table(), minimum_points=64), LinearPerturbationBaseline(_table())],
        ledger=ledger,
    )
    prediction = composite.predict(_request())
    assert prediction.applicable
    assert composite.last_rung == "linear_baseline"
    summary = ledger.summary()
    assert summary["calls"] == {"linear_baseline": 1}
    assert "linear_baseline" not in summary["contract_violations"]
    assert summary["compute_cost"] > 0.0


def test_composite_converts_a_contract_violation_into_an_abstention():
    class BrokenRung:
        name = "broken"

        def capabilities(self):
            return LinearPerturbationBaseline(_table()).capabilities()

        def assess_query(self, request):
            return LinearPerturbationBaseline(_table()).assess_query(request)

        def predict(self, request):
            return StatePrediction(applicable=True, state_change={"viability": 1.0}, uncertainty=None, limitations=())

    ledger = SimulationCostLedger()
    composite = CompositeWorldModel([BrokenRung()], ledger=ledger)
    prediction = composite.predict(_request())
    assert not prediction.applicable
    assert prediction.abstain_reason == "contract_violation"
    assert ledger.summary()["contract_violations"] == {"broken": 1}


def test_shuffled_control_keeps_intervals_but_permutes_values():
    model = LinearPerturbationBaseline(_table())
    control = shuffled(model, seed=3)
    original = model.predict(_request(readout="viability"))
    permuted = control.predict(_request(readout="viability"))
    assert permuted.intervals == original.intervals
    assert permuted.limitations[-1] == "shuffle_control"


def test_descriptive_spread_never_becomes_a_confidence():
    """A rung with only residual dispersion declares no calibrated confidence (F07).

    Both ladder rungs derive their intervals from the residual scale on their
    own fitting rows, which is a dispersion, not a held-out coverage. Mapping
    that width to ``1/(1+width)`` would hand an invented number the authority
    of a calibrated confidence, so the rungs declare none and name the
    unquantified sources instead.
    """

    linear = LinearPerturbationBaseline(_table()).predict(_request())
    assert linear.confidence is None
    assert linear.uncertainty_components
    assert linear.contract_valid

    hierarchical = HierarchicalDoseResponseModel(_table(), minimum_points=4).predict(_request())
    assert hierarchical.confidence is None
    assert hierarchical.uncertainty_components
    assert hierarchical.contract_valid


def test_shuffled_control_preserves_the_unquantified_sources():
    """The shuffled control keeps the named sources that license its absent confidence."""

    permuted = shuffled(LinearPerturbationBaseline(_table()), seed=3).predict(_request())
    assert permuted.confidence is None
    assert permuted.uncertainty_components
    assert permuted.contract_valid


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


def test_real_perturbation_table_can_be_pseudo_bulked():
    if not SCIPLEX_PATH.is_file():
        return
    table = table_from_anndata(SCIPLEX_PATH, max_cells=50_000)
    assert len(table.context_ids) > 0
    assert set(table.readouts) == {"proliferation_index"}
    model = LinearPerturbationBaseline(table)
    contexts = sorted(set(table.context_ids))
    perturbations = sorted(set(table.perturbations))
    request = PredictionRequest(
        request_id="real-1",
        case_id="case-real",
        contrast_id="contrast-real",
        plan_version=1,
        intervention=Intervention(
            identifier=perturbations[0], mode="drug", intended_targets=("TARGET",),
            dose=float(min(dose for dose in table.doses if dose > 0) or 0.0), dose_unit="uM",
        ),
        context=SystemContext(identifier=contexts[0], description="real context", dataset_id="sciplex3", control_dataset_id="sciplex3"),
        readouts=table.readouts,
        model_version="linear_baseline",
    )
    prediction = model.predict(request)
    assert prediction.applicable
    assert prediction.contract_valid
    assert prediction.in_distribution is True
