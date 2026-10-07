"""Independent reconstruction of the registered exposed-development RNA decisions.

Reads only the 45 training reference contexts and two exposed development contexts.
Does not import the study's world-model, belief-update or selection functions.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STUDY = ROOT / "research/astra/decision_opportunity_20261007"
CACHE = ROOT / "data/external/tahoe_zeroshot_20261007"
RUN = STUDY / "development_run1"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def jsonlines(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]


def check_equal(left, right, name, tolerance=1e-11):
    left, right = np.asarray(left), np.asarray(right)
    if left.shape != right.shape or not np.allclose(left, right, atol=tolerance, rtol=tolerance):
        raise AssertionError(name)
    return float(np.max(np.abs(left.astype(float) - right.astype(float)))) if left.size else 0.


def raw_observations(file, keys):
    with np.load(CACHE / "observations" / (file + ".npz")) as archive:
        obs = dict(archive)
    rows = {key: row for row, key in enumerate(zip(obs["label"].tolist(), obs["plate"].tolist()))}
    controls = {plate: row for row, plate in enumerate(obs["ctrl_plate"].tolist())}
    delta = np.zeros((len(keys), 2000), np.float32)
    noise = np.full(len(keys), np.nan)
    counts = np.zeros(len(keys), int)
    for i, key in enumerate(keys):
        if key not in rows:
            continue
        j, c = rows[key], controls[key[1]]
        counts[i] = obs["n"][j]
        if counts[i] >= 8:
            delta[i] = obs["mean"][j].astype(float) - obs["ctrl_mean"][c]
            noise[i] = np.nanmean(obs["var"][j]) / counts[i] + np.mean(obs["ctrl_var"][c]) / obs["ctrl_n"][c]
    basal = np.average(obs["basal_mean"], axis=0, weights=obs["basal_n"])
    return delta, noise, basal, counts, obs, rows, controls


def raw_states(file, keys):
    with np.load(CACHE / "state_forecasts" / (file + ".npz")) as archive:
        state = dict(archive)
    rows = {key: row for row, key in enumerate(zip(state["label"].tolist(), state["plate"].tolist()))}
    vectors = np.zeros((len(keys), 2000), np.float16)
    available = np.zeros(len(keys), bool)
    for i, key in enumerate(keys):
        if key in rows:
            vectors[i] = state["paired_delta"][rows[key]]
            available[i] = True
    return vectors, available, state, rows


def topfive(mean):
    return [int(i) for i in sorted(range(len(mean)), key=lambda i: (-mean[i], i))[:5]]


def independent_policy(prior, cov, variance, offset, yA, policy):
    mean, covariance = prior.copy(), cov.copy()
    remaining = set(range(len(mean)))
    screens, trace = [], []
    normal = np.random.default_rng(42).standard_normal(64)
    prior_order = sorted(remaining, key=lambda i: (-prior[i], i))
    if policy != "none":
        for _ in range(8):
            estimated = None
            if policy == "fixed_top_prior":
                chosen = next(i for i in prior_order if i in remaining)
            else:
                current = sum(sorted(mean)[-5:])
                scores = {}
                for i in sorted(remaining):
                    scale = np.sqrt(covariance[i, i] + variance[i])
                    alternatives = mean[None] + normal[:, None] * covariance[:, i][None] / scale
                    values = np.sort(alternatives, axis=1)[:, -5:].sum(axis=1)
                    scores[i] = float(values.mean() - current)
                chosen = max(scores, key=lambda i: (scores[i], -i))
                estimated = scores[chosen]
                if estimated <= 0:
                    break
            trace.append((chosen, mean.copy(), estimated))
            column = covariance[:, chosen].copy()
            gain = column / (covariance[chosen, chosen] + variance[chosen])
            mean += gain * (yA[chosen] - offset[chosen] - mean[chosen])
            covariance -= np.outer(gain, column)
            remaining.remove(chosen)
            screens.append(chosen)
    return screens, topfive(mean), trace


def main():
    protocol = read_json(STUDY / "PROTOCOL.json")
    frozen = read_json(STUDY / "PROTOCOL_FREEZE.json")
    assert sha(STUDY / "PROTOCOL.json") == frozen["protocol_sha256"]
    assert frozen["protocol_sha256"] == "594597d9a5df8b399b043cb61e6149f56a94c22212a7410cdd1cc4710e24d739"
    for path, identity in protocol["source_dependencies"].items():
        assert sha(ROOT / path) == identity
    receipt = read_json(STUDY / "sources/GENESET_SOURCE_RECEIPT.json")
    assert receipt["retrieved_utc"] < frozen["created_utc"]
    assert sha(STUDY / "sources/genesets.enrichr_msigdb_hallmark_2020.gmt") == receipt["source_sha256"]
    labels = protocol["menu"]["labels"]
    assert len(labels) == len(set(labels)) == 146
    keys = sorted({(label, plate) for label in labels for plate in protocol["menu"]["wells"][label]})
    index = {key: i for i, key in enumerate(keys)}
    ia = np.array([index[(label, protocol["menu"]["wells"][label][0])] for label in labels])
    ib = np.array([index[(label, protocol["menu"]["wells"][label][1])] for label in labels])
    assert np.all(ia != ib)
    excluded = {"c26.h5ad", "c31.h5ad", "c27.h5ad", "c12.h5ad", "c20.h5ad"}
    files = [f"c{i}.h5ad" for i in range(50) if f"c{i}.h5ad" not in excluded]
    delta, noise, basal, state, state_available = [], [], [], [], []
    for file in files:
        d, n, b, *_ = raw_observations(file, keys)
        s, ok, *_ = raw_states(file, keys)
        delta.append(d); noise.append(n); basal.append(b); state.append(s); state_available.append(ok)
    delta, noise, basal = np.array(delta), np.array(noise), np.array(basal)
    state, state_available = np.array(state), np.array(state_available)
    available = np.isfinite(noise)
    precision = np.where(available, 1 / np.maximum(np.where(available, noise, 0), 1e-12), 0.)
    precision /= precision.sum(axis=0)
    m0 = np.einsum("lk,lkd->kd", precision, delta, optimize=True)
    state_mean = (state.astype(np.float32) * state_available[..., None]).sum(0) / state_available.sum(0)[:, None]
    with np.load(RUN / "analysis_arrays.npz") as archive:
        arrays = dict(archive)
    errors = {"train_delta": check_equal(delta, arrays["train_delta"], "training source vectors"),
              "availability": check_equal(available, arrays["train_availability"], "training availability"),
              "panel_mean": check_equal(m0, arrays["panel_mean"], "training empirical panel", 1e-10)}
    names = read_json(ROOT / "data/virtual_cell/tahoe_c39_x_hvg_feature_names.json")["names"]
    term = next(line for line in (STUDY / "sources/genesets.enrichr_msigdb_hallmark_2020.gmt").read_text().splitlines() if line.split("\t")[0] == "Apoptosis")
    members = set(term.split("\t")[2:])
    mapped = [{"coordinate": i, "gene": gene} for i, gene in enumerate(names) if gene in members]
    assert mapped == protocol["primary"]["mapped"] and len(mapped) == 39
    primary = np.zeros(2000); primary[[r["coordinate"] for r in mapped]] = 1 / 39
    permuted = np.zeros(2000)
    permuted[np.random.default_rng(42).choice([i for i, n in enumerate(names) if n is not None], 39, replace=False)] = 1 / 39
    reference = m0[index[(protocol["secondary"]["reference_label"], protocol["secondary"]["reference_plate"])]]
    phenocopy = reference / np.linalg.norm(reference) / np.sqrt(2000)
    weights = {"curated_transcript_projection": primary, "native_reference_phenocopy": phenocopy,
               "permuted_transcript_membership": permuted}
    for name, weight in (("curated", primary), ("phenocopy", phenocopy), ("permuted", permuted)):
        errors[name + "_weights"] = check_equal(weight, arrays[name + "_weights"], name + " weights")
    parameters = {}
    both = available[:, ia] & available[:, ib]
    for endpoint, weight in weights.items():
        projected = delta.astype(float) @ weight
        a, b = projected[:, ia], projected[:, ib]
        centre = np.sum(np.where(both, b, 0), axis=0) / both.sum(axis=0)
        imputed = np.where(both, b, centre)
        centred = imputed - imputed.mean(axis=0)
        covariance = centred.T @ centred / (len(files) - 1)
        covariance = .5 * covariance + .5 * np.diag(np.diag(covariance)) + np.eye(146) * 1e-12
        differences = np.where(both, a - b, np.nan)
        offset = np.nanmean(differences, axis=0)
        variance = np.maximum(np.nanvar(differences, axis=0, ddof=1), 1e-12)
        for name, value in (("cov", covariance), ("obsvar", variance), ("offset", offset)):
            errors[endpoint + "_" + name] = check_equal(value, arrays[endpoint + "_" + name], endpoint + name)
        parameters[endpoint] = covariance, variance, offset
    episodes = {row["case_id"]: row for row in jsonlines(RUN / "EPISODES.jsonl")}
    policy_events, purchase_events = defaultdict(list), defaultdict(list)
    for row in jsonlines(RUN / "policy.jsonl"):
        policy_events[row["case_id"]].append(row)
    for row in jsonlines(RUN / "purchases.jsonl"):
        purchase_events[row["case_id"]].append(row)
    reconstructed, fingerprints = [], {}
    for context, file in protocol["contexts"].items():
        assert context in ("PANC-1", "HepG2/C3A")
        _, _, target_basal, _, obs, rowindex, ctrlindex = raw_observations(file, keys)
        obs_delta = np.array([obs["mean"][rowindex[key]].astype(float) - obs["ctrl_mean"][ctrlindex[key[1]]] for key in keys])
        _, _, s, si = raw_states(file, keys)
        deviation = np.array([s["paired_delta"][si[key]].astype(float) for key in keys]) - state_mean
        xbar = precision.T @ basal
        xc = basal[:, None, :] - xbar[None]
        ss = np.einsum("lk,lkj->kj", precision, xc ** 2)
        coefficients = precision[..., None] * xc * ((target_basal[None] - xbar) / np.maximum(ss, 1e-12))[None]
        gate = np.einsum("lkj,lkj->kj", coefficients, delta.astype(float))
        import ast
        strata = defaultdict(list)
        for i, (label, plate) in enumerate(keys):
            strata[(float(ast.literal_eval(label)[0][1]), plate)].append(i)
        rng = np.random.default_rng(42); permutation = np.arange(len(keys))
        for indices in strata.values():
            permutation[indices] = rng.permutation(indices)
        forecasts = {"M0": m0, "M1": m0 + .5 * gate, "M2": m0 + .5 * deviation,
                     "M21": m0 + .5 * gate + .5 * deviation, "M2_state_permuted": m0 + .5 * deviation[permutation]}
        token = context.replace("/", "_").replace("-", "_")
        fingerprints[file] = {"observation_sha256": sha(CACHE / "observations" / (file + ".npz")),
                              "state_sha256": sha(CACHE / "state_forecasts" / (file + ".npz"))}
        errors[token + "_observed_A"] = check_equal(obs_delta[ia], arrays[token + "_observed_A"], "observed A")
        errors[token + "_observed_B"] = check_equal(obs_delta[ib], arrays[token + "_observed_B"], "observed B")
        for model, forecast in forecasts.items():
            errors[token + "_" + model] = check_equal(forecast, arrays[token + "_" + model], model + " vector", 1e-10)
        for endpoint, weight in weights.items():
            yA, yB = obs_delta[ia] @ weight, obs_delta[ib] @ weight
            covariance, variance, offset = parameters[endpoint]
            for model, forecast in forecasts.items():
                prior = forecast[ib] @ weight
                for policy in protocol["policies"]:
                    case_id = f"{token}.{endpoint}.{model}.{policy}"
                    row = episodes[case_id]
                    screens, final, trace = independent_policy(prior, covariance, variance, offset, yA, policy)
                    assert screens == row["screened"] and final == row["final_flags"]
                    assert topfive(prior) == row["initial_flags"]
                    utility = float(yB[final].sum())
                    check_equal(utility, row["utility"], "independent confirmation utility")
                    assert row["actual_credits"] == len(screens) + 5 <= 13
                    events = purchase_events[case_id]
                    commits = [j for j, event in enumerate(events) if event["event"] == "flags_committed"]
                    assert len(commits) == 1 and events[commits[0]]["candidates"] == final
                    paid = [event for event in events if event["event"] == "paid_reveal"]
                    assert len(paid) == len(screens) + 5
                    assert [event["candidate"] for event in paid if event["role"] == "A"] == screens
                    assert [event["candidate"] for event in paid if event["role"] == "B"] == final
                    assert all(event["role"] == "A" for event in events[:commits[0]] if event["event"] == "paid_reveal")
                    assert all(not event["retry_created"] for event in paid)
                    assert [event["recorded_credits"] for event in paid] == list(range(1, len(paid) + 1))
                    for j, (choice, mean, gain) in enumerate(trace):
                        policy_row = policy_events[case_id][j]
                        assert policy_row["choice"] == choice
                        check_equal(mean, policy_row["mean_before"], "paid-only posterior", 1e-9)
                    reconstructed.append({"case_id": case_id, "utility": utility, "actual_credits": len(paid)})
    assert len(reconstructed) == len(episodes) == 90
    connection = sqlite3.connect(RUN / "cases.sqlite")
    tables = {row[0] for row in connection.execute("select name from sqlite_master where type='table'")}
    connection.close()
    result = {"verdict": "PASS", "registered_protocol_sha256": frozen["protocol_sha256"],
              "reconstructed_episodes": len(reconstructed), "credits": sum(row["actual_credits"] for row in reconstructed),
              "menu_candidates": 146, "training_contexts": 45, "exposed_development_contexts": 2,
              "gene_members": len(members), "verified_mapped_coordinates": len(mapped),
              "source_before_registration": True, "independent_B_after_flag_commit": True,
              "paid_A_only_selection_reproduced": True, "numerical_errors": errors,
              "source_files": fingerprints, "case_store_tables": sorted(tables),
              "limitations": ["Two already exposed development cells; no independent biological confirmation.",
                              "RNA member projection is not apoptosis, ATP, protein activity or mechanism evidence.",
                              "Across-context A-B dispersion includes batch/biology; mean-imputed covariance is an empirical heuristic.",
                              "Training STATE predictions are in-sample; no independent calibration claim."]}
    target = HERE / "DIRECTION_VERIFICATION.json"
    with target.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False); handle.write("\n")
    print(json.dumps({key: value for key, value in result.items() if key not in ("numerical_errors", "source_files")}, indent=2))


if __name__ == "__main__":
    main()
