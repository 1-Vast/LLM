"""Nested, low-parameter calibration of authenticated STATE response differences.

No unresolved MAP decoder coordinates are used. Readout targets are the existing
named39geneRNA endpoint; this is exposed development, not STATE transfer proof.
"""
import ast
import hashlib
import importlib.util
import json
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKET = ROOT / "research/astra/boundary_acquisition_20261007/packet2"
OUT = ROOT / "outputs/paper_01286/state_readout_repair"
STRENGTHS = (None, 0., 1., 10., 100., 1000.)
ARMS = ("M0", "M2", "global_gain", "drug_gain", "permuted_gain")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def references(arrays, train, held, permuted=False):
    indices = [i for i in train if i != held]
    if not indices:
        raise ValueError("empty_reference_set")
    obs = arrays["train_B"][indices]
    available = arrays["availability_B"][indices]
    precision = np.where(available, arrays["precision_B"][indices], 0.)
    totals = precision.sum(0)
    if np.any(totals <= 0):
        raise ValueError("candidate_missing_reference_support")
    mean = (np.where(available, obs, 0.) * precision).sum(0) / totals
    suffix = "_permuted" if permuted else ""
    states = arrays["state_B" + suffix][indices]
    support = arrays["state_available_B" + suffix][indices]
    count = support.sum(0)
    if np.any(count <= 0):
        raise ValueError("candidate_missing_STATE_reference_support")
    centre = np.where(support, states, 0.).sum(0) / count
    held_support = arrays["state_available_B" + suffix][held]
    deviation = np.where(held_support, arrays["state_B" + suffix][held] - centre, 0.)
    eligible = arrays["availability_A"][held] & arrays["availability_B"][held] & held_support
    return mean, deviation, arrays["train_B"][held], eligible


def fit(arrays, train, groups, arm, strength):
    # None retains exactly the predetermined0.5 STATE coefficient. Finite lambda
    # shrinks calibrated coefficients toward0.5; bounds prevent extrapolative gain.
    if strength is None:
        return np.full(len(groups), .5)
    permuted = arm == "permuted_gain"
    num = np.zeros(len(groups))
    den = np.zeros(len(groups))
    for cell in train:
        mean, deviation, y, valid = references(arrays, train, cell, permuted)
        num += np.where(valid, deviation * (y - mean), 0.)
        den += np.where(valid, deviation**2, 0.)
    active_groups = np.zeros_like(groups) if arm == "global_gain" else groups
    scale = max(float(den.sum() / (len(train) * len(groups))), 1e-12)
    coefficients = np.full(len(groups), .5)
    for group in np.unique(active_groups):
        ix = active_groups == group
        n, d = num[ix].sum(), den[ix].sum()
        penalty = strength * scale
        gain = (n + penalty * .5) / (d + penalty) if d + penalty > 0 else .5
        coefficients[ix] = np.clip(gain, 0., 1.5)
    return coefficients


def choose(arrays, train, groups, arm):
    if arm in ("M0", "M2"):
        return None, []
    losses = []
    for strength in STRENGTHS:
        errors = []
        for held in train:
            keep = [i for i in train if i != held]
            gains = fit(arrays, keep, groups, arm, strength)
            mean, deviation, y, valid = references(arrays, keep, held, arm == "permuted_gain")
            errors.append(float(np.mean((mean[valid] + gains[valid] * deviation[valid] - y[valid])**2)))
        losses.append({"strength": strength, "mean_cell_mse": float(np.mean(errors))})
    # Tie preference retains the original0.5 coefficient, not a new fitted head.
    best = min(range(len(losses)), key=lambda i: (losses[i]["mean_cell_mse"], i))
    return losses[best]["strength"], losses


def ordering(prediction, observed):
    correct, total = 0, 0
    for i in range(len(prediction)):
        dy = observed[i] - observed[i+1:]
        dp = prediction[i] - prediction[i+1:]
        defined = np.abs(dy) > 1e-12
        correct += int(((dy * dp > 0) & defined).sum())
        total += int(defined.sum())
    return correct / total


def main():
    frozen = json.loads((HERE / "FREEZE.json").read_text())
    for path, expected in frozen["inputs"].items():
        assert sha(ROOT / path) == expected, path
    if (OUT / "RESULTS.json").exists() or (OUT / "PREDICTIONS.npz").exists():
        raise RuntimeError("Refuse to overwrite registered readout experiment")
    started = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)
    with np.load(PACKET / "training_arrays.npz") as value:
        arrays = {k: value[k].copy() for k in value.files}
    manifest = json.loads((PACKET / "PACKET_MANIFEST.json").read_text())
    drugs = [ast.literal_eval(label)[0][0] for label in manifest["labels"]]
    index = {name: i for i, name in enumerate(sorted(set(drugs)))}
    groups = np.array([index[name] for name in drugs])
    diagnostics, choices, forecasts = [], {}, {}
    for fold in range(3):
        held = [i for i in range(45) if i % 3 == fold]
        train = [i for i in range(45) if i not in held]
        for arm in ARMS:
            strength, losses = choose(arrays, train, groups, arm)
            gains = fit(arrays, train, groups, arm, strength)
            for cell in held:
                mean, deviation, y, mask = references(arrays, train, cell, arm == "permuted_gain")
                p = mean if arm == "M0" else mean + gains * deviation
                diagnostics.append({"fold": fold, "cell": cell, "arm": arm,
                    "strength": strength, "mse": float(np.mean((p[mask] - y[mask])**2)),
                    "pair_accuracy": ordering(p[mask], y[mask]), "eligible": int(mask.sum())})
    with np.load(PACKET / "public_prior.npz") as data:
        public = {k: data[k].copy() for k in data.files}
    train = list(range(45))
    for arm in ARMS:
        strength, losses = choose(arrays, train, groups, arm)
        gains = fit(arrays, train, groups, arm, strength)
        choices[arm] = {"strength": strength, "losses": losses, "gains": gains.tolist()}
        for cell in manifest["contexts"]:
            key = cell.replace("-", "_").replace("/", "_")
            mean = public[key + "__M0"]
            state_key = "__M2_permuted" if arm == "permuted_gain" else "__M2"
            deviation = 2 * (public[key + state_key] - mean)
            forecasts[key + "__" + arm] = mean.copy() if arm == "M0" else mean + gains * deviation
    np.savez_compressed(OUT / "PREDICTIONS.npz", **forecasts)
    (OUT / "MODEL_CHOICES.json").write_text(json.dumps(choices, indent=2), encoding="utf-8")
    # Outcomes become available to evaluation only after all forecasts are saved.
    with np.load(PACKET / "evaluator_private.npz") as data:
        evaluator = {k: data[k].copy() for k in data.files}
    import sys
    sys.path.insert(0, str(HERE.parent / "boundary_acquisition_20261007"))
    spec = importlib.util.spec_from_file_location("frozen_map_pilot", HERE.parent / "map_knowledge_pilot_20261008/run.py")
    pilot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pilot)
    kg_replay = pilot.kg_replay
    results = []
    for key, prediction in forecasts.items():
        context, arm = key.split("__")
        y = evaluator[context + "__B"]
        selected = np.lexsort((np.arange(146), -prediction))[:5].tolist()
        base = np.lexsort((np.arange(146), -public[context + "__M2"]))[:5].tolist()
        kg = kg_replay(prediction, public["cov"], public["obsvar"], public["offset"],
                       evaluator[context + "__A"], y)
        results.append({"context": context, "arm": arm,
            "mse": float(np.mean((prediction - y)**2)), "pair_accuracy": ordering(prediction, y),
            "initial_selected": selected, "initial_B": float(y[selected].sum()),
            "swapped_in": sorted(set(selected) - set(base)), "swapped_out": sorted(set(base) - set(selected)),
            "replacement_B": float(y[selected].sum() - y[base].sum()), "kg": kg})
    summary = {arm: {"target_mse": float(np.mean([r["mse"] for r in results if r["arm"] == arm])),
        "reference_outer_mse": float(np.mean([r["mse"] for r in diagnostics if r["arm"] == arm])),
        "target_pair_accuracy": float(np.mean([r["pair_accuracy"] for r in results if r["arm"] == arm])),
        "initial_B": float(np.mean([r["initial_B"] for r in results if r["arm"] == arm])),
        "terminal_KG_B": float(np.mean([r["kg"]["terminal_B"] for r in results if r["arm"] == arm])),
        "cost": sum(r["kg"]["cost"] for r in results if r["arm"] == arm)} for arm in ARMS}
    for name, value in (("RESULTS.json", results), ("DIAGNOSTICS.json", diagnostics),
                         ("SUMMARY.json", {"arms": summary, "seconds": time.perf_counter() - started,
                            "scope": "Named39geneRNA readout calibration; cached STATE-ST, not MAP or SE native prediction; exposed targets and in-pretraining reference contexts"})):
        (OUT / name).write_text(json.dumps(value, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
