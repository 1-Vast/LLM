"""Dual-core v2 analyses: repaired risk control by design, calibration, risk ranking, policies and world effects.

File summary
- Path: research/dual_core_v2/analysis.py
- Purpose: every scored quantity of `protocol.json`, computed from traces (block 7's or the v2 runs').
- Core points:
  - Designs give, per test fold f, the calibration episodes and the test episodes of one arm:
    - `block7_crossfit`: calibration = block 7's traces of the other folds (their models saw f);
    - `split`: calibration = M(f, c) on fold c, test = M(f, c) on fold f (one frozen process);
    - `nested_crossfit`: calibration = M(f, g) on g for all g != f; test = the mean over M(f, g) on f.
  - Conditional risk is NaN when no decision is made; bootstrap intervals skip NaN draws and report
    how many were undefined.
  - Unit-cluster bootstrap everywhere (10,000 draws, seed 20260928), units as protocol v2.1.
- Interfaces: `episode_table`, `design_roles`, `certify_design`, `summarise`, `risk_ranking`,
  `platt_crossfit`, `load_runs`
- Depends on: risk_control.py, arms.py, research/dual_core (agent, e2)
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import risk_control as RC

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "outputs/dual_core_v2_20260928/runs"
SEED = 20260928
DRAWS = 10_000
FOLDS = (0, 1, 2, 3, 4)


def protocol() -> dict:
    return json.loads((ROOT / "research/dual_core_v2/protocol.json").read_text(encoding="utf-8"))


def candidates() -> list:
    return [0.0025, 0.005, 0.01, 0.015, 0.02, 0.03, 0.04, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0]


# ------------------------------------------------------------------------------------ loading
def load_runs(runs: Path = RUNS, parts=("traces",)) -> dict:
    out = {p: [] for p in parts}
    out["meta"] = []
    for meta in sorted(runs.glob("*.json")):
        base = str(meta)[:-5]
        m = json.loads(meta.read_text(encoding="utf-8"))
        out["meta"].append(m)
        for p in parts:
            with gzip.open(f"{base}.{p}.jsonl.gz", "rt", encoding="utf-8") as fh:
                rows = [json.loads(line) for line in fh]
            if p == "ablation":                      # ablation rows carry their job's model and dataset
                rows = [dict(r, model=[m["job"][2], m["job"][3]], dataset=m["job"][0], tier=m["job"][1]) for r in rows]
            out[p] += rows
    return out


def model_id(trace) -> str:
    m = trace.get("model")
    return "m" + "".join(map(str, sorted(m))) if m else f"block7_f{trace['fold']}"


# ------------------------------------------------------------------------------------ tables
def step_risk(note, measure: str):
    """A step's recorded risk. 'step' goes through block 7's `note_risk`, which also covers block 2's
    reference notes (they record belief and per-hypothesis p_wrong, not `risk_forecast`)."""
    from research.dual_core import agent as AG
    if measure == "step":
        return AG.note_risk(note or {})
    value = (note or {}).get({"plan": "p_wrong_plan", "plan_upper": "p_wrong_upper_plan"}[measure])
    return None if value is None else float(value)


def truncate(trace, truth, threshold, measure="step") -> dict:
    """Stop-only outcome at `threshold`: steps run while the chosen action's risk is <= threshold."""
    kept, abstained = [], False
    for step in trace["steps"]:
        risk = step_risk(step.get("note"), measure)
        if risk is not None and risk > threshold:
            abstained = True
            break
        kept.append(step)
    eliminated = set(kept[-1]["eliminated"]) if kept else set()
    decided = bool(eliminated)
    return {"decided": decided, "wrong": truth in eliminated, "correct": decided and truth not in eliminated,
            "abstained": abstained, "measurements": len(kept)}


def episode_table(traces, threshold, measure="step") -> pd.DataFrame:
    """One row per episode: the stop-only outcome at `threshold` on risk `measure` (None = P0)."""
    rows = []
    for t in traces:
        o = truncate(t, t["truth"], threshold, measure) if threshold is not None else _no_truncation(t)
        rows.append({"fold": t["fold"], "unit": str(t["unit"]), "tier": t["tier"], "model": model_id(t),
                     "episode": (t["compound"], t["h1"], t["h2"]),
                     **{k: o[k] for k in ("decided", "wrong", "correct", "abstained", "measurements")}})
    return pd.DataFrame(rows)


def _no_truncation(t) -> dict:
    steps = t["steps"]
    eliminated = set(steps[-1]["eliminated"]) if steps else set()
    return {"decided": bool(eliminated), "wrong": t["truth"] in eliminated,
            "correct": bool(eliminated) and t["truth"] not in eliminated, "abstained": False,
            "measurements": len(steps)}


# ------------------------------------------------------------------------------------ designs
def design_roles(design: str, f: int):
    """[(calibration model id, calibration fold)], [(test model id, test fold)] for test fold f."""
    if design == "block7_crossfit":
        return [(f"block7_f{g}", g) for g in FOLDS if g != f], [(f"block7_f{f}", f)]
    if design == "split":
        c = (f + 1) % 5
        m = "m" + "".join(map(str, sorted((f, c))))
        return [(m, c)], [(m, f)]
    if design == "nested_crossfit":
        cal = [("m" + "".join(map(str, sorted((f, g)))), g) for g in FOLDS if g != f]
        return cal, [(m, f) for m, _ in cal]
    raise ValueError(design)


def _select(frame, roles):
    keep = np.zeros(len(frame), bool)
    for m, fold in roles:
        keep |= ((frame.model == m) & (frame.fold == fold)).to_numpy()
    return frame[keep]


def certify_design(traces, design: str, *, measure="step", method="betting", alpha=0.05, delta=0.1, rho=0.5):
    """Per test fold: the certificate from calibration and the test episodes of the chosen policy."""
    grid = candidates()
    tables = {lam: episode_table(traces, lam, measure) for lam in grid}
    out = {"folds": {}, "test": [], "plugin_test": []}
    for f in FOLDS:
        cal_roles, test_roles = design_roles(design, f)
        cal = {lam: _select(tables[lam], cal_roles) for lam in grid}
        if cal[1.0].empty:
            out["folds"][f] = {"status": "no_calibration_episodes"}
            continue
        units = sorted(cal[1.0].unit.unique())
        losses = {lam: RC.unit_losses(cal[lam], units) for lam in grid}
        cert = RC.certify(losses, losses[1.0], alpha=alpha, delta=delta, rho=rho, method=method, reference_key=1.0)
        plug, plug_status = RC.plugin_select(losses, losses[1.0], alpha=alpha, rho=rho)
        test = {lam: _select(tables[lam], test_roles) for lam in grid}
        chosen = RC.apply_policy(test, cert.policy)
        plugin = RC.apply_policy(test, plug)
        out["folds"][f] = {**cert.payload(), "calibration_units": len(units),
                           "plugin_policy": plug, "plugin_status": plug_status,
                           "test_units": int(test[1.0].unit.nunique())}
        out["test"].append(chosen.assign(test_fold=f))
        out["plugin_test"].append(plugin.assign(test_fold=f))
    out["test"] = pd.concat(out["test"], ignore_index=True) if out["test"] else pd.DataFrame()
    out["plugin_test"] = pd.concat(out["plugin_test"], ignore_index=True) if out["plugin_test"] else pd.DataFrame()
    return out


# ------------------------------------------------------------------------------------ summaries
def unit_means(frame: pd.DataFrame, cols=("wrong", "decided", "correct", "abstained", "measurements")) -> pd.DataFrame:
    """Unit means; with several models on the same unit (nested cross-fit test), models are averaged first."""
    return frame.groupby("unit")[list(cols)].mean()


def summarise(frame: pd.DataFrame, rng=None, draws=DRAWS) -> dict:
    if frame.empty:
        return {"episodes": 0}
    u = unit_means(frame.assign(**{c: frame[c].astype(float) for c in ("wrong", "decided", "correct", "abstained")}))
    rng = rng or np.random.default_rng(SEED)
    idx = rng.integers(len(u), size=(draws, len(u)))
    w, d = u.wrong.to_numpy()[idx].mean(1), u.decided.to_numpy()[idx].mean(1)
    cond = np.where(d > 0, w / np.where(d > 0, d, 1.0), np.nan)
    risk = RC.conditional_risk(u.wrong, u.decided)
    return {"units": int(len(u)), "episodes": int(len(frame)), "coverage": float(u.decided.mean()),
            "coverage_ci": np.quantile(d, [0.025, 0.975]).tolist(),
            "wrong_per_episode": float(u.wrong.mean()), "correct": float(u.correct.mean()),
            "abstained": float(u.abstained.mean()), "measurements": float(u.measurements.mean()),
            "wrong_among_decided": None if np.isnan(risk) else risk,
            "wrong_among_decided_ci": (np.nanquantile(cond, [0.025, 0.975]).tolist()
                                       if np.isfinite(cond).any() else None),
            "undefined_draws": int(np.isnan(cond).sum())}


def paired_difference(a: pd.DataFrame, b: pd.DataFrame, metric: str, rng=None, draws=DRAWS) -> dict:
    """a - b on the same units; metric 'wrong_among_decided' is a ratio of unit means."""
    ua, ub = unit_means(a.astype({c: float for c in ("wrong", "decided", "correct", "abstained")})), \
        unit_means(b.astype({c: float for c in ("wrong", "decided", "correct", "abstained")}))
    units = sorted(set(ua.index) & set(ub.index))
    ua, ub = ua.reindex(units), ub.reindex(units)
    rng = rng or np.random.default_rng(SEED)
    idx = rng.integers(len(units), size=(draws, len(units)))

    def stat(u):
        if metric == "wrong_among_decided":
            w, d = u.wrong.to_numpy()[idx].mean(1), u.decided.to_numpy()[idx].mean(1)
            return np.where(d > 0, w / np.where(d > 0, d, 1.0), np.nan)
        return u[metric].to_numpy()[idx].mean(1)

    diff = stat(ua) - stat(ub)
    point = (RC.conditional_risk(ua.wrong, ua.decided) - RC.conditional_risk(ub.wrong, ub.decided)
             if metric == "wrong_among_decided" else float(ua[metric].mean() - ub[metric].mean()))
    ok = np.isfinite(diff)
    return {"difference": None if not np.isfinite(point) else float(point),
            "ci": np.quantile(diff[ok], [0.025, 0.975]).tolist() if ok.any() else None,
            "undefined_draws": int((~ok).sum()), "units": len(units)}


# ------------------------------------------------------------------------------------ risk ranking
def step_table(traces) -> pd.DataFrame:
    rows = []
    for t in traces:
        before = set()
        for i, s in enumerate(t["steps"]):
            note = s.get("note") or {}
            now = set(s["eliminated"]) - before
            rows.append({"arm": t["arm"], "dataset": t["dataset"], "tier": t["tier"], "fold": t["fold"],
                         "unit": str(t["unit"]), "model": model_id(t), "step": i,
                         "risk_step": step_risk(note, "step"), "risk_plan": note.get("p_wrong_plan"),
                         "risk_plan_upper": note.get("p_wrong_upper_plan"),
                         "wrong": t["truth"] in now, "eliminating": bool(now), "prompts": note.get("prompts")})
            before |= set(s["eliminated"])
    return pd.DataFrame(rows)


def _auroc(score, y):
    from scipy.stats import rankdata
    score, y = np.asarray(score, float), np.asarray(y, bool)
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0:
        return np.nan
    r = rankdata(score)
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def risk_ranking(steps: pd.DataFrame, score: str, rng=None, draws=2000) -> dict:
    """AUROC and average precision of `score` for a wrong elimination, with a unit-cluster bootstrap."""
    from sklearn.metrics import average_precision_score
    s = steps.dropna(subset=[score])
    if s.wrong.sum() == 0:
        return {"steps": int(len(s)), "events": 0}
    rng = rng or np.random.default_rng(SEED)
    groups = {u: g.index.to_numpy() for u, g in s.groupby("unit")}
    units = list(groups)
    boots = []
    for _ in range(draws):
        pick = np.concatenate([groups[units[i]] for i in rng.integers(len(units), size=len(units))])
        boots.append(_auroc(s.loc[pick, score], s.loc[pick, "wrong"]))
    return {"steps": int(len(s)), "events": int(s.wrong.sum()), "event_units": int(s[s.wrong].unit.nunique()),
            "units": len(units), "auroc": _auroc(s[score], s.wrong), "auroc_ci": np.nanquantile(boots, [0.025, 0.975]).tolist(),
            "average_precision": float(average_precision_score(s.wrong, s[score])), "event_rate": float(s.wrong.mean())}
