"""Frozen contract-only B arithmetic checker; no raw-profile reads or model fits.

The author has seen the separate A results. B implementation, phenotype
features and outputs must remain unopened until this source has a hash receipt.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np


METHODS = [
    "fixed_same", "fixed_opposite", "global_mean", "gene_shrink10",
    "pooled_ridge100", "pooled_rbf1", "conditional_ridge100", "conditional_rbf1",
    "cell_mean", "gene_cell_shrink10", "spatial_ridge100", "conditional_spatial_ridge100",
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
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def read_tsv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_npz(path):
    with np.load(path, allow_pickle=False) as archive:
        return {key: archive[key] for key in archive.files}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def close(actual, expected, name):
    try:
        actual = np.asarray(actual, dtype=np.float64)
        expected = np.asarray(expected, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"{name}: nonnumeric value") from exc
    require(actual.shape == expected.shape, f"{name}: shape mismatch")
    require(np.all(np.isfinite(actual)), f"{name}: nonfinite value")
    require(np.allclose(actual, expected, rtol=0, atol=1e-12), f"{name}: numerical mismatch")


def reconstruct_groups(rows, structure):
    ids = [row["broad_sample"] for row in rows]
    parent = {item: item for item in ids}

    def find(item):
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    tables = {key: {} for key in ("same_name_group", "exact_InChIKey_group", "connectivity_block_group")}
    for item in ids:
        require(item in structure, f"missing structure identity: {item}")
        for key, seen in tables.items():
            value = structure[item][key]
            if value and value.upper() not in {"NA", "NAN", "NONE"}:
                if value in seen:
                    first, second = find(item), find(seen[value])
                    parent[max(first, second)] = min(first, second)
                else:
                    seen[value] = item
    components = {}
    for item in ids:
        components.setdefault(find(item), []).append(item)
    names = {item: min(members) for members in components.values() for item in members}
    return np.asarray([names[item] for item in ids])


def metadata():
    freeze_path = EPISODE / "b_metadata_freeze.json"
    freeze = read_json(freeze_path)
    require(freeze["phase"] == "before_phenotype_values" and freeze["phenotype_values_opened"] is False,
            "prephenotype metadata freeze declaration")
    for filename, expected in freeze["sha256"].items():
        require(sha256(filename) == expected, f"metadata input changed: {filename}")
    rows = read_tsv(EPISODE / "b_compound_split.tsv")
    compounds = np.asarray([row["broad_sample"] for row in rows])
    require(len(rows) == 260 and np.array_equal(compounds, np.unique(compounds)), "260 lexical unique source IDs")
    require(all(row["pert_type"] == "trt" for row in rows), "positive/control role in compound split")
    structures = read_tsv(EPISODE / "cpjump_source/compound_structure_grouping.tsv")
    structure = {row["broad_sample"]: row for row in structures}
    require(len(structure) == len(structures), "duplicate source structure identities")
    groups = reconstruct_groups(rows, structure)
    require(np.array_equal(groups, [row["group"] for row in rows]), "transitive source identity group closure")
    require(len(np.unique(groups)) == 255, "255 identity groups")
    folds = np.asarray([int(hashlib.sha256(("20261030|" + group).encode()).hexdigest(), 16) % 5
                        for group in groups], dtype=np.int64)
    require(np.array_equal(folds, [int(row["fold"]) for row in rows]), "frozen SHA compound-group folds")
    expected_counts = {str(fold): int(np.sum(folds == fold)) for fold in range(5)}
    require(expected_counts == {"0": 47, "1": 56, "2": 56, "3": 52, "4": 49}, "frozen fold counts")
    require(freeze["fold_counts"] == expected_counts, "metadata freeze fold declarations")
    require(freeze["queries"] == 260 and freeze["groups"] == 255 and freeze["names"] == 256,
            "metadata freeze population counts")
    require(len({row["pert_iname"] for row in rows}) == 256, "256 frozen source names")
    targets = np.asarray([row["target"] for row in rows])
    genes = np.unique(targets)
    require(len(genes) == 130, "130 nominal reference targets")
    wells = read_tsv(EPISODE / "cpjump_source/selected_well_identity_freeze.tsv")
    plate_ids = sorted({row["Metadata_Plate"] for row in wells})
    require(len(plate_ids) == 8 and len(wells) == 3072, "eight frozen 384-well metadata plates")
    expected = {}
    for plate in plate_ids:
        records = [row for row in wells if row["Metadata_Plate"] == plate]
        require(len(records) == 384 and len({row["Metadata_Well"] for row in records}) == 384,
                f"{plate}: complete unique well identities")
        contexts = {(row["Metadata_experiment_type"], row["Metadata_cell_line"], row["Metadata_timepoint"])
                    for row in records}
        require(len(contexts) == 1, f"{plate}: mixed metadata context")
        modality, cell, time = next(iter(contexts))
        require(modality in {"Compound", "ORF"} and cell in {"A549", "U2OS"} and time == "48",
                f"{plate}: inadmissible context")
        controls = [row for row in records if row["Metadata_pert_type"] == "control"
                    and row["Metadata_control_type"] == "negcon"]
        treatments = [row for row in records if row["Metadata_pert_type"] == "trt" and
                      ((modality == "Compound" and row["Metadata_broad_sample"] in compounds)
                       or (modality == "ORF" and row["Metadata_gene"] in genes))]
        require(len(treatments) == 260, f"{plate}: admitted treatment count")
        require(len(controls) == (64 if modality == "Compound" else 60), f"{plate}: negative controls")
        if modality == "Compound":
            require(sorted(row["Metadata_broad_sample"] for row in treatments) == compounds.tolist(),
                    f"{plate}: one chemical well per ID")
        else:
            require(all(sum(row["Metadata_gene"] == gene for row in treatments) == 2 for gene in genes),
                    f"{plate}: two ORF wells per target")
        expected[plate] = {"cell": cell, "modality": modality, "control_rows": len(controls),
                           "treatment_rows": len(treatments), "decoded_rows": len(controls) + len(treatments),
                           "skipped_rows": len(records) - len(controls) - len(treatments),
                           "allowed_wells": sorted(row["Metadata_Well"] for row in controls + treatments)}
    for cell in ("A549", "U2OS"):
        for modality in ("Compound", "ORF"):
            require(sum(item["cell"] == cell and item["modality"] == modality for item in expected.values()) == 2,
                    "two lexical plates per modality/cell")
    supported = sum(bool(np.any(targets[folds != folds[i]] == targets[i])) for i in range(260))
    require(supported == 198, "198 source-target-supported source IDs")
    return {"compounds": compounds, "groups": groups, "folds": folds, "targets": targets,
            "genes": genes, "plate_ids": plate_ids, "plates": expected, "supported": supported,
            "metadata_freeze": freeze_path}


def validate_run(run, launcher, expected):
    keys = ("status", "threads", "completed_folds", "python", "numpy", "settings", "freeze",
            "shapes", "failure", "wall_seconds", "cpu_seconds")
    require(all(key in run for key in keys), "run fields incomplete")
    require(run["threads"] == 4, "four declared compute threads")
    for key, value in {"n_bootstrap": 2000, "bootstrap_seed": 20261032, "alpha_ridge": 100, "alpha_rbf": 1}.items():
        require(run["settings"].get(key) == value, f"frozen setting {key}")
    require(run["shapes"].get("relations") == [260, 2], "declared relation shape")
    require(run["shapes"].get("predictions") == [12, 260, 2], "declared prediction shape")
    require(isinstance(run["numpy"], str) and bool(run["numpy"]), "recorded NumPy version")
    for record in (run, launcher):
        require(str(record.get("python", "")).replace("\\", "/").lower() == EXPECTED_PYTHON,
                "direct required Python environment")
        require(isinstance(record.get("wall_seconds"), (int, float)) and np.isfinite(record["wall_seconds"])
                and record["wall_seconds"] >= 0, "finite nonnegative wall time")
    require(launcher.get("timeout_seconds") == 1800 and "exit_code" in launcher and "status" in launcher,
            "hard launcher timeout/exit metadata")
    require(run["wall_seconds"] <= 1800 and launcher["wall_seconds"] <= 1810, "hard wall limit/grace")
    require(run["wall_seconds"] <= launcher["wall_seconds"] + 2, "child versus launcher wall time")
    require(0 <= run["cpu_seconds"] <= 4 * run["wall_seconds"] + 5, "CPU/thread accounting")
    pins = run["freeze"].get("sha256", {})
    require(isinstance(pins, dict) and bool(pins), "preexecution SHA manifest")
    paths = {Path(filename).resolve(): digest for filename, digest in pins.items()}
    raw_paths = {}
    for path, digest in paths.items():
        require(isinstance(digest, str) and len(digest) == 64
                and all(ch in "0123456789abcdef" for ch in digest.lower()), "SHA-256 digest syntax")
        matches = [plate for plate in expected["plate_ids"] if plate in str(path)]
        if matches and path.suffix.lower() in {".csv", ".gz"}:
            require(len(matches) == 1 and matches[0] not in raw_paths, "unique admitted raw path per plate")
            raw_paths[matches[0]] = str(path)
        else:
            require(path.is_file() and sha256(path) == digest.lower(), f"changed nonraw preexecution pin: {path}")
    require(set(raw_paths) == set(expected["plate_ids"]), "eight raw-profile SHA declarations")
    for name in ("protocol_b.md", "protocol_b_v1_1.md", "output_contract_b.md", "b_compound_split.tsv",
                 "b_metadata_freeze.json", "b_chemical_features.npz"):
        require((EPISODE / name).resolve() in paths, f"missing preexecution input pin: {name}")
    for path in (EPISODE / "cpjump_source/compound_structure_grouping.tsv",
                 EPISODE / "cpjump_source/selected_well_identity_freeze.tsv", Path(__file__)):
        require(path.resolve() in paths, f"missing metadata/checker pin: {path}")
    require(any(path.name == "source_manifest.tsv" for path in paths), "missing original source manifest pin")
    return raw_paths


def validate_access(access, expected, raw_paths):
    require(str(access.get("status")).upper() in COMPLETE, "completed source-access receipt")
    require(access.get("all_hashes_checked") is True, "loader raw hash check declaration")
    require(access.get("protected_CGI_access") is False, "protected CGI access declaration")
    require(set(access["per_plate"]) == set(expected["plate_ids"]), "receipt plate population")
    decoded = skipped = 0
    for plate, item in expected["plates"].items():
        actual = access["per_plate"][plate]
        for key in ("decoded_rows", "control_rows", "treatment_rows", "skipped_rows"):
            require(type(actual.get(key)) is int and actual[key] == item[key], f"{plate}: receipt {key}")
        require(sorted(actual["allowed_wells"]) == item["allowed_wells"], f"{plate}: admitted row identities")
        require(Path(actual["path"]).resolve() == Path(raw_paths[plate]), f"{plate}: admitted original path")
        decoded += actual["decoded_rows"]
        skipped += actual["skipped_rows"]
    require(access.get("decoded_rows") == decoded == 2576, "decoded row total")
    require(access.get("skipped_rows") == skipped == 496, "skipped row total")
    require(access.get("decoded_numeric_cells") == decoded * 5792, "decoded numeric cell total")


def cosine_grid(chemical, orf, target_indices):
    matched = orf[target_indices]
    numerator = np.einsum("icpf,icqf->icpq", chemical, matched)
    denominator = np.linalg.norm(chemical, axis=-1)[..., :, None] * np.linalg.norm(matched, axis=-1)[..., None, :]
    return np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator != 0)


def validate_preprocessing(pre, expected):
    names, mask = pre["feature_names"], pre["retained_mask"]
    require(names.shape == (5792,) and names.dtype.kind in "US" and len(np.unique(names)) == 5792,
            "5792 unique frozen feature headers")
    require(mask.shape == (5792,) and mask.dtype.kind == "b", "boolean control-only feature mask")
    p = int(mask.sum())
    require(p >= 100, "fewer than 100 surviving features requires terminal stop")
    require(pre["plate_ids"].tolist() == expected["plate_ids"], "lexical eight-plate order")
    for key in ("control_centers", "control_scales"):
        require(pre[key].shape == (8, 5792) and pre[key].dtype.kind == "f", f"{key} shape/type")
        require(np.all(np.isfinite(pre[key][:, mask])), f"retained {key} finiteness")
    require(np.all(pre["control_scales"][:, mask] > 1e-12), "retained control-scale threshold")
    require(pre["control_counts"].shape == (8,) and pre["control_counts"].dtype.kind in "iu",
            "negative-control count shape/type")
    require(np.array_equal(pre["control_counts"], [expected["plates"][plate]["control_rows"]
                                                  for plate in expected["plate_ids"]]), "control counts by plate")
    require(np.array_equal(pre["orf_genes"], expected["genes"]), "130 lexical reference ORF targets")
    for key, shape in (("chemical_effects", (260, 2, 2, p)), ("orf_effects", (130, 2, 2, p))):
        require(pre[key].shape == shape and pre[key].dtype.kind == "f", f"{key} shape/type")
        require(np.all(np.isfinite(pre[key])) and np.all(np.abs(pre[key]) <= 10),
                f"{key}: finite normalized clipped aggregates")
    return p


def simple_predictors(relations, targets, folds):
    out = {0: np.ones_like(relations), 1: -np.ones_like(relations)}
    for index in (2, 3, 8, 9):
        out[index] = np.empty_like(relations)
    for fold in np.unique(folds):
        query = np.flatnonzero(folds == fold)
        source = np.flatnonzero(folds != fold)
        source_y = relations[source]
        global_mean = source_y.sum(dtype=np.float64) / source_y.size
        cell_mean = source_y.sum(axis=0, dtype=np.float64) / len(source)
        out[2][query] = global_mean
        out[8][query] = cell_mean
        for i in query:
            source_target = source[targets[source] == targets[i]]
            same = relations[source_target]
            out[3][i] = (same.sum(dtype=np.float64) + 10 * global_mean) / (same.size + 10)
            out[9][i] = (same.sum(axis=0, dtype=np.float64) + 10 * cell_mean) / (len(source_target) + 10)
    return out


def bootstrap(differences, groups):
    names = np.unique(groups)
    group_sums = np.asarray([differences[groups == group].sum(dtype=np.float64) for group in names])
    counts = np.asarray([2 * np.sum(groups == group) for group in names], dtype=np.int64)
    selected = np.random.default_rng(20261032).integers(0, len(names), size=(2000, len(names)))
    gains = group_sums[selected].sum(axis=1, dtype=np.float64) / counts[selected].sum(axis=1, dtype=np.int64)
    return np.quantile(gains, [.025, .975])


def mean_utility(utility):
    return np.asarray([row.sum(dtype=np.float64) / row.size for row in utility])


def select_direct(means):
    rivals = [index for index in range(12) if index != 6]
    return rivals[int(np.argmax(means[rivals]))]


def verify(data_dir):
    expected = metadata()
    run, launcher = read_json(data_dir / "run.json"), read_json(data_dir / "launcher.json")
    decision = read_json(data_dir / "decision.json")
    require(decision.get("status") == "EXPLORATORY_ONLY", "exploratory decision status")
    for key in ("robust_benefit_established", "core_promotion", "Agent"):
        require(decision.get(key) is False, f"unsupported gate: {key}")
    raw_paths = validate_run(run, launcher, expected)
    complete = str(run["status"]).upper() in COMPLETE and not run["failure"]
    if not complete:
        require(bool(run["failure"]) and decision.get("information_gate_pass") is False,
                "failed/incomplete execution must document failure and close information gate")
        require(0 <= run["completed_folds"] <= 5, "failed run fold completion")
        require(read_json(data_dir / "access_receipt.json").get("protected_CGI_access") is False,
                "failure protected CGI access declaration")
        return {"status": "VALID_RECORDED_FAILURE", "verification_pass": True,
                "saved_arithmetic_complete": False, "failure": run["failure"]}
    require(run["completed_folds"] == 5, "complete five-fold matrix")
    require(str(launcher["status"]).upper() in COMPLETE and launcher["exit_code"] == 0,
            "successful bounded launcher")
    validate_access(read_json(data_dir / "access_receipt.json"), expected, raw_paths)
    labels, pre = read_npz(data_dir / "labels.npz"), read_npz(data_dir / "preprocessing.npz")
    require(labels["cells"].tolist() == ["A549", "U2OS"], "frozen cell order")
    for key in ("compounds", "groups", "folds", "targets"):
        require(np.array_equal(labels[key], expected[key]), f"saved identity/fold mismatch: {key}")
    require(labels["folds"].dtype.kind in "iu", "integer fold identities")
    p = validate_preprocessing(pre, expected)
    indices = np.searchsorted(expected["genes"], expected["targets"])
    reconstructed = cosine_grid(pre["chemical_effects"], pre["orf_effects"], indices)
    require(labels["relation_grid"].shape == (260, 2, 2, 2), "full four-pair response grid")
    require(labels["relations"].shape == (260, 2), "unchanged 520 ID/cell queries")
    close(labels["relation_grid"], reconstructed, "reconstructed cosines")
    close(labels["relations"], labels["relation_grid"].mean(axis=(2, 3)), "four-pair mean relations")
    require(np.all(np.abs(labels["relation_grid"]) <= 1 + 1e-12), "cosine bounds")
    relation = np.asarray(labels["relations"], dtype=np.float64)
    saved = read_npz(data_dir / "predictions.npz")
    require(saved["methods"].tolist() == METHODS, "fixed twelve-method panel")
    predictions = saved["predictions"]
    require(predictions.shape == (12, 260, 2) and predictions.dtype == np.float64, "float64 full predictions")
    require(np.all(np.isfinite(predictions)) and np.all(np.abs(predictions) <= 1), "finite clipped predictions")
    for index, result in simple_predictors(relation, expected["targets"], expected["folds"]).items():
        close(predictions[index], result, f"source-only simple predictor: {METHODS[index]}")
    require(np.array_equal(predictions[4:6, :, 0], predictions[4:6, :, 1]), "pooled predictors identical across cells")
    signs = np.sign(predictions)
    utility = signs * relation[None, :, :]
    regret = np.abs(relation)[None, :, :] - utility
    close(saved["utility"], utility, "saved per-query utility")
    close(saved["regret"], regret, "saved per-query regret")
    means = mean_utility(utility)
    best = select_direct(means)
    differences = utility[6] - utility[best]
    gain = float(differences.sum(dtype=np.float64) / differences.size)
    interval = bootstrap(differences, expected["groups"])
    sign_difference = signs[6] - signs[best]
    grid = np.asarray(labels["relation_grid"], dtype=np.float64)
    repeat = grid.mean(axis=3)
    repeat_gains = np.asarray([(sign_difference * repeat[:, :, i]).sum(dtype=np.float64) / 520 for i in range(2)])
    diagonal = (grid[:, :, 0, 0] + grid[:, :, 1, 1]) / 2
    off_diagonal = (grid[:, :, 0, 1] + grid[:, :, 1, 0]) / 2
    pair_gains = [(sign_difference * item).sum(dtype=np.float64) / 520 for item in (diagonal, off_diagonal)]
    summary = read_json(data_dir / "summary.json")
    require(summary["methods"] == METHODS, "summary method order")
    close(summary["mean_utility"], means, "mean utility")
    close(summary["mean_regret"], mean_utility(regret), "mean regret")
    close(summary["mean_mse"], mean_utility((predictions - relation[None, :, :]) ** 2), "mean MSE")
    close(summary["per_cell_utility"], utility.sum(axis=1, dtype=np.float64) / 260, "per-cell utility")
    close(summary["oracle_mean_utility"], np.abs(relation).sum(dtype=np.float64) / 520, "oracle mean utility")
    close(summary["mean_absolute_relation"], np.abs(relation).sum(dtype=np.float64) / 520, "mean absolute relation")
    close(summary["replicate_sign_agreement"],
          np.mean(np.sign(repeat[:, :, 0]) == np.sign(repeat[:, :, 1])), "chemical-repeat sign agreement")
    require(summary["candidate_method"] == METHODS[6], "fixed primary candidate index6")
    require(summary["best_direct_method"] == METHODS[best], "exact float strongest eleven-method comparator")
    close(summary["selected_gain"], gain, "paired selected gain")
    close(summary["paired_identity_interval95"], interval, "fixed integer-index identity bootstrap")
    close(summary["chemical_repeat_gains"], repeat_gains, "same-comparator chemical-repeat sensitivities")
    close(summary["diagonal_offdiagonal_gains"], pair_gains, "same-comparator pair sensitivities")
    for key, value in {"retained_feature_count": p, "compounds": 260, "groups": 255,
                       "target_support_queries": 198, "source_unseen_target_queries": 62}.items():
        require(summary[key] == value, f"summary fixed population: {key}")
    gate = gain > 0 and bool(np.all(repeat_gains > 0)) and bool(interval[0] > 0)
    require(decision.get("information_gate_pass") is gate, "exact exploratory gate conjunction")
    require(not any(key in summary or key in decision for key in ("p_value", "permutation_p")), "unadmitted randomization p-value")
    return {
        "status": "PASS", "verification_pass": True, "saved_arithmetic_complete": True,
        "candidate_method": METHODS[6], "best_direct_method": METHODS[best],
        "mean_utility": dict(zip(METHODS, means.tolist())), "selected_gain": gain,
        "paired_identity_interval95": interval.tolist(), "chemical_repeat_gains": repeat_gains.tolist(),
        "diagonal_offdiagonal_gains": pair_gains, "information_gate_pass": gate,
        "retained_feature_count": p, "raw_profile_files_opened_by_verifier": 0,
        "raw_profile_hash_declarations": raw_paths,
    }


def self_test():
    chemical = np.asarray([[[[1., 0.], [0., 0.]]]])
    orf = np.asarray([[[[1., 0.], [0., 1.]]]])
    close(cosine_grid(chemical, orf, [0]), [[[[1., 0.], [0., 0.]]]], "synthetic zero-norm cosines")
    rows = [{"broad_sample": name} for name in ("a", "b", "c", "d")]
    structures = {name: {"same_name_group": name, "exact_InChIKey_group": name,
                          "connectivity_block_group": name} for name in ("a", "b", "c", "d")}
    structures["b"]["same_name_group"] = "a"
    structures["c"]["connectivity_block_group"] = "b"
    close_groups = reconstruct_groups(rows, structures)
    require(close_groups.tolist() == ["a", "a", "a", "d"], "synthetic transitive grouping")
    relation = np.asarray([[.1, .3], [.2, .4], [-.1, -.3], [-.2, -.4]])
    targets = np.asarray(["x", "y", "x", "z"])
    folds = np.asarray([0, 0, 1, 1])
    simple = simple_predictors(relation, targets, folds)
    close(simple[2][0], [-.25, -.25], "synthetic source global mean")
    close(simple[8][0], [-.15, -.35], "synthetic source cell means")
    close(simple[3][0], [(-.4 - 2.5) / 12] * 2, "synthetic pooled target pseudo-count")
    close(simple[9][0], [(-.1 - 1.5) / 11, (-.3 - 3.5) / 11], "synthetic gene-cell pseudo-count")
    close(simple[3][1], [-.25, -.25], "synthetic absent-target fallback")
    means = np.zeros(12)
    means[[1, 6, 11]] = 1
    require(select_direct(means) == 1, "synthetic exact tie order excludes candidate")
    means[11] = np.nextafter(1., 2.)
    require(select_direct(means) == 11, "synthetic no tolerance in direct winner")
    differences = np.asarray([[.2, -.1], [.3, .1], [-.4, .2], [.1, .2]])
    groups = np.asarray(["a", "a", "b", "c"])
    interval = bootstrap(differences, groups)
    rng = np.random.default_rng(20261032)
    reference = []
    for _ in range(2000):
        selected = rng.integers(0, 3, size=3)
        sums = [differences[:2].sum(dtype=np.float64), differences[2].sum(dtype=np.float64), differences[3].sum(dtype=np.float64)]
        reference.append(sum(sums[i] for i in selected) / sum([4, 2, 2][i] for i in selected))
    close(interval, np.quantile(reference, [.025, .975]), "synthetic unequal-group bootstrap")
    return {"status": "SELF_TEST_PASS", "verification_pass": True,
            "B_numerical_outputs_read": False, "raw_profile_files_opened": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=REPO / "data/processed/functional_anchor_binding_20261030/b")
    parser.add_argument("--report", type=Path, default=Path(__file__).with_name("b_arithmetic_verification.json"))
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            result = self_test()
        elif args.metadata_only:
            expected = metadata()
            result = {"status": "METADATA_ONLY_PASS", "verification_pass": True,
                      "B_numerical_outputs_read": False, "groups": len(np.unique(expected["groups"])),
                      "decoded_rows_expected": sum(item["decoded_rows"] for item in expected["plates"].values())}
        else:
            result = verify(args.data_dir)
    except (ContractError, OSError, KeyError, TypeError, ValueError) as exc:
        result = {"status": "FAIL", "verification_pass": False, "error": str(exc)}
    result["verifier_sha256"] = sha256(__file__)
    result["limitations"] = [
        "Normalized aggregate cosine and saved-prediction audit only; no raw profile access or model refit.",
        "Source loader/code review owns raw hashes, decoding admission, preprocessing and treatment aggregation.",
        "Saved declarations cannot certify nuisance removal, biological replication, causality or practical drug benefit.",
        "Conditional exploratory uncertainty omits refitting, selection and shared control/reference uncertainty.",
        "Author previously audited A; this is a distinct B endpoint, not independent A confirmation.",
    ]
    if not args.self_test and not args.metadata_only:
        result["output_sha256"] = {str(path): sha256(path) for path in sorted(args.data_dir.iterdir())
                                   if path.is_file() and path.suffix in {".json", ".npz"}}
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("verification_pass") else 1


if __name__ == "__main__":
    sys.exit(main())
