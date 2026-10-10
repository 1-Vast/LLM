"""Independent verification of conditional A/B means and paid residual transfer.

Only previously frozen independent numerical primitives are shared. No producer
fitting, update, acquisition, commitment or scoring function is imported.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time

import numpy as np
from scipy.stats import norm, t
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKET = ROOT/"research/astra/boundary_acquisition_20261007/packet2"
OLD_VERIFIER = ROOT/"research/decision_value/pairwise_20261009/verify.py"
spec = importlib.util.spec_from_file_location("prior_independent_pairwise_arithmetic", OLD_VERIFIER)
independent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(independent)
REPRESENTATIONS = ("molecule", "knowledge", "Morgan", "permutedknowledge")
ALPHAS, ETAS, SIZES, SEEDS = (0., .01, .1, .25), (0., .5), (4, 8, 16), (11, 23, 47)
ARMS = ("no_update", "knowledge_mean", "knowledge_old", "knowledge_refit_empirical", "knowledge_refit_map",
        "knowledge_strong_shrink", "molecule_refit_map", "Morgan_refit_map", "permutedknowledge_refit_map")


def coordinates(arrays):
    basal = arrays["basal"]
    centre = basal.mean(0)
    scale = np.sqrt(((basal-centre)**2).mean(0))
    scale = np.where(scale > 0, scale, 1.)
    standardized = (basal-centre)/scale
    difference = standardized[:, None, :]-standardized[None, :, :]
    squared_distance = np.sum(difference**2, axis=2)
    positive = squared_distance[np.triu_indices(len(basal), 1)]
    positive = positive[positive > 0]
    bandwidth = float(np.median(positive)) if len(positive) else 1.
    similarity = np.exp(-squared_distance/(2*bandwidth))
    return dict(centre=centre, scale=scale, standardized=standardized,
                squared_distance=squared_distance, bandwidth=bandwidth, similarity=similarity)


def support(reference, history, cell):
    weights = reference["similarity"][cell, history]
    square_sum = float(np.dot(weights, weights))
    neff = float(weights.sum()**2/square_sum) if square_sum > 0 else 0.
    support_factor = neff/(neff+4.)
    distance_ratio = float(np.min(reference["squared_distance"][cell, history])/reference["bandwidth"])
    return dict(n_eff=neff, support_factor=support_factor, distance_ratio=distance_ratio,
                distance_factor=1/(1+distance_ratio), weight=support_factor/(1+distance_ratio),
                weights=weights.tolist())


def baseline_bank(arrays, history):
    if len(history) < 2:
        return np.empty((0, 146)), np.empty((0, 146))
    errors_B, errors_A = [], []
    for cell in history:
        keep = [other for other in history if other != cell]
        mean = independent.prior(arrays, keep, cell)
        errors_B.append(arrays["train_B"][cell]-mean)
        errors_A.append(arrays["train_A"][cell]-mean-independent.shift(arrays, keep))
    return np.asarray(errors_B), np.asarray(errors_A)


def conditional_means(arrays, history, cell, reference, drug_eigen, cache):
    key = (tuple(history), id(drug_eigen[0]))
    base = independent.prior(arrays, history, cell)
    offset = independent.shift(arrays, history)
    if len(history) == 1:
        return base, base+offset
    if key not in cache:
        error_B, error_A = baseline_bank(arrays, history)
        cell_matrix = reference["similarity"][np.ix_(history, history)]
        cell_values, cell_vectors = np.linalg.eigh(cell_matrix)
        cell_values = np.maximum(cell_values, 0.)
        drug_values, drug_vectors = drug_eigen
        denominator = np.outer(cell_values, drug_values)+10.
        transformed = [cell_vectors.T@errors@drug_vectors/denominator for errors in (error_B, error_A)]
        cache[key] = cell_vectors, transformed
    cell_vectors, transformed = cache[key]
    drug_values, drug_vectors = drug_eigen
    target = reference["similarity"][cell, history]@cell_vectors
    correction_B, correction_A = [(target@values*drug_values)@drug_vectors.T for values in transformed]
    return base+correction_B, base+offset+correction_A


def model_bank(arrays, history, reference, kernels, eigens, mask, cache):
    fitted = {}
    old = fit_moments(arrays, history, reference, kernels, eigens, mask, None, False, cache)
    for representation in REPRESENTATIONS:
        fitted[representation] = dict(old=old, refit=fit_moments(arrays, history, reference, kernels,
                                                               eigens, mask, representation, True, cache))
    return fitted


def configurations(selected):
    result = dict(no_update=dict(mean_representation=None, residual_kind="old", representation=None, eta=0., alpha=0.),
                  knowledge_mean=dict(mean_representation="knowledge", residual_kind="refit", representation=None, eta=0., alpha=0.))
    for arm, bank, representation in (("knowledge_old", "old", None),
                                      ("knowledge_refit_empirical", "refit", None),
                                      ("knowledge_refit_map", "refit", "knowledge")):
        result[arm] = dict(mean_representation="knowledge", residual_kind=bank, representation=representation, **selected[arm])
    result["knowledge_strong_shrink"] = dict(mean_representation="knowledge", residual_kind="refit", representation=None, eta=0., alpha=.01)
    for representation in ("molecule", "Morgan", "permutedknowledge"):
        result[representation+"_refit_map"] = dict(mean_representation=representation, residual_kind="refit",
                                                 representation=representation, **selected[representation+"_refit_map"])
    result["knowledge_prebuy_stop"] = dict(result["knowledge_refit_map"])
    return result


def descriptor(arrays, history, cell, reference, eigens, models, pairs, query, configuration, cache):
    representation = configuration["mean_representation"]
    if representation:
        mean_B, mean_A = conditional_means(arrays, history, cell, reference, eigens[representation], cache)
    else:
        mean_B = independent.prior(arrays, history, cell)
        mean_A = mean_B+independent.shift(arrays, history)
    matrices = models[representation or "knowledge"][configuration["residual_kind"]]["matrices"]
    covariance = matrices["empirical"]
    if configuration["representation"]:
        covariance = (1-configuration["eta"])*covariance+configuration["eta"]*matrices[configuration["representation"]]
    left, right = pairs.T
    cross, variance = covariance[:146, 146+query], float(covariance[146+query, 146+query])
    pair_variance = np.diag(covariance)[left]+np.diag(covariance)[right]-2*covariance[left, right]
    return dict(mean_before=mean_B, predicted_A=float(mean_A[query]), gain=cross/variance,
        variance_A=variance, pair_variance=np.maximum(pair_variance, 1e-12),
        pair_reduction=(cross[left]-cross[right])**2/variance,
        support=support(reference, history, cell), configuration=configuration)


def forecast(desc, observed, pairs):
    alpha = desc["configuration"]["alpha"]
    innovation, z, clip = 0., None, 1.
    if alpha > 0:
        assert observed is not None and np.isfinite(observed)
        innovation = float(observed-desc["predicted_A"])
        z = innovation/np.sqrt(desc["variance_A"])
        clip = min(1., 3/abs(z)) if z else 1.
    effective = alpha*desc["support"]["weight"]*clip
    mean = desc["mean_before"]+effective*desc["gain"]*innovation
    left, right = pairs.T
    return dict(mean=mean, pair_delta=mean[left]-mean[right],
                pair_variances=np.maximum(desc["pair_variance"]-effective*desc["pair_reduction"], 1e-12),
                alpha_effective=effective, innovation=innovation, innovation_z=z, outlier_factor=clip)


def choose(arrays, history, reference, kernels, eigens, mask, cache):
    inner, folds = [], []
    for fold in range(3):
        keep_positions = [position for position in range(len(history)) if position%3 != fold]
        held_positions = [position for position in range(len(history)) if position%3 == fold]
        keep = [history[position] for position in keep_positions]
        models = model_bank(arrays, keep, reference, kernels, eigens, mask, cache)
        folds.append(dict(keep_positions=keep_positions, held_positions=held_positions))
        for position in held_positions:
            cell = history[position]
            prior = independent.prior(arrays, keep, cell)
            pairs, query = independent.frozen_comparisons(prior)
            inner.append(dict(history=keep, cell=cell, models=models, pairs=pairs, query=query,
                              observed=float(arrays["train_A"][cell, query]), outcome=arrays["train_B"][cell]))
    selected, tuning = {}, {}
    for arm, representation, bank, covariance_representation in (
            ("knowledge_old", "knowledge", "old", None),
            ("knowledge_refit_empirical", "knowledge", "refit", None),
            ("knowledge_refit_map", "knowledge", "refit", "knowledge"),
            *((r+"_refit_map", r, "refit", r) for r in ("molecule", "Morgan", "permutedknowledge"))):
        trials = []
        for eta in ETAS if covariance_representation else (0.,):
            for alpha in ALPHAS:
                configuration = dict(mean_representation=representation, residual_kind=bank,
                                     representation=covariance_representation, eta=eta, alpha=alpha)
                losses = []
                for row in inner:
                    desc = descriptor(arrays, row["history"], row["cell"], reference, eigens, row["models"],
                                      row["pairs"], row["query"], configuration, cache)
                    pred = forecast(desc, row["observed"] if alpha>0 else None, row["pairs"])
                    outcome = row["outcome"]
                    losses.append(float(outcome[independent.top(outcome)].sum()-outcome[independent.top(pred["mean"])].sum()))
                trials.append(dict(alpha=alpha, eta=eta, top5_regret=float(np.mean(losses))))
        best = min(trials, key=lambda row:(row["top5_regret"], row["alpha"], row["eta"]))
        selected[arm] = dict(alpha=best["alpha"], eta=best["eta"])
        tuning[arm] = trials
    configs, scales = configurations(selected), {}
    for arm, configuration in configs.items():
        errors = []
        for row in inner:
            desc = descriptor(arrays, row["history"], row["cell"], reference, eigens, row["models"],
                              row["pairs"], row["query"], configuration, cache)
            pred = forecast(desc, row["observed"] if configuration["alpha"] > 0 else None, row["pairs"])
            left, right = row["pairs"].T
            truth = row["outcome"][left]-row["outcome"][right]
            errors.extend(((pred["pair_delta"]-truth)/np.sqrt(pred["pair_variances"])).tolist())
        scales[arm] = max(1., float(np.sqrt(np.mean(np.square(errors)))))
    return dict(configurations=configs, probability_scales=scales, tuning=tuning, inner_folds=folds)


def relative_flips(mean, before, outcome, pairs):
    left, right = pairs.T
    old_delta, delta, truth = before[left]-before[right], mean[left]-mean[right], outcome[left]-outcome[right]
    old = (old_delta > 0) | ((old_delta == 0) & (left < right))
    new = (delta > 0) | ((delta == 0) & (left < right))
    changed = old != new
    defined = np.abs(truth) > 1e-12
    correct = new == (truth > 0)
    return dict(total=int(changed.sum()), corrected=int((changed & defined & correct).sum()),
                harmful=int((changed & defined & ~correct).sum()), ambiguous=int((changed & ~defined).sum()),
                coverage=float(changed.mean()))


def comparison(results, arm, control):
    lookup = {(row["episode"], row["arm"]):row for row in results}
    delta = []
    for context in sorted({row["context"] for row in results}):
        group = [row for row in results if row["context"] == context and row["arm"] == arm]
        assert len(group) == 3
        delta.append(float(np.mean([row["terminal_B"]-lookup[(row["episode"], control)]["terminal_B"] for row in group])))
    n, mean = len(delta), float(np.mean(delta))
    variance = np.std(delta, ddof=1) if n>1 else 0.
    radius = t.ppf(.975, n-1)*variance/np.sqrt(n) if n>1 else None
    pvalue = float(t.sf(mean/(variance/np.sqrt(n)), n-1)) if n>1 and variance>0 else (0. if n>1 and mean>0 else 1.)
    return dict(mean=mean, context_95CI=[float(mean-radius), float(mean+radius)] if radius is not None else None,
                one_sided_p=pvalue, context_units=n)


def summary_arithmetic(results):
    groups, comparisons = {}, {}
    for size in SIZES:
        rows = [row for row in results if row["history_size"] == size]
        arms = {}
        for arm in (*ARMS, "knowledge_prebuy_stop"):
            group = [row for row in rows if row["arm"] == arm]
            arm_summary = {field:float(np.mean([row[field] for row in group])) for field in
                ("terminal_B", "top5_regret", "pair_regret", "RNA_MSE", "flip_coverage", "gaussian_interval_95_coverage")}
            defined_brier = [row["brier"] for row in group if row["brier"] is not None]
            feedback_flips = sum(row["feedback_relative_mean"]["total"] for row in group)
            feedback_harm = sum(row["feedback_relative_mean"]["harmful"] for row in group)
            arm_summary.update(brier=float(np.mean(defined_brier)) if defined_brier else None,
                brier_defined_episodes=len(defined_brier), episodes=len(group),
                corrected_flips=sum(row["corrected_flips"] for row in group),
                harmful_flips=sum(row["harmful_flips"] for row in group),
                feedback_corrected_flips=sum(row["feedback_relative_mean"]["corrected"] for row in group),
                feedback_harmful_flips=feedback_harm, feedback_flips=feedback_flips,
                feedback_harm_fraction=feedback_harm/feedback_flips if feedback_flips else None,
                feedback_coverage=float(np.mean([row["feedback_relative_mean"]["coverage"] for row in group])),
                effective_updates=sum(row["alpha_effective"] > 0 for row in group),
                A_purchases=sum(bool(row["purchased_A"]) for row in group), total_cost=sum(row["cost"] for row in group),
                eta_positive_effective=sum(row["alpha_effective"] > 0 and row["configuration"]["eta"] > 0 for row in group))
            arms[arm] = arm_summary
        groups[str(size)] = arms
        comparisons[str(size)] = {control:comparison(rows, "knowledge_refit_map", control)
                                 for control in (*ARMS, "knowledge_prebuy_stop") if control != "knowledge_refit_map"}
    primary = comparisons["8"]
    transfer = {name:dict(primary[name]) for name in ("knowledge_mean", "no_update", "knowledge_old")}
    attribution = {name:dict(primary[name]) for name in ("knowledge_refit_empirical", "knowledge_strong_shrink",
                  "molecule_refit_map", "Morgan_refit_map", "permutedknowledge_refit_map")}
    for group in (transfer, attribution):
        adjusted = independent.holm_adjust({name:record["one_sided_p"] for name, record in group.items()})
        for name, value in adjusted.items():
            group[name]["holm_p"] = value
    policy, baseline, mean_only = (groups["8"][name] for name in ("knowledge_refit_map", "no_update", "knowledge_mean"))
    gates = dict(positive_top5_transfer=all(row["mean"] > 0 and row["holm_p"] <= .05 for row in transfer.values()),
                 meaningful_pair_regret=baseline["pair_regret"]-policy["pair_regret"] >= .001,
                 feedback_harm=policy["feedback_harm_fraction"] is not None and policy["feedback_harm_fraction"] <= .1,
                 feedback_coverage=policy["feedback_coverage"] >= .05,
                 brier_noninferiority=policy["brier"] is not None and mean_only["brier"] is not None
                 and policy["brier"] <= mean_only["brier"]+.01)
    transfer_pass = all(gates.values())
    knowledge_pass = transfer_pass and all(row["mean"] > 0 and row["holm_p"] <= .05 for row in attribution.values())
    knowledge_pass = knowledge_pass and policy["eta_positive_effective"] > 0
    return dict(history_sizes=groups, top5_context_comparisons=comparisons,
                primary_transfer_comparisons=transfer, primary_attribution_comparisons=attribution,
                transfer_gate_components=gates, transfer_gate=transfer_pass,
                knowledge_specific_gate=knowledge_pass, P2_broad_acquisition_release=transfer_pass)


def fit_moments(arrays, history, reference, kernels, eigens, mask, representation, refitted, cache):
    residuals = []
    for cell in history:
        keep = [other for other in history if other != cell]
        if refitted:
            mean_B, mean_A = conditional_means(arrays, keep, cell, reference, eigens[representation], cache)
        else:
            mean_B = independent.prior(arrays, keep, cell)
            mean_A = mean_B+independent.shift(arrays, keep)
        residuals.append(np.r_[arrays["train_B"][cell]-mean_B, arrays["train_A"][cell]-mean_A])
    residuals = np.asarray(residuals)
    matrices, rho = independent.joint_covariances(residuals, kernels)
    for matrix in matrices.values():
        matrix *= np.kron(np.ones((2, 2)), mask)
    return dict(residuals=residuals, matrices=matrices, rho=rho)


def predict(arrays, history, cell, reference, eigens, model, query, observed_A, configuration, cache):
    mean_representation = configuration.get("mean_representation")
    if mean_representation:
        mean_B, mean_A = conditional_means(arrays, history, cell, reference, eigens[mean_representation], cache)
    else:
        mean_B = independent.prior(arrays, history, cell)
        mean_A = mean_B+independent.shift(arrays, history)
    residual_kind = configuration.get("residual_kind", "refit")
    representation = configuration.get("representation")
    eta = configuration.get("eta", 0.)
    alpha = float(configuration.get("alpha", 0.))
    gated = configuration.get("gated", True)
    matrices = model[residual_kind]["matrices"]
    covariance = matrices["empirical"]
    if representation:
        covariance = (1-eta)*covariance+eta*matrices[representation]
    cross = covariance[:146, 146+query]
    variance = float(covariance[146+query, 146+query])
    diagnostics = support(reference, history, cell)
    actual_alpha, innovation, innovation_z, outlier = alpha, 0., None, 1.
    if alpha > 0:
        assert observed_A is not None and np.isfinite(observed_A)
        innovation = float(observed_A-mean_A[query])
        innovation_z = innovation/np.sqrt(variance) if variance > 0 else None
        if gated:
            outlier = min(1., 3/abs(innovation_z)) if innovation_z else 1.
            actual_alpha *= diagnostics["weight"]*outlier
    if variance <= 0:
        actual_alpha = 0.
    increment = actual_alpha*cross/variance*innovation if actual_alpha else np.zeros(146)
    posterior = covariance[:146, :146].copy()
    if actual_alpha:
        posterior -= actual_alpha*np.outer(cross, cross)/variance
    return dict(mean=mean_B+increment, mean_B_before=mean_B, mean_A=mean_A,
                covariance=(posterior+posterior.T)/2, alpha_effective=actual_alpha,
                innovation=innovation, innovation_z=innovation_z, outlier_factor=outlier,
                predicted_A=float(mean_A[query]), variance_A=variance, feedback_increment=increment,
                support=diagnostics, residual_kind=residual_kind)


def verify(out):
    started = time.perf_counter()
    for name in ("FREEZE.json", "VERIFY_FREEZE.json"):
        for filename, expected in independent.read(HERE/name)["inputs"].items():
            assert independent.sha(ROOT/filename) == expected, filename
    for name in ("PRE_A_FREEZE.json", "COMMITMENT_FREEZE.json"):
        frozen = independent.read(out/name)
        assert frozen["source_freeze_sha256"] == independent.sha(HERE/"FREEZE.json")
        for filename, expected in frozen["inputs"].items():
            assert independent.sha(out/filename) == expected, filename
    arrays = dict(np.load(PACKET/"training_arrays.npz"))
    manifest = independent.read(PACKET/"PACKET_MANIFEST.json")
    records = independent.read(independent.AUDIT)["records"]
    features = dict(np.load(independent.RELEASE/"FEATURES.npz"))
    identities = independent.read(independent.RELEASE/"IDENTITIES.json")["records"]
    assert [(record["cid"], record["smiles"]) for record in records] == [(record["cid"], record["smiles"]) for record in identities]
    kernels = independent.candidate_kernels(records, features, manifest["labels"])
    mask = independent.condition_mask(records, manifest["labels"])
    eigens = {}
    for representation, kernel in kernels.items():
        values, vectors = np.linalg.eigh(kernel)
        assert values.min() >= -1e-8
        eigens[representation] = (np.maximum(values, 0.), vectors)
    ref = coordinates(arrays)
    reference = dict(np.load(HERE/"PUBLIC_REFERENCE.npz"))
    independent.equal(ref["centre"], reference["centre"])
    independent.equal(ref["scale"], reference["scale"])
    independent.equal(ref["bandwidth"], reference["bandwidth_sq"])
    independent.equal(ref["standardized"], reference["reference_standardized"])
    assert reference["public_context_count"] == 45
    complete = np.flatnonzero((arrays["availability_A"] & arrays["availability_B"] & arrays["state_available_B"]).all(1)).tolist()
    assert len(complete) == 43
    choices = independent.read(out/"CHOICES.json")
    plans = independent.read(out/"PLANS.json")
    diagnostics = independent.read(out/"TRAINING_DIAGNOSTICS.json")
    prepared = dict(np.load(out/"PRE_A_ARRAYS.npz"))
    requests = independent.read(out/"POLICY_REQUESTS.json")
    receipts = independent.read(out/"A_RECEIPTS.json")
    commitments = independent.read(out/"COMMITMENTS.json")
    predictions = dict(np.load(out/"PREDICTIONS.npz"))
    results = independent.read(out/"RESULTS.json")
    summary = independent.read(out/"SUMMARY.json")
    contexts = sorted({plan["context"] for plan in plans})
    assert contexts == complete or contexts == complete[:1]
    episodes = len(contexts)*9
    assert len(plans) == len(choices) == len(receipts) == episodes
    assert len(requests) == len(commitments) == len(results) == len(predictions) == episodes*10
    plan_lookup = {plan["episode"]:plan for plan in plans}
    request_lookup = {(row["episode"], row["arm"]):row for row in requests}
    receipt_lookup = {row["episode"]:row for row in receipts}
    commitment_lookup = {(row["episode"], row["arm"]):row for row in commitments}
    result_lookup = {(row["episode"], row["arm"]):row for row in results}
    expected_results, policy_charges, stopped = [], 0, 0
    for cell in contexts:
        for seed in SEEDS:
            order = np.random.default_rng(np.random.SeedSequence([seed, cell])).permutation(sorted(set(complete)-{cell}))
            previous = set()
            for size in SIZES:
                key = f"ref{cell}__seed{seed}__n{size}"
                history = sorted(order[:size].tolist())
                assert cell not in history and previous < set(history)
                previous = set(history)
                cache = {}
                chosen = choose(arrays, history, ref, kernels, eigens, mask, cache)
                independent.equal_tree(chosen, {name:choices[key][name] for name in chosen}, key+"/choice")
                models = model_bank(arrays, history, ref, kernels, eigens, mask, cache)
                baseline = independent.prior(arrays, history, cell)
                pairs, query = independent.frozen_comparisons(baseline)
                plan = dict(episode=key, context=cell, seed=seed, history_size=size, history_ids=history,
                            pairs=pairs.tolist(), query_A=query, initial_selected=independent.top(baseline))
                independent.equal_tree(plan, plan_lookup[key], key+"/plan")
                for representation in REPRESENTATIONS:
                    old, refit = models[representation]["old"], models[representation]["refit"]
                    old_B, old_A = old["residuals"][:, :146], old["residuals"][:, 146:]
                    error_B, error_A = refit["residuals"][:, :146], refit["residuals"][:, 146:]
                    loo_mean_B = arrays["train_B"][history]-error_B
                    loo_mean_A = arrays["train_A"][history]-error_A
                    for name, values in (("loo_mean_A", loo_mean_A), ("loo_mean_B", loo_mean_B),
                                         ("error_A", error_A), ("error_B", error_B)):
                        independent.equal(values, prepared[key+"__"+representation+"__"+name])
                    expected_diagnostics = dict(old_A_MSE=float(np.mean(old_A**2)), old_B_MSE=float(np.mean(old_B**2)),
                        refit_A_MSE=float(np.mean(error_A**2)), refit_B_MSE=float(np.mean(error_B**2)),
                        old_rho=old["rho"], refit_rho=refit["rho"])
                    independent.equal_tree(expected_diagnostics, diagnostics[key][representation], key+"/diagnostic")
                value = float(arrays["train_A"][cell, query])
                independent.equal_tree(dict(episode=key, context=cell, query_A=query, observed_A=value, measurement_units=1),
                                       receipt_lookup[key], key+"/receipt")
                for arm, configuration in chosen["configurations"].items():
                    desc = descriptor(arrays, history, cell, ref, eigens, models, pairs, query, configuration, cache)
                    for name in ("mean_before", "gain", "pair_variance", "pair_reduction"):
                        independent.equal(desc[name], prepared[key+"__"+arm+"__"+name])
                    recorded_desc = {name:value for name, value in desc.items()
                                     if name not in ("mean_before", "gain", "pair_variance", "pair_reduction")}
                    independent.equal_tree(recorded_desc, choices[key]["descriptors"][arm], key+"/desc")
                    buy = arm not in ("no_update", "knowledge_mean") and (arm != "knowledge_prebuy_stop" or configuration["alpha"] > 0)
                    independent.equal_tree(dict(episode=key, arm=arm, query_A=query, A_units=int(buy),
                        status="charged_before_release" if buy else "stopped_before_release"), request_lookup[(key, arm)], key+"/request")
                    policy_charges += int(buy)
                    stopped += int(arm == "knowledge_prebuy_stop" and not buy)
                    pred = forecast(desc, value if buy else None, pairs)
                    scale = chosen["probability_scales"][arm]
                    probability = norm.cdf(pred["pair_delta"]/(np.sqrt(pred["pair_variances"])*scale))
                    decisions = [int(i if delta>0 or (delta==0 and i<j) else j) for (i, j), delta in zip(pairs, pred["pair_delta"])]
                    row = dict(plan, arm=arm, configuration=configuration, prediction_key=key+"__"+arm,
                        selected=independent.top(pred["mean"]), mean_only_selected=independent.top(desc["mean_before"]),
                        cost=5+int(buy), purchased_A=[query] if buy else [], A_released=buy,
                        pair_decisions=decisions, pair_delta=pred["pair_delta"].tolist(), pair_variances=pred["pair_variances"].tolist(),
                        pair_probabilities=probability.tolist(), probability_scale=scale, predicted_A=desc["predicted_A"],
                        variance_A=desc["variance_A"], support=desc["support"],
                        **{name:pred[name] for name in ("alpha_effective", "innovation", "innovation_z", "outlier_factor")})
                    independent.equal_tree(row, commitment_lookup[(key, arm)], key+"/commit")
                    independent.equal(pred["mean"], predictions[row["prediction_key"]])
                    outcome = arrays["train_B"][cell]
                    scored = dict(row, **independent.scored_metrics(row, pred["mean"], outcome),
                        near_equivalence_sensitivity=independent.scored_metrics(row, pred["mean"], outcome, tolerance=.001),
                        feedback_relative_mean=relative_flips(pred["mean"], desc["mean_before"], outcome, pairs))
                    independent.equal_tree(scored, result_lookup[(key, arm)], key+"/result")
                    expected_results.append(scored)
        print(f"Verified true dual-source LOO means, moments, tuning and all paid commitments: ref{cell}", flush=True)
    expected_summary = summary_arithmetic(expected_results)
    for name, expected in expected_summary.items():
        independent.equal_tree(expected, summary[name], "summary/"+name)
    payload = dict(status="PASS", episodes=episodes, result_rows=episodes*10, backgrounds=len(contexts), arms=10,
        common_source_A_receipts=episodes, counterfactual_A_policy_charges=policy_charges,
        prebuy_stopped_episodes=stopped, frozen_pairs=episodes*9, inference_units_per_history_size=len(contexts),
        checks=["Producer and independent source freezes; pre-A/pre-B saved hashes",
                "Label-free transductive45-state reference and continuous support/distance",
                "All nested scarce histories and inner folds; independent fixed conditional A/B means",
                "TrueLOO joint residuals excluding own labels and nested adapter bank own labels",
                "Old/refit moments and exact dose Schur kernels; no duplicate observation noise",
                "All Top5-regret alpha/eta choices and training-side probability scales",
                "All frozen queries/pairs, pre-A arrays, charged or stopped requests, one-A receipts and predictions",
                "Every commitment, pair/terminal/swap/calibration metric and mean-relative harmful flip",
                "43-context seedmean contrasts; separate transfer/knowledge Holm gates and P2release"],
        seconds=time.perf_counter()-started,
        claim_boundary="Independent arithmetic on exposed transductive cached RNA research; not new biological cultures, functional benefit, conditional-risk certification, financial NetVOI or LLM advantage.")
    with (out/"VERIFIED.json").open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(payload, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT/"outputs/decision_value/pairwise_v3")
    args = parser.parse_args()
    verify(args.out)


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
