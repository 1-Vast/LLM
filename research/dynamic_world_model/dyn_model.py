"""The `dyn_model` policy: step 2 forecast from the held-out compound's own step-1 profile.

File summary
- Path: research/dynamic_world_model/dyn_model.py
- Purpose: when the first measurement was detected but ambiguous, forecast the compound's own
  profile at every remaining menu condition with the best transition arm (gene-space ridge, the
  best learned arm in every transfer family), and estimate how likely the validator is to
  eliminate each hypothesis there. Use `dyn_ref` for measurement choice until conditional
  forecasts can distinguish correct eliminations from wrong ones.
- Core points:
  - The forecast is read by the validator only as a planner diagnostic. It is a model prediction
    and is never itself imported as evidence.
  - Pseudo-measurements add a model residual (closed-form leave-one-out residuals of the ridge on
    training compounds) and two replicate-noise draws from training replicate differences at the
    target line and time, so detection is simulated the way the validator detects.
  - A transition forecast estimates which hypothesis the validator would eliminate, not whether
    that elimination is correct. Without hypothesis-conditional forecasts it is retained only as
    a diagnostic; measurement choice falls back explicitly to `dyn_ref`'s measured references.
- Run: python research/dynamic_world_model/dyn_model.py
- Depends on: common.py, episodes.py, transition.py
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np

import common as C
import episodes as E
import transition as T

DRAWS = 50
_LOO: dict = {}
_NOISE: dict = {}


def loo_residuals(data: C.Data, fold: int, key_s, key_t) -> np.ndarray | None:
    cache_key = (fold, key_s, key_t)
    if cache_key not in _LOO:
        model = T.fitted(data, fold, key_s, key_t)
        if model is None:
            _LOO[cache_key] = None
        else:
            K = model.Ys @ model.Ys.T
            lam = model.gene_lambda * (float(np.mean(np.diag(K))) or 1.0)
            H = K @ np.linalg.inv(K + lam * np.eye(len(K)))
            fitted_values = H @ model.Yt
            leverage = np.clip(1.0 - np.diag(H), 1e-6, None)
            _LOO[cache_key] = (model.Yt - fitted_values) / leverage[:, None]
    return _LOO[cache_key]


def replicate_noise(data: C.Data, fold: int, line_time) -> np.ndarray:
    cache_key = (fold, line_time)
    if cache_key not in _NOISE:
        comp = data.compounds.drop_duplicates("compound").set_index("compound")
        rows = [r for (line, t, _), members in data.index.items() if (line, t) == line_time
                for c, r in members.items() if comp.fold.get(c) != fold and C.qc_passed(data, r)]
        _NOISE[cache_key] = ((data.rep1[rows] - data.rep2[rows]) / math.sqrt(2.0)).astype(np.float64)
    return _NOISE[cache_key]


def forecast_card(ctx: E.FoldContext, compound, key1, key2, h1, h2, threshold: float, rng) -> dict:
    data = ctx.data
    fold = ctx.ft.fold
    model = T.fitted(data, fold, key1, key2)
    residuals = loo_residuals(data, fold, key1, key2)
    if model is None or residuals is None:
        return {"served": False, "reason": "no_transition_fit_for_pair"}
    y1 = data.shift[data.index[key1][compound]].astype(np.float64)
    forecast = model.predict("gene_ridge", y1)
    noise = replicate_noise(data, fold, (key2[0], key2[1]))
    counts = {"eliminate_a": 0, "eliminate_b": 0, "ambiguous": 0, "undetected": 0}
    for _ in range(DRAWS):
        base = forecast + residuals[rng.integers(len(residuals))]
        r1 = base + noise[rng.integers(len(noise))]
        r2 = base + noise[rng.integers(len(noise))]
        detected = C._pearson(r1, r2) >= threshold
        outcome = C.read_profile(ctx.ft, key2, 0.5 * (r1 + r2), detected, h1, h2, ctx.params)["outcome"]
        counts[outcome] += 1
    # The same elimination is correct under one hypothesis and wrong under the other. The
    # compound's pooled predictive distribution supplies neither conditional branch.
    return {"served": False, "reason": "hypothesis_conditional_forecast_unavailable",
            "p_elimination": (counts["eliminate_a"] + counts["eliminate_b"]) / DRAWS,
            "p_eliminate_h1": counts["eliminate_a"] / DRAWS,
            "p_eliminate_h2": counts["eliminate_b"] / DRAWS,
            "hypotheses": [h1, h2], "forecast": "gene_ridge",
            "draws": DRAWS, "counts": counts, "evidence_kind": "model_prediction"}


def make_policy(null: dict):
    def policy(ctx: E.FoldContext, compound, h1, h2, executed, menu):
        if not executed:
            return E.choose("separation", ctx, compound, h1, h2, executed, None)
        first = executed[0]
        if first["outcome"] != "ambiguous":
            return E.choose("dyn_ref", ctx, compound, h1, h2, executed, None)
        rng = np.random.default_rng([C.SEED, E.stable(compound, h1, h2, C.action_id(first["key"]))])
        cards = {}
        for key in menu:
            threshold = null[f"{key[0]}|{key[1]:g}"]["threshold"]
            cards[key] = forecast_card(ctx, compound, first["key"], key, h1, h2, threshold, rng)
        key, note = E.choose("dyn_ref", ctx, compound, h1, h2, executed, None)
        return key, {**note, "forecast_fallback": "dyn_ref",
                     "forecast_refusal": "hypothesis_conditional_forecast_unavailable",
                     "dynamic_forecasts": {C.action_id(k): cards[k] for k in menu}}
    return policy


def run_fold(task):
    tier_name, fold = task
    protocol = C.load_protocol()
    data = C.load()
    null = C.detection_null(data, protocol)
    detected = C.detected_flags(data, null)
    magnitude = E.Magnitude(data, detected)
    records = []
    for ctx, f in E.contexts(data, protocol, detected, magnitude, tier_names=(tier_name,), folds=(fold,)):
        ctx.extra["policies"] = {"dyn_model": make_policy(null)}
        for compound, truth, decoy, h1, h2 in E.episode_list(ctx, f):
            records.append({"tier": ctx.tier.name, "fold": f, "decoy": decoy}
                           | E.run_episode("dyn_model", ctx, compound, truth, h1, h2, None))
    return records


def main() -> None:
    from concurrent.futures import ProcessPoolExecutor
    started = time.time()
    data = C.load()
    folds = sorted(int(f) for f in data.compounds.fold.unique())
    tasks = [(t, f) for t in ("B", "A") for f in folds]
    records = []
    with ProcessPoolExecutor(max_workers=10) as pool:
        for (t, f), recs in zip(tasks, pool.map(run_fold, tasks)):
            records += recs
            print(f"{t} fold {f}: {len(recs)} episodes, {time.time() - started:.0f}s", flush=True)
    path = C.OUTPUTS / "episodes" / "episodes_dyn_model.jsonl"
    with path.open("w", encoding="utf-8") as stream:
        for r in records:
            stream.write(json.dumps(C.clean(r), default=C._default) + chr(10))
    C.write_json(C.OUTPUTS / "episodes" / "dyn_model_manifest.json", {
        "protocol_hashes": C.frozen_hashes(), "episodes": len(records), "seconds": round(time.time() - started, 1),
        "runner_sha256": {n: hashlib.sha256((C.HERE / n).read_bytes()).hexdigest()
                          for n in ("dyn_model.py", "episodes.py", "common.py", "transition.py")}})


if __name__ == "__main__":
    main()
