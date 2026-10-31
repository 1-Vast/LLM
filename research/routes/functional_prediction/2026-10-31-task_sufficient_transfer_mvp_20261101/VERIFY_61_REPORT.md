# VERIFY 61 independent numerical report

## Verdict

- `pipeline_verdict`: **PASS**
- `scientific_gate`: **INCONCLUSIVE**

The pipeline artifacts are internally consistent under the allowed-input boundary. The scientific gate remains inconclusive because the frozen protocol defines an exploratory, non-confirmatory pilot and no independent external test is present.

## Frozen inputs and data contract

- PROTOCOL SHA-256: `a73b24c4c4e9b5633d82322243fb741761003a9db7ff1486a17d676279baac1e`; FREEZE match: `True`
- dev_pool SHA-256: `1a09d2d5aa13e84a7744c8eea4bd0b07a64e76dd259e5b4a856e1e0ee387a15d`; FREEZE match: `True`
- Schema matches FREEZE metadata for all array fields: `True`; derived scalar metadata are recorded as `NOT_APPLICABLE` to NPZ key schema.
- Deterministic fold rule independently reproduced as `sha256(ik14 or missing-singleton-{index}) mod 5`; fold counts: `[272, 274, 280, 294, 283]`
- Active rule independently reproduced (`>=5%` finite LFC values `<= -1`): `348` active compounds

## Checks

- `protocol_hash_matches_freeze`: `True`
- `data_hash_matches_freeze`: `True`
- `schema_matches_freeze` (array fields): `True`
- `fold_array_matches_predictions`: `True`
- `fold_counts_match_results`: `True`
- `active_array_matches_predictions`: `True`
- `active_count_348`: `True`
- `global_residual_equals_gat`: `True`
- `raw_k5_query5_recomputed`: `True`
- `raw_k20_query5_recomputed`: `True`
- `chemistry_k20_query5_recomputed`: `True`
- `gat_d5_query5_recomputed`: `True`
- `full_flat_query5_recomputed`: `True`
- `csv_summary_matches_results`: `True`
- `residualized_primary_match_all_1403`: `True`

## Schema check correction

The initial draft compared NPZ array keys to FREEZE derived scalar metadata (`finite_signature_fraction`, `finite_profile_fraction`, `missing_ik14`) and showed a false mismatch. The corrected check compares the seven array fields only; all shape/dtype pairs match.

## Independent numerical recomputation

- `raw_k5`, `raw_k20`, and `chemistry_k20` were independently recomputed for representative held-out query 5 and matched the saved predictions.
- `gat_d5_k20` was independently recomputed for query 5 using reference-only per-option centering and full SVD top-5 residualisation and matched.
- `full_flat_residual_k20` was independently recomputed for query 5 and matched.
- `global_residual_diagnostic` equals `gat_d5_k20` to floating-point precision.
- An independent constrained metric check reports residualized primary top-m hit precision matches the CSV for all 1,403 queries/method rows; CSV summaries reaggregate to RESULTS.

## Uncompleted arms and limits

`pca_residual_k2/5/10/20/50/100`, `random_residual_k2/5/10/20/50/100`, and `ridge_raw` were **NOT_RECOMPUTED** independently in this pass. Their saved predictions and summary records were only checked structurally. No causal, biological-mechanism, generalization, or external-test conclusion is warranted.

No protocol deviation was confirmed. A raw-vs-residualized ranking coincidence for one query was not treated as a deviation after the all-query residualized check matched the CSV.
