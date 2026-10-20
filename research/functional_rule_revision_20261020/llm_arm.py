"""Bounded secondary arm: an LLM selects one edit id (or NO_EDIT) from the frozen dictionary.

The model sees only opaque identifiers, frozen numerical feature definitions and the same legal
S/C evidence table the deterministic selector uses. It never sees dataset names, drug or cell
names, G/F information or workbooks. Its answer is validated locally against the allowed ids;
nothing it writes is executed. Failures yield an explicit fallback, never extra candidate search.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

MAX_HTTP_ATTEMPTS = 4          # including client retries, for the whole study
MAX_LOGICAL_REQUESTS = 2
MAX_OUTPUT_TOKENS = 1024       # <= 2,048 allowed
MAX_INPUT_TOKENS = 6000        # conservative allowance
CHARS_PER_TOKEN_CONSERVATIVE = 2.5   # no provider token counter is used; this over-estimates for English/JSON

SYSTEM = (
    "You are a screening assistant for a bounded model-revision test. You are given a finite menu of "
    "candidate structural edits to a fitted regression model and numerical evidence from legal training "
    "observations only. Choose exactly one edit id from the menu, or NO_EDIT. Cite the observation ids "
    "(field 'obs' in the counterexample list) that support your choice. Do not invent ids. Return one JSON "
    "object with keys: edit_id (string), cited_observation_ids (list of strings, at most 6), "
    "rationale (string, at most 60 words). Explanations are not measurements.")


class ForbiddenPayload(ValueError):
    pass


def estimate_tokens(text: str) -> int:
    return int(len(text) / CHARS_PER_TOKEN_CONSERVATIVE) + 1


def check_payload(summary: dict, forbidden_terms) -> str:
    """Serialise the evidence summary and refuse it if any forbidden term occurs (case-insensitive)."""
    text = json.dumps(summary, sort_keys=True, ensure_ascii=False)
    lowered = text.lower()
    hits = sorted({t for t in forbidden_terms if t and t.lower() in lowered})
    if hits:
        raise ForbiddenPayload(f"payload contains forbidden terms: {hits[:5]}")
    return text


def make_messages(summary_text: str) -> list:
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": "Evidence summary (JSON):\n" + summary_text}]


@dataclass
class ApiReceipt:
    enabled: bool = True
    outcome: str = "NOT_RUN"           # VALID_EDIT | VALID_NO_EDIT | INVALID_RESPONSE | API_FAILURE | NOT_RUN | PAYLOAD_REFUSED
    selected: str | None = None
    cited: list = field(default_factory=list)
    model: str | None = None
    prompt_sha256: str | None = None
    est_input_tokens: int | None = None
    usage: dict = field(default_factory=dict)
    latency_seconds: float | None = None
    http_attempts: int = 0
    logical_requests: int = 0
    error: str | None = None
    response_text: str | None = None
    rationale: str | None = None
    money: str = "unverified: provider prices were not verified, so no monetary figure is asserted; token and attempt bounds enforced"

    def as_dict(self):
        return dict(self.__dict__)


def propose(summary: dict, allowed_ids, legal_obs_ids, forbidden_terms, client, *, attempts_used: int = 0,
            count_attempts=None) -> ApiReceipt:
    """One logical request. `count_attempts()` returns HTTP attempts made so far by `client` (wrapper-provided)."""
    receipt = ApiReceipt()
    try:
        text = check_payload(summary, forbidden_terms)
    except ForbiddenPayload as error:
        receipt.outcome, receipt.error = "PAYLOAD_REFUSED", str(error)
        return receipt
    messages = make_messages(text)
    full = json.dumps(messages, ensure_ascii=False)
    receipt.prompt_sha256 = hashlib.sha256(full.encode("utf-8")).hexdigest()
    receipt.est_input_tokens = estimate_tokens(full)
    if receipt.est_input_tokens > MAX_INPUT_TOKENS:
        receipt.outcome, receipt.error = "PAYLOAD_REFUSED", f"estimated {receipt.est_input_tokens} input tokens exceeds {MAX_INPUT_TOKENS}"
        return receipt
    if attempts_used >= MAX_HTTP_ATTEMPTS:
        receipt.outcome, receipt.error = "API_FAILURE", "attempt budget exhausted before the request"
        return receipt
    receipt.logical_requests = 1
    start = time.time()
    try:
        result, response = client.complete_json(messages, max_tokens=MAX_OUTPUT_TOKENS)
    except Exception as error:  # transport/protocol failure: explicit fallback, no repair loop
        receipt.latency_seconds = round(time.time() - start, 2)
        receipt.outcome, receipt.error = "API_FAILURE", f"{type(error).__name__}: {str(error)[:200]}"
        receipt.http_attempts = (count_attempts() if count_attempts else 1) - attempts_used
        return receipt
    receipt.latency_seconds = round(time.time() - start, 2)
    receipt.http_attempts = (count_attempts() if count_attempts else 1) - attempts_used
    receipt.model = getattr(response, "model", None)
    receipt.usage = dict(getattr(response, "usage", {}) or {})
    receipt.response_text = json.dumps(result, sort_keys=True, ensure_ascii=False)[:2000]
    edit = result.get("edit_id")
    cited = result.get("cited_observation_ids", [])
    allowed = set(allowed_ids) | {"NO_EDIT"}
    legal = set(legal_obs_ids)
    if not isinstance(edit, str) or edit not in allowed:
        receipt.outcome, receipt.error = "INVALID_RESPONSE", "edit_id is not in the allowed menu"
        return receipt
    if not isinstance(cited, list) or len(cited) > 6 or any((not isinstance(c, str)) or c not in legal for c in cited):
        receipt.outcome, receipt.error = "INVALID_RESPONSE", "cited observation ids are not legal visible ids"
        return receipt
    rationale = result.get("rationale", "")
    receipt.rationale = rationale[:400] if isinstance(rationale, str) else None
    receipt.selected, receipt.cited = edit, cited
    receipt.outcome = "VALID_NO_EDIT" if edit == "NO_EDIT" else "VALID_EDIT"
    return receipt


class AttemptCounter:
    """Counts HTTP attempts made through the maintained client by wrapping its module-level urlopen."""

    def __init__(self, llm_module, limit: int = MAX_HTTP_ATTEMPTS):
        self.llm = llm_module
        self.limit = limit
        self.count = 0
        self._original = None
        self._original_attempts = None

    def __enter__(self):
        self._original = self.llm.urlopen
        self._original_attempts = self.llm._MAX_ATTEMPTS
        counter = self

        def counted(*args, **kwargs):
            counter.count += 1
            return counter._original(*args, **kwargs)

        self.llm.urlopen = counted
        self.llm._MAX_ATTEMPTS = max(1, min(self._original_attempts, self.limit))
        return self

    def __exit__(self, *exc):
        self.llm.urlopen = self._original
        self.llm._MAX_ATTEMPTS = self._original_attempts
        return False

    def __call__(self):
        return self.count
