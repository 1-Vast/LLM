# Pre-value conditional protein information protocol

## Falsifiable question and information

For the same48development drugs and same outer42scaffold groups as the functional pilot, predict published metabolic relative intensity at10/100/1000nM. Every method receives target10000nMfunctional entry. Molecular programs additionally receive the protein Normalized_Intensity_10000 vector from that same nominal treatment condition. All source programs see the same source whole functional curves and source high-dose protein vectors. No source/target lower-dose protein values are read. The primary question is conditional protein information, not novelty or world-model necessity. Protein acquisition is an extra proteomic profile, not a free scalar.

Same frozen48/48/48partition; no selection/later response access. Reuse previous developmental functional arrays, chemical kernel and groups. Both exact/file metadata and rowdrug identity must agree using explicit documented aliases. The standardizedALLfiles are chosen before values; no RF/curve class, significance, peptide count, future-dose missingness, slope/EC50/AUC, Mean_Intensity or MAD used as features or row filters.

## Selective decoding and preprocessing

Decode identifier, drug and Normalized_Intensity_10000 only. Keep original payload text and row number for audit. Duplicate identifiers within one drug file cause STOP before model fitting rather than an arbitrary aggregation. Empty/NA/NaN/nonfinite intensity is missing; numerical finite zero is retained as zero; negative finite intensity stops preparation for scientific review. Keep an explicit missingness mask. Do not collapse distinct proteins by fuzzy gene name. File row membership is processed-ALL ascertainment, not independently verified selected-dose detection.

Build a global identifier list for storage only; each model fold's eligible features depend **only on that source fold**. Values: source observed fraction at least.8 and nonzero source std after transform log2(1+intensity), threshold1e-6. Impute transformed source mean, standardize by source observed std(ddof0), floored1e-6; target missing values map to source mean(z=0). Missingness: source row-presence/validity bits only, use all identifiers present in at least one source file with source varying missingness; center source mean and divide source std floored1e-6. Target-only protein identifiers cannot become predictive features. No outcome-based feature selection; no test-derived quantiles/scales. Report source eligibility and target missingness.

Protein linear kernels divide by the number of retained features so block size alone does not increase feature weight. Chemical Tanimoto and source-standardized high-functional support kernels match the previous pilot (fixed equal kernel-block weights), with source-only centering. Mask and value blocks receive equal fixed weight when combined. No hyperparameter rescue or post-result feature grid.

## Fixed ordinary program menu

Nested group leave-one-out tunes λ∈{.01,.1,1,10}; outer held-out group never contributes to source means, eligibility, imputation, kernel scales, projection or model/parameter selection. Source functional risk at the same three query doses selects. Inner held-out drugs reveal only their high functional and high molecular inputs, as legal for that method.

1. **F-Gaussian**: the previous ordinary five-dose covariance conditional predictor, exact same λ/scale conventions, using high functional entry only. Prior result is reference; save/check numerical agreement rather than interpreting recomputation as a second experiment.
2. **F-direct**: previous chemical+high-functional direct kernel ridge, same conventions. This is another functional-only baseline.
3. **M-mask-direct**: F-direct plus mask linear kernel.
4. **M-value-direct**: F-direct plus value linear kernel.
5. **M-both-direct**: F-direct plus mask and value linear kernels.
6. **M-RBF-direct**: F-direct plus an RBF on the concatenation of the source-standardized values and masks (each block divided by sqrt(numberfeatures)); bandwidth equals the median positive source pair squared distance, frozen rule, zero-distance fallback kernel1. Same λgrid.
7. **M-joint-PC**: ordinary joint Gaussian/linear conditional prediction of query function from high functional plus the top8source-only PCs of combined standardized molecular values/masks. PCA components are standardized on source, then divided by sqrt(rank); source support is standardized; rank=min(8,Nsource−2,nonzeroeigenvalues). Linear conditional regression regularized by λI in feature covariance, equivalently kernel ridge. No chemical input in this program; equivalent same-information direct form will be checked mathematically rather than claiming a new operation.
8. **M-residual**: F-Gaussian plus molecular kernel ridge correction, using the M-both protein kernel without chemical. Source correction targets are **source-group-cross-fitted F-Gaussian residuals**, obtained entirely within current source set; never in-sample F-Gaussian residuals that use their own query values. For this finite baseline use fixed Gaussianλ.1 for residual construction and base prediction, tune residual ridgeλsame4. Retain this fixed base variation explicitly; it is not the nested-optimal F-Gaussian.
9. **M-mix**: fixed equal average of F-Gaussian and M-both-direct fitted at the same λ, tune same4λ. Not a new method; checks simple error complementarity.

All same-information molecular programs are ordinary controls. Program count does not prove significance. Define a functional-only portfolio selecting1/2using inner risk and a molecular portfolio selecting3–9using inner risk. Also save each program's OOF predictions, hyperchoices and risks. Main comparison is molecular-selected versus functional-selected; disclose extra source search opportunities (28molecular configurations vs8functional, before fold duplication). No claim of agent or equal-budgetsearch superiority. Direct values-versus-mask comparisons isolate missingness contributions.

## Loss, uncertainty and advance/stop

Primary MSE equal weights across three query doses then drugs; secondary MAE/per-dose risks and full per-drug losses. Main paired95%percentile interval from10000resamples of the42development scaffold groups with all drug weights retained and normalized by sampled drug count; seed20261022. FixedOOFonly, no biological measurement uncertainty or retraining uncertainty. Source fitting and model search are exploratory within the previously exposed48drug development set; reserves remain closed.

Advance to focused new-mechanism proposals only if molecular portfolio beats functional portfolio with lower95%gaininterval>0, nonnegative gains in at least2query-dose means, and mean gain remains positive after deleting each of the3largest absolute-gain drugs separately. It must also outperform F-Gaussian overall MSE and a **value-containing direct program** must show positive average gain over M-mask-direct (to avoid calling pure missingness or one favorable indirect portfolio a molecular value contribution). This is a development allocation gate, not utility/noise/novelty confirmation. Report all comparisons; no endpoint switch, opening96drugs, larger grid or second molecular dose to rescue failure.

If gate fails: STOP this exact high-dose incremental-information expansion toward WM/agent/RSI; preserve scoped positive/negative information. Do not conclude all molecular data useless. If gate passes: results establish a useful ordinary conditional-information candidate at most; prior published-processing uncertainty and absent functional repeats still limit interpretation. Proposed innovation must identify a repeatable residual error beyond these strong same-information controls, then receive opposing independent review before testing.

## Verification and cost

Save raw responses/headers/receipts/hash, exact rows/payloads, drug×protein matrix and missingness, predictions, source-selected choices, eligibility counts, timings and environments. Tests: target query perturbation leaves its prediction and selection unchanged; holdout-only protein changes do not alter source eligible set/scaling; joint-PC primal/dual equality within1e-8. Independent auditor selectively reconstructs all high-dose values and redoes metrics/bootstrap without importing model implementation; does not need to rerun all regressions unless concern arises. Count48target/source published high-dose profiles and48functional source curves; no actual wet cost/API dollars invented.
