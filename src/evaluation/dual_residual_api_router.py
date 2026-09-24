"""One-call API router smoke/decision test for the real virtual-cell panel."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from agent.configuration import MAESTROSettings
from agent.llm import DeepSeekChatClient, json_object_from_text

ALLOWED = {"repair_realization", "repair_hypothesis", "keep"}

def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument("--workspace", type=Path, default=Path.cwd()); p.add_argument("--panel", type=Path, required=True); p.add_argument("--out", type=Path, required=True)
    a = p.parse_args(); panel = json.loads(a.panel.read_text(encoding="utf-8")); row = panel["rows"][0]
    visible = {"target": {"endpoint": "x_hvg_perturbation_shift", "target_vector": "registered_goal_G0"},
               "current_prediction": row["values"],
               "repair_menu": {"repair_realization": ["A_01", "A_02"], "repair_hypothesis": ["H_01", "H_02"]},
               "constraints": ["choose exactly one branch", "do not invent predictions or candidates", "return JSON only"]}
    messages = [{"role":"system","content":"You are a routing controller. Return exactly one JSON object of the form {\"branch\":\"repair_realization\"}. Allowed values: repair_realization, repair_hypothesis, keep."}, {"role":"user","content":json.dumps(visible, ensure_ascii=True)}]
    result = {"schema":"maestro.e0.dir.api_router.v1", "model":None, "request_ok":False, "parsed":False, "decision":None, "error":None, "visible_state":visible}
    try:
        settings = MAESTROSettings.from_workspace(a.workspace); client = DeepSeekChatClient(settings)
        response = client.complete(messages, max_tokens=128, json_output=False, thinking_enabled=False)
        result["request_ok"] = True; result["model"] = response.model; result["finish_reason"] = response.finish_reason; result["usage"] = dict(response.usage)
        result["raw_response"] = response.content[:1000]
        parsed = json_object_from_text(response.content)
        if not isinstance(parsed, dict) or set(parsed) != {"branch"} or parsed["branch"] not in ALLOWED: raise ValueError("invalid_branch_contract")
        result["parsed"] = True; result["decision"] = parsed["branch"]
    except Exception as e:
        result["error"] = type(e).__name__ + ": " + str(e)
    a.out.parent.mkdir(parents=True, exist_ok=True); a.out.write_text(json.dumps(result, indent=2, ensure_ascii=True)+"\n", encoding="utf-8"); print(a.out)
    return 0 if result["parsed"] else 1

if __name__ == "__main__": raise SystemExit(main())

