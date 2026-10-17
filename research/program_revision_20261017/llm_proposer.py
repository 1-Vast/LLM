"""LLM proposer for program-library edits (deepseek-flash), with a digest-keyed spend ledger.

File summary
- Path: research/program_revision_20261017/llm_proposer.py
- Purpose: the evaluated agent's reasoning component. It reads the same diagnosis packet as the
  enumerative proposer and returns at most ``n`` edits in the restricted program language.
- Boundaries:
  - The model never sees an outcome of a development query line, a fitted coefficient's value
    beyond its sign, or any held-out project. It cannot set a number: loadings are fitted.
  - It must state a direction (sensitising/protective) and an applicability condition for each
    add edit; the direction is checked against the fitted loading after the experiment.
  - Malformed output is refused by name (`llm_protocol_error`, `llm_transport_error`,
    `llm_budget_exhausted`) and that step proceeds with zero LLM edits.
  - Every request/response is cached by prompt digest in a JSONL ledger with token usage, so a
    rerun makes no new calls and the spend is auditable. Spend cap: USD 1.00 for this study.
- Interfaces: `LLMProposer(ledger_path, offline=False, n=6).propose(diagnosis, lib, bench)`.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

from revise import Edit
from engine import legal_atoms

ROOT = Path(__file__).resolve().parents[2]
RATE_IN, RATE_OUT = 0.30, 1.20  # USD per million tokens (provider contract, cache-miss input)
SPEND_CAP = 1.00

SYSTEM = (
    "You are the program-revision component of MAESTRO, an autonomous drug-discovery research agent. "
    "A strong statistical response model predicts cancer-cell-line viability (log2 fold change, 2.5 uM, "
    "PRISM) for drugs on new cell lines. On top of it sits a small library of executable response "
    "programs. Each program says: drugs in SCOPE (a mechanism-of-action or target token) have an extra "
    "response that scales with a STATE of the cell line computed from legal measurements. The goal of the "
    "library is to nominate more context-specific strong responders on future, unseen cell lines. "
    "You propose edits. Each edit is then fitted on source data (you never set numbers) and tested by a "
    "distinguishing experiment on held-out development lines whose outcomes you have not seen; it is kept "
    "only if it predicts those outcomes better AND changes nominations for the better. Edits that do not "
    "change predictions earn nothing. Prefer biologically motivated conditional programs; you may propose "
    "states that are not in the residual list. Never invent measurements outside the legal atoms."
)

GRAMMAR = (
    "ops: add(scope,state) | retire(key) | split(key,gate) | replace_state(key,state) | narrow(key,scope). "
    "state: atom | and(A,B) | andnot(A,B) | mul(C,G) with at most 3 atoms; and/andnot need binary atoms, "
    "mul multiplies a continuous atom C by a binary gate G. atoms: mut:GENE (binary, DNA panel), "
    "lin:TISSUE (binary, free), probe:CORE (continuous: the line's measured response to that probe drug; "
    "more negative = more sensitive), b (continuous: inferred overall sensitivity offset of the line; "
    "more negative = more sensitive), expr:GENE (continuous, only if legal). scope: moa:TOKEN | target:GENE. "
    "direction: 'sensitising' = drugs in scope respond MORE (lower viability) where the state is high; "
    "'protective' = they respond LESS."
)

GRAMMAR_JOINT = (
    " Joint mode adds one op: measure(key=DESIGN_PROBE_TO_DROP, gate=NEW_PROBE_CORE, scope, state). It swaps one "
    "probe of the fixed 8-well design for an unmeasured source drug from measurement_candidates (or any listed core) "
    "and, if scope/state are given, adds the program that reads it (state may use probe:NEW_PROBE_CORE). Each "
    "measurement edit is charged one extra well on every development line. A design probe used by a program "
    "cannot be dropped."
)


def _provider():
    name = "maestro_src_agent_llm"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ROOT / "src" / "agent" / "llm.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


class LLMProposer:
    name = "llm"

    def __init__(self, ledger_path, offline: bool = False, n: int = 6, max_tokens: int = 1800, joint: bool = False):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache = {}
        if self.ledger_path.exists():
            for line in self.ledger_path.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                self.cache[row["digest"]] = row
        self.offline, self.n, self.max_tokens, self.joint = offline, n, max_tokens, joint
        self.client = None
        self.history = []  # (edit label, decision, reason) fed back as prior evidence
        if not offline:
            llm = _provider()
            self.client = llm.DeepSeekChatClient(llm.MAESTROSettings.from_workspace(ROOT))

    def spend(self) -> dict:
        rows = list(self.cache.values())
        pin = sum(r.get("usage", {}).get("prompt_tokens", 0) for r in rows)
        pout = sum(r.get("usage", {}).get("completion_tokens", 0) for r in rows)
        return {"calls": len(rows), "prompt_tokens": pin, "completion_tokens": pout,
                "usd_upper_bound": round(pin * RATE_IN / 1e6 + pout * RATE_OUT / 1e6, 6)}

    def packet(self, diagnosis, lib, bench):
        dom = bench.dom
        legal = sorted(legal_atoms(bench.info))
        f = bench.query[bench.projects[0]]
        ctx_tr, _ = f.contexts()
        tmp = lib.copy()
        signs = {}
        if tmp.programs:
            tmp.fit(f.R_train, tmp.states(ctx_tr), dom.df, f.drows)
            signs = {p.key: ("sensitising" if b < 0 else "protective") for p, b in zip(tmp.programs, tmp.beta)}
        from revise import candidate_scopes
        scopes = [s for s, _ in candidate_scopes(bench)]
        probes = {c: f"{dom.drugs.name[dom.drug_index[c]]} ({dom.drugs.moa[dom.drug_index[c]]})" for c in f.probe_cores}
        extra = {}
        if self.joint:
            extra = {"measurement_candidates": diagnosis.get("measurement_candidates", []),
                     "design_probes_droppable": [c for c in bench.probes if not any(c in p.state for p in lib.programs)]}
        return {
            **extra,
            "legal_atom_kinds": legal,
            "panel_genes": list(map(str, dom.lf["panel_genes"])),
            "source_lineages": sorted(set(dom.lines.primary_tissue[dom.src_line])),
            "probe_drugs": probes,
            "allowed_scopes": scopes,
            "library": [{"key": p.key, "origin": p.origin, "fitted_direction": signs.get(p.key, "")} for p in lib.programs],
            "current_project": diagnosis["project"],
            "residual_clusters": [{k: c[k] for k in ("scope", "state", "t_project", "t_all_support", "residual_direction")}
                                  for c in diagnosis["clusters"][:20]],
            "previous_tests": self.history[-24:],
            "max_edits": self.n,
            "grammar": GRAMMAR + (GRAMMAR_JOINT if self.joint else ""),
            "reply_format": {"edits": [{"op": "add", "scope": "moa:...", "state": "...", "key": "", "gate": "",
                                        "direction": "sensitising|protective",
                                        "applicability": "which lines it applies to and how that is measured",
                                        "distinguishing_prediction": "what the held-out lines should show",
                                        "rationale": "short biological reason"}]},
        }

    def propose(self, diagnosis, lib, bench):
        user = json.dumps(self.packet(diagnosis, lib, bench), sort_keys=True)
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]
        digest = hashlib.sha256(json.dumps(messages, sort_keys=True).encode()).hexdigest()
        meta = {"digest": digest[:16]}
        row = self.cache.get(digest)
        if row is None:
            if self.offline:
                meta["refusal"] = "llm_offline_cache_miss"
                return [], meta
            if self.spend()["usd_upper_bound"] >= SPEND_CAP:
                meta["refusal"] = "llm_budget_exhausted"
                return [], meta
            try:
                obj, resp = self.client.complete_json(messages, max_tokens=self.max_tokens)
                row = {"digest": digest, "response": obj, "usage": resp.usage, "finish": resp.finish_reason}
            except Exception as e:  # noqa: BLE001 - recorded and refused by name
                code = getattr(e, "code", type(e).__name__)
                row = {"digest": digest, "error": f"{type(e).__name__}:{code}", "usage": {}}
            self.cache[digest] = row
            with self.ledger_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
        if "error" in row:
            meta["refusal"] = "llm_protocol_error" if "Protocol" in row["error"] else "llm_transport_error"
            return [], meta
        edits = []
        raw = row["response"].get("edits", []) if isinstance(row["response"], dict) else []
        if not self.joint:
            raw = [e for e in raw if not (isinstance(e, dict) and str(e.get("op", "")).strip() == "measure")]
        for e in raw[: self.n]:
            if not isinstance(e, dict):
                continue
            edits.append(Edit(op=str(e.get("op", "")).strip(), scope=str(e.get("scope", "")).strip(),
                              state=str(e.get("state", "")).replace(" ", ""), key=str(e.get("key", "")).strip(),
                              gate=str(e.get("gate", "")).replace(" ", ""), origin=self.name,
                              rationale=(str(e.get("rationale", "")) + " | applies: " + str(e.get("applicability", ""))
                                         + " | predicts: " + str(e.get("distinguishing_prediction", "")))[:600],
                              direction=str(e.get("direction", "")).strip().lower()))
        meta["n_raw"] = len(raw)
        return edits, meta

    def feedback(self, recs):
        for r in recs:
            self.history.append({"edit": r.get("edit"), "decision": r.get("decision"), "reason": r.get("reason", ""),
                                 "hits_gain": (r.get("hits_new_only", 0) - r.get("hits_cur_only", 0)) if "llr" in r else None})
