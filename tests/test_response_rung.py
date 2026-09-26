"""The SciPlex3 response rung serves pathway readouts, refuses by name, and earns its intervals.

File summary
- Path: tests/test_response_rung.py
- Purpose: pin the contract of `virtual_cell.response_rung` on a synthetic, digest-bound library
  of real small-molecule structures, so no local asset is needed.
- Core points: a supported query yields a contract-valid planning-only prediction; each unsupported
  input is refused by name; a compound already in the library is refused so its measurement is used;
  intervals are CALIBRATED only when their coverage receipt passed; novelty flips in_distribution.
- Interfaces: `test_*` functions only.
- Depends on: virtual_cell.response_rung, virtual_cell.interface
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("rdkit")

from virtual_cell.applicability import SupportLevel
from virtual_cell.interface import (
    IntervalKind, Intervention, PredictionRequest, QuerySupport, SystemContext, safe_predict,
)
from virtual_cell.response_rung import NORM_READOUT, ResponseRungConfig, SciPlexResponseRung
from virtual_cell.signature_retrieval import LIBRARY_SCHEMA

GENES = [f"G{i}" for i in range(60)]
LINES = ["A549", "MCF7"]
DOSES = [10.0, 100.0, 1000.0, 10000.0]
LIBRARY = {
    "aspirin": "CC(=O)OC1=CC=CC=C1C(=O)O",
    "ibuprofen": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
    "caffeine": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
    "paracetamol": "CC(=O)NC1=CC=C(O)C=C1",
    "naproxen": "COC1=CC2=CC=C(C=C2C=C1)C(C)C(=O)O",
}
QUERIES = {
    "aspirin_methyl_ester": "CC(=O)OC1=CC=CC=C1C(=O)OC",
    "hexadecane": "CCCCCCCCCCCCCCCC",
    "aspirin_salt": "CC(=O)OC1=CC=CC=C1C(=O)[O-].[Na+]",
}


def _build(tmp_path: Path, *, overall_passed=True, coverage=0.8, informative_sets=True) -> SciPlexResponseRung:
    rng = np.random.default_rng(0)
    directions = {name: rng.normal(0, 1, len(GENES)) for name in LIBRARY}
    profiles, ec, el, ed = [], [], [], []
    for ci, name in enumerate(LIBRARY):
        for li in range(len(LINES)):
            for di, dose in enumerate(DOSES):
                profiles.append(directions[name] * np.log10(dose))   # response grows with log dose
                ec.append(ci), el.append(li), ed.append(di)
    profiles = np.asarray(profiles, dtype=np.float32)
    systematic = np.stack([[profiles[(np.asarray(el) == li) & (np.asarray(ed) == di)].mean(0) for di in range(4)]
                           for li in range(2)]).astype(np.float32)
    lib = tmp_path / "lib"
    lib.mkdir()
    np.savez(lib / "library.npz", profiles=profiles, entry_compound=np.asarray(ec), entry_line=np.asarray(el),
             entry_dose=np.asarray(ed), systematic=systematic)
    compounds = [{"name": n, "skeleton": "", "class": "c", "smiles": s} for n, s in LIBRARY.items()]
    from virtual_cell.response_rung import _skeleton
    for item in compounds:
        item["skeleton"] = _skeleton(item["smiles"])
    meta = {"schema": LIBRARY_SCHEMA, "genes": GENES, "lines": LINES, "doses": DOSES, "compounds": compounds,
            "arrays_sha256": hashlib.sha256((lib / "library.npz").read_bytes()).hexdigest()}
    (lib / "library.json").write_text(json.dumps(meta), encoding="utf-8")
    strata = [f"{l}|{d:g}|{n}" for l in LINES for d in DOSES for n in ("in", "novel")]
    readouts = [NORM_READOUT, "hallmark:SET_A"]
    calibration = {"level": 0.8, "quantiles": {r: {s: 0.5 for s in strata} for r in readouts},
                   "gene_sets": {"SET_A": GENES[:20]}, "coverage": {r: coverage for r in readouts},
                   "acceptance": {"per_readout_minimum": 0.7, "overall_passed": overall_passed},
                   "informative": {NORM_READOUT: True, "hallmark:SET_A": informative_sets}}
    (tmp_path / "calibration.json").write_text(json.dumps(calibration), encoding="utf-8")
    registrations = {**QUERIES, "aspirin": LIBRARY["aspirin"]}
    return SciPlexResponseRung(ResponseRungConfig(lib, tmp_path / "calibration.json", registrations))


def _request(rung, identifier="aspirin_methyl_ester", *, context="A549", dose=1000.0, unit="nM", time=24.0,
             mode="drug", readouts=(NORM_READOUT, "hallmark:SET_A")):
    return PredictionRequest(
        request_id="r1", case_id="case", contrast_id="c1", plan_version=1,
        intervention=Intervention(identifier=identifier, mode=mode, intended_targets=(), dose=dose,
                                  dose_unit=unit, time_hours=time),
        context=SystemContext(identifier=context, description="line"), readouts=tuple(readouts),
        model_version=rung.model_version)


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
    from virtual_cell.backends import BACKEND_CHOICES, build_backend

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

    from virtual_cell.backends import build_backend

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
