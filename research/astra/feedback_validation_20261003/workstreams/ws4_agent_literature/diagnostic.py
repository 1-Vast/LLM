"""Exact-cardinality diagnostic of the LLM planner contract on O'Neil development data.

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws4_agent_literature/diagnostic.py
- Purpose: find which response contract lets deepseek-flash return a valid selection of k
  candidates from a 2k menu, at k = 5..128, and what each valid selection costs. The frozen
  confirmatory run asked for about 128 of 256 ids and got the whole menu in every round.
- Core points:
  - Data: O'Neil 2016 only (exposed development screen); three lines drawn by a fixed seed; the
    line state is two world-model rounds of 15 purchases; the menu is the top 2k untested
    candidates by the frozen world model's P(hit). ALMANAC is never loaded.
  - Prompts: the frozen `LLMPlannerArm._prompt` (named / anonymous / blind) builds every table,
    so the EXACT contract is byte-for-byte the frozen one. RANK and CHUNK16 edit the frozen text
    by asserted string replacement (a silent replacement failure invalidated dev_llm v1).
  - Contracts: EXACT (choose exactly k), RANK (rank the whole menu; the first k are the
    selection), CHUNK16 (sequential calls of <= 16 from the shrinking menu).
  - Spend: `SpendBook` from the frozen module with ceiling USD 0.80; before every call the
    worst-case reservation (prompt at cache-miss rate + max_tokens of output) must fit under
    the ceiling, else the run stops with SPEND_CEILING. Usage is read from the client's
    provider_usage delta, so a call that fails after the provider answered is still priced; a
    call with no decoded response is charged at its reservation. HTTP attempts are counted.
  - Write-once outputs under results/; `--plan` writes plan.json and makes no call; `--run`
    refuses unless plan.json matches this file's digest.
- Interfaces: `python diagnostic.py --plan | --run`; analysis in summarise.py.
- Depends on: numpy, scipy, research.certified_discovery (import only, frozen), src agent.llm.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from research.certified_discovery.llm_agent import RATES, LLMPlannerArm, SpendBook  # noqa: E402
from research.certified_discovery.screens import CACHE, load_library, sha256  # noqa: E402
from research.certified_discovery.world import TransferWorld, WorldConfig  # noqa: E402

LIBRARY = CACHE / "oneil_v1.npz"
OUT = HERE / "results"
PLAN = HERE / "plan.json"
CEILING_USD = 0.80
MAX_TOKENS = 3000            # the frozen LLMPlannerArm default
LINE_SEED = 20261003
KS = (5, 15, 32, 64, 128)
CHUNK = 16
STATE_ROUNDS, STATE_BATCH = 2, 15
CHARS_PER_TOKEN_RESERVE = 1.8  # conservative prompt-token estimate for the pre-call reservation
FINAL_SYSTEM = "Return exactly one JSON object and no prose. Do not use markdown fences."  # as complete_json
TZ = timezone(timedelta(hours=8))

RANK_FROM = "Choose exactly {k} candidate ids to measure next so that as many as possible are hits"
RANK_TO = ("Rank all {m} candidate ids from most to least likely to be a hit; the first {k} of your ranking "
           "will be measured next, so order them so that as many as possible of the first {k} are hits")
JSON_FROM = '{"chosen": [ids], "rationale": "<= 40 words"}'
JSON_TO = '{"ranking": [every candidate id exactly once, best first], "rationale": "<= 40 words"}'
USER_FROM = "Candidates ({m}, choose {k}):"
USER_TO = "Candidates ({m}; rank all {m}, the first {k} will be measured):"
RETRY_PARSE = ("Invalid reply: it was not one parseable JSON object. Return exactly {k} distinct candidate ids from "
               "the list as the JSON object requested, and nothing else.")
RETRY = ("Invalid reply: your list had {n} entries ({dup} duplicates, {bad} not in the candidate list, {nonint} not "
         "integers); exactly {k} distinct candidate ids from the list are required. Return the corrected JSON only.")

VARIANTS = {  # name -> (frozen planner mode, presentation order)
    "base": ("named", "model"),               # names, scores visible, world-model order (the failing setting)
    "shuffled": ("named", "shuffled"),        # names, scores visible, seeded random order
    "blind": ("blind", "shuffled"),           # names, no scores, random order (frozen SYSTEM_BLIND)
    "anonymised": ("anonymous", "model"),     # D### codes, scores visible, world-model order
}


def now() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def chosen_lines(n_lines: int) -> list[int]:
    return sorted(np.random.default_rng(LINE_SEED).choice(n_lines, 3, replace=False).tolist())


def cells() -> list[dict]:
    """The predeclared design, in execution order (earlier cells are more important)."""
    lines = chosen_lines(39)
    out = []
    for contract in ("exact", "rank"):
        for k in KS:
            for line in lines:
                out.append({"block": "A", "contract": contract, "variant": "base", "k": k, "line": line,
                            "retry": contract == "exact"})
    for k in (32, 64, 128):
        for line in lines[:2]:
            out.append({"block": "A", "contract": "chunk16", "variant": "base", "k": k, "line": line, "retry": True})
    for contract in ("exact", "rank"):
        for variant in ("shuffled", "blind", "anonymised"):
            for line in lines:
                out.append({"block": "B", "contract": contract, "variant": variant, "k": 128, "line": line,
                            "retry": False})
    for i, cell in enumerate(out):
        cell["id"] = f"{i:03d}_{cell['contract']}_{cell['variant']}_k{cell['k']}_L{cell['line']}"
    return out


class State:
    """One line after STATE_ROUNDS world-model rounds of STATE_BATCH purchases."""

    def __init__(self, lib, line: int):
        self.lib, self.line = lib, line
        self.world = TransferWorld(lib, line, WorldConfig())
        rows = self.world.rows
        self.truth = lib.y[rows]
        measured = np.zeros(rows.size, bool)
        for _ in range(STATE_ROUNDS):
            idx = np.flatnonzero(measured)
            mean, var = self.world.posterior(idx, self.truth[idx])
            p = self.world.p_hit(mean, var)
            cand = np.flatnonzero(~measured)
            measured[cand[np.argsort(-p[cand], kind="stable")[:STATE_BATCH]]] = True
        self.measured = np.flatnonzero(measured)
        self.values = self.truth[self.measured]
        self.mean, var = self.world.posterior(self.measured, self.values)
        self.p_hit = self.world.p_hit(self.mean, var)
        cand = np.flatnonzero(~measured)
        self.order = cand[np.argsort(-self.p_hit[cand], kind="stable")]   # world-model order

    def menu(self, k: int) -> np.ndarray:
        return self.order[: 2 * k]


def build_messages(state: State, cell: dict, menu: np.ndarray, k: int) -> tuple[list[dict], list[int]]:
    """Frozen prompt for this variant (and contract edit); returns messages and presented id order."""
    mode, order = VARIANTS[cell["variant"]]
    arm = LLMPlannerArm(state.world, None, None, batch=k, mode=mode)
    shown = menu
    if order == "shuffled" and mode != "blind":     # blind permutes inside the frozen _prompt
        shown = np.random.default_rng([LINE_SEED, state.line, k]).permutation(menu)
    messages = arm._prompt(shown, state.mean, state.p_hit, state.measured, state.values, k)
    user = messages[1]["content"]
    header = f"Candidates ({menu.size}, choose {k}):"
    assert user.count(header) == 1, "frozen user header not found"
    table = user.split(header, 1)[1].strip().splitlines()[1:]
    presented = [int(row.split("|", 1)[0]) for row in table]
    assert sorted(presented) == sorted(menu.tolist()), "presented table does not match the menu"
    if order == "model":
        assert presented == menu.tolist(), "model-order presentation was permuted"
    if cell["contract"] == "rank":
        system = messages[0]["content"]
        m = menu.size
        for old, new in ((RANK_FROM.format(k=k), RANK_TO.format(m=m, k=k)), (JSON_FROM, JSON_TO)):
            assert system.count(old) == 1, f"rank edit failed: {old[:40]}"
            system = system.replace(old, new)
        assert user.count(USER_FROM.format(m=m, k=k)) == 1
        user = user.replace(USER_FROM.format(m=m, k=k), USER_TO.format(m=m, k=k))
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        assert "rank all" in messages[1]["content"] and '"ranking"' in messages[0]["content"]
    return messages, presented


def reservation(messages: list[dict]) -> tuple[int, float]:
    chars = sum(len(m["content"]) for m in messages) + len(FINAL_SYSTEM)
    tokens = int(math.ceil(chars / CHARS_PER_TOKEN_RESERVE))
    return tokens, (tokens * RATES["input_cache_miss"] + MAX_TOKENS * RATES["output"]) / 1e6


def check_list(items, allowed: list[int], need: int) -> dict:
    allowed_set = set(allowed)
    ints, nonint = [], 0
    for item in items if isinstance(items, list) else []:
        try:
            if isinstance(item, bool):
                raise TypeError
            value = int(item)
            if isinstance(item, float) and value != item:
                raise ValueError
            ints.append(value)
        except (TypeError, ValueError):
            nonint += 1
    seen, distinct_valid, dup, bad = set(), [], 0, 0
    for v in ints:
        if v not in allowed_set:
            bad += 1
        elif v in seen:
            dup += 1
        else:
            seen.add(v)
            distinct_valid.append(v)
    n = len(items) if isinstance(items, list) else 0
    return {"n": n, "nonint": nonint, "dup": dup, "bad": bad, "distinct_valid": distinct_valid,
            "exact": n == need and nonint == 0 and dup == 0 and bad == 0 and len(distinct_valid) == need}


class Caller:
    """Sequential provider caller with a hard pre-call ceiling and a full call log."""

    def __init__(self, out: Path):
        from agent import llm as llm_module
        from agent.llm import DeepSeekChatClient, MAESTROSettings

        self.llm = llm_module
        self.client = DeepSeekChatClient(MAESTROSettings.from_workspace(ROOT))
        if self.client.settings.chat_model.lower() != "deepseek-flash":
            raise SystemExit("configured chat model is not deepseek-flash; refusing")
        self.book = SpendBook(out / "spend.json", CEILING_USD)
        self.log = open(out / "calls.jsonl", "a", encoding="utf-8", newline="\n")
        self.attempts = 0
        original = llm_module.urlopen

        def counting(*args, **kwargs):
            self.attempts += 1
            return original(*args, **kwargs)

        llm_module.urlopen = counting
        self.stopped = False

    def call(self, label: str, messages: list[dict], meta: dict) -> dict:
        tokens, reserve = reservation(messages)
        record = {"label": label, "time": now(), "reserve_prompt_tokens": tokens, "reserve_usd": round(reserve, 6),
                  **meta}
        if self.stopped or self.book.total + reserve > CEILING_USD:
            self.stopped = True
            record.update({"code": "SPEND_CEILING", "spent_before": round(self.book.total, 6)})
            self.log.write(json.dumps(record) + "\n")
            self.log.flush()
            return record
        before = dict(self.client.provider_usage)
        attempts_before = self.attempts
        started = time.perf_counter()
        response, error = None, None
        try:
            response = self.client.complete(messages + [{"role": "system", "content": FINAL_SYSTEM}],
                                            model="deepseek-flash", temperature=0.0, max_tokens=MAX_TOKENS,
                                            json_output=False, thinking_enabled=False)
        except Exception as exc:  # recorded by type and code only; messages carry no secrets
            error = {"type": type(exc).__name__, "code": getattr(exc, "code", None)}
        seconds = time.perf_counter() - started
        after = self.client.provider_usage
        usage = {key: after.get(key, 0) - before.get(key, 0) for key in after if key != "calls"}
        decoded = after.get("calls", 0) - before.get("calls", 0)
        if decoded:
            self.book.charge(label, usage, seconds)
            priced = "provider_usage"
        else:  # no decoded response: billing unknown, charged at the reservation
            self.book.charge(label + ":reservation", {"prompt_tokens": tokens, "completion_tokens": MAX_TOKENS},
                             seconds)
            priced = "reservation"
        record.update({"seconds": round(seconds, 3), "http_attempts": self.attempts - attempts_before,
                       "usage": usage, "usd": round(self.book.entries[-1]["usd"], 7), "priced_by": priced,
                       "error": error})
        if response is not None:
            record.update({"finish_reason": response.finish_reason, "model": response.model,
                           "content": response.content, "content_chars": len(response.content)})
        self.log.write(json.dumps(record) + "\n")
        self.log.flush()
        return record


def parse(record: dict, key: str) -> tuple[object, str | None]:
    if record.get("code") == "SPEND_CEILING":
        return None, "SPEND_CEILING"
    if record.get("error"):
        return None, "TRANSPORT_OR_PROTOCOL_FAILURE"
    try:
        from agent.llm import json_object_from_text
        value = json_object_from_text(record["content"])
    except (json.JSONDecodeError, ValueError):
        return None, "PARSE_FAILURE"
    if not isinstance(value, dict):
        return None, "PARSE_FAILURE"
    return value.get(key), None


def run_exact(caller: Caller, state: State, cell: dict, menu: np.ndarray, k: int, label: str,
              retry: bool) -> dict:
    messages, presented = build_messages(state, cell, menu, k)
    attempts = []
    for attempt in range(2 if retry else 1):
        record = caller.call(f"{label}:a{attempt}", messages, {"cell": cell["id"], "attempt": attempt, "k": k,
                                                              "menu": int(menu.size)})
        items, failure = parse(record, "chosen")
        check = check_list(items, presented, k) if failure is None else None
        attempts.append({"record": record, "failure": failure, "check": check, "items": items})
        if failure == "SPEND_CEILING" or (check is not None and check["exact"]):
            break
        if attempt == 0 and retry and record.get("content") is not None:
            if check is None:
                text = RETRY_PARSE.format(k=k)
            else:
                text = RETRY.format(n=check["n"], dup=check["dup"], bad=check["bad"], nonint=check["nonint"], k=k)
            messages = messages + [{"role": "assistant", "content": record["content"]},
                                   {"role": "user", "content": text}]
        # after a transport failure (no content) the original request is resent once
    return {"presented": presented, "attempts": attempts}


def run_cell(caller: Caller, state: State, cell: dict) -> dict:
    k = cell["k"]
    menu = state.menu(k)
    result = {"cell": cell, "menu_model_order": menu.tolist(), "wm_topk": menu[:k].tolist()}
    if cell["contract"] == "exact":
        r = run_exact(caller, state, cell, menu, k, cell["id"], cell["retry"])
        result.update(presented=r["presented"], calls=[serial(a) for a in r["attempts"]])
        last = r["attempts"][-1]
        first = r["attempts"][0]
        result["valid_first"] = bool(first["check"] and first["check"]["exact"])
        result["valid"] = bool(last["check"] and last["check"]["exact"])
        result["failure"] = last["failure"] or (None if result["valid"] else "INVALID_SELECTION")
        result["reply_order"] = (first["check"] or {}).get("distinct_valid", [])
        result["selection"] = last["check"]["distinct_valid"] if result["valid"] else None
    elif cell["contract"] == "rank":
        messages, presented = build_messages(state, cell, menu, k)
        record = caller.call(f"{cell['id']}:a0", messages, {"cell": cell["id"], "attempt": 0, "k": k,
                                                           "menu": int(menu.size)})
        items, failure = parse(record, "ranking")
        check = check_list(items, presented, menu.size) if failure is None else None
        result.update(presented=presented, calls=[serial({"record": record, "failure": failure, "check": check,
                                                          "items": items})])
        prefix = check_list(items[:k], presented, k) if check and isinstance(items, list) else None
        result["valid_first"] = result["valid"] = bool(check and check["exact"])
        result["prefix_valid"] = bool(prefix and prefix["exact"])
        result["failure"] = failure or (None if result["valid"] else "INVALID_RANKING")
        result["reply_order"] = (check or {}).get("distinct_valid", [])
        result["selection"] = prefix["distinct_valid"] if result["prefix_valid"] else None
    else:  # chunk16
        presented_full = None
        chosen: list[int] = []
        calls, all_first, all_valid, failure = [], True, True, None
        j = 0
        while len(chosen) < k:
            kk = min(CHUNK, k - len(chosen))
            remaining = np.array([i for i in menu.tolist() if i not in set(chosen)])
            r = run_exact(caller, state, cell, remaining, kk, f"{cell['id']}:c{j}", cell["retry"])
            presented_full = presented_full or r["presented"]
            calls.extend(serial(a, chunk=j) for a in r["attempts"])
            first, last = r["attempts"][0], r["attempts"][-1]
            all_first &= bool(first["check"] and first["check"]["exact"])
            ok = bool(last["check"] and last["check"]["exact"])
            all_valid &= ok
            if last["failure"] == "SPEND_CEILING":
                failure = "SPEND_CEILING"
                break
            if not ok:
                failure = failure or last["failure"] or "INVALID_CHUNK"
            got = (last["check"] or {}).get("distinct_valid", [])[:kk]
            got += [i for i in remaining.tolist() if i not in set(got)][: kk - len(got)]  # frozen repair rule
            chosen += got
            j += 1
        result.update(presented=presented_full, calls=calls, valid_first=all_first and failure is None,
                      valid=all_valid and failure is None, failure=failure,
                      reply_order=chosen, selection=chosen if all_valid and failure is None else None,
                      chunks=j)
    return result


def serial(attempt: dict, chunk: int | None = None) -> dict:
    record, check = attempt["record"], attempt["check"]
    return {"label": record["label"], "chunk": chunk, "code": record.get("code"), "failure": attempt["failure"],
            "finish_reason": record.get("finish_reason"), "seconds": record.get("seconds"),
            "http_attempts": record.get("http_attempts"), "usd": record.get("usd"), "usage": record.get("usage"),
            "content_chars": record.get("content_chars"),
            "check": None if check is None else {key: check[key] for key in ("n", "nonint", "dup", "bad", "exact")}
            | {"n_distinct_valid": len(check["distinct_valid"])}}


def make_plan() -> dict:
    lib = load_library(LIBRARY)
    lines = chosen_lines(len(lib.lines))
    states = {line: State(lib, line) for line in lines}
    design = cells()
    # Calibrate characters per prompt token on the recorded dev_v2 round-0 named calls.
    spend = json.loads((ROOT / "research/certified_discovery/results/dev_llm_20261003_v2/spend.json")
                       .read_text(encoding="utf-8"))
    recorded = {e["label"]: e["prompt_tokens"] for e in spend["entries"]}
    ratios = []
    for line in lines:
        world = TransferWorld(lib, line, WorldConfig())
        none, empty = np.array([], int), np.array([])
        mean, var = world.posterior(none, empty)
        p = world.p_hit(mean, var)
        menu = np.argsort(-p, kind="stable")[:30]
        arm = LLMPlannerArm(world, None, None, batch=15, mode="named")
        msgs = arm._prompt(menu, mean, p, none, empty, 15)
        chars = sum(len(m["content"]) for m in msgs) + len(FINAL_SYSTEM)
        if f"llm_named:{line}:0" in recorded:
            ratios.append(chars / recorded[f"llm_named:{line}:0"])
    cpt = float(np.mean(ratios)) if ratios else 3.0
    rows, exp_total, worst_total, first_calls, max_calls = [], 0.0, 0.0, 0, 0
    for cell in design:
        k = cell["k"]
        menu = states[cell["line"]].menu(k)
        if cell["contract"] == "chunk16":
            n_calls = math.ceil(k / CHUNK)
            sizes = [(menu.size - CHUNK * j, min(CHUNK, k - CHUNK * j)) for j in range(n_calls)]
        else:
            n_calls, sizes = 1, [(menu.size, k)]
        exp_usd, worst_usd = 0.0, 0.0
        for m_size, kk in sizes:
            sub = menu[:m_size]
            msgs, _ = build_messages(states[cell["line"]], cell, sub, kk)
            chars = sum(len(m["content"]) for m in msgs) + len(FINAL_SYSTEM)
            out_ids = m_size if cell["contract"] == "rank" else kk
            exp_out = 3.5 * out_ids + 60
            if cell["contract"] == "exact" and k >= 64:
                exp_out = 3.5 * m_size + 60     # the recorded failure: the whole menu comes back
            exp_usd += (chars / cpt * RATES["input_cache_miss"] + exp_out * RATES["output"]) / 1e6
            worst_one = reservation(msgs)[1]
            worst_usd += worst_one * (2 if cell["retry"] else 1)
        if cell["retry"] and cell["contract"] == "exact" and k >= 64:
            exp_usd *= 2                          # expect a retry where the recorded failure applies
        first_calls += n_calls
        max_calls += n_calls * (2 if cell["retry"] else 1)
        exp_total += exp_usd
        worst_total += worst_usd
        rows.append({**cell, "menu": int(menu.size), "first_attempt_calls": n_calls,
                     "max_calls": n_calls * (2 if cell["retry"] else 1), "expected_usd": round(exp_usd, 5),
                     "worst_usd": round(worst_usd, 5)})
    plan = {
        "written": now(), "purpose": "diagnose the exact-cardinality failure of the LLM planner contract (WS4)",
        "data": {"library": str(LIBRARY.relative_to(ROOT)), "library_sha256": sha256(LIBRARY),
                 "lines": {str(l): lib.lines[l] for l in lines}, "line_seed": LINE_SEED,
                 "state": f"{STATE_ROUNDS} world-model rounds of {STATE_BATCH} purchases (30 measured)",
                 "menu": "top 2k untested by frozen TransferWorld P(hit); 583 candidates per line",
                 "ALMANAC": "not loaded"},
        "provider": {"model": "deepseek-flash", "temperature": 0.0, "thinking": "disabled", "max_tokens": MAX_TOKENS,
                     "final_system_message": FINAL_SYSTEM, "rates_usd_per_mtok": RATES},
        "factors": {"k": list(KS), "menu": "2k",
                    "contract": {"exact": "frozen SYSTEM / SYSTEM_BLIND prompt, choose exactly k",
                                 "rank": "frozen prompt with asserted edits: rank all 2k ids; selection = first k",
                                 "chunk16": "frozen exact prompt per call, choose min(16, remaining) from the menu "
                                            "minus ids already chosen, world-model order kept"},
                    "variant": {name: {"mode": mode, "order": order} for name, (mode, order) in VARIANTS.items()}},
        "design": {"block_A": "contract x k at the base variant (names, scores visible, model order): exact and rank "
                              "at all k on 3 lines; chunk16 at k in {32, 64, 128} on the first 2 lines",
                   "block_B": "k = 128 only, 3 lines: exact and rank under shuffled, blind and anonymised"},
        "rules": {
            "exact_valid": "reply parses, list length == k, all integers, no duplicates, all in the presented menu",
            "rank_valid_strict": "list is a permutation of the 2k menu",
            "rank_prefix_valid": "first k entries are k distinct menu integers (reported separately, not as strict)",
            "chunk_valid": "every chunk call valid (after its allowed retry)",
            "retry": "exact (block A) and every chunk16 call: at most one retry, sent only after a reply that was "
                     "received but invalid or unparseable, with the frozen messages + the reply + a corrective "
                     "message stating counts (or that the reply did not parse); after a transport failure the original "
                     "request is resent once; rank and block B: no retry. A retry is a charged call; 'valid after "
                     "retry' is reported apart from 'valid at first attempt'.",
            "repair": "frozen rule (first k distinct valid ids, fill from world-model order) is applied only inside "
                      "chunk16 to continue the sequence; a repaired selection is never counted as valid",
            "transport": "the client's own transport retries (<= 4 HTTP attempts) are counted per call; a call with "
                         "no decoded response is charged at its reservation",
            "ceiling": f"hard USD {CEILING_USD}: before every call, spent + reservation (prompt chars / "
                       f"{CHARS_PER_TOKEN_RESERVE} at cache-miss rate + {MAX_TOKENS} output tokens) must be <= ceiling; "
                       "otherwise the call and all later cells are skipped and recorded as SPEND_CEILING",
            "order": "cells run sequentially in the listed order (contract x k first, factor probes last)",
        },
        "measures": ["exact-cardinality rate (first attempt, after retry)", "returned count / k", "duplicates",
                     "ids not in menu", "non-integers", "parse failures", "finish_reason=length (truncation)",
                     "latency", "prompt/completion tokens", "USD per call and per valid selection",
                     "echo of presented order (prefix match, Kendall tau vs presented and vs model order)",
                     "overlap of the selection with the world-model top k and the presented top k",
                     "descriptive hits of the selection vs world-model top k (exposed labels; no inference)"],
        "calibration": {"chars_per_prompt_token_dev_v2_round0": round(cpt, 3), "lines_used": len(ratios)},
        "cost": {"first_attempt_calls": first_calls, "max_calls_with_retries": max_calls,
                 "expected_usd": round(exp_total, 4), "worst_case_usd_if_every_call_hits_max_tokens": round(worst_total, 4),
                 "ceiling_usd": CEILING_USD},
        "cells": rows,
        "code_sha256": file_sha(Path(__file__)),
    }
    PLAN.write_text(json.dumps(plan, indent=1), encoding="utf-8")
    return plan


def run() -> int:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    if plan["code_sha256"] != file_sha(Path(__file__)):
        raise SystemExit("plan.json was written for a different diagnostic.py; re-plan before any call")
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}: records are write-once")
    OUT.mkdir(parents=True)
    lib = load_library(LIBRARY)
    states = {int(l): State(lib, int(l)) for l in plan["data"]["lines"]}
    caller = Caller(OUT)
    started = now()
    with open(OUT / "selections.jsonl", "w", encoding="utf-8", newline="\n") as handle:
        for cell in cells():
            result = run_cell(caller, states[cell["line"]], cell)
            truth = states[cell["line"]].truth
            hit = lambda ids: None if ids is None else int((truth[np.array(ids, int)] > lib.threshold).sum())  # noqa
            result["hits_selection"] = hit(result["selection"])
            result["hits_wm_topk"] = hit(result["wm_topk"])
            result["hits_menu"] = hit(result["menu_model_order"])
            handle.write(json.dumps(result) + "\n")
            handle.flush()
            print(cell["id"], "valid", result["valid"], "first", result["valid_first"], "failure", result["failure"],
                  "spent", round(caller.book.total, 4), flush=True)
    caller.log.close()
    manifest = {"started": started, "finished": now(), "plan_sha256": file_sha(PLAN), "code_sha256": file_sha(Path(__file__)),
                "library_sha256": sha256(LIBRARY), "spend_usd": caller.book.total, "priced_calls": len(caller.book.entries),
                "http_attempts": caller.attempts, "stopped_by_ceiling": caller.stopped,
                "provider_usage": caller.client.provider_usage, "python": sys.version.split()[0],
                "numpy": np.__version__}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("spend_usd", "priced_calls", "http_attempts", "stopped_by_ceiling")}))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan", action="store_true")
    group.add_argument("--run", action="store_true")
    args = parser.parse_args(argv)
    if args.plan:
        if OUT.exists():
            raise SystemExit("results exist: the plan cannot be rewritten after calls were made")
        plan = make_plan()
        print(json.dumps({**plan["cost"], **plan["calibration"]}))
        return 0
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
