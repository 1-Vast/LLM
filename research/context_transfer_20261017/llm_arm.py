"""Secondary agent arm: an LLM chooses which shortlisted items to measure first.

File summary
- Path: research/context_transfer_20261017/llm_arm.py
- Purpose: test whether biomedical reasoning by deepseek-flash improves the bridge choice of the
  deterministic agent, with the Virtual Cell posterior still making the final nominations.
- Core points:
  - The model sees the context description (lineage, or a patient's mutated genes and
    diagnosis), the well budget, and a fixed shortlist of 30 items with the Virtual Cell's prior
    P(hit) and predictive SD. It never sees any outcome of the target context.
  - It must return exactly `k` distinct shortlist ids. Anything else is refused by name
    (`llm_invalid_selection`, `llm_transport_error`, `llm_protocol_error`) and the arm falls back
    to the deterministic lookahead bridge, so a refusal costs the arm nothing it did not earn.
  - Every request/response is cached by prompt digest in a JSONL ledger with token usage, so a
    rerun makes no new calls and the spend can be audited.
- Interfaces: `LLMBridge(ledger_path, offline=False).choose(context_text, shortlist, k, budget)`.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _provider():
    """Load src/agent/llm.py by path: this study's own agent.py shadows the src agent package."""

    import importlib.util
    name = "maestro_src_agent_llm"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ROOT / "src" / "agent" / "llm.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]

RATE_IN, RATE_OUT = 0.30, 1.20   # USD per million tokens (provider contract, cache-miss input)

SYSTEM = (
    "You are the experiment-selection component of an autonomous drug-discovery research agent. "
    "A response model has already scored each candidate item for this new biological context. "
    "You choose which items to measure FIRST. After those measurements the response model is "
    "updated and it picks the remaining wells. The goal is the largest total number of hits over "
    "all wells (first measurements count too). A hit is an unusually strong, context-specific "
    "response compared with other contexts. Use biological knowledge where it helps; the model "
    "scores are calibrated guesses, not facts."
)


class LLMBridge:
    def __init__(self, ledger_path, offline: bool = False, max_tokens: int = 600):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache = {}
        if self.ledger_path.exists():
            for line in self.ledger_path.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                self.cache[row["digest"]] = row
        self.offline = offline
        self.max_tokens = max_tokens
        self.client = None
        if not offline:
            llm = _provider()
            self.client = llm.DeepSeekChatClient(llm.MAESTROSettings.from_workspace(ROOT))

    def spend(self) -> dict:
        rows = list(self.cache.values())
        pin = sum(r.get("usage", {}).get("prompt_tokens", 0) for r in rows)
        pout = sum(r.get("usage", {}).get("completion_tokens", 0) for r in rows)
        return {"calls": len(rows), "prompt_tokens": pin, "completion_tokens": pout,
                "usd_upper_bound": round(pin * RATE_IN / 1e6 + pout * RATE_OUT / 1e6, 6)}

    def choose(self, context_text: str, shortlist: list[dict], k: int, budget: int):
        user = {
            "context": context_text,
            "wells_total": budget,
            "measure_first": k,
            "candidates": shortlist,
            "answer_format": {"measure_first_ids": f"list of exactly {k} distinct candidate ids",
                              "reason": "at most 30 words"},
        }
        messages = [{"role": "system", "content": SYSTEM},
                    {"role": "user", "content": json.dumps(user, ensure_ascii=False)}]
        digest = hashlib.sha256(json.dumps(messages, sort_keys=True).encode()).hexdigest()
        row = self.cache.get(digest)
        if row is None:
            if self.offline:
                return None, "llm_offline_not_cached"
            LLMError = _provider().LLMError
            try:
                obj, resp = self.client.complete_json(messages, max_tokens=self.max_tokens)
                row = {"digest": digest, "answer": obj, "usage": dict(resp.usage),
                       "finish_reason": resp.finish_reason, "model": resp.model}
            except LLMError as error:
                code = getattr(error, "code", None) or type(error).__name__
                row = {"digest": digest, "answer": None, "error": str(code), "usage": {}}
            self.cache[digest] = row
            with self.ledger_path.open("a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(row) + "\n")
        if row.get("answer") is None:
            return None, "llm_protocol_error"
        ids = row["answer"].get("measure_first_ids")
        valid = {c["id"] for c in shortlist}
        if not isinstance(ids, list) or len(ids) != k or len(set(map(str, ids))) != k \
                or not set(map(str, ids)) <= valid:
            return None, "llm_invalid_selection"
        return [str(i) for i in ids], None
