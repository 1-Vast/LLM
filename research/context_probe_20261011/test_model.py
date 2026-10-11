"""Isolation and behavioral checks for the fixed-probe diagnostic."""
import numpy as np
import pytest

from research.context_probe_20261011.model import fit_prior, fit_reference


def example():
    rng = np.random.default_rng(73)
    basal = rng.normal(size=(24, 12))
    drug_loadings = rng.normal(size=(20, 2))
    response = rng.normal(size=(24, 2)) @ drug_loadings.T + rng.normal(size=(24, 20)) * 0.01
    return basal, response


def test_unpurchased_target_poison_cannot_change_any_predictions_or_order():
    basal, response = example()
    target = response[-1].copy()
    model = fit_reference(basal[:-1], response[:-1], prior="knn", n_neighbors=5)
    probes = model.select_probes(8)
    poisoned = target.copy()
    poisoned[np.setdiff1d(np.arange(len(target)), probes)] = 1e100
    for method in ("none", "offset", "lowrank", "shuffled", "conditional"):
        before = model.predict(basal[-1], probes, target[probes], method=method)
        after = model.predict(basal[-1], probes, poisoned[probes], method=method)
        np.testing.assert_array_equal(before, after)
        np.testing.assert_array_equal(np.argsort(before), np.argsort(after))
    np.testing.assert_array_equal(probes, model.select_probes(8))


@pytest.mark.parametrize("family", ["mean", "knn", "ridge"])
def test_crossfit_predictor_never_uses_held_context_response(family):
    basal, response = example()
    model = fit_reference(basal, response, prior=family, n_features=5)
    changed = response.copy()
    held = 3
    changed[held] = 1e6
    poisoned = fit_reference(basal, changed, prior=family, n_features=5)
    same_fold = model.fold_ids_ == model.fold_ids_[held]
    np.testing.assert_array_equal(model.crossfit_predictions_[same_fold],
                                  poisoned.crossfit_predictions_[same_fold])
    assert np.linalg.norm(model.residuals_[held]) > 1e-8


def test_each_crossfit_fold_refits_reference_feature_selection_and_scaling():
    basal, response = example()
    basal[0, 0] = 10000
    model = fit_reference(basal, response, prior="knn", n_features=4, n_neighbors=3)
    for held in range(len(basal)):
        keep = model.fold_ids_ != model.fold_ids_[held]
        manual = fit_prior(basal[keep], response[keep], prior="knn", n_features=4, n_neighbors=3)
        np.testing.assert_allclose(model.crossfit_predictions_[held], manual.predict(basal[held]))
    before = model.prior_model.center.copy(), model.prior_model.scale.copy(), model.prior_model.genes.copy()
    model.predict_prior(np.full(basal.shape[1], 1e8))
    for original, current in zip(before, (model.prior_model.center, model.prior_model.scale, model.prior_model.genes)):
        np.testing.assert_array_equal(original, current)


def test_offset_preserves_rank_and_identity_shuffle_changes_differential_prediction():
    basal, response = example()
    model = fit_reference(basal[:-1], response[:-1])
    probes = model.select_probes(8)
    baseline = model.predict_prior(basal[-1])
    offset = model.predict(basal[-1], probes, response[-1, probes], method="offset")
    np.testing.assert_array_equal(np.argsort(baseline), np.argsort(offset))
    regular = model.predict(basal[-1], probes, response[-1, probes], method="lowrank", rank=2)
    shuffled = model.predict(basal[-1], probes, response[-1, probes], method="shuffled", rank=2)
    assert not np.allclose(regular, shuffled)
    assert not np.array_equal(np.argsort(regular), np.argsort(shuffled))


def test_predicted_probes_add_no_information():
    basal, response = example()
    model = fit_reference(basal, response)
    probes = model.select_probes(8)
    baseline = model.predict_prior(basal[0])
    for method in ("offset", "lowrank", "conditional"):
        updated = model.predict(basal[0], probes, baseline[probes], method=method)
        np.testing.assert_array_equal(baseline, updated)


def test_missing_reference_outcomes_remain_missing_and_counts_are_auditable():
    basal, response = example()
    response[0, :4] = np.nan
    model = fit_reference(basal, response, prior="ridge", n_features=4)
    assert np.isnan(model.residuals_[0, :4]).all()
    np.testing.assert_array_equal(model.valid_counts_[:4], 23)
    np.testing.assert_array_equal(model.residual_bank_[0, :4], 0)
    assert np.isfinite(model.predict_prior(basal[0])).all()


def test_purchased_probe_contract_rejects_missing_or_duplicated_measurements():
    basal, response = example()
    model = fit_reference(basal, response)
    with pytest.raises(ValueError, match="finite purchased"):
        model.predict(basal[0], [0, 1], [0.1, np.nan], method="lowrank")
    with pytest.raises(ValueError, match="unique valid"):
        model.predict(basal[0], [0, 0], [0.1, 0.2], method="lowrank")
