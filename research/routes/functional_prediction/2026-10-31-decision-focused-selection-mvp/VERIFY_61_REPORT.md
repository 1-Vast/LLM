# VERIFY 61 report — decision-focused selection MVP

- `pipeline_verdict`: **FAIL** (artifact hashes/folds pass, but independent primary-metric recomputation does not reproduce all saved primary metrics)
- `scientific_gate`: **INCONCLUSIVE**

## Integrity

Protocol and input hashes match FREEZE. Fold counts are `[272, 274, 280, 294, 283]` and active count is `348`; saved fold/active arrays match.

## Independent checks

- `raw_k20` query 5 was independently recomputed from shared-option cosine and clipped-similarity weighted k=20; representative prediction matched within numerical precision.
- `ridge_raw` query 0 was independently refit with reference-only feature/target imputation and dual alpha=100 ridge; representative prediction matched within `5.22e-15`.
- Decision scores reproduce the query-0 top-set direction when ranked descending.
- `raw_r` and `raw_mae` recompute exactly from saved predictions.

## Primary metric discrepancy

Using the protocol's stated reference-fold generic-profile projection residualisation, finite-line top-10% sets, and descending decision scores, the independent implementation does **not** reproduce all CSV primary fields. Maximum observed errors were: top10_overlap `0.2678571428571429`, selection_regret `0.6639069069537253`, raw_threshold_hit `0.3035714285714286`; raw_r and raw_mae error was approximately zero. Aggregate summaries differ by at most `0.09550365753329748`.

The exact residualisation/missing-mask/tie convention cannot be resolved without reading the prohibited `run.py`; this is recorded as an unresolved implementation ambiguity rather than silently forcing agreement.

## Scientific limits

This is an exploratory, non-confirmatory exposed development-pool experiment. The negative or mixed decision-head result does not establish or refute a core innovation, mechanism, causality, or external generalisation.
