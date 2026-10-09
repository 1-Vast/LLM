"""Independently reconstruct the frozen v9 pilot; no threshold fitting imports.

Run in maestro: python log/20261008/v9_verify.py
The explicit --write-receipt option records this check beside the verifier.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import binom

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from research.viability_contrast import prepare, run6, run8, world5b

OUT = ROOT / "outputs/viability_contrast_20261008/run9_pilot"
ALPHA, DELTA, FAMILY = .05, .05, 126
GRID = np.geomspace(.5, 64., 21)
ACQS = ("ginfo", "world", "random")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def upper(wrong, n, delta):
    """Invert the binomial lower tail, independently of run9's beta quantile."""
    if n == 0 or wrong == n:
        return 1.
    return float(brentq(lambda p: binom.cdf(wrong, n, p) - delta,
                        0., 1., xtol=1e-14))


def outcome(episode, threshold):
    if threshold is None:
        return False, False, 0, 0
    for score, cost in episode["trajectory"]:
        if abs(score) >= threshold:
            return (True, (1 if score > 0 else -1) != episode["truth_sign"],
                    cost, episode["qc_prefix"][cost - 1])
    return (False, False, episode["trajectory"][-1][1] if episode["trajectory"] else 0,
            episode["qc_prefix"][-1] if episode["trajectory"] else 0)


def verify():
    calibration = json.loads((OUT / "calibration.json").read_text())
    trajectories = json.loads((OUT / "trajectories.json").read_text())
    summary = json.loads((OUT / "summary.json").read_text())
    frame = pd.read_csv(OUT / "episodes.csv")
    freeze = json.loads((ROOT / "research/viability_contrast/freeze9_retry1.json").read_text())
    assert all(digest(ROOT / p) == h for p, h in freeze["files"].items())
    assert calibration["family_size"] == FAMILY
    minimum = math.ceil(math.log(DELTA / FAMILY) / math.log(1 - ALPHA))
    assert minimum == calibration["zero_error_min_n"] == 153

    pack = prepare.load_pack()
    classes = pack["menu"]["classes"]
    class_index = {c: i for i, c in enumerate(classes)}
    labels = np.array([class_index[pack["meta"].loc[c, "moa_main"]]
                       for c in pack["compounds"]])
    pools = np.array([pack["line_index"][l] for l in pack["menu"]["pool_lines"]])
    units = {c: str(pack["meta"].loc[c, "unit"]) for c in pack["compounds"]}
    assert len(set(units.values())) == len(units) == 517
    sets = [set(calibration[k]) for k in ("train", "calibration", "evaluation")]
    assert [len(s) for s in sets] == [200, 200, 117]
    assert all(not sets[i] & sets[j] for i in range(3) for j in range(i + 1, 3))
    assert set.union(*sets) == set(pack["compounds"])
    assert sets[2] == set(pack["folds"]["0"])
    ordered_units = sorted({units[c] for c in sets[0] | sets[1]}, key=lambda u:
                           hashlib.sha256(f"viability-contrast-9|split|{u}".encode()).hexdigest())
    assert {units[c] for c in sets[0]} == set(ordered_units[:200])
    assert set(trajectories["calibration"]) == set(trajectories["evaluation"]) == set(ACQS)

    supported = {"calibration": {}, "evaluation": {}}
    for split, expected_names in (("calibration", sets[1]), ("evaluation", sets[2])):
        for acquisition, episodes in trajectories[split].items():
            assert len(episodes) == len(expected_names)
            assert {e["compound"] for e in episodes} == expected_names
            supported[split][acquisition] = sum(e["pair"] is not None for e in episodes)
            for episode in episodes:
                c = episode["compound"]
                ci = int(labels[pack["index"][c]])
                rival = calibration["rivals"].get(str(ci))
                assert episode["unit"] == units[c]
                if rival is None:
                    assert episode["pair"] is None and episode["trajectory"] == []
                    assert episode["qc_prefix"] == []
                    continue
                pair = sorted((ci, rival))
                assert episode["pair"] == pair
                assert episode["truth_sign"] == (1 if ci == pair[0] else -1)
                assert [x[1] for x in episode["trajectory"]] == list(range(1, 17))
                assert len(episode["qc_prefix"]) == 16
                previous_qc, previous_score = 0, 0.
                for (score, cost), qc in zip(episode["trajectory"], episode["qc_prefix"]):
                    assert math.isfinite(score) and qc - previous_qc in (0, 1)
                    assert 0 <= qc <= cost
                    if qc > previous_qc:
                        assert math.isclose(score, previous_score, abs_tol=1e-12)
                    previous_qc, previous_score = qc, score

    bound_checks = 0
    for acquisition, episodes in trajectories["calibration"].items():
        assert len(calibration["tables"][acquisition]) == len(GRID)
        for row, threshold in zip(calibration["tables"][acquisition], GRID):
            assert math.isclose(row["threshold"], threshold, abs_tol=1e-12)
            outcomes = [outcome(e, threshold) for e in episodes]
            decided, wrong = sum(o[0] for o in outcomes), sum(o[1] for o in outcomes)
            assert (row["n"], row["decided"], row["wrong"]) == (200, decided, wrong)
            for endpoint, n in (("marginal", 200), ("conditional", decided)):
                assert math.isclose(row[endpoint + "_ucb"], upper(wrong, n, DELTA / FAMILY),
                                    abs_tol=1e-11)
                bound_checks += 1
        for endpoint in ("marginal", "conditional"):
            safe = [r for r in calibration["tables"][acquisition]
                    if r[endpoint + "_ucb"] <= ALPHA]
            selected = max(safe, key=lambda r: (r["decided"], -r["threshold"])) if safe else None
            assert calibration["selected"][acquisition][endpoint] == (
                selected["threshold"] if selected else None)

    checked_rows = 0
    assert len(frame) == 1053
    for acquisition, episodes in trajectories["evaluation"].items():
        for endpoint, threshold in {**calibration["selected"][acquisition], "abstain": None}.items():
            group = frame[(frame.acquisition == acquisition) & (frame.endpoint == endpoint)].set_index("compound")
            assert len(group) == 117 and group.index.is_unique
            for episode in episodes:
                row = group.loc[episode["compound"]]
                actual = (bool(row.decided), bool(row.wrong), int(row.measurements), int(row.qc))
                assert actual == outcome(episode, threshold)
                assert row.unit == episode["unit"]
                assert bool(row.supported) == (episode["pair"] is not None)
                assert (pd.isna(row.threshold) if threshold is None else
                        math.isclose(row.threshold, threshold, abs_tol=1e-12))
                checked_rows += 1
            n, decided, wrong = len(group), int(group.decided.sum()), int(group.wrong.sum())
            expected = {"n": n, "decided": decided, "wrong": wrong,
                        "coverage": decided / n, "marginal_wrong": wrong / n,
                        "conditional_wrong": wrong / decided if decided else None,
                        "marginal_ucb95": upper(wrong, n, .05),
                        "conditional_ucb95": upper(wrong, decided, .05),
                        "measurements": int(group.measurements.sum()), "qc": int(group.qc.sum())}
            observed = summary["arms"][acquisition + "__" + endpoint]
            for key, value in expected.items():
                assert observed[key] is None if value is None else math.isclose(observed[key], value, abs_tol=1e-11)
    primary = summary["arms"]["ginfo__marginal"]
    gate = (calibration["selected"]["ginfo"]["marginal"] is not None
            and primary["coverage"] >= .2 and primary["marginal_wrong"] <= .05
            and primary["marginal_ucb95"] <= .15)
    assert gate == summary["proceed_to_global"]

    # Rebuild only the proper-training proxy, using the committed hyperparameters.
    # The diagnostic input is synthetic; no evaluation outcome is used for model selection.
    positions = np.array([pack["index"][c] for c in calibration["train"]])
    by_class = [[pack["index"][c] for c in calibration["train"]
                 if labels[pack["index"][c]] == i] for i in range(len(classes))]
    fit = run6.FoldWorld(pack["auc"], by_class, positions, pools, "viability-contrast-9",
                        pack["meta"]["unit"].to_numpy(), select=False)
    fit.rank, fit.weight = calibration["rank"], calibration["weight"]
    fit.center, fit.V, fit.tau2 = world5b.fit_basis(pack["auc"][positions][:, pools], fit.rank)
    world = fit.make_world()
    prior_mean, _ = world.mean_scale()
    world.update(np.array([.5]), np.array([0]))
    means, scales = world.mean_scale()
    first = int(next(iter(calibration["rivals"])))
    second = calibration["rivals"][str(first)]
    first, second = sorted((first, second))
    candidates = np.arange(1, len(pools))
    increment = lambda a, j: run8.run7.huber_inc(a, j, means[first], scales[first], means[second], scales[second])
    chosen = run6.world_pick(means[first], scales[first], means[second], scales[second],
                            candidates, .5, 0., increment)
    collapse = {
        "rank": fit.rank, "weight": fit.weight,
        "prior_max_class_mean_gap": float(np.max(np.abs(prior_mean - prior_mean[0]))),
        "after_synthetic_read_max_class_mean_gap": float(np.max(np.abs(means - means[0]))),
        "after_synthetic_read_max_class_scale_gap": float(np.max(np.abs(scales - scales[0]))),
        "max_hypothesis_increment": float(max(abs(increment(.2, j)) for j in candidates)),
        "world_pick_next": int(chosen), "first_unpurchased": int(candidates[0]),
    }
    assert collapse["weight"] == 1.
    assert collapse["after_synthetic_read_max_class_mean_gap"] == 0.
    assert collapse["after_synthetic_read_max_class_scale_gap"] == 0.
    assert collapse["max_hypothesis_increment"] == 0.
    assert chosen == candidates[0]
    maximum_decisions = max(supported["calibration"].values())
    assert maximum_decisions == 116 < minimum
    return {
        "verdict": "PASS: frozen v9 artifacts reconstruct; scientific pilot does not pass",
        "method": "Independent first-crossing evaluator and binomial-CDF root inversion; run9.calibrate not imported",
        "frozen_pins_checked": len(freeze["files"]), "split_sizes": [200, 200, 117],
        "calibration_rows_checked": len(ACQS) * len(GRID), "calibration_bounds_checked": bound_checks,
        "evaluation_rows_checked": checked_rows, "supported_units": supported,
        "selected": calibration["selected"], "proceed_to_global": gate,
        "conditional_capacity": {"maximum_decisions": maximum_decisions,
                                 "zero_error_minimum": minimum,
                                 "best_possible_ucb": upper(0, maximum_decisions, DELTA / FAMILY),
                                 "interpretation": "Conditional certification is impossible in this frozen supported calibration set, even with zero errors."},
        "proper_training_world_collapse": collapse,
        "scope": [
            "Previously exposed fold0; annotation-conditioned true-versus-rival contrast, not blind mechanism discovery.",
            "Exact binomial risk claims require IID calibration/deployment episodes conditional on fixed training; class-stratified folds do not establish that assumption.",
            "The low-rank AUC proxy is not the official pretrained STATE model.",
            "All prefix outcomes and QC counts reconstruct from recorded trajectories; raw purchase identities are not stored, so this is not an independent raw-source replay of each acquisition.",
            "Collapse is a concrete hypothesis-conditioning flaw; it does not establish that adaptive acquisition or the dual-core framework cannot improve.",
            "No original frozen files, production modules or pilot results were edited by this verifier.",
        ],
        "artifact_sha256": {p.name: digest(p) for p in sorted(OUT.iterdir()) if p.is_file()},
        "verifier_sha256": digest(__file__),
    }


if __name__ == "__main__":
    result = verify()
    text = json.dumps(result, indent=2) + "\n"
    if "--write-receipt" in sys.argv:
        destination = Path(__file__).with_name("VIABILITY_CONTRAST_V9_VERIFY.json")
        if destination.exists():
            raise RuntimeError("Refusing to overwrite the independent verification receipt")
        destination.write_text(text, encoding="utf-8")
    print(text)
