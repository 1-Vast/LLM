"""Independent offline checks of root fixes; report only, fresh receipts only."""
import ast
from copy import deepcopy
from dataclasses import replace
from datetime import date
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from agent import llm, decision_critic as jev
from agent.model_audit import ModelAuditAgent
from tests.test_agent_world_model_integration import _controller, _request, CountingWorldModel
from tests.test_typed_decision_critic import CONTRAST, ACTIONS
from tests.fixtures.stub_client import StubClient
from virtual_cell.interface import PredictionCache, StatePrediction, safe_predict


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Reply:
    def __init__(self, raw): self.raw = raw
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return self.raw


def outcome(call):
    try:
        value = call()
        return {"returned": type(value).__name__, "refusal": getattr(value, "refusal", None)}, value
    except Exception as error:
        return {"raised": type(error).__name__, "message": str(error)}, None


results, checks = {}, {}
for provider, module in (("deepseek", llm), ("jev", jev)):
    settings = (llm.MAESTROSettings("offline-placeholder", "https://invalid.example", "model", "vision", OUT)
        if provider == "deepseek" else jev.TypeSafeSettings("offline-placeholder", "https://invalid.example", "jev-test"))
    for name, raw in (("null", b"null"), ("array", b"[]"), ("invalid_utf8", b"\xff"), ("invalid_json", b"not json")):
        client = llm.DeepSeekChatClient(settings) if provider == "deepseek" else jev.TypeSafeJevClient(settings)
        call = (lambda: client.complete_json([{"role": "user", "content": "Return {}."}])) if provider == "deepseek" else (
            lambda: client.evaluate("state", (jev.noul("q", "Is a measurement present?"),)))
        with patch.object(module, "urlopen", return_value=Reply(raw)):
            observed, value = outcome(call)
        key = provider + "_" + name
        results[key] = observed
        checks[key] = observed.get("raised") == "LLMProtocolError" if provider == "deepseek" else (
            value is not None and not value.answers and (value.refusal or "").startswith("JevProtocolError:"))

usage = {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10}
client = llm.DeepSeekChatClient(llm.MAESTROSettings("offline-placeholder", "https://invalid.example", "model", "vision", OUT))
body = {"choices": [{"message": {"content": None}, "finish_reason": "length"}], "usage": usage}
with patch.object(llm, "urlopen", return_value=Reply(json.dumps(body).encode())):
    observed, _ = outcome(lambda: client.complete_json([{"role": "user", "content": "Return {}."}]))
results["unusable_text_usage"] = {"observed": observed, "reported": usage, "counted": client.provider_usage}
checks["usage_retained"] = observed.get("raised") == "LLMProtocolError" and client.provider_usage == dict(usage, calls=1)

for workers in (1, 2):
    for reuse in (False, True):
        model = CountingWorldModel(supported=("drug-known", "drug-other"))
        controller = _controller(OUT / f"dedup_{workers}_{reuse}", StubClient([]), world_model=model,
                                 max_parallel_predictions=workers, reuse_predictions=reuse)
        counts, bindings, zero_duplicate_cost = [], [], []
        for run in ("first", "second"):
            other = replace(_request(run + "other"), intervention=replace(_request().intervention, identifier="drug-other"))
            requests = {"origin": _request(run + "origin"), "duplicate": _request(run + "duplicate"), "other": other}
            answers = controller._predict_many(requests, run)
            counts.append(model.predictions)
            bindings.append([v[1].request_id for v in answers.values()] == [r.request_id for r in requests.values()])
            zero_duplicate_cost.append(answers["duplicate"][1].compute_cost == 0)
        key = f"dedup_{workers}_{reuse}"
        results[key] = {"distinct_per_round": 2, "requests_per_round": 3, "cumulative_predictions": counts,
                        "binding_valid": bindings, "duplicate_cost_zero": zero_duplicate_cost}
        checks[key] = counts == ([2, 2] if reuse else [2, 4]) and all(bindings) and all(zero_duplicate_cost)

class Abstaining(CountingWorldModel):
    def predict(self, request):
        self.predictions += 1
        return StatePrediction(False, None, None, ("synthetic unsupported result",), request_id=request.request_id,
                               model_version=request.model_version, abstain_reason="synthetic_refusal", compute_cost=3)

model = Abstaining()
controller = _controller(OUT / "abstention_dedup", StubClient([]), world_model=model, max_parallel_predictions=2)
for run in ("first", "second"):
    answers = controller._predict_many({"a": _request(run + "a"), "b": _request(run + "b")}, run)
    checks["abstention_reason_" + run] = all(v[1].abstain_reason == "synthetic_refusal" for v in answers.values())
results["abstention_dedup"] = {"predictions_after_two_rounds": model.predictions,
    "duplicate_compute_cost": answers["b"][1].compute_cost}
checks["abstentions_not_persistently_cached"] = model.predictions == 2 and answers["b"][1].compute_cost == 0

class Repeated:
    model = "jev-latest"
    def __init__(self, mixed_model=False, mixed_state=False):
        self.calls, self.mixed_model, self.mixed_state = 0, mixed_model, mixed_state
    def evaluate(self, state, questions):
        self.calls += 1
        question = next(q for q in questions if q.identifier == "decision_separation")
        answer = jev.TypedAnswer.parse(question, {"probability": 0.1 if self.calls == 1 else 0.9})
        version = f"v{self.calls}" if self.mixed_model else "v1"
        state_id = jev.state_digest(state + str(self.calls)) if self.mixed_state else jev.state_digest(state)
        return jev.JevEvaluation(version, state_id, {question.identifier: answer})

for name, models, states in (("mixed_model", True, False), ("mixed_state", False, True), ("same_identity", False, False)):
    critic = jev.TypedDecisionCritic(Repeated(models, states))
    before = critic.ledger.records, critic.stability.records
    report = critic.review_plan(CONTRAST, ACTIONS, repeats=2)
    after = critic.ledger.records, critic.stability.records
    results[name] = {"model_version": report.model_version, "judgments": len(report.judgments),
        "refusals": list(report.refusals), "stability_records_before_after": [len(before[1]), len(after[1])],
        "judgment_records_before_after": [len(before[0]), len(after[0])]}
    checks[name] = ((not report.judgments and not report.findings and after == before and
        any(r.startswith("mixed_model_versions" if models else "mixed_state_digests") for r in report.refusals))
        if (models or states) else bool(report.judgments) and len(after[1]) == 1)

bad = replace(_request(), history=({"action": "a", "outcome": "unresolved", "extra": float("nan")},), forecast_mode="history_aware")
model = CountingWorldModel()
assessment, prediction = safe_predict(model, bad)
results["nonfinite_history"] = {"validation_errors": list(bad.validation_errors()), "cache_key": PredictionCache.key_for(bad, "backend"),
    "abstain_reason": prediction.abstain_reason, "backend_predictions": model.predictions}
checks["nonfinite_history"] = "invalid_history" in bad.validation_errors() and PredictionCache.key_for(bad, "backend") is None and model.predictions == 0
checks["history_and_sampling_modes_distinct"] = len({PredictionCache.key_for(replace(_request(), history=({"action": "a", "outcome": label},),
    forecast_mode=mode), "backend") for label in ("unresolved", "absent") for mode in ("state", "history_aware")}) == 4
results["default_log"] = str(llm._log_directory(ROOT, ""))
checks["default_log"] = llm._log_directory(ROOT, "") == ROOT / "log" / date.today().strftime("%Y%m%d")

card = {"remaining_budget": 2, "qualified_prerequisites": [], "attempted_actions": [],
        "actions": [{"id": "legal", "cost": 1}, {"id": "blocked", "cost": 1, "prerequisites": ["p"]}],
        "forecasts": [{"supplies": ["p"], "kind": "model_prediction"}], "evidence": []}
auditor = ModelAuditAgent()
for action, authority in (("legal", False), ("blocked", False), ("unknown", False), ("legal", True)):
    proposal = {"action": action, "terminal_authorized": authority}
    before = deepcopy((card, proposal, vars(auditor)))
    report = auditor.review(card, proposal)
    key = f"auditor_{action}_{authority}"
    results[key] = [f.code for f in report.findings]
    checks[key] = (card, proposal, vars(auditor)) == before and not hasattr(report, "action") and not hasattr(report, "repair")

tree = ast.parse((ROOT / "src/agent/model_audit.py").read_text())
results["auditor_imports"] = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)] + [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
checks["auditor_no_execution_dependency"] = set(results["auditor_imports"]) <= {"__future__", "dataclasses", "hashlib", "json", "math", "typing"}
invalid_card = deepcopy(card); invalid_card["remaining_budget"] = float("nan")
results["auditor_invalid_numeric_input"], _ = outcome(lambda: auditor.review(invalid_card, {"action": "defer", "terminal_authorized": False}))
results["auditor_nonjson_proposal"], _ = outcome(lambda: auditor.review(card, {"action": "legal", "terminal_authorized": False, "extra": set()}))

prior = OUT.parent / "reproduction_receipt.json"
source_paths = [ROOT / p for p in ("src/agent/llm.py", "src/agent/decision_critic.py", "src/agent/orchestrator.py", "src/virtual_cell/interface.py", "src/agent/model_audit.py")]
record = {"date": "2026-10-01", "command": [sys.executable, *sys.argv], "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "environment": {"interpreter": sys.executable, "python": sys.version, "platform": platform.platform()},
    "source_sha256": {str(p.relative_to(ROOT)): sha(p) for p in source_paths}, "code_sha256": sha(Path(__file__)),
    "original_frozen_receipt_sha256": sha(prior), "checks": checks, "all_six_original_cases_resolved": all(checks.values()),
    "results": results, "new_open_cases": ["auditor_invalid_numeric_input", "auditor_nonjson_proposal"],
    "limits": "Offline synthetic engineering checks; no provider call, training, repair or mutation of original receipts."}
with (OUT / "independent_validation.json").open("x") as stream: json.dump(record, stream, indent=2, allow_nan=False)
print(json.dumps({"original_cases_resolved": record["all_six_original_cases_resolved"], "checks": checks,
    "new_open_cases": {k: results[k] for k in record["new_open_cases"]}}, indent=2))
