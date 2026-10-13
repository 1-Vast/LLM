"""The report's quantitative claims and the run manifest they are audited against (CLAIMS.json, RUNS.json).

File summary
- Path: research/selective_hit_triage_20261013/claims.py
- Purpose: state every number README.md reports as a machine-checkable claim on one run's artifact, and
  list every run of the study, so `maestro.claim_audit.audit` can check the report deterministically.
- Run statuses (`maestro.claim_audit.RunStatus`):
  - succeeded;
  - negative: a hypothesis or design idea that was not supported. The report must cite it, or the
    audit raises OMITTED_NEGATIVE_RUN;
  - failed: a run that refused or crashed. It carries a reason and may have no artifact;
  - excluded: a run whose artifact exists but may not support a claim. Here that is the as-run test
    results, whose outcome reader dropped half of the registered endpoint.
- Several runs may share one artifact (TEST_RESULTS_REGISTERED.json holds P1, P2, R1, R2 and the
  secondaries). That keeps negative hypotheses visible as runs of their own.
- Manifest roots: the study folder, with result-file patterns. Any new result file, such as
  AGENT_RESULTS.json after an authorised paid run, makes the audit fail (MANIFEST_INCOMPLETE) until it
  is listed.
- Write-once: a rerun recomputes both files and must reproduce them (CLAIMS_MISMATCH, RUNS_MISMATCH).
- Interfaces: `CLAIMS`, `RUNS`, `main`.
"""
from __future__ import annotations

import json

from census import HERE, ROOT

STUDY = str(HERE.relative_to(ROOT)).replace("\\", "/")
REG, POST = "TEST_RESULTS_REGISTERED.json", "POSTHOC.json"

# run_id, status, artifact (relative to the study folder), reason
RUNS = [
    ("census", "succeeded", "CENSUS.json", ""),
    ("split", "succeeded", "SPLIT.json", ""),
    ("design_lock_v1", "failed", "features.py",
     "np.load(allow_pickle=False) refused features.npz (object array of line names); rebuilt with a string dtype and the lock "
     "re-issued before any CTRP value was read (DEVIATIONS.json)"),
    ("design_lock", "succeeded", "DESIGN_LOCK.json", ""),
    ("development", "succeeded", "DEVELOPMENT.json", ""),
    ("dev_explore", "succeeded", "DEV_EXPLORE.json", ""),
    ("dev_explore2", "succeeded", "DEV_EXPLORE2.json", ""),
    ("dev_memory", "negative", "DEV_EXPLORE3.json", ""),
    ("dev_review", "negative", "DEV_REVIEW.json", ""),
    ("leakage", "succeeded", "LEAKAGE.json", ""),
    ("freeze", "succeeded", "FREEZE.json", ""),
    ("test_choices", "succeeded", "TEST_CHOICES.json", ""),
    ("choices_lock", "succeeded", "CHOICES_LOCK.json", ""),
    ("test_as_run", "excluded", "TEST_RESULTS.json",
     "outcomes.qualified_outcomes divided every test viability by 100 (unit guess tripped by 4 overgrowth curves), so the "
     "registered top-dose viability condition was never applied; superseded by TEST_RESULTS_REGISTERED.json"),
    ("registered_v1", "failed", "evaluate_registered.py",
     "THRESHOLD_TIE: restoring viability by x100 could not decide 13 pairs that sit exactly on 0.5; replaced by an exact "
     "re-read of the archive before any result was written"),
    ("P1", "succeeded", REG, ""),
    ("P2", "negative", REG, ""),
    ("R1", "negative", REG, ""),
    ("R2", "succeeded", REG, ""),
    ("test_secondary", "succeeded", REG, ""),
    ("strong_learners", "negative", POST, ""),
    ("split_transfer", "succeeded", POST, ""),
]
PATTERNS = ["CENSUS.json", "SPLIT.json", "DESIGN_LOCK.json", "DEVELOPMENT.json", "DEV_*.json", "LEAKAGE.json", "FREEZE.json",
            "CHOICES_LOCK.json", "TEST_*.json", "POSTHOC.json", "AGENT_*.json", "SDR_*.json"]

A = ("arms", "1.0")
# claim_id, statement, run_id, pointer, relation, value, tolerance
CLAIMS = [
    ("C01", "P1 (MAESTRO > D3 at b = 1) is CONFIRMED on the registered endpoint", "P1", ("primary", "P1", "verdict"), "==", "CONFIRMED", 0),
    ("C02", "MAESTRO found 22 validated selective hits in 128 nominations", "P1", A + ("MAESTRO", "validated_hits"), "==", 22, 0),
    ("C03", "D3 found 12", "P1", A + ("D3_two_way_z", "validated_hits"), "==", 12, 0),
    ("C04", "P1 one-sided p = 0.004", "P1", ("primary", "P1", "p_greater"), "approx", 0.00375, 1e-4),
    ("C05", "P1 holds with mechanism-family clusters (p 0.015)", "P1", ("primary", "P1", "family_clusters", "p_greater"), "<=", 0.025, 0),
    ("C06", "P1 holds without the 38 test compounds that share a target gene with development (+8, p 0.017)", "P1",
     ("secondary", "S12_leakage_sensitivity", "P1:without_shared_target_gene", "p_greater"), "<=", 0.025, 0),
    ("C07", "P2 (MAESTRO_LOOP > CONV_LOOP) is NOT_CONFIRMED", "P2", ("primary", "P2", "verdict"), "==", "NOT_CONFIRMED", 0),
    ("C08", "P2 difference +5 hits (23 vs 18)", "P2", ("primary", "P2", "difference"), "==", 5.0, 0),
    ("C09", "P2 one-sided p = 0.18", "P2", ("primary", "P2", "p_greater"), "approx", 0.1795, 1e-4),
    ("C10", "R1 (evidence vetoes less often confirmable than NEED_MORE_EVIDENCE) is NOT_CONFIRMED", "R1",
     ("review", "R1_veto_correctness", "verdict"), "==", "NOT_CONFIRMED", 0),
    ("C11", "3 of 23 vetoed compounds were confirmable", "R1", ("review", "R1_veto_correctness", "vetoed_confirmable"), "==", 3, 0),
    ("C12", "15 of 42 NEED_MORE_EVIDENCE compounds were confirmable", "R1",
     ("review", "R1_veto_correctness", "need_more_evidence_confirmable"), "==", 15, 0),
    ("C13", "R1 Fisher one-sided p = 0.045", "R1", ("review", "R1_veto_correctness", "p_one_sided"), "approx", 0.0448, 1e-4),
    ("C14", "R2 (admitting virtual-cell predictions as evidence causes more false NO-GOs) is CONFIRMED", "R2",
     ("review", "R2_evidence_verification", "verdict"), "==", "CONFIRMED", 0),
    ("C15", "15 false NO-GOs with predictions admitted", "R2", ("review", "R2_evidence_verification", "false_no_go_unverified"), "==", 15, 0),
    ("C16", "3 false NO-GOs with measured evidence only", "R2", ("review", "R2_evidence_verification", "false_no_go_verified"), "==", 3, 0),
    ("C17", "13 of 29 prediction-vetoed compounds were confirmable", "R2",
     ("review", "S13_decision_quality_b1", "SDR_unverified", "NO_GO", "by_reason", "PREDICTED_NON_REPLICATING", "confirmable"), "==", 13, 0),
    ("C18", "decision-aware acquisition added 1 hit at b = 1 (SDR_acquire 24 vs MAESTRO_LOOP 23)", "test_secondary",
     ("review", "ablations", "1.0:SDR_acquire-MAESTRO_LOOP", "difference"), "==", 1.0, 0),
    ("C19", "the full review (re-rank, veto, acquisition) lost 1 hit against veto + acquisition", "test_secondary",
     ("review", "ablations", "1.0:SDR_full-SDR_veto_acquire", "difference"), "==", -1.0, 0),
    ("C20", "every stored decision record re-derives from features.npz (0 unsupported of 543)", "test_secondary",
     ("secondary", "S14_record_audit", "SDR_veto:1.0", "unsupported"), "==", 0, 0),
    ("C21", "ML+context found 38 hits at b = 1 with no secondary bought", "test_secondary", A + ("ML+context", "validated_hits"), "==", 38, 0),
    ("C22", "MAESTRO_LOOP found 23 with 32 secondaries", "test_secondary", A + ("MAESTRO_LOOP", "validated_hits"), "==", 23, 0),
    ("C23", "line memory added 10 hits over no memory (33 vs 23, exploratory)", "test_secondary",
     ("secondary", "S8_memory_b1", "MEM-NO_MEM", "difference"), "==", 10.0, 0),
    ("C24", "the score effect: MAESTRO_top beats CONV_LOOP by 9 (p 0.015)", "test_secondary",
     ("secondary", "contrasts", "S3:1.0:MAESTRO_top-CONV_LOOP", "difference"), "==", 9.0, 0),
    ("C25", "frontier acquisition lost 4 hits against top acquisition (MAESTRO_LOOP - MAESTRO_top)", "test_secondary",
     ("secondary", "contrasts", "S3:1.0:MAESTRO_LOOP-MAESTRO_top", "difference"), "==", -4.0, 0),
    ("C26", "the development calibrator expected 43.8 hits for MAESTRO_LOOP; 23 were realised", "test_secondary",
     ("secondary", "S7_calibration", "MAESTRO_LOOP:1.0", "expected_hits"), "approx", 43.8, 0.05),
    ("C27", "the registered endpoint keeps 1,076 validated pairs", "test_secondary", ("validated_pairs",), "==", 1076, 0),
    ("C43", "74 of 128 test compounds are pan-active", "test_secondary", ("pan_active_compounds",), "==", 74, 0),
    ("C28", "13 pairs sit exactly on the 0.5 viability threshold", "test_secondary", ("correction", "pairs_on_viability_threshold"), "==", 13, 0),
    ("C29", "post hoc: ML+context beats MAESTRO_LOOP by 15 hits at b = 1 (p 0.004)", "strong_learners",
     ("learners_vs_engines", "1.0:ML+context-MAESTRO_LOOP", "difference"), "==", 15.0, 0),
    ("C30", "post hoc: that comparison's one-sided p", "strong_learners",
     ("learners_vs_engines", "1.0:ML+context-MAESTRO_LOOP", "p_greater"), "approx", 0.0038, 1e-4),
    ("C31", "post hoc: VC (all evidence, no follow-up) +9 over MAESTRO_LOOP, p 0.085", "strong_learners",
     ("learners_vs_engines", "1.0:VC-MAESTRO_LOOP", "difference"), "==", 9.0, 0),
    ("C32", "one development MoA family holds 82% of development's screen-selective validated pairs", "split_transfer",
     ("split_transfer", "development", "largest_family_share_of_validated_z_le_-3", "share"), "approx", 0.82, 0.005),
    ("C33", "validated rate of pairs with z_r <= -3: 30% on development", "split_transfer",
     ("split_transfer", "development", "validated_rate_by_screen_z", "-3.0", "validated_rate"), "approx", 0.299, 0.001),
    ("C34", "and 9% on test", "split_transfer",
     ("split_transfer", "test", "validated_rate_by_screen_z", "-3.0", "validated_rate"), "approx", 0.093, 0.001),
    ("C35", "every name difference between census and CTRP is a structure match", "split_transfer",
     ("identity_audit", "structure_matched"), "==", True, 0),
    ("C36", "development: D3 59 hits, ML 32 (why D3 was designated)", "development", ("arms", "1.0", "D3_two_way_z", "hits"), "==", 59, 0),
    ("C37", "development: ML 32", "development", ("arms", "1.0", "ML", "hits"), "==", 32, 0),
    ("C38", "development: the MAESTRO frontier loop found 76 hits", "dev_explore2",
     ("results", "1.0", "MAESTRO_frontier_sqrt", "0"), "==", 76, 0),
    ("C39", "development: no review variant added hits (SDR_veto 75 vs MAESTRO_LOOP 76)", "dev_review",
     ("results", "1.0", "SDR_veto", "hits"), "==", 75, 0),
    ("C40", "development: the breadth re-rank coefficient was 2.6 in fold 0 and about 0 elsewhere", "dev_review",
     ("coefficients_by_fold", "1", "beta"), "approx", 0.0, 0.1),
    ("C44", "development: fold 0 re-rank coefficient 2.6", "dev_review", ("coefficients_by_fold", "0", "beta"), "approx", 2.6, 0.01),
    ("C45", "P1 bootstrap 95% interval lower bound +4", "P1", ("primary", "P1", "ci95", "0"), "==", 4.0, 0),
    ("C46", "P1 bootstrap 95% interval upper bound +18", "P1", ("primary", "P1", "ci95", "1"), "==", 18.0, 0),
    ("C47", "line memory over no memory, one-sided p 0.015 (exploratory)", "test_secondary",
     ("secondary", "S8_memory_b1", "MEM-NO_MEM", "p_greater"), "approx", 0.0153, 1e-4),
    ("C48", "54,130 evaluable test pairs", "test_secondary", ("evaluable_pairs",), "==", 54130, 0),
    ("C49", "MAESTRO_ALL (98 secondaries) beat MAESTRO_LOOP (32) by 8 hits", "test_secondary",
     ("secondary", "contrasts", "S5:1.0:MAESTRO_ALL-MAESTRO_LOOP", "difference"), "==", 8.0, 0),
    ("C50", "543 evidence values checked in SDR_veto's b = 1 records", "test_secondary",
     ("secondary", "S14_record_audit", "SDR_veto:1.0", "claims_checked"), "==", 543, 0),
    ("C51", "38 test compounds share a target gene with development", "leakage",
     ("test_compounds_sharing_a_target_gene_with_development",), "count", 38, 0),
    ("C52", "the dominant development family has 56 members", "split_transfer",
     ("split_transfer", "development", "largest_family_share_of_validated_z_le_-3", "family_members"), "==", 56, 0),
    ("C53", "77 of 125 development compounds are pan-active", "development", ("pan_active_compounds",), "==", 77, 0),
    ("C54", "uncertainty acquisition (LOOP_uncertain) +5 over MAESTRO_LOOP at b = 1", "test_secondary",
     ("secondary", "contrasts", "S11:1.0:LOOP_uncertain-MAESTRO_LOOP", "difference"), "==", 5.0, 0),
    ("C55", "R3: SDR_veto and MAESTRO_LOOP hits differ by 0", "test_secondary",
     ("review", "R3_hits_non_inferiority", "difference"), "==", 0.0, 0),
    ("C41", "development: line memory 67 vs no memory 65 (negligible)", "dev_memory",
     ("results", "line_memory_lambda1.0", "1.0"), "==", 67, 0),
    ("C42", "no test compound is a close analogue (Tanimoto >= 0.7) of a development compound", "leakage", ("close_analogues",), "count", 0, 0),
]


# README's arm table at b = 1 (validated hits; registered endpoint), typed by hand so the audit checks the transcription
TABLE_B1 = {"zero": 9, "random": 12, "D1_magnitude": 7, "D2_compound_z": 12, "D3_two_way_z": 12, "D3f_two_way_z_hits": 14,
            "D4_target_mutation": 11, "ML": 30, "VC": 32, "VC+S": 32, "ML+context": 38, "ML+mechanism": 28, "ML+transcriptional": 31,
            "MAESTRO": 22, "CONV_LOOP": 18, "MAESTRO_LOOP": 23, "CONV_frontier": 16, "MAESTRO_top": 27, "CONV_ALL": 23,
            "MAESTRO_ALL": 31, "LOOP_uncertain": 28, "LOOP_top": 29, "SDR_veto": 23, "SDR_acquire": 24, "SDR_veto_acquire": 24,
            "SDR_unverified": 21, "SDR_full": 23}
CLAIMS += [(f"T-{arm}", f"{arm} found {hits} validated hits at b = 1", "test_secondary", A + (arm, "validated_hits"), "==", hits, 0)
           for arm, hits in TABLE_B1.items()]


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
