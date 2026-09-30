"""Cost curves, paired grouped uncertainty and chosen-action calibration from real replays."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/sparse_value/evaluation"
COSTS = (0.0, .005, .01, .02, .05, .1, .2)
SEED = 20260926
BASELINES = ("legacy_fallback", "fixed_fallback", "two_step", "fixed", "da_unconditioned")


def paired(frame, left, right, metric, cost):
    keys = ["compound", "h1", "h2"]
    a = frame[frame.policy == left].set_index(keys)
    b = frame[frame.policy == right].set_index(keys)
    if set(a.index) != set(b.index):
        raise ValueError(f"Unmatched episodes: {left}, {right}")
    a_value = a.utility - cost * a.measurements if metric == "net" else a[metric]
    b_value = b.utility - cost * b.measurements if metric == "net" else b[metric]
    delta = pd.DataFrame({"delta": a_value - b_value.reindex(a.index), "unit": a.unit})
    blocks = delta.groupby("unit").delta.agg(["sum", "size"]).to_numpy()
    draws = np.random.default_rng(SEED).integers(len(blocks), size=(2000, len(blocks)))
    boot = blocks[draws, 0].sum(axis=1) / blocks[draws, 1].sum(axis=1)
    return {"left": left, "right": right, "cost_per_measurement": cost, "metric": metric,
            "difference": float(delta.delta.mean()), "ci95": np.quantile(boot, [.025, .975]).tolist(),
            "units": len(blocks), "episodes": len(delta)}


def selected_calibration(records):
    rows = []
    for record in records:
        for step in record["steps"]:
            note = step.get("note") or {}
            branches = note.get("prediction_by_hypothesis", {})
            branch = branches.get(record["truth"])
            if not branch or not step["qc"]:
                continue
            correct_label = "eliminate_b" if record["truth"] == record["h1"] else "eliminate_a"
            wrong_label = "eliminate_a" if record["truth"] == record["h1"] else "eliminate_b"
            # The policy records canonical correct/wrong branch probabilities for calibration.
            if "p_correct" not in branch or "p_wrong" not in branch:
                continue
            rows.append({"dataset": record["dataset"], "tier": record["tier"], "policy": record["policy"],
                         "p_correct": branch["p_correct"], "p_wrong": branch["p_wrong"],
                         "correct": float(step["outcome"] == correct_label), "wrong": float(step["outcome"] == wrong_label)})
    result = []
    if not rows:
        return result
    frame = pd.DataFrame(rows)
    for (dataset, tier, policy), group in frame.groupby(["dataset", "tier", "policy"]):
        entry = {"dataset": dataset, "tier": tier, "policy": policy, "selected_valid_measurements": len(group)}
        for target in ("correct", "wrong"):
            p, y = group[f"p_{target}"].to_numpy(), group[target].to_numpy()
            bins = np.minimum((p * 10).astype(int), 9)
            ece = sum(float(np.mean(bins == b) * abs(np.mean(p[bins == b]) - np.mean(y[bins == b])))
                      for b in range(10) if np.any(bins == b))
            entry[target] = {"predicted": float(p.mean()), "observed": float(y.mean()), "brier": float(np.mean((p-y)**2)), "ece": ece}
        result.append(entry)
    return result


def main():
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    records = [json.loads(line) for name in sorted(manifest["files"])
               for line in (OUT / name).read_text(encoding="utf-8").splitlines()]
    frame = pd.DataFrame(records)
    if len(frame) != manifest["records"]:
        raise ValueError("Manifest count mismatch")
    frame["correct"] = (frame.final == "correct").astype(float)
    frame["wrong"] = frame.final.isin(("wrong", "exhausted")).astype(float)
    frame["deferred"] = (frame.final == "deferred").astype(float)
    rates, curves, comparisons, pareto, yields, batch_sensitivity = [], [], [], [], [], []
    lincs_conditions = pd.read_csv(ROOT / "outputs/sequence_audit_20260926/l1000/prepared/conditions.csv")
    first_batch = lincs_conditions[(lincs_conditions.cell_line == "A549") & (lincs_conditions.time == 6.0)].set_index("compound").batch
    for (dataset, tier), sub in frame.groupby(["dataset", "tier"]):
        means = sub.groupby("policy")[["correct", "wrong", "utility", "measurements", "days", "deferred"]].mean()
        for policy, values in means.iterrows():
            steps = sub[sub.policy == policy].steps
            neutral = [s for s in steps if s and s[0]["qc"] and s[0]["outcome"] in ("ambiguous", "undetected")]
            rates.append({"dataset": dataset, "tier": tier, "policy": policy,
                          "episodes": int((sub.policy == policy).sum()), **{k: float(v) for k,v in values.items()},
                          "neutral_first": len(neutral), "continued_after_neutral": sum(len(s) > 1 for s in neutral),
                          "stop_counts": {str(k): int(v) for k, v in sub[sub.policy == policy].stop.value_counts().items()}})
            dominated = [other for other, ov in means.iterrows() if other != policy
                         and ov.utility >= values.utility and ov.wrong <= values.wrong and ov.measurements <= values.measurements
                         and (ov.utility > values.utility or ov.wrong < values.wrong or ov.measurements < values.measurements)]
            pareto.append({"dataset": dataset, "tier": tier, "policy": policy, "dominated_by": dominated,
                           "on_empirical_frontier": not dominated})
        for cost in COSTS:
            name = f"sparse_{cost:g}"
            policies = [name, *BASELINES]
            if cost == .02:
                policies += ["marginal_0.02", "paired_only_0.02", "permuted_0.02"]
            for policy in policies:
                values = means.loc[policy]
                curves.append({"dataset": dataset, "tier": tier, "cost_per_measurement": cost, "policy": policy,
                               "net": float(values.utility - cost * values.measurements),
                               **{k: float(values[k]) for k in ("utility", "correct", "wrong", "measurements", "days")}})
            for baseline in ("fixed_fallback", "da_unconditioned", "fixed"):
                for metric in ("net", "utility", "correct", "wrong", "measurements", "days"):
                    comparisons.append({"dataset": dataset, "tier": tier, **paired(sub, name, baseline, metric, cost)})
                dc = float(means.loc[name, "correct"] - means.loc[baseline, "correct"])
                dm = float(means.loc[name, "measurements"] - means.loc[baseline, "measurements"])
                yields.append({"dataset": dataset, "tier": tier, "cost_per_measurement": cost, "left": name,
                               "right": baseline, "correct_difference": dc, "measurement_difference": dm,
                               "additional_correct_per_extra_assay": dc / dm if dm > 1e-12 and dc > 0 else None,
                               "interpretation": "extra assays add correct decisions" if dm > 1e-12 and dc > 0 else
                               "fewer or equal assays with no correctness loss" if dm <= 0 and dc >= 0 else "tradeoff; positive-gain-per-extra-assay ratio is not applicable"})
                if dataset == "l1000" and baseline in ("fixed_fallback", "da_unconditioned"):
                    batch_frame = sub.assign(unit=sub.compound.map(first_batch).fillna("unavailable"))
                    for metric in ("net", "wrong"):
                        batch_sensitivity.append({"dataset": dataset, "tier": tier, "unit": "A549_6h_batch_cohort",
                                                  **paired(batch_frame, name, baseline, metric, cost)})
            if cost == .02:
                for baseline in ("marginal_0.02", "paired_only_0.02", "permuted_0.02"):
                    for metric in ("net", "utility", "correct", "wrong", "measurements"):
                        comparisons.append({"dataset": dataset, "tier": tier, **paired(sub, name, baseline, metric, cost)})
        for metric in ("utility", "correct", "wrong", "measurements"):
            comparisons.append({"dataset": dataset, "tier": tier,
                                **paired(sub, "fixed_fallback", "legacy_fallback", metric, 0.0)})
    calibration = selected_calibration(records)
    summary = {"status": manifest["status"], "freeze": manifest["freeze"], "rates": rates, "cost_curves": curves,
               "paired_comparisons": comparisons, "empirical_pareto": pareto, "marginal_yield": yields,
               "selected_action_calibration": calibration, "batch_sensitivity": batch_sensitivity,
               "limits": ["These SciPlex3 and LINCS outcomes informed development; all results are exploratory replays.",
                          "Measurement prices are sensitivity assumptions in utility units, not inferred user preferences or currency.",
                          "Assay-days remain a hard budget and are reported separately; no claim of optimal economic price.",
                          "Paired 95% intervals cluster by LINCS chemical/scaffold component or SciPlex3 skeleton; shared plate dependence remains.",
                          "Selected-action calibration measures the policy's chosen distribution, not whole-menu calibration.",
                          "Empirical Pareto membership is descriptive, without uncertainty-adjusted dominance."]}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False), encoding="utf-8")
    lines = ["# Sparse-reference decision value on real data", "", manifest["status"], "",
             "Net value = correct - 2 × wrong - measurement price × assays. Prices are assumptions; every comparator is scored at the same price.", "",
             "|Dataset/tier|Policy|Correct|Wrong|Utility|Assays|Days|Deferred|", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in rates:
        lines.append(f"|{r['dataset']}/{r['tier']}|{r['policy']}|{r['correct']:.3f}|{r['wrong']:.3f}|{r['utility']:.3f}|{r['measurements']:.3f}|{r['days']:.2f}|{r['deferred']:.3f}|")
    lines += ["", "## Net value differences at matching measurement prices", "",
              "|Dataset/tier|Price|Comparator|Difference|95% grouped CI|", "|---|---:|---|---:|---|"]
    for r in comparisons:
        if r["metric"] == "net":
            lines.append(f"|{r['dataset']}/{r['tier']}|{r['cost_per_measurement']:g}|{r['right']}|{r['difference']:+.4f}|[{r['ci95'][0]:+.4f}, {r['ci95'][1]:+.4f}]|")
    lines += ["", "Selected-action calibration, all raw costs, wrong-decision intervals, ablations and per-assay yields are in `summary.json`.", "", "## Limits", ""]
    lines += ["- " + limit for limit in summary["limits"]]
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"records":len(records), "rates":len(rates), "paired_comparisons":len(comparisons), "calibration_rows":len(calibration)}))


if __name__ == "__main__":
    main()
