"""Focused regression tests for the sci-Plex pilot v2 repair (protocol v2).

Small adversarial counterexamples reproducing the v1 defects found in
research/dataset_discovery/PILOT_REVIEW.md, plus unit coverage of the shared
sciplex_v2_lib logic used by builder and QA.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.datasets.sciplex_v2_lib import (abs_above, build_gene_mapping, classify_two_intervention,
                                        is_missing, mapping_stats, parse_sheet_key_s2,
                                        parse_sheet_key_s4, strip_name_suffix)

import tools.datasets.qa_sciplex_pilot_v2 as qa_mod


# ---------------------------------------------------------------------------
# identity validation (review P1: unknown identity manufactured into a condition)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value", [None, float("nan"), np.nan, "nan", "NaN", "None", "", "   "])
def test_is_missing_catches_all_missing_forms(value):
    assert is_missing(value)


@pytest.mark.parametrize("value", ["control", "Abexinostat", "A549", 0, 0.5, "plate10"])
def test_is_missing_keeps_valid_identities(value):
    assert not is_missing(value)


def test_missing_identities_never_classified_as_vehicle():
    # 40-cell v1 failure mode: missing treatment/dose/cell must be unresolved, never a
    # 'nan::nan' vehicle condition.
    assert classify_two_intervention(None, None) == "unresolved_identity"
    assert classify_two_intervention("nan", "nan") == "unresolved_identity"
    assert classify_two_intervention("nan", "Abexinostat") == "unresolved_identity"


# ---------------------------------------------------------------------------
# complete two-intervention classification (review P1: 28 mislabeled conditions)
# ---------------------------------------------------------------------------

def test_agent2_only_not_vehicle_control():
    # The exact v1 misclassification: first=control, second=Abexinostat/Pracinostat.
    assert classify_two_intervention("control", "Abexinostat") == "agent2_only"
    assert classify_two_intervention("control", "Pracinostat") == "agent2_only"
    assert classify_two_intervention("control", "Abexinostat") != "vehicle_vehicle"


def test_full_two_intervention_classification():
    assert classify_two_intervention("control", "control") == "vehicle_vehicle"
    assert classify_two_intervention("Acetate", "control") == "agent1_only"
    assert classify_two_intervention("Acetate", "Abexinostat") == "combination"


# ---------------------------------------------------------------------------
# QA arithmetic (review P1: np.abs(effect > t) counted only positives)
# ---------------------------------------------------------------------------

def test_abs_above_counts_negative_effects():
    # v1's np.abs(effect > 0.1) counted only positives; this fixture has 1 positive and
    # 1 negative above threshold -> correct answer 2, buggy answer 1.
    effect = np.array([0.2, -0.3, 0.05, -0.05, 0.0])
    assert abs_above(effect, 0.1) == 2
    buggy = int(np.abs(effect > 0.1).sum())
    assert buggy == 1 and buggy != abs_above(effect, 0.1)


# ---------------------------------------------------------------------------
# suffix handling (protocol v2 rule F/G)
# ---------------------------------------------------------------------------

def test_strip_name_suffix_only_verified_pattern():
    assert strip_name_suffix("CD99:1") == ("CD99", True)
    assert strip_name_suffix("CD99") == ("CD99", False)
    assert strip_name_suffix("A::B") == ("A::B", False)  # arbitrary colons untouched
    assert strip_name_suffix("X:12") == ("X", True)


# ---------------------------------------------------------------------------
# sample-sheet key parsing
# ---------------------------------------------------------------------------

def test_sheet_key_parsers():
    k = parse_sheet_key_s4("100_Acetate_0_DMSO_MCF7_plate3_A1")
    assert k == {"dose1": "100", "agent1": "Acetate", "dose2": "0", "agent2": "DMSO",
                 "cell": "MCF7", "plate": "plate3", "well": "A1"}
    assert parse_sheet_key_s4("malformed_key") is None
    assert parse_sheet_key_s2("Nutlin_50_AA02") == {"agent": "Nutlin", "dose": "50",
                                                    "well": "AA02"}
    assert parse_sheet_key_s2("Nutlin_50") is None


# ---------------------------------------------------------------------------
# gene mapping (review P1: stable-ID conflicts, first-wins aliases, collisions)
# ---------------------------------------------------------------------------

def _mini_hgnc() -> pd.DataFrame:
    return pd.DataFrame([
        {"hgnc_id": "HGNC:1", "symbol": "PWWP3A", "prev_symbol": "", "alias_symbol": "",
         "ensembl_gene_id": "ENSG00000160953"},
        {"hgnc_id": "HGNC:2", "symbol": "IRF4", "prev_symbol": "MUM1",
         "alias_symbol": "", "ensembl_gene_id": "ENSG00000186311"},
        {"hgnc_id": "HGNC:3", "symbol": "CFTR-AS2", "prev_symbol": "", "alias_symbol": "",
         "ensembl_gene_id": "ENSG00000083622"},
        {"hgnc_id": "HGNC:4", "symbol": "CD99", "prev_symbol": "", "alias_symbol": "",
         "ensembl_gene_id": "ENSG00000002686"},
        {"hgnc_id": "HGNC:5", "symbol": "MATR3", "prev_symbol": "", "alias_symbol": "",
         "ensembl_gene_id": "ENSG0000015818146"},
        {"hgnc_id": "HGNC:6", "symbol": "BAR1", "prev_symbol": "", "alias_symbol": "FOO",
         "ensembl_gene_id": "ENSGX1"},
        {"hgnc_id": "HGNC:7", "symbol": "BAR2", "prev_symbol": "", "alias_symbol": "FOO",
         "ensembl_gene_id": "ENSGX2"},
    ])


def test_mum1_stable_id_wins_over_alias():
    # MUM1 / ENSG00000160953 must NOT silently map to IRF4 (the alias target); the stable
    # ID corresponds to PWWP3A and the conflict must be recorded.
    mp = build_gene_mapping(["MUM1"], ["ENSG00000160953"], _mini_hgnc())
    row = mp.iloc[0]
    assert row.selected_symbol == "PWWP3A"
    assert row.mapping_method == "stable_id"
    assert row.conflict_status == "stable_id_vs_symbol_resolved_stable_wins"
    assert "IRF4" in row.symbol_candidates


def test_accession_name_resolved_through_stable_id():
    mp = build_gene_mapping(["AC000061.1"], ["ENSG00000083622"], _mini_hgnc())
    row = mp.iloc[0]
    assert row.selected_symbol == "CFTR-AS2"
    assert row.mapping_method == "stable_id"


def test_suffix_collision_shared_vs_differing_ensembl():
    # CD99/CD99:1 share one Ensembl ID; MATR3/MATR3:1 carry different IDs. These are
    # different situations and must be flagged differently.
    names = ["CD99", "CD99:1", "MATR3", "MATR3:1"]
    eids = ["ENSG00000002686", "ENSG00000002686", "ENSG0000015818146", "ENSG00000158147"]
    hgnc = _mini_hgnc()
    hgnc.loc[hgnc.symbol == "MATR3", "ensembl_gene_id"] = "ENSG0000015818146"
    mp = build_gene_mapping(names, eids, hgnc)
    cd99 = mp[mp.symbol_lookup_name == "CD99"]
    matr3 = mp[mp.symbol_lookup_name == "MATR3"]
    assert cd99.collision_group.nunique() == 1
    assert (cd99.shared_ensembl_in_collision == "yes").all()
    assert matr3.collision_group.nunique() == 1
    assert (matr3.shared_ensembl_in_collision == "no").all()
    # both members of each collision keep their own row (no merging)
    assert len(mp) == 4


def test_multi_target_alias_stays_ambiguous():
    mp = build_gene_mapping(["FOO"], ["ENSGZ9"], _mini_hgnc())
    row = mp.iloc[0]
    assert row.mapping_method == "symbol_alias_ambiguous"
    assert row.selected_symbol == ""
    assert row.ambiguity_status == "ambiguous"
    assert set(row.symbol_candidates.split("|")) == {"BAR1", "BAR2"}


def test_mapping_stats_reconcile():
    mp = build_gene_mapping(
        ["CD99", "CD99:1", "MUM1", "AC000061.1", "FOO", "ZZZUNK"],
        ["ENSG00000002686", "ENSG00000002686", "ENSG00000160953", "ENSG00000083622",
         "ENSGZ9", ""],
        _mini_hgnc())
    stats = mapping_stats(mp)
    assert stats["input_feature_rows"] == 6
    # mapped + ambiguous-unselected + unresolved must reconcile to the input
    assert (stats["mapped_rows"] + stats["ambiguous_rows"] + stats["unresolved_rows"]
            == stats["input_feature_rows"])
    assert sum(stats["mapping_method_counts_mutually_exclusive"].values()) == 6
    assert stats["stable_id_vs_symbol_conflicts"] == 1


# ---------------------------------------------------------------------------
# QA acceptance gate (review P2: QA must fail invalid packages, nonzero exit)
# ---------------------------------------------------------------------------

def _write_invalid_package(tmp_path: Path) -> Path:
    pkg = tmp_path / "invalid_pkg"
    pkg.mkdir()
    (pkg / "pilot_manifest.json").write_text(json.dumps({
        "sources": {}, "content_hashes": {}, "gene_mapping": {},
        "studies": {}, "sample_sheet_reconciliation": {}, "rescue_contrasts": {}}))
    (pkg / "response_arrays.npz").write_bytes(b"not an npz")
    (pkg / "response_genes.txt").write_text("GENE1\n")
    for f in ("observation_provenance.csv", "condition_classification.csv",
              "response_index.csv", "gene_mapping.csv", "quarantine_ledger.csv",
              "sample_sheet_reconciliation.csv", "rescue_contrast_ledger.csv",
              "well_summaries.csv", "typed_evidence.csv"):
        pd.DataFrame().to_csv(pkg / f, index=False)
    return pkg


def test_invalid_package_fails_the_gate(tmp_path):
    pkg = _write_invalid_package(tmp_path)
    code, gates = qa_mod.run_checks(out_dir=pkg, qa_dir=tmp_path / "qa",
                                    src_dir=tmp_path / "src", make_figures=False)
    assert code == 1
    assert any(not g["passed"] for g in gates)


def test_pickled_array_fails_package_readability(tmp_path):
    pkg = _write_invalid_package(tmp_path)
    np.savez_compressed(pkg / "response_arrays.npz",
                        **{"wells::sciplex2": np.array([None], dtype=object)})
    code, gates = qa_mod.run_checks(out_dir=pkg, qa_dir=tmp_path / "qa",
                                    src_dir=tmp_path / "src", make_figures=False)
    assert code == 1
    assert any(g["name"] == "package_files_readable" and not g["passed"] for g in gates)


def test_tampered_output_hashes_fail_the_gate(tmp_path):
    # a manifest whose recorded content hash does not match the file must fail
    pkg = tmp_path / "tampered"
    pkg.mkdir()
    (pkg / "response_genes.txt").write_text("GENE1\n")
    manifest = {"sources": {}, "studies": {}, "content_hashes": {
        "response_genes.txt": "0" * 64}, "gene_mapping": {},
        "sample_sheet_reconciliation": {}, "rescue_contrasts": {}}
    (pkg / "pilot_manifest.json").write_text(json.dumps(manifest))
    code, gates = qa_mod.run_checks(out_dir=pkg, qa_dir=tmp_path / "qa",
                                    src_dir=tmp_path / "src", make_figures=False)
    assert code == 1
    assert any(g["name"] == "derived_checksums" and not g["passed"] for g in gates)


@pytest.mark.skipif(not (ROOT / "data/processed/sciplex_pilot_v2/pilot_manifest.json").exists(),
                    reason="sciplex_pilot_v2 not built yet")
def test_real_package_passes_the_gate():
    code, gates = qa_mod.run_checks(make_figures=False)
    failed = [g for g in gates if not g["passed"]]
    assert code == 0, f"failed gates: {[g['name'] for g in failed]}"
