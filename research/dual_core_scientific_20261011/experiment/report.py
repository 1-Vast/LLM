"""Produce an English study report and standalone scientific cost-curve plots."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent


def interval(result):
    return f"{result['effect']:+.4f} [{result['ci95'][0]:+.4f}, {result['ci95'][1]:+.4f}]"


def main():
    results = json.loads((HERE / "TEST_RESULTS.json").read_text(encoding="utf-8"))
    supplement = json.loads((HERE / "SUPPLEMENT_RESULTS.json").read_text(encoding="utf-8"))
    frozen = json.loads((HERE / "CALIBRATION_FREEZE.json").read_text(encoding="utf-8"))
    verification = json.loads((HERE / "VERIFIED.json").read_text(encoding="utf-8"))
    price = json.loads((HERE / "COST_SCENARIOS.json").read_text(encoding="utf-8"))
    table = pd.read_csv(HERE / "TEST_ROWS.csv")
    extra = pd.read_csv(HERE / "SUPPLEMENT_ROWS.csv")
    table = pd.concat([table, extra[extra.role == "confirmation"]], ignore_index=True)
    means = table[table.budget == 16].groupby("arm").mean(numeric_only=True)
    labels = {"adaptive_dual": "Adaptive empirical dual core",
              results["best_fixed"]: "Best calibration-selected batch GP",
              "batch_particle_kg": "Batch with identical particle model",
              "adaptive_without_l1000": "Adaptive without transcription",
              "source_only": "One-shot transcriptional transfer"}
    colors = ("#3366AA", "#BB5533", "#4A995A", "#8C6BB1", "#666666")
    figure, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    for (arm, label), color in zip(labels.items(), colors):
        for axis, metric, title in zip(axes, ("utility", "precision"),
                                       ("Primary selective utility", "Top-10 sensitive-line precision")):
            points = table[table.arm == arm].groupby("budget")[metric].mean()
            if arm == "source_only":
                axis.axhline(points.iloc[0], color=color, linestyle="--", label=label + " (0 reads)")
            else:
                axis.plot(points.index, points.values, marker="o", color=color, label=label)
            axis.set_xlabel("Purchased line-compound readouts")
            axis.set_title(title)
            axis.set_xticks([2, 4, 8, 16])
            axis.grid(axis="y", color="#DDDDDD", linewidth=0.6)
            axis.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Negative mean selected selective residual")
    axes[1].set_ylabel("Fraction among most sensitive 10%")
    handles, names = axes[0].get_legend_handles_labels()
    figure.legend(handles, names, fontsize=8, loc="lower center", ncol=2, frameon=False)
    figure.subplots_adjust(left=0.09, right=0.98, top=0.90, bottom=0.25, wspace=0.30)
    figure.savefig(HERE / "COST_CURVE.png", dpi=180)
    figure.savefig(HERE / "COST_CURVE.pdf")
    plt.close(figure)
    primary_rows = "\n".join(f"| {r['id']} | {r['a']} minus {r['b']} | {interval(r)} | {r['p_holm']:.5f} | {r['verdict']} |"
                             for r in results["primary"])
    secondary_rows = "\n".join(f"| {r['metric']} | {interval(r)} | {r['p_one_sided']:.5f} |"
                               for r in supplement["contrasts"] if r["budget"] == 16 and r["b"] == "batch_particle_kg")
    arm_rows = "\n".join(f"| {arm} | {row.utility:.4f} | {row.precision:.4f} | {row.selective_r:.4f} | {row.secondary_utility:.4f} | {int(row.spent)} | {int(row.rounds)} |"
                         for arm, row in means.iterrows())
    reliability_rows = "\n".join(f"| {row['arm']} | {row['simultaneous_coverage90']:.3f} | {row['active_simultaneous_coverage90']:.3f} | {row['simultaneous_interval_width']:.3f} |"
                                 for row in results["cost_curve"] if row["budget"] == 16)
    price_rows = "\n".join(f"| {r['reference']} | {r['prices']['turnaround']:.3f} | {r['net_utility_increment']:+.4f} | [{r['cluster_bootstrap_95'][0]:+.4f}, {r['cluster_bootstrap_95'][1]:+.4f}] |"
                           for r in price["scenarios"])
    strict = next(r for r in supplement["contrasts"] if r["budget"] == 16 and r["b"] == "batch_particle_kg" and r["metric"] == "utility")
    adaptive = means.loc["adaptive_dual"]
    same = means.loc["batch_particle_kg"]
    text = f"""# Frozen scientific-decision campaign replay

The registered dual-core verdict is **{results['dual_core_gate']}** on {results['n_drugs']} retrospective drug campaigns. The observation-dependent deterministic policy is compared with the strongest calibration-selected batch model and with a separately frozen batch policy that uses the identical particle posterior. The latter utility difference is {interval(strict)}. These are empirical-library policies; **zero LLM/API calls** were made.

## What is measured

Every campaign receives a query compound's existing L1000 inputs, and may buy up to 16 recorded PRISM primary measurements from a 64-line reference-derived discovery menu. It then selects 10 unpurchasable terminal lines. The primary utility is the negative mean observed selective residual of those selections, after removing offset and the fixed reference-derived generic-sensitivity axis. Precision describes overlap with the most sensitive 10% of recorded terminal lines. Neither metric establishes a causal mechanism or prospective experimental discovery.

Only 701 old Block N reference compounds fit source moments, nuisance coefficients and candidate panels. The 281 development compounds select temperature, observation noise and the best fixed baseline. The 421 old confirmation compounds evaluate the frozen algorithm. **All these public compounds were already exposed in earlier studies**: this is algorithm separation within retrospective data, not a newly untouched biological holdout. Every input-qualified test compound is included; hidden killing activity never filters the primary population. The source pool excludes the query's exact annotated mechanism class. Cell-line identities are known from references, so this is not unseen-cell-context generalization.

`PROTOCOL_FREEZE.json` binds protocol and source bytes before new campaign metrics; `CALIBRATION_FREEZE.json` binds executable code, chosen parameters and calibration rows before the algorithm-test replay. A clarification about calibrating the particle temperature rather than the parameter-free kNN comparator is recorded in `DEVIATIONS.json`.

## Registered results at 16 reads

| Contrast | Comparison | Mean paired utility difference [95% drug bootstrap] | Holm p | Verdict |
|---|---|---:|---:|---|
{primary_rows}

The primary comparison against a Gaussian posterior changes both acquisition and posterior model. It evaluates the complete proposed policy against a strong practical alternative, and cannot alone attribute a difference to adaptation. `fixed_library` preserves the particle model but uses a reference-variance panel; its separate contrasts are retained in `SUPPLEMENT_RESULTS.json`.

| Arm | Primary utility | Precision | Selective r | Secondary utility | Reads/campaign | Turnarounds/campaign |
|---|---:|---:|---:|---:|---:|---:|
{arm_rows}

The one-shot arm buys zero new measurements. All L1000 acquisition cost is shared input and has not been authenticated as a procurement price. Adaptive turnarounds are simulated sequential decision rounds; no wet-lab experiment was purchased. Feature similarities are cached and shared, so per-arm CPU times are not independent cold-start cost estimates. Calibration took {frozen['seconds']:.1f} seconds and the full primary replay took {results['seconds']:.1f} seconds in the maestro Python environment.

![Read-budget cost curves](COST_CURVE.png)

## Identical-posterior acquisition control

While the primary replay was running and before any algorithm-test values or summaries were inspected, an independent review identified the Gaussian-versus-particle confound. `SUPPLEMENT_PROTOCOL.json` and `SUPPLEMENT_FREEZE.json` freeze a secondary comparator; the original primary protocol and executable hashes remain unchanged. The batch comparator precomputes its entire plan from the exact initial particle Gaussian moments, with covariance-only updates and zero innovation. Both policies subsequently condition the **same particle posterior on purchased true values**. Its first action and EVSI match the adaptive policy on {supplement['identical_initial_moments_cases']} development cases.

| Metric, adaptive minus identical-posterior batch | Mean paired difference [95% drug bootstrap] | Uncorrected secondary p |
|---|---:|---:|
{secondary_rows}

The identical-posterior batch primary utility is {same.utility:.4f}, against {adaptive.utility:.4f} for adaptation. Secondary-screen contrasts use independently measured values that never enter policy updates; paired availability and uncertainty are recorded in JSON. These secondary contrasts do not replace the registered primary gate or constitute fresh biological replication. Secondary availability is incomplete and dose selection differs from the primary screen. Requiring at least five selected lines with secondary values makes eligibility selection-dependent; paired comparisons use the intersection and do not correct this missingness bias. Drug sign-flip p-values assume symmetric paired differences under the null, and are not a randomized prospective laboratory trial.

## Reliability and efficiency

A finite-sample 90% conformal order statistic on development campaigns bounds the maximum absolute selective-coordinate prediction error across all terminal lines. The frozen bound is evaluated without test adjustment. This is marginal coverage under exchangeability, and wide intervals do not establish useful biological precision.

| Arm | Test simultaneous coverage | Active-drug subgroup coverage | Full interval width |
|---|---:|---:|---:|
{reliability_rows}

The active-drug subgroup is descriptive, defined only during evaluation; it is not a selected primary cohort. Mechanism-cluster bootstrap intervals and the production `paired_campaign_report` independently assess dependence sensitivity. Prices below are **declared utility-unit scenarios, not real laboratory or monetary costs**. Measurements are equal between these comparisons; a sequential adaptive policy uses 15 additional turnarounds.

| Comparator | Price per turnaround | Net adaptive utility difference | Mechanism-cluster 95% interval |
|---|---:|---:|---|
{price_rows}

## Verification and artifacts

Source/execution digests match. Independently recomputing all {verification['ledger']['n_terminal_ledgers']} primary terminal ledgers gives maximum metric error {verification['ledger']['max_metric_error']:.3g}; {supplement['independent_ledger_verification']['n_terminal_ledgers']} supplementary ledgers also agree. There are no duplicate, terminal-line or over-budget purchases. Poisoning terminal truth leaves full action traces and predictions unchanged in eight development cases; changing the first bought value changes the second action in {verification['guards']['changed_second_actions']}/8 cases. Feedback and signature permutations are retained as controls. `VERIFIED.json` also preserves the outcome-association shuffle diagnostic; no control is silently removed.

`TEST_ROWS.csv` retains all 2/4/8/16 cost rows; `TEST_LEDGER.jsonl.gz` and `SUPPLEMENT_LEDGER.jsonl.gz` are lossless archives of predictions, selected identities, purchases and evaluation truth. `CAMPAIGN_RESULTS.json` exports the production reporting contract, and `COST_SCENARIOS.json` records independent cluster statistics and explicit prices. Original expanded ledgers remain local and are ignored by this study directory's `.gitignore`.

## Reproduction

Use `D:/anaconda/envs/maestro/python.exe` or an equivalent environment with NumPy, SciPy, pandas, matplotlib and threadpoolctl. From repository root, the original execution order in a fresh output directory was:

```powershell
& 'D:/anaconda/envs/maestro/python.exe' research/dual_core_scientific_20261011/experiment/run.py calibrate
& 'D:/anaconda/envs/maestro/python.exe' research/dual_core_scientific_20261011/experiment/run.py evaluate
& 'D:/anaconda/envs/maestro/python.exe' research/dual_core_scientific_20261011/experiment/supplement.py
& 'D:/anaconda/envs/maestro/python.exe' research/dual_core_scientific_20261011/experiment/run.py analyze
& 'D:/anaconda/envs/maestro/python.exe' research/dual_core_scientific_20261011/experiment/verify.py
& 'D:/anaconda/envs/maestro/python.exe' research/dual_core_scientific_20261011/experiment/analyze_supplement.py
& 'D:/anaconda/envs/maestro/python.exe' research/dual_core_scientific_20261011/experiment/export_decision_report.py
& 'D:/anaconda/envs/maestro/python.exe' research/dual_core_scientific_20261011/experiment/report.py
```

Calibration/evaluation refuse to overwrite completed freezes or outputs. To verify retained archives, first run `archive_ledgers.py --restore`, then `run.py analyze`, `verify.py` and `analyze_supplement.py`; all source assets are still needed for the poisoning/source checks. `replay_check.py` independently reruns all ten frozen policies and all four budgets on eight algorithm-test compounds, compares every retained primary and secondary metric, and writes a separate receipt without changing the original outputs. `replay_check.py --all` extends that algorithm reconstruction to the complete test population. The sample reconstruction is software verification on test data, not additional calibration.

The four frozen derived npz inputs under ignored `data/external` occupy about 86 MB. A clean checkout **does not contain these assets** and correctly refuses missing or digest-mismatched inputs. `SOURCE_REACQUISITION.json` contains verified public PRISM figshare v4 download URLs, sizes and md5 values (137,848,721 bytes across four raw CSV files), plus the GEO L1000 source URL. Old Block M/N extraction scripts and receipts specify the transformation and SHA hashes; their write-once behavior means recovering missing derived assets requires a separate staged rebuild. Automated raw-to-derived restoration was not implemented or claimed here. No new dataset was downloaded for the experiment, and existing unrelated research files were not edited.

No empirical prediction or adaptive-planning algorithm is promoted to production by this replay. The useful engineering contracts are truthful observation access, deterministic provenance, typed paired campaigns and explicit cost accounting; predictive or Agent superiority needs an additional qualifying experiment.
"""
    (HERE / "README.md").write_text(text, encoding="utf-8")
    print("Wrote README.md, COST_CURVE.png and COST_CURVE.pdf")


if __name__ == "__main__":
    main()
