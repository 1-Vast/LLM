# Static pre-fit review: matched-guide common-panel comparison

**Reviewer:** independent static audit (2026-10-22)
**Scope:** `research/norman_matched_guide_20261022/compare.py` and the frozen `PREDICTION_PROTOCOL.md` only. No model fit was run and no development/protected labels were read.

## Verdict

**PASS WITH NON-BLOCKING CONDITIONS.** The implementation matches the stated source-only five-fold protocol. I found no code-level source/development/protected leakage or inner-selection leakage that blocks the planned run. The output must remain descriptive and endpoint-specific as stated in the protocol.

## Checks supporting the verdict

- The input is `SOURCE_MATCHED_ENDPOINT.csv`; the code asserts 3,107 unique pairs and asserts every pair has `split == source` from the frozen `PAIR_SPLITS.csv`. Fold assignment uses the predeclared reliability salt and outer assessment is disjoint from outer training.
- Pair order for outer training is taken from `source_order`; the inner split is the first 75% of that outer training sequence and the final 25% is used only for parameter selection. The code asserts inner and validation disjointness. The outer assessment labels are not used in selection.
- For each endpoint, the quadratic baseline is fitted on the relevant inner or outer training subset only. Residual ridge scalers/models are fitted only on the corresponding training subset. Nuclear completion receives only training residual observations; its predictions for validation/assessment are generated after fitting on the corresponding training subset.
- The average and chosen endpoints use separate endpoint-matched single-gene priors and separate targets. Endpoint values are not used as features for the other endpoint. Both endpoints receive the same five folds, feature construction, model menu, and parameter menus.
- RNA features are used only as inputs. The global 102-gene SVD/correlation transforms do not consume pair labels, and therefore are unsupervised/transductive feature preprocessing rather than outcome leakage. This should remain explicitly disclosed in the final result.
- The planned fit accounting is internally consistent: per endpoint and outer fold, two quadratic fits plus four model families × (three inner candidates + one outer refit) = 18 fit records; two endpoints × five folds gives 180 records. `COSTS.json` is prepared to audit this.

## Conditions and limitations (non-blocking for this run)

1. **Compute budget is not equal in wall-clock terms.** Ridge, SVD and nuclear completion have different computational costs and nuclear completion can run up to 2,000 iterations per candidate. The protocol equalizes labels, folds, and parameter-search opportunities, but not elapsed compute. Preserve all `seconds`, `iterations`, and `converged` fields and report cost alongside accuracy; do not call this a total-compute-matched comparison.
2. **Feature preprocessing is transductive.** SVD and the gene-gene correlation side matrix are formed from all 102 eligible genes before outer folds. They use no functional labels, so this is not outcome leakage, but it is not a fully inductive fold-local feature pipeline. Keep the claim to the declared common-panel capability comparison and do not infer cross-panel or new-gene generalization.
3. **The endpoint comparison changes the estimand and prior association jointly.** A positive `G_chosen - G_average` cannot establish causal guide alignment, noise reduction, or method superiority. The protocol correctly limits this to a descriptive direction; preserve the stop rule if the difference is non-positive.
4. **The comparison is source-only and one K562 context.** It cannot establish independent generalization, world-model necessity, agent benefit, inheritance, or RSI. No subsequent architecture claim should be made from this run alone.
5. **Convergence is audited but not a universal success criterion.** `complete()` records `converged`, iteration count, and objective, while `RESULT.json` records a stop-heuristic count. A high non-convergence count or non-finite output should invalidate the run or trigger a predeclared review, rather than being silently treated as a successful model fit.

## Arithmetic review

The outer MSEs are computed from assembled out-of-fold predictions, and fold scores are computed only on each fold's held-out pairs. Relative gain is correctly defined against the same-endpoint `identity_nuclear` MSE, with endpoint variance and ratio retained. The quadratic baseline is included as a separate arm. No protected values are referenced by the reviewed code.

## Decision

**Allow the pre-registered execution**, subject to preserving the above disclosures and auditing `fit_count == 180`, finite OOF predictions, five non-overlapping folds, source-only membership, parameter selections, and convergence/cost fields after execution. This review does not endorse a positive scientific result in advance.
