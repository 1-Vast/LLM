"""Independently reconstruct source features, fitting, stopping and paid decisions."""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from independent_math import condition, crossing_scores, dataset, fit_ridge, nearest_distance, predict, reference_features, topfive

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STUDY = HERE.parent / "boundary_acquisition_20261007"
CACHE = ROOT / "data/external/tahoe_zeroshot_20261007"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def lines(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]


def equal(a, b, label, tolerance=1e-10):
    a, b = np.asarray(a), np.asarray(b)
    assert a.shape == b.shape and np.allclose(a, b, atol=tolerance, rtol=tolerance, equal_nan=True), label


def raw(file, keys):
    obs = dict(np.load(CACHE / "observations" / (file + ".npz")))
    oi = {key: i for i, key in enumerate(zip(obs["label"].tolist(), obs["plate"].tolist()))}
    ci = {plate: i for i, plate in enumerate(obs["ctrl_plate"].tolist())}
    delta = np.zeros((len(keys), 2000), np.float32)
    variance = np.full(len(keys), np.nan)
    counts = np.zeros(len(keys), int)
    for i, key in enumerate(keys):
        if key not in oi:
            continue
        j, c = oi[key], ci[key[1]]
        counts[i] = obs["n"][j]
        if counts[i] >= 8:
            delta[i] = obs["mean"][j].astype(float) - obs["ctrl_mean"][c]
            variance[i] = np.nanmean(obs["var"][j]) / counts[i] + np.mean(obs["ctrl_var"][c]) / obs["ctrl_n"][c]
    basal = np.average(obs["basal_mean"], axis=0, weights=obs["basal_n"])
    state = dict(np.load(CACHE / "state_forecasts" / (file + ".npz")))
    si = {key: i for i, key in enumerate(zip(state["label"].tolist(), state["plate"].tolist()))}
    native = np.zeros((len(keys), 2000), np.float16)
    available = np.array([key in si for key in keys])
    for i, key in enumerate(keys):
        if key in si:
            native[i] = state["paired_delta"][si[key]]
    exact = np.array([state["paired_delta"][si[key]].astype(float) if key in si else np.zeros(2000) for key in keys])
    return delta, variance, counts, basal, native, available, exact, obs, oi, ci


def covariance_parameters(a, included):
    available = (a["availability_A"] & a["availability_B"])[included]
    x = a["train_B"][included]
    centre = np.sum(np.where(available, x, 0), axis=0) / available.sum(axis=0)
    filled = np.where(available, x, centre)
    centred = filled - filled.mean(axis=0)
    c = centred.T @ centred / (len(filled) - 1)
    c = .5 * c + .5 * np.diag(np.diag(c)) + np.eye(c.shape[0]) * 1e-12
    diff = np.where(available, a["train_A"][included] - x, np.nan)
    return c, np.maximum(np.nanvar(diff, axis=0, ddof=1), 1e-12), np.nanmean(diff, axis=0)


def kg(mean, covariance, variance, available, draws):
    current = float(sum(sorted(mean)[-5:]))
    result = {}
    for i in sorted(available):
        direction = covariance[:, i] / np.sqrt(covariance[i, i] + variance[i])
        alternative = mean[None] + draws[:, None] * direction[None]
        utility = np.sort(alternative, axis=1)[:, -5:].sum(axis=1)
        result[i] = float(utility.mean() - current)
    return result


def main(packet, run, output):
    p, freeze = read(STUDY / "PROTOCOL.json"), read(STUDY / "FREEZE.json")
    assert sha(STUDY / "PROTOCOL.json") == freeze["protocol_sha256"]
    for collection in ("source_dependencies", "upstream_dependencies"):
        for path, identity in p[collection].items():
            assert sha(ROOT / path) == identity, path
    final_review = read(HERE / "FINAL_DRAFT_REVIEW.json")
    assert final_review["created_utc"] < freeze["created_utc"]
    reviewed_source_differences = {name: {"reviewed": identity, "frozen": sha(STUDY / name)}
                                 for name, identity in final_review["source_hashes"].items()
                                 if sha(STUDY / name) != identity}
    manifest = read(packet / "PACKET_MANIFEST.json")
    assert manifest["protocol_sha256"] == freeze["protocol_sha256"]
    for name, identity in manifest["hashes"].items():
        assert sha(packet / name) == identity
    a, public, private = (dict(np.load(packet / name)) for name in ("training_arrays.npz", "public_prior.npz", "evaluator_private.npz"))
    labels, wells = p["menu"]["labels"], p["menu"]["wells"]
    assert len(labels) == len(set(labels)) == 146 and len(p["arms"]) == 12
    keys = sorted({(label, plate) for label in labels for plate in wells[label]})
    ki = {key: i for i, key in enumerate(keys)}
    ia = np.array([ki[(label, wells[label][0])] for label in labels])
    ib = np.array([ki[(label, wells[label][1])] for label in labels])
    assert np.all(ia != ib)
    weight = np.zeros(2000); weight[[row["coordinate"] for row in p["endpoint"]["mapped"]]] = 1 / 39
    names = read(ROOT / "data/virtual_cell/tahoe_c39_x_hvg_feature_names.json")["names"]
    for row in p["endpoint"]["mapped"]:
        assert names[row["coordinate"]] == row["gene"]
    strata = defaultdict(list)
    for i, (label, plate) in enumerate(keys):
        strata[(float(ast.literal_eval(label)[0][1]), plate)].append(i)
    permutation = np.arange(len(keys)); rng = np.random.default_rng(42)
    for indices in strata.values():
        permutation[indices] = rng.permutation(indices)
    excluded = {"c26.h5ad", "c31.h5ad", "c27.h5ad", "c12.h5ad", "c20.h5ad"}
    training_files = [f"c{i}.h5ad" for i in range(50) if f"c{i}.h5ad" not in excluded]
    delta, noise, basal, states, state_ok = [], [], [], [], []
    for file in training_files:
        d, v, _, b, s, ok, *_ = raw(file, keys)
        delta.append(d); noise.append(v); basal.append(b); states.append(s); state_ok.append(ok)
    delta, noise, basal, states, state_ok = np.array(delta), np.array(noise), np.array(basal), np.array(states), np.array(state_ok)
    available = np.isfinite(noise)
    precision = np.where(available, 1 / np.maximum(np.where(available, noise, 0), 1e-12), 0)
    scalar = delta.astype(float) @ weight
    scalar_state = states.astype(float) @ weight
    reconstructed = {"train_A": scalar[:, ia], "train_B": scalar[:, ib], "availability_A": available[:, ia],
                     "availability_B": available[:, ib], "precision_B": precision[:, ib], "basal": basal,
                     "state_B": scalar_state[:, ib], "state_B_permuted": scalar_state[:, permutation][:, ib],
                     "state_available_B": state_ok[:, ib], "state_available_B_permuted": state_ok[:, permutation][:, ib]}
    for key, value in reconstructed.items():
        equal(value, a[key], "original training source " + key)
    plates = sorted(set(wells[label][1] for label in labels))
    equal(a["dose"], [float(ast.literal_eval(label)[0][1]) for label in labels], "dose identity")
    equal(a["plate_design"], [[float(wells[label][1] == plate) for plate in plates] for label in labels], "plate design")
    model_values, fit_parameters = dict(np.load(packet / "fitted_models.npz")), read(packet / "FIT_PARAMETERS.json")
    models = {}
    for name, permuted, design in (("residual", False, False), ("design", False, True), ("permuted", True, False)):
        x, error, groups = dataset(a, np.ones(45, bool), permuted)
        model = fit_ridge(x, error, design); models[name] = model
        for key in ("centre", "scale", "coef"):
            equal(model[key], model_values[name + "__" + key], "QR ridge " + name + key, 1e-9)
        for key in ("intercept", "predicted_centre", "floor"):
            equal(model[key], fit_parameters[name][key], "ridge scalar " + name + key)
    diagnostic = dict(np.load(packet / "nested_reference_diagnostic.npz"))
    predicted, true, constant = [], [], []
    for held in range(45):
        included = np.ones(45, bool); included[held] = False
        x, error, _ = dataset(a, included)
        model = fit_ridge(x, error)
        held_features, held_error, selected, _ = reference_features(a, held)
        predicted.extend(predict(model, held_features[selected]))
        true.extend(np.log(held_error[selected] + model["floor"]))
        constant.extend([model["intercept"]] * int(selected.sum()))
    for name, value in (("predicted", predicted), ("true", true), ("constant", constant)):
        equal(value, diagnostic[name], "genuine nested reference " + name, 1e-8)
    cov, variance, offset = covariance_parameters(a, np.ones(45, bool))
    for name, value in (("cov", cov), ("obsvar", variance), ("offset", offset)):
        equal(value, public[name], "shared belief " + name)
    thresholds = []
    for held in range(45):
        included = np.ones(45, bool); included[held] = False
        _, _, _, prior = reference_features(a, held)
        c, v, _ = covariance_parameters(a, included)
        values, _ = crossing_scores(prior, c, v, range(146))
        thresholds.append(max(values.values()))
    training_summary = read(packet / "TRAINING_DIAGNOSTIC.json")
    equal(thresholds, training_summary["threshold_m0_loo_scores"], "training-only threshold scores")
    tau = .1 * float(np.median(thresholds)); equal(tau, public["tau"], "shared M0 stopping convention")
    print(json.dumps({"stage": "training/source/QR/nested/tau verified", "nested_rows": len(true), "tau": tau}), flush=True)
    normalized = precision / precision.sum(axis=0)
    m0 = np.einsum("lk,lkd->kd", normalized, delta, optimize=True)
    state_mean = (states.astype(np.float32) * state_ok[..., None]).sum(axis=0) / state_ok.sum(axis=0)[:, None]
    policy_rows, purchase_rows = defaultdict(list), defaultdict(list)
    for row in lines(run / "policy.jsonl"):
        policy_rows[row["case_id"]].append(row)
    for row in lines(run / "purchases.jsonl"):
        purchase_rows[row["case_id"]].append(row)
    episodes = {row["case_id"]: row for row in lines(run / "EPISODES.jsonl")}
    eigenvalues, reconstruction = {}, []
    for context, file in p["contexts"].items():
        token = context.replace("/", "_").replace("-", "_")
        _, _, counts, b, _, ok, exact_state, obs, oi, ci = raw(file, keys)
        assert np.all(ok)
        exact_delta = np.array([obs["mean"][oi[key]].astype(float) - obs["ctrl_mean"][ci[key[1]]] for key in keys])
        dev = exact_state - state_mean
        predictions = {"M0": m0[ib] @ weight, "M2": (m0 + .5 * dev)[ib] @ weight,
                       "M2_permuted": (m0 + .5 * dev[permutation])[ib] @ weight}
        for model, value in predictions.items():
            equal(value, public[token + "__" + model], "target STATE/empirical source " + model)
        for role, indices in (("A", ia), ("B", ib)):
            equal(exact_delta[indices] @ weight, private[token + "__" + role], "target source projection " + role)
            equal(counts[indices], private[token + "__counts_" + role], "source well counts")
        reference_variance = np.nanvar(np.where(a["availability_B"], a["train_B"], np.nan), axis=0, ddof=1)
        reference_coverage, state_coverage = a["availability_B"].mean(axis=0), a["state_available_B"].mean(axis=0)
        distance = nearest_distance(b, a["basal"])
        features = {}
        for name, correction in (("features", .5 * dev[ib] @ weight), ("features_permuted", .5 * dev[permutation][ib] @ weight)):
            features[name] = np.column_stack((np.log(np.abs(correction) + 1e-12), np.repeat(distance, 146),
                                             np.log10(a["dose"]), a["plate_design"], reference_coverage,
                                             state_coverage, np.log(np.maximum(reference_variance, 1e-12)),
                                             reference_coverage < 1., state_coverage < 1.))
            equal(features[name], public[token + "__" + name], "target lawful features")
        ratios = {}
        for name, model in models.items():
            feature = features["features_permuted" if name == "permuted" else "features"]
            ratio = np.exp(np.clip(.5 * (predict(model, feature) - model["predicted_centre"]), np.log(.5), np.log(2.)))
            ratios[name] = ratio
            equal(ratio, public[token + "__ratio_" + name], "target candidate variance scaling", 1e-9)
        yA, yB = private[token + "__A"], private[token + "__B"]
        for arm in p["arms"]:
            case = token + "." + arm["name"]
            saved = episodes[case]
            prior = predictions[arm["model"]]
            c = cov.copy()
            if arm["uncertainty"] != "common":
                scale_name = "permuted" if arm["model"] == "M2_permuted" else ("design" if arm["uncertainty"] == "design_missingness" else "residual")
                d = np.sqrt(ratios[scale_name]); c *= d[:, None] * d[None]
            mineigen = float(np.linalg.eigvalsh(c).min()); assert mineigen > -1e-12
            eigenvalues[case] = mineigen
            selected, prefix = [], [topfive(prior)]
            original_order = sorted(range(146), key=lambda i: (-prior[i], i))
            draws = np.random.default_rng(42).standard_normal(arm.get("normal_draws", 64))
            logs = policy_rows[case]; logged_screens = [row for row in logs if row["event"] == "paid_screen"]
            stopping = None
            for step in range(arm["max_A"]):
                mean, posterior = condition(prior, c, variance, offset, selected, yA)
                available_queries = sorted(set(range(146)) - set(selected))
                score, pair = None, None
                if arm["acquisition"] == "fixed":
                    choice = next(i for i in original_order if i not in selected)
                elif arm["acquisition"] == "KG":
                    values = kg(mean, posterior, variance, available_queries, draws)
                    choice = max(values, key=lambda i: (values[i], -i)); score = values[choice]
                    if score <= 0:
                        stopping = "nonpositive_KG_surrogate"; break
                else:
                    values, details = crossing_scores(mean, posterior, variance, available_queries)
                    choice = max(values, key=lambda i: (values[i], -i)); score, pair = values[choice], details[choice]
                    if arm["stopping"] and score <= tau:
                        stop = next(row for row in logs if row["event"] == "stop")
                        assert stop["next_candidate"] == choice
                        equal(score, stop["boundary_score"], "registered boundary stop score")
                        stopping = "boundary_surrogate_below_training_tau"; break
                logged = logged_screens[step]
                assert logged["candidate"] == choice
                assert logged["current_flags"] == topfive(mean)
                equal(logged["predicted_A"], mean[choice] + offset[choice], "paid-only pre-screen prediction")
                equal(logged["purchased_A"], yA[choice], "paid A observation")
                if score is not None:
                    equal(score, logged["boundary_or_KG_score"], "query objective", 1e-9)
                if pair is not None:
                    for name, value in pair.items():
                        equal(value, logged["active_comparison"][name], "consequential pair " + name, 1e-9)
                selected.append(choice)
                mean, _ = condition(prior, c, variance, offset, selected, yA)
                prefix.append(topfive(mean))
            if stopping is None:
                stopping = "fixed_screen_count" if arm["acquisition"] == "fixed" else "max_A_profiles"
            final = prefix[-1]
            assert selected == saved["screened"] and final == saved["final_flags"] and prefix == saved["prefix_flags"]
            assert stopping == saved["stopreason"]
            equal(yB[final], saved["final_B_values"], "committed independent B values")
            equal(yB[final].sum(), saved["utility"], "final independent B utility")
            assert saved["actual_credits"] == len(selected) + 5 <= 13
            assert saved["common_cap"] == 13 and saved["unused_cap"] == 13 - len(selected) - 5
            events = purchase_rows[case]
            commits = [i for i, event in enumerate(events) if event["event"] == "flags_committed"]
            assert len(commits) == 1 and events[commits[0]]["candidates"] == final
            assert all(event["role"] == "A" for event in events[:commits[0]] if event["event"] == "paid_reveal")
            paid = [event for event in events if event["event"] == "paid_reveal"]
            assert [event["candidate"] for event in paid if event["role"] == "A"] == selected
            assert [event["candidate"] for event in paid if event["role"] == "B"] == final
            assert len(paid) == saved["actual_credits"] and all(not event["retry_created"] for event in paid)
            assert [event["recorded_credits"] for event in paid] == list(range(1, len(paid) + 1))
            reconstruction.append({"case_id": case, "utility": float(yB[final].sum()), "profiles": len(paid),
                                   "screens": selected, "stopreason": stopping})
        print(json.dumps({"stage": "target verified", "context": context, "episodes": len(p["arms"])}), flush=True)
    assert len(reconstruction) == len(episodes) == 60
    with (run / "PREFIX_FRONTIER.csv").open(encoding="utf-8", newline="") as handle:
        frontier = list(csv.DictReader(handle))
    for point in frontier:
        token = point["context"].replace("/", "_").replace("-", "_")
        saved = episodes[token + "." + point["arm"]]
        k = int(point["A"]); flags = saved["prefix_flags"][k]
        assert flags == json.loads(point["flags"]) and int(point["credits"]) == k + 5
        equal(private[token + "__B"][flags].sum(), float(point["utility"]), "full prefix frontier")
    summary = read(run / "SUMMARY.json")
    assert sum(row["profiles"] for row in reconstruction) == summary["profiles"]
    receipt = {
        "verdict": "PASS", "protocol_sha256": freeze["protocol_sha256"],
        "source_and_upstream_hashes_verified": len(p["source_dependencies"]) + len(p["upstream_dependencies"]),
        "pre_freeze_reviewed_source_differences": reviewed_source_differences,
        "episodes": len(reconstruction), "profiles": sum(row["profiles"] for row in reconstruction),
        "full_menu": 146, "common_cap": 13, "B_confirmations": 5, "maximum_A": 8,
        "training_source_reconstructed": True, "independent_QR_ridge_and_nested_context_fits": True,
        "nested_diagnostic_rows": len(true), "shared_M0_loo_tau": tau,
        "independent_batch_conditioning_and_analytical_pair_scores": True,
        "highprecision4096_KG_choices_reproduced": True, "B_before_flag_commit": False,
        "duplicate_retries_add_cost": False, "prefix_points": len(frontier),
        "covariance_min_eigenvalues": eigenvalues, "episode_reconstruction": reconstruction,
        "limits": ["Allfivecontexts previously exposed; results descriptive not untouched confirmation.",
                   "STATE trainingreference residuals in-sample despite nested empirical/ridge cross-fitting.",
                   "Stop score/tau model-implied heuristic, not calibrated biological risk or multistepVOI bound.",
                   "Singlecandidate error ordering is not validated rankingdifference calibration."]}
    with output.open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2, allow_nan=False); handle.write("\n")
    print(json.dumps({key: value for key, value in receipt.items() if key not in ("episode_reconstruction", "covariance_min_eigenvalues")}, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True); parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(); main(args.packet, args.run, args.out)
