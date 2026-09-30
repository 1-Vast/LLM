"""The Bayes-loss API is distinct from registered evidence termination."""
import gzip
import json

import pytest

from maestro.acquisition import OutcomeBranch, OutcomeForecast
from research.dual_core_followup.decision_contract import diagnose, digest, reference_probes


def forecast(h1, h2):
    return OutcomeForecast("assay", (OutcomeBranch("H1", h1, 20), OutcomeBranch("H2", h2, 20)), basis="synthetic")


@pytest.mark.parametrize("consequences", ({}, {"unresolved": frozenset(), "absent": frozenset()}))
def test_informative_noneliminating_reading_has_bayes_value_and_no_registered_terminal_value(consequences):
    value = diagnose(forecast({"unresolved": .9, "absent": .1}, {"unresolved": .1, "absent": .9}),
                     ("H1", "H2"), consequences)
    assert value["bayes_value"] == pytest.approx(.8)
    assert value["bayes_decision_sensitivity"] == 1
    assert value["noneliminating_bayes_gain"] == pytest.approx(.8)
    assert value["registered_attempt_gross_utility"] == 0
    assert value["registered_attempt_net_utility"] == -.02
    assert value["registered_attempt_p_correct"] == value["registered_attempt_p_wrong"] == 0
    assert value["registered_chosen"] is None
    assert value["bayes_positive_registered_stops"]


def test_same_noisy_elimination_forecast_retains_distinct_loss_and_reward_scales():
    value = diagnose(forecast({"matches_h1": .8, "matches_h2": .2},
                              {"matches_h1": .2, "matches_h2": .8}), ("H1", "H2"),
                     {"matches_h1": frozenset({"H2"}), "matches_h2": frozenset({"H1"})})
    assert value["bayes_value"] == pytest.approx(.6)
    assert value["registered_attempt_gross_utility"] == pytest.approx(.4)
    assert value["registered_attempt_p_wrong"] == pytest.approx(.2)
    assert value["registered_chosen"] == "assay"
    assert value["noneliminating_bayes_gain"] == 0


def bank_row(**changes):
    row = {"task": "fixture", "episode": "0|compound|H1|H2", "task_input": "frozen", "forecast": "reference",
           "compound": "compound", "h1": "H1", "h2": "H2", "action": "assay", "history": [],
           "channel": "probe", "available": True, "refusal": None,
           "content": {"branches": [], "version": "fixture", "basis": "synthetic", "refusal": None, "action": "assay"}}
    row.update(changes)
    row["input_sha256"] = digest({key: row[key] for key in
                                ("task_input", "forecast", "compound", "h1", "h2", "action", "history")})
    row["output_sha256"] = digest(row["content"])
    return row


def write_bank(path, rows):
    with gzip.open(path, "wt", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row) + "\n")


def test_bank_filter_removes_repeated_calls_controls_and_conditional_queries(tmp_path):
    path = tmp_path / "bank.jsonl.gz"
    chosen = bank_row()
    write_bank(path, [chosen, chosen, bank_row(channel="selector"), bank_row(forecast="permuted"),
                      bank_row(history=[["previous", "unresolved"]]), bank_row(available=False)])
    rows = list(reference_probes(path))
    assert len(rows) == 1 and rows[0]["input_sha256"] == chosen["input_sha256"]
    assert set(rows[0]) == {"task", "episode", "compound", "h1", "h2", "action", "input_sha256", "output_sha256", "content"}


def test_bank_content_hash_is_checked_before_diagnosis(tmp_path):
    path = tmp_path / "bank.jsonl.gz"
    row = bank_row()
    row["content"]["basis"] = "changed"
    write_bank(path, [row])
    with pytest.raises(ValueError, match="frozen_query_hash_mismatch"):
        list(reference_probes(path))
