"""Development evaluation, conventional search and agent search over acquisition-value programs.

File summary
- Path: research/acquisition_program_20261018/ap_search.py
- Purpose: the only editable scientific object is the acquisition-value program: an expression over the lookahead
  features (`ap_task.FEATURES`) whose argmax over the non-target candidate pools picks each compound's second pool.
  Everything else (backend, scoring, nomination, budget, target set) is immutable.
- Development objective: total nominated target events summed over the development cells (2 folds x 2 target groups
  x 5 paired noise scenarios = 20 cells; the same keyed noise for every policy, the same training support).
- Acceptance rule (identical for both searches): a candidate replaces the incumbent only if its development total
  exceeds the incumbent's AND it wins more cells than it loses. Otherwise the incumbent is retained and the cycle
  continues; every proposal, valid or not, consumes one of the 12 allocated proposals.
- Searches (start incumbent = the handwritten one-step lookahead `la`):
  - conventional: 12 random linear combinations of standardised features (fixed seed), greedy acceptance;
  - agent: 12 proposals by `deepseek-flash` through the existing client, each with a falsifiable decision hypothesis, an
    expected nomination change (share of compounds changing pool, direction of hits) stated BEFORE evaluation, and the
    observed result recorded. The agent sees aggregated development results only; virtual-cell/posterior simulations
    are inputs to features (planning), never to grading.
- Interfaces: `Dev`, `conventional_search`, `agent_search`, `write_trace`.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ap_build as B  # noqa: E402
import ap_task as A  # noqa: E402

BUDGET = 12
START = "la"
FEATURE_HELP = {
    "la": "expected terminal nomination utility (sum of posterior-sampled event estimates of the 3 lines the ridge scoring rule would nominate) after reading the candidate pool; unvalidated model probability",
    "ev0": "the same quantity before reading any further pool (constant over a compound's candidates)",
    "gain": "la - ev0, expected utility gain of the one-step lookahead",
    "vr": "posterior variance reduction summed over the target lines",
    "vr_rel": "vr divided by the current total target variance",
    "shift": "expected absolute shift of the posterior mean on target lines",
    "flip": "probability that the nominated top-3 set changes after reading the pool",
    "rank": "position of the pool in the fixed A-optimal order (0 = the fixed policy's choice)",
    "n_lines": "number of lines in the pool",
    "obs_min": "most negative log2 fold change seen so far for this compound (constant over candidates)",
}


class Dev:
    """Cached development cells; `result(expr)` evaluates a program on all cells."""

    def __init__(self):
        self.data = B.load_all("dev")
        self.cache = {}

    def result(self, expr):
        key = expr or "<fixed>"
        if key not in self.cache:
            cells = []
            for task, scs in self.data:
                ev = A.eval_program(task, scs, expr)["per_scenario"]
                cells += [{"task": task.name, "salt": sc["salt"], "hits": r["hits"], "changed": r["changed_share"], "hits_c": r["hits_c"]}
                          for sc, r in zip(scs, ev)]
            self.cache[key] = cells
        return self.cache[key]

    def diff_share(self, a: str, b: str) -> float:
        """Share of (compound, scenario) decisions that differ between two programs."""

        ra, rb = A.compile_program(a), A.compile_program(b)
        diff = n = 0
        for task, scs in self.data:
            for sc in scs:
                ca, cb = A.choose(sc["features"], ra), A.choose(sc["features"], rb)
                diff += int((ca != cb).sum())
                n += len(ca)
        return diff / n

    @staticmethod
    def summary(cells, base=None):
        tot = int(sum(c["hits"] for c in cells))
        out = {"total_hits": tot, "mean_changed_share": float(np.mean([c["changed"] for c in cells])),
               "per_task": {t: int(sum(c["hits"] for c in cells if c["task"] == t)) for t in sorted({c["task"] for c in cells})}}
        if base is not None:
            d = np.array([a["hits"] - b["hits"] for a, b in zip(cells, base)])
            out.update({"delta_total": int(d.sum()), "cells_better": int((d > 0).sum()), "cells_worse": int((d < 0).sum())})
        return out


def accepts(summary: dict) -> bool:
    return summary["delta_total"] > 0 and summary["cells_better"] > summary["cells_worse"]


def conventional_search(dev: Dev, seed: int = 20261018) -> dict:
    rng = np.random.default_rng(seed)
    names = ["la", "gain", "vr_rel", "shift", "flip"]
    inc_expr, inc_cells = START, dev.result(START)
    trace = []
    for k in range(BUDGET):
        w = np.round(rng.uniform(-1, 1, len(names)), 2)
        expr = " + ".join(f"{float(wi)}*zs({n})" for wi, n in zip(w, names))
        cells = dev.result(expr)
        s = dev.summary(cells, inc_cells)
        ok = accepts(s)
        trace.append({"proposal": k + 1, "source": "conventional_random_linear", "expression": expr, "observed": s, "accepted": bool(ok),
                      "incumbent_after": expr if ok else inc_expr})
        if ok:
            inc_expr, inc_cells = expr, cells
    return {"incumbent": inc_expr, "trace": trace}


SYSTEM = ("You are the scientific agent of MAESTRO proposing edits to ONE object: the acquisition-value program of a screening "
          "campaign. You may not change the backend, scoring, nomination rules, budget or target set. Return exactly one JSON object.")


def _prompt(incumbent: str, inc_summary: dict, trace: list, k: int) -> str:
    hist = [{"proposal": t["proposal"], "expression": t["expression"], "hypothesis": t.get("hypothesis"), "expected": t.get("expected"),
             "observed": t["observed"], "accepted": t["accepted"], "error": t.get("error")} for t in trace]
    return json.dumps({
        "task": "Each compound has a fixed seed pool read. You choose its SECOND pool among the candidate pools outside a predeclared "
                "target set of whole pools (a third pool is then bought by a fixed policy). Then a ridge model scores the target lines, "
                "campaign-level nomination picks 32 pairs per 64 compounds (max 3 per compound) and true selective events are counted. "
                "Higher total events is better. Probes never reveal target entries.",
        "program": "value = expression over feature names evaluated per compound (rows) and candidate pool (columns); the pool with the largest value is "
                   "read; ties go to the lowest rank. Allowed: + - * / unary minus, comparisons, numeric constants, abs sqrt log1p exp tanh minimum "
                   "maximum where, zs(x) (row-wise z-score across candidates), rk(x) (row-wise rank). No power operator. Max 400 characters.",
        "features": FEATURE_HELP,
        "notes": ["Model probabilities in la/gain/flip are unvalidated estimates from posterior sampling.",
                  "The handwritten baseline is value = la. The fixed policy corresponds to value = -rank.",
                  "Development totals are sums over 20 paired cells (2 folds x 2 target groups x 5 noise scenarios); noise draws are not extra biological samples."],
        "incumbent": {"expression": incumbent, "development": inc_summary},
        "history": hist, "proposal_number": k, "of": BUDGET,
        "respond_with": {"hypothesis": "one falsifiable sentence about WHY this value ordering should nominate more events",
                         "expected_nomination_changes": {"share_of_compounds_choosing_a_different_pool_than_incumbent": "number 0-1",
                                                         "direction_of_total_events_vs_incumbent": "up|down|flat",
                                                         "which_compounds_change": "short text"},
                         "expression": "program"}}, indent=1)


def agent_search(dev: Dev, client, log=print) -> dict:
    inc_expr, inc_cells = START, dev.result(START)
    base = dev.summary(inc_cells)
    trace = []
    for k in range(1, BUDGET + 1):
        msg = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": _prompt(inc_expr, base, trace, k)}]
        rec = {"proposal": k, "source": "agent_deepseek_flash"}
        try:
            obj, resp = client.complete_json(msg, max_tokens=1500)
            expr = str(obj.get("expression", "")).strip()
            rec.update({"hypothesis": obj.get("hypothesis"), "expected": obj.get("expected_nomination_changes"), "expression": expr})
            A.compile_program(expr)
            cells = dev.result(expr)
            s = dev.summary(cells, inc_cells)
            s["share_changed_vs_incumbent"] = dev.diff_share(expr, inc_expr)
            ok = accepts(s)
            rec.update({"observed": s, "accepted": bool(ok), "incumbent_after": expr if ok else inc_expr})
            if ok:
                inc_expr, inc_cells, base = expr, cells, dev.summary(cells)
        except Exception as e:  # noqa: BLE001 - a failed proposal consumes budget and keeps the incumbent
            rec.update({"expression": rec.get("expression", ""), "observed": {"total_hits": None}, "accepted": False, "error": f"{type(e).__name__}: {str(e)[:200]}",
                        "incumbent_after": inc_expr})
        trace.append(rec)
        log(k, rec.get("expression"), rec.get("observed", {}).get("delta_total"), rec["accepted"], rec.get("error", ""))
    return {"incumbent": inc_expr, "trace": trace}


def write_trace(path: Path, obj: dict) -> None:
    path.write_bytes((json.dumps(obj, indent=1, default=lambda x: x.tolist() if hasattr(x, "tolist") else str(x)) + "\n").encode("utf-8"))


def choice_overlap(dev: Dev, expr_a: str, expr_b: str) -> float:
    """Share of compounds choosing the same pool under two programs (decision-level diagnostic)."""

    same, n = 0, 0
    ra, rb = A.compile_program(expr_a), A.compile_program(expr_b)
    for task, scs in dev.data:
        for sc in scs[:1]:
            ca, cb = A.choose(sc["features"], ra), A.choose(sc["features"], rb)
            same += int((ca == cb).sum())
            n += len(ca)
    return same / n


def make_client():
    sys.path.insert(0, str(HERE.parents[1] / "src"))
    from agent.llm import DeepSeekChatClient, MAESTROSettings

    return DeepSeekChatClient(MAESTROSettings.from_workspace(HERE.parents[1]))
