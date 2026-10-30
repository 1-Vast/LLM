"""Authorized one-call proposal test; no credentials in receipt."""
from pathlib import Path
import json, time, urllib.request, urllib.error
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
OUT = HERE / "api_candidate.json"
PROMPT = """Propose one minimal computational-biology learning principle. A world
model holds competing condition-scoped functional predictions; an Agent buys real
tumour/normal paired plates, distinguishes hypotheses, improves separately measured
drug choices, revises a boundary reusable for new cells/drugs.
Public BATCHIE: source rounds1-10, paired plates11-15, later selected-hit panel:
five Ewing labels plus BJ/RPE; 23 common pairs at 0.1+0.1uM, only5 identical source
pairs/doses. Historical exposure. Files are not authenticated independent cultures.
No matched engagement/rescue, no mechanistic truth. Do not invent measurements.
Rejected: few-interaction selection; prediction-disagreement sampling; fixed search
as RSI; upward-cone deletion of monotone validity (ordinary same-prior MAP).
Same-information rivals: retraining, hierarchical/multitask, multi-output GP,
random, decision KG/BOED, direct confirmation. TI loss/LLM/KG additions not novel.
Give an exact one-feedback update and falsifiable next-task prediction, not modules.
No novelty claim or citations. Admit equivalence when present. Output concise JSON
keys: core_question, changed_premise, competing_claims, available_inputs,
exact_update, next_task_prediction, real_discriminating_test,
strongest_equivalence_risk, why_not_extra_prior_or_budget, stop_condition.
"""

if __name__ == "__main__":
    if OUT.exists():
        print("Existing receipt; no repeated API call.")
        raise SystemExit(0)
    cfg = {}
    for line in (HERE.parents[1] / ".env").read_text(encoding="utf-8-sig").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            name, value = line.split("=", 1)
            cfg[name.strip()] = value.strip().strip('"').strip("'")
    key, base, model = [cfg.get(n, "") for n in ["DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL"]]
    assert key and model and urlparse(base).hostname == "api.deepseek.com"
    body = dict(model=model, messages=[dict(role="user", content=PROMPT)], max_tokens=3000,
                reasoning_effort="none", response_format={"type": "json_object"}, stream=False)
    receipt = dict(purpose="proposal_only_not_biological_evidence", request=body, paid_cost=None)
    started = time.perf_counter()
    try:
        req = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=json.dumps(body).encode(),
                  headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as response:
            data = json.load(response)
        choice = data["choices"][0]
        content = choice["message"].get("content") or ""
        assert key not in content
        receipt.update(status="completed", server_model=data.get("model"), usage=data.get("usage"),
                       response_id=data.get("id"), finish_reason=choice.get("finish_reason"), content=content)
    except urllib.error.HTTPError as error:
        receipt.update(status="failed", error_type="HTTPError", http_status=error.code)
    except Exception as error:
        receipt.update(status="failed", error_type=type(error).__name__)
    receipt["elapsed_seconds"] = time.perf_counter() - started
    serialized = json.dumps(receipt, ensure_ascii=False, indent=2)
    assert key not in serialized
    OUT.write_text(serialized + "\n", encoding="utf-8")
    print(json.dumps({k: receipt.get(k) for k in ["status", "server_model", "usage", "finish_reason", "elapsed_seconds", "http_status"]}))
