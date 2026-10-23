# Luna code cleanup audit

Repository: `D:\MAESTRO`; HEAD `9c6fc0e5`. This is a read-only candidate audit for the requested cleanup. It covers all 202 immediate local directories under `research/`, including untracked directories, rather than only the Git tree. `CODE_CANDIDATES.json` is the exact-path manifest with per-directory file counts/bytes, per-code-file bytes and Git tracking status, log mapping and decision/report excerpts, and source-code reference hits.

## Findings

The manifest contains **142 candidate directories with 1267 exact code-file paths**. These are unregistered one-off or completed phase scripts with a corresponding final log document, no exact directory/path mention in the scanned runtime/formal source code, and no identified current-run dependency. A local phase can be complete even where the overall research objective remains active; historical provenance mentions in logs are retained as evidence and do not block cleanup.

**19 directories were marked HOLD in the original manifest** because the first pass lacked a reliable final-log or parent-role match. The follow-up `HOLD_REVIEW.md`/`.json` subsequently traced all 19 to log outputs or parent-role records and found no true orphan; the original candidate manifest and its 19 HOLD labels remain unchanged as the historical first-pass result. The retained set includes all 39 registered study code trees and the two current studies named by the task.

The dependency scan covered 616 source files across `src/`, `tools/`, `tests/`, and the 39 registered study trees. Exact target-name/path references are stored per directory; all proposed candidate directories have zero such hits. `log/` itself was not treated as a runtime root. Historical log references are evidence/provenance, not a runtime dependency.

## Preserve records and evidence

Keep concise key reports and result records in `log/`. Move bulk data and external source payloads to their corresponding `data/` locations (for example `data/raw/research_inputs`, `data/external/research_sources`, and `data/processed/research_results`); the exact nested destinations are defined by `DATA_MIGRATION_PLAN.json` when produced. Preserve payload contents and record old/new paths plus hashes in the migration map. The inventory in `CODE_CANDIDATES.json` lists 638 code-like files found under `log/` at audit time (2,605,274 bytes); many are downloaded source-code assets and should migrate as external source data, not be deleted or treated as runtime code. No code is promoted to `src/` or `tools/` by this audit.

The archive step keeps the top-level historical `REPORT`/`EVIDENCE`/`STUDIES` and other key reports/results under `log/research_records/<research-relative-path>/`; bulk data moves to the mapped `data/` destination with original-path hashes and a path migration record in `log/`. The earlier archive batch reported 1,641 files / about 2.56 GB undergoing SHA verification; that inventory is subject to the revised data placement policy. Registered study code remains protected in `research/` unless separately validated and promoted. Candidate paths in the JSON are exact files only; they are not whole-directory delete instructions. No experiments, APIs, promotions, or research-code deletions were performed by this audit.

## Candidate directories

- `research/action_rule_search_20261023` — 17 code files, 28014 bytes; log evidence: `log/20261023/action_rule_search/DECISION.md`.
- `research/almanac_feedback_pilot_20261022` — 17 code files, 52733 bytes; log evidence: `log/20261022/almanac_feedback_pilot/DECISION.md`.
- `research/aml_identity_qualification_20261023` — 10 code files, 26144 bytes; log evidence: `log/20261023/aml_identity_qualification/DECISION.md`.
- `research/antibiotic_schedule_qualification_20261022` — 16 code files, 47144 bytes; log evidence: `log/20261022/antibiotic_schedule_qualification/DECISION.md`, `log/20261022/antibiotic_schedule_qualification/schema_audit/REPORT.md`, `log/20261022/antibiotic_schedule_qualification/title_registry_audit/REPORT.md`, `log/20261022/antibiotic_schedule_qualification/title_registry_audit/version_followup/REPORT.md`.
- `research/antibiotic_state_refinement_review_20261022` — 3 code files, 9437 bytes; log evidence: `log/20261022/antibiotic_state_refinement_review/DECISION.md`, `log/20261022/antibiotic_state_refinement_review/primary_prior/REPORT.md`.
- `research/api_evidence_innovation_20261022` — 10 code files, 36589 bytes; log evidence: `log/20261022/api_evidence_innovation/DECISION.md`.
- `research/attenuation_identifiability_20261023` — 7 code files, 23930 bytes; log evidence: `log/20261023/attenuation_identifiability/DECISION.md`.
- `research/az_paid_reference_gate_20261022` — 19 code files, 205371 bytes; log evidence: `log/20261022/az_paid_reference_gate/DECISION.md`.
- `research/caf_mechanics_qualification_20261022` — 14 code files, 32625 bytes; log evidence: `log/20261022/caf_mechanics_qualification/DECISION.md`.
- `research/cardiac_mechanism_review_20261022` — 3 code files, 9033 bytes; log evidence: role-owner mapping in JSON.
- `research/cdk_functional_increment_20261022` — 5 code files, 22009 bytes; log evidence: `log/20261022/cdk_functional_increment/DECISION.md`.
- `research/cdk_middle_feedback_20261022` — 10 code files, 42284 bytes; log evidence: `log/20261022/cdk_middle_feedback/DECISION.md`.
- `research/chemical_genetics_qualification_20261022` — 15 code files, 72561 bytes; log evidence: `log/20261022/chemical_genetics_qualification/DECISION.md`, `log/20261022/chemical_genetics_qualification/REPORT.md`, `log/20261022/chemical_genetics_qualification/identity_followup/REPORT.md`, `log/20261022/chemical_genetics_qualification/numeric_identity/REPORT.md`, `log/20261022/chemical_genetics_qualification/workbook_identity/REPORT.md`.
- `research/cipa_calibration_probe_20261022` — 8 code files, 74619 bytes; log evidence: `log/20261022/cipa_calibration_probe/DECISION.md`.
- `research/cipa_control_information_20261022` — 8 code files, 85688 bytes; log evidence: `log/20261022/cipa_control_information/DECISION.md`.
- `research/contrast_gate_check_20261022` — 2 code files, 7309 bytes; log evidence: `log/20261022/contrast_gate_check/DECISION.md`.
- `research/contrast_transport_mechanism_20261023` — 6 code files, 24335 bytes; log evidence: `log/20261023/contrast_transport_mechanism/DECISION.md`.
- `research/cross_context_interaction_20261023` — 4 code files, 5855 bytes; log evidence: `log/20261023/cross_context_interaction/DECISION.md`.
- `research/cxcl9_source_feasibility_20261023` — 14 code files, 44673 bytes; log evidence: `log/20261023/cxcl9_source_feasibility/DECISION.md`.
- `research/dead_stock_information_gate_20261022` — 16 code files, 73398 bytes; log evidence: `log/20261022/dead_stock_information_gate/DECISION.md`, `log/20261022/dead_stock_information_gate/data_auditor/target_failure_audit/REPORT.md`.
- `research/decision_probe_mechanism_20261023` — 7 code files, 10600 bytes; log evidence: `log/20261023/decision_probe_mechanism/DECISION.md`.
- `research/decision_update_mechanism_20261022` — 3 code files, 6187 bytes; log evidence: `log/20261022/decision_update_mechanism/DECISION.md`.
- `research/decrypte_feedback_audit_20261022` — 1 code files, 9595 bytes; log evidence: `log/20261022/decrypte_feedback_pilot/DECISION.md`, `log/20261022/decrypte_source_qualification/DECISION.md`.
- `research/decrypte_feedback_pilot_20261022` — 7 code files, 31535 bytes; log evidence: `log/20261022/decrypte_feedback_pilot/DECISION.md`.
- `research/decrypte_molecular_audit_20261022` — 1 code files, 3489 bytes; log evidence: `log/20261022/decrypte_molecular_increment/key_correction/DECISION.md`.
- `research/decrypte_molecular_download_20261022` — 5 code files, 14363 bytes; log evidence: `log/20261022/decrypte_molecular_increment/key_correction/DECISION.md`.
- `research/decrypte_molecular_increment_20261022` — 10 code files, 40989 bytes; log evidence: `log/20261022/decrypte_molecular_increment/key_correction/DECISION.md`.
- `research/decrypte_molecular_increment_audit_20261022` — 1 code files, 13478 bytes; log evidence: `log/20261022/decrypte_feedback_pilot/DECISION.md`, `log/20261022/decrypte_molecular_increment/key_correction/DECISION.md`.
- `research/decrypte_molecular_key_correction_20261022` — 2 code files, 7662 bytes; log evidence: `log/20261022/decrypte_molecular_increment/key_correction/DECISION.md`.
- `research/decrypte_source_qualification_20261022` — 4 code files, 11006 bytes; log evidence: `log/20261022/decrypte_source_qualification/DECISION.md`.
- `research/depmap_state_increment_20261023` — 7 code files, 32860 bytes; log evidence: `log/20261023/depmap_state_increment/DECISION.md`.
- `research/dose_update_qualification_20261023` — 11 code files, 25603 bytes; log evidence: `log/20261023/dose_update_qualification/DECISION.md`.
- `research/dynamic_source_followup_20261022` — 5 code files, 13570 bytes; log evidence: `log/20261022/dynamic_source_followup/REPORT.md`, `log/20261022/dynamic_source_followup/ncbi_scout/REPORT.md`, `log/20261022/dynamic_source_followup/ncbi_scout/version_followup/REPORT.md`.
- `research/early_update_mechanism_20261022` — 4 code files, 10584 bytes; log evidence: `log/20261022/early_update_mechanism/DECISION.md`.
- `research/early_update_mechanism_recursive_20261022` — 3 code files, 7783 bytes; log evidence: `log/20261022/rsi_later_task_literature/DECISION.md`.
- `research/efaecalis_dynamic_qualification_20261022` — 16 code files, 84271 bytes; log evidence: `log/20261022/efaecalis_dynamic_qualification/DECISION.md`, `log/20261022/efaecalis_dynamic_qualification/REPORT.md`, `log/20261022/efaecalis_dynamic_qualification/code_io/REPORT.md`, `log/20261022/efaecalis_dynamic_qualification/numeric_identity/REPORT.md`, `log/20261022/efaecalis_dynamic_qualification/rank_pilot/REPORT.md`, `log/20261022/efaecalis_dynamic_qualification/redirect_followup/REPORT.md`.
- `research/emerald_functional_rule_20261023` — 9 code files, 32094 bytes; log evidence: `log/20261023/emerald_functional_rule/DECISION.md`.
- `research/feedback_law_discovery_20261023` — 22 code files, 70408 bytes; log evidence: `log/20261023/feedback_law_discovery/DECISION.md`.
- `research/feedback_shift_mechanism_20261023` — 18 code files, 38788 bytes; log evidence: `log/20261023/feedback_shift_mechanism/DECISION.md`.
- `research/feedback_sufficiency_renewal_20261023` — 11 code files, 17884 bytes; log evidence: `log/20261023/feedback_sufficiency_renewal/DECISION.md`.
- `research/frontier_mechanism_renewal_20261022` — 5 code files, 10219 bytes; log evidence: `log/20261022/frontier_mechanism_renewal/DECISION.md`.
- `research/frontier_operator_20261022` — 5 code files, 13989 bytes; log evidence: `log/20261022/operator_renewal/root/DECISION.md`.
- `research/frontier_transfer_20261022` — 3 code files, 3445 bytes; log evidence: `log/20261022/frontier_transfer/DECISION.md`.
- `research/function_update_renewal_20261023` — 12 code files, 21162 bytes; log evidence: `log/20261023/function_update_renewal/DECISION.md`.
- `research/functional_dynamics_gate_20261022` — 18 code files, 63767 bytes; log evidence: `log/20261022/functional_dynamics_gate/DECISION.md`.
- `research/functional_error_renewal_20261023` — 10 code files, 31656 bytes; log evidence: `log/20261023/functional_error_renewal/DECISION.md`.
- `research/functional_error_structure_20261022` — 2 code files, 6737 bytes; log evidence: `log/20261022/functional_error_structure/DECISION.md`.
- `research/functional_mechanism_frontier_20261023` — 11 code files, 17751 bytes; log evidence: `log/20261023/functional_mechanism_frontier/DECISION.md`.
- `research/functional_operator_20261022` — 5 code files, 13093 bytes; log evidence: role-owner mapping in JSON.
- `research/functional_rule_discovery_20261023` — 13 code files, 17973 bytes; log evidence: `log/20261023/functional_rule_discovery/DECISION.md`.
- `research/functional_source_bridge_20261023` — 15 code files, 28163 bytes; log evidence: `log/20261023/functional_source_bridge/DECISION.md`, `log/20261023/functional_source_bridge/growth/DECISION.md`.
- `research/functional_update_operation_20261023` — 6 code files, 14675 bytes; log evidence: `log/20261023/functional_update_operation/DECISION.md`.
- `research/grounded_feedback_renewal_20261023` — 11 code files, 12109 bytes; log evidence: `log/20261023/grounded_feedback_renewal/DECISION.md`.
- `research/hcc_link_recovery_20261023` — 6 code files, 11281 bytes; log evidence: `log/20261023/hcc_link_recovery/DECISION.md`.
- `research/hcc_task_qualification_20261023` — 14 code files, 22792 bytes; log evidence: `log/20261023/hcc_task_qualification/DECISION.md`.
- `research/inherited_update_renewal_20261023` — 14 code files, 29609 bytes; log evidence: `log/20261023/inherited_update_renewal/DECISION.md`.
- `research/interaction_error_diagnostic_20261023` — 12 code files, 48954 bytes; log evidence: `log/20261023/interaction_error_diagnostic/DECISION.md`.
- `research/intervention_constraint_20261023` — 8 code files, 22929 bytes; log evidence: `log/20261023/intervention_constraint/DECISION.md`.
- `research/intervention_dynamics_renewal_20261022` — 38 code files, 153677 bytes; log evidence: `log/20261022/intervention_dynamics_renewal/DECISION.md`, `log/20261022/intervention_dynamics_renewal/ap1_code_io/REPORT.md`, `log/20261022/intervention_dynamics_renewal/functional_scout/REPORT.md`, `log/20261022/intervention_dynamics_renewal/melanoma_sequence/REPORT.md`.
- `research/intervention_program_renewal_20261022` — 19 code files, 72352 bytes; log evidence: `log/20261022/intervention_program_renewal/DECISION.md`.
- `research/intervention_schedule_qualification_20261022` — 13 code files, 37734 bytes; log evidence: `log/20261022/intervention_schedule_qualification/DECISION.md`.
- `research/mechanism_gap_20261022` — 6 code files, 24963 bytes; log evidence: `log/20261022/mechanism_gap/root/DECISION.md`.
- `research/mechanism_gap_frontier_20261022` — 2 code files, 6378 bytes; log evidence: role-owner mapping in JSON.
- `research/mechanism_gap_functional_20261022` — 7 code files, 14529 bytes; log evidence: role-owner mapping in JSON.
- `research/mechanism_gap_recursive_20261022` — 1 code files, 5452 bytes; log evidence: role-owner mapping in JSON.
- `research/mechanism_reentry_20261023` — 12 code files, 21062 bytes; log evidence: `log/20261023/mechanism_reentry/DECISION.md`.
- `research/mixed_feedback_estimator_20261023` — 13 code files, 58718 bytes; log evidence: `log/20261023/mixed_feedback_estimator/DECISION.md`.
- `research/mse_source_gate_20261022` — 5 code files, 26483 bytes; log evidence: `log/20261022/mse_source_gate/DECISION.md`.
- `research/multi_context_state_function_20261022` — 15 code files, 26781 bytes; log evidence: `log/20261022/multi_context_state_function/DECISION.md`.
- `research/naiad_direct_baseline_20261022` — 8 code files, 37893 bytes; log evidence: `log/20261022/naiad_direct_baseline/DECISION.md`.
- `research/native_biological_20261022` — 11 code files, 12550 bytes; log evidence: role-owner mapping in JSON.
- `research/native_improver_20261022` — 7 code files, 13703 bytes; log evidence: role-owner mapping in JSON.
- `research/native_operation_20261022` — 10 code files, 28265 bytes; log evidence: `log/20261022/native_operation/improver/FINAL_SCOPED_DECISION.md`, `log/20261022/native_operation/root/DECISION.md`.
- `research/next_asset_20261022` — 23 code files, 32768 bytes; log evidence: `log/20261022/next_asset/DECISION.md`.
- `research/next_mechanism_20261022` — 8 code files, 26972 bytes; log evidence: `log/20261022/next_mechanism/root/DECISION.md`.
- `research/next_mechanism_frontier_20261022` — 3 code files, 7961 bytes; log evidence: role-owner mapping in JSON.
- `research/next_mechanism_recursive_20261022` — 11 code files, 12053 bytes; log evidence: `log/20261022/rsi_external_proposal_review/DECISION.md`.
- `research/next_mechanism_source_20261022` — 6 code files, 25579 bytes; log evidence: `log/20261022/mechanism_gap/root/DECISION.md`.
- `research/norman_baseline_calibration_20261022` — 3 code files, 11830 bytes; log evidence: `log/20261022/norman_baseline_calibration/DECISION.md`.
- `research/norman_feedback_transport_20261022` — 3 code files, 12174 bytes; log evidence: `log/20261022/norman_feedback_transport/DECISION.md`.
- `research/norman_function_reliability_20261022` — 6 code files, 23434 bytes; log evidence: `log/20261022/norman_function_reliability/DECISION.md`.
- `research/norman_functional_contract_20261022` — 11 code files, 20706 bytes; log evidence: `log/20261022/norman_functional_contract/DECISION.md`.
- `research/norman_matched_guide_20261022` — 8 code files, 31739 bytes; log evidence: `log/20261022/norman_matched_guide/DECISION.md`.
- `research/norman_numeric_qualification_20261022` — 5 code files, 13755 bytes; log evidence: `log/20261022/norman_numeric_qualification/DECISION.md`.
- `research/oasis_dev_g0_20261022` — 6 code files, 38399 bytes; log evidence: `log/20261022/oasis_dev_g0/REPORT.md`.
- `research/oasis_identity_qualification_20261021` — 5 code files, 17327 bytes; log evidence: `log/20261021/oasis_source_qualification/REPORT.md`.
- `research/oasis_source_qualification_20261021` — 5 code files, 16881 bytes; log evidence: `log/20261021/oasis_source_qualification/REPORT.md`.
- `research/observation_law_search_20261023` — 14 code files, 31554 bytes; log evidence: `log/20261023/observation_law_search/DECISION.md`.
- `research/operator_renewal_20261022` — 6 code files, 28174 bytes; log evidence: `log/20261022/operator_renewal/root/DECISION.md`.
- `research/organoid_schedule_forecast_20261023` — 6 code files, 28203 bytes; log evidence: `log/20261023/organoid_schedule_forecast/DECISION.md`.
- `research/organoid_schedule_qualification_20261023` — 6 code files, 10563 bytes; log evidence: `log/20261023/organoid_schedule_qualification/DECISION.md`.
- `research/plk1_payload_qualification_20261022` — 5 code files, 8403 bytes; log evidence: `log/20261022/plk1_payload_qualification/DECISION.md`.
- `research/post_almanac_biology_20261022` — 1 code files, 1479 bytes; log evidence: role-owner mapping in JSON.
- `research/post_almanac_frontier_20261022` — 5 code files, 6769 bytes; log evidence: role-owner mapping in JSON.
- `research/post_almanac_mechanism_20261022` — 7 code files, 17183 bytes; log evidence: `log/20261022/post_almanac_mechanism/DECISION.md`.
- `research/post_almanac_skeptic_20261022` — 2 code files, 1626 bytes; log evidence: role-owner mapping in JSON.
- `research/post_anchor_mechanism_20261023` — 25 code files, 41796 bytes; log evidence: `log/20261023/post_anchor_mechanism/DECISION.md`.
- `research/post_decrypte_renewal_20261022` — 13 code files, 32945 bytes; log evidence: `log/20261022/post_decrypte_renewal/DECISION.md`.
- `research/post_decrypte_renewal_assay_20261022` — 2 code files, 1777 bytes; log evidence: role-owner mapping in JSON.
- `research/post_rna_mechanism_renewal_20261022` — 19 code files, 36361 bytes; log evidence: `log/20261022/post_rna_mechanism_renewal/DECISION.md`.
- `research/prism_profile_opportunity_20261022` — 14 code files, 68675 bytes; log evidence: `log/20261022/prism_profile_opportunity/DECISION.md`.
- `research/ptpc_late_information_20261022` — 9 code files, 39993 bytes; log evidence: `log/20261022/ptpc_late_information/DECISION.md`.
- `research/ptpc_late_information_audit_20261022` — 2 code files, 22628 bytes; log evidence: `log/20261022/ptpc_late_information/DECISION.md`, `log/20261022/ptpc_update_opportunity/DECISION.md`.
- `research/ptpc_update_opportunity_20261022` — 16 code files, 71119 bytes; log evidence: `log/20261022/ptpc_update_opportunity/DECISION.md`.
- `research/public_recovery_task_20261023` — 9 code files, 24683 bytes; log evidence: `log/20261023/public_recovery_task/DECISION.md`.
- `research/query_teacher_resolution_20261022` — 3 code files, 5180 bytes; log evidence: `log/20261022/query_teacher_resolution/DECISION.md`, `log/20261023/query_teacher_resolution/DECISION.md`.
- `research/query_teacher_resolution_20261023` — 3 code files, 4550 bytes; log evidence: `log/20261022/query_teacher_resolution/DECISION.md`, `log/20261023/query_teacher_resolution/DECISION.md`.
- `research/query_teacher_resolution_frontier_20261022` — 1 code files, 1469 bytes; log evidence: role-owner mapping in JSON.
- `research/rank_reversal_mechanism_20261023` — 9 code files, 24414 bytes; log evidence: `log/20261023/rank_reversal_mechanism/DECISION.md`.
- `research/rechallenge_forecast_20261023` — 7 code files, 27014 bytes; log evidence: `log/20261023/rechallenge_forecast/DECISION.md`.
- `research/rechallenge_task_20261023` — 9 code files, 20227 bytes; log evidence: `log/20261023/rechallenge_task/DECISION.md`.
- `research/reciprocity_resolution_20261023` — 9 code files, 24250 bytes; log evidence: `log/20261023/reciprocity_resolution/DECISION.md`.
- `research/recursive_operator_20261022` — 3 code files, 10195 bytes; log evidence: role-owner mapping in JSON.
- `research/regrowth_data_qualification_20261023` — 5 code files, 9910 bytes; log evidence: `log/20261023/regrowth_data_qualification/DECISION.md`.
- `research/renewal_application_20261022` — 25 code files, 79188 bytes; log evidence: `log/20261022/renewal_application/DECISION.md`.
- `research/repair_information_opportunity_20261022` — 6 code files, 24280 bytes; log evidence: `log/20261022/repair_information_opportunity/DECISION.md`.
- `research/repair_information_source_20261022` — 5 code files, 8256 bytes; log evidence: role-owner mapping in JSON.
- `research/replicated_contrast_20261023` — 9 code files, 23988 bytes; log evidence: `log/20261023/replicated_contrast/DECISION.md`.
- `research/replogle_growth_acquisition_20261022` — 10 code files, 20684 bytes; log evidence: `log/20261022/replogle_growth_acquisition/DECISION.md`.
- `research/response_law_revision_20261023` — 7 code files, 13988 bytes; log evidence: `log/20261023/response_law_revision/DECISION.md`.
- `research/reusable_error_mechanism_20261023` — 16 code files, 43828 bytes; log evidence: `log/20261023/reusable_error_mechanism/DECISION.md`.
- `research/revision_value_operation_20261022` — 5 code files, 11716 bytes; log evidence: `log/20261022/revision_value_operation/DECISION.md`.
- `research/rsi_external_proposal_review_20261022` — 2 code files, 5170 bytes; log evidence: `log/20261022/rsi_external_proposal_review/DECISION.md`.
- `research/rsi_later_task_literature_20261022` — 14 code files, 27455 bytes; log evidence: `log/20261022/rsi_later_task_literature/DECISION.md`.
- `research/rsi_next_qualification_20261021` — 6 code files, 30397 bytes; log evidence: `log/20261021/rsi_next_qualification/DECISION.md`.
- `research/serial_antibiotic_alternatives_20261022` — 15 code files, 50521 bytes; log evidence: `log/20261022/serial_antibiotic_alternatives/DECISION.md`, `log/20261022/serial_antibiotic_alternatives/REPORT.md`, `log/20261022/serial_antibiotic_alternatives/biosample_identity_followup/REPORT.md`, `log/20261022/serial_antibiotic_alternatives/manifest_followup/REPORT.md`, `log/20261022/serial_antibiotic_alternatives/manifest_followup/amendment2_sources/REPORT.md`, `log/20261022/serial_antibiotic_alternatives/supplement_followup/REPORT.md`.
- `research/srs_prefix_qualification_20261023` — 8 code files, 10002 bytes; log evidence: `log/20261023/srs_prefix_qualification/DECISION.md`.
- `research/stack_conditional_information_20261022` — 5 code files, 55706 bytes; log evidence: `log/20261022/stack_conditional_information/DECISION.md`.
- `research/stack_raw_qualification_20261022` — 18 code files, 43541 bytes; log evidence: `log/20261022/stack_raw_qualification/DECISION.md`.
- `research/strategy_rethink_20261022` — 8 code files, 31275 bytes; log evidence: role-owner mapping in JSON.
- `research/sustained_function_task_20261023` — 8 code files, 12124 bytes; log evidence: `log/20261023/sustained_function_task/DECISION.md`.
- `research/tggates_clock_observability_20261022` — 2 code files, 5797 bytes; log evidence: `log/20261022/tggates_functional_qualification/clock_observability/REPORT.md`.
- `research/tggates_feedback_headroom_20261022` — 12 code files, 97628 bytes; log evidence: `log/20261022/tggates_feedback_headroom/DECISION.md`.
- `research/tggates_functional_qualification_20261022` — 9 code files, 33309 bytes; log evidence: `log/20261022/tggates_functional_qualification/DECISION.md`, `log/20261022/tggates_functional_qualification/REPORT.md`, `log/20261022/tggates_functional_qualification/clock_observability/REPORT.md`.
- `research/tggates_source_qualification_20261022` — 4 code files, 10224 bytes; log evidence: `log/20261022/tggates_source_qualification/REPORT.md`.
- `research/update_law_search_20261023` — 11 code files, 24899 bytes; log evidence: `log/20261023/update_law_search/DECISION.md`.
- `research/update_rule_renewal_20261022` — 8 code files, 16510 bytes; log evidence: `log/20261022/update_rule_renewal/DECISION.md`.
- `research/update_rule_renewal_frontier_20261022` — 3 code files, 2815 bytes; log evidence: role-owner mapping in JSON.
- `research/update_signal_reassessment_20261022` — 6 code files, 8263 bytes; log evidence: `log/20261022/update_signal_reassessment/DECISION.md`.
- `research/update_strategy_renewal_20261023` — 11 code files, 20732 bytes; log evidence: `log/20261023/update_strategy_renewal/DECISION.md`.
- `research/update_value_qualification_20261022` — 22 code files, 91821 bytes; log evidence: `log/20261022/update_value_qualification/DECISION.md`.
- `research/vuscope_prefix_diagnostic_20261023` — 11 code files, 39758 bytes; log evidence: `log/20261023/vuscope_prefix_diagnostic/DECISION.md`.

## HOLD directories

- `research/autonomous_rsi_round1` — 2 code files; final log/role-owner evidence was not established.
- `research/az_chemical_identity_20261022` — 6 code files; final log/role-owner evidence was not established.
- `research/biological_decision_scout_20261022` — 3 code files; final log/role-owner evidence was not established.
- `research/contrast_independent_review_20261022` — 2 code files; final log/role-owner evidence was not established.
- `research/contrast_mechanism_scout_20261022` — 6 code files; final log/role-owner evidence was not established.
- `research/decrypte_feedback_assay_20261022` — 2 code files; final log/role-owner evidence was not established.
- `research/decrypte_molecular_source_20261022` — 6 code files; final log/role-owner evidence was not established.
- `research/early_update_mechanism_biology_20261022` — 5 code files; final log/role-owner evidence was not established.
- `research/early_update_mechanism_frontier_20261022` — 4 code files; final log/role-owner evidence was not established.
- `research/functional_transition_law_20261023` — 8 code files; final log/role-owner evidence was not established.
- `research/generative_repair_source_20261022` — 9 code files; final log/role-owner evidence was not established.
- `research/measurement_repair_source_qualification_20261021` — 3 code files; final log/role-owner evidence was not established.
- `research/mse_mechanism_renewal_20261022` — 4 code files; final log/role-owner evidence was not established.
- `research/mse_source_gate_audit_20261022` — 2 code files; final log/role-owner evidence was not established.
- `research/mse_source_gate_review_20261022` — 2 code files; final log/role-owner evidence was not established.
- `research/oasis_evaluation_contract_20261021` — 5 code files; final log/role-owner evidence was not established.
- `research/tggates_mechanism_review_20261022` — 4 code files; final log/role-owner evidence was not established.
- `research/tggates_method_audit_20261022` — 2 code files; final log/role-owner evidence was not established.
- `research/tggates_rna_feedback_pilot_20261022` — 56 code files; final log/role-owner evidence was not established.

The first audit pass marked every unregistered directory HOLD because its simple log-name matching was insufficient. This revision adds final log document matching, explicit log paths and parent-role ownership evidence, plus the source dependency scan; the later `HOLD_REVIEW` follow-up resolves those ownership gaps while leaving the original first-pass labels unchanged.


Audit housekeeping: temporary scan/helper files created during this audit were removed after the final manifest was written; the audit deliverables are this report, `CODE_CANDIDATES.json`, and the later `HOLD_REVIEW` pair.
