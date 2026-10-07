"""Independent compact-packet, latent-trust and all-budget-prefix checks.

Uses closed-form conditioning on all purchased observations, rather than the
successor's sequential update implementation. No study modules are imported.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from verify_direction import HERE, ROOT, RUN, STUDY, check_equal, jsonlines, read_json, sha, topfive


def conditional(mean0, covariance0, H, chosen, observed, baseA, noise):
    if not chosen:
        return mean0.copy(), covariance0.copy()
    design = H[chosen]
    cross = covariance0 @ design.T
    marginal = design @ cross + np.diag(noise[chosen])
    innovation = observed[chosen] - baseA[chosen] - design @ mean0
    mean = mean0 + cross @ np.linalg.solve(marginal, innovation)
    covariance = covariance0 - cross @ np.linalg.solve(marginal, cross.T)
    return mean, covariance


def main():
    packet = STUDY / "compact_packet2"
    manifest = read_json(packet / "PACKET_MANIFEST.json")
    for name, identity in manifest["hashes"].items():
        assert sha(packet / name) == identity
    for path, identity in manifest["source_hashes"].items():
        assert sha(ROOT / path) == identity
    assert manifest["sizes"] == {name: (packet / name).stat().st_size for name in manifest["sizes"]}
    public = dict(np.load(packet / "public_prior.npz"))
    private = dict(np.load(packet / "evaluator_private.npz"))
    arrays = dict(np.load(RUN / "analysis_arrays.npz"))
    p = read_json(STUDY / "PROTOCOL.json")
    keys = [tuple(row) for row in arrays["keys"].tolist()]
    ki = {key: i for i, key in enumerate(keys)}
    roles = {role: [ki[(label, p["menu"]["wells"][label][j])] for label in manifest["labels"]]
             for j, role in enumerate(("A", "B"))}
    weights = {"curated_transcript_projection": "curated_weights", "native_reference_phenocopy": "phenocopy_weights",
               "permuted_transcript_membership": "permuted_weights"}
    for endpoint, weight_key in weights.items():
        for suffix in ("cov", "obsvar", "offset"):
            check_equal(public[endpoint + "__" + suffix], arrays[endpoint + "_" + suffix], "packet belief parameters")
        for role, indices in roles.items():
            check_equal(public[endpoint + "__train_" + role], arrays["train_delta"][:, indices].astype(float) @ arrays[weight_key], "packet training projection")
        for context in manifest["contexts"]:
            token = context.replace("/", "_").replace("-", "_")
            for role, indices in roles.items():
                check_equal(private[token + "__" + endpoint + "__" + role], arrays[token + "_" + endpoint + "_y" + role], "packet private source")
                for model in ("M0", "M1", "M2", "M21", "M2_state_permuted"):
                    check_equal(public[token + "__" + endpoint + "__" + model + "__" + role], arrays[token + "_" + model][indices] @ arrays[weight_key], "packet prior projection")
    original = {row["case_id"]: row for row in jsonlines(RUN / "EPISODES.jsonl")}
    replay = read_json(STUDY / "packet_replay2/REPLAY.json")
    assert len(replay["episodes"]) == 90
    for row in replay["episodes"]:
        source = original[row["case_id"]]
        for key in ("screened", "final_flags", "actual_credits"):
            assert source[key] == row[key]
        check_equal(source["utility"], row["utility"], "packet replay utility")
    successor = read_json(STUDY / "SUCCESSOR_PROTOCOL.json")
    freeze = read_json(STUDY / "SUCCESSOR_FREEZE.json")
    assert sha(STUDY / "SUCCESSOR_PROTOCOL.json") == freeze["protocol_sha256"]
    assert sha(packet / "PACKET_MANIFEST.json") == successor["packet_manifest_sha256"]
    successor_rows = jsonlines(STUDY / "trust_run1/EPISODES.jsonl")
    policy, purchases = defaultdict(list), defaultdict(list)
    for row in jsonlines(STUDY / "trust_run1/policy.jsonl"):
        policy[row["case_id"]].append(row)
    for row in jsonlines(STUDY / "trust_run1/purchases.jsonl"):
        purchases[row["case_id"]].append(row)
    gamma = {}
    normals = np.random.default_rng(42).standard_normal(64)
    endpoint = "curated_transcript_projection"
    for row in successor_rows:
        context, arm, case = row["context"], row["arm"], row["case_id"]
        assert context in ("PANC-1", "HepG2/C3A")
        token = context.replace("/", "_").replace("-", "_")
        forecast = {model: {role: public[token + "__" + endpoint + "__" + model + "__" + role]
                            for role in ("A", "B")} for model in ("M0", "M1", "M2", "M2_state_permuted")}
        base = forecast["M0" if arm == "M0_KG" else "M1"]
        if arm == "M0_KG":
            correction = {role: np.zeros(146) for role in ("A", "B")}
        else:
            state_model = "M2_state_permuted" if "permuted" in arm else "M2"
            correction = {role: 2 * (forecast[state_model][role] - forecast["M0"][role]) for role in ("A", "B")}
        G, H = np.column_stack((correction["B"], np.eye(146))), np.column_stack((correction["A"], np.eye(146)))
        mean0 = np.zeros(147); mean0[0] = .5
        covariance0 = np.zeros((147, 147)); covariance0[1:, 1:] = public[endpoint + "__cov"]
        covariance0[0, 0] = .25 if arm.startswith("adaptive_gamma") else 0.
        noise = public[endpoint + "__obsvar"]
        yA, yB = (private[token + "__" + endpoint + "__" + role] for role in ("A", "B"))
        prior = base["B"] + G @ mean0
        assert topfive(prior) == row["initial_flags"]
        order = sorted(range(146), key=lambda i: (-prior[i], i))
        chosen = []
        for step, recorded in enumerate(policy[case]):
            mean, covariance = conditional(mean0, covariance0, H, chosen, yA, base["A"], noise)
            target = base["B"] + G @ mean
            check_equal(target, recorded["predictions_before"], "latent trust posterior before", 1e-9)
            check_equal(mean[0], recorded["gamma_before"], "latent gamma before", 1e-9)
            if arm == "adaptive_gamma_fixed_top8":
                choice = next(i for i in order if i not in chosen)
            else:
                scores = {}
                for i in range(146):
                    if i in chosen:
                        continue
                    observation = H[i]
                    uncertainty = float(observation @ covariance @ observation + noise[i])
                    direction = G @ covariance @ observation / np.sqrt(uncertainty)
                    draws = target[None] + normals[:, None] * direction[None]
                    scores[i] = float(np.sort(draws, axis=1)[:, -5:].sum(1).mean() - sum(sorted(target)[-5:]))
                choice = max(scores, key=lambda i: (scores[i], -i))
                check_equal(scores[choice], recorded["expected_gaussian_gain"], "latent KG value", 1e-9)
            assert choice == recorded["choice"] == row["screened"][step]
            innovation = yA[choice] - base["A"][choice] - H[choice] @ mean
            check_equal(innovation, row["trajectory"][step]["innovation"], "paid A innovation", 1e-9)
            chosen.append(choice)
            updated_mean, updated_cov = conditional(mean0, covariance0, H, chosen, yA, base["A"], noise)
            check_equal(updated_mean[0], row["trajectory"][step]["gamma_after"], "gamma posterior", 1e-9)
            check_equal(updated_cov[0, 0], row["trajectory"][step]["gamma_var_after"], "gamma posterior variance", 1e-9)
        mean, covariance = conditional(mean0, covariance0, H, chosen, yA, base["A"], noise)
        final = topfive(base["B"] + G @ mean)
        assert final == row["final_flags"]
        check_equal(yB[final].sum(), row["utility"], "trust independent B utility")
        check_equal(mean[0], row["final_gamma"], "final gamma", 1e-9)
        events = purchases[case]
        commit = next(i for i, event in enumerate(events) if event["event"] == "flags_committed")
        assert all(event["role"] == "A" for event in events[:commit] if event["event"] == "paid_reveal")
        paid = [event for event in events if event["event"] == "paid_reveal"]
        assert len(paid) == row["actual_credits"] == len(chosen) + 5 <= 13
        assert [event["candidate"] for event in paid if event["role"] == "B"] == final
        assert [event["recorded_credits"] for event in paid] == list(range(1, len(paid) + 1))
        assert all(not event["retry_created"] for event in paid)
        gamma[case] = float(mean[0])
    assert len(successor_rows) == 12
    frontier = STUDY / "budget_frontier1"
    frontier_p = read_json(frontier / "PROTOCOL.json")
    assert sha(frontier / "PROTOCOL.json") == read_json(frontier / "FREEZE.json")["protocol_sha256"]
    assert frontier_p["source_episode_sha256"] == sha(RUN / "EPISODES.jsonl")
    assert frontier_p["packet_manifest_sha256"] == sha(packet / "PACKET_MANIFEST.json")
    with (frontier / "FRONTIER.csv").open(encoding="utf-8", newline="") as handle:
        points = list(csv.DictReader(handle))
    checked = []
    for point in points:
        context, model, policy_name, count = point["context"], point["model"], point["policy"], int(point["screens"])
        token = context.replace("/", "_").replace("-", "_")
        row = original[f"{token}.{endpoint}.{model}.{policy_name}"]
        prefix = row["screened"][:count]
        assert len(prefix) == count and prefix == json.loads(point["selection_prefix"])
        prior = public[token + "__" + endpoint + "__" + model + "__B"]
        mean, _ = conditional(prior, public[endpoint + "__cov"], np.eye(146), prefix,
                              private[token + "__" + endpoint + "__A"], public[endpoint + "__offset"], public[endpoint + "__obsvar"])
        final = topfive(mean)
        assert final == json.loads(point["flags"])
        utility = float(private[token + "__" + endpoint + "__B"][final].sum())
        check_equal(utility, float(point["utility"]), "budget frontier utility")
        assert int(point["counterfactual_credits"]) == count + 5
        checked.append({"context": context, "model": model, "policy": policy_name, "screens": count, "utility": utility})
    assert len(checked) == 144
    baseline = {context: next(point["utility"] for point in checked if point["context"] == context and point["model"] == "M0" and point["policy"] == "knowledge_gradient" and point["screens"] == 8) for context in manifest["contexts"]}
    attainment = {}
    for model in frontier_p["models"]:
        for policy_name in frontier_p["policies"]:
            budgets = []
            for count in range(9):
                chosen = [point for point in checked if point["model"] == model and point["policy"] == policy_name and point["screens"] == count]
                assert len(chosen) == 2
                if all(point["utility"] >= baseline[point["context"]] - 1e-12 for point in chosen):
                    budgets.append(count)
            attainment[model + ":" + policy_name] = min(budgets) if budgets else None
    assert attainment == read_json(frontier / "SUMMARY.json")["first_exact_attainment"]
    result = {"verdict": "PASS", "packet_scalar_bytes": sum(manifest["sizes"].values()), "packet_replayed_episodes": 90,
              "trust_episodes": 12, "trust_profiles": sum(row["actual_credits"] for row in successor_rows),
              "closed_form_joint_conditioning_matches": True, "trust_gamma": gamma,
              "successor_protocol_sha256": freeze["protocol_sha256"], "frontier_points": len(points),
              "frontier_new_purchases": 0, "first_exact_both_context_attainment": attainment,
              "limitations": ["Frontier is posthoc, all outcomes previously exposed; no selected budget is confirmatory.",
                              "Trust channel changes gamma but does not improve utility against empirical-panel KG.",
                              "STATE forecast helps some early prefixes while hurting HepG2 at others; full per-cell curve required.",
                              "Packet reproduces scalar decisions, not fresh raw-data extraction or checkpoint inference."]}
    with (HERE / "FOLLOWUP_VERIFICATION.json").open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False); handle.write("\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
