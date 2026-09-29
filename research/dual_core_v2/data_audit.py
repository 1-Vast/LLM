"""Data-bottleneck audit: independent units, effective sizes, detection, quality, confounding, support and power.

File summary
- Path: research/dual_core_v2/data_audit.py
- Purpose: separate "a poor model", "a weak risk-ranking signal", "an uninformative task",
  "insufficient power" and "a conservative bound" with numbers from the registered data and traces.
- Core points:
  - Counts are by independent unit (SciPlex3 InChIKey connectivity block, L1000 identity/scaffold
    component), never by cell, row, episode or candidate action.
  - Quality scores are reported per dataset and never pooled: SciPlex3's is a split-half Pearson
    correlation of pseudobulk shifts, L1000's is `cc_q75` (replicate consensus quantile).
  - Power is post hoc and specific: for one policy's empirical unit-level loss distribution, the
    probability that a single-candidate test (and the Holm-adjusted one) certifies at alpha, as a
    function of the number of units drawn from that distribution. It is not a project-wide bound:
    a different task, candidate, loss variance or test changes it.
- Interfaces: `dataset_audit`, `trace_audit`, `power_curve`; CLI `python -m research.dual_core_v2.data_audit TRACES.pkl OUT.json`
- Depends on: research/protocol_v2 loaders, risk_control.py, analysis.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import analysis as A
from . import risk_control as RC

ROOT = Path(__file__).resolve().parents[2]


def _cramers_v(a, b) -> float:
    from scipy.stats import chi2_contingency
    table = pd.crosstab(a, b)
    if min(table.shape) < 2:
        return float("nan")
    chi2 = chi2_contingency(table, correction=False)[0]
    n = table.values.sum()
    return float(np.sqrt(chi2 / (n * (min(table.shape) - 1))))


def dataset_audit() -> dict:
    from research.belief_planning import tasks as T
    from research.protocol_v2 import tasks_v21 as TV
    C, LP = TV.C, TV.LP
    out = {}
    for ds in ("sciplex3", "l1000"):
        data = C.load() if ds == "sciplex3" else LP.load()
        comp = data.compounds.drop_duplicates("compound").set_index("compound")
        units = T.units(ds)[T.UNIT[ds]].astype(str)
        cond = data.conditions.copy()
        cond["unit"] = cond.compound.map(units)
        cond["klass"] = cond.compound.map(comp.klass)
        if ds == "sciplex3":
            spec = C.load_protocol()
            detected = C.detected_flags(data, C.detection_null(data, spec))
            batch = cond.plate_rep1.astype(str)
        else:
            detected = cond.detected.to_numpy(bool)
            batch = cond.batch.astype(str)
        qc = np.array([C.qc_passed(data, i) for i in range(len(cond))])
        q = np.asarray(data.agreement, float)
        labelled = cond.klass.notna()
        per_class_units = cond[labelled].groupby("klass").unit.nunique().sort_values()
        out[ds] = {
            "rows": int(len(cond)), "compounds": int(cond.compound.nunique()), "units": int(cond.unit.nunique()),
            "labelled_units": int(cond[labelled].unit.nunique()), "classes": int(per_class_units.size),
            "units_per_class_quantiles": per_class_units.quantile([0, 0.25, 0.5, 0.75, 1]).to_dict(),
            "classes_with_fewer_than_3_units": int((per_class_units < 3).sum()),
            "qc_pass_rate": float(qc.mean()), "detected_rate_among_qc_pass": float(detected[qc].mean()),
            "quality_kind": "split-half Pearson of pseudobulk shifts" if ds == "sciplex3" else "cc_q75 (replicate consensus)",
            "quality_quantiles": {str(k): float(v) for k, v in pd.Series(q[np.isfinite(q)]).quantile([0.1, 0.25, 0.5, 0.75, 0.9]).items()},
            "quality_missing": int((~np.isfinite(q)).sum()),
            "rows_per_unit_median": float(cond.groupby("unit").size().median()),
            "conditions": int(cond[["cell_line", "time", "dose"]].drop_duplicates().shape[0]),
            "batch_class_cramers_v": _cramers_v(batch[labelled & qc], cond.klass[labelled & qc]),
            "batch_count": int(batch.nunique()),
            "largest_batch_share_per_class_median": float(
                cond[labelled].assign(b=batch[labelled]).groupby("klass").b.agg(lambda s: s.value_counts(normalize=True).iloc[0]).median()),
            "detected_by_class_range": [float(x) for x in pd.Series(detected[qc & labelled.to_numpy()]).groupby(
                cond.klass[qc & labelled.to_numpy()].to_numpy()).mean().quantile([0, 1]).tolist()],
        }
    return out


def trace_audit(traces) -> dict:
    out = {}
    df = A.episode_table(traces, None)
    steps = A.step_table(traces)
    for (ds, arm), g in df.assign(dataset=[t["dataset"] for t in traces], arm=[t["arm"] for t in traces]).groupby(["dataset", "arm"]):
        if arm != "reference":
            continue
        s = steps[(steps.dataset == ds) & (steps.arm == arm)]
        u = g.groupby("unit")[["decided", "wrong"]].mean()
        ev = s[s.wrong].groupby("unit").size().sort_values(ascending=False)
        labels = [st["outcome"] for t in traces if t["dataset"] == ds and t["arm"] == arm for st in t["steps"]]
        out[ds] = {"episodes": int(len(g)), "units": int(g.unit.nunique()),
                   "episodes_per_unit_quantiles": g.groupby("unit").size().quantile([0, 0.5, 0.9, 1]).to_dict(),
                   "units_ever_deciding": int((u.decided > 0).sum()), "coverage_unit_mean": float(u.decided.mean()),
                   "no_measurement_episodes": int((g.measurements == 0).sum()),
                   "wrong_events": int(s.wrong.sum()), "units_with_wrong_events": int(len(ev)),
                   "top5_unit_share_of_events": float(ev.head(5).sum() / max(ev.sum(), 1)),
                   "events_by_fold": s[s.wrong].groupby("fold").size().to_dict(),
                   "executed_step_readings": pd.Series(labels).value_counts(normalize=True).round(4).to_dict(),
                   "tiers": {t: {"episodes": int(len(gt)), "units": int(gt.unit.nunique()),
                                 "coverage": float(gt.groupby("unit").decided.mean().mean())}
                             for t, gt in g.groupby("tier")}}
    return out


def power_curve(unit_losses: RC.UnitLosses, *, alpha=0.05, delta=0.1, sizes=(100, 200, 400, 800, 1600, 3200),
                reps=200, family=15, seed=20260928) -> dict:
    """P(certify) when n units are drawn with replacement from one policy's empirical unit losses."""
    rng = np.random.default_rng(seed)
    z = (unit_losses.wrong - alpha * unit_losses.decided + alpha) / (1 + alpha)
    t = alpha / (1 + alpha)
    out = {"risk": unit_losses.risk(), "coverage": unit_losses.coverage(), "z_mean": float(z.mean()),
           "z_sd": float(z.std()), "t": t, "units_in_sample": int(len(z)), "curve": {}}
    for n in sizes:
        hits = {"betting_single": 0, "betting_holm": 0, "hb_single": 0, "hb_holm": 0}
        for _ in range(reps):
            x = z[rng.integers(len(z), size=n)]
            pb = RC.betting_pvalue(x, t, delta=delta)
            ph = RC.hb_pvalue(float(x.mean()), n, t)
            hits["betting_single"] += pb <= delta
            hits["betting_holm"] += pb <= delta / family
            hits["hb_single"] += ph <= delta
            hits["hb_holm"] += ph <= delta / family
        out["curve"][n] = {k: v / reps for k, v in hits.items()}
    return out


def main(traces_path: str, out_path: str) -> None:
    import pickle
    traces = pickle.load(open(traces_path, "rb"))
    result = {"status": "post hoc audit on exposed development data", "datasets": dataset_audit(),
              "traces_block7": trace_audit(traces), "power_post_hoc": {}}
    for ds, lam in (("sciplex3", 0.01), ("sciplex3", 0.015), ("sciplex3", 1.0), ("l1000", 0.1), ("l1000", 1.0)):
        tr = [t for t in traces if t["dataset"] == ds and t["arm"] == "reference"]
        losses = RC.unit_losses(A.episode_table(tr, lam))
        result["power_post_hoc"][f"{ds}|reference|lambda={lam}"] = power_curve(losses)
    Path(out_path).write_text(json.dumps(result, indent=1, default=float), encoding="utf-8")
    print(json.dumps(result, indent=1, default=float)[:8000])


if __name__ == "__main__":
    sys.path[:0] = [str(ROOT), str(ROOT / "src")]
    main(sys.argv[1], sys.argv[2])
