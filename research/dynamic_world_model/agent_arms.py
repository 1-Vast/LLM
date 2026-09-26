"""Language-model and Jev measurement-choice arms under identical evidence, menu and budget.

File summary
- Path: research/dynamic_world_model/agent_arms.py
- Purpose: run the registered provider arms on one seeded contrast per held-out compound in each
  tier. Each arm only *chooses* the next registered measurement (or defers); the measurement is
  executed against the compound's real data and read by the same validator and `EvidenceState`
  as every deterministic policy.
- Core points:
  - The compound's identity, structure and annotation are withheld; the hypotheses are named.
  - Every arm sees the same results so far (validator outcome, replicate agreement, template
    similarities). The card arms also see planning-only scenario cards, headed as model output.
  - Jev is asked a typed choice over the action identifiers plus `defer`, eight times on the same
    state. A stable modal answer (agreement >= 0.6 over eight) is executed; otherwise the
    deterministic separation choice is, and the fallback is recorded.
  - Spend goes through `SpendLedger` with the protocol's caps; the API key never leaves the clients.
- Run: python research/dynamic_world_model/agent_arms.py [--arms ...] [--dry-run]
- Depends on: common.py, episodes.py, agent.llm, agent.typesafe, evaluation.provider_spend, maestro.stability
"""
from __future__ import annotations

import argparse
import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

import common as C
import episodes as E

ARMS = ("deepseek_base", "deepseek_cards", "deepseek_cards_permuted", "jev_cards", "jev_base")
JEV_USD_PER_MILLION_INPUT = 0.042
JEV_REPEATS = 8
PRIOR_DEEPSEEK_USD = 0.016066 + 12 * 0.004
# Jev carry-in: every logged Jev call of the smoke run and of the jev_cards launch that stopped on an
# uncaught RemoteDisconnected (read from the response logs at start-up), plus one failed call's allowance.
JEV_FAILED_CALL_ALLOWANCE_TOKENS = 4000


def _logged_jev_tokens() -> int:
    total = 0
    for path in (C.OUTPUTS / "agent_arms_smoke" / "responses.jsonl", C.OUTPUTS / "agent_arms" / "responses.jsonl"):
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                record = json.loads(line)
                if record.get("provider") == "jev":
                    total += int(sum(v for k, v in record["usage"].items() if "input" in k or "prompt" in k))
    return total
LINE_TEXT = {"A549": "A549, lung adenocarcinoma (KRAS-mutant, TP53 wild-type)",
             "K562": "K562, chronic myeloid leukaemia (BCR-ABL1 fusion, TP53-null)",
             "MCF7": "MCF7, ER-positive breast adenocarcinoma (TP53 wild-type)"}
SYSTEM = ("You plan experiments for MAESTRO, an evidence-bounded drug-mechanism system. You choose the next "
          "registered measurement or defer. You never interpret results yourself: a deterministic validator reads "
          "every measurement. Reply with one JSON object only.")
_LOCK = threading.Lock()


def _number(value) -> str:
    return "n/a" if value is None or not np.isfinite(value) else f"{value:.2f}"


def outcome_text(step: dict, null: dict) -> str:
    key = step["key"]
    threshold = null[f"{key[0]}|{key[1]:g}"]["threshold"]
    agreement = step.get("agreement")
    agree = "n/a" if agreement is None or not np.isfinite(agreement) else f"{agreement:.2f}"
    return {
        "quality_failed": "the measurement failed quality control (too few cells or a missing replicate); nothing was learned",
        "undetected": f"no detectable response (replicate agreement {agree}, detection threshold {threshold:.2f}); "
                      "the validator eliminates nothing, because a failed perturbation and an inert mechanism look alike",
        "ambiguous": f"response detected (replicate agreement {agree}) but unresolved: best similarity to H1 templates "
                     f"{_number(step.get('score_h1'))}, to H2 templates {_number(step.get('score_h2'))}",
        "eliminate_b": "the profile matched H1's templates; H2 eliminated",
        "eliminate_a": "the profile matched H2's templates; H1 eliminated",
    }[step["outcome"]]


def card_text(card: dict, h1: str, h2: str) -> str:
    if not card.get("served"):
        return f"no card (refused: {card.get('reason')})"
    b1, b2 = card["branches"]["H1"], card["branches"]["H2"]

    def branch(b, own, other):
        return (f"if {own} is true ({b['references']} measured references): eliminates {other} {b['p_correct']:.2f}, "
                f"eliminates {own} {b['p_wrong']:.2f}, unresolved {b['p_ambiguous']:.2f}, no response {b['p_undetected']:.2f}")
    return (f"{branch(b1, 'H1', 'H2')}; {branch(b2, 'H2', 'H1')}; estimated probability of a correct decision "
            f"{card['p_correct']:.2f} (90% interval {card['epistemic_interval'][0]:.2f}-{card['epistemic_interval'][1]:.2f})")


def state_text(ctx, h1, h2, menu, executed, remaining, null, cards=None) -> str:
    lines = ["An uncharacterised compound (identity withheld) has two competing mechanism hypotheses:",
             f"H1: {h1}", f"H2: {h2}", "",
             "Each registered measurement is a single-cell RNA-seq (sci-RNA-seq3) pseudobulk profile of the compound "
             "in one cell line at one dose and exposure time, two replicate wells, read against vehicle wells.",
             "The validator eliminates a hypothesis only when a detected profile clearly matches the other hypothesis's "
             "measured reference compounds at the same condition. Scoring: correct elimination +1, wrong elimination -2, "
             "no elimination 0. Cost matters only after that.", "",
             f"Measurements remaining: {remaining}.", "", "Registered menu (id: line, dose, time, cost):"]
    for key in menu:
        days, wells = E.days(key), 2
        lines.append(f"- {C.action_id(key)}: {LINE_TEXT[key[0]]}; {key[2]:g} nM; {key[1]:g} h; {days:g} days, {wells} wells")
    lines.append("- defer: stop without measuring (no decision)")
    lines += ["", "Results so far:"]
    lines += [f"- {s['action']}: {outcome_text(s, null)}" for s in executed] or ["- none"]
    if cards is not None:
        lines += ["", "SCENARIO CARDS (planning-only model output: how the validator behaved on measured reference "
                      "compounds of each hypothesis at each condition; not evidence about this compound):"]
        lines += [f"- {C.action_id(k)}: {card_text(cards[k], h1, h2)}" for k in menu]
    return "\n".join(lines)


class Providers:
    def __init__(self, out: Path, protocol: dict):
        from agent.configuration import MAESTROSettings
        from agent.llm import DeepSeekChatClient
        from agent.typesafe import TypeSafeJevClient, TypeSafeSettings
        from evaluation.provider_spend import SpendLedger
        caps = protocol["llm_arms"]["spend_caps_usd"]
        # Carry-in, reconstructed with evaluation.provider_spend.price_usage from the logged usage of the smoke
        # run and of two aborted launches (2 + 51 calls, $0.016066), plus 12 possibly in-flight calls at the
        # stop charged at their $0.004 reservation because they may be billed without a usage record.
        self.ledger = SpendLedger.load(out / "deepseek_spend.json", ceiling_usd=caps["deepseek"],
                                       prior_total_usd=PRIOR_DEEPSEEK_USD,
                                       prior_note="measurement-choice arms 2026-09-26: smoke run and two aborted launches "
                                                  "(0.016066 logged) + 12 x 0.004 in-flight allowance")
        self.client = DeepSeekChatClient(MAESTROSettings.from_workspace(C.ROOT))
        settings = TypeSafeSettings.from_workspace(C.ROOT)
        self.jev = TypeSafeJevClient(settings) if settings else None
        self.jev_cap = caps["jev"]
        self.prior_jev_tokens = _logged_jev_tokens() + JEV_FAILED_CALL_ALLOWANCE_TOKENS
        self.jev_tokens = self.prior_jev_tokens
        self.raw = (out / "responses.jsonl").open("a", encoding="utf-8")

    def log(self, record: dict) -> None:
        with _LOCK:
            self.raw.write(json.dumps(C.clean(record), default=C._default) + chr(10))
            self.raw.flush()

    def deepseek(self, label: str, text: str, options: list[str]) -> dict:
        from agent.llm import LLMError
        messages = [{"role": "system", "content": SYSTEM},
                    {"role": "user", "content": text + "\n\nReturn JSON: {\"action\": \"<one menu id or defer>\", "
                                                       "\"reason\": \"<at most 40 words>\"}"}]
        for attempt in (1, 2):
            with _LOCK:
                self.ledger.reserve(label, 0.004)
            try:
                data, response = self.client.complete_json(messages, max_tokens=400)
            except LLMError as error:
                with _LOCK:
                    self.ledger.charge(label, None, status="failed", reserved_usd=0.004,
                                       note=getattr(error, "code", type(error).__name__))
                    self.ledger.write()
                return {"choice": None, "failure": getattr(error, "code", type(error).__name__)}
            with _LOCK:
                self.ledger.charge(label, response.usage)
                self.ledger.write()
            answer = str(data.get("action", "")).strip()
            self.log({"provider": "deepseek", "label": label, "attempt": attempt, "reply": data, "usage": response.usage,
                      "state_sha256": hashlib.sha256(text.encode()).hexdigest()})
            if answer in options:
                return {"choice": answer, "reason": data.get("reason"), "attempts": attempt}
            messages += [{"role": "assistant", "content": json.dumps(data)},
                         {"role": "user", "content": f"'{answer}' is not a menu id. Reply with exactly one id from the menu, or defer."}]
        return {"choice": None, "failure": "answer_outside_menu_after_one_correction"}

    def jev_choice(self, label: str, text: str, options: list[str]) -> dict:
        from agent.typesafe import choice
        from maestro.judgment import JudgmentScope
        from maestro.stability import RepeatedJudgment, StabilityVerdict
        if self.jev is None:
            return {"choice": None, "failure": "jev_not_configured"}
        values, probabilities, refusals, model = [], [], [], ""
        question = choice("next_action", "Which registered measurement should run next to separate H1 from H2, or defer?", options)
        for repeat in range(JEV_REPEATS):
            with _LOCK:
                if self.jev_tokens * JEV_USD_PER_MILLION_INPUT / 1e6 > self.jev_cap:
                    return {"choice": None, "failure": "jev_budget_exhausted"}
            evaluation = self.jev.evaluate(text, [question])
            tokens = int(sum(v for k, v in evaluation.usage.items() if "input" in k or "prompt" in k) or 0)
            with _LOCK:
                self.jev_tokens += tokens
            answer = evaluation.answers.get("next_action")
            model = evaluation.model or model
            self.log({"provider": "jev", "label": label, "repeat": repeat, "model": evaluation.model,
                      "usage": dict(evaluation.usage), "refusals": list(evaluation.refusals()),
                      "value": getattr(answer, "value", None), "probability": getattr(answer, "probability", None),
                      "state_sha256": evaluation.state_digest})
            if answer is not None and answer.usable:
                values.append(str(answer.value))
                probabilities.append(float(answer.probability) if answer.probability is not None else float("nan"))
            else:
                refusals.append(";".join(evaluation.refusals()) or "unusable")
        if not values:
            return {"choice": None, "failure": "no_usable_jev_answer", "refusals": refusals}
        repeated = RepeatedJudgment("next_action", JudgmentScope.ACTION_RANKING, "choice", model or "jev",
                                    hashlib.sha256(text.encode()).hexdigest(), tuple(values),
                                    tuple(p for p in probabilities if np.isfinite(p)))
        stable = repeated.verdict is StabilityVerdict.STABLE
        return {"choice": repeated.modal_value if stable else None, "modal": repeated.modal_value,
                "agreement": repeated.agreement, "verdict": repeated.verdict.value, "repeats": repeated.repeats,
                "counts": dict(repeated.counts), "refusals": refusals}


def make_policy(arm: str, providers: Providers | None, null: dict, trace: list):
    def policy(ctx, compound, h1, h2, executed, menu):
        cards = None
        if arm in ("deepseek_cards", "jev_cards", "deepseek_cards_permuted"):
            cards = {k: E.card_for(ctx, k, h1, h2, permuted=(arm == "deepseek_cards_permuted")) for k in menu}
        text = state_text(ctx, h1, h2, menu, executed, 2 - len(executed), null, cards)
        options = [C.action_id(k) for k in menu] + ["defer"]
        label = f"{arm}:{ctx.tier.name}:{compound}:{len(executed) + 1}"
        if providers is None:
            trace.append({"label": label, "text": text})
            return None, {"reason": "dry_run"}
        if arm.startswith("deepseek"):
            answer = providers.deepseek(label, text, options)
        else:
            answer = providers.jev_choice(label, text, options)
        trace.append({"label": label, "arm": arm, "answer": answer, "state_sha256": hashlib.sha256(text.encode()).hexdigest()})
        chosen = answer.get("choice")
        if arm.startswith("jev") and chosen is None and answer.get("failure") is None:
            key, note = E.choose("separation", ctx, compound, h1, h2, executed, None)
            return key, {"reason": "jev_unstable_fallback_to_separation", "jev": answer}
        if chosen is None:
            return None, {"reason": f"planner_failure:{answer.get('failure')}"}
        if chosen == "defer":
            return None, {"reason": "planner_deferred"}
        return next(k for k in menu if C.action_id(k) == chosen), {"reason": "provider_choice", "provider": answer}
    return policy


def selected_episodes(ctx, fold) -> list:
    chosen = {}
    for compound, truth, decoy, h1, h2 in E.episode_list(ctx, fold):
        chosen.setdefault(compound, []).append((compound, truth, decoy, h1, h2))
    out = []
    for compound, options in sorted(chosen.items()):
        index = E.stable("llm_decoy", ctx.tier.name, compound) % len(options)
        out.append(options[index])
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arms", nargs="*", default=list(ARMS))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--limit", type=int, default=None, help="smoke runs only: first N episodes, written under smoke/")
    args = parser.parse_args()
    started = time.time()
    protocol = C.load_protocol()
    data = C.load()
    null = C.detection_null(data, protocol)
    detected = C.detected_flags(data, null)
    magnitude = E.Magnitude(data, detected)
    out = C.OUTPUTS / ("agent_arms_smoke" if args.limit else "agent_arms")
    out.mkdir(parents=True, exist_ok=True)
    providers = None if args.dry_run else Providers(out, protocol)
    contexts = list(E.contexts(data, protocol, detected, magnitude))
    jobs = [(ctx, fold, ep) for ctx, fold in contexts for ep in selected_episodes(ctx, fold)]
    if args.limit:
        jobs = jobs[:args.limit]
    print(f"episodes per arm: {len(jobs)}", flush=True)
    if args.dry_run:
        trace = []
        ctx, fold, (compound, truth, decoy, h1, h2) = jobs[0]
        for arm in ("deepseek_base", "deepseek_cards"):
            make_policy(arm, None, null, trace)(ctx, compound, h1, h2, [], list(ctx.tier.keys))
        print(trace[0]["text"]); print("-----"); print(trace[1]["text"])
        return
    for arm in args.arms:
        trace: list = []
        policy = make_policy(arm, providers, null, trace)

        def run(job):
            ctx, fold, (compound, truth, decoy, h1, h2) = job
            ctx.extra.setdefault("policies", {})[arm] = policy
            return {"tier": ctx.tier.name, "fold": fold, "decoy": decoy} | E.run_episode(arm, ctx, compound, truth, h1, h2, None)

        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            records = list(pool.map(run, jobs))
        with (out / f"episodes_{arm}.jsonl").open("w", encoding="utf-8") as stream:
            for r in records:
                stream.write(json.dumps(C.clean(r), default=C._default) + chr(10))
        with (out / f"trace_{arm}.jsonl").open("w", encoding="utf-8") as stream:
            for r in trace:
                stream.write(json.dumps(C.clean(r), default=C._default) + chr(10))
        providers.ledger.write()
        C.write_json(out / "jev_usage.json", {"input_tokens_including_prior": providers.jev_tokens,
                                             "prior_input_tokens": providers.prior_jev_tokens,
                                             "usd_at_0.042_per_million": providers.jev_tokens * JEV_USD_PER_MILLION_INPUT / 1e6})
        print(f"{arm}: {len(records)} episodes, {time.time() - started:.0f}s, deepseek ${providers.ledger.total_usd:.4f}, "
              f"jev tokens {providers.jev_tokens}", flush=True)
    C.write_json(out / "manifest.json", {"protocol_hashes": C.frozen_hashes(), "arms": args.arms, "episodes_per_arm": len(jobs),
                                         "deepseek_usd": providers.ledger.total_usd, "jev_input_tokens": providers.jev_tokens,
                                         "jev_usd": providers.jev_tokens * JEV_USD_PER_MILLION_INPUT / 1e6,
                                         "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})


if __name__ == "__main__":
    main()
