"""Two evidence-audit prerequisites: unknown source dependence, and unsited engagement premises.

File summary
- Path: tests/test_evidence_audit_prerequisites.py
- Purpose: pin the block-4 audit rows E3 and E5 (research/gated_plan/AUDIT.md) as reported
  properties, without changing any production default. An unregistered source is dependence-
  unknown, not independent; an engagement premise without a sample site can be met by a lysate
  grant of the same quantity and context, and the case lint names such premises.
- Run: python -m pytest tests/test_evidence_audit_prerequisites.py -q
"""
from __future__ import annotations

from pathlib import Path

import pytest

from maestro.models import BiologicalQuantity, PremiseGrant, PremiseRequirement
from maestro.handoff import SourceCluster, SourceClusterIndex


def test_unregistered_citations_are_dependence_unknown_not_independent():
    index = SourceClusterIndex()
    citations = ("paper:a:table2", "review:b:figure1")
    assert index.count_independent(citations) == 2  # the historical count, unchanged
    report = index.independence(citations)
    assert report["independent_clusters"] == frozenset()
    assert report["dependence_unknown"] == frozenset(citations)
    index.register(SourceCluster("experiment:1", frozenset(citations)))
    report = index.independence(citations)
    assert report["independent_clusters"] == frozenset({"experiment:1"})
    assert report["dependence_unknown"] == frozenset()


def test_an_unsited_engagement_premise_accepts_a_lysate_grant():
    context = "ACH-000551:K562"
    unsited = PremiseRequirement("engagement:index_on_target", quantity=BiologicalQuantity.ENGAGEMENT_SHIFT,
                                 context_identifier=context)
    sited = PremiseRequirement("engagement:index_on_target", quantity=BiologicalQuantity.ENGAGEMENT_SHIFT,
                               context_identifier=context, site="intact_cell")
    lysate = PremiseGrant("engagement:index_on_target", "lysate_thermal_shift",
                          quantity=BiologicalQuantity.ENGAGEMENT_SHIFT, site="lysate", context_identifier=context,
                          quality_passed=True)
    assert unsited.unmet_reasons(lysate) == ()
    assert any(reason.startswith("site_mismatch") for reason in sited.unmet_reasons(lysate))


def test_the_case_lint_names_unsited_engagement_premises_in_the_engagement_package():
    public = Path("data/evaluation/cases/engagement_v1/public")
    private = Path("data/evaluation/cases/engagement_v1/private")
    if not public.is_dir():
        pytest.skip("engagement_v1 package unavailable")
    from tools.evaluation.cases import CaseRepository
    cases = CaseRepository(public, private).load()
    assert cases
    for case, _ in cases:
        flagged = case.public.unsited_engagement_premises()
        assert "engagement:index_on_target" in flagged
        assert "abundance:target_rna" not in flagged
