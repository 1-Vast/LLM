"""Robust wrong-risk calibration across studies, and bounded-likelihood belief updates.

File summary
- Path: research/protocol_v2/calibration.py
- Purpose: measure whether the world model's wrong-elimination forecasts, and conservative bounds
  built on them, hold on a study they were not fitted on. Decide by a pre-registered gate whether
  the model may drive automatic stopping. Test whether a contamination-mixture observation model
  keeps the belief from collapsing onto the wrong hypothesis.
- Core points:
  - Items: every executed, QC-passed step of the current planner (`belief`). The forecast is the
    chosen action's probability, under the true hypothesis, of the reading that removes the true
    hypothesis; the outcome is whether it did.
  - Strata: reference support of the true branch (0-4, 5-9, 10-19, 20-49, 50+), structural
    novelty (nearest training Tanimoto < 0.30, 0.30-0.40, 0.40-0.60, >= 0.60, no structure), step
    (first or second measurement), study, cell line. Validator disagreement is not in the
    protocol-v1 records; protocol-v2 records carry the validator scores for it.
  - Methods, all fitted on the source study only:
    - `raw`: the forecast as issued.
    - `planner_upper`: the planner's own conservative bound (one-sided 95% Jeffreys bound on the
      branch's reference support), which is what a risk cap would act on.
    - `platt`: logistic recalibration of the forecast (ordinary calibration).
    - `hierarchical`: the stratum's wrong rate, partially pooled to the source's overall rate
      with `KAPPA` = 20 pseudo-observations (`statistics.MIN_CALIBRATION_SUPPORT`).
    - `hierarchical_upper`: the 95% quantile of that stratum's Beta posterior.
    - `discounted_upper`: the same with the source evidence discounted by half (a power prior,
      lambda = 0.5, fixed in advance), for study shift.
  - Leave-one-study-out: SciPlex3 -> L1000 Phase I and L1000 Phase I -> SciPlex3 are the
    development tests. GSE70138 (source: both development studies) is reported post hoc: its
    labels were opened once by protocol v1 and nothing here is tuned on them.
  - Gate (`stop_gate`): the model may drive a stop only if the planner's own bound covers the
    observed wrong rate on both development targets: overall, and in at least 95% of strata with
    20 or more items, with no stratum whose observed rate is significantly above the bound.
  - Belief updates: after a non-eliminating first reading, the posterior on the truth under
    P_eps(y|h) = (1 - eps) P(y|h) + eps / 5, for eps in `EPSILONS`. Log loss, and collapse
    (posterior on the truth below 0.1), chosen on the source and reported on the target.
- Run: python -m research.protocol_v2.calibration --out FILE
- Interfaces: `items`, `evaluate`, `stop_gate`, `belief_items`, `belief_update_table`, `main`
- Depends on: records.py, maestro.planning, research/external_validation/statistics.py, scipy
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta as beta_dist

from maestro.planning import _upper as planner_upper
from research.external_validation import statistics as S

from . import records as RC

KAPPA = S.MIN_CALIBRATION_SUPPORT
DISCOUNT = 0.5
MIN_STRATUM = 20
EPSILONS = (0.0, 0.02, 0.05, 0.1, 0.2, 0.3)
LABEL = {"eliminate_b": "profile_matches_h1", "eliminate_a": "profile_matches_h2",
         "ambiguous": "profile_unresolved", "undetected": "no_detectable_response"}
DEV = Path("outputs/belief_planning_20260927/registered/dev")
EXTERNAL = Path("outputs/belief_planning_20260927/external/records.jsonl.gz")


def support_bin(n) -> str:
    n = -1 if n is None or (isinstance(n, float) and np.isnan(n)) else int(n)
    for lo, hi, name in ((0, 4, "0-4"), (5, 9, "5-9"), (10, 19, "10-19"), (20, 49, "20-49")):
        if lo <= n <= hi:
            return name
    return "50+" if n >= 50 else "unknown"


def novelty_bin(t) -> str:
    if t is None or (isinstance(t, float) and np.isnan(t)):
        return "no_structure"
    return "<0.30" if t < 0.30 else "0.30-0.40" if t < 0.40 else "0.40-0.60" if t < 0.60 else ">=0.60"


def _features(path: Path) -> dict:
    if not path.is_file():
        return {}
    f = pd.read_csv(path)
    return {(str(r.tier), str(r.compound)): float(r.max_train_tanimoto) for r in f.itertuples()}


def items(frame: pd.DataFrame, features: dict) -> pd.DataFrame:
    """One row per executed QC-passed step with a forecast for the true hypothesis."""
    rows = []
    for r in frame.itertuples():
        truth = r.truth
        for i, s in enumerate(r.steps):
            note = s.get("note") or {}
            pred = (note.get("prediction_by_hypothesis") or {}).get(truth)
            if not pred or not s["qc"]:
                continue
            outcome = s["outcome"]
            wrong = (outcome == "eliminate_a" and truth == r.h1) or (outcome == "eliminate_b" and truth == r.h2)
            correct = (outcome == "eliminate_b" and truth == r.h1) or (outcome == "eliminate_a" and truth == r.h2)
            support = pred.get("support")
            tanimoto = features.get((str(r.tier), str(r.compound)), float("nan"))
            rows.append({"study": r.dataset, "tier": r.tier, "unit": r.unit, "compound": r.compound, "step": i,
                         "line": s["key"][0], "p_wrong": float(pred["p_wrong"]), "p_correct": float(pred["p_correct"]),
                         "support": support, "y_wrong": float(wrong), "y_correct": float(correct),
                         "support_bin": support_bin(support), "novelty_bin": novelty_bin(tanimoto),
                         "planner_upper": planner_upper(float(pred["p_wrong"]), int(support or 0))})
    out = pd.DataFrame(rows)
    out["stratum"] = out.support_bin + "|" + out.novelty_bin + "|step" + out.step.astype(str)
    return out


# ------------------------------------------------------------------------------ methods
def fit(source: pd.DataFrame) -> dict:
    y, p = source.y_wrong.to_numpy(float), source.p_wrong.to_numpy(float)
    beta = S._newton(np.column_stack([np.ones(len(p)), S._logit(p)]), y, np.zeros(len(p)))
    parent = float(y.mean())
    strata = source.groupby("stratum").y_wrong.agg(["sum", "size"])
    return {"platt": None if beta is None else beta.tolist(), "parent": parent,
            "strata": {k: (float(v["sum"]), float(v["size"])) for k, v in strata.iterrows()}}


def _posterior(model: dict, stratum: str, discount: float = 1.0) -> tuple[float, float]:
    k, n = model["strata"].get(stratum, (0.0, 0.0))
    k, n = k * discount, n * discount
    theta = model["parent"]
    return k + KAPPA * theta + 0.5, n - k + KAPPA * (1 - theta) + 0.5


def predict(model: dict, target: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=target.index)
    out["raw"] = target.p_wrong
    out["planner_upper"] = target.planner_upper
    if model["platt"] is not None:
        a, b = model["platt"]
        out["platt"] = S._expit(a + b * S._logit(target.p_wrong.to_numpy(float)))
    else:
        out["platt"] = model["parent"]
    post = {s: _posterior(model, s) for s in target.stratum.unique()}
    disc = {s: _posterior(model, s, DISCOUNT) for s in target.stratum.unique()}
    out["hierarchical"] = [post[s][0] / sum(post[s]) for s in target.stratum]
    out["hierarchical_upper"] = [float(beta_dist.ppf(0.95, *post[s])) for s in target.stratum]
    out["discounted_upper"] = [float(beta_dist.ppf(0.95, *disc[s])) for s in target.stratum]
    return out


POINT = ("raw", "platt", "hierarchical")
UPPER = ("planner_upper", "hierarchical_upper", "discounted_upper")


def evaluate(target: pd.DataFrame, pred: pd.DataFrame) -> dict:
    y = target.y_wrong.to_numpy(float)
    out = {"n": int(len(y)), "units": int(target.unit.nunique()), "observed": float(y.mean()),
           "observed_wilson_upper95": S.wilson_upper(float(y.sum()), len(y)), "methods": {}}
    lower = _wilson_lower(float(y.sum()), len(y))
    for m in POINT + UPPER:
        p = pred[m].to_numpy(float)
        q = np.clip(p, 1e-6, 1 - 1e-6)
        entry = {"mean": float(p.mean()), "observed_over_forecast": float(y.mean() / max(p.mean(), 1e-12))}
        if m in POINT:
            entry.update({"brier": float(np.mean((p - y) ** 2)),
                          "log_loss": float(-np.mean(y * np.log(q) + (1 - y) * np.log(1 - q))),
                          "significantly_under": bool(lower > p.mean())})
        out["methods"][m] = entry
    strata = []
    for (stratum, study), g in target.assign(**{m: pred[m] for m in POINT + UPPER}).groupby(["stratum", "study"]):
        if len(g) < MIN_STRATUM:
            continue
        k, n = float(g.y_wrong.sum()), len(g)
        row = {"stratum": stratum, "study": study, "n": n, "units": int(g.unit.nunique()), "observed": k / n,
               "observed_wilson_lower95": _wilson_lower(k, n)}
        for m in POINT + UPPER:
            row[m] = float(g[m].mean())
        strata.append(row)
    out["strata"] = strata
    for m in UPPER:
        judged = [s for s in strata]
        covered = [s["observed"] <= s[m] + 1e-12 for s in judged]
        violated = [s["observed_wilson_lower95"] > s[m] for s in judged]
        out["methods"][m].update({
            "overall_covered": bool(y.mean() <= pred[m].mean() + 1e-12),
            "strata_judged": len(judged), "strata_coverage": float(np.mean(covered)) if judged else None,
            "strata_significantly_violated": int(sum(violated))})
    return out


def _wilson_lower(k: float, n: float, z: float = 1.959964) -> float:
    if n <= 0:
        return 0.0
    p = k / n
    centre = p + z * z / (2 * n)
    spread = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return float(max(0.0, (centre - spread) / (1 + z * z / n)))


def stop_gate(results: dict, method: str = "planner_upper") -> dict:
    """Pre-registered: the model may drive stops only if its bound holds on both development targets."""
    checks = {}
    for target in ("l1000", "sciplex3"):
        m = results["loso"][target]["methods"][method]
        checks[target] = {"overall_covered": m["overall_covered"],
                          "strata_coverage": m["strata_coverage"],
                          "strata_significantly_violated": m["strata_significantly_violated"],
                          "passes": bool(m["overall_covered"] and (m["strata_coverage"] or 0) >= 0.95
                                         and m["strata_significantly_violated"] == 0)}
    return {"method": method, "targets": checks, "allow_model_stop": all(c["passes"] for c in checks.values()),
            "rule": "overall observed <= mean bound, >= 95% of strata (n >= 20) covered, and no stratum "
                    "significantly above the bound, on both leave-one-study-out development targets"}


# ------------------------------------------------------------------------------ belief updates
def belief_items(frame: pd.DataFrame) -> pd.DataFrame:
    """First readings that did not end the episode: the likelihood under each hypothesis."""
    rows = []
    for r in frame.itertuples():
        if not r.steps:
            continue
        s = r.steps[0]
        label = LABEL.get(s["outcome"])
        pred = (s.get("note") or {}).get("prediction_by_hypothesis") or {}
        if not s["qc"] or s["eliminated"] or label not in ("profile_unresolved", "no_detectable_response"):
            continue
        if r.truth not in pred:
            continue
        other = r.h2 if r.truth == r.h1 else r.h1
        if other not in pred:
            continue
        rows.append({"study": r.dataset, "unit": r.unit, "p_truth": float(pred[r.truth]["probabilities"].get(label, 0.0)),
                     "p_other": float(pred[other]["probabilities"].get(label, 0.0))})
    return pd.DataFrame(rows)


def posterior_truth(b: pd.DataFrame, eps: float) -> np.ndarray:
    lt = (1 - eps) * b.p_truth.to_numpy(float) + eps / 5.0
    lo = (1 - eps) * b.p_other.to_numpy(float) + eps / 5.0
    total = lt + lo
    return np.where(total > 0, lt / np.maximum(total, 1e-300), 0.5)


def _belief_scores(b: pd.DataFrame, eps: float) -> dict:
    post = np.clip(posterior_truth(b, eps), 1e-12, 1.0)
    return {"eps": eps, "n": int(len(b)), "log_loss": float(-np.log(post).mean()),
            "brier": float(np.mean((1 - post) ** 2)), "collapse_rate": float(np.mean(post < 0.1)),
            "mean_posterior_truth": float(post.mean())}


def belief_update_table(beliefs: pd.DataFrame) -> dict:
    out = {"by_study": {}, "loso": {}}
    for study, g in beliefs.groupby("study"):
        out["by_study"][study] = [_belief_scores(g, e) for e in EPSILONS]
    for target, source in (("l1000", "sciplex3"), ("sciplex3", "l1000"), ("gse70138", None)):
        src = beliefs[beliefs.study != target] if source is None else beliefs[beliefs.study == source]
        src = src[src.study != "gse70138"]
        tgt = beliefs[beliefs.study == target]
        if src.empty or tgt.empty:
            continue
        chosen = min(EPSILONS, key=lambda e: _belief_scores(src, e)["log_loss"])
        out["loso"][target] = {"source": source or "sciplex3+l1000", "eps_chosen_on_source": chosen,
                               "target_at_eps0": _belief_scores(tgt, 0.0),
                               "target_at_chosen": _belief_scores(tgt, chosen)}
    return out


# ------------------------------------------------------------------------------ driver
def load_items(dev: Path = DEV, external: Path = EXTERNAL) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames, beliefs = [], []
    for path, features in ((dev, _features(dev / "compound_features.csv")),
                           (external, _features(external.parent / "compound_features.csv"))):
        if not Path(path).exists():
            continue
        frame = RC.load(path, ("belief",), keep_steps=True)
        frames.append(items(frame, features))
        beliefs.append(belief_items(frame))
    return pd.concat(frames, ignore_index=True), pd.concat(beliefs, ignore_index=True)


def run(all_items: pd.DataFrame, beliefs: pd.DataFrame) -> dict:
    results = {"loso": {}, "post_hoc_external": None, "items": int(len(all_items)),
               "items_by_study": all_items.study.value_counts().to_dict()}
    for target, source in (("l1000", "sciplex3"), ("sciplex3", "l1000")):
        model = fit(all_items[all_items.study == source])
        tgt = all_items[all_items.study == target]
        results["loso"][target] = {"source": source, **evaluate(tgt, predict(model, tgt))}
    ext = all_items[all_items.study == "gse70138"]
    if not ext.empty:
        model = fit(all_items[all_items.study.isin(("sciplex3", "l1000"))])
        results["post_hoc_external"] = {"source": "sciplex3+l1000", "status": "post hoc; labels opened once by "
                                        "protocol v1; nothing tuned on them", **evaluate(ext, predict(model, ext))}
    results["stop_gate"] = stop_gate(results)
    results["stop_gate_alternatives"] = {m: stop_gate(results, m)["allow_model_stop"] for m in UPPER}
    results["belief_updates"] = belief_update_table(beliefs)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    all_items, beliefs = load_items()
    results = run(all_items, beliefs)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_bytes(json.dumps(results, indent=1, default=float).encode("utf-8"))
    for target, r in results["loso"].items():
        print(target, "<-", r["source"], "n", r["n"], "observed", round(r["observed"], 4),
              {m: round(v["mean"], 4) for m, v in r["methods"].items()},
              {m: (r["methods"][m]["overall_covered"], r["methods"][m]["strata_coverage"],
                   r["methods"][m]["strata_significantly_violated"]) for m in UPPER})
    if results["post_hoc_external"]:
        r = results["post_hoc_external"]
        print("gse70138 (post hoc) n", r["n"], "observed", round(r["observed"], 4),
              {m: round(v["mean"], 4) for m, v in r["methods"].items()},
              {m: (r["methods"][m]["overall_covered"], r["methods"][m]["strata_coverage"]) for m in UPPER})
    print("stop gate:", results["stop_gate"]["allow_model_stop"], results["stop_gate_alternatives"])
    print("belief updates:", json.dumps(results["belief_updates"]["loso"], indent=None)[:1500])


if __name__ == "__main__":
    main()
