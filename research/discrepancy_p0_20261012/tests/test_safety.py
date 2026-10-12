"""Behavioral checks for retrospective diagnostics on immutable commitments."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from itertools import combinations
from pathlib import Path

import numpy as np
import pytest


SPEC = importlib.util.spec_from_file_location(
    "p0_diagnose_archive", Path(__file__).resolve().parents[1] / "diagnose_archive.py"
)
diagnostic = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(diagnostic)


def archive_fixture():
    contexts = np.array(["reference", "first", "development", "second"])
    roles = np.array(["reference", "evaluation", "development", "evaluation"])
    drugs = np.array(["D0", "PROBE", "D2", "D3", "D4"])
    arms = ["zero_purchase", "candidate"]
    predictions = np.array([
        [[0, -100, 1, 2, 3], [3, -100, 0, 1, 2]],
        [[3, -100, 2, 0, 1], [0, -100, 3, 2, 1]],
    ], dtype=float)
    selections = [[0, 2], [2, 3], [3, 4], [0, 4]]
    commits = [
        {"index": index, "context": str(contexts[index]), "arm": arm,
         "selected_indices": selected, "selected_ids": drugs[selected].tolist()}
        for index, arm, selected in zip([1, 1, 3, 3], arms * 2, selections)
    ]
    return contexts, roles, drugs, predictions, commits, [1], arms, 2


def test_fixed_menu_and_commitments_do_not_follow_hidden_outcomes():
    contexts, roles, drugs, predictions, commits, probes, arms, k = archive_fixture()
    indices, menu = diagnostic.validate_alignment(
        contexts, roles, drugs, predictions, commits, probes, arms, k
    )
    np.testing.assert_array_equal(indices, [1, 3])
    np.testing.assert_array_equal(menu, [0, 2, 3, 4])
    original = deepcopy(commits)
    reports = []
    for truth in (np.array([-1., -100., -2., 3., 4.]),
                  np.array([-1., -100., -2., -1000., np.nan])):
        reports.append(diagnostic.diagnose_case(
            truth, predictions[0, 0], predictions[0, 0],
            commits[0]["selected_indices"], commits[0]["selected_indices"], menu, k
        ))
    for report in reports:
        assert report["selected_indices"] == [0, 2]
        assert report["baseline_selected_indices"] == [0, 2]
        assert report["added_indices"] == report["removed_indices"] == []
        assert report["utility"] == 1.5
    assert commits == original
    assert reports[0]["measured_per_band"]["selected_prior"] == 2
    assert reports[1]["measured_per_band"]["selected_prior"] == 2
    assert reports[1]["measured_per_band"]["boundary"] == 1


def test_missing_selected_outcome_stays_null_without_replacement():
    prediction = np.arange(6, dtype=float)
    truth = np.array([np.nan, -1., -2., -3., -4., -1000.])
    report = diagnostic.diagnose_case(
        truth, prediction, prediction, [0, 1], [0, 1], np.arange(6), 2
    )
    assert report["selected_indices"] == [0, 1]
    assert report["selected_missing"] == 1
    for key in ("utility", "baseline_utility", "utility_increment", "swap_gain",
                "exact_full_menu_oracle_utility", "exact_full_menu_regret",
                "full_menu_regret_lower_bound"):
        assert report[key] is None
    assert report["observed_subset_hindsight_utility"] == 502.
    assert report["exact_oracle_status"] == "UNKNOWN_MISSING_MENU_OUTCOMES"


def test_incomplete_menu_reference_is_only_a_regret_lower_bound():
    truth = np.array([-5., -1., 0., 1., np.nan, 2.])
    prediction = np.array([4., -2., -1., 1., 2., 3.])
    menu = np.arange(6)
    report = diagnostic.diagnose_case(
        truth, prediction, prediction, [1, 2], [1, 2], menu, 2
    )
    assert diagnostic.exact_oracle(truth, menu, 2) is None
    assert report["exact_full_menu_regret"] is None
    assert report["observed_subset_hindsight_utility"] == 3.
    assert report["full_menu_regret_lower_bound"] == 2.5
    for missing_response in (100., -100.):
        complete = truth.copy()
        complete[4] = missing_response
        possible_oracle = max(-sum(complete[list(choice)]) / 2 for choice in combinations(menu, 2))
        realized_regret = possible_oracle - report["utility"]
        assert realized_regret >= report["full_menu_regret_lower_bound"]


def test_complete_menu_oracle_and_swap_decomposition_match_enumeration():
    truth = np.array([-4., -2., -1., 0., -100., 5.])
    menu = np.array([0, 1, 2, 3, 5])
    baseline = np.array([0., 2., 1., 3., -100., 4.])
    prediction = np.array([2., 0., 1., 3., -100., 4.])
    expected_oracle = max(-sum(truth[list(choice)]) / 2 for choice in combinations(menu, 2))
    report = diagnostic.diagnose_case(
        truth, prediction, baseline, [1, 2], [0, 2], menu, 2
    )
    assert report["exact_oracle_status"] == "COMPLETE_FIXED_MENU"
    assert report["exact_full_menu_oracle_utility"] == expected_oracle == 3.
    assert report["exact_full_menu_regret"] == 1.5
    assert report["utility_increment"] == report["swap_gain"] == -1.
    assert report["added_indices"] == [1]
    assert report["removed_indices"] == [0]


def test_ties_use_frozen_drug_indices_and_exclude_attractive_probes():
    prediction = np.array([0., -100., 0., 0., 0.])
    np.testing.assert_array_equal(diagnostic.rank_menu(prediction, [4, 2, 0, 3]), [0, 2, 3, 4])
    with pytest.raises(ValueError):
        diagnostic.rank_menu(prediction, [0, 0, 2])


@pytest.mark.parametrize("mutation", ["context_axis", "arm_axis", "roles", "drug_ids", "commits", "probe_selection"])
def test_alignment_rejects_misaligned_archives(mutation):
    contexts, roles, drugs, predictions, commits, probes, arms, k = archive_fixture()
    if mutation == "context_axis":
        predictions = predictions[::-1]
    elif mutation == "arm_axis":
        predictions = predictions[:, ::-1]
    elif mutation == "roles":
        roles[[0, 1]] = roles[[1, 0]]
    elif mutation == "drug_ids":
        drugs[[0, 2]] = drugs[[2, 0]]
    elif mutation == "commits":
        commits = commits[::-1]
    else:
        commits[0]["selected_indices"] = [0, 1]
        commits[0]["selected_ids"] = ["D0", "PROBE"]
    with pytest.raises(ValueError):
        diagnostic.validate_alignment(contexts, roles, drugs, predictions, commits, probes, arms, k)
