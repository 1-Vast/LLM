"""Scientific boundary and observation-only tracing contracts."""
import numpy as np
import pytest
import torch
import subprocess

from research.astra.zero_audit import (
    activation_observer, choice, endpoint_index, execute_replay, numbers, paired_contrasts, policy_diagnostics,
)


@pytest.mark.parametrize("axis", [["unknown"] * 2000, ["0546:EGR1"] * 2000, ["0546:EGR1"]])
def test_missing_ambiguous_or_wrong_axis_never_becomes_zero(axis):
    with pytest.raises(ValueError, match="never substitute zero"):
        endpoint_index(axis)


@pytest.mark.parametrize("value", [[], [float("nan")], [float("inf")]])
def test_invalid_readout_never_becomes_zero(value):
    with pytest.raises(ValueError, match="never substitute zero"):
        numbers(value)


def test_zero_mean_cancellation_is_distinct_from_all_zero_and_display_rounding():
    assert numbers(np.array([-1., 1.]))["exact_zeros"] == 0
    exact = numbers(np.zeros(16, dtype=np.float32))
    assert exact["exact_zeros"] == 16 and exact["mean_float64"] == 0
    tiny = numbers(np.array([1e-12], dtype=np.float32))
    assert tiny["exact_zeros"] == 0 and tiny["float_hex"] != exact["float_hex"][:1]


class Model:
    def __init__(self):
        self.relu = torch.nn.ReLU()

    def predict_step(self, batch):
        return {"preds": self.relu(batch["ctrl_cell_emb"])}


def test_observer_preserves_prediction_rng_input_and_hooks():
    model, records = Model(), []
    value = torch.tensor([[-2., 3.], [-1., 0.]])
    batch = {"ctrl_cell_emb": value, "pert_name": ["A", "A"]}
    original, rng = Model.predict_step, torch.random.get_rng_state().clone()
    expected = model.predict_step(batch)["preds"].clone()
    with activation_observer(Model, records, endpoint=0):
        actual = model.predict_step(batch)["preds"]
    assert torch.equal(expected, actual) and torch.equal(rng, torch.random.get_rng_state())
    assert torch.equal(value, torch.tensor([[-2., 3.], [-1., 0.]]))
    assert Model.predict_step is original and not model.relu._forward_hooks
    assert records[0]["pre_EGR1"]["negative"] == 2
    assert records[0]["post_EGR1"]["exact_zeros"] == 2


@pytest.mark.parametrize("failure", ["backend", "changed_output", "duplicate_relu"])
def test_observer_failure_restores_class_and_module_hooks(failure):
    class Failed(Model):
        def predict_step(self, batch):
            result = super().predict_step(batch)
            if failure == "backend":
                raise RuntimeError("backend failure")
            if failure == "changed_output":
                result["preds"] = result["preds"] + 1
            if failure == "duplicate_relu":
                self.relu(batch["ctrl_cell_emb"])
            return result
    model, original = Failed(), Failed.predict_step
    with pytest.raises((ValueError, RuntimeError)):
        with activation_observer(Failed, [], endpoint=0):
            model.predict_step({"ctrl_cell_emb": torch.tensor([[-1., 2.]]), "pert_name": ["A"]})
    assert Failed.predict_step is original and not model.relu._forward_hooks


def test_fixed_pair_linear_average_cannot_escape_tolerance():
    utilities = np.array([[0., 5e-7, -1.], [0., -5e-7, -1.], [0., 1e-6, -1.]])
    pair = paired_contrasts(utilities, True)[0]
    assert pair["every_seed_within_numeric_tolerance"] and pair["fixed_pair_convexity_pass"]
    with pytest.raises(ValueError, match="paired basals"):
        paired_contrasts(utilities, False)


def test_changing_tied_pairs_can_create_unique_aggregate_winner():
    utilities = np.array([[0., 0., -.03], [-.003, 0., 0.], [-.15, 0., 0.]])
    assert all(choice(row)["selected"] is None for row in utilities)
    assert choice(utilities.mean(axis=0))["selected"] == 1
    assert all(c["fixed_pair_convexity_pass"] for c in paired_contrasts(utilities, True))


def test_nonlinear_utility_aggregation_requires_estimand():
    draws = np.array([0., 2.])
    utility = lambda y: np.square(y)
    assert utility(draws.mean()) != utility(draws).mean()
    # The audited utility is linear; this equality must not generalize to above.
    assert -draws.mean() == (-draws).mean()


def test_numeric_ranking_does_not_certify_advantage_equivalence_or_terminal():
    rows = [dict(pool="plate10", seed=s, utilities=[-s / 100., 0., -.1],
                 choice=choice([-s / 100., 0., -.1]), paired_inputs_verified=True)
            for s in (17, 42, 103)]
    result = policy_diagnostics(rows)["plate10"]
    assert result["fixed_K_aggregate"]["selected"] == 1
    assert result["uncertainty_preserving"]["candidate_indices"] == [0, 1, 2]
    assert result["uncertainty_preserving"]["selected"] is None
    assert result["meaningful_delta"] is None and result["physical_CI"] is None
    assert result["realized_utility"] is None and result["refusal_contribution"] is None
    assert all(c["practical_equivalence"] == "unknown" for c in result["paired_contrasts"])
    assert result["prospective_inference_forwards"]["fixed_K_aggregate"] == 12
    assert result["prospective_inference_forwards"]["fixed_action"] == 0


@pytest.mark.parametrize("timeout", [False, True])
def test_failed_worker_retains_logs_without_claiming_validated_completion(tmp_path, monkeypatch, timeout):
    def failed(*args, **kwargs):
        if timeout:
            raise subprocess.TimeoutExpired("worker", 600, output=b"partial output", stderr=b"partial error")
        return subprocess.CompletedProcess("worker", 1, stdout="failed output", stderr="failed error")
    monkeypatch.setattr(subprocess, "run", failed)
    result = execute_replay(["worker"], tmp_path, tmp_path)
    assert result["subprocess_completed"] is (not timeout)
    assert not result["validated"] and not result["full_output_bitwise_equal"]
    assert result["returncode"] == (None if timeout else 1)
    assert (tmp_path / "stdout.txt").read_text() == ("partial output" if timeout else "failed output")
    assert (tmp_path / "stderr.txt").read_text() == ("partial error" if timeout else "failed error")
