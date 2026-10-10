"""Freeze training choices, charge one A reveal, commit, then evaluate isolated B."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from scipy.stats import norm, t, ttest_1samp
from threadpoolctl import threadpool_limits

if __package__:
    from . import model
else:
    import model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKET = ROOT / "research/astra/boundary_acquisition_20261007/packet2"
RELEASE = ROOT / "outputs/paper_01286/released_test"
AUDIT = ROOT / "outputs/knowledge_layer_validation_20261009/AUDIT.json"
DEFAULT_OUT = ROOT / "outputs/decision_value/pairwise_20261009_v2"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_freeze(path, base=ROOT):
    frozen = read(path)
    for name, expected in frozen["inputs"].items():
        if sha(base / name) != expected:
            raise ValueError("freeze_mismatch:" + name)
    return frozen


def freeze_outputs(out, name, files):
    write(out / name, dict(inputs={file: sha(out / file) for file in files},
                           source_freeze_sha256=sha(HERE / "FREEZE.json")))


def public_kernels():
    records = read(AUDIT)["records"]
    identities = read(RELEASE / "IDENTITIES.json")["records"]
    if [(r["cid"], r["smiles"]) for r in records] != [(r["cid"], r["smiles"]) for r in identities]:
        raise ValueError("authenticated_cache_identity_mismatch")
    with np.load(RELEASE / "FEATURES.npz") as features:
        return model.prepare_kernels(records, dict(features))


def prepare(out):
    if out.exists():
        raise RuntimeError("refuse_to_overwrite_pairwise_study")
    out.mkdir(parents=True)
    started = time.perf_counter()
    kernels, eigens, mask, metadata = public_kernels()
    with np.load(PACKET / "training_arrays.npz") as archive:
        arrays = dict(archive)
    complete = np.flatnonzero((arrays["availability_A"] & arrays["availability_B"] &
                              arrays["state_available_B"]).all(1)).tolist()
    factors, choices, plans = {}, {}, []
    for held in complete:
        for seed in model.SEEDS:
            for size, training in model.histories(complete, held, seed).items():
                key = f"ref{held}__seed{seed}__n{size}"
                history, target = model.training_view(arrays, training), model.public_view(arrays, held)
                chosen = model.choose(history, kernels, eigens, mask)
                fitted = model.fit(history, kernels, mask)
                base = model.prior(history, target)
                pairs, query, initial = model.pairs_and_query(base)
                for name in ("error_B", "error_A", "offset", "basal_centre", "normalized_basal",
                             "cell_values", "cell_vectors"):
                    factors[key + "__" + name] = fitted[name]
                factors[key + "__prior"] = base
                factors[key + "__target_basal"] = target["basal"]
                choices[key] = dict(context=held, seed=seed, history_size=size, history_ids=training,
                                    rho=fitted["rho"], **chosen)
                plans.append(dict(episode=key, context=held, seed=seed, history_size=size,
                                  pairs=pairs, query_A=query, initial_selected=initial,
                                  prediction_key=key + "__prior"))
        print(f"Prepared ref{held}: nine scarce histories; no target A/B inspected", flush=True)
    np.savez_compressed(out / "FACTORS.npz", **factors)
    write(out / "MODEL_CHOICES.json", choices)
    write(out / "PRE_A_PLANS.json", plans)
    write(out / "KERNEL_METADATA.json", metadata)
    write(out / "PREPARE_TIMING.json", dict(seconds=time.perf_counter() - started))
    freeze_outputs(out, "PRE_A_FREEZE.json",
                   ["FACTORS.npz", "MODEL_CHOICES.json", "PRE_A_PLANS.json", "KERNEL_METADATA.json"])


def restore(factors, key, kernels, mask):
    fitted = {name: factors[key + "__" + name] for name in
              ("error_B", "error_A", "offset", "basal_centre", "normalized_basal", "cell_values", "cell_vectors")}
    fitted["matrices"], fitted["rho"] = model.kernel.covariances(fitted["error_B"], fitted["error_A"], kernels)
    for name in fitted["matrices"]:
        fitted["matrices"][name] *= np.tile(mask, (2, 2))
    return fitted


def reveal(request, buy):
    if request["status"] != "charged_before_release" or request["measurement_units"] != 1:
        raise ValueError("A_release_requires_prior_charge")
    value = float(buy(request["query_A"]))
    if not np.isfinite(value):
        raise ValueError("paid_A_returned_nonfinite_value")
    return value


def commit(out):
    validate_freeze(out / "PRE_A_FREEZE.json", out)
    if (out / "PURCHASE_REQUESTS.json").exists():
        raise RuntimeError("refuse_to_repeat_paid_A_phase")
    started = time.perf_counter()
    kernels, eigens, mask, _ = public_kernels()
    choices, plans = read(out / "MODEL_CHOICES.json"), read(out / "PRE_A_PLANS.json")
    with np.load(out / "FACTORS.npz") as archive:
        factors = dict(archive)
    # Every request and charged unit is persisted before target A is released.
    requests = [dict(episode=p["episode"], context=p["context"], query_A=p["query_A"],
                     measurement_units=1, status="charged_before_release") for p in plans]
    write(out / "PURCHASE_REQUESTS.json", requests)
    with np.load(PACKET / "training_arrays.npz") as archive:
        measured_A = archive["train_A"]
    predictions, commitments, receipts = {}, [], []
    for plan, request in zip(plans, requests):
        key, query = plan["episode"], plan["query_A"]
        value = reveal(request, lambda index: measured_A[plan["context"], index])
        receipts.append(dict(episode=key, context=plan["context"], query_A=query,
                             observed_A=value, measurement_units=1))
        fitted = restore(factors, key, kernels, mask)
        base = factors[key + "__prior"]
        target = dict(basal=factors[key + "__target_basal"])
        choice = choices[key]
        for arm, configuration in choice["configurations"].items():
            feedback = arm not in ("no_update", *(r + "_only" for r in model.REPRESENTATIONS))
            predicted = model.predict(fitted, target, base, query, value if feedback else None, eigens, **configuration)
            row = model.commit(predicted, base, plan["pairs"], plan["initial_selected"],
                               choice["probability_scales"][arm], selective=arm == "selective_knowledge")
            prediction_key = key + "__" + arm
            predictions[prediction_key] = np.array(row.pop("mean"))
            commitments.append(dict(plan, arm=arm, selected_simple=choice["selected_simple"],
                configuration=configuration, prediction_key=prediction_key, cost=6 if feedback else 5,
                purchased_A=[query] if feedback else [], **row))
    np.savez_compressed(out / "PREDICTIONS.npz", **predictions)
    write(out / "A_RECEIPTS.json", receipts)
    write(out / "COMMITMENTS.json", commitments)
    write(out / "COMMIT_TIMING.json", dict(seconds=time.perf_counter() - started))
    freeze_outputs(out, "COMMITMENT_FREEZE.json",
        ["PRE_A_FREEZE.json", "PURCHASE_REQUESTS.json", "A_RECEIPTS.json", "PREDICTIONS.npz", "COMMITMENTS.json"])


def score(row, mean, outcomes, epsilon=1e-12):
    pair = np.array(row["pairs"])
    difference = outcomes[pair[:, 0]] - outcomes[pair[:, 1]]
    decisions = row["pair_decisions"]
    chosen_first = np.array([decision is None or decision == i for (i, _), decision in zip(pair, decisions)])
    defined = abs(difference) > epsilon
    flipped = ~chosen_first
    corrected = flipped & (difference < -epsilon)
    harmful = flipped & (difference > epsilon)
    ambiguous = flipped & ~defined
    probabilities = np.array(row["pair_probabilities"])
    regret = np.where(chosen_first, np.maximum(-difference, 0.), np.maximum(difference, 0.))
    labels = difference > 0
    initial, selected = row["initial_selected"], row["selected"]
    bins = []
    for low in np.arange(0., 1., .2):
        valid = defined & (probabilities >= low) & ((probabilities < low + .2) if low < .8 else (probabilities <= 1.))
        bins.append(dict(count=int(valid.sum()), sum_probability=float(probabilities[valid].sum()),
                         sum_positive=int(labels[valid].sum())))
    incoming, outgoing = sorted(set(selected) - set(initial)), sorted(set(initial) - set(selected))
    replacements = [dict(incoming=i, outgoing=j, B_delta=float(outcomes[i] - outcomes[j])) for i, j in
        zip(sorted(incoming, key=lambda i: (-mean[i], i)), sorted(outgoing, key=lambda i: (mean[i], i)))]
    coverage = abs(np.array(row["pair_delta"]) - difference) <= norm.ppf(.975) * np.sqrt(row["pair_variances"]) * row["probability_scale"]
    return dict(pair_regret=float(regret.mean()), corrected_flips=int(corrected.sum()),
                harmful_flips=int(harmful.sum()), ambiguous_flips=int(ambiguous.sum()), flips=int(flipped.sum()), defined_pairs=int(defined.sum()),
                flip_coverage=float(flipped.mean()),
                selective_coverage=sum(decision is not None for decision in decisions) / len(decisions),
                brier=float(np.mean((probabilities[defined] - labels[defined]) ** 2)) if defined.any() else None,
                true_pair_delta=difference.tolist(), calibration_bins=bins,
                gaussian_interval_95_coverage=float(coverage.mean()),
                swapped_in=incoming, swapped_out=outgoing, replacement_pairs=replacements,
                harmful_replacements=sum(pair["B_delta"] < -epsilon for pair in replacements),
                terminal_B=float(outcomes[selected].sum()), initial_B=float(outcomes[initial].sum()),
                terminal_delta=float(outcomes[selected].sum() - outcomes[initial].sum()),
                top5_regret=float(np.sort(outcomes)[-5:].sum() - outcomes[selected].sum()),
                RNA_MSE=float(np.mean((mean - outcomes) ** 2)))


def interval(values):
    values = np.asarray(values)
    delta = float(values.mean())
    radius = float(t.ppf(.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values)))
    return [delta - radius, delta + radius]


def summarize(results):
    summaries, comparisons = {}, {}
    for size in model.SIZES:
        rows = [r for r in results if r["history_size"] == size]
        contexts = sorted({r["context"] for r in rows})
        summaries[str(size)] = {}
        for arm in model.ARMS:
            group = [r for r in rows if r["arm"] == arm]
            summaries[str(size)][arm] = {name: float(np.mean([r[name] for r in group])) for name in
                ("pair_regret", "terminal_B", "top5_regret", "RNA_MSE", "flip_coverage", "selective_coverage", "gaussian_interval_95_coverage")}
            defined_brier = [r["brier"] for r in group if r["brier"] is not None]
            summaries[str(size)][arm].update(brier=float(np.mean(defined_brier)) if defined_brier else None,
                                             brier_defined_episodes=len(defined_brier))
            flips = sum(r["flips"] for r in group)
            summaries[str(size)][arm].update(contexts=len(contexts), seed_episodes=len(group),
                corrected_flips=sum(r["corrected_flips"] for r in group), harmful_flips=sum(r["harmful_flips"] for r in group),
                ambiguous_flips=sum(r["ambiguous_flips"] for r in group), harmful_replacements=sum(r["harmful_replacements"] for r in group),
                flips=flips, harmful_flip_fraction=sum(r["harmful_flips"] for r in group) / flips if flips else None,
                total_cost=sum(r["cost"] for r in group))
        lookup = {(r["episode"], r["arm"]): r for r in rows}
        knowledge = [r for r in rows if r["arm"] == "knowledge_feedback"]
        controls = ("no_update", "selected_simple", "Morgan_feedback", "permutedknowledge_feedback", "matched_strength_empirical")
        comparisons[str(size)] = {}
        for control in controls:
            differences, brier_differences = [], []
            for context in contexts:
                group = [r for r in knowledge if r["context"] == context]
                pairs = [(r, lookup[(r["episode"], r["selected_simple"] if control == "selected_simple" else control)]) for r in group]
                differences.append(float(np.mean([b["pair_regret"] - r["pair_regret"] for r, b in pairs])))
                defined = [r["brier"] - b["brier"] for r, b in pairs
                           if r["brier"] is not None and b["brier"] is not None]
                if defined:
                    brier_differences.append(float(np.mean(defined)))
            if np.max(np.abs(differences)) == 0:
                probability = 1.
            else:
                probability = float(ttest_1samp(differences, 0., alternative="greater").pvalue)
            comparisons[str(size)][control] = dict(regret_improvement=float(np.mean(differences)),
                context_95CI=interval(differences), one_sided_p=probability,
                brier_delta=float(np.mean(brier_differences)) if brier_differences else None,
                brier_delta_context_95CI=interval(brier_differences) if len(brier_differences) >= 2 else None,
                brier_context_unit_count=len(brier_differences),
                context_unit_count=len(contexts))
        # The factorial is a descriptive predictor interaction, not causal knowledge attribution.
        interaction = [lookup[(r["episode"], "knowledge_feedback")]["terminal_B"]
            - lookup[(r["episode"], "knowledge_only")]["terminal_B"]
            - lookup[(r["episode"], "gated_cv_shrink")]["terminal_B"]
            + lookup[(r["episode"], "no_update")]["terminal_B"] for r in knowledge]
        summaries[str(size)]["factorial_terminal_interaction"] = float(np.mean(interaction))
        interaction = [-lookup[(r["episode"], "knowledge_feedback")]["pair_regret"]
            + lookup[(r["episode"], "knowledge_only")]["pair_regret"]
            + lookup[(r["episode"], "gated_cv_shrink")]["pair_regret"]
            - lookup[(r["episode"], "no_update")]["pair_regret"] for r in knowledge]
        summaries[str(size)]["factorial_pair_utility_interaction"] = float(np.mean(interaction))
    primary = comparisons["8"]
    sorted_controls = sorted(primary, key=lambda name: primary[name]["one_sided_p"])
    running = 0.
    for rank, name in enumerate(sorted_controls):
        running = max(running, min(1., (len(sorted_controls) - rank) * primary[name]["one_sided_p"]))
        primary[name]["holm_adjusted_p"] = running
    arm = summaries["8"]["knowledge_feedback"]
    gates = dict(positive_regret=all(r["regret_improvement"] > 0 and r["holm_adjusted_p"] <= .05 for r in primary.values())
                 and primary["no_update"]["regret_improvement"] >= .001,
                 harmful_flip_fraction=arm["harmful_flip_fraction"] is not None and arm["harmful_flip_fraction"] <= .10,
                 nontrivial_flip_coverage=arm["flip_coverage"] >= .05,
                 brier_noninferiority=primary["selected_simple"]["brier_delta"] is not None
                 and primary["selected_simple"]["brier_delta"] <= .01)
    return dict(history_sizes=summaries, paired_seed_mean_context_comparisons=comparisons,
                primary_history_size=8, gate_components=gates, registered_development_gate=all(gates.values()),
                inference_unit="Three seeds averaged within each of 43 held contexts; exposed development only.",
                claim_boundary="Signed39geneRNA only. Fixed STATE pretraining, shared one-A feedback, no independent-risk or functional certificate, no monetary NetVOI, no production promotion.")


def evaluate(out):
    validate_freeze(out / "COMMITMENT_FREEZE.json", out)
    if (out / "RESULTS.json").exists():
        raise RuntimeError("refuse_to_overwrite_pairwise_evaluation")
    started = time.perf_counter()
    commitments = read(out / "COMMITMENTS.json")
    with np.load(out / "PREDICTIONS.npz") as archive:
        predictions = dict(archive)
    # Only this phase accesses each evaluation context's B outcomes.
    with np.load(PACKET / "training_arrays.npz") as archive:
        measured_B = archive["train_B"]
    results = []
    for row in commitments:
        mean, outcomes = predictions[row["prediction_key"]], measured_B[row["context"]]
        results.append(dict(**row, **score(row, mean, outcomes),
                            near_equivalence_sensitivity=score(row, mean, outcomes, epsilon=.001)))
    write(out / "RESULTS.json", results)
    write(out / "SUMMARY.json", summarize(results))
    write(out / "EVALUATE_TIMING.json", dict(seconds=time.perf_counter() - started))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--phase", choices=("prepare", "commit", "evaluate", "all"), default="all")
    args = parser.parse_args()
    validate_freeze(HERE / "FREEZE.json")
    phases = ("prepare", "commit", "evaluate") if args.phase == "all" else (args.phase,)
    for phase in phases:
        globals()[phase](args.out)


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
