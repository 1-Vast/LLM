"""Critique-and-revise pass over literature-grounded hypotheses (variant ``lit_critic``).

A separate critic call receives one ``lit`` hypothesis and the same retrieved abstracts, and returns
a corrected hypothesis in the same schema plus the list of changes. It never sees L1000 values.
This tests whether a Co-Scientist-style reflection step improves hypotheses that data will later
judge, against the single-pass ``lit`` variant.
"""
from __future__ import annotations

import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import emh as E  # noqa: E402
from literature import slug  # noqa: E402

CRITIC = """You are an independent scientific critic reviewing a hypothesis written by another agent
about a transcriptional profiling experiment (10 micromolar drug, nine cell lines, 978 landmark
genes, 6 h and 24 h). You do not see any measurement.

Check, item by item:
1. Direction: is each gene's listed direction (up or down) what this mechanism would cause? For
   example, inhibiting a signalling kinase lowers the transcription of that pathway's immediate
   target genes. Move a gene to the correct list, or remove it if its direction cannot be
   justified. A gene must not appear in both an up and a down list of the same time.
2. Specificity: remove generic proliferation or stress genes from the proximal lists.
3. Line responses: correct levels that contradict known biology of the line (lineage, driver
   mutations, receptor expression, TP53/RB status, immortalisation by viral oncogenes).
4. Kinetics and magnitude: correct them if they contradict the mechanism.
5. Evidence: keep only citations whose abstract supports the stated claim.

Return one JSON object with the same keys as the input hypothesis (same allowed values and limits),
plus "changes": a list of short strings describing each correction (empty if none)."""


def main(limit: int | None = None, workers: int = 6) -> None:
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    classes = sorted({v["moa"] for v in split["drugs"].values()})[:limit]
    lms = E.landmark_genes()
    lmset = set(lms)
    client = E.DeepSeekChatClient(E.MAESTROSettings.from_workspace(E.ROOT))
    ledger = E.SpendLedger.load(E.LEDGER, ceiling_usd=E.CEILING_USD, prior_note="block M (mechanism falsification) provider spend")
    lock = threading.Lock()
    out_dir = HERE / "emh" / "lit_critic"
    out_dir.mkdir(parents=True, exist_ok=True)

    def one(moa: str) -> None:
        path = out_dir / f"{slug(moa)}.json"
        src = HERE / "emh" / "lit" / f"{slug(moa)}.json"
        if path.exists() or not src.exists():
            return
        base = json.loads(src.read_text(encoding="utf-8"))
        lit = json.loads((HERE / "literature" / f"{slug(moa)}.json").read_text(encoding="utf-8"))
        allowed = {h["pmid"] for h in lit["hits"]}
        parts = [f"Mechanism class: {moa}", "Landmark genes: " + " ".join(lms)]
        if lit["hits"]:
            parts.append("Retrieved abstracts (Europe PMC):")
            for h in lit["hits"]:
                parts.append(f"PMID {h['pmid']} ({h['year']}): {h['title']}\n{h['abstract']}")
        parts.append("Hypothesis to review:\n" + json.dumps(base["hypothesis"], ensure_ascii=False))
        msgs = [{"role": "system", "content": CRITIC}, {"role": "user", "content": "\n\n".join(parts)}]
        label = f"emh:lit_critic:{slug(moa)}"
        with lock:
            ledger.reserve(label, 0.01)
        t0 = time.time()
        try:
            obj, resp = client.complete_json(msgs, max_tokens=3500)
            status, err = "ok", None
        except E.LLMError as error:
            obj, resp, status, err = {}, None, "failed", f"{type(error).__name__}:{getattr(error, 'code', '')}"
        with lock:
            ledger.charge(label, resp.usage if resp else None, status=status if resp else "failed_unpriced",
                          reserved_usd=0.01, note=err or "")
            ledger.write()
        hyp, dropped = E.validate(obj, moa, lmset, allowed)
        if status != "ok":
            hyp = base["hypothesis"]  # a failed critique leaves the reviewed hypothesis unchanged, recorded as such
        rec = {"variant": "lit_critic", "mechanism": moa, "status": status, "error": err, "seconds": round(time.time() - t0, 2),
               "model": resp.model if resp else None, "finish_reason": resp.finish_reason if resp else None,
               "usage": resp.usage if resp else None, "dropped": dropped, "hypothesis": hyp,
               "changes": [str(c) for c in (obj.get("changes") or [])][:30], "raw": obj,
               "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        tmp = path.with_suffix(".part")
        tmp.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)

    with ThreadPoolExecutor(workers) as pool:
        list(pool.map(one, classes))
    print("lit_critic done; ledger total", round(ledger.total_usd, 4))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
