"""Bounded LLM proposer for research-program edits (DeepSeek V4.1 Flash through the maintained client).  Caps: 8 logical requests, 50,000 tokens in total.
Every request is written to RUN/llm_ledger.jsonl (hashes, usage, outcome); no credential or raw response with secrets is stored."""
from __future__ import annotations
import hashlib, json, sys, time
from pathlib import Path
sys.path.insert(0, "D:/MAESTRO")
sys.path.insert(0, str(Path(__file__).parent))

HERE = Path(__file__).parent
LEDGER = HERE / "RUN" / "llm_ledger.jsonl"
MAX_REQUESTS = 8
MAX_TOKENS_TOTAL = 50_000
MAX_OUTPUT = 2200

SYSTEM = (
    "You edit a small research-program function for a drug-screening replay. Return ONE JSON object with keys: "
    "'program_lines' (a list of strings, one per source line, that together define `def run(env):`), and 'rationale' (at most 50 words). "
    "Rules: no imports (np and math are predefined), no attribute names starting with underscore, no open/eval/exec/getattr. Allowed builtins: "
    "len range min max sum sorted abs round float int list dict set tuple enumerate zip any all bool reversed. Do not hard-code drug ids or "
    "numeric tables; the program must be a general procedure. API: env.drugs (list of opaque ids); env.W[d] (probability of sensitive from the "
    "world model, 0-1); env.prior[d] (label rate over other backgrounds); env.nn[d] (fingerprint-neighbour label rate); env.sim(a,b) "
    "(similarity, -1..1); env.left() (remaining budget); env.query_f(d) -> 0/1 (functional label, costs 1.0); env.has_mol(); env.query_m(d) -> "
    "dict with 'score' (float) and 'z' (8 floats) (molecular measurement, costs 0.5); env.queried() -> dict of functional results. "
    "Total budget 5.0. The objective is the number of DISTINCT drugs with a queried functional label that is positive. Re-reading a queried "
    "label is free. A query that exceeds the budget ends the episode. Make a structural change (control flow, selection logic, update rule or "
    "use of the molecular tool), not only a constant change; if you see no improvement, return the incumbent unchanged.")


class Budget:
    def __init__(self):
        self.requests = 0; self.tokens = 0; self.failures = 0
        if LEDGER.exists():
            for l in LEDGER.read_text().splitlines():
                r = json.loads(l); self.requests += 1; self.tokens += r.get("total_tokens", 0); self.failures += r["outcome"] != "OK"


def propose(tag: str, evidence: str, incumbent: str, budget: Budget):
    """One logical request.  Returns (program_source or None, record)."""
    from src.agent.llm import DeepSeekChatClient, MAESTROSettings
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": "INCUMBENT PROGRAM:\n" + incumbent + "\n\nEVIDENCE (development backgrounds only; ids opaque):\n" + evidence}]
    full = json.dumps(msgs)
    rec = {"tag": tag, "prompt_sha256": hashlib.sha256(full.encode()).hexdigest(), "est_input_tokens": int(len(full) / 2.5), "time": time.strftime("%Y-%m-%d %H:%M:%S")}
    if budget.requests >= MAX_REQUESTS or budget.tokens + rec["est_input_tokens"] + MAX_OUTPUT > MAX_TOKENS_TOTAL:
        rec["outcome"] = "BUDGET_REFUSED"; return None, rec
    settings = MAESTROSettings.from_workspace(Path("D:/MAESTRO"))
    client = DeepSeekChatClient(settings)
    t0 = time.time()
    try:
        res, resp = client.complete_json(msgs, model="deepseek-flash", max_tokens=MAX_OUTPUT)
        rec["usage"] = dict(resp.usage); rec["total_tokens"] = int(resp.usage.get("total_tokens", 0)) or int(resp.usage.get("prompt_tokens", 0) + resp.usage.get("completion_tokens", 0))
        rec["model"] = getattr(resp, "model", None)
        lines = res.get("program_lines")
        if not isinstance(lines, list) or not all(isinstance(x, str) for x in lines):
            rec["outcome"] = "INVALID_RESPONSE"; src = None
        else:
            src = "\n".join(lines) + "\n"; rec["outcome"] = "OK"; rec["rationale"] = str(res.get("rationale", ""))[:400]; rec["program_sha256"] = hashlib.sha256(src.encode()).hexdigest()
    except Exception as e:
        rec["outcome"] = f"API_FAILURE:{type(e).__name__}"; rec["error"] = str(e)[:200]; src = None
        rec["total_tokens"] = int(client.provider_usage.get("total_tokens", 0)) if hasattr(client, "provider_usage") and not callable(client.provider_usage) else rec["est_input_tokens"]
    rec["latency_s"] = round(time.time() - t0, 1)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a") as fh:
        fh.write(json.dumps(rec) + "\n")
    budget.requests += 1; budget.tokens += rec.get("total_tokens", 0); budget.failures += rec["outcome"] != "OK"
    return src, rec
