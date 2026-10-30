"""R200-D5: metadata-only qualification + strict temporal-split design (NO fitting, NO effect run).

Hard constraints enforced by this script:
  * reads ONLY the Mix-seq h5ad metadata (obs/var columns, design-column values, QC flags,
    key counts) and file-level metadata of other local assets (paths/sizes/counts);
  * NEVER reads the expression matrix X values, obsm/layers, or any response/functional matrix;
  * NEVER fits a model, runs a prediction, or computes an effect statistic;
  * deterministic: sorted outputs, fixed seed constant, no timestamps, no random draws.

Output: d5.json (machine-readable qualification + split design).
"""
import hashlib
import json
import math
import os
import re

import anndata as ad
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(HERE, "d5.json")
H5AD = os.path.join(ROOT, "data", "external", "mixseq_scperturb", "mcfarland_2020.h5ad")

SEED = 20261027
DELTA_MIN = 0.10          # frozen operational minimum detectable/meaningful effect (Δ Spearman)
MIN_NORMAL_CELLS = 20     # pseudobulk condition eligibility
MIN_LINES = 20            # confirmatory minimum eligible cell lines

BACKGROUND = {
    "a3_meta": "research/2026-10-27-innovation-scouting/dynamic_route/a3_meta.json",
    "a3_qualification": "research/2026-10-27-innovation-scouting/dynamic_route/qualification.md",
    "a3_spec": "research/2026-10-27-innovation-scouting/dynamic_route/spec.md",
    "a3_protocol_v2": "research/2026-10-27-innovation-scouting/dynamic_route/protocol_draft_v2.md",
    "a3_revision": "research/2026-10-27-innovation-scouting/dynamic_route/REVISION_A3.md",
    "a3_challenge": "research/2026-10-27-innovation-scouting/dynamic_route/challenge_A3.md",
    "a3_cadence": "research/2026-10-27-innovation-scouting/dynamic_route/cadence_evidence.md",
    "r200_brief": "research/2026-10-27-innovation-round-r200/BRIEF.md",
    "direction_report": "research/2026-10-27-direction-mechanism-expansion/report.md",
    "mechanisms_v3": "research/2026-10-27-direction-mechanism-expansion/mechanisms_v3.md",
    "latest_evidence": "research/2026-10-27-direction-mechanism-expansion/latest_evidence.md",
    "errata_a3": "research/2026-10-27-conditional-shift/ERRATA_A3.md",
    "r199_brief": "research/2026-10-27-innovation-round-r199/BRIEF.md",
}

LOCAL_ASSETS = [
    "data/external/mixseq_scperturb",
    "data/external/tahoe_phenotype_20261010",
    "data/external/kinetic_horizon_20261010",
    "data/external/prism_19q4",
    "data/external/gdsc_combinations",
    "data/external/gdsc2_fitted",
    "data/external/vis2024_pancancer_combinations",
    "data/external/beataml2_20261017",
]

RESPONSE_WORDS = ["viab", "apop", "response", "effect", "ic50", "ic_50", "auc", "survival",
                  "growth", "inhibit", "kill", "death", "regrow", "ctg", "celltiter", "function"]
MORPH_WORDS = ["image", "imaging", "morph", "area", "shape", "texture", "pixel"]
LINK_WORDS = ["cell_id", "lineage", "track", "trajectory", "parent", "barcode_link", "lineage_id"]
EXPOSURE_WORDS = ["exposure", "duration", "treated_for", "exposure_time"]
BATCH_WORDS = ["batch", "plate", "plate_id", "well", "run_id", "lane", "sample_id", "donor"]
REPLICATE_WORDS = ["replicate", "rep", "bio_rep", "tech_rep", "donor", "passage"]


def sha256_file(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def file_meta(path):
    if not os.path.exists(path):
        return {"present": False}
    return {"present": True, "bytes": os.path.getsize(path), "sha256": sha256_file(path)}


def dir_meta(path, max_files=5000):
    if not os.path.isdir(path):
        return {"present": False}
    n = 0
    total = 0
    names = []
    for dirpath, _dirs, files in os.walk(path):
        for fn in files:
            n += 1
            total += os.path.getsize(os.path.join(dirpath, fn))
            if len(names) < 40:
                names.append(os.path.relpath(os.path.join(dirpath, fn), ROOT).replace(os.sep, "/"))
            if n >= max_files:
                break
        if n >= max_files:
            break
    return {"present": True, "n_files": n, "total_bytes": total, "first_files": names}


def value_counts(series):
    s = series.astype("string")
    vc = s.value_counts(dropna=False)
    return {str(k): int(v) for k, v in vc.items()}


def normalized_channel(x):
    s = "" if x is None else str(x)
    if s in ("nan", "<NA>", "None", ""):
        return None
    try:
        f = float(s)
        return str(int(f)) if f.is_integer() else str(f)
    except ValueError:
        return s


def mde_prerun(n):
    """Conservative pre-run MDE80 upper bound for a paired Δ under independent-error assumption,
    plus the across-model error correlation required for MDE80 ≤ δ_min."""
    if n is None or n < 2:
        return {"n": n, "mde80_upper": None, "required_r_err": None,
                "note": "n<2: not computable"}
    z = 1.959964 + 0.841621
    upper = z * math.sqrt(2.0 / (n - 1.0))
    req = 1.0 - (DELTA_MIN ** 2 * (n - 1.0)) / (2.0 * z ** 2)
    return {"n": int(n), "mde80_upper": round(upper, 3), "required_r_err": round(req, 3),
            "formula": "z*sqrt(2/(n-1)); r_err>=1-delta^2*(n-1)/(2*z^2)"}


def main():
    meta = {
        "meta": {
            "task": "task-88 R200-D5 early-state -> late-response temporal prediction boundary",
            "agent": "cellstate-lit",
            "scope": ("metadata-only resource qualification + strict temporal-split design; "
                      "NO model fitting, NO prediction run, NO expression/response value read"),
            "expression_matrix_read": False,
            "response_values_read": False,
            "model_fit": False,
            "seed": SEED,
            "delta_min": DELTA_MIN,
            "min_normal_cells": MIN_NORMAL_CELLS,
            "min_lines_confirmatory": MIN_LINES,
        },
        "inputs_sha256": {k: file_meta(os.path.join(ROOT, p)) for k, p in BACKGROUND.items()},
        "input_mixseq": file_meta(H5AD),
    }
    meta["inputs_sha256"]["mixseq_scperturb_dir"] = dir_meta(
        os.path.join(ROOT, "data", "external", "mixseq_scperturb"))

    # ---------- h5ad metadata (no expression values) ----------
    adata = ad.read_h5ad(H5AD, backed="r")
    obs = adata.obs.copy()
    var_cols = [str(c) for c in adata.var.columns]
    n_obs, n_vars = int(adata.n_obs), int(adata.n_vars)
    x_shape = [int(x) for x in adata.X.shape]
    obsm_keys = [str(k) for k in adata.obsm.keys()]
    layers_keys = [str(k) for k in adata.layers.keys()]
    uns_keys = [str(k) for k in adata.uns.keys()]
    raw_present = bool(adata.raw is not None)
    adata.file.close()

    obs_cols = [str(c) for c in obs.columns]
    for c in obs_cols:
        obs[c] = obs[c].astype("string")

    hit = {k: [c for c in obs_cols + var_cols if any(w in c.lower() for w in words)]
           for k, words in {"functional": RESPONSE_WORDS, "morphology": MORPH_WORDS,
                            "linkage": LINK_WORDS, "exposure": EXPOSURE_WORDS,
                            "batch": BATCH_WORDS, "replicate": REPLICATE_WORDS}.items()}

    meta["h5ad_structure"] = {
        "path": "data/external/mixseq_scperturb/mcfarland_2020.h5ad",
        "n_obs": n_obs, "n_vars": n_vars, "X_shape": x_shape,
        "X_values_read": False,
        "obsm_keys": obsm_keys, "layers_keys": layers_keys, "uns_keys": uns_keys,
        "raw_present": raw_present,
        "obs_columns": obs_cols, "var_columns": var_cols,
        "obs_index_unique": bool(obs.index.is_unique),
    }
    meta["columns"] = {
        "functional_endpoint_columns": hit["functional"],
        "morphology_or_imaging_columns": hit["morphology"],
        "same_cell_linkage_columns": hit["linkage"],
        "exposure_duration_columns": hit["exposure"],
        "batch_or_plate_columns": hit["batch"],
        "replicate_columns": hit["replicate"],
        "any_functional_endpoint": bool(hit["functional"]),
        "any_morphology": bool(hit["morphology"]),
        "any_same_cell_linkage": bool(hit["linkage"]),
        "any_exposure_record": bool(hit["exposure"]),
        "any_batch_or_plate_record": bool(hit["batch"]),
        "any_replicate_record": bool(hit["replicate"]),
    }

    # ---------- design counts: exact 6h / 24h ----------
    obs["_t"] = obs["time"]
    obs["_p"] = obs["perturbation"]
    obs["_c"] = obs["cell_line"]
    obs["_q"] = obs["cell_quality"]
    obs["_ch"] = obs["channel"].map(normalized_channel).astype("string")

    normal = obs["_q"] == "normal"
    sub6 = obs[obs["_t"] == "6"]
    sub24 = obs[obs["_t"] == "24"]
    n6 = (sub6[sub6["_q"] == "normal"].groupby(["_p", "_c"]).size()
          .rename("normal").reset_index())
    n24 = (sub24[sub24["_q"] == "normal"].groupby(["_p", "_c"]).size()
           .rename("normal").reset_index())
    dict6 = {(p, c): int(v) for p, c, v in n6.itertuples(index=False, name=None)}
    dict24 = {(p, c): int(v) for p, c, v in n24.itertuples(index=False, name=None)}

    keys6_all = set(zip(sub6["_p"], sub6["_c"]))
    keys24_all = set(zip(sub24["_p"], sub24["_c"]))
    common = keys6_all & keys24_all

    per_drug = {}
    for p in sorted({p for p, _ in common}):
        kk = [(p, c) for q, c in common if q == p]
        ge20 = [k for k in kk if dict6.get(k, 0) >= MIN_NORMAL_CELLS
                and dict24.get(k, 0) >= MIN_NORMAL_CELLS]
        ge10 = [k for k in kk if dict6.get(k, 0) >= 10 and dict24.get(k, 0) >= 10]
        both_norm = [min(dict6.get(k, 0), dict24.get(k, 0)) for k in kk]
        per_drug[p] = {
            "n_common_keys": len(kk),
            "n_keys_ge20_normal_both_times": len(ge20),
            "n_keys_ge10_normal_both_times": len(ge10),
            "normal_cells_per_key_min": min(both_norm),
            "normal_cells_per_key_max": max(both_norm),
        }

    control_ok = {c for (p, c) in common
                  if p == "control" and dict6.get((p, c), 0) >= MIN_NORMAL_CELLS
                  and dict24.get((p, c), 0) >= MIN_NORMAL_CELLS}
    per_drug_eligible = {}
    for p in sorted({p for p, _ in common if p != "control"}):
        lines = sorted({c for (q, c) in common
                        if q == p and dict6.get((q, c), 0) >= MIN_NORMAL_CELLS
                        and dict24.get((q, c), 0) >= MIN_NORMAL_CELLS and c in control_ok})
        per_drug_eligible[p] = {"n_eligible_lines": len(lines), "lines": lines}

    meta["v1_exact_6_24"] = {
        "n_time6_cells": int(len(sub6)),
        "n_time24_cells": int(len(sub24)),
        "n_keys_time6": len(keys6_all),
        "n_keys_time24": len(keys24_all),
        "n_common_keys": len(common),
        "n_common_cell_lines": len({c for _, c in common}),
        "per_drug": per_drug,
        "per_drug_eligible_with_time_matched_control": per_drug_eligible,
        "control_lines_ge20_both_times": len(control_ok),
        "eligibility_rule": ">=20 QC-normal cells per drug key AND per time-matched control key, at both 6h and 24h",
    }

    # ---------- hashed Trametinib 5-timepoint arm (metadata labels only) ----------
    mix = obs[obs["_t"] == "3, 6, 12, 24, 48"].copy()
    rx = re.compile(r"^(Tram|DMSO|Untreated)_(\d+)hr$")

    def parse_hash(x):
        s = str(x)
        if s in ("", "nan", "<NA>", "None", "multiplet", "unknown") or "," in s:
            return None
        m = rx.match(s)
        return (m.group(1), int(m.group(2))) if m else None

    mix["_parsed"] = mix["hash_assignment"].map(parse_hash)
    mix["_treat"] = mix["_parsed"].map(lambda v: v[0] if v else None)
    mix["_time"] = mix["_parsed"].map(lambda v: v[1] if v else None)
    clean = mix[mix["_treat"].notna()].copy()
    clean_norm = clean[clean["_q"] == "normal"].copy()

    cond_counts = (clean_norm.groupby(["_c", "_treat", "_time"]).size()
                   .rename("n").reset_index())
    nval = {(c, t, tm): int(n) for c, t, tm, n in
            cond_counts.itertuples(index=False, name=None)}
    lines_all = sorted(clean_norm["_c"].unique())
    cond_label_counts = (clean.groupby(["_treat", "_time"])["hash_assignment"].nunique()
                         .rename("n_labels").reset_index())

    def eligible_lines(target, inputs):
        need = [(tm, t) for tm in ["Tram", "DMSO"] for t in list(inputs) + [target]]
        out = []
        for c in lines_all:
            if all(nval.get((c, tm, t), 0) >= MIN_NORMAL_CELLS for tm, t in need):
                out.append(c)
        return out

    contrasts = {}
    for target, input_sets in {
        24: [(6,), (6, 12), (3, 6, 12)],
        48: [(6,), (6, 12), (6, 12, 24)],
    }.items():
        for inputs in input_sets:
            key = f"target{target}h_inputs{'+'.join(str(x) + 'h' for x in inputs)}"
            lines = eligible_lines(target, inputs)
            contrasts[key] = {
                "target_h": target,
                "input_times_h": list(inputs),
                "time_order_ok": all(t < target for t in inputs),
                "n_eligible_lines": len(lines),
                "lines": lines,
            }
    # paired sets for nested contrasts
    paired = {}
    for target in (24, 48):
        e1 = set(contrasts[f"target{target}h_inputs6h"]["lines"])
        e2 = set(contrasts[f"target{target}h_inputs6h+12h"]["lines"])
        paired[f"target{target}h_E1_vs_E2_paired_lines"] = sorted(e1 & e2)
        if target == 48:
            e3 = set(contrasts["target48h_inputs6h+12h+24h"]["lines"])
            paired["target48h_E2_vs_E3_paired_lines"] = sorted(e2 & e3)

    def hash_kind(x):
        s = str(x)
        if s in ("", "nan", "<NA>", "None"):
            return "missing"
        if s in ("multiplet", "unknown"):
            return "unresolved"
        return "combo" if "," in s else ("single" if rx.match(s) else "other")

    kinds = mix["hash_assignment"].map(hash_kind)
    meta["v2_hashed_arm"] = {
        "n_rows_with_aggregate_time_label": int(len(mix)),
        "assignment_kind_counts": value_counts(kinds),
        "n_clean_single_label_cells": int(len(clean)),
        "n_clean_single_label_normal_cells": int(len(clean_norm)),
        "n_cell_lines_clean": len(lines_all),
        "clean_lines_equal_focal24": len(lines_all) == 24,
        "coverage_normal_cells": {
            f"{tr}_{tm}": {"n_cells": int(len(clean_norm[(clean_norm["_treat"] == tr)
                                                       & (clean_norm["_time"] == tm)])),
                           "n_lines": int(clean_norm[(clean_norm["_treat"] == tr)
                                                     & (clean_norm["_time"] == tm)]["_c"].nunique())}
            for tr in ["Tram", "DMSO", "Untreated"]
            for tm in sorted(clean_norm.loc[clean_norm["_treat"] == tr, "_time"].unique())
        },
        # one hash label per (treatment,time) => no sample-level replicates in this arm
        "hash_labels_per_condition": {
            f"{tr}_{tm}": int(cond_label_counts[(cond_label_counts._treat == tr)
                                               & (cond_label_counts._time == tm)]["n_labels"].iloc[0])
            for tr in ["Tram", "DMSO", "Untreated"]
            for tm in sorted(cond_label_counts.loc[cond_label_counts._treat == tr, "_time"].unique())
        },
        "n_conditions_with_one_sample_label": int(
            ((cond_label_counts["n_labels"] == 1)).sum()),
        "temporal_contrasts": contrasts,
        "nested_paired_line_sets": {k: {"n": len(v), "lines": v} for k, v in paired.items()},
        "eligibility_rule": (">=20 QC-normal single-hash-label cells for Tram AND time-matched DMSO "
                             "at every input time and the target time"),
    }

    # ---------- early/late presence + same-cell / same-intervention ----------
    obs_index = obs.index.astype("string")
    meta["early_late_presence"] = {
        "early_rna": {"present": True, "time_label": "6", "cells": int(len(sub6)),
                      "note": "RNA pseudobulk possible; morphology not present"},
        "early_morphology": {"present": False, "reason": "no imaging/morphology columns or obsm keys"},
        "late_molecular_rna": {"present": True, "time_label": "24", "cells": int(len(sub24))},
        "late_functional_viability_regrowth": {
            "present": False,
            "reason": ("no viability/apoptosis/regrowth/IC50/response column in obs/var; "
                       "obsm/layers/uns empty; local Mix-seq asset is a transcriptome h5ad"),
        },
        "same_cell_early_late": {
            "present": False,
            "reason": ("destructive snapshots: obs index is unique across all 182,875 cells, so no "
                       "barcode appears at both 6h and 24h; no lineage/cell-id linkage column"),
            "obs_index_unique": bool(obs.index.is_unique),
            "n_obs_index": int(obs_index.nunique()),
        },
        "same_intervention_same_key": {
            "present": True,
            "note": ("the 285 keys share the same perturbation name at 6h and 24h; this is key-level "
                     "matching, not same-cell matching"),
        },
        "time_matched_control": {
            "present": True,
            "note": "control keys exist at both 6h and 24h (115 keys each) for the non-hashed arm",
        },
    }

    # ---------- exposure / dose / batch / repeat / missingness ----------
    dose_tab = (obs.groupby(["_p", "dose_value", "dose_unit"], dropna=False, observed=True).size()
                .reset_index(name="cells"))
    dose_rows = [{"perturbation": str(p),
                  "dose_value": "" if pd.isna(d) else str(d),
                  "dose_unit": "" if pd.isna(u) else str(u),
                  "cells": int(n)}
                 for p, d, u, n in dose_tab.itertuples(index=False, name=None) if int(n) > 0]
    dose_rows = sorted(dose_rows, key=lambda r: (r["perturbation"], r["dose_value"]))
    channel_by_time = {}
    for lbl, sub in [("6", sub6), ("24", sub24)]:
        chv = sub["_ch"].value_counts(dropna=False)
        channel_by_time[lbl] = {
            "n_cells": int(len(sub)),
            "n_missing_channel": int((sub["_ch"].isna() | (sub["_ch"] == "nan")).sum()),
            "value_counts": {str(k): int(v) for k, v in chv.items()},
        }
    meta["exposure_dose_batch"] = {
        "exposure_duration_record": {"present": False,
                                     "note": ("no exposure/duration column; `time` is a harvest/time label; "
                                              "treatment start synchrony and exposure duration unverified")},
        "dose_record": {"present": True, "dose_units": value_counts(obs["dose_unit"]),
                        "dose_rows_nonzero": dose_rows},
        "batch_plate_record": {"present": False,
                               "note": "no batch/plate/well/run/donor columns"},
        "channel_record": {"present": True, "n_unique": int(obs["_ch"].nunique()),
                           "availability_by_time": channel_by_time,
                           "note": "channel missing for all 6h cells; partially present at 24h"},
        "hash_record": {"hash_tag_unique": int(obs["hash_tag"].nunique()),
                        "hash_assignment_unique": int(obs["hash_assignment"].nunique())},
    }
    ge10 = 0
    for (p, c) in common:
        if dict6.get((p, c), 0) >= 10 and dict24.get((p, c), 0) >= 10:
            ge10 += 1
    meta["repeats_and_missingness"] = {
        "n_obs": n_obs,
        "obs_index_unique": bool(obs.index.is_unique),
        "duplicate_obs_index": int(n_obs - obs.index.nunique()),
        "cell_quality_counts": value_counts(obs["_q"]),
        "n_normal_cells": int((obs["_q"] == "normal").sum()),
        "n_non_normal_cells": int((obs["_q"] != "normal").sum()),
        "v1_keys_ge10_normal_both_times": ge10,
        "v1_ge20_per_key": {p: v["n_keys_ge20_normal_both_times"] for p, v in per_drug.items()},
        "v2_one_sample_label_per_condition": meta["v2_hashed_arm"]["n_conditions_with_one_sample_label"],
        "explicit_replicate_column": False,
        "note": ("no replicate/donor/passage columns; hashed arm has exactly one hash sample label per "
                 "(treatment,time); non-hashed 6/24 arms have no sample label at all"),
    }

    # ---------- time-axis strictness ----------
    meta["time_axis_strictness"] = {
        "same_plate_or_batch_pairing": {"verified": False,
                                        "reason": "no plate/batch/run column; channel missing at 6h"},
        "early_late_channel_overlap": {"present": False,
                                       "note": "no common channel identifiers between 6h and 24h cells"},
        "hash_labels_for_exact_6_24": {"present": False,
                                       "note": "hash_tag/hash_assignment are nan for all exact 6h/24h cells"},
        "hashed_multi_time_arm_run_record": {"present": False,
                                             "note": ("one hash label per (treatment,time) is consistent "
                                                      "with multiplexing, but no run/plate/batch id exists")},
        "mixed_time_label_rows": {
            "n_cells_total": int((obs["_t"].str.contains(",", regex=False)).sum()),
            "n_cells_trametinib_arm": int(len(mix)),
            "n_cells_crispr_arm": int(((obs["_t"] == "72, 96")).sum()),
            "note": ("comma-joined labels are aggregation artifacts; the Trametinib arm's per-cell "
                     "treatment/time is recoverable from hash_assignment for single-tag cells; "
                     "the CRISPR arm is not used in D5"),
        },
        "verdict": "same-plate/same-batch pairing NOT verified; time-axis strictness unverified",
    }

    # ---------- functional endpoint qualification ----------
    local_assets = {}
    for rel in LOCAL_ASSETS:
        stats = dir_meta(os.path.join(ROOT, rel))
        stats["role"] = {
            "data/external/mixseq_scperturb": "primary time-resolved transcriptome asset (h5ad)",
            "data/external/tahoe_phenotype_20261010": ("different perturbation atlas; morphology/relative "
                                                      "survival derived endpoints, NOT matched to Mix-seq"),
            "data/external/kinetic_horizon_20261010": ("prior-study derived caches; provenance/splits "
                                                       "unverified; not a certified functional endpoint"),
            "data/external/prism_19q4": ("viability screen response matrices; different assay/time/dose, "
                                         "NOT time-matched to Mix-seq 6h/24h"),
            "data/external/gdsc_combinations": "combination ΔEMAX resource; not Mix-seq time-matched",
            "data/external/gdsc2_fitted": "monotherapy IC50 resource (local dir may be empty)",
            "data/external/vis2024_pancancer_combinations": "combination resource; not Mix-seq time-matched",
            "data/external/beataml2_20261017": "patient ex vivo resource; not Mix-seq time-matched",
        }.get(rel, "candidate only")
        local_assets[rel] = stats
    meta["functional_endpoint_qualification"] = {
        "h5ad_functional_endpoint_present": False,
        "local_candidate_assets": local_assets,
        "local_candidate_assets_note": ("file names/sizes only; no response/functional matrix contents were read; "
                                        "none is matched to the Mix-seq cells x interventions x timepoints"),
        "matched_late_functional_endpoint": False,
        "conclusion": ("no local functional readout (viability/apoptosis/regrowth) matched to the Mix-seq "
                       "cells x interventions x timepoints; RNA proxy is NOT a functional endpoint; "
                       "functional branch is not_qualified/data_unavailable"),
        "not_claimed": ("local absence is not evidence about the original public study's other outputs; "
                        "only the local scPerturb h5ad was qualified"),
    }

    # ---------- strict split design ----------
    def fold_manifest(lines):
        lines = sorted(lines)
        return {str(i % 5): [c for j, c in enumerate(lines) if j % 5 == i % 5] for i in range(5)}

    v1_folds = {p: fold_manifest(v["lines"]) for p, v in per_drug_eligible.items()}
    v2_folds = {}
    for key, c in contrasts.items():
        v2_folds[key] = {"folds": fold_manifest(c["lines"]), "n_lines": len(c["lines"])}
    fold_hash = hashlib.sha256(json.dumps({"v1": v1_folds, "v2": v2_folds},
                                          sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    meta["split_design"] = {
        "seed": SEED,
        "unit_of_replication": "cell line (not key/cell/timepoint)",
        "v1_outer_split": "leave-cell-line-out 5 folds; eligible lines sorted, fold = index % 5",
        "v1_inner_split": "leave-cell-line-out 5 folds inside training lines only",
        "v1_folds": v1_folds,
        "v2_outer_split": "target-time fixed; strictly earlier input times only; leave-cell-line-out 5 folds",
        "v2_inner_split": "leave-cell-line-out 5 folds inside training lines",
        "v2_folds": v2_folds,
        "forbidden": [
            "any target-time or future-time feature in input (code assertion)",
            "random row/key split instead of cell-line-grouped split",
            "preprocessing/feature selection/gene set fitted on test lines",
            "using target-time labels to select hyperparameters or genes",
        ],
        "manifest_sha256": fold_hash,
    }

    # ---------- primary contrasts + gates ----------
    v1_n = {p: v["n_eligible_lines"] for p, v in per_drug_eligible.items()}
    v2_n = {k: c["n_eligible_lines"] for k, c in contrasts.items()}
    meta["primary_contrasts"] = {
        "V1_early6h_vs_static": {
            "target": "24h molecular effect (pseudobulk logFC vs time-matched control)",
            "per_drug_n": v1_n,
            "primary_statistic": ("mean over 4 drugs of Δρ_d = ρ(early-6h model, observed 24h effect score) "
                                  "− ρ(static model, observed 24h effect score), equal weight per drug"),
            "status": "confirmatory-development (all 4 drugs n>=20)",
            "forbidden_arms": ["C3 two-snapshot (only V2)", "any 24h-derived input", "future-time features"],
        },
        "V1_sufficiency_gap": {
            "definition": ("gap = ρ_oracle(24h) − ρ_early(6h); report per drug and mean; "
                           "oracle is not a candidate model"),
            "role": "descriptive (no pass/fail); used to report whether one early snapshot is sufficient within precision",
        },
        "V2_extra_early_snapshot": {
            "contrasts": [
                {"target_h": 24, "E1": "inputs 6h", "E2": "inputs 6h+12h",
                 "n_E1": v2_n["target24h_inputs6h"], "n_E2": v2_n["target24h_inputs6h+12h"],
                 "paired_n": len(meta["v2_hashed_arm"]["nested_paired_line_sets"]["target24h_E1_vs_E2_paired_lines"])},
                {"target_h": 48, "E1": "inputs 6h", "E2": "inputs 6h+12h", "E3": "inputs 6h+12h+24h",
                 "n_E1": v2_n["target48h_inputs6h"], "n_E2": v2_n["target48h_inputs6h+12h"],
                 "n_E3": v2_n["target48h_inputs6h+12h+24h"],
                 "paired_n_E1_E2": len(meta["v2_hashed_arm"]["nested_paired_line_sets"]["target48h_E1_vs_E2_paired_lines"]),
                 "paired_n_E2_E3": len(meta["v2_hashed_arm"]["nested_paired_line_sets"]["target48h_E2_vs_E3_paired_lines"])},
            ],
            "status": "exploratory only (n<20 eligible lines in every contrast; no pass/fail verdict)",
            "primary_statistic": "paired Δρ = ρ(E2) − ρ(E1) per target, across eligible lines",
            "capacity_control": ("same-dimension random/noise features added to E1 (or E2-second-time shuffled) "
                                 "must not reproduce Δρ; otherwise the increment is capacity, not time information"),
        },
        "functional_route": {
            "status": "not_qualified / data_unavailable",
            "reason": "no late functional (viability/regrowth/apoptosis) readout matched to the same Mix-seq cells/interventions",
        },
    }

    meta["gates"] = {
        "delta_min": DELTA_MIN,
        "operational_definition": ("Δ Spearman = 0.10 corresponds to ~1–2 stable position changes in a top-5 "
                                   "line list at n=15–95; smaller increments would not change a development action; "
                                   "fixed before any run and not changed after seeing results"),
        "G0_eligibility": {
            "rule": f"V1: every drug has >= {MIN_LINES} eligible lines (actual {v1_n}); "
                    f"V2: every contrast has >= {MIN_LINES} eligible lines (actual {v2_n})",
            "V1_status": "pass" if all(n >= MIN_LINES for n in v1_n.values()) else "fail",
            "V2_status": "exploratory_only" if any(n < MIN_LINES for n in v2_n.values()) else "pass",
        },
        "G1_split_half_reliability": {
            "rule": "Spearman–Brown rho_sb >= delta_min + MDE80 computed from target-condition cell split-half",
            "fail_semantics": "evaluation_cannot_distinguish",
        },
        "G2_room": {
            "rule": "room = rho_oracle − rho_static >= max(delta_min, MDE80)",
            "fail_semantics": "evaluation_cannot_distinguish",
        },
        "G3_MDE80": {
            "rule": "MDE80(paired Δ, cell-line cluster bootstrap, 1,000 draws, seed 20261027) <= delta_min",
            "prerun_upper_bounds": {"V1_per_drug": {p: mde_prerun(n) for p, n in v1_n.items()},
                                    "V2_contrasts": {k: mde_prerun(n) for k, n in v2_n.items()}},
            "fail_semantics": "evaluation_cannot_distinguish",
        },
        "G4_primary_effect": {
            "rule": "V1 mean Δ >= delta_min and 95% CI lower bound > 0; V2 only descriptive (exploratory)",
            "fail_semantics": "no_increment (V1)",
        },
        "G5_leakage_audit": {
            "rule": ("target/future time absent from inputs; V1 model set excludes two-snapshot C3; "
                     "folds grouped by cell line; preprocessing only on training folds; assertions in code"),
            "fail_semantics": "design_invalid",
        },
    }

    meta["null_models_design"] = {
        "N0_mean_baseline": "per drug/time mean of target effect",
        "N1_cell_shuffle": "permute cell-line labels of early features; ρ should be ~0",
        "N2_intervention_shuffle_V1": "permute drug labels of early features; preserves marginal but breaks drug specificity",
        "N3_time_shuffle_V2": ("permute earlier-time labels among allowed earlier times of the same "
                               "(line,treatment) — tests time specificity; only meaningful where >=2 earlier times exist"),
        "N4_capacity_control_V2": ("add matched-dimension random/noise features to E1 (or replace the "
                                   "second time with shuffled features); Δρ must not be reproduced"),
        "N5_future_leak_sentinel": ("replace early features by target-time features; if this does NOT raise ρ vs early, "
                                    "the pipeline/metric is broken (positive control for information flow)"),
        "N6_static_capacity": "same-dimension random gene block for the static baseline",
    }

    meta["failure_classes"] = [
        "data_unavailable",
        "design_invalid",
        "evaluation_cannot_distinguish",
        "no_increment",
        "exploratory_only",
        "time_axis_unverified",
        "functional_route_not_qualified",
        "identifiability_unsupported",
    ]
    meta["stop_conditions"] = [
        "any G1–G3 gate fails -> evaluation_cannot_distinguish; stop L1; do not report a negative",
        "G4 fails (early ≈ static) -> stop dynamic-necessity claims; retain description",
        "V2 extra-snapshot Δρ CI includes 0 / capacity control reproduces it -> no extra-early-time increment",
        "functional route lacks matched late functional endpoint -> stop functional/latency claims; keep molecular branch",
        "no batch/exposure/same-cell records -> no absolute time-course/same-cell claims (time_axis_unverified)",
        "leakage audit fails -> design_invalid; stop and fix before any run",
        "no post-hoc threshold/endpoint/split changes; no replacing a failed endpoint",
    ]

    meta["verdicts"] = {
        "molecular_temporal_route": {
            "verdict": "qualified_with_conditions",
            "conditions": [
                "only 6h→24h RNA-to-RNA development (V1, 4 drugs; 95/22/24/24 eligible lines) and the Trametinib 5-timepoint arm as exploratory",
                "no functional endpoint: RNA proxy is not viability/regrowth",
                "no same-cell early–late pairing (destructive snapshots)",
                "same-plate/same-batch and exposure duration not certified (time_axis_unverified)",
                "no replicate samples in the hashed arm; no independent-culture record",
                "no absolute time-course/path/trajectory/mechanism/decision claims",
            ],
        },
        "functional_route": {
            "verdict": "not_qualified",
            "failure_class": "data_unavailable",
            "reason": "no late functional outcome matched to the same cells/interventions/timepoints",
        },
        "overall_D5": {
            "verdict": "qualified_with_conditions",
            "scope": "molecular temporal prediction development only; functional/path/mechanism/decision claims not qualified",
            "recommend_independent_challenge": True,
            "recommend_effect_run": False,
        },
    }

    meta["background_boundaries"] = {
        "old_A3_dynamic_route": ("A3v2 L1-feasible/L2-blocked is background only; this D5 qualification re-derives "
                                 "counts from the h5ad metadata; uncertified A3 parts are not reused as evidence"),
        "r200_brief": "D5 is a design/qualification task; effect run only after independent challenge (R200 discipline)",
        "c176_r197_revocation": ("C176/C177: R196 'replicated_under_audit' revoked and R197 v1 protocol void; "
                                 "these do not establish or exclude temporal predictability; do not cite old verdicts"),
        "c179_r197v2": ("R197v2 0.2073→0.7206 is an unverified descriptive quantity (C179); not evidence for temporal structure"),
        "c181_r199_a1": "R199 A1 relations_check failed frozen coverage gate -> data_unavailable; not evidence against relations",
        "errata_a3_r195": ("R195/A3 not_qualified applies only to its frozen large-scale cross-screen design; not a general "
                           "exclusion of narrower temporal questions"),
        "no_claims": ["no novelty", "no cell-state mechanism", "no migration", "no decision benefit", "no true trajectory"],
    }

    meta["limits"] = [
        "metadata-only: no expression matrix read, no response read, no model fit, no prediction run",
        "h5ad is a scPerturb-processed transcriptome asset; no local functional endpoint matched to it",
        "destructive snapshots: no same-cell early–late linkage; obs index unique across 182,875 cells",
        "no batch/plate/run/exposure columns; channel missing at 6h; same-plate pairing unverified",
        "hashed arm has one sample label per condition -> no sample-level replicates",
        "mixed comma time labels resolved only via hash_assignment; hash calls not re-derived",
        "nested contrasts share lines; V2 n<20 => exploratory only",
        "local absence of functional readouts is not a claim about the original public study's other outputs",
        "no novel method/mechanism claim; bounded background only",
    ]

    # script self-hash for provenance (deterministic output)
    meta["script"] = {"path": os.path.relpath(os.path.abspath(__file__), ROOT).replace(os.sep, "/"),
                      "sha256": sha256_file(os.path.abspath(__file__))}

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2, sort_keys=True)
    print("WROTE", OUT)
    print(json.dumps({
        "n_obs": n_obs, "n_vars": n_vars,
        "v1_common_keys": len(common),
        "v1_eligible": {p: v["n_eligible_lines"] for p, v in per_drug_eligible.items()},
        "v2_clean_cells": int(len(clean)),
        "v2_contrasts_n": v2_n,
        "functional_endpoint": False,
        "verdicts": {k: v["verdict"] for k, v in meta["verdicts"].items()},
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
