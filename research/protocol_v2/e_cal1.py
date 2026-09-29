"""E-CAL1: wrong-elimination calibration on the actions each arm selected, per step and per episode.

File summary
- Path: research/protocol_v2/e_cal1.py
- Purpose: test whether the world model's wrong-elimination forecasts, or a registered bound on
  them, cover the observed rate on selected actions across studies (`protocol_v2_1.json`,
  experiment E-CAL1; gate committed in `research/gated_plan/registry.json` at c3d2345). Protocol v2
  calibrated the belief planner's steps only, and its stop gate passed with a bound 10-35 times the
  observed rate.
- Core points:
  - Items come from the E-DATA1 v2.1 records. `belief` and `myopic_edv` record, per executed step,
    their forecast for each hypothesis. `fixed` chooses without a forecast, so its steps get the
    same fold's `ReferenceWorld` forecast post hoc (evaluation side; no truth enters the forecast).
    `safe` is reported through `fixed` when its executed sequences are identical.
  - A step item is an executed, valid (QC-passed) measurement: the forecast is the probability,
    under the true hypothesis, of the reading that removes it; the outcome is whether it did.
  - Methods and strata are `calibration.py`'s (raw, planner Jeffreys upper, Platt, hierarchical
    kappa 20 and its upper bound, discounted lambda 0.5), fitted leave-one-study-out (SciPlex3 to
    L1000 and the reverse), per arm.
  - Gate: a bound passes on a target if it covers the observed rate overall and in >= 95% of
    strata with >= 20 items, with no stratum significantly above it, and its mean is at most
    3 times the observed rate. It must pass on both targets.
  - Episode level, among decided episodes: the conditional forecast
    P(wrong elimination) / P(any elimination), accumulated over executed steps with stop-at-first-
    elimination, against the observed wrong share. The protocol text's unconditional form
    1 - prod(1 - p_wrong) over episodes with a valid step is reported beside it.
- Run: python -m research.protocol_v2.e_cal1
- Interfaces: `step_items`, `fixed_forecasts`, `episode_items`, `analyse`, `main`
- Depends on: calibration.py, e_data1.py, tasks_v21.py, research/belief_planning (world model)
"""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.belief_planning.planner import _upper as planner_upper
from research.external_validation import statistics as S

from . import calibration as CB
from . import contracts as K
from .e_data1 import OUT as E_DATA1

C = K.T.C
OUT = E_DATA1.parent / "e_cal1"
ARMS = ("belief", "myopic_edv", "fixed")
INFORMATIVE_RATIO = 3.0


def _records(arms) -> list:
    rows = []
    for path in sorted((E_DATA1 / "scored").glob("*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            rows.extend(r for r in (json.loads(line) for line in fh) if r["arm"] in arms)
    return rows


def fixed_forecasts(records: list) -> dict:
    """Post-hoc `ReferenceWorld` forecasts for fixed-arm steps: (task, compound, h1, h2, step) -> branch dict."""
    from research.belief_planning import arms as BA
    from research.belief_planning import world as W

    from . import tasks_v21 as V
    by_task: dict = {}
    for r in records:
        by_task.setdefault((r["dataset"], str(r["tier"]), int(r["fold"])), []).append(r)
    out = {}
    for (dataset, tier, fold), group in sorted(by_task.items()):
        data, ctx, setting, design = V.load(dataset, tier, fold)
        comp = data.compounds.drop_duplicates("compound").set_index("compound")
        heldout = set(comp.index[comp.fold == fold])
        view = K.public_view(ctx, heldout, training_compounds=V.training_compounds(ctx, fold), design=design)
        world = BA.world_for(view, "on", "true")
        for r in group:
            history = []
            for i, s in enumerate(r["steps"]):
                key = tuple(s["key"])
                forecast = world.forecast(key, r["h1"], r["h2"], r["compound"], tuple(history))
                if forecast.refusal is None:
                    out[(dataset, tier, fold, r["compound"], r["h1"], r["h2"], i)] = {
                        b.hypothesis: {"support": b.support,
                                       "p_correct": b.probabilities.get(W.MATCH_H1 if b.hypothesis == r["h1"] else W.MATCH_H2, 0.0),
                                       "p_wrong": b.probabilities.get(W.MATCH_H2 if b.hypothesis == r["h1"] else W.MATCH_H1, 0.0)}
                        for b in forecast.branches}
                history.append((key, W.label_of(s["outcome"] if s["qc"] else "quality_failed")))
    return out


def _prediction(r, i, s, posthoc):
    note = s.get("note") or {}
    pred = note.get("prediction_by_hypothesis")
    if pred is None and posthoc is not None:
        pred = posthoc.get((r["dataset"], str(r["tier"]), int(r["fold"]), r["compound"], r["h1"], r["h2"], i))
    return pred


def step_items(records: list, arm: str, posthoc=None) -> pd.DataFrame:
    rows = []
    for r in records:
        if r["arm"] != arm:
            continue
        truth = r["score"]["truth"]
        for i, s in enumerate(r["steps"]):
            if s.get("lifecycle") != "measured_valid":
                continue
            pred = (_prediction(r, i, s, posthoc) or {}).get(truth)
            if not pred:
                continue
            outcome = s["outcome"]
            wrong = (outcome == "eliminate_a" and truth == r["h1"]) or (outcome == "eliminate_b" and truth == r["h2"])
            support = pred.get("support")
            rows.append({"arm": arm, "study": r["dataset"], "tier": str(r["tier"]), "unit": str(r["unit"]),
                         "compound": r["compound"], "step": i, "line": s["key"][0],
                         "p_wrong": float(pred["p_wrong"]), "p_correct": float(pred["p_correct"]), "support": support,
                         "y_wrong": float(wrong), "support_bin": CB.support_bin(support),
                         "novelty_bin": CB.novelty_bin(r.get("max_train_tanimoto")),
                         "planner_upper": planner_upper(float(pred["p_wrong"]), int(support or 0))})
    out = pd.DataFrame(rows)
    if len(out):
        out["stratum"] = out.support_bin + "|" + out.novelty_bin + "|step" + out.step.astype(str)
    return out


def episode_items(records: list, arm: str, posthoc=None) -> pd.DataFrame:
    rows = []
    for r in records:
        if r["arm"] != arm:
            continue
        truth = r["score"]["truth"]
        reach, pw, pc, unconditional, valid, complete = 1.0, 0.0, 0.0, 1.0, 0, True
        for i, s in enumerate(r["steps"]):
            if s.get("lifecycle") != "measured_valid":
                continue
            pred = (_prediction(r, i, s, posthoc) or {}).get(truth)
            if not pred:
                complete = False
                break
            valid += 1
            pw += reach * float(pred["p_wrong"])
            pc += reach * float(pred["p_correct"])
            reach *= max(0.0, 1.0 - float(pred["p_wrong"]) - float(pred["p_correct"]))
            unconditional *= 1.0 - float(pred["p_wrong"])
        if not valid or not complete:
            continue
        final = r["score"]["final"]
        rows.append({"arm": arm, "study": r["dataset"], "unit": str(r["unit"]), "decided": final in ("correct", "wrong"),
                     "y_wrong": float(final == "wrong"), "conditional": pw / (pw + pc) if pw + pc > 0 else float("nan"),
                     "unconditional": 1.0 - unconditional})
    return pd.DataFrame(rows)


def _gate(results: dict, method: str) -> dict:
    checks = {}
    for target, r in results.items():
        m = r["methods"][method]
        informative = m["mean"] <= INFORMATIVE_RATIO * max(r["observed"], 1e-12)
        checks[target] = {"overall_covered": m["overall_covered"], "strata_coverage": m["strata_coverage"],
                          "strata_significantly_violated": m["strata_significantly_violated"],
                          "mean_bound_over_observed": m["mean"] / max(r["observed"], 1e-12),
                          "informative": bool(informative),
                          "passes": bool(m["overall_covered"] and (m["strata_coverage"] is None or m["strata_coverage"] >= 0.95)
                                         and m["strata_significantly_violated"] == 0 and informative)}
    return {"method": method, "targets": checks, "passes": all(c["passes"] for c in checks.values())}


def _episode_summary(frame: pd.DataFrame) -> dict:
    out = {}
    for study, g in frame.groupby("study"):
        decided = g[g.decided]
        k, n = float(decided.y_wrong.sum()), len(decided)
        cond = float(decided.conditional.mean()) if n else float("nan")
        unc_obs, unc_fc = float(g.y_wrong.mean()), float(g.unconditional.mean())
        out[study] = {"decided": n, "units": int(decided.unit.nunique()), "observed_selective_risk": k / n if n else None,
                      "observed_wilson95": [CB._wilson_lower(k, n), S.wilson_upper(k, n)] if n else None,
                      "forecast_conditional": cond, "observed_over_forecast": (k / n) / cond if n and cond > 0 else None,
                      "all_measured_episodes": int(len(g)), "observed_wrong_all": unc_obs,
                      "forecast_unconditional": unc_fc,
                      "observed_over_forecast_unconditional": unc_obs / unc_fc if unc_fc > 0 else None}
    return out


def analyse(out: Path = OUT) -> dict:
    records = _records(set(ARMS) | {"safe"})
    fixed_seq = {(r["dataset"], r["tier"], r["fold"], r["compound"], r["h1"], r["h2"]): [s["action"] for s in r["steps"]]
                 for r in records if r["arm"] == "fixed"}
    safe_seq = {(r["dataset"], r["tier"], r["fold"], r["compound"], r["h1"], r["h2"]): [s["action"] for s in r["steps"]]
                for r in records if r["arm"] == "safe"}
    safe_identical = sum(fixed_seq.get(k) == v for k, v in safe_seq.items())
    posthoc = fixed_forecasts([r for r in records if r["arm"] == "fixed"])
    results = {"safe_sequences_identical_to_fixed": [safe_identical, len(safe_seq)], "arms": {}}
    for arm in ARMS:
        items = step_items(records, arm, posthoc if arm == "fixed" else None)
        loso = {}
        for target, source in (("l1000", "sciplex3"), ("sciplex3", "l1000")):
            src, tgt = items[items.study == source], items[items.study == target]
            if len(src) < 20 or len(tgt) < 20:
                loso[target] = {"status": "too_few_items", "n_source": int(len(src)), "n_target": int(len(tgt))}
                continue
            model = CB.fit(src)
            loso[target] = {"source": source, **CB.evaluate(tgt, CB.predict(model, tgt))}
        entry = {"step_items": int(len(items)), "loso": loso}
        if all("methods" in v for v in loso.values()):
            entry["gates"] = {m: _gate(loso, m) for m in CB.UPPER}
            entry["any_bound_passes"] = any(g["passes"] for g in entry["gates"].values())
        entry["episodes"] = _episode_summary(episode_items(records, arm, posthoc if arm == "fixed" else None))
        results["arms"][arm] = entry
    results["verdict"] = ("PASS" if any(a.get("any_bound_passes") for a in results["arms"].values()) else "FAIL")
    out.mkdir(parents=True, exist_ok=True)
    (out / "analysis.json").write_bytes(json.dumps(results, indent=1, default=float).encode("utf-8") + b"\n")
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    results = analyse(Path(args.out))
    print("safe identical to fixed:", results["safe_sequences_identical_to_fixed"])
    for arm, entry in results["arms"].items():
        print(f"== {arm}: {entry['step_items']} step items")
        for target, r in entry["loso"].items():
            if "methods" not in r:
                print("  ", target, r)
                continue
            print(f"   {target} <- {r['source']}: n {r['n']} observed {r['observed']:.4f} ",
                  {m: round(v["mean"], 4) for m, v in r["methods"].items()})
        for m, g in (entry.get("gates") or {}).items():
            print("   gate", m, g["passes"], {t: (c["overall_covered"], c["strata_coverage"], c["strata_significantly_violated"],
                                                  round(c["mean_bound_over_observed"], 2)) for t, c in g["targets"].items()})
        for study, e in entry["episodes"].items():
            print(f"   episodes {study}: decided {e['decided']} risk {e['observed_selective_risk']} forecast "
                  f"{e['forecast_conditional']:.4f} ratio {e['observed_over_forecast']}; unconditional ratio "
                  f"{e['observed_over_forecast_unconditional']}")
    print("verdict", results["verdict"])


if __name__ == "__main__":
    main()
