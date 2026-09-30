"""Digest-bound synthetic response library shared by contract tests."""
import hashlib
import json
from pathlib import Path

import numpy as np

from virtual_cell.interface import Intervention, PredictionRequest, SystemContext
from virtual_cell.signature_retrieval import LIBRARY_SCHEMA, NORM_READOUT, ResponseRungConfig, SciPlexResponseRung


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
    from virtual_cell.signature_retrieval import _skeleton
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
