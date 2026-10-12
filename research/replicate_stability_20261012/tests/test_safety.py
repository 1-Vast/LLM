"""Behavioral checks before any secondary response-value admission."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import numpy as np
import pytest


SPEC = importlib.util.spec_from_file_location(
    "repeat_stability_runner", Path(__file__).resolve().parents[1] / "run.py"
)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def paired_metadata():
    metadata, repeats = {}, []
    for number in (1, 2, 3):
        plate = f"PLATE_X{number}"
        repeat = {"detection_plate": plate}
        for side, drug, well in (("left", "DRUG_A", "A01"), ("right", "DRUG_B", "A02")):
            column = f"{plate}:{well}::HTS002"
            metadata[column] = {"broad_id": drug, "dose": "2.5", "screen_id": "HTS002",
                "perturbation_type": "experimental_treatment", "compound_plate": "PLATE", "detection_plate": plate, "well": well}
            repeat[f"{side}_column"] = column
            repeat[f"{side}_well"] = well
            repeat[f"{side}_column_in_response_header"] = True
        repeats.append(repeat)
    case = {"eligible": True, "left_broad_id": "DRUG_A", "right_broad_id": "DRUG_B", "repeat_columns": repeats,
        "blocks": [{"eligible": True, "compound_plate": "PLATE", "expected_detection_plates": [r["detection_plate"] for r in repeats], "repeat_columns": repeats}]}
    return case, metadata


def test_missing_third_repeat_is_retained_and_never_replaced():
    case, metadata = paired_metadata()
    case["repeat_columns"][2]["left_column_in_response_header"] = False
    runner.validate_pair_columns(case, metadata)
    snapshot = deepcopy(case)
    diagnosis = runner.diagnose_pair([-2., -1., np.nan], 1., -.2)
    assert diagnosis["expected_repeats"] == 3
    assert diagnosis["observed_repeats"] == 2
    assert diagnosis["missing_repeat_comparisons"] == 2
    assert diagnosis["secondary_differences"] == [-2., -1., None]
    assert diagnosis["complete"] is False
    assert diagnosis["status"] == "INCOMPLETE_REPEAT_OBSERVATIONS"
    assert case == snapshot


def test_expected_plate_set_cannot_be_shrunk_to_hide_missing_repeat():
    case, metadata = paired_metadata()
    shortened = case["repeat_columns"][:2]
    case["repeat_columns"] = shortened
    case["blocks"][0]["repeat_columns"] = shortened
    case["blocks"][0]["expected_detection_plates"] = [r["detection_plate"] for r in shortened]
    with pytest.raises(ValueError):
        runner.validate_pair_columns(case, metadata)


@pytest.mark.parametrize("differences,status", [
    ([-2., -1., -3.], "STABLE_SUPPORTS_PRIOR_ORDER"),
    ([2., 1., 3.], "STABLE_OPPOSES_PRIOR_ORDER"),
    ([-2., 1., -3.], "DIRECTION_DISAGREEMENT"),
    ([0., 0., 0.], "ALL_ZERO_TIES"),
    ([0., 1., 3.], "TIES_WITH_ONE_DIRECTION"),
])
def test_repeat_direction_labels_are_signed_contrasts(differences, status):
    diagnosis = runner.diagnose_pair(differences, np.nan, -.2)
    assert diagnosis["complete"] is True
    assert diagnosis["status"] == status
    assert diagnosis["primary_difference"] is None


def test_zero_ties_do_not_count_as_directional_agreement():
    diagnosis = runner.diagnose_pair([0., 0., 0.], 0., -.2)
    assert diagnosis["nonzero_repeat_comparisons"] == 0
    assert diagnosis["discordant_repeat_comparisons"] == 0
    assert diagnosis["tied_repeat_comparisons"] == 3
    mixed = runner.diagnose_pair([1., -1., 0.], 0., -.2)
    assert mixed["nonzero_repeat_comparisons"] == 1
    assert mixed["discordant_repeat_comparisons"] == 1
    assert mixed["tied_repeat_comparisons"] == 2
    assert mixed["status"] == "DIRECTION_DISAGREEMENT"


def test_a_signed_near_zero_contrast_keeps_its_magnitude_and_tied_prior_flag():
    diagnosis = runner.diagnose_pair([1e-12, 2e-12, 3e-12], 0., 0.)
    assert diagnosis["prior_prediction_tied"] is True
    assert diagnosis["min_abs_secondary_difference"] == 1e-12
    assert diagnosis["mean_secondary_difference"] == pytest.approx(2e-12)


@pytest.mark.parametrize("mutation", ["cross_plate", "cross_screen", "wrong_dose", "swapped_repeat", "duplicate_repeat", "changed_well", "duplicate_condition"])
def test_pairing_rejects_fake_or_ambiguous_repeat_axes(mutation):
    case, metadata = paired_metadata()
    runner.validate_pair_columns(case, metadata)
    repeat = case["repeat_columns"][1]
    if mutation == "cross_plate":
        metadata[repeat["right_column"]]["compound_plate"] = "OTHER_PLATE"
    elif mutation == "cross_screen":
        metadata[repeat["right_column"]]["screen_id"] = "MTS010"
    elif mutation == "wrong_dose":
        metadata[repeat["right_column"]]["dose"] = "10"
    elif mutation == "swapped_repeat":
        repeat["right_column"] = case["repeat_columns"][2]["right_column"]
    elif mutation == "duplicate_repeat":
        case["repeat_columns"][1] = deepcopy(case["repeat_columns"][0])
        case["blocks"][0]["expected_detection_plates"][1] = "PLATE_X1"
    elif mutation == "changed_well":
        metadata[repeat["right_column"]]["well"] = "B02"
        repeat["right_well"] = "B02"
    else:
        metadata["DUPLICATE"] = deepcopy(metadata[repeat["right_column"]])
    with pytest.raises(ValueError):
        runner.validate_pair_columns(case, metadata)


def test_outcome_direction_does_not_recruit_or_modify_fixed_pair():
    case, metadata = paired_metadata()
    frozen = deepcopy(case)
    runner.validate_pair_columns(case, metadata)
    for differences in ([-1., -2., -3.], [1., 2., 3.], [np.nan, np.nan, np.nan]):
        runner.diagnose_pair(differences, np.nan, -.2)
        assert case == frozen
        runner.validate_pair_columns(case, metadata)


def test_context_ledger_retains_ineligible_and_empty_contexts_without_success():
    contexts = [{"context": "partial", "index": 0}, {"context": "unmapped", "index": 1}, {"context": "empty", "index": 2}]
    rows = [{"context": "partial", "eligible": True, **runner.diagnose_pair([-1., np.nan, -1.], 1., -.2)},
            {"context": "unmapped", "eligible": False, **runner.diagnose_pair([], 1., -.2)}]
    summary = runner.summarize(rows, contexts)
    assert summary["contexts"] == 3
    assert summary["complete_pairs"] == 0
    assert summary["context_macro"]["stable_opposes_fraction_complete"]["mean"] is None
    assert summary["context_macro"]["stable_opposes_fraction_complete"]["contributing_contexts"] == 0
    ledger = {row["context"]: row for row in summary["context_rows"]}
    assert ledger["partial"]["incomplete_eligible_pairs"] == 1
    assert ledger["partial"]["missing_repeat_comparisons"] == 2
    assert summary["repeat_comparison_counts"]["missing_repeat_comparisons"] == 2
    assert ledger["unmapped"]["intended_pairs"] == 1
    assert ledger["unmapped"]["metadata_eligible_pairs"] == 0
    assert ledger["empty"]["intended_pairs"] == 0
    assert ledger["empty"]["repeat_discordance_fraction"] is None
