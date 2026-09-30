"""E2: calibration after action selection, and a risk-controlled abstention policy, for old and new world models.

File summary
- Path: research/dual_core/e2.py
- Purpose: run and analyse protocol_e2.json's E2 on the 20 protocol-v2.1 development tasks.
- Core points:
  - Two planners run through the registered runner on every episode, with one `LedgerExecutor`:
    - `reference`: the block-2 belief planner with the reference world;
    - `incontext`: the same planner with `world2.StrictInContextWorld`.
    The reference arm must reproduce E-DATA1's `belief` traces; this is checked and reported.
  - After each episode, both world models forecast every executed step of both planners. The
    history and purchased prompts are those available at that step (cross-scoring on identical
    selected steps). Both hypotheses' branches are stored, because the runner is truth-free.
  - Policies are evaluated from the unconstrained traces by exact truncation (`agent.truncate`):
    - P0: no abstention;
    - P1: naive, abstain when the raw risk forecast exceeds alpha;
    - P2: a threshold chosen on the calibration folds as the largest grid value whose unit-weighted
      wrong-among-decided rate is at most alpha;
    - P3: Learn-then-Test, fixed-sequence Hoeffding-Bentkus tests of E[wrong - alpha x decided] <= 0
      over units at delta.
    Thresholds and calibrators for test fold f are fitted only on the other folds
    (`splits.crossfit_roles`).
  - Step calibration: a cross-fitted Platt map (logistic in logit risk) on each planner's own
    selected steps, against the raw risk.
  - A live-abstention check replays a deterministic subsample with `agent.abstaining` and compares it
    with truncation.
- Interfaces: `run_task`, `analyse`, `posthoc_binding_alpha`; CLI
  `python -m research.dual_core.e2 run [--workers N] | analyse | posthoc`
- Depends on: agent.py, world2.py, ledger.py, splits.py, research/protocol_v2, research/belief_planning
"""
from __future__ import annotations

import argparse
import gzip
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import splits as SP

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/dual_core_20260927/e2"
SEED = 20260927
DRAWS = 10_000
TASKS = tuple((d, t, f) for d, t in (("sciplex3", "B"), ("l1000", "LT"), ("sciplex3", "A"), ("l1000", "T"))
              for f in SP.FOLDS)
LIVE_CHECK = 12
"""Episodes per task replayed live with abstention to check exact truncation."""


def _protocol() -> dict:
    return json.loads((ROOT / "research/dual_core/protocol_e2.json").read_text(encoding="utf-8"))


def run_task(task) -> dict:
    from threadpoolctl import threadpool_limits

    from research.belief_planning import arms as BA
    from research.belief_planning import tasks as T
    from research.belief_planning import world as W
    from research.protocol_v2 import contracts as K
    from research.protocol_v2 import runner as RN
    from research.protocol_v2 import tasks_v21 as TV

    from . import agent as AG
    from . import world2 as W2

    dataset, tier, fold = task
    spec = _protocol()
    started = time.time()
    E, C = K.T.E, K.T.C
    with threadpool_limits(limits=1):
        data, real_ctx, setting, design = TV.load(dataset, tier, fold)
        comp = data.compounds.drop_duplicates("compound").set_index("compound")
        heldout = set(comp.index[comp.fold == fold])
        episodes = TV.episode_list(real_ctx, fold)
        training = TV.training_compounds(real_ctx, fold)
        view = K.public_view(real_ctx, heldout, training_compounds=training, design=design)
        problems = K.public_view_problems(view, heldout)
        unit_of = T.units(dataset)[T.UNIT[dataset]].astype(str).to_dict()
        reference = BA.world_for(view, "on", "true")
        fp, pos = view.extra["fingerprints"]
        public = view.data.compounds.drop_duplicates("compound").set_index("compound")
        unit_col = "component" if "component" in public.columns else "skeleton"
        groups = {c: g for c, g in public[unit_col].items() if isinstance(g, str)}
        quality = np.clip(np.nan_to_num(np.asarray(data.agreement, dtype=np.float64), nan=0.0), 0.0, 1.0)
        ref_quality = {}
        for key, table in view.ft.tables.items():
            for name in table.names:
                row = data.index[key][name]
                ref_quality.setdefault(name, {})[key] = float(quality[row])
        fit_started = time.time()
        world = W2.StrictInContextWorld(view.ft, view.params, training, reference_quality=ref_quality,
                                        transfer_arm=spec["world_model"]["transfer_arm"], source="auto",
                                        fingerprints=fp, positions=pos, vc="on", feedback="true",
                                        hyperparameters=reference.hyperparameters, groups=groups, heldout=heldout)
        fit_seconds = time.time() - fit_started
        detected = real_ctx.detected
        batch = (data.conditions.plate_rep1 if dataset == "sciplex3" else data.conditions.batch).astype(str).to_numpy()
        executor = AG.LedgerExecutor(real_ctx, dataset=dataset,
                                     assay="sci-RNA-seq3 pseudobulk shift" if dataset == "sciplex3" else "L1000 Level 5 MODZ",
                                     quality=quality, batch=batch, detected=detected, cost_days=setting.days)
        arms = {"reference": BA.belief_arm(), "incontext": AG.incontext_arm(executor, {id(view): world})}
        traces, audit, cross, live = [], [], [], []
        for n_ep, (compound, truth, decoy, h1, h2) in enumerate(episodes):
            available = view.data.availability[compound]
            local = RN.local_setting(setting, available)
            meta = {"dataset": dataset, "tier": tier, "fold": fold, "decoy": decoy, "unit": unit_of.get(compound, compound)}
            for name, arm in arms.items():
                ledger = executor.open(compound, h1, h2)
                trace = RN.run_episode(name, arm, view, real_ctx, compound, h1, h2, setting, execute=executor,
                                       design_menu=True)
                audit += [f"{name}:{compound}:{p}" for p in RN.audit_trace(trace, local)]
                trace.update(meta, ledger_refusals=[list(map(str, r)) for r in ledger.refusals])
                # cross-scoring: both world models on this planner's executed steps, truth-free
                public_steps = [{k: s[k] for k in ("key", "action", "outcome", "qc", "eliminated")} for s in trace["steps"]]
                real = [(tuple(s["key"]), W.label_of(s["outcome"])) for s in trace["steps"]]
                for i, step in enumerate(trace["steps"]):
                    key = tuple(step["key"])
                    prompts = ledger.prompts(target=key, executed=public_steps[:i])
                    fr = reference.forecast(key, h1, h2, compound, tuple(real[:i]))
                    fi = world.forecast(key, h1, h2, compound, tuple(real[:i]), profiles=prompts)
                    cross.append({"arm": name, "compound": compound, "h1": h1, "h2": h2, "step": i, "key": list(key),
                                  "label": real[i][1], "prompts": len(prompts),
                                  "reference": {b.hypothesis: dict(b.probabilities) for b in fr.branches},
                                  "incontext": {b.hypothesis: dict(b.probabilities) for b in fi.branches}})
                traces.append(trace)
                if n_ep < LIVE_CHECK:
                    threshold = spec["live_check_threshold"]
                    executor.open(compound, h1, h2)
                    live_trace = RN.run_episode(name, AG.abstaining(arm, threshold), view, real_ctx, compound, h1, h2,
                                                setting, execute=executor, design_menu=True)
                    predicted = AG.truncate(trace, truth, threshold)
                    observed_keys = [tuple(s["key"]) for s in live_trace["steps"]]
                    live_decided = bool(live_trace["steps"] and live_trace["steps"][-1]["eliminated"])
                    live.append({"arm": name, "compound": compound, "h1": h1, "h2": h2,
                                 "match": observed_keys == predicted["keys"] and live_decided == predicted["decided"]})
        truth_of = {(c, a, b): t for c, t, _, a, b in episodes}
        for trace in traces:
            trace["score"] = K.score(trace, truth_of[(trace["compound"], trace["h1"], trace["h2"])])
            trace["truth"] = trace["score"]["truth"]
    return {"task": list(task), "traces": traces, "cross": cross, "live": live, "problems": problems + audit,
            "episodes": len(episodes), "reference_hyperparameters": {k: reference.hyperparameters[k] for k in ("s", "k", "e")},
            "incontext": {k: v for k, v in world.incontext.items()}, "fit_seconds": fit_seconds,
            "seconds": time.time() - started}


def _write(result: dict) -> str:
    dataset, tier, fold = result["task"]
    base = OUT / "tasks" / f"{dataset}_{tier}_{fold}"
    base.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(f"{base}.traces.jsonl.gz", "wt", encoding="utf-8") as f:
        for t in result["traces"]:
            f.write(json.dumps(t, default=str) + "\n")
    with gzip.open(f"{base}.cross.jsonl.gz", "wt", encoding="utf-8") as f:
        for c in result["cross"]:
            f.write(json.dumps(c, default=str) + "\n")
    meta = {k: v for k, v in result.items() if k not in ("traces", "cross")}
    Path(f"{base}.json").write_text(json.dumps(meta, indent=1, default=str), encoding="utf-8")
    live_ok = sum(x["match"] for x in result["live"])
    return (f"{result['task']} episodes {result['episodes']} problems {len(result['problems'])} live {live_ok}/"
            f"{len(result['live'])} fit {result['fit_seconds']:.0f}s total {result['seconds']:.0f}s "
            f"source {result['incontext'].get('source')} kappa {result['incontext'].get('kappa')}")


def run(workers: int) -> None:
    import multiprocessing as mp
    OUT.mkdir(parents=True, exist_ok=True)
    todo = [t for t in TASKS if not (OUT / "tasks" / f"{t[0]}_{t[1]}_{t[2]}.json").exists()]
    with mp.get_context("spawn").Pool(workers) as pool:
        for result in pool.imap_unordered(run_task, todo):
            print(_write(result), flush=True)


# ------------------------------------------------------------------------------------ analysis
def _load(out: Path):
    traces, cross, metas = [], [], []
    for meta_path in sorted((out / "tasks").glob("*.json")):
        base = str(meta_path)[:-5]
        metas.append(json.loads(meta_path.read_text(encoding="utf-8")))
        with gzip.open(base + ".traces.jsonl.gz", "rt", encoding="utf-8") as f:
            traces += [json.loads(line) for line in f]
        with gzip.open(base + ".cross.jsonl.gz", "rt", encoding="utf-8") as f:
            cross += [dict(json.loads(line), task=meta_path.stem) for line in f]
    return traces, cross, metas


def step_table(traces) -> pd.DataFrame:
    from . import agent as AG
    rows = []
    for t in traces:
        truth, h1 = t["truth"], t["h1"]
        eliminated_before = set()
        for i, s in enumerate(t["steps"]):
            note = s.get("note") or {}
            pred = note.get("prediction_by_hypothesis") or {}
            now = set(s["eliminated"]) - eliminated_before
            rows.append({"arm": t["arm"], "dataset": t["dataset"], "tier": t["tier"], "fold": t["fold"], "unit": t["unit"],
                         "compound": t["compound"], "h1": h1, "h2": t["h2"], "step": i,
                         "risk": AG.note_risk(note), "risk_truth": (pred.get(truth) or {}).get("p_wrong"),
                         "wrong": truth in now, "eliminating": bool(now), "qc": bool(s["qc"])})
            eliminated_before |= set(s["eliminated"])
    return pd.DataFrame(rows)


def _logit(p):
    p = np.clip(np.asarray(p, dtype=np.float64), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def platt(train: pd.DataFrame):
    """Logistic recalibration a + b logit(risk), weakly regularised; ratio scaling if no event is present."""
    from sklearn.linear_model import LogisticRegression
    x, y = _logit(train.risk)[:, None], train.wrong.to_numpy(int)
    if y.sum() == 0 or y.sum() == len(y):
        ratio = (y.sum() + 0.5) / (train.risk.sum() + 0.5)
        return lambda r: np.clip(np.asarray(r, float) * ratio, 0, 1), {"kind": "ratio", "ratio": float(ratio)}
    model = LogisticRegression(C=100.0).fit(x, y)
    a, b = float(model.intercept_[0]), float(model.coef_[0, 0])
    return lambda r: 1 / (1 + np.exp(-(a + b * _logit(r)))), {"kind": "platt", "a": a, "b": b}


def _bern_nll(p, y):
    p = np.clip(np.asarray(p, float), 1e-9, 1 - 1e-9)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def _unit_boot(values_by_unit: np.ndarray, rng, draws=DRAWS):
    index = rng.integers(len(values_by_unit), size=(draws, len(values_by_unit)))
    return np.quantile(values_by_unit[index].mean(1), [0.025, 0.975]).tolist()


def calibration(steps: pd.DataFrame, roles: dict) -> dict:
    """Cross-fitted Platt on each planner's own selected steps; raw vs calibrated on held-out folds."""
    out = {}
    rng = np.random.default_rng(SEED)
    for (dataset, arm), g in steps.dropna(subset=["risk"]).groupby(["dataset", "arm"]):
        parts, fits = [], {}
        for f, cal in roles.items():
            test, train = g[g.fold == f], g[g.fold.isin(cal)]
            if test.empty:
                continue
            fn, info = platt(train)
            fits[int(f)] = info
            parts.append(test.assign(calibrated=fn(test.risk.to_numpy())))
        h = pd.concat(parts, ignore_index=True)
        y = h.wrong.to_numpy(float)
        h = h.assign(nll_raw=_bern_nll(h.risk, y), nll_cal=_bern_nll(h.calibrated, y),
                     brier_raw=(h.risk - y) ** 2, brier_cal=(h.calibrated - y) ** 2)
        per_unit = h.groupby("unit").agg(obs=("wrong", "sum"), raw=("risk", "sum"), cal=("calibrated", "sum"),
                                         dn=("nll_cal", "sum"), rn=("nll_raw", "sum"), n=("wrong", "size"))
        idx = rng.integers(len(per_unit), size=(DRAWS, len(per_unit)))
        ratio = lambda num, den: (per_unit[num].to_numpy()[idx].sum(1) / np.maximum(per_unit[den].to_numpy()[idx].sum(1), 1e-12))
        diff = (per_unit.dn - per_unit.rn).to_numpy() / per_unit.n.to_numpy()
        bins = [0, 0.005, 0.01, 0.02, 0.05, 0.1, 1.0]
        reliability = {}
        for col in ("risk", "calibrated"):
            cut = pd.cut(h[col], bins, include_lowest=True)
            reliability[col] = {str(k): {"steps": int(len(v)), "forecast": float(v[col].mean()), "observed": float(v.wrong.mean())}
                                for k, v in h.groupby(cut, observed=True)}
        out[f"{dataset}|{arm}"] = {
            "steps": int(len(h)), "units": int(h.unit.nunique()), "wrong_events": int(y.sum()),
            "observed_over_forecast_raw": float(y.sum() / h.risk.sum()),
            "observed_over_forecast_raw_ci": np.quantile(ratio("obs", "raw"), [0.025, 0.975]).tolist(),
            "observed_over_forecast_calibrated": float(y.sum() / h.calibrated.sum()),
            "observed_over_forecast_calibrated_ci": np.quantile(ratio("obs", "cal"), [0.025, 0.975]).tolist(),
            "nll_raw": float(h.nll_raw.mean()), "nll_calibrated": float(h.nll_cal.mean()),
            "nll_calibrated_minus_raw_unit_mean": float(diff.mean()), "nll_difference_ci": _unit_boot(diff, rng),
            "brier_raw": float(h.brier_raw.mean()), "brier_calibrated": float(h.brier_cal.mean()),
            "reliability": reliability, "by_tier": {t: {"observed": int(v.wrong.sum()), "raw": float(v.risk.sum()),
                                                        "calibrated": float(v.calibrated.sum())} for t, v in h.groupby("tier")},
            "fits": fits}
    return out


def _hb_pvalue(mean: float, n: int, t: float) -> float:
    """Hoeffding-Bentkus p-value for H0: E[loss] >= t, losses in [0, 1] (Bates et al. 2021)."""
    from scipy.stats import binom
    if mean >= t:
        return 1.0
    h1 = mean * np.log(mean / t) + (1 - mean) * np.log((1 - mean) / (1 - t)) if 0 < mean < 1 else \
        (np.log(1 / (1 - t)) if mean == 0 else np.inf)
    hoeffding = float(np.exp(-n * h1))
    bentkus = float(np.e * binom.cdf(np.ceil(n * mean), n, t))
    return min(hoeffding, bentkus, 1.0)


def _episode_outcomes(traces, arm, dataset, threshold, calibrate=lambda r: r):
    from . import agent as AG
    rows = []
    for t in traces:
        if t["arm"] != arm or t["dataset"] != dataset:
            continue
        o = AG.truncate(t, t["truth"], threshold, calibrate)
        rows.append({"fold": t["fold"], "unit": t["unit"], "tier": t["tier"], "episode": (t["compound"], t["h1"], t["h2"]),
                     **{k: o[k] for k in ("decided", "wrong", "correct", "abstained", "measurements")}})
    return pd.DataFrame(rows)


def _conditional(frame: pd.DataFrame) -> float:
    u = frame.groupby("unit")[["wrong", "decided"]].mean()
    return float(u.wrong.mean() / u.decided.mean()) if u.decided.mean() > 0 else float("nan")


def policies(traces, roles: dict, spec: dict) -> dict:
    alpha, delta, grid = spec["alpha"], spec["delta"], spec["threshold_grid"]
    out = {}
    for dataset in sorted({t["dataset"] for t in traces}):
        for arm in ("reference", "incontext"):
            per_policy = {"P0": [], "P1": [], "P2": [], "P3": []}
            chosen = {}
            full = {lam: _episode_outcomes(traces, arm, dataset, lam) for lam in grid}
            for f, cal in roles.items():
                test_mask = {lam: full[lam].fold == f for lam in grid}
                # P2: plug-in on calibration folds
                p2 = [lam for lam in grid if _conditional(full[lam][full[lam].fold.isin(cal)]) <= alpha]
                lam2 = max(p2) if p2 else min(grid)
                # P3: Learn-then-Test, fixed sequence from the strictest threshold upward
                lam3 = None
                for lam in sorted(grid):
                    c = full[lam][full[lam].fold.isin(cal)]
                    z = c.groupby("unit").apply(lambda u: (u.wrong - alpha * u.decided).mean(), include_groups=False)
                    zt = (z.to_numpy() + alpha) / (1 + alpha)
                    if _hb_pvalue(float(zt.mean()), len(zt), alpha / (1 + alpha)) <= delta:
                        lam3 = lam
                    else:
                        break
                lam3 = lam3 if lam3 is not None else 0.0
                chosen[int(f)] = {"P2": lam2, "P3": lam3}
                per_policy["P0"].append(full[max(grid)][test_mask[max(grid)]])
                per_policy["P1"].append(_episode_outcomes(traces, arm, dataset, alpha).query("fold == @f"))
                per_policy["P2"].append(full[lam2][test_mask[lam2]] if lam2 in full else
                                        _episode_outcomes(traces, arm, dataset, lam2).query("fold == @f"))
                per_policy["P3"].append(_episode_outcomes(traces, arm, dataset, lam3).query("fold == @f"))
            summary = {}
            frames = {k: pd.concat(v, ignore_index=True) for k, v in per_policy.items()}
            rng = np.random.default_rng(SEED)
            units = sorted(frames["P0"].unit.astype(str).unique())
            idx = rng.integers(len(units), size=(DRAWS, len(units)))
            for k, fr in frames.items():
                u = fr.groupby(fr.unit.astype(str))[["wrong", "decided", "correct", "abstained", "measurements"]].mean().reindex(units)
                cond_boot = u.wrong.to_numpy()[idx].mean(1) / np.maximum(u.decided.to_numpy()[idx].mean(1), 1e-12)
                summary[k] = {"wrong_among_decided": float(u.wrong.mean() / max(u.decided.mean(), 1e-12)),
                              "wrong_among_decided_ci": np.quantile(cond_boot, [0.025, 0.975]).tolist(),
                              "wrong_per_episode": float(u.wrong.mean()), "coverage": float(u.decided.mean()),
                              "correct": float(u.correct.mean()), "abstained": float(u.abstained.mean()),
                              "measurements": float(u.measurements.mean()), "episodes": int(len(fr)), "units": len(units)}
            for k in ("P1", "P2", "P3"):
                a, b = frames[k], frames["P0"]
                ua = a.groupby(a.unit.astype(str))[["wrong", "decided"]].mean().reindex(units)
                ub = b.groupby(b.unit.astype(str))[["wrong", "decided"]].mean().reindex(units)
                ca = ua.wrong.to_numpy()[idx].mean(1) / np.maximum(ua.decided.to_numpy()[idx].mean(1), 1e-12)
                cb = ub.wrong.to_numpy()[idx].mean(1) / np.maximum(ub.decided.to_numpy()[idx].mean(1), 1e-12)
                summary[f"{k}-P0"] = {"wrong_among_decided": np.quantile(ca - cb, [0.025, 0.5, 0.975]).tolist(),
                                      "coverage": np.quantile(ua.decided.to_numpy()[idx].mean(1) - ub.decided.to_numpy()[idx].mean(1),
                                                              [0.025, 0.5, 0.975]).tolist()}
            curve = {str(lam): {"coverage": float(full[lam].groupby("unit").decided.mean().mean()),
                                "wrong_among_decided": _conditional(full[lam])} for lam in grid}
            out[f"{dataset}|{arm}"] = {"policies": summary, "thresholds": chosen, "risk_coverage_all_folds": curve,
                                       "frames": frames}
    return out


def interaction(pol: dict) -> dict:
    """2 x 2 on identical episodes: world {reference, incontext} x policy {P0, P2}, unit bootstrap."""
    out = {}
    for dataset in sorted({k.split("|")[0] for k in pol}):
        fr = {(w, p): pol[f"{dataset}|{w}"]["frames"][p] for w in ("reference", "incontext") for p in ("P0", "P2")}
        units = sorted(fr[("reference", "P0")].unit.astype(str).unique())
        rng = np.random.default_rng(SEED)
        idx = rng.integers(len(units), size=(DRAWS, len(units)))
        means = {k: v.groupby(v.unit.astype(str))[["wrong", "decided"]].mean().reindex(units) for k, v in fr.items()}
        res = {}
        for metric in ("decided", "wrong"):
            m = {k: v[metric].to_numpy()[idx].mean(1) for k, v in means.items()}
            inter = (m[("incontext", "P2")] - m[("incontext", "P0")]) - (m[("reference", "P2")] - m[("reference", "P0")])
            world_at_p2 = m[("incontext", "P2")] - m[("reference", "P2")]
            res[metric] = {"interaction": np.quantile(inter, [0.025, 0.5, 0.975]).tolist(),
                           "incontext_minus_reference_under_P2": np.quantile(world_at_p2, [0.025, 0.5, 0.975]).tolist(),
                           "cells": {f"{w}|{p}": float(v[metric].mean()) for (w, p), v in means.items()}}
        out[dataset] = res
    return out


def cross_scoring(cross: list, traces: list) -> dict:
    """Both world models' truth-branch NLL of the realised label on identical selected steps (paired)."""
    truth = {(t["arm"], t["compound"], t["h1"], t["h2"]): (t["truth"], t["unit"], t["dataset"]) for t in traces}
    rows = []
    for c in cross:
        tr, unit, dataset = truth[(c["arm"], c["compound"], c["h1"], c["h2"])]
        rows.append({"arm": c["arm"], "dataset": dataset, "unit": unit, "prompts": c["prompts"],
                     "nll_reference": -np.log(max(c["reference"][tr].get(c["label"], 0.0), 1e-12)),
                     "nll_incontext": -np.log(max(c["incontext"][tr].get(c["label"], 0.0), 1e-12))})
    df = pd.DataFrame(rows)
    out = {}
    rng = np.random.default_rng(SEED)
    for (dataset, arm), g in df.groupby(["dataset", "arm"]):
        for scope, h in (("all_steps", g), ("steps_with_prompt", g[g.prompts > 0])):
            if h.empty:
                continue
            u = h.groupby("unit").apply(lambda x: (x.nll_incontext - x.nll_reference).mean(), include_groups=False).to_numpy()
            out[f"{dataset}|{arm}|{scope}"] = {"difference_unit_mean": float(u.mean()), "ci": _unit_boot(u, rng),
                                                "steps": int(len(h)), "units": int(len(u))}
    return out


def analyse(out: Path = OUT) -> dict:
    spec = _protocol()
    traces, cross, metas = _load(out)
    roles = SP.crossfit_roles()
    got = {tuple(m["task"]) for m in metas}
    missing = [list(t) for t in TASKS if tuple(t) not in got]
    steps = step_table(traces)
    pol = policies(traces, roles, spec["E2"])
    result = {"spec": "research/dual_core/protocol_e2.json", "tasks": len(metas), "missing_tasks": missing,
              "problems": sum(len(m["problems"]) for m in metas),
              "live_abstention_check": {"episodes": sum(len(m["live"]) for m in metas),
                                        "matches": sum(sum(x["match"] for x in m["live"]) for m in metas)},
              "fits": {"_".join(map(str, m["task"])): {k: m["incontext"].get(k) for k in ("source", "kappa", "tau", "gain")}
                       for m in metas},
              "calibration": calibration(steps, roles),
              "policies": {k: {kk: vv for kk, vv in v.items() if kk != "frames"} for k, v in pol.items()},
              "interaction": interaction(pol),
              "cross_scoring": cross_scoring(cross, traces),
              "decisions_descriptive": {f"{d}|{a}": {m: float(np.mean([t["score"][m] for t in traces if t["dataset"] == d and t["arm"] == a]))
                                                     for m in ("correct", "wrong", "decided")}
                                        for d in sorted({t["dataset"] for t in traces}) for a in ("reference", "incontext")}}
    (out / "analysis.json").write_text(json.dumps(result, indent=1, default=float), encoding="utf-8")
    return result


def posthoc_binding_alpha(out: Path = OUT, alphas=(0.02, 0.025, 0.03)) -> dict:
    """POST HOC (written after the registered analysis was read): does the policy act when the target binds?

    The registered alpha (0.05) is the validator's own maximum wrong-elimination rate, and both planners
    already satisfy it at full coverage, so P2 correctly selects no abstention. This repeats P2 and P3
    at stricter targets, where the constraint binds, and adds a coverage floor to P3 so that the
    trivial always-abstain solution cannot satisfy it. Not part of any gate.
    """
    spec = _protocol()["E2"]
    traces, _, _ = _load(out)
    roles = SP.crossfit_roles()
    grid = spec["threshold_grid"]
    result = {"status": "post hoc; the registered alpha is 0.05 and is not binding at full coverage",
              "coverage_floor_fraction": 0.5, "results": {}}
    for dataset in sorted({t["dataset"] for t in traces}):
        for arm in ("reference", "incontext"):
            full = {lam: _episode_outcomes(traces, arm, dataset, lam) for lam in grid}
            base_cov = float(full[max(grid)].groupby("unit").decided.mean().mean())
            for alpha in alphas:
                per = {"P2": [], "P3f": []}
                chosen = {}
                for f, cal in roles.items():
                    cal_frames = {lam: full[lam][full[lam].fold.isin(cal)] for lam in grid}
                    ok2 = [lam for lam in grid if _conditional(cal_frames[lam]) <= alpha
                           and float(cal_frames[lam].groupby("unit").decided.mean().mean()) >= 0.5 * base_cov]
                    lam2 = max(ok2) if ok2 else min(grid)
                    lam3 = None
                    for lam in sorted(grid):
                        c = cal_frames[lam]
                        cov = float(c.groupby("unit").decided.mean().mean())
                        z = c.groupby("unit").apply(lambda u: (u.wrong - alpha * u.decided).mean(), include_groups=False)
                        zt = (z.to_numpy() + alpha) / (1 + alpha)
                        if cov >= 0.5 * base_cov and _hb_pvalue(float(zt.mean()), len(zt), alpha / (1 + alpha)) <= spec["delta"]:
                            lam3 = lam
                    chosen[int(f)] = {"P2": lam2, "P3f": lam3 if lam3 is not None else min(grid)}
                    per["P2"].append(full[lam2].query("fold == @f"))
                    per["P3f"].append(full[chosen[int(f)]["P3f"]].query("fold == @f"))
                entry = {"thresholds": chosen}
                for k, frames in per.items():
                    fr = pd.concat(frames, ignore_index=True)
                    u = fr.groupby(fr.unit.astype(str))[["wrong", "decided", "measurements", "abstained"]].mean()
                    entry[k] = {"wrong_among_decided": float(u.wrong.mean() / max(u.decided.mean(), 1e-12)),
                                "coverage": float(u.decided.mean()), "measurements": float(u.measurements.mean()),
                                "abstained": float(u.abstained.mean())}
                entry["P0"] = {"wrong_among_decided": _conditional(full[max(grid)]), "coverage": base_cov}
                result["results"][f"{dataset}|{arm}|alpha={alpha}"] = entry
    (out / "posthoc_binding_alpha.json").write_text(json.dumps(result, indent=1, default=float), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("run", "analyse", "posthoc"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.command == "posthoc":
        print(json.dumps(posthoc_binding_alpha(), indent=1, default=float)[:4000])
        return
    if args.command == "run":
        run(args.workers)
    print(json.dumps(analyse(), indent=1, default=float)[:6000])


if __name__ == "__main__":
    main()
