"""LLM hypothesis-debate arm of the Scientific Decision Review (SDR_debate): frozen, not run without authorisation.

File summary
- Path: research/selective_hit_triage_20261013/agent_review.py
- Purpose: test the one role the Co-Scientist evidence leaves open for an LLM here. The LLM may
  generate competing falsifiable explanations and run a tournament that decides *which candidates
  to explore*. It never decides GO or NO-GO, and its ranking is never read as a probability.
- Core points:
  - Window: the capped top 2B pairs under the MAESTRO pre-acquisition score (`review.window`),
    collapsed to compounds. Each packet carries the compound's annotation and evidence for its
    three best window lines.
  - Generation, one call per campaign: every window compound gets at least two explanations,
    exactly one of them SELECTIVE. Each explanation states predictions on registered observables
    and cites the supporting and contradicting evidence values it relies on.
  - Claim audit: every cited value is compared with the packet. A cited field that is absent, or
    off by more than 0.05, is an UNSUPPORTED_CLAIM. The rate is reported, and the explanations
    are used anyway, because they only steer exploration.
  - Tournament: `maestro.decision_review.exploration_tournament`, 3 Swiss rounds, among window
    compounds with a secondary available and a valid explanation set. Each match is one call:
    "whose secondary dose-response would better discriminate its explanations in a way that could
    change its decision?". The top K are bought.
  - The deterministic review (`review_campaign`, veto on, verified evidence) then decides with
    that purchase. Invalid output is refused (INVALID_AGENT_OUTPUT); the fallback is the
    deterministic explanation acquisition.
  - Spend goes through `agent_arms.Ledger` (deepseek-flash, hard ceiling, prompt-hash cache).
    Without `--authorized-usd` nothing runs.
- Interfaces: `OBSERVABLES`, `packets`, `generation_prompt`, `match_prompt`, `parse_explanations`,
  `audit_citations`, `run`.
"""
from __future__ import annotations

import argparse
import json
import sys

import numpy as np

from agent_arms import INVALID_OUTPUT, MODEL, SYSTEM, Ledger, _r
from arms import load_table
from census import HERE, ROOT
from dev_explore2 import K_FRACTION
from review import explanation_features, review_campaign, window
from test_choose import components, load_choices, pair_id

sys.path.insert(0, str(ROOT / "src"))
from maestro.decision_review import exploration_tournament  # noqa: E402

OBSERVABLES = ("secondary_z", "breadth", "generic_fraction", "ctx", "z_r", "tgt_mut", "lineage_z", "vc")
EXPLANATION_IDS = ("SELECTIVE", "NOISE", "GENERIC")
CITATION_TOLERANCE = 0.05
ROUNDS = 3


def packets(t: dict, rows: np.ndarray, c: dict, ex: dict, B: int, compounds: dict) -> list[dict]:
    win = window(c, ex, np.arange(len(rows)), B)
    out: dict = {}
    for k in win:
        core = str(c["core"][k])
        p = out.setdefault(core, {"compound": core, "name": compounds[core]["name"], "moa": compounds[core]["moas"],
                                  "targets": compounds[core]["targets"][:12], "phase": compounds[core]["phase"],
                                  "secondary_available": bool(c["has"][c["core"] == core].any()),
                                  "breadth": int(ex["breadth"][k]), "generic_fraction": round(float(ex["generic_fraction"][k]), 3),
                                  "lines": []})
        r = rows[k]
        p["lines"].append({"pair": pair_id(core, c["line"][k]), "lineage": str(t["lineage"][r]), "z_r": _r(t["z_r"][r]),
                           "ctx": _r(t["ctx_pred"][r]), "lineage_z": _r(t["lineage_pred"][r]), "tgt_mut": int(t["tgt_mut"][r] > 0),
                           "vc": _r(t["vc_pred"][r]), "lfc": _r(t["lfc"][r])})
    return list(out.values())


def generation_prompt(pk: list[dict]) -> list[dict]:
    return [{"role": "system", "content": SYSTEM + " You generate competing, falsifiable explanations; you do not decide."},
            {"role": "user", "content": json.dumps({
                "task": "For EVERY compound below, give at least two competing explanations of why its listed lines look selectively "
                        "sensitive in a single-dose pooled screen. Exactly one must have id SELECTIVE (a real, coherent sensitive "
                        "subpopulation). Alternatives may be NOISE (isolated outlier that will not replicate), GENERIC (broad "
                        "cytotoxicity, fragile line), or OTHER:<short label>. Each explanation must state predictions on these "
                        f"observables only: {list(OBSERVABLES)} (secondary_z = selectivity z of the not-yet-measured 8-dose secondary "
                        "screen for the best line). Cite the evidence values you rely on, copied exactly from the packet.",
                "compounds": pk,
                "answer_schema": {"explanations": [{"compound": "id", "id": "SELECTIVE|NOISE|GENERIC|OTHER:label", "statement": "one sentence",
                                                    "predictions": [{"observable": "secondary_z", "relation": "<=|>=|<|>", "threshold": -2.0}],
                                                    "supporting": [{"field": "breadth", "value": 4}],
                                                    "contradicting": [{"field": "ctx", "value": 0.3}]}]}})}]


def match_prompt(a: dict, b: dict) -> list[dict]:
    return [{"role": "system", "content": SYSTEM + " You rank which candidate to explore first; this is not a probability of success."},
            {"role": "user", "content": json.dumps({
                "task": "Only one of these two compounds can receive the 8-dose secondary dose-response now. Which one's result would "
                        "better discriminate between its competing explanations in a way that could change its GO / NO-GO decision?",
                "candidates": [a, b], "answer_schema": {"explore_first": "compound id", "reason": "one sentence"}})}]


def parse_explanations(resp, window_compounds: set) -> tuple[dict, list[str]]:
    """Valid explanation sets per compound; compounds with an invalid set are named in the refusals."""
    items = resp.get("explanations") if isinstance(resp, dict) else None
    if not isinstance(items, list):
        return {}, [f"{INVALID_OUTPUT}:no_explanations"]
    sets: dict = {}
    for e in items:
        if not isinstance(e, dict) or str(e.get("compound")) not in window_compounds:
            continue
        preds = [p for p in e.get("predictions") or [] if isinstance(p, dict) and p.get("observable") in OBSERVABLES
                 and p.get("relation") in ("<=", ">=", "<", ">") and isinstance(p.get("threshold"), (int, float))]
        ident = str(e.get("id", ""))
        if not preds or not (ident in EXPLANATION_IDS or ident.startswith("OTHER:")):
            continue
        sets.setdefault(str(e["compound"]), []).append({"id": ident, "statement": str(e.get("statement", ""))[:300], "predictions": preds,
                                                         "supporting": e.get("supporting") or [], "contradicting": e.get("contradicting") or []})
    valid, refusals = {}, []
    for c in sorted(window_compounds):
        s = sets.get(c, [])
        if len(s) >= 2 and sum(x["id"] == "SELECTIVE" for x in s) == 1 and len({x["id"] for x in s}) == len(s):
            valid[c] = s
        else:
            refusals.append(f"{INVALID_OUTPUT}:{c}")
    return valid, refusals


def audit_citations(sets: dict, pk: list[dict]) -> dict:
    """Cited evidence values checked against the packet; absent fields and wrong values are unsupported."""
    by = {p["compound"]: p for p in pk}
    total = unsupported = 0
    for c, s in sets.items():
        p = by[c]
        values: dict = {"breadth": [p["breadth"]], "generic_fraction": [p["generic_fraction"]]}
        for line in p["lines"]:
            for f in ("z_r", "ctx", "lineage_z", "tgt_mut", "vc", "lfc"):
                values.setdefault(f, []).append(line[f])
        for e in s:
            for cite in list(e["supporting"]) + list(e["contradicting"]):
                total += 1
                f, v = (cite.get("field"), cite.get("value")) if isinstance(cite, dict) else (None, None)
                ok = isinstance(v, (int, float)) and not isinstance(v, bool) and any(
                    x is not None and abs(float(x) - float(v)) <= CITATION_TOLERANCE for x in values.get(f, []))
                unsupported += not ok
    return {"citations": total, "unsupported": unsupported}


def run(completer, ledger: Ledger, replicates: int, *, choices: dict | None = None, campaigns: list[int] | None = None) -> dict:
    choices = choices or load_choices()
    t = load_table()
    compounds = {r["core"]: r for r in json.loads((HERE / "compounds.json").read_text(encoding="utf-8"))}
    allrows = np.flatnonzero(t["role"] == "test")
    out: dict = {"model": MODEL, "replicates": replicates, "arm": "SDR_debate", "runs": []}
    for rep in range(replicates):
        camps = []
        for ci in campaigns if campaigns is not None else range(len(choices["campaigns"])):
            camp = choices["campaigns"][ci]
            rows = allrows[np.isin(t["core"][allrows], camp)]
            c, ex = components(t, rows), explanation_features(t, rows)
            B, K = len(camp), int(round(K_FRACTION * len(camp)))
            pk = packets(t, rows, c, ex, B, compounds)
            resp, err = ledger.call(completer, generation_prompt(pk), f"sdr_gen_c{ci}_r{rep}", max_tokens=8000)
            sets, refusals = parse_explanations(resp, {p["compound"] for p in pk}) if err is None else ({}, [err])
            cites = audit_citations(sets, pk)
            eligible = [p["compound"] for p in pk if p["secondary_available"] and p["compound"] in sets]
            brief = {p["compound"]: {"compound": p["compound"], "name": p["name"], "breadth": p["breadth"],
                                     "explanations": [{"id": e["id"], "statement": e["statement"], "predictions": e["predictions"]}
                                                      for e in sets.get(p["compound"], [])]} for p in pk}
            match_refusals = []

            def judge(a, b):
                r, e = ledger.call(completer, match_prompt(brief[a], brief[b]), f"sdr_match_c{ci}_r{rep}_{a}_{b}", max_tokens=300)
                pick = r.get("explore_first") if isinstance(r, dict) and e is None else None
                if pick not in (a, b):
                    match_refusals.append(e or INVALID_OUTPUT)
                return pick

            ranking = exploration_tournament(eligible, judge, rounds=ROUNDS, seed_order=[p["compound"] for p in pk])
            bought = set(ranking.order[:K])
            sel = np.arange(len(rows))
            if len(bought) < K:                                         # fill from the deterministic explanation rule
                fallback = review_campaign(c, ex, sel, B, K, veto=True, acquire="explanation")["bought"]
                bought |= set(sorted(fallback - bought)[:K - len(bought)])
            r = review_campaign(c, ex, sel, B, K, veto=True, acquire=bought)
            camps.append({"campaign": ci, "bought": sorted(bought), "ranking": list(ranking.order), "matches": ranking.matches,
                          "nominations": [pair_id(c["core"][k], c["line"][k]) for k in r["nominated"]],
                          "decisions": {k: {"status": v["status"], "reasons": v["reasons"]} for k, v in r["decisions"].items()},
                          "refusals": refusals + match_refusals, "citations": cites})
        out["runs"].append(camps)
    out["spent_usd"] = ledger.spent
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorized-usd", type=float, required=True, help="hard spend ceiling approved by the owner")
    parser.add_argument("--replicates", type=int, default=3)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / "src"))
    from agent.llm import DeepSeekChatClient, MAESTROSettings
    settings = MAESTROSettings.from_workspace(ROOT)
    if settings.chat_model != MODEL:
        raise SystemExit(f"MODEL_NOT_AUTHORISED: {settings.chat_model}")
    target = HERE / "SDR_DEBATE_CHOICES.json"
    if target.exists():
        raise SystemExit("AGENT_CHOICES_EXISTS: agent choices are write-once")
    ledger = Ledger(HERE / "api_ledger.json", HERE / "llm_cache", args.authorized_usd)
    out = run(DeepSeekChatClient(settings), ledger, args.replicates)
    target.write_bytes((json.dumps(out, indent=1) + "\n").encode())
    print(json.dumps({"spent_usd": out["spent_usd"]}))


if __name__ == "__main__":
    main()
