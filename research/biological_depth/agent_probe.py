"""Agent probe: can MAESTRO's reasoning components read a measured signature mechanistically?

File summary
- Path: research/biological_depth/agent_probe.py
- Purpose: give DeepSeek and Jev an anonymised measured SciPlex3 response (no name, structure or
  annotation) and ask for the mechanism class, with and without a retrieval evidence card, under
  the provider ledger's ceiling.
- Core points:
  - The signature is centered on the other skeletons' mean at the same line and dose, so the
    shared stress response cannot decide the answer.
  - The card is labelled as a retrieved analysis of other compounds' measurements; it never
    names the query compound or its annotation.
  - An answer outside the option list is named back once, then scored as a named failure.
  - The score is agreement with a vendor annotation, not mechanism accuracy.
- Run: python research/biological_depth/agent_probe.py --prepared <dir> --output <dir> [--dry-run]
- Depends on: common.py, src/agent/llm.py, src/agent/typesafe.py, src/evaluation/provider_spend.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

import common

sys.path.insert(0, str(common.ROOT / "src"))

LINES = ("A549", "K562", "MCF7")
TOP = 10000.0
JEV_USD_PER_MILLION_INPUT = 0.042


def build_items(prepared: Path, protocol: dict) -> tuple[list[dict], list[str]]:
    conditions = pd.read_csv(prepared / "conditions.csv", index_col="condition_id")
    compounds = pd.read_csv(prepared / "compounds.csv").set_index("compound")
    genes = pd.read_csv(prepared / "genes.csv").symbol.to_numpy()
    y = np.load(prepared / "shifts.npz")["shift"]
    null = json.loads((prepared / "vehicle_null.json").read_text())
    key = {(r.cell_line, r.compound, float(r.dose)): i for i, r in conditions.iterrows()}
    skeleton = compounds.skeleton
    top = {c: {l: key.get((l, c, TOP)) for l in LINES} for c in compounds.index}
    centered, responsive, percentile = {}, {}, {}
    for line in LINES:
        rows = {c: top[c][line] for c in compounds.index if top[c][line] is not None}
        norms = {c: float(np.linalg.norm(y[r])) for c, r in rows.items()}
        ranked = np.array(sorted(norms.values()))
        for c, r in rows.items():
            others = [rows[o] for o in rows if skeleton[o] != skeleton[c]]
            centered[(c, line)] = y[r] - y[others].mean(0)
            threshold = null[line]["q95_at_128_cells"] * np.sqrt(128.0 / conditions.n_cells[r])
            responsive[(c, line)] = norms[c] > threshold
            percentile[(c, line)] = int(round(100.0 * np.searchsorted(ranked, norms[c]) / len(ranked)))
    classes = compounds.pathway_level_2
    per_class = compounds.reset_index().drop_duplicates("skeleton").pathway_level_2.value_counts()
    representative = compounds.reset_index().sort_values("compound").drop_duplicates("skeleton").set_index("skeleton").compound
    eligible = [representative[s] for s in representative.index
                if per_class.get(classes[representative[s]], 0) >= 2
                and any(responsive.get((representative[s], l), False) for l in LINES)
                and all((representative[s], l) in centered for l in LINES)]
    eligible.sort(key=lambda c: hashlib.sha256(("maestro-biodepth-agent|" + skeleton[c]).encode()).hexdigest())
    chosen = eligible[:40]
    options = sorted({classes[c] for c in chosen})
    profile = {c: np.concatenate([centered[(c, l)] for l in LINES]) for c in compounds.index
               if all((c, l) in centered for l in LINES)}
    items = []
    for c in chosen:
        lines_text = []
        for line in LINES:
            if not responsive[(c, line)]:
                lines_text.append(f"{line}: no response above the vehicle noise threshold "
                                  f"(response-size percentile {percentile[(c, line)]} among compounds in this line).")
                continue
            v = centered[(c, line)]
            order = np.argsort(v)
            up = ", ".join(genes[order[::-1][:20]])
            down = ", ".join(genes[order[:20]])
            lines_text.append(f"{line} (response-size percentile {percentile[(c, line)]} among compounds in this line):\n"
                              f"  most increased: {up}\n  most decreased: {down}")
        query = profile[c]
        best: dict[str, float] = {}
        for other, vector in profile.items():
            if skeleton[other] == skeleton[c]:
                continue
            sim = float(query @ vector / (np.linalg.norm(query) * np.linalg.norm(vector)))
            label = classes[other]
            best[label] = max(best.get(label, -1.0), sim)
        ranking = sorted(best.items(), key=lambda kv: -kv[1])
        card = ("Retrieved analysis (signature retrieval over measured SciPlex3 profiles of OTHER compounds; "
                "a similarity to reference compounds, not a measurement of this compound's mechanism; "
                "similar responses can arise from different targets):\n" +
                "\n".join(f"  {i + 1}. {label} (best matching reference compound, cosine {sim:.2f})"
                          for i, (label, sim) in enumerate(ranking[:3])))
        tool = next((label for label, _ in ranking if label in options), None)
        items.append({"compound": c, "skeleton": skeleton[c], "truth": classes[c], "signature": "\n".join(lines_text),
                      "card": card, "tool_answer": tool, "card_classes": [label for label, _ in ranking[:3]]})
    return items, options


def prompt(item: dict, options: list[str], with_card: bool) -> str:
    parts = ["A compound was applied for 24 hours to three human cancer cell lines (A549 lung, K562 myeloid "
             "leukemia, MCF7 breast). Below is the measured transcriptional response at 10 uM, expressed relative "
             "to the average response of other compounds in the same line and dose, so generic stress shared by "
             "most compounds is removed. Gene symbols are HGNC.", "", item["signature"]]
    if with_card:
        parts += ["", item["card"]]
    parts += ["", "Which mechanism class best explains this response? Choose exactly one option from this list:",
              *[f"- {o}" for o in options]]
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true", help="build items and prompts, call nothing")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    protocol = common.load_protocol()
    items, options = build_items(args.prepared, protocol)
    common.write_json(args.output / "items.json", {"options": options, "items": items})
    print(f"items {len(items)}; options {len(options)}", flush=True)
    if args.dry_run:
        print(prompt(items[0], options, True))
        return

    from agent.configuration import MAESTROSettings
    from agent.llm import DeepSeekChatClient, LLMError
    from agent.typesafe import TypeSafeJevClient, TypeSafeSettings, choice
    from evaluation.provider_spend import SpendLedger

    budget = protocol["agent_probe"]["budget_usd"]
    ledger = SpendLedger.load(args.output / "deepseek_spend.json", ceiling_usd=budget["deepseek"],
                              prior_note="agent probe 2026-09-26; separate from the session campaign total")
    client = DeepSeekChatClient(MAESTROSettings.from_workspace(common.ROOT))
    jev_settings = TypeSafeSettings.from_workspace(common.ROOT)
    jev = TypeSafeJevClient(jev_settings) if jev_settings else None
    jev_tokens = 0
    records = []
    raw = (args.output / "responses.jsonl").open("a", encoding="utf-8")
    system = ("You are an expert molecular pharmacologist interpreting drug-induced transcriptional responses. "
              "Reply with one JSON object only.")

    def ask_deepseek(item, with_card):
        messages = [{"role": "system", "content": system},
                    {"role": "user", "content": prompt(item, options, with_card) +
                     '\n\nReturn JSON: {"class": "<exact option text>", "confidence": <0 to 1>, '
                     '"rationale": "<at most 40 words naming the genes that decided it>"}'}]
        label = f"agent_probe:{item['skeleton']}:{'card' if with_card else 'signature'}"
        for attempt in (1, 2):
            ledger.reserve(label, 0.005)
            try:
                data, response = client.complete_json(messages, max_tokens=600)
            except LLMError as error:
                ledger.charge(label, None, status="failed", reserved_usd=0.005,
                              note=getattr(error, "code", type(error).__name__))
                return {"answer": None, "failure": getattr(error, "code", type(error).__name__)}
            ledger.charge(label, response.usage)
            answer = str(data.get("class", "")).strip()
            match = next((o for o in options if o.lower() == answer.lower()), None)
            raw.write(json.dumps({"arm": "deepseek", "card": with_card, "skeleton": item["skeleton"],
                                  "attempt": attempt, "reply": data, "usage": response.usage}) + "\n")
            if match:
                return {"answer": match, "confidence": data.get("confidence"), "rationale": data.get("rationale"),
                        "attempts": attempt}
            messages += [{"role": "assistant", "content": json.dumps(data)},
                         {"role": "user", "content": f"'{answer}' is not one of the listed options. "
                                                     "Choose exactly one option text from the list."}]
        return {"answer": None, "failure": "answer_outside_options_after_one_correction"}

    def ask_jev(item, with_card):
        nonlocal jev_tokens
        if jev is None:
            return {"answer": None, "failure": "jev_not_configured"}
        if jev_tokens * JEV_USD_PER_MILLION_INPUT / 1e6 > budget["jev"]:
            return {"answer": None, "failure": "jev_budget_exhausted"}
        question = choice("mechanism_class", "Which mechanism class best explains this measured response?", options)
        evaluation = jev.evaluate(prompt(item, options, with_card), [question])
        jev_tokens += int(sum(v for k, v in evaluation.usage.items() if "input" in k or "prompt" in k) or 0)
        answer = evaluation.answers.get("mechanism_class")
        raw.write(json.dumps({"arm": "jev", "card": with_card, "skeleton": item["skeleton"], "model": evaluation.model,
                              "usage": dict(evaluation.usage), "refusals": list(evaluation.refusals()),
                              "value": getattr(answer, "value", None),
                              "distribution": dict(getattr(answer, "distribution", {}) or {})}) + "\n")
        if answer is None or not answer.usable:
            return {"answer": None, "failure": ";".join(evaluation.refusals()) or "unusable"}
        return {"answer": answer.value, "probability": answer.probability, "confidence": answer.confidence,
                "distribution": dict(answer.distribution)}

    started = time.time()
    for index, item in enumerate(items):
        record = {"compound": item["compound"], "skeleton": item["skeleton"], "truth": item["truth"],
                  "tool": item["tool_answer"]}
        for with_card in (False, True):
            record[f"deepseek_{'card' if with_card else 'signature'}"] = ask_deepseek(item, with_card)
            record[f"jev_{'card' if with_card else 'signature'}"] = ask_jev(item, with_card)
        if index < 10:
            record["jev_signature_repeats"] = [ask_jev(item, False) for _ in range(2)]
        records.append(record)
        ledger.write()
        print(f"{index + 1}/{len(items)} {time.time() - started:.0f}s spend ${ledger.session_total_usd:.4f}", flush=True)
    raw.close()
    common.write_json(args.output / "records.json", records)
    counts = pd.Series([r["truth"] for r in records]).value_counts()
    prior = sorted(counts[counts == counts.max()].index)[0]

    def accuracy(get) -> dict:
        return common.cluster_bootstrap({r["skeleton"]: float(get(r) == r["truth"]) for r in records})

    arms = {"prior": lambda r: prior, "tool": lambda r: r["tool"]}
    for name in ("deepseek_signature", "deepseek_card", "jev_signature", "jev_card"):
        arms[name] = (lambda n: lambda r: r[n].get("answer"))(name)
    scores = {name: accuracy(get) for name, get in arms.items()}
    per = {name: {r["skeleton"]: float(get(r) == r["truth"]) for r in records} for name, get in arms.items()}
    agreement = []
    for r in records[:10]:
        answers = [r["jev_signature"].get("answer")] + [x.get("answer") for x in r.get("jev_signature_repeats", [])]
        answers = [a for a in answers if a]
        if len(answers) >= 2:
            pairs = [(a, b) for i, a in enumerate(answers) for b in answers[i + 1:]]
            agreement.append(np.mean([a == b for a, b in pairs]))
    summary = {"items": len(records), "options": options, "chance": 1.0 / len(options), "prior_class": prior,
               "accuracy": scores,
               "primary_deepseek_card_minus_signature": common.paired_bootstrap(per["deepseek_card"], per["deepseek_signature"]),
               "jev_card_minus_signature": common.paired_bootstrap(per["jev_card"], per["jev_signature"]),
               "deepseek_card_minus_tool": common.paired_bootstrap(per["deepseek_card"], per["tool"]),
               "jev_pairwise_agreement_first10": float(np.mean(agreement)) if agreement else None,
               "failures": {name: sum(1 for r in records if isinstance(r.get(name), dict) and r[name].get("failure"))
                            for name in ("deepseek_signature", "deepseek_card", "jev_signature", "jev_card")},
               "spend": {"deepseek_usd": round(ledger.session_total_usd, 6), "deepseek_calls": len(ledger.entries),
                         "jev_input_tokens": jev_tokens,
                         "jev_usd_estimate": round(jev_tokens * JEV_USD_PER_MILLION_INPUT / 1e6, 6)},
               "claim_boundary": "Agreement with a vendor pathway annotation from an anonymised 24 h signature; not mechanism accuracy."}
    common.write_json(args.output / "summary.json", summary)
    print(json.dumps(summary, indent=1, default=str), flush=True)


if __name__ == "__main__":
    main()
