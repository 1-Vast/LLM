"""Build sciplex_pilot_v2 per research/dataset_discovery/CONSTRUCTION_PROTOCOL_V2.md.

File summary
- Path: tools/datasets/build_sciplex_pilot_v2.py
- Purpose: repair build of the sci-Plex pilot data products, resolving
  research/dataset_discovery/PILOT_REVIEW.md findings:
  identity quarantine (no 'nan' conditions), complete two-intervention classification,
  same-plate control matching with explicit unavailable contrasts, per-well summaries
  with a named well-unweighted aggregation estimand, stable-ID-first row-level gene
  mapping, real sample-sheet reconciliation, NaN-masked missingness.
- This is a REPAIR protocol: written after full exposure to v1 results. Development-only.
- Run: `python -m tools.datasets.build_sciplex_pilot_v2`
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.datasets.sciplex_v2_lib import (build_gene_mapping, classify_two_intervention,
                                        is_missing, mapping_stats, parse_sheet_key_s2,
                                        parse_sheet_key_s4)
from tools.case_memory import md5, sha256

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data/external/sciplex_family"
OUT = ROOT / "data/processed/sciplex_pilot_v2"
QA = ROOT / "outputs/sciplex_pilot_v2"
PROTOCOL = "research/dataset_discovery/CONSTRUCTION_PROTOCOL_V2.md"
HGNC_PATH = ROOT / "data/external/hgnc/hgnc_complete_set.txt"

SCIPLEX2_MD5 = "12a48293a166a859f994551653a2ad8c"
SCIPLEX4_MD5 = "9335b581baba2df02ecf92eed4b56ad7"

MISSING_FIELD_REASONS = "missing_identity_fields"


def _prov_row(tag, cond_key, classification, contrast_kind, p1, d1, p2, d2, cell, plate,
              n_cells, n_wells, ctrl_key, rule, available, reason):
    return {"study": tag, "condition_key": cond_key, "classification": classification,
            "contrast_kind": contrast_kind, "first_intervention": p1, "first_dose": d1,
            "second_intervention": p2, "second_dose": d2, "cell_line": cell, "plate": plate,
            "cells_in_condition": n_cells, "wells_in_condition": n_wells,
            "control_key": ctrl_key, "control_matching_rule": rule,
            "available": available, "unavailability_reason": reason}


def _validate_identities(obs: pd.DataFrame, required: list[str], study: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split obs into identifiable rows and a quarantine ledger BEFORE string coercion."""
    missing_mask = pd.Series(False, index=obs.index)
    reasons: list[str] = []
    for idx in obs.index:
        miss = [c for c in required if is_missing(obs.at[idx, c])]
        reasons.append(",".join(miss))
        missing_mask.loc[idx] = bool(miss)
    quar = obs[missing_mask].copy()
    quar["study"] = study
    quar["source_row_id"] = quar.index.astype(str)
    quar["missing_fields"] = [r for r, keep in zip(reasons, missing_mask) if keep]
    quar["reason"] = MISSING_FIELD_REASONS
    quar = quar[["study", "source_row_id", "missing_fields", "reason"]]
    return obs[~missing_mask].copy(), quar


def _normalize_cells(X: sp.csr_matrix) -> sp.csr_matrix:
    """Deterministic per-cell CP10K + log1p from raw counts."""
    library = np.asarray(X.sum(axis=1)).ravel()
    library[library == 0] = 1.0
    Xn = X.multiply(1e4 / library[:, None]).tocsr()
    Xn.data = np.log1p(Xn.data)
    return Xn


def _group_mean_by_key(Xn: sp.csr_matrix, keys: np.ndarray) -> tuple[np.ndarray, list, np.ndarray]:
    """Unweighted-safe helper: per-group SUMS and counts (used for wells and conditions)."""
    groups, inverse = np.unique(keys, return_inverse=True)
    indicator = sp.csr_matrix(
        (np.ones(len(inverse)), (inverse, np.arange(len(inverse)))),
        shape=(len(groups), len(inverse)), dtype=np.float64)
    sums = indicator @ Xn
    counts = np.bincount(inverse, minlength=len(groups))
    return sums, list(groups), counts


def _matrix_provenance(a) -> dict:
    layers = list(a.layers.keys()) if hasattr(a, "layers") else []
    X = sp.csr_matrix(a.X)
    data = X.data
    return {
        "X_dtype": str(X.dtype),
        "layers_present": layers,
        "raw_present": a.raw is not None,
        "X_min": float(data.min()),
        "X_max": float(data.max()),
        "X_fraction_integer": float(np.mean(data == np.floor(data))),
        "X_nonnegative": bool(data.min() >= 0),
        "note": ("count-like properties observed; integer/nonnegative checks do not prove "
                 "that upstream processing preserved raw experimental information"),
    }


def build() -> dict:
    import anndata as ad

    OUT.mkdir(parents=True, exist_ok=True)
    QA.mkdir(parents=True, exist_ok=True)
    report: dict = {"protocol": PROTOCOL, "sources": {}, "studies": {},
                    "missingness": {}, "sample_sheet_reconciliation": {},
                    "rescue_contrasts": {}, "gene_mapping": {}}

    quarantine_frames = []
    prov_frames = []
    class_frames = []
    well_frames = []
    recon_frames = []
    response_blocks: dict[str, np.ndarray] = {}
    response_index_rows = []
    var_axis = None

    # ---------------- shared gene axis & mapping ---------------------------
    a2 = ad.read_h5ad(SRC / "SrivatsanTrapnell2020_sciplex2.h5ad", backed="r")
    a4 = ad.read_h5ad(SRC / "SrivatsanTrapnell2020_sciplex4.h5ad", backed="r")
    assert (a2.var_names == a4.var_names).all(), "var axes differ between sources"
    assert (a2.var["ensembl_id"].astype(str) == a4.var["ensembl_id"].astype(str)).all()
    var_axis = list(a2.var_names.astype(str))
    ensembl_axis = [("" if is_missing(v) else str(v).strip()) for v in a2.var["ensembl_id"]]
    hgnc = pd.read_csv(HGNC_PATH, sep="\t", low_memory=False)
    gmap = build_gene_mapping(var_axis, ensembl_axis, hgnc)
    gmap.to_csv(OUT / "gene_mapping.csv", index=False)
    report["gene_mapping"] = mapping_stats(gmap)
    report["gene_mapping"]["hgnc_resource"] = {
        "file": "data/external/hgnc/hgnc_complete_set.txt",
        "sha256": sha256(HGNC_PATH), "rows": int(len(hgnc))}
    report["gene_mapping"]["feature_axis"] = (
        "original var axis preserved (58347 columns); no column merging/summing; "
        "gene_mapping.csv is the identity product")

    for tag, ann, filename, expected_md5, sheet_name, required, sheet_parser in (
        ("sciplex2", a2, "SrivatsanTrapnell2020_sciplex2.h5ad", SCIPLEX2_MD5,
         "GSM4150377_sciPlex2_hashSampleSheet.txt.gz",
         ["perturbation", "dose_value", "cell_line", "well"], parse_sheet_key_s2),
        ("sciplex4", a4, "SrivatsanTrapnell2020_sciplex4.h5ad", SCIPLEX4_MD5,
         "GSM4150379_sciPlex4_hashSampleSheet.txt.gz",
         ["perturbation", "dose_value", "perturbation_2", "dose_value_2", "cell_line",
          "plate_id", "well_id"], parse_sheet_key_s4),
    ):
        path = SRC / filename
        actual_md5 = md5(path)
        assert actual_md5 == expected_md5, f"checksum mismatch: {filename}"
        ann = ad.read_h5ad(path)  # full read: backed X has dtype object
        report["sources"][tag] = {
            "file": f"data/external/sciplex_family/{filename}", "bytes": path.stat().st_size,
            "md5": actual_md5, "sha256": sha256(path),
            "md5_verified_against": "Zenodo record 13350497",
            "sample_sheet": f"data/external/sciplex_family/{sheet_name}",
            "sample_sheet_sha256": sha256(SRC / sheet_name),
            "license": "CC BY 4.0 (Zenodo record)",
            "matrix_provenance": _matrix_provenance(ann),
        }
        obs = ann.obs.copy()
        identifiable, quarantined = _validate_identities(obs, required, tag)
        quarantine_frames.append(quarantined)

        if tag == "sciplex2":
            ident_fields = dict(
                p1=identifiable["perturbation"], d1=identifiable["dose_value"],
                cell=identifiable["cell_line"], well=identifiable["well"], plate="")
            well_key = (identifiable["cell_line"].astype(str) + "::"
                        + identifiable["well"].astype(str))
            # condition key: cell_line is included even though the processed file holds
            # A549 only (verified in v2) so the key is context-complete.
            cond_key = (identifiable["perturbation"].astype(str) + "::"
                        + identifiable["dose_value"].astype(str) + "@"
                        + identifiable["cell_line"].astype(str))
        else:
            ident_fields = dict(
                p1=identifiable["perturbation"], d1=identifiable["dose_value"],
                p2=identifiable["perturbation_2"], d2=identifiable["dose_value_2"],
                cell=identifiable["cell_line"], plate=identifiable["plate_id"],
                well=identifiable["well_id"])
            well_key = (identifiable["plate_id"].astype(str) + "::"
                        + identifiable["well_id"].astype(str))
            cond_key = (identifiable["perturbation"].astype(str) + "::"
                        + identifiable["dose_value"].astype(str) + "|"
                        + identifiable["perturbation_2"].astype(str) + "::"
                        + identifiable["dose_value_2"].astype(str) + "@"
                        + identifiable["cell_line"].astype(str) + "@"
                        + identifiable["plate_id"].astype(str))

        # ---- per-well summaries (protocol v2 section 4) --------------------
        Xn = _normalize_cells(sp.csr_matrix(ann.X))
        # restrict matrices to identifiable cells (quarantined rows never enter)
        ident_pos = obs.index.get_indexer(identifiable.index)
        assert (ident_pos >= 0).all() and len(ident_pos) == len(identifiable)
        Xn = Xn[ident_pos]
        w_sums, wells, w_counts = _group_mean_by_key(Xn, well_key.to_numpy())
        well_idx = {w: i for i, w in enumerate(wells)}
        w_means = (w_sums / np.maximum(w_counts[:, None], 1)).astype(np.float32)
        response_blocks[f"wells::{tag}"] = w_means.toarray()
        for i, w in enumerate(wells):
            well_frames.append(pd.DataFrame([{
                "study": tag, "well_key": w, "n_cells": int(w_counts[i]),
                "well_recovered_from": "obs well field of the processed h5ad"}]))

        # ---- condition grouping (identifiable cells only) -------------------
        c_sums, conds, c_cell_counts = _group_mean_by_key(Xn, cond_key.to_numpy())
        # unweighted mean of per-well means per condition
        cond_well_matrix = np.zeros((len(conds), len(wells)), dtype=np.int64)
        cell2well = {w: i for i, w in enumerate(wells)}
        for cond_i, ck in enumerate(conds):
            member_cells = np.flatnonzero(cond_key.to_numpy() == ck)
            member_wells = sorted({well_key.iloc[c] for c in member_cells})
            for w in member_wells:
                cond_well_matrix[cond_i, cell2well[w]] = 1
        cond_means = (cond_well_matrix @ w_means) / np.maximum(
            cond_well_matrix.sum(axis=1, keepdims=True), 1)
        cond_means = cond_means.astype(np.float32)
        cond_well_counts = cond_well_matrix.sum(axis=1)
        cidx = {c: i for i, c in enumerate(conds)}
        response_blocks[f"means::{tag}"] = cond_means

        # ---- classification, control matching, effects ----------------------
        first_field = cond_key.iloc[0]
        rows_prov, rows_cls, rows_index = [], [], []
        effects = np.full(cond_means.shape, np.nan, dtype=np.float32)
        avail = np.zeros(len(conds), dtype=bool)

        if tag == "sciplex2":
            def parse_cond(ck):
                agent_dose, cell = ck.split("@")
                agent, dose = agent_dose.split("::")
                return agent, dose, cell
            parsed = {c: parse_cond(c) for c in conds}
            for j, ck in enumerate(conds):
                agent, dose, cell = parsed[ck]
                is_vehicle = float(dose) == 0.0
                cls = "vehicle" if is_vehicle else "single_agent"
                rows_cls.append({"study": tag, "condition_key": ck,
                                 "first_intervention": agent, "first_dose": dose,
                                 "second_intervention": "", "second_dose": "",
                                 "cell_line": cell, "plate": "",
                                 "classification": cls})
                rule, ctrl_key, reason = "", "", ""
                if is_vehicle:
                    contrast_kind, avail[j] = "baseline_self", True
                    effects[j] = 0.0
                else:
                    agent_zero = f"{agent}::0@{cell}"
                    if agent_zero in cidx:
                        ctrl_key, rule = agent_zero, "same_agent_zero_dose_same_cell"
                    elif "control::0@" + cell in cidx:
                        ctrl_key, rule = "control::0@" + cell, "global_control_token_fallback"
                    else:
                        reason = "no_control_available"
                    if ctrl_key:
                        effects[j] = cond_means[j] - cond_means[cidx[ctrl_key]]
                        avail[j] = True
                        contrast_kind = "treatment_vs_vehicle"
                    else:
                        contrast_kind = "unavailable"
                rows_prov.append(_prov_row(tag, ck, cls, contrast_kind, agent, dose,
                                                "", "", cell, "", int(c_cell_counts[j]),
                                                int(cond_well_counts[j]), ctrl_key, rule,
                                                bool(avail[j]), reason))
                rows_index.append({"block": tag, "condition_key": ck, "row": j,
                                   "available": bool(avail[j]),
                                   "contrast_kind": contrast_kind,
                                   "unavailability_reason": reason})
        else:
            def parse_cond(ck):
                body, cell, plate = ck.split("@")
                p1d1, p2d2 = body.split("|")
                p1, d1 = p1d1.split("::")
                p2, d2 = p2d2.split("::")
                return p1, d1, p2, d2, cell, plate
            parsed = {c: parse_cond(c) for c in conds}
            vv_keys = {c for c in conds
                       if classify_two_intervention(parsed[c][0], parsed[c][2]) == "vehicle_vehicle"}
            for j, ck in enumerate(conds):
                p1, d1, p2, d2, cell, plate = parsed[ck]
                cls = classify_two_intervention(p1, p2)
                rows_cls.append({"study": tag, "condition_key": ck,
                                 "first_intervention": p1, "first_dose": d1,
                                 "second_intervention": p2, "second_dose": d2,
                                 "cell_line": cell, "plate": plate,
                                 "classification": cls})
                ctrl_key, rule, reason = "", "", ""
                if cls == "vehicle_vehicle":
                    contrast_kind, avail[j] = "baseline_self", True
                    effects[j] = 0.0
                else:
                    ctrl_key = f"control::0|control::0@{cell}@{plate}"
                    if ctrl_key in cidx:
                        effects[j] = cond_means[j] - cond_means[cidx[ctrl_key]]
                        avail[j] = True
                        contrast_kind = "treatment_vs_vehicle"
                        rule = "same_cell_same_plate_dmso_dmso"
                    else:
                        contrast_kind = "unavailable"
                        reason = ("no same-plate DMSO/DMSO control in the processed source "
                                  f"(cell={cell}, plate={plate})")
                rows_prov.append(_prov_row(tag, ck, cls, contrast_kind, p1, d1, p2, d2,
                                                cell, plate, int(c_cell_counts[j]),
                                                int(cond_well_counts[j]), ctrl_key, rule,
                                                bool(avail[j]), reason))
                rows_index.append({"block": tag, "condition_key": ck, "row": j,
                                   "available": bool(avail[j]),
                                   "contrast_kind": contrast_kind,
                                   "unavailability_reason": reason})
        response_blocks[f"effects::{tag}"] = effects
        prov_frames.append(pd.DataFrame(rows_prov))
        class_frames.append(pd.DataFrame(rows_cls))
        response_index_rows.extend(rows_index)

        # ---- Task B: rescue contrast constructibility ledger -----------------
        if tag == "sciplex4":
            rescue_rows = []
            for ck in conds:
                p1, d1, p2, d2, cell, plate = parsed[ck]
                if classify_two_intervention(p1, p2) != "combination":
                    continue
                vv = f"control::0|control::0@{cell}@{plate}" in cidx
                t1 = f"{p1}::{d1}|control::0@{cell}@{plate}" in cidx
                t2 = f"control::0|{p2}::{d2}@{cell}@{plate}" in cidx
                base_reason = ("combination is not on a plate with a same-plate DMSO/DMSO "
                               "control or single-treatment reference (processed source)")
                for kind, ok, refs in (
                    ("combination_vs_vehicle", vv, "DMSO/DMSO same plate"),
                    ("agent1_alone_vs_vehicle", vv and t1,
                     "DMSO/DMSO + agent1-alone same plate/dose"),
                    ("agent2_alone_vs_vehicle", vv and t2,
                     "DMSO/DMSO + agent2-alone same plate/dose"),
                    ("combination_vs_agent1", vv and t1, "as above"),
                    ("combination_vs_agent2", vv and t2, "as above"),
                    ("interaction_contrast", vv and t1 and t2, "full matched design"),
                ):
                    rescue_rows.append({
                        "study": tag, "combination_key": ck, "cell_line": cell,
                        "plate": plate, "contrast_kind": kind,
                        "required_references": refs,
                        "available": bool(ok),
                        "unavailability_reason": "" if ok else base_reason})
            report["rescue_contrasts"][tag] = {
                "n_combination_conditions": len(rescue_rows) // 6,
                "constructible_rescue_contrasts": sum(r["available"] for r in rescue_rows) // 6,
                "verdict": ("RESCUE CONTRASTS NOT CONSTRUCTIBLE FROM THE QUALIFIED SUBSET"
                            if not any(r["available"] for r in rescue_rows)
                            else "some rescue contrasts constructible"),
            }
            pd.DataFrame(rescue_rows).to_csv(OUT / "rescue_contrast_ledger.csv", index=False)

        # ---- sample-sheet reconciliation (real key-level join) ---------------
        import gzip
        # the sheets have no header line; every line is a hash-row record
        sheet_keys = [l.split("\t")[0] for l in
                      gzip.open(SRC / sheet_name, "rt").read().splitlines() if l.strip()]
        parsed_sheet = [sheet_parser(k) for k in sheet_keys]
        bad = sum(p is None for p in parsed_sheet)
        if tag == "sciplex2":
            expected = sorted({f"{p['agent']}::{p['dose']}" for p in parsed_sheet
                               if p is not None})
            expected_wells = {p["well"] for p in parsed_sheet if p is not None}
            observed = sorted({c.split("@")[0] for c in conds})
            matched = sorted(set(expected) & set(observed))
            exp_not_obs = sorted(set(expected) - set(observed))
            obs_not_exp = sorted(set(observed) - set(expected))
            recon_frames.append(pd.DataFrame([
                {"study": tag, "level": "condition", "key": k, "status": s}
                for k, s in ([(k, "matched") for k in matched]
                             + [(k, "expected_not_observed_in_processed_source")
                                for k in exp_not_obs]
                             + [(k, "observed_not_in_sample_sheet") for k in obs_not_exp])]))
            well_obs = {w for w in well_key.astype(str)}
            recon_frames.append(pd.DataFrame([
                {"study": tag, "level": "well", "key": w, "status": status}
                for w, status in (
                    [(w, "matched") for w in sorted(expected_wells & well_obs)]
                    + [(w, "expected_not_observed_in_processed_source")
                       for w in sorted(expected_wells - well_obs)]
                    + [(w, "observed_not_in_sample_sheet") for w in sorted(well_obs - expected_wells)])]))
            report["sample_sheet_reconciliation"][tag] = {
                "sheet_rows": len(parsed_sheet), "unparseable_keys": bad,
                "sheet_has_header": False,
                "expected_conditions": len(expected), "observed_conditions": len(observed),
                "matched": len(matched), "expected_not_observed": len(exp_not_obs),
                "observed_not_in_sheet": len(obs_not_exp)}
        else:
            # Declared token normalization (verified from the sources): the sciPlex4
            # sample sheets encode vehicle wells as 'DMSO'; the processed h5ad obs uses
            # 'control'. Applied to BOTH interventions, recorded in the ledger.
            sheet_token_normalization = {"DMSO": "control"}

            def norm(tok: str) -> str:
                return sheet_token_normalization.get(tok, tok)

            def exp_key(p):
                return (f"{norm(p['agent1'])}::{p['dose1']}|{norm(p['agent2'])}::{p['dose2']}"
                        f"@{p['cell']}@{p['plate']}")

            expected = sorted({exp_key(p) for p in parsed_sheet if p is not None})
            observed = sorted(conds)
            matched = sorted(set(expected) & set(observed))
            exp_not_obs = sorted(set(expected) - set(observed))
            obs_not_exp = sorted(set(observed) - set(expected))
            recon_frames.append(pd.DataFrame([
                {"study": tag, "level": "condition", "key": k,
                 "status": s,
                 "note": ""}
                for k, s in ([(k, "matched") for k in matched]
                             + [(k, "expected_not_observed_in_processed_source")
                                for k in exp_not_obs]
                             + [(k, "observed_not_in_sample_sheet") for k in obs_not_exp])]))
            well_obs = set(well_key.astype(str))
            expected_wells = {f"{p['plate']}::{p['well']}" for p in parsed_sheet
                              if p is not None}
            recon_frames.append(pd.DataFrame([
                {"study": tag, "level": "well", "key": w, "status": status}
                for w, status in (
                    [(w, "matched") for w in sorted(expected_wells & well_obs)]
                    + [(w, "expected_not_observed_in_processed_source")
                       for w in sorted(expected_wells - well_obs)]
                    + [(w, "observed_not_in_sample_sheet") for w in sorted(well_obs - expected_wells)])]))
            report["sample_sheet_reconciliation"][tag] = {
                "sheet_rows": len(parsed_sheet), "unparseable_keys": bad,
                "sheet_has_header": False,
                "sheet_token_normalization": {"DMSO": "control"},
                "expected_conditions": len(expected), "observed_conditions": len(observed),
                "matched": len(matched), "expected_not_observed": len(exp_not_obs),
                "observed_not_in_sheet": len(obs_not_exp)}

        report["studies"][tag] = {
            "source_cells": int(len(obs)),
            "identifiable_cells": int(len(identifiable)),
            "quarantined_cells": int(len(quarantined)),
            "conditions_identifiable": int(len(conds)),
            "wells_recovered": int(len(wells)),
            "cell_lines_observed": sorted(identifiable["cell_line"].astype(str).unique()),
        }

    # ---- assemble outputs -----------------------------------------------------
    prov = pd.concat(prov_frames, ignore_index=True)
    prov["dose_unit"] = "unverified_token (no unit field in sheets or h5ad)"
    prov["biological_replicate_id"] = "unavailable (hash/index rows are not replicates)"
    prov["sampling_frame"] = "processed_source_only (no attempted-experiment denominator)"
    prov["independent_grouping_unit"] = ("condition (treatment x context); well summaries retained; "
                                         "no independent biological replication verified")
    prov.to_csv(OUT / "observation_provenance.csv", index=False)
    pd.concat(class_frames, ignore_index=True).to_csv(OUT / "condition_classification.csv",
                                                      index=False)
    pd.concat(well_frames, ignore_index=True).to_csv(OUT / "well_summaries.csv", index=False)
    pd.concat(recon_frames, ignore_index=True).to_csv(OUT / "sample_sheet_reconciliation.csv",
                                                      index=False)
    pd.concat(quarantine_frames, ignore_index=True).to_csv(OUT / "quarantine_ledger.csv",
                                                           index=False)
    pd.DataFrame(response_index_rows).to_csv(OUT / "response_index.csv", index=False)
    np.savez_compressed(OUT / "response_arrays.npz", **response_blocks)
    with open(OUT / "response_genes.txt", "w") as fh:
        fh.write("\n".join(var_axis))

    # typed evidence (no layer upgrade; design type separated from evidence)
    ev = prov.copy()
    ev["experimental_design_type"] = np.where(
        ev.study == "sciplex4", "chemical_metabolic_rescue_design",
        "dose_response_design")
    ev["evidence_layer"] = np.where(
        ev.classification.isin(["vehicle", "vehicle_vehicle"]),
        "direct_molecular_measurement", "derived_population_response")
    ev["evidence_class"] = ev["evidence_layer"]
    ev["label_kind"] = "none (no outcome labels constructed)"
    ev["qualified_experimental_evidence"] = False
    ev["conditioning_hypothesis"] = ""
    ev["rescue_interpretation"] = ""
    ev.to_csv(OUT / "typed_evidence.csv", index=False)

    # unavailable contrast ledger from the index
    idx_df = pd.DataFrame(response_index_rows)
    idx_df[~idx_df.available].to_csv(OUT / "unavailable_contrasts.csv", index=False)

    # ---- manifest -------------------------------------------------------------
    report["missingness"] = {
        "quarantine_ledger": "quarantine_ledger.csv (source row ids, missing fields, reason)",
        "unavailable_contrasts": "unavailable_contrasts.csv",
        "representation": ("effects arrays use NaN exactly where contrasts are unavailable; "
                           "baseline self-contrasts are defined zeros marked baseline_self; "
                           "unknown-identity cells never enter arrays"),
    }
    report["aggregation_estimand"] = {
        "name": "well-unweighted mean of per-well mean log1p-CP10K",
        "description": ("per-well mean of single-cell log1p-CP10K, then unweighted mean over "
                        "the wells of the condition; n_cells and n_wells retained; NOT a "
                        "count-summed biological-replicate pseudobulk; no replicate "
                        "uncertainty estimable"),
        "per_well_arrays": "response_arrays.npz blocks 'wells::sciplex2' / 'wells::sciplex4'",
    }
    report["implementation"] = {}
    for f in ("__init__.py", "sciplex_v2_lib.py", "build_sciplex_pilot_v2.py", "qa_sciplex_pilot_v2.py"):
        p = Path(__file__).resolve().parent / f
        if p.exists():
            report["implementation"][f] = sha256(p)
    report["implementation"]["tools/case_memory/__init__.py"] = sha256(
        ROOT / "tools/case_memory/__init__.py")
    report["use_restrictions"] = [
        "development-only; no performance, calibration, mechanism, engagement or decision claims",
        "no genetic rescue claims; Task B rescue contrasts not constructible from the "
        "qualified subset (see rescue_contrasts)",
        "hash rows, wells and cells are not biological replicates; dose units are "
        "unverified tokens",
        "not an untouched evaluation set; no attempted-experiment denominator",
    ]
    report["rows"] = {
        "observation_provenance": int(len(prov)),
        "condition_classification": int(sum(len(c) for c in class_frames)),
        "well_summaries": int(sum(len(w) for w in well_frames)),
        "gene_mapping_rows": int(len(gmap)),
        "quarantined_cells": int(sum(len(q) for q in quarantine_frames)),
        "response_conditions": int(len(idx_df)),
    }
    report["built_at"] = pd.Timestamp.now().isoformat()
    report["content_hashes"] = {
        f: sha256(OUT / f) for f in sorted(os_listdir(OUT)) if f != "pilot_manifest.json"
    }
    (OUT / "pilot_manifest.json").write_text(json.dumps(report, indent=1))
    print(json.dumps({"studies": report["studies"], "rows": report["rows"],
                      "rescue": report["rescue_contrasts"],
                      "recon": report["sample_sheet_reconciliation"],
                      "gene_mapping": {k: v for k, v in report["gene_mapping"].items()
                                       if k != "hgnc_resource"}}, indent=1))


def os_listdir(path: Path) -> list[str]:
    import os
    return os.listdir(path)


if __name__ == "__main__":
    build()
