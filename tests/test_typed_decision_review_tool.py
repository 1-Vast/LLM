import json
from pathlib import Path

import pytest

from maestro.tool_analysis import typed_decision_review


def _artifact(tmp_path: Path, **updates):
    data = {
        "schema_version": "1.0",
        "state_digest": "state-123",
        "judgments": [
            {
                "question_id": "best_separating_action",
                "scope": "action_ranking",
                "kind": "choice",
                "value": "activity",
                "probability": 0.8,
                "evidence_kind": "model_prediction",
                "satisfies_premise": False,
                "eliminates_hypothesis": False,
                "is_measurement": False,
            },
            {
                "question_id": "evidence_sufficiency",
                "scope": "plan_critique",
                "kind": "score",
                "value": 2,
                "probability": None,
                "evidence_kind": "model_prediction",
            },
        ],
        "stability": [],
        "refusals": [],
        "suppressed_by_revocation": False,
    }
    data.update(updates)
    path = tmp_path / "review.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_review_tool_keeps_jev_advisory_and_exposes_action_suggestion(tmp_path):
    result = typed_decision_review({"dataset_path": str(_artifact(tmp_path))})
    payload = result["payload"]
    assert payload["advisory_only"] is True
    assert payload["belief_update_allowed"] is False
    assert payload["premise_satisfaction_allowed"] is False
    assert payload["action_selection_authority"] == "deterministic_validator"
    assert payload["advisory_action_ids"] == ["activity"]
    assert all(item["evidence_kind"] == "model_prediction" for item in payload["judgments"])


def test_review_tool_suppresses_unstable_action_ranking(tmp_path):
    path = _artifact(tmp_path, suppressed_by_revocation=True,
                     stability=[{"scope": "action_ranking", "verdict": "unstable", "revoked": True}])
    payload = typed_decision_review({"dataset_path": str(path)})["payload"]
    assert payload["suppressed_scopes"] == ["action_ranking"]
    assert payload["advisory_action_ids"] == []


@pytest.mark.parametrize("field,value", [
    ("evidence_kind", "real_measurement"),
    ("satisfies_premise", True),
    ("eliminates_hypothesis", True),
    ("is_measurement", True),
])
def test_review_tool_rejects_jev_escalation(tmp_path, field, value):
    judgment = _artifact(tmp_path)
    data = json.loads(judgment.read_text(encoding="utf-8"))
    data["judgments"][0][field] = value
    judgment.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        typed_decision_review({"dataset_path": str(judgment)})


def test_review_tool_rejects_unknown_scope_and_extra_fields(tmp_path):
    path = _artifact(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["judgments"][0]["scope"] = "mechanism_contrast"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        typed_decision_review({"dataset_path": str(path)})

    data["judgments"][0]["scope"] = "action_ranking"
    data["unexpected"] = "not allowed"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        typed_decision_review({"dataset_path": str(path)})
