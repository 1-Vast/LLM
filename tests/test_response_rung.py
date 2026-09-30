"""The SciPlex3 response rung serves pathway readouts, refuses by name, and earns its intervals.

File summary
- Path: tests/test_response_rung.py
- Purpose: pin the contract of `virtual_cell.signature_retrieval` on a synthetic, digest-bound library
  of real small-molecule structures, so no local asset is needed.
- Core points: a supported query yields a contract-valid planning-only prediction; each unsupported
  input is refused by name; a compound already in the library is refused so its measurement is used;
  intervals are CALIBRATED only when their coverage receipt passed; novelty flips in_distribution.
- Interfaces: `test_*` functions only.
- Depends on: virtual_cell.signature_retrieval, virtual_cell.interface
"""
import json
from pathlib import Path

import pytest

pytest.importorskip("rdkit")

from virtual_cell.applicability import SupportLevel
from virtual_cell.interface import (
    IntervalKind, QuerySupport, SystemContext, safe_predict,
)
from virtual_cell.signature_retrieval import NORM_READOUT

from tests.fixtures.response_rung import _build, _request


def test_a_supported_query_is_a_contract_valid_planning_prediction(tmp_path):
    rung = _build(tmp_path)
    assessment, prediction = safe_predict(rung, _request(rung))
    assert assessment.support is QuerySupport.SUPPORTED
    assert assessment.validation_status is SupportLevel.VALIDATED
    assert prediction.applicable and prediction.contract_valid and prediction.in_distribution is True
    interval = prediction.intervals["hallmark:SET_A"]
    assert interval.kind is IntervalKind.CALIBRATED and interval.level == 0.8 and "receipt" in interval.basis
    assert any("not a measurement" in text for text in prediction.limitations)


@pytest.mark.parametrize("change, reason", [
    ({"context": "HepG2"}, "context_not_supported:HepG2"),
    ({"time": 72.0}, "time_not_supported:72h"),
    ({"dose": 50000.0}, "dose_outside_fitted_range"),
    ({"unit": "uM", "dose": 1.0}, "dose_unit_unsupported:uM"),
    ({"mode": "crispr_knockout"}, "modality_unsupported:crispr_knockout"),
    ({"readouts": ("viability",)}, "readout_not_served:viability"),
    ({"identifier": "aspirin"}, "query_compound_in_reference_library:use_its_measurement"),
    ({"identifier": "aspirin_salt"}, "query_compound_in_reference_library:use_its_measurement"),
])
def test_unsupported_queries_are_refused_by_name(tmp_path, change, reason):
    rung = _build(tmp_path)
    assessment, prediction = safe_predict(rung, _request(rung, **change))
    assert assessment.support is QuerySupport.UNSUPPORTED
    assert reason in assessment.limitations
    assert not prediction.applicable and prediction.abstain_reason


def test_an_unregistered_structure_is_a_missing_input(tmp_path):
    rung = _build(tmp_path)
    assessment = rung.assess_query(_request(rung, identifier="unknown_compound"))
    assert assessment.missing_inputs == ("registered_structure",)


def test_intervals_are_calibrated_only_when_the_receipt_passed(tmp_path):
    rung = _build(tmp_path, overall_passed=False)
    assessment, prediction = safe_predict(rung, _request(rung))
    assert assessment.validation_status is SupportLevel.EVALUATED_BELOW_ACCEPTANCE
    assert all(i.kind is IntervalKind.DESCRIPTIVE for i in prediction.intervals.values())
    assert prediction.contract_valid


def test_a_readout_no_better_than_the_average_response_is_refused(tmp_path):
    rung = _build(tmp_path, informative_sets=False)
    assert rung.served_readouts == (NORM_READOUT,)
    assessment, prediction = safe_predict(rung, _request(rung))
    assert "readout_not_informative_beyond_average_response:hallmark:SET_A" in assessment.limitations
    assert not prediction.applicable
    _, magnitude = safe_predict(rung, _request(rung, readouts=(NORM_READOUT,)))
    assert magnitude.applicable and set(magnitude.state_change) == {NORM_READOUT}


def test_a_structurally_novel_compound_is_out_of_distribution(tmp_path):
    rung = _build(tmp_path)
    _, prediction = safe_predict(rung, _request(rung, identifier="hexadecane"))
    assert prediction.applicable and prediction.in_distribution is False
    assert "novel" in prediction.intervals[NORM_READOUT].basis


def test_the_backend_choice_refuses_without_structures_or_library(tmp_path):
    from virtual_cell.world_model import BACKEND_CHOICES, build_backend

    assert "sciplex_response" in BACKEND_CHOICES
    with pytest.raises(ValueError, match="requires declared structures"):
        build_backend("sciplex_response", workspace=tmp_path)
    with pytest.raises(ValueError, match="needs its library and calibration"):
        build_backend("sciplex_response", workspace=tmp_path, structures={"x": "CCO"})


def test_a_query_template_carries_its_declared_dose_and_time():
    from virtual_cell.interface import VirtualCellQueryTemplate

    template = VirtualCellQueryTemplate("vorinostat", "drug", SystemContext("MCF7", "line"), (NORM_READOUT,), "v1",
                                        dose=1000.0, dose_unit="nM", time_hours=24.0)
    request = template.build(request_id="r", case_id="c", contrast_id="k", plan_version=1, intended_targets=("HDAC1",))
    assert (request.intervention.dose, request.intervention.dose_unit, request.intervention.time_hours) == (1000.0, "nM", 24.0)
    bare = VirtualCellQueryTemplate("vorinostat", "drug", SystemContext("MCF7", "line"), (NORM_READOUT,), "v1")
    built = bare.build(request_id="r", case_id="c", contrast_id="k", plan_version=1, intended_targets=())
    assert built.intervention.dose is None and built.intervention.time_hours is None


ROOT = Path(__file__).resolve().parents[1]
LIBRARY_DIR = ROOT / "data/virtual_cell/sciplex3_signature_library"


@pytest.mark.skipif(not (LIBRARY_DIR / "calibration.json").is_file(), reason="needs the local SciPlex3 signature library")
def test_the_built_library_serves_magnitude_and_refuses_pathways_and_known_compounds():
    """Pins the 2026-09-26 artifacts: only the response magnitude beat the average response."""

    from virtual_cell.world_model import build_backend

    library = json.loads((LIBRARY_DIR / "library.json").read_text(encoding="utf-8"))
    panobinostat = next(c["smiles"] for c in library["compounds"] if c["name"].startswith("Panobinostat"))
    rung = build_backend("sciplex_response", workspace=ROOT,
                         structures={"vorinostat": "ONC(=O)CCCCCCC(=O)Nc1ccccc1", "panobinostat": panobinostat})
    assert rung.served_readouts == (NORM_READOUT,)
    assessment, prediction = safe_predict(rung, _request(rung, identifier="vorinostat", context="MCF7",
                                                         readouts=(NORM_READOUT,)))
    assert prediction.applicable and prediction.intervals[NORM_READOUT].kind is IntervalKind.CALIBRATED
    assert assessment.validation_status is SupportLevel.VALIDATED
    known = rung.assess_query(_request(rung, identifier="panobinostat", readouts=(NORM_READOUT,)))
    assert "query_compound_in_reference_library:use_its_measurement" in known.limitations
    pathway = rung.assess_query(_request(rung, identifier="vorinostat", readouts=("hallmark:HALLMARK_P53_PATHWAY",)))
    assert "readout_not_informative_beyond_average_response:hallmark:HALLMARK_P53_PATHWAY" in pathway.limitations


def test_doses_between_measured_ones_are_interpolated_in_log_dose(tmp_path):
    rung = _build(tmp_path)
    low = safe_predict(rung, _request(rung, dose=100.0))[1].state_change[NORM_READOUT]
    mid = safe_predict(rung, _request(rung, dose=316.0))[1].state_change[NORM_READOUT]
    high = safe_predict(rung, _request(rung, dose=1000.0))[1].state_change[NORM_READOUT]
    assert low < mid < high
