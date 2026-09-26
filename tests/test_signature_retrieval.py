"""Signature retrieval ranks measured reference classes and refuses what it cannot compare.

File summary
- Path: tests/test_signature_retrieval.py
- Purpose: pin the retrieval analysis behind `tools/signature_retrieval/` on a synthetic,
  digest-bound library, so the test needs no local asset.
- Core points: a query shaped like one class ranks that class first and beats the permutation
  null; centering on the library's shared response is applied to uncentered queries only;
  unsupported lines, too few genes, a missing or tampered library are refused by name.
- Interfaces: `test_*` functions only.
- Depends on: virtual_cell.signature_retrieval
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from virtual_cell.signature_retrieval import LIBRARY_SCHEMA, load_library, signature_retrieval

GENES = [f"G{i}" for i in range(300)]
LINES = ["A549", "MCF7"]


def _library(directory: Path) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(1)
    shared = rng.normal(0, 0.5, len(GENES))           # the response most compounds share
    directions = {c: rng.normal(0, 1, len(GENES)) for c in ("HDAC", "HSP90", "MEK")}
    compounds, profiles, ec, el, ed = [], [], [], [], []
    for label, direction in directions.items():
        for k in range(3):
            compounds.append({"name": f"{label}-{k}", "skeleton": f"SK{label}{k}", "class": label})
            for li, _ in enumerate(LINES):
                profiles.append(shared + direction + rng.normal(0, 0.3, len(GENES)))
                ec.append(len(compounds) - 1)
                el.append(li)
                ed.append(0)
    profiles = np.asarray(profiles, dtype=np.float32)
    systematic = np.stack([[profiles[np.asarray(el) == li].mean(0)] for li in range(len(LINES))]).astype(np.float32)
    directory.mkdir(parents=True, exist_ok=True)
    np.savez(directory / "library.npz", profiles=profiles, entry_compound=np.asarray(ec), entry_line=np.asarray(el),
             entry_dose=np.asarray(ed), systematic=systematic)
    meta = {"schema": LIBRARY_SCHEMA, "genes": GENES, "lines": LINES, "doses": [10000.0], "compounds": compounds,
            "arrays_sha256": hashlib.sha256((directory / "library.npz").read_bytes()).hexdigest(),
            "source": "synthetic", "validation": {"top1_agreement": None}, "created": "test"}
    (directory / "library.json").write_text(json.dumps(meta), encoding="utf-8")
    return {"shared": shared, **directions}


def _query(tmp_path: Path, genes: dict, **extra) -> Path:
    path = tmp_path / "query.json"
    body = {"schema_version": "1.0", "signatures": [{"context": "MCF7", "dose_nM": 10000, "genes": genes}], **extra}
    path.write_text(json.dumps(body), encoding="utf-8")
    return path


def test_a_query_shaped_like_one_class_ranks_that_class_first(tmp_path):
    parts = _library(tmp_path / "lib")
    vector = parts["shared"] + parts["HSP90"] + np.random.default_rng(9).normal(0, 0.3, len(GENES))
    result = signature_retrieval({"dataset_path": str(_query(tmp_path, dict(zip(GENES, vector.tolist()))))},
                                 library_directory=tmp_path / "lib")
    payload = result["payload"]
    assert payload["ranking"][0]["class"] == "HSP90"
    assert payload["permutation_null"]["best_above_null"] is True
    assert payload["evidence_kind"] == "derived_analysis" and not payload["rejected"]
    assert any("not a mechanism" in text for text in result["limitations"])


def test_centering_is_applied_exactly_once(tmp_path):
    """A raw signature and the same signature already centered by the caller rank identically."""

    parts = _library(tmp_path / "lib")
    library = load_library(tmp_path / "lib")
    raw = parts["shared"] + parts["MEK"] + np.random.default_rng(3).normal(0, 0.3, len(GENES))
    first = signature_retrieval({"dataset_path": str(_query(tmp_path, dict(zip(GENES, raw.tolist()))))},
                                library_directory=tmp_path / "lib")["payload"]
    centered = raw - library.systematic[1, 0]
    body = {"schema_version": "1.0", "signatures": [
        {"context": "MCF7", "dose_nM": 10000, "centered": True, "genes": dict(zip(GENES, centered.tolist()))}]}
    path = tmp_path / "centered.json"
    path.write_text(json.dumps(body))
    second = signature_retrieval({"dataset_path": str(path)}, library_directory=tmp_path / "lib")["payload"]
    assert first["ranking"][0]["class"] == second["ranking"][0]["class"] == "MEK"
    assert first["ranking"][0]["best_cosine"] == pytest.approx(second["ranking"][0]["best_cosine"], abs=1e-4)


def test_a_compound_can_be_excluded_from_its_own_reference_set(tmp_path):
    parts = _library(tmp_path / "lib")
    library = load_library(tmp_path / "lib")
    own = library.profile(0, 1, 0)  # HDAC-0 in MCF7, exactly as measured
    query = _query(tmp_path, dict(zip(GENES, own.tolist())), exclude_reference_compounds=["HDAC-0"])
    payload = signature_retrieval({"dataset_path": str(query)}, library_directory=tmp_path / "lib")["payload"]
    assert all(item["compound"] != "HDAC-0" for item in payload["nearest"])
    assert payload["ranking"][0]["class"] == "HDAC"


def test_unsupported_input_is_refused_by_name(tmp_path):
    _library(tmp_path / "lib")
    body = {"schema_version": "1.0", "signatures": [{"context": "K562", "dose_nM": 10000, "genes": {"G1": 1.0}}]}
    path = tmp_path / "k562.json"
    path.write_text(json.dumps(body))
    payload = signature_retrieval({"dataset_path": str(path)}, library_directory=tmp_path / "lib")["payload"]
    assert payload["rejected"][0]["reason"] == "context_not_in_library:K562"
    few = _query(tmp_path, {g: 1.0 for g in GENES[:50]})
    payload = signature_retrieval({"dataset_path": str(few)}, library_directory=tmp_path / "lib")["payload"]
    assert payload["rejected"][0]["reason"].startswith("too_few_library_genes_matched:50<")
    missing = signature_retrieval({"dataset_path": str(few)}, library_directory=tmp_path / "absent")["payload"]
    assert missing["rejected"] == [{"reason": "signature_library_missing"}]


def test_a_tampered_library_is_refused(tmp_path):
    _library(tmp_path / "lib")
    arrays = tmp_path / "lib" / "library.npz"
    arrays.write_bytes(arrays.read_bytes() + b"x")
    with pytest.raises(ValueError, match="digest_mismatch"):
        load_library(tmp_path / "lib")


ROOT = Path(__file__).resolve().parents[1]
LIBRARY_DIR = ROOT / "data/virtual_cell/sciplex3_signature_library"


@pytest.mark.skipif(not (LIBRARY_DIR / "library.json").is_file(), reason="needs the local SciPlex3 signature library")
def test_a_held_out_hsp90_inhibitor_retrieves_its_class_from_the_real_library(tmp_path):
    library = load_library(LIBRARY_DIR)
    names = [c["name"] for c in library.compounds]
    index = names.index("Luminespib (AUY-922, NVP-AUY922)")
    signatures = [{"context": line, "dose_nM": 10000,
                   "genes": dict(zip(library.genes, map(float, library.profile(index, i, 3))))}
                  for i, line in enumerate(library.lines)]
    path = tmp_path / "luminespib.json"
    path.write_text(json.dumps({"schema_version": "1.0", "signatures": signatures,
                                "exclude_reference_compounds": [names[index]]}), encoding="utf-8")
    payload = signature_retrieval({"dataset_path": str(path)})["payload"]
    assert payload["ranking"][0]["class"] == "HSP90 activity"
    assert payload["permutation_null"]["best_above_null"] is True
    assert payload["library"]["validation"]["top1_agreement_with_vendor_annotation"]["mean"] == 0.5


def test_malformed_input_raises(tmp_path):
    _library(tmp_path / "lib")
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"schema_version": "1.0", "signatures": [], "surprise": 1}))
    with pytest.raises(ValueError):
        signature_retrieval({"dataset_path": str(path)}, library_directory=tmp_path / "lib")
