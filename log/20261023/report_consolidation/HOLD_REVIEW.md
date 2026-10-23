# HOLD review: ownership and retirement evidence

Scope: all 19 directories left HOLD in `CODE_CANDIDATES.json`. This review adds ownership evidence only; it does not edit the original 142-directory/1,267-file candidate manifest. Policy update: key reports/results stay in `log/`; bulk data and downloaded source payloads move to corresponding `data/` locations under `DATA_MIGRATION_PLAN.json`, with old/new paths and hashes recorded in log. The paths below describe the locations observed during this audit and may be remapped by that migration plan.

A read-only scan found no registration in `STUDIES.json`, no exact source references in the earlier 616-file `src/`, `tools/`, `tests/`, and registered-study scan, and no matching command line among running Python/R/Node processes at the time of the check. A process scan is a snapshot, not a future guarantee. None is an unowned orphan: every directory has an exact `log/` output destination or an identifiable parent-role log.

The two early-update role probes were absorbed into the main phase: the biology source and review files are bound by `early_update_mechanism/FINAL_BINDINGS.json` and `biology/INDEPENDENT_SEAL.json`; the frontier/SPD check and cross-review are in `frontier/CROSS_REVIEW.md` and `CROSS_REVIEW_SEAL.json`. Both are covered by `early_update_mechanism/DECISION.md`. The MSE discovery and contrast roles similarly roll into `contrast_gate_check/DECISION.md` and the `research_records/REPORT.md` summary.

## Directory findings

### `research/autonomous_rsi_round1`

Owner: `log/20261021/autonomous_rsi_round1`. One-off OASIS metadata/lineage audit support. DATA_AUDITOR.md explicitly says these scripts were not executed; no scientific conclusion or completed analysis is claimed.
Execution: NOT_EXECUTED_PER_LOG; no final scientific conclusion.
Recommendation: RETIRE_ONE_OFF_CODE; retain the explicit non-execution note in log; migrate any source payload according to the data migration map.
Files (2, 5276 bytes): `data_auditor_lineage.py`, `data_auditor_metadata.py`.
Evidence: `log/20261021/autonomous_rsi_round1/DATA_AUDITOR.md`; `log/20261022/dynamic_source_followup/REPORT.md`.

### `research/az_chemical_identity_20261022`

Owner: `log/20261022/az_chemical_identity`. One-off chemical identity, source metadata, ZIP-prefix inspection and receipt sealing for the AZ paid-reference gate. Main gate decision and integrity/preservation ledgers own the output.
Execution: EXECUTED_ARTIFACTS_PRESENT; phase decision belongs to parent gate.
Recommendation: RETIRE_ONE_OFF_CODE; retain receipts/identity summary and parent decision in log; migrate source payloads as data.
Files (6, 19482 bytes): `extract_metadata.py`, `fetch_s2_from_zip.py`, `finalize_qualification.py`, `http_capture.py`, `inspect_local.py`, `inspect_zip_prefix.py`.
Evidence: `log/20261022/az_paid_reference_gate/DECISION.md`; `log/20261022/az_paid_reference_gate/REPORTING_INTEGRITY.json`; `log/20261022/az_paid_reference_gate/FINAL_INTEGRITY.json`.

### `research/biological_decision_scout_20261022`

Owner: `log/20261022/biological_decision_scout/sources`. MSE source discovery, archive-prefix recovery and saved-key audit. Absorbed into the contrast/MSE source qualification and its NO_PROMOTION decision.
Execution: EXECUTED_SOURCE_ARTIFACTS_PRESENT; no separate decision document.
Recommendation: RETIRE_ROLE_CODE; retain source captures, review seal and parent decision.
Files (3, 10113 bytes): `audit_mse_keys.py`, `fetch_sources.py`, `recover_zip_prefix.py`.
Evidence: `log/20261022/contrast_gate_check/DECISION.md`; `log/20261022/contrast_independent_review/MSE_SOURCE_REVIEW_SEAL.json`; `log/research_records/REPORT.md:27`.

### `research/contrast_independent_review_20261022`

Owner: `log/20261022/contrast_independent_review`. Independent MSE metadata reconstruction and common-unit qualification. Its audit/seal is incorporated into the contrast gate and later MSE source gate.
Execution: EXECUTED_AUDIT_SEAL_PRESENT.
Recommendation: RETIRE_ROLE_CODE; preserve reconstruction JSON, review/seal and parent decision.
Files (2, 13457 bytes): `audit_mse_metadata.py`, `qualify_mse_unit_scope.py`.
Evidence: `log/20261022/contrast_gate_check/DECISION.md`; `log/20261022/contrast_independent_review/MSE_SOURCE_REVIEW_SEAL.json`; `log/research_records/REPORT.md:27`.

### `research/contrast_mechanism_scout_20261022`

Owner: `log/20261022/contrast_mechanism_scout`. Source/header acquisition, algebra checks, initial sealing and a bounded proposal scout; parent report records NO_PROMOTION and links the decision.
Execution: SOURCE/REVIEW ARTIFACTS PRESENT; any proposal-call completion should be read from its receipt, not inferred from script presence.
Recommendation: RETIRE_ROLE_CODE; retain receipts and cross-review records in log; migrate source bodies to the mapped external-source data location.
Files (6, 11990 bytes): `acquire.py`, `algebra.py`, `header_only.py`, `inspect_sources.py`, `scout_api.py`, `seal_initial.py`.
Evidence: `log/20261022/contrast_gate_check/DECISION.md`; `log/research_records/REPORT.md:27`; `log/research_records/REPORT.md:25`.

### `research/decrypte_feedback_assay_20261022`

Owner: `log/20261022/decrypte_feedback_pilot/assay/source`. Assay/source metadata identity and bounded source fetch; parent pilot contract and bindings record seven HTTP attempts and preserve receipts.
Execution: EXECUTED; source receipts and contract exist.
Recommendation: RETIRE_ONE_OFF_CODE; retain receipts and parent decision in log; migrate source bytes as data.
Files (2, 2471 bytes): `chdi_identity.py`, `fetch_sources.py`.
Evidence: `log/20261022/decrypte_feedback_pilot/DECISION.md`; `log/20261022/decrypte_feedback_pilot/assay/CONTRACT.md`; `log/20261022/decrypte_feedback_pilot/FINAL_BINDINGS.json`.

### `research/decrypte_molecular_source_20261022`

Owner: `log/20261022/decrypte_feedback_pilot/molecular`. Molecular-file listing, selective download, header identity and source sealing. Molecular log seal binds exact source and code snapshots; parent pilot owns scientific decision.
Execution: EXECUTED; file list, source bodies, identity contract and SEAL are present.
Recommendation: RETIRE_ONE_OFF_CODE; retain the seal and result summary in log; migrate molecular source payloads as data.
Files (6, 7298 bytes): `download_selected.py`, `ftp_list.py`, `inspect_headers.py`, `parse_listing.py`, `probe.py`, `seal.py`.
Evidence: `log/20261022/decrypte_feedback_pilot/DECISION.md`; `log/20261022/decrypte_feedback_pilot/molecular/SEAL.json`; `log/20261022/decrypte_feedback_pilot/FINAL_BINDINGS.json`.

### `research/early_update_mechanism_biology_20261022`

Owner: `log/20261022/early_update_mechanism/biology`. Primary literature retrieval and independent/cross-review sealing for the early-update mechanism branch. Main early-update decision and bindings absorb this role work.
Execution: EXECUTED_REVIEW_AND_SEALS_PRESENT; no separate biological experiment.
Recommendation: RETIRE_ROLE_CODE; retain reviews/seals in log; migrate retrieved source payloads as data.
Files (5, 8845 bytes): `collect_primary.py`, `fetch_decryptE_text.py`, `read_primary.py`, `seal_cross.py`, `seal_independent.py`.
Evidence: `log/20261022/early_update_mechanism/DECISION.md`; `log/20261022/early_update_mechanism/FINAL_BINDINGS.json`; `log/20261022/early_update_mechanism/biology/INDEPENDENT_SEAL.json`.

### `research/early_update_mechanism_frontier_20261022`

Owner: `log/20261022/early_update_mechanism/frontier`. Frontier literature retrieval and SPD transport falsifier. Parent decision/cross-review absorb the branch; log explicitly says no biological input and no API call for the falsifier.
Execution: EXECUTED_BOUNDED_LOGIC_CHECK_AND_REVIEW; no biological experiment.
Recommendation: RETIRE_ROLE_CODE; retain result and sealed review in log; migrate captured source payloads as data.
Files (4, 9678 bytes): `archive_metadata.py`, `check_spd_transport.py`, `download_methods.py`, `retrieve_primary.py`.
Evidence: `log/20261022/early_update_mechanism/DECISION.md`; `log/20261022/early_update_mechanism/frontier/CROSS_REVIEW.md`; `log/20261022/early_update_mechanism/frontier/CROSS_REVIEW_SEAL.json`.

### `research/functional_transition_law_20261023`

Owner: `log/20261023/functional_transition_law`. Release metadata inspection, source review, temporal innovation check and phase verification. Root assessment says no numerical benchmark/RSI go; no biological fit, author-code execution or protected-value decode.
Execution: SOURCE/LOGIC REVIEW EXECUTED; no biological experiment; scoped no-go is recorded.
Recommendation: RETIRE_PHASE_CODE; retain root assessment, reviews, manifests and verification in log; migrate downloaded source payloads as data.
Files (8, 12273 bytes): `inspect_release.py`, `release_manifest.py`, `verify_phase.py`, `fetch.py`, `project.py`, `extract_text.py`, `source_review.py`, `temporal_innovation_check.py`.
Evidence: `log/20261023/functional_transition_law/ROOT_ASSESSMENT.md`; `log/20261023/functional_transition_law/START.md`; `log/20261023/functional_transition_law/VERIFICATION.json`.

### `research/generative_repair_source_20261022`

Owner: `log/20261022/generative_repair_renewal/source`. Archive and primary-source identity qualification, workbook/stock checks, extraction and sealing. Results are recorded in source and archive-followup subtrees; no standalone final scientific decision was found.
Execution: EXECUTED_SOURCE_QUALIFICATION; no final scientific conclusion in this subtree.
Recommendation: RETIRE_ONE_OFF_SOURCE_CODE; record no final conclusion and retain protocols/results/receipts/seals in log; migrate bulk source payloads as data.
Files (9, 22927 bytes): `annotation_text.py`, `archive_qualify.py`, `extract_links.py`, `identity_pass.py`, `inspect_archive_workbook.py`, `old_stock_check.py`, `qualify_primary.py`, `seal_archive.py`, `seal_primary.py`.
Evidence: `log/20261022/generative_repair_renewal/source/PROTOCOL.md`; `log/20261022/generative_repair_renewal/source/INDEPENDENT.md`; `log/20261022/generative_repair_renewal/source/archive_followup/RESULT.md`; `log/20261022/generative_repair_renewal/source/archive_followup/SEAL.json`.

### `research/measurement_repair_source_qualification_20261021`

Owner: `log/20261021/measurement_repair_source_qualification`. NCATS source acquisition, metadata inventory and blind-identity qualification. No separate final DECISION/REPORT was located for the code folder.
Execution: EXECUTED_ACQUISITION_ARTIFACTS_PRESENT; no final scientific conclusion located.
Recommendation: RETIRE_ONE_OFF_SOURCE_CODE; mark conclusion absent and retain receipt/identity summaries in log; migrate source/data payloads as data.
Files (3, 9445 bytes): `acquire_and_inventory.py`, `qualify_ncats.py`, `test_blind_inventory.py`.
Evidence: `log/20261021/measurement_repair_source_qualification/PROTOCOL.md`; `log/20261021/measurement_repair_source_qualification/METADATA_RECEIPT.json`; `log/20261021/measurement_repair_source_qualification/IDENTITY_ROWS.json`.

### `research/mse_mechanism_renewal_20261022`

Owner: `log/20261022/mse_mechanism_renewal`. Source and operation scout for MSE follow-up; later fixed source gate produced a scoped STOP with independent audit. Its experiment/decision ownership is the MSE source gate.
Execution: SCOUT_ARTIFACTS_PRESENT; parent gate conclusion is final for the fixed configuration.
Recommendation: RETIRE_ROLE_CODE; retain algebra/decision in log; migrate source payloads as data.
Files (4, 9066 bytes): `check_operation.py`, `fetch_primary.py`, `scout_api.py`, `seal_initial.py`.
Evidence: `log/20261022/mse_source_gate/DECISION.md`; `log/research_records/REPORT.md:25`.

### `research/mse_source_gate_audit_20261022`

Owner: `log/20261022/mse_source_gate_audit`. Independent reconstruction of the MSE source gate and manifest schema. The parent gate decision and postrun audit own the final result.
Execution: EXECUTED_POSTRUN_AUDIT_ARTIFACTS_PRESENT.
Recommendation: RETIRE_AUDIT_CODE; retain audit outputs in log; migrate any bulk source payloads as data.
Files (2, 23776 bytes): `reconstruct_source_gate.py`, `review_manifest_schema.py`.
Evidence: `log/20261022/mse_source_gate/DECISION.md`; `log/20261022/mse_source_gate_audit/postrun`; `log/research_records/REPORT.md:25`.

### `research/mse_source_gate_review_20261022`

Owner: `log/20261022/mse_source_gate_review`. Independent composition/schema and manifest review for the MSE gate. Final scientific disposition is in parent gate decision.
Execution: EXECUTED_REVIEW_ARTIFACTS_PRESENT.
Recommendation: RETIRE_AUDIT_CODE; retain review artifacts and parent decision in log; migrate bulk source payloads as data.
Files (2, 4127 bytes): `inspect_composition_schema.py`, `verify_manifest.py`.
Evidence: `log/20261022/mse_source_gate/DECISION.md`; `log/20261022/mse_source_gate_review/COMPOSITION_SCHEMA_INSPECTION.json`; `log/20261022/mse_source_gate_review/MANIFEST_REVIEW.json`.

### `research/oasis_evaluation_contract_20261021`

Owner: `log/20261021/oasis_evaluation_contract`. Duplicate-read checks and reservation/evaluation contract. The v2 reservation is hash-bound and consumed by later OASIS dev-g0 freeze; this role has no separate result conclusion.
Execution: CONTRACT_AND_RESERVATION_ARTIFACTS_PRESENT; later phase froze them.
Recommendation: RETIRE_CONTRACT_CODE; retain contract, amendment, reservation and downstream freeze in log; migrate source payloads as data.
Files (5, 22273 bytes): `check_duplicate_reads.py`, `reserve_chemistry.py`, `reserve_chemistry_initial_failed.py`, `test_reservation.py`, `verify_reservation.py`.
Evidence: `log/20261021/oasis_evaluation_contract/AMENDMENT_01.md`; `log/20261021/oasis_evaluation_contract/RESERVATION_v2.json`; `log/20261021/oasis_source_qualification/REPORT.md`; `log/20261022/oasis_dev_g0/PRE_OPEN_FREEZE.json`.

### `research/tggates_mechanism_review_20261022`

Owner: `log/20261022/tggates_functional_qualification`. Primary-mechanism/source review supporting the functional qualification. Parent decision says close the clock-correction core candidate while retaining the temporal asset.
Execution: REVIEW MATERIAL PRESENT; parent qualification decision exists.
Recommendation: RETIRE_ROLE_CODE; retain review outputs in log; migrate source payloads as data.
Files (4, 9995 bytes): `fetch_primary.py`, `followup_sources.py`, `primary_sources.py`, `source_review.py`.
Evidence: `log/20261022/tggates_functional_qualification/DECISION.md`; `log/20261022/tggates_functional_qualification/advocate_sources`; `log/20261022/tggates_functional_qualification/skeptic_sources`.

### `research/tggates_method_audit_20261022`

Owner: `log/20261022/tggates_functional_qualification`. Methods/lineage extraction and audit of the TG-GATEs functional qualification. Parent decision and observability report absorb the audit.
Execution: AUDIT/REPORT PRESENT; no separate biological fit.
Recommendation: RETIRE_AUDIT_CODE; retain lineage and observability reports in log; migrate source payloads as data.
Files (2, 4228 bytes): `extract_lineage.py`, `fetch_methods.py`.
Evidence: `log/20261022/tggates_functional_qualification/DECISION.md`; `log/20261022/tggates_functional_qualification/DOSE_LINEAGE_REPORT.md`; `log/20261022/tggates_functional_qualification/clock_observability/REPORT.md`.

### `research/tggates_rna_feedback_pilot_20261022`

Owner: `log/20261022/tggates_rna_feedback_pilot`. Full RNA source/preprocessing and pilot pipeline. The final result review records actual processing/fits, ordinary-control wins and the scoped STOP. Large executed phase; code deletion reduces future replay, but records/predictions/integrity and exact source receipts are retained.
Execution: EXECUTED_REAL_DATA_PIPELINE; final result and stop exist.
Recommendation: RETIRE_PHASE_CODE_WITH_REPLAY_LIMIT; retain result review, predictions, receipts, integrity and seals in log; migrate bulk datasets/external sources to mapped data locations. Code deletion still limits future replay.
Files (56, 206798 bytes): `audit_conversion_snapshot.py`, `build_rna_manifest.py`, `call_review.py`, `checkpoint.py`, `close_implementation_audit.py`, `diagnose_cdf.R`, `diagnose_cdf_environment.R`, `export_manufacturer_probesets.R`, `extract_available.py`, `finalize_next_mechanism_review.py`, `finalize_phase.py`, `freeze_acquisition.py`, `freeze_numerical_execution.py`, `freeze_protocols.py`, `freeze_signature_annotation.py`, `gate_geometry_audit.py`, `inspect_cdf_package.py`, `install_affy_private.R`, `linear_models.py`, `mas5_single_array.R`, `mas5_single_array_v2.R`, `mechanism_local_audit.py`, `mechanism_r_environment.R`, `pilot_core.py`, `post_result_reviews.py`, `prepare_audit_resolution.py`, `prepare_code_audit.py`, `prepare_cross_reviews.py`, `prepare_next_mechanism_cross.py`, `prepare_next_mechanism_review.py`, `prepare_numeric_inputs.py`, `prepare_qc_revision.py`, `preserve.py`, `processed_source_code_metadata.py`, `process_arrivals.py`, `revalidate_application_scope.py`, `review_actual_result.py`, `rna_archive_acquire.py`, `rna_archive_heads.py`, `rna_metadata_followup.py`, `rna_metadata_sources.py`, `rna_processed_metadata.py`, `run_mas5.py`, `run_mas5_v2.py`, `run_pilot.py`, `run_when_ready.py`, `score_pilot.py`, `seal_data_metadata.py`, `test_full_pipeline.py`, `test_linear_models.py`, `test_pilot_core.py`, `test_prepare_numeric_inputs.py`, `test_rna_archive_acquire.py`, `test_score_pilot.py`, `reference_assembly.py`, `test_reference_assembly.py`.
Evidence: `log/20261022/tggates_rna_feedback_pilot/RESULT_REVIEW_DECISION.md`; `log/20261022/tggates_rna_feedback_pilot/FINAL_INTEGRITY.json`; `log/20261022/tggates_rna_feedback_pilot/PREDICTION_SEAL.json`; `log/research_records/REPORT.md:39`.

## Residual orphan review

No true orphan code was identified in the 19 HOLD directories. `autonomous_rsi_round1` explicitly has no execution claim in its owner note; `generative_repair_source_20261022` and `measurement_repair_source_qualification_20261021` have source receipts/results but no final scientific conclusion located. Their key reports should carry those limitations if the scripts are retired; data/source payloads follow the migration map and remain hash-linked. `tggates_rna_feedback_pilot_20261022` did execute a real-data pipeline; removing its code limits future reruns, while the final decision, predictions, receipts, integrity records, and seals remain in `log/`; bulk source/data payloads migrate to mapped `data/` destinations.
