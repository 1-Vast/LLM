import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("module_replacement", HERE/"run.py")
study = importlib.util.module_from_spec(spec); spec.loader.exec_module(study)
kernel = sys.modules["kernel"]


def fixture():
    rng = np.random.default_rng(7); n, candidates = 12, 10
    state = rng.normal(size=(n, candidates)); observed = np.arange(candidates)[None]*.01+.1*state
    arrays = dict(train_A=observed+rng.normal(scale=.03, size=observed.shape), train_B=observed,
                  availability_A=np.ones_like(observed, bool), availability_B=np.ones_like(observed, bool),
                  precision_B=np.ones_like(observed), state_B=state, state_available_B=np.ones_like(observed, bool))
    records = [dict(cid=str(i//2), smiles="C"*(i//2+1), dose=float(i%2+1), unit="uM") for i in range(candidates)]
    feature = np.repeat(rng.normal(size=(5, 8)), 2, axis=0)
    kernels, metadata = kernel.candidate_kernels(records, dict(molecule256=feature, knowledge1024=feature*2))
    return arrays, records, kernels, metadata


def test_kernels_are_PSD_dose_matched_and_whole_identity_permuted():
    _, records, kernels, metadata = fixture()
    for value in kernels.values():
        np.testing.assert_allclose(np.diag(value), 1.)
        assert np.linalg.eigvalsh(value).min() > -1e-10
        assert value[0, 1] == 0 and value.shape == (10, 10)
    assert len(metadata["permutation"]) == 5
    assert len(set(metadata["permutation"])) == 5
    records[0]["smiles"] = "not_a_smiles"
    with pytest.raises(ValueError, match="canonical"):
        kernel.candidate_kernels(records, dict(molecule256=np.ones((10, 2)), knowledge1024=np.ones((10, 2))))


def test_covariances_share_diagonals_and_eta0_exactly_restores_empirical():
    arrays, _, kernels, _ = fixture()
    matrices, current_offset, _ = study.fitted(arrays, list(range(10)), kernels)
    for name, value in matrices.items():
        np.testing.assert_allclose(np.diag(value), np.diag(matrices["empirical"]), atol=1e-14)
        assert np.linalg.eigvalsh(value).min() > 0
        np.testing.assert_array_equal(kernel.blend(matrices["empirical"], value, 0.), matrices["empirical"])


def test_outer_excluded_outcomes_do_not_change_fit_choice_or_prior():
    arrays, _, kernels, _ = fixture(); train = list(range(1, 12))
    original, detail = study.choose(arrays, train, kernels)
    old, old_offset, _ = study.fitted(arrays, train, kernels)
    prediction = study.prior(arrays, train, 0)
    poisoned = {key: value.copy() for key, value in arrays.items()}
    for key in ("train_A", "train_B", "precision_B"):
        poisoned[key][0] = 1e6
    assert study.choose(poisoned, train, kernels) == (original, detail)
    new, new_offset, _ = study.fitted(poisoned, train, kernels)
    np.testing.assert_array_equal(new_offset, old_offset)
    for arm in old:
        np.testing.assert_array_equal(new[arm], old[arm])
    np.testing.assert_array_equal(study.prior(poisoned, train, 0), prediction)


def test_batch_posterior_equals_sequential_paid_same_information():
    arrays, _, kernels, _ = fixture(); train = list(range(1, 12))
    matrices, current_offset, _ = study.fitted(arrays, train, kernels)
    prediction = study.prior(arrays, train, 0); schedule = kernel.boundary_schedule(prediction)
    for covariance in matrices.values():
        result = study.posterior.replay(prediction, current_offset, covariance, lambda i: arrays["train_A"][0, i], schedule=schedule)
        batch = kernel.conditional_mean(prediction, current_offset, covariance, schedule, arrays["train_A"][0, schedule])
        np.testing.assert_allclose(batch, result["posterior_mean_B"], atol=1e-12)
        assert result["purchased_A"] == schedule and result["cost"] == 13


def test_incomplete_contexts_are_masked_mean_inputs_not_covariance_rows():
    arrays, _, kernels, _ = fixture()
    arrays["availability_A"][0, 0] = False; arrays["availability_B"][0, 0] = False
    matrices, current_offset, detail = study.fitted(arrays, list(range(12)), kernels)
    assert detail["mean_contexts"] == 12 and detail["covariance_contexts"] == 11
    assert 0 not in detail["residual_cells"] and np.isfinite(current_offset).all()


def test_unit_mismatch_blocks_transfer_and_insufficient_covariance_support_refuses():
    arrays, records, _, _ = fixture()
    records[2]["unit"] = "nM"
    features = np.repeat(np.arange(1., 41.).reshape(5, 8), 2, axis=0).astype("float32")
    kernels, _ = kernel.candidate_kernels(records, dict(molecule256=features, knowledge1024=features))
    for matrix in kernels.values():
        assert matrix[0, 2] == 0
        assert np.linalg.eigvalsh(matrix).min() > -1e-12
    arrays["availability_A"][:] = False; arrays["availability_A"][0] = True
    with pytest.raises(ValueError, match="two_complete"):
        study.fitted(arrays, list(range(12)), kernels)
