"""Contracts of the verified evidence registry (maestro.evidence_registry)."""
import pytest

from maestro.case_memory import ScientificMeasurementStatus as S
from maestro.evidence_registry import (CONTEXT_MISMATCH, KIND_NOT_MEASURED, NO_LINEAGE, NO_MEASURED_ROOT, PREDICTION_IN_LINEAGE,
                                       PROTOCOL_MISMATCH, RECEIPT_WITHDRAWN, SOURCE_DIGEST_MISMATCH, SOURCE_MISSING,
                                       canonical_value, holds)
from maestro.models import EvidenceKind as K
from tests.fixtures.strict_evidence import CONTEXT, PROTOCOL, Lab


def _admit(lab, rid, **kw):
    return lab.ledger.admit(rid, CONTEXT, PROTOCOL, **kw)


def test_a_well_formed_digest_does_not_authenticate_missing_or_altered_bytes(tmp_path):
    lab = Lab(tmp_path)
    lab.source("s1", "z\n-3.0\n", experiment="exp1")
    lab.receipt("r1", "s1", "engagement_z", -3.0)
    assert _admit(lab, "r1") == (True, "admitted")
    (tmp_path / "s1.csv").write_bytes(b"z\n-9.0\n")                       # same name, different bytes
    assert _admit(lab, "r1") == (False, SOURCE_DIGEST_MISMATCH)
    (tmp_path / "s1.csv").unlink()
    assert _admit(lab, "r1") == (False, SOURCE_MISSING)


def test_receipt_digest_must_equal_the_registered_digest(tmp_path):
    lab = Lab(tmp_path)
    lab.source("s1", "a", experiment="exp1")
    lab.source("s2", "b", experiment="exp2")
    lab.receipt("r1", "s1", "engagement_z", -3.0)
    forged = lab.ledger.receipt("r1").__class__(**{**lab.ledger.receipt("r1").__dict__, "receipt_id": "r2", "source_sha256": "c" * 64})
    lab.ledger.add(forged)
    assert _admit(lab, "r2") == (False, SOURCE_DIGEST_MISMATCH)


def test_only_measured_kinds_with_a_measured_root_and_no_prediction_ancestor_are_admitted(tmp_path):
    lab = Lab(tmp_path)
    lab.source("meas", "m", experiment="exp1")
    lab.source("pred", "p", experiment="exp1")
    lab.receipt("m", "meas", "x", -3.0)
    lab.receipt("p", "pred", "x", -3.0, kind=K.MODEL_PREDICTION)
    lab.receipt("retrieved", "pred", "x", -3.0, kind=K.RETRIEVED_SOURCE)
    lab.receipt("relabelled", "pred", "x", -3.0, kind=K.DERIVED_ANALYSIS, parents=("p",))     # prediction relabelled as analysis
    lab.receipt("mixed", "pred", "x", -3.0, kind=K.DERIVED_ANALYSIS, parents=("m", "p"))
    lab.receipt("bare_derived", "pred", "x", -3.0, kind=K.DERIVED_ANALYSIS)
    lab.receipt("from_annotation", "pred", "x", -3.0, kind=K.DERIVED_ANALYSIS, parents=("retrieved",))
    assert _admit(lab, "m")[0]
    assert _admit(lab, "p")[1].startswith(KIND_NOT_MEASURED)
    assert _admit(lab, "retrieved")[1].startswith(KIND_NOT_MEASURED)
    assert _admit(lab, "relabelled")[1] == PREDICTION_IN_LINEAGE
    assert _admit(lab, "mixed")[1] == PREDICTION_IN_LINEAGE
    assert _admit(lab, "bare_derived")[1] == NO_LINEAGE
    assert _admit(lab, "from_annotation")[1] == NO_MEASURED_ROOT


def test_status_context_and_protocol_gate_admission(tmp_path):
    lab = Lab(tmp_path)
    lab.source("s", "m", experiment="e")
    lab.receipt("qc", "s", "x", 1.0, status=S.QC_FAILED)
    lab.receipt("planned", "s", "x", 1.0, status=S.PLANNED_MISSING)
    lab.receipt("und", "s", "x", 1.0, status=S.UNDETECTED)
    lab.receipt("ctx", "s", "x", 1.0, context="HeLa:cetsa:1h")
    lab.receipt("proto", "s", "x", 1.0, protocol="study-v0")
    assert _admit(lab, "qc")[1].startswith("STATUS_NOT_ADMITTED")
    assert _admit(lab, "planned")[1].startswith("STATUS_NOT_ADMITTED")
    assert _admit(lab, "und")[0] is False and _admit(lab, "und", allow_undetected=True)[0]
    assert _admit(lab, "ctx")[1].startswith(CONTEXT_MISMATCH)
    assert _admit(lab, "proto")[1].startswith(PROTOCOL_MISMATCH)


def test_independence_is_computed_from_upstream_groups_not_declared(tmp_path):
    lab = Lab(tmp_path)
    lab.source("a1", "run A copy 1", experiment="expA")
    lab.source("a2", "run A reprocessed", experiment="expA")                 # another file, the same experiment
    lab.source("b", "run B", experiment="expB")
    lab.source("db1", "db record 1", publication="paperP")
    lab.source("db2", "db record 2", publication="paperP")                   # copied from the same publication
    lab.source("anon1", "x1")
    lab.source("anon2", "x2")
    for rid, sid in (("ra1", "a1"), ("ra2", "a2"), ("rb", "b"), ("rd1", "db1"), ("rd2", "db2"), ("rn1", "anon1"), ("rn2", "anon2")):
        lab.receipt(rid, sid, "x", -3.0)
    groups = lambda *ids: lab.ledger.independent_groups(ids)
    assert groups("ra1") == groups("ra1", "ra2") == groups("ra1", "ra1", "ra2")      # duplication adds nothing
    assert len(groups("ra1", "rb")) == 2
    assert len(groups("rd1", "rd2")) == 1
    assert len(groups("rn1", "rn2")) == 1                                           # unattributed sources are not shown independent
    lab.receipt("analysis", "a1", "x", -2.0, kind=K.DERIVED_ANALYSIS, parents=("ra1", "ra2"))
    assert groups("analysis") == groups("ra1")                                      # an analysis inherits its measurement's group
    assert groups("ra1", "rb", "analysis") == groups("rb", "ra2")                   # order-free


def test_withdrawal_and_broken_parents_invalidate_dependants(tmp_path):
    lab = Lab(tmp_path)
    lab.source("s", "m", experiment="e")
    lab.receipt("m", "s", "x", -3.0)
    lab.receipt("d", "s", "x", -3.0, kind=K.DERIVED_ANALYSIS, parents=("m",))
    assert _admit(lab, "d")[0]
    lab.ledger.withdraw("m", "plate failed re-QC")
    assert lab.ledger.authenticate("m") == (False, RECEIPT_WITHDRAWN)
    assert lab.ledger.authenticate("d")[1].startswith("PARENT_REFUSED:m")
    with pytest.raises(ValueError):
        lab.ledger.withdraw("d", " ")


def test_units_convert_by_division_so_boundaries_classify_alike():
    assert canonical_value(50.0, "percent") == canonical_value(0.5, "fraction") == ("viability_fraction", 0.5)
    for percent in (29.0, 33.0, 57.0, 58.0, 70.0, 1.1):
        assert holds(canonical_value(percent, "percent")[1], "<=", canonical_value(percent / 100.0, "fraction")[1])
        assert holds(canonical_value(percent, "percent")[1], ">=", canonical_value(percent / 100.0, "fraction")[1])
    assert holds(0.5, "<=", 0.5) and not holds(0.5, "<", 0.5) and not holds(0.5, ">", 0.5)
    with pytest.raises(ValueError, match="UNIT_UNKNOWN"):
        canonical_value(1.0, "furlongs")
