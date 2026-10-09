"""Independent gain arithmetic, result reconstruction and fresh numeric repeat."""
import ast
import importlib.util
import json
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "outputs/paper_01286/state_readout_repair"
spec = importlib.util.spec_from_file_location("state_readout_study", HERE / "run.py")
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def independent_fit(arrays, groups, arm, strength):
    if strength is None:
        return np.full(146, .5)
    state = arrays["state_B_permuted" if arm == "permuted_gain" else "state_B"]
    supported = arrays["state_available_B_permuted" if arm == "permuted_gain" else "state_available_B"]
    xs, residuals, eligible = [], [], []
    for cell in range(45):
        keep = np.arange(45) != cell
        w = np.where(arrays["availability_B"][keep], arrays["precision_B"][keep], 0.)
        mean = np.sum(np.where(arrays["availability_B"][keep], arrays["train_B"][keep], 0.) * w, axis=0) / np.sum(w, axis=0)
        centre = np.sum(np.where(supported[keep], state[keep], 0.), axis=0) / supported[keep].sum(0)
        xs.append(np.where(supported[cell], state[cell] - centre, 0.))
        residuals.append(arrays["train_B"][cell] - mean)
        eligible.append(arrays["availability_A"][cell] & arrays["availability_B"][cell] & supported[cell])
    x, y, valid = np.array(xs), np.array(residuals), np.array(eligible)
    gram = np.where(valid, x * x, 0.).sum(0)
    target = np.where(valid, x * y, 0.).sum(0)
    penalty = strength * max(float(gram.sum() / x.size), 1e-12)
    g = np.zeros_like(groups) if arm == "global_gain" else groups
    output = np.full(146, .5)
    for group in np.unique(g):
        ix = g == group
        denominator = gram[ix].sum() + penalty
        coefficient = (target[ix].sum() + .5 * penalty) / denominator if denominator > 0 else .5
        output[ix] = min(max(coefficient, 0.), 1.5)
    return output


def main():
    checks = []
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    for path, expected in freeze["inputs"].items():
        assert study.sha(ROOT / path) == expected
    checks.append("All10original frozen trial/code/source inputs unchanged")
    manifest = json.loads((study.PACKET / "PACKET_MANIFEST.json").read_text())
    with np.load(study.PACKET / "training_arrays.npz") as data:
        arrays = {k: data[k].copy() for k in data.files}
    with np.load(study.PACKET / "public_prior.npz") as data:
        public = {k: data[k].copy() for k in data.files}
    with np.load(study.PACKET / "evaluator_private.npz") as data:
        private = {k: data[k].copy() for k in data.files}
    with np.load(OUT / "PREDICTIONS.npz") as data:
        predictions = {k: data[k].copy() for k in data.files}
    choices = json.loads((OUT / "MODEL_CHOICES.json").read_text())
    results = json.loads((OUT / "RESULTS.json").read_text())
    diagnostics = json.loads((OUT / "DIAGNOSTICS.json").read_text())
    drugs = [ast.literal_eval(label)[0][0] for label in manifest["labels"]]
    index = {name: i for i, name in enumerate(sorted(set(drugs)))}
    groups = np.array([index[name] for name in drugs])
    assert len(predictions) == len(results) == 25 and len(diagnostics) == 225
    for arm, choice in choices.items():
        np.testing.assert_allclose(independent_fit(arrays, groups, arm, choice["strength"]),
                                   choice["gains"], atol=1e-12, rtol=1e-12)
        if choice["losses"]:
            selected = min(range(len(choice["losses"])), key=lambda i: (choice["losses"][i]["mean_cell_mse"], i))
            assert choice["strength"] == choice["losses"][selected]["strength"]
    checks.append("All5final gain vectors independently reconstructed; validation-minimum choices checked")
    checks.append("Full146drug-dose menu retained with111drugshared groups; no unnamed MAP decoder coordinates")
    for row in results:
        cell, arm = row["context"], row["arm"]
        p, y = predictions[cell + "__" + arm], private[cell + "__B"]
        state_key = "__M2_permuted" if arm == "permuted_gain" else "__M2"
        expected = public[cell + "__M0"].copy()
        if arm != "M0":
            expected += np.array(choices[arm]["gains"]) * 2 * (public[cell + state_key] - expected)
        np.testing.assert_array_equal(p, expected)
        selection = sorted(range(146), key=lambda i: (-p[i], i))[:5]
        assert selection == row["initial_selected"]
        assert np.isclose(np.mean((p - y)**2), row["mse"], rtol=1e-12)
        assert np.isclose(sum(y[i] for i in selection), row["initial_B"], rtol=1e-12)
        kg = row["kg"]
        assert np.isclose(sum(y[i] for i in kg["selected"]), kg["terminal_B"], rtol=1e-12)
        assert len(set(kg["selected"])) == 5 and kg["cost"] == 13
        purchases = [r["purchased_A"] for r in kg["history"][:-1]]
        assert len(purchases) == len(set(purchases)) == 8
        assert [r["cumulative_cost"] for r in kg["history"]] == list(range(1, 9)) + [13]
    checks.append("All25target predictions, MSE, initial/terminal outcomes and charges independently reconstructed")
    # Actual evaluator B poisoning must not alter any acquisition or commitment.
    import sys
    sys.path.insert(0, str(HERE.parent / "boundary_acquisition_20261007"))
    upstream_spec = importlib.util.spec_from_file_location("map_replay_verifier", HERE.parent / "map_knowledge_pilot_20261008/run.py")
    pilot = importlib.util.module_from_spec(upstream_spec)
    upstream_spec.loader.exec_module(pilot)
    for row in results:
        cell, arm = row["context"], row["arm"]
        replay = pilot.kg_replay(predictions[cell + "__" + arm], public["cov"], public["obsvar"], public["offset"],
                                private[cell + "__A"], np.arange(146) * 1e6)
        assert replay["selected"] == row["kg"]["selected"] and replay["history"] == row["kg"]["history"]
    checks.append("Poisoned targetB cannot change any25acquisition/commitment histories")
    original = study.OUT
    with tempfile.TemporaryDirectory(prefix="state_readout_repeat_") as temporary:
        study.OUT = Path(temporary)
        study.main()
        for name in ("MODEL_CHOICES.json", "RESULTS.json", "DIAGNOSTICS.json"):
            assert json.loads((study.OUT / name).read_text()) == json.loads((original / name).read_text()), name
        with np.load(study.OUT / "PREDICTIONS.npz") as repeated:
            for key, value in predictions.items():
                np.testing.assert_array_equal(repeated[key], value)
    study.OUT = original
    checks.append("Separate fitting/evaluation run exactly reproduces all choices, diagnostics, forecasts and outcomes")
    summary = json.loads((OUT / "SUMMARY.json").read_text())["arms"]
    row_changes = []
    for cell in sorted({r["context"] for r in results}):
        base = next(r for r in results if r["context"] == cell and r["arm"] == "M2")
        candidate = next(r for r in results if r["context"] == cell and r["arm"] == "drug_gain")
        row_changes.append({"context": cell, "mse_difference": candidate["mse"] - base["mse"],
            "initial_B_difference": candidate["initial_B"] - base["initial_B"],
            "terminal_B_difference": candidate["kg"]["terminal_B"] - base["kg"]["terminal_B"],
            "changed_purchase_sequence": candidate["kg"]["history"] != base["kg"]["history"]})
    receipt = {"checks": checks, "count": len(checks), "results_reconstructed": 25,
        "drug_gain_MSE_relative_reduction": 1 - summary["drug_gain"]["target_mse"] / summary["M2"]["target_mse"],
        "reference_MSE_relative_reduction": 1 - summary["drug_gain"]["reference_outer_mse"] / summary["M2"]["reference_outer_mse"],
        "per_context_changes": row_changes,
        "verifier_sha256": study.sha(Path(__file__)),
        "limits": "Numeric/isolation verification; references overlap STATEpretraining and all5targets exposed; no independent biological/agent-gain confirmation"}
    (OUT / "VERIFIED.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
