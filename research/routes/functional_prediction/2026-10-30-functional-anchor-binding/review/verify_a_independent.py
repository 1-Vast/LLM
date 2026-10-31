"""Independent contract-only verification of saved A ranks; never fits a model.

Run --self-test without reading real output arrays. The source SHA must be frozen
before the author's first real-output audit. This script deliberately does not
import the model implementation or reconstruct unsaved prediction profiles.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np


METHODS = [
    "frequency", "chemical_ridge100", "knowledge_ridge100", "joint_ridge1",
    "joint_ridge10", "joint_ridge100", "joint_rbf1", "joint_teacher32",
]
EPISODE = Path(__file__).resolve().parent.parent
REPO = EPISODE.parents[3]
EXPECTED_PYTHON = "d:/anaconda/envs/maestro/python.exe"
COMPLETE = {"COMPLETE", "COMPLETED", "SUCCESS", "OK"}


class ContractError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise ContractError(message)


def read_json(path):
    with Path(path).open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def read_npz(path):
    with np.load(path, allow_pickle=False) as archive:
        return {key: archive[key] for key in archive.files}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def numeric_equal(actual, expected, name, atol=1e-14):
    try:
        actual = np.asarray(actual, dtype=float)
        expected = np.asarray(expected, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"{name}: nonnumeric value") from exc
    require(actual.shape == expected.shape, f"{name}: shape mismatch")
    require(np.all(np.isfinite(actual)), f"{name}: nonfinite value")
    require(np.allclose(actual, expected, rtol=0, atol=atol),
            f"{name}: numerical mismatch")


def integer_equal(actual, expected, name):
    actual = np.asarray(actual)
    expected = np.asarray(expected)
    require(actual.shape == expected.shape, f"{name}: shape mismatch")
    require(actual.dtype.kind in "iu", f"{name}: requires exact integers")
    require(np.array_equal(actual, expected), f"{name}: integer mismatch")


def coherent_assignments(groups, rounds, n_draws=49):
    names = np.unique(groups)
    blocks = {name: np.flatnonzero(groups == name) for name in names}
    strata = {}
    for name in names:
        strata.setdefault(tuple(rounds[blocks[name]]), []).append(name)
    movable = sum(len(blocks[name]) for members in strata.values()
                  if len(members) > 1 for name in members)
    rng = np.random.default_rng(20261030)
    assignments = []
    for _ in range(n_draws):
        assignment = np.arange(len(groups))
        for key in sorted(strata):
            members = strata[key]
            for target, source in enumerate(rng.permutation(len(members))):
                assignment[blocks[members[target]]] = blocks[members[source]]
        assignments.append(assignment)
    return np.asarray(assignments, dtype=np.int64), movable


def score_ranks(calls, folds, indices, scores):
    n, n_genes = calls.shape
    require(indices.shape == (8, n, 20), "rank indices shape")
    require(indices.dtype.kind in "iu", "rank indices must be integers")
    require(np.all((indices >= 0) & (indices < n_genes)), "gene index out of range")
    require(scores.shape == indices.shape and scores.dtype.kind == "f", "scores shape/type")
    require(np.all(np.isfinite(scores)), "nonfinite saved score")
    require(np.all((scores >= 0) & (scores <= 1)), "scores outside clipped [0,1]")
    require(np.all(np.diff(scores, axis=2) <= 0), "scores not descending")
    tied = scores[:, :, :-1] == scores[:, :, 1:]
    require(np.all(~tied | (np.diff(indices, axis=2) > 0)), "lexical score tie order")
    require(np.all(np.diff(np.sort(indices, axis=2), axis=2) > 0), "duplicate recommendations")
    eligible_calls = np.zeros(n, dtype=np.int64)
    eligible_counts = {}
    for fold in np.unique(folds):
        query = np.flatnonzero(folds == fold)
        source = np.flatnonzero(folds != fold)
        counts = calls[source].sum(axis=0, dtype=np.int64)
        eligible = (counts >= 1) & (counts * 10 <= len(source))
        eligible_counts[str(fold)] = int(eligible.sum())
        require(eligible.sum() >= 20, f"fold {fold}: fewer than 20 eligible genes")
        require(np.all(eligible[indices[:, query]]), f"fold {fold}: ineligible recommendation")
        genes = np.flatnonzero(eligible)
        top = genes[np.lexsort((genes, -counts[genes]))][:20]
        require(np.array_equal(indices[0, query], np.broadcast_to(top, (len(query), 20))),
                f"fold {fold}: frequency exact count/lexical order")
        # Compare the once-divided values at the storage precision, never infer
        # frequency ties from sums of floating-point row means.
        frequency = (counts[top] / len(source)).astype(scores.dtype)
        require(np.array_equal(scores[0, query], np.broadcast_to(frequency, (len(query), 20))),
                f"fold {fold}: frequency scores not exact count divided once")
        eligible_calls[query] = calls[np.ix_(query, genes)].sum(axis=1, dtype=np.int64)
    hits = calls[np.arange(n)[None, :, None], indices].sum(axis=2, dtype=np.int64)
    precision = hits / 20
    recall = np.divide(hits, eligible_calls[None, :], out=np.zeros_like(precision),
                       where=eligible_calls[None, :] != 0)
    totals = hits.sum(axis=1, dtype=np.int64)
    best = int(np.argmax(totals[:7]))
    return {
        "hits": hits, "precision": precision, "recall": recall, "totals": totals,
        "best": best, "integer_gain": int(totals[7] - totals[best]),
        "oracle": np.minimum(20, eligible_calls) / 20,
        "eligible_counts": eligible_counts,
    }


def scaffold_bootstrap(differences, groups):
    names = np.unique(groups)
    sizes = np.asarray([np.sum(groups == name) for name in names], dtype=np.int64)
    sums = np.asarray([differences[groups == name].sum(dtype=np.int64)
                       for name in names], dtype=np.int64)
    rng = np.random.default_rng(20261031)
    sample = rng.integers(0, len(names), size=(2000, len(names)))
    gains = sums[sample].sum(axis=1, dtype=np.int64) / (
        20 * sizes[sample].sum(axis=1, dtype=np.int64))
    return np.percentile(gains, [2.5, 97.5])


def validate_labels(labels):
    for key in ("compounds", "genes", "calls", "folds", "groups", "rounds", "annotation_available"):
        require(key in labels, f"labels missing {key}")
    calls = labels["calls"]
    require(calls.shape == (231, 18415), "fixed development call dimensions")
    require(calls.dtype.kind in "biu" and np.all((calls == 0) | (calls == 1)), "binary calls")
    for key, n in (("compounds", 231), ("genes", 18415)):
        values = labels[key]
        require(values.shape == (n,) and values.dtype.kind in "US", f"{key} string dimensions")
        require(np.array_equal(values, np.unique(values)), f"{key} must be lexical and unique")
        require(np.all(values != ""), f"{key}: empty identity")
    for key in ("folds", "groups", "rounds", "annotation_available"):
        require(labels[key].shape == (231,), f"{key} dimensions")
    folds, counts = np.unique(labels["folds"], return_counts=True)
    require(len(folds) == 3 and sorted(counts.tolist()) == [64, 70, 97], "frozen fold sizes")
    require(labels["groups"].dtype.kind in "US", "scaffold groups must have lexical identities")
    require(len(np.unique(labels["groups"])) == 181, "181 scaffold groups")
    for group in np.unique(labels["groups"]):
        require(len(np.unique(labels["folds"][labels["groups"] == group])) == 1,
                "scaffold crosses source/query folds")
    annotation = labels["annotation_available"]
    require(annotation.dtype.kind == "b" and int(annotation.sum()) == 54, "54 frozen annotations")
    require(sorted(int(annotation[labels["folds"] == fold].sum()) for fold in folds) == [11, 19, 24],
            "frozen annotation fold counts")


def validate_metadata(run, launcher, labels_path):
    required = ("status", "threads", "completed_nulls", "python", "numpy", "failure", "access",
                "freeze", "shapes", "wall_seconds", "cpu_seconds", "settings")
    require(all(key in run for key in required), "run metadata fields missing")
    require(run["threads"] == 4, "run thread ceiling/declaration")
    settings = {"threads": 4, "null_seed": 20261030, "bootstrap_seed": 20261031,
                "n_null": 49, "n_bootstrap": 2000, "teacher_rank": 32}
    for key, value in settings.items():
        require(run["settings"].get(key) == value, f"run setting {key}")
    require(run["shapes"].get("calls") == [231, 18415], "run declared calls shape")
    require(run["shapes"].get("ranks") == [8, 231, 20], "run declared ranks shape")
    require(isinstance(run["access"], (str, dict)) and bool(run["access"]), "access boundary disclosure")
    require(isinstance(run["numpy"], str) and bool(run["numpy"]), "NumPy version disclosure")
    for record in (run, launcher):
        require(str(record.get("python", "")).replace("\\", "/").lower() == EXPECTED_PYTHON,
                "required direct environment Python")
        require(isinstance(record.get("wall_seconds"), (int, float))
                and np.isfinite(record["wall_seconds"]) and record["wall_seconds"] >= 0,
                "nonnegative finite wall time")
    require(launcher.get("timeout_seconds") == 1800, "launcher hard timeout declaration")
    require("status" in launcher and "exit_code" in launcher, "launcher status/exit metadata")
    require(launcher["wall_seconds"] <= 1810, "launcher wall time exceeds hard limit/grace")
    require(run["wall_seconds"] <= 1800, "child exceeds 1800-second hard limit")
    require(0 <= run["cpu_seconds"] <= 4 * run["wall_seconds"] + 5, "child CPU/thread accounting")
    require(run["wall_seconds"] <= launcher["wall_seconds"] + 2, "child wall exceeds launcher wall")
    pins = run["freeze"].get("sha256", {})
    require(isinstance(pins, dict) and bool(pins), "input/script freeze SHA manifest")
    pinned = set()
    for filename, digest in pins.items():
        path = Path(filename)
        if not path.is_absolute():
            path = REPO / path
        require(path.is_file(), f"pinned file missing: {filename}")
        require(isinstance(digest, str) and len(digest) == 64, f"invalid SHA pin: {filename}")
        require(sha256(path) == digest.lower(), f"pinned file changed: {filename}")
        pinned.add(path.resolve())
    for name in ("protocol_a.md", "protocol_a_v1_1.md", "a_numerical_amendment.md", "output_contract_a.md"):
        require((EPISODE / name).resolve() in pinned, f"unfrozen protocol: {name}")
    require(labels_path.resolve() in pinned, "saved development labels lack immutable SHA pin")
    require(any(path.suffix == ".py" and path != Path(__file__).resolve() for path in pinned),
            "model/launcher script pin missing")
    return sorted(str(path) for path in pinned)


def validate_teacher_records(record, expected, folds, name):
    require(isinstance(record, dict), f"{name}: teacher fold diagnostics")
    require(set(record) == set(expected), f"{name}: diagnostic fold keys")
    for fold, eligible in expected.items():
        item = record[fold]
        positive = item.get("positive_modes")
        rank = item.get("rank")
        source_n = int(np.sum(folds.astype(str) != fold))
        require(type(positive) is int and 0 <= positive <= min(18415, source_n - 1),
                f"{name}/{fold}: positive mode count")
        require(type(rank) is int and rank == min(32, positive), f"{name}/{fold}: fixed teacher rank")
        largest = item.get("largest_eigenvalue")
        require(isinstance(largest, (float, int)) and np.isfinite(largest) and largest >= 0,
                f"{name}/{fold}: largest eigenvalue")
        tolerance = 1e-10 * max(1, largest)
        numeric_equal(item.get("tolerance"), tolerance, f"{name}/{fold}: eigenvalue tolerance", 1e-15)
        require(positive == 0 or largest > tolerance, f"{name}/{fold}: positive-mode threshold")
        gap = item.get("boundary_gap")
        if positive > 32:
            require(isinstance(gap, (float, int)) and np.isfinite(gap)
                    and tolerance < gap <= largest, f"{name}/{fold}: TIED_RANK_BOUNDARY")
        else:
            require(gap is None, f"{name}/{fold}: unexpected rank-boundary gap")
        require(item.get("eligible_genes") == eligible, f"{name}/{fold}: teacher eligible count")


def verify(data_dir):
    run = read_json(data_dir / "run.json")
    launcher = read_json(data_dir / "launcher.json")
    decision = read_json(data_dir / "decision.json")
    require(decision.get("status") == "NO_HELD_OUT_RELEASE", "decision status")
    for key in ("held_out_release", "robust_benefit_established"):
        require(decision.get(key) is False, f"forbidden gate: {key}")
    pinned = validate_metadata(run, launcher, data_dir / "labels.npz")
    complete = str(run["status"]).upper() in COMPLETE and not run["failure"]
    if not complete:
        require(bool(run["failure"]), "failed/incomplete run missing failure record")
        for key in ("information_gate_pass", "conditional_interval_above_zero"):
            require(decision.get(key) is False, f"failure must force {key}=false")
        require(0 <= run["completed_nulls"] <= 49, "failure completion count")
        return {"status": "VALID_RECORDED_FAILURE", "verification_pass": True,
                "saved_rank_arithmetic_complete": False, "failure": run["failure"],
                "pinned_files": pinned}
    require(run["completed_nulls"] == 49, "completed run must finish all 49 nulls")
    require(str(launcher["status"]).upper() in COMPLETE and launcher["exit_code"] == 0,
            "completed run needs successful launcher exit")
    labels = read_npz(data_dir / "labels.npz")
    validate_labels(labels)
    ranks = read_npz(data_dir / "ranks.npz")
    require(ranks["methods"].tolist() == METHODS, "saved method order")
    assignments, movable = coherent_assignments(labels["groups"], labels["rounds"])
    integer_equal(ranks["null_assignments"], assignments, "seeded coherent null mappings")
    saved_assignments = read_npz(data_dir / "permutation_assignments.npz")
    integer_equal(saved_assignments["assignments"], assignments, "separate frozen mappings")
    require(ranks["null_indices"].shape == (49, 8, 231, 20), "49 complete null ranks")
    require(ranks["null_scores"].shape == (49, 8, 231, 20), "49 complete null scores")
    aligned = score_ranks(labels["calls"], labels["folds"], ranks["aligned_indices"], ranks["aligned_scores"])
    diagnostics = read_json(data_dir / "teacher_diagnostics.json")
    require(len(diagnostics["nulls"]) == 49, "49 null teacher diagnostics")
    validate_teacher_records(diagnostics["aligned"], aligned["eligible_counts"], labels["folds"], "aligned")
    null_integer_gains = []
    null_best = []
    for draw, assignment in enumerate(assignments):
        result = score_ranks(labels["calls"][assignment], labels["folds"],
                             ranks["null_indices"][draw], ranks["null_scores"][draw])
        null_integer_gains.append(result["integer_gain"])
        null_best.append(METHODS[result["best"]])
        validate_teacher_records(diagnostics["nulls"][draw], result["eligible_counts"],
                                 labels["folds"], f"null/{draw}")
    null_integer_gains = np.asarray(null_integer_gains, dtype=np.int64)
    denominator = 20 * len(labels["compounds"])
    gain = aligned["integer_gain"] / denominator
    null_gains = null_integer_gains / denominator
    p = (1 + int(np.sum(null_integer_gains >= aligned["integer_gain"]))) / 50
    differences = aligned["hits"][7] - aligned["hits"][aligned["best"]]
    interval = scaffold_bootstrap(differences, labels["groups"])
    summary = read_json(data_dir / "summary.json")
    require(summary.get("methods") == METHODS, "summary method order")
    numeric_equal(summary["precision"], aligned["precision"], "per-compound precision")
    numeric_equal(summary["recall"], aligned["recall"], "per-compound eligible recall")
    integer_equal(summary["recovered_totals"], aligned["totals"], "recovered call totals")
    for i, method in enumerate(METHODS):
        numeric_equal(summary["mean_precision"][method], aligned["precision"][i].mean(), f"{method} mean P20")
        numeric_equal(summary["mean_recall"][method], aligned["recall"][i].mean(), f"{method} mean recall")
        numeric_equal(summary["annotated_mean_precision"][method],
                      aligned["precision"][i, labels["annotation_available"]].mean(), f"{method} annotated P20")
    require(summary["candidate_method"] == METHODS[7], "fixed candidate")
    require(summary["best_direct_method"] == METHODS[aligned["best"]], "exact integer direct selection")
    integer_equal(summary["selected_integer_gain"], aligned["integer_gain"], "aligned integer gain")
    integer_equal(summary["null_integer_gains"], null_integer_gains, "null integer gains")
    numeric_equal(summary["selected_gain"], gain, "selected mean gain")
    numeric_equal(summary["null_gains"], null_gains, "49 null mean gains")
    numeric_equal(summary["permutation_p"], p, "integer null p")
    numeric_equal(summary["oracle"], aligned["oracle"], "source-eligible oracle")
    numeric_equal(summary["mean_oracle"], aligned["oracle"].mean(), "mean oracle")
    require(summary["eligible_gene_counts"] == aligned["eligible_counts"], "source eligible gene counts")
    distinct = len(np.unique(assignments, axis=0))
    require(summary["distinct_mappings"] == distinct, "distinct mapping count")
    require(summary["movable_compounds"] == movable, "movable compound count")
    information_gate = aligned["integer_gain"] > 0 and p <= .05
    require(decision.get("information_gate_pass") is information_gate, "information gate conjunction")
    numeric_equal(decision["paired_scaffold_interval95"], interval, "integer scaffold bootstrap interval")
    require(decision.get("conditional_interval_above_zero") is bool(interval[0] > 0), "conditional interval gate")
    return {
        "status": "PASS", "verification_pass": True, "saved_rank_arithmetic_complete": True,
        "candidate_method": METHODS[7], "best_direct_method": METHODS[aligned["best"]],
        "recovered_totals": aligned["totals"].tolist(), "selected_integer_gain": aligned["integer_gain"],
        "selected_gain": gain, "null_integer_gains": null_integer_gains.tolist(),
        "null_best_direct_methods": null_best, "permutation_p": p,
        "paired_scaffold_interval95": interval.tolist(), "information_gate_pass": information_gate,
        "distinct_mappings": distinct, "movable_compounds": movable,
        "changed_compounds_per_mapping": np.sum(assignments != np.arange(231), axis=1).tolist(),
        "pinned_files": pinned,
    }


def self_test():
    # Synthetic data only: exact frequency ties, integer zero-gain null comparison,
    # coherent whole-scaffold assignments and unequal-size cluster bootstrap.
    groups = np.asarray(["a", "a", "b", "b", "c"])
    rounds = np.asarray([1, 2, 1, 2, 3])
    maps, movable = coherent_assignments(groups, rounds, n_draws=49)
    require(movable == 4, "synthetic mobility")
    require(np.all(maps[:, 4] == 4), "synthetic immovable scaffold")
    require(np.all((maps[:, :2] == [0, 1]).all(axis=1) | (maps[:, :2] == [2, 3]).all(axis=1)),
            "synthetic ordered whole-scaffold mapping")
    require(np.all(np.sort(maps, axis=1) == np.arange(5)), "synthetic mapping bijection")
    counts = np.asarray([2, 1, 2, 0], dtype=np.int64)
    require(np.array_equal(np.lexsort((np.arange(4), -counts)), [0, 2, 1, 3]), "synthetic exact ties")
    calls = np.zeros((40, 30), dtype=np.uint8)
    for i in range(40):
        calls[i, i % 20] = 1
        calls[i, i % 20 + 10] = 1
    folds = np.repeat([0, 1], 20)
    top = np.r_[np.arange(10, 20), np.arange(10)]
    indices = np.broadcast_to(top, (8, 40, 20)).copy()
    scores = np.broadcast_to(np.r_[np.full(10, .1), np.full(10, .05)], (8, 40, 20)).copy()
    scored = score_ranks(calls, folds, indices, scores)
    integer_equal(scored["totals"], np.full(8, 60), "synthetic recovered calls")
    numeric_equal(scored["precision"].mean(), .075, "synthetic P20")
    numeric_equal(scored["recall"].mean(), .75, "synthetic eligible recall")
    numeric_equal(scored["oracle"], np.full(40, .1), "synthetic oracle")
    require(scored["eligible_counts"] == {"0": 30, "1": 30}, "synthetic eligible universe")
    malformed = indices.copy()
    malformed[0, 0, -2:] = malformed[0, 0, -2:][::-1]
    try:
        score_ranks(calls, folds, malformed, scores)
    except ContractError:
        pass
    else:
        raise ContractError("synthetic lexical-tie violation was accepted")
    totals = np.asarray([2, 2, 1, 0, 2, 1, 1, 2], dtype=np.int64)
    require(np.argmax(totals[:7]) == 0, "synthetic direct tie takes first")
    require((1 + np.sum(np.zeros(49, dtype=np.int64) >= 0)) / 50 == 1, "synthetic null ties included")
    differences = np.asarray([1, -1, 2, 0, -1], dtype=np.int64)
    interval = scaffold_bootstrap(differences, groups)
    rng = np.random.default_rng(20261031)
    manual = []
    for _ in range(2000):
        selected = rng.integers(0, 3, size=3)
        manual.append(sum([0, 2, -1][i] for i in selected) /
                      (20 * sum([2, 2, 1][i] for i in selected)))
    numeric_equal(interval, np.percentile(manual, [2.5, 97.5]), "synthetic bootstrap")
    return {"status": "SELF_TEST_PASS", "real_output_arrays_read": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=REPO / "data/processed/functional_anchor_binding_20261030/a")
    parser.add_argument("--report", type=Path, default=Path(__file__).with_name("a_arithmetic_verification.json"))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        result = self_test() if args.self_test else verify(args.data_dir)
    except (ContractError, OSError, KeyError, TypeError, ValueError) as exc:
        result = {"status": "FAIL", "verification_pass": False, "error": str(exc)}
    result["verifier_sha256"] = sha256(__file__)
    result["limitations"] = [
        "Saved Top20 audit only; no refit or certification of full unsaved predictions.",
        "No independent certification of label ancestry, access history, teacher eigensolutions, or biology.",
        "Supplied freeze hashes checked; independent completeness of source inventory is not established.",
        "Exploratory exposed-development arithmetic cannot authorize held-out release or robust benefit.",
    ]
    if not args.self_test:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("verification_pass", result["status"] == "SELF_TEST_PASS") else 1


if __name__ == "__main__":
    sys.exit(main())
