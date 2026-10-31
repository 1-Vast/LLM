"""Independently verify frozen Stage1 output arithmetic; never fit a model.

Authored before numerical access. See stage1_independent_preaccess_freeze.json.
The chemistry checks concern saved selections and scores, not unsaved predictions.
"""

import argparse
import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np


METHODS = ["frequency", "nearest5", "ridge1", "ridge10", "ridge100"]
N, G, K, PERMUTATIONS = 231, 18415, 20, 49
NULL_SEED, BOOTSTRAP_SEED, BOOTSTRAPS = 20261030, 20261031, 2000
SPLIT_HASH = "6457a9e411afed38c0a56cdeff88ccea57c8d7abb7b6131a654243a73d0df8f2"
GENE_IDS_HASH = "cca1ac12566776c4eaf597e3548a583f70b05ac49d44ce62aafd8044f2fa7ba2"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def string_vector(array, size, name):
    require(array.shape == (size,), f"{name}: expected shape {(size,)}, got {array.shape}")
    require(array.dtype.kind in "US", f"{name}: requires a string dtype, not object/pickle")
    return array.astype(str)


def integer_array(array, shape, name):
    require(array.shape == shape, f"{name}: expected shape {shape}, got {array.shape}")
    require(array.dtype.kind in "iu", f"{name}: requires integer dtype")
    return array.astype(np.int64, copy=False)


def load_npz(path, keys):
    with np.load(path, allow_pickle=False) as saved:
        require(set(keys) <= set(saved.files), f"{path.name}: missing {set(keys) - set(saved.files)}")
        return {key: saved[key] for key in keys}


def frozen_metadata(args):
    manifest = read_json(args.freeze)
    require(sha256(__file__) == manifest["verifier_sha256"], "Verifier differs from its pre-access freeze")
    for relative, expected in manifest["input_sha256"].items():
        require(sha256(args.episode / relative) == expected, f"Frozen metadata changed: {relative}")
    identity = read_json(args.episode / "identity_freeze.json")
    gene_freeze = read_json(args.episode / "gene_universe_freeze.json")
    require(identity["split_sha256"] == SPLIT_HASH, "Unexpected identity split freeze")
    require(gene_freeze["included_gene_count"] == G, "Unexpected gene-universe size")
    require(gene_freeze["included_gene_ids_sha256"] == GENE_IDS_HASH, "Unexpected gene-universe freeze")
    split_path = args.episode / "identity_split.tsv"
    require(sha256(split_path) == SPLIT_HASH, "Identity split bytes do not match original freeze")
    with split_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    representatives = [row for row in rows if row["representative"] == "True"]
    development = {row["compound"]: row for row in representatives if row["partition"] == "development"}
    held_out = {row["compound"] for row in representatives if row["partition"] == "held_out"}
    require(len(representatives) == 294 and len(development) == N and len(held_out) == 63,
            "Frozen representative/partition count mismatch")
    require(set(development).isdisjoint(held_out), "Development and held-out IDs overlap")
    return development, held_out


def block_plan(compounds, groups, rounds):
    blocks = [np.flatnonzero(groups == group) for group in sorted(set(groups.tolist()))]
    blocks = [block[np.argsort(compounds[block], kind="stable")] for block in blocks]
    strata = defaultdict(list)
    for block in blocks:
        strata[tuple(rounds[block].tolist())].append(block)
    return blocks, strata


def expected_assignments(strata):
    rng = np.random.default_rng(NULL_SEED)
    assignments = np.empty((PERMUTATIONS, N), dtype=np.int64)
    for replicate in range(PERMUTATIONS):
        mapping = np.arange(N)
        for stratum in sorted(strata):
            blocks = strata[stratum]
            order = rng.permutation(len(blocks))
            for destination, source_index in zip(blocks, order):
                mapping[destination] = blocks[int(source_index)]
        assignments[replicate] = mapping
    return assignments


def check_assignments(assignments, expected, blocks, groups, rounds):
    block_by_group = {groups[block[0]]: block for block in blocks}
    for replicate, mapping in enumerate(assignments):
        require(np.array_equal(np.sort(mapping), np.arange(N)), f"Null {replicate}: not a full permutation")
        require(np.array_equal(rounds[mapping], rounds), f"Null {replicate}: round identity changed")
        for destination in blocks:
            source_rows = mapping[destination]
            source_groups = set(groups[source_rows].tolist())
            require(len(source_groups) == 1, f"Null {replicate}: scaffold block split")
            source_group = next(iter(source_groups))
            source_block = block_by_group[source_group]
            require(np.array_equal(source_rows, source_block),
                    f"Null {replicate}: incomplete source block or compound-position order changed")
    require(np.array_equal(assignments, expected), "Null assignments differ from frozen seed/ordering convention")


def source_eligibility(truth, folds):
    masks, counts = {}, {}
    for fold in range(3):
        training = folds != fold
        hits = truth[training].sum(axis=0, dtype=np.int64)
        masks[fold] = (hits > 0) & (10 * hits <= int(training.sum()))
        counts[fold] = hits
    return masks, counts


def verify_selection(indices, scores, truth, folds, eligible, source_counts, name):
    require(indices.shape == (len(METHODS), N, K), f"{name}: incomplete method/query/selection axes")
    require(scores.shape == indices.shape and scores.dtype.kind == "f", f"{name}: invalid score shape/dtype")
    require(np.isfinite(scores).all(), f"{name}: non-finite selected score")
    require(((scores >= 0) & (scores <= 1)).all(), f"{name}: selected score outside [0,1]")
    require(((indices >= 0) & (indices < G)).all(), f"{name}: out-of-universe gene index")
    require((np.diff(np.sort(indices, axis=2), axis=2) != 0).all(), f"{name}: duplicate gene selection")
    require((scores[:, :, :-1] >= scores[:, :, 1:]).all(), f"{name}: scores not descending")
    ties = scores[:, :, :-1] == scores[:, :, 1:]
    require((~ties | (indices[:, :, :-1] < indices[:, :, 1:])).all(), f"{name}: non-lexical score tie")
    eligible_truth = np.empty(N, dtype=np.int64)
    for fold in range(3):
        query = np.flatnonzero(folds == fold)
        require(eligible[fold][indices[:, query, :]].all(), f"{name}/fold {fold}: source-ineligible gene selected")
        eligible_truth[query] = truth[np.ix_(query, np.flatnonzero(eligible[fold]))].sum(axis=1, dtype=np.int64)
        available = np.flatnonzero(eligible[fold])
        frequency_order = available[np.lexsort((available, -source_counts[fold][available]))][:K]
        require(np.array_equal(indices[0, query, :], np.broadcast_to(frequency_order, (len(query), K))),
                f"{name}/fold {fold}: frequency top20 differs from source counts/lexical ties")
        frequency_scores = source_counts[fold][frequency_order] / int((folds != fold).sum())
        score_tolerance = max(1e-12, 4 * np.finfo(scores.dtype).eps)
        require(np.allclose(scores[0, query, :], frequency_scores, rtol=0, atol=score_tolerance),
                f"{name}/fold {fold}: frequency scores do not reproduce source counts")
    hits = np.stack([truth[np.arange(N)[:, None], selected].sum(axis=1, dtype=np.int64) for selected in indices])
    precision = hits / K
    recall = np.divide(hits, eligible_truth[None, :], out=np.zeros(hits.shape, dtype=float),
                       where=eligible_truth[None, :] != 0)
    oracle = np.minimum(K, eligible_truth) / K
    return hits, precision, recall, oracle, eligible_truth


def bootstrap_interval(per_compound_gain, blocks):
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    draws = np.empty(BOOTSTRAPS)
    for draw in range(BOOTSTRAPS):
        sampled = rng.integers(0, len(blocks), size=len(blocks))
        members = np.concatenate([blocks[int(index)] for index in sampled])
        draws[draw] = per_compound_gain[members].mean()
    return np.quantile(draws, [0.025, 0.975], method="linear"), draws


def compare_root(summary, decision, root_summary, root_decision):
    expected_summary = read_json(root_summary)
    expected_decision = read_json(root_decision)
    comparisons = []

    def same(actual, expected, field):
        require(np.asarray(actual).shape == np.asarray(expected).shape, f"Root {field}: shape mismatch")
        require(np.allclose(actual, expected, rtol=0, atol=1e-12), f"Root {field}: numerical mismatch")
        comparisons.append(field)

    for method in METHODS:
        for field in ("p_at_20", "per_compound_p_at_20", "recall", "per_compound_recall"):
            same(summary["methods"][method][field], expected_summary["methods"][method][field], f"{method}.{field}")
    for field in ("p_at_20", "per_compound_p_at_20"):
        same(summary["oracle"][field], expected_summary["oracle"][field], f"oracle.{field}")
    require(summary["source_eligible_genes"] == expected_summary["source_eligible_genes"], "Root eligibility counts differ")
    require(summary["best_method"] == expected_summary["best_method"], "Root selected method differs")
    for field in ("null_maximum_gains", "permutation_p", "selected_gain"):
        same(summary[field], expected_summary[field], field)
    for field in ("status", "information_gate_pass", "held_out_release", "conditional_interval_above_zero", "robust_benefit_established"):
        require(decision[field] == expected_decision[field], f"Root decision.{field} differs")
    same(decision["paired_scaffold_interval95"], expected_decision["paired_scaffold_interval95"], "paired_scaffold_interval95")
    return {"status": "MATCH", "numeric_fields": comparisons,
            "root_summary_sha256": sha256(root_summary), "root_decision_sha256": sha256(root_decision)}


def verify(args, audit):
    development, held_out = frozen_metadata(args)
    label_path, rank_path = args.data_dir / "labels.npz", args.data_dir / "ranks.npz"
    labels = load_npz(label_path, ["compounds", "genes", "calls", "folds", "groups", "rounds"])
    audit["labels_sha256"] = sha256(label_path)
    compounds = string_vector(labels["compounds"], N, "compounds")
    genes = string_vector(labels["genes"], G, "genes")
    groups = string_vector(labels["groups"], N, "groups")
    rounds = string_vector(labels["rounds"], N, "rounds")
    folds = integer_array(labels["folds"], (N,), "folds")
    calls = labels["calls"]
    require(calls.shape == (N, G) and calls.dtype == np.dtype(bool), "Calls must be boolean (231,18415)")
    require(len(set(compounds.tolist())) == N and set(compounds.tolist()) == set(development), "Incorrect development identity set")
    require(set(compounds.tolist()).isdisjoint(held_out), "Held-out identity found in numerical labels")
    require(genes.tolist() == sorted(set(genes.tolist())), "Canonical genes are not unique and lexical")
    gene_hash = hashlib.sha256("\n".join(genes.tolist()).encode("utf-8")).hexdigest()
    require(gene_hash == GENE_IDS_HASH, "Canonical gene IDs differ from fixed universe")
    for row_index, compound in enumerate(compounds):
        metadata = development[compound]
        require(groups[row_index] == metadata["group_hash"], f"Group metadata mismatch: {compound}")
        require(rounds[row_index] == metadata["round"], f"Round metadata mismatch: {compound}")
        require(folds[row_index] == int(metadata["development_fold"]), f"Fold metadata mismatch: {compound}")
    require({int(fold): int((folds == fold).sum()) for fold in set(folds)} == {0: 70, 1: 97, 2: 64}, "Fold coverage differs")
    require(len(set(groups.tolist())) == 181, "Development scaffold-group count differs")
    for group in set(groups.tolist()):
        require(len(set(folds[groups == group].tolist())) == 1, "Scaffold group spans folds")
    blocks, strata = block_plan(compounds, groups, rounds)
    planned_assignments = expected_assignments(strata)
    truths = [calls] + [calls[mapping] for mapping in planned_assignments]
    eligibility = [source_eligibility(truth, folds) for truth in truths]
    unsupported = [{"label_assignment": "aligned" if index == 0 else f"null_{index - 1}",
                    "fold": fold, "eligible_genes": int(mask.sum())}
                   for index, (masks, _) in enumerate(eligibility) for fold, mask in masks.items() if int(mask.sum()) < K]
    audit["unsupported_sources"] = unsupported
    require(not unsupported, "TERMINAL_INSUFFICIENT_SUPPORT: at least one aligned/null source fold has fewer than20 eligible genes")
    ranks = load_npz(rank_path, ["methods", "aligned_indices", "aligned_scores", "null_indices", "null_scores", "null_assignments"])
    audit["ranks_sha256"] = sha256(rank_path)
    require(string_vector(ranks["methods"], 5, "methods").tolist() == METHODS, "Method panel/order differs")
    aligned_indices = integer_array(ranks["aligned_indices"], (5, N, K), "aligned_indices")
    null_indices = integer_array(ranks["null_indices"], (PERMUTATIONS, 5, N, K), "null_indices")
    null_scores = ranks["null_scores"]
    require(null_scores.shape == (PERMUTATIONS, 5, N, K), "Incomplete null scores")
    assignments = integer_array(ranks["null_assignments"], (PERMUTATIONS, N), "null_assignments")
    check_assignments(assignments, planned_assignments, blocks, groups, rounds)
    metrics = [verify_selection(aligned_indices, ranks["aligned_scores"], calls, folds, *eligibility[0], "aligned")]
    for replicate in range(PERMUTATIONS):
        metrics.append(verify_selection(null_indices[replicate], null_scores[replicate], truths[replicate + 1], folds,
                                        *eligibility[replicate + 1], f"null {replicate}"))
    aligned_hits, precision, recall, oracle, eligible_truth = metrics[0]
    aligned_totals = aligned_hits.sum(axis=1)
    best_index = 1 + int(np.argmax(aligned_totals[1:]))
    observed_gain_count = int(aligned_totals[best_index] - aligned_totals[0])
    null_totals = np.stack([metric[0].sum(axis=1) for metric in metrics[1:]])
    null_best = 1 + np.argmax(null_totals[:, 1:], axis=1)
    null_gain_counts = null_totals[np.arange(PERMUTATIONS), null_best] - null_totals[:, 0]
    extreme = int((null_gain_counts >= observed_gain_count).sum())
    p_value = (1 + extreme) / (PERMUTATIONS + 1)
    gain = observed_gain_count / (N * K)
    per_compound_gain = (aligned_hits[best_index] - aligned_hits[0]) / K
    interval, bootstrap_draws = bootstrap_interval(per_compound_gain, blocks)
    summary = {
        "compounds": compounds.tolist(), "methods": {},
        "source_eligible_genes": {str(fold): int(mask.sum()) for fold, mask in eligibility[0][0].items()},
        "oracle": {"p_at_20": float(oracle.mean()), "per_compound_p_at_20": oracle.tolist()},
        "per_compound_eligible_truth_calls": eligible_truth.tolist(), "best_method": METHODS[best_index],
        "selected_gain": gain, "null_best_methods": [METHODS[int(index)] for index in null_best],
        "null_maximum_gains": (null_gain_counts / (N * K)).tolist(),
        "null_extreme_count_including_ties": extreme, "permutation_p": p_value,
        "bootstrap_group_order": "lexical scaffold-group hash", "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_draws": BOOTSTRAPS,
    }
    for index, method in enumerate(METHODS):
        summary["methods"][method] = {"p_at_20": float(precision[index].mean()),
                                      "per_compound_p_at_20": precision[index].tolist(),
                                      "recall": float(recall[index].mean()),
                                      "per_compound_recall": recall[index].tolist()}
    decision = {"status": "NO_HELD_OUT_RELEASE", "information_gate_pass": bool(gain > 0 and p_value <= 0.05),
                "held_out_release": False, "paired_scaffold_interval95": interval.tolist(),
                "conditional_interval_above_zero": bool(interval[0] > 0), "robust_benefit_established": False}
    audit.update({"arithmetic_status": "PASS", "N": N, "G": G, "methods": METHODS, "permutations": PERMUTATIONS,
                  "distinct_mappings": int(np.unique(assignments, axis=0).shape[0]),
                  "strata": len(strata), "fixed_singleton_strata": sum(len(value) == 1 for value in strata.values()),
                  "movable_blocks": sum(len(value) for value in strata.values() if len(value) > 1),
                  "movable_compounds": sum(len(block) for value in strata.values() if len(value) > 1 for block in value),
                  "assignment_sha256": [hashlib.sha256(row.astype("<i8").tobytes()).hexdigest() for row in assignments],
                  "input_shapes": {key: list(value.shape) for key, value in labels.items()},
                  "rank_shapes": {key: list(value.shape) for key, value in ranks.items()}})
    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "decision.json", decision)
    np.savez_compressed(args.output_dir / "metrics.npz", aligned_hits=aligned_hits, aligned_precision=precision,
                        aligned_recall=recall, aligned_oracle=oracle, bootstrap_gain=bootstrap_draws,
                        null_hits=np.stack([metric[0] for metric in metrics[1:]]),
                        null_recall=np.stack([metric[2] for metric in metrics[1:]]),
                        null_oracle=np.stack([metric[3] for metric in metrics[1:]]),
                        null_source_eligibility_counts=np.array([[int(masks[fold].sum()) for fold in range(3)]
                                                               for masks, _ in eligibility[1:]]),
                        null_gain_counts=null_gain_counts, null_assignments=assignments)
    if args.compare_root:
        audit["root_comparison"] = compare_root(summary, decision, args.data_dir / "summary.json", args.data_dir / "decision.json")
    return summary, decision


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    episode = Path(__file__).resolve().parent.parent
    parser.add_argument("--episode", type=Path, default=episode)
    parser.add_argument("--data-dir", type=Path, default=Path("D:/MAESTRO/data/processed/conditional_interventions_20261030/cgi/stage1"))
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent / "independent_metrics")
    parser.add_argument("--freeze", type=Path, default=Path(__file__).resolve().parent / "stage1_independent_preaccess_freeze.json")
    parser.add_argument("--compare-root", action="store_true", help="Also compare root summary/decision using the pre-access schema")
    args = parser.parse_args()
    require(args.output_dir.resolve() != args.data_dir.resolve(), "Independent outputs must have their own directory")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    audit = {"arithmetic_status": "NOT_COMPLETED", "verifier_sha256": sha256(__file__),
             "scope": "Output arithmetic/completeness only; no refit, biological truth, label construction, leakage, practical-benefit or secure-blinding certification",
             "held_out_policy": "NO_HELD_OUT_RELEASE"}
    try:
        summary, decision = verify(args, audit)
        write_json(args.output_dir / "audit.json", audit)
        print(json.dumps({"arithmetic_status": audit["arithmetic_status"], "best_method": summary["best_method"],
                          "selected_gain": summary["selected_gain"], "permutation_p": summary["permutation_p"],
                          "decision": decision, "output_dir": str(args.output_dir)}, allow_nan=False))
        return 0
    except Exception as error:
        audit["arithmetic_status"] = "TERMINAL_INSUFFICIENT_SUPPORT" if audit.get("unsupported_sources") else "FAIL"
        audit["error"] = f"{type(error).__name__}: {error}"
        write_json(args.output_dir / "audit.json", audit)
        print(audit["error"], file=sys.stderr)
        return 2 if audit["arithmetic_status"] == "TERMINAL_INSUFFICIENT_SUPPORT" else 1


if __name__ == "__main__":
    sys.exit(main())
