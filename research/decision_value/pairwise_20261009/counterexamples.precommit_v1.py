"""Counterexamples for training isolation, legal feedback and decision accounting."""
import json

import numpy as np
import pytest

from research.decision_value.pairwise_20261009 import model, run


def fixture():
    rng = np.random.default_rng(17)
    state = rng.normal(size=(14, 10))
    outcomes = np.arange(10)[None] * .01 + state * .1 + rng.normal(scale=.02, size=state.shape)
    arrays = dict(train_A=outcomes + rng.normal(scale=.03, size=state.shape), train_B=outcomes,
        precision_B=np.ones_like(state), state_B=state, state_available_B=np.ones_like(state, dtype=bool),
        basal=rng.normal(size=(14, 7)))
    records = [dict(cid=str(i // 2), smiles="C" * (i // 2 + 1), dose=float(i % 2 + 1), unit="uM") for i in range(10)]
    values = np.repeat(rng.normal(size=(5, 8)), 2, axis=0)
    kernels, eigens, mask, _ = model.prepare_kernels(records, dict(molecule256=values, knowledge1024=values * 2))
    return arrays, kernels, eigens, mask


def test_nested_histories_exclude_held_and_incomplete():
    complete = [i for i in range(45) if i not in (31, 34)]
    first = model.histories(complete, 7, 11)
    assert first == model.histories(complete, 7, 11)
    assert set(first[4]) < set(first[8]) < set(first[16])
    assert all(not {7, 31, 34}.intersection(value) for value in first.values())


def test_held_label_poison_cannot_change_choices_prior_pairs_or_query():
    arrays, kernels, eigens, mask = fixture()
    training = list(range(1, 9))
    history, target = model.training_view(arrays, training), model.public_view(arrays, 0)
    expected = model.choose(history, kernels, eigens, mask)
    baseline = model.prior(history, target)
    arrays["train_B"][0] = 1e8
    arrays["train_A"][0] = -1e8
    arrays["precision_B"][0] = 1e8
    repeated = model.choose(model.training_view(arrays, training), kernels, eigens, mask)
    assert json.dumps(expected, sort_keys=True) == json.dumps(repeated, sort_keys=True)
    assert set(target) == {"state_B", "state_available_B", "basal"}
    np.testing.assert_array_equal(baseline, model.prior(model.training_view(arrays, training), target))
    assert model.pairs_and_query(baseline) == model.pairs_and_query(model.prior(history, target))


def test_every_covariance_blocks_wrong_dose_and_remains_PSD():
    arrays, kernels, _, mask = fixture()
    fitted = model.fit(model.training_view(arrays, list(range(8))), kernels, mask)
    for covariance in fitted["matrices"].values():
        assert covariance[0, 11] == 0.
        assert np.linalg.eigvalsh(covariance).min() > -1e-10


def test_single_A_requires_prior_charge_and_no_unused_A_enters_posterior():
    seen = []
    request = dict(status="charged_before_release", measurement_units=1, query_A=3)
    assert run.reveal(request, lambda index: seen.append(index) or .2) == .2
    assert seen == [3]
    with pytest.raises(ValueError, match="prior_charge"):
        run.reveal(dict(request, status="unpaid"), lambda index: seen.append(index) or .2)
    assert seen == [3]
    arrays, kernels, eigens, mask = fixture()
    history, target = model.training_view(arrays, list(range(1, 9))), model.public_view(arrays, 0)
    fitted = model.fit(history, kernels, mask)
    base = model.prior(history, target)
    _, query, _ = model.pairs_and_query(base)
    observed = arrays["train_A"][0, query]
    result = model.predict(fitted, target, base, query, observed, eigens, alpha=.1)
    arrays["train_A"][0, np.arange(10) != query] = 1e8
    actual = model.predict(fitted, target, base, query, observed, eigens, alpha=.1)
    np.testing.assert_array_equal(result["mean"], actual["mean"])
    with pytest.raises(ValueError, match="paid_finite"):
        model.predict(fitted, target, base, query, None, eigens, alpha=.1)


def test_zero_and_unsupported_updates_fall_back_without_fake_noise_variance():
    arrays, kernels, eigens, mask = fixture()
    history, target = model.training_view(arrays, list(range(1, 9))), model.public_view(arrays, 0)
    fitted = model.fit(history, kernels, mask)
    base = model.prior(history, target)
    _, query, _ = model.pairs_and_query(base)
    zero = model.predict(fitted, target, base, query, None, eigens, alpha=0.)
    np.testing.assert_array_equal(zero["mean"], base)
    unsupported = dict(target, basal=fitted["basal_centre"].copy())
    result = model.predict(fitted, unsupported, base, query, 1e3, eigens, alpha=1., gated=True)
    assert result["n_eff"] == result["alpha_effective"] == 0.
    np.testing.assert_array_equal(result["mean"], base)
    assert zero["variance_A"] == fitted["matrices"]["empirical"][10 + query, 10 + query]


def test_tensor_product_adapter_matches_explicit_small_kronecker_ridge():
    arrays, kernels, eigens, mask = fixture()
    fitted = model.fit(model.training_view(arrays, list(range(4))), kernels, mask)
    target = model.public_view(arrays, 8)
    drug = kernels["knowledge"]
    cell = fitted["normalized_basal"] @ fitted["normalized_basal"].T
    coefficients = np.linalg.solve(np.kron(cell, drug) + np.eye(40) * 10., fitted["error_B"].ravel())
    expected = np.kron(model.cell_similarity(fitted, target)[None], drug) @ coefficients
    actual = model.adapter(fitted, target, eigens["knowledge"], 10.)
    np.testing.assert_allclose(actual, expected, atol=1e-12)
    np.testing.assert_array_equal(model.adapter(fitted, target, eigens["knowledge"], None), np.zeros(10))


def test_selective_abstention_keeps_initial_actions_and_does_not_erase_regret():
    base = np.arange(10., 0., -1)
    pairs, query, initial = model.pairs_and_query(base)
    changed = base.copy()
    changed[5] = changed[4] + .01
    prediction = dict(mean=changed, covariance=np.eye(10) * 100., alpha_effective=.1, innovation=1.,
        innovation_z=.1, n_eff=4., support_factor=1., outlier_factor=1., predicted_A=0., variance_A=1.)
    committed = model.commit(prediction, base, pairs, initial, 1., selective=True)
    assert committed["selected"] == initial and not committed["swap_accepted"]
    assert all(value is None for value in committed["pair_decisions"])
    row = dict(committed, pairs=pairs, initial_selected=initial)
    outcomes = -base
    scored = run.score(row, changed, outcomes)
    assert scored["pair_regret"] > 0.
    assert scored["selective_coverage"] == 0.


def test_pair_variance_and_stable_tie_probabilities_use_one_SD_inflation():
    arrays, kernels, eigens, mask = fixture()
    history, target = model.training_view(arrays, list(range(8))), model.public_view(arrays, 8)
    fitted = model.fit(history, kernels, mask)
    base = model.prior(history, target)
    pairs, query, initial = model.pairs_and_query(base)
    result = model.predict(fitted, target, base, query, .1, eigens, alpha=.25)
    cross = fitted["matrices"]["empirical"][:10, 10 + query]
    variance = fitted["matrices"]["empirical"][10 + query, 10 + query]
    np.testing.assert_allclose(result["covariance"], fitted["matrices"]["empirical"][:10, :10]
                               - .25 * np.outer(cross, cross) / variance, atol=1e-12)
    delta, pairvariance, probability = model.pair_diagnostics(result, pairs, scale=2.)
    np.testing.assert_allclose(probability, model.norm.cdf(delta / np.sqrt(pairvariance * 4.)))
