"""Synthetic tests only: no official functional archive is opened by pytest."""
import json

import pytest

from worker import FLAGS, IDENTITY, missing, project_rows
from census import join_flags, temporal_census


def row(**updates):
    value = dict(zip(IDENTITY, ["005001", "01", "1", "drug", "Human", "Female", "2 hr", "0.10", "μM", "Low"]))
    value.update({"DNA(%)": "77.123456789", "LDH(%)": "88.987654321"})
    value.update(updates)
    return value


def test_whitelist_preserves_identity_and_never_exports_response():
    exported, counts = project_rows([row()])
    assert set(exported[0]) == set(IDENTITY + FLAGS)
    assert exported[0]["EXP_ID"] == "005001"
    assert exported[0]["GROUP_ID"] == "01"
    assert exported[0]["DOSE"] == "0.10"
    serialized = json.dumps([exported, counts])
    assert "77.123456789" not in serialized
    assert "88.987654321" not in serialized
    assert all(type(exported[0][f]) is bool for f in FLAGS)


@pytest.mark.parametrize("token", ["", " ", " n/A ", "NaN", "NULL", "none", "--", "no data", "not available"])
def test_declared_missing(token):
    assert missing(token)


@pytest.mark.parametrize("token", ["0", "0.0", " -0 ", "77.123456789", "NOT_NUMERIC_BUT_NONMISSING"])
def test_zero_and_unknown_are_nonmissing(token):
    exported, _ = project_rows([row(**{"DNA(%)": token})])
    assert not exported[0]["DNA_missing"]


def test_duplicate_conflict_does_not_choose_or_merge_rows():
    a, b = row(), row(**{"DNA(%)": "66.012345678", "LDH(%)": "NULL"})
    exported, counts = project_rows([a, b])
    assert len(exported) == 2
    assert counts["all_source_unique_keys"] == 1
    assert all(r["DNA_conflict"] for r in exported)
    assert not any(r["LDH_conflict"] for r in exported)
    assert [r["LDH_missing"] for r in exported] == [False, True]
    assert "66.012345678" not in json.dumps(exported)


def test_exact_raw_string_disagreement_and_identity_conflict_are_explicit():
    exported, _ = project_rows([row(**{"DNA(%)": "100"}), row(DOSE="0.1", **{"DNA(%)": "100.0"})])
    assert all(r["DNA_conflict"] and r["identity_conflict"] for r in exported)
    assert {r["DOSE"] for r in exported} == {"0.10", "0.1"}


def test_nonhuman_outcomes_never_exported():
    exported, counts = project_rows([row(SPECIES="Rat")])
    assert exported == []
    assert counts["all_source_rows"] == counts["nonhuman_source_rows"] == 1


@pytest.mark.parametrize("bad", [row(EXTRA="forbidden-response"), {k: v for k, v in row().items() if k != "DOSE"}, row(**{"DNA(%)": None})])
def test_malformed_or_extra_fields_fail_without_value_echo(bad):
    with pytest.raises(ValueError) as error:
        project_rows([bad])
    assert "77.123456789" not in str(error.value)
    assert "forbidden-response" not in str(error.value)


def test_same_key_with_different_dose_does_not_count_as_pair():
    cell = {c: row()[c] for c in IDENTITY}
    cell["BARCODE"] = "0012345"
    attrs = [dict(cell)]
    functional, _ = project_rows([row(DOSE="0.1")])
    joined, mismatches = join_flags([cell], attrs, functional)
    assert joined[0]["CEL_identity_and_barcode_match"]
    assert not joined[0]["functional_identity_match"]
    assert not joined[0]["DNA_nonmissing_unconflicted"]
    assert mismatches[0]["functional_mismatch_fields"] == ["DOSE"]


def test_barcode_mismatch_and_missing_function_cannot_be_complete_menu():
    cells, attrs, functional = [], [], []
    for index, time in enumerate(["2 hr", "8 hr", "24 hr"]):
        item = row(GROUP_ID=f"{index + 1:02}", SACRIFICE_PERIOD=time)
        projected, _ = project_rows([item])
        cell = {c: item[c] for c in IDENTITY}
        cell["BARCODE"] = f"00{index}"
        cells.append(cell)
        attrs.append({**cell, "BARCODE": "WRONG" if index == 2 else cell["BARCODE"]})
        if index != 0:
            functional.extend(projected)
    joined, _ = join_flags(cells, attrs, functional)
    counts = temporal_census(joined)
    assert counts["all_identity_samples"]["at_least_one_per_time_conditions"] == 1
    assert counts["CEL_and_both_nonmissing"]["at_least_one_per_time_conditions"] == 0
    assert not joined[0]["DNA_nonmissing_unconflicted"]
    assert not joined[2]["CEL_identity_and_barcode_match"]
