"""LLM-driven arms for block M (configurations C1, C3, agent-chosen design, and revision).

* ``agent``      (C1) the agent alone: it reads the observations as top up/down landmark genes,
                 chooses each next observation from the menu, and states the mechanisms it has not
                 ruled out. No world model, no calibration.
* ``interface``  (C3) the same, plus the world model's conformal p-values for the 30 most
                 plausible hypotheses after each observation (a conventional "tool output" link).
* ``design``     the agent only chooses the next observation; the calibrated falsifier decides
                 which hypotheses survive (agent-chosen design for H3).
* ``revise``     after HYPOTHESIS_SET_EXHAUSTED, the agent proposes up to five mechanisms from the
                 vocabulary that are not yet rejected, given the observations.

The agent never sees the drug's name or class. Every call is priced in the block's spend ledger.
Unknown option or class names in a reply are dropped and counted, never guessed.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

import numpy as np

import emh as E

HERE = Path(__file__).resolve().parent

SYSTEM_AGENT = """You are a scientific agent identifying the mechanism of action of an unknown compound.
The compound was applied at 10 micromolar to human cell lines; mRNA of 978 landmark genes was
measured 6 h or 24 h later as signed z-scores against vehicle. You see each observation you bought
as its most up- and down-regulated genes and its overall strength (L2 norm of the 978 z-scores;
{noise_hint}).

Candidate mechanisms (the true one is one of these):
{vocab}

At every step, return one JSON object:
{{"next_option": one option from the menu (or null if no budget remains),
  "plausible": the mechanisms that the observations so far do NOT rule out,
  "ruled_out": the mechanisms that the observations so far DO rule out,
  "reasoning": one or two sentences}}
Fill exactly one of "plausible" and "ruled_out" (whichever list is shorter) and set the other to
null; with "ruled_out", every mechanism not listed counts as plausible. The plausible set should
contain the true mechanism at least 90% of the time. Before any observation, use "ruled_out": []
(nothing is ruled out yet)."""


def summarise(z_gene: np.ndarray, genes: list[str], k: int = 15) -> dict:
    order = np.argsort(z_gene)
    return {"up": [genes[i] for i in order[::-1][:k]], "down": [genes[i] for i in order[:k]],
            "strength": round(float(np.linalg.norm(z_gene)), 1)}


class AgentArms:
    def __init__(self, vocab: list[str], genes: list[str], options: list[str], noise_hint: str):
        self.vocab = vocab
        self.vset = set(vocab)
        self.genes = genes
        self.options = options
        self.client = E.DeepSeekChatClient(E.MAESTROSettings.from_workspace(E.ROOT))
        self.ledger = E.SpendLedger.load(E.LEDGER, ceiling_usd=E.CEILING_USD, prior_note="block M (mechanism falsification) provider spend")
        self.lock = threading.Lock()
        self.system = SYSTEM_AGENT.format(vocab="\n".join(vocab), noise_hint=noise_hint)

    def call(self, label: str, user: str, max_tokens: int = 4000) -> tuple[dict, dict]:
        msgs = [{"role": "system", "content": self.system}, {"role": "user", "content": user}]
        with self.lock:
            self.ledger.reserve(label, 0.01)
        try:
            obj, resp = self.client.complete_json(msgs, max_tokens=max_tokens)
            status, usage = "ok", resp.usage
        except E.LLMError as error:
            obj, status, usage = {}, f"failed:{getattr(error, 'code', type(error).__name__)}", None
        with self.lock:
            self.ledger.charge(label, usage, status="ok" if usage else "failed_unpriced", reserved_usd=0.01, note=status)
            self.ledger.write()
        return obj, {"status": status, "usage": usage}

    def parse_set(self, obj: dict) -> tuple[list[str] | None, int]:
        raw, out = obj.get("plausible"), obj.get("ruled_out")
        if raw == "ALL" or raw == ["ALL"]:
            return list(self.vocab), 0
        if raw is None and isinstance(out, list):  # complement form
            names = [str(x) for x in out]
            gone = {x for x in names if x in self.vset}
            return [x for x in self.vocab if x not in gone], len(names) - len(gone)
        if not isinstance(raw, list):
            return None, 0  # no set stated (counted as the whole vocabulary by the summaries)
        names = [str(x) for x in raw]
        keep = [x for x in dict.fromkeys(names) if x in self.vset]
        return keep, len(names) - len(keep)

    def parse_option(self, obj: dict, menu: list[int]) -> int | None:
        o = obj.get("next_option")
        if o is None:
            return None
        o = str(o).strip()
        names = {self.options[j]: j for j in menu}
        return names.get(o)

    def user_text(self, obs: list[tuple[int, dict]], menu: list[int], remaining: int, tool: str | None) -> str:
        parts = [f"Budget remaining: {remaining} observation(s).",
                 "Menu (options not yet bought): " + ", ".join(self.options[j] for j in menu)]
        if not obs:
            parts.append("No observation yet.")
        for o, s in obs:
            parts.append(f"Observation {self.options[o]}: strength {s['strength']}; up: {' '.join(s['up'])}; down: {' '.join(s['down'])}")
        if tool:
            parts.append(tool)
        return "\n".join(parts)

    def episode(self, drug_key: str, z_gene_by_opt: dict[int, np.ndarray], avail: list[int], budget: int,
                mode: str, fz=None, z_proj=None, rng_fallback: int = 0) -> dict:
        """Run one LLM-driven episode; returns per-budget sets (None = no set stated)."""
        obs: list[tuple[int, dict]] = []
        steps, calls = [], []
        menu = list(avail)
        tool = None
        dropped = 0
        for k in range(budget + 1):
            remaining = budget - k
            obj, meta = self.call(f"agent:{mode}:{drug_key}:{k}", self.user_text(obs, menu, remaining, tool))
            calls.append(meta)
            if k > 0:
                st, d = self.parse_set(obj)
                dropped += d
                rec = {"budget": k, "option": self.options[obs[-1][0]], "agent_set": st}
                if fz is not None:
                    opts = [o for o, _ in obs]
                    p = fz.pvalues(z_proj, opts, np.arange(len(fz.names)))
                    rec["falsifier_set"] = [str(x) for x in fz.names[p > fz.alpha]]
                steps.append(rec)
            if remaining == 0 or not menu:
                break
            o = self.parse_option(obj, menu)
            if o is None:  # invalid or missing choice: fixed fallback, counted
                o = menu[rng_fallback % len(menu)]
                calls[-1]["invalid_option"] = True
            menu.remove(o)
            obs.append((o, summarise(z_gene_by_opt[o], self.genes)))
            if mode == "interface" and fz is not None:
                opts = [x for x, _ in obs]
                p = fz.pvalues(z_proj, opts, np.arange(len(fz.names)))
                top = np.argsort(-p)[:30]
                n_surv = int((p > fz.alpha).sum())
                tool = (f"World-model falsifier (conformal, alpha={fz.alpha}): {n_surv} of {len(p)} mechanisms not rejected. "
                        "Top p-values: " + "; ".join(f"{fz.names[i]} {p[i]:.2f}" for i in top))
        return {"steps": steps, "calls": calls, "dropped_names": dropped}

    def revise(self, drug_key: str, z_gene_by_opt: dict[int, np.ndarray], observed: list[int], rejected: list[str],
               n_propose: int = 5) -> tuple[list[str], dict]:
        obs = "\n".join(
            f"Observation {self.options[o]}: strength {summarise(z_gene_by_opt[o], self.genes)['strength']}; "
            f"up: {' '.join(summarise(z_gene_by_opt[o], self.genes)['up'])}; "
            f"down: {' '.join(summarise(z_gene_by_opt[o], self.genes)['down'])}" for o in observed)
        user = (f"Every mechanism tested so far was rejected by a calibrated test against these observations:\n{obs}\n\n"
                f"Rejected (do not propose again): {', '.join(rejected)}\n\n"
                f"Propose up to {n_propose} other mechanisms from the candidate list that could explain the observations. "
                'Return {"next_option": null, "plausible": [your proposals, most likely first], "ruled_out": null, "reasoning": "..."}')
        obj, meta = self.call(f"agent:revise:{drug_key}", user)
        st, d = self.parse_set(obj)
        st = [x for x in (st or []) if x not in set(rejected)][:n_propose]
        meta["dropped_names"] = d
        return st, meta
