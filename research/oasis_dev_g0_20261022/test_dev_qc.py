"""Meaningful data-flow, physical-grain and normalisation contracts."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SPEC = importlib.util.spec_from_file_location("dev_qc", Path(__file__).with_name("dev_qc.py"))
qc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qc)


def test_predicate_export_refuses_other_compounds(tmp_path):
    path = tmp_path / "mixed.parquet"
    pd.DataFrame({"compound": ["dev", "reserve", "selection", "DMSO"],
                  "response": [1., 9876543., 1234567., 0.]}).to_parquet(path)
    result = qc.scan_allowed(path, {"dev", "DMSO"}, ["compound", "response"], "compound")
    assert set(result["compound"]) == {"dev", "DMSO"}
    assert set(result["response"]) == {0., 1.}


def test_duplicate_conflict_and_well_canonicalisation():
    frame = pd.DataFrame({"source": ["assayworks_prod_25", "prod_25"], "plate": ["p", "p"],
                          "well": ["a1", "A01"], "compound_name": ["drug", "drug"],
                          "compound_concentration_um": [1., 1.], "mt": [3., 3.]})
    assert len(qc.deduplicate(frame, ["mt"])) == 1
    frame.loc[1, "mt"] = 4.
    with pytest.raises(ValueError, match="Conflicting"):
        qc.deduplicate(frame, ["mt"])


def test_control_only_normalisation_is_invariant_to_drug_values():
    frame = pd.DataFrame({"batch": ["b"]*10, "plate": ["p"]*10,
        "is_dmso": [True]*8 + [False]*2, "mtt_lumi": [100., 101., 99., 102., 98., 100., 100., 100., 50., 80.],
        "ldh_abs": [0., 1., -1., 2., -2., 1., -1., 0., 4., 2.],
        "ldh_abs_signal": [0.]*10, "ldh_abs_background": [0.]*10, "cell_count": [10.]*8 + [5., 8.]})
    controls = qc.plate_controls(frame)
    assert controls.iloc[0]["plate_pass"]
    first = qc.normalise(frame, controls)
    assert first.iloc[8]["mt_target"] == -1.
    altered = frame.copy()
    altered.loc[9, ["mtt_lumi", "ldh_abs", "cell_count"]] = [1e9, 1e6, 1e8]
    pd.testing.assert_frame_equal(controls, qc.plate_controls(altered))
    assert qc.normalise(altered, qc.plate_controls(altered)).iloc[8]["mt_target"] == -1.


def test_repeat_pair_selection_does_not_select_by_response():
    frame = pd.DataFrame({"compound_id": ["c"]*3, "group_id": ["g"]*3, "dose_um": [1.]*3,
        "batch": ["b"]*3, "plate": ["p3", "p1", "p2"], "well": ["A01"]*3,
        "mt_target": [100., 1., 2.], "ldh_target": [100., 3., 4.]})
    pair = qc.pairs_for_repeat(frame).iloc[0]
    assert (pair["plate_1"], pair["plate_2"]) == ("p1", "p2")
    assert (pair["mt_1"], pair["mt_2"]) == (1., 2.)
    frame["observation_pass"] = [True, False, True]
    failed_pair = qc.pairs_for_repeat(frame).iloc[0]
    assert (failed_pair["plate_1"], failed_pair["plate_2"]) == ("p1", "p2")
    assert not failed_pair["pair_pass"]


def test_constant_response_is_negative_evidence_not_serialisation_failure():
    pairs = pd.DataFrame({"group_id": ["a", "b"], "pair_pass": [True, True],
                          "mt_1": [1., 1.], "mt_2": [1., 1.],
                          "ldh_1": [0., 0.], "ldh_2": [0., 0.]})
    result = qc.repeat_summary(pairs, draws=5)
    assert not result["pass"]
    assert result["endpoints"]["mt"]["spearman"] is None
    assert result["endpoints"]["ldh"]["reason"] == "NO_DYNAMIC_RANGE"


def test_missing_count_and_nonpositive_mt_are_failed_observations():
    frame = pd.DataFrame({"batch": ["b"]*10, "plate": ["p"]*10, "is_dmso": [True]*8+[False]*2,
        "mtt_lumi": [100.]*8+[0., 50.], "ldh_abs": [0., 1., -1., 2., -2., 1., -1., 0., 3., 4.],
        "ldh_abs_signal": [0.]*10, "ldh_abs_background": [0.]*10, "cell_count": [10.]*9+[np.nan]})
    result = qc.normalise(frame, qc.plate_controls(frame))
    assert not result.iloc[8]["observation_pass"]
    assert not result.iloc[9]["observation_pass"]
    assert np.isnan(result.iloc[8]["mt_target"])
