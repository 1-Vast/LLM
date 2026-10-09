"""Repeated complete-history scarcity without new or synthetic RNA outcomes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

import numpy as np
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("frozen_replacement_for_scarcity", HERE/"run.py")
study = importlib.util.module_from_spec(spec); spec.loader.exec_module(study)
from kernel import ARMS, blend, boundary_schedule, candidate_kernels, conditional_mean, covariances

ROOT = study.ROOT
OUT = ROOT/"outputs/map_module_replacement_20261009/scarcity"
SIZES = (4, 8, 16)
SEEDS = (11, 23, 47)


def histories(complete, held, seed, sizes=SIZES):
    available = sorted(set(complete)-{held})
    if held not in complete or max(sizes) > len(available):
        raise ValueError("insufficient_complete_history_support")
    permutation = np.random.default_rng(np.random.SeedSequence([seed, held])).permutation(available)
    return {size: sorted(permutation[:size].tolist()) for size in sizes}


def choose(arrays, train, kernels):
    """Position-grouped inner folds keep at least two history rows at size four."""
    train = sorted(train)
    losses = {arm: {eta: [] for eta in study.ETAS} for arm in ARMS}
    folds = []
    for fold in range(3):
        held = [cell for position, cell in enumerate(train) if position % 3 == fold]
        keep = [cell for position, cell in enumerate(train) if position % 3 != fold]
        matrices, current_offset, detail = study.fitted(arrays, keep, kernels)
        folds.append(dict(fold=fold, held=held, **detail))
        for cell in held:
            prediction = study.prior(arrays, keep, cell)
            schedule = boundary_schedule(prediction)
            values = arrays["train_A"][cell, schedule]
            for arm in ARMS:
                for eta in study.ETAS:
                    updated = conditional_mean(prediction, current_offset,
                        blend(matrices["empirical"], matrices[arm], eta), schedule, values)
                    losses[arm][eta].append(float(np.mean((updated-arrays["train_B"][cell])**2)))
    choices = {}
    for arm in ARMS:
        scores = {eta: float(np.mean(values)) for eta, values in losses[arm].items()}
        choices[arm] = dict(eta=min(study.ETAS, key=lambda eta: (scores[eta], eta)), inner_posterior_mse=scores)
    return choices, folds


def residual_factors(arrays, train):
    errors_B, errors_A = [], []
    for cell in train:
        keep = [i for i in train if i != cell]
        prediction = study.prior(arrays, keep, cell)
        errors_B.append(arrays["train_B"][cell]-prediction)
        errors_A.append(arrays["train_A"][cell]-prediction-study.offset(arrays, keep))
    return np.array(errors_B), np.array(errors_A)


def build(arrays, kernels):
    complete = np.flatnonzero((arrays["availability_A"] & arrays["availability_B"]).all(1)).tolist()
    factors, choices = {}, {}
    for held in complete:
        for seed in SEEDS:
            for size, train in histories(complete, held, seed).items():
                key = f"ref{held}__seed{seed}__n{size}"
                chosen, folds = choose(arrays, train, kernels)
                _, current_offset, detail = study.fitted(arrays, train, kernels)
                error_B, error_A = residual_factors(arrays, train)
                factors[key+"__prior"] = study.prior(arrays, train, held)
                factors[key+"__offset"] = current_offset
                factors[key+"__error_B"] = error_B
                factors[key+"__error_A"] = error_A
                choices[key] = dict(context=held, seed=seed, history_size=size, arms=chosen, inner_folds=folds, **detail)
        print(f"Fitted scarcity ref{held}: nine registered histories", flush=True)
    return factors, choices


def evaluate(arrays, kernels, factors, choices):
    results = []
    for key, choice in choices.items():
        held = choice["context"]
        prediction, current_offset = factors[key+"__prior"], factors[key+"__offset"]
        matrices, rho = covariances(factors[key+"__error_B"], factors[key+"__error_A"], kernels)
        if rho != choice["rho"]:
            raise AssertionError("persisted_residual_factors_changed_model")
        initial = study.posterior.top5(prediction)
        schedule = boundary_schedule(prediction)
        for arm in ("no_screen", "empirical", *ARMS):
            if arm == "no_screen":
                result = dict(selected=initial, purchased_A=[], cost=5, posterior_mean_B=prediction.copy(),
                              history=[dict(committed_B=initial, cost_after_five_B=5)])
                eta = None
            else:
                eta = choice["arms"][arm]["eta"] if arm in ARMS else 0.
                covariance = blend(matrices["empirical"], matrices[arm], eta)
                result = study.posterior.replay(prediction, current_offset, covariance,
                    lambda i: float(arrays["train_A"][held, i]), schedule=schedule)
                result.pop("posterior_cov_B")
            # B outcomes enter only after this strategy commits selected indices.
            yB = arrays["train_B"][held]
            selected, final_mean = result["selected"], np.asarray(result["posterior_mean_B"])
            incoming, outgoing = sorted(set(selected)-set(initial)), sorted(set(initial)-set(selected))
            pairs = list(zip(sorted(incoming, key=lambda i: (-final_mean[i], i)),
                             sorted(outgoing, key=lambda i: (final_mean[i], i))))
            replacements = [dict(incoming=i, outgoing=j, B_delta=float(yB[i]-yB[j])) for i, j in pairs]
            result["posterior_mean_B"] = final_mean.tolist()
            results.append(dict(episode=key, context=held, seed=choice["seed"], history_size=choice["history_size"],
                arm=arm, eta=eta, initial_selected=initial, terminal_B=float(yB[selected].sum()),
                initial_B=float(yB[initial].sum()), delta_vs_no_screen=float(yB[selected].sum()-yB[initial].sum()),
                initial_mse=float(np.mean((prediction-yB)**2)), posterior_mse=float(np.mean((final_mean-yB)**2)),
                swapped_in=incoming, swapped_out=outgoing, replacement_pairs=replacements,
                harmful_replacements=sum(pair["B_delta"] < -1e-12 for pair in replacements), **result))
    return results


def summarize(results):
    summaries, comparisons = {}, {}
    for size in SIZES:
        rows = [row for row in results if row["history_size"] == size]
        contexts = sorted({row["context"] for row in rows})
        by_arm = {}
        summaries[str(size)] = {}
        for arm in ("no_screen", "empirical", *ARMS):
            group = [row for row in rows if row["arm"] == arm]
            by_arm[arm] = [float(np.mean([r["terminal_B"] for r in group if r["context"] == cell])) for cell in contexts]
            frequencies = {str(eta): sum(r["eta"] == eta for r in group) for eta in study.ETAS} if arm in ARMS else {}
            summaries[str(size)][arm] = dict(contexts=len(contexts), seed_episodes=len(group),
                mean_B=float(np.mean(by_arm[arm])), initial_mse=float(np.mean([r["initial_mse"] for r in group])),
                posterior_mse=float(np.mean([r["posterior_mse"] for r in group])),
                delta_vs_no_screen=float(np.mean([r["delta_vs_no_screen"] for r in group])),
                harm_seed_episodes=sum(r["delta_vs_no_screen"] < -1e-12 for r in group),
                harmful_replacements=sum(r["harmful_replacements"] for r in group),
                replacements=sum(len(r["replacement_pairs"]) for r in group), total_cost=sum(r["cost"] for r in group), eta_frequencies=frequencies)
        comparisons[str(size)] = {control: study.comparison(by_arm["knowledge"], by_arm[control])
                                  for control in ("empirical", "molecule", "Morgan", "permutedknowledge", "no_screen")}
    primary = comparisons["8"]
    gate = all(primary[control]["relative_delta"] is not None and primary[control]["relative_delta"] > .02
               and primary[control]["paired_context_95CI"][0] > 0 for control in ("empirical", "molecule", "Morgan"))
    return dict(history_sizes=summaries, paired_seed_mean_context_comparisons=comparisons,
                primary_history_size=8, registered_development_gate=gate,
                inference_unit="Average the three seed outcomes within each held context before computing paired nominal95%t intervals;43 context units, not129 independent seed repetitions.",
                claim_boundary="Scarce historical labels and STATE centering only; checkpoint pretraining unchanged. Known-exposed development RNA endpoints, not independent transfer, functional benefit, calibrated model risk or financial net value.")


def main():
    frozen = json.loads((HERE/"SCARCITY_FREEZE.json").read_text())
    for name, expected in frozen["inputs"].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != expected:
            raise ValueError("scarcity_freeze_mismatch:"+name)
    if OUT.exists():
        raise RuntimeError("Refuse to overwrite registered scarcity trial")
    OUT.mkdir(parents=True)
    started = time.perf_counter()
    arrays = dict(np.load(study.PACKET/"training_arrays.npz"))
    records = json.loads(study.AUDIT.read_text())["records"]
    identities = json.loads((study.RELEASE/"IDENTITIES.json").read_text())["records"]
    if [(r["cid"], r["smiles"]) for r in records] != [(r["cid"], r["smiles"]) for r in identities]:
        raise ValueError("authenticated_cache_identity_mismatch")
    kernels, metadata = candidate_kernels(records, dict(np.load(study.RELEASE/"FEATURES.npz")))
    factors, choices = build(arrays, kernels)
    np.savez_compressed(OUT/"FACTORS.npz", **factors)
    study.write(OUT/"MODEL_CHOICES.json", choices); study.write(OUT/"KERNEL_METADATA.json", metadata)
    results = evaluate(arrays, kernels, factors, choices)
    study.write(OUT/"RESULTS.json", results)
    study.write(OUT/"SUMMARY.json", dict(**summarize(results), seconds=time.perf_counter()-started))


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
