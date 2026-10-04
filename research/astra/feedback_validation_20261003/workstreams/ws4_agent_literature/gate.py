"""Gate test: does the LLM planner add anything beyond presentation order and displayed scores?

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws4_agent_literature/gate.py
- Purpose: bounded diagnostic on O'Neil development data (exposed; not confirmation). In every
  round of the deterministic world-model campaign of every line, two LLM arms choose k of the
  same 2k menu, shown in the same shuffled order with the same line evidence:
  - L_true: drug names + the world model's TRUE scores;
  - L_perm: drug names + the score tuples (P(hit), predicted label, pair mean in other lines)
    PERMUTED across menu rows, so the numbers carry no information about the pair.
  Contrasts are paired on the same menu: E1 = L_true - sort-by-score (the world model's top k);
  E2 = L_perm - first-k-presented (a uniformly random subset of the menu).
- Core points:
  - Contract: frozen exact-k prompt (k <= 15, one call per round), candidate ids <= 3 digits,
    presented order and raw replies logged, max_tokens 600 (replies use ~85-160 tokens).
  - One corrective retry per invalid or unparseable reply (charged, counted, reported as
    "valid after retry"). A harness repair (first distinct valid ids, filled from the arm's
    deterministic rule) is a SEPARATE fallback policy and never enters the LLM contrasts.
  - Every call is priced from the provider-usage delta, including replies that fail to parse;
    a call with no decoded response is charged at its reservation and marked unknown-actual.
  - Hard ceiling USD 0.40 of new spend, enforced before every call (WS4 cumulative < 0.80).
  - Evaluation is ONE-STEP and paired: the state of each round is the frozen world model after
    the deterministic campaign's purchases; LLM picks do not feed back into later rounds.
- Interfaces: `python gate.py --plan | --run | --analyse`.
- Depends on: diagnostic.py (Caller, parse, check_list, retry texts; imported unchanged), the
  frozen research.certified_discovery modules (import only), numpy.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import diagnostic as D  # noqa: E402

OUT = HERE / "results_gate"
PLAN = HERE / "gate_plan.json"
SUMMARY = HERE / "gate_summary.json"
GATE_SEED = 20261004
NEW_CEILING_USD = 0.40
WS4_PRIOR_FILES = (HERE / "results/spend.json", HERE / "results_addendum/spend.json")
MAX_TOKENS = 600
BOOT = 10000
ROW = re.compile(r"^(\d+) \| [^|]+ \| [^|]+ \| ([0-9.]+) \| (-?[0-9.]+) \| (-?[0-9.]+)$", re.M)
ARMS = ("L_true", "L_perm")


def campaign_states(lib, line: int) -> list[dict]:
    """The deterministic world-model campaign (sort by P(hit)); one state per round."""
    world = D.TransferWorld(lib, line, D.WorldConfig())
    truth = lib.y[world.rows]
    n = world.rows.size
    budget = int(math.ceil(0.10 * n))
    batch = int(math.ceil(budget / 4))
    measured = np.zeros(n, bool)
    states = []
    for r in range(4):
        k = int(min(batch, budget - measured.sum()))
        idx = np.flatnonzero(measured)
        mean, var = world.posterior(idx, truth[idx])
        p = world.p_hit(mean, var)
        cand = np.flatnonzero(~measured)
        order = cand[np.argsort(-p[cand], kind="stable")]
        menu = order[: 2 * k]
        states.append({"round": r, "k": k, "measured": idx, "values": truth[idx], "mean": mean, "p_hit": p,
                       "menu": menu, "world": world, "truth": truth})
        measured[order[:k]] = True
    return states


def arm_messages(lib, st: dict, line: int, arm: str):
    """Frozen named prompt, shuffled order; L_perm permutes score tuples across menu rows."""
    menu, k = st["menu"], st["k"]
    presented = np.random.default_rng([GATE_SEED, line, st["round"]]).permutation(menu)
    world, mean, p = st["world"], st["mean"], st["p_hit"]
    if arm == "L_perm":
        sigma = np.random.default_rng([GATE_SEED, line, st["round"], 7]).permutation(menu.size)
        source = menu[sigma]
        p, mean = p.copy(), mean.copy()
        world = copy.copy(world)
        world.X_target = world.X_target.copy()
        p[menu], mean[menu] = st["p_hit"][source], st["mean"][source]
        world.X_target[menu, 0] = st["world"].X_target[source, 0]
    planner = D.LLMPlannerArm(world, None, None, batch=k, mode="named")
    messages = planner._prompt(presented, mean, p, st["measured"], st["values"], k)
    rows = ROW.findall(messages[1]["content"])
    assert [int(r[0]) for r in rows] == presented.tolist(), "presented order not reproduced in the table"
    shown_p = {int(r[0]): float(r[1]) for r in rows}
    for i in presented[:3]:
        assert abs(shown_p[int(i)] - round(float(p[i]), 2)) < 1e-9, "displayed P(hit) mismatch"
    if arm == "L_perm":
        assert any(abs(shown_p[int(i)] - round(float(st["p_hit"][i]), 2)) > 1e-9 for i in menu), "scores not permuted"
    # deterministic references on the SAME menu
    disp_rank = sorted(presented.tolist(), key=lambda i: (-p[i], list(menu).index(i)))
    return messages, presented.tolist(), {
        "R_sort_true": menu[:k].tolist(),                  # world-model top k = sort by true score
        "R_sort_displayed": disp_rank[:k],                # sort by the numbers this arm was shown
        "R_order": presented[:k].tolist(),                # first k presented = random subset of the menu
    }


def plan() -> dict:
    lib = D.load_library(D.LIBRARY)
    prior = sum(json.loads(p.read_text(encoding="utf-8"))["total_usd"] for p in WS4_PRIOR_FILES)
    calls, chars_total, reserve_total = 0, 0, 0.0
    for line in range(len(lib.lines)):
        for st in campaign_states(lib, line):
            for arm in ARMS:
                msgs, _, _ = arm_messages(lib, st, line, arm)
                chars = sum(len(m["content"]) for m in msgs) + len(D.FINAL_SYSTEM)
                chars_total += chars
                reserve_total += (math.ceil(chars / D.CHARS_PER_TOKEN_RESERVE) * D.RATES["input_cache_miss"]
                                  + MAX_TOKENS * D.RATES["output"]) / 1e6
                calls += 1
    expected = (chars_total / 2.2 * D.RATES["input_cache_miss"] + calls * 120 * D.RATES["output"]) / 1e6
    doc = {
        "written": D.now(),
        "question": "does the LLM add decision value beyond presentation order and displayed scores?",
        "data": {"library": "O'Neil 2016 (data/processed/certified_discovery/oneil_v1.npz), EXPOSED development data; "
                            "hits are the O'Neil primary-screen label (> 10); this is a diagnostic, not confirmation",
                 "library_sha256": D.sha256(D.LIBRARY), "lines": len(lib.lines), "rounds": 4, "k": "15, 15, 15, 14",
                 "state": "frozen TransferWorld after the deterministic world-model campaign's purchases (sort by "
                          "P(hit)); menu = top 2k untested; identical menu, line evidence and presented order for both arms"},
        "arms": {"L_true": "LLM, names + true scores, shuffled order (seed [20261004, line, round])",
                 "L_perm": "LLM, names + score tuples permuted across menu rows (seed [20261004, line, round, 7]), "
                           "same shuffled order",
                 "R_sort_true": "deterministic world-model top k (sort by true score)",
                 "R_order": "deterministic first k presented (uniform random subset of the menu)",
                 "R_sort_displayed": "deterministic sort by the scores the arm was shown (= R_sort_true for L_true)"},
        "contract": {"prompt": "frozen LLMPlannerArm named prompt (SYSTEM), exact k, one call per round",
                     "ids": "O'Neil candidate indices 0..582 (<= 3 digits)", "model": "deepseek-flash",
                     "temperature": 0.0, "thinking": "disabled", "max_tokens": MAX_TOKENS,
                     "logging": "presented order, displayed numbers, raw replies (results_gate/calls.jsonl), usage, latency"},
        "rules": {
            "valid": "parsed list of exactly k distinct integers, all in the presented menu",
            "retry": "one corrective retry after an invalid or unparseable reply, or a resend after a transport failure; "
                     "charged; 'valid after retry' counts as an LLM selection and is reported separately",
            "repair": "if still invalid: fallback policy = first distinct valid ids, filled from the arm's deterministic "
                      "reference (L_true: R_sort_true; L_perm: R_order); reported as its own policy and EXCLUDED "
                      "from E1/E2 (contrasts use rounds where the LLM selection is valid; pairing kept per round)",
            "pricing": "provider-usage delta per call, so unparseable replies are priced; no decoded response -> charged "
                       "at reservation and marked unknown-actual",
            "ceiling": f"new spend <= USD {NEW_CEILING_USD}, checked before every call against spent + reservation "
                       f"(prompt chars / {D.CHARS_PER_TOKEN_RESERVE} at cache-miss rate + {MAX_TOKENS} output tokens); "
                       f"WS4 spend before this run USD {prior:.4f}",
        },
        "estimands": {
            "E1": "per line, sum over valid rounds of hits(L_true) - hits(R_sort_true)",
            "E2": "per line, sum over valid rounds of hits(L_perm) - hits(R_order)",
            "explained": "pooled share of LLM picks inside R_order, inside R_sort_displayed, and inside their union "
                         "(chance: 0.5, 0.5, ~0.75)",
            "residual": "L_perm picks outside R_order and R_sort_displayed: pooled hit rate minus the pooled menu base "
                        "rate of the same rounds",
            "uncertainty": f"percentile bootstrap over the 39 lines, {BOOT} resamples, seed {GATE_SEED}",
            "secondary": "E2 against the menu-random expectation k * menu hits / 2k; L_perm vs R_sort_displayed; "
                         "fallback-policy contrasts",
        },
        "decision": {
            "STOP": "upper 95% bound of E1 < +0.5 AND upper 95% bound of E2 < +0.5 hits/line, OR the best single-rule "
                    "explained share (max of order, displayed score) > 0.90 in both LLM arms",
            "CONTINUE": "not STOP, AND E2 lower 95% bound > 0, AND residual hit rate - menu base rate has lower 95% bound > 0",
            "MODIFY": "otherwise (e.g. E1 > 0 only, or inconclusive)",
            "precedence": "STOP is evaluated first",
        },
        "cost": {"calls_first_attempt": calls, "max_calls_with_retries": 2 * calls,
                 "expected_usd": round(expected, 4), "worst_usd_first_attempts_at_max_tokens": round(reserve_total, 4),
                 "ceiling_new_usd": NEW_CEILING_USD, "ws4_prior_usd": round(prior, 6),
                 "ws4_cumulative_cap_usd": round(prior + NEW_CEILING_USD, 4)},
        "code_sha256": {"gate.py": D.file_sha(Path(__file__)), "diagnostic.py": D.file_sha(HERE / "diagnostic.py")},
    }
    PLAN.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    return doc


def select(caller, messages, presented, k, label, meta):
    attempts = []
    for attempt in range(2):
        record = caller.call(f"{label}:a{attempt}", messages, {**meta, "attempt": attempt})
        items, failure = D.parse(record, "chosen")
        check = D.check_list(items, presented, k) if failure is None else None
        attempts.append({"failure": failure, "check": None if check is None else
                         {key: check[key] for key in ("n", "dup", "bad", "nonint", "exact")} | {"ids": check["distinct_valid"]},
                         "usd": record.get("usd"), "finish_reason": record.get("finish_reason"),
                         "seconds": record.get("seconds"), "code": record.get("code")})
        if failure == "SPEND_CEILING" or (check is not None and check["exact"]):
            break
        if record.get("content") is not None:
            text = D.RETRY_PARSE.format(k=k) if check is None else D.RETRY.format(
                n=check["n"], dup=check["dup"], bad=check["bad"], nonint=check["nonint"], k=k)
            messages = messages + [{"role": "assistant", "content": record["content"]},
                                   {"role": "user", "content": text}]
    return attempts


def run() -> int:
    doc = json.loads(PLAN.read_text(encoding="utf-8"))
    if doc["code_sha256"] != {"gate.py": D.file_sha(Path(__file__)), "diagnostic.py": D.file_sha(HERE / "diagnostic.py")}:
        raise SystemExit("gate_plan.json does not match the code; re-plan before any call")
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    OUT.mkdir(parents=True)
    D.MAX_TOKENS = MAX_TOKENS            # read by Caller.call and reservation at call time
    D.CEILING_USD = NEW_CEILING_USD      # read when the Caller's SpendBook is built and before every call
    lib = D.load_library(D.LIBRARY)
    caller = D.Caller(OUT)
    started = D.now()
    with open(OUT / "rounds.jsonl", "w", encoding="utf-8", newline="\n") as handle:
        for line in range(len(lib.lines)):
            for st in campaign_states(lib, line):
                truth = st["truth"]
                hit = lambda ids: int((truth[np.array(ids, int)] > lib.threshold).sum())  # noqa: E731
                for arm in ARMS:
                    msgs, presented, refs = arm_messages(lib, st, line, arm)
                    label = f"{arm}:{line}:{st['round']}"
                    attempts = select(caller, msgs, presented, st["k"], label,
                                      {"cell": label, "k": st["k"], "menu": int(st["menu"].size)})
                    last = attempts[-1]
                    valid = bool(last["check"] and last["check"]["exact"])
                    ids = last["check"]["ids"] if last["check"] else []
                    fill = refs["R_sort_true"] if arm == "L_true" else refs["R_order"]
                    repaired = (ids[: st["k"]] + [i for i in fill if i not in set(ids)])[: st["k"]]
                    row = {"line": line, "line_name": lib.lines[line], "round": st["round"], "arm": arm, "k": st["k"],
                           "presented": presented, "menu_model_order": st["menu"].tolist(), **refs,
                           "selection": ids if valid else None, "valid": valid,
                           "valid_first": bool(attempts[0]["check"] and attempts[0]["check"]["exact"]),
                           "retries": len(attempts) - 1, "attempts": attempts,
                           "ceiling_stop": any(a["failure"] == "SPEND_CEILING" for a in attempts),
                           "fallback_selection": repaired,
                           "hits": {"llm": hit(ids) if valid else None, "fallback": hit(repaired),
                                    "R_sort_true": hit(refs["R_sort_true"]), "R_order": hit(refs["R_order"]),
                                    "R_sort_displayed": hit(refs["R_sort_displayed"]), "menu": hit(st["menu"]),
                                    "picks_hit": [int(truth[i] > lib.threshold) for i in ids] if valid else None}}
                    handle.write(json.dumps(row) + "\n")
                    handle.flush()
            print(line, lib.lines[line], "spent", round(caller.book.total, 4), flush=True)
    caller.log.close()
    manifest = {"started": started, "finished": D.now(), "plan_sha256": D.file_sha(PLAN),
                "spend_usd": caller.book.total, "priced_calls": len(caller.book.entries),
                "reservation_priced": sum(e["label"].endswith(":reservation") for e in caller.book.entries),
                "http_attempts": caller.attempts, "stopped_by_ceiling": caller.stopped,
                "provider_usage": caller.client.provider_usage,
                "ws4_cumulative_usd": caller.book.total + doc["cost"]["ws4_prior_usd"]}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("spend_usd", "priced_calls", "http_attempts", "stopped_by_ceiling",
                                               "ws4_cumulative_usd")}))
    return 0


def analyse() -> int:
    rows = [json.loads(line) for line in open(OUT / "rounds.jsonl", encoding="utf-8")]
    lines = sorted({r["line"] for r in rows})
    by = {(r["line"], r["round"], r["arm"]): r for r in rows}
    rng = np.random.default_rng(GATE_SEED)
    draws = rng.integers(0, len(lines), size=(BOOT, len(lines)))

    def ci(per_line: np.ndarray) -> dict:
        boot = per_line[draws].mean(axis=1)
        return {"mean": round(float(per_line.mean()), 4), "lo": round(float(np.percentile(boot, 2.5)), 4),
                "hi": round(float(np.percentile(boot, 97.5)), 4), "sum": round(float(per_line.sum()), 2)}

    def ratio_ci(num: np.ndarray, den: np.ndarray, base_num: np.ndarray, base_den: np.ndarray) -> dict:
        point = num.sum() / max(den.sum(), 1) - base_num.sum() / max(base_den.sum(), 1)
        boot = num[draws].sum(1) / np.maximum(den[draws].sum(1), 1) - base_num[draws].sum(1) / np.maximum(base_den[draws].sum(1), 1)
        return {"residual_hit_rate": round(float(num.sum() / max(den.sum(), 1)), 4), "residual_picks": int(den.sum()),
                "menu_base_rate": round(float(base_num.sum() / max(base_den.sum(), 1)), 4),
                "difference": round(float(point), 4), "lo": round(float(np.percentile(boot, 2.5)), 4),
                "hi": round(float(np.percentile(boot, 97.5)), 4)}

    out: dict = {"scope": "O'Neil development (exposed), 39 lines x 4 rounds, one-step paired evaluation"}
    for arm, ref in (("L_true", "R_sort_true"), ("L_perm", "R_order")):
        rs = [r for r in rows if r["arm"] == arm]
        diff, diff_rand, diff_disp, diff_fb = (np.zeros(len(lines)) for _ in range(4))
        res_hit, res_n, menu_hit, menu_n = (np.zeros(len(lines)) for _ in range(4))
        in_order = in_disp = in_union = in_model = picks = 0
        for r in rs:
            j = lines.index(r["line"])
            h = r["hits"]
            diff_fb[j] += h["fallback"] - h[ref]
            if not r["valid"]:
                continue
            diff[j] += h["llm"] - h[ref]
            diff_rand[j] += h["llm"] - r["k"] * h["menu"] / len(r["menu_model_order"])
            diff_disp[j] += h["llm"] - h["R_sort_displayed"]
            sel = r["selection"]
            order_set, disp_set = set(r["R_order"]), set(r["R_sort_displayed"])
            in_order += len(set(sel) & order_set)
            in_disp += len(set(sel) & disp_set)
            in_union += len(set(sel) & (order_set | disp_set))
            in_model += len(set(sel) & set(r["R_sort_true"]))
            picks += len(sel)
            residual = [i for i, ok in zip(sel, r["hits"]["picks_hit"]) if i not in order_set and i not in disp_set]
            res_n[j] += len(residual)
            res_hit[j] += sum(ok for i, ok in zip(sel, r["hits"]["picks_hit"]) if i not in order_set and i not in disp_set)
            menu_hit[j] += h["menu"]
            menu_n[j] += len(r["menu_model_order"])
        valid = sum(r["valid"] for r in rs)
        out[arm] = {
            "rounds": len(rs), "valid": valid, "valid_first_attempt": sum(r["valid_first"] for r in rs),
            "retries": sum(r["retries"] for r in rs), "ceiling_stops": sum(r["ceiling_stop"] for r in rs),
            "parse_failures": sum(a["failure"] == "PARSE_FAILURE" for r in rs for a in r["attempts"]),
            "truncated": sum(a["finish_reason"] == "length" for r in rs for a in r["attempts"]),
            f"contrast_vs_{ref}": ci(diff), "contrast_vs_menu_random_expectation": ci(diff_rand),
            "contrast_vs_R_sort_displayed": ci(diff_disp), f"fallback_policy_vs_{ref}": ci(diff_fb),
            "share_in_R_order": round(in_order / max(picks, 1), 4),
            "share_in_R_sort_displayed": round(in_disp / max(picks, 1), 4),
            "share_in_union": round(in_union / max(picks, 1), 4),
            "share_in_world_model_topk": round(in_model / max(picks, 1), 4),
            "best_single_rule_share": round(max(in_order, in_disp) / max(picks, 1), 4),
            "residual": ratio_ci(res_hit, res_n, menu_hit, menu_n),
            "hits_total": {"llm": sum(r["hits"]["llm"] or 0 for r in rs if r["valid"]),
                           ref: sum(r["hits"][ref] for r in rs if r["valid"]),
                           "menu_random_expectation": round(sum(r["k"] * r["hits"]["menu"] / len(r["menu_model_order"])
                                                                for r in rs if r["valid"]), 2)},
        }
    e1, e2 = out["L_true"]["contrast_vs_R_sort_true"], out["L_perm"]["contrast_vs_R_order"]
    stop = (e1["hi"] < 0.5 and e2["hi"] < 0.5) or (out["L_true"]["best_single_rule_share"] > 0.9
                                                    and out["L_perm"]["best_single_rule_share"] > 0.9)
    cont = (not stop) and e2["lo"] > 0 and out["L_perm"]["residual"]["lo"] > 0
    out["decision"] = "STOP" if stop else ("CONTINUE" if cont else "MODIFY")
    out["decision_inputs"] = {"E1_hi": e1["hi"], "E2_hi": e2["hi"], "E2_lo": e2["lo"],
                              "best_share_true": out["L_true"]["best_single_rule_share"],
                              "best_share_perm": out["L_perm"]["best_single_rule_share"],
                              "residual_lo": out["L_perm"]["residual"]["lo"]}
    out["manifest"] = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    SUMMARY.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan", action="store_true")
    group.add_argument("--run", action="store_true")
    group.add_argument("--analyse", action="store_true")
    args = parser.parse_args(argv)
    if args.plan:
        if OUT.exists():
            raise SystemExit("gate results exist; the plan cannot be rewritten")
        print(json.dumps(plan()["cost"]))
        return 0
    return run() if args.run else analyse()


if __name__ == "__main__":
    raise SystemExit(main())
