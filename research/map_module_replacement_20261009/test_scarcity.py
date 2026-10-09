import importlib.util
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("scarcity_study", HERE/"scarcity.py")
scarcity = importlib.util.module_from_spec(spec); spec.loader.exec_module(scarcity)


def fixture():
    rng = np.random.default_rng(7)
    state = rng.normal(size=(12, 10)); observed = np.arange(10)[None]*.01+.1*state
    arrays = dict(train_A=observed+rng.normal(scale=.03, size=observed.shape), train_B=observed,
        availability_A=np.ones_like(observed, bool), availability_B=np.ones_like(observed, bool),
        precision_B=np.ones_like(observed), state_B=state, state_available_B=np.ones_like(observed, bool))
    records = [dict(cid=str(i//2), smiles="C"*(i//2+1), dose=float(i%2+1), unit="uM") for i in range(10)]
    values = np.repeat(rng.normal(size=(5, 8)), 2, axis=0)
    kernels, _ = scarcity.candidate_kernels(records, dict(molecule256=values, knowledge1024=values*2))
    return arrays, kernels


def test_histories_are_nested_deterministic_and_exclude_held_and_incomplete():
    complete = [i for i in range(45) if i not in (31, 34)]
    first = scarcity.histories(complete, 7, 11)
    assert first == scarcity.histories(complete, 7, 11)
    assert set(first[4]) < set(first[8]) < set(first[16])
    assert all(7 not in train and 31 not in train and 34 not in train for train in first.values())
    assert first != scarcity.histories(complete, 7, 23)


def test_size4_position_folds_fit_only_train_and_have_minimum_covariance_support():
    arrays, kernels = fixture()
    choices, folds = scarcity.choose(arrays, [0, 3, 6, 9], kernels)
    assert [f["held"] for f in folds] == [[0, 9], [3], [6]]
    assert min(f["covariance_contexts"] for f in folds) == 2
    assert all(set(f["held"]).isdisjoint(f["train"]) for f in folds)
    poisoned = {key: value.copy() for key, value in arrays.items()}
    for key in ("train_A", "train_B", "precision_B"):
        poisoned[key][1] = 1e6
    assert scarcity.choose(poisoned, [0, 3, 6, 9], kernels) == (choices, folds)


def test_persisted_residual_factors_exactly_reconstruct_frozen_covariance():
    arrays, kernels = fixture(); train = [0, 3, 6, 9]
    expected, _, detail = scarcity.study.fitted(arrays, train, kernels)
    b, a = scarcity.residual_factors(arrays, train)
    actual, rho = scarcity.covariances(b, a, kernels)
    assert rho == detail["rho"]
    for arm in expected:
        np.testing.assert_array_equal(actual[arm], expected[arm])


def test_seed_averaging_is_the_context_inference_unit():
    rows = []
    for size in scarcity.SIZES:
        for cell in range(3):
            for seed in scarcity.SEEDS:
                for arm in ("no_screen", "empirical", *scarcity.ARMS):
                    rows.append(dict(history_size=size, context=cell, seed=seed, arm=arm,
                        terminal_B=float(cell+seed/100+(.1 if arm == "knowledge" else 0)),
                        initial_mse=1., posterior_mse=1., delta_vs_no_screen=0., harmful_replacements=0,
                        replacement_pairs=[], cost=5 if arm == "no_screen" else 13, eta=.5))
    summary = scarcity.summarize(rows)
    result = summary["paired_seed_mean_context_comparisons"]["8"]["empirical"]
    np.testing.assert_allclose(result["delta_B"], .1, atol=1e-14)
    assert result["improved_contexts"] == 3
    assert summary["history_sizes"]["8"]["knowledge"]["contexts"] == 3
    assert summary["history_sizes"]["8"]["knowledge"]["seed_episodes"] == 9
