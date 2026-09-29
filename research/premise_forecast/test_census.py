"""Census boundaries: signature tables are read by design column only; decisions follow the registered rule.

File summary
- Path: research/premise_forecast/test_census.py
- Purpose: pin the two properties the E-AG1 stage-0 census relies on. It never asks a signature
  table for a value or quality column, and its decision rule is the registered one (30 target-gene
  clusters). One data-backed test checks that the census reproduces the engagement_v1 MCF7 case
  under the same archetype rule; it skips when the releases are absent.
- Run: python -m pytest research/premise_forecast -q -p no:cacheprovider
"""
from __future__ import annotations

import pandas as pd
import pytest

from research.premise_forecast import census as CS


def test_signature_reads_are_design_columns_only(monkeypatch):
    for columns in CS.SIGINFO_COLUMNS.values():
        assert not set(columns) & CS.FORBIDDEN_COLUMNS
    requested = []
    real = pd.read_csv

    def spy(path, *args, **kwargs):
        name = str(path)
        if "sig_info" in name or "siginfo" in name:
            requested.append((name, kwargs.get("usecols")))
            if kwargs.get("usecols") is None:
                raise AssertionError(f"signature table read without usecols: {name}")
        return real(path, *args, **kwargs)

    monkeypatch.setattr(CS.pd, "read_csv", spy)
    for reader in (lambda: CS._geo_signatures(CS.GSE70138), CS._lincs2020_signatures):
        try:
            reader()
        except (FileNotFoundError, OSError):
            pytest.skip("signature metadata unavailable")
    assert requested and all(not set(cols) & CS.FORBIDDEN_COLUMNS for _, cols in requested)


def test_decision_rule_is_the_registered_threshold():
    assert CS.decide(29, 40, 0)["AG-G0_population"] == "NOT_READY"
    assert CS.decide(30, 0, 0)["AG-G0_population"] == "READY_FOR_STAGE1_PREREGISTRATION"
    assert CS.decide(0, 29, 0)["phenocopy_track"] == "INSUFFICIENT"
    assert CS.decide(0, 30, 0)["phenocopy_track"] == "CANDIDATE_TASK_FOR_A_DIFFERENT_PREMISE"
    assert CS.decide(0, 0, 19)["joint_task"] == "NOT_READY"


def test_census_reproduces_the_engagement_v1_mcf7_case():
    try:
        cases, _ = CS.discordance_cases(require_selective=False)
    except (FileNotFoundError, OSError) as exc:
        pytest.skip(f"premise releases unavailable: {exc}")
    gap = cases[cases.archetype == "engagement_gap_or_mode"]
    row = gap[(gap.depmap_id == "ACH-000019") & (gap.name == "AZD2014")]
    assert len(row) == 1 and row.target.iloc[0] == "MTOR"
    selective, _ = CS.discordance_cases(require_selective=True)
    assert not ((selective.depmap_id == "ACH-000019") & (selective.name == "AZD2014")
                & (selective.archetype == "engagement_gap_or_mode")).any()  # MTOR is pan-essential
