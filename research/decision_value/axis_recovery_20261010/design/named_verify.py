"""Reconstruct the new named-X channel independently from retained source bytes."""
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np

from research.decision_value.observation_reliability.axis_verify import SavedFile, slice_array


HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[2]
OLD = STUDY.parent / "observation_reliability"
CHANNEL = STUDY / "named_channel"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def singleton_indices(source_names, requested):
    if len(requested) != len(set(requested)):
        raise ValueError("duplicate_requested_symbols")
    lookup = {}
    for index, name in enumerate(source_names):
        lookup.setdefault(name, []).append(index)
    if any(len(lookup.get(name, [])) != 1 for name in requested):
        raise ValueError("missing_or_duplicate_source_symbol")
    return [lookup[name][0] for name in requested]


def check_old_gate(certificates, files, required=39):
    """Prospective counterexample guard: certification belongs to each file."""
    return all(file in certificates and certificates[file].get("file") == file
               and certificates[file].get("passed_coordinates") == required
               and certificates[file].get("heldout_informative") is True
               for file in files)


def calibration_eligible(group, excluded_conditions, excluded_sample_ids):
    """Pooled sample exclusion applies across every cell-line partition."""
    return group["label"] not in excluded_conditions and group["sample"] not in excluded_sample_ids


def verify():
    protocol, frozen, result = [read(CHANNEL / name) for name in ("PROTOCOL.json", "FREEZE.json", "RESULTS.json")]
    for path, expected in frozen["sha256"].items():
        assert digest(ROOT / path) == expected
    assert frozen["already_exposed_vectors"] is True and frozen["before_new_endpoint_estimation"] is True
    old_protocol = read(OLD / "axis/PROTOCOL.json")
    expected_groups = [group for group in old_protocol["selected"] if group["file"] == protocol["source_file"]]
    assert protocol["selected"] == expected_groups
    assert protocol["source_file"] == "c44.h5ad" and protocol["source_revision"] == old_protocol["source_revision"]
    assert protocol["transform"] == "log1p(normalized stored X); not raw UMI or a new normalization step"
    weights = np.asarray(protocol["weights"], dtype=float)
    assert weights.tolist() == [1/39]*39 and len(protocol["symbols"]) == 39
    assert len(result["groups"]) == len(expected_groups) == 28
    receipts = [json.loads(line) for line in (OLD / "axis/NETWORK.jsonl").read_text().splitlines()]
    source_receipts = [entry for entry in receipts if entry["file"] == protocol["source_file"]]
    census = read(OLD / "axis/CENSUSES.json")[protocol["source_file"]]
    for receipt in source_receipts:
        assert receipt["http_status"] == 206
        assert receipt["source_revision"] == protocol["source_revision"]
        assert receipt["public_url"] == (f"https://huggingface.co/datasets/{protocol['source_repo']}"
            f"/resolve/{protocol['source_revision']}/{protocol['source_file']}")
        body = (ROOT / receipt["asset"]).read_bytes()
        assert len(body) == receipt["bytes"] == receipt["end"] - receipt["start"] + 1
        assert hashlib.sha256(body).hexdigest() == receipt["sha256"]
    source = SavedFile(protocol["source_file"], census["file_bytes"], source_receipts)
    vectors, all_rows, ratios = [], [], []
    with h5py.File(source, "r") as h5:
        names = [name.decode() if isinstance(name, bytes) else str(name) for name in h5["var/gene_name"][:]]
        indices = singleton_indices(names, protocol["symbols"])
        assert len(names) == 62_710 and indices == result["source_gene_indices"]
        for position, (group, observed) in enumerate(zip(expected_groups, result["groups"])):
            assert group["file"] == protocol["source_file"]
            expected_metadata = {key: group[key] for key in ("file", "cell", "plate", "sample", "rows")}
            assert observed["metadata"] == expected_metadata
            assert observed["group_index"] == position and observed["cells"] == len(group["rows"]) == 8
            matrix = []
            for row in group["rows"]:
                first, last = map(int, slice_array(source, h5["X/indptr"], row, row+2))
                columns = slice_array(source, h5["X/indices"], first, last)
                counts = slice_array(source, h5["X/data"], first, last)
                assert len(columns) == len(counts) == len(np.unique(columns))
                assert np.isfinite(counts).all() and (counts >= 0).all()
                dense = np.zeros(len(names), dtype=np.float64)
                dense[columns] = counts
                matrix.append(np.log1p(dense[indices]))
            x = np.asarray(matrix)
            vectors.append(x); all_rows.extend(group["rows"])
            scalar = x @ weights
            covariance = np.cov(x, rowvar=False, ddof=1)
            full, diagonal = float(weights @ covariance @ weights / 8), float(np.diag(covariance) @ (weights**2) / 8)
            quantities = dict(scalar_mean=float(scalar.mean()), scalar_sample_variance=full*8,
                scalar_sample_mean_variance=full, diagonal_only_scalar_sample_variance=diagonal*8,
                diagonal_only_sample_mean_variance=diagonal, covariance_sample_mean_variance=full-diagonal)
            for name, value in quantities.items():
                np.testing.assert_allclose(observed[name], value, rtol=1e-11, atol=1e-14)
            if diagonal > 0:
                np.testing.assert_allclose(observed["full_to_diagonal_ratio"], full/diagonal)
                ratios.append(full/diagonal)
            else:
                assert observed["full_to_diagonal_ratio"] is None
            resamples = np.random.default_rng(np.random.SeedSequence([protocol["seed"], position])).integers(
                0, 8, size=(protocol["bootstrap_draws"], 8))
            draw_scalar, draw_vectors = scalar[resamples], x[resamples]
            bf = np.var(draw_scalar, axis=1, ddof=1)/8
            bd = np.var(draw_vectors, axis=1, ddof=1) @ (weights**2)/8
            draws = dict(scalar_mean=draw_scalar.mean(1), scalar_sample_mean_variance=bf,
                diagonal_only_sample_mean_variance=bd, covariance_sample_mean_variance=bf-bd)
            valid = bd > 0
            assert observed["ratio_defined_bootstrap_draws"] == int(valid.sum())
            if valid.any():
                draws["full_to_diagonal_ratio"] = bf[valid]/bd[valid]
            else:
                assert observed["bootstrap_percentile_95"]["full_to_diagonal_ratio"] is None
            for name, distribution in draws.items():
                np.testing.assert_allclose(observed["bootstrap_percentile_95"][name], np.quantile(distribution,[.025,.975]),
                    rtol=1e-11, atol=1e-14)
    data = np.concatenate(vectors)
    assert len(set(all_rows)) == len(all_rows) == result["cells"] == 224
    saved = np.load(CHANNEL / "VECTORS.npz", allow_pickle=False)
    assert set(saved.files) == {"rows","expression","symbols"}
    np.testing.assert_array_equal(saved["rows"], all_rows)
    np.testing.assert_array_equal(saved["symbols"], protocol["symbols"])
    np.testing.assert_array_equal(saved["expression"], data)
    np.testing.assert_allclose(result["descriptive_summary"]["full_to_diagonal_ratio_min_median_max"], np.quantile(ratios,[0,.5,1]))
    assert result["descriptive_summary"]["nonzero_cells_by_named_gene"] == (data > 0).sum(0).tolist()
    assert result["pooled_sample_ids"] == len({group["sample"] for group in expected_groups}) == 28
    assert result["new_network_calls"] == 0 and result["decision_gain"] is None
    assert result["old_HVG_axis_authenticated"] is False and result["old250_noise_study_released"] is False
    assert result["descriptive_summary"]["independent_culture_count"] is None
    verdict = dict(status="PASS_INDEPENDENT_NAMED_X_RECONSTRUCTION", rows=224, groups=28, cells_per_group=8,
        raw_named_source_genes=len(names), endpoint_genes=39, zero_observed_genes=[symbol for symbol, count in
            zip(protocol["symbols"], (data>0).sum(0)) if count == 0], source_revision=protocol["source_revision"],
        full_diagonal_ratio_min_median_max=np.quantile(ratios,[0,.5,1]).tolist(), new_network_calls=0,
        producer_imported=False, noise_estimator_imported=False, old_HVG_gate_released=False,
        verifier_sha256=digest(Path(__file__)), results_sha256=digest(CHANNEL/"RESULTS.json"),
        vectors_sha256=digest(CHANNEL/"VECTORS.npz"),
        boundary="Previously exposed named-source control sampling diagnostic, no hidden-axis identity or biological decision gain.")
    destination = HERE / "NAMED_VERIFIED.json"
    with destination.open("x",encoding="utf-8") as stream:
        json.dump(verdict,stream,indent=2); stream.write("\n")
    print(json.dumps(verdict))
    return verdict


if __name__ == "__main__":
    verify()
