"""Executable mechanism hypotheses (EMH) written by the LLM agent, before any L1000 value is read.

For every mechanism class in SPLIT.json the agent writes one structured hypothesis: what the
mechanism should do to the measured landmark genes, in which of the nine core lines, how fast, and
what observation would contradict it. The agent never sees L1000 values. Two variants:

* ``lit``   - the class's retrieved abstracts (``literature/<slug>.json``) are in the prompt and every
              cited PMID must come from them (others are dropped and counted);
* ``nolit`` - the same prompt without abstracts (parametric knowledge only).

Categories only: the agent states directions and ordinal levels (none/weak/moderate/strong). Numbers
come from the world model's calibration on reference drugs, never from the agent.

Output: ``emh/<variant>/<slug>.json`` (one per class, written once; a rerun skips existing files)
and the spend ledger ``tmp/mechanism_falsification_spend.json`` (written after every call).
"""
from __future__ import annotations

import gzip
import json
import sys
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from agent.llm import DeepSeekChatClient, LLMError, MAESTROSettings  # noqa: E402
from tools.evaluation.costs import SpendLedger  # noqa: E402

from literature import slug  # noqa: E402

SRC = ROOT / "data/external/lincs_l1000_gse92742"
LEDGER = ROOT / "tmp/mechanism_falsification_spend.json"
CEILING_USD = 10.0
LEVELS = ("none", "weak", "moderate", "strong")
KINETICS = ("fast", "slow", "sustained", "none")
GENERIC = ("proliferation_down", "g1_arrest", "g2m_arrest", "dna_damage_response", "unfolded_protein_response",
           "oxidative_stress", "heat_shock", "apoptosis", "interferon", "cholesterol_synthesis_up", "none")
LINES = ("A375", "A549", "HA1E", "HCC515", "HEPG2", "HT29", "MCF7", "PC3", "VCAP")

SYSTEM = """You are the hypothesis-compiler component of a scientific agent. You turn a drug mechanism
class into an executable, falsifiable hypothesis about a transcriptional profiling experiment.

Experiment: each drug of the class is applied at 10 micromolar to each of nine human cell lines
(A375, A549, HA1E, HCC515, HEPG2, HT29, MCF7, PC3, VCAP); mRNA of 978 landmark genes is measured
6 hours and 24 hours later and expressed as a signed change against vehicle. You do not see any
measurement. Predict only directions and ordinal levels; never give numbers.

Return one JSON object with exactly these keys:
- "mechanism": the class name as given.
- "primary_targets": gene symbols of the direct targets (may be empty).
- "proximal_up", "proximal_down": landmark genes expected to change within about 6 h because of
  this specific mechanism (direct transcriptional targets of the affected pathway). Exclude generic
  proliferation, cell-cycle and stress markers that many unrelated drugs also move. At most 15
  each; only genes from the landmark list; an empty list is acceptable.
- "late_up", "late_down": landmark genes expected to change by 24 h as secondary consequences
  specific to this mechanism (at most 15 each; only landmark genes).
- "generic_effects": the generic programs expected by 24 h, chosen from: proliferation_down,
  g1_arrest, g2m_arrest, dna_damage_response, unfolded_protein_response, oxidative_stress,
  heat_shock, apoptosis, interferon, cholesterol_synthesis_up, none.
- "kinetics": "fast" (clear at 6 h), "slow" (mostly after 6 h), "sustained" (similar at both) or
  "none" (no transcriptional response expected in these lines).
- "magnitude": {"6h": level, "24h": level} for a responsive line; level is one of
  none, weak, moderate, strong.
- "line_response": an object mapping each of the nine lines to a level, using what is known about
  each line (lineage, driver mutations, receptor expression, TP53/RB status, immortalisation).
- "context_requirements": short statements of what a cell must have for a response.
- "falsifiers": observations in this experiment that would contradict the hypothesis.
- "confidence": one of low, medium, high, for the hypothesis as a whole.
- "evidence": list of {"pmid": ..., "supports": short claim}; cite only PMIDs given in the
  abstracts below (an empty list if none are relevant or none are given).
State weak or none honestly when a class is not expected to act on these cell lines."""


def landmark_genes() -> list[str]:
    g = pd.read_csv(SRC / "GSE92742_Broad_LINCS_gene_info.txt.gz", sep="\t")
    return sorted(g[g.pr_is_lm == 1].pr_gene_symbol.astype(str))


def class_targets(split: dict, drugs_table: pd.DataFrame) -> dict[str, list[str]]:
    tgt = drugs_table.set_index("pert_iname").target.to_dict()
    out: dict[str, dict[str, int]] = {}
    for d, v in split["drugs"].items():
        t = tgt.get(d)
        if isinstance(t, str):
            for g in t.split("|"):
                out.setdefault(v["moa"], {}).setdefault(g, 0)
                out[v["moa"]][g] += 1
    return {k: [g for g, _ in sorted(v.items(), key=lambda x: -x[1])][:12] for k, v in out.items()}


def prompt(moa: str, targets: list[str], landmarks: list[str], lit: dict | None) -> list[dict]:
    parts = [f"Mechanism class: {moa}",
             f"Annotated targets of drugs in this class (Drug Repurposing Hub): {', '.join(targets) or 'none listed'}",
             "Landmark genes: " + " ".join(landmarks)]
    if lit is not None:
        if lit["hits"]:
            parts.append("Retrieved abstracts (Europe PMC):")
            for h in lit["hits"]:
                parts.append(f"PMID {h['pmid']} ({h['year']}): {h['title']}\n{h['abstract']}")
        else:
            parts.append("Retrieved abstracts: none were found for this class.")
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": "\n\n".join(parts)}]


def validate(obj: dict, moa: str, landmarks: set[str], allowed_pmids: set[str]) -> tuple[dict, dict]:
    """Coerce to the schema; count every dropped item so a malformed answer is visible."""
    dropped = {"non_landmark_genes": 0, "bad_levels": 0, "foreign_pmids": 0, "missing_lines": 0}
    out: dict = {"mechanism": moa}
    out["primary_targets"] = [str(g) for g in obj.get("primary_targets") or []][:20]
    for k in ("proximal_up", "proximal_down", "late_up", "late_down"):
        genes = [str(g).upper() for g in obj.get(k) or []]
        keep = [g for g in dict.fromkeys(genes) if g in landmarks][:15]
        dropped["non_landmark_genes"] += len(genes) - len(keep)
        out[k] = keep
    generic = [str(x).lower() for x in obj.get("generic_effects") or []]
    out["generic_effects"] = [x for x in dict.fromkeys(generic) if x in GENERIC]
    dropped["bad_generic"] = len(generic) - len(out["generic_effects"])
    kin = str(obj.get("kinetics", "")).lower()
    out["kinetics"] = kin if kin in KINETICS else "none"
    mag = obj.get("magnitude") or {}
    out["magnitude"] = {}
    for t in ("6h", "24h"):
        lv = str(mag.get(t, "")).lower()
        if lv not in LEVELS:
            dropped["bad_levels"] += 1
            lv = "none"
        out["magnitude"][t] = lv
    lr = obj.get("line_response") or {}
    out["line_response"] = {}
    for line in LINES:
        lv = str(lr.get(line, "")).lower()
        if lv not in LEVELS:
            dropped["missing_lines" if line not in lr else "bad_levels"] += 1
            lv = "none"
        out["line_response"][line] = lv
    out["context_requirements"] = [str(x) for x in obj.get("context_requirements") or []][:10]
    out["falsifiers"] = [str(x) for x in obj.get("falsifiers") or []][:10]
    conf = str(obj.get("confidence", "")).lower()
    out["confidence"] = conf if conf in ("low", "medium", "high") else "low"
    ev = []
    for e in obj.get("evidence") or []:
        pmid = str((e or {}).get("pmid", "")).strip()
        if pmid in allowed_pmids:
            ev.append({"pmid": pmid, "supports": str(e.get("supports", ""))[:300]})
        else:
            dropped["foreign_pmids"] += 1
    out["evidence"] = ev
    return out, dropped


def main(variants: list[str], limit: int | None = None, workers: int = 6) -> None:
    import threading
    from concurrent.futures import ThreadPoolExecutor
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    drugs_table = pd.read_csv(SRC / "repurposing_drugs_20200324.txt", sep="	", comment="!")
    classes = sorted({v["moa"] for v in split["drugs"].values()})[:limit]
    targets = class_targets(split, drugs_table)
    lms = landmark_genes()
    lmset = set(lms)
    client = DeepSeekChatClient(MAESTROSettings.from_workspace(ROOT))
    ledger = SpendLedger.load(LEDGER, ceiling_usd=CEILING_USD, prior_note="block M (mechanism falsification) provider spend")
    lock = threading.Lock()
    skipped: list[str] = []

    def one(task: tuple[str, str]) -> None:
        variant, moa = task
        out_dir = HERE / "emh" / variant
        path = out_dir / f"{slug(moa)}.json"
        if path.exists():
            return
        lit_path = HERE / "literature" / f"{slug(moa)}.json"
        if variant == "lit" and not lit_path.exists():
            skipped.append(moa)
            return
        lit = json.loads(lit_path.read_text(encoding="utf-8")) if variant == "lit" else None
        allowed = {h["pmid"] for h in lit["hits"]} if lit else set()
        msgs = prompt(moa, targets.get(moa, []), lms, lit)
        label = f"emh:{variant}:{slug(moa)}"
        with lock:
            ledger.reserve(label, 0.01)
        t0 = time.time()
        try:
            obj, resp = client.complete_json(msgs, max_tokens=3000)
            status, err = "ok", None
        except LLMError as error:
            obj, resp, status, err = {}, None, "failed", f"{type(error).__name__}:{getattr(error, 'code', '')}"
        with lock:
            ledger.charge(label, resp.usage if resp else None, status=status if resp else "failed_unpriced",
                          reserved_usd=0.01, note=err or "")
            ledger.write()
        emh, dropped = validate(obj, moa, lmset, allowed)
        rec = {"variant": variant, "mechanism": moa, "status": status, "error": err, "seconds": round(time.time() - t0, 2),
               "model": resp.model if resp else None, "finish_reason": resp.finish_reason if resp else None,
               "usage": resp.usage if resp else None, "dropped": dropped, "hypothesis": emh,
               "raw": obj, "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        out_dir.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".part")
        tmp.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)

    tasks = [(v, m) for v in variants for m in classes]
    with ThreadPoolExecutor(workers) as pool:
        list(pool.map(one, tasks))
    print(variants, "done; skipped (no literature yet):", len(skipped), "; ledger total", round(ledger.total_usd, 4))


if __name__ == "__main__":
    main(sys.argv[1].split(","), int(sys.argv[2]) if len(sys.argv) > 2 else None)
