"""Contracts for metadata-only episode construction."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C
import episodes as E


def _data():
    key_a = ("A549", 24.0, 100.0)
    key_b = ("A549", 72.0, 100.0)
    return SimpleNamespace(index={key_a: {"heldout": 0, "reference": 1},
                                  key_b: {"heldout": 2, "reference": 3}}), key_a, key_b


def test_metadata_episode_menu_ignores_truth_columns():
    data, key_a, key_b = _data()
    first = C.metadata_episode_menu(data, (key_a, key_b), eligibility_keys=(key_b,))

    # The menu only receives condition metadata.  A truth table may be added or
    # changed after construction without changing the public candidate set.
    data.compounds = pd.DataFrame({"compound": ["heldout", "reference"],
                                   "klass": ["H1", "H2"]})
    before = first.eligible
    data.compounds.loc[data.compounds.compound == "heldout", "klass"] = "different_hidden_truth"
    second = C.metadata_episode_menu(data, (key_a, key_b), eligibility_keys=(key_b,))
    assert second.eligible == before == ("heldout", "reference")


def test_metadata_menu_accepts_a_manifest_universe_without_labels():
    data, key_a, key_b = _data()
    menu = C.metadata_episode_menu(data, (key_a, key_b), compounds=("heldout",))
    assert menu.keys == (key_a, key_b)
    assert menu.compounds == ("heldout",)


def test_episode_candidates_are_fixed_before_truth_is_attached():
    data, key_a, _ = _data()
    data.compounds = pd.DataFrame({"compound": ["heldout"], "klass": ["H1"], "fold": [0]})
    tier = C.Tier("B", (key_a,), ("H1", "H2"), ("heldout",))
    ctx = type("Context", (), {"data": data, "tier": tier})()
    first = {row[0] for row in E.episode_list(ctx, 0)}
    data.compounds.loc[:, "klass"] = "H2"
    second = {row[0] for row in E.episode_list(ctx, 0)}
    assert first == second == {"heldout"}


def test_metadata_tiers_do_not_require_an_outcome_label_table():
    data, key_a, key_b = _data()
    data.compounds = pd.DataFrame({"compound": ["heldout", "reference"]})
    tiers = C.metadata_tiers(data, {
        "tiers": {
            "B_line_dose": {"lines": ["A549"], "doses_nM": [100], "minimum_units_per_class": 1},
            "A_time_dose": {"lines": ["A549"], "time_hours": [24, 72], "doses_nM": [100],
                            "minimum_compounds_per_class_at_72h": 1},
        }
    })
    assert tiers["B"].compounds == ("heldout", "reference")
    assert tiers["A"].compounds == ("heldout", "reference")
    assert tiers["B"].pool == tiers["A"].pool == ()
