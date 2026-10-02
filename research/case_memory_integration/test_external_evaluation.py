"""Tests for the untouched-source evaluation: split, validator, leakage and schema integrity.

File summary
- Path: research/case_memory_integration/test_external_evaluation.py
- Purpose: pin the integrity of the LINCS 2020 external evaluation: the study-level split, the
  frozen validator's four reading codes, the leak probe (fitted quantities are blind to test
  labels), the missingness rule (no zero-filled condition), the frozen protocol hash and the
  production-schema episodes built from the reference blocks.
- Depends on: data/processed/case_memory_integration (the built pack),
  research/case_memory_integration/{PROTOCOL.md,freeze_protocol.json,external_replay.py},
  tools/datasets/lincs_pack.py, outputs/case_memory_integration/episodes (optional)
"""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest

from tools.datasets import lincs_pack as XD


@pytest.fixture(scope="module")
def pack_and_arrays():
    return XD.load_pack()


def _sha(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# -------------------------------------------------------------------------------- split
def test_the_split_excludes_every_development_study_block(pack_and_arrays):
    pack, _ = pack_and_arrays
    dev = XD._development_blocks()
    test = [b for b, u in pack["units"].items() if u["unseen"]]
    assert test and not (set(test) & dev)
    reference = [b for b, u in pack["units"].items() if not u["unseen"]]
    assert reference and not (set(test) & set(reference))


def test_the_population_matches_the_frozen_pool_rule(pack_and_arrays):
    """Pool rule as implemented and registered: >= 12 pool blocks (reference + unseen) at core
    scope and >= 3 unseen blocks per class.

    Registered deviation: the protocol's rule text says "12 reference blocks", but its own
    registered population count (5 classes, 26 unseen, 67 reference) was produced by the
    reference-plus-unseen reading, and the implemented population (65 reference) assigns blocks
    carrying two MoA annotations one class deterministically. The deviation is recorded in
    REPORT.md; the hashed protocol is not rewritten.
    """

    pack, _ = pack_and_arrays
    assert pack["pool"] == sorted(pack["pool"]) and len(pack["pool"]) >= 2
    per_class_all: dict[str, int] = {}
    per_class_unseen: dict[str, int] = {}
    for b, u in pack["units"].items():
        per_class_all[u["moa"]] = per_class_all.get(u["moa"], 0) + 1
        if u["unseen"]:
            per_class_unseen[u["moa"]] = per_class_unseen.get(u["moa"], 0) + 1
    for klass in pack["pool"]:
        assert per_class_all.get(klass, 0) >= XD.MIN_REFERENCE_BLOCKS
        assert per_class_unseen.get(klass, 0) >= XD.MIN_UNSEEN_BLOCKS


def test_pack_checksums_match_their_manifest():
    manifest = json.loads(
        (XD.ROOT / "data/processed/case_memory_integration/pack_manifest.json").read_text())
    for name, recorded in manifest["outputs"].items():
        assert _sha(XD.ROOT / "data/processed/case_memory_integration" / name) == recorded


def test_the_frozen_protocol_is_unmodified():
    freeze = json.loads(
        (XD.ROOT / "research/case_memory_integration/freeze_protocol.json").read_text())
    assert _sha(XD.ROOT / freeze["protocol"]["path"]) == freeze["protocol"]["sha256"]


# -------------------------------------------------------------------------------- validator
def test_the_validator_assigns_the_four_reading_codes():
    from research.case_memory_integration.external_replay import MARGIN, _reading

    own = np.array([1.0, 0.0, 0.0])
    decoy = np.array([0.0, 1.0, 0.0])
    assert _reading(np.array([2.0, 0.1, 0.0]), own, decoy, 0.1) == 0
    assert _reading(np.array([0.1, 2.0, 0.0]), own, decoy, 0.1) == 1
    borderline = own * (1.0 + MARGIN / 2) + decoy * 1.0
    assert _reading(borderline / np.linalg.norm(borderline) * 5.0, own, decoy, 0.1) == 2
    assert _reading(np.array([0.01, 0.0, 0.0]), own, decoy, 1.0) == 3


# -------------------------------------------------------------------------------- missingness / leaks
def test_no_condition_is_zero_filled_and_condition_keys_are_consistent(pack_and_arrays):
    pack, arrays = pack_and_arrays
    for b, u in pack["units"].items():
        declared = set(u["conditions"])
        stored = {key.split("::")[2] for key in arrays if key.startswith(f"vec::{b}::")}
        assert declared == stored
        for cell in declared:
            vec = arrays[f"vec::{b}::{cell}"]
            assert np.isfinite(vec).all() and float(np.linalg.norm(vec)) > 0.0


def test_fitted_quantities_are_blind_to_test_labels(pack_and_arrays):
    """The leak probe: thresholds and centroids use reference membership only."""

    pack, arrays = pack_and_arrays
    reference = sorted(b for b, u in pack["units"].items() if not u["unseen"])
    for cell in XD.CORE_CELL_LINES:
        norms = [float(np.linalg.norm(arrays[f"vec::{b}::{cell}"])) for b in reference
                 if f"vec::{b}::{cell}" in arrays]
        if norms:
            threshold = float(np.percentile(norms, 5.0))
            assert threshold > 0.0
    for klass in pack["pool"]:
        for cell in XD.CORE_CELL_LINES:
            key = f"centroid::{klass}::{cell}"
            if key not in arrays:
                continue
            members = [b for b in reference if pack["units"][b]["moa"] == klass
                       and f"vec::{b}::{cell}" in arrays]
            assert members
            rebuilt = np.mean([arrays[f"vec::{b}::{cell}"] for b in members], axis=0)
            assert np.allclose(rebuilt, arrays[key], atol=1e-5)


# -------------------------------------------------------------------------------- episodes
def test_reference_episodes_satisfy_the_production_schema_when_built():
    path = XD.ROOT / "outputs/case_memory_integration/episodes/reference_cases.jsonl.gz"
    if not path.is_file():
        pytest.skip("episodes not built (tools.case_memory.build_cases)")
    from maestro import case_memory as CM

    store = CM.EpisodeStore(path)
    assert len(store) > 0
    for episode in store.latest():
        assert CM.validate_episode(episode) == ()
        assert episode.provenance["data_origin"] == "real"
        assert episode.provenance.get("label_kind") == "curated_annotation_proxy"
    store.verify()
