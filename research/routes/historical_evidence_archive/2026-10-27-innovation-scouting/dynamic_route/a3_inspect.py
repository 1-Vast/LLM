"""R198-A3 metadata-only inspector (v2) for local Mix-seq (scPerturb) asset.

Hard rules: reads ONLY h5ad metadata (obs/var column names and design-metadata values,
X encoding/shape attrs, key presence); NEVER reads expression values, obsm embeddings,
or layers. Computes only column presence / null counts / value counts of design metadata,
entity-key counts, QC-flag counts and identity joins. No response statistics, no model fitting.

Outputs dynamic_route/a3_meta.json.
"""
import hashlib
import json
import os
import re
import datetime as _dt

import anndata as ad
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
H5AD = os.path.join(ROOT, "data", "external", "mixseq_scperturb", "mcfarland_2020.h5ad")
CENSUS = os.path.join(ROOT, "research", "eight_directions_20261026",
                      "evidence_audit", "mixseq_design_census.csv")
SAMPLE_INFO = os.path.join(ROOT, "data", "external", "depmap_19q4", "sample_info.csv")
OUT = os.path.join(HERE, "a3_meta.json")

RESPONSE_WORDS = ["viab", "apop", "response", "effect", "ic50", "ic_50", "auc", "survival",
                  "growth", "inhibit", "kill", "death", "phenotype", "synergy", "efficacy",
                  "treated", "resistant", "sensitive"]


def sha256_file(path, chunk=1 << 22):
    h = hashlib.sha256()
    size = 0
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
            size += len(block)
    return h.hexdigest(), size


def value_counts(series, limit=None):
    s = series.astype("string")
    vc = s.value_counts(dropna=False)
    items = [[str(k), int(v)] for k, v in vc.items()]
    if limit is not None and len(items) > limit:
        kept = items[:limit]
        kept.append(["<TRUNCATED>", int(vc.iloc[limit:].sum())])
        return dict(kept)
    return dict(items)


def summarize_col(series, limit=80):
    s = series.astype("string")
    return {"dtype": str(series.dtype), "n_null": int(series.isna().sum()),
            "n_unique": int(s.nunique(dropna=True)), "value_counts": value_counts(series, limit)}


def norm_channel(x):
    if x is None:
        return None
    s = str(x)
    if s in ("nan", "<NA>", "None", ""):
        return None
    try:
        f = float(s)
        if f.is_integer():
            return str(int(f))
        return str(f)
    except ValueError:
        return s


def main():
    meta = {
        "meta": {
            "task": "task-26 R198-A3 dynamic-route metadata qualification",
            "agent": "cellstate-lit",
            "generated_local": _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "scope": ("metadata-only: column presence, null counts, design-metadata value counts, "
                      "entity-key counts, QC-flag counts, identity joins; no expression read, no "
                      "response statistics, no model fitting"),
            "expression_matrix_read": False,
            "response_read": False,
            "training_run": False,
        }
    }

    h5_sha, h5_bytes = sha256_file(H5AD)
    census_sha = hashlib.sha256(open(CENSUS, "rb").read()).hexdigest()
    meta["files"] = {
        "h5ad": {"path": os.path.relpath(H5AD, ROOT).replace(os.sep, "/"),
                 "bytes": h5_bytes, "sha256": h5_sha},
        "census_csv": {"path": os.path.relpath(CENSUS, ROOT).replace(os.sep, "/"),
                       "bytes": os.path.getsize(CENSUS), "sha256": census_sha},
    }

    adata = ad.read_h5ad(H5AD, backed="r")
    obs = adata.obs.copy()
    var = adata.var
    meta["h5ad_structure"] = {
        "n_obs": int(adata.n_obs), "n_vars": int(adata.n_vars),
        "X": {"type": type(adata.X).__name__, "shape": [int(x) for x in adata.X.shape],
              "encoding_type": str(getattr(adata.X, "encoding_type", None))},
        "obs_columns": [str(c) for c in obs.columns],
        "var_columns": [str(c) for c in var.columns],
        "obsm_keys": [str(k) for k in adata.obsm.keys()],
        "layers_keys": [str(k) for k in adata.layers.keys()],
        "uns_keys": [str(k) for k in adata.uns.keys()],
        "obs_index_unique": bool(obs.index.is_unique),
        "obs_index_example": [str(obs.index.min())[:100], str(obs.index.max())[:100]],
        "raw_present": bool(adata.raw is not None),
    }

    key_cols = ["time", "perturbation", "perturbation_type", "cell_line", "channel",
                "hash_tag", "hash_assignment", "dose_value", "dose_unit", "organism",
                "tissue_type", "cancer", "sex", "DepMap_ID", "chembl-ID", "cell_quality",
                "nperts", "doublet_GMM_prob", "singlet_dev", "ncounts", "ngenes",
                "tot_reads", "percent.mito"]
    meta["columns"] = {c: (summarize_col(obs[c]) if c in obs.columns else {"present": False})
                       for c in key_cols}
    meta["columns_absent_from_obs"] = [c for c in key_cols if c not in obs.columns]

    # functional endpoint: column-name level only
    obs_hits, var_hits = [], []
    for c in obs.columns:
        for w in RESPONSE_WORDS:
            if w in str(c).lower():
                obs_hits.append({"column": str(c), "matched": w})
    for c in var.columns:
        for w in RESPONSE_WORDS:
            if w in str(c).lower():
                var_hits.append({"column": str(c), "matched": w})
    meta["functional_endpoint_check"] = {
        "response_word_hits_in_obs_column_names": obs_hits,
        "response_word_hits_in_var_column_names": var_hits,
        "any_viability_or_apoptosis_column": bool(obs_hits or var_hits),
        "note": ("obs columns are single-cell transcriptome design/QC metadata; var columns are "
                 "gene-level summary metadata (no response endpoint); obsm/layers/uns are empty"),
    }

    # ---- exact 6h / 24h keys (design metadata only) ----
    obs["_t"] = obs["time"].astype("string")
    obs["_p"] = obs["perturbation"].astype("string")
    obs["_c"] = obs["cell_line"].astype("string")
    obs["_ch"] = obs["channel"].map(norm_channel).astype("string")
    obs["_dose"] = obs["dose_value"].astype("string")
    obs["_dq"] = obs["cell_quality"].astype("string")

    m6 = (obs["_t"] == "6").to_numpy()
    m24 = (obs["_t"] == "24").to_numpy()

    def keys(mask, extra=None):
        parts = [obs.loc[mask, "_p"], obs.loc[mask, "_c"]]
        if extra is not None:
            parts.append(obs.loc[mask, extra])
        return set(pd.MultiIndex.from_arrays(parts))

    s6, s24 = keys(m6), keys(m24)
    common = s6 & s24
    per_pert = {p: sum(1 for q, _ in common if q == p) for p in sorted({p for p, _ in common})}
    meta["exact_6_24_from_h5ad"] = {
        "n_time6_cells": int(m6.sum()), "n_time24_cells": int(m24.sum()),
        "n_keys_time6": len(s6), "n_keys_time24": len(s24),
        "n_common_pert_cell_keys": len(common),
        "n_common_perturbations": len({p for p, _ in common}),
        "n_common_cell_lines": len({c for _, c in common}),
        "per_perturbation_common_key_counts": per_pert,
        "perturbations_time6": sorted({p for p, _ in s6}),
        "perturbations_time24_only": sorted({p for p, _ in s24} - {p for p, _ in common}),
    }

    meta["key_definition_sensitivity"] = {}
    for label, mask in [("time6", m6), ("time24", m24)]:
        meta["key_definition_sensitivity"][label] = {
            "base_pert_cell": len(keys(mask)),
            "with_normalized_channel": len(keys(mask, "_ch")),
            "with_dose_value": len(keys(mask, "_dose")),
        }

    # per common key: cells, QC-normal cells, channel sets, doses, hash tags
    rows = []
    for (p, c) in sorted(common):
        s6k = obs[(obs["_t"] == "6") & (obs["_p"] == p) & (obs["_c"] == c)]
        s24k = obs[(obs["_t"] == "24") & (obs["_p"] == p) & (obs["_c"] == c)]
        rows.append({
            "perturbation": p, "cell_line": c,
            "cells_6h": int(len(s6k)), "cells_24h": int(len(s24k)),
            "normal_cells_6h": int((s6k["_dq"] == "normal").sum()),
            "normal_cells_24h": int((s24k["_dq"] == "normal").sum()),
            "channels_6h": sorted({x for x in s6k["_ch"].dropna() if x != "nan"}),
            "channels_24h": sorted({x for x in s24k["_ch"].dropna() if x != "nan"}),
            "dose_6h": sorted({x for x in s6k["_dose"].dropna()}),
            "dose_24h": sorted({x for x in s24k["_dose"].dropna()}),
        })
    same_ch = sum(1 for r in rows if r["channels_6h"] and r["channels_24h"]
                  and set(r["channels_6h"]) == set(r["channels_24h"]))
    both_ch_missing = sum(1 for r in rows if not r["channels_6h"] and not r["channels_24h"])
    one_ch_missing = sum(1 for r in rows if bool(r["channels_6h"]) != bool(r["channels_24h"]))
    dose_mm = sum(1 for r in rows if r["dose_6h"] and r["dose_24h"]
                  and set(r["dose_6h"]) != set(r["dose_24h"]))
    dose_missing = sum(1 for r in rows if not r["dose_6h"] or not r["dose_24h"])
    n6 = np.array([r["cells_6h"] for r in rows]); n24 = np.array([r["cells_24h"] for r in rows])
    nq6 = np.array([r["normal_cells_6h"] for r in rows]); nq24 = np.array([r["normal_cells_24h"] for r in rows])
    meta["common_key_design_match"] = {
        "n_common_keys": len(rows),
        "n_keys_channel_missing_at_both_times": both_ch_missing,
        "n_keys_with_identical_nonempty_normalized_channel_sets": same_ch,
        "n_keys_with_channel_on_only_one_time": one_ch_missing,
        "n_keys_with_dose_mismatch_6h_vs_24h": dose_mm,
        "n_keys_missing_dose_on_at_least_one_time": dose_missing,
        "cells_6h_min_median_max": [int(n6.min()), float(np.median(n6)), int(n6.max())],
        "cells_24h_min_median_max": [int(n24.min()), float(np.median(n24)), int(n24.max())],
        "normal_cells_6h_min_median_max": [int(nq6.min()), float(np.median(nq6)), int(nq6.max())],
        "normal_cells_24h_min_median_max": [int(nq24.min()), float(np.median(nq24)), int(nq24.max())],
        "n_keys_with_normal_cells_ge10_both_times": int(((nq6 >= 10) & (nq24 >= 10)).sum()),
        "n_keys_with_normal_cells_ge20_both_times": int(((nq6 >= 20) & (nq24 >= 20)).sum()),
        "n_keys_with_normal_cells_ge30_both_times": int(((nq6 >= 30) & (nq24 >= 30)).sum()),
        "per_drug_n_keys_normal_ge10_both_times": {
            p: int(sum(1 for r in rows if r["perturbation"] == p
                       and r["normal_cells_6h"] >= 10 and r["normal_cells_24h"] >= 10))
            for p in sorted(per_pert)},
        "examples_first5": rows[:5],
    }

    # dose metadata for the common-key arms (design metadata only; no zero rows)
    dose_rows = []
    for p in sorted(per_pert):
        sub = obs[(obs["_p"] == p) & (obs["_t"].isin(["6", "24"]))]
        g = (sub.groupby(["_t", "_dose", "dose_unit"], dropna=False, observed=True).size()
             .reset_index(name="cells"))
        for r in g.itertuples(index=False, name=None):
            time_lbl, dose_val, dose_unit, cells_n = r
            if int(cells_n) > 0:
                dose_rows.append({"time": str(time_lbl), "perturbation": p,
                                  "dose_value": str(dose_val), "dose_unit": str(dose_unit),
                                  "cells": int(cells_n)})
    meta["dose_metadata_common_arms"] = dose_rows

    # drug identity annotations available in obs (metadata only)
    chem = obs[["_p", "chembl-ID"]].drop_duplicates()
    meta["perturbation_chembl_map"] = {
        str(p): sorted({str(x) for x in sub["chembl-ID"].dropna()})
        for p, sub in chem.groupby("_p")}

    # ---- time labels & mixed-label unresolved rows ----
    meta["time_labels"] = {"n_unique": int(obs["_t"].nunique()),
                           "counts": value_counts(obs["_t"])}
    mixed = obs["_t"].astype("string").str.contains(",", regex=False)
    meta["mixed_time_labels"] = {
        "n_cells": int(mixed.sum()),
        "labels": value_counts(obs.loc[mixed, "_t"]),
        "perturbations": value_counts(obs.loc[mixed, "_p"], 30),
        "perturbation_types": value_counts(obs.loc[mixed, "perturbation_type"]),
        "note": ("cells carry a comma-joined time label; a single time cannot be assigned from "
                 "metadata, so these cells cannot enter a two-snapshot 6h-vs-24h comparison"),
    }
    meta["perturbation_type"] = summarize_col(obs["perturbation_type"])
    meta["perturbation_type_by_exact_time"] = {
        "time6": value_counts(obs.loc[m6, "perturbation_type"]),
        "time24": value_counts(obs.loc[m24, "perturbation_type"]),
    }

    # ---- 24h-only drug arms (single-snapshot, static-only candidates) ----
    drug24 = obs[(obs["_t"] == "24") & (obs["perturbation_type"].astype("string") == "drug")]
    per_arm = drug24.groupby("_p").agg(n_cells=("_p", "size"),
                                       n_cell_lines=("_c", "nunique"),
                                       n_channels=("_ch", "nunique")).reset_index()
    meta["time24_drug_arm_cell_counts"] = [
        {"perturbation": str(pert), "n_cells": int(n_cells),
         "n_cell_lines": int(n_cells_lines), "n_channels": int(n_channels)}
        for pert, n_cells, n_cells_lines, n_channels in per_arm.itertuples(index=False, name=None)]

    # ---- cell identity join to DepMap sample_info (metadata-only join) ----
    join = {}
    if os.path.exists(SAMPLE_INFO):
        si = pd.read_csv(SAMPLE_INFO, usecols=["DepMap_ID", "stripped_cell_line_name",
                                               "COSMIC_ID", "disease", "lineage"])
        hd = set(obs["DepMap_ID"].astype("string").dropna())
        sd = set(si["DepMap_ID"].astype("string").dropna())
        common_ids = hd & sd
        join = {"sample_info_path": os.path.relpath(SAMPLE_INFO, ROOT).replace(os.sep, "/"),
                "n_h5ad_depmap_ids": len(hd), "n_sample_info_depmap_ids": len(sd),
                "n_overlap": len(common_ids),
                "n_h5ad_ids_not_in_sample_info": len(hd - sd),
                "common_keys_115_all_have_depmap_id": bool(
                    all(c for _, c in common) and
                    obs[obs["_p"].isin(set(per_pert))]["DepMap_ID"].notna().all())}
        # map common cell lines -> DepMap_ID (metadata only)
        cell2id = (obs[["_c", "DepMap_ID"]].drop_duplicates().sort_values("_c"))
        join["n_cell_lines_with_multiple_depmap_ids"] = int(
            cell2id.groupby("_c").size().gt(1).sum())
    meta["depmap_identity_join"] = join

    # ---- census CSV replay (prior-round source) ----
    cdf = pd.read_csv(CENSUS, encoding="utf-8-sig")
    census_orig_columns = [str(c) for c in cdf.columns]
    census_orig_nulls = {str(c): int(cdf[c].isna().sum()) for c in cdf.columns}
    cdf["_t"] = cdf["time"].astype("string")
    cdf["_p"] = cdf["perturbation"].astype("string")
    cdf["_c"] = cdf["cell_line"].astype("string")
    cdf["_ch"] = cdf["channel"].map(norm_channel).astype("string")
    c6 = set(zip(cdf.loc[cdf._t == "6", "_p"], cdf.loc[cdf._t == "6", "_c"]))
    c24 = set(zip(cdf.loc[cdf._t == "24", "_p"], cdf.loc[cdf._t == "24", "_c"]))
    cov = c6 & c24
    meta["census_replay"] = {
        "path": os.path.relpath(CENSUS, ROOT).replace(os.sep, "/"),
        "columns": census_orig_columns,
        "n_rows": int(len(cdf)),
        "n_null_per_column": census_orig_nulls,
        "all_time_labels": sorted({str(x) for x in cdf["_t"].dropna().unique()}),
        "cells_column_sum": int(cdf["cells"].sum()),
        "n_keys_time6": len(c6), "n_keys_time24": len(c24),
        "n_common_pert_cell_keys": len(cov),
        "per_perturbation_common_key_counts": {
            p: sum(1 for q, _ in cov if q == p) for p in sorted({p for p, _ in cov})},
        "n_common_cell_lines": len({c for _, c in cov}),
        "n_rows_with_channel_time6": int((cdf._t == "6").sum()),
        "n_rows_with_channel_time24": int((cdf._t == "24").sum()),
        "normalized_channel_key_counts_time6": None,
        "column_note": ("census has columns time/perturbation/cell_line/channel/cells only: no dose, "
                        "batch, culture or functional-endpoint columns"),
    }
    meta["census_replay"]["normalized_channel_key_counts_time6"] = len(set(zip(
        cdf.loc[cdf._t == "6", "_p"], cdf.loc[cdf._t == "6", "_c"],
        cdf.loc[cdf._t == "6", "_ch"])))
    # compare census vs h5ad common-key sets (metadata only)
    h5_common = {(p, c) for (p, c) in common}
    meta["census_vs_h5ad_agreement"] = {
        "common_key_sets_identical": bool(h5_common == cov),
        "h5ad_minus_census": sorted(list(h5_common - cov))[:20],
        "census_minus_h5ad": sorted(list(cov - h5_common))[:20],
    }

    # ---- availability of independent functional endpoints in this asset ----
    meta["independent_functional_endpoint"] = {
        "present_in_h5ad": False,
        "evidence": ("no viability/apoptosis/GR/IC50/response-like column in obs or var; "
                     "obsm/layers empty; uns empty; var columns are gene-level summary metadata"),
        "consequence": ("decision-level evaluation (does dynamic information change a concrete drug "
                        "decision) cannot be run on this asset alone; an external functional readout "
                        "matched to the same perturbations/cell lines is required"),
    }

    # ---- batch / culture independence proxies ----
    meta["batch_proxies"] = {
        "explicit_batch_or_plate_column_present": any(
            c in obs.columns for c in ["batch", "plate", "plate_id", "sample", "donor", "replicate"]),
        "available_proxies": [c for c in ["channel", "hash_tag", "hash_assignment",
                                          "singlet_ID", "DepMap_ID"] if c in obs.columns],
        "channel_value_types_mixed": True,
        "note": ("channel/hash_tag are multiplexing metadata (mixed numeric/letter values, sparse); "
                 "they do not certify independent cultures, batches, or matched experimental runs "
                 "between 6h and 24h"),
    }

    # ---- channel availability: time 6 vs time 24, by arm ----
    ch_by_time = {}
    for label, mask in [("time6", m6), ("time24", m24)]:
        sub = obs.loc[mask]
        ch_by_time[label] = {
            "n_cells": int(len(sub)),
            "n_cells_channel_missing": int((sub["_ch"].isna() | (sub["_ch"] == "nan")).sum()),
            "channel_value_counts": value_counts(sub["_ch"]),
        }
    meta["channel_availability"] = {
        "by_exact_time": ch_by_time,
        "note": ("channel is missing for all exact-6h cells and for the 4-drug/control 24h cells; "
                 "it is populated only for some 24h-only dose arms -> it cannot serve as a matched "
                 "batch proxy for the 6h-vs-24h comparison"),
    }

    # ---- cell-line arm structure (metadata only) ----
    lines_by_drug = {p: sorted({c for q, c in common if q == p}) for p in sorted(per_pert)}
    focal24 = set(lines_by_drug.get("Idasanutlin", []))
    ctrl = set(lines_by_drug.get("control", []))
    brd = set(lines_by_drug.get("BRD3379", []))
    arm_struct = {
        "n_lines_per_arm": {p: len(v) for p, v in lines_by_drug.items()},
        "focal24_set_equals_three_drug_arms": all(
            set(lines_by_drug.get(p, [])) == focal24
            for p in ["Bortezomib", "Idasanutlin", "Trametinib"]),
        "n_focal24_in_control": len(focal24 & ctrl),
        "n_brd3379_in_control": len(brd & ctrl),
        "n_focal24_in_brd3379": len(focal24 & brd),
        "control_equals_brd_union_focal": bool(ctrl == (brd | focal24)),
    }
    meta["cell_line_arm_structure"] = arm_struct

    # ---- hashed time-course arm (Trametinib + DMSO / Untreated labels in hash_assignment) ----
    regex_time = re.compile(r"^(Tram|DMSO|Untreated)_(\d+)hr$")
    txt = obs["_p"]
    type_col = obs["perturbation_type"].astype("string")
    mixmask = (obs["_t"].str.contains(",", regex=False).to_numpy()
               & (type_col == "drug").to_numpy())
    mix = obs.loc[mixmask].copy()
    mix["_ht"] = mix["hash_tag"].astype("string")
    mix["_ha"] = mix["hash_assignment"].astype("string")

    def parse_hash(s):
        s = "" if s is None else str(s)
        if s in ("", "nan", "<NA>", "multiplet", "unknown"):
            return ("unresolved", None, None)
        if "," in s:
            return ("combo", None, None)
        m = regex_time.match(s)
        if m:
            return ("single", m.group(1), int(m.group(2)))
        return ("other", None, None)

    parsed = mix["_ha"].map(parse_hash)
    mix["_kind"] = [p[0] for p in parsed]
    mix["_treat"] = [p[1] for p in parsed]
    mix["_time"] = [p[2] for p in parsed]
    clean = mix[mix["_kind"] == "single"].copy()
    clean_norm = clean[clean["_dq"] == "normal"].copy()
    clean["_treattime"] = clean["_treat"] + "_" + clean["_time"].astype(str)
    clean_norm["_treattime"] = clean_norm["_treat"] + "_" + clean_norm["_time"].astype(str)

    def coverage(df):
        out = {}
        for key, g in df.groupby(["_treat", "_time"]):
            out[f"{key[0]}_{key[1]}"] = {
                "n_cells": int(len(g)), "n_cell_lines": int(g["_c"].nunique())}
        return {k: out[k] for k in sorted(out)}

    def all_time_lines(df):
        res = {}
        for treat in ["Tram", "DMSO"]:
            sub = df[df["_treat"] == treat]
            if len(sub) == 0:
                res[treat] = 0
                continue
            pv = sub.groupby(["_c", "_time"]).size().unstack(fill_value=0)
            res[treat] = {"n_lines": int(pv.shape[0]),
                          "n_lines_with_all_5_times": int((pv > 0).all(axis=1).sum())}
        return res

    def cells_per_condition(df):
        if len(df) == 0:
            return None
        g = df.groupby(["_c", "_treat", "_time"]).size()
        return {"n_conditions": int(len(g)), "min": int(g.min()),
                "median": float(g.median()), "max": int(g.max())}

    hashed_lines = set(clean["_c"])
    meta["hashed_timecourse_arm"] = {
        "n_rows_with_comma_time_label_drug": int(len(mix)),
        "perturbation_field_values": value_counts(mix["_p"]),
        "assignment_kind_counts": value_counts(mix["_kind"]),
        "n_hash_tag_vs_hash_assignment_disagree": int((mix["_ht"] != mix["_ha"]).sum()),
        "clean_single_label_cells": int(len(clean)),
        "clean_single_label_cells_normal_qc": int(len(clean_norm)),
        "coverage_all_cells": coverage(clean),
        "coverage_normal_qc": coverage(clean_norm),
        "lines_with_all_times_all_cells": all_time_lines(clean),
        "lines_with_all_times_normal_qc": all_time_lines(clean_norm),
        "cells_per_condition_all": cells_per_condition(clean),
        "cells_per_condition_normal_qc": cells_per_condition(clean_norm),
        "n_cell_lines_clean": len(hashed_lines),
        "clean_lines_equal_focal24": bool(hashed_lines == focal24),
        "dose_values_in_arm": value_counts(mix["_dose"]),
        "cell_quality_in_arm": value_counts(mix["_dq"]),
        "n_untreated_48hr_cells": int((clean["_treat"] == "Untreated").sum()),
        "field_conflicts": {
            "perturbation_says": "Trametinib for all rows (incl. hash labels DMSO_*/Untreated_*)",
            "dose_placeholder": "dose_value=0.1 uM for all rows incl. DMSO labels",
            "hash_tag_vs_assignment_differs_cells": int((mix["_ht"] != mix["_ha"]).sum()),
        },
        "note": ("per-cell time/treatment is recoverable from hash_assignment for single-tag cells "
                 "only; hash calls are not re-derived here; combo/multiplet cells are excluded; "
                 "batch/run metadata absent; samples are destructive snapshots, not trajectories"),
    }

    # ---- 24h-only drug arms: cell-line coverage and overlap with control set ----
    arms24 = {}
    for p in sorted(set(obs.loc[m24 & (type_col == "drug").to_numpy(), "_p"])):
        if p in set(per_pert):
            continue
        sub = obs[m24 & (obs["_p"] == p).to_numpy()]
        lines = set(sub["_c"].dropna())
        arms24[p] = {"n_cells": int(len(sub)), "n_cell_lines": len(lines),
                     "n_lines_overlapping_control115": len(lines & ctrl)}
    meta["time24_only_drug_arms"] = arms24

    # ---- DepMap / PRISM metadata joins (metadata only; no response files opened) ----
    prism_ti = os.path.join(ROOT, "data", "external", "prism_19q4", "raw",
                            "primary-screen-replicate-collapsed-treatment-info.csv")
    prism_ci = os.path.join(ROOT, "data", "external", "prism_19q4", "raw",
                            "primary-screen-cell-line-info.csv")
    prism = {"treatment_info_path": os.path.relpath(prism_ti, ROOT).replace(os.sep, "/"),
             "cell_line_info_path": os.path.relpath(prism_ci, ROOT).replace(os.sep, "/"),
             "note": "metadata columns only (drug names/doses, DepMap IDs); response matrices not opened"}
    if os.path.exists(prism_ti):
        ti = pd.read_csv(prism_ti, usecols=["name", "dose", "moa", "target"], low_memory=False)
        found = {}
        for nm in ["Bortezomib", "Trametinib", "Idasanutlin", "BRD3379"]:
            hit = ti[ti["name"].astype(str).str.strip().str.lower() == nm.lower()]
            found[nm] = {"n_rows": int(len(hit)), "doses": sorted({float(x) for x in hit["dose"]}),
                         "targets": sorted({str(x) for x in hit["target"].dropna()}),
                         "moa": sorted({str(x) for x in hit["moa"].dropna()})}
        prism["drug_name_matches"] = found
    if os.path.exists(prism_ci):
        ci = pd.read_csv(prism_ci, usecols=["row_name", "depmap_id"], low_memory=False)
        pids = set(ci["depmap_id"].astype("string").dropna())
        hids = set(obs["DepMap_ID"].astype("string").dropna())
        prism["n_primary_cell_lines"] = len(pids)
        prism["n_mixseq_depmap_ids"] = len(hids)
        prism["n_mixseq_ids_in_prism_primary"] = len(hids & pids)
        prism["n_hashed24_ids_in_prism_primary"] = len(
            set(clean["DepMap_ID"].astype("string")) & pids)
    meta["prism_metadata_check"] = prism

    # ---- prior derived assets (listing only; contents not opened) ----
    derived = []
    kh = os.path.join(ROOT, "data", "external", "kinetic_horizon_20261010")
    if os.path.isdir(kh):
        for dirpath, _dirnames, filenames in os.walk(kh):
            for fn in sorted(filenames):
                fp = os.path.join(dirpath, fn)
                derived.append({"path": os.path.relpath(fp, ROOT).replace(os.sep, "/"),
                                "bytes": os.path.getsize(fp)})
    meta["prior_derived_assets_listing_only"] = {
        "files": derived,
        "note": ("listing only; npz caches from a prior study (kinetic_horizon_20261010) appear to "
                 "hold derived pseudobulk/state/PRISM-matched arrays. Provenance, splits and response "
                 "values were NOT audited and NOT read in this metadata-only qualification; they cannot "
                 "be treated as certified functional endpoints."),
    }

    meta["limitations"] = [
        "Metadata-only: no expression matrix was read; no response statistics computed.",
        "h5ad obs has no explicit batch/plate/donor/run column; channel/hash_tag are multiplexing "
        "proxies only, and channel is missing for all exact-6h and 4-drug 24h cells.",
        "The 285 common keys are (perturbation, cell_line) at exact time labels '6' and '24'; channel or "
        "dose added to the key changes counts (see key_definition_sensitivity).",
        "The comma time labels are aggregation artifacts: the Trametinib arm's per-cell time/treatment is "
        "recoverable from hash_assignment for single-tag cells (3/6/12/24/48 h + DMSO controls), but the "
        "hash calls are not re-derived here and 2,339 combo + 136 unresolved cells are excluded.",
        "Dose metadata is a single placeholder value per arm (0.0 for BRD3379/control, 0.1 for Trametinib, "
        "2.5 for Bortezomib/Idasanutlin; the hashed arm records 0.1 even for DMSO labels) -> not certified.",
        "No independent functional endpoint (viability/apoptosis) is present in the h5ad, so decision-level "
        "questions cannot be evaluated on this asset alone.",
        "Cells at different time points are separate populations (destructive snapshots); no cell-level "
        "trajectory or lineage link exists in the asset.",
        "Prior derived caches (kinetic_horizon_20261010 npz) are listed only; provenance/splits/response "
        "values were not audited and are not used here.",
    ]

    adata.file.close()
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)
    print("WROTE", OUT)
    print(json.dumps({
        "n_obs": meta["h5ad_structure"]["n_obs"],
        "n_vars": meta["h5ad_structure"]["n_vars"],
        "common_keys_h5ad": meta["exact_6_24_from_h5ad"]["n_common_pert_cell_keys"],
        "common_keys_census": meta["census_replay"]["n_common_pert_cell_keys"],
        "per_pert": meta["exact_6_24_from_h5ad"]["per_perturbation_common_key_counts"],
        "normal_ge10_both": meta["common_key_design_match"]["n_keys_with_normal_cells_ge10_both_times"],
        "hashed_clean_cells": meta["hashed_timecourse_arm"]["clean_single_label_cells"],
        "hashed_coverage": meta["hashed_timecourse_arm"]["coverage_all_cells"],
        "hashed_lines_all_times": meta["hashed_timecourse_arm"]["lines_with_all_times_all_cells"],
        "hashed_lines_equal_focal24": meta["hashed_timecourse_arm"]["clean_lines_equal_focal24"],
        "depmap_overlap": meta["depmap_identity_join"].get("n_overlap"),
        "census_h5ad_identical": meta["census_vs_h5ad_agreement"]["common_key_sets_identical"],
        "prism_matches": meta["prism_metadata_check"].get("drug_name_matches"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
