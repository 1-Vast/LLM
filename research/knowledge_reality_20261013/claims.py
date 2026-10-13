"""The report's quantitative claims and the run manifest they are audited against (CLAIMS.json, RUNS.json).

File summary
- Path: research/knowledge_reality_20261013/claims.py
- Purpose: state the numbers README.md reports as machine-checkable claims on one run's artifact, and
  list every run of the study, so `maestro.claim_audit.audit` can check the report deterministically.
- Run statuses (`maestro.claim_audit.RunStatus`):
  - succeeded;
  - negative: a hypothesis that was not supported. The report must cite it, or the audit raises
    OMITTED_NEGATIVE_RUN. Here: knowledge biology (G2), typing and provenance, strict new targets,
    and knowledge after a primary screen. All share DEVELOPMENT.json.
  - failed: the stage-2 prediction step, which refuses with GATE_NOT_PASSED;
  - excluded: the pre-run smoke output (a subsample pipeline check, not evidence).
- Manifest roots: the study folder, with result-file patterns. A later PREDICTION_LOCK.json or
  RESULTS.json makes the audit fail (MANIFEST_INCOMPLETE) until it is listed.
- Write-once: a rerun recomputes both files and must reproduce them (CLAIMS_MISMATCH, RUNS_MISMATCH).
- Interfaces: `CLAIMS`, `RUNS`, `main`.
"""
from __future__ import annotations

import json

from sources import HERE, ROOT

STUDY = str(HERE.relative_to(ROOT)).replace("\\", "/")
DEV = "DEVELOPMENT.json"

# run_id, status, artifact (relative to the study folder), reason
RUNS = [
    ("census", "succeeded", "CENSUS.json", ""),
    ("build", "succeeded", "BUILD.json", ""),
    ("leakage", "succeeded", "LEAKAGE.json", ""),
    ("sealed_census", "succeeded", "SEALED_CENSUS.json", ""),
    ("smoke", "excluded", "SMOKE_DEVELOPMENT.json",
     "pipeline check on one compound in eight with one control seed, 32 s before the registered run; not evidence"),
    ("development", "succeeded", DEV, ""),
    ("knowledge_biology_G2", "negative", DEV, ""),
    ("typed_provenance", "negative", DEV, ""),
    ("strict_new_target", "negative", DEV, ""),
    ("t1_knowledge", "negative", DEV, ""),
    ("power", "succeeded", "POWER.json", ""),
    ("freeze", "succeeded", "FREEZE.json", ""),
    ("stage2_predict", "failed", "confirm.py",
     "GATE_NOT_PASSED: the development gate failed (G2), so confirm.py predict refuses; no prediction was locked and the "
     "24Q2 outcome file was not downloaded"),
]
PATTERNS = ["CENSUS.json", "BUILD.json", "LEAKAGE.json", "SEALED_CENSUS.json", "SMOKE_*.json", "DEVELOPMENT.json",
            "POWER.json", "FREEZE.json", "PREDICTION_LOCK.json", "RESULTS.json"]

R = 5e-5      # tolerance for r values quoted to four decimals
CMP = "comparisons"
CTL = "controls"

# claim_id, statement, run_id, pointer, relation, value, tolerance
CLAIMS = [
    # Gate
    ("C01", "the development gate FAILED", "development", ("gate", "verdict"), "==", "FAIL", 0),
    ("C02", "G1 (knowledge gain over chemistry) passes", "development", ("gate", "G1_knowledge_gain"), "==", True, 0),
    ("C03", "G3 (specificity gain) passes", "development", ("gate", "G3_specificity"), "==", True, 0),
    ("C04", "G2 (beats every control) fails", "knowledge_biology_G2", ("gate", "G2_beats_every_control"), "==", False, 0),
    # Population
    ("C05", "4,528 compounds in development", "development", ("population", "compounds"), "==", 4528, 0),
    ("C06", "1,460 active compounds", "development", ("population", "active"), "==", 1460, 0),
    ("C07", "1,207 active compounds have a T0 target", "development", ("population", "active_annotated"), "==", 1207, 0),
    ("C08", "26 active strict-new-target compounds", "strict_new_target", ("population", "active_strict_new_target_annotated"),
     "==", 26, 0),
    ("C09", "the development run took 2,535 s", "development", ("runtime_seconds",), "==", 2535, 0),
    # G1 and G3
    ("C10", "know_full - chem_full = +0.0056", "development", (CMP, "know_full-chem_full:active", "difference"), "approx", 0.0056, R),
    ("C11", "G1 interval lower bound +0.0028", "development", (CMP, "know_full-chem_full:active", "ci95", "0"), "approx", 0.0028, R),
    ("C12", "G1 interval upper bound +0.0085", "development", (CMP, "know_full-chem_full:active", "ci95", "1"), "approx", 0.0085, R),
    ("C13", "G1 p < 0.0001", "development", (CMP, "know_full-chem_full:active", "p_greater"), "<", 0.0001, 0),
    ("C14", "821 compounds favour knowledge", "development", (CMP, "know_full-chem_full:active", "favour"), "==", 821, 0),
    ("C15", "593 compounds oppose", "development", (CMP, "know_full-chem_full:active", "oppose"), "==", 593, 0),
    ("C16", "531 family clusters", "development", (CMP, "know_full-chem_full:active", "clusters"), "==", 531, 0),
    ("C17", "specificity gain +0.0056", "development", (CMP, "specificity:know_full-chem_full:active", "difference"), "approx", 0.0056, R),
    ("C18", "specificity interval lower bound +0.0030", "development", (CMP, "specificity:know_full-chem_full:active", "ci95", "0"),
     "approx", 0.0030, R),
    ("C19", "specificity interval upper bound +0.0083", "development", (CMP, "specificity:know_full-chem_full:active", "ci95", "1"),
     "approx", 0.0083, R),
    ("C20", "specificity p < 0.0001", "development", (CMP, "specificity:know_full-chem_full:active", "p_greater"), "<", 0.0001, 0),
    # Controls
    ("C21", "degree null: know_full mean 0.0785", "development", (CTL, "degree", "know_full", "null_mean"), "approx", 0.0785, R),
    ("C22", "degree null: know_full 95th percentile 0.0787", "development", (CTL, "degree", "know_full", "null_p95"), "approx", 0.0787, R),
    ("C23", "set-permutation null: know_full mean 0.0785", "development", (CTL, "setperm", "know_full", "null_mean"), "approx", 0.0785, R),
    ("C24", "set-permutation null: know_full 95th percentile 0.0786", "development", (CTL, "setperm", "know_full", "null_p95"),
     "approx", 0.0786, R),
    ("C25", "degree null: gain mean -0.0001", "development", (CTL, "degree", "tc_gain", "null_mean"), "approx", -0.0001, R),
    ("C26", "set-permutation null: gain mean -0.0001", "development", (CTL, "setperm", "tc_gain", "null_mean"), "approx", -0.0001, R),
    ("C27", "the true gain beats every degree null (empirical p 0.048)", "development", (CTL, "degree", "tc_gain", "empirical_p"),
     "approx", 0.0476, 1e-4),
    ("C28", "and every set-permutation null (empirical p 0.048)", "development", (CTL, "setperm", "tc_gain", "empirical_p"),
     "approx", 0.0476, 1e-4),
    ("C29", "degree null: know_only mean 0.0161", "development", (CTL, "degree", "know_only", "null_mean"), "approx", 0.0161, R),
    ("C30", "set-permutation null: know_only mean 0.0106", "development", (CTL, "setperm", "know_only", "null_mean"), "approx", 0.0106, R),
    ("C31", "relabelling null: gain mean +0.0057", "knowledge_biology_G2", (CTL, "relabel", "tc_gain", "null_mean"), "approx", 0.0057, R),
    ("C32", "relabelling null: true gain at empirical p 0.95", "knowledge_biology_G2", (CTL, "relabel", "tc_gain", "empirical_p"),
     "approx", 0.9524, 1e-4),
    ("C33", "relabelling null: know_full mean 0.0843", "knowledge_biology_G2", (CTL, "relabel", "know_full", "null_mean"), "approx", 0.0843, R),
    ("C34", "relabelling null: know_only mean 0.0587", "knowledge_biology_G2", (CTL, "relabel", "know_only", "null_mean"), "approx", 0.0587, R),
    ("C35", "relabelling null: specificity mean 0.0557", "knowledge_biology_G2", (CTL, "relabel", "specificity", "null_mean"),
     "approx", 0.0557, R),
    ("C36", "annot_full is unchanged by relabelling (0.0836)", "knowledge_biology_G2", (CTL, "relabel", "annot_full", "null_max"),
     "approx", 0.0836, R),
    # Ablations and strata
    ("C37", "know_full - rkt_full +0.0003, p 0.27", "typed_provenance", (CMP, "know_full-rkt_full:active", "p_greater"), "approx", 0.2745, 1e-4),
    ("C38", "know_full - annot_full +0.0007, p 0.20", "typed_provenance", (CMP, "know_full-annot_full:active", "p_greater"),
     "approx", 0.1974, 1e-4),
    ("C39", "typing loses 0.0002 against untyped", "typed_provenance", (CMP, "know_full-know_untyped:active", "difference"),
     "approx", -0.0002, R),
    ("C40", "measured edges in the context route add 0.0000 (p 0.83)", "typed_provenance",
     (CMP, "know_full-know_curated_tc:active", "p_greater"), "approx", 0.8289, 1e-4),
    ("C41", "engagement edges (T1) add -0.0001 (p 0.80)", "typed_provenance", (CMP, "know_full_t1-know_full:active", "p_greater"),
     "approx", 0.8034, 1e-4),
    ("C42", "strict new target: +0.0007", "strict_new_target", (CMP, "know_full-chem_full:active_strict_new_target", "difference"),
     "approx", 0.0007, R),
    ("C43", "strict new target: p 0.39", "strict_new_target", (CMP, "know_full-chem_full:active_strict_new_target", "p_greater"),
     "approx", 0.39, 1e-4),
    ("C44", "knowledge after a primary screen: +0.0004", "t1_knowledge", (CMP, "t1_know-t1_base:active", "difference"), "approx", 0.0004, R),
    ("C45", "knowledge after a primary screen: p 0.063", "t1_knowledge", (CMP, "t1_know-t1_base:active", "p_greater"), "approx", 0.0631, 1e-4),
    ("C46", "density alone loses 0.0027 against chemistry", "development", (CMP, "density_full-chem_full:active", "difference"),
     "approx", -0.0027, R),
    ("C47", "know_full beats density_full by +0.0083", "development", (CMP, "know_full-density_full:active", "difference"), "approx", 0.0083, R),
    ("C48", "rkt_full - chem_full p 0.0002", "development", (CMP, "rkt_full-chem_full:active", "p_greater"), "approx", 0.0002, 1e-4),
    # Single routes and calibration
    ("C49", "target-context route alone r 0.0090", "knowledge_biology_G2", ("single_routes", "tc", "mean_r_active"), "approx", 0.0090, R),
    ("C50", "kn_typed alone r 0.0588", "development", ("single_routes", "kn_typed", "mean_r_active"), "approx", 0.0588, R),
    ("C51", "chemical ridge alone r 0.0738", "development", ("single_routes", "chem_ridge", "mean_r_active"), "approx", 0.0738, R),
    ("C52", "Tanimoto kNN refuses 20% of compounds", "development", ("single_routes", "chem_knn", "refused_share"), "approx", 0.2025, 1e-3),
    ("C53", "Brier 0.0069 for know_full", "development", ("arms", "know_full", "brier"), "approx", 0.0069, R),
    ("C54", "ECE 0.0014 for chemistry", "development", ("arms", "chem_full", "ece"), "approx", 0.0014, R),
    ("C55", "ECE 0.0017 for know_full", "development", ("arms", "know_full", "ece"), "approx", 0.0017, R),
    ("C56", "zero arm 15 selective events in 1,000 nominations", "development", ("zero_arm_decision", "hits"), "==", 15, 0),
    # Power
    ("C57", "762 active compounds needed for 80% power", "power", ("min_active",), "==", 762, 0),
    ("C58", "about 396 active sealed compounds expected", "power", ("expected_sealed_active",), "approx", 396.3, 0.05),
    ("C59", "power about 52% at that size", "power", ("power_at_expected_active",), "approx", 0.524, 0.001),
    ("C60", "development standard error 0.00145", "power", ("se_dev",), "approx", 0.00145, 1e-5),
    # Census, leakage, sealed census
    ("C61", "58 outcome-proximal edges removed", "census", ("edges", "removed_outcome_proximal"), "==", 58, 0),
    ("C62", "21,972 metabolic edges removed", "census", ("edges", "removed_metabolic"), "==", 21972, 0),
    ("C63", "969 cell-engagement edges kept as T1 only", "census", ("edges", "tier", "T1"), "==", 969, 0),
    ("C64", "giant component 4,029 units", "census", ("families", "giant_component_units"), "==", 4029, 0),
    ("C65", "of 4,449 compound units", "census", ("coverage", "compound_units"), "==", 4449, 0),
    ("C66", "the Hub licence is non-commercial use only", "census", ("licences", "repurposing_hub"), "==",
     "Broad Drug Repurposing Hub: non-commercial use only (file header); file dated 2020-03-24 (after the PRISM 19Q4 release)", 0),
    ("C67", "no structural alias spans folds", "leakage", ("structural_alias_units_spanning_folds",), "==", 0, 0),
    ("C68", "3 Hub annotations flagged as PRISM-derived", "leakage", ("outcome_derived_curated_flags", "compounds"), "==", 3, 0),
    ("C69", "lowest target-gene overlap with training 74%", "leakage", ("mechanism_overlap_with_training", "2", "shares_t0_gene_with_training"),
     "approx", 0.742, 0.001),
    ("C70", "highest target-gene overlap with training 88%", "leakage", ("mechanism_overlap_with_training", "0", "shares_t0_gene_with_training"),
     "approx", 0.881, 0.001),
    ("C71", "1,229 eligible sealed compounds", "sealed_census", ("eligible_compounds",), "==", 1229, 0),
    ("C72", "23 REP.1M compounds refused by core", "sealed_census", ("refused", "IN_19Q4_BY_CORE"), "==", 23, 0),
    ("C73", "11 by name", "sealed_census", ("refused", "IN_19Q4_BY_NAME"), "==", 11, 0),
    ("C74", "15 by connectivity", "sealed_census", ("refused", "IN_19Q4_BY_CONNECTIVITY"), "==", 15, 0),
    ("C75", "49 overlap compounds", "sealed_census", ("overlap_with_19q4",), "==", 49, 0),
    ("C76", "285 new-context lines", "sealed_census", ("lines", "new_context_with_ccle"), "==", 285, 0),
    ("C77", "545 panel lines", "sealed_census", ("lines", "panel_with_ccle"), "==", 545, 0),
    ("C78", "2024 and 2020 target annotations agree for every eligible compound", "sealed_census",
     ("annotation_agreement_2020_vs_2024_target",), "==", 1.0, 0),
    ("C79", "561 development lines", "build", ("lines",), "==", 561, 0),
]

# README's arm table (active compounds), typed by hand so the audit checks the transcription
TABLE = {"chem_full": (0.0786, 0.0500, 142, 108, 532), "density_full": (0.0759, 0.0431, 121, 108, 561),
         "annot_full": (0.0836, 0.0552, 161, 154, 579), "rkt_full": (0.0839, 0.0554, 152, 149, 569),
         "know_full": (0.0842, 0.0556, 143, 141, 572), "know_only": (0.0589, 0.0471, 87, 104, 482),
         "know_untyped": (0.0845, 0.0559, 142, 143, 572), "know_full_t1": (0.0842, 0.0556, 145, 143, 571)}
for arm, (r, sp, hits, conf, ev) in TABLE.items():
    CLAIMS += [(f"T-{arm}-r", f"{arm} mean r {r}", "development", ("arms", arm, "mean_r_active"), "approx", r, R),
               (f"T-{arm}-spec", f"{arm} specificity {sp}", "development", ("arms", arm, "specificity_active"), "approx", sp, R),
               (f"T-{arm}-hits", f"{arm} {hits} selective events", "development", ("arms", arm, "hits"), "==", hits, 0),
               (f"T-{arm}-conf", f"{arm} {conf} secondary-confirmed", "development", ("arms", arm, "sec_confirmed"), "==", conf, 0),
               (f"T-{arm}-eval", f"{arm} {ev} secondary-evaluable", "development", ("arms", arm, "sec_eval"), "==", ev, 0)]
CLAIMS += [("T-t1_base-r", "t1_base mean r 0.2016", "t1_knowledge", ("arms", "t1_base", "mean_r_active"), "approx", 0.2016, R),
           ("T-t1_know-r", "t1_know mean r 0.2020", "t1_knowledge", ("arms", "t1_know", "mean_r_active"), "approx", 0.2020, R),
           ("T-t1_base-spec", "t1_base specificity 0.2984", "t1_knowledge", ("arms", "t1_base", "specificity_active"), "approx", 0.2984, R),
           ("T-t1_know-spec", "t1_know specificity 0.2971", "t1_knowledge", ("arms", "t1_know", "specificity_active"), "approx", 0.2971, R)]


def build() -> tuple[str, str]:
    from maestro.claim_audit import file_sha256
    runs = [{"run_id": r, "status": s, "artifact": f"{STUDY}/{a}",
             "sha256": "" if s == "failed" else file_sha256(HERE / a), **({"reason": why} if why else {})} for r, s, a, why in RUNS]
    manifest = {"label": "every run of the study, including failed, excluded and negative runs", "roots": [STUDY], "patterns": PATTERNS,
                "runs": runs}
    claims = {"label": "README.md results as machine-checkable claims",
              "claims": [{"claim_id": c, "statement": s, "run_id": r, "pointer": list(p), "relation": rel, "value": v,
                          **({"tolerance": tol} if tol else {})} for c, s, r, p, rel, v, tol in CLAIMS]}
    return json.dumps(claims, indent=1) + "\n", json.dumps(manifest, indent=1) + "\n"


def main() -> None:
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    texts = dict(zip(("CLAIMS.json", "RUNS.json"), build()))
    for name, text in texts.items():
        path = HERE / name
        if path.exists():
            if path.read_text(encoding="utf-8").replace("\r\n", "\n") != text:
                raise SystemExit(f"{name.split('.')[0]}_MISMATCH: recomputed {name} differs")
            print("REPRODUCED", name)
        else:
            path.write_bytes(text.encode())
            print("WROTE", name)


if __name__ == "__main__":
    main()
