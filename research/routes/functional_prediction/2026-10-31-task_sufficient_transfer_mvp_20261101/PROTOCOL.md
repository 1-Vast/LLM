# Task-sufficient transfer MVP: exploratory pilot

Study: `task_sufficient_transfer_mvp_20261101`
Date: 2026-10-31 (client date; actual UTC/local timestamps in FREEZE.json)
Status: exploratory / non-confirmatory

## Question

Can a reference-only low-dimensional state retain the drug-response transfer behavior of the full L1000 signature while improving or preserving selective cell-line selection on an exposed PRISM 19Q4 development pool?

This is a task-sufficient representation probe. It does not test a biological intervention-sufficient state, causality, organoid behavior, or Agent utility. The data contain compound-level L1000 signatures and PRISM viability profiles, but no matched baseline state, dose series, spatial variables or single-cell composition.

## Information boundary

Only `D:/MAESTRO/data/processed/generic_axis_transfer_20261031/dev_pool.npz` may be read. This file is the exposed PRISM 19Q4 development pool used for an exploratory pilot. The following are prohibited: NCI-60 or PRISM 24Q2 response arrays, any unblind/unseal operation, the RTL-01 runner, existing GAT confirmation runners, `src/` or `tools/` edits, model weights, external downloads and Agent modules.

The source file is copied by reference and bound by SHA-256 in `FREEZE.json`. Existing GAT study files are read only for conceptual alignment; no existing study is modified.

## Data contract

`dev_pool.npz` contains:

- `signature`: `(n_compounds, 18_options, 978_genes)` L1000 signatures at 10 uM for up to nine core lines at 6/24 h; unmeasured options are NaN.
- `profile`: `(n_compounds, 578_lines)` PRISM 19Q4 log2 fold-change profiles; missing values are NaN.
- `ik14`: InChIKey connectivity blocks used only for grouped folds.
- `drug`, `line`, `option`, `fingerprint`: identifiers or unused metadata; fingerprints are not used in the state candidates.

Observed contract facts are recorded from the exposed file at freeze time. No confirmation response values are read.

## Fixed folds and fitting rules

Five folds are assigned deterministically from SHA-256 of the non-empty `ik14` connectivity block modulo 5. Empty `ik14` entries receive unique singleton group labels. Every mean, generic direction, PCA basis, random projection, feature imputation, target imputation and ridge fit is fitted on the reference folds only. The query fold is never used to fit a transformation or target statistic.

## Arms

1. `raw_k5`: raw mean cosine across shared options; clipped-similarity weighted kNN with `k=5`.
2. `raw_k20`: raw mean cosine and k=20, controlling neighbor count.
3. `chemistry_k20`: Morgan fingerprint Tanimoto with k=20 and no transcriptomic input.
4. `global_residual_diagnostic`: decompose each reference outcome into compound mean plus generic-profile projection plus residual; transfer both components with the same GAT weights and reassemble. This is an algebraic diagnostic and should equal GAT within floating-point error.
5. `gat_d5_k20`: reference-centred per-option signatures with the top `D=5` reference principal directions removed; mean cosine and clipped-similarity weighted kNN with `k=20`.
3. `pca_residual_k{2,5,10,20,50,100}`: GAT residuals flattened with unmeasured entries at zero; a reference-only randomized PCA basis fitted at 100 components (`iterated_power=3`, `n_oversamples=10`, QR normalization, seed=20261101+fold); both reference and query states use `.transform` after fitting; the first K state coordinates are compared by cosine and transferred with `k=20`.
4. `random_residual_k{2,5,10,20,50,100}`: the same residual flattened state projected by a fixed reference-independent orthonormal Gaussian matrix of dimension K; kNN transfer with `k=20`. This is a dimension-matched control.
5. `ridge_raw`: ordinary reference-only multi-output ridge on flattened raw signatures, reference-mean imputation for missing signature features and response lines, `alpha=100`, `solver=cholesky` (dual system for n_features > n_samples). No outcome-derived feature selection is used.

The PCA and random state dimensions are fixed before execution. The random projection seed is `20261101`.

7. `full_flat_residual_k20`: full flattened GAT residual cosine, controlling the geometry change from option-mean cosine to flattened cosine.
8. `gat_permuted_null`: GAT similarities with reference viability rows permuted using `seed=20261101+1000+fold`.

## Endpoints

A compound is exploratory-active when at least 5% of its evaluated lines have LFC <= -1 (missing values are not hits), matching the exposed GAT development rule. Primary summaries are reported on active compounds and on all compounds separately.

For each held-out compound and arm:

- Primary: selective top-10% cell-line hit precision, computed after residualising predicted and observed profiles on the reference-fold generic profile. PRISM sensitivity is `-LFC`; top count is nearest integer with at least one line.
- Primary companion: selective top-10% selection regret = observed oracle top-m mean sensitivity minus observed mean sensitivity of the predicted top-m set, using the same reference-generic residuals. `1 - hit_precision` is separately named miss rate.
- Secondary: selective Pearson `r`, raw profile Pearson `r`, mean absolute raw profile error, and neighbor overlap with `raw_k20` for kNN arms (Jaccard; raw_k5 has five neighbors). The neighbor quantity is a representation-overlap diagnostic, not a causal stability claim.

Undefined correlations are recorded as NaN and excluded from means; hit precision is NaN when fewer than 40 shared lines or a flat profile prevents ranking. Per-query metrics and predictions are saved.

## Exploratory decision rule

This pilot is non-confirmatory and cannot promote code or establish the core innovation. Existing NCI-60 and PRISM 24Q2 outcomes were already exposed in GAT and would only support retrospective checks, never pristine confirmation for this new candidate. The pilot describes paired changes and dimension-performance curves against `gat_d5_k20`; no non-inferiority claim is made because no formal margin or confirmatory confidence procedure is specified. Any retained candidate requires a separately frozen external test. A positive correlation alone is insufficient. If the full signature and compressed states perform equivalently, the result is measurement compression rather than evidence for a minimal functional state. If decision utility falls, the task-sufficient-state line stops.

No post-run arm, hyperparameter, fold, metric or outcome transformation may be added to change this disposition.

## Reproducibility

`mvp_run.py` is the only runner. It writes `RUN/RESULTS.json`, per-query predictions and metrics, `environment.json`, and `RUN_stdout.log`. The execution is exactly once after `FREEZE.json` is written. An independent verifier is required before any interpretation beyond this exploratory pilot.



## Final pre-freeze corrections

Actual receipt UTC: 2026-10-31T07:42:56.207315+00:00. Before freeze: corrected date label; distinguished miss rate from true selective selection regret; removed formal non-inferiority language; added raw k20, chemistry k20, target-decomposition identity diagnostic, full flattened residual geometry control and reference-target permutation null; fixed PCA/random settings; chose cholesky ridge to avoid repeated LSQR target solves. All are final pre-run choices. No model grid was executed before freeze.
