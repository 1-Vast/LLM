"""Offline regressions for independently reproduced runtime failures; no fitting/API calls."""
import json
from dataclasses import replace
from datetime import date

import pytest

from agent import llm, decision_critic as jev
from tests.test_agent_world_model_integration import _controller, _request, CountingWorldModel
from tests.test_typed_decision_critic import CONTRAST, ACTIONS
from tests.fixtures.stub_client import StubClient
from virtual_cell.interface import PredictionCache, safe_predict


class Reply:
    def __init__(self, raw):
        self.raw = raw

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.raw


@pytest.mark.parametrize("raw", [b"null", b"[]", b"\xff", b"not json"])
def test_invalid_provider_envelopes_stay_inside_provider_contracts(tmp_path, monkeypatch, raw):
    for module in (llm, jev):
        monkeypatch.setattr(module, "urlopen", lambda *a, **kw: Reply(raw))
    client = llm.DeepSeekChatClient(llm.MAESTROSettings("secret", "https://invalid.example", "model", "vision", tmp_path))
    with pytest.raises(llm.LLMProtocolError):
        client.complete_json([{"role": "user", "content": "Return {}."}])
    critic = jev.TypeSafeJevClient(jev.TypeSafeSettings("secret", "https://invalid.example", "jev-test"))
    result = critic.evaluate("state", (jev.noul("q", "Is there measured evidence?"),))
    assert not result.answers
    assert result.refusal.startswith("JevProtocolError:")
    assert "secret" not in result.refusal


@pytest.mark.parametrize("choices", [[], [{"message": {"content": None}, "finish_reason": "length"}], "bad"])
def test_reported_usage_is_retained_when_text_is_unusable(tmp_path, monkeypatch, choices):
    usage = {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10}
    body = {"choices": choices, "usage": usage}
    monkeypatch.setattr(llm, "urlopen", lambda *a, **kw: Reply(json.dumps(body).encode()))
    client = llm.DeepSeekChatClient(llm.MAESTROSettings("secret", "https://invalid.example", "model", "vision", tmp_path))
    with pytest.raises(llm.LLMProtocolError):
        client.complete_json([{"role": "user", "content": "Return {}."}])
    assert client.provider_usage == dict(usage, calls=1)


@pytest.mark.parametrize("parallel", [1, 2])
@pytest.mark.parametrize("reuse", [False, True])
def test_round_deduplication_is_independent_of_cross_round_cache(tmp_path, parallel, reuse):
    model = CountingWorldModel()
    controller = _controller(tmp_path, StubClient([]), world_model=model,
                             max_parallel_predictions=parallel, reuse_predictions=reuse)
    for run in ("first", "second"):
        answers = controller._predictions.predict_many({"a": _request(run + "a"), "b": _request(run + "b")}, run)
        assert [v[1].request_id for v in answers.values()] == [run + "a", run + "b"]
        assert answers["b"][1].compute_cost == 0
    assert model.predictions == (1 if reuse else 2)
    # Distinct model inputs still require distinct inferences.
    controller._predictions.predict_many({"different": _request("different", dose=2)}, "third")
    assert model.predictions == (2 if reuse else 3)


def test_mixed_served_versions_are_not_aggregated_or_written_to_judgment_ledgers():
    class Mixed:
        model = "jev-latest"
        calls = 0

        def evaluate(self, state, questions):
            self.calls += 1
            question = next(q for q in questions if q.identifier == "decision_separation")
            answer = jev.TypedAnswer.parse(question, {"probability": 0.1 if self.calls == 1 else 0.9})
            return jev.JevEvaluation(f"v{self.calls}", jev.state_digest(state), {question.identifier: answer})

    critic = jev.TypedDecisionCritic(Mixed())
    result = critic.review_plan(CONTRAST, ACTIONS, repeats=2)
    assert not result.judgments and not result.findings and not result.stability
    assert "mixed_model_versions:v1,v2" in result.refusals
    assert result.model_version is None


@pytest.mark.parametrize("value", [float("nan"), float("inf"), {"nested": [float("nan")]}])
def test_nonfinite_history_refuses_before_backend_or_cache(value):
    request = replace(_request(), history=({"action": "a", "outcome": "unresolved", "extra": value},),
                      forecast_mode="history_aware")
    assert "invalid_history" in request.validation_errors()
    assert PredictionCache.key_for(request, "backend") is None
    model = CountingWorldModel()
    _, prediction = safe_predict(model, request)
    assert prediction.abstain_reason == "invalid_request" and model.predictions == 0


def test_default_log_uses_execution_date_and_explicit_override_remains_supported(tmp_path):
    assert llm._log_directory(tmp_path, "") == tmp_path / "log" / date.today().strftime("%Y%m%d")
    assert llm._log_directory(tmp_path, "log/frozen") == tmp_path / "log" / "frozen"
