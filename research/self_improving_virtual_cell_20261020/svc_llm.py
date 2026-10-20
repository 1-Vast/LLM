"""Bounded secondary arm: an LLM proposes one typed executable candidate program per generation from visible evidence.

Visibility: opaque module-class ids (K0..), numeric diagnosis, the incumbent program and the grammar. No drug, cell or dataset names,
no outcomes of unqueried pairs. The reply is validated locally against the grammar before anything executes; invalid replies yield
no candidate (explicit fallback, no repair loop). Credentials are read by the maintained client and never persisted.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

import svc_programs as P

ROOT = Path(__file__).resolve().parents[2]
MAX_HTTP_ATTEMPTS = 6
MAX_TOTAL_TOKENS = 30000
MAX_OUTPUT_TOKENS = 1500
CHARS_PER_TOKEN = 2.5

GRAMMAR_TEXT = (
    "Program = {phi: [...], Q: [...], f: {...}}.\n"
    "phi entries: {\"t\":\"global\"} | {\"t\":\"latent\",\"k\":1..4} (at most one latent entry) | {\"t\":\"class\",\"id\":\"K<n>\"} (a listed module-class id). At most 8 state entries in total (a latent entry of size k counts k).\n"
    "Q stages (fractions sum to 1, 1..3 stages, at least one probe, at most one confirm and it is last): "
    "{\"kind\":\"probe\",\"frac\":x,\"rule\":\"random|coverage|variance|aoptimal|witness|exploit\",\"cond\":null} | "
    "{\"kind\":\"probe\",\"frac\":x,\"rule\":\"witness\",\"cond\":{\"coord\":<index into the expanded state entries>,\"thr\":number,\"else\":\"coverage|variance|aoptimal|confirm\"}} | {\"kind\":\"confirm\",\"frac\":x}.\n"
    "f = {\"type\":\"ridge\",\"inter\":[subset of \"class\",\"anchor\",\"product\"],\"lam\":0.01..1000}.\n"
    "A probe measures the full pair-by-cell grid of one pair; the confirm stage spends the remaining budget on top predicted pairs (not available under the transfer contract).")

SYSTEM = (
    "You design measurement-and-state programs for ranking drug combinations in a new cell background. You are shown a numeric diagnosis of "
    "where the incumbent program fails on previously released backgrounds, using opaque module-class ids. Propose ONE new program in the stated "
    "grammar that you expect to fix the decision-relevant failure, or answer {\"decision\":\"none\"} if the evidence does not support any program "
    "(for example when failure scores are below the noise floor) . Cite evidence ids (field 'ev') that support your proposal. Return one JSON object "
    "with keys: decision ('propose' or 'none'), program (object), cited (list of evidence ids, at most 6), rationale (at most 60 words). "
    "Explanations are not measurements; nothing you write is accepted without held-out testing.")


class AttemptCounter:
    def __init__(self, llm_module, limit=MAX_HTTP_ATTEMPTS, used=0):
        self.llm, self.limit, self.count = llm_module, limit, used

    def __enter__(self):
        self._orig, self._orig_attempts = self.llm.urlopen, self.llm._MAX_ATTEMPTS
        c = self

        def counted(*a, **k):
            if c.count >= c.limit:
                raise RuntimeError("HTTP attempt budget exhausted")
            c.count += 1
            return c._orig(*a, **k)

        self.llm.urlopen = counted
        self.llm._MAX_ATTEMPTS = max(1, min(self._orig_attempts, self.limit - self.count))
        return self

    def __exit__(self, *exc):
        self.llm.urlopen, self.llm._MAX_ATTEMPTS = self._orig, self._orig_attempts
        return False


def opaque_ids(static, seed):
    """Opaque class ids K0.. in a seeded permutation; the mapping stays local."""
    order = np.random.default_rng(int.from_bytes(hashlib.sha256(f"opaque|{seed}".encode()).digest()[:8], "little")).permutation(len(static.classes))
    to_class = {f"K{k}": int(order[k]) for k in range(len(order))}
    return to_class, {v: k for k, v in to_class.items()}


def evidence_payload(diag, incumbent_spec, static, to_opaque, contract, budget, history_cells):
    cl = static.classes
    items = []
    for c in np.argsort(-np.array(diag["class_scores"]))[:5]:
        items.append({"ev": f"E{len(items) + 1}", "class_id": to_opaque[int(c)], "unexplained_cell_variation_score": diag["class_scores"][int(c)],
                      "above_noise_floor": bool(diag["class_scores"][int(c)] > diag["noise_floor"])})
    inc = copy.deepcopy(incumbent_spec)
    for e in inc["phi"]:
        if e["t"] == "class":
            e["id"] = to_opaque[cl.index((e.pop("a"), e.pop("b")))]
    return {"contract": contract, "query_budget_units": budget, "n_released_background_cells": len(history_cells), "incumbent_program": inc,
            "diagnosis": {"verdict": diag["verdict"], "noise_floor": diag["noise_floor"], "shared_latent_share_of_residual": diag["latent_share"],
                          "incumbent_utility_on_released": round(diag["incumbent_dev_utility"], 4), "zero_probe_utility_on_released": round(diag["zero_dev_utility"], 4)},
            "evidence": items, "grammar": GRAMMAR_TEXT}


def to_spec(program, to_class, static):
    """API-facing program -> internal spec; raises ValueError on anything outside the grammar."""
    if not isinstance(program, dict):
        raise ValueError("program must be an object")
    s = copy.deepcopy(program)
    cl = static.classes
    for e in s.get("phi", []):
        if isinstance(e, dict) and e.get("t") == "class":
            if set(e) != {"t", "id"} or e["id"] not in to_class:
                raise ValueError("class entry must be {t,id} with a listed id")
            a, b = cl[to_class[e["id"]]]
            e.clear()
            e.update({"t": "class", "a": a, "b": b})
    errs = P.validate_spec(s, static)
    if errs:
        raise ValueError("; ".join(errs))
    return s


class ApiProposer:
    """One logical request per generation; all limits are cumulative over the study."""

    def __init__(self, static, seed, contract, budget, ledger_path: Path | None = None):
        self.static, self.seed, self.contract, self.budget = static, seed, contract, budget
        self.to_class, self.to_opaque = opaque_ids(static, seed)
        self.receipts, self.tokens, self.attempts = [], 0, 0
        self.client, self.llm, self.config_error = None, None, None
        try:
            sys.path.insert(0, str(ROOT / "src"))
            from agent import llm
            settings = llm.MAESTROSettings.from_workspace(ROOT)
            self.client, self.llm = llm.DeepSeekChatClient(settings), llm
        except Exception as error:
            self.config_error = f"{type(error).__name__}"

    def candidates(self, gen, diag, incumbent_spec, history_cells):
        rec = {"gen": gen, "outcome": "NOT_RUN", "http_attempts": 0, "usage": {}, "latency_seconds": None, "accepted_for_testing": False}
        self.receipts.append(rec)
        if self.client is None:
            rec["outcome"], rec["error"] = "API_FAILURE", f"configuration: {self.config_error}"
            return []
        payload = evidence_payload(diag, incumbent_spec, self.static, self.to_opaque, self.contract, self.budget, history_cells)
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": "Visible evidence (JSON):\n" + json.dumps(payload, sort_keys=True)}]
        full = json.dumps(messages)
        rec["prompt_sha256"] = hashlib.sha256(full.encode()).hexdigest()
        rec["evidence_logged"] = payload
        est = int(len(full) / CHARS_PER_TOKEN) + 1 + MAX_OUTPUT_TOKENS
        if self.tokens + est > MAX_TOTAL_TOKENS or self.attempts >= MAX_HTTP_ATTEMPTS:
            rec["outcome"], rec["error"] = "BUDGET_REFUSED", f"estimated {est} tokens would exceed the cumulative cap"
            return []
        start = time.time()
        with AttemptCounter(self.llm, MAX_HTTP_ATTEMPTS, self.attempts) as counter:
            try:
                result, response = self.client.complete_json(messages, max_tokens=MAX_OUTPUT_TOKENS)
            except Exception as error:
                rec["outcome"], rec["error"] = "API_FAILURE", f"{type(error).__name__}: {str(error)[:200]}"
                rec["latency_seconds"] = round(time.time() - start, 2)
                rec["http_attempts"] = counter.count - self.attempts
                self.attempts = counter.count
                return []
            rec["http_attempts"] = counter.count - self.attempts
            self.attempts = counter.count
        rec["latency_seconds"] = round(time.time() - start, 2)
        rec["model"] = getattr(response, "model", None)
        usage = dict(getattr(response, "usage", {}) or {})
        rec["usage"] = usage
        self.tokens += int(usage.get("total_tokens") or (usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)) or est)
        rec["response"] = json.dumps(result, sort_keys=True)[:3000]
        if not isinstance(result, dict) or result.get("decision") not in ("propose", "none"):
            rec["outcome"], rec["error"] = "INVALID_RESPONSE", "decision must be propose or none"
            return []
        cited = result.get("cited", [])
        valid_ev = {e["ev"] for e in payload["evidence"]}
        if not isinstance(cited, list) or any(c not in valid_ev for c in cited):
            rec["outcome"], rec["error"] = "INVALID_RESPONSE", "cited evidence ids are not visible ids"
            return []
        if result["decision"] == "none":
            rec["outcome"] = "VALID_NO_PROGRAM"
            return []
        try:
            spec = to_spec(result.get("program"), self.to_class, self.static)
        except ValueError as error:
            rec["outcome"], rec["error"] = "INVALID_PROGRAM", str(error)[:300]
            return []
        rec["outcome"], rec["accepted_for_testing"], rec["cited"] = "VALID_PROGRAM", True, cited
        return [{"op": "api", "spec": spec}]

    def ledger(self):
        return {"model_requests": len(self.receipts), "http_attempts": self.attempts, "cumulative_tokens": self.tokens,
                "limits": {"max_http_attempts": MAX_HTTP_ATTEMPTS, "max_total_tokens": MAX_TOTAL_TOKENS, "max_output_tokens": MAX_OUTPUT_TOKENS},
                "money": "unverified: provider prices were not verified, so no monetary figure is asserted",
                "no_credentials_or_headers_persisted": True, "receipts": self.receipts}
