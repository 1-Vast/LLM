"""Arm L: an LLM knowledge prior over the 5 uM menu (one fixed prompt, no tuning, temperature 0).

The model sees the line's name, organ and driver alterations, and each drug's targets and MoA. It
never sees a phenotype, RNA value or STATE output. Reply: up to 30 drug names, most selective first.
Names outside the menu are dropped and counted; an unparseable reply is refused as LLM_UNPARSEABLE.
Spend is priced from provider usage into a ledger with a study ceiling (LLM_SPEND_CEILING).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(HERE)]
import analysis as A  # noqa: E402

CEILING_USD = 1.00
SHORTLIST = 30
PROMPT = (
    "You are advising a cancer pharmacology screen. A pooled panel of 50 cancer cell lines is treated for 24 hours "
    "with each drug at 5 uM; each line's relative survival is measured against DMSO. For the line below, choose "
    "the drugs most likely to reduce THIS line's survival MORE than they reduce the average line in the panel "
    "(selective vulnerability, not general toxicity). Use the line's lineage and driver alterations and the drugs' "
    "targets and mechanisms. Return JSON {\"ranked\": [up to 30 drug names copied exactly from the list, most "
    "selective first]}."
)


def menu_text(drugs: pd.DataFrame, names: list[str]) -> str:
    rows = {A.norm(r.drug): r for _, r in drugs.iterrows()}
    out = []
    for name in names:
        r = rows.get(A.norm(name))
        targets = str(r.targets) if r is not None and r.targets else "unknown"
        moa = str(r["moa-fine"]) if r is not None else "unknown"
        out.append(f"{name} | targets: {targets} | {moa}")
    return "\n".join(out)


def line_text(cells: pd.DataFrame, name: str) -> str:
    rows = cells[cells.cell_name.map(A.norm) == A.norm(name)]
    organ = rows.Organ.iloc[0] if len(rows) else "unknown"
    alts = [f"{r.Driver_Gene_Symbol} {r.Driver_ProtEffect_or_CdnaEffect} ({r.Driver_Mech_InferDM or 'unknown'})" for _, r in rows.iterrows()]
    return f"Cell line: {name}\nOrgan: {organ}\nDriver alterations: {'; '.join(alts) if alts else 'none recorded'}"


def main():
    from agent.llm import DeepSeekChatClient, MAESTROSettings
    from tools.evaluation.costs import SpendLedger

    parser = argparse.ArgumentParser()
    parser.add_argument("--files", nargs="+", required=True)
    parser.add_argument("--out", type=Path, default=HERE / "llm")
    args = parser.parse_args()
    if any(f in A.P.HELDOUT for f in args.files) and not (HERE / "FREEZE.json").exists():
        raise SystemExit("held-out LLM answers may be requested only after FREEZE.json exists")
    drugs = pd.read_parquet(A.CACHE / "metadata/tahoe_drugs.parquet")
    cells = pd.read_parquet(A.CACHE / "metadata/tahoe_cells.parquet")
    labels = json.loads((HERE / "MENU.json").read_text(encoding="utf-8"))["labels_5uM"]
    names = [A.drug_of(l) for l in labels]
    menu = menu_text(drugs, names)
    lookup = {A.norm(n): n for n in names}
    client = DeepSeekChatClient(MAESTROSettings.from_workspace(ROOT))
    ledger_path = ROOT / "tmp/phenotype_anchor_20261010_spend.json"
    ledger = SpendLedger.load(ledger_path, ceiling_usd=CEILING_USD)
    args.out.mkdir(parents=True, exist_ok=True)
    for f in args.files:
        target = args.out / f"{f}.json"
        if target.exists():
            continue
        census = json.loads((ROOT / f"research/astra/zeroshot_context_20261007/census/{f}.json").read_text(encoding="utf-8"))
        line = census["cell_names"][0]
        messages = [{"role": "system", "content": PROMPT},
                    {"role": "user", "content": line_text(cells, line) + "\n\nDrugs (name | targets | mechanism):\n" + menu}]
        record = {"file": f, "line": line, "prompt_sha256": hashlib.sha256(json.dumps(messages).encode()).hexdigest()}
        try:
            ledger.reserve(f"llm_arm:{f}", 0.02)
        except ValueError as error:
            record.update(status="refused", reason="LLM_SPEND_CEILING", detail=str(error))
            target.write_text(json.dumps(record, indent=1), encoding="utf-8")
            continue
        started = time.perf_counter()
        try:
            reply, response = client.complete_json(messages, max_tokens=1500)
            usage = dict(response.usage)
            ledger.charge(f"llm_arm:{f}", usage, reserved_usd=0.02)
            ranked = reply.get("ranked", []) if isinstance(reply, dict) else []
            kept = [lookup[A.norm(x)] for x in ranked if isinstance(x, str) and A.norm(x) in lookup]
            kept = list(dict.fromkeys(kept))[:SHORTLIST]
            record.update(status="ok", ranked=kept, dropped=[x for x in ranked if not (isinstance(x, str) and A.norm(x) in lookup)],
                          usage=usage, finish_reason=response.finish_reason, model=response.model)
        except Exception as error:  # noqa: BLE001 -- every failure is recorded by name, charged at its reservation
            ledger.charge(f"llm_arm:{f}", None, status="error", reserved_usd=0.02, note=type(error).__name__)
            record.update(status="refused", reason="LLM_UNPARSEABLE", detail=f"{type(error).__name__}: {error}"[:400])
        record["seconds"] = round(time.perf_counter() - started, 2)
        ledger.write()
        target.write_text(json.dumps(record, indent=1), encoding="utf-8")
        print(json.dumps({k: record.get(k) for k in ("file", "line", "status", "seconds")}), flush=True)
    print(json.dumps({"session_usd": ledger.session_total_usd, "total_usd": ledger.total_usd}))


if __name__ == "__main__":
    main()
