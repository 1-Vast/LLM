"""DeepSeek repeatability: 30 first-step deepseek_cards decisions asked three more times.

File summary
- Path: research/dynamic_world_model/repeatability.py
- Purpose: the registered reproducibility check for the language-model planner. The first 30
  first-step states of the deepseek_cards arm (in episode order) are re-sent unchanged three more
  times; agreement is the collision probability of the four answers per state
  (`maestro.stability.RepeatedJudgment`), the same estimator the Jev gate uses.
- Run: python research/dynamic_world_model/repeatability.py
- Depends on: common.py, episodes.py, agent_arms.py, maestro.stability
"""
from __future__ import annotations

import hashlib
import json

import common as C
import episodes as E
import agent_arms as AA


def main() -> None:
    protocol = C.load_protocol()
    data = C.load()
    null = C.detection_null(data, protocol)
    detected = C.detected_flags(data, null)
    magnitude = E.Magnitude(data, detected)
    out = C.OUTPUTS / "agent_arms"
    providers = AA.Providers(out, protocol)
    first = {}
    for line in (out / "trace_deepseek_cards.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["label"].endswith(":1") and r["answer"].get("choice"):
            first[r["label"]] = r["answer"]["choice"]
    contexts = list(E.contexts(data, protocol, detected, magnitude))
    jobs = [(ctx, fold, ep) for ctx, fold in contexts for ep in AA.selected_episodes(ctx, fold)]
    from maestro.judgment import JudgmentScope
    from maestro.stability import RepeatedJudgment
    records = []
    for ctx, fold, (compound, truth, decoy, h1, h2) in jobs:
        label = f"deepseek_cards:{ctx.tier.name}:{compound}:1"
        if label not in first:
            continue
        menu = list(ctx.tier.keys)
        cards = {k: E.card_for(ctx, k, h1, h2) for k in menu}
        text = AA.state_text(ctx, h1, h2, menu, [], 2, null, cards)
        options = [C.action_id(k) for k in menu] + ["defer"]
        answers = [first[label]]
        for repeat in range(3):
            answer = providers.deepseek(f"repeatability:{label}:{repeat + 1}", text, options)
            answers.append(answer.get("choice") or f"failure:{answer.get('failure')}")
        repeated = RepeatedJudgment("next_action", JudgmentScope.ACTION_RANKING, "choice", "deepseek",
                                    hashlib.sha256(text.encode()).hexdigest(), tuple(answers))
        records.append({"label": label, "answers": answers, "agreement": repeated.agreement,
                        "all_identical": len(set(answers)) == 1})
        if len(records) == 30:
            break
    providers.ledger.write()
    summary = {"states": len(records), "mean_agreement": sum(r["agreement"] for r in records) / len(records),
               "all_four_identical": sum(r["all_identical"] for r in records) / len(records),
               "deepseek_usd_total": providers.ledger.total_usd, "records": records}
    C.write_json(out / "repeatability.json", C.clean(summary))
    print({k: v for k, v in summary.items() if k != "records"})


if __name__ == "__main__":
    main()
