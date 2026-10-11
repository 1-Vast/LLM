"""Conventional LLM agent + virtual-cell tool (arm CONV), and its feedback-permutation twin.

This is the common agent-world-model integration (ReAct-style tool use, as in BioDiscoveryAgent).
Each round the LLM (deepseek-flash, thinking off) sees:
* the campaign goal and budget left;
* every compound screened so far, with its measured lineage selectivity and hit status;
* a shortlist of SHORTLIST unscreened compounds ranked by the virtual cell's tool output (a stack
  of the two transcriptional sources, refit on the known set), each with its name, annotated
  mechanism, the tool's P(hit), predicted selectivity, and its three nearest screened
  transcriptional neighbours with their measured selectivity.

It must return exactly ``k`` shortlist ids.
* An invalid or failed reply is refused by name (``LLM_INVALID_SELECTION`` or
  ``LLM_CALL_FAILED``) and filled from the tool's ranking; the count of filled picks is reported.
* The permutation twin shows the LLM permuted outcomes (within each revealed batch) for both history
  and neighbours, and the tool is refit on the permuted profiles too. Scoring uses the truth.
"""
from __future__ import annotations

import json
import re
import sys
import threading
import time
from pathlib import Path

import numpy as np

import campaign as CA
import world as WM

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LEDGER = ROOT / "tmp/selective_discovery_spend.json"
CEILING_USD = 10.0
SHORTLIST = 24

SYSTEM = """You direct a phenotypic screening campaign. Goal: find as many compounds as possible that
SELECTIVELY kill one target tumour lineage in a 5-day, 2.5 micromolar pooled viability screen of
about 578 cancer cell lines. A compound is a hit when its mean log2 fold change in the target
lineage is at least 0.5 below its mean over all other lines AND its target-lineage mean is -0.5 or
lower. Each screen of one compound reveals its full profile and costs one unit of budget.

A virtual-cell tool ranks unscreened compounds by transferring measured profiles from compounds with
similar L1000 transcriptional responses; its neighbours may belong to other mechanism classes. Use
the tool, the measured results so far, and your pharmacological knowledge to choose the next batch.

Return one JSON object: {"reasoning": at most three sentences, "picks": [list of exactly K ids]}
where ids are the integers shown in the shortlist."""


def fmt(x):
    return "na" if x is None or not np.isfinite(x) else f"{x:+.2f}"


class ConvAgent:
    def __init__(self, U, names, out_dir: Path, workers_lock=None):
        sys.path.insert(0, str(ROOT / "src"))
        sys.path.insert(0, str(ROOT))
        from agent.llm import DeepSeekChatClient, MAESTROSettings  # noqa: E402
        from tools.evaluation.costs import SpendLedger  # noqa: E402
        self.U = U
        self.names = names
        self.client = DeepSeekChatClient(MAESTROSettings.from_workspace(ROOT))
        self.ledger = SpendLedger.load(LEDGER, ceiling_usd=CEILING_USD, prior_note="block P (selective discovery) provider spend")
        self.lock = workers_lock or threading.Lock()
        self.out_dir = out_dir

    def message(self, st: CA.State, cand, p, sel_pred, k):
        U, t = self.U, st.t
        T = U.lineages[t]
        s_known, _ = U.selectivity(st.Y)
        nref = len(st.ref)
        hist = []
        for j, (_, c) in enumerate(st.screened):
            s = s_known[nref + j, t]
            hit = bool((s <= WM.HIT_S) and (U.selectivity(st.Y[nref + j][None])[1][0, t] <= WM.HIT_M))
            hist.append(f"- {self.names[c]} [{U.moa[c]}]: selectivity {fmt(s)}{' HIT' if hit else ''}")
        known = np.array(st.known)
        S = U.sims["vc_native"][np.ix_(cand, known)]
        lines = []
        for i, c in enumerate(cand):
            row = S[i]
            ok = np.isfinite(row)
            nb = []
            if ok.any():
                for j in np.argsort(-np.where(ok, row, -np.inf))[:3]:
                    if np.isfinite(row[j]):
                        nb.append(f"{self.names[known[j]]} (sim {row[j]:.2f}, sel {fmt(s_known[j, t])})")
            lines.append(f"{i}: {self.names[c]} [{U.moa[c]}] tool P(hit) {p[i]:.3f}, predicted selectivity "
                         f"{fmt(sel_pred[i])}; neighbours: {'; '.join(nb) or 'none'}")
        return (f"Target lineage: {T}\nBudget left: {st.budget - st.n_screened} screens. Choose K = {k}.\n\n"
                f"Screened so far ({len(hist)}):\n" + ("\n".join(hist) or "(none)") +
                "\n\nShortlist (id: compound [mechanism] ...):\n" + "\n".join(lines))

    def choose(self, st: CA.State, cand, p, sel_pred, k, label):
        from agent.llm import LLMError  # noqa: E402
        msgs = [{"role": "system", "content": SYSTEM.replace("exactly K", f"exactly {k}")},
                {"role": "user", "content": self.message(st, cand, p, sel_pred, k)}]
        with self.lock:
            self.ledger.reserve(label, 0.02)
        t0 = time.time()
        try:
            obj, resp = self.client.complete_json(msgs, max_tokens=2500)
            status, err = "ok", None
        except LLMError as error:
            obj, resp, status, err = {}, None, "failed", f"{type(error).__name__}:{str(error)[:120]}"
        with self.lock:
            self.ledger.charge(label, resp.usage if resp else None, status=status if resp else "failed_unpriced",
                               reserved_usd=0.02, note=err or "")
            self.ledger.write()
        raw = obj.get("picks", []) if isinstance(obj, dict) else []
        ids = []
        for v in raw if isinstance(raw, list) else []:
            try:
                v = int(v)
            except (TypeError, ValueError):
                continue
            if 0 <= v < len(cand) and v not in ids:
                ids.append(v)
        reason = None
        if status != "ok":
            reason = "LLM_CALL_FAILED"
        elif len(ids) != k:
            reason = "LLM_INVALID_SELECTION"
        valid = ids[:k]
        filled = 0
        if len(valid) < k:
            for i in np.argsort(-p):
                if int(i) not in valid:
                    valid.append(int(i))
                    filled += 1
                if len(valid) == k:
                    break
        rec = {"label": label, "status": status, "error": err, "reason_code": reason, "returned": raw, "filled": filled,
               "seconds": round(time.time() - t0, 2), "usage": resp.usage if resp else None,
               "reasoning": obj.get("reasoning") if isinstance(obj, dict) else None,
               "prompt": msgs[1]["content"]}
        return [int(cand[i]) for i in valid], rec

    def run(self, st: CA.State, rng, permute_rng=None, tag="conv"):
        U = self.U
        log = []
        while st.n_screened < st.budget:
            tool = WM.Stack(U, WM.VC_SOURCES).fit(np.array(st.known), Y=st.Y)
            cand_all = np.array(st.left)
            p_all = tool.score(np.array(st.known), cand_all, Y=st.Y)[:, st.t]
            order = np.argsort(-(p_all + 1e-12 * rng.standard_normal(len(cand_all))))[:SHORTLIST]
            cand, p = cand_all[order], p_all[order]
            preds = tool.source_preds(np.array(st.known), cand, loo=False, Y=st.Y)["vc_native"][0][:, st.t]
            k = min(st.batch, st.budget - st.n_screened)
            picks, rec = self.choose(st, cand, p, preds, k, f"{tag}:{U.lineages[st.t]}:r{st.round}")
            pos = {c: i for i, c in enumerate(cand)}
            st.predictions += [(c, float(p[pos[c]])) for c in picks]
            if rec["reason_code"]:
                st.refusals.append({"round": st.round, "code": rec["reason_code"], "filled": rec["filled"]})
            log.append(rec)
            st.reveal(U, picks, permute_rng)
        return st, log
