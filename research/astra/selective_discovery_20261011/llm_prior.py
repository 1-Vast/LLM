"""LLM literature prior for block P: which lineages would a compound selectively kill?

One deepseek-flash call per compound (thinking off, ``complete_json``). The model sees the
compound's name, annotated mechanism, targets, clinical phase and indication, and returns a
probability for each of the 14 target lineages that the compound kills that lineage selectively
(registered hit definition, stated in words). It never sees a viability value. A ``masked`` arm
withholds the name (mechanism and targets only) as a memorisation check.

Records are cached per compound under ``agent_outputs/prior[_masked]/``. Every call is priced in the
block's spend ledger (``tmp/selective_discovery_spend.json``, ceiling USD 10).
"""
from __future__ import annotations

import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LEDGER = ROOT / "tmp/selective_discovery_spend.json"
CEILING_USD = 10.0
OUT = HERE / "agent_outputs"

SYSTEM = """You are a cancer pharmacologist. A compound is tested once at 2.5 micromolar for 5 days in a
pooled viability screen of about 578 adherent human cancer cell lines (PRISM). For each tumour
lineage listed, estimate the probability that the compound kills that lineage SELECTIVELY: the mean
log2 fold change over lines of that lineage is at least 0.5 lower than over all other lines, and the
lineage's own mean log2 fold change is -0.5 or lower. Most compounds are selective for no lineage;
base rates are about 0.2-2.5% per lineage. Use what is known about the compound's cytotoxic
mechanism at this concentration, lineage-specific dependencies (for example oncogenic drivers,
lineage transcription factors, drug transporters), and any published screening evidence.

Return one JSON object:
{"rationale": at most two sentences,
 "p": {lineage: probability in [0, 1] for every listed lineage}}
Use the lineage names exactly as given."""


def slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")[:80] or "x"


def user_message(name: str | None, moa: str, targets: list[str], phase: str, indication: str, lineages: list[str]) -> str:
    who = f"Compound: {name}\n" if name else "Compound: (name withheld)\n"
    return (who + f"Annotated mechanism: {moa}\nTargets: {', '.join(sorted(targets)) or 'unknown'}\n"
            f"Clinical phase: {phase}\nIndication: {indication}\nLineages: {', '.join(lineages)}")


class Prior:
    def __init__(self, workers: int = 8):
        sys.path.insert(0, str(ROOT / "src"))
        sys.path.insert(0, str(ROOT))
        from agent.llm import DeepSeekChatClient, MAESTROSettings  # noqa: E402
        from tools.evaluation.costs import SpendLedger  # noqa: E402
        self.client = DeepSeekChatClient(MAESTROSettings.from_workspace(ROOT))
        self.ledger = SpendLedger.load(LEDGER, ceiling_usd=CEILING_USD, prior_note="block P (selective discovery) provider spend")
        self.lock = threading.Lock()
        self.workers = workers

    def run_one(self, arm: str, brd: str, name: str, moa: str, targets: list[str], phase: str, indication: str,
                lineages: list[str]) -> dict:
        from agent.llm import LLMError  # noqa: E402
        p = OUT / arm / f"{slug(brd)}.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        msgs = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": user_message(None if arm == "prior_masked" else name, moa, targets, phase,
                                                         indication, lineages)}]
        label = f"{arm}:{slug(brd)}"
        with self.lock:
            self.ledger.reserve(label, 0.01)
        t0 = time.time()
        try:
            obj, resp = self.client.complete_json(msgs, max_tokens=1500)
            status, err = "ok", None
        except LLMError as error:
            obj, resp, status, err = {}, None, "failed", f"{type(error).__name__}:{str(error)[:120]}"
        with self.lock:
            self.ledger.charge(label, resp.usage if resp else None, status=status if resp else "failed_unpriced",
                               reserved_usd=0.01, note=err or "")
            self.ledger.write()
        probs = {}
        raw = obj.get("p", {}) if isinstance(obj, dict) else {}
        for T in lineages:
            v = raw.get(T) if isinstance(raw, dict) else None
            try:
                v = float(v)
                probs[T] = min(max(v, 0.0), 1.0) if v == v else None
            except (TypeError, ValueError):
                probs[T] = None
        rec = {"arm": arm, "brd": brd, "name": name if arm != "prior_masked" else None, "status": status, "error": err,
               "seconds": round(time.time() - t0, 2), "model": resp.model if resp else None,
               "finish_reason": resp.finish_reason if resp else None, "usage": resp.usage if resp else None,
               "p": probs, "n_missing": sum(v is None for v in probs.values()), "raw": obj,
               "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".part")
        tmp.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        tmp.replace(p)
        return rec

    def run(self, tasks: list[tuple]) -> list[dict]:
        with ThreadPoolExecutor(self.workers) as pool:
            return list(pool.map(lambda t: self.run_one(*t), tasks))
