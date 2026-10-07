"""Scientific input boundaries on synthetic plates and reference queries."""
import numpy as np
import pandas as pd
import pytest

from research.astra.functional_data_20261007.extract import interpolate_observed, plate_mono, summarize_curves
from research.astra.functional_data_20261007.mono_world import predict
from research.astra.functional_data_20261007.prism import structures
from research.astra.functional_data_20261007.recipes import top_vectors, as_intervention


def plate():
    f = pd.DataFrame(dict(POSITION=[str(i) for i in range(10)], TAG=["B"] * 3 + ["NC-1"] * 3 + ["A1-S", "L1-D1-S", "L1-D2-S", "L1-D3-S"],
                          INTENSITY=[10.] * 3 + [110.] * 3 + [60., 100., 70., 30.],
                          DRUG_ID=[None] * 6 + ["1", "2", "2", "2"], CONC=[None] * 6 + ["1", ".01", ".1", "1"]))
    for col, value in dict(BARCODE="plate1", SANGER_MODEL_ID="history", CELL_ID="cell1", DATE_CREATED="2020-01-01",
                           RESEARCH_PROJECT="GDSC_Colo-2", ASSAY="Glo", DURATION="4", SEEDING_DENSITY="600").items():
        f[col] = value
    return f


def test_controls_normalize_mono_without_joint_fit():
    points, qc = plate_mono(plate(), "Colon")
    assert qc["reason"] == "PASS"
    assert set(points.tissue) == {"Colon"} and set(points.project) == {"GDSC_Colo-2"}
    assert points.loc[points.role.eq("anchor"), "viability"].iloc[0] == .5


def test_combo_poisoning_does_not_change_mono_points():
    f = plate()
    combo = f.iloc[-1:].copy()
    combo["POSITION"], combo["TAG"], combo["INTENSITY"] = "10", "A1-C", 99999.
    a, _ = plate_mono(f, "Colon")
    b, _ = plate_mono(pd.concat([f, combo]), "Colon")
    pd.testing.assert_frame_equal(a, b)


def test_ambiguous_component_well_quarantined():
    f = plate()
    extra = f.iloc[-1:].copy(); extra["DRUG_ID"] = "3"
    points, qc = plate_mono(pd.concat([f, extra]), "Colon")
    assert qc["omitted_ambiguous_or_invalid_rows"] == 2
    assert not points.dose_uM.eq(1).loc[points.role.eq("library")].any()


def test_invalid_controls_reject_before_response():
    f = plate(); f.loc[f.TAG.eq("NC-1"), "INTENSITY"] = 10.
    points, qc = plate_mono(f, "Colon")
    assert points is None and qc["reason"] == "invalid_normalization_denominator"


def test_no_clipping_of_measurement():
    f = plate();f.loc[f.TAG.eq("A1-S"), "INTENSITY"] = 160.
    points, _ = plate_mono(f, "Colon")
    assert points.loc[points.role.eq("anchor"), "viability"].iloc[0] == 1.5


def test_log_interpolation_is_bracketed_and_exact_single_point_allowed():
    assert interpolate_observed([1, 4], [1, 0], 2) == (.5, "bracketed_log_interpolation")
    assert interpolate_observed([1], [.6], 1) == (.6, "exact_observed")
    assert interpolate_observed([1, 4], [1, 0], 10) is None
    assert interpolate_observed([1], [.6], 2) is None


def test_area_and_adjacent_change_are_observed_summaries():
    points, _ = plate_mono(plate(), "Colon")
    _, curves = summarize_curves(points)
    a = curves[curves.role.eq("anchor")].iloc[0]
    assert pd.isna(a.observed_range_area) and pd.isna(a.top_adjacent_change)
    b = curves[curves.role.eq("library")].iloc[0]
    assert b.n_doses == 3 and np.isfinite(b.observed_range_area)


def test_world_state_arrives_and_queries_have_no_target_labels():
    context = pd.DataFrame({"pathway": np.arange(12, dtype=float)}, index=[f"s{i}" for i in range(12)])
    train = pd.DataFrame(dict(sidm=[f"s{i}" for i in range(10)], tissue="Breast", drug_id="1", dose_uM=1., viability=np.arange(10) / 10))
    queries = pd.DataFrame(dict(sidm=["s10", "s11"], tissue="Breast", drug_id="1", dose_uM=1.))
    base = predict(train, queries, context, False)
    state = predict(train, queries, context, True)
    assert base.prediction.iloc[0] == base.prediction.iloc[1]
    assert state.prediction.iloc[0] != state.prediction.iloc[1]
    swapped = context.copy(); swapped.loc[["s10", "s11"]] = context.loc[["s11", "s10"]].to_numpy()
    other = predict(train, queries, swapped, True)
    np.testing.assert_allclose(state.prediction, other.prediction.iloc[::-1])


def test_world_unsupported_drug_dose_refuses():
    train = pd.DataFrame(dict(sidm=["s"], tissue=["Breast"], drug_id=["1"], dose_uM=[1.], viability=[.5]))
    queries = pd.DataFrame(dict(sidm=["target"], tissue=["Breast"], drug_id=["1"], dose_uM=[1000.]))
    out = predict(train, queries, pd.DataFrame(), False)
    assert out.prediction.isna().all() and out.status.iloc[0] == "no_exact_drug_dose_history"


def test_prism_repeated_same_structure_is_not_multiple_components():
    assert structures("CCO, CCO") == structures("CCO")
    assert len(structures("CCO, CCC")) == 2


def test_composite_top_uses_actual_vectors_not_tag_step_number():
    recipe = pd.DataFrame(dict(BARCODE=["p"] * 3, dose_step=[1, 2, 7], component_doses_uM=["10|1", "5|.5", ".009765625|.0009765625"]))
    assert top_vectors(recipe).component_doses_uM.iloc[0] == "10|1"


def test_no_single_well_top_across_components_is_rejected():
    recipe = pd.DataFrame(dict(BARCODE=["p"] * 2, component_doses_uM=["10|.1", "5|1"]))
    with pytest.raises(ValueError, match="no_common_componentwise_top"):
        top_vectors(recipe)


def test_existing_core_type_keeps_component_specific_doses_and_no_target_action_claim():
    obj = as_intervention(dict(composite_id="1032|1372", component_ids="1032|1372", component_doses_uM="10|1"))
    assert obj.is_combination
    assert [z.dose for z in obj.components] == [10., 1.]
    assert all(z.dose_unit == "uM" and not z.realized_effects for z in obj.components)
