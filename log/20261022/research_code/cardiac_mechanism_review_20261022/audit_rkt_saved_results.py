"""Independent postrun audit from saved scores/rows; no raw responses or refitting."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "log/20261022/strategy_rethink"
OUT = ROOT / "log/20261022/cardiac_mechanism_review"


def read(name):
    return json.loads((SOURCE / name).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mean(values):
    return sum(values) / len(values)


def near(a, b):
    assert abs(a - b) < 1e-12, (a, b)


def main():
    frozen = read("FREEZE.json")
    assert all(sha(ROOT / x["path"]) == x["sha256"] for x in frozen["files"])
    seal = read("DEPLOYMENT_SEAL.json")
    assert seal["deployments_sha256"] == sha(SOURCE / "DEPLOYMENTS.json")
    assert seal["source_learning_sha256"] == sha(SOURCE / "SOURCE_LEARNING.json")
    assert seal["terminal_selected_for_scoring"] is False
    assert seal["terminal_feedback_exposed"] is False
    assert seal["earlier_full_truth_array_decoded"] is True
    assert seal["oracle_exposed"] is False
    result, trajectories = read("RESULT.json"), read("TRAJECTORY_RESULTS.json")
    deployments = read("DEPLOYMENTS.json")
    assert len(trajectories) == len(deployments) == 168
    by_key = {(d["episode"], d["seed"], d["arm"]): d for d in deployments}
    assert len(by_key) == 168
    feedback = {}
    expected_arms = {"old", "new", "cyclic", "source_best", "contextual", "history", "permuted"}
    assert {d["arm"] for d in deployments} == expected_arms
    assert {d["seed"] for d in deployments} == {1729, 2718, 31415}
    for d in deployments:
        assert d["start_program"] == 4
        proposed = [t["program"] for t in d["trajectory"]]
        assert len(proposed) == len(set(proposed)) == 4 and 4 not in proposed
        assert d["deployment"] in proposed + [4]
        # The saved trajectory omits S0 feedback; check chosen beats all saved candidates.
        candidates = {t["program"]: t["development_score"] for t in d["trajectory"]}
        if d["deployment"] != 4:
            assert d["deployment"] == min(candidates, key=lambda j: (-candidates[j], j))
        for t in d["trajectory"]:
            key = (d["episode"], t["program"])
            if key in feedback:
                near(feedback[key], t["development_score"])
            feedback[key] = t["development_score"]
    rows, reconstructed = read("TERMINAL_ROWS.json"), {}
    assert len(rows) == 104
    for saved in rows:
        values = {}
        assert len(saved["comp"]) == len(saved["line"]) == len(saved["row_cosine"])
        for compound, cosine in zip(saved["comp"], saved["row_cosine"]):
            values.setdefault(compound, []).append(cosine)
        assert len(values) == 32
        score = mean([mean(v) for v in values.values()])
        reconstructed[(saved["episode"], saved["program"])] = score
        recorded = result["episode_scores"][saved["episode"]]
        near(score, recorded["mixture"] if saved["program"] == "mixture"
             else recorded["program_scores"][saved["program"]])
    for d in trajectories:
        source = by_key[(d["episode"], d["seed"], d["arm"])]
        assert all(d[k] == v for k, v in source.items())
        near(d["terminal_score"], reconstructed[(d["episode"], d["deployment"])])
    means = {arm: mean([d["terminal_score"] for d in trajectories if d["arm"] == arm])
             for arm in expected_arms}
    for arm, program in [("S0", 4), ("full_dictionary", 10), ("mixture", "mixture")]:
        means[arm] = mean([score for (episode, p), score in reconstructed.items() if p == program])
    episodes = sorted({episode for episode, _ in reconstructed})
    means["oracle"] = mean([max(reconstructed[(e, p)] for p in range(12)) for e in episodes])
    for arm, value in means.items():
        near(value, result["means"][arm])
    difference = means["new"] - means["old"]
    near(difference, result["new_minus_old"])
    ordinary = ["old", "cyclic", "source_best", "contextual", "history", "S0", "full_dictionary", "mixture"]
    best = max(ordinary, key=lambda arm: means[arm])
    assert best == result["strongest_ordinary_envelope"]
    positive = means["oracle"] > means["S0"] and means["new"] > means["old"] and means["new"] > means[best]
    assert result["decision"] == ("ALLOW_SEPARATELY_FROZEN_SCREEN_ONLY" if positive else "STOP_CURRENT_ARENA_GRAMMAR")
    max_redundancy = max(abs(reconstructed[(e, p)] - reconstructed[(e, 0)]) for e in episodes for p in (1, 2))
    assert max_redundancy < 1e-12
    report = {"status": "PASS", "raw_response_arrays_loaded": False, "refits": 0,
              "freeze_sha256": sha(SOURCE / "FREEZE.json"),
              "screen_sha256": sha(ROOT / "research/strategy_rethink_20261022/screen.py"),
              "freeze_file_hashes": len(frozen["files"]), "equal_budget_trajectories": len(trajectories),
              "nominal_candidate_requests": len(trajectories) * 4, "reassembled_scores": len(rows),
              "new_minus_old": difference, "decision": result["decision"],
              "intercept_only_programs_0_1_2_max_terminal_difference": max_redundancy,
              "limit": "Saved candidate trajectories omit S0 development feedback; common-S0 fit/selection checked in code, not independently reconstructed from saved scores."}
    with (OUT / "RKT_SAVED_RESULT_AUDIT.json").open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report))


if __name__ == "__main__":
    main()
