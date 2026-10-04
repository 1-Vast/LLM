"""LLM planning core: a language model chooses each batch from the world model's shortlist.

File summary
- Path: research/certified_discovery/llm_agent.py
- Purpose: test whether a language-model planner adds knowledge or judgment to the world
  model's ranking, and show that certification stays valid when the acquisition policy is a
  black box whose selection probabilities nobody can write down.
- Core points:
  - Each round the planner sees the world model's top `menu_factor` x batch candidates (drug
    names, P(hit), predicted label, the pair's mean in other lines) and what the line has
    shown so far (per-drug results and every measured hit), and returns exactly `batch` ids.
  - `anonymous=True` replaces drug and cell-line names with stable codes: the same numbers,
    no pharmacology. Named minus anonymous isolates name-borne knowledge, which for public
    2016-2017 screens includes possible memorisation; that limit is stated with every result.
  - A reply that is not exactly `batch` distinct menu ids is repaired from the world-model
    order and counted (`LLM_INVALID_SELECTION`); a failed call falls back to the world model
    and is counted (`LLM_UNAVAILABLE`). Neither is silently treated as a planner choice.
  - Provider spend is recorded per call at declared rates and written after every call; it is
    reported separately from laboratory cost and stops the run at a ceiling (`SPEND_CEILING`).
- Interfaces: `SpendBook`, `LLMPlannerArm`.
- Depends on: numpy, `agent.llm` (DeepSeek client, src), `world`.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import numpy as np

from .world import TransferWorld

# USD per million tokens, the rates recorded for MAESTRO's provider on 2026-09-12.
RATES = {"input_cache_miss": 0.30, "input_cache_hit": 0.006, "output": 1.20}


class SpendBook:
    """Thread-safe provider-spend ledger, persisted after every call."""

    def __init__(self, path: Path, ceiling_usd: float):
        self.path, self.ceiling = path, ceiling_usd
        self.lock = threading.Lock()
        self.entries: list[dict] = []

    @property
    def total(self) -> float:
        return sum(e["usd"] for e in self.entries)

    def charge(self, label: str, usage: dict, seconds: float) -> None:
        hit = int(usage.get("prompt_cache_hit_tokens", 0) or 0)
        prompt = int(usage.get("prompt_tokens", 0) or 0)
        miss = int(usage.get("prompt_cache_miss_tokens", max(prompt - hit, 0)) or 0)
        output = int(usage.get("completion_tokens", 0) or 0)
        usd = (miss * RATES["input_cache_miss"] + hit * RATES["input_cache_hit"] + output * RATES["output"]) / 1e6
        with self.lock:
            self.entries.append({"label": label, "prompt_tokens": prompt, "cache_hit_tokens": hit,
                                 "completion_tokens": output, "usd": usd, "seconds": round(seconds, 2)})
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps({"ceiling_usd": self.ceiling, "rates": RATES,
                                             "total_usd": self.total, "calls": len(self.entries),
                                             "entries": self.entries}, indent=1), encoding="utf-8")

    def exhausted(self) -> bool:
        with self.lock:
            return self.total >= self.ceiling


SYSTEM = (
    "You are the planning core of a drug-combination discovery agent. A virtual-cell world model "
    "has ranked candidate experiments in one cancer cell line. Each experiment measures one drug pair "
    "over a dose matrix; it is a hit if its mean Bliss excess exceeds 10 percentage points (about "
    "{base:.1%} of experiments in this screen are hits). Choose exactly {batch} candidate ids to "
    "measure next so that as many as possible are hits. Use pharmacology and the evidence shown; you "
    "may disagree with the world model. Return JSON: {{\"chosen\": [ids], \"rationale\": \"<= 40 words\"}}."
)


SYSTEM_BLIND = (
    "You are the planning core of a drug-combination discovery agent. A virtual-cell world model has "
    "shortlisted candidate experiments in one cancer cell line; the list is in random order and the "
    "model's scores are withheld. Each experiment measures one drug pair over a dose matrix; it is a hit "
    "if its mean Bliss excess exceeds 10 percentage points (about {base:.1%} of experiments in this "
    "screen are hits). Choose exactly {batch} candidate ids to measure next so that as many as possible "
    "are hits, using pharmacology (mechanism complementarity, known synergistic classes) and the "
    "evidence already measured in this line. Return JSON: {{\"chosen\": [ids], \"rationale\": \"<= 40 words\"}}."
)


class LLMPlannerArm:
    probabilistic = True

    def __init__(self, world: TransferWorld, client, book: SpendBook, *, batch: int,
                 mode: str, menu_factor: int = 2, max_tokens: int = 3000):
        if mode not in ("named", "anonymous", "blind"):
            raise ValueError(mode)
        self.world, self.client, self.book = world, client, book
        self.batch, self.mode, self.menu_factor, self.max_tokens = batch, mode, menu_factor, max_tokens
        self.anonymous = mode == "anonymous"
        self.blind = mode == "blind"          # names and line evidence, but no model numbers
        self.name = f"llm_{mode}"
        self.rng = np.random.default_rng(4242 + world.target)
        self.last_p_hit = None
        self.events: list[dict] = []
        lib = world.lib
        self.base_rate = float(np.mean(lib.y[lib.c != world.target] > lib.threshold))

    def _drug(self, index: int) -> str:
        return f"D{index:03d}" if self.anonymous else self.world.lib.drugs[index]

    def _prompt(self, menu: np.ndarray, mean, p_hit, measured, values, k: int) -> list[dict]:
        lib, world = self.world.lib, self.world
        rows = world.rows
        line = "line L" if self.anonymous else f"cell line {lib.lines[world.target]}"
        evidence = ["no combination measured yet in this line"]
        if len(measured):
            drug_sum: dict[int, list[float]] = {}
            for i, v in zip(measured, values):
                for d in (lib.a[rows[i]], lib.b[rows[i]]):
                    drug_sum.setdefault(int(d), []).append(float(v))
            hits = [f"{self._drug(lib.a[rows[i]])}+{self._drug(lib.b[rows[i]])}:{v:.0f}"
                    for i, v in zip(measured, values) if v > lib.threshold]
            per_drug = [f"{self._drug(d)} n={len(v)} mean={np.mean(v):.1f} hits={sum(x > lib.threshold for x in v)}"
                        for d, v in sorted(drug_sum.items(), key=lambda kv: -np.mean(kv[1]))]
            evidence = [f"{len(measured)} measured, {len(hits)} hits", "hits: " + (", ".join(hits) or "none"),
                        "per-drug results in this line: " + "; ".join(per_drug)]
        if self.blind:
            table = ["id | drug A | drug B"]
            for i in self.rng.permutation(menu):
                table.append(f"{i} | {self._drug(lib.a[rows[i]])} | {self._drug(lib.b[rows[i]])}")
        else:
            table = ["id | drug A | drug B | P(hit) | predicted label | pair mean in other lines"]
            for i in menu:
                table.append(f"{i} | {self._drug(lib.a[rows[i]])} | {self._drug(lib.b[rows[i]])} | "
                             f"{p_hit[i]:.2f} | {mean[i]:.1f} | {world.X_target[i, 0]:.1f}")
        user = "\n".join([f"Target: {line}.", *evidence, f"Candidates ({menu.size}, choose {k}):", *table])
        system = (SYSTEM_BLIND if self.blind else SYSTEM).format(base=self.base_rate, batch=k)
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]

    def choose(self, available: np.ndarray, measured, values, k: int) -> np.ndarray:
        """Return k candidate indices, recording how the choice was made."""
        mean, var = self.world.posterior(measured, values)
        p_hit = self.world.p_hit(mean, var)
        self.last_p_hit = p_hit
        candidates = np.flatnonzero(available)
        order = candidates[np.argsort(-p_hit[candidates], kind="stable")]
        menu = order[: self.menu_factor * k]
        event = {"round_measured": int(len(measured)), "menu": int(menu.size), "k": int(k)}
        if self.book.exhausted():
            event["code"] = "SPEND_CEILING"
            self.events.append(event)
            return order[:k]
        messages = self._prompt(menu, mean, p_hit, measured, values, k)
        started = time.perf_counter()
        try:
            reply, response = self.client.complete_json(messages, max_tokens=self.max_tokens)
            self.book.charge(f"{self.name}:{self.world.target}:{len(measured)}", dict(response.usage),
                             time.perf_counter() - started)
        except Exception as error:  # transport or protocol failure: fall back, and say so
            event.update({"code": "LLM_UNAVAILABLE", "error": type(error).__name__,
                          "detail": getattr(error, "code", str(error)[:120])})
            self.events.append(event)
            return order[:k]
        chosen_raw = reply.get("chosen", []) if isinstance(reply, dict) else []
        allowed = set(menu.tolist())
        chosen, seen = [], set()
        for item in chosen_raw if isinstance(chosen_raw, list) else []:
            try:
                value = int(item)
            except (TypeError, ValueError):
                continue
            if value in allowed and value not in seen:
                chosen.append(value)
                seen.add(value)
        valid = len(chosen) == k and len(chosen_raw) == k
        if len(chosen) < k:
            chosen += [i for i in order.tolist() if i not in seen][: k - len(chosen)]
        chosen = chosen[:k]
        overlap = len(set(chosen) & set(order[:k].tolist()))
        event.update({"code": None if valid else "LLM_INVALID_SELECTION", "returned": len(chosen_raw),
                      "agreement_with_world_model": overlap / max(k, 1),
                      "rationale": str(reply.get("rationale", ""))[:300] if isinstance(reply, dict) else ""})
        self.events.append(event)
        return np.array(chosen, dtype=int)

    def scores(self, measured, values):  # used for the terminal shortlist and certification
        mean, var = self.world.posterior(measured, values)
        self.last_p_hit = self.world.p_hit(mean, var)
        return self.last_p_hit
