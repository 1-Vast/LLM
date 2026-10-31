# Decision-focused selection MVP

Date: 2026-10-31 (Asia/Shanghai)
Status: exploratory, non-confirmatory, no core-promotion authority

## Question

Using only the already available L1000 perturbation signatures, does a supervised
top-10% cell-line decision head improve held-out cell-line selection utility over
raw signature-neighbor transfer and ordinary continuous ridge prediction?

This tests the prediction-to-choice mismatch identified by the cross-field review.
It does not test treatment history, sequence, dose response, causal transport,
intervention-sufficient state, organoid behavior or Agent value.

## Information boundary

The only scientific input is:

`D:/MAESTRO/data/processed/generic_axis_transfer_20261031/dev_pool.npz`

The input contains 1,403 compounds, 18 L1000 option slots, 978 genes and 578 PRISM
19Q4 cell-line profiles. NCI-60, PRISM 24Q2, sealed outcomes, external downloads,
model weights, `src/`, `tools/` and Agent modules are prohibited.

## Frozen split and fitting

Five folds are assigned by SHA-256 of non-empty `ik14` connectivity blocks modulo 5;
empty entries use a unique singleton label. Every feature imputation, generic profile,
decision label, and model fit uses reference compounds only. Query outcomes are used
only for evaluation.

## Arms

1. `raw_k20`: mean cosine over shared measured L1000 options and clipped-similarity
   weighted k=20 neighbor transfer.
2. `ridge_raw`: ordinary multi-output ridge (`alpha=100`, cholesky solver) predicting
   the continuous PRISM profile from the flattened raw signature with reference-fold
   feature and target imputation.
3. `decision_top10_ridge`: a direct decision head. For each reference compound,
   residualize its profile on the reference-fold generic profile, mark the most
   sensitive 10% of observed cell lines as label 1 and the remainder as 0, then fit
   the same ordinary ridge to these labels. Query scores rank cell lines directly.

The decision head has no post-freeze hyperparameter search. It is a standard supervised
surrogate for selection loss, not a new algorithm or a biological mechanism.

## Endpoints

For each query, residualized observed sensitivity is `-residualize(profile, generic)`.
The predicted top set contains `round(10% of finite lines)` lines.

- `top10_overlap`: fraction of the oracle top set recovered by the predicted set;
- `selection_regret`: oracle top-set mean sensitivity minus predicted top-set mean
  sensitivity, lower is better;
- `raw_threshold_hit`: fraction of selected lines whose raw LFC is at most -1,
  reported as a secondary descriptive quantity.

Continuous profile Pearson and MAE are reported for the calibrated `ridge_raw` arm.
The decision head is not treated as a calibrated viability profile. Summaries are
reported on active compounds and all compounds. No inferential gate or novelty claim
is attached to this exposed development experiment.

## Interpretation and stop rule

If the decision head improves selection metrics, this is evidence that a decision
surrogate deserves a fairer external comparison; it is not evidence of a new cell
state or biology. If it ties or loses to ridge/raw transfer, the decision-focused
head is parked under this input contract. Either outcome leaves the action-contrast
core question dependent on a real early-state/next-action/later-function dataset.

No result from this MVP may promote code to `src/` or `tools/`, start AIVO work, or
authorize an Agent implementation.

## Reproducibility

`run.py` is executed once after this protocol and its freeze metadata are written. It
must save per-query metrics, predictions, environment, input/code hashes and a JSON
summary. An independent reviewer must inspect the protocol and recompute the primary
metrics before any scientific interpretation beyond this pilot.
