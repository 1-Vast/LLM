"""Frozen full-menu MAP representation covariance replacement experiment."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

import numpy as np
from scipy.stats import t
from threadpoolctl import threadpool_limits

from kernel import ARMS, blend, boundary_schedule, candidate_kernels, conditional_mean, covariances

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PACKET = ROOT/"research/astra/boundary_acquisition_20261007/packet2"
RELEASE = ROOT/"outputs/paper_01286/released_test"
AUDIT = ROOT/"outputs/knowledge_layer_validation_20261009/AUDIT.json"
OUT = ROOT/"outputs/map_module_replacement_20261009/response"
ETAS = (0., .25, .5, 1.)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


readout = load("replacement_readout", ROOT/"research/astra/state_readout_repair_20261009/run.py")
posterior = load("replacement_posterior", ROOT/"research/astra/state_feedback_repair_20261009/posterior.py")


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write("\n")


def offset(arrays, train):
    valid = (arrays["availability_A"] & arrays["availability_B"])[train]
    return np.nanmean(np.where(valid, arrays["train_A"][train]-arrays["train_B"][train], np.nan), axis=0)


def prior(arrays, train, held):
    mean, deviation, _, _ = readout.references(arrays, train, held)
    return mean+.5*deviation


def fitted(arrays, train, kernels):
    cells = [cell for cell in train if (arrays["availability_A"][cell] & arrays["availability_B"][cell]).all()]
    if len(cells) < 2:
        raise ValueError("two_complete_crossfit_contexts_required")
    error_B, error_A = [], []
    for cell in cells:
        keep = [i for i in train if i != cell]
        prediction = prior(arrays, keep, cell)
        error_B.append(arrays["train_B"][cell]-prediction)
        error_A.append(arrays["train_A"][cell]-prediction-offset(arrays, keep))
    matrices, rho = covariances(np.array(error_B), np.array(error_A), kernels)
    return matrices, offset(arrays, train), dict(train=list(train), residual_cells=cells,
                                                mean_contexts=len(train), covariance_contexts=len(cells), rho=rho)


def choose(arrays, train, kernels):
    losses = {arm: {eta: [] for eta in ETAS} for arm in ARMS}
    folds = []
    for fold in range(3):
        keep = [i for i in train if i % 3 != fold]
        held = [i for i in train if i % 3 == fold and (arrays["availability_A"][i] & arrays["availability_B"][i]).all()]
        matrices, current_offset, detail = fitted(arrays, keep, kernels)
        folds.append(dict(fold=fold, held=held, **detail))
        for arm in ARMS:
            for eta in ETAS:
                covariance = blend(matrices["empirical"], matrices[arm], eta)
                for cell in held:
                    prediction = prior(arrays, keep, cell)
                    schedule = boundary_schedule(prediction)
                    updated = conditional_mean(prediction, current_offset, covariance, schedule, arrays["train_A"][cell, schedule])
                    losses[arm][eta].append(float(np.mean((updated-arrays["train_B"][cell])**2)))
    choices = {}
    for arm in ARMS:
        scores = {eta: float(np.mean(values)) for eta, values in losses[arm].items()}
        best = min(ETAS, key=lambda eta: (scores[eta], eta))
        choices[arm] = dict(eta=best, inner_posterior_mse=scores)
    return choices, folds


def build(arrays, public, manifest, kernels):
    models, predictions, choices = {}, {}, {}
    complete = (arrays["availability_A"] & arrays["availability_B"]).all(1)
    scopes = [(f"ref{cell}", [i for i in range(45) if i != cell], cell)
              for cell in range(45) if complete[cell]]+[("targets", list(range(45)), None)]
    for scope, train, held in scopes:
        chosen, inner = choose(arrays, train, kernels)
        matrices, current_offset, detail = fitted(arrays, train, kernels)
        models[scope+"__offset"] = current_offset
        models[scope+"__empirical"] = matrices["empirical"]
        for arm in ARMS:
            models[scope+"__"+arm] = blend(matrices["empirical"], matrices[arm], chosen[arm]["eta"])
        choices[scope] = dict(arms=chosen, inner_folds=inner, **detail)
        if held is not None:
            predictions[scope] = prior(arrays, train, held)
        else:
            for context in manifest["contexts"]:
                token = context.replace("-", "_").replace("/", "_")
                predictions[token] = public[token+"__M2"]
        print(f"Fitted {scope}: {len(train)} mean contexts / {len(detail['residual_cells'])} covariance contexts", flush=True)
    return models, predictions, choices


def evaluate(arrays, private, manifest, models, predictions):
    results = []
    for context, prediction in predictions.items():
        reference = context.startswith("ref")
        scope = context if reference else "targets"
        if reference:
            cell = int(context[3:]); yA, yB = arrays["train_A"][cell], arrays["train_B"][cell]
        else:
            yA, yB = private[context+"__A"], private[context+"__B"]
        initial = posterior.top5(prediction)
        schedule = boundary_schedule(prediction)
        configurations = [("no_screen", "empirical", None)]
        configurations += [("shared", arm, schedule) for arm in ("empirical", *ARMS)]
        configurations += [("adaptiveKG", arm, None) for arm in ("empirical", *ARMS)]
        for policy, arm, fixed in configurations:
            if policy == "no_screen":
                result = dict(selected=initial, purchased_A=[], cost=5, posterior_mean_B=prediction.copy(),
                              history=[dict(committed_B=initial, cost_after_five_B=5)])
            else:
                result = posterior.replay(prediction, models[scope+"__offset"], models[scope+"__"+arm],
                                          lambda i: float(yA[i]), schedule=fixed)
                result.pop("posterior_cov_B")
            selected = result["selected"]
            final_mean = np.asarray(result["posterior_mean_B"])
            result["posterior_mean_B"] = final_mean.tolist()
            results.append(dict(context=context, scope="reference" if reference else "exposed_targets",
                policy=policy, arm=arm, initial_selected=initial, terminal_B=float(yB[selected].sum()),
                initial_B=float(yB[initial].sum()), delta_vs_no_screen=float(yB[selected].sum()-yB[initial].sum()),
                posterior_mse=float(np.mean((final_mean-yB)**2)),
                swapped_in=sorted(set(selected)-set(initial)), swapped_out=sorted(set(initial)-set(selected)), **result))
        print(f"Evaluated {context}: common boundary information plus registered adaptive secondary", flush=True)
    return results


def comparison(new, base):
    delta = np.array(new)-np.array(base)
    radius = float(t.ppf(.975, len(delta)-1)*delta.std(ddof=1)/np.sqrt(len(delta)))
    average = float(delta.mean()); denominator = float(np.mean(base))
    return dict(delta_B=average, relative_delta=average/denominator if denominator > 0 else None,
                paired_context_95CI=[average-radius, average+radius],
                improved_contexts=int((delta > 1e-12).sum()), harmed_contexts=int((delta < -1e-12).sum()))


def summarize(results):
    arms, comparisons = {}, {}
    for scope in ("reference", "exposed_targets"):
        rows = [row for row in results if row["scope"] == scope]
        arms[scope] = {}
        for policy, arm in sorted({(row["policy"], row["arm"]) for row in rows}):
            group = [row for row in rows if (row["policy"], row["arm"]) == (policy, arm)]
            arms[scope][policy+"__"+arm] = dict(contexts=len(group), mean_B=float(np.mean([r["terminal_B"] for r in group])),
                posterior_mse=float(np.mean([r["posterior_mse"] for r in group])),
                delta_vs_no_screen=float(np.mean([r["delta_vs_no_screen"] for r in group])),
                harm_vs_no_screen=sum(r["delta_vs_no_screen"] < -1e-12 for r in group), total_cost=sum(r["cost"] for r in group))
        knowledge = {r["context"]: r for r in rows if r["policy"] == "shared" and r["arm"] == "knowledge"}
        comparisons[scope] = {}
        for control in ("empirical", "molecule", "Morgan", "permutedknowledge"):
            base = [r for r in rows if r["policy"] == "shared" and r["arm"] == control]
            comparisons[scope][control] = comparison([knowledge[r["context"]]["terminal_B"] for r in base], [r["terminal_B"] for r in base])
    primary = comparisons["reference"]
    gate = all(primary[arm]["relative_delta"] is not None and primary[arm]["relative_delta"] > .02
               and primary[arm]["paired_context_95CI"][0] > 0 for arm in ("empirical", "molecule", "Morgan"))
    return dict(arms=arms, paired_shared_comparisons=comparisons, registered_development_gate=gate,
                claim_boundary="Cached signed39geneRNA module replacement, development only. Nominal context t intervals; overlapping training/pretraining and exposed targets preclude independent certification. No module promotion, functional or calibrated-risk claim.")


def main():
    freeze = json.loads((HERE/"FREEZE.json").read_text())
    for name, expected in freeze["inputs"].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != expected:
            raise ValueError("freeze_mismatch:"+name)
    if OUT.exists():
        raise RuntimeError("Refuse to overwrite registered replacement trial")
    OUT.mkdir(parents=True)
    started = time.perf_counter()
    arrays = dict(np.load(PACKET/"training_arrays.npz")); public = dict(np.load(PACKET/"public_prior.npz"))
    manifest = json.loads((PACKET/"PACKET_MANIFEST.json").read_text())
    records = json.loads(AUDIT.read_text())["records"]
    identities = json.loads((RELEASE/"IDENTITIES.json").read_text())["records"]
    if [(r["cid"], r["smiles"]) for r in records] != [(r["cid"], r["smiles"]) for r in identities]:
        raise ValueError("authenticated_cache_identity_mismatch")
    kernels, kernel_metadata = candidate_kernels(records, dict(np.load(RELEASE/"FEATURES.npz")))
    models, predictions, choices = build(arrays, public, manifest, kernels)
    np.savez_compressed(OUT/"MODELS.npz", **models); np.savez_compressed(OUT/"PREDICTIONS.npz", **predictions)
    write(OUT/"MODEL_CHOICES.json", choices); write(OUT/"KERNEL_METADATA.json", kernel_metadata)
    private = dict(np.load(PACKET/"evaluator_private.npz"))  # All fits/forecasts persisted first.
    results = evaluate(arrays, private, manifest, models, predictions)
    write(OUT/"RESULTS.json", results); write(OUT/"SUMMARY.json", dict(**summarize(results), seconds=time.perf_counter()-started))


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
