"""LLM biomarker hypotheses from a partial observation (block N, knowledge-as-prior arm).

The agent sees part of a drug's viability data (the most and least selectively sensitive
*discovery* lines with lineage and driver mutations), the drug's literature and the virtual cell's
transcriptional evidence. It proposes up to 12 genomic features (CCLE expression or mutation) with a
direction and a rationale. The claims are executable: statistics tests them on discovery lines and
they are scored on held-out *test* lines the agent never saw.

Arms (all single calls, deepseek-flash):
* ``explain_full``  literature + virtual-cell evidence + discovery lines
* ``explain_novc``  literature + discovery lines (no virtual-cell evidence)
* ``explain_prior`` literature + virtual-cell evidence, no discovery lines (hypotheses before data)
"""
from __future__ import annotations

import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
import sys as _sys  # noqa: E402
_sys.path.insert(0, str(HERE))
import models as M  # noqa: E402
OUT = HERE / "agent_outputs"
DRIVERS = ("TP53 KRAS NRAS HRAS BRAF PIK3CA PTEN EGFR ERBB2 ERBB3 APC CTNNB1 SMAD4 ARID1A KMT2D KMT2C NF1 NF2 RB1 "
           "STK11 KEAP1 NFE2L2 FBXW7 MTOR IDH1 IDH2 CDKN2A ATM BRCA1 BRCA2 SMARCA4 SETD2 BAP1 PBRM1 VHL MAP2K1 "
           "MAP3K1 GNAQ GNA11 KIT FLT3 JAK2 NOTCH1 ESR1 AR CREBBP EP300 ASXL1 TET2 DNMT3A SF3B1 U2AF1 SPOP FGFR2 "
           "FGFR3 ALK RET MET POLE").split()
GENE = re.compile(r"^[A-Z0-9][A-Z0-9\-\.]{0,14}$")
N_SHOW = 20

SYSTEM = """You are a cancer pharmacologist looking for the cause of a drug's selective killing pattern.
The drug was screened at 2.5 micromolar for 5 days across hundreds of cancer cell lines (pooled
viability). You may be shown some of the lines that were most and least affected beyond what is
typical for any drug (lineage and driver mutations listed), the drug's literature, and evidence from a
transcriptional virtual cell. Propose genomic features that explain *which* lines are selectively
killed and would predict this in lines you have not seen.

Return one JSON object:
{"explanation": two or three sentences on the most plausible mechanism of selectivity,
 "features": [{"gene": HGNC symbol, "feature": "expression" or "mutation",
               "effect": "sensitizing" or "protective",
               "basis": one short phrase (mechanism, literature, observed pattern),
               "pmids": PMIDs from the provided abstracts (may be empty)}]}
List up to 12 features, most confident first. Mutation features mean damaging or hotspot mutations.
Prefer features with a mechanistic reason; a feature suggested only by a few listed lines is weak
evidence. Do not invent PMIDs."""


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:80]


def line_annotations(world) -> dict:
    info = pd.read_csv(ROOT / "data/external/depmap_19q4/sample_info.csv")
    info = info.set_index("DepMap_ID")
    _, mutated = world.ccle()
    out = {}
    for line in world.lines:
        name = str(info.at[line, "CCLE_Name"]) if line in info.index else line
        lin = " ".join(str(info.at[line, c]) for c in ("lineage", "lineage_subtype") if line in info.index and isinstance(info.at[line, c], str))
        muts = [g for g in DRIVERS if line in mutated.get(g, set())]
        out[line] = f"{name} | {lin} | mut: {', '.join(muts) if muts else 'none of the listed drivers'}"
    return out


def vc_evidence(world, i, genes, n_genes=8) -> str:
    norms = np.where(world.l1000_have[i], world.l1000_norm[i], -1)
    top = np.argsort(-norms)[:2]
    parts = []
    for o in top:
        if norms[o] <= 0:
            continue
        x = world.Xf[i, o]
        up = [genes[j] for j in np.argsort(-x)[:n_genes]]
        dn = [genes[j] for j in np.argsort(x)[:n_genes]]
        parts.append(f"{world.options[o]}: up {', '.join(up)}; down {', '.join(dn)}")
    nb = world.neighbours(i, "known_class", n=5)
    parts.append("most similar reference drugs: " + "; ".join(f"{n} ({m}, {s:.2f})" for n, m, s, _ in nb))
    return "\n".join(parts)


def user_message(arm, drug, moa, targets, lit, vc, shown) -> str:
    lines = [f"Drug: {drug}", f"Annotated mechanism (Drug Repurposing Hub): {moa}",
             f"Annotated targets: {', '.join(targets) if targets else 'none listed'}"]
    if lit and lit.get("hits"):
        lines.append("\nRetrieved abstracts:")
        for h in lit["hits"]:
            lines.append(f"[PMID {h['pmid']}, {h.get('year')}] {h['title']}\n{h['abstract']}")
    if vc:
        lines.append("\nVirtual cell (L1000 landmark response at 10 uM in its two most responsive line x time conditions, "
                     "and transcriptionally most similar screened drugs):\n" + vc)
    if shown:
        sens, res = shown
        lines.append(f"\nMost selectively killed lines (of those shown to you):\n" + "\n".join(f"- {s}" for s in sens))
        lines.append(f"\nLeast affected lines (of those shown to you):\n" + "\n".join(f"- {s}" for s in res))
    return "\n".join(lines)


def validate(obj: dict, pmids: set) -> tuple[dict, dict]:
    dropped = {"bad_gene": 0, "foreign_pmid": 0, "duplicate": 0}
    feats, seen = [], set()
    for f in (obj.get("features") or [])[:12]:
        g = str(f.get("gene", "")).upper().strip() if isinstance(f, dict) else ""
        if not GENE.match(g):
            dropped["bad_gene"] += 1
            continue
        kind = "mutation" if str(f.get("feature", "")).lower().startswith("mut") else "expression"
        if (g, kind) in seen:
            dropped["duplicate"] += 1
            continue
        seen.add((g, kind))
        ps = [str(p) for p in (f.get("pmids") or [])]
        dropped["foreign_pmid"] += sum(p not in pmids for p in ps)
        feats.append({"gene": g, "feature": kind,
                      "effect": "protective" if str(f.get("effect", "")).lower().startswith("prot") else "sensitizing",
                      "basis": str(f.get("basis", ""))[:200], "pmids": [p for p in ps if p in pmids]})
    return {"explanation": str(obj.get("explanation", ""))[:800], "features": feats}, dropped


class Explainer:
    def __init__(self, world, ledger, client, workers=8, profile="flash"):
        self.world, self.ledger, self.client, self.workers = world, ledger, client, workers
        self.profile = profile
        self.lock = threading.Lock()
        self.ann = line_annotations(world)
        import sys
        sys.path.insert(0, str(HERE.parents[2] / "research/astra/mechanism_falsification_20261010"))
        import study as S  # noqa: E402
        self.genes = [str(g) for g in S.load_tier("open")["gene"]]

    def run_one(self, arm: str, i: int, size_tag: str, shown_rows: np.ndarray | None, y: np.ndarray) -> dict:
        from agent.llm import LLMError  # noqa: E402
        w = self.world
        drug = str(w.drug[i])
        tag = arm if self.profile == "flash" else f"{arm}@{self.profile}"
        p = OUT / tag / size_tag / f"{slug(drug)}.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        lp = HERE / "literature" / f"{slug(drug)}.json"
        lit = json.loads(lp.read_text(encoding="utf-8")) if lp.exists() else None
        vc = vc_evidence(w, i, self.genes) if arm in ("explain_full", "explain_prior") else None
        shown = None
        if arm != "explain_prior" and shown_rows is not None:
            r = shown_rows[np.isfinite(y[shown_rows])]
            order = r[np.argsort(y[r])]
            shown = ([self.ann[w.lines[j]] for j in order[:N_SHOW]], [self.ann[w.lines[j]] for j in order[::-1][:N_SHOW]])
        msgs = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": user_message(arm, drug, str(w.moa[i]), w.targets[i], lit, vc, shown)}]
        label = f"{arm}@{self.profile}:{size_tag}:{slug(drug)}"
        with self.lock:
            self.ledger.reserve(label, 0.05 if self.profile == "pro" else 0.01)
        t0 = time.time()
        try:
            obj, resp = M.call_json(self.client, msgs, self.profile)
            status, err = "ok", None
        except LLMError as error:
            obj, resp, status, err = {}, None, "failed", f"{type(error).__name__}:{str(error)[:120]}"
        booked, reserved = M.ledger_usage(resp.usage if resp else None, self.profile)
        with self.lock:
            self.ledger.charge(label, booked, status=status if resp else "failed_unpriced",
                               reserved_usd=reserved if resp else (0.05 if self.profile == "pro" else 0.01), note=err or "")
            self.ledger.write()
        claims, dropped = validate(obj if isinstance(obj, dict) else {}, {h["pmid"] for h in (lit or {}).get("hits", [])})
        rec = {"arm": arm, "profile": self.profile, "size": size_tag, "drug": drug, "status": status, "error": err,
               "seconds": round(time.time() - t0, 2), "usage": resp.usage if resp else None,
               "shown_lines": None if shown is None else {"sensitive": shown[0], "resistant": shown[1]},
               "dropped": dropped, "claims": claims, "raw": obj,
               "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".part")
        tmp.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        tmp.replace(p)
        return rec

    def run(self, tasks):
        with ThreadPoolExecutor(self.workers) as pool:
            return list(pool.map(lambda t: self.run_one(*t), tasks))
