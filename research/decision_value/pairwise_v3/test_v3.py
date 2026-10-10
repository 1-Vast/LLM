"""Counterexamples for label-free support and joint conditional residual repair."""
import numpy as np
import pytest
from threadpoolctl import threadpool_limits

from research.decision_value.pairwise_20261009 import model as base
from research.decision_value.pairwise_v3 import joint_residual as joint, run, support


@pytest.fixture(autouse=True)
def single_cpu_thread():
    with threadpool_limits(limits=1):
        yield


def fixture():
    rng = np.random.default_rng(71)
    state, basal = rng.normal(size=(12, 10)), rng.normal(size=(12, 7))
    B = state * .1 + np.arange(10)[None] * .01 + rng.normal(scale=.02, size=state.shape)
    A = B + rng.normal(scale=.04, size=state.shape)
    arrays = dict(train_A=A, train_B=B, precision_B=np.ones_like(B), state_B=state,
                  state_available_B=np.ones_like(B, dtype=bool), basal=basal)
    records = [dict(cid=str(i // 2), smiles="C" * (i // 2 + 1), dose=float(i % 2 + 1), unit="uM") for i in range(10)]
    vectors = np.repeat(rng.normal(size=(5, 8)), 2, axis=0)
    kernels, eigens, mask, _ = base.prepare_kernels(records, dict(molecule256=vectors, knowledge1024=vectors * 2))
    return arrays, kernels, eigens, mask, support.freeze_reference(basal)


def test_support_reference_is_label_free_and_survives_tiny_folds():
    arrays, _, _, _, reference = fixture()
    frozen = support.freeze_reference(arrays["basal"])
    arrays["train_A"][:] = 1e8
    arrays["train_B"][:] = -1e8
    repeated = support.freeze_reference(arrays["basal"])
    for key in ("centre", "scale", "reference_standardized"):
        np.testing.assert_array_equal(frozen[key], repeated[key])
    assert frozen["bandwidth_sq"] == repeated["bandwidth_sq"]
    gram, weights = support.cell_kernel(arrays["basal"][:2], arrays["basal"][3], reference)
    assert np.linalg.eigvalsh(gram).min() > 0 and np.all(weights > 0)
    diagnostic = support.assess(arrays["basal"][:2], arrays["basal"][3], reference)
    assert diagnostic["n_eff"] > 1 and diagnostic["weight"] > 0


def test_distribution_distance_attenuates_uniform_tiny_weight_false_support():
    arrays, _, _, _, reference = fixture()
    history = arrays["basal"][:4]
    nearby = support.assess(history, history[0], reference)
    distant = support.assess(history, np.full(7, 1e5), reference)
    assert distant["distance_ratio"] > nearby["distance_ratio"]
    assert distant["weight"] < nearby["weight"] * 1e-6
    with pytest.raises(ValueError, match="finite_matched"):
        support.assess(history, np.full(7, np.nan), reference)


def test_joint_true_LOO_mean_excludes_own_A_B_and_precision_labels():
    arrays, kernels, eigens, mask, reference = fixture()
    history = base.training_view(arrays, list(range(8)))
    original = joint.fit(history, kernels, eigens, mask, reference, "knowledge")
    poisoned = {key: value.copy() for key, value in history.items()}
    poisoned["train_A"][2] += 1e4
    poisoned["train_B"][2] -= 2e4
    poisoned["precision_B"][2] = 1e8
    actual = joint.fit(poisoned, kernels, eigens, mask, reference, "knowledge")
    np.testing.assert_array_equal(original["loo_mean_A"][2], actual["loo_mean_A"][2])
    np.testing.assert_array_equal(original["loo_mean_B"][2], actual["loo_mean_B"][2])
    np.testing.assert_allclose(actual["error_A"][2] - original["error_A"][2], 1e4)
    np.testing.assert_allclose(actual["error_B"][2] - original["error_B"][2], -2e4)


def test_singleton_adapter_and_two_row_residual_fit_have_no_empty_training():
    arrays, kernels, eigens, mask, reference = fixture()
    singleton = base.training_view(arrays, [0])
    target = base.public_view(arrays, 3)
    fitted = joint.fit_mean(singleton, eigens, reference, "knowledge")
    actual = joint.mean(fitted, target, eigens, reference)
    expected = joint.baseline(singleton, target)
    np.testing.assert_array_equal(actual[0], expected[0])
    np.testing.assert_array_equal(actual[1], expected[1])
    two = joint.fit(base.training_view(arrays, [0, 1]), kernels, eigens, mask, reference, "knowledge")
    assert np.isfinite(two["error_A"]).all() and np.isfinite(two["error_B"]).all()
    np.testing.assert_array_equal(two["loo_mean_B"], two["baseline_loo_B"])


def test_joint_tensor_adapters_match_explicit_A_and_B_kronecker_ridge():
    arrays, kernels, eigens, _, reference = fixture()
    history, target = base.training_view(arrays, list(range(4))), base.public_view(arrays, 8)
    fitted = joint.fit_mean(history, eigens, reference, "knowledge")
    corrected = joint.mean(fitted, target, eigens, reference)
    baseline = joint.baseline(history, target)
    error_B, error_A, _, _ = joint.baseline_bank(history)
    gram, weights = support.cell_kernel(history["basal"], target["basal"], reference)
    matrix = np.kron(gram, kernels["knowledge"]) + np.eye(40) * 10.
    projected = np.kron(weights[None], kernels["knowledge"])
    for observed, original, error in zip(corrected, baseline, (error_B, error_A)):
        expected = original + projected @ np.linalg.solve(matrix, error.ravel())
        np.testing.assert_allclose(observed, expected, atol=1e-12)


def test_old_and_refit_covariance_are_PSD_dose_bound_and_include_noise_once():
    arrays, kernels, eigens, mask, reference = fixture()
    fitted = joint.fit(base.training_view(arrays, list(range(8))), kernels, eigens, mask, reference, "knowledge")
    errors = np.concatenate([fitted["error_B"], fitted["error_A"]], axis=1)
    moment = errors.T @ errors / len(errors)
    expected = (.5 * moment + .5 * np.diag(np.diag(moment)) + np.eye(20) * 1e-12) * np.tile(mask, (2, 2))
    np.testing.assert_array_equal(fitted["refit_matrices"]["empirical"], expected)
    for matrices in (fitted["old_matrices"], fitted["refit_matrices"]):
        for covariance in matrices.values():
            assert covariance[0, 11] == 0.
            assert np.linalg.eigvalsh(covariance).min() > -1e-10


def test_feedback_uses_corrected_A_mean_and_only_purchased_A_value():
    arrays, kernels, eigens, mask, reference = fixture()
    history, target = base.training_view(arrays, list(range(8))), base.public_view(arrays, 8)
    fitted = joint.fit(history, kernels, eigens, mask, reference, "knowledge")
    before_B, before_A = joint.mean(fitted, target, eigens, reference)
    query = base.pairs_and_query(joint.baseline(history, target)[0])[1]
    # A observation equal to corrected expectation must cause zero innovation.
    observed = float(before_A[query])
    result = joint.predict(fitted, target, query, observed, eigens, reference,
                           representation="knowledge", eta=.5, alpha=.1)
    assert result["innovation"] == 0. and result["predicted_A"] == observed
    np.testing.assert_array_equal(result["mean"], before_B)
    arrays["train_A"][8] = 1e8
    arrays["train_B"][8] = -1e8
    repeated = joint.predict(fitted, target, query, observed, eigens, reference,
                             representation="knowledge", eta=.5, alpha=.1)
    np.testing.assert_array_equal(result["mean"], repeated["mean"])
    with pytest.raises(ValueError, match="paid_finite"):
        joint.predict(fitted, target, query, None, eigens, reference, alpha=.1)


def test_zero_update_and_underflow_support_preserve_covariance():
    arrays, kernels, eigens, mask, reference = fixture()
    history, target = base.training_view(arrays, list(range(8))), base.public_view(arrays, 8)
    fitted = joint.fit(history, kernels, eigens, mask, reference, "knowledge")
    query = 2
    zero = joint.predict(fitted, target, query, None, eigens, reference, alpha=0.)
    np.testing.assert_array_equal(zero["covariance"], fitted["refit_matrices"]["empirical"][:10, :10])
    distant = dict(target, basal=np.full(7, 1e8))
    no_support = joint.predict(fitted, distant, query, 1e3, eigens, reference, alpha=.1)
    assert no_support["alpha_effective"] == 0.
    np.testing.assert_array_equal(no_support["covariance"], zero["covariance"])
    invalid = dict(target, state_available_B=np.zeros(10, dtype=bool))
    with pytest.raises(ValueError, match="complete_target_STATE"):
        joint.mean(fitted, invalid, eigens, reference)


def test_real_commit_phase_charges_shared_A_and_stops_zero_alpha_without_B_asset(tmp_path, monkeypatch):
    arrays, kernels, eigens, mask, reference = fixture()
    history, target = base.training_view(arrays, list(range(8))), base.public_view(arrays, 8)
    fits = {rep: joint.fit(history, kernels, eigens, mask, reference, rep) for rep in run.REPRESENTATIONS}
    prior, _ = joint.baseline(history, target)
    pairs, _, initial = base.pairs_and_query(prior)
    query, key = 7, 'synthetic__seed11__n8'
    selected = {arm: dict(alpha=.1, eta=0.) for arm in
                ('knowledge_old', 'knowledge_refit_empirical', 'knowledge_refit_map',
                 'molecule_refit_map', 'Morgan_refit_map', 'permutedknowledge_refit_map')}
    # The main matched-information arm still buys A at alpha0; only prebuy_stop skips it.
    selected['knowledge_refit_map'] = dict(alpha=0., eta=.5)
    configurations = run.configurations(selected)
    choices = dict(configurations=configurations,
                   probability_scales={arm: 1. for arm in run.ARMS}, descriptors={})
    prepared = {}
    for arm, configuration in configurations.items():
        descriptor = run.descriptor(fits, history, target, pairs, query, eigens, reference, configuration)
        for name in ('mean_before', 'gain', 'pair_variance', 'pair_reduction'):
            prepared[key + '__' + arm + '__' + name] = descriptor.pop(name)
        choices['descriptors'][arm] = descriptor
    out, packet, source = tmp_path / 'output', tmp_path / 'packet', tmp_path / 'source'
    for directory in (out, packet, source):
        directory.mkdir()
    # A genuinely absent evaluation asset catches accidental B access in the phase.
    np.savez(packet / 'training_arrays.npz', train_A=arrays['train_A'])
    run.write(source / 'FREEZE.json', dict(inputs={}))
    np.savez_compressed(out / 'PRE_A_ARRAYS.npz', **prepared)
    run.write(out / 'PLANS.json', [dict(episode=key, context=8, seed=11, history_size=8,
        history_ids=list(range(8)), pairs=pairs, query_A=query, initial_selected=initial)])
    run.write(out / 'CHOICES.json', {key: choices})
    monkeypatch.setattr(run, 'PACKET', packet)
    monkeypatch.setattr(run, 'HERE', source)
    run.freeze(out, 'PRE_A_FREEZE.json', ['PRE_A_ARRAYS.npz', 'PLANS.json', 'CHOICES.json'])
    original_reveal, releases = run.previous.reveal, []

    def paid_reveal(request, buy):
        requests = run.read(out / 'POLICY_REQUESTS.json')
        assert len(requests) == 10
        assert sum(row['A_units'] for row in requests) == 7
        assert all(row['query_A'] == query for row in requests)
        releases.append(request['query_A'])
        return original_reveal(request, buy)

    monkeypatch.setattr(run.previous, 'reveal', paid_reveal)
    run.commit(out)
    assert releases == [query] and len(run.read(out / 'A_RECEIPTS.json')) == 1
    commitments = run.read(out / 'COMMITMENTS.json')
    assert len(commitments) == 10
    lookup = {row['arm']: row for row in commitments}
    for arm, row in lookup.items():
        stopped = arm in ('no_update', 'knowledge_mean', 'knowledge_prebuy_stop')
        assert row['cost'] == (5 if stopped else 6)
        assert row['A_released'] == (not stopped)
        assert row['purchased_A'] == ([] if stopped else [query])
        assert len(row['selected']) == len(set(row['selected'])) == 5
        assert set(row['selected']).issubset(range(10))
    value = arrays['train_A'][8, query]
    with np.load(out / 'PREDICTIONS.npz') as predictions:
        for arm in ('knowledge_strong_shrink', 'knowledge_old'):
            cfg = configurations[arm]
            expected = joint.predict(fits['knowledge'], target, query, value, eigens, reference,
                residual_kind=cfg['residual_kind'], representation=cfg['representation'], eta=cfg['eta'], alpha=cfg['alpha'])
            np.testing.assert_allclose(predictions[key + '__' + arm], expected['mean'], atol=1e-12)
            _, variance, _ = base.pair_diagnostics(expected, pairs)
            np.testing.assert_allclose(lookup[arm]['pair_variances'], variance, atol=1e-12)
            assert lookup[arm]['alpha_effective'] == expected['alpha_effective']
    run.validate(out / 'PRE_A_FREEZE.json', out)
    run.validate(out / 'COMMITMENT_FREEZE.json', out)


def test_all_tie_summary_and_feedback_flips_use_conditional_mean_baseline():
    import json
    prior = np.arange(10., 0., -1)
    pairs, _, initial = base.pairs_and_query(prior)
    before = prior.copy()
    before[5] = before[4] + 1.
    unchanged = run.relative_flips(before, before, np.ones(10), pairs)
    assert unchanged['total'] == 0
    to_prior = run.relative_flips(prior, before, np.ones(10), pairs)
    assert to_prior['total'] > 0 and to_prior['ambiguous'] == to_prior['total']
    prediction = dict(mean=prior, covariance=np.eye(10), alpha_effective=0., innovation=0.,
        innovation_z=None, n_eff=4., support_factor=1., outlier_factor=1., predicted_A=0., variance_A=1.)
    committed = base.commit(prediction, prior, pairs, initial, 1.)
    metrics = run.previous.score(dict(committed, pairs=pairs, initial_selected=initial), prior, np.ones(10))
    rows = []
    for size in base.SIZES:
        for context in (0, 1):
            for arm in run.ARMS:
                rows.append(dict(episode=f'ref{context}__seed11__n{size}', context=context, history_size=size,
                    arm=arm, cost=5, purchased_A=[], alpha_effective=0., configuration=dict(eta=0.),
                    feedback_relative_mean=unchanged, **metrics))
    summary = run.summarize(rows)
    for size in base.SIZES:
        for arm in run.ARMS:
            group = summary['history_sizes'][str(size)][arm]
            assert group['brier'] is None and group['brier_defined_episodes'] == 0
            assert group['pair_regret'] == 0 and group['feedback_flips'] == 0
    assert not summary['transfer_gate'] and not summary['knowledge_specific_gate']
    json.dumps(summary, allow_nan=False)


def test_real_prepare_commit_evaluate_phases_preserve_target_outcome_separation(tmp_path, monkeypatch):
    arrays, kernels, eigens, mask, reference = fixture()
    arrays['availability_A'] = np.ones_like(arrays['train_A'], dtype=bool)
    arrays['availability_B'] = np.ones_like(arrays['train_B'], dtype=bool)
    out, packet, source = tmp_path / 'output', tmp_path / 'packet', tmp_path / 'source'
    packet.mkdir()
    source.mkdir()
    run.write(source / 'FREEZE.json', dict(inputs={}))
    np.savez(packet / 'training_arrays.npz', **arrays)
    monkeypatch.setattr(base, 'SIZES', (4, 8))
    monkeypatch.setattr(base, 'SEEDS', (11,))
    monkeypatch.setattr(run, 'PACKET', packet)
    monkeypatch.setattr(run, 'HERE', source)
    monkeypatch.setattr(run, 'reference', lambda: reference)
    monkeypatch.setattr(run.previous, 'public_kernels', lambda: (kernels, eigens, mask, {}))
    run.prepare(out, pilot=True)
    plans = run.read(out / 'PLANS.json')
    assert len(plans) == 2 and {plan['history_size'] for plan in plans} == {4, 8}
    assert all(plan['context'] not in plan['history_ids'] for plan in plans)
    frozen_prior = run.sha(out / 'PRE_A_FREEZE.json')
    # Commit really cannot obtain evaluator B: its source contains only A.
    np.savez(packet / 'training_arrays.npz', train_A=arrays['train_A'])
    run.commit(out)
    assert len(run.read(out / 'COMMITMENTS.json')) == 20
    assert run.sha(out / 'PRE_A_FREEZE.json') == frozen_prior
    committed = run.sha(out / 'COMMITMENT_FREEZE.json')
    # Evaluator really needs no unpurchased A: its source contains only B.
    np.savez(packet / 'training_arrays.npz', train_B=arrays['train_B'])
    run.evaluate(out)
    results, summary = run.read(out / 'RESULTS.json'), run.read(out / 'SUMMARY.json')
    assert len(results) == 20 and set(summary['history_sizes']) == {'4', '8'}
    assert run.sha(out / 'COMMITMENT_FREEZE.json') == committed
    assert all(len(row['selected']) == 5 for row in results)
    assert all(row['context_units'] == 1 and row['context_95CI'] is None
               for row in summary['primary_transfer_comparisons'].values())
