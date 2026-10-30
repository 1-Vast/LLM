"""Contracts of selective hit triage (maestro.hit_triage): identity, context binding, QC, budgets, seal."""
import random

import pytest

from maestro.campaign_budget import CampaignBudget
from maestro.case_memory import ScientificMeasurementStatus as S
from maestro.hit_triage import (BUDGET_EXCEEDED, CHOICES_MISMATCH, CHOICES_NOT_LOCKED, CONTEXT_MISMATCH, FREEZE_MISMATCH,
                                INSUFFICIENT_LINES, MALFORMED_IDENTITY, SPLIT_LEAK, AssayContext, CompoundIdentity,
                                OutcomeSeal, PairMeasurement, TriageLedger, admit_curves, assert_disjoint, bind, nominate)

PRISM = AssayContext("PRISM", "barcode_abundance", 120, 1, "pooled", "1" * 64)
CTRP = AssayContext("CTRP", "atp_luminescence", 72, 16, "arrayed", "2" * 64)


def test_compound_identity_collapses_salts_and_refuses_malformed_ids():
    a = CompoundIdentity.from_broad_id("BRD-A09722536-002-18-0", "CMSMOCZEIVJLDB", "cyclophosphamide")
    b = CompoundIdentity.from_broad_id("BRD-A09722536-001-01-9")
    c = CompoundIdentity("BRD-K00000001", "CMSMOCZEIVJLDB")          # different core, same structure
    assert a.core == "BRD-A09722536" and a.same_compound(b) and a.same_compound(c)
    assert not b.same_compound(CompoundIdentity("BRD-K00000001"))
    for bad in ("BRD-123", "cyclophosphamide", "brd-a09722536"):
        with pytest.raises(ValueError, match=MALFORMED_IDENTITY):
            CompoundIdentity(bad)
    with pytest.raises(ValueError, match=MALFORMED_IDENTITY):
        CompoundIdentity("BRD-A09722536", "short")


def test_measurements_are_bound_to_their_assay_context():
    m = PairMeasurement(CompoundIdentity("BRD-A09722536"), "ACH-000001", PRISM, -2.4, S.QUALIFIED)
    assert bind(m, PRISM) is m
    with pytest.raises(ValueError, match=CONTEXT_MISMATCH):
        bind(m, CTRP)
    moved = AssayContext("PRISM", "barcode_abundance", 120, 1, "pooled", "3" * 64)   # same name, other source bytes
    with pytest.raises(ValueError, match=CONTEXT_MISMATCH):
        bind(m, moved)
    with pytest.raises(ValueError, match=MALFORMED_IDENTITY):
        PairMeasurement(CompoundIdentity("BRD-A09722536"), "A549", PRISM, -2.4, S.QUALIFIED)
    with pytest.raises(ValueError, match="finite"):
        PairMeasurement(CompoundIdentity("BRD-A09722536"), "ACH-000001", PRISM, float("nan"), S.QUALIFIED)
    assert PairMeasurement(CompoundIdentity("BRD-A09722536"), "CTRP:17", CTRP, float("nan"), S.PLANNED_MISSING).status == S.PLANNED_MISSING


def test_curve_admission_is_a_named_status_never_a_zero():
    assert admit_curves(264, 100) == (S.QUALIFIED, None)
    assert admit_curves(40, 100) == (S.QC_FAILED, INSUFFICIENT_LINES)
    assert admit_curves(0, 100) == (S.PLANNED_MISSING, INSUFFICIENT_LINES)


def test_ledger_books_curves_and_followups_against_shared_budgets():
    ledger = TriageLedger(CampaignBudget(16, 1, 0, "confirmation curve"), CampaignBudget(4, 1, 0, "secondary compound"))
    ledger.book(followups=4, turnarounds=1, label="secondary round")
    ledger.book(curves=16, label="confirmation")
    with pytest.raises(ValueError, match=BUDGET_EXCEEDED):
        ledger.book(curves=1, label="one more curve")
    with pytest.raises(ValueError, match=BUDGET_EXCEEDED):
        ledger.book(followups=1, label="one more secondary")
    assert (ledger.curves, ledger.followups, ledger.turnarounds) == (16, 4, 1) and len(ledger.entries) == 2


def test_nomination_is_capped_and_independent_of_input_order():
    rows = [(5.0, "BRD-A00000001", f"ACH-00000{k}") for k in range(5)] + [(4.0, "BRD-B00000002", "ACH-000009"),
                                                                         (4.0, "BRD-C00000003", "ACH-000008"),
                                                                         (float("nan"), "BRD-D00000004", "ACH-000007")]
    picks = nominate(*zip(*rows), 5, cap=3, salt="s")
    assert sum(c == "BRD-A00000001" for c, _ in picks) == 3 and len(picks) == 5
    assert all(c != "BRD-D00000004" for c, _ in picks)
    for seed in range(5):
        shuffled = rows[:]
        random.Random(seed).shuffle(shuffled)
        assert nominate(*zip(*shuffled), 5, cap=3, salt="s") == picks


def test_outcomes_open_only_for_frozen_code_and_locked_choices():
    import hashlib
    code = b"def arm():\n    return 1\n"
    choices = b'{"nominations": ["BRD-A09722536|ACH-000001"]}\n'
    seal = OutcomeSeal({"arms.py": hashlib.sha256(code).hexdigest()}, hashlib.sha256(choices).hexdigest())
    assert len(seal.release({"arms.py": code.replace(b"\n", b"\r\n")}, choices)) == 64     # CRLF checkout still matches
    with pytest.raises(PermissionError, match=FREEZE_MISMATCH):
        seal.release({"arms.py": code + b"# tuned\n"}, choices)
    with pytest.raises(PermissionError, match=CHOICES_MISMATCH):
        seal.release({"arms.py": code}, choices.replace(b"ACH-000001", b"ACH-000002"))
    with pytest.raises(PermissionError, match=CHOICES_NOT_LOCKED):
        OutcomeSeal({"arms.py": hashlib.sha256(code).hexdigest()}, None).release({"arms.py": code}, choices)


def test_split_leak_is_refused_by_compound_structure_or_family():
    dev = [CompoundIdentity("BRD-A00000001", "AAAAAAAAAAAAAA")]
    family = {"BRD-A00000001": "F1", "BRD-B00000002": "F2", "BRD-C00000003": "F1", "BRD-D00000004": "F3"}
    assert_disjoint(dev, [CompoundIdentity("BRD-B00000002", "BBBBBBBBBBBBBB")], family) is None
    with pytest.raises(ValueError, match=f"{SPLIT_LEAK}:compound"):
        assert_disjoint(dev, [CompoundIdentity("BRD-D00000004", "AAAAAAAAAAAAAA")], family)
    with pytest.raises(ValueError, match=f"{SPLIT_LEAK}:family"):
        assert_disjoint(dev, [CompoundIdentity("BRD-C00000003", "CCCCCCCCCCCCCC")], family)
