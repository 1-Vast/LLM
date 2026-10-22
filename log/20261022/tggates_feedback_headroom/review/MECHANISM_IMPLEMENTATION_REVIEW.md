# Mechanism implementation review — initial version, final SHA pending

2026-10-22. Read run_headroom.py, prepare.py, metadata-only MANIFEST prefix and revised PROTOCOL_DRAFT. No raw ZIP/CSV, DNA/LDH numeric projection, target array or RNA opened; no numerical execution. The runner is being revised by skeptic for KRR response centering, partial-numeric exposure accounting and development bootstrap. This review does **not** approve a moving/final file; final code SHA and those revisions must be confirmed separately. Prior API/renewal records unchanged.

## Data-flow findings

The primary role boundary is correctly placed: permitted_samples builds only source/development exact sample keys. project_rows obtains EXP_ID/GROUP_ID/INDIVIDUAL_ID first, skips every key outside that map and only then compares remaining identity fields or accesses response columns. Because prepare asserts global selected treatment-key uniqueness across roles, a later/control row cannot alias an allowed source key. Later Low/Middle/High and control assay strings are all skipped; this is stronger than filtering only laterHigh. A selected identity mismatch also fails before assay access. Byte decoding/CSV tokenization still contacts all raw strings as disclosed; no OS isolation is claimed.

Required meaningful synthetic guard: a skipped row object should raise if DNA/LDH or nonkey assay access occurs; include later and control cases, not merely corrupt numeric strings. Also test selected mismatched identity, duplicate/absent keys and DNA-success/LDH-invalid partial exposure. The existing hardcoded skipped_response_columns_accessed=0 is supported by this audited control flow and guard test, not a runtime instrumentation measurement; label it accordingly in reporting.

Projection preserves finite negative and >100 percentages, divides by100 and flags them. It aborts missing/unparseable/nonfinite selected data instead of dropping compounds. Aggregation uses all prelisted replicates, arithmetic means and ddof1SD (single-observation0). Lower-dose source/dev outcomes are extracted by design but are not predictor inputs in this fixedMiddle screen; they remain study exposure/cost and cannot silently enter later policy development.

## Predictor input and fold findings

feature_arrays accesses High concentration and Middle concentration/mean/SD only. It does not access test/development High mean/SD as features. targets(test) is reached for lawful development evaluation and prediction output, not model fitting. Fingerprints and all45unit vocabulary are frozen outcome-blind metadata; using that vocabulary is permitted catalog metadata exposure rather than future response leakage.

Source LOCO removes all rows sharing the held proxy block before training. StandardScaler and RBF positive-distance median are fitted inside each source training fold; zero variance receives sklearn's standard behavior. Later labels/High targets cannot enter source feature scaling. Source-selected hyperparameter CV performance remains a selected tuning score, not unbiased nested validation. Final development fits use all source and the frozen source-selected config per family.

Nearest-Tanimoto transfer is explicitly Middle plus the selected source compound's High−Middle residual; ties choose lexicographically smallest training compound_label. Empty-union similarity is1.0. This label is a deterministic tie break, not a learned chemical feature. Constant sourceHigh median and median residual are recomputed from fold training data. The RBF no-positive-distance fallback is fixed1.0; include that predeclared deterministic choice in final protocol. It is source-only and not an outcome-tuned rescue.

The initial KRR lacked a response intercept; root/skeptic have already identified the correct centering/add-back change. A strong direct baseline should be translation equivariant like the constant/offset competitors. Verify both outputs receive train-only centering and the mean is restored for test predictions. No dev mean may enter this step.

## One additional ledger fix recommended before freeze

The initial runner counts fits by family but catches an exception with only error_type. If a source fold/model fails, SOURCE_CV has not yet been written, so the exact failing candidate and held-out block are lost. Add the active candidate config and source-held-out block (or final-development context) to the failure receipt before every fit. Training/prediction label or block identifiers are sufficient; no new response value is needed. Retain the existing cumulative attempt counts, and distinguish sklearn actual calls versus pipeline attempts if an exception can occur before model.fit. This is a small auditability fix, not a request for another model abstraction.

For the declared menu, a complete run should make29candidate pipelines×24source folds plus9source-selected development pipelines =705pipeline fits/attempts. Actual sklearn fit calls should be24learned configs×24folds plus4selected learned development families =580, absent failed/retried work. Constants/copy/nearest rules are pipeline evaluations rather than sklearn optimization calls. Source/development fit grids and selected configs must all be retained.

The parent is already adding partial-cast accounting: a finite DNA conversion followed by invalid LDH has exposed DNA even though no complete record is saved. A receipt based only on complete projection record count would understate that exposure. Confirm the new counters count assay lookups/conversion attempts/successes separately and leave skipped/later response values untouched.

## Routing and uncertainty findings

The revised strictly>0.02 future requirement makes stop at development MAE<=0.02 arithmetically consistent. It is a local exposed-development headroom statement only. The best family is the minimum across fixed prelisted development scores; any bootstrap describes the already selected predictions conditional on these groups, not unbiased model-selection or future-culture uncertainty. Bootstrap whole proxy groups and retain equal-compound primary loss; do not bootstrap individual assay repeats. Small seven-group development limits precision. The gate itself is based on the declared observed MAE, not on post-hoc CI-based threshold changes.

The current screen cannot establish that any error is reducible by RNA, that the innovation branches are scientifically distinct, or that the full Middle RNA/function acquisition is cost-effective. The exact ordinaryjoint/direct algebraic copy is correctly scoped as the same method; future comparisons must not demand beating it. No agent query, CL/inheritance or C4 claim is supported by this runner.

**Current conclusion: data-flow and predictor construction are suitable for the narrow protocol, conditional on the parent-listed three fixes, the failure-context ledger fix, synthetic checks and final SHA confirmation. No raw numerical run is authorized by this review alone.**
