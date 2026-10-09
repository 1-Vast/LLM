"""Released drug-encoder comparison with fixed STATE forecasts and equal capacity."""
import json
import sys
import time
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "outputs/paper_01286/released_test"
sys.path.insert(0, str(ROOT / "research/astra/map_knowledge_pilot_20261008"))
import run as pilot

ARMS = {"M2": "knowledge", "missing": "knowledge",
        "structure_release": "structure", "knowledge_release": "knowledge",
        "permuted_release": "permuted"}


def main():
    frozen = json.loads((HERE / "FREEZE.json").read_text())
    for path, expected in frozen["inputs"].items():
        assert pilot.sha(ROOT / path) == expected, path
    if (OUT / "PREDICTIONS.npz").exists():
        raise RuntimeError("Refuse to overwrite published-weight comparison")
    started = time.perf_counter()
    features = dict(np.load(OUT / "FEATURES.npz"))
    arrays = dict(np.load(pilot.PACKET / "training_arrays.npz"))
    manifest = json.loads((pilot.PACKET / "PACKET_MANIFEST.json").read_text())
    mask = features["mask"]
    prior = dict(np.load(pilot.PACKET / "public_prior.npz"))
    diagnostics, choices, predictions = [], {}, {}
    for fold in range(3):
        held = [i for i in range(45) if i % 3 == fold]
        train = [i for i in range(45) if i not in held]
        for arm, key in ARMS.items():
            embedding = features[key]
            method = arm if arm in ("M2", "missing") else "knowledge"
            alpha, _ = pilot.choose(arrays, train, embedding, mask, method)
            for cell in held:
                prediction, y, observed = pilot.predict(arrays, train, cell, embedding, mask, method, alpha)
                diagnostics.append({"fold": fold, "arm": arm, "cell": cell, "alpha": alpha,
                                    **pilot.metrics(prediction, y, observed)})
    x, y, p, _, valid = pilot.fold_data(arrays, list(range(45)), 0)
    for arm, key in ARMS.items():
        embedding = features[key]
        method = arm if arm in ("M2", "missing") else "knowledge"
        alpha, losses = pilot.choose(arrays, list(range(45)), embedding, mask, method)
        choices[arm] = {"alpha": alpha, "inner_losses": losses}
        for cell, file in manifest["contexts"].items():
            name = cell.replace("-", "_").replace("/", "_")
            prediction = prior[name + "__M2"].copy()
            if method != "M2":
                obs = np.load(ROOT / "data/external/tahoe_zeroshot_20261007/observations" / f"{file}.npz")
                basal = np.average(obs["basal_mean"], axis=0, weights=obs["basal_n"])
                design = pilot.feature_rows(np.concatenate([x[:45], prior[name + "__features"][None]]),
                    np.concatenate([arrays["basal"], basal[None]]), embedding, mask, method)
                correction = pilot.ridge_predict(design[:-1], y[:45] - p[:45], valid[:45] & mask,
                                                 design[-1], alpha)
                prediction += np.where(mask, correction, 0)
            predictions[name + "__" + arm] = prediction
    np.savez_compressed(OUT / "PREDICTIONS.npz", **predictions)
    (OUT / "MODEL_CHOICES.json").write_text(json.dumps(choices, indent=2))
    # Open target outcomes only after all forecasts/choices are committed.
    evaluator = dict(np.load(pilot.PACKET / "evaluator_private.npz"))
    results = []
    for key, prediction in predictions.items():
        cell, arm = key.split("__")
        results.append({"context": cell, "arm": arm,
            **pilot.metrics(prediction, evaluator[cell + "__B"], np.ones(len(mask), bool)),
            "kg": pilot.kg_replay(prediction, prior["cov"], prior["obsvar"], prior["offset"],
                                 evaluator[cell + "__A"], evaluator[cell + "__B"])})
    summary = {}
    for arm in ARMS:
        rows = [r for r in results if r["arm"] == arm]
        summary[arm] = {"alpha": choices[arm]["alpha"],
            "mean_mse": float(np.mean([r["mse"] for r in rows])),
            "mean_pair_accuracy": float(np.mean([r["pair_accuracy"] for r in rows])),
            "mean_KG_B": float(np.mean([r["kg"]["terminal_B"] for r in rows])),
            "cost": sum(r["kg"]["cost"] for r in rows)}
    for file, value in (("RESULTS.json", results), ("DIAGNOSTICS.json", diagnostics),
                        ("SUMMARY.json", {"arms": summary, "seconds": time.perf_counter() - started,
                          "scope": "Official released molecular/projector weights; fixed STATE forecasts; exposed evaluation; not full MAP or agent-gain validation"})):
        (OUT / file).write_text(json.dumps(value, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
