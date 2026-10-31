"""Frozen development-only chemical-to-sensitizer call diagnostic."""
import os
for option in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ[option] = "4"

import hashlib
import json
from pathlib import Path
import time
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[3]
OUT = PROJECT / "data/processed/conditional_interventions_20261030/cgi/stage1"
METHODS = ["frequency", "nearest5", "ridge1", "ridge10", "ridge100"]
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, obj):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def checkpoint(indices, scores, null_indices, null_scores, mappings):
    temporary = OUT / "ranks.partial.tmp.npz"
    np.savez_compressed(temporary, methods=np.array(METHODS), aligned_indices=indices,
        aligned_scores=scores,
        null_indices=np.array(null_indices) if null_indices else np.empty((0, *indices.shape), dtype=np.int32),
        null_scores=np.array(null_scores) if null_scores else np.empty((0, *scores.shape)),
        null_assignments=mappings)
    temporary.replace(OUT / "ranks.partial.npz")


def extract_labels(rows, universe, source):
    """Only selected development rows reach gene linkage/score conversion."""
    genes = np.array(sorted(universe.loc[universe.included.eq("True"), "canonical_gene"]))
    keep = universe[universe.included.eq("True")]
    old_to_current = dict(zip(keep["HGNC(2020)_Gene_Symbol"], keep.canonical_gene))
    assert len(old_to_current) == len(genes)
    screen_to_row = {screen: i for i, screen in enumerate(rows.screen)}
    gene_to_col = {gene: i for i, gene in enumerate(genes)}
    calls = np.zeros((len(rows), len(genes)), dtype=bool)
    selected_calls = []
    development_rows = 0
    excluded_identity_rows = 0
    numeric_values_decoded = 0
    status = "failed"
    try:
        with ZipFile(source) as archive:
            shared = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            strings = ["".join(si.itertext()) for si in shared.findall(NS + "si")]

            def value(cell):
                if cell is None:
                    return ""
                v = cell.find(NS + "v")
                if cell.get("t") == "s":
                    return strings[int(v.text)]
                if cell.get("t") == "inlineStr":
                    return "".join(cell.find(NS + "is").itertext())
                return "" if v is None else v.text

            with archive.open("xl/worksheets/sheet6.xml") as handle:
                for _, row in ET.iterparse(handle, events=("end",)):
                    if row.tag != NS + "row":
                        continue
                    cells = row.findall(NS + "c")
                    screen_cell = next((c for c in cells if c.get("r", "").rstrip("0123456789") == "A"), None)
                    screen = value(screen_cell)
                    # Container XML characters exist, but no nonselected gene pairing
                    # or score/FDR conversion is performed across this boundary.
                    if screen not in screen_to_row:
                        row.clear()
                        continue
                    development_rows += 1
                    by_col = {c.get("r").rstrip("0123456789"): c for c in cells}
                    old_gene = value(by_col.get("C"))
                    if old_gene not in old_to_current:
                        excluded_identity_rows += 1
                        row.clear()
                        continue
                    score = float(value(by_col.get("D")))
                    numeric_values_decoded += 1
                    fdr = float(value(by_col.get("F")))
                    numeric_values_decoded += 1
                    if not np.isfinite(score) or not np.isfinite(fdr):
                        raise ValueError("nonfinite authorized development call")
                    if score < 0 and fdr < .05:
                        gene = old_to_current[old_gene]
                        calls[screen_to_row[screen], gene_to_col[gene]] = True
                        selected_calls.append({"compound": rows.iloc[screen_to_row[screen]].compound,
                                               "screen": screen, "gene": gene,
                                               "score": score, "fdr": fdr})
                    row.clear()
        status = "complete"
    finally:
        pd.DataFrame(selected_calls, columns=["compound", "screen", "gene", "score", "fdr"]).to_csv(
            OUT / "authorized_calls.csv", index=False, lineterminator="\n")
        write_json(OUT / "call_access_receipt.json", {
            "status": status, "numeric_values_decoded": numeric_values_decoded,
            "partial_exposure_unknown": False,
            "source_sha256": sha(source), "selected_development_compounds": len(rows),
            "selected_representative_screens": len(screen_to_row),
            "authorized_call_rows_examined": development_rows,
            "authorized_rows_excluded_by_identity": excluded_identity_rows,
            "retained_sensitizer_rows": len(selected_calls),
            "held_out_call_values_decoded_or_used": False,
            "s2_numeric_values_decoded_or_used": False,
            "boundary": "public XML container parsing is not secure blinding; only selected development screen rows reach gene/score/FDR reconstruction"})
    return genes, calls


def assignments(groups, rounds):
    blocks = {g: np.flatnonzero(groups == g) for g in np.unique(groups)}
    strata = {}
    for g, indices in blocks.items():
        strata.setdefault(tuple(rounds[indices]), []).append(g)
    rng = np.random.default_rng(20261030)
    result = []
    for _ in range(49):
        mapping = np.arange(len(groups))
        for key in sorted(strata):
            names = strata[key]
            order = rng.permutation(len(names))
            for target, source in enumerate(order):
                mapping[blocks[names[target]]] = blocks[names[source]]
        result.append(mapping)
    movable = [g for names in strata.values() if len(names) > 1 for g in names]
    return np.array(result), {
        "strata": len(strata), "movable_blocks": len(movable),
        "movable_compounds": sum(len(blocks[g]) for g in movable),
        "fixed_blocks": len(blocks) - len(movable)}


def source_eligible(truth, source):
    count = truth[source].sum(axis=0)
    return np.flatnonzero((count > 0) & (count <= .1 * len(source)))


def prediction_weights(x, compounds, folds):
    result = {}
    for fold in sorted(set(folds)):
        train = np.flatnonzero(folds != fold)
        query = np.flatnonzero(folds == fold)
        a, b = x[train], x[query]
        overlap = b @ a.T
        union = b.sum(axis=1)[:, None] + a.sum(axis=1)[None, :] - overlap
        similarity = np.divide(overlap, union, out=np.zeros_like(overlap), where=union > 0)
        order = np.argsort(-similarity, axis=1, kind="stable")[:, :min(5, len(train))]
        nearest = np.zeros((len(query), len(train)))
        np.put_along_axis(nearest, order, 1 / order.shape[1], axis=1)
        weights = [np.full_like(nearest, 1 / len(train)), nearest]
        mean, sd = a.mean(axis=0), a.std(axis=0)
        sd[sd == 0] = 1
        for alpha in [1, 10, 100]:
            model = Ridge(alpha=alpha, fit_intercept=True, solver="cholesky")
            model.fit((a - mean) / sd, np.eye(len(train)))
            weight = model.predict((b - mean) / sd)
            assert np.allclose(weight.sum(axis=1), 1, atol=1e-8)
            weights.append(weight)
        result[int(fold)] = (train, query, weights)
    return result


def evaluate(truth, folds, weights):
    top = np.full((5, len(truth), 20), -1, dtype=np.int32)
    scores = np.full(top.shape, np.nan)
    precision = np.full((5, len(truth)), np.nan)
    recall = np.full_like(precision, np.nan)
    oracle = np.full(len(truth), np.nan)
    eligible_counts = {}
    for fold, (train, query, matrices) in weights.items():
        eligible = source_eligible(truth, train)
        if len(eligible) < 20:
            raise RuntimeError(f"INSUFFICIENT_ELIGIBLE_GENES fold={fold} count={len(eligible)}")
        eligible_counts[str(fold)] = len(eligible)
        y = truth[np.ix_(train, eligible)].astype(float)
        denominator = truth[np.ix_(query, eligible)].sum(axis=1)
        oracle[query] = np.minimum(20, denominator) / 20
        for method, matrix in enumerate(matrices):
            predicted = np.clip(matrix @ y, 0, 1)
            if not np.isfinite(predicted).all():
                raise ValueError("nonfinite model output")
            selected = np.argsort(-predicted, axis=1, kind="stable")[:, :20]
            indices = eligible[selected]
            recovered = truth[query[:, None], indices].sum(axis=1)
            top[method, query] = indices
            scores[method, query] = np.take_along_axis(predicted, selected, axis=1)
            precision[method, query] = recovered / 20
            recall[method, query] = np.divide(recovered, denominator,
                out=np.zeros(len(query)), where=denominator > 0)
    assert (top >= 0).all() and np.isfinite(precision).all()
    return top, scores, precision, recall, oracle, eligible_counts


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / "run.json").exists(), "preserve previous run; no automatic replay"
    started, cpu_started = time.perf_counter(), time.process_time()
    receipt = {"status": "running", "threads": 4, "python": os.sys.executable,
               "python_version": os.sys.version,
               "numpy": np.__version__, "sklearn": sklearn.__version__,
               "script_sha256": sha(Path(__file__)),
               "protocol_sha256": sha(ROOT / "stage1_protocol.md"),
               "amendment_sha256": sha(ROOT / "stage1_protocol_v1_1.md"),
               "identity_split_sha256": sha(ROOT / "identity_split.tsv"),
               "gene_universe_sha256": sha(ROOT / "gene_universe.tsv"),
               "feature_sha256": sha(ROOT / "chemical_features.npz"),
               "input_freeze_sha256": sha(ROOT / "input_freeze.json"),
               "completed_nulls": 0, "label_extraction_started": False,
               "settings": {"methods": METHODS, "k": 20, "nearest_k": 5, "ridge_alphas": [1, 10, 100],
                   "standardization_ddof": 0, "rare_max_source_fraction": .1,
                   "rare_min_source_calls": 1, "null_draws": 49, "null_seed": 20261030,
                   "bootstrap_draws": 2000, "bootstrap_seed": 20261031,
                   "wall_seconds_ceiling": 1800}, "failure": None}
    write_json(OUT / "run.json", receipt)
    try:
        frozen = json.loads((ROOT / "input_freeze.json").read_text(encoding="utf-8"))
        for name, expected in frozen["sha256"].items():
            path = Path(name) if Path(name).is_absolute() else ROOT / name
            if sha(path) != expected:
                raise ValueError(f"pre-access input hash mismatch: {name}")
        receipt["input_hash_preflight_passed"] = True
        write_json(OUT / "run.json", receipt)
        split = pd.read_csv(ROOT / "identity_split.tsv", sep="\t", dtype=str)
        rows = split[(split.partition == "development") & (split.representative == "True")].sort_values("compound").reset_index(drop=True)
        assert len(rows) == 231 and rows.compound.is_unique
        universe = pd.read_csv(ROOT / "gene_universe.tsv", sep="\t", dtype=str).fillna("")
        manifest = pd.read_csv(ROOT / "cgi_source/source_file_manifest.tsv", sep="\t", dtype=str)
        original = [Path(p) for p in manifest.path if Path(p).name == "TableS1.xlsx"]
        assert len(original) == 1
        source = original[0]
        receipt["label_source_sha256"] = sha(source)
        receipt["label_extraction_started"] = True
        write_json(OUT / "run.json", receipt)
        genes, calls = extract_labels(rows, universe, source)
        assert len(genes) == 18415
        compounds, folds = rows.compound.to_numpy(), rows.development_fold.to_numpy(int)
        groups, rounds = rows.group_hash.to_numpy(), rows["round"].to_numpy()
        np.savez_compressed(OUT / "labels.npz", compounds=compounds.astype(str), genes=genes.astype(str),
                            calls=calls, folds=folds, groups=groups.astype(str), rounds=rounds.astype(str))
        mappings, mobility = assignments(groups, rounds)
        np.savez_compressed(OUT / "permutation_assignments.npz", null_assignments=mappings)
        for fold in sorted(set(folds)):
            if len(source_eligible(calls, np.flatnonzero(folds != fold))) < 20:
                raise RuntimeError("INSUFFICIENT_ELIGIBLE_GENES before fitting")
        with np.load(ROOT / "chemical_features.npz", allow_pickle=False) as features:
            lookup = {str(c): i for i, c in enumerate(features["compounds"])}
            x = features["fingerprints"][[lookup[c] for c in compounds]].astype(float)
        with threadpool_limits(limits=4):
            weights = prediction_weights(x, compounds, folds)
            aligned = evaluate(calls, folds, weights)
            null_indices, null_scores, null_gains, null_gain_counts, null_means = [], [], [], [], []
            checkpoint(aligned[0], aligned[1], null_indices, null_scores, mappings)
            for i, mapping in enumerate(mappings):
                if time.perf_counter() - started > 1800:
                    raise RuntimeError("thirty-minute deadline exceeded")
                result = evaluate(calls[mapping], folds, weights)
                totals = np.rint(result[2] * 20).astype(np.int64).sum(axis=1)
                means = totals / (20 * len(rows))
                null_indices.append(result[0]); null_scores.append(result[1])
                null_means.append(means.tolist())
                null_count = int(totals[1:].max() - totals[0])
                null_gain_counts.append(null_count)
                null_gains.append(null_count / (20 * len(rows)))
                checkpoint(aligned[0], aligned[1], null_indices, null_scores, mappings)
                receipt["completed_nulls"] = i + 1
                write_json(OUT / "run.json", receipt)
                if (i + 1) % 10 == 0:
                    print("completed_null", i + 1, flush=True)
        indices, scores, precision, recall, oracle, eligible_counts = aligned
        totals = np.rint(precision * 20).astype(np.int64).sum(axis=1)
        means = totals / (20 * len(rows))
        best = int(np.argmax(totals[1:])) + 1
        gain_count = int(totals[best] - totals[0])
        gain = gain_count / (20 * len(rows))
        p_value = (1 + np.count_nonzero(np.array(null_gain_counts) >= gain_count)) / 50
        recovered_counts = np.rint(precision * 20).astype(np.int64)
        differences = recovered_counts[best] - recovered_counts[0]
        ordered_groups = np.unique(groups)
        sums = np.array([differences[groups == g].sum() for g in ordered_groups])
        counts = np.array([np.count_nonzero(groups == g) for g in ordered_groups])
        rng = np.random.default_rng(20261031)
        sampled = rng.integers(0, len(ordered_groups), size=(2000, len(ordered_groups)))
        interval = np.quantile(sums[sampled].sum(axis=1) / (20 * counts[sampled].sum(axis=1)), [.025, .975]).tolist()
        summary = {"scope": "selected development-only native-call recovery; no physical-effect or independent-biology claim",
            "methods": {m: {"p_at_20": float(means[i]), "per_compound_p_at_20": precision[i].tolist(),
                              "recall": float(recall[i].mean()), "per_compound_recall": recall[i].tolist()}
                        for i, m in enumerate(METHODS)},
            "oracle": {"p_at_20": float(oracle.mean()), "per_compound_p_at_20": oracle.tolist()},
            "source_eligible_genes": eligible_counts, "best_method": METHODS[best],
            "null_method_means": null_means, "null_maximum_gains": null_gains,
            "permutation_p": float(p_value), "selected_gain": gain, "permutation_mobility": mobility,
            "distinct_null_mappings": len({mapping.tobytes() for mapping in mappings})}
        decision = {"status": "NO_HELD_OUT_RELEASE", "information_gate_pass": bool(gain > 0 and p_value <= .05),
                    "held_out_release": False, "paired_scaffold_interval95": interval,
                    "conditional_interval_above_zero": bool(interval[0] > 0),
                    "robust_benefit_established": False}
        if time.perf_counter() - started > 1800:
            raise RuntimeError("thirty-minute deadline exceeded before completion")
        (OUT / "ranks.partial.npz").replace(OUT / "ranks.npz")
        write_json(OUT / "summary.json", summary); write_json(OUT / "decision.json", decision)
        receipt.update(status="complete", compounds=len(rows), genes=len(genes), permutations=len(mappings),
                       actual_shapes={"labels": list(calls.shape), "features": list(x.shape), "aligned_indices": list(indices.shape),
                                      "aligned_scores": list(scores.shape),
                                      "null_scores": [len(null_scores), *scores.shape],
                                      "null_indices": [len(null_indices), *indices.shape],
                                      "assignments": list(mappings.shape)},
                       artifact_sha256={p: sha(OUT / p) for p in ["labels.npz", "ranks.npz", "summary.json", "decision.json"]})
        print(json.dumps({"means": dict(zip(METHODS, means.tolist())), "decision": decision,
                          "best": METHODS[best], "permutation_p": p_value}, indent=2), flush=True)
    except Exception as exc:
        receipt.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        write_json(OUT / "decision.json", {"status": "NO_HELD_OUT_RELEASE", "information_gate_pass": False,
                   "held_out_release": False, "robust_benefit_established": False,
                   "failure": receipt["failure"]})
        partial = OUT / "ranks.partial.npz"
        if partial.exists():
            receipt["partial_ranks_sha256"] = sha(partial)
        raise
    finally:
        receipt.update(wall_seconds=time.perf_counter() - started, cpu_seconds=time.process_time() - cpu_started)
        write_json(OUT / "run.json", receipt)


if __name__ == "__main__":
    main()
