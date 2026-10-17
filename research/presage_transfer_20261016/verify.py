"""Authenticate inputs, entity split and actual prediction-based ranking results."""
import json
import numpy as np
import pandas as pd

import evaluate as e


def main():
    e.verify_freeze()
    results = json.loads((e.HERE / "RESULTS.json").read_text())
    for name, expected in results["artifact_sha256"].items():
        path = e.HERE / name if name == "SPLIT.csv" else e.OUT / name
        assert e.digest(path) == expected, name
    split = pd.read_csv(e.HERE / "SPLIT.csv")
    assert split.core.is_unique
    assert split.groupby("connectivity").fold.nunique().max() == 1
    assert split.groupby("family_component").fold.nunique().max() == 1
    scores = pd.read_csv(e.OUT / "per_compound.csv")
    assert list(scores.core) == list(split.core)
    assert len(scores) == results["counts"]["compounds"]
    z = np.load(e.OUT / "predictions.npz")
    np.testing.assert_array_equal(z["cores"], split.core)
    info = pd.read_csv(e.RAW / "primary-screen-replicate-collapsed-treatment-info.csv")
    raw = pd.read_csv(e.RAW / "primary-screen-replicate-collapsed-logfold-change.csv", index_col=0)
    mapping = info.set_index("column_name").broad_id.str[:13]
    line_meta = pd.read_csv(e.RAW / "primary-screen-cell-line-info.csv")
    lines = line_meta.loc[line_meta.depmap_id.notna(), "row_name"].astype(str).to_numpy()
    y = raw.reindex(lines).T.groupby(mapping.reindex(raw.columns).to_numpy()).mean().reindex(z["cores"]).to_numpy(float)
    for arm, value in results["arms"].items():
        assert np.isclose(scores[arm].mean(), value["mean_pearson"], atol=1e-12)
        assert np.isfinite(z[arm]).all()
        r, mse = e.scores(z[arm].astype(float), y)
        np.testing.assert_allclose(r, scores[arm], atol=2e-6)
        assert np.isclose(mse.mean(), value["mean_mse"], atol=2e-6)
        for k, row in value["ranking"].items():
            assert row["slots"] == len(scores) * int(k)
            assert 0 <= row["hits"] <= row["slots"]
            assert e.ranking(z[arm], y, int(k)) == row, (arm, k)
    for arm, contrast in results["contrasts"].items():
        d = scores.pathway.to_numpy() - scores[arm].to_numpy()
        assert np.isclose(d.mean(), contrast["gain"], atol=1e-12)
        np.testing.assert_allclose(e.interval(d, split.family_component.to_numpy()), contrast["ci95"], atol=1e-12)
    null = [results["arms"][f"permuted_{i:02}"]["mean_pearson"] for i in range(20)]
    real = results["arms"]["pathway"]["mean_pearson"]
    p = (1 + sum(v >= real for v in null)) / 21
    assert p == results["correspondence_null"]["p"]
    passed = all(c["gain"] >= .01 and c["ci95"][0] > 0 for c in results["contrasts"].values()) and p <= 1/21
    assert results["verdict"] == ("PASS" if passed else "NO_GO")
    assert results["costs"]["provider_calls"] == results["costs"]["purchased_assays"] == 0
    def hits_per_compound(arm):
        chosen = np.argsort(z[arm], axis=1, kind="stable")[:, :3]
        selected = np.take_along_axis(y, chosen, axis=1)
        return (np.isfinite(selected) & (selected <= -1)).sum(1)
    difference = (hits_per_compound("pathway") - hits_per_compound("ungated_neighbour")) / 3
    e.write(e.HERE / "VERIFICATION.json", {
        "status": "PASS", "prediction_storage": "float32; Pearson and MSE replay tolerance 2e-6; rankings replay exactly",
        "posthoc_top3_pathway_minus_ungated_hit_yield": {
            "difference": float(difference.mean()),
            "ci95_family_cluster": e.interval(difference, split.family_component.to_numpy()),
            "grade": "exposed-data diagnostic, not independent terminal validation"},
        "results_sha256": e.digest(e.HERE / "RESULTS.json")})
    print("PASS: frozen inputs, split, prediction artifacts, compound scores, cluster intervals, costs and P0 verdict")


if __name__ == "__main__":
    main()
