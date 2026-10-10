"""Agent analogies: which observed mechanism classes should an unobserved one resemble? (no data read)

For every mechanism class, the agent chooses, from the classes that have reference drugs (excluding
the class itself), up to five whose drugs should produce the most similar landmark-gene response
in the nine core lines at 10 uM, 6-24 h, with an ordinal similarity, and states the expected
overall response strength. It sees only class names and the class's annotated targets (Drug
Repurposing Hub), never an L1000 value. The knowledge compiler can then predict an unobserved class
as a similarity-weighted mean of the analog classes' prototypes built from reference drugs.

Output: ``analogy/<slug>.json`` (one per class, written once) and the shared spend ledger.
Usage: python analogy.py [limit]
"""
from __future__ import annotations

import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

import emh as E
from literature import slug

HERE = Path(__file__).resolve().parent
LEVELS = ("none", "weak", "moderate", "strong")
SIM = ("high", "medium", "low")

SYSTEM = """You are the analogical-reasoning component of a scientific agent studying drug mechanisms.

Experiment: drugs are applied at 10 micromolar to nine human cell lines (A375 melanoma, A549 lung,
HA1E immortalised kidney epithelium, HCC515 lung, HEPG2 liver, HT29 colon, MCF7 breast, PC3 and
VCAP prostate); mRNA of 978 landmark genes is measured 6 h and 24 h later as signed change against
vehicle. You never see measurements.

Given one mechanism class, choose from the REFERENCE LIST the classes whose drugs should produce the
most similar transcriptional response in these cells: shared pathway, shared downstream program
(for example mitotic arrest, translation stress, DNA damage, sterol synthesis, nuclear receptor
activation), or, for mechanisms that act on receptors these cells barely express, other classes that
should also produce little or no response. Use only names exactly as written in the list.

Return one JSON object:
{"expected_response": "none" | "weak" | "moderate" | "strong",
 "analogs": [{"class": name from the list, "similarity": "high" | "medium" | "low"}, ... at most 5,
             most similar first],
 "rationale": one or two sentences}"""


def prompt(moa: str, targets: list[str], reference: list[str]) -> list[dict]:
    user = (f"Mechanism class: {moa}\n"
            f"Annotated targets of drugs in this class: {', '.join(targets) or 'none listed'}\n\n"
            "REFERENCE LIST:\n" + "\n".join(c for c in reference if c != moa))
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


def validate(obj: dict, moa: str, reference: set[str]) -> tuple[dict, dict]:
    dropped = {"unknown_class": 0, "self": 0, "bad_similarity": 0}
    out = {"mechanism": moa}
    lev = str(obj.get("expected_response", "")).lower()
    out["expected_response"] = lev if lev in LEVELS else "weak"
    analogs, seen = [], set()
    for a in obj.get("analogs") or []:
        name = str(a.get("class", "")) if isinstance(a, dict) else str(a)
        sim = str(a.get("similarity", "")).lower() if isinstance(a, dict) else "medium"
        if name == moa:
            dropped["self"] += 1
            continue
        if name not in reference or name in seen:
            dropped["unknown_class"] += 1
            continue
        if sim not in SIM:
            dropped["bad_similarity"] += 1
            sim = "low"
        analogs.append({"class": name, "similarity": sim})
        seen.add(name)
    out["analogs"] = analogs[:5]
    out["rationale"] = str(obj.get("rationale", ""))[:600]
    return out, dropped


def main(limit: int | None = None, workers: int = 8) -> None:
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    drugs_table = pd.read_csv(E.SRC / "repurposing_drugs_20200324.txt", sep="\t", comment="!")
    classes = sorted({v["moa"] for v in split["drugs"].values()})[:limit]
    reference = sorted({v["moa"] for v in split["drugs"].values() if v["role"] == "reference"})
    refset = set(reference)
    targets = E.class_targets(split, drugs_table)
    client = E.DeepSeekChatClient(E.MAESTROSettings.from_workspace(E.ROOT))
    ledger = E.SpendLedger.load(E.LEDGER, ceiling_usd=E.CEILING_USD, prior_note="block M (mechanism falsification) provider spend")
    lock = threading.Lock()
    out_dir = HERE / "analogy"
    out_dir.mkdir(exist_ok=True)

    def one(moa: str) -> None:
        path = out_dir / f"{slug(moa)}.json"
        if path.exists():
            return
        label = f"analogy:{slug(moa)}"
        with lock:
            ledger.reserve(label, 0.01)
        t0 = time.time()
        try:
            obj, resp = client.complete_json(prompt(moa, targets.get(moa, []), reference), max_tokens=1500)
            status, err = "ok", None
        except E.LLMError as error:
            obj, resp, status, err = {}, None, "failed", f"{type(error).__name__}:{getattr(error, 'code', '')}"
        with lock:
            ledger.charge(label, resp.usage if resp else None, status=status if resp else "failed_unpriced", reserved_usd=0.01, note=err or "")
            ledger.write()
        hyp, dropped = validate(obj, moa, refset)
        rec = {"mechanism": moa, "status": status, "error": err, "seconds": round(time.time() - t0, 2),
               "usage": resp.usage if resp else None, "dropped": dropped, "analogy": hyp, "raw": obj,
               "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        tmp = path.with_suffix(".part")
        tmp.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)

    with ThreadPoolExecutor(workers) as pool:
        list(pool.map(one, classes))
    print("analogy done; ledger total", round(ledger.total_usd, 4))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
