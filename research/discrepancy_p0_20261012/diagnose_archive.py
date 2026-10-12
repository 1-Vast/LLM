"""Diagnose immutable, already exposed context-probe predictions without fitting."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
ARCHIVE = ROOT / "research/context_probe_20261011/runs/fixed8"
DATA = ROOT / "research/context_probe_20261011/data/output.npz"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def rank_menu(prediction, menu):
    """Order the fixed menu without accepting truth or availability."""
    menu = np.asarray(menu, dtype=int)
    if len(set(menu.tolist())) != len(menu) or not np.isfinite(prediction[menu]).all():
        raise ValueError("unique menu and finite predictions required")
    return menu[np.lexsort((menu, prediction[menu]))]


def terminal_utility(truth, selected):
    values = np.asarray(truth)[np.asarray(selected, dtype=int)]
    return -float(values.mean()) if len(values) and np.isfinite(values).all() else None


def exact_oracle(truth, menu, k):
    """Exact realized oracle only on a completely measured unchanged menu."""
    menu = np.asarray(menu, dtype=int)
    if k < 1 or len(menu) < k:
        raise ValueError("enough menu entries for the requested top-k required")
    if not np.isfinite(truth[menu]).all():
        return None
    return terminal_utility(truth, rank_menu(truth, menu)[:k])


def validate_alignment(context_ids, roles, drug_ids, predictions, commits, probes, arms, k):
    """Validate axes and fixed commitments using identities and predictions only."""
    indices = np.flatnonzero(roles == "evaluation")
    menu = np.setdiff1d(np.arange(len(drug_ids)), probes)
    if len(set(probes)) != len(probes) or np.any(np.asarray(probes) < 0) or np.any(np.asarray(probes) >= len(drug_ids)):
        raise ValueError("invalid frozen probes")
    if predictions.shape != (len(indices), len(arms), len(drug_ids)) or len(commits) != len(indices) * len(arms):
        raise ValueError("archive axes or record count do not match")
    for position, index in enumerate(indices):
        for arm_position, arm in enumerate(arms):
            record = commits[position * len(arms) + arm_position]
            chosen = np.asarray(record["selected_indices"], dtype=int)
            if (record["index"] != int(index) or record["context"] != str(context_ids[index])
                    or record["arm"] != arm or len(chosen) != k
                    or len(set(chosen.tolist())) != k or not np.isin(chosen, menu).all()
                    or record["selected_ids"] != drug_ids[chosen].tolist()
                    or not np.array_equal(chosen, rank_menu(predictions[position, arm_position], menu)[:k])):
                raise ValueError("archive role/order/identity/commitment mismatch")
    return indices, menu


def pair_mse(prediction, truth, prior_order, k):
    left = prior_order[:k]
    right = prior_order[k:2 * k]
    left = left[np.isfinite(truth[left])]
    right = right[np.isfinite(truth[right])]
    if not len(left) or not len(right):
        return None, 0
    error = (prediction[left, None] - prediction[right]) - (truth[left, None] - truth[right])
    return float(np.square(error).mean()), int(error.size)


def diagnose_case(truth, prediction, baseline, selected, base_selected, menu, k):
    prior_order = rank_menu(baseline, menu)
    bands = {"selected_prior": prior_order[:k], "boundary": prior_order[k:3 * k],
             "remainder": prior_order[3 * k:]}
    mse, counts = {}, {}
    for name, band in {"all": menu, **bands}.items():
        measured = band[np.isfinite(truth[band])]
        counts[name] = len(measured)
        mse[name] = float(np.square(prediction[measured] - truth[measured]).mean()) if len(measured) else None
    utility = terminal_utility(truth, selected)
    baseline_utility = terminal_utility(truth, base_selected)
    increment = utility - baseline_utility if utility is not None and baseline_utility is not None else None
    added = sorted(set(selected) - set(base_selected))
    removed = sorted(set(base_selected) - set(selected))
    swap_gain = float((truth[removed].sum() - truth[added].sum()) / k) if increment is not None else None
    oracle = exact_oracle(truth, menu, k)
    observed = menu[np.isfinite(truth[menu])]
    observed_oracle = terminal_utility(truth, rank_menu(truth, observed)[:k]) if len(observed) >= k else None
    pair_error, pair_count = pair_mse(prediction, truth, prior_order, k)
    return {
        "selected_indices": list(map(int, selected)), "baseline_selected_indices": list(map(int, base_selected)),
        "added_indices": added, "removed_indices": removed,
        "utility": utility, "baseline_utility": baseline_utility, "utility_increment": increment,
        "swap_gain": swap_gain, "selected_missing": int((~np.isfinite(truth[selected])).sum()),
        "mse": mse, "measured_per_band": counts, "pairwise_difference_mse": pair_error,
        "pairwise_observed_pairs": pair_count,
        "prior_margin_10_11": float(baseline[prior_order[k]] - baseline[prior_order[k - 1]]),
        "exact_full_menu_oracle_utility": oracle,
        "exact_full_menu_regret": oracle - utility if oracle is not None and utility is not None else None,
        "exact_oracle_status": "COMPLETE_FIXED_MENU" if oracle is not None else "UNKNOWN_MISSING_MENU_OUTCOMES",
        "observed_subset_hindsight_utility": observed_oracle,
        "full_menu_regret_lower_bound": observed_oracle - utility if observed_oracle is not None and utility is not None else None,
    }


def mean(values):
    values = [v for v in values if v is not None]
    return float(np.mean(values)) if values else None


def summarize(rows, arms, prices):
    summaries = {}
    base = {r["context"]: r for r in rows if r["arm"] == "zero_purchase"}
    for arm in arms:
        rr = [r for r in rows if r["arm"] == arm]
        complete = [r for r in rr if r["utility_increment"] is not None]
        summaries[arm] = {
            "contexts": len(rr), "paired_complete_contexts": len(complete),
            "improved": sum(r["utility_increment"] > 1e-12 for r in complete),
            "harmed": sum(r["utility_increment"] < -1e-12 for r in complete),
            "equal": sum(abs(r["utility_increment"]) <= 1e-12 for r in complete),
            "mean_utility_increment": mean(r["utility_increment"] for r in complete),
            "mean_positive_contribution": float(sum(max(0, r["utility_increment"]) for r in complete) / len(complete)) if complete else None,
            "mean_negative_contribution": float(sum(min(0, r["utility_increment"]) for r in complete) / len(complete)) if complete else None,
            "mse_improves_but_utility_harmed": sum(r["mse"]["all"] < base[r["context"]]["mse"]["all"] and r["utility_increment"] < -1e-12 for r in complete),
            "mean_mse": {name: mean(r["mse"][name] for r in rr) for name in ("all", "selected_prior", "boundary", "remainder")},
            "mean_pairwise_difference_mse": mean(r["pairwise_difference_mse"] for r in rr),
            "exact_oracle_contexts": sum(r["exact_full_menu_regret"] is not None for r in rr),
            "mean_exact_regret_complete_menu_only": mean(r["exact_full_menu_regret"] for r in rr),
            "lower_bound_contexts": sum(r["full_menu_regret_lower_bound"] is not None for r in rr),
            "mean_regret_lower_bound_complete_selection_only": mean(r["full_menu_regret_lower_bound"] for r in rr),
            "scenario_net_increment": {str(price): mean(r["utility_increment"] - price * r["resource"] for r in complete) for price in prices},
        }
    return {"status": "EXPOSED_ARCHIVE_DIAGNOSIS_COMPLETE_NO_NEW_POLICY",
            "contexts": len(base), "arm_contexts": len(rows), "arms": summaries,
            "reliability": "No coverage construction, biological independence, causal attribution or inferential interval",
            "oracle_scope": "Observed complete-menu exact regret, and observed-subset LOWER bounds on complete committed selections; neither establishes useful purchasable information",
            "progression": "Fixed-eight-probe feedback branch remains stopped; qualify a distinct evidence channel before a new study"}


def run(output):
    output = Path(output)
    if output.exists():
        raise ValueError("fresh output path required; preserve prior receipts")
    protocol = read(HERE / "PROTOCOL.json")
    verification_path = ARCHIVE.parent.parent / "review/VERIFICATION.json"
    verification = read(verification_path)
    for filename, expected in verification["files"].items():
        if sha(ARCHIVE / filename) != expected:
            raise ValueError(f"changed archived artifact: {filename}")
    freeze = read(ARCHIVE / "FREEZE.json")
    if sha(DATA) != freeze["input_sha256"]:
        raise ValueError("changed archived input")
    inputs = [HERE / "PROTOCOL.json", Path(__file__), DATA, verification_path,
              *[ARCHIVE / name for name in verification["files"]],
              ARCHIVE / "COMMIT_RECEIPT.json", ARCHIVE.parent.parent / "PROTOCOL.json"]
    output.mkdir(parents=True)
    dump(output / "FREEZE.json", {"scope": protocol["scope"],
         "files": {str(path.relative_to(ROOT)): sha(path) for path in inputs}})
    started = time.perf_counter()
    old_protocol = read(ARCHIVE.parent.parent / "PROTOCOL.json")
    arms = old_protocol["arms"]
    k = protocol["top_k"]
    with np.load(DATA, allow_pickle=False) as data:
        context_ids, roles, drug_ids = data["context_id"], data["role"], data["drug_id"]
        lineage, truth = data["lineage"], data["y"]
    with np.load(ARCHIVE / "predictions.npz", allow_pickle=False) as data:
        predictions = data["predictions"]
    commits = read(ARCHIVE / "COMMITS.json")
    probes = read(ARCHIVE / "FIT_FREEZE.json")["probe_indices"]
    indices, menu = validate_alignment(context_ids, roles, drug_ids, predictions, commits, probes, arms, k)
    rows = []
    for position, index in enumerate(indices):
        base_selected = commits[position * len(arms)]["selected_indices"]
        for arm_position, arm in enumerate(arms):
            record = commits[position * len(arms) + arm_position]
            row = diagnose_case(truth[index], predictions[position, arm_position], predictions[position, 0],
                                record["selected_indices"], base_selected, menu, k)
            if row["utility_increment"] is not None and not np.isclose(row["swap_gain"], row["utility_increment"], atol=1e-12, rtol=0):
                raise ValueError("swap decomposition does not match fixed selected-set utility")
            rows.append({"context": str(context_ids[index]), "index": int(index), "lineage": str(lineage[index]),
                         "arm": arm, "resource": record["resource"], "update_status": record["update_status"], **row})
    dump(output / "ROWS.json", rows)
    dump(output / "RESULTS.json", summarize(rows, arms, protocol["price_grid"]))
    dump(output / "RECEIPT.json", {"seconds": time.perf_counter() - started, "contexts": len(indices),
         "arm_contexts": len(rows), "source_artifact_hashes_matched": len(verification["files"]),
         "terminal_menu_count": len(menu), "terminal_menu_sha256": hashlib.sha256(menu.astype("<i8").tobytes()).hexdigest(),
         "rows_sha256": sha(output / "ROWS.json"), "results_sha256": sha(output / "RESULTS.json"),
         "new_model_fits": 0, "new_measurements": 0, "llm_calls": 0})
    print(json.dumps({"output": str(output), "contexts": len(indices), "arm_contexts": len(rows)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
