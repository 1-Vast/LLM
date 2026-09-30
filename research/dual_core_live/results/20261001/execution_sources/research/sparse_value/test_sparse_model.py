"""Counterexamples for sparse, grouped, hypothesis-conditional reference forecasts."""
from __future__ import annotations

from types import SimpleNamespace
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model as M  # noqa: E402

EARLY = ("A549", 6.0, 10000.0)
LATE = ("A549", 24.0, 10000.0)


def make_model(monkeypatch, rows, *, groups=None, eliminates=True):
    """Rows are (compound, hypothesis, source reading or None, target reading)."""
    tables, outcomes = {}, {}
    for key, index in ((EARLY, 2), (LATE, 3)):
        present = [row for row in rows if row[index] is not None]
        tables[key] = SimpleNamespace(names=[r[0] for r in present], klass=[r[1] for r in present],
                                      detected=[r[index] != "undetected" for r in present])
        outcomes[key] = {(r[0], "H2" if r[1] == "H1" else "H1"): r[index] for r in present}
    monkeypatch.setattr(M.C, "loo_outcomes", lambda ft, key, *args: outcomes[key])
    return M.SparseReferenceModel(SimpleNamespace(tables=tables),
                                  {"floor": 0.1, "margin": 0.1, "eliminates": eliminates},
                                  groups or {r[0]: r[0] for r in rows})


def test_missing_paired_references_use_explicit_marginal_backoff(monkeypatch):
    model = make_model(monkeypatch, [("a", "H1", None, "eliminate_b"),
                                    ("b", "H2", None, "eliminate_b")])
    forecast = model.forecast(LATE, "H1", "H2", source=EARLY, observed_label=M.LABELS[3])
    assert forecast.refusal is None
    for branch in forecast.branches.values():
        assert branch.basis == "marginal_backoff"
        assert branch.local_support == 0 and branch.parent_support == 1
        assert sum(branch.alpha.values()) == pytest.approx(2.0)
        assert branch.p_correct == pytest.approx(0.5)


def test_no_target_references_are_unknown_not_a_zero_probability(monkeypatch):
    model = make_model(monkeypatch, [("a", "H1", "ambiguous", "eliminate_b"),
                                    ("b", "H2", "ambiguous", None)])
    forecast = model.forecast(LATE, "H1", "H2")
    assert forecast.refusal == "no_target_references:H2"
    assert forecast.branches == {}


def test_strong_local_measurements_dominate_adverse_parent_counts(monkeypatch):
    rows = [(f"{h}_local_{i}", h, "ambiguous", "eliminate_b") for h in ("H1", "H2") for i in range(30)]
    rows += [(f"{h}_parent_{i}", h, "undetected", "eliminate_a") for h in ("H1", "H2") for i in range(30)]
    model = make_model(monkeypatch, rows)
    branch = model.forecast(LATE, "H1", "H2", source=EARLY, observed_label=M.LABELS[2]).branches["H1"]
    assert branch.p_correct > 0.93
    assert branch.value_mean > 0.8
    assert branch.local_support == branch.parent_support == 30
    assert sum(branch.alpha.values()) == pytest.approx(32.0)


def test_high_wrong_risk_has_negative_signed_value(monkeypatch):
    rows = [(f"{h}_{i}", h, None, "eliminate_a") for h in ("H1", "H2") for i in range(10)]
    branch = make_model(monkeypatch, rows).forecast(LATE, "H1", "H2").branches["H1"]
    assert branch.value_mean == pytest.approx(branch.p_correct - 2 * branch.p_wrong)
    assert branch.value_mean < -1.5
    assert branch.wrong_upper95 > branch.p_wrong
    assert 0 < branch.value_variance < 1


def test_a_group_counts_once_and_aliases_cannot_enter_the_parent(monkeypatch):
    rows = [("a", "H1", "ambiguous", "eliminate_b"), ("alias", "H1", "undetected", "eliminate_a"),
            ("a2", "H1", "ambiguous", "eliminate_b"), ("p", "H1", None, "undetected"),
            ("b", "H2", "ambiguous", "eliminate_b")]
    groups = {"a": "g", "alias": "g", "a2": "g", "p": "p", "b": "b"}
    branch = make_model(monkeypatch, rows, groups=groups).forecast(
        LATE, "H1", "H2", source=EARLY, observed_label=M.LABELS[2]).branches["H1"]
    assert branch.local_compounds == ("a", "a2") and branch.local_groups == ("g",)
    assert branch.parent_compounds == ("p",) and branch.parent_groups == ("p",)
    assert branch.local_support == branch.parent_support == 1
    assert not set(branch.local_groups) & set(branch.parent_groups)
    assert sum(branch.alpha.values()) == pytest.approx(3.0)


def test_conflicting_compounds_in_one_group_share_one_unit_of_weight(monkeypatch):
    rows = [("a", "H1", None, "eliminate_b"), ("alias", "H1", None, "eliminate_a"),
            ("b", "H2", None, "eliminate_b")]
    model = make_model(monkeypatch, rows, groups={"a": "g", "alias": "g", "b": "b"})
    branch = model.forecast(LATE, "H1", "H2").branches["H1"]
    assert branch.parent_support == 1
    assert branch.alpha[M.LABELS[0]] == branch.alpha[M.LABELS[1]] == 1.0
    assert sum(branch.alpha.values()) == 3.0


def test_h2_correctness_maps_to_the_global_h2_label(monkeypatch):
    model = make_model(monkeypatch, [("a", "H1", "ambiguous", "eliminate_b"),
                                    ("b", "H2", "ambiguous", "eliminate_b")])
    forecast = model.forecast(LATE, "H1", "H2", source=EARLY, observed_label=M.LABELS[2])
    branch = forecast.branches["H2"]
    assert branch.basis == "local_only"
    assert branch.probabilities[M.LABELS[1]] == branch.p_correct == 0.5
    assert branch.probabilities[M.LABELS[0]] == branch.p_wrong == pytest.approx(1 / 6)


def test_absence_is_neutral_and_disabled_validator_uses_detection(monkeypatch):
    model = make_model(monkeypatch, [("a", "H1", "ambiguous", "eliminate_b"),
                                    ("b", "H2", "ambiguous", "undetected")], eliminates=False)
    forecast = model.forecast(LATE, "H1", "H2")
    assert forecast.branches["H1"].probabilities[M.LABELS[2]] == 0.5
    assert forecast.branches["H2"].probabilities[M.LABELS[3]] == 0.5
    assert forecast.branches["H1"].p_correct == forecast.branches["H2"].p_correct == pytest.approx(1 / 6)
    # The 0.5 priors are visible uncertainty, never counted as measured elimination outcomes.
    assert forecast.branches["H2"].alpha[M.LABELS[1]] == 0.5


def test_forecast_cache_ignores_unrelated_heldout_group_metadata(monkeypatch):
    class UnreadableHeldout:
        def __str__(self):
            raise AssertionError("held-out metadata was accessed")

    model = make_model(monkeypatch, [("a", "H1", None, "undetected"), ("b", "H2", None, "undetected")],
                       groups={"a": "a", "b": "b", "heldout": UnreadableHeldout()})
    first = model.forecast(LATE, "H1", "H2")
    assert model.forecast(LATE, "H1", "H2") is first
    with pytest.raises(ValueError, match="neutral"):
        model.forecast(LATE, "H1", "H2", source=EARLY, observed_label=M.LABELS[0])


def test_paired_only_ablation_does_not_borrow_parent_support(monkeypatch):
    pooled = make_model(monkeypatch, [("a", "H1", "ambiguous", "eliminate_b"),
                                     ("p", "H1", "undetected", "eliminate_a"),
                                     ("b", "H2", "ambiguous", "eliminate_b")])
    paired = M.SparseReferenceModel(pooled.ft, pooled.params, pooled.group_map, pooling=False)
    assert paired.forecast(LATE, "H1", "H2") == pooled.forecast(LATE, "H1", "H2")
    branch = paired.forecast(LATE, "H1", "H2", source=EARLY, observed_label=M.LABELS[2]).branches["H1"]
    assert branch.basis == "paired_only" and branch.p_correct == 0.5
    assert branch.alpha[M.LABELS[1]] == 0.5
    missing = paired.forecast(LATE, "H1", "H2", source=EARLY, observed_label=M.LABELS[3])
    assert missing.refusal.startswith("no_paired_references:H2:") and not missing.branches
