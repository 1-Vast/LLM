"""Optional secondary arm (added after the freeze; the deterministic experiment never depends on it): an LLM proposes one typed gate program per generation.

Visible to the model: opaque class ids, numeric class-level unexplained variation and correlations, the incumbent gate scopes, the grammar. No drug, cell or dataset names,
no outcomes of unqueried pairs. The reply is validated against the grammar locally; invalid or absent replies yield no candidate (no repair loop). A proposal becomes a
candidate in the SAME lifecycle (same fit, same validation replay, same promotion rule) as every other candidate. Limits: <= 6 HTTP attempts, <= 30 000 tokens in total.
Credentials are read by the maintained client and never persisted; no monetary figure is asserted.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "self_improving_virtual_cell_20261020"))
import iv_core as C  # noqa: E402
import iv_gates as G  # noqa: E402
import iv_search as S  # noqa: E402
import iv_worlds as W  # noqa: E402
from svc_llm import AttemptCounter  # noqa: E402

MAX_ATTEMPTS, MAX_TOKENS, MAX_OUT = 6, 30000, 1500
SYSTEM = ("You propose hidden-state ('gate') hypotheses for combination-response residuals in a new cell background. A gate is a binary hidden state that shifts the "
          "residual of every drug pair in its scope classes by a same-signed amount. You see opaque class ids with numeric evidence. Propose up to 2 NEW gates "
          "(scope: 1-3 class ids, signs: +1/-1 per class, same sign means the classes rise together) that you expect to explain unexplained cell-to-cell variation, "
          "or answer {\"decision\":\"none\"}. Return one JSON object: decision ('propose' or 'none'), gates (list of {scope:[ids], signs:[+-1,...]}), cited (evidence ids, at most 6), "
          "rationale (at most 50 words). Explanations are not measurements; nothing is accepted without held-out validation.")


class Proposer:
    def __init__(self, n_cls, seed):
        order = np.random.default_rng(int.from_bytes(hashlib.sha256(f"opaque|{seed}".encode()).digest()[:8], "little")).permutation(n_cls)
        self.to_class = {f"K{k}": int(order[k]) for k in range(n_cls)}
        self.to_opaque = {v: k for k, v in self.to_class.items()}
        self.receipts, self.tokens, self.attempts = [], 0, 0
        self.client = self.llm = None
        self.err = None
        try:
            sys.path.insert(0, str(ROOT / "src"))
            from agent import llm
            self.llm, self.client = llm, llm.DeepSeekChatClient(llm.MAESTROSettings.from_workspace(ROOT))
        except Exception as e:                                                   # configuration failure must not block anything
            self.err = type(e).__name__

    def propose(self, Mpre, lib, gen):
        rec = {"gen": gen, "outcome": "NOT_RUN", "http_attempts": 0, "accepted_for_testing": False}
        self.receipts.append(rec)
        if self.client is None:
            rec["outcome"], rec["error"] = "API_FAILURE", f"configuration: {self.err}"
            return []
        cm = C.class_matrix(Mpre)
        var = cm.var(1)
        top = [int(c) for c in np.argsort(-var)[:6]]
        corr = np.corrcoef(cm[top]) if len(top) > 1 else np.ones((1, 1))
        ev = [{"ev": f"E{i + 1}", "class_id": self.to_opaque[c], "cell_to_cell_variance": round(float(var[c]), 6)} for i, c in enumerate(top)]
        ev.append({"ev": "E7", "correlation_among_top_classes": {f"{self.to_opaque[a]}~{self.to_opaque[b]}": round(float(corr[i, j]), 2) for i, a in enumerate(top) for j, b in enumerate(top) if j > i}})
        inc = [] if lib.deployed is None else [[self.to_opaque[c] for c in lib.gates[g].scope] for g in lib.deployed.gates]
        payload = {"n_released_cells": len(Mpre.cells), "incumbent_gate_scopes": inc, "evidence": ev}
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": "Visible evidence (JSON):\n" + json.dumps(payload, sort_keys=True)}]
        full = json.dumps(messages)
        rec["prompt_sha256"], rec["evidence_logged"] = hashlib.sha256(full.encode()).hexdigest(), payload
        est = int(len(full) / 2.5) + 1 + MAX_OUT
        if self.tokens + est > MAX_TOKENS or self.attempts >= MAX_ATTEMPTS:
            rec["outcome"], rec["error"] = "BUDGET_REFUSED", f"estimated {est} tokens would exceed the cap"
            return []
        t0 = time.time()
        with AttemptCounter(self.llm, MAX_ATTEMPTS, self.attempts) as counter:
            try:
                result, resp = self.client.complete_json(messages, max_tokens=MAX_OUT)
            except Exception as e:
                rec["outcome"], rec["error"] = "API_FAILURE", f"{type(e).__name__}: {str(e)[:200]}"
                rec["http_attempts"], self.attempts = counter.count - self.attempts, counter.count
                return []
            rec["http_attempts"], self.attempts = counter.count - self.attempts, counter.count
        rec["latency_seconds"] = round(time.time() - t0, 2)
        usage = dict(getattr(resp, "usage", {}) or {})
        rec["usage"] = usage
        self.tokens += int(usage.get("total_tokens") or est)
        rec["response"] = json.dumps(result, sort_keys=True)[:2500]
        if not isinstance(result, dict) or result.get("decision") not in ("propose", "none"):
            rec["outcome"], rec["error"] = "INVALID_RESPONSE", "decision must be propose or none"
            return []
        if result["decision"] == "none":
            rec["outcome"] = "VALID_NO_PROGRAM"
            return []
        gates = []
        try:
            for g in result.get("gates", [])[:2]:
                ids, signs = g["scope"], g["signs"]
                if not (1 <= len(ids) <= 3 and len(ids) == len(signs) and all(i in self.to_class for i in ids) and all(s in (-1, 1) for s in signs)):
                    raise ValueError("gate outside the grammar")
                b = np.zeros(len(self.to_class))
                for i, s in zip(ids, signs):
                    b[self.to_class[i]] = 0.1 * s
                b, _ = G.canonical(b, np.zeros(1))
                gt = G.Gate("api", b, scope=G.scope_of(b), gen=gen, parents=("llm",))
                gt.gid = f"api{gen}_{gt.identity()[:6]}"
                gates.append(gt)
        except (KeyError, ValueError, TypeError) as e:
            rec["outcome"], rec["error"] = "INVALID_PROGRAM", str(e)[:200]
            return []
        if not gates:
            rec["outcome"] = "VALID_NO_PROGRAM"
            return []
        rec["outcome"], rec["accepted_for_testing"] = "VALID_PROGRAM", True
        return gates

    def ledger(self):
        return {"model_requests": len(self.receipts), "http_attempts": self.attempts, "cumulative_tokens": self.tokens,
                "limits": {"max_http_attempts": MAX_ATTEMPTS, "max_total_tokens": MAX_TOKENS, "max_output_tokens": MAX_OUT},
                "money": "unverified: provider prices were not verified, so no monetary figure is asserted", "no_credentials_or_headers_persisted": True, "receipts": self.receipts}


def run(kind="alias", seed=9001, budget=4):
    s = W.make_stream(kind, seed)
    w, sc, st = s["world"], s["schedule"], s["world"].static
    prop = Proposer(len(st.classes), seed)
    lib = S.Library()
    rel = list(sc["H0"])
    orig = S.propose
    rows, gens = [], []
    for b in range(1, 5):
        batch = sc["batches"][b - 1]
        Mrel = C.build_models(w, rel, st)
        fits = S.make_fits(lib, Mrel, lib.deployed, lib.gates, lib.rank)
        for cell in batch:
            r = S.run_task(w, st, cell, Mrel, fits, lib.policy, budget, "E", None, S.seed_of("task", f"{kind}_{seed}", cell))[0]
            rows.append({"gen": b, "cell": cell, "utility": r["utility"], "oracle": r["oracle"]})
        Mpre_cells = list(rel)

        def hooked(arm, lib_, Mpre, gen, tag, n_max, _orig=orig):
            gl = prop.propose(Mpre, lib_, gen)
            extra = []
            if gl:
                store = dict(lib_.gates)
                for g in gl:
                    store[g.gid] = g
                inc = tuple(lib_.deployed.gates) if lib_.deployed is not None else ()
                ids = (inc + tuple(g.gid for g in gl))[:S.DEPLOY_MAX_GATES]
                extra.append((S._prog(ids, gen, ("llm",), (), "api"), store))
            return (extra + _orig(arm, lib_, Mpre, gen, tag, n_max))[:n_max]
        S.propose = hooked
        try:
            rec = S.evolve("inherit", lib, w, st, f"api|{kind}_{seed}", b, Mpre_cells, batch, Mpre_cells + batch, budget, False, S.CAND_PER_GEN)
        finally:
            S.propose = orig
        gens.append({"gen": b, "deployed_after": rec["deployed_after"], "candidates": [{k: c.get(k) for k in ("pid", "status", "gain", "wins", "losses", "parents")} for c in rec["candidates"] if c.get("fit")]})
        rel = rel + batch
    return {"condition": {"kind": kind, "seed": seed, "label": "dev stream, secondary descriptive arm", "budget": budget}, "ledger": prop.ledger(), "rows": rows, "generation_records": gens}


if __name__ == "__main__":
    out = run()
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps({k: out["ledger"][k] for k in ("model_requests", "http_attempts", "cumulative_tokens")}), [r["outcome"] for r in out["ledger"]["receipts"]])
