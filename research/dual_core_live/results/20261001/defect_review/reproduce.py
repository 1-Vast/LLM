"""Offline reproductions only; no provider request, fitting, or production mutation."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from dataclasses import replace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from agent import llm, decision_critic as jev
from tests.test_agent_world_model_integration import _controller, _request, CountingWorldModel
from tests.test_typed_decision_critic import CONTRAST, ACTIONS
from tests.fixtures.stub_client import StubClient
from virtual_cell.interface import PredictionCache


class Reply:
    def __init__(self, raw):
        self.raw = raw
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return self.raw


def observed(call):
    try:
        result = call()
        return {"returned": type(result).__name__, "refusal": getattr(result, "refusal", None)}
    except Exception as error:
        return {"raised": type(error).__name__, "message": str(error)}


results = {}
for provider, module in (("deepseek", llm), ("jev", jev)):
    settings = (llm.MAESTROSettings("offline-placeholder", "https://invalid.example", "model", "vision", OUT)
                if provider == "deepseek" else jev.TypeSafeSettings("offline-placeholder", "https://invalid.example", "jev-test"))
    for name, raw in (("null_envelope", b"null"), ("invalid_utf8", b"\xff")):
        client = llm.DeepSeekChatClient(settings) if provider == "deepseek" else jev.TypeSafeJevClient(settings)
        call = (lambda: client.complete_json([{"role": "user", "content": "Return {}."}])) if provider == "deepseek" else (
            lambda: client.evaluate("registered state", (jev.noul("q", "Does this plan discriminate?"),)))
        with patch.object(module, "urlopen", return_value=Reply(raw)), patch.object(module, "sleep", lambda _: None):
            results[provider + "_" + name] = observed(call)

client = llm.DeepSeekChatClient(llm.MAESTROSettings("offline-placeholder", "https://invalid.example", "model", "vision", OUT))
reported = {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10}
envelope = {"choices": [{"message": {"content": None}, "finish_reason": "length"}], "usage": reported}
with patch.object(llm, "urlopen", return_value=Reply(json.dumps(envelope).encode())):
    results["deepseek_unusable_text_usage"] = {"reported_usage": reported,
        "outcome": observed(lambda: client.complete_json([{"role": "user", "content": "Return {}."}])),
        "client_usage_after_response": client.provider_usage}

requests = {"first": _request("first"), "duplicate": _request("duplicate")}
for reuse in (True, False):
    model = CountingWorldModel()
    controller = _controller(OUT / ("dedup_" + str(reuse)), StubClient([]), world_model=model,
                             max_parallel_predictions=2, reuse_predictions=reuse)
    replies = controller._predict_many(requests, "offline")
    results["round_dedup_reuse_" + str(reuse)] = {"distinct_inputs": 1, "requests": 2,
        "backend_predictions": model.predictions, "response_ids": [v[1].request_id for v in replies.values()]}

class MixedVersions:
    model = "jev-latest"
    def __init__(self):
        self.calls = 0
    def evaluate(self, state, questions):
        self.calls += 1
        probability = 0.1 if self.calls == 1 else 0.9
        question = next(q for q in questions if q.identifier == "decision_separation")
        answer = jev.TypedAnswer.parse(question, {"probability": probability})
        return jev.JevEvaluation("jev-version-" + str(self.calls), jev.state_digest(state),
                                 {question.identifier: answer})

mixed = jev.TypedDecisionCritic(MixedVersions()).review_plan(CONTRAST, ACTIONS, repeats=2)
judgment = next(j for j in mixed.judgments if j.question_id == "decision_separation")
results["jev_mixed_version_repeats"] = {"served_versions": ["jev-version-1", "jev-version-2"],
    "reported_model_version": mixed.model_version, "aggregated_probability": judgment.probability,
    "refusals": list(mixed.refusals), "repeats": mixed.repeats}

bad_history = replace(_request(), history=({"action": "a", "outcome": "unresolved", "extra": float("nan")},),
                      forecast_mode="history_aware")
results["nonfinite_history_cache"] = {"validation_errors": list(bad_history.validation_errors()),
    "cache_outcome": observed(lambda: PredictionCache.key_for(bad_history, "backend"))}

results["default_log_date"] = {"requested_default": "2026-10-01 local execution date",
    "configured_result": str(llm._log_directory(ROOT, ""))}

paths = [Path(__file__), ROOT / "src/agent/llm.py", ROOT / "src/agent/decision_critic.py",
         ROOT / "src/agent/orchestrator.py", ROOT / "src/virtual_cell/interface.py",
         ROOT / "tests/test_agent_world_model_integration.py", ROOT / "tests/test_typed_decision_critic.py"]
record = {"date": "2026-10-01", "scope": "offline synthetic engineering reproductions, not biological or live API results",
    "command": [sys.executable, *sys.argv], "git_commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "environment": {"python": sys.version, "platform": platform.platform(), "interpreter": sys.executable},
    "input_and_code_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    "results": results}
with (OUT / "reproduction_receipt.json").open("x", encoding="utf-8") as stream:
    json.dump(record, stream, indent=2, allow_nan=False)
print(json.dumps(results, indent=2))
