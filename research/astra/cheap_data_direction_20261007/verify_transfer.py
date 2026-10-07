"""Independent frozen exploratory task-transfer reconstruction from qualified caches."""
from __future__ import annotations

import json
from collections import defaultdict

import numpy as np

from verify_direction import (HERE, ROOT, RUN, STUDY, check_equal,
                              jsonlines, raw_observations, raw_states, read_json, sha, topfive)
from verify_followups import conditional


def policy(prior, covariance, variance, offset, yA, kind, maximum):
    selected, trace = [], []
    normals = np.random.default_rng(42).standard_normal(64)
    order = sorted(range(146), key=lambda i: (-prior[i], i))
    for _ in range(maximum):
        mean, cov = conditional(prior, covariance, np.eye(146), selected, yA, offset, variance)
        gain = None
        if kind == "fixed_top_prior":
            choice = next(i for i in order if i not in selected)
        else:
            current = sum(sorted(mean)[-5:])
            scores = {}
            for i in range(146):
                if i in selected:
                    continue
                direction = cov[:, i] / np.sqrt(cov[i, i] + variance[i])
                samples = mean[None] + normals[:, None] * direction[None]
                scores[i] = float(np.sort(samples, axis=1)[:, -5:].sum(1).mean() - current)
            choice = max(scores, key=lambda i: (scores[i], -i))
            gain = scores[choice]
            if gain <= 0:
                break
        trace.append((choice, mean, gain))
        selected.append(choice)
    mean, _ = conditional(prior, covariance, np.eye(146), selected, yA, offset, variance)
    return selected, topfive(mean), trace


def main():
    p = read_json(STUDY / "TRANSFER_PROTOCOL.json")
    freeze = read_json(STUDY / "TRANSFER_FREEZE.json")
    assert sha(STUDY / "TRANSFER_PROTOCOL.json") == freeze["protocol_sha256"]
    assert freeze["protocol_sha256"] == "7b680de1ee6b66d5aec28a755eb129db6a3b8646ae069eedebc038b2968a160a"
    assert freeze["prior_full_profiles_and_development_direction_already_exposed"]
    for path, identity in p["source_dependencies"].items():
        assert sha(ROOT / path) == identity
    packet = STUDY / "transfer_packet1"
    meta = read_json(packet / "PACKET_MANIFEST.json")
    for path, identity in meta["source_hashes"].items():
        assert sha(ROOT / path) == identity
    for name, identity in meta["hashes"].items():
        assert sha(packet / name) == identity
    public, private = dict(np.load(packet / "public_prior.npz")), dict(np.load(packet / "evaluator_private.npz"))
    labels = p["menu"]["labels"]
    assert len(labels) == len(set(labels)) == 146
    keys = sorted({(label, plate) for label in labels for plate in p["menu"]["wells"][label]})
    index = {key: i for i, key in enumerate(keys)}
    roles = {role: np.array([index[(label, p["menu"]["wells"][label][j])] for label in labels])
             for j, role in enumerate(("A", "B"))}
    arrays = dict(np.load(RUN / "analysis_arrays.npz"))
    weights = arrays["curated_weights"]
    assert np.count_nonzero(weights) == 39
    assert np.flatnonzero(weights).tolist() == [r["coordinate"] for r in p["primary"]["mapped"]]
    m0 = arrays["panel_mean"]  # Source independently reconstructed in DIRECTION_VERIFICATION.json.
    for name in ("cov", "obsvar", "offset"):
        check_equal(public[name], arrays["curated_transcript_projection_" + name], "transfer common belief")
    both = arrays["train_availability"][:, roles["A"]] & arrays["train_availability"][:, roles["B"]]
    assert np.array_equal(both, public["availability"])
    for role in ("A", "B"):
        check_equal(public["train_" + role], arrays["train_delta"][:, roles[role]].astype(float) @ weights, "transfer train projection")
    excluded = {"c26.h5ad", "c31.h5ad", "c27.h5ad", "c12.h5ad", "c20.h5ad"}
    state, available = [], []
    for file in [f"c{i}.h5ad" for i in range(50) if f"c{i}.h5ad" not in excluded]:
        source, present, *_ = raw_states(file, keys)
        state.append(source); available.append(present)
    state, available = np.array(state), np.array(available)
    state_mean = (state.astype(np.float32) * available[..., None]).sum(0) / available.sum(0)[:, None]
    results = jsonlines(STUDY / "transfer_run1/EPISODES.jsonl")
    by_case = {row["case_id"]: row for row in results}
    traces, events = defaultdict(list), defaultdict(list)
    for row in jsonlines(STUDY / "transfer_run1/policy.jsonl"):
        traces[row["case_id"]].append(row)
    for row in jsonlines(STUDY / "transfer_run1/purchases.jsonl"):
        events[row["case_id"]].append(row)
    comparisons, costs = [], []
    for context, file in p["contexts"].items():
        assert context in ("HOP62", "Hs 766T", "C32")
        _, _, _, _, obs, row_index, controls = raw_observations(file, keys)
        observed = np.array([obs["mean"][row_index[key]].astype(float) - obs["ctrl_mean"][controls[key[1]]] for key in keys])
        _, _, state, state_index = raw_states(file, keys)
        native = np.array([state["paired_delta"][state_index[key]].astype(float) for key in keys])
        m2 = m0 + .5 * (native - state_mean)
        token = context.replace("/", "_").replace("-", "_")
        for model, prediction in (("M0", m0), ("M2", m2)):
            check_equal(public[token + "__" + model], prediction[roles["B"]] @ weights, "transfer native prior")
        for role in ("A", "B"):
            check_equal(private[token + "__" + role], observed[roles[role]] @ weights, "transfer original RNA projection")
            expected_counts = np.array([obs["n"][row_index[keys[i]]] for i in roles[role]])
            assert np.array_equal(expected_counts, private[token + "__counts_" + role])
            assert np.all(expected_counts >= 50)
        utility = {}
        for arm in p["arms"]:
            case_id = token + "." + arm["name"]
            row = by_case[case_id]
            prior = public[token + "__" + arm["model"]]
            screens, final, trace = policy(prior, public["cov"], public["obsvar"], public["offset"],
                                           private[token + "__A"], arm["policy"], arm["screens"])
            assert screens == row["screened"] and final == row["final_flags"]
            assert row["initial_flags"] == topfive(prior)
            check_equal(private[token + "__B"][final], row["final_B_values"], "transfer committed B values")
            check_equal(private[token + "__B"][final].sum(), row["utility"], "transfer utility")
            assert len(screens) + 5 == row["actual_credits"] == arm["cap"]
            assert row["unused_cap"] == 0
            assert len(traces[case_id]) == len(trace)
            for expected, recorded in zip(trace, traces[case_id]):
                assert expected[0] == recorded["choice"]
                check_equal(expected[1], recorded["mean_before"], "transfer paid-only posterior")
                if expected[2] is not None:
                    check_equal(expected[2], recorded["estimated_gaussian_gain"], "transfer KG value")
            purchases = events[case_id]
            commits = [j for j, event in enumerate(purchases) if event["event"] == "flags_committed"]
            assert len(commits) == 1 and purchases[commits[0]]["candidates"] == final
            assert all(event["role"] == "A" for event in purchases[:commits[0]] if event["event"] == "paid_reveal")
            paid = [event for event in purchases if event["event"] == "paid_reveal"]
            assert len(paid) == row["actual_credits"]
            assert [event["candidate"] for event in paid if event["role"] == "A"] == screens
            assert [event["candidate"] for event in paid if event["role"] == "B"] == final
            assert [event["recorded_credits"] for event in paid] == list(range(1, len(paid) + 1))
            assert all(not event["retry_created"] for event in paid)
            utility[arm["name"]] = row["utility"]
            costs.append({"case_id": case_id, "actual_profiles": len(paid), "policy_cap": arm["cap"],
                          "unused_policy_cap": 0, "common_reference_ceiling": 13,
                          "unused_common_reference_ceiling": 13 - len(paid)})
        comparisons.append({"context": context, "utility": utility,
                            "M2fixed5_minus_M0KG8": utility["M2_fixed5"] - utility["M0_KG8"],
                            "M2fixed5_minus_M0fixed5": utility["M2_fixed5"] - utility["M0_fixed5"],
                            "M2KG8_minus_M0KG8": utility["M2_KG8"] - utility["M0_KG8"],
                            "M2fixed8_minus_M0KG8": utility["M2_fixed8"] - utility["M0_KG8"]})
    assert len(results) == 15 and sum(row["actual_credits"] for row in results) == 177
    means = {arm["name"]: float(np.mean([row["utility"] for row in results if row["arm"] == arm["name"]])) for arm in p["arms"]}
    summary = read_json(STUDY / "transfer_run1/SUMMARY.json")
    for name, value in means.items():
        check_equal(value, summary["mean_utilities"][name], "transfer means")
    success = means["M2_fixed5"] >= means["M0_KG8"]
    assert success == summary["registered_raw_mean_cost_transfer_success"] == False
    result = {"verdict": "PASS", "protocol_sha256": freeze["protocol_sha256"],
              "episodes": len(results), "profiles": 177, "full_menu": 146,
              "source_projection_and_priors_reconstructed": True,
              "independent_closed_form_paid_A_policy_reproduction": True,
              "B_after_all_flags_committed": True, "all_retries_unbilled": True,
              "registered_lower_cost_transfer_success": success,
              "mean_utilities": means, "per_context_comparisons": comparisons, "cost_accounting": costs,
              "limits": ["All three source RNA profiles were exposed before this task freeze; not fresh heldout outcomes.",
                         "Direction and K5 derived on two other exposed development cells.",
                         "K5cap10 versus KG8cap13 is a measurement-efficiency comparison; samecost control M0fixed5 is separate.",
                         "The 13credit common ceiling is an analytical reference; K5 has three unused relative to it.",
                         "The endpoint is member-transcript RNA delta, not apoptosis function or independent biological efficacy."]}
    with (HERE / "TRANSFER_VERIFICATION.json").open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False); handle.write("\n")
    print(json.dumps({key: value for key, value in result.items() if key != "cost_accounting"}, indent=2))


if __name__ == "__main__":
    main()
