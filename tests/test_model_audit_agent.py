"""The dedicated auditor reports defects without state changes or repair authority."""
from copy import deepcopy
from dataclasses import FrozenInstanceError

import pytest

from agent.model_audit import ModelAuditAgent


def card():
    return {"remaining_budget": 2, "qualified_prerequisites": [], "attempted_actions": ["done"],
            "actions": [{"id": "legal", "cost": 1}, {"id": "expensive", "cost": 3},
                        {"id": "blocked", "cost": 1, "prerequisites": ["measured_activity"]},
                        {"id": "done", "cost": 1}],
            "forecasts": [{"supplies": ["measured_activity"], "kind": "model_prediction"}], "evidence": []}


@pytest.mark.parametrize("action", ["expensive", "blocked", "done", "unknown"])
def test_reports_action_defects_without_replacing_action_or_qualifying_forecasts(action):
    task = card()
    proposal = {"action": action, "terminal_authorized": False}
    original = deepcopy((task, proposal))
    result = ModelAuditAgent().review(task, proposal)
    assert [f.code for f in result.findings] == ["illegal_action"]
    assert (task, proposal) == original
    assert not hasattr(result, "action") and not hasattr(result, "repair")
    assert len(result.input_sha256) == len(result.proposal_sha256) == 64
    with pytest.raises(FrozenInstanceError):
        result.findings = ()


@pytest.mark.parametrize("proposal,code", [([], "malformed_proposal"), ({"action": "legal"}, "malformed_proposal"),
    ({"action": "legal", "terminal_authorized": 1}, "malformed_proposal"),
    ({"action": "legal", "terminal_authorized": True}, "terminal_authority_claim")])
def test_reports_shape_and_authority_defects(proposal, code):
    assert [f.code for f in ModelAuditAgent().review(card(), proposal).findings] == [code]


def test_valid_proposal_and_defer_report_no_defect_and_task_adapter_is_not_named():
    auditor = ModelAuditAgent()
    for selected in ("legal", "defer"):
        assert not auditor.review(card(), {"action": selected, "terminal_authorized": False}).findings
    malformed = card()
    malformed["actions"].append(malformed["actions"][0])
    assert auditor.review(malformed, {}).findings[0].code == "invalid_task_contract"
    malformed["actions"] = None
    assert auditor.review(malformed, {}).findings[0].code == "invalid_task_contract"


def test_unserializable_inputs_report_defects_with_unavailable_hash_instead_of_crashing():
    malformed = card()
    malformed["remaining_budget"] = float("nan")
    report = ModelAuditAgent().review(malformed, {})
    assert report.findings[0].code == "invalid_task_contract" and report.input_sha256 is None
    report = ModelAuditAgent().review(card(), {"action": "legal", "terminal_authorized": False, "extra": {1, 2}})
    assert report.findings[0].code == "malformed_proposal" and report.proposal_sha256 is None
    assert ModelAuditAgent().review([], {}).findings[0].code == "invalid_task_contract"


@pytest.mark.parametrize("value", [10**1000, "\ud800"])
def test_extreme_numeric_and_unicode_inputs_stay_inside_report_contract(value):
    malformed = card()
    if isinstance(value, int):
        malformed["remaining_budget"] = value
    else:
        malformed["actions"][0]["id"] = value
    assert ModelAuditAgent().review(malformed, {}).findings[0].code == "invalid_task_contract"
