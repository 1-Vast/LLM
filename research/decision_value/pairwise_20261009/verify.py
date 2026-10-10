"""Independent arithmetic for frozen single-measurement pairwise research.

No producer fitting, updating, choosing or metric function is imported here.
The completed verification entry point is bound before scored outputs are read.
"""
import ast
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdMolDescriptors
from scipy.stats import norm, t
from threadpoolctl import threadpool_limits


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKET = ROOT / "research/astra/boundary_acquisition_20261007/packet2"
AUDIT = ROOT / "outputs/knowledge_layer_validation_20261009/AUDIT.json"
RELEASE = ROOT / "outputs/paper_01286/released_test"
REPRESENTATIONS = ("molecule", "knowledge", "Morgan", "permutedknowledge")
ALPHAS = (0., .1, .25, .5, 1.)
ETAS = (0., .5, 1.)
LAMBDAS = (None, 1., 10., 100.)
SIMPLE = ("no_update", "empirical_full", "fixed_shrink", "cv_shrink", "gated_cv_shrink")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def equal(actual, expected):
    np.testing.assert_allclose(actual, expected, atol=1e-12, rtol=1e-10)


def top(values, count=5):
    return sorted(range(len(values)), key=lambda i: (-values[i], i))[:count]


def prior(arrays, history, cell):
    if not history or cell in history:
        raise ValueError("prior_requires_nonempty_disjoint_history")
    weights = np.where(arrays["availability_B"][history], arrays["precision_B"][history], 0.)
    if np.any(weights.sum(0) <= 0):
        raise ValueError("missing_B_reference_support")
    observed = np.where(arrays["availability_B"][history], arrays["train_B"][history], 0.)
    baseline = (weights * observed).sum(0) / weights.sum(0)
    support = arrays["state_available_B"][history]
    if np.any(support.sum(0) <= 0):
        raise ValueError("missing_STATE_reference_support")
    centre = np.where(support, arrays["state_B"][history], 0.).sum(0) / support.sum(0)
    delta = np.where(arrays["state_available_B"][cell], arrays["state_B"][cell] - centre, 0.)
    return baseline + .5 * delta


def shift(arrays, history):
    support = (arrays["availability_A"] & arrays["availability_B"])[history]
    values = np.where(support, arrays["train_A"][history] - arrays["train_B"][history], 0.)
    return values.sum(0) / support.sum(0)


def errors(arrays, history):
    residuals = []
    for cell in history:
        others = [other for other in history if other != cell]
        mean = prior(arrays, others, cell)
        residuals.append(np.r_[arrays["train_B"][cell] - mean,
                               arrays["train_A"][cell] - mean - shift(arrays, others)])
    return np.array(residuals)


def condition_mask(records, labels):
    declarations = [ast.literal_eval(label) for label in labels]
    for record, declaration in zip(records, declarations):
        assert len(declaration) == 1
        assert (record["dose"], record["unit"]) == tuple(declaration[0][1:])
    return np.array([[(a["dose"], a["unit"]) == (b["dose"], b["unit"])
                      for b in records] for a in records], dtype=float)


def candidate_kernels(records, features, labels):
    groups = {}
    for index, record in enumerate(records):
        molecule = Chem.MolFromSmiles(record["smiles"])
        assert molecule is not None
        assert Chem.MolToSmiles(molecule, isomericSmiles=True) == record["smiles"]
        groups.setdefault((record["cid"], record["smiles"]), []).append(index)
    identities = sorted(groups)
    permutation = np.random.default_rng(20261009).permutation(len(identities))
    shuffled = np.empty_like(features["knowledge1024"])
    for destination, source in zip(identities, permutation):
        shuffled[groups[destination]] = features["knowledge1024"][groups[identities[source]][0]]
    fingerprints = []
    RDLogger.DisableLog("rdApp.warning")
    for record in records:
        bits = np.zeros(2048)
        fingerprint = rdMolDescriptors.GetMorganFingerprintAsBitVect(
            Chem.MolFromSmiles(record["smiles"]), 2, nBits=2048)
        DataStructs.ConvertToNumpyArray(fingerprint, bits)
        fingerprints.append(bits)
    mask = condition_mask(records, labels)
    kernels = {}
    for arm, matrix in (("molecule", features["molecule256"]),
                        ("knowledge", features["knowledge1024"]),
                        ("Morgan", np.array(fingerprints)),
                        ("permutedknowledge", shuffled)):
        matrix = np.asarray(matrix, dtype=float)
        assert matrix.shape[0] == len(records) and np.isfinite(matrix).all()
        norms = np.sqrt((matrix * matrix).sum(1))
        assert (norms > 0).all()
        matrix = matrix / norms[:, None]
        kernel = np.einsum("id,jd->ij", matrix, matrix) * mask
        np.fill_diagonal(kernel, 1.)
        kernels[arm] = kernel
    return kernels


def joint_covariances(residuals, kernels):
    n = residuals.shape[1] // 2
    raw = np.einsum("ni,nj->ij", residuals, residuals) / len(residuals)
    scales = np.sqrt(np.diag(raw))
    standardized = np.divide(residuals, scales, out=np.zeros_like(residuals), where=scales > 0)
    rho = float(np.clip(np.mean(standardized[:, :n] * standardized[:, n:]), -1., 1.))
    matrices = {"empirical": raw}
    for arm, kernel in kernels.items():
        matrices[arm] = np.kron(np.array([[1., rho], [rho, 1.]]), kernel) * np.outer(scales, scales)
    for arm, matrix in matrices.items():
        matrices[arm] = .5 * (matrix + np.diag(np.diag(matrix))) + np.eye(2*n) * 1e-12
    return matrices, rho


def fitted_model(arrays, history, kernels, mask):
    residuals = errors(arrays, history)
    matrices, rho = joint_covariances(residuals, kernels)
    for matrix in matrices.values():
        matrix *= np.kron(np.ones((2, 2)), mask)
    centre = arrays["basal"][history].mean(0)
    states = arrays["basal"][history] - centre
    norms = np.sqrt((states*states).sum(1))
    normalized = np.divide(states, norms[:, None], out=np.zeros_like(states), where=norms[:, None] > 0)
    values, vectors = np.linalg.eigh(np.einsum("ig,jg->ij", normalized, normalized))
    return dict(residuals=residuals, matrices=matrices, rho=rho, shift=shift(arrays, history),
                centre=centre, normalized=normalized, values=np.maximum(values, 0.), vectors=vectors)


def target_similarity(arrays, cell, model):
    state = arrays["basal"][cell] - model["centre"]
    norm_value = np.sqrt(np.dot(state, state))
    return model["normalized"] @ state / norm_value if norm_value > 0 else np.zeros(len(model["residuals"]))


def mean_correction(arrays, cell, model, drug_eigen, penalty):
    if penalty is None:
        return np.zeros(146)
    drug_values, drug_vectors = drug_eigen
    cell_values, cell_vectors = model["values"], model["vectors"]
    residual_B = model["residuals"][:, :146]
    rotated = cell_vectors.T @ residual_B @ drug_vectors
    solution = rotated / (np.outer(cell_values, drug_values) + penalty)
    target_row = target_similarity(arrays, cell, model) @ cell_vectors
    return (target_row @ solution * drug_values) @ drug_vectors.T


def forecast(arrays, cell, model, baseline, query, observed_A, eigens, configuration):
    representation = configuration.get("representation")
    penalty = configuration.get("penalty")
    eta = configuration.get("eta", 0.)
    alpha = float(configuration.get("alpha", 0.))
    gated = configuration.get("gated", False)
    correction = mean_correction(arrays, cell, model, eigens[representation], penalty) if representation else np.zeros(146)
    covariance = model["matrices"]["empirical"]
    if representation:
        covariance = (1-eta)*covariance + eta*model["matrices"][representation]
    cross, variance = covariance[:146, 146+query], float(covariance[146+query, 146+query])
    weights = np.maximum(target_similarity(arrays, cell, model), 0.)
    effective_count = float(weights.sum()**2 / np.dot(weights, weights)) if np.dot(weights, weights) > 0 else 0.
    support = min(1., effective_count/4) if effective_count >= 2 else 0.
    innovation, innovation_z, outlier, actual_alpha = 0., None, 1., alpha
    if alpha > 0:
        assert observed_A is not None and np.isfinite(observed_A)
        innovation = float(observed_A - baseline[query] - model["shift"][query])
        innovation_z = innovation/np.sqrt(variance) if variance > 0 else None
        if gated:
            outlier = min(1., 3/abs(innovation_z)) if innovation_z else 1.
            actual_alpha *= support*outlier
    if variance <= 0:
        actual_alpha = 0.
    movement = actual_alpha*cross/variance*innovation if actual_alpha else np.zeros(146)
    posterior = covariance[:146, :146].copy()
    if actual_alpha:
        posterior -= actual_alpha*np.outer(cross, cross)/variance
    return dict(mean=baseline+correction+movement, covariance=(posterior+posterior.T)/2,
                alpha_effective=actual_alpha, innovation=innovation, innovation_z=innovation_z,
                n_eff=effective_count, support_factor=support, outlier_factor=outlier,
                variance_A=variance, predicted_A=float(baseline[query]+model["shift"][query]),
                adapter=correction, feedback=movement, cross=cross)


def frozen_comparisons(mean):
    ranked = top(mean, len(mean))
    pairs = [(left, right) for left in ranked[2:5] for right in ranked[5:8]]
    centre = (mean[ranked[4]] + mean[ranked[5]]) / 2
    query = min(range(len(mean)), key=lambda index: (abs(mean[index] - centre), index))
    return np.array(pairs), query


def pair_metrics(mean, covariance, pairs, outcome, prior_mean, inflation=1., tolerance=1e-12):
    left, right = pairs.T
    actual = outcome[left] - outcome[right]
    delta = mean[left] - mean[right]
    old = prior_mean[left] - prior_mean[right]
    variance = np.diag(covariance)[left] + np.diag(covariance)[right] - 2*covariance[left, right]
    variance = np.maximum(variance, 1e-12)
    probability = norm.cdf(delta / (np.sqrt(variance)*inflation))
    # Coherent full-menu ranking uses ascending candidate index for score ties.
    choice_left = (delta > 0) | ((delta == 0) & (left < right))
    initial_left = (old > 0) | ((old == 0) & (left < right))
    defined = np.abs(actual) > tolerance
    correct = choice_left == (actual > 0)
    initial_correct = initial_left == (actual > 0)
    regret = np.where(correct, 0., np.abs(actual))
    flipped = choice_left != initial_left
    return dict(delta=delta, variance=variance, probability=probability,
                regret=float(np.mean(regret)), flips=int(flipped.sum()),
                corrected=int((flipped & ~initial_correct & correct & defined).sum()),
                harmful=int((flipped & initial_correct & ~correct & defined).sum()),
                brier=float(np.mean((probability[defined] - (actual[defined] > 0))**2)) if defined.any() else 0.)


def paired_context_comparison(new, control):
    differences = np.asarray(control) - np.asarray(new)
    radius = t.ppf(.975, len(differences)-1) * differences.std(ddof=1) / np.sqrt(len(differences))
    standard_error = differences.std(ddof=1) / np.sqrt(len(differences))
    pvalue = float(t.sf(differences.mean()/standard_error, len(differences)-1)) if standard_error > 0 else (0. if differences.mean() > 0 else 1.)
    return dict(delta=float(differences.mean()), ci=[float(differences.mean()-radius),
                float(differences.mean()+radius)], pvalue=pvalue)


def holm_adjust(values):
    ordered = sorted(values, key=lambda name: (values[name], name))
    adjusted, running = {}, 0.
    for rank, name in enumerate(ordered):
        running = max(running, values[name] * (len(ordered)-rank))
        adjusted[name] = min(1., running)
    return adjusted


def regret(mean, outcome, pairs):
    left, right = pairs.T
    choose_left = (mean[left] > mean[right]) | ((mean[left] == mean[right]) & (left < right))
    chosen = np.where(choose_left, outcome[left], outcome[right])
    return float(np.mean(np.maximum(outcome[left], outcome[right])-chosen))


def configurations(chosen, matched_alpha):
    configs = dict(no_update={}, empirical_full=dict(alpha=1.), fixed_shrink=dict(alpha=.1),
                   cv_shrink=dict(alpha=chosen["empirical_alpha"]),
                   gated_cv_shrink=dict(alpha=chosen["gated_empirical_alpha"], gated=True),
                   matched_strength_empirical=dict(alpha=matched_alpha))
    for representation in REPRESENTATIONS:
        settings = chosen[representation]
        configs[representation+"_only"] = dict(representation=representation, penalty=settings["penalty"])
        configs[representation+"_feedback"] = dict(representation=representation, penalty=settings["penalty"],
                eta=settings["eta"], alpha=settings["alpha"], gated=True)
    configs["knowledge_feedback_only"] = dict(configs["knowledge_feedback"], penalty=None)
    configs["selective_knowledge"] = dict(configs["knowledge_feedback"])
    return configs


def choose_models(arrays, history, kernels, eigens, mask):
    inner = []
    folds = []
    for fold in range(3):
        positions = [position for position in range(len(history)) if position % 3 != fold]
        held_positions = [position for position in range(len(history)) if position % 3 == fold]
        keep = [history[position] for position in positions]
        model = fitted_model(arrays, keep, kernels, mask)
        folds.append(dict(keep_positions=positions, held_positions=held_positions))
        for position in held_positions:
            cell = history[position]
            baseline = prior(arrays, keep, cell)
            pairs, query = frozen_comparisons(baseline)
            inner.append(dict(model=model, cell=cell, baseline=baseline, pairs=pairs, query=query,
                observed_A=float(arrays["train_A"][cell, query]), outcome=arrays["train_B"][cell]))

    def forecasts(configuration):
        return [forecast(arrays, row["cell"], row["model"], row["baseline"], row["query"],
                         row["observed_A"], eigens, configuration) for row in inner]

    def loss(configuration):
        return float(np.mean([regret(prediction["mean"], row["outcome"], row["pairs"])
                              for row, prediction in zip(inner, forecasts(configuration))]))

    alpha_losses = [(alpha, loss(dict(alpha=alpha))) for alpha in ALPHAS]
    gated_alpha_losses = [(alpha, loss(dict(alpha=alpha, gated=True))) for alpha in ALPHAS]
    chosen = dict(empirical_alpha=min(alpha_losses, key=lambda item: (item[1], item[0]))[0],
                  gated_empirical_alpha=min(gated_alpha_losses, key=lambda item: (item[1], item[0]))[0])
    tuning = dict(empirical_alpha_losses=[dict(alpha=alpha, regret=value) for alpha, value in alpha_losses],
                  gated_empirical_alpha_losses=[dict(alpha=alpha, regret=value) for alpha, value in gated_alpha_losses])
    for representation in REPRESENTATIONS:
        mean_losses = [(penalty, loss(dict(representation=representation, penalty=penalty))) for penalty in LAMBDAS]
        penalty = min(range(len(mean_losses)), key=lambda index: (mean_losses[index][1], index))
        selected_penalty = mean_losses[penalty][0]
        feedback_losses = [dict(eta=eta, alpha=alpha, regret=loss(dict(representation=representation,
            penalty=selected_penalty, eta=eta, alpha=alpha, gated=True))) for eta in ETAS for alpha in ALPHAS]
        best = min(feedback_losses, key=lambda item: (item["regret"], item["alpha"], item["eta"]))
        chosen[representation] = dict(penalty=selected_penalty, eta=best["eta"], alpha=best["alpha"])
        tuning[representation] = dict(penalty_losses=[dict(penalty=penalty, regret=value) for penalty, value in mean_losses],
                                      feedback_losses=feedback_losses)
    knowledge_expected, empirical_expected = [], []
    clip_second_moment = 1-6*norm.pdf(3)+16*norm.sf(3)
    for row in inner:
        left, right = row["pairs"].T
        setting = chosen["knowledge"]
        for representation, eta, alpha, gated, destination in (
                ("knowledge", setting["eta"], setting["alpha"], True, knowledge_expected),
                (None, 0., 1., False, empirical_expected)):
            pred = forecast(arrays, row["cell"], row["model"], row["baseline"], row["query"], None,
                            eigens, dict(representation=representation, eta=eta))
            cross_difference = pred["cross"][left]-pred["cross"][right]
            multiplier = alpha**2
            if gated:
                multiplier *= pred["support_factor"]**2*clip_second_moment
            destination.extend((multiplier*cross_difference**2/pred["variance_A"]).tolist())
    target_rms = float(np.sqrt(np.mean(knowledge_expected)))
    full_rms = float(np.sqrt(np.mean(empirical_expected)))
    uncapped = target_rms/full_rms if full_rms > 0 else 0.
    matched_alpha = min(1., uncapped)
    configs = configurations(chosen, matched_alpha)
    scales, inner_losses = {}, {}
    for arm, configuration in configs.items():
        residual_z = []
        for row, pred in zip(inner, forecasts(configuration)):
            left, right = row["pairs"].T
            variance = np.maximum(np.diag(pred["covariance"])[left]+np.diag(pred["covariance"])[right]
                                  -2*pred["covariance"][left, right], 1e-12)
            predicted = pred["mean"][left]-pred["mean"][right]
            observed = row["outcome"][left]-row["outcome"][right]
            residual_z.extend(((predicted-observed)/np.sqrt(variance)).tolist())
        scales[arm] = max(1., float(np.sqrt(np.mean(np.square(residual_z)))))
        inner_losses[arm] = loss(configuration)
    return dict(chosen=chosen, configurations=configs, probability_scales=scales,
                selected_simple=min(SIMPLE, key=lambda arm: (inner_losses[arm], SIMPLE.index(arm))),
                inner_losses=inner_losses, inner_folds=folds, tuning=tuning,
                matched_strength=dict(alpha=matched_alpha, uncapped_alpha=uncapped, capped=uncapped>1.,
                    target_pair_movement_RMS=target_rms, empirical_full_pair_movement_RMS=full_rms,
                    achieved_pair_movement_RMS=matched_alpha*full_rms,
                    residual_match_error=matched_alpha*full_rms-target_rms,
                    matching="model-implied training-OOF expected feedback movement; Gaussian clipped-Z second moment",
                    clipped_normal_second_moment=float(clip_second_moment)))


def equal_tree(expected, actual, path=""):
    if isinstance(expected, dict):
        assert set(expected) == set(actual), path+":fields"
        for key, value in expected.items():
            equal_tree(value, actual[key], path+"/"+key)
    elif isinstance(expected, (list, tuple, np.ndarray)):
        assert len(expected) == len(actual), path+":length"
        for index, value in enumerate(expected):
            equal_tree(value, actual[index], path+f"/{index}")
    elif expected is None or isinstance(expected, (str, bool)):
        assert expected == actual, path
    elif isinstance(expected, (int, float, np.number)):
        equal(expected, actual)
    else:
        raise TypeError(type(expected))


def expected_commit(prediction, baseline, pairs, scale, selective):
    mean, covariance = prediction["mean"], prediction["covariance"]
    left, right = pairs.T
    delta = mean[left]-mean[right]
    variance = np.maximum(np.diag(covariance)[left]+np.diag(covariance)[right]-2*covariance[left, right], 1e-12)
    probability = norm.cdf(delta/(np.sqrt(variance)*scale))
    proposal, initial = top(mean), top(baseline)
    incoming, outgoing = sorted(set(proposal)-set(initial)), sorted(set(initial)-set(proposal))
    swap_checks = []
    for i in incoming:
        for j in outgoing:
            sd = np.sqrt(max(covariance[i, i]+covariance[j, j]-2*covariance[i, j], 1e-12))*scale
            swap_checks.append(dict(incoming=i, outgoing=j, probability=float(norm.cdf((mean[i]-mean[j])/sd))))
    accepted = not selective or all(check["probability"] >= .95 for check in swap_checks)
    decisions = []
    for i, j, difference, pvalue in zip(left, right, delta, probability):
        winner = int(i if difference > 0 or (difference == 0 and i < j) else j)
        decisions.append(None if selective and .05 < pvalue < .95 else winner)
    result = dict(selected=proposal if accepted else initial, proposal=proposal, swap_accepted=accepted,
        swap_checks=swap_checks, pair_probabilities=probability.tolist(), pair_variances=variance.tolist(),
        pair_delta=delta.tolist(), pair_decisions=decisions, probability_scale=scale)
    for key in ("alpha_effective", "innovation", "innovation_z", "n_eff", "support_factor",
                "outlier_factor", "predicted_A", "variance_A"):
        result[key] = prediction[key]
    return result


def scored_metrics(commitment, mean, outcome, tolerance=1e-12):
    pairs = np.asarray(commitment["pairs"])
    left, right = pairs.T
    difference = outcome[left]-outcome[right]
    chosen_left = np.array([decision is None or decision == i for decision, i in zip(commitment["pair_decisions"], left)])
    flipped, defined = ~chosen_left, np.abs(difference) > tolerance
    probabilities = np.array(commitment["pair_probabilities"])
    labels = difference > 0
    bins = []
    for low in np.arange(0., 1., .2):
        in_bin = defined & (probabilities >= low) & ((probabilities < low+.2) if low < .8 else (probabilities <= 1.))
        bins.append(dict(count=int(in_bin.sum()), sum_probability=float(probabilities[in_bin].sum()),
                         sum_positive=int(labels[in_bin].sum())))
    initial, selected = commitment["initial_selected"], commitment["selected"]
    incoming, outgoing = sorted(set(selected)-set(initial)), sorted(set(initial)-set(selected))
    replacements = [dict(incoming=i, outgoing=j, B_delta=float(outcome[i]-outcome[j]))
        for i, j in zip(sorted(incoming, key=lambda i: (-mean[i], i)), sorted(outgoing, key=lambda i: (mean[i], i)))]
    error = np.abs(np.array(commitment["pair_delta"])-difference)
    interval_radius = norm.ppf(.975)*np.sqrt(commitment["pair_variances"])*commitment["probability_scale"]
    chosen_outcome = np.where(chosen_left, outcome[left], outcome[right])
    return dict(pair_regret=float(np.mean(np.maximum(outcome[left], outcome[right])-chosen_outcome)),
        corrected_flips=int((flipped & (difference < -tolerance)).sum()),
        harmful_flips=int((flipped & (difference > tolerance)).sum()),
        ambiguous_flips=int((flipped & ~defined).sum()), flips=int(flipped.sum()), defined_pairs=int(defined.sum()),
        flip_coverage=float(flipped.mean()),
        selective_coverage=sum(decision is not None for decision in commitment["pair_decisions"])/len(pairs),
        brier=float(np.mean((probabilities[defined]-labels[defined])**2)) if defined.any() else None,
        true_pair_delta=difference.tolist(), calibration_bins=bins,
        gaussian_interval_95_coverage=float((error <= interval_radius).mean()),
        swapped_in=incoming, swapped_out=outgoing, replacement_pairs=replacements,
        harmful_replacements=sum(item["B_delta"] < -tolerance for item in replacements),
        terminal_B=float(outcome[selected].sum()), initial_B=float(outcome[initial].sum()),
        terminal_delta=float(outcome[selected].sum()-outcome[initial].sum()),
        top5_regret=float(outcome[top(outcome)].sum()-outcome[selected].sum()),
        RNA_MSE=float(np.mean((mean-outcome)**2)))


def confidence_interval(values):
    values = np.asarray(values)
    radius = float(t.ppf(.975, len(values)-1)*values.std(ddof=1)/np.sqrt(len(values)))
    return [float(values.mean()-radius), float(values.mean()+radius)]


def summary_arithmetic(results, sizes=(4, 8, 16)):
    summaries, comparisons = {}, {}
    arms = tuple(configurations(dict(empirical_alpha=0., gated_empirical_alpha=0.,
                    **{name:dict(penalty=None, eta=0., alpha=0.) for name in REPRESENTATIONS}), 0.))
    for size in sizes:
        rows = [row for row in results if row["history_size"] == size]
        contexts = sorted({row["context"] for row in rows})
        lookup = {(row["episode"], row["arm"]):row for row in rows}
        summaries[str(size)] = {}
        for arm in arms:
            group = [row for row in rows if row["arm"] == arm]
            total_flips = sum(row["flips"] for row in group)
            arm_summary = {field:float(np.mean([row[field] for row in group])) for field in
                ("pair_regret", "terminal_B", "top5_regret", "RNA_MSE", "flip_coverage",
                 "selective_coverage", "gaussian_interval_95_coverage")}
            defined_brier = [row["brier"] for row in group if row["brier"] is not None]
            arm_summary["brier"] = float(np.mean(defined_brier)) if defined_brier else None
            arm_summary["brier_defined_episodes"] = len(defined_brier)
            arm_summary.update(contexts=len(contexts), seed_episodes=len(group),
                **{field:sum(row[field] for row in group) for field in
                   ("corrected_flips", "harmful_flips", "ambiguous_flips", "harmful_replacements")},
                flips=total_flips,
                harmful_flip_fraction=sum(row["harmful_flips"] for row in group)/total_flips if total_flips else None,
                total_cost=sum(row["cost"] for row in group))
            summaries[str(size)][arm] = arm_summary
        knowledge = [row for row in rows if row["arm"] == "knowledge_feedback"]
        comparisons[str(size)] = {}
        for comparator in ("no_update", "selected_simple", "Morgan_feedback", "permutedknowledge_feedback", "matched_strength_empirical"):
            delta, brier_delta = [], []
            for context in contexts:
                group = [row for row in knowledge if row["context"] == context]
                matched = [(row, lookup[(row["episode"], row["selected_simple"] if comparator == "selected_simple" else comparator)])
                           for row in group]
                assert len(matched) == 3
                delta.append(float(np.mean([base["pair_regret"]-row["pair_regret"] for row, base in matched])))
                defined_brier = [row["brier"]-base["brier"] for row, base in matched
                                 if row["brier"] is not None and base["brier"] is not None]
                if defined_brier:
                    brier_delta.append(float(np.mean(defined_brier)))
            n, variance = len(delta), np.std(delta, ddof=1)
            pvalue = float(t.sf(np.mean(delta)/(variance/np.sqrt(n)), n-1)) if variance > 0 else (0. if np.mean(delta)>0 else 1.)
            comparisons[str(size)][comparator] = dict(regret_improvement=float(np.mean(delta)), context_95CI=confidence_interval(delta),
                one_sided_p=pvalue, brier_delta=float(np.mean(brier_delta)) if brier_delta else None,
                brier_delta_context_95CI=confidence_interval(brier_delta) if len(brier_delta)>1 else None,
                brier_context_unit_count=len(brier_delta), context_unit_count=n)
        terminal, pair_utility = [], []
        for row in knowledge:
            episode = row["episode"]
            only, feedback, initial = (lookup[(episode, arm)] for arm in ("knowledge_only", "gated_cv_shrink", "no_update"))
            terminal.append(row["terminal_B"]-only["terminal_B"]-feedback["terminal_B"]+initial["terminal_B"])
            pair_utility.append(-row["pair_regret"]+only["pair_regret"]+feedback["pair_regret"]-initial["pair_regret"])
        summaries[str(size)]["factorial_terminal_interaction"] = float(np.mean(terminal))
        summaries[str(size)]["factorial_pair_utility_interaction"] = float(np.mean(pair_utility))
    primary = comparisons["8"]
    adjusted = holm_adjust({name:record["one_sided_p"] for name, record in primary.items()})
    for name, value in adjusted.items():
        primary[name]["holm_adjusted_p"] = value
    knowledge = summaries["8"]["knowledge_feedback"]
    gates = dict(positive_regret=all(item["regret_improvement"] > 0 and item["holm_adjusted_p"] <= .05 for item in primary.values())
                 and primary["no_update"]["regret_improvement"] >= .001,
                 harmful_flip_fraction=knowledge["harmful_flip_fraction"] is not None and knowledge["harmful_flip_fraction"] <= .10,
                 nontrivial_flip_coverage=knowledge["flip_coverage"] >= .05,
                 brier_noninferiority=primary["selected_simple"]["brier_delta"] is not None
                 and primary["selected_simple"]["brier_delta"] <= .01)
    return dict(history_sizes=summaries, paired_seed_mean_context_comparisons=comparisons,
                gate_components=gates, registered_development_gate=all(gates.values()))


def freeze_inputs():
    for filename in ("FREEZE.json", "VERIFY_FREEZE.json"):
        for name, expected in read(HERE / filename)["inputs"].items():
            assert sha(ROOT / name) == expected, name


def verify(out):
    started = time.perf_counter()
    freeze_inputs()
    for filename in ("PRE_A_FREEZE.json", "COMMITMENT_FREEZE.json"):
        frozen = read(out/filename)
        assert frozen["source_freeze_sha256"] == sha(HERE/"FREEZE.json")
        for name, expected in frozen["inputs"].items():
            assert sha(out/name) == expected, name
    arrays = dict(np.load(PACKET/"training_arrays.npz"))
    manifest = read(PACKET/"PACKET_MANIFEST.json")
    records = read(AUDIT)["records"]
    identities = read(RELEASE/"IDENTITIES.json")["records"]
    assert [(row["cid"], row["smiles"]) for row in records] == [(row["cid"], row["smiles"]) for row in identities]
    features = dict(np.load(RELEASE/"FEATURES.npz"))
    kernels = candidate_kernels(records, features, manifest["labels"])
    mask = condition_mask(records, manifest["labels"])
    eigens = {}
    for name, matrix in kernels.items():
        values, vectors = np.linalg.eigh(matrix)
        assert values.min() >= -1e-8
        eigens[name] = (np.maximum(values, 0.), vectors)
    complete = np.flatnonzero((arrays["availability_A"] & arrays["availability_B"] & arrays["state_available_B"]).all(1)).tolist()
    assert len(complete) == 43 and 31 not in complete and 34 not in complete
    factors = dict(np.load(out/"FACTORS.npz"))
    predictions = dict(np.load(out/"PREDICTIONS.npz"))
    choices = read(out/"MODEL_CHOICES.json")
    plans = read(out/"PRE_A_PLANS.json")
    requests = read(out/"PURCHASE_REQUESTS.json")
    receipts = read(out/"A_RECEIPTS.json")
    commitments = read(out/"COMMITMENTS.json")
    results = read(out/"RESULTS.json")
    summary = read(out/"SUMMARY.json")
    assert len(choices) == len(plans) == len(requests) == len(receipts) == 387
    assert len(commitments) == len(results) == len(predictions) == 387*16
    plan_lookup = {row["episode"]:row for row in plans}
    request_lookup = {row["episode"]:row for row in requests}
    receipt_lookup = {row["episode"]:row for row in receipts}
    commitment_lookup = {(row["episode"], row["arm"]):row for row in commitments}
    result_lookup = {(row["episode"], row["arm"]):row for row in results}
    assert len(plan_lookup) == len(request_lookup) == len(receipt_lookup) == 387
    assert len(commitment_lookup) == len(result_lookup) == 387*16
    expected_results = []
    policy_charges = 0
    for cell in complete:
        for seed in (11, 23, 47):
            pool = np.array(sorted(set(complete)-{cell}))
            order = np.random.default_rng(np.random.SeedSequence([seed, cell])).permutation(pool)
            previous = set()
            for size in (4, 8, 16):
                episode = f"ref{cell}__seed{seed}__n{size}"
                history = sorted(order[:size].tolist())
                assert previous < set(history) and cell not in history
                previous = set(history)
                choice = choices[episode]
                equal_tree(history, choice["history_ids"])
                assert choice["context"] == cell and choice["seed"] == seed and choice["history_size"] == size
                expected_choice = choose_models(arrays, history, kernels, eigens, mask)
                equal_tree(expected_choice, {key:choice[key] for key in expected_choice}, episode+"/choice")
                fitted = fitted_model(arrays, history, kernels, mask)
                base = prior(arrays, history, cell)
                equal(fitted["rho"], choice["rho"])
                equal(factors[episode+"__prior"], base)
                equal(factors[episode+"__error_B"], fitted["residuals"][:, :146])
                equal(factors[episode+"__error_A"], fitted["residuals"][:, 146:])
                equal(factors[episode+"__offset"], fitted["shift"])
                equal(factors[episode+"__basal_centre"], fitted["centre"])
                equal(factors[episode+"__normalized_basal"], fitted["normalized"])
                equal(factors[episode+"__target_basal"], arrays["basal"][cell])
                values = factors[episode+"__cell_values"]
                vectors = factors[episode+"__cell_vectors"]
                equal(vectors.T@vectors, np.eye(size))
                equal((vectors*values)@vectors.T, fitted["normalized"]@fitted["normalized"].T)
                equal(values, fitted["values"])
                pairs, query = frozen_comparisons(base)
                plan = dict(episode=episode, context=cell, seed=seed, history_size=size, pairs=pairs.tolist(),
                            query_A=query, initial_selected=top(base), prediction_key=episode+"__prior")
                equal_tree(plan, plan_lookup[episode], episode+"/plan")
                equal_tree(dict(episode=episode, context=cell, query_A=query, measurement_units=1,
                                status="charged_before_release"), request_lookup[episode], episode+"/request")
                value = float(arrays["train_A"][cell, query])
                equal_tree(dict(episode=episode, context=cell, query_A=query, observed_A=value,
                                measurement_units=1), receipt_lookup[episode], episode+"/receipt")
                for arm, configuration in expected_choice["configurations"].items():
                    feedback = arm not in ("no_update", *(representation+"_only" for representation in REPRESENTATIONS))
                    pred = forecast(arrays, cell, fitted, base, query, value if feedback else None, eigens, configuration)
                    committed = expected_commit(pred, base, pairs, expected_choice["probability_scales"][arm],
                                                selective=arm == "selective_knowledge")
                    prediction_key = episode+"__"+arm
                    expected_row = dict(plan, arm=arm, selected_simple=expected_choice["selected_simple"],
                        configuration=configuration, prediction_key=prediction_key, cost=6 if feedback else 5,
                        purchased_A=[query] if feedback else [], **committed)
                    equal_tree(expected_row, commitment_lookup[(episode, arm)], episode+"/"+arm+"/commit")
                    equal(pred["mean"], predictions[prediction_key])
                    policy_charges += int(feedback)
                    outcome = arrays["train_B"][cell]
                    scored = dict(expected_row, **scored_metrics(expected_row, pred["mean"], outcome),
                        near_equivalence_sensitivity=scored_metrics(expected_row, pred["mean"], outcome, tolerance=.001))
                    equal_tree(scored, result_lookup[(episode, arm)], episode+"/"+arm+"/result")
                    expected_results.append(scored)
        print(f"Independently verified all histories/models/one-A commitments/scores: ref{cell}", flush=True)
    expected_summary = summary_arithmetic(expected_results)
    for field, value in expected_summary.items():
        equal_tree(value, summary[field], "summary/"+field)
    assert summary["primary_history_size"] == 8
    payload = dict(status="PASS", episodes=387, result_rows=len(expected_results), contexts=43,
        history_sizes=[4, 8, 16], seed_repetitions=3, inference_units_per_size=43,
        common_paid_source_receipts=len(receipts), counterfactual_policy_A_charges=policy_charges,
        frozen_comparisons=387*9, arms=16,
        checks=["All producer and independent-verifier freezes; pre-A and pre-B persisted artifact hashes",
                "Whole-context nested histories, all three inner folds and exclusion of outer target labels",
                "Independent precision-weighted STATE prior, residual moments and exact dose/unit kernels",
                "Tensor ridge, every lambda/eta/alpha regret choice including identically gated simple control",
                "Expected movement matching from A variance and analytic clipped Gaussian moment",
                "OOF probability scales, basal support and realized outlier gates",
                "Frozen nine pairs and common query; charge/one-A receipt; all coherent commitments and probabilities",
                "Every pair regret, harmful/corrected/ambiguous flip, calibration bin, interval, swap and terminal metric",
                "Three-seed context aggregation, five Holm comparisons, factorial interaction and development gate"],
        seconds=time.perf_counter()-started,
        claim_boundary="Independent numerical reconstruction of exposed RNA development research; not independent cultures, calibrated conditional risk, functional effect or financial NetVOI.")
    with (out/"VERIFIED.json").open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(payload, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT/"outputs/decision_value/pairwise_20261009")
    args = parser.parse_args()
    verify(args.out)


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
