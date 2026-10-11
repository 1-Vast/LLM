"""LLM scientific agent for block N: literature-grounded mechanism routing and biomarker hypotheses.

For a query drug the agent states, as structured and executable claims:

* ``routes``: up to four mechanism classes from the reference vocabulary whose *cytotoxic*
  phenotype across cancer cell lines it expects the drug to share, with weights. They are compiled
  into a mixture of those classes' reference viability profiles.
* ``biomarkers``: up to four gene features (expression or mutation in CCLE) expected to make a line
  more sensitive or more resistant. They are compiled into a line score from CCLE 19Q4.
* ``keep_neighbours`` (arm ``adjudicate``): which of the virtual cell's ten most transcriptionally
  similar reference drugs share the drug's cytotoxic mechanism, rather than a response that only
  looks alike (generic stress, cationic amphiphilic effects, a different target).

Arms: ``route_lit`` (name, Hub annotation, abstracts), ``route_nolit`` (no abstracts),
``adjudicate_lit`` (route_lit plus the virtual cell's neighbours), ``masked_nolit`` (no name, no
abstracts: annotation and targets only; a leakage check against ``route_nolit``). The agent never
sees a viability value. Every call is priced in the block's spend ledger.
"""
from __future__ import annotations

import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
import sys as _sys  # noqa: E402
_sys.path.insert(0, str(HERE))
import models as M  # noqa: E402
LEDGER = ROOT / "tmp/mechanism_routing_spend.json"
CEILING_USD = 10.0
OUT = HERE / "agent_outputs"
ARMS = ("route_lit", "route_nolit", "adjudicate_lit", "masked_nolit")
GENE = re.compile(r"^[A-Z0-9][A-Z0-9\-\.]{0,14}$")

SYSTEM = """You are a cancer pharmacologist. A compound was tested at 2.5 micromolar for 5 days against
about 578 barcoded human cancer cell lines (pooled viability screen). Its effect on each line will be
predicted by analogy: you name the mechanism classes, among a fixed vocabulary of classes whose
member drugs were screened, whose pattern of *which lines are killed* the compound should share. A
pattern of killing is driven by what actually kills cells at this concentration (for example a
dominant off-target, a cytotoxic class effect, a physicochemical effect such as cationic amphiphilic
lysosomal stress, or no killing at all), which need not be the compound's annotated indication.

Return one JSON object:
{"cytotoxic_mechanism": one sentence on what most plausibly kills cells at 2.5 uM, or that it is
   expected to be largely inactive,
 "expected_killing": one of "broad", "selective", "weak", "none",
 "routes": [{"class": exact class name from the vocabulary, "weight": number in (0, 1],
             "pmids": PMIDs from the provided abstracts that support it (may be empty)}] (0 to 4 items;
   empty if no class in the vocabulary shares the killing pattern),
 "biomarkers": [{"gene": HGNC symbol, "feature": "expression" or "mutation",
                 "effect": "sensitizing" or "protective", "pmids": [...]}] (0 to 4 items; only
   features with a mechanistic reason to change sensitivity to this compound),
 "keep_neighbours": names from the transcriptional neighbour list that share the compound's
   cytotoxic mechanism (only when a neighbour list is given; may be empty)}
Use class names exactly as written in the vocabulary. Do not invent PMIDs. Prefer fewer, well-
justified claims to many weak ones."""


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:80]


def user_message(arm: str, drug: str, moa: str, targets: list[str], vocab: dict, lit: dict | None,
                 neighbours: list | None) -> str:
    name = "an undisclosed compound" if arm.startswith("masked") else drug
    lines = [f"Compound: {name}", f"Annotated mechanism (Drug Repurposing Hub): {moa}",
             f"Annotated targets: {', '.join(targets) if targets else 'none listed'}"]
    if lit and lit.get("hits"):
        lines.append("\nRetrieved abstracts:")
        for h in lit["hits"]:
            lines.append(f"[PMID {h['pmid']}, {h.get('year')}] {h['title']}\n{h['abstract']}")
    if neighbours:
        lines.append("\nTranscriptional neighbours from the virtual cell (reference drugs whose L1000 responses in "
                     "9 lines at 6 h and 24 h are most similar; similarity is mean cosine):")
        for n, m, s, _ in neighbours:
            lines.append(f"- {n} | {m} | {s:.2f}")
    lines.append("\nVocabulary of mechanism classes with screened reference drugs (number of drugs):")
    lines.append("; ".join(f"{c} ({k})" for c, k in sorted(vocab.items())))
    return "\n".join(lines)


def validate(obj: dict, vocab: dict, offered: list | None, pmids: set) -> tuple[dict, dict]:
    vl = {c.lower(): c for c in vocab}
    dropped = {"unknown_class": 0, "unknown_neighbour": 0, "bad_gene": 0, "foreign_pmid": 0}
    routes = []
    for r in (obj.get("routes") or [])[:4]:
        c = vl.get(str(r.get("class", "")).lower()) if isinstance(r, dict) else None
        if c is None:
            dropped["unknown_class"] += 1
            continue
        try:
            w = min(max(float(r.get("weight", 1.0)), 0.0), 1.0)
        except (TypeError, ValueError):
            w = 1.0
        ps = [str(p) for p in (r.get("pmids") or [])]
        dropped["foreign_pmid"] += sum(p not in pmids for p in ps)
        routes.append({"class": c, "weight": w, "pmids": [p for p in ps if p in pmids]})
    bms = []
    for b in (obj.get("biomarkers") or [])[:4]:
        g = str(b.get("gene", "")).upper().strip() if isinstance(b, dict) else ""
        if not GENE.match(g):
            dropped["bad_gene"] += 1
            continue
        ps = [str(p) for p in (b.get("pmids") or [])]
        dropped["foreign_pmid"] += sum(p not in pmids for p in ps)
        bms.append({"gene": g, "feature": "mutation" if str(b.get("feature", "")).lower().startswith("mut") else "expression",
                    "effect": "protective" if str(b.get("effect", "")).lower().startswith("prot") else "sensitizing",
                    "pmids": [p for p in ps if p in pmids]})
    keep = []
    if offered:
        names = {n.lower(): n for n, _, _, _ in offered}
        for k in obj.get("keep_neighbours") or []:
            n = names.get(str(k).lower())
            if n is None:
                dropped["unknown_neighbour"] += 1
            elif n not in keep:
                keep.append(n)
    return {"cytotoxic_mechanism": str(obj.get("cytotoxic_mechanism", ""))[:400],
            "expected_killing": str(obj.get("expected_killing", "")).lower(),
            "routes": routes, "biomarkers": bms, "keep_neighbours": keep}, dropped


class Agent:
    def __init__(self, world, workers: int = 8, profile: str = "flash"):
        import sys
        sys.path.insert(0, str(ROOT / "src"))
        sys.path.insert(0, str(ROOT))
        from agent.llm import DeepSeekChatClient, MAESTROSettings  # noqa: E402
        from tools.evaluation.costs import SpendLedger  # noqa: E402
        self.world = world
        self.client = DeepSeekChatClient(MAESTROSettings.from_workspace(ROOT))
        self.ledger = SpendLedger.load(LEDGER, ceiling_usd=CEILING_USD, prior_note="block N (mechanism routing) provider spend")
        self.lock = threading.Lock()
        self.workers = workers
        self.profile = profile

    def path(self, arm, regime, drug):
        tag = arm if self.profile == "flash" else f"{arm}@{self.profile}"
        return OUT / tag / regime / f"{slug(drug)}.json"

    def run_one(self, arm: str, regime: str, i: int) -> dict:
        from agent.llm import LLMError  # noqa: E402
        w = self.world
        drug = str(w.drug[i])
        p = self.path(arm, regime, drug)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        vocab = w.vocabulary(i, regime)
        lit = None
        if arm.endswith("_lit"):
            lp = HERE / "literature" / f"{slug(drug)}.json"
            lit = json.loads(lp.read_text(encoding="utf-8")) if lp.exists() else None
        offered = w.neighbours(i, regime) if arm.startswith("adjudicate") else None
        msgs = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": user_message(arm, drug, str(w.moa[i]), w.targets[i], vocab, lit, offered)}]
        label = f"{arm}@{self.profile}:{regime}:{slug(drug)}"
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
        pm = {h["pmid"] for h in (lit or {}).get("hits", [])}
        out, dropped = validate(obj if isinstance(obj, dict) else {}, vocab, offered, pm)
        rec = {"arm": arm, "profile": self.profile, "regime": regime, "drug": drug, "status": status, "error": err,
               "seconds": round(time.time() - t0, 2), "model": resp.model if resp else None,
               "finish_reason": resp.finish_reason if resp else None, "usage": resp.usage if resp else None,
               "offered_neighbours": [[n, m, round(s, 4)] for n, m, s, _ in offered] if offered else None,
               "n_vocabulary": len(vocab), "n_abstracts": len((lit or {}).get("hits", [])),
               "dropped": dropped, "claims": out, "raw": obj,
               "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".part")
        tmp.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        tmp.replace(p)
        return rec

    def run(self, tasks: list[tuple[str, str, int]]) -> list[dict]:
        with ThreadPoolExecutor(self.workers) as pool:
            return list(pool.map(lambda t: self.run_one(*t), tasks))
