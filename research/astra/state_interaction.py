"""Descriptive state/action diagnostics; no refitting or observed policy value.

Run with maestro: python -m research.astra.state_interaction --out NEW_DIRECTORY.
Existing test outcomes remain exploratory; no shrinkage is selected from them.
"""
from __future__ import annotations

import argparse
import hashlib
from itertools import combinations
import json
from pathlib import Path

import numpy as np


def finite_matrix(values):
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 2 or min(values.shape) == 0 or not np.isfinite(values).all():
        raise ValueError("Expected a nonempty finite matrix")
    return values


def action_center(utility):
    """Center an already defined utility, not raw RNA under nonlinear utility."""
    utility = finite_matrix(utility)
    return utility - utility.mean(axis=1, keepdims=True)


def double_center(utility):
    utility = finite_matrix(utility)
    return (utility - utility.mean(axis=1, keepdims=True)
            - utility.mean(axis=0, keepdims=True) + utility.mean())


def choices(utility, tolerance):
    utility = finite_matrix(utility)
    if utility.shape[1] < 2 or not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError("At least two actions and a finite nonnegative tolerance required")
    rows = []
    for row in utility:
        order = np.argsort(-row, kind="stable")
        gap = float(row[order[0]] - row[order[1]])
        rows.append(dict(best_set=np.flatnonzero(row.max() - row <= tolerance).tolist(),
                         selected=int(order[0]) if gap > tolerance else None,
                         gap=gap, exact_top_tie=bool(gap == 0)))
    return rows


def compare_choices(first, second, first_utility, second_utility, tolerance):
    """Ignore arbitrary ordering among tied actions when detecting rank changes."""
    a, b = first["selected"], second["selected"]
    if a is None or b is None:
        return "abstention_change" if a != b else "both_abstain"
    if a != b:
        return "best_action_change"
    others = [i for i in range(len(first_utility)) if i != a]
    for i, j in combinations(others, 2):
        x, y = first_utility[i] - first_utility[j], second_utility[i] - second_utility[j]
        sign_x = 0 if abs(x) <= tolerance else np.sign(x)
        sign_y = 0 if abs(y) <= tolerance else np.sign(y)
        if sign_x != sign_y:
            return "subordinate_relation_change"
    return "same_choice_and_subordinate_relations"


def residual_diagnostics(truth, baseline, prediction):
    """Uniform row/gene weighting, consistent with saved MSE; no tuning."""
    truth, baseline, prediction = map(finite_matrix, (truth, baseline, prediction))
    if not (truth.shape == baseline.shape == prediction.shape):
        raise ValueError("Truth, baseline and prediction shapes must match")
    residual, forecast = truth - baseline, prediction - baseline
    kappa = float(np.mean(residual * forecast))
    variance = float(np.mean(forecast * forecast))
    risk_zero = float(np.mean(residual ** 2))
    risk_one = float(np.mean((truth - prediction) ** 2))
    return dict(kappa=kappa, v=variance, risk_zero=risk_zero, risk_one=risk_one,
                risk_difference=risk_one - risk_zero,
                identity_difference=variance - 2 * kappa,
                weighting="uniform matched rows and genes; coordinate-mean inner product")


def development_shrinkage(truth, baseline, prediction, *, split):
    """Only independent development predictions may choose the coefficient."""
    if split != "development":
        raise ValueError("Shrinkage selection requires development data, never test outcomes")
    diagnostic = residual_diagnostics(truth, baseline, prediction)
    return float(np.clip(diagnostic["kappa"] / diagnostic["v"], 0, 1)) if diagnostic["v"] > 0 else 0.0


def matched_permutation_diagnostic(truth, prediction, *, seed=20261002, repeats=100):
    """Permute only within the scored population of a single frozen context.

    Descriptive Monte Carlo results are not physical confidence intervals or
    p-values: independence/exchangeability of sister units is uncertified.
    """
    truth, prediction = map(finite_matrix, (truth, prediction))
    if truth.shape != prediction.shape or repeats < 1:
        raise ValueError("Matched shapes and positive repetition count required")
    rng = np.random.default_rng(seed)
    risks = [float(np.mean((truth - prediction[rng.permutation(len(truth))]) ** 2))
             for _ in range(repeats)]
    return dict(seed=seed, repeats=repeats, unit_count=len(truth),
                observed_MSE=float(np.mean((truth - prediction) ** 2)),
                permutation_MSE_mean=float(np.mean(risks)),
                permutation_MSE_min=min(risks), permutation_MSE_max=max(risks),
                permutation_MSE=risks,
                interpretation="matched-only association diagnostic; no physical CI or causal interpretation")


def split_reliability(treatment_first, treatment_second, control_first, control_second):
    """Technical split diagnostics only, not independent-culture replication.

    Inputs are disjoint cell splits provided by the caller, each a cells/genes
    matrix. Every action shares the same legal control within each split. This
    function does not certify sample identities or control matching.
    """
    if set(treatment_first) != set(treatment_second) or len(treatment_first) < 2:
        raise ValueError("At least two identical action sets required")
    c1, c2 = map(finite_matrix, (control_first, control_second))
    means = [{action: finite_matrix(matrix).mean(axis=0) for action, matrix in group.items()}
             for group in (treatment_first, treatment_second)]
    features = c1.shape[1]
    if c2.shape[1] != features or any(v.shape != (features,) for m in means for v in m.values()):
        raise ValueError("All splits must use the same ordered feature axis")
    shared = (c1.mean(axis=0) + c2.mean(axis=0)) / 2
    rms = lambda value: float(np.sqrt(np.mean(value ** 2)))
    absolute = {action: dict(
        shared_control_split_RMS=rms((means[0][action] - shared) - (means[1][action] - shared)),
        independent_control_split_RMS=rms((means[0][action] - c1.mean(axis=0))
                                          - (means[1][action] - c2.mean(axis=0))))
        for action in means[0]}
    contrasts = [{"actions": [a, b], "split_RMS": rms(
        (means[0][a] - means[0][b]) - (means[1][a] - means[1][b]))}
        for a, b in combinations(sorted(means[0]), 2)]
    return dict(absolute_response=absolute, action_contrasts=contrasts,
                scope="technical cell splits; caller must verify disjoint identities and shared-control legality",
                physical_CI="not_reported")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verified_input(directory, name):
    path = directory / name
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get(name) != sha256(path):
        raise ValueError(f"Frozen input hash mismatch: {path}")
    return path


def sensitivity_diagnostics(summary, freeze):
    rows = summary["selector_rows"]
    labels, tolerance = freeze["actions"], 1e-6
    if freeze["selector"] != "minimum endpoint; abstain if top-two gap <=1e-6":
        raise ValueError("Unknown frozen selector: specify utility contract explicitly")
    endpoint = finite_matrix([row["scores"] for row in rows])
    if endpoint.shape[1] != len(labels):
        raise ValueError("Scores do not cover frozen action menu")
    utility = -endpoint  # Frozen EGR1 surrogate, larger utility is better.
    selection = choices(utility, tolerance)
    if any(row["selected"] != sel["selected"] for row, sel in zip(rows, selection)):
        raise ValueError("Saved selector cannot be reproduced")
    keys = [(row["pool"], row["seed"]) for row in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate pool/seed rows")
    centered = action_center(utility)
    pools, seeds = sorted({p for p, _ in keys}), sorted({s for _, s in keys})
    if len(keys) != len(pools) * len(seeds):
        raise ValueError("Incomplete pool/seed grid")
    pairs = []
    for i, j in combinations(range(len(rows)), 2):
        p, s = keys[i]
        q, t = keys[j]
        if s != t and p != q:
            continue
        pairs.append(dict(first=keys[i], second=keys[j],
                          kind="between_pool_same_seed" if s == t else "within_pool_sampling",
                          relation=compare_choices(selection[i], selection[j], utility[i], utility[j], tolerance),
                          raw_utility_RMS=float(np.sqrt(np.mean((utility[i] - utility[j]) ** 2))),
                          action_centered_RMS=float(np.sqrt(np.mean((centered[i] - centered[j]) ** 2)))))
    pairing = []
    for receipt in summary["receipts"]:
        calls = receipt["trace"]["calls"]
        hashes = {action: [call.get("basal_sha256") for call in calls if call.get("action") == action]
                  for action in labels}
        available = all(len(value) == 1 and value[0] for value in hashes.values())
        paired = available and len({value[0] for value in hashes.values()}) == 1
        pairing.append(dict(pool=receipt["pool"], seed=receipt["seed"],
                            action_basal_hashes=hashes, same_basal_tensor=bool(paired)))
    averaged = np.stack([utility[[i for i, key in enumerate(keys) if key[0] == p]].mean(axis=0) for p in pools])
    return dict(scope="saved STATE technical RNA surrogate; no observed action value",
                utility="negative mean predicted EGR1; original frozen surrogate",
                action_labels=labels, tolerance=tolerance,
                endpoint_exact_zeros=int(np.sum(endpoint == 0)), endpoint_values=int(endpoint.size),
                exact_top_ties=sum(sel["exact_top_tie"] for sel in selection),
                abstentions=sum(sel["selected"] is None for sel in selection),
                choices=selection, row_keys=keys,
                action_centered_utility=centered.tolist(),
                double_centered_utility=double_center(utility).tolist(),
                comparisons=pairs, seed_averaged_choices=dict(zip(pools, choices(averaged, tolerance))),
                globally_weakly_best_actions=[a for a in range(len(labels))
                                             if np.all(utility[:, a] >= utility.max(axis=1) - tolerance)],
                basal_pairing=pairing, paired_requests=sum(p["same_basal_tensor"] for p in pairing),
                limitation="pool is confounded with plate; distinct action basal tensors contaminate contrasts; no biological gain claim")


def analyze(root, out):
    historical = root / "tools/datasets/audit_results/20261001_state_response"
    sensitivity = historical / "sensitivity_v1"
    retrospective = historical / "resistrace_v1"
    paths = [verified_input(sensitivity, name) for name in ("summary.json", "freeze.json")]
    paths += [verified_input(retrospective, name) for name in ("predictions_and_observations.npz", "freeze.json")]
    diagnostic = sensitivity_diagnostics(*(json.loads(p.read_text(encoding="utf-8")) for p in paths[:2]))
    retrospective_results = {}
    with np.load(paths[2], allow_pickle=False) as archive:
        for context in ("carboplatin", "growth_control"):
            prefix = context + "_"
            indices = archive[prefix + "scored_query_indices"]
            visible = finite_matrix(archive[prefix + "state_visible"])
            if indices.ndim != 1 or not np.issubdtype(indices.dtype, np.integer):
                raise ValueError("Scoring indices must be a one-dimensional integer array")
            if len(np.unique(indices)) != len(indices) or np.any(indices < 0) or np.any(indices >= len(visible)):
                raise ValueError("Invalid or repeated scored indices")
            truth = archive[prefix + "observed_matched"]
            baseline = archive[prefix + "context_mean_response"][indices]
            old_permuted = archive[prefix + "state_permuted"][indices]
            retrospective_results[context] = dict(
                scope="exact-match deposited descendants; exploratory already-viewed test",
                residual=residual_diagnostics(truth, baseline, visible[indices]),
                matched_only_permutation=matched_permutation_diagnostic(truth, visible[indices]),
                original_all_baseline_permutation_MSE=float(np.mean((old_permuted - truth) ** 2)),
                shrinkage_selection="not_run: saved development predictions unavailable; test outcomes cannot choose lambda",
                missingness="missing descendants are not deaths; matched-only analysis does not identify all starting cells")
    report = dict(STATE=diagnostic, RidgeRNA=retrospective_results, actual_model_calls=0,
                  retraining=False, terminal_utility="not_identified", physical_CI="not_reported",
                  inputs={str(p.relative_to(root)): sha256(p) for p in paths},
                  code_sha256=sha256(Path(__file__)))
    out.mkdir(parents=True, exist_ok=False)
    (out / "execution_source.py.txt").write_bytes(Path(__file__).read_bytes())
    (out / "diagnostics.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.root.resolve(), args.out.resolve())
    print(json.dumps({"output": str(args.out.resolve()), "STATE_paired_requests": result["STATE"]["paired_requests"]}))
