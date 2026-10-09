"""Frozen-input, outcome-isolation and arithmetic checks for released transfer."""
import json
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

import compare
from encoder import encode

ROOT, OUT, pilot = compare.ROOT, compare.OUT, compare.pilot


def main():
    checks = []
    freeze = json.loads((compare.HERE / "FREEZE.json").read_text())
    for path, digest in freeze["inputs"].items():
        assert pilot.sha(ROOT / path) == digest, path
    checks.append("All15 frozen sources, protocol, representations and packet inputs unchanged")

    features = dict(np.load(OUT / "FEATURES.npz"))
    identities = json.loads((OUT / "IDENTITIES.json").read_text())
    records = identities["records"]
    assert len(records) == 146 and features["mask"].shape == (146,)
    for key in ("structure", "knowledge", "permuted"):
        assert features[key].shape == (146, 24)
        assert np.isfinite(features[key]).all()
    checks.append("Full146candidate menu and equal24dimrepresentation capacity retained")

    # Permutation preserves every dose of a structure and the entire multiset of
    # structure representations; repeated doses cannot get unrelated identities.
    unique = {}
    for i, record in enumerate(records):
        if record["smiles"] in unique:
            j = unique[record["smiles"]]
            for key in ("molecule256", "knowledge1024", "permuted"):
                np.testing.assert_array_equal(features[key][i], features[key][j])
        else:
            unique[record["smiles"]] = i
    indices = list(unique.values())
    original = sorted(tuple(row) for row in features["knowledge"][indices])
    permuted = sorted(tuple(row) for row in features["permuted"][indices])
    # Matrix multiplication of permuted/repeated rows may change the final
    # floating-point bit while preserving the fixed projected representation.
    np.testing.assert_allclose(original, permuted, atol=1e-12, rtol=1e-12)
    labels = json.loads((pilot.PACKET / "PACKET_MANIFEST.json").read_text())["labels"]
    for label, record in zip(labels, records):
        drug, dose, unit = pilot.ast.literal_eval(label)[0]
        assert (drug, dose, unit) == (record["drug"], record["dose"], record["unit"])
    checks.append("Drug/dose/unit identities preserved; grouped permutation is a genuine bijection")
    try:
        encode(None, ["this is not a SMILES"])
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid structure must be refused before inference")
    checks.append("Invalid structure rejected without methane substitution")

    arrays = dict(np.load(pilot.PACKET / "training_arrays.npz"))
    train = list(range(1, 45))
    embedding, mask = features["knowledge"], features["mask"]
    prediction, _, _ = pilot.predict(arrays, train, 0, embedding, mask, "knowledge", 1000)
    poisoned = {k: v.copy() for k, v in arrays.items()}
    poisoned["train_A"][0] = -1e6
    poisoned["train_B"][0] = 1e6
    changed, _, _ = pilot.predict(poisoned, train, 0, embedding, mask, "knowledge", 1000)
    np.testing.assert_allclose(prediction, changed, atol=1e-13, rtol=1e-11)
    checks.append("Heldreference response poisoning cannot change its nonzero-correction forecast")

    incomplete = mask.copy()
    incomplete[::7] = False
    fallback, _, _ = pilot.predict(arrays, train, 0, embedding, incomplete, "knowledge", 1000)
    baseline, _, _ = pilot.predict(arrays, train, 0, embedding, incomplete, "M2", 0)
    np.testing.assert_array_equal(fallback[~incomplete], baseline[~incomplete])
    disabled, _, _ = pilot.predict(arrays, train, 0, embedding, mask, "knowledge", 0)
    np.testing.assert_array_equal(disabled, baseline)
    checks.append("Missingstructure candidates retain exact STATE fallback; alpha0 disables correction")

    public = dict(np.load(pilot.PACKET / "public_prior.npz"))
    private = dict(np.load(pilot.PACKET / "evaluator_private.npz"))
    predictions = dict(np.load(OUT / "PREDICTIONS.npz"))
    choices = json.loads((OUT / "MODEL_CHOICES.json").read_text())
    results = json.loads((OUT / "RESULTS.json").read_text())
    assert len(results) == len(predictions) == 25
    for row in results:
        cell, arm = row["context"], row["arm"]
        p, y = predictions[cell + "__" + arm], private[cell + "__B"]
        assert choices[arm]["alpha"] == 0
        np.testing.assert_array_equal(p, public[cell + "__M2"])
        selected = sorted(range(146), key=lambda i: (-p[i], i))[:5]
        assert selected == row["selected"]
        correct = [int((y[i] - y[j]) * (p[i] - p[j]) > 0)
                   for i in range(146) for j in range(i + 1, 146) if abs(y[i] - y[j]) > 1e-12]
        assert np.isclose(np.mean((p - y)**2), row["mse"], rtol=1e-12)
        assert np.isclose(np.mean(correct), row["pair_accuracy"], rtol=1e-12)
        assert np.isclose(sum(y[i] for i in selected), row["top5_B"], rtol=1e-12)
        kg = row["kg"]
        assert np.isclose(sum(y[i] for i in kg["selected"]), kg["terminal_B"], rtol=1e-12)
        assert len(set(kg["selected"])) == 5
        purchases = [r["purchased_A"] for r in kg["history"][:-1]]
        assert len(purchases) == len(set(purchases)) == 8
        assert [r["cumulative_cost"] for r in kg["history"]] == list(range(1, 9)) + [13]
        assert kg["history"][-1]["committed_B"] == kg["selected"]
        assert kg["cost"] == 8 + len(kg["selected"]) == 13
    checks.append("All25result rows independently reconstructed: error, ordering, endpoint and purchase charges")

    cell = results[0]["context"]
    p, a, b = public[cell + "__M2"], private[cell + "__A"], private[cell + "__B"]
    args = (p, public["cov"], public["obsvar"], public["offset"])
    original = pilot.kg_replay(*args, a, b)
    poisoned_b = pilot.kg_replay(*args, a, np.arange(146) * 1e6)
    assert original["history"] == poisoned_b["history"]
    assert original["selected"] == poisoned_b["selected"]
    unpurchased = np.ones(146, bool)
    for event in original["history"][:-1]:
        unpurchased[event["purchased_A"]] = False
    altered_a = a.copy()
    altered_a[unpurchased] = 1e6
    assert pilot.kg_replay(*args, altered_a, b) == original
    checks.append("Unpurchased A and all B outcomes cannot alter acquisition or final commitment")

    summary = json.loads((OUT / "SUMMARY.json").read_text())["arms"]
    for arm, declared in summary.items():
        rows = [r for r in results if r["arm"] == arm]
        assert len(rows) == 5 and sum(r["kg"]["cost"] for r in rows) == declared["cost"] == 65
        for metric, field in (("mean_mse", "mse"), ("mean_pair_accuracy", "pair_accuracy")):
            assert np.isclose(np.mean([r[field] for r in rows]), declared[metric], rtol=1e-12)
        assert np.isclose(np.mean([r["kg"]["terminal_B"] for r in rows]), declared["mean_KG_B"], rtol=1e-12)
    assert len(json.loads((OUT / "DIAGNOSTICS.json").read_text())) == 225
    checks.append("All5arm summaries and225 reference diagnostic records accounted for")
    receipt = {"checks": checks, "count": len(checks), "target_results_reconstructed": len(results),
               "verifier_sha256": pilot.sha(Path(__file__)),
               "limits": "Software/isolation/arithmetic checks; not independent biological confirmation"}
    (OUT / "VERIFIED.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
