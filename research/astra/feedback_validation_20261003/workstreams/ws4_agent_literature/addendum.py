"""Addendum: which surface difference from the confirmatory screen breaks the exact-k contract?

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws4_agent_literature/addendum.py
- Purpose: the predeclared diagnostic (diagnostic.py, plan.json) found the frozen exact-k prompt
  VALID at k = 128 on O'Neil, so k alone does not reproduce the confirmatory failure (0 of 468
  exact replies on NCI-ALMANAC). This addendum, declared in plan_addendum.json before any of its
  calls, tests on O'Neil only the surface differences that can be imitated without opening
  ALMANAC: 4-digit candidate ids, round-0 state (no line evidence), an inflated P(hit) display,
  and concurrent calls (the confirmatory run used 12 threads).
- Core points:
  - Every prompt is still built by the frozen `LLMPlannerArm._prompt` via diagnostic.build_messages;
    the id remap rewrites only the leading id of each table row (seeded injective map into
    1000-9999), and replies are mapped back before validation, so an unmapped or invented id stays
    invalid. The inflated display is p ** 0.25 (same order), a synthetic manipulation.
  - Spend is cumulative with the main run: the ceiling for this addendum is USD 0.80 minus the
    main run's recorded spend, enforced before every call (and for a concurrent batch, before the
    batch, on the sum of reservations).
  - A conditional follow-up (rank on 3 lines, chunk16 on 1 line, no retries) runs only at the first
    core condition with >= 2 of 3 invalid exact selections.
- Interfaces: `python addendum.py --plan | --run`; summarise.py reads results_addendum/.
- Depends on: diagnostic.py (unchanged; imported), numpy.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import diagnostic as D  # noqa: E402

OUT = HERE / "results_addendum"
PLAN = HERE / "plan_addendum.json"
K = 128
CONCURRENCY = 6
CORE = [  # (name, id4, round0, inflate, mode-variant)
    ("id4_named", True, False, False, "base"),
    ("id4_blind", True, False, False, "blind"),
    ("round0_named", False, True, False, "base"),
    ("round0_blind", False, True, False, "blind"),
    ("round0_id4_named", True, True, False, "base"),
    ("round0_id4_blind", True, True, False, "blind"),
    ("inflated_named", False, False, True, "base"),
    ("round0_id4_inflated_named", True, True, True, "base"),
]
CONCURRENT = ("round0_id4_named", "round0_id4_blind")
ROW = re.compile(r"^(\d+) \|", re.M)


class Condition:
    active: dict | None = None   # {"forward": {native: code}, "inverse": {code: native}} or None


def id_map(line: int) -> dict:
    codes = np.random.default_rng([D.LINE_SEED, line, 4]).choice(np.arange(1000, 10000), size=583, replace=False)
    forward = {i: int(c) for i, c in enumerate(codes)}
    return {"forward": forward, "inverse": {c: i for i, c in forward.items()}}


def make_state(lib, line: int, round0: bool, inflate: bool):
    state = D.State(lib, line)
    if round0:
        state = copy.copy(state)
        none, empty = np.array([], int), np.array([])
        state.measured, state.values = none, empty
        state.mean, var = state.world.posterior(none, empty)
        state.p_hit = state.world.p_hit(state.mean, var)
        state.order = np.argsort(-state.p_hit, kind="stable")
    if inflate:
        state = copy.copy(state)
        state.p_hit = state.p_hit ** 0.25      # display only; the menu order is unchanged (monotone)
    return state


_build, _parse = D.build_messages, D.parse


def build_messages(state, cell, menu, k):
    messages, presented = _build(state, cell, menu, k)
    if Condition.active is not None:
        fwd = Condition.active["forward"]
        user = messages[1]["content"]
        head, sep, table = user.partition("\nid |")
        assert sep, "table header not found"
        new_table, count = ROW.subn(lambda m: f"{fwd[int(m.group(1))]} |", table)
        assert count == len(presented), "id remap did not touch every row"
        messages = [messages[0], {"role": "user", "content": head + sep + new_table}]
    return messages, presented


def parse(record, key):
    items, failure = _parse(record, key)
    if failure is None and Condition.active is not None and isinstance(items, list):
        inv = Condition.active["inverse"]
        mapped = []
        for item in items:
            try:
                value = int(item)
                mapped.append(inv.get(value, value + 100000))   # an unknown code can never be a menu id
            except (TypeError, ValueError):
                mapped.append(item)
        items = mapped
    return items, failure


D.build_messages, D.parse = build_messages, parse


def core_cells(lines: list[int]) -> list[dict]:
    out = []
    for name, id4, round0, inflate, variant in CORE:
        for line in lines:
            out.append({"block": "C", "contract": "exact", "variant": variant, "k": K, "line": line, "retry": False,
                        "factor": name, "id4": id4, "round0": round0, "inflate": inflate,
                        "id": f"C_{name}_L{line}"})
    return out


def followup_cells(lines: list[int], name: str) -> list[dict]:
    spec = {n: (i, r, f, v) for n, i, r, f, v in CORE}[name]
    id4, round0, inflate, variant = spec
    base = {"block": "F", "variant": variant, "k": K, "retry": False, "factor": name, "id4": id4,
            "round0": round0, "inflate": inflate}
    cells = [{**base, "contract": "rank", "line": l, "id": f"F_rank_{name}_L{l}"} for l in lines]
    cells.append({**base, "contract": "chunk16", "line": lines[0], "id": f"F_chunk16_{name}_L{lines[0]}"})
    return cells


def plan() -> dict:
    main_spend = json.loads((D.OUT / "spend.json").read_text(encoding="utf-8"))["total_usd"]
    lib = D.load_library(D.LIBRARY)
    lines = D.chosen_lines(len(lib.lines))
    expected, worst, rows = 0.0, 0.0, []
    for cell in core_cells(lines):
        Condition.active = id_map(cell["line"]) if cell["id4"] else None
        state = make_state(lib, cell["line"], cell["round0"], cell["inflate"])
        msgs, _ = build_messages(state, cell, state.menu(K), K)
        tokens, reserve = D.reservation(msgs)
        n = 2 if cell["factor"] in CONCURRENT else 1
        exp = n * (tokens / 1.25 * D.RATES["input_cache_miss"] + (3.5 * 2 * K + 60) * D.RATES["output"]) / 1e6
        expected, worst = expected + exp, worst + n * reserve
        rows.append({**cell, "calls": n, "reserve_usd_each": round(reserve, 5)})
    # follow-up worst case: rank on 3 lines (one call each) + chunk16 on one line (8 calls, no retry)
    follow_worst = 3 * max(r["reserve_usd_each"] for r in rows) + 8 * max(r["reserve_usd_each"] for r in rows)
    Condition.active = None
    doc = {
        "written": D.now(),
        "why": ("plan.json's predeclared base cell (frozen exact-k prompt, named, model order, k = 128) was VALID "
                "in 3 of 3 O'Neil lines, so the confirmatory failure is not explained by k. This addendum is "
                "declared after seeing the main results and before any addendum call."),
        "data": "O'Neil only; same 3 lines (HT144, OV90, UACC62); ALMANAC is not loaded",
        "k": K, "menu": 2 * K, "contract": "frozen exact-k prompt, no retry",
        "core_conditions": {n: {"id4": i, "round0": r, "inflate": f, "variant": v} for n, i, r, f, v in CORE},
        "transforms": {"id4": "seeded injective map of candidate index -> 1000..9999 (rng [20261003, line, 4]); "
                              "only the leading id of each table row is rewritten; replies mapped back",
                       "round0": "no purchases: evidence line reads 'no combination measured yet'; menu = prior top 256",
                       "inflate": "displayed P(hit) = p ** 0.25 (monotone, order unchanged; synthetic display probe)"},
        "concurrency": f"{', '.join(CONCURRENT)} are re-sent as one batch of {CONCURRENCY} concurrent calls "
                       "(the confirmatory run used 12 threads)",
        "followup_rule": ("if any core condition has >= 2 of 3 invalid exact selections, run at the FIRST such "
                          "condition (listed order): rank on 3 lines and chunk16 on the first line, no retries; "
                          "otherwise record NOT_TRIGGERED"),
        "ceiling": {"ws4_total_usd": 0.80, "main_run_spend_usd": main_spend,
                    "addendum_ceiling_usd": round(0.80 - main_spend, 6),
                    "rule": "spent + reservation <= addendum ceiling before every call; a concurrent batch "
                            "reserves the sum of its calls first"},
        "cost": {"core_calls": sum(r["calls"] for r in rows), "followup_max_calls": 11,
                 "expected_usd_core": round(expected, 4), "worst_usd_core": round(worst, 4),
                 "worst_usd_followup": round(follow_worst, 4)},
        "cells": rows,
        "code_sha256": {"addendum.py": D.file_sha(Path(__file__)), "diagnostic.py": D.file_sha(HERE / "diagnostic.py")},
    }
    PLAN.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    return doc


def finish(result, lib, state):
    truth = state.truth
    hit = lambda ids: None if ids is None else int((truth[np.array(ids, int)] > lib.threshold).sum())  # noqa: E731
    result["hits_selection"] = hit(result["selection"])
    result["hits_wm_topk"] = hit(result["wm_topk"])
    result["hits_menu"] = hit(result["menu_model_order"])
    return result


def run() -> int:
    doc = json.loads(PLAN.read_text(encoding="utf-8"))
    if doc["code_sha256"] != {"addendum.py": D.file_sha(Path(__file__)), "diagnostic.py": D.file_sha(HERE / "diagnostic.py")}:
        raise SystemExit("plan_addendum.json does not match the code; re-plan before any call")
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    OUT.mkdir(parents=True)
    D.CEILING_USD = doc["ceiling"]["addendum_ceiling_usd"]      # read by Caller.call at call time
    lib = D.load_library(D.LIBRARY)
    lines = D.chosen_lines(len(lib.lines))
    caller = D.Caller(OUT)
    started = D.now()
    results = []
    handle = open(OUT / "selections.jsonl", "w", encoding="utf-8", newline="\n")

    def do(cell):
        Condition.active = id_map(cell["line"]) if cell["id4"] else None
        state = make_state(lib, cell["line"], cell["round0"], cell["inflate"])
        result = finish(D.run_cell(caller, state, cell), lib, state)
        Condition.active = None
        handle.write(json.dumps(result) + "\n")
        handle.flush()
        results.append(result)
        print(cell["id"], "valid", result["valid"], "failure", result["failure"], "spent", round(caller.book.total, 4),
              flush=True)

    for cell in core_cells(lines):
        do(cell)
    # concurrent replicate: same prompts, sent together; bookkeeping after the batch
    batch = [dict(c, id=c["id"].replace("C_", "P_"), block="P") for c in core_cells(lines) if c["factor"] in CONCURRENT]
    prepared = []
    for cell in batch:
        Condition.active = id_map(cell["line"]) if cell["id4"] else None
        state = make_state(lib, cell["line"], cell["round0"], cell["inflate"])
        msgs, presented = build_messages(state, cell, state.menu(K), K)
        prepared.append((cell, state, msgs, presented, dict(Condition.active) if Condition.active else None))
        Condition.active = None
    reserve = sum(D.reservation(p[2])[1] for p in prepared)
    log = open(OUT / "calls.jsonl", "a", encoding="utf-8", newline="\n")
    if caller.book.total + reserve > D.CEILING_USD:
        log.write(json.dumps({"label": "concurrent_batch", "code": "SPEND_CEILING", "reserve_usd": reserve}) + "\n")
    else:
        def send(item):
            t0 = time.perf_counter()
            try:
                resp = caller.client.complete(item[2] + [{"role": "system", "content": D.FINAL_SYSTEM}],
                                              model="deepseek-flash", temperature=0.0, max_tokens=D.MAX_TOKENS,
                                              json_output=False, thinking_enabled=False)
                return resp, None, time.perf_counter() - t0
            except Exception as exc:
                return None, {"type": type(exc).__name__, "code": getattr(exc, "code", None)}, time.perf_counter() - t0

        with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
            replies = list(pool.map(send, prepared))
        for (cell, state, msgs, presented, mapping), (resp, error, secs) in zip(prepared, replies):
            label = f"{cell['id']}:a0"
            if resp is not None:
                caller.book.charge(label, dict(resp.usage), secs)
                priced = "response_usage"
            else:
                tokens, _ = D.reservation(msgs)
                caller.book.charge(label + ":reservation", {"prompt_tokens": tokens, "completion_tokens": D.MAX_TOKENS},
                                   secs)
                priced = "reservation"
            record = {"label": label, "time": D.now(), "seconds": round(secs, 3), "usage": dict(resp.usage) if resp else {},
                      "usd": round(caller.book.entries[-1]["usd"], 7), "priced_by": priced, "error": error,
                      "cell": cell["id"], "attempt": 0, "k": K, "menu": 2 * K, "concurrent": CONCURRENCY}
            if resp is not None:
                record.update({"finish_reason": resp.finish_reason, "model": resp.model, "content": resp.content,
                               "content_chars": len(resp.content)})
            log.write(json.dumps(record) + "\n")
            Condition.active = mapping
            items, failure = parse(record, "chosen")
            Condition.active = None
            check = D.check_list(items, presented, K) if failure is None else None
            result = {"cell": cell, "menu_model_order": state.menu(K).tolist(), "wm_topk": state.menu(K)[:K].tolist(),
                      "presented": presented, "calls": [D.serial({"record": record, "failure": failure, "check": check,
                                                                   "items": items})],
                      "valid_first": bool(check and check["exact"]), "valid": bool(check and check["exact"]),
                      "failure": failure or (None if check and check["exact"] else "INVALID_SELECTION"),
                      "reply_order": (check or {}).get("distinct_valid", []),
                      "selection": check["distinct_valid"] if check and check["exact"] else None}
            result = finish(result, lib, state)
            handle.write(json.dumps(result) + "\n")
            handle.flush()
            results.append(result)
            print(cell["id"], "valid", result["valid"], "failure", result["failure"], flush=True)
    log.close()
    # conditional follow-up
    trigger = None
    for name, *_ in CORE:
        rows = [r for r in results if r["cell"].get("factor") == name and r["cell"]["block"] == "C"]
        if sum(not r["valid"] for r in rows) >= 2:
            trigger = name
            break
    if trigger:
        for cell in followup_cells(lines, trigger):
            do(cell)
    handle.close()
    caller.log.close()
    manifest = {"started": started, "finished": D.now(), "plan_sha256": D.file_sha(PLAN),
                "followup": trigger or "NOT_TRIGGERED", "spend_usd": caller.book.total,
                "priced_calls": len(caller.book.entries), "http_attempts_sequential": caller.attempts,
                "ws4_cumulative_usd": caller.book.total + doc["ceiling"]["main_run_spend_usd"],
                "stopped_by_ceiling": caller.stopped}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(json.dumps(manifest))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan", action="store_true")
    group.add_argument("--run", action="store_true")
    args = parser.parse_args(argv)
    if args.plan:
        if OUT.exists():
            raise SystemExit("addendum results exist; the plan cannot be rewritten")
        print(json.dumps(plan()["cost"]))
        return 0
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
