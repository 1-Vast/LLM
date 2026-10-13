"""LLM agent arms (comparators 4 and 5): frozen prompts, typed outputs and admission rules.

File summary
- Path: research/selective_hit_triage_20261013/agent_arms.py
- Purpose: run the two language-model arms on the test campaigns with the same evidence, the same
  nomination budget (B = 16 per campaign) and the same dose-response budget (K = 4) as the
  non-LLM arms at b = 1. Paid calls run only with an explicit spend ceiling; nothing here reads an
  outcome, so the arms can be run after the non-LLM test evaluation without contamination.
- Core points:
  - Conventional agent (comparator 4) uses no decision engine. It works through two tool steps
    per campaign:
    1. see every compound's annotation and its candidate pairs with all evidence fields, then buy
       secondary dose-response for K compounds;
    2. see the bought results, then submit B pairs (at most three per compound).
    Candidate pairs are the top six per compound by two-way z and by the MAESTRO score.
  - MAESTRO agent (comparator 5): the decision engine runs MAESTRO_LOOP (frontier acquisition,
    context plus secondary scoring). The agent sees the engine's capped top 2B pairs and may flag
    at most ceil(B/4) of them with a named reason (FLAG_REASONS). `admit_flags` drops flagged
    pairs and takes the next pairs in the engine's order. The agent cannot add a pair, reorder
    pairs or change a number.
  - Invalid output is refused by name (INVALID_AGENT_OUTPUT, or the client's error class) and
    falls back to the arm's deterministic default:
    - conventional: CONV_LOOP acquisition, then D3 nominations;
    - MAESTRO: no flags.
  - Every call is ledgered (tokens, and USD at 0.30 / 1.20 per million input / output tokens).
    Successful calls are cached by prompt hash; failed calls are never cached.
    `--authorized-usd` is the hard ceiling and is required.
  - The model is deepseek-flash, never pro. Compound names are shown, as a working scientist
    would see them. Pretraining may hold published CTRP associations, so a positive agent effect
    is suspect while a null is not.
- Interfaces: `campaign_inputs`, `candidate_table`, `parse_acquisition`, `parse_nominations`,
  `parse_flags`, `admit_flags`, `run`, `Ledger`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

from arms import CAP, load_table, tie
from census import HERE, ROOT
from dev_explore2 import K_FRACTION
from test_choose import components, load_choices, loop_scores, pair_id

FLAG_REASONS = ("GENERIC_TOXICITY_SUSPECTED", "ASSAY_ARTIFACT_SUSPECTED", "MECHANISM_INCOHERENT")
INVALID_OUTPUT = "INVALID_AGENT_OUTPUT"
CANDIDATES_PER_RULE = 6
USD_IN, USD_OUT = 0.30e-6, 1.20e-6
MODEL = "deepseek-flash"
SYSTEM = "You are a drug-discovery scientist triaging a phenotypic oncology screen. Answer with one JSON object only."
ENDPOINT_TEXT = (
    "A nomination is one (compound, cell line) pair sent to an independent confirmation assay: a 16-dose viability "
    "curve on a different platform (ATP luminescence, 72 h). It counts as a VALIDATED SELECTIVE HIT only if that line is "
    "among the compound's most sensitive lines there (AUC robust z <= -2 across hundreds of lines) and viability at the "
    "top dose is at most 50%. Broadly cytotoxic compounds rarely give selective hits. Evidence fields: lfc = primary-screen "
    "log2 fold change at 2.5 uM (5-day pooled barcoded screen); z_r = selectivity z after removing the line's general "
    "sensitivity and the compound's median (more negative = more selective); ctx = the compound's mean z_r in the 25 lines "
    "most similar in expression (context coherence); lineage_z = mean z_r in other lines of the same lineage; tgt_mut = 1 "
    "if the line carries a protein-changing mutation in an annotated target; bio = target-expression prediction of z_r; "
    "vc = transcriptional-transfer prediction from drugs with similar L1000 responses (null if unavailable); sec_z = "
    "dose-response selectivity z from the same-platform 8-dose secondary screen (only once bought); promisc = fraction "
    "of lines with lfc <= -1.")


def _r(x) -> float | None:
    return None if x is None or not np.isfinite(x) else round(float(x), 2)


def _row(t: dict, r: int, bought: set) -> dict:
    return {"pair": pair_id(t["core"][r], t["line"][r]), "lineage": str(t["lineage"][r]), "lfc": _r(t["lfc"][r]),
            "z_r": _r(t["z_r"][r]), "ctx": _r(t["ctx_pred"][r]), "lineage_z": _r(t["lineage_pred"][r]),
            "tgt_mut": int(t["tgt_mut"][r] > 0), "bio": _r(t["biomarker_pred"][r]), "vc": _r(t["vc_pred"][r]),
            "sec_z": _r(t["sec_auc_z"][r]) if t["core"][r] in bought else None}


def candidate_table(t: dict, rows: np.ndarray, maestro: np.ndarray, bought: set) -> list[dict]:
    """Candidate pairs of one campaign: the top six per compound by -z_r and by the MAESTRO score."""
    core = t["core"][rows]
    keep: set = set()
    for c in sorted(set(core)):
        idx = np.flatnonzero(core == c)
        for s in (-t["z_r"][rows][idx], maestro[idx]):
            s = np.where(np.isfinite(s), s, -np.inf)
            keep |= set(idx[np.argsort(-s, kind="stable")[:CANDIDATES_PER_RULE]].tolist())
    return [_row(t, rows[k], bought) for k in sorted(keep, key=lambda k: (core[k], t["line"][rows][k]))]


def campaign_inputs(ci: int, choices: dict | None = None, t: dict | None = None) -> dict:
    """Everything one test campaign's agents may see, at b = 1, rebuilt from the locked choices."""
    choices = choices or load_choices()
    t = t if t is not None else load_table()
    compounds = {r["core"]: r for r in json.loads((HERE / "compounds.json").read_text(encoding="utf-8"))}
    camp = choices["campaigns"][ci]
    allrows = np.flatnonzero(t["role"] == "test")
    rows = allrows[np.isin(t["core"][allrows], camp)]
    c = components(t, rows)
    B, K = len(camp), int(round(K_FRACTION * len(camp)))
    has = {k: bool(c["has"][c["core"] == k].any()) for k in camp}
    maestro = -(c["zr"] + c["ctx"]) / np.sqrt(2)
    arm = choices["arms"]["1.0"]
    bought_m = set(arm["MAESTRO_LOOP"]["campaigns"][ci]["bought"])
    _, post = loop_scores(c, np.arange(len(rows)), B, K, "maestro", "frontier")
    s = np.where(np.isfinite(post), post, -np.inf)
    order = [k for k in np.lexsort((tie(c["core"], c["line"]), -s)) if np.isfinite(s[k])]
    ranked = [pair_id(c["core"][k], c["line"][k]) for k in order]
    capped, per = [], {}
    for p in ranked:
        per[p.split("|")[0]] = per.get(p.split("|")[0], 0) + 1
        if per[p.split("|")[0]] <= CAP:
            capped.append(p)
    position = {p: k for k, p in enumerate(ranked)}
    by_pair = {pair_id(t["core"][r], t["line"][r]): r for r in rows}
    return {
        "campaign": ci, "budget": B, "k_secondary": K,
        "compound_table": [{"compound": k, "name": compounds[k]["name"], "moa": compounds[k]["moas"],
                            "targets": compounds[k]["targets"][:12], "phase": compounds[k]["phase"],
                            "promisc": round(compounds[k]["promiscuity"], 3), "secondary_available": has[k]} for k in sorted(camp)],
        "candidates_pre": candidate_table(t, rows, maestro, set()),
        "candidates_for": lambda bought: candidate_table(t, rows, maestro, set(bought)),
        "conventional_top_bought": arm["CONV_LOOP"]["campaigns"][ci]["bought"],
        "d3_nominations": arm["D3_two_way_z"]["campaigns"][ci]["nominations"],
        "maestro_loop_nominations": arm["MAESTRO_LOOP"]["campaigns"][ci]["nominations"],
        "maestro_loop_ranked": ranked, "maestro_window": capped[:2 * B],
        "ranked_rows": lambda pairs: [dict(_row(t, by_pair[p], bought_m), engine_rank=position[p] + 1) for p in pairs],
    }


def acquisition_prompt(cmp: list[dict], cand: list[dict], k: int) -> list[dict]:
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": json.dumps({
        "tool": "buy_secondary",
        "task": f"Choose exactly {k} compounds to receive a same-platform 8-dose secondary dose-response screen across all lines "
                "before you nominate pairs for independent confirmation. Only compounds with secondary_available=true can be chosen.",
        "endpoint": ENDPOINT_TEXT, "compounds": cmp, "candidates": cand,
        "answer_schema": {"secondary": ["compound id"], "rationale": "one short paragraph"}})}]


def nomination_prompt(cmp: list[dict], cand: list[dict], budget: int) -> list[dict]:
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": json.dumps({
        "tool": "submit_nominations",
        "task": f"Nominate exactly {budget} candidate pairs for independent confirmation, at most {CAP} per compound, "
                "to maximise validated selective hits. Use only pair ids listed in candidates.",
        "endpoint": ENDPOINT_TEXT, "compounds": cmp, "candidates": cand,
        "answer_schema": {"nominations": ["pair id"], "rationale": "one short paragraph"}})}]


def review_prompt(cmp: list[dict], ranked: list[dict], budget: int, max_flags: int) -> list[dict]:
    return [{"role": "system", "content": SYSTEM + " You review a deterministic triage engine's ranking. You may only flag pairs; "
                                                    "you cannot add, reorder or change numbers."},
            {"role": "user", "content": json.dumps({
                "tool": "flag_candidates",
                "task": f"The engine will nominate its top {budget} pairs of ranked_candidates. Flag at most {max_flags} listed pairs that "
                        f"you have a specific scientific reason to expect to fail independent selective confirmation. Allowed reasons: "
                        f"{list(FLAG_REASONS)}. Each flagged pair is replaced by the next unflagged pair in the engine's order. "
                        "Flag nothing if you have no specific reason.",
                "endpoint": ENDPOINT_TEXT, "compounds": cmp, "ranked_candidates": ranked,
                "answer_schema": {"flags": [{"pair": "pair id", "reason": FLAG_REASONS[0], "evidence": "one sentence"}]}})}]


def parse_acquisition(resp, allowed: set, k: int) -> tuple[list[str] | None, str | None]:
    got = resp.get("secondary") if isinstance(resp, dict) else None
    if not isinstance(got, list) or len(got) != k or len(set(map(str, got))) != k or not set(map(str, got)) <= allowed:
        return None, INVALID_OUTPUT
    return sorted(set(map(str, got))), None


def parse_nominations(resp, allowed: set, budget: int) -> tuple[list[str] | None, str | None]:
    got = resp.get("nominations") if isinstance(resp, dict) else None
    if not isinstance(got, list):
        return None, INVALID_OUTPUT
    got = [str(p) for p in got]
    per: dict = {}
    for p in got:
        per[p.split("|")[0]] = per.get(p.split("|")[0], 0) + 1
    if len(got) != budget or len(set(got)) != budget or not set(got) <= allowed or max(per.values(), default=0) > CAP:
        return None, INVALID_OUTPUT
    return got, None


def parse_flags(resp, window: list[str], max_flags: int) -> tuple[list[dict] | None, str | None]:
    got = resp.get("flags") if isinstance(resp, dict) else None
    if not isinstance(got, list) or len(got) > max_flags:
        return None, INVALID_OUTPUT
    out = []
    for f in got:
        if not isinstance(f, dict) or str(f.get("pair")) not in window or f.get("reason") not in FLAG_REASONS:
            return None, INVALID_OUTPUT
        out.append({"pair": str(f["pair"]), "reason": f["reason"], "evidence": str(f.get("evidence", ""))[:300]})
    if len({f["pair"] for f in out}) != len(out):
        return None, INVALID_OUTPUT
    return out, None


def admit_flags(ranked: list[str], flags: list[dict], budget: int) -> list[str]:
    """The engine's order with flagged pairs removed, at most CAP per compound, first ``budget`` pairs."""
    flagged = {f["pair"] for f in flags}
    out, per = [], {}
    for p in ranked:
        c = p.split("|")[0]
        if p in flagged or per.get(c, 0) >= CAP:
            continue
        out.append(p)
        per[c] = per.get(c, 0) + 1
        if len(out) == budget:
            break
    return out


class Ledger:
    """Spend ledger and prompt-hash cache; a call that would cross the ceiling is refused before it is made."""

    def __init__(self, path: Path, cache: Path, ceiling: float):
        self.path, self.cache, self.ceiling = path, cache, ceiling
        self.entries = json.loads(path.read_text(encoding="utf-8"))["entries"] if path.exists() else []
        cache.mkdir(exist_ok=True)

    @property
    def spent(self) -> float:
        return sum(e["usd"] for e in self.entries)

    def call(self, completer, messages: list[dict], tag: str, max_tokens: int = 4000) -> tuple[dict | None, str | None]:
        key = hashlib.sha256(json.dumps(messages, sort_keys=True).encode()).hexdigest()
        cached = self.cache / f"{tag}_{key[:16]}.json"
        if cached.exists():
            rec = json.loads(cached.read_text(encoding="utf-8"))
            return rec["response"], rec["error"]
        reserve = sum(len(m["content"]) for m in messages) / 3.0 * USD_IN + max_tokens * USD_OUT
        if self.spent + reserve > self.ceiling:
            raise SystemExit(f"SPEND_CEILING: spent {self.spent:.4f} + reservation {reserve:.4f} > {self.ceiling}")
        before = dict(getattr(completer, "provider_usage", {}) or {})
        try:
            resp, meta = completer.complete_json(messages, max_tokens=max_tokens)
            usage, error = dict(getattr(meta, "usage", {}) or {}), None
        except Exception as exc:                       # protocol or transport failure: refused by name, cost still counted
            after = dict(getattr(completer, "provider_usage", {}) or {})
            usage = {k: after.get(k, 0) - before.get(k, 0) for k in ("prompt_tokens", "completion_tokens")}
            resp, error = None, f"{type(exc).__name__}:{getattr(exc, 'code', '')}"
        tin, tout = int(usage.get("prompt_tokens", 0) or 0), int(usage.get("completion_tokens", 0) or 0)
        metered = bool(tin or tout) or getattr(completer, "free", False)
        usd = tin * USD_IN + tout * USD_OUT if metered else reserve
        self.entries.append({"tag": tag, "prompt_sha256": key, "model": MODEL, "input_tokens": tin, "output_tokens": tout,
                             "usd": usd, "metered": metered, "error": error})
        if error is None:                              # failed responses are ledgered but never cached
            cached.write_bytes((json.dumps({"messages": messages, "response": resp, "error": None}, indent=1) + "\n").encode())
        self.path.write_bytes((json.dumps({"ceiling_usd": self.ceiling, "spent_usd": self.spent, "entries": self.entries}, indent=1) + "\n").encode())
        return resp, error


def run(completer, ledger: Ledger, replicates: int, *, choices: dict | None = None, campaigns: list[int] | None = None) -> dict:
    """Agent choices for the test campaigns at b = 1; the caller writes the result."""
    choices = choices or load_choices()
    t = load_table()
    out: dict = {"model": MODEL, "replicates": replicates, "arms": {"AGENT_conventional": [], "AGENT_maestro": []}}
    for rep in range(replicates):
        conv, maes = [], []
        for ci in campaigns if campaigns is not None else range(len(choices["campaigns"])):
            inp = campaign_inputs(ci, choices, t)
            cmp, B, K = inp["compound_table"], inp["budget"], inp["k_secondary"]
            allowed = {x["compound"] for x in cmp if x["secondary_available"]}
            resp, err1 = ledger.call(completer, acquisition_prompt(cmp, inp["candidates_pre"], K), f"conv_acq_c{ci}_r{rep}")
            bought, ref1 = parse_acquisition(resp, allowed, K) if err1 is None else (None, err1)
            bought = bought or inp["conventional_top_bought"]
            cand = inp["candidates_for"](bought)
            resp, err2 = ledger.call(completer, nomination_prompt(cmp, cand, B), f"conv_nom_c{ci}_r{rep}")
            noms, ref2 = parse_nominations(resp, {x["pair"] for x in cand}, B) if err2 is None else (None, err2)
            conv.append({"campaign": ci, "bought": sorted(bought), "nominations": noms or inp["d3_nominations"],
                         "refusals": [r for r in (ref1, ref2) if r]})
            window, max_flags = inp["maestro_window"], math.ceil(B / 4)
            resp, err3 = ledger.call(completer, review_prompt(cmp, inp["ranked_rows"](window), B, max_flags), f"maestro_review_c{ci}_r{rep}")
            flags, ref3 = parse_flags(resp, window, max_flags) if err3 is None else (None, err3)
            maes.append({"campaign": ci, "flags": flags or [], "nominations": admit_flags(inp["maestro_loop_ranked"], flags or [], B),
                         "bought": sorted(choices["arms"]["1.0"]["MAESTRO_LOOP"]["campaigns"][ci]["bought"]),
                         "refusals": [ref3] if ref3 else []})
        out["arms"]["AGENT_conventional"].append(conv)
        out["arms"]["AGENT_maestro"].append(maes)
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
    target = HERE / "AGENT_CHOICES.json"
    if target.exists():
        raise SystemExit("AGENT_CHOICES_EXISTS: agent choices are write-once")
    ledger = Ledger(HERE / "api_ledger.json", HERE / "llm_cache", args.authorized_usd)
    out = run(DeepSeekChatClient(settings), ledger, args.replicates)
    target.write_bytes((json.dumps(out, indent=1) + "\n").encode())
    print(json.dumps({"spent_usd": out["spent_usd"]}))


if __name__ == "__main__":
    main()
