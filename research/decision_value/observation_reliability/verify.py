"""Independently recompute the control-cell audit from saved source arrays."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(output):
    frozen = read(HERE / "FREEZE.json")
    for path, expected in frozen["inputs"].items():
        assert digest(ROOT / path) == expected, path
    run = read(output / "RUN_RECEIPT.json")
    assert run["freeze_sha256"] == digest(HERE / "FREEZE.json")
    for path, expected in run["outputs"].items():
        assert digest(output / path) == expected, path
    plan, endpoint, protocol = [read(HERE / name) for name in ("CONTROL_PLAN.json", "ENDPOINT.json", "PROTOCOL.json")]
    result, receipts = read(output / "RESULTS.json"), read(output / "DOWNLOADS.json")
    source = np.load(output / "CONTROLS.npz", allow_pickle=False)
    weights = np.asarray(endpoint["weights"], dtype=float)
    coordinates = endpoint["coordinates"]
    assert len(coordinates) == len(set(coordinates)) == len(weights) == 39
    assert weights.tolist() == [1 / 39] * 39
    assert result["P2_release"] is False and result["decision_gain"] is None
    assert result["treated_RNA_bytes"] == 0 and result["independent_culture_count"] is None
    assert len(result["groups"]) == len(plan["selected"])
    assert set(source.files) == {f"group_{index}" for index in range(len(plan["selected"]))}
    matrices, cells = {}, 0
    for index, (group, observed) in enumerate(zip(plan["selected"], result["groups"])):
        values = source[f"group_{index}"]
        assert values.shape == (group["selected_cells"], 2000)
        assert np.isfinite(values).all()
        assert observed["cells"] == len(group["rows"]) == len(values)
        assert observed["metadata"]["rows"] == group["rows"]
        for key in ("file", "cell_name", "plate", "sample", "selected_cells"):
            assert observed["metadata"][key] == group[key]
        cells += len(values)
        for row, vector in zip(group["rows"], values):
            assert (group["file"], row) not in matrices
            matrices[(group["file"], row)] = vector
        x = values[:, coordinates].astype(float)
        scalar = x @ weights
        covariance = np.cov(x, rowvar=False, ddof=1)
        full = float(weights @ covariance @ weights / len(x))
        diagonal = float(np.diag(covariance) @ (weights ** 2) / len(x))
        expected = dict(scalar_mean=float(scalar.mean()),
            scalar_sample_variance=full * len(x), scalar_sample_mean_variance=full,
            diagonal_only_scalar_sample_variance=diagonal * len(x),
            diagonal_only_sample_mean_variance=diagonal,
            covariance_sample_mean_variance=full - diagonal,
            legacy_mean_2000gene_control_mean_variance=float(np.var(values, axis=0, ddof=1).mean() / len(x)))
        for name, value in expected.items():
            np.testing.assert_allclose(observed[name], value, rtol=1e-10, atol=1e-14)
        if diagonal > 0:
            np.testing.assert_allclose(observed["full_to_diagonal_ratio"], full / diagonal)
        else:
            assert observed["full_to_diagonal_ratio"] is None
        indices = np.random.default_rng(np.random.SeedSequence([protocol["seed"], index])).integers(
            0, len(x), size=(protocol["bootstrap_draws"], len(x)))
        bx = x[indices]
        bs = scalar[indices]
        bf = np.var(bs, axis=1, ddof=1) / len(x)
        bd = np.var(bx, axis=1, ddof=1) @ (weights ** 2) / len(x)
        distributions = dict(scalar_mean=bs.mean(axis=1), scalar_sample_mean_variance=bf,
            diagonal_only_sample_mean_variance=bd, covariance_sample_mean_variance=bf - bd)
        if (bd > 0).any():
            distributions["full_to_diagonal_ratio"] = bf[bd > 0] / bd[bd > 0]
        else:
            assert observed["bootstrap_percentile_95"]["full_to_diagonal_ratio"] is None
        for name, distribution in distributions.items():
            np.testing.assert_allclose(observed["bootstrap_percentile_95"][name],
                np.quantile(distribution, [.025, .975]), rtol=1e-10, atol=1e-14)
        assert observed["ratio_defined_bootstrap_draws"] == int((bd > 0).sum())
    released = set()
    for receipt in receipts:
        file_groups = [group for group in plan["selected"] if group["file"] == receipt["file"]]
        registered = {row: span for group in file_groups for row, span in zip(group["rows"], group["exact_x_hvg_ranges"])}
        assert receipt["rows"] == list(range(receipt["rows"][0], receipt["rows"][-1] + 1))
        assert receipt["byte_start"] == registered[receipt["rows"][0]]["start"]
        assert receipt["byte_end"] == registered[receipt["rows"][-1]]["end"]
        assert receipt["public_url"] == plan["source_url_template"].format(file=receipt["file"])
        assert receipt["content_range"].startswith(f"bytes {receipt['byte_start']}-{receipt['byte_end']}/")
        payload = b"".join(matrices[(receipt["file"], row)].astype("<f4").tobytes() for row in receipt["rows"])
        assert receipt["http_status"] == 206
        assert len(payload) == receipt["bytes"] == receipt["byte_end"] - receipt["byte_start"] + 1
        assert hashlib.sha256(payload).hexdigest() == receipt["sha256"]
        for row in receipt["rows"]:
            key = receipt["file"], row
            assert key not in released
            released.add(key)
    assert released == set(matrices) and cells == 250
    assert sum(item["bytes"] for item in receipts) == result["control_RNA_bytes"] == 2_000_000
    summary = dict(status="PASS_INDEPENDENT_CONTROL_AUDIT", groups=len(plan["selected"]), cells=cells,
        actual_group_sizes=[group["selected_cells"] for group in plan["selected"]],
        checks=["Frozen source/code/axis and saved output hashes", "Declared control rows only, unique range charges",
            "Independent w-transpose covariance w and diagonal covariance algebra using actual n_g",
            "Independent complete-cell vector bootstrap intervals", "Exact received expression payload reconstruction",
            "No treated/B expression, biological variance fraction, checkpoint-axis or P2 claim"],
        scope="Within-control conditional sampling arithmetic, not independent biological confirmation.")
    (output / "VERIFIED.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "outputs/decision_value/observation_reliability")
    print(json.dumps(verify(parser.parse_args().out)))
