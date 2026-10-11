"""Frozen calibration, replay, and paired scientific analysis in the maestro environment."""
from __future__ import annotations

import argparse
from dataclasses import replace
import datetime
import json
from pathlib import Path
import platform
import sys
import time

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

import campaign as C

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "CALIBRATION_FREEZE.json"
FIXED = ("batch_gp_kg", "batch_gp_ivr", "fixed_library")
ARMS = C.PROTOCOL["arms"]


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def freeze_execution() -> dict:
    return {name: C.sha256(HERE / name)
            for name in ("campaign.py", "run.py", "verify.py", "PROTOCOL.json", "PROTOCOL_FREEZE.json", "DEVIATIONS.json")}


def conformal_quantile(values: np.ndarray, alpha: float = 0.1) -> float:
    finite = np.sort(values[np.isfinite(values)])
    rank = int(np.ceil((len(finite) + 1) * (1 - alpha)))
    if rank > len(finite):
        raise ValueError("INSUFFICIENT_CALIBRATION")
    return float(finite[rank - 1])


def run_one(library, datum, arm, cfg, signature_map=None):
    query, primary, secondary = datum
    if arm == "adaptive_signature_shuffle":
        other = signature_map[query.drug]
        query = replace(query, signature=other.signature, have=other.have)
    env = C.MeasuredEnvironment(library, query, primary, secondary, arm == "adaptive_feedback_shuffle")
    rows, ledgers = C.run_policy(library, query, env, arm, cfg)
    for row in rows:
        row.update(drug=query.drug, moa=query.moa, role=query.role)
    return rows, ledgers


def signature_permutation(data):
    mapping = {}
    for role in ("development", "confirmation"):
        queries = [d[0] for d in data if d[0].role == role]
        perm = np.random.default_rng(C.SEED + (1 if role == "development" else 2)).permutation(len(queries))
        for query, index in zip(queries, perm):
            mapping[query.drug] = queries[int(index)]
    return mapping


def calibrate(library, data):
    if CONFIG.exists():
        raise RuntimeError("CALIBRATION_ALREADY_FROZEN")
    calibration = [d for d in data if d[0].role == "development"]
    print(f"calibration drugs={len(calibration)} reference={len(library.drug)}", flush=True)
    start = time.perf_counter()
    fits = []
    for tau in C.PROTOCOL["algorithm"]["tau_grid"]:
        utility = []
        for query, primary, secondary in calibration:
            posterior = C.ParticlePosterior(library, query, tau, 1.0)
            env = C.MeasuredEnvironment(library, query, primary, secondary)
            score, _ = env.score(posterior.predict())
            utility.append(score["utility"])
        fits.append({"tau": tau, "utility": float(np.mean(utility))})
    tau = sorted(fits, key=lambda fit: (-fit["utility"], fit["tau"]))[0]["tau"]
    print(f"tau selected={tau}, seconds={time.perf_counter() - start:.1f}", flush=True)
    sigma_fits = []
    for sigma in C.PROTOCOL["algorithm"]["noise_sigma_grid"]:
        utility = []
        for datum in calibration:
            rows, _ = run_one(library, datum, "fixed_library", {"tau": tau, "sigma": sigma})
            utility.append(rows[-1]["utility"])
        sigma_fits.append({"sigma": sigma, "utility": float(np.mean(utility))})
    sigma = sorted(sigma_fits, key=lambda fit: (-fit["utility"], fit["sigma"]))[0]["sigma"]
    cfg = {"tau": tau, "sigma": sigma}
    print(f"sigma selected={sigma}, seconds={time.perf_counter() - start:.1f}", flush=True)
    signature_map = signature_permutation(data)
    rows = []
    for index, datum in enumerate(calibration):
        for arm in ARMS:
            result, _ = run_one(library, datum, arm, cfg, signature_map)
            rows.extend(result)
        if index % 20 == 0:
            print(f"calibration {index}/{len(calibration)} seconds={time.perf_counter() - start:.1f}", flush=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(HERE / "CALIBRATION_ROWS.csv", index=False)
    terminal = frame[frame.budget == 16]
    fixed_results = {arm: float(terminal[terminal.arm == arm].utility.mean()) for arm in FIXED}
    best_fixed = sorted(FIXED, key=lambda arm: (-fixed_results[arm], arm))[0]
    bounds = {arm: conformal_quantile(terminal[terminal.arm == arm].max_error.to_numpy()) for arm in ARMS}
    metadata = {"created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "scope": C.PROTOCOL["scope"], "parameters": cfg,
                "n_calibration": len(calibration), "n_reference": len(library.drug),
                "tau_grid": fits, "sigma_grid": sigma_fits,
                "best_fixed": best_fixed, "fixed_mean_utility": fixed_results,
                "simultaneous_90pct_error_bound": bounds,
                "discovery_lines": [str(library.lines[i]) for i in library.discovery],
                "terminal_lines": [str(library.lines[i]) for i in library.targets],
                "menu_panel": [str(library.lines[i]) for i in library.panel],
                "execution_sha256": freeze_execution(),
                "calibration_rows_sha256": C.sha256(HERE / "CALIBRATION_ROWS.csv"),
                "python": sys.executable, "version": sys.version,
                "platform": platform.platform(), "seconds": time.perf_counter() - start,
                "llm_api_calls": 0}
    dump(CONFIG, metadata)
    print(f"calibration frozen best_fixed={best_fixed} seconds={metadata['seconds']:.1f}", flush=True)


def verify_execution() -> dict:
    frozen = json.loads(CONFIG.read_text(encoding="utf-8"))
    for name, expected in frozen["execution_sha256"].items():
        if C.sha256(HERE / name) != expected:
            raise RuntimeError(f"EXECUTION_DIGEST_MISMATCH: {name}")
    if C.sha256(HERE / "CALIBRATION_ROWS.csv") != frozen["calibration_rows_sha256"]:
        raise RuntimeError("CALIBRATION_DIGEST_MISMATCH")
    return frozen


def evaluate(library, data, smoke_limit=None):
    frozen = verify_execution()
    cfg = frozen["parameters"]
    units = [d for d in data if d[0].role == ("development" if smoke_limit else "confirmation")]
    if smoke_limit:
        units = units[:smoke_limit]
    prefix = "SMOKE" if smoke_limit else "TEST"
    if (HERE / f"{prefix}_ROWS.csv").exists():
        raise RuntimeError("EVALUATION_OUTPUT_ALREADY_EXISTS")
    start = time.perf_counter()
    signature_map = signature_permutation(data)
    rows = []
    with (HERE / f"{prefix}_LEDGER.jsonl").open("w", encoding="utf-8") as stream:
        for index, datum in enumerate(units):
            query = datum[0]
            for arm in ARMS:
                result, ledgers = run_one(library, datum, arm, cfg, signature_map)
                rows.extend(result)
                # Full terminal vectors are retained once; intermediate cost rows stay in CSV.
                record = dict(ledgers[-1], drug=query.drug, moa=query.moa, arm=arm,
                              signature_from=signature_map[query.drug].drug if arm == "adaptive_signature_shuffle" else query.drug)
                stream.write(json.dumps(record, allow_nan=False) + "\n")
            if index % 20 == 0:
                print(f"{prefix} {index}/{len(units)} seconds={time.perf_counter() - start:.1f}", flush=True)
    pd.DataFrame(rows).to_csv(HERE / f"{prefix}_ROWS.csv", index=False)
    dump(HERE / f"{prefix}_RECEIPT.json", {"created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "n_drugs": len(units), "scope": C.PROTOCOL["scope"], "role": "development" if smoke_limit else "confirmation",
         "seconds": time.perf_counter() - start, "calibration_freeze_sha256": C.sha256(CONFIG),
         "rows_sha256": C.sha256(HERE / f"{prefix}_ROWS.csv"),
         "ledger_sha256": C.sha256(HERE / f"{prefix}_LEDGER.jsonl"), "llm_api_calls": 0})
    print(f"{prefix} finished {len(units)} drugs seconds={time.perf_counter() - start:.1f}", flush=True)


def paired_statistics(delta, clusters, seed):
    delta = np.asarray(delta, float)
    ok = np.isfinite(delta)
    delta, clusters = delta[ok], np.asarray(clusters)[ok]
    if not len(delta):
        return {"n": 0, "effect": None, "ci95": None, "p_one_sided": None, "cluster_ci95": None}
    rng = np.random.default_rng(seed)
    samples = delta[rng.integers(len(delta), size=(4000, len(delta)))].mean(axis=1)
    flips = rng.choice(np.array([-1.0, 1.0]), size=(20000, len(delta))) @ delta / len(delta)
    p = (1 + int(np.sum(flips >= delta.mean() - 1e-12))) / (len(flips) + 1)
    unique = np.unique(clusters)
    sums = np.array([delta[clusters == cluster].sum() for cluster in unique])
    counts = np.array([np.sum(clusters == cluster) for cluster in unique])
    draw = rng.integers(len(unique), size=(4000, len(unique)))
    cluster_boot = sums[draw].sum(axis=1) / counts[draw].sum(axis=1)
    return {"n": len(delta), "effect": float(delta.mean()), "ci95": np.quantile(samples, [0.025, 0.975]).tolist(),
            "p_one_sided": float(p), "n_mechanism_clusters": len(unique),
            "cluster_ci95": np.quantile(cluster_boot, [0.025, 0.975]).tolist()}


def holm(values):
    order = np.argsort(values)
    adjusted = np.ones(len(values))
    prior = 0.0
    for rank, index in enumerate(order):
        prior = max(prior, (len(values) - rank) * values[index])
        adjusted[index] = min(1.0, prior)
    return adjusted.tolist()


def analysis(prefix="TEST"):
    frozen = verify_execution()
    receipt = json.loads((HERE / f"{prefix}_RECEIPT.json").read_text(encoding="utf-8"))
    for suffix, key in (("ROWS.csv", "rows_sha256"), ("LEDGER.jsonl", "ledger_sha256")):
        if C.sha256(HERE / f"{prefix}_{suffix}") != receipt[key]:
            raise RuntimeError("EVALUATION_DIGEST_MISMATCH")
    frame = pd.read_csv(HERE / f"{prefix}_ROWS.csv")
    terminal = frame[frame.budget == 16]
    summaries = []
    for (arm, budget), group in frame.groupby(["arm", "budget"]):
        row = {"arm": arm, "budget": int(budget), "n": len(group),
               "spent_total": int(group.spent.sum()), "rounds_total": int(group.rounds.sum()),
               "mean_seconds": float(group.seconds.mean())}
        for metric in ("utility", "precision", "selective_r", "secondary_utility", "secondary_precision", "secondary_r"):
            vals = group[metric].dropna()
            row[metric] = None if not len(vals) else float(vals.mean())
            row[f"{metric}_n"] = len(vals)
        if budget == 16:
            row["simultaneous_coverage90"] = float((group.max_error <= frozen["simultaneous_90pct_error_bound"][arm]).mean())
            row["simultaneous_interval_width"] = 2 * frozen["simultaneous_90pct_error_bound"][arm]
            active = group[group.active_query]
            row["active_n"] = len(active)
            row["active_simultaneous_coverage90"] = None if not len(active) else float((active.max_error <= frozen["simultaneous_90pct_error_bound"][arm]).mean())
        summaries.append(row)
    pivot = terminal.pivot(index="drug", columns="arm", values="utility")
    cluster = terminal.drop_duplicates("drug").set_index("drug").moa.reindex(pivot.index)
    primary = []
    for index, contrast in enumerate(C.PROTOCOL["primary_contrasts"]):
        b = frozen["best_fixed"] if contrast["b"] == "frozen_best_fixed" else contrast["b"]
        delta = pivot[contrast["a"]] - pivot[b]
        stats = paired_statistics(delta, cluster, C.SEED + index)
        primary.append(dict(contrast, b=b, **stats))
    for contrast, p in zip(primary, holm([x["p_one_sided"] for x in primary])):
        contrast["p_holm"] = p
        contrast["verdict"] = "PASS" if contrast["effect"] > 0 and p <= 0.05 else "NOT_SUPPORTED"
    comparisons = []
    for index, comparator in enumerate([frozen["best_fixed"], "source_only", "adaptive_without_l1000",
                                         "adaptive_feedback_shuffle", "adaptive_signature_shuffle", "random_library"]):
        for metric in ("utility", "precision", "selective_r", "secondary_utility", "secondary_precision", "secondary_r"):
            values = terminal.pivot(index="drug", columns="arm", values=metric)
            stats = paired_statistics(values.adaptive_dual - values[comparator], cluster, C.SEED + 10 + index)
            comparisons.append({"a": "adaptive_dual", "b": comparator, "metric": metric, **stats})
    precision = next(x for x in comparisons if x["b"] == frozen["best_fixed"] and x["metric"] == "precision")
    secondary = next(x for x in comparisons if x["b"] == frozen["best_fixed"] and x["metric"] == "secondary_utility")
    gate = (all(x["verdict"] == "PASS" for x in primary) and precision["effect"] >= -0.02
            and secondary["ci95"] is not None and secondary["ci95"][0] > 0)
    result = {"scope": C.PROTOCOL["scope"], "n_drugs": receipt["n_drugs"], "best_fixed": frozen["best_fixed"],
              "parameters": frozen["parameters"], "primary": primary, "comparisons": comparisons,
              "cost_curve": summaries, "dual_core_gate": "CONFIRMED_IN_RETROSPECTIVE_REPLAY" if gate else "NOT_CONFIRMED",
              "seconds": receipt["seconds"], "llm_api_calls": 0,
              "limits": ["Previously exposed compounds; no fresh biological holdout.",
                         "Primary and secondary assays have differing dose/platform details.",
                         "Adaptive policies require 16 turnarounds versus one batch.",
                         "Library posterior and Gaussian EVSI are empirical approximations.",
                         "No causal mechanism or LLM policy is tested.",
                         "Same-molecule replicates and mechanism clusters limit independence."]}
    dump(HERE / f"{prefix}_RESULTS.json", result)
    print(json.dumps({"gate": result["dual_core_gate"], "primary": primary, "best_fixed": frozen["best_fixed"]}, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("calibrate", "evaluate", "analyze", "smoke"))
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        if args.phase == "analyze":
            analysis()
            return
        library, data = C.load_data()
        if args.phase == "calibrate":
            calibrate(library, data)
        elif args.phase == "evaluate":
            evaluate(library, data)
        else:
            evaluate(library, data, args.limit)


if __name__ == "__main__":
    main()
