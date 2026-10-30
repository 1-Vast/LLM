"""R200-D5.1 revision: metadata-only revision of D5 v0.1 per challenge_D5.md (5 must-fix).

NO effect run, NO prediction fitting, NO expression/response matrix reading.
Reads: v0.1 artifacts (read-only, for SHA/input registry + cross-check), challenge_D5.md,
       Mix-seq h5ad obs/var metadata only.
Writes: d5_v0_2.json (deterministic; sort_keys; no timestamps; two runs byte-identical).

Fixes (challenge_D5.md §2):
  1. BRD3379 (0.0 uM) excluded from V1 primary; V1 primary = 3 active drugs
     (Bortezomib n=22 / Idasanutlin n=24 / Trametinib n=24); BRD3379 = zero-dose/vehicle-like
     control/secondary only.
  2. V2 paired_n corrected to paired cell-line counts (target24h E1/E2=15; target48h E1/E2=16,
     E2/E3=15) with explicit paired line sets; the v0.1 `paired_n=2` bug is documented.
  3. G0 adds an active-dose/treatment-identity gate (metadata-level; BRD3379 does not pass).
  4. v0.1 4-drug confirmatory status withdrawn; MDE table lists only the 3 active drugs.
  5. Pre-execution detail checklist added (loading/QC/pseudobulk/folds/paired sets/null/future
     sentinel/B1-B8 tuning/determinism/schema/measured-MDE pre-certification/failure template/G5).
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
H5AD = os.path.join(ROOT, "data", "external", "mixseq_scperturb", "mcfarland_2020.h5ad")
V01 = {
    "d5.py": "d5.py",
    "d5.json": "d5.json",
    "PROTOCOL_D5.md": "PROTOCOL_D5.md",
    "report_d5.md": "report_d5.md",
    "record_d5.md": "record_d5.md",
    "usage_d5.json": "usage_d5.json",
    "challenge_D5.md": "challenge_D5.md",
}
OUT = os.path.join(HERE, "d5_v0_2.json")

SEED = 20261027
DELTA_MIN = 0.10
MIN_NORMAL_CELLS = 20
MIN_LINES = 20
ACTIVE_DRUGS = ["Bortezomib", "Idasanutlin", "Trametinib"]
ZERO_DOSE_DRUG = "BRD3379"
CONTROL_ARM = "control"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def file_meta(path):
    return {"present": os.path.exists(path),
            "bytes": os.path.getsize(path) if os.path.exists(path) else None,
            "sha256": sha256_file(path) if os.path.exists(path) else None}


def value_counts(series):
    s = series.astype("string")
    vc = s.value_counts(dropna=False)
    return {str(k): int(v) for k, v in vc.items()}


def norm_channel(x):
    s = "" if x is None else str(x)
    if s in ("nan", "<NA>", "None", ""):
        return None
    try:
        f = float(s)
        return str(int(f)) if f.is_integer() else str(f)
    except ValueError:
        return s


def mde_prerun(n):
    if n is None or n < 2:
        return {"n": n, "mde80_upper": None, "required_r_err": None}
    z = 1.959964 + 0.841621
    upper = z * math.sqrt(2.0 / (n - 1.0))
    req = 1.0 - (DELTA_MIN ** 2 * (n - 1.0)) / (2.0 * z ** 2)
    return {"n": int(n), "mde80_upper": round(upper, 3), "required_r_err": round(req, 3),
            "formula": "z*sqrt(2/(n-1)); r_err>=1-delta^2*(n-1)/(2*z^2)"}


def fold_manifest(lines):
    lines = sorted(lines)
    return {str(i): [c for j, c in enumerate(lines) if j % 5 == i] for i in range(5)}


def main():
    out = {
        "meta": {
            "task": "task-96 R200-D5.1 revision of D5 v0.1 per challenge_D5.md (revise, 5 must-fix)",
            "agent": "cellstate-lit",
            "revision_of": "R200-D5 v0.1 (PROTOCOL_D5.md / d5.py / d5.json / report_d5.md / record_d5.md / usage_d5.json)",
            "status": "design revision only; not an effect run; not a new qualification",
            "scope": ("metadata-only revision: re-derive active-dose classification, V1 3-active-drug primary, "
                      "V2 paired cell-line counts, G0 active-dose gate, execution checklist; "
                      "NO expression/response read, NO model fitting, NO prediction run"),
            "expression_matrix_read": False,
            "response_values_read": False,
            "model_fit": False,
            "seed": SEED,
            "delta_min": DELTA_MIN,
        },
        "inputs_sha256": {name: file_meta(os.path.join(HERE, name)) for name in V01},
        "input_mixseq": file_meta(H5AD),
    }
    for name in V01:
        out["inputs_sha256"][name]["path"] = os.path.relpath(os.path.join(HERE, name), ROOT).replace(os.sep, "/")

    # ---------- load v0.1 JSON for cross-check ----------
    v01 = json.load(open(os.path.join(HERE, "d5.json"), encoding="utf-8"))

    # ---------- h5ad metadata only ----------
    adata = ad.read_h5ad(H5AD, backed="r")
    obs = adata.obs.copy()
    n_obs, n_vars = int(adata.n_obs), int(adata.n_vars)
    x_shape = [int(x) for x in adata.X.shape]
    obsm_keys = [str(k) for k in adata.obsm.keys()]
    layers_keys = [str(k) for k in adata.layers.keys()]
    uns_keys = [str(k) for k in adata.uns.keys()]
    adata.file.close()
    for c in obs.columns:
        obs[c] = obs[c].astype("string")
    obs["_t"] = obs["time"]
    obs["_p"] = obs["perturbation"]
    obs["_c"] = obs["cell_line"]
    obs["_q"] = obs["cell_quality"]

    sub6 = obs[obs["_t"] == "6"]
    sub24 = obs[obs["_t"] == "24"]
    n6 = (sub6[sub6["_q"] == "normal"].groupby(["_p", "_c"]).size()
          .rename("n").reset_index())
    n24 = (sub24[sub24["_q"] == "normal"].groupby(["_p", "_c"]).size()
           .rename("n").reset_index())
    dict6 = {(p, c): int(v) for p, c, v in n6.itertuples(index=False, name=None)}
    dict24 = {(p, c): int(v) for p, c, v in n24.itertuples(index=False, name=None)}
    keys6 = set(zip(sub6["_p"], sub6["_c"]))
    keys24 = set(zip(sub24["_p"], sub24["_c"]))
    common = keys6 & keys24
    arms = sorted({p for p, _ in common})
    control_ok = {c for (p, c) in common
                  if p == CONTROL_ARM and dict6.get((p, c), 0) >= MIN_NORMAL_CELLS
                  and dict24.get((p, c), 0) >= MIN_NORMAL_CELLS}
    eligible_lines = {}
    for p in arms:
        if p == CONTROL_ARM:
            continue
        lines = sorted({c for (q, c) in common
                        if q == p and dict6.get((q, c), 0) >= MIN_NORMAL_CELLS
                        and dict24.get((q, c), 0) >= MIN_NORMAL_CELLS and c in control_ok})
        eligible_lines[p] = lines

    # ---------- active-dose / treatment-identity classification (metadata only) ----------
    arm_meta = {}
    for p in arms:
        rows = obs[(obs["_p"] == p) & obs["_t"].isin(["6", "24"])]
        doses = sorted({str(x) for x in rows["dose_value"].dropna().unique()})
        units = sorted({str(x) for x in rows["dose_unit"].dropna().unique()})
        chembl = sorted({str(x) for x in rows["chembl-ID"].dropna().unique()})
        dose_numeric = []
        for d in doses:
            try:
                dose_numeric.append(float(d))
            except ValueError:
                pass
        dose_positive = bool(dose_numeric) and all(x > 0 for x in dose_numeric)
        has_identity_annotation = bool(chembl)
        active_evidence = dose_positive and bool(units) and has_identity_annotation
        arm_meta[p] = {
            "dose_values": doses, "dose_units": units, "chembl_ids": chembl,
            "dose_positive": dose_positive,
            "treatment_identity_annotation_present": has_identity_annotation,
            "active_dose_metadata_check": "pass" if active_evidence else "fail",
            "certification_level": "metadata-only (dose>0 + ChEMBL annotation); NOT an independent dose/vehicle identity assay",
        }
    for p in [ZERO_DOSE_DRUG, CONTROL_ARM]:
        arm_meta[p]["role"] = ("zero-dose/vehicle-like control; excluded from active primary; "
                               "secondary/descriptive only") if p == ZERO_DOSE_DRUG else "reference control arm"
    for p in ACTIVE_DRUGS:
        arm_meta[p]["role"] = "active drug (metadata-level verification)"
    # derive active primary drugs from metadata (do not rely on the hardcoded list)
    active_drugs = [p for p in arms
                    if p not in (ZERO_DOSE_DRUG, CONTROL_ARM)
                    and arm_meta[p]["active_dose_metadata_check"] == "pass"
                    and len(eligible_lines.get(p, [])) >= MIN_LINES]
    excluded_active = [p for p in [ZERO_DOSE_DRUG, CONTROL_ARM] if p in arm_meta]

    # ---------- V1 folds: active primary + BRD3379 secondary ----------
    v1_folds_active = {p: fold_manifest(eligible_lines[p]) for p in active_drugs}
    v1_folds_brd = ({ZERO_DOSE_DRUG: fold_manifest(eligible_lines[ZERO_DOSE_DRUG])}
                    if ZERO_DOSE_DRUG in eligible_lines else {})
    active_primary_manifest_sha = hashlib.sha256(
        json.dumps(v1_folds_active, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    # ---------- V2 hashed arm: re-derive contrasts and PAIRED LINE COUNTS ----------
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
    clean_norm = clean[clean["_q"] == "normal"]
    lines_all = sorted(clean_norm["_c"].unique())
    nval = {(c, t, tm): int(n) for c, t, tm, n in
            clean_norm.groupby(["_c", "_treat", "_time"]).size().reset_index(name="n")
            .itertuples(index=False, name=None)}

    def eligible_lines_v2(target, inputs):
        need = [(tm, t) for tm in ["Tram", "DMSO"] for t in list(inputs) + [target]]
        return [c for c in lines_all
                if all(nval.get((c, tm, t), 0) >= MIN_NORMAL_CELLS for tm, t in need)]

    contrast_defs = {
        24: [(6,), (6, 12), (3, 6, 12)],
        48: [(6,), (6, 12), (6, 12, 24)],
    }
    contrasts = {}
    lines_by_contrast = {}
    for target, input_sets in contrast_defs.items():
        for inputs in input_sets:
            key = f"target{target}h_inputs{'+'.join(str(x) + 'h' for x in inputs)}"
            ls = eligible_lines_v2(target, inputs)
            lines_by_contrast[key] = ls
            contrasts[key] = {"target_h": target, "input_times_h": list(inputs),
                              "time_order_ok": all(t < target for t in inputs),
                              "n_eligible_lines": len(ls), "lines": ls}
    paired_sets = {}
    for target in (24, 48):
        e1 = set(lines_by_contrast[f"target{target}h_inputs6h"])
        e2 = set(lines_by_contrast[f"target{target}h_inputs6h+12h"])
        paired_sets[f"target{target}h_E1_vs_E2_paired_lines"] = sorted(e1 & e2)
        if target == 48:
            e3 = set(lines_by_contrast["target48h_inputs6h+12h+24h"])
            paired_sets["target48h_E2_vs_E3_paired_lines"] = sorted(e2 & e3)
    v2_folds = {k: fold_manifest(lines_by_contrast[k]) for k in lines_by_contrast}

    # v0.1 bug cross-check
    old_v2 = v01["primary_contrasts"]["V2_extra_early_snapshot"]["contrasts"]
    old_pair_bug = {
        "target24h": {"paired_n": old_v2[0].get("paired_n")},
        "target48h": {"paired_n_E1_E2": old_v2[1].get("paired_n_E1_E2"),
                      "paired_n_E2_E3": old_v2[1].get("paired_n_E2_E3")},
    }
    old_pairs_nested = {k: v["n"] for k, v in
                       v01["v2_hashed_arm"]["nested_paired_line_sets"].items()}
    paired_corrected = {
        "target24h_E1_vs_E2": len(paired_sets["target24h_E1_vs_E2_paired_lines"]),
        "target48h_E1_vs_E2": len(paired_sets["target48h_E1_vs_E2_paired_lines"]),
        "target48h_E2_vs_E3": len(paired_sets["target48h_E2_vs_E3_paired_lines"]),
    }
    # cross-check re-derived qualification against v0.1 JSON
    old_elig = {k: v["n_eligible_lines"]
                for k, v in v01["v1_exact_6_24"]["per_drug_eligible_with_time_matched_control"].items()}
    new_elig = {k: len(v) for k, v in eligible_lines.items()}
    old_v2_n = {k: v["n_eligible_lines"]
                for k, v in v01["v2_hashed_arm"]["temporal_contrasts"].items()}
    new_v2_n = {k: len(v) for k, v in lines_by_contrast.items()}
    out["v0_1_cross_check"] = {
        "v1_eligible_lines_v0_1": old_elig,
        "v1_eligible_lines_v0_2_rederived": new_elig,
        "v1_eligible_lines_match": old_elig == new_elig,
        "v2_eligible_lines_v0_1": old_v2_n,
        "v2_eligible_lines_v0_2_rederived": new_v2_n,
        "v2_eligible_lines_match": old_v2_n == new_v2_n,
        "old_paired_n_bug": old_pair_bug,
        "old_nested_paired_n": old_pairs_nested,
        "correct_paired_n": paired_corrected,
    }

    # ---------- build v0.2 ----------
    out["revision_changes"] = [
        {"id": 1, "challenge_item": "BRD3379 = 0.0 uM must not be the 4th active drug in V1 primary",
         "before": "V1 primary = 4-drug equal-weight mean including BRD3379 (n=95 eligible lines) and stated '4 drugs n>=20 confirmatory'",
         "after": "V1 primary = 3 active drugs (Bortezomib n=22 / Idasanutlin n=24 / Trametinib n=24); BRD3379 only zero-dose/vehicle-like control, secondary/descriptive; 4-drug confirmatory status withdrawn",
         "status": "fixed"},
        {"id": 2, "challenge_item": "V2 paired_n field semantics wrong (paired_n=2)",
         "before": "primary_contrasts.V2 contrasts[*].paired_n = 2 (bug: len(dict) instead of dict['n'])",
         "after": f"paired cell-line counts: target24h E1/E2={paired_corrected['target24h_E1_vs_E2']}; "
                  f"target48h E1/E2={paired_corrected['target48h_E1_vs_E2']}, "
                  f"E2/E3={paired_corrected['target48h_E2_vs_E3']}; paired line sets listed",
         "status": "fixed"},
        {"id": 3, "challenge_item": "G0 must add active-dose/treatment-identity gate; BRD3379 must not pass",
         "before": "G0 only checked each arm has >=20 eligible lines; BRD3379 0.0 uM passed",
         "after": "G0a coverage (active drugs >=20 lines) + G0b active-dose/identity (metadata-level: dose>0 + ChEMBL annotation); BRD3379 fails G0b and is excluded from primary; control reference only",
         "status": "fixed"},
        {"id": 4, "challenge_item": "Update 4-drug wording/MDE/primary across d5.json/report/protocol/record/usage; recompute SHA",
         "before": "MDE table listed BRD3379 (n=95 -> 0.409); primary per_drug_n had 4 drugs",
         "after": "MDE table lists only Bortezomib 0.865 / Idasanutlin 0.826 / Trametinib 0.826 (with required r_err 0.987/0.985/0.985); BRD3379 shown only as zero-dose control; v0.2 artifacts + SHA recorded; v0.1 files unchanged",
         "status": "fixed"},
        {"id": 5, "challenge_item": "Add pre-execution protocol checklist",
         "before": "v0.1 lacked execution-level details",
         "after": "structured pre-execution checklist added (loading/QC/pseudobulk/panel/folds/paired sets/null/sentinel/B1-B8 tuning/determinism/schema/measured-MDE pre-certification/failure template/G5)",
         "status": "fixed"},
    ]

    out["active_drug_qualification"] = {
        "arms": arm_meta,
        "active_drugs_primary": active_drugs,
        "excluded_from_primary": excluded_active,
        "certification_level": ("metadata-level only: dose>0 + ChEMBL annotation; execution protocol must "
                                "re-verify compound identity/dose/vehicle before any run"),
        "brd3379_label": "zero-dose/vehicle-like control (0.0 uM; no ChEMBL annotation) - secondary/descriptive only",
    }

    out["v1_primary"] = {
        "status": "confirmatory-development (3 active drugs; BRD3379 excluded)",
        "active_drugs": {p: {"n_eligible_lines": len(eligible_lines[p]),
                             "n_common_keys": sum(1 for q, _ in common if q == p)} for p in active_drugs},
        "primary_statistic": ("equal-weight mean over the 3 active drugs of "
                              "Delta_rho_d = rho(early6h_d) - rho(static_d) on held-out cell lines"),
        "note_line_sets": ("the 3 active drugs use different eligible line sets (22/24/24); the primary is "
                           "a mean of drug-level Delta_rho values, NOT a paired-across-drug line contrast; "
                           "report per-drug CIs and the drug-level range"),
        "forbidden_arms": ["any target-time (24h) input", "future-time features", "two-snapshot arm in V1"],
        "mde_prerun_active_only": {p: mde_prerun(len(eligible_lines[p])) for p in active_drugs},
    }
    out["v1_secondary_brd3379"] = {
        "role": "zero-dose/vehicle-like control; secondary/descriptive only",
        "n_eligible_lines": len(eligible_lines.get(ZERO_DOSE_DRUG, [])),
        "included_in_primary_mean": False,
        "label_required_in_outputs": "BRD3379 zero-dose/vehicle-like control (not active)",
    }

    out["v2_corrected"] = {
        "paired_n_definition": "number of cell lines in the intersection of the two/first three eligible line sets (paired cell-line count)",
        "contrasts": [
            {"target_h": 24, "E1": "inputs 6h", "E2": "inputs 6h+12h",
             "n_E1": contrasts["target24h_inputs6h"]["n_eligible_lines"],
             "n_E2": contrasts["target24h_inputs6h+12h"]["n_eligible_lines"],
             "paired_n": paired_corrected["target24h_E1_vs_E2"]},
            {"target_h": 48, "E1": "inputs 6h", "E2": "inputs 6h+12h", "E3": "inputs 6h+12h+24h",
             "n_E1": contrasts["target48h_inputs6h"]["n_eligible_lines"],
             "n_E2": contrasts["target48h_inputs6h+12h"]["n_eligible_lines"],
             "n_E3": contrasts["target48h_inputs6h+12h+24h"]["n_eligible_lines"],
             "paired_n_E1_E2": paired_corrected["target48h_E1_vs_E2"],
             "paired_n_E2_E3": paired_corrected["target48h_E2_vs_E3"]},
        ],
        "paired_line_sets": {k: {"n": len(v), "lines": v} for k, v in paired_sets.items()},
        "v0_1_bug": {"field": "primary_contrasts.V2_extra_early_snapshot.contrasts[*].paired_n",
                     "v0_1_values": old_pair_bug,
                     "v0_1_nested_paired_n": old_pairs_nested,
                     "cause": "len(dict) counted the {'n','lines'} wrapper instead of the paired line count",
                     "corrected": paired_corrected},
        "status": "exploratory only (n<20 eligible lines in every contrast; no pass/fail verdict)",
    }

    out["folds_v0_2"] = {
        "seed": SEED,
        "v1_active_drugs": v1_folds_active,
        "v1_brd3379_secondary": v1_folds_brd,
        "v2": v2_folds,
        "v1_active_primary_manifest_sha256": active_primary_manifest_sha,
        "rule": "eligible lines sorted by name; fold = index % 5; same cell line never split",
    }

    n_active = {p: len(eligible_lines[p]) for p in active_drugs}
    out["gates_v0_2"] = {
        "delta_min": DELTA_MIN,
        "G0_eligibility": {
            "G0a_coverage": {
                "rule": f"every active primary drug has >= {MIN_LINES} eligible lines",
                "actual_active": n_active,
                "status": "pass" if all(n >= MIN_LINES for n in n_active.values()) else "fail",
            },
            "G0b_active_dose_identity": {
                "rule": ("active drug must have dose>0, non-null dose unit, and a treatment-identity "
                         "annotation (ChEMBL); BRD3379 does not pass"),
                "actual": {p: {"dose": arm_meta[p]["dose_values"],
                               "chembl_ids": arm_meta[p]["chembl_ids"],
                               "check": arm_meta[p]["active_dose_metadata_check"]}
                           for p in active_drugs + [ZERO_DOSE_DRUG, CONTROL_ARM]
                           if p in arm_meta},
                "status": ("conditional_pass_metadata_level_for_3_active_drugs; "
                           "BRD3379_and_control_fail; execution re-verification required"),
                "certification_level": "metadata-level only; execution re-verification required",
            },
            "V1_primary_status": "pass_with_3_active_drugs",
            "BRD3379_status": "excluded_from_primary (G0b fail; zero-dose/vehicle-like control; secondary only)",
            "V2_status": "exploratory_only (n<20 in every contrast)",
        },
        "G1_split_half_reliability": {"rule": "Spearman-Brown rho_sb >= delta_min + MDE80",
                                      "fail_semantics": "evaluation_cannot_distinguish"},
        "G2_room": {"rule": "room = rho_oracle - rho_static >= max(delta_min, MDE80)",
                    "fail_semantics": "evaluation_cannot_distinguish"},
        "G3_MDE80": {"rule": "MDE80(paired delta, cell-line cluster bootstrap) <= delta_min",
                     "prerun_upper_bounds_active_only": {p: mde_prerun(n) for p, n in n_active.items()},
                     "fail_semantics": "evaluation_cannot_distinguish"},
        "G4_primary_effect": {"rule": ("mean over 3 active drugs of Delta_rho >= delta_min and "
                                       "95% CI lower bound > 0"),
                              "fail_semantics": "no_increment"},
        "G5_leakage_audit": {"rule": ("target/future time absent; V1 has no two-snapshot arm; "
                                      "cell-line-grouped folds; train-only preprocessing; code assertions"),
                             "fail_semantics": "design_invalid"},
    }

    out["execution_protocol_checklist"] = {
        "note": ("even after this revision, a separate execution protocol + independent challenge are required; "
                 "this round only writes the checklist"),
        "items": [
            {"id": "E1_data_loading",
             "content": ("load h5ad obs + expression (execution only; anndata); freeze QC rule "
                         "(cell_quality=='normal'); pseudobulk per (drug,line,time) = mean expression; "
                         "control = time-matched perturbation=control (V1) or DMSO hash label (V2); "
                         "logFC = log2((pseudo+1)/(ctrl+1)); record cell counts per condition; no additional "
                         "expression-based filtering that could select on target")},
            {"id": "E2_200_gene_panel",
             "content": ("per drug/target/fold compute mean |logFC| on TRAINING lines only; take top-K=200; "
                         "freeze gene list SHA per fold; test lines never used in panel selection; vector "
                         "endpoint = same 200 genes")},
            {"id": "E3_fold_loader_assertions",
             "content": ("load d5_v0_2.json folds; assert each drug's folds partition its eligible lines "
                         "exactly; assert no cell line appears in >1 test fold; assert fold rule index%5; "
                         "assert seed/version; recompute manifest SHA and compare")},
            {"id": "E4_v1_paired_sets",
             "content": ("V1 has NO paired-across-drug line set by design; each active drug uses its own "
                         "eligible lines (22/24/24); primary = mean of 3 drug-level Delta_rho; report per-drug "
                         "CIs and drug-level range; BRD3379 secondary only")},
            {"id": "E5_v2_paired_sets",
             "content": ("use paired cell-line sets: target24h E1/E2 n=15; target48h E1/E2 n=16; "
                         "target48h E2/E3 n=15 (line lists in d5_v0_2.json); assert inputs strictly earlier "
                         "than target; paired Delta_rho computed only on the paired set")},
            {"id": "E6_null_models_future_sentinel",
             "content": ("N0 mean; N1 cell-shuffle; N2 drug-shuffle (V1); N3 time-shuffle among allowed earlier "
                         "times (V2); N4 capacity control (same-dim random/2nd-time shuffled); "
                         "N5 future-leak sentinel (replace early features with target-time features; expect "
                         "near-oracle; if not, pipeline/metric broken); N6 static-capacity random gene block; "
                         "fixed seeds and >=200 permutations where applicable")},
            {"id": "E7_B1_B8_tuning_budget",
             "content": ("pre-register identical tuning budgets (same #candidates x inner folds) for B1 static "
                         "ridge, B2 cell identity, B3 linear ridge, B4 tree/GBM (library/grid fixed before run; "
                         "e.g. sklearn HistGradientBoosting), B5 GP, B6 simple linear-time (V2), B7 single early, "
                         "B8 two early; report chosen hyperparameters and budget counts; no test-tuned choices")},
            {"id": "E8_two_run_determinism_schema",
             "content": ("two runs with same seed; outputs byte-identical (no timestamps); fixed JSON schema: "
                         "per contrast {n, rho_early, rho_static, delta, CI, MDE80, room, reliability, "
                         "gate statuses, verdict}; config/fold SHA; predictions stored only as pseudobulk-level "
                         "arrays with SHA")},
            {"id": "E9_measured_MDE_precertification",
             "content": ("before G4: compute split-half reliability, room, and measured MDE80 via cell-line "
                         "cluster bootstrap (1,000 draws, seed 20261027); if G1-G3 fail -> "
                         "evaluation_cannot_distinguish and do NOT run G4; record measured values")},
            {"id": "E10_failure_template",
             "content": ("failure record fields: verdict_class, reason, failing gate, measured values, "
                         "what is NOT claimed, data/spec needed; negative != absence; no post-hoc threshold "
                         "change")},
            {"id": "E11_G5_code_assertions",
             "content": ("assert target time not in input time lists; assert V1 model set excludes two-snapshot; "
                         "assert folds group cell lines; assert train-only preprocessing; assert no "
                         "expression-derived test information; run future-leak sentinel; fail closed")},
            {"id": "E12_no_effect_this_round",
             "content": "this revision does not run any effect, prediction, or expression read; execution needs a new task and independent challenge"},
        ],
    }

    out["failure_classes"] = [
        "data_unavailable", "design_invalid", "evaluation_cannot_distinguish", "no_increment",
        "exploratory_only", "time_axis_unverified", "functional_route_not_qualified",
        "identifiability_unsupported", "active_dose_identity_unverified",
    ]
    out["stop_conditions"] = [
        "G0a/G0b fails -> data_unavailable / active_dose_identity_unverified; stop",
        "G1-G3 fail -> evaluation_cannot_distinguish; stop; do not report negative",
        "G4 fails (early ~= static) -> no_increment; stop dynamic-necessity claim",
        "V2 extra-snapshot delta CI includes 0 / capacity control reproduces it -> no extra-early-time increment",
        "no matched late functional endpoint -> functional_route_not_qualified; stop functional/latency claims",
        "no batch/exposure/same-cell records -> time_axis_unverified; no absolute time-course/trajectory claims",
        "leakage audit fails -> design_invalid; stop and fix before run",
        "no post-hoc threshold/endpoint/split changes; no replacing a failed endpoint",
    ]
    out["verdicts"] = {
        "molecular_temporal_route": {
            "verdict": "qualified_with_conditions",
            "scope": "3 active drugs (Bortezomib/Idasanutlin/Trametinib) for 6h->24h RNA-to-RNA development; BRD3379 zero-dose/vehicle-like control secondary only; V2 exploratory",
            "conditions": [
                "V1 primary excludes BRD3379 (zero-dose); no '4 drugs' confirmatory claim",
                "V1 has no same-cell early-late pairing; destructive snapshots",
                "no functional endpoint: RNA proxy is not viability/regrowth",
                "no same-plate/same-batch or exposure certification (time_axis_unverified)",
                "no replicate samples / independent-culture record",
                "no absolute time-course/path/trajectory/mechanism/migration/decision-benefit/novelty claims",
            ],
        },
        "functional_route": {"verdict": "not_qualified", "failure_class": "data_unavailable"},
        "overall_D5": {
            "verdict": "qualified_with_conditions",
            "scope": "molecular temporal prediction development only; 3 active drugs; functional/path/mechanism/decision claims not qualified",
            "approve_to_lead_exec": False,
            "recommend_rechallenge": True,
            "recommend_effect_run_now": False,
        },
    }
    out["background_boundaries"] = {
        "old_A3_dynamic_route": "A3v2 L1/L2 is background only; no uncertified A3 part is reused",
        "r200_brief": "design/qualification task; effect run only after independent challenge and Lead approval",
        "c176_c177_c179_c181_c186": ("revocations/status only background; no temporal predictability evidence; do not cite old verdicts; "
                                      "do not reopen R196v2/R197v2"),
        "errata_a3_r195": "R195/A3 not_qualified is limited to its frozen large-scale design; not a general exclusion",
        "no_claims": ["novelty", "cell-state mechanism", "migration", "decision benefit", "true trajectory"],
    }
    out["limits"] = [
        "metadata-only revision: no expression values read; no response/functional values read; no fit/prediction",
        "active-dose verification is metadata-level (dose>0 + ChEMBL annotation), not an independent dose/vehicle identity assay",
        "v0.1 files are untouched; v0.1 4-drug primary is superseded and not authoritative",
        "V2 remains exploratory (n<20); BRCA/functional/time-axis gaps unchanged",
        "execution protocol checklist is not an execution protocol; a separate frozen protocol + independent challenge are required",
        "no novelty/mechanism/migration/decision-benefit claims",
    ]
    out["script"] = {"path": os.path.relpath(os.path.abspath(__file__), ROOT).replace(os.sep, "/"),
                     "sha256": sha256_file(os.path.abspath(__file__))}

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2, sort_keys=True)
    print("WROTE", OUT)
    print(json.dumps({
        "active_drugs": active_drugs,
        "v1_n": n_active,
        "brd3379_lines": len(eligible_lines.get(ZERO_DOSE_DRUG, [])),
        "v2_paired": paired_corrected,
        "g0b": {p: arm_meta[p]["active_dose_metadata_check"] for p in active_drugs + [ZERO_DOSE_DRUG, CONTROL_ARM] if p in arm_meta},
        "old_paired_n_bug": old_pair_bug,
        "v1_manifest_sha": active_primary_manifest_sha,
        "verdicts": {k: v["verdict"] for k, v in out["verdicts"].items()},
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
