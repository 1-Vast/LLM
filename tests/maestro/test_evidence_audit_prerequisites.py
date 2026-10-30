"""Two evidence-audit prerequisites: unknown source dependence, and unsited engagement premises."""
from __future__ import annotations



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
