"""Reference-only calibration of charged A feedback for fixed STATE-ST readouts."""
import ast
import hashlib
import importlib.util
import json
import time
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

from posterior import common_joint, fit_joint, replay, top5

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKET = ROOT / "research/astra/boundary_acquisition_20261007/packet2"
OUT = ROOT / "outputs/paper_01286/state_feedback_repair"
MEANS = ("M0", "M2", "drug_gain")
spec = importlib.util.spec_from_file_location("frozen_named_readout", HERE.parent / "state_readout_repair_20261009/run.py")
readout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(readout)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def common_parameters(arrays, train):
    """Exact old common model, refitted without the outer held backgrounds."""
    valid = (arrays["availability_A"] & arrays["availability_B"])[train]
    a, b = arrays["train_A"][train], arrays["train_B"][train]
    if np.any(valid.sum(0) < 2):
        raise ValueError("insufficient_candidate_training_support")
    masked_b = np.where(valid, b, np.nan)
    centre = np.nanmean(masked_b, axis=0)
    covariance = np.cov(np.where(valid, b, centre), rowvar=False)
    covariance = .5 * covariance + .5 * np.diag(np.diag(covariance))
    covariance += np.eye(b.shape[1]) * 1e-12
    difference = np.where(valid, a - b, np.nan)
    return covariance, np.maximum(np.nanvar(difference, axis=0, ddof=1), 1e-12), np.nanmean(difference, axis=0)


def predict(arrays, train, held, arm, gains):
    mean, deviation, _, _ = readout.references(arrays, train, held)
    return mean if arm == "M0" else mean + gains * deviation


def build_models(arrays, public, manifest):
    """Fit before opening target outcomes; crossfit includes coefficient selection."""
    drugs = [ast.literal_eval(label)[0][0] for label in manifest["labels"]]
    index = {name: i for i, name in enumerate(sorted(set(drugs)))}
    groups = np.array([index[name] for name in drugs])
    cache, models, predictions, choices = {}, {}, {}, {}

    def fitted(train, arm):
        key = (tuple(train), arm)
        if key not in cache:
            strength, losses = readout.choose(arrays, train, groups, arm)
            gains = readout.fit(arrays, train, groups, arm, strength)
            cache[key] = (gains, {"strength": strength, "losses": losses})
        return cache[key]

    for fold in (*range(3), "targets"):
        train = [i for i in range(45) if fold == "targets" or i % 3 != fold]
        scope = "targets" if fold == "targets" else f"fold{fold}"
        print(f"Fitting {scope}: {len(train)} reference backgrounds", flush=True)
        covariance, obsvar, offset = common_parameters(arrays, train)
        old = common_joint(covariance, obsvar)
        for arm in MEANS:
            prefix = scope + "__" + arm
            gains, choice = fitted(train, arm)
            eb, ea, valid, residual_cells, crossfit_choices = [], [], [], [], []
            for cell in train:
                available = arrays["availability_A"][cell] & arrays["availability_B"][cell]
                # Incomplete contexts remain in mean fits, but never become
                # zero-filled observations for covariance or selection evaluation.
                if not available.all():
                    continue
                keep = [i for i in train if i != cell]
                cross_gains, cross_choice = fitted(keep, arm)
                p = predict(arrays, keep, cell, arm, cross_gains)
                _, _, cross_offset = common_parameters(arrays, keep)
                eb.append(arrays["train_B"][cell] - p)
                ea.append(arrays["train_A"][cell] - cross_offset - p)
                valid.append(available)
                residual_cells.append(cell)
                crossfit_choices.append({"cell": cell, "strength": cross_choice["strength"]})
            eb, ea, valid = np.array(eb), np.array(ea), np.array(valid)
            joint, count = fit_joint(eb, ea, valid)
            models[prefix + "__common"] = old
            models[prefix + "__joint"] = joint
            models[prefix + "__offset"] = offset
            models[prefix + "__error_B"] = eb
            models[prefix + "__error_A"] = ea
            models[prefix + "__gains"] = gains
            choices[prefix] = {**choice, "train": train, "residual_cells": residual_cells,
                               "crossfit_choices": crossfit_choices, "covariance_contexts": count}
            if fold == "targets":
                for context in manifest["contexts"]:
                    key = context.replace("-", "_").replace("/", "_")
                    mean = public[key + "__M0"]
                    p = mean if arm == "M0" else mean + gains * 2 * (public[key + "__M2"] - mean)
                    predictions[key + "__" + arm] = p
            else:
                for cell in range(45):
                    if cell % 3 == fold:
                        predictions[f"ref{cell}__" + arm] = predict(arrays, train, cell, arm, gains)
    return models, predictions, choices


def evaluate(arrays, private, manifest, models, predictions):
    complete = (arrays["availability_A"] & arrays["availability_B"]).all(1)
    units = [(f"ref{i}", i % 3, arrays["train_A"][i], arrays["train_B"][i])
             for i in range(45) if complete[i]]
    units += [(c.replace("-", "_").replace("/", "_"), "targets",
               private[c.replace("-", "_").replace("/", "_") + "__A"],
               private[c.replace("-", "_").replace("/", "_") + "__B"])
              for c in manifest["contexts"]]
    results = []
    for context, fold, y_a, y_b in units:
        scope = "targets" if fold == "targets" else f"fold{fold}"
        for arm in MEANS:
            prefix = scope + "__" + arm
            p = predictions[context + "__" + arm]
            initial = top5(p)
            configurations = [("common_kg", "common", "kg", None),
                              ("joint_kg", "joint", "kg", None)]
            for label, model, policy, schedule in configurations:
                result = replay(p, models[prefix + "__offset"], models[prefix + "__" + model],
                                lambda i: float(y_a[i]), policy=policy, schedule=schedule)
                if label == "common_kg":
                    shared = [h["purchased_A"] for h in result["history"][:-1]]
                    configurations.append(("joint_shared", "joint", "kg", shared))
                    if arm != "M0":
                        configurations.append(("joint_boundary", "joint", "boundary", None))
                # Only the evaluator receives B after the policy commits.
                selected = result["selected"]
                final_mean = np.array(result["posterior_mean_B"])
                result["posterior_mean_B"] = final_mean.tolist()
                result["posterior_variance_B"] = np.diag(result.pop("posterior_cov_B")).tolist()
                results.append({"context": context, "fold": fold, "mean": arm, "policy": label,
                    "initial_selected": initial, "initial_B": float(y_b[initial].sum()),
                    "terminal_B": float(y_b[selected].sum()), "static_delta_B": float(y_b[selected].sum()-y_b[initial].sum()),
                    "initial_mse": float(np.mean((p-y_b)**2)), "posterior_mse": float(np.mean((final_mean-y_b)**2)),
                    "swapped_in": sorted(set(selected)-set(initial)), "swapped_out": sorted(set(initial)-set(selected)),
                    "swap_in_B": float(y_b[sorted(set(selected)-set(initial))].sum()),
                    "swap_out_B": float(y_b[sorted(set(initial)-set(selected))].sum()), **result})
        print(f"Replayed {context}: full146 menu, 11 fixed policies", flush=True)
    return results


def summarize(results):
    summaries = {}
    for scope in ("reference", "targets"):
        rows = [r for r in results if (r["fold"] == "targets") == (scope == "targets")]
        grouped = {}
        for key in sorted({r["mean"] + "__" + r["policy"] for r in rows}):
            group = [r for r in rows if r["mean"] + "__" + r["policy"] == key]
            grouped[key] = {"units": len(group), "terminal_B": float(np.mean([r["terminal_B"] for r in group])),
                "initial_B": float(np.mean([r["initial_B"] for r in group])),
                "posterior_mse": float(np.mean([r["posterior_mse"] for r in group])), "total_cost": sum(r["cost"] for r in group)}
        summaries[scope] = grouped
    comparisons = []
    for arm in MEANS:
        old = {r["context"]: r for r in results if r["mean"] == arm and r["policy"] == "common_kg"}
        for policy in ("joint_kg", "joint_shared", "joint_boundary"):
            new = [r for r in results if r["mean"] == arm and r["policy"] == policy]
            if not new:
                continue
            for scope in ("reference", "targets"):
                rows = [r for r in new if (r["fold"] == "targets") == (scope == "targets")]
                deltas = [r["terminal_B"] - old[r["context"]]["terminal_B"] for r in rows]
                base = np.mean([old[r["context"]]["terminal_B"] for r in rows])
                fold_deltas = {str(f): float(np.mean([r["terminal_B"]-old[r["context"]]["terminal_B"] for r in rows if r["fold"] == f]))
                               for f in sorted({r["fold"] for r in rows}, key=str)}
                comparisons.append({"mean": arm, "policy": policy, "scope": scope,
                    "delta_B": float(np.mean(deltas)), "relative_delta": float(np.mean(deltas)/base),
                    "positive_units": sum(d > 1e-12 for d in deltas), "negative_units": sum(d < -1e-12 for d in deltas),
                    "changed_units": sum(r["selected"] != old[r["context"]]["selected"] for r in rows), "fold_delta_B": fold_deltas})
    primary = next(r for r in comparisons if r["scope"] == "reference" and r["mean"] == "M2" and r["policy"] == "joint_kg")
    gate = primary["relative_delta"] > .02 and sum(d > 0 for d in primary["fold_delta_B"].values()) >= 2
    return {"arms": summaries, "comparisons": comparisons, "registered_development_gate": bool(gate),
            "gate_scope": "M2 joint KG >2% outer-reference mean gain with at least2of3 positive folds; independent verification also required; never production promotion",
            "claim_boundary": "Named39geneRNA signed score, not viability/confirmed discoveries. STATE-pretraining references and exposed5targets. Deterministic acquisition; no LLM effect tested."}


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    for path, expected in freeze["inputs"].items():
        if sha(ROOT / path) != expected:
            raise ValueError("freeze_mismatch:" + path)
    if OUT.exists():
        raise RuntimeError("Use fresh output; do not overwrite a frozen trial")
    OUT.mkdir(parents=True)
    started = time.perf_counter()
    arrays = dict(np.load(PACKET / "training_arrays.npz"))
    public = dict(np.load(PACKET / "public_prior.npz"))
    manifest = json.loads((PACKET / "PACKET_MANIFEST.json").read_text())
    models, predictions, choices = build_models(arrays, public, manifest)
    np.savez_compressed(OUT / "MODELS.npz", **models)
    np.savez_compressed(OUT / "PREDICTIONS.npz", **predictions)
    write(OUT / "MODEL_CHOICES.json", choices)
    # Opening target evaluation is deliberately after all model/forecast writes.
    private = dict(np.load(PACKET / "evaluator_private.npz"))
    results = evaluate(arrays, private, manifest, models, predictions)
    write(OUT / "RESULTS.json", results)
    write(OUT / "SUMMARY.json", {**summarize(results), "seconds": time.perf_counter()-started})
    print(json.dumps(summarize(results), indent=2), flush=True)


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
