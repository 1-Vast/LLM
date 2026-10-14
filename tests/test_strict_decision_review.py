"""Contracts of the strict decision review (maestro.strict_decision_review) and its metamorphic invariants."""
import itertools

import pytest

from maestro.case_memory import ScientificMeasurementStatus as S
from maestro.decision_review import APPROVAL_MISMATCH, SELF_APPROVAL, DiscriminatingExperiment, EvidenceItem, Explanation, Prediction, review
from maestro.models import EvidenceKind as K
from maestro.strict_decision_review import (NO_DISCRIMINATING_EXPERIMENT, Limitation, NoSignalRule, Role, StrictExplanation,
                                            StrictPolicy, StrictPrediction, StrictStatus, approve_basis, certificate_problems,
                                            strict_review)
from tests.fixtures.strict_evidence import CONTEXT, Lab

MENU = (DiscriminatingExperiment("cetsa", "engagement_z", cost=2), DiscriminatingExperiment("rescue", "rescue_fraction", cost=3))
POLICY = StrictPolicy("study-v1", min_independent_groups=1,
                      no_signal_rules=(NoSignalRule("sel_flat", "selective_z", ">", -1.0, "z"),))


def explanations(exclude=True):
    target = StrictExplanation("TARGET", "engages the target", (
        StrictPrediction("engage", "engagement_z", "<=", -2.0, "z"),
        StrictPrediction("rescue", "rescue_fraction", ">=", 0.5, "fraction"),
        StrictPrediction("opt_phenotype", "phenotype_z", "<=", -1.0, "z", Role.SUPPORTIVE)), progression=True)
    off = StrictExplanation("OFF", "acts off target", (StrictPrediction("off_engage", "engagement_z", ">", -1.0, "z"),))
    return (target, off)


def lab_with(tmp_path, **spec):
    lab = Lab(tmp_path)
    for i, (rid, (obs, value, unit)) in enumerate(spec.items()):
        lab.source(f"s{i}", f"data {rid}", experiment=f"exp_{rid}")
        lab.receipt(rid, f"s{i}", obs, value, unit=unit, rule={"engagement_z": "engage", "rescue_fraction": "rescue"}.get(obs, obs))
    return lab


def sub(root, name):
    path = root / name
    path.mkdir()
    return path


def run(lab, expl=None, **kw):
    kw.setdefault("funded", True)
    return strict_review("cand", expl or explanations(), lab.ledger, POLICY, context=CONTEXT, menu=MENU, **kw)


def test_historical_review_semantics_are_unchanged():
    ctx = "assay:A"
    expl = (Explanation("T", "t", (Prediction("a", "<=", -2.0), Prediction("b", ">=", 0.5)), progression=True),
            Explanation("O", "o", (Prediction("a", ">", -1.0),)))
    item = EvidenceItem("a", -3.0, K.REAL_MEASUREMENT, S.QUALIFIED, ctx, "x.csv", "0" * 64)
    assert review("c", expl, [item], context=ctx, funded=True).status.value == "GO"          # one of two predictions untested
    assert review("c", expl, [], context=ctx, funded=True, no_signal=True).status.value == "NO_GO"


def test_a_boolean_or_unknown_receipt_cannot_authorize_no_go(tmp_path):
    lab = Lab(tmp_path)
    d = run(lab, no_signal_receipt="nope", no_signal_rule="sel_flat")
    assert d.status is StrictStatus.NEED_MORE_EVIDENCE
    assert any(x.startswith("NO_SIGNAL_REFUSED:RECEIPT_UNKNOWN") for x in d.limitations)
    d = run(lab, no_signal_receipt=None, no_signal_rule="sel_flat")
    assert d.status is StrictStatus.NEED_MORE_EVIDENCE


def test_no_go_needs_an_authenticated_in_context_receipt_that_satisfies_the_registered_rule(tmp_path):
    lab = Lab(tmp_path)
    lab.source("s", "flat screen", experiment="e")
    lab.receipt("flat", "s", "selective_z", -0.2, rule="sel_flat")
    d = run(lab, no_signal_receipt="flat", no_signal_rule="sel_flat")
    assert d.status is StrictStatus.NO_GO and d.reasons == ("NO_SELECTIVE_SIGNAL:sel_flat",)
    lab.receipt("strong", "s", "selective_z", -3.0, rule="sel_flat")                             # signal present -> not a no-signal finding
    assert run(lab, no_signal_receipt="strong", no_signal_rule="sel_flat").status is StrictStatus.NEED_MORE_EVIDENCE
    lab.receipt("wrongctx", "s", "selective_z", -0.2, rule="sel_flat", context="HeLa:other")
    assert run(lab, no_signal_receipt="wrongctx", no_signal_rule="sel_flat").status is not StrictStatus.NO_GO
    lab.receipt("pred", "s", "selective_z", -0.2, rule="sel_flat", kind=K.MODEL_PREDICTION)
    assert run(lab, no_signal_receipt="pred", no_signal_rule="sel_flat").status is not StrictStatus.NO_GO
    assert run(lab, no_signal_receipt="flat", no_signal_rule="unregistered_rule").status is not StrictStatus.NO_GO
    (tmp_path / "s.csv").write_bytes(b"tampered")                                              # bytes no longer match the registry
    assert run(lab, no_signal_receipt="flat", no_signal_rule="sel_flat").status is not StrictStatus.NO_GO


def test_undetected_status_is_admitted_only_for_a_registered_no_signal_rule(tmp_path):
    lab = Lab(tmp_path)
    lab.source("s", "below detection", experiment="e")
    lab.receipt("und", "s", "selective_z", 0.0, status=S.UNDETECTED, rule="sel_flat")
    assert run(lab, no_signal_receipt="und", no_signal_rule="sel_flat").status is StrictStatus.NO_GO
    lab.receipt("und_pred", "s", "engagement_z", -9.0, status=S.UNDETECTED, rule="engage")
    assert run(lab).results["TARGET"]["engage[required] engagement_z <= -2 z"] == "untested"


def test_one_supported_prediction_is_not_enough_for_go(tmp_path):
    lab = lab_with(tmp_path, e1=("engagement_z", -3.0, "z"))
    d = run(lab)
    assert d.status is StrictStatus.NEED_MORE_EVIDENCE
    assert "UNTESTED:rescue" in d.reasons and d.experiment == MENU[0]      # only engagement_z is predicted incompatibly by two explanations


def test_optional_predictions_may_stay_untested_but_required_ones_may_not(tmp_path):
    lab = lab_with(tmp_path, e1=("engagement_z", -3.0, "z"), r1=("rescue_fraction", 0.8, "fraction"),
                   off=("engagement_z", -3.0, "z"))
    lab.receipt("exclude_off", "s0", "engagement_z", -3.0, rule="off_engage")                 # contradicts the competitor (needs > -1)
    d = run(lab)
    assert d.status is StrictStatus.AWAITING_APPROVAL
    assert any(x.startswith("supportive_untested:opt_phenotype") for x in d.limitations)


def test_go_needs_a_human_approval_bound_to_the_evidence_basis(tmp_path):
    lab = lab_with(tmp_path, e1=("engagement_z", -3.0, "z"), r1=("rescue_fraction", 0.8, "fraction"))
    lab.receipt("exclude_off", "s0", "engagement_z", -3.0, rule="off_engage")
    pending = run(lab)
    assert pending.status is StrictStatus.AWAITING_APPROVAL
    with pytest.raises(PermissionError, match=SELF_APPROVAL):
        approve_basis(pending.basis_sha256, "agent")
    wrong = approve_basis("0" * 64, "Dr. Rivera")
    assert APPROVAL_MISMATCH in run(lab, approval=wrong).limitations
    assert run(lab, approval=wrong).status is StrictStatus.AWAITING_APPROVAL
    go = run(lab, approval=approve_basis(pending.basis_sha256, "Dr. Rivera"))
    assert go.status is StrictStatus.GO and go.approver == "Dr. Rivera" and certificate_problems(go, lab.ledger) == []


def test_unfunded_and_unresolved_critical_limitations_block_go(tmp_path):
    lab = lab_with(tmp_path, e1=("engagement_z", -3.0, "z"), r1=("rescue_fraction", 0.8, "fraction"))
    lab.receipt("exclude_off", "s0", "engagement_z", -3.0, rule="off_engage")
    assert run(lab, funded=False).status is StrictStatus.NEED_MORE_EVIDENCE
    critical = Limitation("OFFTARGET_PANEL", "no off-target panel yet", critical=True)
    d = run(lab, limitations=(critical,))
    assert d.status is StrictStatus.NEED_MORE_EVIDENCE and "CRITICAL_LIMITATION:OFFTARGET_PANEL" in d.reasons
    lab.source("panel", "panel result", experiment="exp_panel")
    lab.receipt("panel_ok", "panel", "offtarget_panel_hits", 0.0, unit="count")
    resolved = Limitation("OFFTARGET_PANEL", "no off-target panel yet", critical=True, resolved_by="panel_ok")
    assert run(lab, limitations=(resolved,)).status is StrictStatus.AWAITING_APPROVAL
    lab.ledger.withdraw("panel_ok", "panel re-run failed QC")
    assert run(lab, limitations=(resolved,)).status is StrictStatus.NEED_MORE_EVIDENCE


def test_a_model_prediction_alone_cannot_certify_engagement_or_replace_a_missing_assay(tmp_path):
    lab = Lab(tmp_path)
    lab.source("sim", "virtual cell output", experiment="vc")
    lab.receipt("synthetic_engage", "sim", "engagement_z", -9.0, kind=K.MODEL_PREDICTION, rule="engage")
    lab.receipt("synthetic_rescue", "sim", "rescue_fraction", 1.0, kind=K.DERIVED_ANALYSIS, rule="rescue", parents=("synthetic_engage",))
    d = run(lab)
    assert d.status is StrictStatus.NEED_MORE_EVIDENCE and d.binding == {}
    assert any("PREDICTION_IN_LINEAGE" in x or "KIND_NOT_MEASURED" in x for x in d.limitations)


def test_measured_contradiction_of_a_required_prediction_is_a_named_no_go(tmp_path):
    lab = lab_with(tmp_path, e1=("engagement_z", -0.3, "z"))
    d = run(lab)
    assert d.status is StrictStatus.NO_GO and d.reasons == ("CONTRADICTED:engage",)


def test_conflicting_independent_measurements_are_not_a_go_and_not_a_no_go(tmp_path):
    lab = lab_with(tmp_path, e1=("engagement_z", -3.0, "z"), e2=("engagement_z", -0.3, "z"))
    d = run(lab)
    assert d.status is StrictStatus.NEED_MORE_EVIDENCE and "CONFLICTED:engage" in d.reasons


def test_no_feasible_experiment_is_a_named_state_not_an_exception(tmp_path):
    d = strict_review("cand", explanations(), Lab(tmp_path).ledger, POLICY, context=CONTEXT, funded=True, menu=())
    assert d.status is StrictStatus.NEED_MORE_EVIDENCE and NO_DISCRIMINATING_EXPERIMENT in d.reasons and d.experiment is None


def test_duplicating_upstream_evidence_does_not_create_independent_support(tmp_path):
    policy = StrictPolicy("study-v1", min_independent_groups=2)
    lab = Lab(tmp_path)
    for i in range(3):                                                                        # three files, one experiment
        lab.source(f"s{i}", f"copy {i}", experiment="expA")
        lab.receipt(f"e{i}", f"s{i}", "engagement_z", -3.0, rule="engage")
        lab.receipt(f"r{i}", f"s{i}", "rescue_fraction", 0.8, unit="fraction", rule="rescue")
        lab.receipt(f"o{i}", f"s{i}", "engagement_z", -3.0, rule="off_engage")
    d = strict_review("c", explanations(), lab.ledger, policy, context=CONTEXT, funded=True, menu=MENU)
    assert d.status is StrictStatus.NEED_MORE_EVIDENCE
    assert any(x.startswith("insufficient_independent_groups") for x in d.limitations)
    lab.source("sB", "second experiment", experiment="expB")
    lab.receipt("eB", "sB", "engagement_z", -2.5, rule="engage")
    lab.receipt("rB", "sB", "rescue_fraction", 0.7, unit="fraction", rule="rescue")
    lab.receipt("oB", "sB", "engagement_z", -2.5, rule="off_engage")
    assert strict_review("c", explanations(), lab.ledger, policy, context=CONTEXT, funded=True, menu=MENU).status is StrictStatus.AWAITING_APPROVAL


def test_reordering_source_records_does_not_change_the_decision(tmp_path):
    specs = [("e1", "engagement_z", -3.0, "z", "engage"), ("r1", "rescue_fraction", 0.8, "fraction", "rescue"),
             ("o1", "engagement_z", -3.0, "z", "off_engage"), ("e2", "engagement_z", -2.4, "z", "engage")]
    digests = set()
    for k, order in enumerate(itertools.islice(itertools.permutations(specs), 12)):
        lab = Lab(sub(tmp_path, f"p{k}"))
        for rid, obs, value, unit, rule in order:
            lab.source(f"src_{rid}", f"body {rid}", experiment=f"exp_{rid}")
            lab.receipt(rid, f"src_{rid}", obs, value, unit=unit, rule=rule)
        d = run(lab)
        digests.add((d.status, d.reasons, d.basis_sha256, tuple(sorted(d.binding))))
    assert len(digests) == 1


def test_withdrawing_or_altering_a_required_receipt_invalidates_the_go_certificate(tmp_path):
    lab = lab_with(tmp_path, e1=("engagement_z", -3.0, "z"), r1=("rescue_fraction", 0.8, "fraction"))
    lab.receipt("exclude_off", "s0", "engagement_z", -3.0, rule="off_engage")
    go = run(lab, approval=approve_basis(run(lab).basis_sha256, "Dr. Rivera"))
    assert go.status is StrictStatus.GO
    lab.ledger.withdraw("r1", "assay plate contamination")
    assert any("RECEIPT_WITHDRAWN" in p for p in certificate_problems(go, lab.ledger))
    assert run(lab).status is StrictStatus.NEED_MORE_EVIDENCE                                   # re-review no longer reaches GO
    lab2 = lab_with(sub(tmp_path, "second"), e1=("engagement_z", -3.0, "z"), r1=("rescue_fraction", 0.8, "fraction"))
    lab2.receipt("exclude_off", "s0", "engagement_z", -3.0, rule="off_engage")
    go2 = run(lab2, approval=approve_basis(run(lab2).basis_sha256, "Dr. Rivera"))
    (tmp_path / "second" / "s1.csv").write_bytes(b"edited after sign-off")
    assert any("SOURCE_DIGEST_MISMATCH" in p for p in certificate_problems(go2, lab2.ledger))


def test_declared_unit_conversion_preserves_the_scientific_classification(tmp_path):
    for value, unit in ((0.8, "fraction"), (80.0, "percent")):
        lab = lab_with(sub(tmp_path, unit), e1=("engagement_z", -3.0, "z"), r1=("rescue_fraction", value, unit))
        lab.receipt("exclude_off", "s0", "engagement_z", -3.0, rule="off_engage")
        assert run(lab).status is StrictStatus.AWAITING_APPROVAL
    lab = lab_with(sub(tmp_path, "boundary"), e1=("engagement_z", -3.0, "z"), r1=("rescue_fraction", 50.0, "percent"))
    assert run(lab).results["TARGET"]["rescue[required] rescue_fraction >= 0.5 fraction"] == "supported"   # exactly on the boundary
    lab = lab_with(sub(tmp_path, "dim"), e1=("engagement_z", -3.0, "z"), r1=("rescue_fraction", 0.8, "z"))
    assert run(lab).results["TARGET"]["rescue[required] rescue_fraction >= 0.5 fraction"] == "untested"


def test_policy_refuses_a_progression_explanation_with_no_required_prediction(tmp_path):
    only_optional = StrictExplanation("T", "t", (StrictPrediction("p", "engagement_z", "<=", -2.0, "z", Role.SUPPORTIVE),), progression=True)
    with pytest.raises(ValueError, match="REQUIRED"):
        strict_review("c", (only_optional, explanations()[1]), Lab(tmp_path).ledger, POLICY, context=CONTEXT, funded=True)


def test_a_competing_explanation_must_be_excluded_by_a_qualified_measurement_unless_the_policy_waives_it(tmp_path):
    lab = lab_with(tmp_path, e1=("engagement_z", -3.0, "z"), r1=("rescue_fraction", 0.8, "fraction"))
    d = run(lab)                                                                              # supported, but OFF is never contradicted
    assert d.status is StrictStatus.NEED_MORE_EVIDENCE and "ALTERNATIVE_NOT_EXCLUDED:OFF" in d.reasons
    waived = StrictPolicy("study-v1", exclude_alternatives=False)
    d = strict_review("c", explanations(), lab.ledger, waived, context=CONTEXT, funded=True, menu=MENU)
    assert d.status is StrictStatus.AWAITING_APPROVAL


def test_an_approval_naming_an_automated_actor_is_refused_even_if_built_by_hand(tmp_path):
    from maestro.decision_review import Approval
    lab = lab_with(tmp_path, e1=("engagement_z", -3.0, "z"), r1=("rescue_fraction", 0.8, "fraction"))
    lab.receipt("exclude_off", "s0", "engagement_z", -3.0, rule="off_engage")
    basis = run(lab).basis_sha256
    d = run(lab, approval=Approval(basis, "agent"))
    assert d.status is StrictStatus.AWAITING_APPROVAL and SELF_APPROVAL in d.limitations


def test_the_alternative_waiver_is_part_of_the_basis_an_approval_binds_to(tmp_path):
    lab = lab_with(tmp_path, e1=("engagement_z", -3.0, "z"), r1=("rescue_fraction", 0.8, "fraction"))
    lab.receipt("exclude_off", "s0", "engagement_z", -3.0, rule="off_engage")
    strict = run(lab)
    waived = strict_review("cand", explanations(), lab.ledger, StrictPolicy("study-v1", exclude_alternatives=False, no_signal_rules=POLICY.no_signal_rules),
                           context=CONTEXT, funded=True, menu=MENU)
    assert strict.status is waived.status is StrictStatus.AWAITING_APPROVAL
    assert strict.basis_sha256 != waived.basis_sha256
    assert run(lab, approval=approve_basis(waived.basis_sha256, "Dr. Rivera")).status is StrictStatus.AWAITING_APPROVAL
