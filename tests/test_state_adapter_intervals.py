"""State adapter serves intervals when, and only when, a calibration is bound.

File summary
- Path: tests/test_state_adapter_intervals.py
- Purpose: pin the second half of the lawful-influence channel: the STATE
  adapter emits a coverage-claiming band for a served readout when a bound,
  receipt-validated interval calibration exists, and nothing otherwise.
- Core points: assertions here are contract tests, not biological results. The
  vector is synthetic, so no number here describes the checkpoint.
- Interfaces: `test_state_prediction_carries_a_calibrated_interval()`,
  `test_state_prediction_without_a_validating_receipt_is_descriptive()`,
  `test_state_prediction_without_an_interval_calibration_serves_none()`.
- Depends on: virtual_cell
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from virtual_cell.state_adapter import DatasetRegistration, StateAdapterConfig, StateCapabilityAdapter
from virtual_cell.interface import IntervalKind, Intervention, SystemContext
from virtual_cell import PredictionRequest
from virtual_cell.applicability import ValidationReceipt
from virtual_cell.calibration import IntervalCalibration, ScaleCalibration

MODEL_VERSION = "state-x-hvg"
CONTEXT = "NCI-H596"
READOUT = "embedding_delta_l2"
PARTITION = "partition-digest"


def _scale_calibration():
    """Scale 1.0 on the same declared partition, so served values stay raw.

    The interval calibration binds to the partition this lineage names, so the
    fixture has to name one for the binding to be checkable at all.
    """

    return ScaleCalibration(
        scale=1.0,
        endpoint="x_hvg_perturbation_shift",
        context_identifier=CONTEXT,
        fitted_on="synthetic development partition",
        independent_units=48,
        model_version=MODEL_VERSION,
        input_schema="X_hvg:3",
        development_partition_sha256=PARTITION,
    )


def _adapter(tmp_path: Path, *, interval_calibration, receipts) -> StateCapabilityAdapter:
    """A configured adapter whose inference is stubbed to one synthetic vector."""

    checkpoint = tmp_path / "model.ckpt"
    config_file = tmp_path / "config.yaml"
    checkpoint.write_text("checkpoint", encoding="utf-8")
    config_file.write_text("config", encoding="utf-8")
    asset = tmp_path / "c39.h5ad"
    asset.write_bytes(b"cells")
    digest = hashlib.sha256(b"cells").hexdigest()
    names = tmp_path / "names.json"
    names.write_text(
        json.dumps({"names": ["g0", "g1", "g2"], "dataset_sha256": digest, "feature_count": 3}),
        encoding="utf-8",
    )
    registration = DatasetRegistration(
        identifier="tahoe_c39",
        path=asset,
        sha256=digest,
        size_bytes=asset.stat().st_size,
        contexts=(CONTEXT,),
        feature_count=3,
        feature_names_path=names,
    )
    config = StateAdapterConfig(
        checkpoint,
        config_file,
        MODEL_VERSION,
        frozenset({"drug_a"}),
        python_executable=Path(sys.executable),
        datasets={"tahoe_c39": registration},
        output_directory=tmp_path / "artifacts",
        input_dim=3,
        input_coordinate_names=("g0", "g1", "g2"),
        validation_receipts=receipts,
        scale_calibration=_scale_calibration(),
        interval_calibration=interval_calibration,
    )
    return StateCapabilityAdapter(config)


@pytest.fixture()
def stubbed_inference(monkeypatch):
    """Replace the State subprocess and its runner with one written vector."""

    def run_runner(self, mode, request, summary_path, *, input_path=None, output=None, extra=()):
        payload = {
            "valid": True,
            "subset_sha256": "subset",
            "row_ids_sha256": "rows",
            "control_rows": 2,
            "perturbation_rows": 2,
        }
        if mode == "validate":
            # The vector is written through --vector-output; `output` is the
            # predicted asset the real runner would have produced.
            for index, argument in enumerate(extra):
                if argument == "--vector-output" and index + 1 < len(extra):
                    np.save(extra[index + 1], np.asarray([3.0, 4.0, 0.0], dtype=float))
            payload["output_sha256"] = "output"
        summary_path.write_text(json.dumps(payload), encoding="utf-8")
        return payload

    monkeypatch.setattr(StateCapabilityAdapter, "_run_runner", run_runner)
    monkeypatch.setattr(
        subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="", stderr="")
    )
    return None


def _request() -> PredictionRequest:
    return PredictionRequest(
        "req-1",
        "case-1",
        "contrast-1",
        1,
        Intervention("drug_a", "drug", ("TARGET",)),
        SystemContext(
            CONTEXT, "context", dataset_id="tahoe_c39", control_dataset_id="tahoe_c39"
        ),
        (READOUT,),
        MODEL_VERSION,
    )


def _calibration() -> IntervalCalibration:
    return IntervalCalibration(
        level=0.9,
        quantiles={READOUT: 1.25},
        endpoint="x_hvg_perturbation_shift",
        context_identifier=CONTEXT,
        fitted_on="synthetic calibration partition",
        independent_units=48,
        support={READOUT: 48},
        model_version=MODEL_VERSION,
        input_schema="X_hvg:3",
        development_partition_sha256=PARTITION,
    )


def _receipt(
    *,
    passed: bool = True,
    holdout_verified: bool = True,
    calibration: IntervalCalibration | None = None,
    metric: str = "interval_coverage",
    nominal_level: float | None = 0.9,
    model_version: str | None = MODEL_VERSION,
    context_identifier: str | None = CONTEXT,
) -> ValidationReceipt:
    bound = calibration if calibration is not None else _calibration()
    return ValidationReceipt(
        receipt_id="receipt-state-interval",
        endpoint=READOUT,
        split="synthetic held-out conditions",
        acceptance_criterion="held-out coverage within the binomial tolerance of 0.90",
        metric=metric,
        value=0.9,
        threshold=0.7,
        passed=passed,
        holdout_verified=holdout_verified,
        holdout_basis="synthetic fixture: declared verified" if holdout_verified else "",
        context_identifier=context_identifier,
        model_version=model_version,
        independent_units=12,
        calibration_sha256=bound.content_sha256(),
        nominal_level=nominal_level,
    )


def test_state_prediction_carries_a_calibrated_interval(tmp_path, stubbed_inference):
    adapter = _adapter(
        tmp_path,
        interval_calibration=_calibration(),
        receipts=(_receipt(passed=True, holdout_verified=True),),
    )
    prediction = adapter.predict(_request())

    assert prediction.applicable
    assert prediction.contract_valid, prediction.contract_errors()
    band = prediction.intervals[READOUT]
    assert band.kind is IntervalKind.CALIBRATED
    assert band.claims_coverage
    assert band.level == 0.9
    assert "receipt receipt-state-interval" in band.basis
    assert "partition-digest" in band.basis
    # The served value is the L2 norm of the synthetic vector, plus or minus the
    # fitted half-width; the band is around the served number, not beside it.
    assert band.low == pytest.approx(5.0 - 1.25)
    assert band.high == pytest.approx(5.0 + 1.25)
    assert prediction.confidence is None


def test_state_prediction_without_a_validating_receipt_is_descriptive(tmp_path, stubbed_inference):
    adapter = _adapter(
        tmp_path,
        interval_calibration=_calibration(),
        receipts=(_receipt(passed=True, holdout_verified=False),),
    )
    prediction = adapter.predict(_request())

    assert prediction.contract_valid, prediction.contract_errors()
    band = prediction.intervals[READOUT]
    assert band.kind is IntervalKind.DESCRIPTIVE
    assert not band.claims_coverage
    assert band.level is None
    assert band.basis

    unregistered = _adapter(tmp_path, interval_calibration=_calibration(), receipts=())
    band = unregistered.predict(_request()).intervals[READOUT]
    assert band.kind is IntervalKind.DESCRIPTIVE
    assert not band.claims_coverage


def test_state_prediction_without_an_interval_calibration_serves_none(tmp_path, stubbed_inference):
    adapter = _adapter(
        tmp_path,
        interval_calibration=None,
        receipts=(_receipt(passed=True, holdout_verified=True),),
    )
    prediction = adapter.predict(_request())

    assert prediction.applicable
    assert prediction.intervals == {}
    assert prediction.state_change["embedding_delta_l2"] == pytest.approx(5.0)
    assert set(prediction.state_change) == {
        "embedding_delta_l2",
        "mean_absolute_embedding_delta",
        "raw_embedding_delta_l2",
        "raw_mean_absolute_embedding_delta",
    }


def test_state_prediction_refuses_an_interval_calibration_bound_to_another_partition(
    tmp_path, stubbed_inference
):
    calibration = _calibration()
    misbound = IntervalCalibration(
        **{**calibration.__dict__, "context_identifier": "another-context"}
    )
    adapter = _adapter(
        tmp_path,
        interval_calibration=misbound,
        receipts=(_receipt(passed=True, holdout_verified=True),),
    )
    prediction = adapter.predict(_request())

    assert prediction.intervals == {}
    assert prediction.artifact_ref is not None


def test_a_receipt_for_another_calibration_artifact_cannot_calibrate(tmp_path, stubbed_inference):
    """A receipt bound to one fit cannot upgrade an interval served from another.

    Matching the readout and model name is not a qualification: the receipt
    has to name the content digest of the calibration actually being served.
    """

    other = IntervalCalibration(
        **{**_calibration().__dict__, "quantiles": {READOUT: 9.99}}
    )
    adapter = _adapter(
        tmp_path, interval_calibration=_calibration(), receipts=(_receipt(calibration=other),)
    )
    band = adapter.predict(_request()).intervals[READOUT]
    assert band.kind is IntervalKind.DESCRIPTIVE
    assert "receipt_calibration_digest_mismatch" in band.basis


def test_a_receipt_for_another_coverage_level_cannot_calibrate(tmp_path, stubbed_inference):
    adapter = _adapter(
        tmp_path,
        interval_calibration=_calibration(),
        receipts=(_receipt(nominal_level=0.8),),
    )
    band = adapter.predict(_request()).intervals[READOUT]
    assert band.kind is IntervalKind.DESCRIPTIVE
    assert "receipt_nominal_level_mismatch" in band.basis


def test_a_receipt_for_another_context_cannot_calibrate(tmp_path, stubbed_inference):
    adapter = _adapter(
        tmp_path,
        interval_calibration=_calibration(),
        receipts=(_receipt(context_identifier="another-context"),),
    )
    band = adapter.predict(_request()).intervals[READOUT]
    assert band.kind is IntervalKind.DESCRIPTIVE
    assert "receipt_context_mismatch" in band.basis


def test_a_receipt_without_a_context_cannot_calibrate(tmp_path, stubbed_inference):
    adapter = _adapter(
        tmp_path,
        interval_calibration=_calibration(),
        receipts=(_receipt(context_identifier=None),),
    )
    band = adapter.predict(_request()).intervals[READOUT]
    assert band.kind is IntervalKind.DESCRIPTIVE
    assert "receipt_context_missing" in band.basis


def test_a_noncoverage_receipt_cannot_calibrate(tmp_path, stubbed_inference):
    """A passing MAE evaluation is evidence about accuracy, not about coverage."""

    adapter = _adapter(
        tmp_path,
        interval_calibration=_calibration(),
        receipts=(_receipt(metric="mean_absolute_error"),),
    )
    band = adapter.predict(_request()).intervals[READOUT]
    assert band.kind is IntervalKind.DESCRIPTIVE
    assert "receipt_metric_not_interval_coverage" in band.basis


def test_a_receipt_with_unstated_bindings_cannot_calibrate(tmp_path, stubbed_inference):
    missing_all = _receipt(
        nominal_level=None,
        model_version=None,
    )
    # Rebuild without the digest binding: a receipt that cannot name the
    # calibration it evaluated must not upgrade the interval.
    unstated = ValidationReceipt(
        **{
            **missing_all.__dict__,
            "calibration_sha256": None,
        }
    )
    adapter = _adapter(tmp_path, interval_calibration=_calibration(), receipts=(unstated,))
    band = adapter.predict(_request()).intervals[READOUT]
    assert band.kind is IntervalKind.DESCRIPTIVE
    assert "receipt_calibration_digest_missing" in band.basis
    assert "receipt_nominal_level_missing" in band.basis
    assert "receipt_model_version_missing" in band.basis


def test_a_receipt_missing_its_holdout_basis_cannot_calibrate(tmp_path, stubbed_inference):
    unbased = ValidationReceipt(
        **{**_receipt().__dict__, "holdout_basis": ""}
    )
    adapter = _adapter(tmp_path, interval_calibration=_calibration(), receipts=(unbased,))
    band = adapter.predict(_request()).intervals[READOUT]
    assert band.kind is IntervalKind.DESCRIPTIVE
    assert "receipt_holdout_basis_missing" in band.basis


def test_the_registry_loads_and_binds_a_declared_interval_calibration(tmp_path):
    """The workspace configuration path binds exactly the declared calibration.

    Production ships none, so the channel stays closed; this pins the loader so
    a future calibration file is bound as written, not silently dropped.
    """

    calibration = _calibration()
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "datasets": {},
                "models": {},
                "interval_calibrations": [
                    {
                        "level": calibration.level,
                        "quantiles": dict(calibration.quantiles),
                        "endpoint": calibration.endpoint,
                        "context_identifier": calibration.context_identifier,
                        "fitted_on": calibration.fitted_on,
                        "independent_units": calibration.independent_units,
                        "support": dict(calibration.support),
                        "model_version": calibration.model_version,
                        "input_schema": calibration.input_schema,
                        "development_partition_sha256": calibration.development_partition_sha256,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    from virtual_cell.state_adapter import load_registry

    registry = load_registry(tmp_path, registry_path)
    loaded = registry.interval_calibration_for(MODEL_VERSION)
    assert loaded is not None
    assert loaded == calibration
    assert registry.interval_calibration_for("another-checkpoint") is None
