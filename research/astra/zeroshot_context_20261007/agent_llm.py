"""LLM acquisition policy: chooses the next first-well profile or stops; nothing else.

The model receives exactly what the deterministic policies receive (the world's prior and current
posterior for every candidate, purchased screen values, the remaining budget) plus the public
metadata both arms could read (drug names, targets, MoA, dose, context organ and driver) and the
knowledge-gradient recommendation. It cannot change the belief update, the final flag rule, the
budget or any evidence permission. Invalid answers and API failures fall back to the
knowledge-gradient choice and are logged as failures.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from agent_policy import kg_values


class LLMAcquisition:
    def __init__(self, client, context: dict, candidates: list[dict], m: int, ledger: Path, max_tokens: int = 400):
        self.client, self.context, self.candidates, self.m = client, context, candidates, m
        self.ledger = Path(ledger)
        self.max_tokens = max_tokens
        self.receipts = []

    def _view(self, belief, available):
        sd = np.sqrt(np.maximum(np.diag(belief.cov), 0))
        order = np.lexsort((np.arange(len(belief.mean)), -belief.mean))
        rows = []
        for i in order:
            c = self.candidates[i]
            rows.append({"id": int(i), "drug": c["drug"], "dose_uM": c["dose_uM"], "targets": c.get("targets"),
                         "moa": c.get("moa"), "posterior_mean": round(float(belief.mean[i]), 4),
                         "posterior_sd": round(float(sd[i]), 4), "prior_mean": round(float(c["prior_mean"]), 4),
                         "screened_value": None if i not in belief.screened else round(float(belief.screened[i]), 4),
                         "available": bool(i in available)})
        return rows

    def __call__(self, belief, m, available, budget_left, rng):
        started = time.perf_counter()
        kg = kg_values(belief, m, available)
        recommended = max(kg, key=lambda i: (kg[i], -i))
        top_kg = sorted(kg, key=lambda i: (-kg[i], i))[:5]
        request = {
            "task": ("A new cancer cell line, never seen by the reference models, is being profiled. Each candidate is a "
                     "drug-dose condition. Buying a candidate's first-well profile reveals its measured root deviation "
                     "energy in that well (how differently this line responds than a 45-line reference panel; "
                     "larger = more context-specific). After buying, a fixed rule flags the m candidates with the highest "
                     "posterior mean; flags are scored in an independent replicate well. You only choose what to buy next, "
                     "or stop."),
            "scale": "root deviation energy, sqrt of mean squared log-expression deviation over 2,000 genes; can be slightly negative after noise correction",
            "m_flags": m, "screens_left": int(budget_left),
            "cell_line": self.context,
            "knowledge_gradient": {"recommended_id": int(recommended),
                                   "top5": [{"id": int(i), "expected_gain": round(kg[i], 5)} for i in top_kg],
                                   "meaning": "expected increase in the sum of the top-m posterior means from one more screen"},
            "candidates": self._view(belief, available),
            "rules": ["Choose only an id with available=true, or stop.", "Do not invent measurements.",
                      "Posterior values already include all purchased screens and their correlations."],
            "response_schema": {"action": "screen or stop", "id": "integer id when action is screen, else null",
                                "reason": "at most 30 words"},
        }
        record = {"request_digest_inputs": {"screens_left": int(budget_left), "screened": sorted(int(i) for i in belief.screened)},
                  "kg_recommended": int(recommended), "started_unix": time.time()}
        try:
            answer, response = self.client.complete_json([
                {"role": "system", "content": "You plan scientific acquisitions under a budget. Use only supplied facts and general biological knowledge. Return one JSON object."},
                {"role": "user", "content": json.dumps(request, separators=(",", ":"))}], max_tokens=self.max_tokens)
            action = str(answer.get("action", "")).lower()
            if action == "stop":
                choice = None
            elif action == "screen":
                choice = int(answer.get("id"))
                if choice not in available:
                    raise ValueError("unavailable_candidate")
            else:
                raise ValueError("unknown_action")
            record.update(status="accepted", answer=answer, model=response.model, usage=dict(response.usage),
                          followed_kg=choice == recommended)
        except Exception as error:  # fall back, never silently
            choice = recommended
            record.update(status="failed_fallback_kg", error_type=type(error).__name__,
                          error=str(error)[:200], usage=dict(getattr(self.client, "provider_usage", {})))
        record["elapsed_seconds"] = round(time.perf_counter() - started, 3)
        record["choice"] = None if choice is None else int(choice)
        self.receipts.append(record)
        with self.ledger.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
        return choice
