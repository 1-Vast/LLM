"""Synthetic checks for the zero-shot context study (no network, no checkpoint, no real labels)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import agent_policy as ap  # noqa: E402
import extract  # noqa: E402
import world_models as wm  # noqa: E402


def test_windows_cover_requested_rows_and_spans_are_exact():
    rows = np.array(list(range(100, 160)) + list(range(400, 900)))
    chosen = extract.choose(rows, 384, 6)
    assert len(chosen) == 384 and set(chosen) <= set(rows)
    covered = [r for a, b in extract.spans(chosen) for r in range(a, b + 1)]
    assert covered == sorted(chosen.tolist())
    small = np.arange(10, 30)
    assert extract.choose(small, 384, 6).tolist() == small.tolist()


def test_role_hash_is_deterministic_and_balanced():
    rows = np.arange(5000)
    a = extract.unit_hash("c99.h5ad", rows, "control-role")
    b = extract.unit_hash("c99.h5ad", rows, "control-role")
    assert np.array_equal(a, b)
    assert 0.45 < (a < 0.5).mean() < 0.55
    assert not np.array_equal(a, extract.unit_hash("c99.h5ad", rows, "half"))


def test_depth_corrected_error_is_unbiased_for_noisy_panel_mean():
    rng = np.random.default_rng(1)
    genes, lines, reps = 400, 30, 400
    truth_panel = rng.normal(0, 0.05, (lines, genes))
    target_truth = truth_panel.mean(0) + rng.normal(0, 0.03, genes)
    true_se = np.mean((truth_panel.mean(0) - target_truth) ** 2)
    sig_line, sig_target = 0.04, 0.02
    estimates = []
    for _ in range(reps):
        panel = truth_panel + rng.normal(0, sig_line, truth_panel.shape)
        obs = target_truth + rng.normal(0, sig_target, genes)
        pred = panel.mean(0)
        model_noise = lines * (1 / lines) ** 2 * sig_line ** 2
        estimates.append(wm.corrected_se(pred[None], obs[None], np.array([model_noise]), np.array([sig_target ** 2]))[0])
    assert abs(np.mean(estimates) - true_se) < 4 * np.std(estimates) / np.sqrt(reps)


def test_gaussian_update_matches_joint_conditioning():
    rng = np.random.default_rng(2)
    A = rng.normal(size=(5, 5))
    cov = A @ A.T + np.eye(5)
    mean = rng.normal(size=5)
    belief = ap.Belief(mean.copy(), cov.copy(), np.full(5, 0.3), obs_slope=0.8, obs_intercept=0.1)
    belief.update(2, 1.7)
    # Joint (y, o) with o = 0.1 + 0.8 y_2 + e
    h = np.zeros(5); h[2] = 0.8
    s = h @ cov @ h + 0.3
    k = cov @ h / s
    expect_mean = mean + k * (1.7 - (0.1 + h @ mean))
    expect_cov = cov - np.outer(k, h @ cov)
    assert np.allclose(belief.mean, expect_mean) and np.allclose(belief.cov, expect_cov)


def test_knowledge_gradient_prefers_uncertain_contender():
    mean = np.array([1.0, 0.95, -3.0])
    cov = np.diag([1e-6, 0.5, 0.5])
    belief = ap.Belief(mean, cov, np.full(3, 0.01))
    kg = ap.kg_values(belief, 1, {0, 1, 2})
    assert kg[1] > kg[2] >= 0 and kg[1] > kg[0]


def test_episode_never_reads_validation_values():
    belief = ap.Belief(np.zeros(4), np.eye(4), np.full(4, 0.1))
    seen = []
    flags, order = ap.run_episode(belief, np.array([0.5, 0.1, 0.2, 0.3]), 2, 2, ap.choose_ucb,
                                  on_purchase=lambda i: seen.append(i) or 0.4)
    assert seen == order and len(order) == 2 and len(flags) == 2


def test_guard_refuses_evaluation_without_matching_freeze(tmp_path, monkeypatch):
    monkeypatch.setattr(wm, "HERE", tmp_path)
    (tmp_path / "WORLD_PROTOCOL.json").write_text("{}")
    with pytest.raises(PermissionError):
        wm.guard([wm.SPLIT["evaluation"][0]])
    (tmp_path / "WORLD_FREEZE.json").write_text(json.dumps({"protocol_sha256": "0" * 64}))
    with pytest.raises(PermissionError):
        wm.guard([wm.SPLIT["evaluation"][0]])
    wm.guard([wm.SPLIT["development"][0]])  # development lines never need a freeze


def test_llm_policy_falls_back_to_kg_on_invalid_answer(tmp_path):
    from agent_llm import LLMAcquisition

    class Bad:
        provider_usage = {"calls": 1}
        def complete_json(self, messages, max_tokens=None):
            class R: model = "fake"; usage = {"prompt_tokens": 1, "completion_tokens": 1}
            return {"action": "screen", "id": 99}, R()

    belief = ap.Belief(np.array([1.0, 0.9, 0.0]), np.diag([0.01, 0.5, 0.5]), np.full(3, 0.05))
    cands = [{"drug": f"d{i}", "dose_uM": 5.0, "prior_mean": 0.0} for i in range(3)]
    policy = LLMAcquisition(Bad(), {"name": "X"}, cands, 1, tmp_path / "ledger.jsonl")
    choice = policy(belief, 1, {0, 1, 2}, 2, None)
    kg = ap.kg_values(belief, 1, {0, 1, 2})
    assert choice == max(kg, key=lambda i: (kg[i], -i))
    assert policy.receipts[-1]["status"] == "failed_fallback_kg"


def test_arm_runs_through_case_store_and_reveals_only_flags(tmp_path):
    import agent_eval as ae
    rng = np.random.default_rng(3)
    rows = []
    for i in range(12):
        rows.append({"label": f"[('Drug{i}', 5.0, 'uM')]", "drug": f"Drug{i}", "dose_uM": 5.0, "plate_A": "plate6",
                     "plate_B": "plate14", "y_A": float(rng.normal()), "y_B": float(rng.normal())})
    mean, sd = rng.normal(size=12), np.full(12, 0.5)
    res = ae.run_arm("A", "TEST-LINE", 0, rows, mean, sd, np.eye(12), (0.0, 1.0, 0.3), 3, 2, ap.choose_kg,
                     tmp_path / "A", "v1", "kg")
    assert len(res["flags"]) == 2 and len(res["screens"]) <= 3
    roles = [r["role"] for r in res["receipts"]]
    assert roles.count("validate") == 2 and roles.index("validate") >= roles.count("screen")
    assert res["V"] == pytest.approx(sum(r["y_B"] for r in rows if r["label"] in res["flags"]))
    assert res["budget"]["recorded_use"] == len(res["screens"]) + 2 and res["budget"]["reserved"] == 0
