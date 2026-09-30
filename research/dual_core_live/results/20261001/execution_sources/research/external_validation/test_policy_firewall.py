"""Typed policy-boundary contracts independent of the replay fixtures."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from maestro.models import BiologicalQuantity, EvidenceAction, EvidenceActionKind

from . import firewall as F


def _action():
    return EvidenceAction(
        identifier="condition-1", description="public assay", cost=1.0,
        distinguishes=("H1", "H2"), kind=EvidenceActionKind.RNA_ABUNDANCE_MEASUREMENT,
        readout="profile", time_hours=24.0,
        quantity=BiologicalQuantity.RNA_ABUNDANCE,
    )


def test_projection_returns_a_closed_typed_policy_input():
    value = F.project_policy_input(
        visible_evidence=({"action": "condition-1", "quality_passed": True},),
        legal_actions=(_action(),), budget=8.0,
        calibrated_action_distributions={"condition-1": {"ambiguous": 1.0}},
        provenance={"source": "frozen-reference"},
    )
    assert F.policy_input_problems(value) == []
    assert value.action_ids == ("condition-1",)
    assert not hasattr(value, "data")


def test_projection_rejects_hidden_truth_fields():
    with pytest.raises(F.PolicyInputViolation, match="evaluator-only"):
        F.project_policy_input(
            visible_evidence=({"action": "condition-1", "truth": "H1"},),
            legal_actions=(_action(),), budget=8.0,
        )


def test_view_projection_copies_only_revealed_profiles():
    import numpy as np

    profile = np.array([1.0, 2.0])
    view = F.Visible()
    view.reveal(("A549", 24.0, 100.0), profile)
    projected = F.project_policy_view(view, legal_actions=(_action(),), budget=8.0)
    profile[0] = 99.0
    assert projected.visible_evidence[0]["profile"][0] == 1.0
    assert F.policy_input_problems(projected) == []
